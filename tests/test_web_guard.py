"""Every write needs the page's header; from another device it also needs the paired PIN (R24)."""

import json

import numpy as np
import pytest
from fastapi.testclient import TestClient

from jarvis import dogs, faces, settings, web

HEADER = {"X-Jarvis-Request": "1"}
TOKEN = "123456789:AAFakeTokenForTheGuardTests_x"


@pytest.fixture(autouse=True)
def config(tmp_path, monkeypatch):
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"notify_token": TOKEN}), encoding="utf-8")
    monkeypatch.setattr(settings, "FILE", path)
    return path


@pytest.fixture
def local():
    return TestClient(web.app, client=("127.0.0.1", 50000))


@pytest.fixture
def remote():
    return TestClient(web.app, client=("192.168.0.50", 50000))


def pin(value):
    return {**HEADER, "X-Jarvis-Pin": value}


def test_a_write_without_the_header_is_refused_even_locally(local):
    assert local.post("/api/pair").status_code == 403
    assert local.post("/api/pair", headers=HEADER).status_code == 200


def test_the_network_cannot_write_before_a_pin_is_set(remote):
    answer = remote.post("/api/pair", headers=HEADER)
    assert answer.status_code == 403
    assert "no PIN is set" in answer.json()["detail"]


def test_only_this_machine_sets_the_pin(local, remote, config):
    assert remote.post("/api/pin", headers=HEADER, json={"pin": "1234"}).status_code == 403
    assert local.post("/api/pin", headers=HEADER, json={"pin": "12a4"}).status_code == 400
    assert local.post("/api/pin", headers=HEADER, json={"pin": "482913"}).status_code == 200
    assert json.loads(config.read_text(encoding="utf-8"))["write_pin"] == "482913"
    assert remote.post("/api/pin", headers=pin("482913"), json={"pin": "1111"}).status_code == 403


def test_a_paired_device_writes_and_others_do_not(local, remote):
    local.post("/api/pin", headers=HEADER, json={"pin": "482913"})
    assert remote.post("/api/pair", headers=HEADER).status_code == 403
    assert remote.post("/api/pair", headers=pin("482914")).status_code == 403
    assert remote.post("/api/pair", headers={"X-Jarvis-Pin": "482913"}).status_code == 403
    assert remote.post("/api/pair", headers=pin("482913")).status_code == 200
    answer = remote.post("/api/settings", headers=pin("482913"), json={"notify_prefix": "[T]"})
    assert answer.status_code == 200
    assert answer.json()["notify_prefix"] == "[T]"


def test_reading_stays_open_and_never_shows_the_secrets(local, remote):
    local.post("/api/pin", headers=HEADER, json={"pin": "482913"})
    for client in (local, remote):
        answer = client.get("/api/settings")
        assert answer.status_code == 200
        assert TOKEN not in answer.text and "482913" not in answer.text
        assert answer.json()["notify_token_set"] and answer.json()["pin_set"]
    assert remote.get("/api/settings").json()["local"] is False
    assert local.get("/api/settings").json()["local"] is True


def test_settings_are_checked_one_by_one(local):
    for bad in ({"archive_after_days": 0}, {"notify_labels": ["car"]},
                {"notify_cooldown": "x"}, {"write_pin": "1234"}, {"notify_token": " "}):
        assert local.post("/api/settings", headers=HEADER, json=bad).status_code == 400


def test_shutdown_is_local_only(remote):
    assert remote.post("/api/shutdown", headers=pin("482913")).status_code == 403


def test_choosing_a_favourite_goes_through_the_guard(local, remote, tmp_path, monkeypatch):
    monkeypatch.setattr(faces, "GALLERY_FILE", tmp_path / "gallery.json")
    monkeypatch.setattr(faces, "FACE_DIR", tmp_path)
    person_id = faces.Gallery().add([[0.1] * 128, [0.2] * 128], "t.jpg",
                                    [np.zeros((40, 40, 3), np.uint8), None])
    route = f"/api/persons/{person_id}/views/0/cover"
    assert remote.post(route, headers=HEADER).status_code == 403
    assert local.post(f"/api/persons/{person_id}/views/1/cover", headers=HEADER).status_code == 400
    answer = local.post(route, headers=HEADER)
    assert answer.status_code == 200 and answer.json()["cover_index"] == 0
    assert local.get("/api/persons").json()["unnamed"][0]["photo"].startswith("/view/")


def test_dismissing_a_dog_goes_through_the_guard(local, remote, tmp_path, monkeypatch):
    monkeypatch.setattr(dogs, "GALLERY_FILE", tmp_path / "dogs" / "gallery.json")
    dog_id = dogs.DogGallery().add([[1.0] + [0.0] * 40], "t.jpg", [np.zeros((40, 40, 3), np.uint8)])
    assert remote.post(f"/api/dogs/{dog_id}/dismiss", headers=HEADER).status_code == 403
    assert local.post(f"/api/dogs/{dog_id}/dismiss", headers=HEADER).status_code == 200
    assert local.post(f"/api/dogs/{dog_id}/dismiss", headers=HEADER).status_code == 404
