"""Subject detection with YOLO11, triggered by motion.

Detects people and animals by body shape, never by face, so a covered face
still counts as human. Animal identity (which dog) is a separate problem and
is not attempted here.

See docs/ARQUITETURA.md for the design and its trade-offs.
"""

import time
from functools import lru_cache

from ultralytics import YOLO

from geometry import Detection, iou, overlap_area

MODEL = "yolo11s.pt"
PERSON_CLASS = 0
ANIMAL_CLASSES = (14, 15, 16, 17, 18, 19)
WANTED_CLASSES = (PERSON_CLASS,) + ANIMAL_CLASSES
CONFIDENCE = 0.35
ANIMAL_CONFIDENCE = 0.45
MIN_PERSON_HEIGHT_FRACTION = 0.20
IMG_SIZE = 640
MIN_INTERVAL = 0.25
SAME_SUBJECT_IOU = 0.5
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


def drop_duplicates(subjects):
    """Keep the most confident box when two of them describe the same subject."""
    subjects = sorted(subjects, key=lambda d: d.confidence, reverse=True)
    kept = []
    for subject in subjects:
        for other in kept:
            if subject.label == other.label and iou(subject, other) > SAME_SUBJECT_IOU:
                break
        else:
            kept.append(subject)
    return kept


class _StaticSpot:
    """A place where a subject-shaped thing keeps being detected without moving."""

    __slots__ = ("box", "hits", "last_seen", "last_cycle")

    def __init__(self, box, now, cycle):
        self.box = box
        self.hits = 1
        self.last_seen = now
        self.last_cycle = cycle

    @property
    def is_scenery(self):
        return self.hits >= STATIC_HITS


class SubjectDetector:
    """Decides whether the motion on ONE camera is a person or an animal."""

    def __init__(self):
        self.model = load_model()
        self.last_run = 0.0
        self.subjects = []
        self.static = []
        self.cycle = 0

    def _note_position(self, subject, now):
        """Record where this detection is, and return its static-spot record."""
        for spot in self.static:
            if _same_place(spot.box, subject):
                spot.hits += 1
                spot.last_seen = now
                spot.last_cycle = self.cycle
                spot.box = tuple(subject[:4])
                return spot
        spot = _StaticSpot(tuple(subject[:4]), now, self.cycle)
        self.static.append(spot)
        return spot

    def _reject_scenery(self, subjects, now):
        """Drop detections pinned to a spot that has not moved for STATIC_HITS cycles."""
        self.cycle += 1
        self.static = [s for s in self.static if now - s.last_seen < STATIC_TTL]
        kept = [s for s in subjects if not self._note_position(s, now).is_scenery]
        for spot in self.static:
            if spot.last_cycle != self.cycle:
                spot.hits = 0
        return kept

    def detect(self, frame, motion_boxes):
        """Return a list of Detection in full-frame pixels."""
        if not motion_boxes:
            self.subjects = []
            return self.subjects

        now = time.monotonic()
        if now - self.last_run < MIN_INTERVAL:
            return self.subjects
        self.last_run = now

        result = self.model.predict(frame, classes=list(WANTED_CLASSES),
                                    conf=CONFIDENCE, imgsz=IMG_SIZE,
                                    verbose=False)[0]

        minimum_person = MIN_PERSON_HEIGHT_FRACTION * frame.shape[0]
        found = []
        for (x1, y1, x2, y2), confidence, class_id in zip(
                result.boxes.xyxy.tolist(),
                result.boxes.conf.tolist(),
                result.boxes.cls.tolist()):
            class_id = int(class_id)
            if class_id != PERSON_CLASS and confidence < ANIMAL_CONFIDENCE:
                continue
            box = (int(x1), int(y1), int(x2 - x1), int(y2 - y1))
            if class_id == PERSON_CLASS and box[3] < minimum_person:
                continue
            if REQUIRE_MOTION_OVERLAP and not any(
                    overlap_area(box, m) for m in motion_boxes):
                continue
            found.append(Detection(*box, float(confidence),
                                   self.model.names[class_id]))

        self.subjects = self._reject_scenery(drop_duplicates(found), now)
        return self.subjects


PersonDetector = SubjectDetector
