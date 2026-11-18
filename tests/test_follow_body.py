"""tools/follow_body.py's pure parts: the restarts, the classes of a faceless message, shared ids, lifetimes (item 7)."""

import importlib
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
follow_body = importlib.import_module("follow_body")

SURE = 0.6
RESIDENT = {"name": "Gustavo", "resident": True, "score": 0.7}


def event(camera, start, tracks, most=None, seconds=10.0):
    key = f"{camera}/{start:%Y-%m-%d}/{start:%H-%M-%S}"
    return {"key": key, "camera": camera, "start": start, "end": start + timedelta(seconds=seconds),
            "tracks": [{"id": i, "first": f, "last": l, "frames": frames, "longest_person_run": 2}
                       for i, f, l, frames in tracks],
            "most_person_tracks": most if most is not None else len(tracks)}


def at(minute, second=0):
    return datetime(2026, 11, 15, 20, minute, second)


PERSON = {"person": 4}


def test_restarts_are_read_from_every_log_and_count_runs(tmp_path):
    (tmp_path / "logs").mkdir()
    (tmp_path / "logs" / "jarvis.log").write_text(
        "2026-11-15 20:30:00,000 INFO MainThread jarvis.cameras: Starting 2 camera(s) on stream2...\n"
        "2026-11-15 20:31:00,000 INFO MainThread jarvis.notify: Notification Back best view: sent\n", encoding="utf-8")
    (tmp_path / "logs" / "jarvis.log.1").write_text(
        "2026-11-14 08:00:00,000 INFO MainThread jarvis.cameras: Starting 2 camera(s) on stream2...\n", encoding="utf-8")
    restarts = follow_body.read_restarts(tmp_path)
    assert restarts == [datetime(2026, 11, 14, 8), datetime(2026, 11, 15, 20, 30)]
    assert follow_body.run_of(at(10), restarts) == 1 and follow_body.run_of(at(40), restarts) == 2


def test_a_faceless_message_whose_body_was_named_earlier_on_the_camera_is_a():
    named = event("Back", at(0), [(7, 0.0, 5.0, PERSON)])
    later = event("Back", at(1), [(7, 0.0, 3.0, PERSON)])
    other = event("Front", at(2), [(7, 0.0, 3.0, PERSON)])
    rows = follow_body.classify([named, later, other], {later["key"]: ["Back best view"],
                                                        other["key"]: ["Front side view"]},
                                {named["key"]: [RESIDENT]}, SURE, [])
    assert [(r["key"], r["class"], r["source"]) for r in rows] == [(later["key"], "a", named["key"]),
                                                                   (other["key"], "c", None)]


def test_a_restart_between_the_events_breaks_the_shared_id():
    named = event("Back", at(0), [(7, 0.0, 5.0, PERSON)])
    later = event("Back", at(10), [(7, 0.0, 3.0, PERSON)])
    rows = follow_body.classify([named, later], {later["key"]: ["Back best view"]}, {named["key"]: [RESIDENT]},
                                SURE, [at(5)])
    assert rows[0]["class"] == "c"


def test_a_probable_or_visitor_face_names_no_body():
    for found in ({**RESIDENT, "score": 0.5}, {**RESIDENT, "resident": False}):
        named = event("Back", at(0), [(7, 0.0, 5.0, PERSON)])
        later = event("Back", at(1), [(7, 0.0, 3.0, PERSON)])
        rows = follow_body.classify([named, later], {later["key"]: ["Back best view"]}, {named["key"]: [found]},
                                    SURE, [])
        assert rows[0]["class"] == "c"


def test_a_hidden_person_beside_a_resident_with_more_tracks_than_faces_is_b():
    both = event("Front", at(0), [(1, 0.0, 5.0, PERSON), (2, 0.0, 5.0, PERSON)], most=2)
    boxes = event("Front", at(5), [(3, 0.0, 5.0, PERSON)], most=1)
    rows = follow_body.classify([both, boxes], {both["key"]: ["Front face, Gustavo", "Front hidden person"],
                                                boxes["key"]: ["Front hidden person"]},
                                {both["key"]: [RESIDENT], boxes["key"]: [RESIDENT]}, SURE, [])
    assert [(r["key"], r["kind"], r["class"]) for r in rows] == [(both["key"], "hidden person", "b"),
                                                                 (boxes["key"], "hidden person", "c")]


def test_a_dog_track_carries_no_name_to_a_person_message():
    named = event("Back", at(0), [(7, 0.0, 5.0, {"dog": 5})])
    later = event("Back", at(1), [(7, 0.0, 3.0, {"dog": 3, "person": 1}), (8, 0.0, 3.0, PERSON)])
    rows = follow_body.classify([named, later], {later["key"]: ["Back best view"]}, {named["key"]: [RESIDENT]},
                                SURE, [])
    assert rows[0]["class"] == "c"


def test_consecutive_events_share_ids_only_within_one_run():
    first = event("Back", at(0), [(7, 0.0, 5.0, PERSON)], seconds=20)
    second = event("Back", at(1), [(7, 0.0, 3.0, PERSON)])
    third = event("Back", at(20), [(7, 0.0, 3.0, PERSON)])
    pairs = follow_body.consecutive([third, first, second], [at(10)])
    assert [(p["before"], p["shared"], p["gap"]) for p in pairs] == [(first["key"], {7}, 40.0),
                                                                     (second["key"], set(), 1130.0)]


def test_a_track_lives_from_its_first_moment_to_its_last_over_its_events():
    first = event("Back", at(0), [(7, 2.0, 30.0, PERSON)])
    second = event("Back", at(3), [(7, 0.0, 10.0, {"person": 1, "dog": 3})])
    joined = follow_body.lifetimes([first, second], {second["key"]: [RESIDENT]}, [])
    track = joined["Back", 0, 7]
    assert track["seconds"] == 188.0 and track["events"] == [first["key"], second["key"]]
    assert track["person"] and track["face"]


def run(video, moment, *boxes):
    """A replayed run: (video, moment, [(track id, Detection)], no frame)."""
    from jarvis.geometry import Detection
    return (video, moment, [(tid, Detection(x, y, w, h, 0.9, label)) for tid, x, y, w, h, label in boxes], None)


def face(x, y, w=20, h=20):
    return {"box": (x, y, w, h), "embedding": [0.0], "score": 0.9}


def test_a_face_binds_to_the_smaller_person_box_of_the_nearest_run_within_half_a_second():
    runs = [run("a.mp4", 1.0, (1, 0, 0, 400, 500, "person"), (2, 50, 50, 100, 200, "person"), (3, 0, 0, 900, 500, "dog")),
            run("a.mp4", 3.0, (1, 0, 0, 400, 500, "person"))]
    entry = {"frames": [{"t": 1.2, "faces": [face(160, 160)]}, {"t": 1.2, "faces": [face(1000, 100)]},
                        {"t": 2.0, "faces": [face(160, 160)]}]}
    bound = follow_body.bind(runs, {"a.mp4": 0.0}, "a.mp4", entry, 0.5, lambda e: "sure resident")
    assert [(f["track"], f["ambiguous"], f["run"]) for f in bound] == [(2, True, 0), (None, False, 0), (None, False, None)]


def test_a_face_in_the_overlap_binds_to_the_earlier_videos_run_on_the_timeline():
    runs = [run("a.mp4", 9.0, (4, 0, 0, 400, 500, "person"))]
    entry = {"frames": [{"t": 1.0, "faces": [face(100, 100)]}]}
    bound = follow_body.bind(runs, {"a.mp4": 0.0, "b.mp4": 8.0}, "b.mp4", entry, 1.0, lambda e: "unknown")
    assert bound[0]["track"] == 4 and bound[0]["moment"] == 9.0


def test_frames_are_saved_only_once_every_person_present_was_named_sure_before():
    runs = [run("a.mp4", 1.0, (1, 0, 0, 400, 500, "person")),
            run("a.mp4", 2.0, (1, 0, 0, 400, 500, "person")),
            run("a.mp4", 3.0, (1, 0, 0, 400, 500, "person"), (2, 500, 0, 300, 500, "person")),
            run("a.mp4", 4.0, (2, 500, 0, 300, 500, "person"))]
    bound = [{"moment": 1.0, "track": 1, "who": "sure resident"}, {"moment": 4.0, "track": 2, "who": "probable resident"}]
    entry = {"frames": [{"t": t, "faces": []} for t in (1.0, 2.0, 3.0, 4.0, 9.0)]}
    assert follow_body.saved_share(runs, bound, "a.mp4", entry, {"a.mp4": 0.0}) == (1, 5)


def test_person_tracks_of_the_last_video_are_voted_from_its_start_on():
    runs = [run("a.mp4", 1.0, (1, 0, 0, 10, 10, "person")),
            run("b.mp4", 9.0, (1, 0, 0, 10, 10, "person"), (2, 0, 0, 10, 10, "dog")),
            run("b.mp4", 10.0, (3, 0, 0, 10, 10, "person"))]
    assert follow_body.person_tracks_in(runs, 8.0) == {1, 3}
