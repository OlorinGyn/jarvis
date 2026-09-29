"""Turns detections into saved events, assembled from the camera's own packets.

Nothing is re-encoded. The clip is built by concatenating whole segments from
the rolling buffer with ffmpeg's stream copy, so the saved video is bit for bit
what the camera produced.

Each event produces three files sharing one basename:
    19-17-30.mp4    the video, assembled losslessly from segments
    19-17-30.jpg    the first frame where the subject appeared
    19-17-30.json   metadata, so the Records screen never decodes a video

See docs/ARQUITETURA.md sections 5 and 8.
"""

import json
import os
import subprocess
import threading
import time
from datetime import date, datetime, timedelta
from pathlib import Path

import cv2

import faces
from capture import SEGMENT_SECONDS, ffmpeg_exe

CLIP_DIR = Path("clips")
BUFFER_DIR = CLIP_DIR / "_buffer"
PRE_SECONDS = 6.0
POST_SECONDS = 5.0
MAX_SECONDS = 60.0
THUMB_WIDTH = 480
ASSEMBLY_DELAY = SEGMENT_SECONDS + 2.0

GREEN = (0, 255, 0)
CYAN = (255, 200, 0)

_jobs = []


def wait_for_jobs():
    """Block until every pending clip assembly has finished."""
    for job in list(_jobs):
        job.join()
    _jobs.clear()


def _concat(segments, destination):
    """Join whole segments into one file without re-encoding."""
    listing = destination.with_suffix(".txt")
    listing.write_text(
        "".join(f"file '{p.resolve().as_posix()}'\n" for p in segments),
        encoding="utf-8")
    try:
        subprocess.run(
            [ffmpeg_exe(), "-y", "-hide_banner", "-loglevel", "error",
             "-f", "concat", "-safe", "0", "-i", str(listing),
             "-c", "copy", "-movflags", "+faststart", str(destination)],
            check=True, capture_output=True)
    except (subprocess.CalledProcessError, OSError):
        pass
    finally:
        listing.unlink(missing_ok=True)


def _assemble(camera, start, end, destination, labels):
    """Wait for the final segment to close, build the clip, then read faces."""
    time.sleep(ASSEMBLY_DELAY)
    segments = camera.covering(start - timedelta(seconds=PRE_SECONDS),
                               end + timedelta(seconds=POST_SECONDS))
    if not segments:
        return
    _concat(segments, destination)
    if "person" in labels and destination.exists():
        try:
            faces.scan_clip(destination, camera.label, start)
        except Exception as problem:
            print(f"  face scan failed on {destination.name}: {problem}")


def available_days():
    """Every day that has at least one recording with metadata."""
    days = set()
    for sidecar in CLIP_DIR.glob("*/*/*.json"):
        try:
            days.add(datetime.strptime(sidecar.parent.name, "%Y-%m-%d").date())
        except ValueError:
            continue
    return days


def reveal(path):
    """Open the system file browser with this clip selected."""
    path = Path(path)
    target = next((c for c in (path, path.parent) if c.exists()), path.parent)
    target = target.resolve()
    try:
        if os.name == "nt":
            subprocess.Popen(f'explorer /select,"{target}"')
        else:
            subprocess.Popen(["xdg-open", str(target if target.is_dir()
                                             else target.parent)])
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


class EventRecorder:
    """Decides when an event starts and ends, then has its clip assembled."""

    def __init__(self, camera, directory=CLIP_DIR):
        self.camera = camera
        self.label = camera.label
        self.directory = Path(directory)
        self.recording = False
        self.started_at = None
        self.started = 0.0
        self.last_subject = 0.0
        self.base = None
        self.labels = set()
        self.best_confidence = 0.0

    @property
    def protect_from(self):
        """Segments newer than this must survive pruning."""
        return self.started_at if self.recording else None

    def update(self, frame, subjects):
        """Feed one analysis frame. Returns a summary when an event closes."""
        now = time.monotonic()

        if subjects:
            self.last_subject = now
            if not self.recording:
                self._start(frame, subjects)
            self.labels.update(s.label for s in subjects)
            self.best_confidence = max(
                [self.best_confidence] + [s.confidence for s in subjects])

        if not self.recording:
            return None

        quiet = now - self.last_subject > POST_SECONDS
        too_long = now - self.started > MAX_SECONDS
        if quiet or too_long:
            return self.stop("max length" if too_long else "subject left")
        return None

    def _start(self, frame, subjects):
        stamp = datetime.now()
        folder = self.directory / self.label / stamp.strftime("%Y-%m-%d")
        folder.mkdir(parents=True, exist_ok=True)
        self.base = folder / stamp.strftime("%H-%M-%S")

        self.started_at = stamp
        self.started = time.monotonic()
        self.recording = True
        self.labels = set()
        self.best_confidence = 0.0
        self._save_thumbnail(frame, subjects)

    def _save_thumbnail(self, frame, subjects):
        shot = frame.copy()
        height, width = shot.shape[:2]
        for subject in subjects:
            colour = GREEN if subject.is_person else CYAN
            cv2.rectangle(shot, (subject.x, subject.y),
                          (subject.x + subject.w, subject.y + subject.h), colour, 3)
            cv2.putText(shot, f"{subject.label} {subject.confidence:.2f}",
                        (subject.x, max(subject.y - 8, 20)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, colour, 2)

        scale = THUMB_WIDTH / width
        shot = cv2.resize(shot, (THUMB_WIDTH, int(height * scale)))
        cv2.imwrite(str(self.base.with_suffix(".jpg")), shot,
                    [cv2.IMWRITE_JPEG_QUALITY, 88])

    def _write_metadata(self, ended_at, reason):
        seconds = (ended_at - self.started_at).total_seconds() + PRE_SECONDS
        meta = {
            "camera": self.label,
            "started_at": self.started_at.isoformat(timespec="seconds"),
            "time": self.started_at.strftime("%H:%M:%S"),
            "seconds": round(seconds, 1),
            "labels": sorted(self.labels),
            "best_confidence": round(self.best_confidence, 2),
            "video": self.base.with_suffix(".mp4").name,
            "thumbnail": self.base.with_suffix(".jpg").name,
            "reason": reason,
        }
        self.base.with_suffix(".json").write_text(
            json.dumps(meta, indent=2), encoding="utf-8")
        return meta

    def stop(self, reason="stopped"):
        """Close the event and queue its clip for assembly."""
        if not self.recording:
            return None
        ended_at = datetime.now()
        meta = self._write_metadata(ended_at, reason)
        destination = self.base.with_suffix(".mp4")

        job = threading.Thread(target=_assemble,
                               args=(self.camera, self.started_at, ended_at,
                                     destination, set(self.labels)))
        job.start()
        _jobs.append(job)

        self.recording = False
        summary = dict(meta)
        summary["path"] = destination
        return summary
