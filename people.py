"""Subject detection with YOLO11, triggered by motion.

Detects people and animals by body shape, never by face, so a covered face
still counts as human. Animal identity is a separate problem, not attempted.

Runs the ONNX export through OpenCV's dnn module rather than PyTorch. See
docs/ARQUITETURA.md section 7.11 for why.
"""

import time
import urllib.request
from functools import lru_cache
from pathlib import Path

import cv2
import numpy as np

from geometry import Detection, iou, overlap_area

MODEL_DIR = Path("models")
MODEL_FILE = MODEL_DIR / "yolo11s.onnx"
MODEL_URL = ("https://github.com/ultralytics/assets/releases/download/"
             f"v8.4.0/{MODEL_FILE.name}")

PERSON_CLASS = 0
CLASS_NAMES = {0: "person", 14: "bird", 15: "cat", 16: "dog",
               17: "horse", 18: "sheep", 19: "cow"}
WANTED_CLASSES = tuple(CLASS_NAMES)

CONFIDENCE = 0.35
ANIMAL_CONFIDENCE = 0.45
MIN_PERSON_HEIGHT_FRACTION = 0.20
IMG_SIZE = 640
NMS_THRESHOLD = 0.45
MIN_INTERVAL = 0.25
SAME_SUBJECT_IOU = 0.5
REQUIRE_MOTION_OVERLAP = True
STATIC_CENTRE_TOLERANCE = 12
STATIC_SIZE_TOLERANCE = 0.30
STATIC_HITS = 50
STATIC_TTL = 600.0


def ensure_model():
    """Download the ONNX export on first use."""
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    if MODEL_FILE.exists() and MODEL_FILE.stat().st_size > 1024:
        return
    print(f"Downloading {MODEL_FILE.name}...")
    urllib.request.urlretrieve(MODEL_URL, MODEL_FILE)


@lru_cache(maxsize=1)
def load_model():
    """Load YOLO once; the network is stateless, so all cameras share it."""
    ensure_model()
    net = cv2.dnn.readNetFromONNX(str(MODEL_FILE))
    net.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)
    net.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)
    return net


def _letterbox(frame):
    """Fit the frame into a square without distorting it. Returns the scale."""
    height, width = frame.shape[:2]
    scale = IMG_SIZE / max(height, width)
    new_h, new_w = int(round(height * scale)), int(round(width * scale))
    canvas = np.zeros((IMG_SIZE, IMG_SIZE, 3), dtype=np.uint8)
    canvas[:new_h, :new_w] = cv2.resize(frame, (new_w, new_h))
    return canvas, scale


def _raw_detections(net, frame):
    """Run the network and return (box, confidence, class id) triples."""
    canvas, scale = _letterbox(frame)
    blob = cv2.dnn.blobFromImage(canvas, 1 / 255.0, (IMG_SIZE, IMG_SIZE),
                                 swapRB=True, crop=False)
    net.setInput(blob)
    predictions = net.forward()[0].T

    boxes, scores, classes = [], [], []
    for row in predictions:
        class_scores = row[4:]
        class_id = int(np.argmax(class_scores))
        if class_id not in CLASS_NAMES:
            continue
        confidence = float(class_scores[class_id])
        if confidence < CONFIDENCE:
            continue
        cx, cy, width, height = row[:4]
        boxes.append([int((cx - width / 2) / scale), int((cy - height / 2) / scale),
                      int(width / scale), int(height / scale)])
        scores.append(confidence)
        classes.append(class_id)

    if not boxes:
        return []

    keep = cv2.dnn.NMSBoxes(boxes, scores, CONFIDENCE, NMS_THRESHOLD)
    return [(boxes[i], scores[i], classes[i]) for i in np.array(keep).ravel()]


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

        minimum_person = MIN_PERSON_HEIGHT_FRACTION * frame.shape[0]
        found = []
        for box, confidence, class_id in _raw_detections(self.model, frame):
            if class_id != PERSON_CLASS and confidence < ANIMAL_CONFIDENCE:
                continue
            if class_id == PERSON_CLASS and box[3] < minimum_person:
                continue
            if REQUIRE_MOTION_OVERLAP and not any(
                    overlap_area(box, m) for m in motion_boxes):
                continue
            found.append(Detection(*box, confidence, CLASS_NAMES[class_id]))

        self.subjects = self._reject_scenery(drop_duplicates(found), now)
        return self.subjects
