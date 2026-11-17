"""Tracks: one ByteTrack tracker per camera, every kept detection under the id of the track it belongs to.

The tracker never looks at the image: it matches YOLO's boxes run after run by
where each track's Kalman filter predicts it. The library gives a track its id
only at its second matched box; here each track has an id of its own from its
first box, so a body seen once is a track of one frame and the first frame of
every track has its vote. Recorded in each event's JSON; in Home an event whose
person frames are all a dog's sends no person message (backlog 41).
See docs/ARCHITECTURE.md section 7.16.
"""

import logging
import math
import time
from collections import Counter

import numpy as np
import supervision as sv
from trackers import ByteTrackTracker

from jarvis.capture import ANALYSIS_FPS
from jarvis.people import MIN_INTERVAL

LABELS = ("person", "dog")
RUN_EVERY = math.ceil(MIN_INTERVAL * ANALYSIS_FPS)
FRAME_RATE = ANALYSIS_FPS / RUN_EVERY
LIBRARY_FPS = 30
LOST_SECONDS = 3.0
PERSON_RUN = 2
FAILURE_LOG_SECONDS = 60

logger = logging.getLogger(__name__)


def as_detections(found):
    """The detector's subjects as supervision Detections, each row's index into found kept in data."""
    if not found:
        return sv.Detections.empty()
    return sv.Detections(xyxy=np.array([[d.x, d.y, d.x + d.w, d.y + d.h] for d in found], dtype=float),
                         confidence=np.array([d.confidence for d in found], dtype=float),
                         class_id=np.array([LABELS.index(d.label) if d.label in LABELS else len(LABELS)
                                            for d in found]),
                         data={"index": np.arange(len(found))})


def voted(labels):
    """A track's label by its frames: a dog only when dog frames are more than person frames, a tie a person."""
    if labels["person"] and labels["person"] >= labels["dog"]:
        return "person"
    return "dog" if labels["dog"] else "other"


def dog_only(summary):
    """Whether an event's every person frame sits in tracks voted dog with no run of PERSON_RUN person frames."""
    persons = [track for track in summary or () if track["frames"].get("person")]
    return bool(persons) and all(voted(Counter(track["frames"])) == "dog" and track["longest_person_run"] < PERSON_RUN
                                 for track in persons)


class Tracks:
    """One camera's tracker; ids are unique for the life of the object, so a walk across two events keeps its id."""

    def __init__(self, lost_seconds=LOST_SECONDS):
        self.lost_seconds = lost_seconds
        self.next_id = 1
        self.restart()

    def restart(self):
        """A fresh library tracker, its state forgotten; the id counter goes on, so ids stay unique."""
        self.tracker = ByteTrackTracker(lost_track_buffer=round(self.lost_seconds * LIBRARY_FPS),
                                        frame_rate=FRAME_RATE, track_activation_threshold=0.0,
                                        high_conf_det_threshold=0.0, minimum_consecutive_frames=1)
        self.ids = {}

    def update(self, found, moment):
        """Feed one run of YOLO at moment seconds; (track id, detection) per detection, the id None if untracked."""
        known = set(self.ids)
        result = self.tracker.update(as_detections(found), timestamp=moment)
        named = {tracklet.tracker_id: tracklet for tracklet in self.tracker.tracks if tracklet.tracker_id != -1}
        born = [tracklet for tracklet in self.tracker.tracks if tracklet not in known and tracklet.tracker_id == -1]
        observed = []
        for xyxy, index, library_id in zip(result.xyxy, result.data.get("index", []), result.tracker_id):
            tracklet = named.get(int(library_id)) if library_id != -1 else self._born_from(born, xyxy)
            if tracklet is not None and tracklet not in self.ids:
                self.ids[tracklet] = self.next_id
                self.next_id += 1
            observed.append((self.ids.get(tracklet), found[int(index)]))
        alive = set(self.tracker.tracks)
        self.ids = {tracklet: track_id for tracklet, track_id in self.ids.items() if tracklet in alive}
        return observed

    @staticmethod
    def _born_from(born, xyxy):
        """The tracklet this update spawned from the box xyxy, taken out of born; None when it spawned none."""
        for tracklet in born:
            if np.allclose(tracklet.get_state_bbox(), xyxy):
                born.remove(tracklet)
                return tracklet
        return None


class Failures:
    """One camera's tracking failures in the log: the first with its traceback, then at most a line a minute."""

    def __init__(self, label, clock=time.monotonic):
        self.label, self.clock = label, clock
        self.since = None
        self.count = 0

    def failed(self):
        """Log the exception being handled, or count it when a line went out less than a minute ago."""
        now = self.clock()
        if self.since is None or (now - self.since >= FAILURE_LOG_SECONDS and not self.count):
            logger.exception("Tracking failed on %s; this run goes untracked and the tracker starts afresh",
                             self.label)
            self.since = now
            return
        self.count += 1
        if now - self.since >= FAILURE_LOG_SECONDS:
            logger.warning("Tracking failed %d more time(s) on %s in the last %d s", self.count, self.label,
                           FAILURE_LOG_SECONDS)
            self.since, self.count = now, 0


class Record:
    """What one stretch of time saw of its tracks: per track its seconds, frames per label and longest person run."""

    def __init__(self, start=0.0):
        self.start = start
        self.tracks = {}
        self.present = []
        self.untracked_runs = 0
        self.untracked_people = 0

    def add(self, moment, observed):
        """Count one run of the tracker at moment seconds; observed None is a run the tracker failed on."""
        if observed is None:
            self.untracked_runs += 1
            return
        seen = set()
        for track_id, detection in observed:
            if track_id is None:
                self.untracked_people += detection.label == "person"
                continue
            seen.add(track_id)
            entry = self.tracks.setdefault(track_id, {"first": moment, "labels": Counter(), "run": 0,
                                                      "longest_person_run": 0})
            entry["last"] = moment
            entry["labels"][detection.label] += 1
            entry["run"] = entry["run"] + 1 if detection.label == "person" else 0
            entry["longest_person_run"] = max(entry["longest_person_run"], entry["run"])
        self.present.append(seen)

    def most_person_tracks(self):
        """The most tracks voted person seen in one run."""
        people = {track_id for track_id, entry in self.tracks.items() if voted(entry["labels"]) == "person"}
        return max((len(seen & people) for seen in self.present), default=0)

    def decided(self):
        """The summary the notification may act on: None when a run or a person box went untracked, so the event decides by its boxes."""
        return None if self.untracked_runs or self.untracked_people else self.summary()

    def summary(self):
        """The event JSON's tracks: id, first and last second from the start, frames per label, longest person run."""
        return [{"id": track_id,
                 "first": round(max(entry["first"] - self.start, 0.0), 1),
                 "last": round(max(entry["last"] - self.start, 0.0), 1),
                 "frames": dict(entry["labels"].most_common()),
                 "longest_person_run": entry["longest_person_run"]}
                for track_id, entry in sorted(self.tracks.items())]
