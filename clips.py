"""Records a short video whenever a person is present, including pre-roll.

See docs/ARQUITETURA.md for the ring-buffer design and its memory cost.
"""

import time
from collections import deque
from datetime import datetime
from pathlib import Path

import cv2

CLIP_DIR = Path("clips")
PRE_FRAMES = 30
POST_SECONDS = 5.0
MAX_SECONDS = 60.0
FOURCC = "mp4v"
DEFAULT_FPS = 12.0


class ClipRecorder:
    """Records clips for ONE camera."""

    def __init__(self, label, directory=CLIP_DIR):
        self.label = label
        self.directory = Path(directory)
        self.buffer = deque(maxlen=PRE_FRAMES)
        self.writer = None
        self.path = None
        self.started = 0.0
        self.last_person = 0.0
        self.frames_written = 0

    @property
    def recording(self):
        """True while a clip file is open."""
        return self.writer is not None

    def update(self, frame, people, fps=DEFAULT_FPS):
        """Feed one frame. Returns a summary dict when a clip has just closed."""
        now = time.monotonic()
        self.buffer.append(frame)

        if people:
            self.last_person = now
            if not self.recording:
                self._start(frame, fps)

        if not self.recording:
            return None

        self.writer.write(frame)
        self.frames_written += 1

        quiet = now - self.last_person > POST_SECONDS
        too_long = now - self.started > MAX_SECONDS
        if quiet or too_long:
            return self.stop("max length" if too_long else "person left")
        return None

    def _start(self, frame, fps):
        """Open a clip file and write the buffered pre-roll into it."""
        stamp = datetime.now()
        folder = self.directory / self.label / stamp.strftime("%Y-%m-%d")
        folder.mkdir(parents=True, exist_ok=True)
        self.path = folder / f"{stamp.strftime('%H-%M-%S')}.mp4"

        height, width = frame.shape[:2]
        self.writer = cv2.VideoWriter(
            str(self.path), cv2.VideoWriter_fourcc(*FOURCC),
            max(round(fps), 1), (width, height))

        self.started = time.monotonic()
        self.frames_written = 0

        for past in list(self.buffer)[:-1]:
            if past.shape == frame.shape:
                self.writer.write(past)
                self.frames_written += 1

    def stop(self, reason="stopped"):
        """Finalise the file. Returns a summary, or None if not recording."""
        if not self.recording:
            return None
        self.writer.release()
        summary = {
            "camera": self.label,
            "path": self.path,
            "frames": self.frames_written,
            "seconds": time.monotonic() - self.started,
            "reason": reason,
        }
        self.writer = None
        self.path = None
        return summary
