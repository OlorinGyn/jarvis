"""Backlog 46 step 1: a scan's finding (observe, matches) is reusable without writing; recording is apart."""

from datetime import datetime

import numpy as np
import pytest

from jarvis import faces, people, settings

SIZE = 512
START = datetime(2026, 11, 18, 9, 30, 0)
GOOD = np.full((8, 8, 3), 200, np.uint8)


def vector(*values):
    found = np.zeros(SIZE, np.float32)
    found[:len(values)] = values
    return (found / np.linalg.norm(found)).tolist()


STRANGER = vector(1.0)
GUSTAVO = vector(0.0, 0.0, 1.0)
IZABEL = vector(0.0, 1.0)


@pytest.fixture(autouse=True)
def world(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "FILE", tmp_path / "config.json")
    monkeypatch.setattr(faces, "FACE_DIR", tmp_path / "faces")
    monkeypatch.setattr(faces, "GALLERY_FILE", tmp_path / "faces" / faces.GALLERY_FILE.name)
    monkeypatch.setattr(faces, "face_quality", lambda image, face=None: None if image is None else 0.9)
    monkeypatch.setattr(faces, "faces_in", lambda frame, sides=None, missed=None: frame)
    monkeypatch.setattr(people, "person_boxes", lambda frame: [(0, 0, 1000, 1000)])


@pytest.fixture
def gallery(tmp_path):
    found = faces.Gallery(tmp_path / "faces" / faces.GALLERY_FILE.name)
    for name, embedding in (("Gustavo", GUSTAVO), ("Izabel", IZABEL)):
        person_id = found.add([embedding], "t.jpg", [GOOD])
        found.rename(person_id, name)
        found.set_resident(person_id, True)
    return found


def seen(embedding, width=60):
    return {"box": (100, 100, width, width), "embedding": embedding, "score": 0.9, "crop": GOOD}


def files(folder):
    return sorted((p.relative_to(folder), p.stat().st_mtime_ns) for p in folder.rglob("*") if p.is_file())


FRAMES = [[seen(GUSTAVO)], [], [seen(STRANGER), seen(vector(0.0, 0.0, 1.0, 0.1))], [seen(vector(1.0, 0.05))]]


def test_finding_and_matching_write_nothing(tmp_path, gallery):
    before = files(tmp_path)
    observations, frames, paused, missed = faces.observe(iter(FRAMES))
    found = list(faces.matches(gallery, observations))
    assert (frames, paused, missed, len(observations)) == (4, 0.0, 0, 4)
    assert [(m["person_id"] is None, round(m["score"], 2) >= 0.99) for m in found] == [(False, True), (True, False)]
    assert len(found[1]["references"]) == 2
    assert files(tmp_path) == before


def test_the_scan_records_what_matches_found(tmp_path, monkeypatch, gallery):
    observations, *_ = faces.observe(iter(FRAMES))
    planned = [(m["person_id"], round(m["score"], 3)) for m in faces.matches(gallery, observations)]
    monkeypatch.setattr(faces, "_sampled_frames", lambda clip, moments=(): iter(FRAMES))
    clip = tmp_path / "clips" / "Back" / "2026-11-18" / "09-30-00.mp4"
    clip.parent.mkdir(parents=True)
    clip.write_bytes(b"x")
    recorded = faces._scan_clip(clip, "Back", START, gallery, ())
    assert [s["person_id"] for s in recorded][0] == planned[0][0]
    assert [round(s["score"], 3) for s in recorded] == [score for _, score in planned]
    assert recorded[1]["person_id"] and recorded[1]["person_id"] not in {p for p, _ in planned}
    assert len(list((tmp_path / "faces" / "2026-11-18").glob("*.json"))) == 2


def test_stop_ends_the_reading_at_the_frame_it_names():
    read = []

    def frames():
        for frame in FRAMES:
            read.append(frame)
            yield frame

    observations, count, _, _ = faces.observe(frames(), stop=lambda kept: bool(kept))
    assert count == 1 and len(read) == 1 and len(observations) == 1


def test_a_new_face_given_no_entry_does_not_hide_a_later_group(gallery):
    observations, *_ = faces.observe(iter([[seen(STRANGER)], [seen(STRANGER)], [seen(IZABEL)]]))
    found = []
    for match in faces.matches(gallery, observations):
        found.append(match)
        if match["person_id"] is None:
            match["person_id"] = ""
    assert [m["person_id"] is None or m["person_id"] == "" for m in found] == [True, False]


def test_one_visitor_takes_the_merge_it_is_given(gallery):
    recorded = [{"person_id": "a", "name": ""}, {"person_id": "b", "name": "", "views": [STRANGER]}]
    tracks = [{"id": 1, "first": 0.0, "last": 5.0, "frames": {"person": 9}, "longest_person_run": 9}]
    [kept] = faces._one_visitor(gallery, recorded, tracks, merge=lambda ids: ids[0])
    assert kept["person_id"] == "a" and kept["views"] == [STRANGER]
