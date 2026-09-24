"""Human detection with YOLO11, triggered by motion.

Detects bodies, never faces, so a covered face still counts as human.
See docs/ARQUITETURA.md for the design and its trade-offs.
"""

import time
from functools import lru_cache

from ultralytics import YOLO

MODEL = "yolo11s.pt"
PERSON_CLASS = 0
CONFIDENCE = 0.35
IMG_SIZE = 640
MIN_INTERVAL = 0.25
SAME_PERSON_IOU = 0.5
REQUIRE_MOTION_OVERLAP = True


@lru_cache(maxsize=1)
def load_model():
    """Load YOLO once; the model is stateless, so all cameras share it."""
    return YOLO(MODEL)


def _overlap_area(a, b):
    """Area shared by two (x, y, w, h) boxes; 0 if they do not touch."""
    ax, ay, aw, ah = a[:4]
    bx, by, bw, bh = b[:4]
    dx = min(ax + aw, bx + bw) - max(ax, bx)
    dy = min(ay + ah, by + bh) - max(ay, by)
    return dx * dy if dx > 0 and dy > 0 else 0


def drop_duplicates(people):
    """Keep the most confident box when two of them describe the same person."""
    people = sorted(people, key=lambda p: p[4], reverse=True)
    kept = []
    for person in people:
        for other in kept:
            shared = _overlap_area(person, other)
            if not shared:
                continue
            combined = person[2] * person[3] + other[2] * other[3] - shared
            if shared / combined > SAME_PERSON_IOU:
                break
        else:
            kept.append(person)
    return kept


class PersonDetector:
    """Decides whether the motion on ONE camera is a human."""

    def __init__(self):
        self.model = load_model()
        self.last_run = 0.0
        self.people = []

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
                    _overlap_area(box, m) for m in motion_boxes):
                continue
            people.append(box + (float(confidence),))

        self.people = drop_duplicates(people)
        return self.people
