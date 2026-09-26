"""Human detection with YOLO11, triggered by motion.

Detects bodies, never faces, so a covered face still counts as human.
See docs/ARQUITETURA.md for the design and its trade-offs.
"""

import time
from functools import lru_cache

from ultralytics import YOLO

from geometry import iou, overlap_area

MODEL = "yolo11s.pt"
PERSON_CLASS = 0
CONFIDENCE = 0.35
IMG_SIZE = 640
MIN_INTERVAL = 0.25
SAME_PERSON_IOU = 0.5
REQUIRE_MOTION_OVERLAP = True
STATIC_CENTRE_TOLERANCE = 12
STATIC_SIZE_TOLERANCE = 0.30
STATIC_HITS = 50
STATIC_TTL = 600.0


@lru_cache(maxsize=1)
def load_model():
    """Load YOLO once; the model is stateless, so all cameras share it."""
    return YOLO(MODEL)


def _centre(box):
    return box[0] + box[2] / 2, box[1] + box[3] / 2


def _same_place(a, b):
    """True when two boxes sit at the same spot and are about the same size."""
    ax, ay = _centre(a)
    bx, by = _centre(b)
    if abs(ax - bx) > STATIC_CENTRE_TOLERANCE or abs(ay - by) > STATIC_CENTRE_TOLERANCE:
        return False
    for one, two in ((a[2], b[2]), (a[3], b[3])):
        if abs(one - two) > STATIC_SIZE_TOLERANCE * max(one, two):
            return False
    return True


def drop_duplicates(people):
    """Keep the most confident box when two of them describe the same person."""
    people = sorted(people, key=lambda p: p[4], reverse=True)
    kept = []
    for person in people:
        for other in kept:
            if iou(person, other) > SAME_PERSON_IOU:
                break
        else:
            kept.append(person)
    return kept


class _StaticSpot:
    """A place where a person-shaped thing keeps being detected without moving."""

    __slots__ = ("box", "hits", "last_seen", "last_cycle")

    def __init__(self, box, now, cycle):
        self.box = box
        self.hits = 1
        self.last_seen = now
        self.last_cycle = cycle

    @property
    def is_scenery(self):
        return self.hits >= STATIC_HITS


class PersonDetector:
    """Decides whether the motion on ONE camera is a human."""

    def __init__(self):
        self.model = load_model()
        self.last_run = 0.0
        self.people = []
        self.static = []
        self.cycle = 0

    def _note_position(self, person, now):
        """Record where this detection is, and return its static-spot record."""
        for spot in self.static:
            if _same_place(spot.box, person):
                spot.hits += 1
                spot.last_seen = now
                spot.last_cycle = self.cycle
                spot.box = person[:4]
                return spot
        spot = _StaticSpot(person[:4], now, self.cycle)
        self.static.append(spot)
        return spot

    def _reject_scenery(self, people, now):
        """Drop detections pinned to a spot that has not moved for STATIC_HITS cycles."""
        self.cycle += 1
        self.static = [s for s in self.static if now - s.last_seen < STATIC_TTL]
        kept = [p for p in people if not self._note_position(p, now).is_scenery]
        for spot in self.static:
            if spot.last_cycle != self.cycle:
                spot.hits = 0
        return kept

    def detect(self, frame, motion_boxes):
        """Return a list of (x, y, w, h, confidence) in full-frame pixels."""
        if not motion_boxes:
            self.people = []
            return self.people

        now = time.monotonic()
        if now - self.last_run < MIN_INTERVAL:
            return self.people
        self.last_run = now

        result = self.model.predict(frame, classes=[PERSON_CLASS],
                                    conf=CONFIDENCE, imgsz=IMG_SIZE,
                                    verbose=False)[0]

        people = []
        for (x1, y1, x2, y2), confidence in zip(result.boxes.xyxy.tolist(),
                                                result.boxes.conf.tolist()):
            box = (int(x1), int(y1), int(x2 - x1), int(y2 - y1))
            if REQUIRE_MOTION_OVERLAP and not any(
                    overlap_area(box, m) for m in motion_boxes):
                continue
            people.append(box + (float(confidence),))

        self.people = self._reject_scenery(drop_duplicates(people), now)
        return self.people
