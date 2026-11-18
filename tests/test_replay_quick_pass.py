"""tools/replay_quick_pass.py's pure parts: the log read, the quick pass's frames, the queue (backlog 46)."""

import importlib
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
replay_quick_pass = importlib.import_module("replay_quick_pass")

from jarvis import faces

LOG = """\
2026-11-17 22:00:01,000 INFO MainThread jarvis.cameras: Starting J.A.R.V.I.S.
2026-11-17 22:10:30,100 INFO Thread-9 (_assemble) jarvis.faces:   face scan 22-10-00.mp4: dense 4.5-11.7 s, 85 frames, 7.1 s (2.0 s paused), 7 face view(s), 0 without landmarks
2026-11-17 22:10:31,000 INFO Thread-8 (_assemble) jarvis.notify: Notification Front face, unknown face: sent
2026-11-17 22:10:31,500 INFO Thread-9 (_assemble) jarvis.notify: Notification Back face, unknown face: sent silently
2026-11-17 22:10:40,000 INFO Thread-9 (_assemble) jarvis.notify: Notification Back best view: sent
2026-11-17 22:11:00,000 INFO Thread-10 (_assemble) jarvis.faces:   face scan 22-10-40.mp4: dense none, 60 frames, 3.0 s (0.0 s paused), 0 face view(s), 0 without landmarks
"""


def test_a_scan_line_and_its_first_sent_message_are_read_from_its_own_thread(tmp_path):
    (tmp_path / "logs").mkdir()
    (tmp_path / "logs" / "jarvis.log").write_text(LOG, encoding="utf-8")
    first, second = replay_quick_pass.read_scans(tmp_path, datetime(2026, 11, 17, 22))
    assert first["stem"] == "22-10-00" and first["windows"] == [(4.5, 11.7)]
    assert (first["frames"], first["seconds"], first["paused"], first["views"]) == (85, 7.1, 2.0, 7)
    assert first["sent"] == datetime(2026, 11, 17, 22, 10, 31) and first["camera"] == "Back"
    assert second["windows"] == [] and second["sent"] is None


def test_a_scan_joins_the_latest_event_of_its_clip_on_its_camera():
    events = {}
    for camera, start in (("Back", datetime(2026, 11, 17, 22, 10)), ("Front", datetime(2026, 11, 17, 22, 10)),
                          ("Back", datetime(2026, 11, 16, 22, 10))):
        key = f"{camera}/{start:%Y-%m-%d}/22-10-00"
        events[key] = {"key": key, "camera": camera, "start": start,
                       "path": Path(f"clips/{camera}/{start:%Y-%m-%d}/22-10-00.json")}
    scan = {"stem": "22-10-00", "when": datetime(2026, 11, 17, 22, 10, 30), "camera": "Back"}
    assert list(replay_quick_pass.join_scans([scan], events)) == ["Back/2026-11-17/22-10-00"]


def test_the_moments_given_back_to_the_scan_make_the_logged_windows():
    for windows in ([(0.0, 9.3)], [(5.5, 9.3), (12.7, 16.0)]):
        assert faces._windows(replay_quick_pass.moments_of(windows)) == [list(w) for w in windows]


def test_the_quick_pass_spreads_its_frames_through_the_person_windows():
    frames = [{"t": t / 2, "faces": []} for t in range(40)]
    chosen = replay_quick_pass.spread_pick(replay_quick_pass.inside(frames, [(5.0, 14.5)]), 4)
    assert [f["t"] for f in chosen] == [6.0, 8.5, 11.0, 13.5]
    assert len(replay_quick_pass.spread_pick(frames[:3], 8)) == 3
    assert replay_quick_pass.inside(frames, []) == frames


class Known:
    def __init__(self, scores):
        self.scores = scores

    def match(self, embedding):
        score = self.scores.get(tuple(embedding), 0.0)
        return ("p_1" if score >= faces.MATCH_THRESHOLD else None), score


def test_the_quick_pass_stops_after_the_first_frame_with_a_sure_face():
    face = lambda e: {"embedding": e}
    frames = [{"t": float(t), "faces": []} for t in range(8)]
    frames[2]["faces"] = [face([0.35])]
    frames[5]["faces"] = [face([0.6])]
    entry = {"frames": frames, "windows": []}
    gallery = Known({(0.35,): 0.35, (0.6,): 0.6})
    assert len(replay_quick_pass.quick_frames(entry, 8, gallery, 0.4)) == 6
    assert len(replay_quick_pass.quick_frames(entry, 8, gallery, 0.3)) == 3


def test_a_paused_scan_works_only_between_recordings():
    busy = [[10.0, 20.0], [25.0, 30.0]]
    assert replay_quick_pass.finish_with_pause(0.0, 5.0, busy) == 5.0
    assert replay_quick_pass.finish_with_pause(8.0, 5.0, busy) == 23.0
    assert replay_quick_pass.finish_with_pause(12.0, 2.0, busy) == 22.0
    assert replay_quick_pass.finish_with_pause(12.0, 2.0, busy, budget=3.0) == 17.0
    assert replay_quick_pass.finish_with_pause(40.0, 2.0, busy) == 42.0


def test_quick_jobs_jump_the_queue_of_full_scans_but_none_is_cut_short():
    jobs = [(0.0, "full", 10.0, "full a"), (1.0, "full", 10.0, "full b"), (2.0, "quick", 1.0, "quick b")]
    assert replay_quick_pass.simulate(jobs, False) == {"full a": 10.0, "full b": 20.0, "quick b": 21.0}
    assert replay_quick_pass.simulate(jobs, True) == {"full a": 10.0, "quick b": 11.0, "full b": 21.0}
    paused = [(0.0, "quick", lambda began: began + 5.0, "q")]
    assert replay_quick_pass.simulate(paused, True) == {"q": 5.0}


def test_a_message_is_compared_by_its_kind_a_side_or_best_view_alike():
    assert replay_quick_pass.kind("Back face, Visitor 3, unknown face") == "face, Visitor 3, unknown face"
    assert replay_quick_pass.kind("Back side view") == replay_quick_pass.kind("Back best view") == "no face"
    assert replay_quick_pass.kind("Back hidden person") == "hidden person"


def test_an_identity_is_sure_probable_or_unknown():
    assert replay_quick_pass.identity({"name": "Izabel", "score": 0.5}, 0.4) == "sure Izabel"
    assert replay_quick_pass.identity({"name": "Izabel", "score": 0.32}, 0.4) == "probable Izabel"
    assert replay_quick_pass.identity({"name": "", "temporary_name": "Visitor 4"}, 0.4) == "unknown face Visitor 4"
    assert replay_quick_pass.identities([], 0.4) == ("none",)
