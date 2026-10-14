"""Backlog 32 for faces: the sure threshold set in Settings from accuracy measured on the named views."""

import json

import numpy as np
import pytest
from fastapi.testclient import TestClient

from jarvis import faces, notify, settings, web

HEADER = {"X-Jarvis-Request": "1"}


@pytest.fixture(autouse=True)
def config(tmp_path, monkeypatch):
    path = tmp_path / "config.json"
    monkeypatch.setattr(settings, "FILE", path)
    return path


@pytest.fixture
def client():
    return TestClient(web.app, client=("127.0.0.1", 50000))


def unit(*values):
    vector = np.zeros(8, np.float32)
    vector[:len(values)] = values
    return (vector / np.linalg.norm(vector)).tolist()


def sighting(score):
    return {"person_id": "p_1", "name": "Ana", "score": score, "resident": True}


def test_without_a_choice_the_sure_threshold_is_todays():
    assert settings.load()["face_sure_threshold"] == faces.LEARN_THRESHOLD
    assert faces.learn_threshold() == faces.LEARN_THRESHOLD


def test_a_value_out_of_range_reads_as_the_default(config):
    config.write_text(json.dumps({"face_sure_threshold": 0.95}), encoding="utf-8")
    assert faces.learn_threshold() == faces.LEARN_THRESHOLD
    config.write_text(json.dumps({"face_sure_threshold": "high"}), encoding="utf-8")
    assert faces.learn_threshold() == faces.LEARN_THRESHOLD


def test_the_chosen_threshold_decides_sure_and_probable(config):
    assert notify.person_case(sighting(0.45)) == "resident_person"
    assert notify._who(sighting(0.45)) == "Ana recognized"
    config.write_text(json.dumps({"face_sure_threshold": 0.5}), encoding="utf-8")
    assert notify.person_case(sighting(0.45)) == "probable_resident_person"
    assert notify._who(sighting(0.45)) == "probably Ana"
    values = {"face_sure_threshold": 0.35}
    assert notify.person_case(sighting(0.38), values) == "resident_person"


def test_a_settings_dict_without_the_key_keeps_todays_threshold():
    assert faces.learn_threshold({"notify_mode": "home"}) == faces.LEARN_THRESHOLD


def test_naming_gathers_look_alikes_by_the_chosen_threshold(tmp_path, config):
    gallery = faces.Gallery(tmp_path / "gallery.json")
    ana = gallery.add([unit(1, 0)], "a.jpg")
    gallery.add([unit(1, 1.5)], "b.jpg")
    config.write_text(json.dumps({"face_sure_threshold": 0.58}), encoding="utf-8")
    gallery.rename(ana, "Ana")
    assert len(faces.Gallery(gallery.path).people) == 2
    config.write_text(json.dumps({"face_sure_threshold": 0.5}), encoding="utf-8")
    gallery.rename(ana, "Ana")
    assert len(faces.Gallery(gallery.path).people) == 1


@pytest.fixture
def measured(tmp_path):
    gallery = faces.Gallery(tmp_path / "gallery.json")
    gallery.people = [
        {"id": "p_a", "name": "Ana", "embeddings": [unit(1, 0.1), unit(1, 0.2), unit(1, 0.2), unit(0.2, 1)]},
        {"id": "p_b", "name": "Bia", "embeddings": [unit(0, 1), unit(0, 1, 0.1)]},
        {"id": "p_c", "name": "", "embeddings": [unit(1, 0.15), unit(0, 0, 1)]},
    ]
    gallery.save()
    return gallery


def test_accuracy_leaves_each_view_and_its_copies_out(measured):
    table = faces.accuracy(measured, thresholds=(0.5, 0.99))
    assert table["views"] == 6 and table["unnamed_views"] == 2
    loose, strict = table["rows"]
    assert loose["named"] == 6 and loose["right"] == 5 and loose["wrong"] == 1
    assert loose["unnamed"] == 1
    assert strict["named"] == 5 and strict["wrong"] == 0 and strict["unnamed"] == 1


def test_accuracy_without_two_views_is_empty(tmp_path):
    table = faces.accuracy(faces.Gallery(tmp_path / "gallery.json"))
    assert table["views"] == 0 and all(row["named"] == 0 for row in table["rows"])


def test_the_page_reads_the_table_and_saves_a_threshold(client, measured, monkeypatch, config):
    monkeypatch.setattr(faces, "GALLERY_FILE", measured.path)
    table = client.get("/api/accuracy/faces").json()
    assert table["current"] == faces.LEARN_THRESHOLD and table["default"] == faces.LEARN_THRESHOLD
    assert faces.LEARN_THRESHOLD in [row["threshold"] for row in table["rows"]]
    saved = client.post("/api/settings", json={"face_sure_threshold": 0.475}, headers=HEADER)
    assert saved.status_code == 200 and saved.json()["face_sure_threshold"] == 0.475
    assert json.loads(config.read_text(encoding="utf-8"))["face_sure_threshold"] == 0.475
    assert client.get("/api/accuracy/faces").json()["current"] == 0.475
    refused = client.post("/api/settings", json={"face_sure_threshold": 0.2}, headers=HEADER)
    assert refused.status_code == 400
