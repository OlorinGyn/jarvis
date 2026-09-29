"""One ffmpeg process per camera, feeding two outputs from a single RTSP pull.

The camera allows only one RTSP session at a time, so a single process has to
serve both purposes:

    output 1  the camera's own H.264 packets, copied byte for byte into short
              segment files. No decoding, no re-encoding, no quality loss.
    output 2  small decoded frames on stdout, for motion and YOLO.

Recorded clips are assembled from the segments, so what lands on disk is
exactly what the camera produced. See docs/ARQUITETURA.md section 5.
"""

import subprocess
import time
from datetime import datetime, timedelta
from pathlib import Path

import imageio_ffmpeg
import numpy as np

ANALYSIS_WIDTH = 960
ANALYSIS_HEIGHT = 540
ANALYSIS_FPS = 10
SEGMENT_SECONDS = 4
BUFFER_SECONDS = 240
RESTART_SECONDS = 5.0
HWACCEL = ""
SEGMENT_NAME = "%Y%m%d-%H%M%S.mp4"
SEGMENT_FORMAT = "%Y%m%d-%H%M%S"


def ffmpeg_exe():
    return imageio_ffmpeg.get_ffmpeg_exe()


class FFmpegCamera:
    """Owns the ffmpeg process and the rolling segment buffer of ONE camera."""

    def __init__(self, label, url, buffer_root):
        self.label = label
        self.url = url
        self.buffer = Path(buffer_root) / label
        self.buffer.mkdir(parents=True, exist_ok=True)
        self.frame_bytes = ANALYSIS_WIDTH * ANALYSIS_HEIGHT * 3
        self.process = None
        self.last_start = 0.0
        self.frames_read = 0
        self.fps = float(ANALYSIS_FPS)
        self.start()

    def _command(self):
        acceleration = ["-hwaccel", HWACCEL] if HWACCEL else []
        return [
            ffmpeg_exe(), "-hide_banner", "-loglevel", "error", "-nostdin",
            "-rtsp_transport", "tcp",
            "-use_wallclock_as_timestamps", "1",
            *acceleration,
            "-i", self.url,
            "-map", "0:v", "-an", "-c", "copy",
            "-f", "segment", "-segment_format", "mp4",
            "-segment_time", str(SEGMENT_SECONDS),
            "-reset_timestamps", "1", "-strftime", "1",
            str(self.buffer / SEGMENT_NAME),
            "-map", "0:v", "-an",
            "-s", f"{ANALYSIS_WIDTH}x{ANALYSIS_HEIGHT}",
            "-r", str(ANALYSIS_FPS), "-pix_fmt", "bgr24",
            "-f", "rawvideo", "pipe:1",
        ]

    def start(self):
        self.stop()
        self.process = subprocess.Popen(
            self._command(), stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL, bufsize=self.frame_bytes)
        self.last_start = time.monotonic()

    def stop(self):
        if self.process is None:
            return
        try:
            self.process.terminate()
            self.process.wait(timeout=5)
        except (OSError, subprocess.TimeoutExpired):
            self.process.kill()
        self.process = None

    @property
    def alive(self):
        return self.process is not None and self.process.poll() is None

    def read(self):
        """Return one analysis frame, or None when the stream is unavailable."""
        if not self.alive:
            if time.monotonic() - self.last_start > RESTART_SECONDS:
                self.start()
            return None

        data = self.process.stdout.read(self.frame_bytes)
        if not data or len(data) < self.frame_bytes:
            return None

        self.frames_read += 1
        frame = np.frombuffer(data, np.uint8)
        return frame.reshape(ANALYSIS_HEIGHT, ANALYSIS_WIDTH, 3).copy()

    def segments(self):
        """Every finished segment as (start time, path), oldest first."""
        found = []
        for path in self.buffer.glob("*.mp4"):
            try:
                found.append((datetime.strptime(path.stem, SEGMENT_FORMAT), path))
            except ValueError:
                continue
        found.sort()
        return found

    def covering(self, start, end):
        """Whole segments overlapping the window, which is why pre-roll is free."""
        found = self.segments()
        chosen = []
        for index, (stamp, path) in enumerate(found):
            following = found[index + 1][0] if index + 1 < len(found) else datetime.max
            if following > start and stamp < end:
                chosen.append(path)
        return chosen

    def prune(self, protect_from=None):
        """Delete buffered segments nobody needs any more.

        The newest segment is never touched: ffmpeg is still writing it.
        """
        limit = datetime.now() - timedelta(seconds=BUFFER_SECONDS)
        if protect_from is not None:
            limit = min(limit, protect_from - timedelta(seconds=2 * SEGMENT_SECONDS))
        for stamp, path in self.segments()[:-1]:
            if stamp < limit:
                path.unlink(missing_ok=True)
