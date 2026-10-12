"""Turns detections into saved events, assembled from the camera's own packets.

Nothing is re-encoded. The clip is built by concatenating whole segments from
the rolling buffer with ffmpeg's stream copy, so the saved video is bit for bit
what the camera produced.

Each event produces three files sharing one basename, plus two optional ones:
    19-17-30.mp4        the video, assembled losslessly from segments
    19-17-30.jpg        the first frame where the subject appeared
    19-17-30.json       metadata, so the Records screen never decodes a video
    19-17-30.alert.jpg  only when the notification went out after the start
    19-17-30.best.jpg   only when a person was seen: the frame showing one best

See docs/ARQUITETURA.md sections 5, 8 and 19.
"""

import json
import logging
import os
import subprocess
import threading
import time
import weakref
from datetime import date, datetime, timedelta
from pathlib import Path

import cv2

from jarvis import ROOT, dogs, faces, notify
from jarvis.capture import NO_WINDOW, SEGMENT_FORMAT, SEGMENT_SECONDS, ffmpeg_exe

CLIP_DIR = ROOT / "clips"
BUFFER_DIR = CLIP_DIR / "_buffer"
PRE_SECONDS = 6.0
POST_SECONDS = 5.0
MAX_SECONDS = 60.0
THUMB_WIDTH = 480
ASSEMBLY_DELAY = SEGMENT_SECONDS + 2.0
PERSON_GAP_SECONDS = 2.0

GREEN = (0, 255, 0)
CYAN = (255, 200, 0)

_jobs = []
_recorders = weakref.WeakSet()
logger = logging.getLogger(__name__)


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
            check=True, capture_output=True, creationflags=NO_WINDOW)
    except (subprocess.CalledProcessError, OSError):
        pass
    finally:
        listing.unlink(missing_ok=True)


def _clip_moments(segments, spans):
    """Turn wall-clock person spans into seconds into the clip the segments make.

    The clip starts where its first segment does, and a segment is named
    after the moment ffmpeg opened it.
    """
    try:
        clip_start = datetime.strptime(Path(segments[0]).stem, SEGMENT_FORMAT)
    except (IndexError, ValueError):
        return []
    return [((first - clip_start).total_seconds(), (last - clip_start).total_seconds())
            for first, last in spans]


def _assemble(camera, start, end, destination, labels, notified=False, best_view=None,
              person_spans=(), dog_view=None, held=False):
    """Wait for the final segment to close, build the clip, then read faces.

    When no face was found, the phone gets the side view or the best view of
    the person instead, so it always ends with a picture of them, even when
    the clip could not be built. When the person was held for the scan, that
    message is the person's only one.
    """
    time.sleep(ASSEMBLY_DELAY)
    segments = camera.covering(start - timedelta(seconds=PRE_SECONDS),
                               end + timedelta(seconds=POST_SECONDS))
    if not segments:
        if "person" in labels:
            notify.after_scan(camera.label, start, [], held, notified, None, best_view)
        return
    _concat(segments, destination)
    found = []
    if "person" in labels and destination.exists():
        try:
            found = faces.scan_clip(destination, camera.label, start,
                                    moments=_clip_moments(segments, person_spans),
                                    busy=recording_now)
        except Exception as problem:
            logger.exception("  face scan failed on %s: %s", destination.name, problem)
    if "person" in labels:
        notify.after_scan(camera.label, start, found, held, notified,
                          faces.side_view_path(destination), best_view)
    if dog_view:
        try:
            dogs.record(dog_view["frame"], dog_view["boxes"], camera.label, start, destination)
        except Exception as problem:
            logger.exception("  dog crops failed on %s: %s", destination.name, problem)


def recording_now():
    """Whether any camera is recording an event at this moment."""
    return any(recorder.recording for recorder in list(_recorders))


def _message_parts(frame, subjects, labels):
    """(words, case) for each subject of a message: each dog named by certainty, a person's case None.

    The notification modes switch each case on or off; a person's is known
    only after the face scan.
    """
    parts = []
    for label in sorted(labels):
        if label == "person":
            parts.append(("person", None))
        elif label == "dog":
            boxes = [(s.x, s.y, s.w, s.h) for s in subjects if s.label == "dog"]
            found = dogs.identify(frame, boxes) if boxes else [("dog", False)]
            parts += [(words, "resident_dog" if resident else "other_dog") for words, resident in found]
        else:
            parts.append((label, "other_animal"))
    return parts


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
            entry = json.loads(path.read_text(encoding="utf-8-sig"))
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
        _recorders.add(self)
        self.label = camera.label
        self.directory = Path(directory)
        self.recording = False
        self.started_at = None
        self.started = 0.0
        self.last_subject = 0.0
        self.base = None
        self.labels = set()
        self.best_confidence = 0.0
        self.notified = False
        self.person_held = False
        self.notify_tried = set()
        self.moment = 0
        self.sent_moment = None
        self.best_view = None
        self.dog_view = None
        self.person_spans = []

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
            else:
                self.moment += 1
                self._notify_late(frame, subjects)
            self._consider_view(frame, subjects)
            self._consider_dogs(frame, subjects)
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
        self.person_held = False
        self.labels = set()
        self.best_confidence = 0.0
        self.moment = 0
        self.sent_moment = None
        self.best_view = None
        self.dog_view = None
        self.person_spans = []
        thumbnail = self.base.with_suffix(".jpg")
        self._save_thumbnail(frame, subjects, thumbnail)

        seen = {s.label for s in subjects}
        self.notify_tried = set(seen)
        self.notified, self.person_held = notify.event(
            self.label, _message_parts(frame, subjects, seen), str(thumbnail))
        if self.notified:
            self.sent_moment = self.moment

    def _notify_late(self, frame, subjects):
        """Notify when a wanted subject shows up after the event began.

        An event that starts with a dog is not announced, because only
        people notify. Without this, a person arriving a few seconds later
        would pass in silence. One attempt per new label keeps config.json
        from being read every frame. The photo is of this moment, saved as
        HH-MM-SS.alert.jpg so the archive moves it with the rest of the event.
        A person arriving after a sent message is still held for the scan
        when the mode asks for it.
        """
        new = {s.label for s in subjects} - self.notify_tried
        if not new:
            return
        self.notify_tried |= new
        if self.notified:
            self.person_held |= "person" in new and notify.holds_person()
            return
        photo = self.base.with_name(f"{self.base.name}.alert.jpg")
        self._save_thumbnail(frame, subjects, photo)
        self.notified, held = notify.event(self.label, _message_parts(frame, subjects, new), str(photo))
        self.person_held |= held
        if self.notified:
            self.sent_moment = self.moment
        else:
            photo.unlink(missing_ok=True)

    def _consider_view(self, frame, subjects):
        """Keep the frame where a person shows best, to be the event's picture.

        The first frame is whatever triggered the event, often a pet. Taller
        boxes win, so a person standing beats a dog lying down even when the
        detector mistakes it for one.
        """
        persons = [s for s in subjects if s.is_person]
        if not persons:
            return
        self._note_person(datetime.now())
        score = max(s.confidence * s.h for s in persons)
        if self.best_view is None or score > self.best_view["score"]:
            self.best_view = {"score": score, "frame": frame.copy(),
                              "subjects": list(subjects), "moment": self.moment}

    def _consider_dogs(self, frame, subjects):
        """Keep the frame where the dogs show best: their crops are what the Dogs tab names."""
        found = [s for s in subjects if s.label == "dog"]
        if not found:
            return
        score = sum(s.confidence * s.w * s.h for s in found)
        if self.dog_view is None or score > self.dog_view["score"]:
            self.dog_view = {"score": score, "frame": frame.copy(),
                             "boxes": [(s.x, s.y, s.w, s.h) for s in found]}

    def _note_person(self, now):
        """Extend the current span of person sightings, or open a new one after a gap."""
        if self.person_spans and (now - self.person_spans[-1][1]).total_seconds() <= PERSON_GAP_SECONDS:
            self.person_spans[-1][1] = now
        else:
            self.person_spans.append([now, now])

    def _write_best_view(self):
        """Save the best view as HH-MM-SS.best.jpg. Returns its path, or None."""
        if self.best_view is None:
            return None
        path = self.base.with_name(f"{self.base.name}.best.jpg")
        self._save_thumbnail(self.best_view["frame"], self.best_view["subjects"], path)
        return path if path.exists() else None

    def _save_thumbnail(self, frame, subjects, path):
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
        cv2.imwrite(str(path), shot,
                    [cv2.IMWRITE_JPEG_QUALITY, 88])

    def _write_metadata(self, ended_at, reason, best=None):
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
        if best is not None:
            meta["best_thumbnail"] = best.name
        self.base.with_suffix(".json").write_text(
            json.dumps(meta, indent=2), encoding="utf-8")
        return meta

    def stop(self, reason="stopped"):
        """Close the event and queue its clip for assembly."""
        if not self.recording:
            return None
        ended_at = datetime.now()
        best = self._write_best_view()
        meta = self._write_metadata(ended_at, reason, best)
        destination = self.base.with_suffix(".mp4")
        already_sent = best is not None and self.best_view["moment"] == self.sent_moment
        followup = best if self.person_held or not already_sent else None

        job = threading.Thread(target=_assemble,
                               args=(self.camera, self.started_at, ended_at,
                                     destination, set(self.labels), self.notified,
                                     followup, [tuple(s) for s in self.person_spans],
                                     self.dog_view, self.person_held))
        job.start()
        _jobs.append(job)

        self.recording = False
        self.best_view = None
        self.dog_view = None
        summary = dict(meta)
        summary["path"] = destination
        return summary
