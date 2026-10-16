"""Measure, for every person box YOLO keeps in a clip, the signals that could tell a dog from a person.

Usage: uv run python tools/person_signals.py <video>... [--gallery FILE] [--verbose]

R59 and R58's measurement, kept so it can run again on new reports. Each
clip is replayed as replay.py does, but YOLO runs on every frame that has
motion, through three SubjectDetectors that each take every third frame: the
three phases a live camera's 0.3 s rhythm can fall on. Each kept person box
gets its origin (YOLO, R44 or R46), the dog score YOLO gave that spot, its
height over width, its DINOv2 distance to the nearest named dog of the
gallery (read, never written), and YOLO's second opinion with the box
zoomed to fill the network's input. Each run with two or more people gets
the largest intersection over the smaller box between them. See
docs/BACKLOG.md section 2.
"""

import argparse
import sys
from collections import Counter, defaultdict
from itertools import islice
from pathlib import Path

import cv2
import numpy as np

from jarvis import dogs, people
from jarvis.capture import ANALYSIS_FPS
from jarvis.geometry import iou
from jarvis.motion import WARMUP_FRAMES, MotionDetector

sys.path.insert(0, str(Path(__file__).parent))
import replay

PHASES = 3
ZOOM_CONTEXT = 0.5
NEAR_IOU = 0.5
RELABELS = ("the person's box from a moment ago", "took the place of a person who vanished")


class Recording:
    """A network wrapper that keeps the last raw output, so the dog score of a person's spot can be read."""

    def __init__(self, net):
        self.net = net
        self.output = None

    def setInput(self, blob):
        self.net.setInput(blob)

    def forward(self):
        self.output = self.net.forward()
        return self.output


def candidates(output, frame_shape, offset=(0, 0)):
    """Every candidate box of a raw output as (box, person score, dog score), in frame pixels."""
    scale = people.IMG_SIZE / max(frame_shape[:2])
    found = []
    for row in output[0].T:
        cx, cy, w, h = row[:4]
        box = [int((cx - w / 2) / scale) + offset[0], int((cy - h / 2) / scale) + offset[1],
               int(w / scale), int(h / scale)]
        found.append((box, float(row[4 + people.PERSON_CLASS]), float(row[4 + people.DOG_CLASS])))
    return found


def spot_dog_score(output, frame_shape, box):
    """The highest dog score among the candidates that sit where the box is."""
    return max((dog for other, _, dog in candidates(output, frame_shape) if iou(other, box) >= NEAR_IOU),
               default=0.0)


def zoomed_opinion(net, frame, box):
    """(person, dog): YOLO's best scores over the box, run again on a square around it scaled to the input."""
    x, y, w, h = box
    side = max(w, h) * (1 + ZOOM_CONTEXT)
    height, width = frame.shape[:2]
    x0, y0 = int(max(x + w / 2 - side / 2, 0)), int(max(y + h / 2 - side / 2, 0))
    x1, y1 = int(min(x + w / 2 + side / 2, width)), int(min(y + h / 2 + side / 2, height))
    crop = np.ascontiguousarray(frame[y0:y1, x0:x1])
    canvas, _ = people._letterbox(crop)
    net.setInput(cv2.dnn.blobFromImage(canvas, 1 / 255.0, (people.IMG_SIZE, people.IMG_SIZE),
                                       swapRB=True, crop=False))
    near = [(p, d) for other, p, d in candidates(net.forward(), crop.shape, (x0, y0)) if iou(other, box) >= 0.3]
    return max((p for p, _ in near), default=0.0), max((d for _, d in near), default=0.0)


def inside_smaller(a, b):
    """The area two boxes share over the smaller box's area: 1 when one sits wholly inside the other."""
    width = min(a[0] + a[2], b[0] + b[2]) - max(a[0], b[0])
    height = min(a[1] + a[3], b[1] + b[3]) - max(a[1], b[1])
    smaller = min(a[2] * a[3], b[2] * b[3])
    return max(width, 0) * max(height, 0) / smaller if smaller else 0.0


def measure(video, gallery):
    """Every kept person box of the video with its signals, as dicts."""
    motion = MotionDetector()
    detectors = [people.SubjectDetector() for _ in range(PHASES)]
    network = Recording(detectors[0].model)
    for detector in detectors:
        detector.model = network
        detector.trace = []
    for frame in islice(replay.frames(video), WARMUP_FRAMES):
        motion.detect(frame)
    motion.candidates = []
    zoom = people.load_background_model()
    boxes = []
    for index, frame in enumerate(replay.frames(video)):
        now = index / ANALYSIS_FPS
        moving = motion.detect(frame)
        detector = detectors[index % PHASES]
        if not moving:
            detector.detect(frame, moving, now=now)
            continue
        detector.trace.clear()
        detector.last_run = float("-inf")
        found = detector.detect(frame, moving, now=now)
        relabelled = {tuple(d[:4]): reason for reason, d in detector.trace if reason in RELABELS}
        persons = [d for d in found if d.is_person]
        for subject in persons:
            box = list(subject[:4])
            descriptor, _ = dogs.describe(frame, box, dogs.LIVE)
            match = dogs.match(descriptor, gallery)
            zoom_person, zoom_dog = zoomed_opinion(zoom, frame, box)
            boxes.append({"t": round(now, 1), "phase": index % PHASES, "box": box,
                          "confidence": subject.confidence, "origin": relabelled.get(tuple(box), "YOLO"),
                          "spot_dog": spot_dog_score(network.output, frame.shape, box),
                          "ratio": subject.h / subject.w, "distance": match["distance"],
                          "certainty": match["certainty"], "name": match["name"],
                          "zoom_person": zoom_person, "zoom_dog": zoom_dog, "people": len(persons)})
    return boxes


def summary(video, boxes):
    """The clip's lines: its boxes' origins and the range of each signal, and its runs with two or more people."""
    lines = [f"{video}: {len(boxes)} person boxes"]
    if not boxes:
        return lines
    origins = Counter(b["origin"] for b in boxes)
    certainty = Counter(b["certainty"] or "none" for b in boxes)
    distances = sorted(b["distance"] for b in boxes if b["distance"] is not None)
    lines.append("  origin   " + ", ".join(f"{k} {v}" for k, v in origins.items()))
    if distances:
        lines.append(f"  dogs     distance {distances[0]:.3f}-{distances[-1]:.3f}, "
                     + ", ".join(f"{k} {v}" for k, v in certainty.items()))
    lines.append(f"  shape    height/width {min(b['ratio'] for b in boxes):.2f}-{max(b['ratio'] for b in boxes):.2f}")
    lines.append(f"  yolo     dog score at the spot up to {max(b['spot_dog'] for b in boxes):.2f}")
    lines.append(f"  zoom     person >= 0.35 in {sum(b['zoom_person'] >= 0.35 for b in boxes)}, "
                 f"dog above person in {sum(b['zoom_dog'] > b['zoom_person'] for b in boxes)}")
    runs = defaultdict(list)
    for b in boxes:
        runs[(b["t"], b["phase"])].append(b["box"])
    crowded = {key: found for key, found in runs.items() if len(found) >= 2}
    for (t, phase), found in sorted(crowded.items()):
        overlap = max(inside_smaller(a, b) for i, a in enumerate(found) for b in found[i + 1:])
        held = (round(t + PHASES / ANALYSIS_FPS, 1), phase) in crowded
        lines.append(f"  {len(found)} people at {t:.1f} s (phase {phase}): inside the smaller {overlap:.2f}"
                     + ("; again at the next run" if held else ""))
    return lines


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("videos", nargs="+")
    parser.add_argument("--gallery", default=str(dogs.GALLERY_FILE), help="the dog gallery to match against")
    parser.add_argument("--verbose", action="store_true", help="print every box")
    options = parser.parse_args()
    gallery = dogs.DogGallery(options.gallery)
    for video in options.videos:
        boxes = measure(video, gallery)
        print("\n".join(summary(video, boxes)))
        if options.verbose:
            for b in boxes:
                print(f"  {b['t']:5.1f} s {b['origin']:5.5} {b['confidence']:.2f} {b['box']} "
                      f"h/w {b['ratio']:.2f} spot dog {b['spot_dog']:.2f} distance {b['distance']} "
                      f"{b['certainty'] or ''} {b['name']} zoom person {b['zoom_person']:.2f} dog {b['zoom_dog']:.2f}")


if __name__ == "__main__":
    sys.exit(main())
