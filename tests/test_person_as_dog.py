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


STANDING = ([300, 80, 80, 180], 0.8, people.PERSON_CLASS)
BENDING = ([295, 150, 110, 120], 0.81, people.DOG_CLASS)
STILL_BENT = ([300, 155, 110, 118], 0.75, people.DOG_CLASS)


def test_a_moving_bend_takes_the_place_of_the_person(detector, monkeypatch):
    run(detector, monkeypatch, [STANDING], now=10.0)
    assert people.iou(BENDING[0], STANDING[0]) < people.SAME_PERSON_IOU
    found = run(detector, monkeypatch, [BENDING], now=10.3)
    assert [s.label for s in found] == ["person"]
    assert ("took the place of a person who vanished",
            people.Detection(*BENDING[0], 0.81, "dog")) in detector.trace


def test_a_long_bend_keeps_renewing_the_person(detector, monkeypatch):
    run(detector, monkeypatch, [STANDING], now=10.0)
    run(detector, monkeypatch, [BENDING], now=10.3)
    for step in range(1, 15):
        found = run(detector, monkeypatch, [STILL_BENT], now=10.3 + 0.3 * step)
        assert [s.label for s in found] == ["person"]
    assert 10.3 + 0.3 * 14 - 10.0 > people.RECENT_PERSON_SECONDS


def test_a_dog_at_the_feet_of_a_person_still_seen_stays_a_dog(detector, monkeypatch):
    dog = ([310, 170, 70, 90], 0.7, people.DOG_CLASS)
    walking = ([304, 82, 80, 180], 0.8, people.PERSON_CLASS)
    run(detector, monkeypatch, [STANDING], now=10.0)
    assert people.REPLACED_PERSON_IOU <= people.iou(dog[0], STANDING[0]) < people.SAME_PERSON_IOU
    found = run(detector, monkeypatch, [walking, dog], now=10.3)
    assert sorted(s.label for s in found) == ["dog", "person"]


def test_one_vanished_person_turns_one_dog_box(detector, monkeypatch):
    other = ([305, 175, 70, 85], 0.6, people.DOG_CLASS)
    run(detector, monkeypatch, [STANDING], now=10.0)
    found = run(detector, monkeypatch, [BENDING, other], now=10.3)
    assert sorted(s.label for s in found) == ["dog", "person"]
    assert next(s for s in found if s.is_person).confidence == 0.81


def test_a_person_gone_too_long_is_not_replaced(detector, monkeypatch):
    run(detector, monkeypatch, [STANDING], now=10.0)
    found = run(detector, monkeypatch, [BENDING], now=10.0 + people.RECENT_PERSON_SECONDS + 0.1)
    assert [s.label for s in found] == ["dog"]
