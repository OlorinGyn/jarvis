"""Backlog 29: /off stops the analysis, never the capture, and /on or a restart bring it back."""

import importlib
import logging

import numpy as np
import pytest
from fastapi.testclient import TestClient

from jarvis import analysis, bot, cameras, clips, notify, web
from jarvis.geometry import Detection

from test_bot import Telegram, TOKEN, arrive, message

FRAME = np.zeros((360, 640, 3), np.uint8)
PERSON = Detection(300, 50, 80, 250, 0.9, "person")


class Clock:
    """A monotonic clock the test moves by hand."""

    def __init__(self, now=1000.0):
        self.now = now

    def monotonic(self):
        return self.now


@pytest.fixture(autouse=True)
def back_on():
    analysis.set_on(True)
    yield
    analysis.set_on(True)


@pytest.fixture
def clock(monkeypatch):
    found = Clock()
    monkeypatch.setattr(analysis, "time", found)
    monkeypatch.setattr(clips, "time", found)
    return found


class Motion:
    def __init__(self):
        self.seen = 0

    def detect(self, frame):
        self.seen += 1
        return [(0, 0, 640, 360)]


class Subjects:
    def __init__(self, found):
        self.found = found
        self.subjects = []
        self.seen = 0

    def detect(self, frame, boxes):
        self.seen += 1
        self.subjects = list(self.found)
        return self.subjects


class Stream:
    label = "Front"

    def covering(self, start, end):
        return []


class Cam:
    def __init__(self, tmp_path, found=()):
        self.label = "Front"
        self.motion = Motion()
        self.subjects = Subjects(found)
        self.recorder = clips.EventRecorder(Stream(), tmp_path)

    def read(self):
        return FRAME

    def prune(self):
        pass


class Idle:
    def tick(self):
        return None


@pytest.fixture
def core(tmp_path, monkeypatch, clock):
    monkeypatch.setattr(cameras, "Housekeeper", Idle)
    monkeypatch.setattr(notify, "event", lambda *args: (False, False))
    monkeypatch.setattr(clips, "_assemble", lambda *args: None)
    return cameras.Core([Cam(tmp_path, [PERSON])])


def test_off_drops_every_frame_before_motion(core):
    cam = core.streams[0]
    analysis.set_on(False)
    assert core.step()
    assert cam.motion.seen == 0 and cam.subjects.seen == 0
    assert not cam.recorder.recording and core.analysed["Front"] == 0


def test_an_open_event_ends_at_off_as_if_the_motion_stopped(core, clock):
    cam = core.streams[0]
    core.step()
    assert cam.recorder.recording
    analysis.set_on(False)
    core.step()
    assert cam.recorder.recording and cam.subjects.subjects == []
    clock.now += clips.POST_SECONDS + 0.1
    core.step()
    assert not cam.recorder.recording
    assert cam.motion.seen == 1


def test_coming_back_on_relearns_the_background(core):
    cam = core.streams[0]
    old = cam.motion
    analysis.set_on(False)
    core.step()
    analysis.set_on(True)
    core.step()
    assert cam.motion is not old and isinstance(cam.motion, cameras.MotionDetector)


def test_a_restart_starts_on():
    analysis.set_on(False)
    importlib.reload(analysis)
    assert analysis.is_on() and analysis.describe() == "On"


@pytest.fixture
def poller(monkeypatch):
    telegram = Telegram()
    stored = {"notify_token": TOKEN, "notify_chat": "42", "notify_mode": "away",
              "notify_labels": ["person"]}
    found = bot.Poller(call=telegram, load=lambda: dict(stored),
                       update=lambda **changes: stored.update(changes))
    monkeypatch.setattr(found.stopping, "wait", lambda seconds=None: False)
    return found, telegram


def test_off_and_on_from_the_configured_chat(poller):
    found, telegram = poller
    arrive(telegram, message(42, "/off"))
    found.poll_once()
    assert not analysis.is_on()
    assert telegram.sent()[-1]["text"].startswith("Analysis Off")
    arrive(telegram, message(42, "/mode", 2))
    found.poll_once()
    assert telegram.sent()[-1]["text"].endswith("Analysis: Off.")
    arrive(telegram, message(42, "/on", 3))
    found.poll_once()
    assert analysis.is_on() and telegram.sent()[-1]["text"] == "Analysis On."


def test_another_chat_cannot_switch_it_off(poller):
    found, telegram = poller
    arrive(telegram, message(99, "/off"))
    found.poll_once()
    assert analysis.is_on() and telegram.sent() == []


def test_a_reminder_every_three_hours_while_off(poller, clock):
    found, telegram = poller
    analysis.set_on(False)
    found.poll_once()
    clock.now += bot.REMINDER_SECONDS - 1
    found.poll_once()
    assert telegram.sent() == []
    clock.now += 1
    found.poll_once()
    found.poll_once()
    assert [s["text"] for s in telegram.sent()] == [
        "Analysis has been Off for 3 h: nothing is recorded or sent. /on resumes it."]
    clock.now += bot.REMINDER_SECONDS
    found.poll_once()
    assert telegram.sent()[-1]["text"].startswith("Analysis has been Off for 6 h")


def test_switched_on_again_the_reminders_start_over(poller, clock):
    found, telegram = poller
    analysis.set_on(False)
    clock.now += bot.REMINDER_SECONDS
    found.poll_once()
    analysis.set_on(True)
    found.poll_once()
    analysis.set_on(False)
    clock.now += bot.REMINDER_SECONDS
    found.poll_once()
    assert len(telegram.sent()) == 2


def test_the_page_status_says_on_or_off():
    client = TestClient(web.app, client=("127.0.0.1", 50000))
    assert client.get("/api/status").json()["analysis"] == "On"
    analysis.set_on(False)
    assert client.get("/api/status").json()["analysis"] == "Off"


HEADER = {"X-Jarvis-Request": "1"}


@pytest.fixture
def page(tmp_path, monkeypatch):
    from jarvis import devices, settings
    monkeypatch.setattr(settings, "FILE", tmp_path / "config.json")
    monkeypatch.setattr(devices, "FILE", tmp_path / "devices.json")
    return TestClient(web.app, client=("127.0.0.1", 50000))


def test_off_and_on_from_the_page_switch_the_same_flag(page, caplog):
    with caplog.at_level(logging.INFO, logger="jarvis.web"):
        answer = page.post("/api/analysis", headers=HEADER, json={"on": False})
    assert answer.status_code == 200
    assert answer.json() == {"analysis": "Off", "changed": True}
    assert not analysis.is_on()
    assert page.get("/api/status").json()["analysis"] == "Off"
    assert "analysis Off from the page" in caplog.text
    again = page.post("/api/analysis", headers=HEADER, json={"on": False}).json()
    assert again == {"analysis": "Off", "changed": False}
    assert page.post("/api/analysis", headers=HEADER, json={"on": True}).json()["analysis"] == "On"
    assert analysis.is_on()


def test_switching_from_the_page_is_never_stored(page, tmp_path):
    page.post("/api/analysis", headers=HEADER, json={"on": False})
    assert not (tmp_path / "config.json").exists()


def test_the_page_switch_wants_a_boolean(page):
    for wrong in ({}, {"on": "off"}, {"on": 0}):
        assert page.post("/api/analysis", headers=HEADER, json=wrong).status_code == 400
    assert analysis.is_on()


def test_the_page_switch_goes_through_the_write_guard(page):
    assert page.post("/api/analysis", json={"on": False}).status_code == 403
    remote = TestClient(web.app, client=("192.168.0.50", 50000))
    assert remote.post("/api/analysis", headers=HEADER, json={"on": False}).status_code == 403
    assert analysis.is_on()


def test_a_reminder_comes_after_off_from_the_page(poller, clock, page):
    found, telegram = poller
    page.post("/api/analysis", headers=HEADER, json={"on": False})
    clock.now += bot.REMINDER_SECONDS
    found.poll_once()
    assert any("Analysis has been Off" in fields["text"] for fields in telegram.sent())
