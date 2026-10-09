"""Read every file the program has ever written, with the current code.

Usage: uv run tools/check_data.py

The user's rule: a new version must never break files written by an older
one. This reads every event, face sighting, the face gallery and config.json
the same way the program does, and fails if any of them can no longer be read.
Run it before and after every production update. See docs/ARQUITETURA.md
section 19.
"""

import json
import sys
from pathlib import Path

from jarvis import faces, settings, web
from jarvis.clips import CLIP_DIR

EVENT_KEYS = ("camera", "started_at", "time", "seconds", "labels", "video", "thumbnail")
SIGHTING_KEYS = ("person_id", "camera", "at", "time", "score", "thumbnail")
PERSON_KEYS = ("id", "name", "embeddings")
EMBEDDING_SIZE = 128


def check_events(root, problems):
    """Every event JSON under root, read as list_clips and the web read them."""
    count = 0
    for sidecar in sorted(Path(root).glob("*/*/*.json")):
        if sidecar.parent.parent.name.startswith("_"):
            continue
        count += 1
        try:
            entry = json.loads(sidecar.read_text(encoding="utf-8-sig"))
        except (OSError, ValueError) as problem:
            problems.append(f"{sidecar}: unreadable ({problem})")
            continue
        missing = [k for k in EVENT_KEYS if k not in entry]
        if missing:
            problems.append(f"{sidecar}: missing {missing}")
        entry["thumbnail_path"] = sidecar.with_suffix(".jpg")
        entry["video_path"] = sidecar.with_suffix(".mp4")
        try:
            web._event(entry)
        except Exception as problem:
            problems.append(f"{sidecar}: the web cannot show it ({problem})")
        if not sidecar.with_suffix(".mp4").exists():
            problems.append(f"{sidecar}: video missing")
    return count


def check_faces(problems):
    """The gallery and every sighting, read as the People screen reads them."""
    gallery = faces.Gallery()
    if faces.GALLERY_FILE.exists() and not gallery.people:
        problems.append(f"{faces.GALLERY_FILE}: exists but no person could be read")
    for person in gallery.people:
        missing = [k for k in PERSON_KEYS if k not in person]
        if missing:
            problems.append(f"gallery person {person.get('id', '?')}: missing {missing}")
            continue
        wrong = [len(e) for e in person["embeddings"] if len(e) != EMBEDDING_SIZE]
        if wrong:
            problems.append(f"gallery person {person['id']}: embeddings of size {wrong}")

    sightings = 0
    for day in sorted(faces.days_with_faces()):
        folder = faces.FACE_DIR / day.isoformat()
        for path in folder.glob("*.json"):
            sightings += 1
            try:
                entry = json.loads(path.read_text(encoding="utf-8-sig"))
            except (OSError, ValueError) as problem:
                problems.append(f"{path}: unreadable ({problem})")
                continue
            missing = [k for k in SIGHTING_KEYS if k not in entry]
            if missing:
                problems.append(f"{path}: missing {missing}")
        try:
            faces.list_sightings(day)
        except Exception as problem:
            problems.append(f"faces of {day}: the People screen cannot list them ({problem})")
    return len(gallery.people), sightings


def check_settings(problems):
    """config.json, if present, read as the program reads it."""
    if not settings.FILE.exists():
        return "absent (defaults apply)"
    try:
        stored = json.loads(settings.FILE.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as problem:
        problems.append(f"{settings.FILE}: unreadable ({problem})")
        return "unreadable"
    unknown = sorted(set(stored) - set(settings.DEFAULTS))
    if unknown:
        problems.append(f"{settings.FILE}: keys this version does not know, "
                        f"and would drop on save: {unknown}")
    settings.load()
    return f"{len(stored)} key(s)"


def main():
    problems = []
    events = check_events(CLIP_DIR, problems)
    print(f"events in clips/: {events}")

    archive = settings.load().get("archive_path")
    if archive and Path(archive).is_dir():
        print(f"events in the archive ({archive}): {check_events(archive, problems)}")
    elif archive:
        print(f"archive {archive}: not reachable, not checked")

    people, sightings = check_faces(problems)
    print(f"gallery: {people} person(s); face sightings: {sightings}")
    print(f"config.json: {check_settings(problems)}")

    if problems:
        print(f"\n{len(problems)} problem(s):")
        for problem in problems:
            print(f"  {problem}")
        sys.exit(1)
    print("\nEvery file is readable by this version.")


if __name__ == "__main__":
    main()
