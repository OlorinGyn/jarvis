"""Backlog 26: many unnamed crops named, or reported, at once."""

import json

import numpy as np
import pytest
from fastapi.testclient import TestClient

from jarvis import dogs, faces, reports, web

CROP = np.zeros((40, 40, 3), np.uint8)
HEADER = {"X-Jarvis-Request": "1"}


def descriptor(tone_bin, infrared=True):
    tone = [0.0] * dogs.TONE_BINS
    tone[tone_bin] = 1.0
    return [1.0 if infrared else 0.0] + tone + [0.0] * (dogs.HUE_BINS + dogs.SATURATION_BINS)


def sighting(gallery, dog_id, stem):
    folder = gallery.path.parent / "2026-10-12"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / f"{stem}.json").write_text(json.dumps({
        "dog_id": dog_id, "camera": "Front", "at": "2026-10-12T10:00:00", "time": "10:00:00"}),
        encoding="utf-8")


@pytest.fixture(autouse=True)
def isolated(tmp_path, monkeypatch):
    monkeypatch.setattr(dogs, "GALLERY_FILE", tmp_path / "dogs" / "gallery.json")
    monkeypatch.setattr(faces, "GALLERY_FILE", tmp_path / "faces" / "gallery.json")
    monkeypatch.setattr(reports, "REPORT_DIR", tmp_path / "reports")


@pytest.fixture
def gallery():
    gallery = dogs.DogGallery()
    aurora = gallery.add([descriptor(1)], "a.jpg", [CROP])
    gallery.rename(aurora, "Aurora")
    gallery.set_cover(aurora, 0)
    return dogs.DogGallery()


@pytest.fixture
def client():
    return TestClient(web.app, client=("127.0.0.1", 50000))


def unnamed(gallery, count, tone_bin=7):
    ids = [gallery.add([descriptor(tone_bin)], "u.jpg", [CROP]) for _ in range(count)]
    for index, dog_id in enumerate(ids):
        sighting(gallery, dog_id, f"10-00-0{index}")
    return ids


def test_three_crops_join_a_named_dog_with_views_sightings_and_favourite(gallery, client):
    aurora = gallery.by_name("Aurora")
    cover = aurora["cover"]
    ids = unnamed(gallery, 3)
    answer = client.post("/api/dogs/assign", json={"ids": ids, "to": aurora["id"]}, headers=HEADER)
    assert answer.status_code == 200
    assert answer.json()["joined"] == ids and answer.json()["gone"] == []
    reloaded = dogs.DogGallery()
    aurora = reloaded.by_name("Aurora")
    assert len(aurora["embeddings"]) == 4 and aurora["cover"] == cover
    assert all(reloaded.get(i) is None for i in ids)
    assert len(dogs.appearances(aurora["id"], reloaded.path.parent)) == 3


def test_an_id_already_gone_is_skipped_and_named(gallery, client):
    ids = unnamed(gallery, 2)
    reports.report_entry(gallery, ids[0])
    answer = client.post("/api/dogs/assign", json={"ids": ids, "to": gallery.by_name("Aurora")["id"]},
                         headers=HEADER).json()
    assert answer["joined"] == [ids[1]] and answer["gone"] == [ids[0]]


def test_a_new_name_creates_the_entry(gallery, client):
    ids = unnamed(gallery, 3, tone_bin=13)
    answer = client.post("/api/dogs/assign", json={"ids": ids, "name": "Mirana"}, headers=HEADER).json()
    mirana = dogs.DogGallery().by_name("Mirana")
    assert answer["id"] == mirana["id"] == ids[0] and answer["joined"] == ids
    assert len(mirana["embeddings"]) == 3


def test_an_existing_name_joins_that_entry(gallery, client):
    ids = unnamed(gallery, 2)
    answer = client.post("/api/dogs/assign", json={"ids": ids, "name": " aurora "}, headers=HEADER).json()
    assert answer["id"] == gallery.by_name("Aurora")["id"]
    assert len(dogs.DogGallery().by_name("Aurora")["embeddings"]) == 3


def test_the_batch_report_writes_one_report_per_entry(gallery, client, tmp_path):
    ids = unnamed(gallery, 3)
    answer = client.post("/api/dogs/report", json={"ids": ids + [ids[0]]}, headers=HEADER).json()
    assert answer == {"reported": ids, "gone": []}
    assert len(list((tmp_path / "reports").rglob("*.json"))) == 3
    assert all(dogs.DogGallery().get(i) is None for i in ids)
    again = client.post("/api/dogs/report", json={"ids": ids[:1]}, headers=HEADER).json()
    assert again == {"reported": [], "gone": ids[:1]}


def test_bad_requests_are_refused(gallery, client):
    ids = unnamed(gallery, 1)
    aurora = gallery.by_name("Aurora")["id"]
    for payload in ({"ids": ids}, {"ids": ids, "to": aurora, "name": "x"}, {"ids": [], "to": aurora},
                    {"ids": ["../x"], "to": aurora}, {"ids": ids, "name": " "}):
        assert client.post("/api/dogs/assign", json=payload, headers=HEADER).status_code == 400
    assert client.post("/api/dogs/assign", json={"ids": ids, "to": ids[0]}, headers=HEADER).status_code == 409
    assert client.post("/api/dogs/assign", json={"ids": ids, "to": aurora}).status_code == 403


def test_the_grid_guesses_who_each_unnamed_crop_looks_like(gallery, client):
    near = unnamed(gallery, 1, tone_bin=1)
    far = unnamed(gallery, 1, tone_bin=7)
    guesses = {c["id"]: c["guess"] for c in client.get("/api/dogs").json()["unnamed"]}
    assert guesses == {near[0]: gallery.by_name("Aurora")["id"], far[0]: None}


def test_faces_are_assigned_the_same_way(client):
    people = faces.Gallery()
    ids = [people.add([[0.1] * 128], "t.jpg", [CROP]) for _ in range(2)]
    answer = client.post("/api/persons/assign", json={"ids": ids, "name": "Gustavo"}, headers=HEADER).json()
    assert answer["joined"] == ids
    assert len(faces.Gallery().by_name("Gustavo")["embeddings"]) == 2
    assert client.post("/api/persons/report", json={"ids": ids}, headers=HEADER).json()["gone"] == ids
