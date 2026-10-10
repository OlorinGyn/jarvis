"""The surveillance service: cameras, detection, recording, and the web page.

Capture is handled by ffmpeg (see capture.py), not by OpenCV, so the video kept
on disk is the camera's own stream with no re-encoding.

See docs/ARQUITETURA.md for the pipeline and the reasoning behind it.
No option: service plus browser. --headless: the service alone. --window: the
old OpenCV window, until the web covers People and settings. --stop: ask a
running service to shut down cleanly. Ctrl+C also stops.
"""

import logging
import sys
import threading
import time
import webbrowser
from urllib.parse import quote

import cv2
import numpy as np
from dotenv import dotenv_values

from jarvis import ROOT, faces, log, ui, web
from jarvis.archive import Housekeeper
from jarvis.capture import FFmpegCamera
from jarvis.clips import BUFFER_DIR, EventRecorder, wait_for_jobs
from jarvis.motion import MotionDetector
from jarvis.people import SubjectDetector

DEFAULT_STREAM = "stream1"
PLACEHOLDER_IP = "ip-da-camera"
PANEL_HEIGHT = 480
LABEL_Y = 62
STALE_SECONDS = 5.0
WINDOW = "J.A.R.V.I.S."
PRUNE_SECONDS = 10.0
RATE_SECONDS = 60.0
REDRAW_SECONDS = 0.15
IDLE_SLEEP = 0.005
HEADLESS_FLAGS = ("--headless", "--sem-janela")
WINDOW_FLAGS = ("--window", "--janela")
STOP_FLAG = "--stop"
HOLD_FILE = ROOT / "HOLD"

logger = logging.getLogger(__name__)

GREEN = (0, 255, 0)
RED = (0, 0, 255)
YELLOW = (0, 220, 255)
CYAN = (255, 200, 0)


def build_camera_list(env):
    """Turn CAM_<LABEL>_IP / _USER / _PASSWORD groups into (label, rtsp_url) pairs.

    CAM_STREAM picks the stream for every camera: stream1 (1080p, one client
    only) for production, stream2 (640x360, several clients) for a test copy.
    """
    stream = env.get("CAM_STREAM") or DEFAULT_STREAM
    cameras = []
    for key in env:
        if not (key.startswith("CAM_") and key.endswith("_IP")):
            continue
        label = key[len("CAM_"):-len("_IP")]
        if env[key] == PLACEHOLDER_IP:
            raise SystemExit(f"Preencha {key} no .env com o IP da camera "
                             f"(app Tapo > engrenagem > Informacoes do dispositivo).")
        user = env.get(f"CAM_{label}_USER", "")
        password = env.get(f"CAM_{label}_PASSWORD", "")
        credentials = f"{quote(user, safe='')}:{quote(password, safe='')}"
        url = f"rtsp://{credentials}@{env[key]}:554/{stream}"
        cameras.append((label.capitalize(), url))
    return sorted(cameras)


class Camera:
    """One camera: its ffmpeg stream plus the per-camera state of every layer."""

    def __init__(self, label, url):
        self.label = label
        self.stream = FFmpegCamera(label, url, BUFFER_DIR)
        self.motion = MotionDetector()
        self.subjects = SubjectDetector()
        self.recorder = EventRecorder(self.stream)

    def read(self):
        return self.stream.read()

    def prune(self):
        self.stream.prune(self.recorder.protect_from)

    def close(self):
        self.stream.stop()

    def status(self, motion_boxes, subjects):
        """Build the caption shown on this camera's panel."""
        if self.motion.warming_up:
            return f"{self.label} - learning background"
        if subjects:
            names = ", ".join(sorted({s.label for s in subjects}))
            return f"{self.label} - {names.upper()} ({len(subjects)})"
        if motion_boxes:
            return f"{self.label} - motion ({len(motion_boxes)})"
        return self.label


def _wrap(text, width):
    """Split a long message into lines that fit the panel."""
    words, lines, current = text.split(), [], ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if len(candidate) > width and current:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)
    return lines


def make_panel(frame, label, height, motion_boxes=(), subjects=(), recording=False,
               reason=""):
    """Scale a frame to a fixed height and draw the label, boxes and REC dot."""
    if frame is None:
        width = height * 16 // 9
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        cv2.putText(frame, f"{label} - no signal", (12, 34),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, RED, 2)
        for index, piece in enumerate(_wrap(reason, 52)[:4]):
            cv2.putText(frame, piece, (12, 70 + index * 22),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, YELLOW, 1)
        return frame

    h, w = frame.shape[:2]
    scale = height / h
    frame = cv2.resize(frame, (int(w * scale), height))

    def to_panel(x, y, bw, bh):
        return ((int(x * scale), int(y * scale)),
                (int((x + bw) * scale), int((y + bh) * scale)))

    for x, y, bw, bh in motion_boxes:
        top_left, bottom_right = to_panel(x, y, bw, bh)
        cv2.rectangle(frame, top_left, bottom_right, YELLOW, 1)

    for subject in subjects:
        top_left, bottom_right = to_panel(subject.x, subject.y, subject.w, subject.h)
        colour = GREEN if subject.is_person else CYAN
        cv2.rectangle(frame, top_left, bottom_right, colour, 3)
        cv2.putText(frame, f"{subject.label} {subject.confidence:.2f}",
                    (top_left[0], max(top_left[1] - 8, 14)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, colour, 2)

    cv2.putText(frame, label, (12, LABEL_Y), cv2.FONT_HERSHEY_SIMPLEX, 0.9, GREEN, 2)

    if recording:
        cv2.circle(frame, (frame.shape[1] - 78, 28), 9, RED, -1)
        cv2.putText(frame, "REC", (frame.shape[1] - 62, 35),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, RED, 2)
    return frame


def window_size(live):
    """The window's current pixel size, falling back to the natural layout."""
    try:
        _, _, width, height = cv2.getWindowImageRect(WINDOW)
    except cv2.error:
        width = height = 0
    if width < 240 or height < 160:
        return ui.SIDEBAR_WIDTH + live.shape[1], live.shape[0]
    return width, height


def start_cameras(env):
    """Open every camera named in the .env and report what each one answered."""
    cameras = build_camera_list(env)

    if not cameras:
        raise SystemExit("No CAM_* entries found in .env")

    stream = env.get("CAM_STREAM") or DEFAULT_STREAM
    logger.info("Starting %d camera(s) on %s...", len(cameras), stream)
    streams = [Camera(label, url) for label, url in cameras]
    for cam in streams:
        logger.info("  %s: %s", cam.label, cam.stream.wait_ready())
    return streams


class Core:
    """The surveillance itself: capture, detection, recording, housekeeping.

    It knows nothing about any interface. Panels are only built when somebody
    asked for drawing, so a core nobody is watching pays nothing for pixels.
    """

    def __init__(self, streams, draw=False):
        self.streams = streams
        self.draw = draw
        self.housekeeper = Housekeeper()
        self.last_prune = time.monotonic()
        self.analysed = {cam.label: 0 for cam in streams}
        self.per_minute = {}
        self.rate_started = self.last_prune
        self.scan_seen = False
        self.panels = {cam.label: make_panel(None, cam.label, PANEL_HEIGHT)
                       for cam in streams} if draw else {}

    def step(self):
        """One pass over every camera. True when at least one frame was new."""
        fresh = False
        for cam in self.streams:
            frame = cam.read()
            if frame is None:
                if cam.stream.latest is None and self.draw:
                    self.panels[cam.label] = make_panel(
                        None, cam.label, PANEL_HEIGHT,
                        reason=cam.stream.last_error)
                continue
            fresh = True

            motion_boxes = cam.motion.detect(frame)
            subjects = cam.subjects.detect(frame, motion_boxes)

            self.analysed[cam.label] += 1
            saved = cam.recorder.update(frame, subjects)
            if saved:
                names = ", ".join(saved["labels"]) or "?"
                logger.info("  event %s %s [%s] %ss, %s", cam.label, saved["path"].name,
                            names, saved["seconds"], saved["reason"])

            if self.draw:
                self.panels[cam.label] = make_panel(
                    frame, cam.status(motion_boxes, subjects), PANEL_HEIGHT,
                    motion_boxes, subjects, cam.recorder.recording)

        now = time.monotonic()
        if now - self.last_prune > PRUNE_SECONDS:
            self.last_prune = now
            for cam in self.streams:
                cam.prune()

        self._tally(now)
        done = self.housekeeper.tick()
        if done and (done["moved"]["moved"] or done["freed"]["removed"]):
            logger.info("  archive: %d moved, %d deleted from the external drive",
                        done["moved"]["moved"], done["freed"]["removed"])
        return fresh

    def _tally(self, now):
        """Every minute, how many frames each camera analysed; logged when a face scan ran."""
        self.scan_seen = self.scan_seen or faces.scanning()
        elapsed = now - self.rate_started
        if elapsed < RATE_SECONDS:
            return
        self.per_minute = {label: round(count * 60 / elapsed)
                           for label, count in self.analysed.items()}
        if self.scan_seen:
            logger.info("  analysed per minute during a face scan: %s",
                        ", ".join(f"{k} {v}" for k, v in self.per_minute.items()))
        self.analysed = dict.fromkeys(self.analysed, 0)
        self.rate_started = now
        self.scan_seen = False

    def mosaic(self):
        """The cameras side by side, for whoever is drawing."""
        return np.hstack([self.panels[cam.label] for cam in self.streams])

    @property
    def labels(self):
        return [cam.label for cam in self.streams]

    def frame_ages(self):
        """Seconds since each camera's last frame; None for one that never delivered."""
        return {cam.label: cam.stream.frame_age for cam in self.streams}

    def live_view(self, label):
        """One camera's newest frame with its detections drawn, built on demand.

        Called from the web thread. It only reads: the frame is never drawn on
        in place, because make_panel resizes into a new array first. A frame
        older than STALE_SECONDS is not shown as live: the camera or its ffmpeg
        stopped, and a frozen picture would look like a quiet scene.
        """
        cam = next((c for c in self.streams if c.label == label), None)
        if cam is None:
            return None
        frame = cam.stream.latest
        age = cam.stream.frame_age
        if frame is None or age > STALE_SECONDS:
            reason = cam.stream.last_error
            if frame is not None:
                reason = f"no frame for {age:.0f} s. {reason}".strip()
            return make_panel(None, cam.label, PANEL_HEIGHT, reason=reason)
        return make_panel(frame, cam.label, PANEL_HEIGHT, (), cam.subjects.subjects,
                          cam.recorder.recording)

    def close(self):
        """Close the pending events and the streams. Safe to call once."""
        for cam in self.streams:
            saved = cam.recorder.stop("shutdown")
            if saved:
                logger.info("  event %s %s", cam.label, saved["path"].name)

        logger.info("Assembling pending clips...")
        wait_for_jobs()
        for cam in self.streams:
            cam.close()
        logger.info("Stopped.")


def run_window(core, stop):
    """Drives the core from the OpenCV window; cv2.waitKey sets the pace."""
    interface = ui.Interface()
    cv2.namedWindow(WINDOW, cv2.WINDOW_NORMAL)
    cv2.setMouseCallback(WINDOW, interface.on_mouse)
    cv2.resizeWindow(WINDOW, ui.SIDEBAR_WIDTH + 1280, 560)
    last_render = 0.0

    while not stop.is_set():
        fresh = core.step()

        now = time.monotonic()
        if fresh or now - last_render > REDRAW_SECONDS:
            last_render = now
            live = core.mosaic()
            cv2.imshow(WINDOW, interface.render(live, window_size(live)))

        key = cv2.waitKey(15) & 0xFF
        if interface.capturing:
            interface.on_key(key)
        elif key == ord("q"):
            break

        if cv2.getWindowProperty(WINDOW, cv2.WND_PROP_VISIBLE) < 1:
            break

    cv2.destroyAllWindows()


def run_headless(core, stop):
    """Drives the core with no window and no drawing.

    Stops on Ctrl+C or when stop is set, which `--stop` does through the web.
    """
    logger.info("Surveillance running. Ctrl+C, or `python -m jarvis --stop`, to stop.")
    try:
        while not stop.is_set():
            if not core.step():
                time.sleep(IDLE_SLEEP)
    except KeyboardInterrupt:
        pass


def _has(argv, flags):
    return any(flag in argv for flag in flags)


def _answers_soon(port, seconds=5):
    """Whether a J.A.R.V.I.S. that just took the port starts answering.

    Two launches a moment apart: the first holds the port but its server may
    not answer yet. If nothing answers, the port belongs to another program,
    and the surveillance runs without the web rather than not at all.
    """
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if web.already_running(port):
            return True
        time.sleep(0.5)
    return False


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    log.setup()
    env = dotenv_values(ROOT / ".env")
    port = int(env.get("WEB_PORT") or web.PORT)
    url = web.local_url(port)

    if STOP_FLAG in argv:
        logger.info(web.request_stop(port))
        return

    window = _has(argv, WINDOW_FLAGS)
    open_browser = not window and not _has(argv, HEADLESS_FLAGS)

    if HOLD_FILE.exists():
        logger.info("Held: %s exists (an update or a deliberate stop). Not starting.",
                    HOLD_FILE)
        return

    if web.already_running(port):
        logger.info("J.A.R.V.I.S. is already running: %s", url)
        if open_browser:
            webbrowser.open(url)
        return

    stop = threading.Event()
    server = web.start(port=port, on_stop=stop.set)
    if server is None and _answers_soon(port):
        logger.info("J.A.R.V.I.S. is already running: %s", url)
        if open_browser:
            webbrowser.open(url)
        return

    log.to_file()
    core = Core(start_cameras(env), draw=window)
    web.attach(core)
    if open_browser and server is not None:
        webbrowser.open(url)
    try:
        (run_window if window else run_headless)(core, stop)
    finally:
        web.stop(server)
        core.close()


if __name__ == "__main__":
    main()
