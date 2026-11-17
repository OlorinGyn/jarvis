"""Replay a stretch of production's person events through the visit rules (backlog 41). Read-only.

Reads the event JSONs under clips/, the face sightings under faces/ and the
logs under logs/ of a J.A.R.V.I.S. folder. Each message the log says was sent,
or failed, is joined to its event by the face scan's clip name on its assembly
thread. Every person event then goes through notify.after_scan itself, in
Home, twice: with the visit off (today's rule, to check the replay against
the log) and on, Telegram replaced by a list.

    uv run python tools/replay_visits.py C:\\JARVIS --since 2026-10-16T21:28
"""

import argparse
import json
import logging
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from jarvis import notify
from jarvis.clips import PRE_SECONDS
from jarvis.faces import side_view_path

LINE = re.compile(r"^(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d),\d+ [A-Z]+ (.+?) jarvis\.(\w+): (.*)$")
SCAN = re.compile(r"^  face scan (\d\d-\d\d-\d\d)\.mp4: ")
NOTIFICATION = re.compile(r"^Notification (\S+) (.+?): (sent silently|sent|failed)")
PERSON_KINDS = ("best view", "side view", "hidden person", "face")


def kind_of(what):
    """best view, side view, hidden person, face, or other, from a logged subject."""
    return next((kind for kind in PERSON_KINDS if what.startswith(kind)), "other")


def read_events(root, since):
    """Every event from since on: key Camera/day/HH-MM-SS to its JSON, with start, end and paths."""
    events = {}
    for path in sorted((root / "clips").glob("*/*/*.json")):
        try:
            meta = json.loads(path.read_text(encoding="utf-8-sig"))
            start = datetime.fromisoformat(meta["started_at"])
        except (OSError, ValueError, KeyError):
            continue
        if start < since:
            continue
        key = f"{path.parent.parent.name}/{path.parent.name}/{path.stem}"
        best = path.with_name(meta["best_thumbnail"]) if meta.get("best_thumbnail") else None
        people = path.with_name(meta["people_thumbnail"]) if meta.get("people_thumbnail") else None
        meta.update(key=key, start=start, path=path, best_path=best, people_path=people,
                    side_path=side_view_path(path.with_suffix(".mp4")),
                    end=start + timedelta(seconds=max(meta.get("seconds", PRE_SECONDS) - PRE_SECONDS, 0)))
        events[key] = meta
    return events


def read_sightings(root, gallery):
    """Per event key, the scan's faces as notify sees them: person_id, name, score, resident."""
    people = {entry["id"]: entry for entry in gallery.get("people", [])}
    found = defaultdict(list)
    for path in (root / "faces").glob("*/*.json"):
        try:
            sighting = json.loads(path.read_text(encoding="utf-8-sig"))
        except (OSError, ValueError):
            continue
        clip = Path(str(sighting.get("clip", "")).replace("\\", "/"))
        if len(clip.parts) < 3:
            continue
        entry = people.get(sighting.get("person_id"), {})
        found[f"{clip.parts[-3]}/{clip.parts[-2]}/{clip.stem}"].append(
            {"person_id": sighting.get("person_id"), "name": entry.get("name", ""),
             "score": sighting.get("score", 0.0), "resident": bool(entry.get("resident")),
             "thumbnail_path": None})
    return found


def read_log(root, since, events):
    """(time, camera, what, outcome, event key or None) per message the logs record from since on."""
    by_name = defaultdict(list)
    for key, meta in events.items():
        by_name[(meta["camera"], meta["path"].stem)].append(meta)
    lines = []
    for path in sorted((root / "logs").glob("jarvis.log*"), key=lambda p: p.stat().st_mtime):
        lines += path.read_text(encoding="utf-8", errors="replace").splitlines()
    scans, found = {}, []
    for line in lines:
        match = LINE.match(line)
        if not match:
            continue
        when = datetime.strptime(match[1], "%Y-%m-%d %H:%M:%S")
        thread, module, text = match[2], match[3], match[4]
        if module == "cameras" and text.startswith("Starting "):
            scans.clear()
        scan = SCAN.match(text) if module == "faces" else None
        if scan:
            scans[thread] = scan[1]
            continue
        message = NOTIFICATION.match(text) if module == "notify" else None
        if not message or when < since:
            continue
        camera, what = message[1].rstrip(":"), message[2]
        key = None
        if "(_assemble)" in thread and thread in scans:
            candidates = [m for m in by_name.get((camera, scans[thread]), ()) if m["start"] <= when]
            key = max(candidates, key=lambda m: m["start"])["key"] if candidates else None
        found.append((when, camera, what, message[3], key))
    return found


def replay(events, sightings, settings, visits):
    """Run each person event's scan through notify.after_scan; the subjects it would send, per event key."""
    sent = defaultdict(list)
    current = {}
    notify._send_logged = lambda subject, text, image, values, silent=False: sent[current["key"]].append(subject) or True
    notify.threading.Timer = Idle
    notify.VISIT_SECONDS = 300 if visits else float("-inf")
    notify.dog_only = real_dog_only if visits else (lambda tracks: False)
    notify.reset_incident()
    for meta in sorted(events.values(), key=lambda m: m["start"]):
        if "person" not in meta.get("labels", ()):
            continue
        current["key"] = meta["key"]
        notify._clock = lambda: meta["start"].timestamp()
        best = meta["best_path"] if meta["best_path"] and meta["best_path"].exists() else None
        notify.after_scan(meta["camera"], meta["start"], sightings.get(meta["key"], []), True, False,
                          meta["side_path"], best, settings, people=meta.get("most_people", 0),
                          people_view=meta["people_path"], ended_at=meta["end"], tracks=meta.get("tracks"))
    return sent


class Reasons(logging.Handler):
    """Counts notify's skip lines by their reason, the visit's details cut off."""

    def __init__(self):
        super().__init__()
        self.counts = Counter()

    def emit(self, record):
        text = record.getMessage()
        if "skipped: visit" in text or "skipped: dog" in text:
            what = kind_of(text.split(": ")[0].split(" ", 2)[2])
            reason = text.split("skipped: ", 1)[1]
            reason = "visit (a resident recognized)" if "recognized at" in reason else reason
            self.counts[f"{what}: {reason.split(', ')[0].rstrip(')').replace(' (', ', ')}"] += 1


class Idle:
    """The floor's timer, never fired: the replay counts the person messages, not the floor's texts."""

    def __init__(self, interval, function, args=()):
        self.daemon = True

    def start(self):
        pass

    def cancel(self):
        pass


real_dog_only = notify.dog_only


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("root", type=Path, help="the J.A.R.V.I.S. folder, e.g. C:\\JARVIS")
    parser.add_argument("--since", type=datetime.fromisoformat, default=datetime(2026, 10, 16, 21, 28))
    args = parser.parse_args()
    root = args.root
    config = json.loads((root / "config.json").read_text(encoding="utf-8-sig"))
    settings = {**config, "notify_token": "0:replay", "notify_chat": "0", "notify_mode": "home"}
    gallery = json.loads((root / "faces" / "gallery_arcface_w600k_r50.json").read_text(encoding="utf-8-sig"))

    events = read_events(root, args.since)
    sightings = read_sightings(root, gallery)
    logged = read_log(root, args.since, events)
    until = max(when for when, *_ in logged)
    days = (until - args.since).total_seconds() / 86400

    person_logged = [m for m in logged if kind_of(m[2]) != "other"]
    other = [m for m in logged if kind_of(m[2]) == "other"]
    joined = [m for m in person_logged if m[4]]
    print(f"{args.since:%d/%m %H:%M} -> {until:%d/%m %H:%M}, {days:.1f} days, "
          f"{sum('person' in m.get('labels', ()) for m in events.values())} person events of {len(events)}")
    print(f"log: {len(logged)} messages ({len(logged) / days:.0f} a day), {len(person_logged)} about a person, "
          f"{len(joined)} joined to their event, {sum(m[3] == 'failed' for m in logged)} failed; "
          f"other: {dict(Counter(m[2].split(',')[0] if kind_of(m[2]) == 'other' else '' for m in other))}")

    today = replay(events, sightings, settings, visits=False)
    reasons = Reasons()
    notify.logger.addHandler(reasons)
    notify.logger.setLevel(logging.INFO)
    visit = replay(events, sightings, settings, visits=True)
    notify.logger.removeHandler(reasons)

    by_event_log = defaultdict(list)
    for message in joined:
        by_event_log[message[4]].append(message[2])
    mismatch = [key for key in set(by_event_log) | set(today)
                if Counter(kind_of(w) for w in by_event_log.get(key, ())) !=
                Counter(kind_of(s.split(" ", 1)[1]) for s in today.get(key, ()))]
    replayed_today = sum(len(v) for v in today.values())
    replayed_visit = sum(len(v) for v in visit.values())
    print(f"replay, visit off: {replayed_today} person messages ({replayed_today / days:.0f} a day); "
          f"events whose kinds differ from the log: {len(mismatch)}")
    print(f"replay, visit on:  {replayed_visit} person messages ({replayed_visit / days:.0f} a day)")
    unjoined = len(person_logged) - len(joined)
    total_visit = replayed_visit + unjoined + len(other)
    print(f"all messages a day: log {len(logged) / days:.0f} -> {total_visit / days:.0f} with the visit "
          f"(the {unjoined} unjoined person messages and {len(other)} others kept as they were)")

    kinds_today = Counter(kind_of(s.split(" ", 1)[1]) for v in today.values() for s in v)
    kinds_visit = Counter(kind_of(s.split(" ", 1)[1]) for v in visit.values() for s in v)
    print("by kind, visit off -> on:", {k: f"{kinds_today[k]} -> {kinds_visit[k]}" for k in PERSON_KINDS})

    dropped_faces = []
    for key, subjects in today.items():
        left = Counter(visit.get(key, ()))
        for subject in subjects:
            if left[subject]:
                left[subject] -= 1
            elif kind_of(subject.split(" ", 1)[1]) == "face":
                dropped_faces.append((key, subject))
    print(f"face messages dropped: {len(dropped_faces)}, every one a non-resident's: Home silences "
          f"the residents' faces, sure and probable")
    print("not sent, by rule:")
    for reason, count in sorted(reasons.counts.items(), key=lambda item: -item[1]):
        print(f"  {count:5d}  {reason}")
    for key in sorted(mismatch)[:15]:
        print(f"  differs: {key}: log {by_event_log.get(key, [])} replay {today.get(key, [])}")


if __name__ == "__main__":
    main()
