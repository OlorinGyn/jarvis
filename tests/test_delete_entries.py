"""Backlog 47: an unnamed entry deleted from the page, as forgetting it would; named ones never."""

import json
import logging
from datetime import date

import numpy as np
import pytest
from fastapi.testclient import TestClient

from dog_vectors import descriptor
from jarvis import dogs, faces, reports, web

SIZE = 512
CROP = np.zeros((40, 40, 3), np.uint8)
HEADER = {"X-Jarvis-Request": "1"}
DAY = "2026-11-17"


def vector(index):
    found = np.zeros(SIZE, np.float32)
    found[index] = 1
    return found.tolist()


@pytest.fixture(autouse=True)
def isolated(tmp_path, monkeypatch):
    monkeypatch.setattr(dogs, "GALLERY_FILE", tmp_path / "dogs" / "gallery.json")
    monkeypatch.setattr(dogs, "DOG_DIR", tmp_path / "dogs")
    monkeypatch.setattr(faces, "GALLERY_FILE", tmp_path / "faces" / "gallery.json")
    monkeypatch.setattr(faces, "FACE_DIR", tmp_path / "faces")
    monkeypatch.setattr(reports, "REPORT_DIR", tmp_path / "reports")


@pytest.fixture
def client():
    return TestClient(web.app, client=("127.0.0.1", 50000))


def seen(gallery, entry_id, stem):
    """A sighting and its thumbnail in a day folder beside the gallery."""
    folder = gallery.path.parent / DAY
    folder.mkdir(parents=True, exist_ok=True)
    (folder / f"{stem}.jpg").write_bytes(b"jpg")
    (folder / f"{stem}.json").write_text(json.dumps({
        gallery.sighting_key: entry_id, "camera": "Front", "at": f"{DAY}T10:00:00", "time": "10:00:00",
        "clip": f"clips/Front/{DAY}/10-00-00.mp4"}), encoding="utf-8")


def faces_with_visitors(count):
    gallery = faces.Gallery()
    ids = [gallery.add([vector(i)], "t.jpg", [CROP]) for i in range(count)]
    for index, person_id in enumerate(ids):
        seen(gallery, person_id, f"10-00-0{index}")
    return faces.Gallery(), ids


def test_an_unnamed_face_is_deleted_its_photos_gone_its_sightings_and_thumbnails_kept(client, caplog):
    gallery, [person_id] = faces_with_visitors(1)
    photos = faces.views_of(gallery.get(person_id))
    assert photos and all((gallery.path.parent.parent / p).exists() for p in photos)
    with caplog.at_level(logging.INFO, logger=web.logger.name):
        answer = client.post(f"/api/persons/{person_id}/delete", headers=HEADER)
    assert answer.status_code == 200 and answer.json() == {"deleted": person_id}
    assert faces.Gallery().get(person_id) is None
    assert not list(gallery.view_dir.glob("*.jpg"))
    day = gallery.path.parent / DAY
    assert json.loads((day / "10-00-00.json").read_text())["person_id"] == person_id
    assert (day / "10-00-00.jpg").exists()
    assert "Deleted 1 unnamed face entries from the page: Visitor 1" in caplog.text


def test_a_deleted_face_reads_in_recordings_as_a_forgotten_one(client):
    gallery, [deleted, forgotten] = faces_with_visitors(2)
    client.post(f"/api/persons/{deleted}/delete", headers=HEADER)
    gallery = faces.Gallery()
    gallery.people.remove(gallery.get(forgotten))
    gallery.save()
    assert web._who_was_seen(date.fromisoformat(DAY)) == {("Front", DAY, "10-00-00"): ["unknown"]}


def test_a_named_face_is_never_deleted(client):
    gallery, [person_id] = faces_with_visitors(1)
    gallery.rename(person_id, "Ana")
    answer = client.post(f"/api/persons/{person_id}/delete", headers=HEADER)
    assert answer.status_code == 400
    assert faces.Gallery().get(person_id)["name"] == "Ana"
    assert client.post("/api/persons/p_00000000/delete", headers=HEADER).status_code == 404


def test_a_mixed_list_deletes_the_unnamed_and_reports_the_rest_as_gone(client):
    gallery, ids = faces_with_visitors(3)
    gallery.rename(ids[1], "Ana")
    answer = client.post("/api/persons/delete", json={"ids": ids + [ids[0], "p_00000000"]}, headers=HEADER)
    assert answer.json() == {"deleted": [ids[0], ids[2]], "gone": [ids[1], "p_00000000"]}
    after = faces.Gallery()
    assert [p["id"] for p in after.people] == [ids[1]]


def test_a_freed_visitor_number_is_given_to_the_next_new_face(client):
    _, ids = faces_with_visitors(3)
    client.post("/api/persons/delete", json={"ids": ids[:2]}, headers=HEADER)
    newest = faces.Gallery().add([vector(9)], "t.jpg", [CROP])
    assert faces.Gallery().get(newest)["temporary_name"] == "Visitor 1"


def test_an_unnamed_dog_is_deleted_the_same_way(client, caplog):
    gallery = dogs.DogGallery()
    named = gallery.add([descriptor(1)], "a.jpg", [CROP])
    gallery.rename(named, "Aurora")
    stray = gallery.add([descriptor(7)], "u.jpg", [CROP])
    seen(gallery, stray, "10-00-00")
    gallery = dogs.DogGallery()
    assert list(gallery.view_dir.glob("*.jpg"))
    with caplog.at_level(logging.INFO, logger=web.logger.name):
        answer = client.post("/api/dogs/delete", json={"ids": [stray, named]}, headers=HEADER)
    assert answer.json() == {"deleted": [stray], "gone": [named]}
    after = dogs.DogGallery()
    assert after.get(stray) is None and after.get(named)["name"] == "Aurora"
    assert set(gallery.view_dir.glob("*.jpg")) == {after.path.parent.parent / v for v in faces.views_of(after.get(named))}
    assert (gallery.path.parent / DAY / "10-00-00.json").exists()
    assert f"Deleted 1 unnamed dog entries from the page: {stray}" in caplog.text
    assert client.post(f"/api/dogs/{named}/delete", headers=HEADER).status_code == 400


def test_a_delete_from_an_unpaired_device_is_refused(client):
    _, [person_id] = faces_with_visitors(1)
    outside = TestClient(web.app, client=("192.168.1.50", 50000))
    assert outside.post(f"/api/persons/{person_id}/delete", headers=HEADER).status_code == 403
    assert client.post(f"/api/persons/{person_id}/delete").status_code == 403
    assert faces.Gallery().get(person_id) is not None
