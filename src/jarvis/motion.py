"""Motion detection by background subtraction (MOG2) with temporal confirmation.

A blob is only reported after it has been seen in roughly the same place for
CONFIRM_FRAMES frames, which rejects insects, rain and sensor flicker.

See docs/ARQUITETURA.md for how each step works and how to tune it.
"""

import cv2

from jarvis.geometry import overlap_area

DETECT_WIDTH = 640
MIN_AREA = 600
MAX_MOTION_FRACTION = 0.5
WARMUP_FRAMES = 60
OPEN_ITERATIONS = 2
CONFIRM_FRAMES = 3
FORGET_FRAMES = 4


class _Candidate:
    """A blob that is not yet trusted, tracked across frames."""

    __slots__ = ("box", "hits", "misses")

    def __init__(self, box):
        self.box = box
        self.hits = 1
        self.misses = 0

    @property
    def confirmed(self):
        return self.hits >= CONFIRM_FRAMES


class MotionDetector:
    """Finds moving regions in the frames of ONE camera."""

    def __init__(self):
        self.subtractor = cv2.createBackgroundSubtractorMOG2(
            history=500,
            varThreshold=16,
            detectShadows=True,
        )
        self.kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        self.frames_seen = 0
        self.candidates = []

    @property
    def warming_up(self):
        """True while the background model is still being learned."""
        return self.frames_seen < WARMUP_FRAMES

    def detect(self, frame):
        """Return confirmed (x, y, w, h) boxes in the original frame's pixels."""
        return self._confirm(self._raw_boxes(frame))

    def _raw_boxes(self, frame):
        """Every blob this frame, before temporal confirmation."""
        h, w = frame.shape[:2]
        scale = DETECT_WIDTH / w
        small = cv2.resize(frame, (DETECT_WIDTH, int(h * scale)))
        small = cv2.GaussianBlur(small, (5, 5), 0)

        mask = self.subtractor.apply(small)
        self.frames_seen += 1
        if self.warming_up:
            return []

        _, mask = cv2.threshold(mask, 200, 255, cv2.THRESH_BINARY)

        if cv2.countNonZero(mask) > MAX_MOTION_FRACTION * mask.size:
            return []

        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, self.kernel,
                                iterations=OPEN_ITERATIONS)
        mask = cv2.dilate(mask, self.kernel, iterations=3)

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        boxes = []
        for contour in contours:
            if cv2.contourArea(contour) < MIN_AREA:
                continue
            x, y, bw, bh = cv2.boundingRect(contour)
            boxes.append((int(x / scale), int(y / scale),
                          int(bw / scale), int(bh / scale)))
        return boxes

    def _confirm(self, boxes):
        """Match this frame's blobs against candidates and age the unmatched."""
        unmatched = list(boxes)

        for candidate in self.candidates:
            best = None
            best_overlap = 0
            for box in unmatched:
                shared = overlap_area(candidate.box, box)
                if shared > best_overlap:
                    best, best_overlap = box, shared

            if best is None:
                candidate.misses += 1
            else:
                candidate.box = best
                candidate.hits += 1
                candidate.misses = 0
                unmatched.remove(best)

        self.candidates = [c for c in self.candidates if c.misses <= FORGET_FRAMES]
        self.candidates.extend(_Candidate(box) for box in unmatched)

        return [c.box for c in self.candidates if c.confirmed and c.misses == 0]
