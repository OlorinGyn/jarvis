"""Delete, once, every stored view the eye read poor or someone else's, and every unread view below the cut (backlog 45).

Usage: uv run python tools/clean_views.py <folder> [--apply] [--verdicts FILE]

<folder> is a J.A.R.V.I.S. folder; its faces/ and dogs/ are read. Every view,
chosen or waiting, of the face and the dog galleries is judged by the verdicts
read by eye (view_quality_verdicts.json): "poor" or "other" is deleted, "ok"
stays, however low a quality model scores it. A view the file does not hold
was never read, and stays only at the cut that now guards what enters: a face
at eDifFIQA(T) >= faces.QUALITY_CUT (no face found is below it), a dog whose
sighting's box is at least dogs.MIN_VIEW_BOX px (no sighting found is below it).
A named entry keeps its best view by the model (Gallery.drop_views); an unnamed
one left with none is removed, its sightings kept.

The dry run, the default, writes nothing: per entry what it holds and what
would go, and leave-one-event-out recognition with today's chosen views and
with what would be left, as ARCHITECTURE 10.18 measures it. --apply refuses
while the folder's J.A.R.V.I.S. answers on its port, copies faces/ and dogs/ to
backups/clean_views_<stamp>/ first, then deletes.
"""

import json
import shutil
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np
from dotenv import dotenv_values

from jarvis import dogs, faces, web

import view_quality

DELETE = {"poor": "read poor", "bad": "read poor", "other": "read someone else's"}


def face_judgement(path, verdict):
    """(reason, score): why a face view goes or stays, and eDifFIQA(T)'s score of its photo (None without a face)."""
    image = cv2.imread(str(path))
    score = faces.face_quality(image)
    if verdict in DELETE:
        return DELETE[verdict], score
    if verdict == "ok":
        return "read good", score
    if score is None:
        return "unread, no face", score
    return ("unread, at the cut" if score >= faces.QUALITY_CUT else "unread, below the cut"), score


def dog_judgement(side, verdict):
    """Why a dog view goes or stays, by its verdict or by its box side in px (0: no sighting found)."""
    if verdict in DELETE:
        return DELETE[verdict]
    if verdict == "ok":
        return "read good"
    return "unread, at the cut" if side >= dogs.MIN_VIEW_BOX else "unread, below the cut"


def goes(reason):
    """Whether a reason deletes the view."""
    return reason not in ("read good", "unread, at the cut")


def dog_sightings(folder):
    """The dog sightings of a folder, by event."""
    by_event = defaultdict(list)
    for path in (Path(folder) / "dogs").glob("*/*.json"):
        try:
            sighting = json.loads(path.read_text(encoding="utf-8-sig"))
        except (OSError, ValueError):
            continue
        if isinstance(sighting, dict) and sighting.get("clip"):
            by_event[faces.event_of(sighting["clip"])].append(sighting)
    return by_event


def views(gallery):
    """(entry, photo name, embedding, waiting) of every view with a photo, chosen first."""
    for person in gallery.people:
        for view, embedding, waiting in view_quality.held_views(person):
            if view:
                yield person, faces.photo_name(view), embedding, waiting


def judge(gallery, verdicts, folder, dog=False):
    """One row per view with a photo: its entry, its reason, its score for keeping the best, and what recognition needs."""
    by_event = dog_sightings(folder) if dog else None
    rows = []
    for person, name, embedding, waiting in views(gallery):
        path = gallery.view_dir / name
        event = (person.get("view_events") or {}).get(name, "")
        verdict = verdicts.get(name)
        if not path.is_file():
            reason, score = "photo missing", None
        elif dog:
            sighting = view_quality.same_picture(path, by_event.get(event, []), Path(folder) / "dogs")
            box = (sighting or {}).get("box") or [0, 0, 0, 0]
            score = max(box[2], box[3])
            reason = dog_judgement(score, verdict)
        else:
            reason, score = face_judgement(path, verdict)
        identity = (person["name"] or None) if dog else view_quality.face_identity(person)
        rows.append({"entry": person["id"], "photo": name, "reason": reason, "score": score, "waiting": waiting,
                     "verdict": verdict, "event": event, "identity": identity, "named": bool(person["name"]),
                     "vector": np.asarray(embedding, np.float64), "infrared": bool(dog and embedding[0])})
    return rows


def best_by(rows):
    """best(view) for drop_views: the view's score, higher is better; -1 for a view without one."""
    scores = {r["photo"]: r["score"] for r in rows}
    return lambda view: scores.get(faces.photo_name(view)) if scores.get(faces.photo_name(view)) is not None else -1


def report(kind, gallery, rows, lines, sure, dog):
    """Per entry what it holds and what would go, the totals, and recognition before and after."""
    reasons = Counter(r["reason"] for r in rows)
    print(f"\n=== {kind}: {len(rows)} views with a photo in {len(gallery.people)} entries; "
          + ", ".join(f"{n} {reason}" for reason, n in sorted(reasons.items())))
    by_entry = defaultdict(Counter)
    for row in rows:
        by_entry[row["entry"]][row["reason"]] += 1
    for line in sorted(lines, key=lambda l: (not l["named"], l["name"] or l["id"])):
        what = ", ".join(f"{n} {reason}" for reason, n in sorted(by_entry[line["id"]].items()) if goes(reason))
        after = "removed" if line["removed"] else f"{len(line['chosen after'])} chosen left"
        extra = (f", spared {line['spared']}" if line["spared"] else "") + (
            f", {line['moved up']} moved up" if line["moved up"] else "")
        print(f"  {line['name'] or line['id']:22} {line['chosen']:2} chosen, {line['waiting']:3} waiting: "
              f"{line['deleted']} deleted ({what}); {after}{extra}")
    untouched = len(gallery.people) - len(lines)
    print(f"  {untouched} entries lose nothing; {sum(l['deleted'] for l in lines)} views deleted, "
          f"{sum(l['removed'] for l in lines)} entries removed")
    chosen_after = {name for line in lines for name in line["chosen after"]}
    touched = {line["id"] for line in lines}
    after = lambda r: r["photo"] in chosen_after or (r["entry"] not in touched and not r["waiting"])
    print("  recognition, leave-one-event-out over the named views:")
    print(f"    today's chosen views: {view_quality.recognition(rows, lambda r: not r['waiting'], sure, dog)}")
    print(f"    what would be left:   {view_quality.recognition(rows, after, sure, dog)}")


def option(argv, name):
    return argv[argv.index(name) + 1] if name in argv else None


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    args = [a for i, a in enumerate(argv) if not a.startswith("--") and (i == 0 or argv[i - 1] != "--verdicts")]
    if not args:
        print(__doc__)
        return 2
    folder = Path(args[0])
    apply = "--apply" in argv
    face_file = folder / "faces" / faces.GALLERY_FILE.name
    dog_file = folder / "dogs" / dogs.GALLERY_FILE.name
    if not face_file.is_file() and not dog_file.is_file():
        print(f"No gallery in {folder}.")
        return 1
    port = int(dotenv_values(folder / ".env").get("WEB_PORT") or web.PORT)
    if apply and web.already_running(port):
        print(f"J.A.R.V.I.S. is running on port {port}: stop it first, or run without --apply.")
        return 1
    verdicts = view_quality.load_verdicts(option(argv, "--verdicts"))
    try:
        values = json.loads((folder / "config.json").read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        values = {}
    values = values if isinstance(values, dict) else {}
    galleries = [("Faces", faces.Gallery(face_file), False, faces.learn_threshold(values)),
                 ("Dogs", dogs.DogGallery(dog_file), True, dogs.sure_distance(values))]
    plans = []
    for kind, gallery, dog, sure in galleries:
        rows = judge(gallery, verdicts, folder, dog)
        names = [r["photo"] for r in rows if goes(r["reason"]) and r["reason"] != "photo missing"]
        lines = gallery.drop_views(names, best_by(rows), dry_run=True)
        report(kind, gallery, rows, lines, sure, dog)
        plans.append((kind, gallery, rows, names))
    if not apply:
        print("\nDry run: nothing written.")
        return 0
    backup = folder / "backups" / f"clean_views_{datetime.now():%Y%m%d-%H%M%S}"
    for part in ("faces", "dogs"):
        if (folder / part).is_dir():
            shutil.copytree(folder / part, backup / part)
    print(f"\nCopied faces/ and dogs/ to {backup}")
    for kind, gallery, rows, names in plans:
        lines = gallery.drop_views(names, best_by(rows))
        print(f"{kind}: {sum(l['deleted'] for l in lines)} views deleted, "
              f"{sum(l['removed'] for l in lines)} entries removed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
