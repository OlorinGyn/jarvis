"""Who gets notified, how often, and that the bot token never leaks into a message."""

from datetime import datetime

import pytest

from jarvis import notify

TOKEN = "123456789:AAFakeTokenForTheNotifyTests_x"
SETTINGS = {"notify_token": TOKEN, "notify_chat": "1", "notify_labels": ["person"],
            "notify_cooldown": 120}
START = datetime(2026, 10, 10, 12, 0, 0)


@pytest.fixture(autouse=True)
def sent(monkeypatch):
    notify.reset_cooldown()
    messages = []

    def record(text, image=None, settings=None):
        messages.append(text)
        return True, ""

    monkeypatch.setattr(notify, "send", record)
    yield messages
    notify.reset_cooldown()


def face(person_id, name="", score=0.5):
    return {"person_id": person_id, "name": name, "score": score, "thumbnail_path": None}


def test_the_token_is_redacted_literal_and_url_encoded():
    text = f"url: /bot{TOKEN}/sendPhoto and /bot{TOKEN.replace(':', '%3A')}/x"
    redacted = notify._redact(text, TOKEN)
    assert TOKEN not in redacted and "%3A" not in redacted
    assert redacted.count("bot<token>") == 2


def test_only_wanted_labels_notify():
    assert notify._wanted(["dog", "person"], SETTINGS)
    assert not notify._wanted(["dog"], SETTINGS)
    assert notify._wanted(["dog"], {**SETTINGS, "notify_labels": ["dog"]})


def test_a_camera_is_notified_once_per_cooldown():
    assert notify.event("Front", ["person"], None, settings=SETTINGS)
    assert not notify.event("Front", ["person"], None, settings=SETTINGS)
    assert notify.event("Back", ["person"], None, settings=SETTINGS)


def test_nothing_is_sent_without_a_token():
    assert not notify.event("Front", ["person"], None, settings={**SETTINGS, "notify_token": ""})
    assert notify.faces_seen("Front", START, [face("p_1")], {**SETTINGS, "notify_token": ""}) == 0


def test_a_face_is_sent_even_when_its_event_was_in_the_cooldown(sent):
    assert notify.event("Front", ["person"], None, settings=SETTINGS)
    assert not notify.event("Front", ["person"], None, settings=SETTINGS)
    assert notify.faces_seen("Front", START, [face("p_1", "Ana", 0.6)], SETTINGS) == 1
    assert sent[-1] == "Front 12:00:00: Ana recognized"


def test_each_person_has_a_cooldown_of_their_own():
    assert notify.faces_seen("Front", START, [face("p_1"), face("p_2")], SETTINGS) == 2
    assert notify.faces_seen("Back", START, [face("p_1"), face("p_3")], SETTINGS) == 1


def test_no_face_messages_when_people_are_not_wanted():
    settings = {**SETTINGS, "notify_labels": ["dog"]}
    assert notify.faces_seen("Front", START, [face("p_1")], settings) == 0


def test_a_weak_match_is_announced_as_probable():
    assert notify._who(face("p_1", "Ana", 0.40)) == "probably Ana"
    assert notify._who(face("p_1", "Ana", 0.50)) == "Ana recognized"
    assert notify._who(face("p_1")) == "unknown face"
