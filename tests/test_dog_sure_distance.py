"""Backlog 32 for dogs: the sure distance set in Settings from accuracy measured by leave-one-event-out."""

import json
import math
from datetime import datetime

import numpy as np
import pytest
from fastapi.testclient import TestClient

from dog_vectors import at_distance, descriptor
from jarvis import dogs, settings, web

HEADER = {"X-Jarvis-Request": "1"}
FRAME = np.zeros((200, 200, 3), np.uint8)


@pytest.fixture(autouse=True)
def config(tmp_path, monkeypatch):
    path = tmp_path / "config.json"
    monkeypatch.setattr(settings, "FILE", path)
    return path


@pytest.fixture
def gallery(tmp_path):
    return dogs.DogGallery(tmp_path / "gallery.json")


def choose(config, value):
    config.write_text(json.dumps({"dog_sure_distance": value}), encoding="utf-8")


def test_without_a_choice_the_sure_distance_is_todays(config):
    assert settings.load()["dog_sure_distance"] == dogs.SURE_DISTANCE == 0.33
    assert dogs.sure_distance() == dogs.SURE_DISTANCE
    choose(config, 0.5)
    assert dogs.sure_distance() == dogs.SURE_DISTANCE
    choose(config, "near")
    assert dogs.sure_distance() == dogs.SURE_DISTANCE
    choose(config, 0.25)
    assert dogs.sure_distance() == 0.25


def test_the_range_ends_at_the_probable_distance():
    assert settings.DOG_SURE_RANGE[1] == dogs.PROBABLE_DISTANCE
    assert dogs.SURE_SWEEP[0] == settings.DOG_SURE_RANGE[0] and dogs.SURE_SWEEP[-1] == dogs.PROBABLE_DISTANCE


def test_the_first_message_follows_the_chosen_distance(gallery, config, monkeypatch):
    gallery.people = [{"id": "d_aaaaaaaa", "name": "Aurora", "resident": True, "embeddings": [descriptor(10)]}]
    monkeypatch.setattr(dogs, "describe", lambda frame, box, network=None: (at_distance(10, 0.30), None))
    assert dogs.identify(FRAME, [(10, 10, 50, 50)], gallery) == [("Aurora", "sure")]
    choose(config, 0.25)
    assert dogs.identify(FRAME, [(10, 10, 50, 50)], gallery) == [("probably Aurora", "probable")]


def test_record_learns_a_view_only_within_the_chosen_distance(gallery, config, monkeypatch):
    gallery.people = [{"id": "d_aaaaaaaa", "name": "Aurora", "embeddings": [descriptor(10)]}]
    gallery.save()
    crop = np.zeros((20, 20, 3), np.uint8)
    monkeypatch.setattr(dogs, "describe", lambda frame, box, network=None: (at_distance(10, 0.30), crop))
    started = datetime(2026, 10, 15, 9, 0, 0)
    choose(config, 0.25)
    assert dogs.record(FRAME, [(10, 10, 50, 50)], "Back", started, "clips/Back/2026-10-15/09-00-00.mp4",
                       gallery) != ["d_aaaaaaaa"]
    choose(config, 0.31)
    assert dogs.record(FRAME, [(10, 10, 50, 50)], "Back", started, "clips/Back/2026-10-15/09-00-00.mp4",
                       gallery) == ["d_aaaaaaaa"]
    assert len(dogs.DogGallery(gallery.path).get("d_aaaaaaaa")["embeddings"]) == 2


def test_naming_gathers_only_crops_within_the_chosen_distance(gallery, config):
    gallery.people = [{"id": "d_aaaaaaaa", "name": "Aurora", "embeddings": [descriptor(10)]},
                      {"id": "d_bbbbbbbb", "name": "", "embeddings": [at_distance(10, 0.30)]}]
    gallery.save()
    choose(config, 0.25)
    assert gallery.rename("d_aaaaaaaa", "Aurora") == 0
    choose(config, 0.31)
    assert gallery.rename("d_aaaaaaaa", "Aurora") == 1


def test_guess_reads_the_chosen_distance_once(gallery, config, monkeypatch):
    gallery.people = [{"id": "d_aaaaaaaa", "name": "Aurora", "embeddings": [descriptor(10)]},
                      {"id": "d_bbbbbbbb", "name": "", "embeddings": [at_distance(10, 0.30)] * 3}]
    reads = []
    monkeypatch.setattr(dogs, "sure_distance", lambda values=None: reads.append(1) or 0.33)
    assert gallery.guess(gallery.get("d_bbbbbbbb")) == "d_aaaaaaaa"
    assert len(reads) == 1


@pytest.fixture
def measured(gallery):
    away = descriptor(10, True, -math.acos(1.0 - 0.22))
    gallery.people = [
        {"id": "d_a", "name": "Aurora", "views": ["a1.jpg", "a2.jpg", "a3.jpg"],
         "embeddings": [descriptor(10), at_distance(10, 0.25), descriptor(10, infrared=False)],
         "view_events": {"a1.jpg": "Back/2026-10-15/09-00-00", "a2.jpg": "Back/2026-10-15/10-00-00"}},
        {"id": "d_b", "name": "Bolt", "views": ["b1.jpg", "b2.jpg"],
         "embeddings": [descriptor(20), at_distance(20, 0.1)],
         "view_events": {"b1.jpg": "Back/2026-10-15/11-00-00", "b2.jpg": "Back/2026-10-15/11-00-00"}},
        {"id": "d_c", "name": "", "views": ["c1.jpg"], "embeddings": [away],
         "view_events": {"c1.jpg": "Front/2026-10-15/12-00-00"}},
    ]
    gallery.save()
    return gallery


def test_accuracy_leaves_out_each_views_event_by_lighting(measured):
    table = dogs.accuracy(measured, distances=(0.20, 0.23, 0.26))
    assert table["views"] == {"day": 0, "night": 4} and table["unknown_events"] == 0
    strict, middle, loose = table["rows"]
    assert strict["night"] == {"sure": 0, "right": 0, "wrong": 0} and strict["unnamed"] == 0
    assert middle["unnamed"] == 1
    assert loose["night"] == {"sure": 2, "right": 2, "wrong": 0} and loose["day"]["sure"] == 0
    measured.people[1]["view_events"]["b2.jpg"] = "Back/2026-10-15/11-30-00"
    measured.save()
    assert dogs.accuracy(measured, distances=(0.20,))["rows"][0]["night"]["sure"] == 2


def test_a_view_without_an_event_leaves_out_only_its_copies(measured):
    del measured.people[1]["view_events"]
    measured.save()
    table = dogs.accuracy(measured, distances=(0.20,))
    assert table["unknown_events"] == 2 and table["rows"][0]["night"]["sure"] == 2


def test_the_page_reads_the_table_and_saves_a_distance(gallery, measured, monkeypatch, config):
    monkeypatch.setattr(dogs, "GALLERY_FILE", measured.path)
    client = TestClient(web.app, client=("127.0.0.1", 50000))
    table = client.get("/api/accuracy/dogs").json()
    assert table["current"] == table["default"] == dogs.SURE_DISTANCE and table["ratio"] == dogs.SURE_RATIO
    assert dogs.SURE_DISTANCE in [row["distance"] for row in table["rows"]]
    saved = client.post("/api/settings", json={"dog_sure_distance": 0.27}, headers=HEADER)
    assert saved.status_code == 200 and saved.json()["dog_sure_distance"] == 0.27
    assert json.loads(config.read_text(encoding="utf-8"))["dog_sure_distance"] == 0.27
    assert client.get("/api/accuracy/dogs").json()["current"] == 0.27
    for refused in (0.1, 0.45, "near"):
        assert client.post("/api/settings", json={"dog_sure_distance": refused}, headers=HEADER).status_code == 400
