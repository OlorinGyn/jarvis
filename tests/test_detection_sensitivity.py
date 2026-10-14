"""Backlog 31: YOLO's minimum confidence per label, set in Settings and read without a restart."""

import json

import numpy as np
import pytest
from fastapi.testclient import TestClient

from jarvis import people, settings, web

HEADER = {"X-Jarvis-Request": "1"}
FRAME = np.zeros((360, 640, 3), np.uint8)
MOTION = [(0, 0, 640, 360)]
WEAK_PERSON = ([40, 100, 80, 200], 0.30, people.PERSON_CLASS)
PERSON = ([200, 100, 80, 200], 0.40, people.PERSON_CLASS)
DOG = ([400, 250, 90, 60], 0.50, people.DOG_CLASS)
CAT = ([520, 250, 60, 50], 0.50, 15)


@pytest.fixture(autouse=True)
def config(tmp_path, monkeypatch):
    path = tmp_path / "config.json"
    monkeypatch.setattr(settings, "FILE", path)
    return path


@pytest.fixture
def client():
    return TestClient(web.app, client=("127.0.0.1", 50000))


@pytest.fixture
def network(monkeypatch):
    """A fake YOLO that returns the given boxes at or above the floor the detector asks for."""
    calls = []

    def raw(net, frame, floor):
        calls.append(floor)
        return [d for d in [WEAK_PERSON, PERSON, DOG, CAT] if d[1] >= floor]

    monkeypatch.setattr(people, "load_model", lambda: None)
    monkeypatch.setattr(people, "_raw_detections", raw)
    return calls


def labels(found):
    return sorted((d.label, d.confidence) for d in found)


def test_an_older_config_keeps_todays_values(config):
    config.write_text(json.dumps({"notify_labels": ["person"]}), encoding="utf-8")
    values = settings.load()
    assert (values["confidence_person"], values["confidence_dog"], values["confidence_animal"]) == (0.35, 0.45, 0.45)
    assert people.minimum_confidences(values)[people.PERSON_CLASS] == people.CONFIDENCE
    assert people.minimum_confidences(values)[15] == people.ANIMAL_CONFIDENCE


def test_a_stored_value_is_read(config):
    config.write_text(json.dumps({"confidence_dog": 0.6}), encoding="utf-8")
    assert settings.load()["confidence_dog"] == 0.6


@pytest.mark.parametrize("bad", [0.05, 0.95, "0.5", True, None])
def test_a_stored_value_out_of_range_falls_back_to_the_default(config, bad):
    config.write_text(json.dumps({"confidence_person": bad}), encoding="utf-8")
    assert settings.load()["confidence_person"] == 0.35


def test_the_defaults_detect_as_before(config, network):
    found = people.SubjectDetector().detect(FRAME, MOTION, now=1.0)
    assert labels(found) == [("cat", 0.5), ("dog", 0.5), ("person", 0.4)]
    assert network == [0.35]


def test_each_label_has_its_own_minimum(config, network):
    config.write_text(json.dumps({"confidence_person": 0.25, "confidence_dog": 0.6,
                                  "confidence_animal": 0.45}), encoding="utf-8")
    detector = people.SubjectDetector()
    detector.trace = []
    found = detector.detect(FRAME, MOTION, now=1.0)
    assert labels(found) == [("cat", 0.5), ("person", 0.3), ("person", 0.4)]
    assert network == [0.25]
    assert [(reason, d.label) for reason, d in detector.trace] == [("animal below confidence", "dog")]


def test_a_change_reaches_the_running_detector(config, network, monkeypatch, client):
    monkeypatch.setattr(people, "SETTINGS_REFRESH_SECONDS", 0.0)
    detector = people.SubjectDetector()
    assert labels(detector.detect(FRAME, MOTION, now=1.0)) == [("cat", 0.5), ("dog", 0.5), ("person", 0.4)]
    answer = client.post("/api/settings", headers=HEADER,
                         json={"confidence_person": 0.5, "confidence_animal": 0.55})
    assert answer.status_code == 200
    assert labels(detector.detect(FRAME, MOTION, now=2.0)) == [("dog", 0.5)]


def test_the_detector_rereads_only_now_and_then(config, network):
    detector = people.SubjectDetector()
    detector.detect(FRAME, MOTION, now=1.0)
    config.write_text(json.dumps({"confidence_dog": 0.9}), encoding="utf-8")
    assert ("dog", 0.5) in labels(detector.detect(FRAME, MOTION, now=2.0))


def test_the_page_gets_the_values_and_the_range(client):
    values = client.get("/api/settings").json()
    assert values["confidence_person"] == 0.35 and values["confidence_dog"] == 0.45
    assert values["confidence_range"] == list(settings.CONFIDENCE_RANGE)
    assert values["confidence_defaults"] == {"confidence_person": 0.35, "confidence_dog": 0.45,
                                             "confidence_animal": 0.45}


@pytest.mark.parametrize("bad", [0.1, 0.95, "0.5", True, None])
def test_the_page_cannot_store_a_value_out_of_range(client, config, bad):
    answer = client.post("/api/settings", headers=HEADER, json={"confidence_dog": bad})
    assert answer.status_code == 400
    assert not config.exists()


def test_the_page_stores_a_value_rounded(client, config):
    answer = client.post("/api/settings", headers=HEADER, json={"confidence_dog": 0.6000000001})
    assert answer.status_code == 200
    assert json.loads(config.read_text(encoding="utf-8"))["confidence_dog"] == 0.6
