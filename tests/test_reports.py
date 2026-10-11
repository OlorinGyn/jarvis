"""A bad detection the user reports leaves the gallery or the card, and is kept as evidence (backlog 23)."""

import json

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
