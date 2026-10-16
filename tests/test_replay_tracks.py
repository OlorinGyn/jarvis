"""tools/replay_tracks.py counts a track's frames by label and sees a box nested in another (item 7)."""

import importlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
replay_tracks = importlib.import_module("replay_tracks")

from jarvis.geometry import Detection


def walk(labels, start=100, step=10, confidence=0.6):
    """One body moving right, a run every 0.3 s, labelled in turn."""
    return [("clip", round(i * 0.3, 1), [Detection(start + i * step, 100, 60, 150, confidence, label)])
            for i, label in enumerate(labels)]


def test_one_body_is_one_track_and_its_frames_are_counted_by_label():
    runs = walk(["person", "dog", "dog", "dog", "person", "dog"])
    tracks, most, untracked, _ = replay_tracks.track(runs, 3)
    assert len(tracks) == 1 and untracked == 1
    entry = next(iter(tracks.values()))
    assert entry["labels"] == {"dog": 4, "person": 1}
    assert most == {"tracks": 1, "person boxes": 1}


def test_a_box_inside_another_is_two_tracks_nested():
    runs = [(video, moment, found + [Detection(found[0].x + 10, 120, 30, 60, 0.5, "person")])
            for video, moment, found in walk(["person"] * 4)]
    tracks, most, _, _ = replay_tracks.track(runs, 3)
    assert most == {"tracks": 2, "person boxes": 2}
    assert max(entry["nested"] for entry in tracks.values()) == 1.0


def test_a_gap_longer_than_the_buffer_starts_a_new_track():
    first, second = walk(["person"] * 3, step=0), walk(["person"] * 3, step=0)
    runs = first + [(video, moment + 5.0, found) for video, moment, found in second]
    assert len(replay_tracks.track(runs, 3)[0]) == 2
    assert len(replay_tracks.track(runs, 8)[0]) == 1
