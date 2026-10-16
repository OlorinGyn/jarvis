"""Replay clips through the live SubjectDetector and a ByteTrack tracker per phase: what each track saw.

Usage: uv run python tools/replay_tracks.py <video>... [--join] [--lost 3 ...] [--verbose]

Item 7's part 1, R59 and R58's measurement through tracks. YOLO runs as in
person_signals.py: on every frame with motion, through three SubjectDetectors
that each take every third frame, the three phases a live camera's rhythm can
fall on. Each phase's kept detections, every label, go to a ByteTrackTracker
of its own, once for each lost-track buffer asked for; YOLO runs once. With
--join the videos are one timeline, each placed at its event's started_at
less PRE_SECONDS, frames already covered by the one before skipped: whether
one track would cover a walk cut into two events. Read-only. See
docs/BACKLOG.md section 3.
"""

import argparse
import json
import sys
import time
from collections import Counter
from datetime import datetime, timedelta
from itertools import islice
from pathlib import Path

import numpy as np
import supervision as sv
from trackers import ByteTrackTracker

from jarvis import people, settings
from jarvis.capture import ANALYSIS_FPS
from jarvis.clips import PRE_SECONDS
from jarvis.motion import WARMUP_FRAMES, MotionDetector

sys.path.insert(0, str(Path(__file__).parent))
import replay
from person_signals import PHASES, inside_smaller

LABELS = ("person", "dog")
FRAME_RATE = ANALYSIS_FPS / PHASES
LIBRARY_FPS = 30
NESTED = 0.8


def tracker(lost_seconds):
    """A ByteTrackTracker with this project's parameters: the live minimums start a track, the buffer in seconds."""
    minimum = min(settings.load()[key] for key in settings.CONFIDENCE_KEYS)
    return ByteTrackTracker(lost_track_buffer=round(lost_seconds * LIBRARY_FPS), frame_rate=FRAME_RATE,
                            track_activation_threshold=minimum, high_conf_det_threshold=minimum,
                            minimum_consecutive_frames=1)


def timeline(videos, join):
    """(video, offset in seconds) per video: all at zero, or with --join each at its event's start."""
    if not join:
        return [(video, 0.0) for video in videos]
    starts = []
    for video in videos:
        event = json.loads(Path(video).with_suffix(".json").read_text(encoding="utf-8"))
        starts.append(datetime.fromisoformat(event["started_at"]) - timedelta(seconds=PRE_SECONDS))
    return [(video, (start - starts[0]).total_seconds()) for video, start in zip(videos, starts)]


def frames(placed):
    """(video, time, frame) over the timeline, a later video's frames before the last one's end skipped."""
    last = float("-inf")
    for video, offset in placed:
        for index, frame in enumerate(replay.frames(video)):
            moment = offset + index / ANALYSIS_FPS
            if moment > last:
                last = moment
                yield video, moment, frame


def detect(placed):
    """Per phase, the (video, time, detections) of every run of YOLO over the timeline."""
    motion = MotionDetector()
    detectors = [people.SubjectDetector() for _ in range(PHASES)]
    for frame in islice(replay.frames(placed[0][0]), WARMUP_FRAMES):
        motion.detect(frame)
    motion.candidates = []
    runs = [[] for _ in range(PHASES)]
    for index, (video, moment, frame) in enumerate(frames(placed)):
        moving = motion.detect(frame)
        detector = detectors[index % PHASES]
        if not moving:
            detector.detect(frame, moving, now=moment)
            continue
        detector.last_run = float("-inf")
        runs[index % PHASES].append((video, moment, list(detector.detect(frame, moving, now=moment))))
    return runs


def as_detections(found):
    """The detector's subjects as supervision Detections, with their labels kept in data."""
    if not found:
        return sv.Detections.empty()
    return sv.Detections(xyxy=np.array([[d.x, d.y, d.x + d.w, d.y + d.h] for d in found], dtype=float),
                         confidence=np.array([d.confidence for d in found], dtype=float),
                         class_id=np.array([LABELS.index(d.label) if d.label in LABELS else len(LABELS)
                                            for d in found]),
                         data={"label": np.array([d.label for d in found])})


def track(runs, lost_seconds):
    """One phase's runs through a fresh tracker: its tracks, the most boxes and tracks at once, the cost."""
    follower = tracker(lost_seconds)
    tracks = {}
    most = Counter()
    untracked = 0
    spent = []
    for video, moment, found in runs:
        start = time.perf_counter()
        result = follower.update(as_detections(found), timestamp=moment)
        spent.append(time.perf_counter() - start)
        most["person boxes"] = max(most["person boxes"], sum(d.label == "person" for d in found))
        boxes = {}
        for xyxy, label, tracker_id in zip(result.xyxy, result.data.get("label", []), result.tracker_id):
            if tracker_id == -1:
                untracked += 1
                continue
            box = [int(xyxy[0]), int(xyxy[1]), int(xyxy[2] - xyxy[0]), int(xyxy[3] - xyxy[1])]
            boxes[int(tracker_id)] = box
            entry = tracks.setdefault(int(tracker_id), {"first": moment, "labels": Counter(), "largest": box,
                                                         "videos": [], "nested": 0.0})
            entry["last"] = moment
            entry["labels"][str(label)] += 1
            if box[2] * box[3] > entry["largest"][2] * entry["largest"][3]:
                entry["largest"] = box
            if video not in entry["videos"]:
                entry["videos"].append(video)
        most["tracks"] = max(most["tracks"], len(boxes))
        for one, box in boxes.items():
            for other, around in boxes.items():
                if one != other and box[2] * box[3] <= around[2] * around[3]:
                    tracks[one]["nested"] = max(tracks[one]["nested"], inside_smaller(box, around))
    return tracks, most, untracked, spent


def report(name, runs, lost_seconds, verbose):
    """The lines of one phase at one lost-track buffer."""
    tracks, most, untracked, spent = track(runs, lost_seconds)
    cost = f"{1000 * float(np.median(spent)):.2f} ms median" if spent else "no update"
    lines = [f"  {name}, lost {lost_seconds:g} s: {len(tracks)} tracks, most at once {most['tracks']} "
             f"(person boxes {most['person boxes']}), {untracked} boxes untracked, update {cost}"]
    for tracker_id, entry in sorted(tracks.items()):
        frames_seen = sum(entry["labels"].values())
        dog_share = entry["labels"]["dog"] / frames_seen
        if not verbose and not (entry["labels"]["person"] or entry["labels"]["dog"]):
            continue
        lines.append(f"    #{tracker_id} {entry['first']:.1f}-{entry['last']:.1f} s, {frames_seen} frames: "
                     + ", ".join(f"{k} {v}" for k, v in entry["labels"].most_common())
                     + f"; dog share {dog_share:.2f}, largest {entry['largest']}"
                     + (f", nested {entry['nested']:.2f}" if entry["nested"] >= NESTED else "")
                     + (f", spans {len(entry['videos'])} clips" if len(entry["videos"]) > 1 else ""))
    return lines


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("videos", nargs="+")
    parser.add_argument("--join", action="store_true", help="the videos are one timeline, by their events' start")
    parser.add_argument("--lost", type=float, nargs="+", default=[3.0], help="lost-track buffers, in seconds")
    parser.add_argument("--verbose", action="store_true", help="also the tracks with no person or dog frame")
    options = parser.parse_args(argv)
    groups = [options.videos] if options.join else [[video] for video in options.videos]
    for group in groups:
        placed = timeline(group, options.join)
        print(" + ".join(f"{video} at {offset:.1f} s" for video, offset in placed))
        runs = detect(placed)
        for lost_seconds in options.lost:
            for phase, phase_runs in enumerate(runs):
                print("\n".join(report(f"phase {phase}", phase_runs, lost_seconds, options.verbose)))


if __name__ == "__main__":
    sys.exit(main())
