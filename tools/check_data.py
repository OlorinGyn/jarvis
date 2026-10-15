"""Read every file the program has ever written, with the current code.

Usage: uv run tools/check_data.py

The user's rule: a new version must never break files written by an older
one. This reads every event, face and dog sighting, both galleries, the
bad-detection reports and config.json the same way the program does, and
fails if any of them can no longer be read.
Run it before and after every production update. See docs/ARCHITECTURE.md
section 19.
"""

import json
import sys
from pathlib import Path

from jarvis import devices, dogs, faces, modes, reports, settings, web
from jarvis.clips import CLIP_DIR

EVENT_KEYS = ("camera", "started_at", "time", "seconds", "labels", "video", "thumbnail")
SIGHTING_KEYS = ("person_id", "camera", "at", "time", "score", "thumbnail")
PERSON_KEYS = ("id", "name", "embeddings")
DOG_SIGHTING_KEYS = ("dog_id", "camera", "at", "time", "thumbnail")
LEGACY_EMBEDDING_SIZE = 128


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
        if "reported_labels" in entry and not isinstance(entry["reported_labels"], list):
            problems.append(f"{sidecar}: reported_labels is not a list")
        people = entry.get("people_thumbnail")
        if people is not None and not (isinstance(people, str) and people.endswith(".people.jpg")):
            problems.append(f"{sidecar}: people_thumbnail is not a .people.jpg name")
        if not sidecar.with_suffix(".mp4").exists():
            problems.append(f"{sidecar}: video missing")
    return count


def check_view_events(entry, label, problems):
    """An entry's view_events, if present: photo names to events, read as the accuracy table reads them (R55)."""
    events = entry.get("view_events")
    if events is not None and not (isinstance(events, dict) and all(
            isinstance(k, str) and isinstance(v, str) for k, v in events.items())):
        problems.append(f"{label}: view_events is not photo names to events")
        return
    faces.events_of(entry)


def check_gallery(path, size, problems):
    """One face gallery file, read as the People screen reads it, with embeddings of the given size."""
    gallery = faces.Gallery(path)
    if path.exists() and not gallery.people:
        problems.append(f"{path}: exists but no person could be read")
    for person in gallery.people:
        missing = [k for k in PERSON_KEYS if k not in person]
        if missing:
            problems.append(f"gallery person {person.get('id', '?')}: missing {missing}")
            continue
        wrong = [len(e) for e in person["embeddings"] if len(e) != size]
        if wrong:
            problems.append(f"gallery person {person['id']}: embeddings of size {wrong}")
        views = person.get("views")
        if views is not None and (not isinstance(views, list)
                                  or len(views) > len(person["embeddings"])):
            problems.append(f"gallery person {person['id']}: views do not match its embeddings")
        faces.views_of(person)
        if "cover" in person and not isinstance(person["cover"], str):
            problems.append(f"gallery person {person['id']}: cover is not a path")
        faces.cover_of(person)
        check_view_events(person, f"gallery person {person['id']}", problems)
        if "resident" in person and not isinstance(person["resident"], bool):
            problems.append(f"gallery person {person['id']}: resident is not true or false")
        for waiting in person.get("pending") or []:
            if not isinstance(waiting, dict) or len(waiting.get("embedding") or []) != size:
                problems.append(f"gallery person {person['id']}: a queued view is unreadable")
    return len(gallery.people)


def check_faces(problems):
    """Both face galleries and every sighting: the older model's file stays for a rollback (ARCHITECTURE 10.14)."""
    people = {path.name: check_gallery(path, size, problems)
              for path, size in ((faces.LEGACY_GALLERY_FILE, LEGACY_EMBEDDING_SIZE),
                                 (faces.GALLERY_FILE, faces.EMBEDDING_SIZE))
              if path.exists()}
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
    return people, sightings


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
    values = settings.load()
    if "notify_mode" in stored and stored["notify_mode"] not in modes.MODES:
        problems.append(f"{settings.FILE}: notify_mode {stored['notify_mode']!r} is not one of {modes.MODES}")
    stored_modes = stored.get("notify_modes")
    if stored_modes is not None and not (
            isinstance(stored_modes, dict)
            and all(isinstance(switches, dict) and all(isinstance(on, bool) for on in switches.values())
                    for switches in stored_modes.values())):
        problems.append(f"{settings.FILE}: notify_modes holds values this version does not read")
    if set(values["notify_modes"]) != set(modes.MODES):
        problems.append(f"{settings.FILE}: the notification modes could not be built")
    ignored = [key for key in settings.CONFIDENCE_KEYS
               if key in stored and not settings.confidence_valid(stored[key])]
    if ignored:
        return (f"{len(stored)} key(s); warning: {ignored} outside {settings.CONFIDENCE_RANGE}, "
                f"the defaults apply (readable, so not a failure)")
    if unknown:
        return (f"{len(stored)} key(s); warning: this version does not know {unknown} "
                f"and would drop them on save (readable, so not a failure)")
    return f"{len(stored)} key(s)"


def check_dog_gallery(path, size, problems):
    """One dog gallery file, read as the Dogs tab reads it, with descriptors of the given size."""
    gallery = dogs.DogGallery(path)
    if path.exists() and not gallery.people:
        problems.append(f"{path}: exists but no dog could be read")
    for dog in gallery.people:
        missing = [k for k in PERSON_KEYS if k not in dog]
        if missing:
            problems.append(f"{path.name} dog {dog.get('id', '?')}: missing {missing}")
            continue
        wrong = [len(e) for e in dog["embeddings"] if len(e) != size]
        wrong += [len(w.get("embedding") or []) for w in dog.get("pending") or []
                  if not isinstance(w, dict) or len(w.get("embedding") or []) != size]
        if wrong:
            problems.append(f"{path.name} dog {dog['id']}: descriptors of size {wrong}")
        faces.views_of(dog)
        faces.cover_of(dog)
        check_view_events(dog, f"{path.name} dog {dog['id']}", problems)
        if "resident" in dog and not isinstance(dog["resident"], bool):
            problems.append(f"{path.name} dog {dog['id']}: resident is not true or false")
    return len(gallery.people)


def check_dogs(problems):
    """Both dog galleries and every dog sighting: the histograms' file stays for a rollback (R53)."""
    galleries = {path.name: check_dog_gallery(path, size, problems)
                 for path, size in ((dogs.LEGACY_GALLERY_FILE, dogs.LEGACY_DESCRIPTOR_SIZE),
                                    (dogs.GALLERY_FILE, dogs.DESCRIPTOR_SIZE))
                 if path.exists()}
    sightings = 0
    for day in sorted(dogs.days_with_dogs()):
        for path in (dogs.DOG_DIR / day.isoformat()).glob("*.json"):
            sightings += 1
            try:
                entry = json.loads(path.read_text(encoding="utf-8-sig"))
            except (OSError, ValueError) as problem:
                problems.append(f"{path}: unreadable ({problem})")
                continue
            missing = [k for k in DOG_SIGHTING_KEYS if k not in entry]
            if missing:
                problems.append(f"{path}: missing {missing}")
    return galleries, sightings


def check_reports(problems):
    """Every bad-detection report, read as the review and the tools read them."""
    count = 0
    for path in sorted(reports.REPORT_DIR.glob("*/*.json")):
        count += 1
        try:
            report = json.loads(path.read_text(encoding="utf-8-sig"))
        except (OSError, ValueError) as problem:
            problems.append(f"{path}: unreadable ({problem})")
            continue
        missing = [k for k in reports.REQUIRED_KEYS if k not in report]
        if missing:
            problems.append(f"{path}: missing {missing}")
        if report.get("crop") and not path.with_name(report["crop"]).is_file():
            problems.append(f"{path}: its crop is missing")
        if "actually" in report and report["actually"] not in reports.choices(report):
            problems.append(f"{path}: actually is not one of {reports.choices(report)}")
    if count != len(reports.listing()):
        problems.append("reports: the listing does not read every report")
    return count


def check_devices(problems):
    """devices.json, if present, read as the write guard reads it."""
    if not devices.FILE.exists():
        return "absent (no device paired)"
    try:
        json.loads(devices.FILE.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as problem:
        problems.append(f"{devices.FILE}: unreadable ({problem})")
        return "unreadable"
    return f"{len(devices.listing())} paired device(s)"


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
    galleries = "; ".join(f"{name} {count} person(s)" for name, count in people.items()) or "none"
    print(f"face galleries: {galleries}; face sightings: {sightings}")
    dog_galleries, dog_sightings = check_dogs(problems)
    galleries = "; ".join(f"{name} {count} dog(s)" for name, count in dog_galleries.items()) or "none"
    print(f"dog galleries: {galleries}; dog sightings: {dog_sightings}")
    print(f"bad-detection reports: {check_reports(problems)}")
    print(f"config.json: {check_settings(problems)}")
    print(f"devices.json: {check_devices(problems)}")

    if problems:
        print(f"\n{len(problems)} problem(s):")
        for problem in problems:
            print(f"  {problem}")
        sys.exit(1)
    print("\nEvery file is readable by this version.")


if __name__ == "__main__":
    main()
