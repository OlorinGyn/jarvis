"""The phone can switch the mode, only from the configured chat, and trouble is logged once."""

import json
import logging
import time

import pytest

from jarvis import bot, modes

TOKEN = "123456789:AAFakeTokenForTheBotTests_x"


class Telegram:
    """A fake Bot API: answers getUpdates from a queue and records every other call."""

    def __init__(self):
        self.updates = []
        self.calls = []

    def __call__(self, token, method, fields, timeout):
        self.calls.append((method, fields))
        if method == "getUpdates":
            return (self.updates.pop(0) if self.updates else {"ok": True, "result": []}), ""
        return {"ok": True, "result": True}, ""

    def sent(self, method="sendMessage"):
        return [fields for name, fields in self.calls if name == method]


@pytest.fixture
def telegram():
    return Telegram()


@pytest.fixture
def stored():
    return {"notify_token": TOKEN, "notify_chat": "42", "notify_mode": "away",
            "notify_labels": ["person"], "notify_modes": modes.defaults(["person"])}


@pytest.fixture
def poller(telegram, stored, monkeypatch):
    found = bot.Poller(call=telegram, load=lambda: dict(stored),
                       update=lambda **changes: stored.update(changes))
    monkeypatch.setattr(found.stopping, "wait", lambda seconds=None: False)
    return found


def message(chat, text, update_id=1, age=0):
    return {"update_id": update_id,
            "message": {"chat": {"id": chat}, "text": text, "date": int(time.time()) - age}}


def arrive(telegram, *updates):
    telegram.updates.append({"ok": True, "result": list(updates)})


def test_a_command_from_the_configured_chat_switches_the_mode(poller, telegram, stored):
    arrive(telegram, message(42, "/home"))
    poller.poll_once()
    assert stored["notify_mode"] == "home"
    assert telegram.sent()[-1]["text"].startswith("Mode set. Home: sends")
    assert poller.offset == 2


def test_another_chat_is_ignored_and_logged(poller, telegram, stored, caplog):
    arrive(telegram, message(99, "/silent"))
    with caplog.at_level(logging.INFO, logger="jarvis.bot"):
        poller.poll_once()
    assert stored["notify_mode"] == "away"
    assert telegram.sent() == []
    assert "ignored a message from chat 99" in caplog.text


def test_a_tap_from_another_chat_changes_nothing(poller, telegram, stored):
    arrive(telegram, {"update_id": 5, "callback_query": {"id": "c1", "data": "mode:silent",
                                                         "message": {"chat": {"id": 7}}}})
    poller.poll_once()
    assert stored["notify_mode"] == "away"


def test_mode_shows_the_current_one_with_tap_buttons(poller, telegram):
    arrive(telegram, message(42, "/mode@jarvis_bot"))
    poller.poll_once()
    answer = telegram.sent()[-1]
    assert answer["text"].startswith("Current mode: Away")
    buttons = json.loads(answer["reply_markup"])["inline_keyboard"][0]
    assert [b["callback_data"] for b in buttons] == ["mode:home", "mode:away", "mode:silent"]


def test_a_tap_switches_the_mode(poller, telegram, stored):
    arrive(telegram, {"update_id": 5, "callback_query": {"id": "c1", "data": "mode:silent",
                                                         "message": {"chat": {"id": 42}}}})
    poller.poll_once()
    assert stored["notify_mode"] == "silent"
    assert telegram.sent("answerCallbackQuery")[-1]["text"] == "Silent is on"


def test_an_old_command_waiting_since_yesterday_is_not_obeyed(poller, telegram, stored):
    arrive(telegram, message(42, "/silent", age=bot.STALE_SECONDS + 60))
    poller.poll_once()
    assert stored["notify_mode"] == "away"


def test_anything_else_gets_the_help_and_plain_text_nothing(poller, telegram):
    arrive(telegram, message(42, "/start", 1), message(42, "hello", 2))
    poller.poll_once()
    assert [s["text"] for s in telegram.sent()] == [f"{bot.HELP} Analysis: On."]


def test_the_commands_are_listed_once_per_token(poller, telegram):
    poller.poll_once()
    poller.poll_once()
    assert len(telegram.sent("setMyCommands")) == 1


def test_find_chat_reads_what_the_poller_saw(poller, telegram, stored):
    stored["notify_chat"] = ""
    arrive(telegram, message(77, "hi"))
    poller.poll_once()
    assert poller.last_chat() == "77"


def test_a_second_reader_is_logged_once_and_backed_off(poller, telegram, caplog):
    waits = []
    poller.stopping.wait = lambda seconds=None: waits.append(seconds)
    conflict = {"ok": False, "error_code": 409, "description": "Conflict: terminated by other getUpdates request"}
    telegram.updates += [conflict, conflict]
    with caplog.at_level(logging.WARNING, logger="jarvis.bot"):
        poller.poll_once()
        poller.poll_once()
    assert caplog.text.count("409") == 1
    assert waits == [bot.CONFLICT_BACKOFF, bot.CONFLICT_BACKOFF]


def test_network_trouble_never_shows_the_token(poller, caplog, monkeypatch):
    def failing(token, method, fields, timeout):
        return None, bot._redact(f"connection to /bot{TOKEN}/getUpdates failed", token)

    poller.call = failing
    with caplog.at_level(logging.WARNING, logger="jarvis.bot"):
        poller.poll_once()
        poller.poll_once()
    assert TOKEN not in caplog.text
    assert caplog.text.count("network") == 1
    assert poller.backoff == bot.FIRST_BACKOFF * 4


def test_without_a_token_nothing_is_asked(poller, telegram, stored):
    stored["notify_token"] = ""
    poller.poll_once()
    assert telegram.calls == []
