"""Backlog 42: an unnamed face unseen for 60 days is forgotten; a dog that is probably a named one makes no card."""

import json
import threading
from datetime import date, datetime, timedelta

import numpy as np
import pytest

from dog_vectors import at_distance, descriptor
from jarvis import dogs, faces

TODAY = date(2026, 11, 17)


def unit(seed):
    return [1.0 if i == seed else 0.0 for i in range(8)]


def entry(gallery, seed, first_seen, name=""):
    person_id = gallery.add([unit(seed), unit(seed)], "t.jpg", [None, None])
    gallery.load()
    person = gallery.get(person_id)
    person["first_seen"] = f"{first_seen.isoformat()}T10:00:00"
    if name:
        person["name"] = name
        person.pop("temporary_name", None)
    gallery.save()
    return person_id


def sighting(folder, person_id, day, key="person_id"):
    path = folder / day.isoformat() / f"10-00-00_{person_id[-6:]}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({key: person_id, "at": f"{day.isoformat()}T10:00:00", "clip": "x.mp4"}),
                    encoding="utf-8")
    return path


@pytest.fixture
def gallery(tmp_path):
    return faces.Gallery(tmp_path / "faces" / "gallery.json")


def test_an_unnamed_face_last_seen_over_60_days_ago_is_forgotten_with_its_photos(gallery):
    old = entry(gallery, 1, TODAY - timedelta(days=90))
    kept_sighting = sighting(gallery.path.parent, old, TODAY - timedelta(days=61))
    photo = gallery.view_dir / "old.jpg"
    photo.parent.mkdir(parents=True, exist_ok=True)
    photo.write_bytes(b"jpg")
    gallery.load()
    gallery.get(old)["views"] = [faces._portable(photo), None]
    gallery.save()
    forgotten = gallery.forget_unseen(today=TODAY)
    assert [p["id"] for p in forgotten] == [old]
    assert faces.Gallery(gallery.path).get(old) is None
    assert not photo.exists() and kept_sighting.exists()
    assert gallery.label(old) == "?"


def test_a_sighting_in_the_last_60_days_keeps_an_unnamed_face(gallery):
    seen = entry(gallery, 1, TODAY - timedelta(days=200))
    sighting(gallery.path.parent, seen, TODAY - timedelta(days=59))
    assert gallery.forget_unseen(today=TODAY) == []
    assert faces.Gallery(gallery.path).get(seen) is not None


def test_a_new_unnamed_face_with_no_sighting_yet_is_kept(gallery):
    new = entry(gallery, 1, TODAY - timedelta(days=5))
    assert gallery.forget_unseen(today=TODAY) == []
    assert faces.Gallery(gallery.path).get(new) is not None


def test_a_named_face_is_never_forgotten(gallery):
    named = entry(gallery, 1, TODAY - timedelta(days=400), name="Dhaniel")
    assert gallery.forget_unseen(today=TODAY) == []
    assert faces.Gallery(gallery.path).get(named)["name"] == "Dhaniel"


def test_a_forgotten_visitors_number_is_given_again(gallery):
    entry(gallery, 1, TODAY - timedelta(days=10))
    last = entry(gallery, 2, TODAY - timedelta(days=100))
    assert faces.Gallery(gallery.path).get(last)["temporary_name"] == "Visitor 2"
    gallery.forget_unseen(today=TODAY)
    newest = gallery.add([unit(3), unit(3)], "t.jpg")
    assert faces.Gallery(gallery.path).get(newest)["temporary_name"] == "Visitor 2"


def test_the_keeper_forgets_at_once_and_then_once_a_day_until_stopped(monkeypatch):
    calls, stop = [], threading.Event()

    class Counting:
        def forget_unseen(self):
            calls.append(datetime.now())
            if len(calls) == 2:
                stop.set()
            return [{"id": "p_1", "temporary_name": "Visitor 1"}]

    waits = []
    monkeypatch.setattr(stop, "wait", lambda seconds: waits.append(seconds) or stop.is_set())
    faces.keep_gallery(stop, Counting)
    assert len(calls) == 2 and waits == [faces.KEEP_SECONDS] * 2


@pytest.fixture
def two_dogs(tmp_path):
    gallery = dogs.DogGallery(tmp_path / "gallery.json")
    dark = gallery.add([descriptor(1, True)], "a.jpg")
    light = gallery.add([descriptor(13, True)], "b.jpg")
    gallery.rename(dark, "Dark one")
    gallery.rename(light, "Light one")
    return dogs.DogGallery(gallery.path)


def test_a_crop_that_is_probably_a_named_dog_stays_a_sighting_and_makes_no_card(two_dogs, tmp_path, monkeypatch):
    probable = at_distance(13, (dogs.SURE_DISTANCE + dogs.PROBABLE_DISTANCE) / 2)
    assert dogs.match(probable, two_dogs)["certainty"] == "probable"
    monkeypatch.setattr(dogs, "describe", lambda frame, box: (probable, np.zeros((8, 8, 3), "uint8")))
    added = dogs.record(np.zeros((8, 8, 3), "uint8"), [(0, 0, 4, 4)], "Front",
                        datetime(2026, 11, 17, 10, 0, 0), tmp_path / "c.mp4", two_dogs)
    reloaded = dogs.DogGallery(two_dogs.path)
    assert added == [] and len(reloaded.people) == 2
    saved = json.loads(next((tmp_path / "2026-11-17").glob("*.json")).read_text(encoding="utf-8"))
    assert saved["dog_id"] == "" and saved["certainty"] == "probable" and saved["match"] == "Light one"
    assert dogs.current_words(saved, reloaded) == "probably Light one"
    assert next((tmp_path / "2026-11-17").glob("*.jpg")).exists()


def test_a_crop_no_named_dog_explains_still_makes_a_card(two_dogs, tmp_path, monkeypatch):
    monkeypatch.setattr(dogs, "describe", lambda frame, box: (descriptor(7, True), np.zeros((8, 8, 3), "uint8")))
    added = dogs.record(np.zeros((8, 8, 3), "uint8"), [(0, 0, 120, 120)], "Front",
                        datetime(2026, 11, 17, 10, 0, 0), tmp_path / "c.mp4", two_dogs)
    assert len(added) == 1 and len(dogs.DogGallery(two_dogs.path).people) == 3
