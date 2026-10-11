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

from jarvis import ROOT, faces

REPORT_DIR = ROOT / "reports"
GALLERY_KINDS = {"p": "face", "d": "dog"}
REQUIRED_KEYS = ("kind", "verdict", "source", "reported_at", "label", "camera", "at")

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
    """Take back a report that could not be completed."""
    report = json.loads(path.read_text(encoding="utf-8"))
    if report.get("crop"):
        path.with_name(report["crop"]).unlink(missing_ok=True)
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
    details = {
        "source": "gallery",
        "label": kind,
        "camera": first.get("camera", ""),
        "at": first.get("at", entry.get("first_seen", "")),
        "time": first.get("time", ""),
        "clip": first.get("clip", ""),
        "score": first.get("score"),
        "box": first.get("box"),
        "entry": {"id": entry["id"], "first_seen": entry.get("first_seen", ""),
                  "embeddings": entry["embeddings"]},
        "sightings": [sighting for _, sighting in sightings],
    }
    path = _write(kind, details, _photo(entry))
    if not gallery.take_out(entry_id):
        _discard(path)
        return None
    for sighting_path, sighting in sightings:
        thumbnail = sighting.get("thumbnail")
        if isinstance(thumbnail, str) and thumbnail:
            sighting_path.with_name(Path(thumbnail).name).unlink(missing_ok=True)
        sighting_path.unlink(missing_ok=True)
    return path


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
