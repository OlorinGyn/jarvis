"""Measure what a name following the body would add over the visit (item 7 part 2), on production's events. Read-only.

Reads the event JSONs' tracks, the logs' restarts and the built path's
messages (replay_quick_pass --built --aside, its face cache filled by
--detect), and classes every person message sent without a face:

    (a) a person track of it is in an earlier event of the camera, in the
        same run, whose full scan found a sure resident
    (b) more person tracks at once than faces found, a sure resident among them
    (c) neither

Then the consecutive person events that share a track id, and the person
tracks that live for minutes.

    uv run python tools/follow_body.py C:\\JARVIS --since 2026-11-10
"""

import argparse
import bisect
import pickle
import re
import statistics
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from itertools import islice
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import replay
import replay_quick_pass
import replay_tracks
from jarvis import faces, people, tracks
from jarvis.capture import ANALYSIS_WIDTH
from jarvis.motion import WARMUP_FRAMES, MotionDetector
from jarvis.tracks import voted
from person_signals import PHASES

BIND_SECONDS = 0.5
STARTING = re.compile(r"^(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d),\d+ [A-Z]+ .+? jarvis\.cameras: Starting \d+ camera")
FACELESS = ("no face", "hidden person")
CLASSES = ("a", "b", "c")
EXAMPLES = 3
LOITER_MINUTES = (2, 5)


def read_restarts(root):
    """Every moment production started its cameras, from the logs, sorted."""
    moments = []
    for path in (root / "logs").glob("jarvis.log*"):
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            found = STARTING.match(line)
            if found:
                moments.append(datetime.strptime(found[1], "%Y-%m-%d %H:%M:%S"))
    return sorted(set(moments))


def run_of(moment, restarts):
    """Which run of production a moment belongs to: the number of restarts before it."""
    return bisect.bisect_right(restarts, moment)


def person_ids(meta):
    """The ids of the event's tracks voted person over its own frames."""
    return {track["id"] for track in meta.get("tracks") or () if voted(Counter(track["frames"])) == "person"}


def track_ids(meta):
    return {track["id"] for track in meta.get("tracks") or ()}


def sure_resident(found, sure):
    """Whether a scan's sightings hold a resident named at the sure threshold or above."""
    return any(s.get("resident") and s.get("name") and s.get("score", 0.0) >= sure for s in found or ())


def kind(subject):
    return replay_quick_pass.kind(subject)


def classify(span, sent, full, sure, restarts):
    """One row per faceless person message: key, camera, day, kind, class, and the named event that explains (a)."""
    named = defaultdict(list)
    rows = []
    for meta in sorted(span, key=lambda m: m["start"]):
        key, run = meta["key"], run_of(meta["start"], restarts)
        ids = person_ids(meta)
        found = full.get(key) or []
        for subject in sent.get(key, ()):
            what = kind(subject)
            if what not in FACELESS:
                continue
            source = next((earlier for earlier, earlier_ids in reversed(named[meta["camera"], run])
                           if ids & earlier_ids), None)
            if source:
                cls = "a"
            elif (meta.get("most_person_tracks") or 0) > len(found) and sure_resident(found, sure):
                cls = "b"
            else:
                cls = "c"
            rows.append({"key": key, "camera": meta["camera"], "day": meta["start"].date(), "kind": what,
                         "class": cls, "source": source})
        if sure_resident(found, sure):
            named[meta["camera"], run].append((key, track_ids(meta)))
    return rows


def consecutive(span, restarts):
    """Each pair of consecutive person events of a camera: shared track ids within one run, and the gap between them."""
    by_camera = defaultdict(list)
    for meta in span:
        by_camera[meta["camera"]].append(meta)
    pairs = []
    for metas in by_camera.values():
        metas.sort(key=lambda m: m["start"])
        for before, after in zip(metas, metas[1:]):
            same_run = run_of(before["start"], restarts) == run_of(after["start"], restarts)
            shared = track_ids(before) & track_ids(after) if same_run else set()
            pairs.append({"before": before["key"], "after": after["key"], "day": after["start"].date(),
                          "shared": shared, "gap": (after["start"] - before["end"]).total_seconds()})
    return pairs


def lifetimes(span, full, restarts):
    """Every track by camera, run and id: its first and last moment over all its events, events, vote, faces."""
    joined = {}
    for meta in span:
        run = run_of(meta["start"], restarts)
        for track in meta.get("tracks") or ():
            name = (meta["camera"], run, track["id"])
            first = meta["start"] + timedelta(seconds=track["first"])
            last = meta["start"] + timedelta(seconds=track["last"])
            entry = joined.setdefault(name, {"first": first, "last": last, "events": [], "frames": Counter(),
                                             "face": False})
            entry["first"], entry["last"] = min(entry["first"], first), max(entry["last"], last)
            entry["events"].append(meta["key"])
            entry["frames"].update(track["frames"])
            entry["face"] = entry["face"] or bool(full.get(meta["key"]))
    for entry in joined.values():
        entry["seconds"] = (entry["last"] - entry["first"]).total_seconds()
        entry["person"] = voted(entry["frames"]) == "person"
    return joined


def per_day(rows, column, values):
    """A table of counts per day, one column per value, and the total."""
    days = sorted({row["day"] for row in rows})
    print(f"    {'day':10s} " + " ".join(f"{str(v):>8s}" for v in values) + "    total")
    for day in days:
        counts = Counter(row[column] for row in rows if row["day"] == day)
        print(f"    {day:%d/%m}      " + " ".join(f"{counts[v]:8d}" for v in values) + f" {sum(counts.values()):8d}")
    totals = Counter(row[column] for row in rows)
    print(f"    {'all':10s} " + " ".join(f"{totals[v]:8d}" for v in values) + f" {sum(totals.values()):8d}")


def report(result, restarts, since):
    """The three tables of part 1, with examples."""
    span, sent, full, sure = result["span"], result["sent"], result["full"], result["sure"]
    days = len({m["start"].date() for m in span})
    tracked = sum(1 for m in span if m.get("tracks"))
    print(f"\n{len(span)} person events since {since:%d/%m}, {tracked} with tracks, over {days} days; "
          f"{len(restarts)} restarts in the logs, {sum(r >= since for r in restarts)} in the span")

    rows = classify(span, sent, full, sure, restarts)
    print(f"\n1. Faceless person messages of the built path: {len(rows)}, by class")
    per_day(rows, "class", CLASSES)
    print("   by kind and class: " + ", ".join(f"{k} {c}: {n}" for (k, c), n in
                                             sorted(Counter((r["kind"], r["class"]) for r in rows).items())))
    for cls in CLASSES:
        examples = [r for r in rows if r["class"] == cls][:EXAMPLES]
        print(f"   ({cls}) " + "; ".join(f"{r['key']} {r['kind']}" + (f" <- {r['source']}" if r["source"] else "")
                                      for r in examples))
    explained = sum(r["class"] in ("a", "b") for r in rows)
    print(f"   (a) and (b) together: {explained}, {explained / max(days, 1):.2f} a day")

    pairs = consecutive(span, restarts)
    for pair in pairs:
        pair["shares"] = "shared" if pair["shared"] else "apart"
    print(f"\n2. Consecutive person events of a camera: {len(pairs)} pairs, sharing a track id or not")
    per_day(pairs, "shares", ("shared", "apart"))
    for shares in ("shared", "apart"):
        gaps = [p["gap"] for p in pairs if p["shares"] == shares]
        if gaps:
            print(f"   {shares}: gap from the first's end to the second's start median {statistics.median(gaps):.0f} s, "
                  f"p90 {replay_quick_pass.percentile(gaps, 0.9):.0f} s, max {max(gaps):.0f} s")
    print("   shared, examples: " + "; ".join(f"{p['before']} -> {p['after']} ({p['gap']:.0f} s, ids "
                                            f"{sorted(p['shared'])})" for p in pairs if p["shared"])[:EXAMPLES * 80])

    joined = lifetimes(span, full, restarts)
    persons = {name: e for name, e in joined.items() if e["person"]}
    print(f"\n3. Person tracks: {len(persons)}, {sum(len(e['events']) > 1 for e in persons.values())} in more than "
          f"one event")
    for minutes in LOITER_MINUTES:
        long = {name: e for name, e in persons.items() if e["seconds"] > minutes * 60}
        rows3 = [{"day": e["first"].date(), "what": ("across" if len(e["events"]) > 1 else "one event")
                  + (", face" if e["face"] else ", no face")} for e in long.values()]
        print(f"   living more than {minutes} min: {len(long)}")
        per_day(rows3, "what", ("across, face", "across, no face", "one event, face", "one event, no face"))
        for name, e in list(sorted(long.items(), key=lambda item: -item[1]["seconds"]))[:EXAMPLES]:
            print(f"     {name[0]} run {name[1]} id {name[2]}: {e['seconds'] / 60:.1f} min over "
                  f"{len(e['events'])} events, {e['events'][0]} .. {e['events'][-1]}")
    return rows, pairs, joined


def replayed_runs(videos, keep=False):
    """The live loop's phase 0 replayed over videos joined into one timeline: (video, moment, observed, frame) per run.

    Motion on every frame, YOLO and the tracker on every PHASES-th one, as
    replay_tracks does for each phase; frame is a half-size copy when kept.
    """
    placed = replay_tracks.timeline([str(v) for v in videos], join=True)
    motion = MotionDetector()
    detector = people.SubjectDetector()
    follower = tracks.Tracks()
    for frame in islice(replay.frames(placed[0][0]), WARMUP_FRAMES):
        motion.detect(frame)
    motion.candidates = []
    runs = []
    for index, (video, moment, frame) in enumerate(replay_tracks.frames(placed)):
        moving = motion.detect(frame)
        if index % PHASES:
            continue
        if not moving:
            detector.detect(frame, moving, now=moment)
            continue
        detector.last_run = float("-inf")
        found = list(detector.detect(frame, moving, now=moment))
        small = cv2.resize(frame, (frame.shape[1] // 2, frame.shape[0] // 2)) if keep else None
        runs.append((video, moment, follower.update(found, moment), small))
    return dict(placed), runs


def contains(box, point):
    x, y, w, h = box
    return x <= point[0] <= x + w and y <= point[1] <= y + h


def bind(runs, offsets, video, entry, scale, label_of):
    """Each cached face of one video on the person box of the nearest run within BIND_SECONDS that holds its centre.

    Joined videos overlap by the tail and the pre-roll, where the timeline
    keeps the earlier video's frames, so a face binds to whichever run is
    nearest in time. Returns per face its moment, track id or None, box at
    analysis size, identity, run index; inside two person boxes, the smaller.
    """
    moments = [moment for _, moment, _, _ in runs]
    bound = []
    for frame in entry["frames"]:
        moment = offsets[video] + frame["t"]
        index = min(range(len(runs)), key=lambda i: abs(moments[i] - moment), default=None)
        near = index is not None and abs(moments[index] - moment) <= BIND_SECONDS
        for face in frame["faces"]:
            box = [int(v * scale) for v in face["box"]]
            centre = (box[0] + box[2] / 2, box[1] + box[3] / 2)
            around = [(d.w * d.h, tid) for tid, d in runs[index][2]
                      if tid is not None and d.label == "person" and contains((d.x, d.y, d.w, d.h), centre)] \
                if near else []
            bound.append({"moment": moment, "track": min(around)[1] if around else None, "box": box,
                          "who": label_of(face["embedding"]), "run": index if near else None,
                          "ambiguous": len(around) > 1})
    return bound


def person_tracks_in(runs, start):
    """The replayed tracks voted person over the runs from start on, the timeline moment the last video begins."""
    labels = defaultdict(Counter)
    for _, moment, observed, _ in runs:
        if moment >= start:
            for tid, detection in observed:
                if tid is not None:
                    labels[tid][detection.label] += 1
    return {tid for tid, counted in labels.items() if voted(counted) == "person"}


def present_at(runs, index):
    return {tid for tid, d in runs[index][2] if tid is not None and d.label == "person"}


def saved_share(runs, bound, video, entry, offsets):
    """The share of the video's scanned frames whose nearest run holds only person tracks already named sure."""
    moments = [moment for _, moment, _, _ in runs]
    named_at = {}
    for face in sorted(bound, key=lambda f: f["moment"]):
        if face["track"] is not None and face["who"] == "sure resident":
            named_at.setdefault(face["track"], face["moment"])
    saved = 0
    for frame in entry["frames"]:
        moment = offsets[video] + frame["t"]
        index = min(range(len(runs)), key=lambda i: abs(moments[i] - moment), default=None)
        if index is None or abs(moments[index] - moment) > BIND_SECONDS:
            continue
        here = present_at(runs, index)
        saved += bool(here) and all(tid in named_at and named_at[tid] < moment for tid in here)
    return saved, len(entry["frames"])


def identity_of(gallery, sure):
    """A label per embedding: sure resident, probable resident, visitor or unknown."""
    def label_of(embedding):
        person_id, score = gallery.match(np.asarray(embedding, np.float32))
        person = gallery.get(person_id) or {}
        if not person.get("name"):
            return "unknown"
        if not person.get("resident"):
            return "visitor"
        return "sure resident" if score >= sure else "probable resident"
    return label_of


def clip_scale(video):
    width = faces._describe(video)[0]
    return ANALYSIS_WIDTH / width if width else 0.5


def bound_event(cache, meta, videos, runs, offsets, label_of):
    """The faces of one event bound to the replay, with its person tracks."""
    video = str(meta["path"].with_suffix(".mp4"))
    path = replay_quick_pass.cache_path(cache, meta["key"])
    entry = pickle.loads(path.read_bytes()) if path.exists() else {"frames": []}
    bound = bind(runs, offsets, video, entry, clip_scale(video), label_of)
    return video, entry, bound, person_tracks_in(runs, offsets[video])


def part2(result, rows, cache, root, sample, sheet_dir):
    """Faces bound to replayed tracks on the (a) and (b) events, a sample of named events, and the sheets."""
    events, span, full, sure = result["events"], result["span"], result["full"], result["sure"]
    label_of = identity_of(faces.Gallery(root / "faces" / faces.GALLERY_FILE.name), sure)
    by_camera = defaultdict(list)
    for meta in sorted(span, key=lambda m: m["start"]):
        by_camera[meta["camera"]].append(meta)
    began = time.monotonic()
    sheets = []
    print(f"\n4. Part 2: faces bound to the replayed tracks (phase 0, lost {tracks.LOST_SECONDS:g} s, "
          f"within {BIND_SECONDS} s, centre in the person box)")
    totals = Counter()
    for row in sorted({r["key"]: r for r in rows if r["class"] in ("a", "b")}.values(), key=lambda r: r["key"]):
        meta = events[row["key"]]
        chain = [meta]
        if row["class"] == "a":
            metas = by_camera[meta["camera"]]
            first = next(i for i, m in enumerate(metas) if m["key"] == row["source"])
            chain = metas[first:metas.index(meta) + 1]
        videos = [m["path"].with_suffix(".mp4") for m in chain]
        offsets, runs = replayed_runs(videos, keep=len(sheets) < EXAMPLES)
        named_tracks = set()
        for earlier in chain[:-1]:
            _, _, bound, _ = bound_event(cache, earlier, videos, runs, offsets, label_of)
            named_tracks |= {f["track"] for f in bound if f["who"] == "sure resident" and f["track"] is not None}
        video, entry, bound, persons = bound_event(cache, meta, videos, runs, offsets, label_of)
        named_tracks |= {f["track"] for f in bound if f["who"] == "sure resident" and f["track"] is not None}
        with_face = {f["track"] for f in bound if f["track"] is not None} & persons
        carried = named_tracks & persons
        every = bool(persons) and persons <= (with_face | carried)
        saved, scanned = saved_share(runs, bound, video, entry, offsets)
        totals.update(events=1, every=every, saved=saved, scanned=scanned, unbound=sum(f["track"] is None for f in bound),
                      faces=len(bound), ambiguous=sum(f["ambiguous"] for f in bound))
        print(f"   ({row['class']}) {row['key']} {row['kind']}: {len(persons)} person tracks, {len(with_face)} with a "
              f"face, {len(carried)} named sure (carried or here), every one named or faced: {every}; faces "
              f"{len(bound)}, unbound {sum(f['track'] is None for f in bound)}; frames saved {saved} of {scanned}"
              + (f"; chain of {len(chain)} events" if len(chain) > 1 else ""), flush=True)
        if runs[0][3] is not None and bound:
            sheets.append((row["key"], runs, bound))
    print(f"   explained (every person track named or with a face): {totals['every']} of {totals['events']}; "
          f"faces unbound {totals['unbound']} of {totals['faces']}, inside two boxes {totals['ambiguous']}")

    named = [m for m in span if sure_resident(full.get(m["key"]), sure)
             and replay_quick_pass.cache_path(cache, m["key"]).exists()]
    picked = faces.evenly(named, sample)
    saved_total = Counter()
    for meta in picked:
        video = meta["path"].with_suffix(".mp4")
        offsets, runs = replayed_runs([video])
        video, entry, bound, persons = bound_event(cache, meta, [video], runs, offsets, label_of)
        saved, scanned = saved_share(runs, bound, video, entry, offsets)
        saved_total.update(saved=saved, scanned=scanned, faces=len(bound),
                           unbound=sum(f["track"] is None for f in bound))
    if picked:
        print(f"   {len(picked)} events with a sure resident (of {len(named)}), evenly spread: frames after a "
              f"track's first sure face with only named tracks present {saved_total['saved']} of "
              f"{saved_total['scanned']} ({100 * saved_total['saved'] / max(saved_total['scanned'], 1):.0f} %); "
              f"faces unbound {saved_total['unbound']} of {saved_total['faces']}")
    for number, path in enumerate(binding_sheets(sheets, sheet_dir), 1):
        print(f"   binding sheet {number}: {path}")
    print(f"   part 2 took {time.monotonic() - began:.0f} s")


def crossing(result, pairs, sheet_dir):
    """The replay of EXAMPLES pairs that shared a live id, joined: the crossing track's last box before the cut and first after."""
    events = result["events"]
    rows = []
    for pair in [p for p in pairs if p["shared"]][::max(sum(bool(p["shared"]) for p in pairs) // EXAMPLES, 1)][:EXAMPLES]:
        videos = [events[pair["before"]]["path"].with_suffix(".mp4"), events[pair["after"]]["path"].with_suffix(".mp4")]
        offsets, runs = replayed_runs(videos, keep=True)
        first, second = (str(v) for v in videos)
        before = {tid for where, _, observed, _ in runs if where == first for tid, d in observed if d.label == "person"}
        after = {tid for where, _, observed, _ in runs if where == second for tid, d in observed if d.label == "person"}
        crossed = sorted((before & after) - {None})
        print(f"   {pair['before']} -> {pair['after']}: live ids {sorted(pair['shared'])}, replayed person tracks "
              f"crossing {crossed}")
        cells = []
        for tid in crossed[:1]:
            last = max((i for i, r in enumerate(runs) if r[0] == first and any(t == tid for t, _ in r[2])))
            nxt = min((i for i, r in enumerate(runs) if r[0] == second and any(t == tid for t, _ in r[2])))
            for index in (last, nxt):
                cells.append(drawn(runs, index, [], f"{Path(runs[index][0]).stem} {runs[index][1]:.1f} s #{tid}", tid))
        if cells:
            rows.append(np.hstack(cells))
    if rows:
        width = max(r.shape[1] for r in rows)
        sheet = np.vstack([np.hstack([r, np.full((r.shape[0], width - r.shape[1], 3), 255, np.uint8)]) for r in rows])
        sheet_dir.mkdir(parents=True, exist_ok=True)
        path = sheet_dir / "crossing.jpg"
        cv2.imwrite(str(path), sheet, [cv2.IMWRITE_JPEG_QUALITY, 88])
        print(f"   crossing sheet: {path}")


def drawn(runs, index, bound, text, only=None):
    """A run's half-size frame with its person boxes and track ids, and the faces bound at it."""
    image = runs[index][3].copy()
    for tid, d in runs[index][2]:
        if d.label != "person" or (only is not None and tid != only):
            continue
        cv2.rectangle(image, (d.x // 2, d.y // 2), ((d.x + d.w) // 2, (d.y + d.h) // 2), (0, 200, 0), 2)
        cv2.putText(image, f"#{tid}", (d.x // 2 + 2, d.y // 2 + 14), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
    for face in bound:
        x, y, w, h = (v // 2 for v in face["box"])
        cv2.rectangle(image, (x, y), (x + w, y + h), (0, 0, 255), 2)
        cv2.putText(image, f"{face['who']} -> #{face['track']}", (x, max(y - 4, 10)), cv2.FONT_HERSHEY_SIMPLEX, 0.4,
                    (0, 0, 255), 1)
    cv2.putText(image, text, (4, image.shape[0] - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1)
    return image


def binding_sheets(sheets, folder):
    """One row per clip: three runs where faces were bound, spread over the clip."""
    folder.mkdir(parents=True, exist_ok=True)
    rows = []
    for key, runs, bound in sheets:
        at = sorted({f["run"] for f in bound if f["run"] is not None})
        cells = [drawn(runs, index, [f for f in bound if f["run"] == index], f"{key} {runs[index][1]:.1f} s")
                 for index in faces.evenly(at, EXAMPLES)]
        if cells:
            rows.append(np.hstack(cells))
    if not rows:
        return []
    width = max(r.shape[1] for r in rows)
    sheet = np.vstack([np.hstack([r, np.full((r.shape[0], width - r.shape[1], 3), 255, np.uint8)]) for r in rows])
    path = folder / "binding.jpg"
    cv2.imwrite(str(path), sheet, [cv2.IMWRITE_JPEG_QUALITY, 88])
    return [path]


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("root", type=Path, help="the J.A.R.V.I.S. folder, e.g. C:\\JARVIS")
    parser.add_argument("--since", type=datetime.fromisoformat, default=datetime(2026, 11, 10))
    parser.add_argument("--cache", type=Path, default=replay_quick_pass.CACHE)
    parser.add_argument("--bind", action="store_true", help="part 2: bind the faces to replayed tracks")
    parser.add_argument("--sample", type=int, default=30, help="with --bind: named events for the saved share")
    args = parser.parse_args()
    replay_quick_pass.lower_priority()
    result = replay_quick_pass.built(args.root, args.since, args.cache, aside=True)
    restarts = read_restarts(args.root)
    rows, pairs, _ = report(result, restarts, args.since)
    if args.bind:
        part2(result, rows, args.cache, args.root, args.sample, args.cache / "sheets")
        crossing(result, pairs, args.cache / "sheets")


if __name__ == "__main__":
    main()
