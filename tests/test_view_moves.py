"""A view is moved only if it is still the one the page showed at that position (R41)."""

import json

import numpy as np
import pytest
from fastapi.testclient import TestClient

from jarvis import faces, settings, web
from queues import queue

HEADER = {"X-Jarvis-Request": "1"}
CROP = np.zeros((20, 20, 3), np.uint8)


def embedding(value):
    return [float(value)] * 128


@pytest.fixture
def full(tmp_path, monkeypatch):
    """A person with two chosen views and a full Waiting of two."""
    config = tmp_path / "config.json"
    config.write_text(json.dumps({}), encoding="utf-8")
    monkeypatch.setattr(settings, "FILE", config)
    monkeypatch.setattr(faces, "GALLERY_FILE", tmp_path / "faces" / "gallery.json")
    monkeypatch.setattr(faces, "MAX_EMBEDDINGS", 2)
    monkeypatch.setattr(faces, "MAX_PENDING", 2)
    gallery = faces.Gallery()
    person_id = gallery.add([embedding(1), embedding(2)], "t.jpg", [CROP, CROP])
    queue(gallery, person_id, [embedding(3), embedding(4)], CROP)
    return gallery, person_id


def shown(url):
    return url.rsplit("/", 1)[-1] if url else ""


def test_a_delete_on_a_page_from_before_another_tab_moved_is_refused(full):
    gallery, person_id = full
    client = TestClient(web.app, client=("127.0.0.1", 50000))
    page = client.get(f"/api/persons/{person_id}").json()
    oldest = shown(page["pending_photos"][0])
    gallery.remove_waiting(person_id, 0)
    answer = client.post(f"/api/persons/{person_id}/pending/0/remove", headers=HEADER,
                         json={"view": oldest})
    assert answer.status_code == 409
    assert "refreshed" in answer.json()["detail"]
    assert len(faces.Gallery().get(person_id)["pending"]) == 1


def test_each_move_goes_ahead_when_the_view_is_still_there(full):
    gallery, person_id = full
    client = TestClient(web.app, client=("127.0.0.1", 50000))
    page = client.get(f"/api/persons/{person_id}").json()
    route = f"/api/persons/{person_id}"
    assert client.post(f"{route}/views/0/cover", headers=HEADER,
                       json={"view": shown(page["view_photos"][0])}).status_code == 200
    assert client.post(f"{route}/pending/1/remove", headers=HEADER,
                       json={"view": shown(page["pending_photos"][1])}).status_code == 200
    page = client.get(route).json()
    assert client.post(f"{route}/views/1/demote", headers=HEADER,
                       json={"view": shown(page["view_photos"][1])}).status_code == 200
    page = client.get(route).json()
    assert client.post(f"{route}/pending/0/promote", headers=HEADER,
                       json={"view": shown(page["pending_photos"][0])}).status_code == 200
    page = client.get(route).json()
    assert client.post(f"{route}/views/1/remove", headers=HEADER,
                       json={"view": shown(page["view_photos"][1])}).status_code == 200


def test_a_move_names_the_wrong_view_and_is_refused_for_each_kind(full):
    _, person_id = full
    client = TestClient(web.app, client=("127.0.0.1", 50000))
    route = f"/api/persons/{person_id}"
    for move in ("views/0/cover", "views/0/remove", "views/0/demote",
                 "pending/0/promote", "pending/0/remove"):
        assert client.post(f"{route}/{move}", headers=HEADER,
                           json={"view": "000000000000.jpg"}).status_code == 409


def test_the_gallery_checks_under_its_own_lock(full):
    gallery, person_id = full
    first = faces.Gallery().get(person_id)["pending"][0]["view"]
    faces.Gallery().remove_waiting(person_id, 0)
    with pytest.raises(faces.ViewsChanged):
        gallery.remove_waiting(person_id, 0, expected=first.rsplit("/", 1)[-1])
