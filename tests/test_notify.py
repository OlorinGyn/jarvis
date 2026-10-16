"""Who gets notified, in which mode, loud or silent, and that the bot token never leaks into a message."""

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
SEND = notify.send

EXPECTED = {
    "away": {"resident_person": True, "probable_resident_person": True, "known_person": True,
             "unknown_face": True, "faceless_person": True, "resident_dog": False,
             "probable_resident_dog": False, "other_dog": False, "other_animal": False,
             "camera_down": True},
    "home": {"resident_person": False, "probable_resident_person": False, "known_person": True,
             "unknown_face": True, "faceless_person": True, "resident_dog": False,
             "probable_resident_dog": False, "other_dog": False, "other_animal": False,
             "camera_down": True},
    "silent": {case: False for case in modes.CASES},
}


class Sent(list):
    """The texts sent, with silent beside them, one flag per message."""

    def __init__(self):
        super().__init__()
        self.silent = []


class Clock:
    """The incident's clock, moved by hand."""

    now = 1000.0


class Timer:
    """The floor's timer, fired by hand."""

    started = []

    def __init__(self, interval, function, args=()):
        self.interval, self.function, self.args = interval, function, args
        self.daemon = False

    def start(self):
        Timer.started.append(self)

    def cancel(self):
        pass

    def fire(self):
        Clock.now += self.interval
        return self.function(*self.args)


@pytest.fixture(autouse=True)
def sent(monkeypatch):
    notify.reset_incident()
    Clock.now = 1000.0
    Timer.started = []
    messages = Sent()

    def record(text, image=None, settings=None, silent=False):
        messages.append(text)
        messages.silent.append(silent)
        return True, ""

    monkeypatch.setattr(notify, "send", record)
    monkeypatch.setattr(notify.threading, "Thread", Inline)
    monkeypatch.setattr(notify.threading, "Timer", Timer)
    monkeypatch.setattr(notify, "_clock", lambda: Clock.now)
    yield messages
    notify.reset_incident()


class Inline:
    """A thread that runs at start(), so a test sees the message at once."""

    def __init__(self, target, args=(), kwargs=None, daemon=None):
        self.target, self.args, self.kwargs = target, args, kwargs or {}

    def start(self):
        self.target(*self.args, **self.kwargs)

    def join(self):
        pass


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


def test_a_second_event_in_the_same_place_goes_out_silently(sent):
    assert notify.event("Front", [("person", None)], None, SETTINGS) == (True, False)
    Clock.now += 40
    assert notify.event("Front", [("person", None)], None, SETTINGS) == (True, False)
    assert sent.silent == [False, True]


def test_another_camera_rings(sent):
    notify.event("Front", [("person", None)], None, SETTINGS)
    Clock.now += 40
    notify.event("Back", [("person", None)], None, SETTINGS)
    assert sent.silent == [False, False]


def test_more_people_at_once_than_the_incident_had_rings(sent, best):
    assert notify.after_scan("Front", START, [], True, False, None, best, HOME, people=1) == 1
    Clock.now += 40
    assert notify.after_scan("Front", START, [], True, False, None, best, HOME, people=1) == 1
    Clock.now += 40
    assert notify.after_scan("Front", START, [], True, False, None, best, HOME, people=2) == 1
    assert sent.silent == [False, True, False]


def test_the_incident_closes_after_its_quiet_window(sent):
    notify.event("Front", [("person", None)], None, SETTINGS)
    for _ in range(3):
        Clock.now += 119
        notify.event("Front", [("person", None)], None, SETTINGS)
    Clock.now += 120
    notify.event("Front", [("person", None)], None, SETTINGS)
    assert sent.silent == [False, True, True, True, False]


def test_a_loud_message_inside_the_floor_goes_out_silently_and_one_text_names_it(sent):
    notify.event("Front", [("person", None)], None, SETTINGS)
    Clock.now += 10
    notify.event("Back", [("person", None)], None, SETTINGS)
    Clock.now += 5
    notify.event("Front", [("person", None)], None, SETTINGS)
    assert sent.silent == [False, True, True] and len(Timer.started) == 1
    assert Timer.started[0].interval == 20
    assert Timer.started[0].fire()
    assert sent[-1].startswith("Back ") and sent[-1].endswith(": person — and 1 more, sent silently above")
    assert sent.silent[-1] is False
    Clock.now += 10
    notify.event("Back", [("person", None)], None, SETTINGS)
    assert sent.silent[-1] is True and len(Timer.started) == 2


def test_one_held_back_message_is_named_alone(sent):
    notify.event("Front", [("person", None)], None, SETTINGS)
    notify.event("Back", [("person", None)], None, SETTINGS)
    Timer.started[0].fire()
    assert sent[-1].endswith(": person — sent silently above")


def test_silent_asks_telegram_for_no_sound(monkeypatch):
    calls = []
    monkeypatch.setattr(notify, "_call", lambda token, method, fields, *a: (calls.append(fields), (True, ""))[1])
    SEND("x", None, SETTINGS, silent=True)
    SEND("x", None, SETTINGS)
    assert calls[0]["disable_notification"] == "true" and "disable_notification" not in calls[1]


def test_the_log_says_which(sent, caplog):
    caplog.set_level("INFO", logger="jarvis.notify")
    notify.faces_seen("Front", START, [face("p_1"), face("p_2")], SETTINGS)
    lines = [r.getMessage() for r in caplog.records]
    assert lines == ["Notification Front face, unknown face: sent",
                     "Notification Front face, unknown face: sent silently"]


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
    assert notify.person_case(face("p_1", "Ana", 0.35, resident=True)) == "probable_resident_person"
    assert notify.person_case(face("p_1", "Ana", 0.6)) == "known_person"
    assert notify.person_case(face("p_1")) == "unknown_face"


def test_in_home_a_resident_face_is_silent_and_a_probable_one_too(sent):
    found = [face("p_1", "Gustavo", 0.6, True), face("p_2", "Gustavo", 0.35, True),
             face("p_3"), face("p_4", "Ana", 0.6), face("p_5", "Ana", 0.35)]
    assert notify.faces_seen("Front", START, found, HOME) == 3
    assert sent == ["Front 12:00:00: unknown face", "Front 12:00:00: Ana recognized",
                    "Front 12:00:00: probably Ana"]


def test_silent_sends_no_face():
    assert notify.faces_seen("Front", START, [face("p_1")], {**SETTINGS, "notify_mode": "silent"}) == 0


def test_a_face_after_its_event_goes_out_silently(sent):
    assert notify.event("Front", [("person", None)], None, SETTINGS)[0]
    assert notify.event("Front", [("person", None)], None, SETTINGS)[0]
    assert notify.faces_seen("Front", START, [face("p_1", "Ana", 0.6)], SETTINGS) == 1
    assert sent[-1] == "Front 12:00:00: Ana recognized"
    assert sent.silent == [False, True, True]


def test_the_same_face_again_is_sent_not_dropped(sent):
    assert notify.faces_seen("Front", START, [face("p_1"), face("p_2")], SETTINGS) == 2
    assert notify.faces_seen("Back", START, [face("p_1"), face("p_3")], SETTINGS) == 2
    assert sent.silent == [False, True, True, True] and len(Timer.started) == 1


def test_a_weak_match_is_announced_as_probable():
    assert notify._who(face("p_1", "Ana", 0.35)) == "probably Ana"
    assert notify._who(face("p_1", "Ana", 0.50)) == "Ana recognized"
    assert notify._who(face("p_1")) == "unknown face"


@pytest.fixture
def best(tmp_path):
    path = tmp_path / "12-00-00.best.jpg"
    path.write_bytes(b"jpg")
    return path


def test_a_held_resident_sends_nothing_and_a_stranger_opens_the_incident(sent, best):
    assert notify.after_scan("Front", START, [face("p_1", "Gustavo", 0.6, True)], True, False,
                             None, best, HOME) == 0
    assert notify.after_scan("Front", START, [face("p_9")], True, False, None, best, HOME) == 1
    assert notify.event("Front", [("dog", "other_dog")], None,
                        {**HOME, "notify_modes": modes.defaults(["person", "dog"])})[0]
    assert sent.silent == [False, True]


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
    monkeypatch.setattr(dogs, "identify", lambda frame, boxes: [("Aurora", "sure")])
    return clips.EventRecorder(Camera(), tmp_path)


DOG = Detection(10, 10, 100, 80, 0.8, "dog")
PERSON = Detection(300, 50, 80, 250, 0.9, "person")


def test_a_person_arriving_mid_event_follows_the_same_rules(tmp_path, monkeypatch, sent):
    home = recorder(tmp_path / "home", monkeypatch, HOME)
    home.update(frame(), [DOG])
    home.update(frame(), [DOG, PERSON])
    assert sent == [] and home.person_held and not home.notified

    notify.reset_incident()
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


def test_a_person_hiding_beside_a_silenced_resident_reaches_the_phone(sent, best):
    resident = face("p_1", "Gustavo", 0.6, True)
    assert notify.after_scan("Front", START, [resident], True, False, None, best, HOME, people=2) == 1
    assert sent == ["Front 12:00:00: 2 people seen, 1 face found"]


def test_as_many_people_as_silenced_faces_sends_nothing(sent, best):
    found = [face("p_1", "Gustavo", 0.6, True), face("p_2", "Izabel", 0.6, True)]
    assert notify.after_scan("Front", START, found, True, False, None, best, HOME, people=2) == 0
    assert notify.after_scan("Front", START, found[:1], True, False, None, best, HOME, people=1) == 0
    assert sent == []


def test_a_face_that_reached_the_phone_accounts_for_the_scene(sent, best):
    found = [face("p_1", "Gustavo", 0.6, True), face("p_9")]
    assert notify.after_scan("Front", START, found, True, False, None, best, HOME, people=3) == 1
    assert sent == ["Front 12:00:00: unknown face"]


def test_the_hidden_person_answers_to_the_faceless_switch_and_is_never_dropped(sent, best):
    resident = [face("p_1", "Gustavo", 0.6, True)]
    off = {**HOME, "notify_modes": {"home": {"faceless_person": False}}}
    assert notify.after_scan("Front", START, resident, True, False, None, best, off, people=2) == 0
    assert notify.after_scan("Front", START, resident, True, False, None, best, HOME, people=2) == 1
    assert notify.after_scan("Front", START, resident, True, False, None, best, HOME, people=2) == 1
    assert notify.after_scan("Front", START, resident, True, True, None, best, HOME, people=2) == 1
    assert sent.silent == [False, True, True]


def test_people_are_counted_at_once_not_over_the_event(tmp_path, monkeypatch, sent):
    home = recorder(tmp_path, monkeypatch, HOME)
    other = Detection(500, 60, 70, 240, 0.8, "person")
    home.update(frame(), [PERSON])
    home.update(frame(), [PERSON, other])
    home.update(frame(), [other])
    assert home.most_people == 2


def test_a_dog_taken_for_a_person_costs_one_extra_message(tmp_path, monkeypatch, sent):
    monkeypatch.setattr(clips, "_assemble", lambda *args, **kwargs: captured.update(kwargs))
    captured = {}
    home = recorder(tmp_path, monkeypatch, HOME)
    dog_as_person = Detection(10, 200, 120, 90, 0.6, "person")
    home.update(frame(), [PERSON, dog_as_person])
    meta = home.stop()
    clips.wait_for_jobs()
    assert captured["people"] == 2 and meta["most_people"] == 2
    best = tmp_path / "12-00-00.best.jpg"
    best.write_bytes(b"jpg")
    resident = [face("p_1", "Gustavo", 0.6, True)]
    assert notify.after_scan("Front", START, resident, True, False, None, best, HOME,
                             people=captured["people"]) == 1


def test_the_hidden_person_follows_a_fake_scan(tmp_path, monkeypatch, sent, best):
    monkeypatch.setattr(notify, "load", lambda: HOME)
    monkeypatch.setattr(clips, "ASSEMBLY_DELAY", 0)
    monkeypatch.setattr(clips, "_concat", lambda segments, destination: destination.write_bytes(b"x"))
    monkeypatch.setattr(faces, "scan_clip", lambda *a, **k: [face("p_1", "Gustavo", 0.6, True)])
    clips._assemble(Camera(), START, START, tmp_path / "12-00-00.mp4", {"person"}, False,
                    best, held=True, people=2)
    assert sent == ["Front 12:00:00: 2 people seen, 1 face found"]


def test_the_frame_where_the_people_were_counted_is_kept(tmp_path, monkeypatch, sent):
    monkeypatch.setattr(clips, "_assemble", lambda *args, **kwargs: captured.update(kwargs))
    captured = {}
    home = recorder(tmp_path, monkeypatch, HOME)
    other = Detection(500, 60, 70, 240, 0.8, "person")
    tall = Detection(300, 20, 90, 400, 0.95, "person")
    home.update(frame(), [PERSON])
    home.update(frame(), [PERSON, other])
    home.update(frame(), [tall])
    meta = home.stop()
    clips.wait_for_jobs()
    people = home.base.with_name(f"{home.base.name}.people.jpg")
    assert people.is_file() and meta["people_thumbnail"] == people.name
    assert captured["people_view"] == people and captured["people"] == 2
    assert meta["best_thumbnail"] != people.name


def test_one_person_at_a_time_keeps_no_people_frame(tmp_path, monkeypatch, sent):
    monkeypatch.setattr(clips, "_assemble", lambda *args, **kwargs: captured.update(kwargs))
    captured = {}
    home = recorder(tmp_path, monkeypatch, HOME)
    home.update(frame(), [PERSON])
    meta = home.stop()
    clips.wait_for_jobs()
    assert "people_thumbnail" not in meta and captured["people_view"] is None
    assert not list(tmp_path.rglob("*.people.jpg"))


def test_the_hidden_person_message_carries_the_counted_frame(tmp_path, monkeypatch, sent, best):
    pictures = []
    monkeypatch.setattr(notify, "send", lambda text, image=None, settings=None, silent=False:
                        (pictures.append(image), (True, ""))[1])
    counted = tmp_path / "12-00-00.people.jpg"
    counted.write_bytes(b"jpg")
    resident = [face("p_1", "Gustavo", 0.6, True)]
    assert notify.after_scan("Front", START, resident, True, False, None, best, HOME,
                             people=2, people_view=counted) == 1
    assert pictures == [str(counted)]
    notify.reset_incident()
    assert notify.after_scan("Front", START, [], True, False, None, best, HOME,
                             people=2, people_view=counted) == 1
    assert pictures[-1] == str(best)


def test_a_held_faceless_person_inside_the_quiet_window_still_reaches_the_phone(sent, best):
    assert notify.after_scan("Front", START, [], True, False, None, best, HOME) == 1
    assert notify.after_scan("Front", START, [], True, False, None, best, HOME) == 1
    assert sent == ["Front 12:00:00: no face seen, best view"] * 2 and sent.silent == [False, True]
