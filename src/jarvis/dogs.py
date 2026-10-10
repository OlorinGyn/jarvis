"""Dogs the household teaches the system, the way People teaches faces.

Each dog detection is cut out of its box with GrabCut, and the fur pixels
alone give an appearance descriptor: a tone histogram, plus hue and
saturation when the frame is in colour. Nothing here knows any particular
dog; the user names crops on the Dogs tab and the gallery learns from that.

The gallery is People's (views with photos, queue, favourite), kept in its
own folder, dogs/. See docs/CONTEXTO.md, backlog 22.
"""

import json
import logging
import uuid
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np

from jarvis import ROOT, faces

DOG_DIR = ROOT / "dogs"
GALLERY_FILE = DOG_DIR / "gallery.json"
TONE_BINS = 16
HUE_BINS = 16
SATURATION_BINS = 8
DESCRIPTOR_SIZE = 1 + TONE_BINS + HUE_BINS + SATURATION_BINS
MARGIN = 0.10
GRABCUT_ITERATIONS = 3
MIN_FUR_PIXELS = 50
GREY_DIFFERENCE = 8.0
CROP_SIDE = 320

logger = logging.getLogger(__name__)


class DogGallery(faces.Gallery):
    """People's gallery for dogs: same views, queue and favourite, in dogs/.

    Unlike faces, naming one dog never gathers other unnamed crops on its
    own: fur histograms of two dogs can look alike, so only the user merges.
    """

    id_prefix = "d"
    sighting_key = "dog_id"

    def __init__(self, path=None):
        super().__init__(path or GALLERY_FILE)

    def _absorb(self, person):
        return 0

    def label(self, dog_id):
        dog = self.get(dog_id)
        if dog is None:
            return "?"
        return dog["name"] or "dog"


def is_infrared(region):
    """Whether a colour image carries no colour: the camera's night mode."""
    if region.ndim < 3:
        return True
    b, g, r = (region[..., i].astype(np.int16) for i in range(3))
    return float(np.mean(np.abs(b - g) + np.abs(g - r))) < GREY_DIFFERENCE


def _region(frame, box):
    """The box widened by MARGIN, clipped to the frame: (x0, y0, x1, y1)."""
    x, y, w, h = (int(v) for v in box[:4])
    height, width = frame.shape[:2]
    dx, dy = int(w * MARGIN), int(h * MARGIN)
    return max(x - dx, 0), max(y - dy, 0), min(x + w + dx, width), min(y + h + dy, height)


def fur_mask(frame, box):
    """The pixels of the dog inside its box, cut out of the background with GrabCut."""
    x0, y0, x1, y1 = _region(frame, box)
    region = np.ascontiguousarray(frame[y0:y1, x0:x1])
    x, y, w, h = (int(v) for v in box[:4])
    rect = (x - x0, y - y0, max(min(w, x1 - x), 1), max(min(h, y1 - y), 1))
    mask = np.zeros(region.shape[:2], np.uint8)
    background, foreground = np.zeros((1, 65), np.float64), np.zeros((1, 65), np.float64)
    try:
        cv2.grabCut(region, mask, rect, background, foreground, GRABCUT_ITERATIONS,
                    cv2.GC_INIT_WITH_RECT)
        fur = (mask == cv2.GC_FGD) | (mask == cv2.GC_PR_FGD)
    except cv2.error:
        fur = np.zeros(region.shape[:2], bool)
    if int(fur.sum()) < MIN_FUR_PIXELS:
        fur = np.zeros(region.shape[:2], bool)
        fur[rect[1]:rect[1] + rect[3], rect[0]:rect[0] + rect[2]] = True
    return region, fur


def _histogram(values, bins, top):
    counts, _ = np.histogram(values, bins=bins, range=(0, top))
    total = counts.sum()
    return (counts / total).tolist() if total else [0.0] * bins


def describe(frame, box):
    """(descriptor, crop) for one dog box: the fur's appearance, and a picture of it.

    The descriptor's first value says whether the frame was infrared, so day
    views are only ever compared with day views, and night with night.
    """
    region, fur = fur_mask(frame, box)
    infrared = is_infrared(region)
    grey = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)[fur]
    descriptor = [1.0 if infrared else 0.0] + _histogram(grey, TONE_BINS, 256)
    if infrared:
        descriptor += [0.0] * (HUE_BINS + SATURATION_BINS)
    else:
        hsv = cv2.cvtColor(region, cv2.COLOR_BGR2HSV)[fur]
        descriptor += _histogram(hsv[:, 0], HUE_BINS, 180)
        descriptor += _histogram(hsv[:, 1], SATURATION_BINS, 256)
    scale = CROP_SIDE / max(region.shape[:2])
    crop = cv2.resize(region, (max(int(region.shape[1] * scale), 1),
                               max(int(region.shape[0] * scale), 1)))
    return descriptor, crop


def record(frame, boxes, camera, started_at, clip, gallery=None):
    """Add every dog of the event's best dog frame to the gallery, unnamed, with a sighting.

    Returns the new dog ids. Naming happens on the Dogs tab; until matching
    exists each crop is its own entry, which the user names or merges.
    """
    if frame is None or not boxes:
        return []
    gallery = gallery or DogGallery()
    folder = gallery.path.parent / started_at.strftime("%Y-%m-%d")
    folder.mkdir(parents=True, exist_ok=True)
    stamp = started_at.strftime("%H-%M-%S")
    added = []
    for box in boxes:
        descriptor, crop = describe(frame, box)
        name = f"{stamp}_{uuid.uuid4().hex[:6]}"
        thumbnail = folder / f"{name}.jpg"
        cv2.imwrite(str(thumbnail), crop, [cv2.IMWRITE_JPEG_QUALITY, 90])
        dog_id = gallery.add([descriptor], thumbnail, [crop])
        sighting = {
            "dog_id": dog_id,
            "camera": camera,
            "at": started_at.isoformat(timespec="seconds"),
            "time": started_at.strftime("%H:%M:%S"),
            "infrared": bool(descriptor[0]),
            "clip": faces._portable(clip),
            "thumbnail": thumbnail.name,
        }
        (folder / f"{name}.json").write_text(json.dumps(sighting, indent=2), encoding="utf-8")
        added.append(dog_id)
    logger.info("  dogs %s %s: %d crop(s) added to the gallery", camera, stamp, len(added))
    return added


def appearances(dog_id, folder=None):
    """Every sighting of a dog, newest first."""
    folder = Path(folder or DOG_DIR)
    found = []
    for path in folder.glob("*/*.json"):
        try:
            sighting = json.loads(path.read_text(encoding="utf-8-sig"))
        except (OSError, ValueError):
            continue
        if sighting.get("dog_id") == dog_id:
            at = sighting.get("at", "")
            found.append({"at": at, "day": at[:10], "time": sighting.get("time", ""),
                          "camera": sighting.get("camera", "")})
    found.sort(key=lambda a: a["at"], reverse=True)
    return found


def days_with_dogs(folder=None):
    days = set()
    for path in Path(folder or DOG_DIR).glob("*"):
        try:
            days.add(datetime.strptime(path.name, "%Y-%m-%d").date())
        except ValueError:
            continue
    return days


def sightings_of(day, folder=None):
    """Every dog sighting of a day, as stored."""
    found = []
    for path in (Path(folder or DOG_DIR) / day.isoformat()).glob("*.json"):
        try:
            found.append(json.loads(path.read_text(encoding="utf-8-sig")))
        except (OSError, ValueError):
            continue
    return found
