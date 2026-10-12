"""Who gets notified, in which mode, how often, and that the bot token never leaks into a message."""

import json
from datetime import datetime

import numpy as np
import pytest

from jarvis import clips, dogs, faces, modes, notify, settings
from jarvis.geometry import Detection

TOKEN = "123456789:AAFakeTokenForTheNotifyTests_x"
SETTINGS = {"notify_token": TOKEN, "notify_chat": "1", "notify_labels": ["person"],
            "notify_cooldown": 120, "notify_mode": "away"}
HOME = {**SETTINGS, "notify_mode": "home"}
START = datetime(2026, 10, 10, 12, 0, 0)

EXPECTED = {
    "away": {"resident_person": True, "known_person": True, "unknown_face": True,
             "faceless_person": True, "resident_dog": False, "other_dog": False,
             "other_animal": False},
    "home": {"resident_person": False, "known_person": True, "unknown_face": True,
             "faceless_person": True, "resident_dog": False, "other_dog": False,
             "other_animal": False},
    "silent": {case: False for case in modes.CASES},
}


@pytest.fixture(autouse=True)
def sent(monkeypatch):
    notify.reset_cooldown()
    messages = []

    def record(text, image=None, settings=None):
        messages.append(text)
        return True, ""

    monkeypatch.setattr(notify, "send", record)
    monkeypatch.setattr(notify.threading, "Thread", Inline)
    yield messages
    notify.reset_cooldown()


class Inline:
    """A thread that runs at start(), so a test sees the message at once."""

    def __init__(self, target, args=(), daemon=None):
        self.target, self.args = target, args

    def start(self):
        self.target(*self.args)


def face(person_id, name="", score=0.5, resident=False):
    return {"person_id": person_id, "name": name, "score": score, "thumbnail_path": None,
            "resident": resident}


def test_the_token_is_redacted_literal_and_url_encoded():
    text = f"url: /bot{TOKEN}/sendPhoto and /bot{TOKEN.replace(':', '%3A')}/x"
    redacted = notify._redact(text, TOKEN)
    assert TOKEN not in redacted and "%3A" not in redacted
    assert redacted.count("bot<token>") == 2


@pytest.mark.parametrize("mode", modes.MODES)
@pytest.mark.parametrize("case", modes.CASES)
def test_the_rules_matrix_each_case_in_each_mode(mode, case):
    assert modes.allowed(case, {**SETTINGS, "notify_mode": mode}) is EXPECTED[mode][case]


def test_animal_switches_start_from_the_older_labels():
    with_dogs = modes.defaults(["person", "dog"])
    assert with_dogs["away"]["other_dog"] and with_dogs["away"]["resident_dog"]
    assert with_dogs["home"]["other_dog"] and not with_dogs["home"]["resident_dog"]
    assert not with_dogs["away"]["other_animal"]
    assert modes.defaults(["person", "cat"])["away"]["other_animal"]


def test_an_older_config_gets_the_defaults_and_keeps_its_labels(tmp_path, monkeypatch):
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"notify_labels": ["person", "dog"], "notify_cooldown": 60}),
                    encoding="utf-8")
    monkeypatch.setattr(settings, "FILE", path)
    values = settings.load()
    assert values["notify_mode"] == "away"
    assert values["notify_modes"] == modes.defaults(["person", "dog"])
    settings.update(notify_mode="home")
    stored = json.loads(path.read_text(encoding="utf-8"))
    assert stored["notify_labels"] == ["person", "dog"] and stored["notify_mode"] == "home"


def test_stored_switches_are_made_whole_and_unknown_values_dropped():
    stored = {"home": {"unknown_face": False, "other_dog": "yes", "nonsense": True}, "party": {}}
    result = modes.normalised(stored, ["person"])
    assert result["home"]["unknown_face"] is False
    assert result["home"]["other_dog"] is False
    assert set(result) == set(modes.MODES) and set(result["home"]) == set(modes.CASES)
    assert modes.mode_of({"notify_mode": "party"}) == "away"


def test_a_camera_is_notified_once_per_cooldown():
    assert notify.event("Front", [("person", None)], None, SETTINGS) == (True, False)
    assert notify.event("Front", [("person", None)], None, SETTINGS) == (False, False)
    assert notify.event("Back", [("person", None)], None, SETTINGS) == (True, False)


def test_nothing_is_sent_without_a_token():
    assert notify.event("Front", [("person", None)], None, {**SETTINGS, "notify_token": ""}) == (False, False)
    assert notify.faces_seen("Front", START, [face("p_1")], {**SETTINGS, "notify_token": ""}) == 0


def test_in_home_a_person_is_held_for_the_scan(sent):
    assert notify.event("Front", [("person", None)], None, HOME) == (False, True)
    assert sent == []


def test_in_home_a_resident_dog_is_silent_and_another_dog_is_sent(sent):
    switches = modes.defaults(["person", "dog"])
    home = {**HOME, "notify_modes": switches}
    assert notify.event("Front", [("Aurora", "resident_dog")], None, home) == (False, False)
    assert notify.event("Front", [("person", None), ("Aurora", "resident_dog"),
                                  ("unidentified dog", "other_dog")], None, home) == (True, True)
    assert sent[-1].startswith("Front: unidentified dog\n")


def test_away_names_the_person_at_once(sent):
    assert notify.event("Front", [("person", None), ("Aurora", "resident_dog")], None,
                        {**SETTINGS, "notify_modes": modes.defaults(["person", "dog"])}) == (True, False)
    assert sent[-1].startswith("Front: person, Aurora\n")


def test_only_a_sure_resident_is_the_resident_case():
    assert notify.person_case(face("p_1", "Ana", 0.6, resident=True)) == "resident_person"
    assert notify.person_case(face("p_1", "Ana", 0.40, resident=True)) == "known_person"
    assert notify.person_case(face("p_1", "Ana", 0.6)) == "known_person"
    assert notify.person_case(face("p_1")) == "unknown_face"


def test_in_home_a_resident_face_is_silent_and_a_probable_one_is_not(sent):
    found = [face("p_1", "Gustavo", 0.6, True), face("p_2", "Gustavo", 0.40, True),
             face("p_3"), face("p_4", "Ana", 0.6)]
    assert notify.faces_seen("Front", START, found, HOME) == 3
    assert sent == ["Front 12:00:00: probably Gustavo", "Front 12:00:00: unknown face",
                    "Front 12:00:00: Ana recognized"]


def test_silent_sends_no_face():
    assert notify.faces_seen("Front", START, [face("p_1")], {**SETTINGS, "notify_mode": "silent"}) == 0


def test_a_face_is_sent_even_when_its_event_was_in_the_cooldown(sent):
    assert notify.event("Front", [("person", None)], None, SETTINGS)[0]
    assert not notify.event("Front", [("person", None)], None, SETTINGS)[0]
    assert notify.faces_seen("Front", START, [face("p_1", "Ana", 0.6)], SETTINGS) == 1
    assert sent[-1] == "Front 12:00:00: Ana recognized"


def test_each_person_has_a_cooldown_of_their_own():
    assert notify.faces_seen("Front", START, [face("p_1"), face("p_2")], SETTINGS) == 2
    assert notify.faces_seen("Back", START, [face("p_1"), face("p_3")], SETTINGS) == 1


def test_a_weak_match_is_announced_as_probable():
    assert notify._who(face("p_1", "Ana", 0.40)) == "probably Ana"
    assert notify._who(face("p_1", "Ana", 0.50)) == "Ana recognized"
    assert notify._who(face("p_1")) == "unknown face"


@pytest.fixture
def best(tmp_path):
    path = tmp_path / "12-00-00.best.jpg"
    path.write_bytes(b"jpg")
    return path


def test_a_held_person_with_no_face_is_sent_once_per_camera_cooldown(sent, best):
    assert notify.after_scan("Front", START, [], True, False, None, best, HOME) == 1
    assert sent == ["Front 12:00:00: no face seen, best view"]
    assert notify.after_scan("Front", START, [], True, False, None, best, HOME) == 0


def test_a_held_resident_sends_nothing_and_a_stranger_claims_the_camera(sent, best):
    assert notify.after_scan("Front", START, [face("p_1", "Gustavo", 0.6, True)], True, False,
                             None, best, HOME) == 0
    assert notify.after_scan("Front", START, [face("p_9")], True, False, None, best, HOME) == 1
    assert not notify.event("Front", [("dog", "other_dog")], None,
                            {**HOME, "notify_modes": modes.defaults(["person", "dog"])})[0]


def test_a_held_person_with_no_face_is_sent_after_the_dog_message_of_the_same_event(sent, best):
    home = {**HOME, "notify_modes": modes.defaults(["person", "dog"])}
    assert notify.event("Front", [("person", None), ("unidentified dog", "other_dog")], None,
                        home) == (True, True)
    assert notify.after_scan("Front", START, [], True, True, None, best, home) == 1
    assert sent[-1] == "Front 12:00:00: no face seen, best view"


def test_without_a_hold_the_best_view_only_follows_a_sent_event(sent, best):
    assert notify.after_scan("Front", START, [], False, False, None, best, SETTINGS) == 0
    assert notify.after_scan("Front", START, [], False, True, None, best, SETTINGS) == 1


class Camera:
    label = "Front"

    def covering(self, start, end):
        return ["20261010-120000.mp4"]


def test_the_held_person_message_follows_a_fake_scan(tmp_path, monkeypatch, sent):
    monkeypatch.setattr(notify, "load", lambda: HOME)
    monkeypatch.setattr(clips, "ASSEMBLY_DELAY", 0)
    monkeypatch.setattr(clips, "_concat", lambda segments, destination: destination.write_bytes(b"x"))
    monkeypatch.setattr(faces, "scan_clip", lambda *a, **k: [face("p_1", "Gustavo", 0.6, True),
                                                             face("p_2", "Ana", 0.6)])
    clips._assemble(Camera(), START, START, tmp_path / "12-00-00.mp4", {"person"}, False,
                    tmp_path / "12-00-00.best.jpg", held=True)
    assert sent == ["Front 12:00:00: Ana recognized"]


class NoSegments(Camera):
    def covering(self, start, end):
        return []


def test_a_held_person_whose_clip_was_not_assembled_still_gets_the_best_view(tmp_path, monkeypatch,
                                                                            sent, best):
    monkeypatch.setattr(notify, "load", lambda: HOME)
    monkeypatch.setattr(clips, "ASSEMBLY_DELAY", 0)
    clips._assemble(NoSegments(), START, START, tmp_path / "12-00-00.mp4", {"person"}, False,
                    best, held=True)
    assert sent == ["Front 12:00:00: no face seen, best view"]


def frame():
    return np.zeros((360, 640, 3), np.uint8)


def recorder(tmp_path, monkeypatch, values):
    monkeypatch.setattr(notify, "load", lambda: values)
    monkeypatch.setattr(dogs, "identify", lambda frame, boxes: [("Aurora", True)])
    return clips.EventRecorder(Camera(), tmp_path)


DOG = Detection(10, 10, 100, 80, 0.8, "dog")
PERSON = Detection(300, 50, 80, 250, 0.9, "person")


def test_a_person_arriving_mid_event_follows_the_same_rules(tmp_path, monkeypatch, sent):
    home = recorder(tmp_path / "home", monkeypatch, HOME)
    home.update(frame(), [DOG])
    home.update(frame(), [DOG, PERSON])
    assert sent == [] and home.person_held and not home.notified

    notify.reset_cooldown()
    away = recorder(tmp_path / "away", monkeypatch, SETTINGS)
    away.update(frame(), [DOG])
    assert sent == []
    away.update(frame(), [DOG, PERSON])
    assert sent[-1].startswith("Front: person\n") and not away.person_held


def test_a_person_after_a_sent_dog_message_is_still_held(tmp_path, monkeypatch, sent):
    values = {**HOME, "notify_modes": {"home": {"resident_dog": True}}}
    home = recorder(tmp_path, monkeypatch, values)
    home.update(frame(), [DOG])
    assert home.notified and sent[-1].startswith("Front: Aurora\n")
    home.update(frame(), [DOG, PERSON])
    assert home.person_held
