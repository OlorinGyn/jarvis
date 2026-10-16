"""Tells the phone when a camera stops delivering pictures, and when they come back.

A thread beside the core loop reads frame_ages() every few seconds, so a
stalled loop does not hide a dead camera. A camera with no frame for
CAMERA_DOWN_SECONDS is down; its first frame after that is its return. Both
are logged whatever the mode, and sent as the camera_down case. Nothing is
said in the first minute after the service starts, while the streams open.
A black or covered picture is not this. See docs/ARCHITECTURE.md section 12.
"""

import logging
import time
from datetime import datetime, timedelta

from . import notify

CAMERA_DOWN_SECONDS = 60
CHECK_SECONDS = 5
GRACE_SECONDS = 60

logger = logging.getLogger(__name__)


class CameraWatch:
    """Which cameras are down, from their frame ages, and the message for each change."""

    def __init__(self, ages, clock=time.monotonic, wall=datetime.now):
        self.ages = ages
        self.clock = clock
        self.wall = wall
        self.started = clock()
        self.down = {}

    def check(self):
        """Look at every camera once. Returns the texts of what changed."""
        now = self.clock()
        if now - self.started < GRACE_SECONDS:
            return []
        changes = []
        for label, age in self.ages().items():
            age = now - self.started if age is None else age
            if label not in self.down and age >= CAMERA_DOWN_SECONDS:
                self.down[label] = now - age
                since = (self.wall() - timedelta(seconds=age)).strftime("%H:%M:%S")
                changes.append((label, f"{label}: no picture since {since}"))
            elif label in self.down and age < CAMERA_DOWN_SECONDS:
                minutes = max(1, round((now - age - self.down.pop(label)) / 60))
                changes.append((label, f"{label}: picture back, {minutes} min without"))
        for label, text in changes:
            logger.warning("Camera %s", text)
            notify.camera_down(label, text)
        return [text for _, text in changes]

    def run(self, stop):
        """Check every CHECK_SECONDS until stop is set."""
        while not stop.wait(CHECK_SECONDS):
            try:
                self.check()
            except Exception as problem:
                logger.exception("Camera watch failed: %s", problem)
