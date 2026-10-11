"""Bad detections the user reported: kept as evidence, never learned from on their own.

An unnamed face or dog marked "Bad detection" leaves the gallery and the
tabs; a label rejected on a recording leaves its card. Each report is a crop
and a JSON in reports/<kind>/, for the replay and tuning tools and for the
next review to read. See docs/CONTEXTO.md, backlog 23.
"""

import json
import logging
import shutil
import uuid
from datetime import datetime
from pathlib import Path

import cv2

from jarvis import ROOT, faces

REPORT_DIR = ROOT / "reports"
GALLERY_KINDS = {"p": "face", "d": "dog"}
REQUIRED_KEYS = ("kind", "verdict", "source", "reported_at", "label", "camera", "at")
ACTUALLY = ("person", "dog", "other animal", "nothing")

logger = logging.getLogger(__name__)


def _stem(at):
    """A report's file name: when the detection was seen, plus a short random tail."""
    try:
        moment = datetime.fromisoformat(at)
    except (TypeError, ValueError):
        moment = datetime.now()
    return f"{moment:%Y-%m-%d_%H-%M-%S}_{uuid.uuid4().hex[:6]}"


def _write(kind, details, crop):
    """Save one report, the crop copied next to its JSON. Returns the JSON's path."""
    folder = REPORT_DIR / kind
    folder.mkdir(parents=True, exist_ok=True)
    stem = _stem(details.get("at"))
    report = {"kind": kind, "verdict": f"not a {details['label']}",
              "reported_at": datetime.now().isoformat(timespec="seconds"), **details}
    if crop is not None and Path(crop).is_file():
        shutil.copyfile(crop, folder / f"{stem}.jpg")
        report["crop"] = f"{stem}.jpg"
    path = folder / f"{stem}.json"
    path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    logger.info("Reported as %s: %s", report["verdict"], path.name)
    return path


def _discard(path):
    """Delete a report: its JSON, its crop and the copies kept for Undo."""
    report = json.loads(path.read_text(encoding="utf-8-sig"))
    if report.get("crop"):
        path.with_name(report["crop"]).unlink(missing_ok=True)
    shutil.rmtree(path.with_suffix(""), ignore_errors=True)
    path.unlink(missing_ok=True)


def _stored(stored):
    if not stored:
        return None
    path = Path(stored)
    return path if path.is_absolute() else ROOT / path


def _sightings(gallery, entry_id):
    """Every sighting of one gallery entry, oldest first: (path, contents)."""
    found = []
    for path in gallery.path.parent.glob("*/*.json"):
        try:
            sighting = json.loads(path.read_text(encoding="utf-8-sig"))
        except (OSError, ValueError):
            continue
        if sighting.get(gallery.sighting_key) == entry_id:
            found.append((path, sighting))
    found.sort(key=lambda pair: pair[1].get("at", ""))
    return found


def _photo(entry):
    """The picture the user saw on the card: the favourite, the newest view, else the first crop."""
    candidates = [faces.cover_of(entry), *reversed(faces.views_of(entry)), entry.get("thumbnail")]
    return next((path for path in map(_stored, candidates) if path and path.is_file()), None)


def report_entry(gallery, entry_id):
    """Report an unnamed face or dog as a bad detection; it leaves the gallery and its sightings go.

    Returns the report's path, or None when the entry is named or gone.
    """
    gallery.load()
    entry = gallery.get(entry_id)
    if entry is None or entry["name"]:
        return None
    kind = GALLERY_KINDS[gallery.id_prefix]
    sightings = _sightings(gallery, entry_id)
    first = sightings[0][1] if sightings else {}
    folder = gallery.path.parent
    details = {
        "source": "gallery",
        "label": kind,
        "camera": first.get("camera", ""),
        "at": first.get("at", entry.get("first_seen", "")),
        "time": first.get("time", ""),
        "clip": first.get("clip", ""),
        "score": first.get("score"),
        "box": first.get("box"),
        "entry": entry,
        "sightings": [sighting for _, sighting in sightings],
        "sighting_files": [p.relative_to(folder).as_posix() for p, _ in sightings],
    }
    path = _write(kind, details, _photo(entry))
    _keep_copies(path.with_suffix(""), entry, sightings)
    if not gallery.take_out(entry_id):
        _discard(path)
        return None
    for sighting_path, sighting in sightings:
        thumbnail = sighting.get("thumbnail")
        if isinstance(thumbnail, str) and thumbnail:
            sighting_path.with_name(Path(thumbnail).name).unlink(missing_ok=True)
        sighting_path.unlink(missing_ok=True)
    return path


def _keep_copies(folder, entry, sightings):
    """Copy the entry's view photos and its sightings' crops beside the report, for Undo."""
    folder.mkdir(parents=True, exist_ok=True)
    pending = [waiting.get("view") for waiting in entry.get("pending") or []]
    files = [_stored(view) for view in faces.views_of(entry) + pending]
    files += [path.with_name(Path(s["thumbnail"]).name) for path, s in sightings
              if isinstance(s.get("thumbnail"), str) and s["thumbnail"]]
    for source in files:
        if source and source.is_file():
            shutil.copyfile(source, folder / source.name)


def _restored_entry(report, crop, gallery):
    """The gallery entry as it was reported; an older report kept only its embeddings and one crop."""
    entry = dict(report["entry"])
    if "views" in entry:
        return entry
    view = gallery._store_view(cv2.imread(str(crop))) if crop and crop.is_file() else None
    single = len(entry["embeddings"]) == 1
    return {"id": entry["id"], "name": "", "embeddings": entry["embeddings"],
            "views": [view] if single else [], "thumbnail": None if single else view,
            "first_seen": entry.get("first_seen", "")}


def _undo_entry(path, report, gallery):
    """Put a reported face or dog back in its gallery, with its photos and sightings."""
    copies = path.with_suffix("")
    crop = path.with_name(report["crop"]) if report.get("crop") else None
    gallery.load()
    if gallery.get(report["entry"]["id"]) is not None:
        return False
    entry = _restored_entry(report, crop, gallery)
    pending = [waiting.get("view") for waiting in entry.get("pending") or []]
    for view in faces.views_of(entry) + pending:
        target = _stored(view)
        if target and (copies / target.name).is_file() and not target.is_file():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(copies / target.name, target)
    folder = gallery.path.parent
    files = report.get("sighting_files") or [
        f"{s.get('at', '')[:10]}/{Path(s.get('thumbnail') or 'x').stem}.json"
        for s in report.get("sightings", [])]
    for relative, sighting in zip(files, report.get("sightings", [])):
        target = folder / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        thumbnail = sighting.get("thumbnail")
        if isinstance(thumbnail, str) and thumbnail:
            source = copies / Path(thumbnail).name
            source = source if source.is_file() else crop
            image = target.with_name(Path(thumbnail).name)
            if source and source.is_file() and not image.is_file():
                shutil.copyfile(source, image)
        target.write_text(json.dumps(sighting, indent=2), encoding="utf-8")
    return gallery.put_back(entry)


def _undo_label(report):
    """Show a reported label on its recording again."""
    clip = _stored(report.get("clip"))
    sidecar = clip.with_suffix(".json") if clip else None
    if sidecar is None or not sidecar.is_file():
        return False
    entry = json.loads(sidecar.read_text(encoding="utf-8-sig"))
    already = reported_labels(entry)
    if report["label"] not in already:
        return False
    entry["reported_labels"] = [label for label in already if label != report["label"]]
    sidecar.write_text(json.dumps(entry, indent=2), encoding="utf-8")
    return True


def undo(path, galleries):
    """Take back a report made by mistake: the entry returns to its gallery, or the label to its card.

    galleries maps a report kind ("face", "dog") to its Gallery. The report is
    deleted once undone. Returns False when there is nothing to put back.
    """
    path = Path(path)
    report = json.loads(path.read_text(encoding="utf-8-sig"))
    if report.get("source") == "gallery":
        gallery = galleries.get(report.get("kind"))
        done = gallery is not None and _undo_entry(path, report, gallery)
    else:
        done = _undo_label(report)
    if done:
        _discard(path)
        logger.info("Report undone: %s", path.name)
    return done


def choices(report):
    """What the user can say a report actually was: anything but what the detector said."""
    return [choice for choice in ACTUALLY if choice != report.get("label")]


def set_actually(path, actually):
    """Record what a report actually showed, or clear it with "". False for a choice that does not fit."""
    path = Path(path)
    report = json.loads(path.read_text(encoding="utf-8-sig"))
    if actually and actually not in choices(report):
        return False
    if actually:
        report["actually"] = actually
    else:
        report.pop("actually", None)
    path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return True


def find(kind, stem, folder=None):
    """The JSON of one report by its kind and file name, or None."""
    path = Path(folder or REPORT_DIR) / kind / f"{stem}.json"
    return path if path.is_file() else None


def reported_labels(entry):
    """The labels of an event the user said were wrong."""
    reported = entry.get("reported_labels")
    return [label for label in reported if isinstance(label, str)] if isinstance(reported, list) else []


def report_event(sidecar, label):
    """Report one label of a recorded event as wrong; the event's card stops showing it.

    The event JSON gains an optional "reported_labels" list; "labels" keeps
    what the detector said. Returns the report's path, or None when the label
    is not the event's or was already reported.
    """
    sidecar = Path(sidecar)
    entry = json.loads(sidecar.read_text(encoding="utf-8-sig"))
    already = reported_labels(entry)
    if label not in entry.get("labels", []) or label in already:
        return None
    best = entry.get("best_thumbnail")
    crop = sidecar.with_name(best) if isinstance(best, str) and best else None
    if crop is None or not crop.is_file():
        crop = sidecar.with_suffix(".jpg")
    details = {
        "source": "event",
        "label": label,
        "camera": entry.get("camera", sidecar.parent.parent.name),
        "at": entry.get("started_at", ""),
        "time": entry.get("time", ""),
        "clip": faces._portable(sidecar.with_suffix(".mp4")),
        "score": entry.get("best_confidence"),
        "box": None,
        "event": entry,
    }
    path = _write(label, details, crop)
    entry["reported_labels"] = already + [label]
    sidecar.write_text(json.dumps(entry, indent=2), encoding="utf-8")
    return path


def listing(folder=None):
    """Every report, newest detection first, as stored."""
    found = []
    for path in Path(folder or REPORT_DIR).glob("*/*.json"):
        try:
            found.append({**json.loads(path.read_text(encoding="utf-8-sig")), "path": str(path)})
        except (OSError, ValueError):
            continue
    found.sort(key=lambda report: report.get("at", ""), reverse=True)
    return found
