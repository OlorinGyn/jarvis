"""R44: a person bending over, called a dog by YOLO, stays a person."""

import numpy as np
import pytest

from jarvis import people

FRAME = np.zeros((360, 640, 3), np.uint8)
MOTION = [(0, 0, 640, 360)]
PERSON = ([300, 100, 80, 200], 0.8, people.PERSON_CLASS)
BENT = ([302, 150, 80, 150], 0.74, people.DOG_CLASS)
AT_THE_FEET = ([330, 260, 50, 40], 0.7, people.DOG_CLASS)


@pytest.fixture
def detector(monkeypatch):
    monkeypatch.setattr(people, "load_model", lambda: None)
    detector = people.SubjectDetector()
    detector.trace = []
    return detector


def run(detector, monkeypatch, raw, now):
    monkeypatch.setattr(people, "_raw_detections", lambda net, frame: raw)
    return detector.detect(FRAME, MOTION, now=now)


def test_a_dog_box_where_a_person_just_stood_becomes_a_person(detector, monkeypatch):
    run(detector, monkeypatch, [PERSON], now=10.0)
    found = run(detector, monkeypatch, [BENT, AT_THE_FEET], now=11.0)
    assert sorted(s.label for s in found) == ["dog", "person"]
    person = next(s for s in found if s.is_person)
    assert tuple(person[:4]) == tuple(BENT[0])
    assert ("the person's box from a moment ago", people.Detection(*BENT[0], 0.74, "dog")) in detector.trace


def test_the_person_must_be_recent(detector, monkeypatch):
    run(detector, monkeypatch, [PERSON], now=10.0)
    found = run(detector, monkeypatch, [BENT], now=10.0 + people.RECENT_PERSON_SECONDS + 0.5)
    assert [s.label for s in found] == ["dog"]


def test_a_dog_with_no_person_before_stays_a_dog(detector, monkeypatch):
    found = run(detector, monkeypatch, [BENT], now=10.0)
    assert [s.label for s in found] == ["dog"]


def test_a_relabelled_box_meets_the_person_rules(detector, monkeypatch):
    short_person = ([300, 300, 80, 50], 0.8, people.PERSON_CLASS)
    short_dog = ([300, 302, 80, 50], 0.7, people.DOG_CLASS)
    run(detector, monkeypatch, [short_person], now=10.0)
    assert run(detector, monkeypatch, [short_dog], now=10.5) == []
