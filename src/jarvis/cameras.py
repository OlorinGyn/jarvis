"""The surveillance service: cameras, detection, recording, and the web page.

Capture is handled by ffmpeg (see capture.py), not by OpenCV, so the video kept
on disk is the camera's own stream with no re-encoding.

See docs/ARQUITETURA.md for the pipeline and the reasoning behind it.
Sem opcao: servico e navegador. --sem-janela: so o servico. --janela: a janela
antiga do OpenCV, ate a web cobrir People e Ajustes. Ctrl+C encerra.
"""

import sys
import time
import webbrowser
from urllib.parse import quote

import cv2
import numpy as np
from dotenv import dotenv_values

from jarvis import ROOT, ui, web
from jarvis.archive import Housekeeper
from jarvis.capture import FFmpegCamera
from jarvis.clips import BUFFER_DIR, EventRecorder, wait_for_jobs
from jarvis.motion import MotionDetector
from jarvis.people import SubjectDetector

STREAM = "stream1"
PLACEHOLDER_IP = "ip-da-camera"
PANEL_HEIGHT = 480
LABEL_Y = 62
WINDOW = "J.A.R.V.I.S."
PRUNE_SECONDS = 10.0
REDRAW_SECONDS = 0.15
IDLE_SLEEP = 0.005
HEADLESS_FLAG = "--sem-janela"
WINDOW_FLAG = "--janela"

GREEN = (0, 255, 0)
RED = (0, 0, 255)
YELLOW = (0, 220, 255)
CYAN = (255, 200, 0)


def build_camera_list(env):
    """Turn CAM_<LABEL>_IP / _USER / _PASSWORD groups into (label, rtsp_url) pairs."""
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
        url = f"rtsp://{credentials}@{env[key]}:554/{STREAM}"
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
        cv2.putText(frame, f"{label} - sem sinal", (12, 34),
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


def start_cameras():
    """Open every camera named in the .env and report what each one answered."""
    env = dotenv_values(ROOT / ".env")
    cameras = build_camera_list(env)

    if not cameras:
        raise SystemExit("No CAM_* entries found in .env")

    print(f"Iniciando {len(cameras)} camera(s)...")
    streams = [Camera(label, url) for label, url in cameras]
    for cam in streams:
        print(f"  {cam.label}: {cam.stream.wait_ready()}")
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

            saved = cam.recorder.update(frame, subjects)
            if saved:
                names = ", ".join(saved["labels"]) or "?"
                print(f"  event {saved['path'].name} [{names}] "
                      f"{saved['seconds']}s, {saved['reason']}")

            if self.draw:
                self.panels[cam.label] = make_panel(
                    frame, cam.status(motion_boxes, subjects), PANEL_HEIGHT,
                    motion_boxes, subjects, cam.recorder.recording)

        now = time.monotonic()
        if now - self.last_prune > PRUNE_SECONDS:
            self.last_prune = now
            for cam in self.streams:
                cam.prune()

        feito = self.housekeeper.tick()
        if feito and (feito["moved"]["moved"] or feito["freed"]["removed"]):
            print(f"  arquivo: {feito['moved']['moved']} movido(s), "
                  f"{feito['freed']['removed']} apagado(s) do HD")
        return fresh

    def mosaic(self):
        """The cameras side by side, for whoever is drawing."""
        return np.hstack([self.panels[cam.label] for cam in self.streams])

    @property
    def labels(self):
        return [cam.label for cam in self.streams]

    def live_view(self, label):
        """One camera's newest frame with its detections drawn, built on demand.

        Called from the web thread. It only reads: the frame is never drawn on
        in place, because make_panel resizes into a new array first.
        """
        cam = next((c for c in self.streams if c.label == label), None)
        if cam is None:
            return None
        frame = cam.stream.latest
        if frame is None:
            return make_panel(None, cam.label, PANEL_HEIGHT, reason=cam.stream.last_error)
        return make_panel(frame, cam.label, PANEL_HEIGHT, (), cam.subjects.subjects,
                          cam.recorder.recording)

    def close(self):
        """Close the pending events and the streams. Safe to call once."""
        for cam in self.streams:
            saved = cam.recorder.stop("shutdown")
            if saved:
                print(f"  event {saved['path'].name}")

        print("Assembling pending clips...")
        wait_for_jobs()
        for cam in self.streams:
            cam.close()


def run_window(core):
    """Drives the core from the OpenCV window; cv2.waitKey sets the pace."""
    interface = ui.Interface()
    cv2.namedWindow(WINDOW, cv2.WINDOW_NORMAL)
    cv2.setMouseCallback(WINDOW, interface.on_mouse)
    cv2.resizeWindow(WINDOW, ui.SIDEBAR_WIDTH + 1280, 560)
    last_render = 0.0

    while True:
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


def run_headless(core):
    """Drives the core with no window and no drawing. Stops on Ctrl+C."""
    print("Vigilancia rodando. Ctrl+C para encerrar.")
    try:
        while True:
            if not core.step():
                time.sleep(IDLE_SLEEP)
    except KeyboardInterrupt:
        print()


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    window = WINDOW_FLAG in argv
    open_browser = not window and HEADLESS_FLAG not in argv

    if web.already_running():
        print(f"O J.A.R.V.I.S. ja esta rodando: {web.LOCAL_URL}")
        if open_browser:
            webbrowser.open(web.LOCAL_URL)
        return

    core = Core(start_cameras(), draw=window)
    server = web.start(core)
    if open_browser and server is not None:
        webbrowser.open(web.LOCAL_URL)
    try:
        (run_window if window else run_headless)(core)
    finally:
        web.stop(server)
        core.close()


if __name__ == "__main__":
    main()
