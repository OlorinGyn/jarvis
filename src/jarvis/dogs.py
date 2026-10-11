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
MAX_UNNAMED = 60
SURE_DISTANCE = 0.35
SURE_RATIO = 0.6
PROBABLE_DISTANCE = 0.5
PROBABLE_RATIO = 0.8

logger = logging.getLogger(__name__)


class DogGallery(faces.Gallery):
    """People's gallery for dogs: same views, queue and favourite, in dogs/.

    Naming a dog gathers only the unnamed crops that match it for sure, in
    the same lighting: fur histograms of two dogs can look alike, so the
    probable ones stay for the user to decide.
    """

    id_prefix = "d"
    sighting_key = "dog_id"

    def __init__(self, path=None):
        super().__init__(path or GALLERY_FILE)

    def _absorb(self, person):
        """Gather the unnamed crops that are this dog for sure; repeat until none joins.

        Only the "sure" rule of match, and only within the same lighting (the
        distance of a day view to a night view is undefined): a view that
        joins can make another crop recognisable, as for faces (R29).
        """
        merged = 0
        changed = True
        while changed:
            changed = False
            for other in list(self.people):
                if other is person or other["name"]:
                    continue
                results = [match(view, self) for view in other["embeddings"]]
                if any(r["certainty"] == "sure" and r["dog_id"] == person["id"] for r in results):
                    self._merge(other, person)
                    merged += 1
                    changed = True
        return merged

    def add(self, embeddings, thumbnail, crops=None):
        """Add an unnamed dog, then keep only the newest MAX_UNNAMED unnamed ones."""
        dog_id = super().add(embeddings, thumbnail, crops)
        self.trim()
        return dog_id

    def _drop(self, dogs_to_drop):
        """Take dogs out of the gallery and delete their view photos. Call under the lock."""
        for dog in dogs_to_drop:
            self.people.remove(dog)
        return [view for dog in dogs_to_drop
                for view in faces.views_of(dog) + [w.get("view") for w in dog.get("pending") or []]]

    def trim(self):
        """Forget the oldest unnamed dogs beyond MAX_UNNAMED; named dogs are never touched."""
        with faces._GALLERY_LOCK:
            self.load()
            unnamed = [dog for dog in self.people if not dog["name"]]
            excess = unnamed[:-MAX_UNNAMED] if len(unnamed) > MAX_UNNAMED else []
            if not excess:
                return 0
            views = self._drop(excess)
            self.save()
        for view in views:
            self._forget_view(view)
        return len(excess)

    def dismiss(self, dog_id):
        """Forget one unnamed dog the user does not want to name. False for a named one."""
        with faces._GALLERY_LOCK:
            self.load()
            dog = self.get(dog_id)
            if dog is None or dog["name"]:
                return False
            views = self._drop([dog])
            self.save()
        for view in views:
            self._forget_view(view)
        return True

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


def _bhattacharyya(a, b):
    """Distance between two normalised histograms: 0 identical, 1 nothing in common."""
    a, b = np.asarray(a, np.float64), np.asarray(b, np.float64)
    if a.sum() <= 0 or b.sum() <= 0:
        return 1.0
    coefficient = float(np.sum(np.sqrt(a * b)))
    return float(np.sqrt(max(1.0 - coefficient, 0.0)))


def distance(first, second):
    """How unlike two descriptors are, or None when one is day and the other infrared."""
    if first[0] != second[0]:
        return None
    tone_end = 1 + TONE_BINS
    parts = [_bhattacharyya(first[1:tone_end], second[1:tone_end])]
    if not first[0]:
        hue_end = tone_end + HUE_BINS
        parts.append(_bhattacharyya(first[tone_end:hue_end], second[tone_end:hue_end]))
        parts.append(_bhattacharyya(first[hue_end:], second[hue_end:]))
    return sum(parts) / len(parts)


def match(descriptor, gallery):
    """Which named dog this looks like: {"dog_id", "name", "certainty", "distance"}.

    Nearest neighbour over every named dog's views in the same lighting. A
    name is given only when the nearest dog is close and clearly closer than
    the second ("sure"), or close enough and somewhat closer ("probable");
    otherwise certainty is None. Dogs that look alike stay "dog".
    """
    nearest = []
    for dog in gallery.people:
        if not dog["name"]:
            continue
        found = [d for d in (distance(descriptor, view) for view in dog["embeddings"]) if d is not None]
        if found:
            nearest.append((min(found), dog))
    nearest.sort(key=lambda pair: pair[0])
    if not nearest:
        return {"dog_id": None, "name": "", "certainty": None, "distance": None}
    best, dog = nearest[0]
    second = nearest[1][0] if len(nearest) > 1 else float("inf")
    certainty = None
    if best <= SURE_DISTANCE and best <= SURE_RATIO * second:
        certainty = "sure"
    elif best <= PROBABLE_DISTANCE and best <= PROBABLE_RATIO * second:
        certainty = "probable"
    return {"dog_id": dog["id"] if certainty else None, "name": dog["name"] if certainty else "",
            "certainty": certainty, "distance": round(best, 3)}


def wording(result, gallery):
    """The words for one dog, by certainty: its name, "probably <name>", or "unidentified dog".

    A household that has named no dog keeps today's plain "dog".
    """
    if result["certainty"] == "sure":
        return result["name"]
    if result["certainty"] == "probable":
        return f"probably {result['name']}"
    return "unidentified dog" if any(d["name"] for d in gallery.people) else "dog"


def current_words(sighting, gallery):
    """What a past sighting says now: its dog's current name, so a crop named later updates it.

    The stored certainty only matters while the crop is still unnamed: then
    a "probable" match keeps saying "probably <name>".
    """
    dog = gallery.get(sighting.get("dog_id"))
    if dog and dog["name"]:
        return dog["name"]
    if sighting.get("certainty") == "probable" and sighting.get("match"):
        return f"probably {sighting['match']}"
    return "unidentified dog" if any(d["name"] for d in gallery.people) else "dog"


def words_for(frame, boxes, gallery=None):
    """The words for every dog box of a frame, for a message. Never raises."""
    try:
        gallery = gallery or DogGallery()
        words = [wording(match(describe(frame, box)[0], gallery), gallery) for box in boxes]
    except Exception as problem:
        logger.warning("  dog matching failed: %s", problem)
        return ["dog"] * len(boxes)
    return list(dict.fromkeys(words))


def record(frame, boxes, camera, started_at, clip, gallery=None):
    """Record every dog of the event's best dog frame, with a sighting each.

    A sure match teaches that dog one more view; anything less becomes an
    unnamed crop for the Dogs tab, where the user names or merges it.
    Returns the dog ids the sightings point to.
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
        result = match(descriptor, gallery)
        if result["certainty"] == "sure":
            dog_id = result["dog_id"]
            gallery.reinforce(dog_id, descriptor, crop)
        else:
            dog_id = gallery.add([descriptor], thumbnail, [crop])
        sighting = {
            "dog_id": dog_id,
            "camera": camera,
            "at": started_at.isoformat(timespec="seconds"),
            "time": started_at.strftime("%H:%M:%S"),
            "infrared": bool(descriptor[0]),
            "certainty": result["certainty"] or "",
            "match": result["name"],
            "words": wording(result, gallery),
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
