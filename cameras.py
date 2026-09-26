"""Live viewer: shows every configured camera side by side.

See docs/ARQUITETURA.md for the pipeline and the reasoning behind it.
Press q or close the window to quit.
"""

import os
import time
from pathlib import Path
from urllib.parse import quote

os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp"

import cv2
import numpy as np

import ui
from clips import ClipRecorder, DEFAULT_FPS, wait_for_compression
from motion import MotionDetector
from people import SubjectDetector

STREAM = "stream1"
PANEL_HEIGHT = 480
WINDOW = "J.A.R.V.I.S."

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


def open_camera(url):
    """Open an RTSP stream with short timeouts and no frame queue."""
    cap = cv2.VideoCapture(url, cv2.CAP_FFMPEG, [
        cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 5000,
        cv2.CAP_PROP_READ_TIMEOUT_MSEC, 5000,
    ])
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    return cap


class Camera:
    """One camera: its stream plus the per-camera state of every layer."""

    def __init__(self, label, url):
        self.label = label
        self.cap = open_camera(url)
        self.motion = MotionDetector()
        self.subjects = SubjectDetector()
        self.recorder = ClipRecorder(label)
        self.fps = DEFAULT_FPS
        self._reads = 0
        self._first_read = None

    def read(self):
        """Return the next frame and refine the frame-rate estimate."""
        ok, frame = self.cap.read()
        if not ok:
            return None

        now = time.monotonic()
        self._reads += 1
        if self._first_read is None:
            self._first_read = now
        else:
            elapsed = now - self._first_read
            if elapsed > 2 and self._reads > 30:
                self.fps = min(max(self._reads / elapsed, 1.0), 60.0)
        return frame

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

    print(f"Connecting to {len(cameras)} camera(s)...")
    streams = [Camera(label, url) for label, url in cameras]

    for cam in streams:
        state = "ok" if cam.cap.isOpened() else "FAILED"
        print(f"  {cam.label}: {state}")

    interface = ui.Interface()
    cv2.namedWindow(WINDOW, cv2.WINDOW_NORMAL)
    cv2.setMouseCallback(WINDOW, interface.on_mouse)
    cv2.resizeWindow(WINDOW, ui.SIDEBAR_WIDTH + 1280, 560)

    while True:
        panels = []
        for cam in streams:
            frame = cam.read()
            if frame is None:
                panels.append(make_panel(None, cam.label, PANEL_HEIGHT))
                continue

            motion_boxes = cam.motion.detect(frame)
            subjects = cam.subjects.detect(frame, motion_boxes)

            saved = cam.recorder.update(frame, subjects, cam.fps)
            if saved:
                names = ", ".join(saved["labels"]) or "?"
                print(f"  saved {saved['path'].name} [{names}] "
                      f"({saved['frames']} frames, {saved['seconds']}s, {saved['reason']})")

            panels.append(make_panel(frame, cam.status(motion_boxes, subjects),
                                     PANEL_HEIGHT, motion_boxes, subjects,
                                     cam.recorder.recording))

        live = np.hstack(panels)
        cv2.imshow(WINDOW, interface.render(live, window_size(live)))

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

        if cv2.getWindowProperty(WINDOW, cv2.WND_PROP_VISIBLE) < 1:
            break

    for cam in streams:
        saved = cam.recorder.stop("shutdown")
        if saved:
            print(f"  saved {saved['path'].name} ({saved['frames']} frames)")
        cam.cap.release()

    print("Finishing video compression...")
    wait_for_compression()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
