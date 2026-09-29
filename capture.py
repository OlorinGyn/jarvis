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
import threading
import time
from collections import deque
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
STARTUP_SECONDS = 25.0
HWACCEL = ""
SEGMENT_NAME = "%Y%m%d-%H%M%S.mp4"
SEGMENT_FORMAT = "%Y%m%d-%H%M%S"


TRANSLATIONS = (
    ("401", "Credenciais incorretas. Confira a Conta da Camera no app Tapo."),
    ("not one of 40", "Camera ocupada. Ela aceita uma conexao RTSP por vez - "
                      "feche outro J.A.R.V.I.S., o app Tapo ou um ffmpeg orfao."),
    ("406", "Camera ocupada. Ela aceita uma conexao RTSP por vez."),
    ("Connection refused", "Conexao recusada. Confira o IP e se a camera esta ligada."),
    ("timed out", "Tempo esgotado. Confira a rede e o IP da camera."),
    ("No route to host", "Camera inalcancavel pela rede. Confira o IP."),
    ("404", "Caminho do stream invalido. Esperado /stream1 ou /stream2."),
)


def _friendly(raw):
    """Turn ffmpeg's wording into something that says what to do."""
    for needle, advice in TRANSLATIONS:
        if needle in raw:
            return advice
    return raw


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
        self._lock = threading.Lock()
        self._pending = None
        self._latest = None
        self._reader = None
        self._errors = deque(maxlen=12)
        self._stop = threading.Event()
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
        self._stop.clear()
        self.process = subprocess.Popen(
            self._command(), stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, bufsize=self.frame_bytes)
        self.last_start = time.monotonic()
        self._reader = threading.Thread(target=self._pump, daemon=True)
        self._reader.start()
        threading.Thread(target=self._drain_errors, args=(self.process,),
                         daemon=True).start()

    def stop(self):
        self._stop.set()
        if self.process is None:
            return
        try:
            self.process.terminate()
            self.process.wait(timeout=5)
        except (OSError, subprocess.TimeoutExpired):
            self.process.kill()
        self.process = None
        self._reader = None

    def _pump(self):
        """Read frames off the pipe forever, so the interface never blocks."""
        process = self.process
        while not self._stop.is_set() and process.poll() is None:
            data = process.stdout.read(self.frame_bytes)
            if not data or len(data) < self.frame_bytes:
                break
            frame = np.frombuffer(data, np.uint8).reshape(
                ANALYSIS_HEIGHT, ANALYSIS_WIDTH, 3).copy()
            with self._lock:
                self._pending = frame
                self._latest = frame
            self.frames_read += 1

    def _drain_errors(self, process):
        """Keep ffmpeg's complaints instead of discarding them.

        Without this a camera that never connects looks identical to one that
        is merely quiet, and the reason is thrown away.
        """
        for line in process.stderr:
            text = line.decode(errors="replace").strip()
            if text:
                with self._lock:
                    self._errors.append(text)

    @property
    def alive(self):
        return self.process is not None and self.process.poll() is None

    @property
    def last_error(self):
        with self._lock:
            raw = self._errors[-1] if self._errors else ""
        return _friendly(raw)

    def wait_ready(self, timeout=STARTUP_SECONDS):
        """Block until the first frame arrives. Returns a status string."""
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            with self._lock:
                if self._latest is not None:
                    return "ok"
            if not self.alive:
                break
            time.sleep(0.1)
        problem = self.last_error
        if problem:
            return f"FALHOU - {problem}"
        return "FALHOU - nenhum frame recebido"

    @property
    def latest(self):
        """The most recent frame, for drawing. None until the first arrives."""
        with self._lock:
            return self._latest

    def read(self):
        """Return the newest frame not yet analysed, or None. Never blocks."""
        if not self.alive and time.monotonic() - self.last_start > RESTART_SECONDS:
            self.start()
        with self._lock:
            frame, self._pending = self._pending, None
        return frame

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
