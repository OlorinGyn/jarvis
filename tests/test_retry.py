"""A message that fails to send is tried again, off the caller's thread, and never lost to one bad answer (R63)."""

import pytest
import requests

from jarvis import notify

TOKEN = "123456789:AAFakeTokenForTheRetryTests_x"
SETTINGS = {"notify_token": TOKEN, "notify_chat": "1", "notify_labels": ["person"],
            "notify_cooldown": 120, "notify_mode": "away"}


class Answer:
    """One HTTP answer from the fake Telegram."""

    def __init__(self, status, payload):
        self.status_code, self.payload = status, payload

    def json(self):
        if self.payload is None:
            raise ValueError("not JSON")
        return self.payload


OK = Answer(200, {"ok": True, "result": {}})
SERVER_ERROR = Answer(500, {"ok": False, "error_code": 500, "description": "Internal Server Error"})
NOT_JSON = Answer(502, None)
BAD_REQUEST = Answer(400, {"ok": False, "error_code": 400, "description": "Bad Request: chat not found"})
TOO_MANY = Answer(429, {"ok": False, "error_code": 429, "description": "Too Many Requests: retry after 7",
                        "parameters": {"retry_after": 7}})


class FakeTelegram:
    """Answers each post with the next scripted outcome: an exception is raised, an Answer returned."""

    def __init__(self, *script):
        self.script = list(script)
        self.posts = []

    def __call__(self, url, data=None, files=None, timeout=None):
        self.posts.append(data)
        outcome = self.script.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


class Inline:
    """A thread that runs at start(), so a test sees every attempt at once."""

    started = 0

    def __init__(self, target, args=(), kwargs=None, daemon=None, name=None):
        self.target, self.args, self.kwargs = target, args, kwargs or {}

    def start(self):
        Inline.started += 1
        self.target(*self.args, **self.kwargs)


@pytest.fixture
def telegram(monkeypatch):
    pauses = []
    Inline.started = 0
    monkeypatch.setattr(notify, "_sleep", pauses.append)
    monkeypatch.setattr(notify.threading, "Thread", Inline)

    def install(*script):
        fake = FakeTelegram(*script)
        monkeypatch.setattr(notify.requests, "post", fake)
        fake.pauses = pauses
        return fake

    return install


@pytest.mark.parametrize("failure", [requests.ReadTimeout("Read timed out. (read timeout=15)"),
                                     SERVER_ERROR,
                                     requests.ConnectionError("[WinError 10061] connection refused"),
                                     NOT_JSON])
def test_a_message_that_fails_once_arrives(telegram, caplog, failure):
    caplog.set_level("INFO", logger="jarvis.notify")
    fake = telegram(failure, OK)
    assert notify._send_logged("Front best view", "Front 12:00:00: no face seen", None, SETTINGS) is False
    assert len(fake.posts) == 2 and fake.pauses == [notify.RETRY_PAUSES[0]] and Inline.started == 1
    lines = [r.getMessage() for r in caplog.records]
    assert lines[0].startswith("Notification Front best view: failed, attempt 1 of 5, trying again in 5 s: ")
    assert lines[-1] == "Notification Front best view: sent, attempt 2"


def test_the_pause_grows_and_the_last_failure_gives_up(telegram, caplog):
    caplog.set_level("INFO", logger="jarvis.notify")
    fake = telegram(*[SERVER_ERROR] * len(notify.RETRY_PAUSES), SERVER_ERROR)
    notify._send_logged("Front face, unknown face", "Front 12:00:00: unknown face", None, SETTINGS)
    assert fake.pauses == list(notify.RETRY_PAUSES) and len(fake.posts) == len(notify.RETRY_PAUSES) + 1
    assert sorted(fake.pauses) == fake.pauses and 60 <= sum(fake.pauses) <= 120
    lines = [r.getMessage() for r in caplog.records]
    assert len(lines) == len(notify.RETRY_PAUSES) + 1
    assert lines[-1] == ("Notification Front face, unknown face: failed, attempt 5 of 5, gave up: "
                         "Internal Server Error")


def test_too_many_requests_waits_what_telegram_says(telegram):
    fake = telegram(TOO_MANY, OK)
    notify._send_logged("Front best view", "x", None, SETTINGS)
    assert fake.pauses == [7] and len(fake.posts) == 2


def test_another_client_error_is_not_tried_again(telegram, caplog):
    caplog.set_level("INFO", logger="jarvis.notify")
    fake = telegram(BAD_REQUEST)
    assert notify._send_logged("Front best view", "x", None, SETTINGS) is False
    assert len(fake.posts) == 1 and fake.pauses == [] and Inline.started == 0
    assert [r.getMessage() for r in caplog.records] == [
        "Notification Front best view: failed, attempt 1, not tried again: Bad Request: chat not found"]


def test_the_first_attempt_is_the_callers_and_the_rest_are_not(telegram, monkeypatch):
    fake = telegram(OK)
    assert notify._send_logged("Front best view", "x", None, SETTINGS) is True
    assert len(fake.posts) == 1 and Inline.started == 0


def test_every_attempt_sends_the_same_message_and_photo(telegram, tmp_path):
    photo = tmp_path / "12-00-00.best.jpg"
    photo.write_bytes(b"jpg")
    fake = telegram(requests.ReadTimeout("Read timed out."), OK)
    notify._send_logged("Front best view", "caption", str(photo), SETTINGS, silent=True)
    assert fake.posts[0] == fake.posts[1]
    assert fake.posts[0]["caption"] == "caption" and fake.posts[0]["disable_notification"] == "true"


def test_the_token_never_reaches_the_log(telegram, caplog):
    caplog.set_level("INFO", logger="jarvis.notify")
    telegram(requests.ConnectionError(f"Max retries exceeded with url: /bot{TOKEN}/sendMessage"), OK)
    notify._send_logged("Front best view", "x", None, SETTINGS)
    assert all(TOKEN not in r.getMessage() for r in caplog.records)


def test_an_error_requests_does_not_wrap_is_a_failed_attempt_not_a_crash(telegram):
    fake = telegram(OSError("[WinError 10054] connection reset"), ValueError("bad answer"), OK)
    assert notify._send_logged("Front best view", "x", None, SETTINGS) is False
    assert len(fake.posts) == 3


def test_the_test_button_tries_once(telegram):
    fake = telegram(SERVER_ERROR)
    assert notify.send("J.A.R.V.I.S.: test notification", settings=SETTINGS) == (False, "Internal Server Error")
    assert len(fake.posts) == 1 and fake.pauses == []
