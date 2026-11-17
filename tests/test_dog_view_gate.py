"""Backlog 45 step 3 for dogs: a crop whose box is under MIN_VIEW_BOX px stores no view; the messages do not change."""

import json
from datetime import datetime

import numpy as np
import pytest

from dog_vectors import at_distance, descriptor
from jarvis import dogs, settings

START = datetime(2026, 11, 17, 10, 0, 0)
FRAME = np.zeros((540, 960, 3), np.uint8)
CROP = np.zeros((8, 8, 3), np.uint8)
SMALL = (100, 100, 119, 80)
LARGE = (100, 100, 80, 120)


@pytest.fixture(autouse=True)
def config(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "FILE", tmp_path / "config.json")


@pytest.fixture
def aurora(tmp_path):
    gallery = dogs.DogGallery(tmp_path / "gallery.json")
    gallery.people = [{"id": "d_aaaaaaaa", "name": "Aurora", "resident": True, "embeddings": [descriptor(10)]}]
    gallery.save()
    return gallery


def record(gallery, tmp_path, monkeypatch, vector, box):
    monkeypatch.setattr(dogs, "describe", lambda frame, box: (vector, CROP))
    added = dogs.record(FRAME, [box], "Back", START, tmp_path / "clips" / "Back" / "2026-11-17" / "10-00-00.mp4",
                        gallery)
    [path] = (gallery.path.parent / "2026-11-17").glob("*.json")
    saved = json.loads(path.read_text(encoding="utf-8"))
    path.unlink()
    return added, saved, dogs.DogGallery(gallery.path)


def test_the_cut_is_the_measured_box():
    assert dogs.MIN_VIEW_BOX == 120


def test_a_sure_match_with_a_small_box_is_named_and_stores_no_view(aurora, tmp_path, monkeypatch):
    added, saved, reloaded = record(aurora, tmp_path, monkeypatch, at_distance(10, 0.05), SMALL)
    assert added == ["d_aaaaaaaa"] and saved["dog_id"] == "d_aaaaaaaa" and saved["words"] == "Aurora"
    assert saved["certainty"] == "sure"
    assert len(reloaded.get("d_aaaaaaaa")["embeddings"]) == 1
    added, saved, reloaded = record(aurora, tmp_path, monkeypatch, at_distance(10, 0.05), LARGE)
    assert len(reloaded.get("d_aaaaaaaa")["embeddings"]) == 2


def test_an_unmatched_small_crop_is_a_sighting_of_no_dog_and_makes_no_card(aurora, tmp_path, monkeypatch):
    added, saved, reloaded = record(aurora, tmp_path, monkeypatch, descriptor(3), SMALL)
    assert added == [] and saved["dog_id"] == "" and saved["certainty"] == ""
    assert saved["words"] == "unidentified dog" == dogs.current_words(saved, reloaded)
    assert len(reloaded.people) == 1
    assert not list((tmp_path / "views").glob("*.jpg"))
    added, saved, reloaded = record(aurora, tmp_path, monkeypatch, descriptor(3), LARGE)
    assert len(added) == 1 and len(reloaded.people) == 2


def test_a_probable_small_crop_still_says_probably(aurora, tmp_path, monkeypatch):
    probable = at_distance(10, (dogs.SURE_DISTANCE + dogs.PROBABLE_DISTANCE) / 2)
    added, saved, reloaded = record(aurora, tmp_path, monkeypatch, probable, SMALL)
    assert added == [] and saved["dog_id"] == "" and saved["certainty"] == "probable"
    assert dogs.current_words(saved, reloaded) == "probably Aurora"


def test_the_first_message_does_not_read_the_box(aurora, monkeypatch):
    monkeypatch.setattr(dogs, "describe", lambda frame, box, network=None: (at_distance(10, 0.05), None))
    assert dogs.identify(FRAME, [SMALL], aurora) == [("Aurora", "sure")]
