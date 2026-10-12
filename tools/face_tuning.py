"""Measure whether the frontal-face limits can be loosened without naming the wrong person.

Usage: uv run tools/face_tuning.py [--root DIR] [--others N]

For every clip in which a named person was seen, each face YuNet finds on a
person (score >= IDENTITY_SCORE, width >= MIN_FACE_WIDTH) is embedded whether
or not it is frontal, and scored against that person's stored views. The
faces are grouped by how far they are from frontal (nose offset, eye spread),
so MAX_NOSE_OFFSET and MIN_EYE_SPREAD in faces.py can be set from data: a
band is safe while the right person still clears MATCH_THRESHOLD. Faces from
the newest person clips where no named person was seen show the other side:
how often a stranger, or the same person unrecognised, would match someone.
--root is a folder laid out like the project (faces/, clips/), such as a copy
of production's. See BACKLOG 2, R30 (b).
"""

import argparse
import json
from collections import defaultdict
from pathlib import Path

import numpy as np

from jarvis import ROOT, faces, people

OFFSET_BANDS = (0.35, 0.5, 0.7, 1.0, float("inf"))
SPREAD_BANDS = (0.38, 0.3, 0.2, 0.0)


def clips_by_person(root, gallery):
    """{clip path: person id} for every sighting of a named person."""
    named = {p["id"] for p in gallery.people if p["name"]}
    found = {}
    for path in (root / "faces").glob("*/*.json"):
        sighting = json.loads(path.read_text(encoding="utf-8-sig"))
        if sighting.get("person_id") in named:
            found[(root / sighting["clip"].replace("\\", "/")).resolve()] = sighting["person_id"]
    return found


def other_clips(root, known, count):
    """The newest person events in which no named person was seen."""
    found = []
    for sidecar in sorted((root / "clips").glob("*/*/*.json"), reverse=True):
        clip = sidecar.with_suffix(".mp4").resolve()
        entry = json.loads(sidecar.read_text(encoding="utf-8-sig"))
        if "person" in entry.get("labels", []) and clip not in known and clip.exists():
            found.append(clip)
    return found[:count]


def measured_faces(clip):
    """(nose offset, eye spread / width, embedding) of every good face on a person in the clip."""
    recogniser = faces._recogniser()
    found = []
    for frame in faces._sampled_frames(clip):
        detected = faces._detect(frame)
        if detected is None:
            continue
        good = [f for f in detected if f[2] >= faces.MIN_FACE_WIDTH and f[-1] >= faces.IDENTITY_SCORE]
        bodies = people.person_boxes(frame) if good else []
        for face in good:
            if not faces._on_a_person(tuple(int(v) for v in face[:4]), bodies):
                continue
            spread = float(np.linalg.norm(face[6:8] - face[4:6])) / float(face[2])
            embedding = recogniser.feature(recogniser.alignCrop(frame, face)).ravel()
            found.append((faces.nose_offset(face), spread, embedding))
    return found


def band(value, edges, rising=True):
    for edge in edges:
        if (value <= edge) if rising else (value >= edge):
            return edge
    return edges[-1]


def report(title, rows):
    print(f"\n{title}")
    print(f"  {'nose offset <=':>15} {'eye spread >=':>14} {'faces':>6} {'match':>6} {'median':>7}")
    for (offset, spread), scores in sorted(rows.items(), key=lambda item: (item[0][0], -item[0][1])):
        scores = np.array(scores)
        print(f"  {offset:>15} {spread:>14} {len(scores):>6} "
              f"{np.mean(scores >= faces.MATCH_THRESHOLD):>6.0%} {np.median(scores):>7.3f}")


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--others", type=int, default=15)
    args = parser.parse_args()
    gallery = faces.Gallery(args.root / "faces" / "gallery.json")
    known = clips_by_person(args.root, gallery)
    right, strangers = defaultdict(list), defaultdict(list)
    for clip, person_id in sorted(known.items()):
        person = gallery.get(person_id)
        for offset, spread, embedding in measured_faces(clip):
            key = (band(offset, OFFSET_BANDS), band(spread, SPREAD_BANDS, rising=False))
            right[key].append(faces._similarity(person, embedding))
        print(f"{clip.name}: done")
    for clip in other_clips(args.root, set(known), args.others):
        for offset, spread, embedding in measured_faces(clip):
            key = (band(offset, OFFSET_BANDS), band(spread, SPREAD_BANDS, rising=False))
            strangers[key].append(max(faces._similarity(p, embedding) for p in gallery.people if p["name"]))
        print(f"{clip.name} (no named person): done")
    report(f"Named people's own clips ({len(known)}): score against the right person", right)
    report("Clips with no named person: best score against any named person", strangers)


if __name__ == "__main__":
    main()
