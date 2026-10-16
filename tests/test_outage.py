"""A camera with no picture for a minute reaches the phone, loud, and so does its return."""

from datetime import datetime

import pytest

from jarvis import modes, notify, outage

SETTINGS = {"notify_token": "x", "notify_chat": "1", "notify_cooldown": 120, "notify_mode": "home"}
WALL = datetime(2026, 10, 16, 16, 33, 10)


class Clock:
    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now


@pytest.fixture
def sent(monkeypatch):
    notify.reset_incident()
    messages = []
    monkeypatch.setattr(notify, "load", lambda: SETTINGS)
    monkeypatch.setattr(notify, "send", lambda text, image=None, settings=None, silent=False:
                        (messages.append((text, silent)), (True, ""))[1])
    yield messages
    notify.reset_incident()


def watch(ages, clock, monkeypatch=None):
    if monkeypatch:
        monkeypatch.setattr(notify, "_clock", clock)
    return outage.CameraWatch(lambda: ages, clock=clock, wall=lambda: WALL)


def test_nothing_is_said_in_the_first_minute(sent):
    clock = Clock()
    ages = {"Back": None, "Front": 0.1}
    camera = watch(ages, clock)
    clock.now += 59
    assert camera.check() == [] and sent == []
    clock.now += 1
    assert camera.check() == ["Back: no picture since 16:32:10"]


def test_a_minute_without_a_frame_is_down_once_and_its_return_says_how_long(sent, monkeypatch):
    clock = Clock()
    ages = {"Back": 0.1, "Front": 0.1}
    camera = watch(ages, clock, monkeypatch)
    clock.now += 120
    ages["Back"] = 59.0
    assert camera.check() == []
    ages["Back"] = 60.0
    assert camera.check() == ["Back: no picture since 16:32:10"]
    ages["Back"] = 65.0
    assert camera.check() == []
    clock.now += 300
    ages["Back"] = 0.2
    assert camera.check() == ["Back: picture back, 6 min without"]
    assert sent == [("Back: no picture since 16:32:10", False), ("Back: picture back, 6 min without", False)]


def test_the_case_is_on_at_home_and_away_and_off_in_silent(sent, caplog):
    for mode in modes.MODES:
        assert modes.allowed("camera_down", {**SETTINGS, "notify_mode": mode}) is (mode != "silent")
    caplog.set_level("INFO")
    assert not notify.camera_down("Back", "Back: no picture since 16:32:10",
                                  {**SETTINGS, "notify_mode": "silent"})
    assert sent == [] and "skipped: silent mode" in caplog.text


def test_it_is_logged_whatever_the_mode(monkeypatch, caplog):
    monkeypatch.setattr(notify, "load", lambda: {**SETTINGS, "notify_mode": "silent"})
    clock = Clock()
    camera = watch({"Back": None}, clock)
    clock.now += 61
    caplog.set_level("WARNING", logger="jarvis.outage")
    camera.check()
    assert "Camera Back: no picture since" in caplog.text


def test_an_older_config_gets_the_new_switch():
    stored = {"home": {"unknown_face": False}, "away": {}, "silent": {}}
    result = modes.normalised(stored, ["person"])
    assert result["home"]["camera_down"] and result["away"]["camera_down"]
    assert not result["silent"]["camera_down"]
