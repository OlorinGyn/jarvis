"""Motion detection by background subtraction (MOG2).

See docs/ARQUITETURA.md for how each step works and why it is there.
"""

import cv2

DETECT_WIDTH = 640
MIN_AREA = 400
MAX_MOTION_FRACTION = 0.5
WARMUP_FRAMES = 60


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

    @property
    def warming_up(self):
        """True while the background model is still being learned."""
        return self.frames_seen < WARMUP_FRAMES

    def detect(self, frame):
        """Return a list of (x, y, w, h) boxes in the original frame's pixels."""
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

        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, self.kernel)
        mask = cv2.dilate(mask, self.kernel, iterations=3)

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        boxes = []
        for contour in contours:
            if cv2.contourArea(contour) < MIN_AREA:
                continue
            x, y, bw, bh = cv2.boundingRect(contour)
            boxes.append((int(x / scale), int(y / scale), int(bw / scale), int(bh / scale)))
        return boxes
