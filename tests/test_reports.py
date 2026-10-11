"""A bad detection the user reports leaves the gallery or the card, and is kept as evidence (backlog 23)."""

import json

import cv2
import numpy as np
import pytest
from fastapi.testclient import TestClient

from jarvis import faces, reports, web

CROP = np.zeros((40, 40, 3), np.uint8)
HEADER = {"X-Jarvis-Request": "1"}


@pytest.fixture(autouse=True)
def report_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(reports, "REPORT_DIR", tmp_path / "reports")
    return tmp_path / "reports"


@pytest.fixture
def gallery(tmp_path):
    return faces.Gallery(tmp_path / "faces" / "gallery.json")


def sighting(gallery, person_id, at="2026-10-11T14:02:07"):
    folder = gallery.path.parent / at[:10]
    folder.mkdir(parents=True, exist_ok=True)
    stem = f"{at[11:].replace(':', '-')}_abcdef"
    (folder / f"{stem}.jpg").write_bytes(b"jpeg")
    (folder / f"{stem}.json").write_text(json.dumps({
        "person_id": person_id, "camera": "Front", "at": at, "time": at[11:], "score": 0.41,
        "box": [10, 20, 40, 48], "clip": "clips/Front/2026-10-11/14-02-07.mp4",
        "thumbnail": f"{stem}.jpg"}), encoding="utf-8")
    return folder / f"{stem}.json"


def test_a_reported_face_leaves_the_gallery_and_is_kept_as_a_report(gallery, report_dir):
    person_id = gallery.add([[0.1] * 128], "t.jpg", [CROP])
    seen = sighting(gallery, person_id)
    path = reports.report_entry(gallery, person_id)
    report = json.loads(path.read_text(encoding="utf-8"))
    assert path.parent == report_dir / "face"
    assert report["verdict"] == "not a face" and report["source"] == "gallery"
    assert report["camera"] == "Front" and report["box"] == [10, 20, 40, 48]
    assert report["clip"].endswith("14-02-07.mp4") and len(report["entry"]["embeddings"]) == 1
    assert (path.parent / report["crop"]).is_file()
    assert faces.Gallery(gallery.path).get(person_id) is None
    assert not seen.exists() and not seen.with_suffix(".jpg").exists()
    assert list(gallery.view_dir.glob("*.jpg")) == []


def test_a_named_person_cannot_be_reported(gallery, report_dir):
    person_id = gallery.add([[0.1] * 128], "t.jpg", [CROP])
    gallery.rename(person_id, "Someone")
    assert reports.report_entry(gallery, person_id) is None
    assert reports.report_entry(gallery, "p_00000000") is None
    assert faces.Gallery(gallery.path).get(person_id) is not None
    assert not report_dir.exists() or list(report_dir.rglob("*")) == []


def event(folder, labels):
    folder.mkdir(parents=True, exist_ok=True)
    sidecar = folder / "15-12-59.json"
    sidecar.write_text(json.dumps({
        "camera": "Front", "started_at": "2026-10-10T15:12:59", "time": "15:12:59",
        "seconds": 12.0, "labels": labels, "best_confidence": 0.71, "video": "15-12-59.mp4",
        "thumbnail": "15-12-59.jpg", "best_thumbnail": "15-12-59.best.jpg"}), encoding="utf-8")
    for suffix in (".jpg", ".best.jpg", ".mp4"):
        (folder / f"15-12-59{suffix}").write_bytes(b"x")
    return sidecar


def test_a_reported_label_leaves_the_card_but_stays_in_the_event(tmp_path, report_dir, monkeypatch):
    clips = tmp_path / "clips"
    sidecar = event(clips / "Front" / "2026-10-10", ["dog", "person"])
    monkeypatch.setattr(web, "CLIP_DIR", clips)
    client = TestClient(web.app, client=("127.0.0.1", 50000))
    route = "/api/events/Front/2026-10-10/15-12-59/report"
    assert client.post(route, json={"label": "cat"}, headers=HEADER).status_code == 400
    assert client.post(route, json={"label": "person"}, headers=HEADER).status_code == 200
    assert client.post(route, json={"label": "person"}, headers=HEADER).status_code == 400
    assert client.post("/api/events/Front/2026-10-10/..%2F..%2Fx/report",
                       json={"label": "person"}, headers=HEADER).status_code == 404
    stored = json.loads(sidecar.read_text(encoding="utf-8"))
    assert stored["labels"] == ["dog", "person"] and stored["reported_labels"] == ["person"]
    shown = web._event({**stored, "thumbnail_path": sidecar.with_suffix(".jpg")})
    assert shown["labels"] == ["dog"] and shown["report"] == route
    [report] = reports.listing()
    assert report["kind"] == "person" and report["verdict"] == "not a person"
    assert report["source"] == "event" and report["score"] == 0.71
    assert (report_dir / "person" / report["crop"]).is_file()


def test_events_written_before_reports_still_show_every_label(tmp_path):
    sidecar = event(tmp_path / "Front" / "2026-10-10", ["person"])
    entry = json.loads(sidecar.read_text(encoding="utf-8"))
    assert web._event({**entry, "thumbnail_path": sidecar.with_suffix(".jpg")})["labels"] == ["person"]


def test_undo_puts_a_reported_face_back_with_its_photos_and_sightings(gallery, report_dir):
    person_id = gallery.add([[0.1] * 128, [0.2] * 128], "t.jpg", [CROP, CROP])
    before = faces.Gallery(gallery.path).get(person_id)
    seen = sighting(gallery, person_id)
    path = reports.report_entry(gallery, person_id)
    assert list(gallery.view_dir.glob("*.jpg")) == []
    assert reports.undo(path, {"face": gallery})
    after = faces.Gallery(gallery.path).get(person_id)
    assert after == before
    assert all(reports._stored(view).is_file() for view in faces.views_of(after))
    assert seen.is_file() and seen.with_suffix(".jpg").is_file()
    assert reports.listing() == [] and not path.with_suffix("").exists()


def test_undo_of_a_report_written_before_undo_existed(tmp_path, report_dir):
    dog_gallery = faces.Gallery(tmp_path / "dogs" / "gallery.json")
    folder = report_dir / "dog"
    folder.mkdir(parents=True)
    cv2.imwrite(str(folder / "2026-10-10_15-36-08_3d0bde.jpg"), CROP)
    path = folder / "2026-10-10_15-36-08_3d0bde.json"
    path.write_text(json.dumps({
        "kind": "dog", "verdict": "not a dog", "reported_at": "2026-10-11T09:00:00",
        "source": "gallery", "label": "dog", "camera": "Front", "at": "2026-10-10T15:36:08",
        "time": "15:36:08", "clip": "clips/Front/2026-10-10/15-36-08.mp4", "score": None,
        "box": [1, 2, 3, 4], "crop": "2026-10-10_15-36-08_3d0bde.jpg",
        "entry": {"id": "d_68b6364f", "first_seen": "2026-10-10T20:14:54", "embeddings": [[0.3] * 8]},
        "sightings": [{"dog_id": "d_68b6364f", "camera": "Front", "at": "2026-10-10T15:36:08",
                       "thumbnail": "15-36-08_643ded.jpg"}]}), encoding="utf-8")
    assert reports.undo(path, {"dog": dog_gallery})
    dog = faces.Gallery(dog_gallery.path).get("d_68b6364f")
    assert dog["name"] == "" and len(dog["embeddings"]) == 1
    assert reports._stored(faces.views_of(dog)[0]).is_file()
    restored = dog_gallery.path.parent / "2026-10-10" / "15-36-08_643ded.json"
    assert json.loads(restored.read_text(encoding="utf-8"))["dog_id"] == "d_68b6364f"
    assert restored.with_suffix(".jpg").is_file()
    assert not path.exists()


def test_undo_from_the_page_returns_a_label_to_its_recording(tmp_path, report_dir, monkeypatch):
    clips = tmp_path / "clips"
    sidecar = event(clips / "Front" / "2026-10-10", ["dog", "person"])
    monkeypatch.setattr(web, "CLIP_DIR", clips)
    reports.report_event(sidecar, "person")
    client = TestClient(web.app, client=("127.0.0.1", 50000))
    [card] = client.get("/api/reports").json()
    assert card["verdict"] == "not a person" and card["source"] == "event"
    assert client.get(card["photo"]).status_code == 200
    assert client.post(card["undo"], headers=HEADER).status_code == 200
    assert json.loads(sidecar.read_text(encoding="utf-8"))["reported_labels"] == []
    assert client.get("/api/reports").json() == []
    assert client.post(card["undo"], headers=HEADER).status_code == 404
    assert client.post("/api/reports/person/..%2F..%2Fx/undo", headers=HEADER).status_code == 404


def test_undo_refuses_an_entry_that_is_already_back(gallery, report_dir):
    person_id = gallery.add([[0.1] * 128], "t.jpg", [CROP])
    entry = faces.Gallery(gallery.path).get(person_id)
    path = reports.report_entry(gallery, person_id)
    gallery.put_back(entry)
    assert not reports.undo(path, {"face": gallery})
    assert path.is_file()
