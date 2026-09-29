"""Live viewer: shows every configured camera side by side.

Capture is handled by ffmpeg (see capture.py), not by OpenCV, so the video kept
on disk is the camera's own stream with no re-encoding.

See docs/ARQUITETURA.md for the pipeline and the reasoning behind it.
Press q or close the window to quit.
"""

import time
from pathlib import Path
from urllib.parse import quote

import cv2
import numpy as np

import ui
from capture import FFmpegCamera
from clips import BUFFER_DIR, EventRecorder, wait_for_jobs
from motion import MotionDetector
from people import SubjectDetector

STREAM = "stream1"
PANEL_HEIGHT = 480
WINDOW = "J.A.R.V.I.S."
PRUNE_SECONDS = 10.0
REDRAW_SECONDS = 0.15

GREEN = (0, 255, 0)
RED = (0, 0, 255)
YELLOW = (0, 220, 255)
CYAN = (255, 200, 0)


def load_env(path=".env"):
    """Read KEY=value lines from a .env file into a dict."""
    values = {}
    for line in Path(path).read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        key, _, value = line.partition("=")
        values[key.strip()] = value.strip()
    return values


def build_camera_list(env):
    """Turn CAM_<LABEL>_IP / _USER / _PASSWORD groups into (label, rtsp_url) pairs."""
    cameras = []
    for key in env:
        if not (key.startswith("CAM_") and key.endswith("_IP")):
            continue
        label = key[len("CAM_"):-len("_IP")]
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


def make_panel(frame, label, height, motion_boxes=(), subjects=(), recording=False):
    """Scale a frame to a fixed height and draw the label, boxes and REC dot."""
    if frame is None:
        frame = np.zeros((height, height * 16 // 9, 3), dtype=np.uint8)
        cv2.putText(frame, f"{label} - no signal", (12, 34),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, RED, 2)
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

    cv2.putText(frame, label, (12, 34), cv2.FONT_HERSHEY_SIMPLEX, 0.9, GREEN, 2)

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


def main():
    env = load_env()
    cameras = build_camera_list(env)

    if not cameras:
        raise SystemExit("No CAM_* entries found in .env")

    print(f"Starting {len(cameras)} camera(s)...")
    streams = [Camera(label, url) for label, url in cameras]
    for cam in streams:
        print(f"  {cam.label}: {'ok' if cam.stream.alive else 'FAILED'}")

    interface = ui.Interface()
    cv2.namedWindow(WINDOW, cv2.WINDOW_NORMAL)
    cv2.setMouseCallback(WINDOW, interface.on_mouse)
    cv2.resizeWindow(WINDOW, ui.SIDEBAR_WIDTH + 1280, 560)
    last_prune = time.monotonic()
    last_render = 0.0
    panels = {cam.label: make_panel(None, cam.label, PANEL_HEIGHT)
              for cam in streams}

    while True:
        fresh = False
        for cam in streams:
            frame = cam.read()
            if frame is None:
                continue
            fresh = True

            motion_boxes = cam.motion.detect(frame)
            subjects = cam.subjects.detect(frame, motion_boxes)

            saved = cam.recorder.update(frame, subjects)
            if saved:
                names = ", ".join(saved["labels"]) or "?"
                print(f"  event {saved['path'].name} [{names}] "
                      f"{saved['seconds']}s, {saved['reason']}")

            panels[cam.label] = make_panel(
                frame, cam.status(motion_boxes, subjects), PANEL_HEIGHT,
                motion_boxes, subjects, cam.recorder.recording)

        now = time.monotonic()
        if now - last_prune > PRUNE_SECONDS:
            last_prune = now
            for cam in streams:
                cam.prune()

        if fresh or now - last_render > REDRAW_SECONDS:
            last_render = now
            live = np.hstack([panels[cam.label] for cam in streams])
            cv2.imshow(WINDOW, interface.render(live, window_size(live)))

        key = cv2.waitKey(15) & 0xFF
        if interface.capturing:
            interface.on_key(key)
        elif key == ord("q"):
            break

        if cv2.getWindowProperty(WINDOW, cv2.WND_PROP_VISIBLE) < 1:
            break

    for cam in streams:
        saved = cam.recorder.stop("shutdown")
        if saved:
            print(f"  event {saved['path'].name}")

    print("Assembling pending clips...")
    wait_for_jobs()
    for cam in streams:
        cam.close()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
