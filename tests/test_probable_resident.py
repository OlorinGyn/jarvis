"""Backlog 30: a probable match to a resident has its own case, off in Home and Silent."""

import json

import numpy as np
import pytest

from jarvis import clips, dogs, modes, notify, settings
from jarvis.geometry import Detection

FRAME = np.zeros((360, 640, 3), np.uint8)
DOG = Detection(10, 10, 100, 80, 0.8, "dog")


@pytest.mark.parametrize("case", modes.PROBABLE_RESIDENT_CASES)
def test_on_in_away_off_in_home_and_silent(case):
    switches = modes.defaults(["person", "dog"])
    assert switches["away"][case] and not switches["home"][case] and not switches["silent"][case]


def test_a_config_written_before_the_new_cases_gets_their_defaults(tmp_path, monkeypatch):
    older = {mode: {case: on for case, on in switches.items()
                    if case not in modes.PROBABLE_RESIDENT_CASES}
             for mode, switches in modes.defaults(["person", "dog"]).items()}
    older["home"]["known_person"] = False
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"notify_labels": ["person", "dog"], "notify_mode": "home",
                                "notify_modes": older}), encoding="utf-8")
    monkeypatch.setattr(settings, "FILE", path)
    stored = settings.load()["notify_modes"]
    assert stored["home"]["known_person"] is False
    assert stored["home"]["probable_resident_person"] is False
    assert stored["away"]["probable_resident_dog"] is True


def test_the_switch_undoes_the_default():
    switches = modes.defaults(["person"])
    switches["home"]["probable_resident_person"] = True
    values = {"notify_mode": "home", "notify_labels": ["person"], "notify_modes": switches}
    assert modes.allowed("probable_resident_person", values)


def test_a_probable_non_resident_stays_a_known_person():
    sighting = {"name": "Ana", "score": 0.40, "resident": False}
    assert notify.person_case(sighting) == "known_person"


@pytest.mark.parametrize("certainty, case", [("sure", "resident_dog"),
                                             ("probable", "probable_resident_dog"),
                                             (None, "other_dog")])
def test_each_dog_certainty_has_its_case(monkeypatch, certainty, case):
    monkeypatch.setattr(dogs, "identify", lambda frame, boxes: [("Aurora", certainty)])
    assert clips._message_parts(FRAME, [DOG], {"dog"}) == [("Aurora", case)]


class Gallery:
    def __init__(self, resident):
        self.people = [{"id": "d_1", "name": "Aurora", "resident": resident, "embeddings": []}]

    def get(self, dog_id):
        return next((d for d in self.people if d["id"] == dog_id), None)


@pytest.mark.parametrize("certainty, resident, expected", [
    ("sure", True, ("Aurora", "sure")),
    ("probable", True, ("probably Aurora", "probable")),
    ("probable", False, ("probably Aurora", None)),
    (None, True, ("unidentified dog", None)),
])
def test_identify_says_how_sure_a_resident_dog_is(monkeypatch, certainty, resident, expected):
    monkeypatch.setattr(dogs, "describe", lambda frame, box: (None,))
    monkeypatch.setattr(dogs, "match", lambda descriptor, gallery: {
        "dog_id": "d_1" if certainty else None, "name": "Aurora" if certainty else "",
        "certainty": certainty, "distance": 0.3})
    assert dogs.identify(FRAME, [(10, 10, 100, 80)], Gallery(resident)) == [expected]
