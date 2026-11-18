"""Notifications by visit in Home: dog tracks, a resident explaining one body, and only news after the first (backlog 41)."""

import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta

import pytest

from jarvis import modes, notify
from jarvis.tracks import dog_only

TOKEN = "123456789:AAFakeTokenForTheVisitTests_x"
REAL_THREAD = threading.Thread
HOME = {"notify_token": TOKEN, "notify_chat": "1", "notify_labels": ["person"],
        "notify_cooldown": 120, "notify_mode": "home"}
AWAY = {**HOME, "notify_mode": "away"}
START = datetime(2026, 11, 17, 12, 0, 0)
GUSTAVO = {"person_id": "p_1", "name": "Gustavo", "score": 0.6, "thumbnail_path": None, "resident": True}
PROBABLY_GUSTAVO = {**GUSTAVO, "score": 0.31}
STRANGER = {"person_id": "p_9", "name": "", "score": 0.0, "thumbnail_path": None, "resident": False}
OTHER_STRANGER = {**STRANGER, "person_id": "p_8"}
DOG_TRACK = [{"id": 4, "first": 0.0, "last": 6.0, "frames": {"dog": 9, "person": 3}, "longest_person_run": 1}]
PERSON_TRACK = [{"id": 5, "first": 0.0, "last": 6.0, "frames": {"person": 9}, "longest_person_run": 9}]


class Clock:
    now = 1000.0


class Inline:
    def __init__(self, target, args=(), kwargs=None, daemon=None, name=None):
        self.target, self.args, self.kwargs = target, args, kwargs or {}

    def start(self):
        self.target(*self.args, **self.kwargs)

    def join(self, timeout=None):
        pass


class Timer:
    """The floor's timer, never fired: these tests count messages, not the floor's text."""

    def __init__(self, interval, function, args=()):
        self.daemon = False

    def start(self):
        pass

    def cancel(self):
        pass


@pytest.fixture(autouse=True)
def sent(monkeypatch):
    notify.reset_incident()
    messages = []
    monkeypatch.setattr(notify, "_post", lambda text, image=None, settings=None, silent=False:
                        (messages.append(text), (True, "", None))[1])
    monkeypatch.setattr(notify.threading, "Thread", Inline)
    monkeypatch.setattr(notify.threading, "Timer", Timer)
    monkeypatch.setattr(notify, "_clock", lambda: Clock.now)
    yield messages
    notify.reset_incident()


@pytest.fixture
def best(tmp_path):
    path = tmp_path / "best.jpg"
    path.write_bytes(b"jpg")
    return path


def scan(camera, minutes, found=(), people=1, best=None, settings=HOME, tracks=None, seconds=10, held=True):
    """One event's scan finishing: it started minutes after START and lasted seconds."""
    start = START + timedelta(minutes=minutes)
    return notify.after_scan(camera, start, list(found), held, False, None, best, settings, people=people,
                             ended_at=start + timedelta(seconds=seconds), tracks=tracks)


def skips(caplog):
    return [r.getMessage() for r in caplog.records if "skipped: visit" in r.getMessage() or "skipped: dog" in r.getMessage()]


def test_a_track_voted_dog_with_no_run_of_two_person_frames_is_a_dog_event():
    assert dog_only(DOG_TRACK)
    assert not dog_only(PERSON_TRACK)
    assert not dog_only(DOG_TRACK + PERSON_TRACK)
    assert not dog_only([{**DOG_TRACK[0], "longest_person_run": 2}])
    assert not dog_only([{**DOG_TRACK[0], "frames": {"dog": 3, "person": 3}}])
    assert not dog_only([])
    assert not dog_only(None)
    assert dog_only(DOG_TRACK + [{"id": 6, "first": 1.0, "last": 2.0, "frames": {"dog": 4},
                                  "longest_person_run": 0}])


def test_a_dog_event_sends_no_person_message(sent, best, caplog):
    caplog.set_level("INFO", logger="jarvis.notify")
    assert scan("Back", 0, best=best, tracks=DOG_TRACK) == 0
    assert sent == [] and skips(caplog) == ["Notification Back best view: skipped: dog tracks"]


def test_an_event_without_tracks_decides_as_today(sent, best):
    assert scan("Back", 0, best=best, tracks=None) == 1
    assert sent == ["Back 12:00:00: no face seen, best view"]


def test_a_dog_event_does_not_extend_the_visit(sent, best):
    scan("Back", 0, [GUSTAVO], best=best)
    scan("Back", 4, best=best, tracks=DOG_TRACK)
    assert scan("Back", 8, best=best) == 1


def test_a_resident_recognised_explains_one_faceless_body_four_minutes_later(sent, best, caplog):
    caplog.set_level("INFO", logger="jarvis.notify")
    assert scan("Back", 0, [GUSTAVO], best=best) == 0
    assert scan("Back", 4, best=best) == 0
    assert sent == []
    assert skips(caplog) == ["Notification Back best view: skipped: visit (Gustavo recognized at 12:00:00)"]


def test_two_people_at_once_are_never_explained_by_a_name(sent, best):
    scan("Back", 0, [GUSTAVO], best=best)
    assert scan("Back", 4, best=best, people=2) == 1
    assert sent == ["Back 12:04:00: no face seen, best view"]


def test_the_hidden_person_beside_a_resident_still_reaches_the_phone(sent, best):
    scan("Back", 0, [GUSTAVO], best=best)
    assert scan("Back", 4, [GUSTAVO], best=best, people=2) == 1
    assert sent == ["Back 12:04:00: 2 people seen, 1 face found"]


def test_a_resident_on_the_other_camera_explains_nothing(sent, best):
    scan("Front", 0, [GUSTAVO], best=best)
    assert scan("Back", 4, best=best) == 1


def test_a_probable_resident_explains_nothing(sent, best):
    scan("Back", 0, [PROBABLY_GUSTAVO], best=best)
    assert scan("Back", 4, best=best) == 1


def test_five_minutes_from_the_end_of_one_event_to_the_start_of_the_next_is_a_new_visit(sent, best):
    scan("Back", 0, [GUSTAVO], best=best, seconds=60)
    assert scan("Back", 5, best=best) == 0
    assert scan("Back", 10, best=best, seconds=1) == 0
    assert scan("Back", 15, seconds=1, best=best) == 0
    assert scan("Back", 20 + 1 / 60, best=best) == 1


def test_a_second_faceless_event_in_a_visit_that_already_sent_stays_quiet(sent, best, caplog):
    caplog.set_level("INFO", logger="jarvis.notify")
    assert scan("Back", 0, best=best) == 1
    assert scan("Back", 2, best=best) == 0
    assert skips(caplog) == ["Notification Back best view: skipped: visit (no news, 1 person at once)"]


def test_more_people_than_the_visit_has_seen_is_news(sent, best):
    scan("Back", 0, best=best)
    assert scan("Back", 2, best=best, people=2) == 1
    assert scan("Back", 3, best=best, people=2) == 0
    assert scan("Back", 4, best=best, people=3) == 1


def test_a_face_not_yet_seen_in_the_visit_is_news_and_the_same_face_again_is_not(sent, best, caplog):
    caplog.set_level("INFO", logger="jarvis.notify")
    assert scan("Front", 0, [STRANGER], best=best) == 1
    assert scan("Front", 2, [STRANGER], best=best) == 0
    assert scan("Front", 3, [OTHER_STRANGER], best=best) == 1
    assert sent == ["Front 12:00:00: unknown face", "Front 12:03:00: unknown face"]
    assert skips(caplog) == ["Notification Front face, unknown face: skipped: visit (the same face again)"]


def test_a_second_body_beside_a_face_already_seen_is_news(sent, best):
    scan("Front", 0, [STRANGER], best=best)
    assert scan("Front", 2, [STRANGER], best=best, people=2) == 1
    assert scan("Front", 3, [STRANGER], best=best, people=2) == 0
    assert sent == ["Front 12:00:00: unknown face", "Front 12:02:00: 2 people seen, 1 face found"]


def test_a_resident_recognised_only_after_the_event_explains_nothing(sent, best):
    scan("Back", 4, [GUSTAVO], best=best)
    assert scan("Back", 2, best=best) == 1
    assert sent == ["Back 12:02:00: no face seen, best view"]


def test_a_face_is_news_once_whatever_the_visit_sent_first(sent, best):
    scan("Front", 0, best=best)
    assert scan("Front", 1, [STRANGER], best=best) == 1
    assert scan("Front", 2, [STRANGER], best=best) == 0


def test_the_first_message_of_a_visit_goes_out_whatever_came_before(sent, best):
    scan("Front", 0, [GUSTAVO], best=best)
    assert scan("Front", 2, [STRANGER], best=best) == 1


def test_a_stranger_whose_face_shows_beside_a_resident_still_reaches_the_phone(sent, best):
    scan("Back", 0, [GUSTAVO], best=best)
    assert scan("Back", 1, [GUSTAVO, STRANGER], best=best, people=2) == 1
    assert sent == ["Back 12:01:00: unknown face"]


def test_away_is_unchanged(sent, best):
    away = {**AWAY, "notify_modes": modes.defaults(["person"])}
    scan("Back", 0, [GUSTAVO], best=best, settings=away, held=False)
    assert notify.after_scan("Back", START + timedelta(minutes=4), [], False, True, None, best, away,
                             people=1, ended_at=START + timedelta(minutes=4, seconds=10), tracks=DOG_TRACK) == 1


def test_a_scan_that_finishes_late_for_an_older_visit_leaves_the_current_one_alone(sent, best):
    scan("Back", 30, [GUSTAVO], best=best)
    assert scan("Back", 0, best=best) == 1
    assert scan("Back", 33, best=best) == 0


def test_the_visit_holds_under_threads(sent, best, monkeypatch):
    monkeypatch.setattr(threading, "Thread", REAL_THREAD)
    scan("Back", 0, best=best)
    with ThreadPoolExecutor(8) as pool:
        results = list(pool.map(lambda minute: scan("Back", 1 + minute / 10, best=best), range(16)))
    assert sum(results) == 0 and len(sent) == 1


class Camera:
    label = "Back"

    def covering(self, start, end):
        return ["20261117-120000.mp4"]


def test_the_assembly_passes_the_events_end_and_tracks(tmp_path, monkeypatch, sent, best):
    from jarvis import clips, faces
    monkeypatch.setattr(notify, "load", lambda: HOME)
    monkeypatch.setattr(clips, "ASSEMBLY_DELAY", 0)
    monkeypatch.setattr(clips, "_concat", lambda segments, destination: destination.write_bytes(b"x"))
    monkeypatch.setattr(faces, "quick_scan", lambda *a, **k: ([], []))
    monkeypatch.setattr(faces, "scan_clip", lambda *a, **k: [])
    clips._assemble(Camera(), START, START, tmp_path / "12-00-00.mp4", {"person"}, False, best,
                    held=True, people=1, tracks=DOG_TRACK)
    assert sent == []
    clips._assemble(Camera(), START, START, tmp_path / "12-00-00.mp4", {"person"}, False, best,
                    held=True, people=1, tracks=PERSON_TRACK)
    assert sent == ["Back 12:00:00: no face seen, best view"]
