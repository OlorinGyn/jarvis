"""Subject detection with YOLO11, triggered by motion.

Detects people and animals by body shape, never by face, so a covered face
still counts as human. Animal identity is a separate problem, not attempted.

Runs the ONNX export through OpenCV's dnn module rather than PyTorch. See
docs/ARCHITECTURE.md section 7.11 for why.
"""

import time
import urllib.request
from functools import lru_cache

import cv2
import numpy as np

from jarvis import ROOT
from jarvis.geometry import Detection, iou, overlap_area

MODEL_DIR = ROOT / "models"
MODEL_FILE = MODEL_DIR / "yolo11s.onnx"
MODEL_URL = ("https://github.com/ultralytics/assets/releases/download/"
             f"v8.4.0/{MODEL_FILE.name}")

PERSON_CLASS = 0
DOG_CLASS = 16
CLASS_NAMES = {0: "person", 14: "bird", 15: "cat", 16: "dog",
               17: "horse", 18: "sheep", 19: "cow"}
WANTED_CLASSES = tuple(CLASS_NAMES)

CONFIDENCE = 0.35
ANIMAL_CONFIDENCE = 0.45
MIN_PERSON_HEIGHT_FRACTION = 0.20
WIDE_PERSON_RATIO = 2.0
BOTTOM_EDGE_FRACTION = 0.03
IMG_SIZE = 640
NMS_THRESHOLD = 0.45
MIN_INTERVAL = 0.25
SAME_SUBJECT_IOU = 0.5
REQUIRE_MOTION_OVERLAP = True
STATIC_CENTRE_TOLERANCE = 12
STATIC_SIZE_TOLERANCE = 0.30
STATIC_HITS = 50
STATIC_TTL = 600.0
SAME_PERSON_IOU = 0.5
RECENT_PERSON_SECONDS = 2.0


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
    return cv2.dnn.readNetFromONNX(str(MODEL_FILE))


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


@lru_cache(maxsize=1)
def load_background_model():
    """A second copy of the network for work outside the main loop.

    A cv2.dnn.Net keeps internal buffers between calls and must never run in
    two threads at once; sharing load_model() with the clip thread crashed the
    live loop mid-inference.
    """
    ensure_model()
    return cv2.dnn.readNetFromONNX(str(MODEL_FILE))


def person_boxes(frame):
    """Every person YOLO sees in a frame, as (x, y, w, h). Background threads only."""
    return [box for box, _, class_id in _raw_detections(load_background_model(), frame)
            if class_id == PERSON_CLASS]


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


def wide_at_bottom(box, frame_height):
    """A "person" lying across the bottom edge: on the Front camera, the dog on the mat.

    Both conditions, not one: a wide box mid-frame could be a person lying
    down, and a standing person whose feet touch the edge is always tall.
    """
    x, y, w, h = box[:4]
    return w > WIDE_PERSON_RATIO * h and y + h >= (1 - BOTTOM_EDGE_FRACTION) * frame_height


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
        self.recent_people = []
        self.trace = None

    def _drop(self, reason, subject):
        """Note why a detection was dropped, when someone asked for a trace."""
        if self.trace is not None:
            self.trace.append((reason, subject))

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
        kept = []
        for subject in subjects:
            if self._note_position(subject, now).is_scenery:
                self._drop("static spot", subject)
            else:
                kept.append(subject)
        for spot in self.static:
            if spot.last_cycle != self.cycle:
                spot.hits = 0
        return kept

    def _was_person_a_moment_ago(self, box, now):
        """True when a person box of the last RECENT_PERSON_SECONDS sits where this box is."""
        return any(now - seen < RECENT_PERSON_SECONDS and iou(box, person) >= SAME_PERSON_IOU
                   for seen, person in self.recent_people)

    def detect(self, frame, motion_boxes, now=None):
        """Return a list of Detection in full-frame pixels.

        now defaults to the monotonic clock; a replay passes the video's time.
        """
        if not motion_boxes:
            self.subjects = []
            return self.subjects

        now = time.monotonic() if now is None else now
        if now - self.last_run < MIN_INTERVAL:
            return self.subjects
        self.last_run = now

        minimum_person = MIN_PERSON_HEIGHT_FRACTION * frame.shape[0]
        raw = _raw_detections(self.model, frame)
        found = []
        for box, confidence, class_id in raw:
            detection = Detection(*box, confidence, CLASS_NAMES[class_id])
            if class_id != PERSON_CLASS and confidence < ANIMAL_CONFIDENCE:
                self._drop("animal below confidence", detection)
                continue
            if class_id == DOG_CLASS and self._was_person_a_moment_ago(box, now):
                self._drop("the person's box from a moment ago", detection)
                class_id = PERSON_CLASS
                detection = detection._replace(label=CLASS_NAMES[class_id])
            if class_id == PERSON_CLASS and box[3] < minimum_person:
                self._drop("person too short", detection)
                continue
            if class_id == PERSON_CLASS and wide_at_bottom(box, frame.shape[0]):
                self._drop("wide at the bottom edge", detection)
                continue
            if REQUIRE_MOTION_OVERLAP and not any(
                    overlap_area(box, m) for m in motion_boxes):
                self._drop("no motion overlap", detection)
                continue
            found.append(detection)

        self.recent_people = [(seen, person) for seen, person in self.recent_people
                              if now - seen < RECENT_PERSON_SECONDS]
        self.recent_people += [(now, box) for box, _, class_id in raw if class_id == PERSON_CLASS]
        unique = drop_duplicates(found)
        for subject in found:
            if subject not in unique:
                self._drop("duplicate", subject)
        self.subjects = self._reject_scenery(unique, now)
        return self.subjects
