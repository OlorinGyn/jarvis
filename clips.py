"""Records a video whenever a person or animal is present, plus a thumbnail.

Each event produces three files sharing one basename:
    19-17-30.mp4    the video, re-encoded to H.264
    19-17-30.jpg    the first frame where the subject appeared
    19-17-30.json   metadata, so the Records screen never decodes a video

See docs/ARQUITETURA.md for the ring-buffer, compression and metadata design.
"""

import json
import os
import subprocess
import threading
import time
from collections import deque
from datetime import date, datetime
from pathlib import Path

import cv2
import imageio_ffmpeg

CLIP_DIR = Path("clips")
PRE_FRAMES = 30
POST_SECONDS = 5.0
MAX_SECONDS = 60.0
FOURCC = "mp4v"
DEFAULT_FPS = 12.0
THUMB_WIDTH = 480
COMPRESS = True
CRF = 26
PRESET = "veryfast"

GREEN = (0, 255, 0)
CYAN = (255, 200, 0)

_jobs = []


def _ffmpeg():
    return imageio_ffmpeg.get_ffmpeg_exe()


def _compress(raw, final):
    """Re-encode to H.264, then remove the raw file."""
    command = [
        _ffmpeg(), "-y", "-hide_banner", "-loglevel", "error",
        "-i", str(raw),
        "-c:v", "libx264", "-preset", PRESET, "-crf", str(CRF),
        "-pix_fmt", "yuv420p", "-movflags", "+faststart",
        str(final),
    ]
    try:
        subprocess.run(command, check=True, capture_output=True)
        raw.unlink(missing_ok=True)
    except Exception:
        raw.replace(final)


def wait_for_compression():
    """Block until every background encode has finished."""
    for job in list(_jobs):
        job.join()
    _jobs.clear()


def available_days():
    """Every day that has at least one recording with metadata.

    Counts .json sidecars rather than folders, so clips predating the metadata
    format do not mark a day the Records screen would then show as empty.
    """
    days = set()
    for sidecar in CLIP_DIR.glob("*/*/*.json"):
        try:
            days.add(datetime.strptime(sidecar.parent.name, "%Y-%m-%d").date())
        except ValueError:
            continue
    return days


def reveal(path):
    """Open the system file browser with this file selected."""
    path = Path(path)
    target = path if path.exists() else path.parent
    try:
        if os.name == "nt":
            subprocess.Popen(["explorer", f"/select,{target.resolve()}"])
        else:
            subprocess.Popen(["xdg-open", str(target.parent)])
    except OSError:
        pass


def list_clips(day=None):
    """Read the metadata of every clip recorded on a day, newest first."""
    folder = (day or date.today()).strftime("%Y-%m-%d")
    entries = []
    for path in CLIP_DIR.glob(f"*/{folder}/*.json"):
        try:
            entry = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        entry["thumbnail_path"] = path.with_suffix(".jpg")
        entry["video_path"] = path.with_suffix(".mp4")
        entries.append(entry)
    entries.sort(key=lambda e: e.get("started_at", ""), reverse=True)
    return entries


class ClipRecorder:
    """Records clips for ONE camera."""

    def __init__(self, label, directory=CLIP_DIR):
        self.label = label
        self.directory = Path(directory)
        self.buffer = deque(maxlen=PRE_FRAMES)
        self.writer = None
        self.raw_path = None
        self.final_path = None
        self.started = 0.0
        self.started_at = None
        self.last_subject = 0.0
        self.frames_written = 0
        self.fps = DEFAULT_FPS
        self.labels = set()
        self.best_confidence = 0.0

    @property
    def recording(self):
        return self.writer is not None

    def update(self, frame, subjects, fps=DEFAULT_FPS):
        """Feed one frame. Returns a summary dict when a clip has just closed."""
        now = time.monotonic()
        self.buffer.append(frame)

        if subjects:
            self.last_subject = now
            if not self.recording:
                self._start(frame, subjects, fps)
            self.labels.update(s.label for s in subjects)
            self.best_confidence = max(
                [self.best_confidence] + [s.confidence for s in subjects])

        if not self.recording:
            return None

        self.writer.write(frame)
        self.frames_written += 1

        quiet = now - self.last_subject > POST_SECONDS
        too_long = now - self.started > MAX_SECONDS
        if quiet or too_long:
            return self.stop("max length" if too_long else "subject left")
        return None

    def _start(self, frame, subjects, fps):
        """Open the file, save the thumbnail, write the pre-roll."""
        stamp = datetime.now()
        folder = self.directory / self.label / stamp.strftime("%Y-%m-%d")
        folder.mkdir(parents=True, exist_ok=True)
        base = folder / stamp.strftime("%H-%M-%S")

        self.final_path = base.with_suffix(".mp4")
        self.raw_path = base.with_suffix(".raw.mp4")
        self.started_at = stamp
        self.fps = fps
        self.labels = set()
        self.best_confidence = 0.0

        self._save_thumbnail(frame, subjects, base.with_suffix(".jpg"))

        height, width = frame.shape[:2]
        target = self.raw_path if COMPRESS else self.final_path
        self.writer = cv2.VideoWriter(
            str(target), cv2.VideoWriter_fourcc(*FOURCC),
            max(round(fps), 1), (width, height))

        self.started = time.monotonic()
        self.frames_written = 0

        for past in list(self.buffer)[:-1]:
            if past.shape == frame.shape:
                self.writer.write(past)
                self.frames_written += 1

    def _save_thumbnail(self, frame, subjects, path):
        """Save the first frame the subject appeared in, with its boxes marked."""
        shot = frame.copy()
        for subject in subjects:
            colour = GREEN if subject.is_person else CYAN
            cv2.rectangle(shot, (subject.x, subject.y),
                          (subject.x + subject.w, subject.y + subject.h), colour, 4)
            cv2.putText(shot, f"{subject.label} {subject.confidence:.2f}",
                        (subject.x, max(subject.y - 12, 26)),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, colour, 3)

        height, width = shot.shape[:2]
        scale = THUMB_WIDTH / width
        shot = cv2.resize(shot, (THUMB_WIDTH, int(height * scale)))
        cv2.imwrite(str(path), shot, [cv2.IMWRITE_JPEG_QUALITY, 85])

    def _write_metadata(self, seconds, reason):
        meta = {
            "camera": self.label,
            "started_at": self.started_at.isoformat(timespec="seconds"),
            "time": self.started_at.strftime("%H:%M:%S"),
            "seconds": round(seconds, 1),
            "frames": self.frames_written,
            "fps": round(self.fps, 1),
            "labels": sorted(self.labels),
            "best_confidence": round(self.best_confidence, 2),
            "video": self.final_path.name,
            "thumbnail": self.final_path.with_suffix(".jpg").name,
            "reason": reason,
        }
        self.final_path.with_suffix(".json").write_text(
            json.dumps(meta, indent=2), encoding="utf-8")
        return meta

    def stop(self, reason="stopped"):
        """Finalise the file. Returns a summary, or None if not recording."""
        if not self.recording:
            return None
        self.writer.release()
        seconds = time.monotonic() - self.started
        meta = self._write_metadata(seconds, reason)

        if COMPRESS:
            job = threading.Thread(target=_compress,
                                   args=(self.raw_path, self.final_path))
            job.start()
            _jobs.append(job)

        self.writer = None
        summary = dict(meta)
        summary["path"] = self.final_path
        self.raw_path = None
        self.final_path = None
        return summary
