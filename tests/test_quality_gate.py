"""Backlog 45 step 3: a face view enters a gallery only at eDifFIQA(T) >= QUALITY_CUT; the messages do not change."""

import json
import threading
from datetime import datetime, timedelta

import numpy as np
import pytest

from jarvis import downloads, faces, notify, people, settings, web

SIZE = 512
START = datetime(2026, 11, 17, 15, 44, 28)
GOOD = np.full((8, 8, 3), 200, np.uint8)
POOR = np.zeros((8, 8, 3), np.uint8)
TOKEN = "123456789:AAFakeTokenForTheQualityGate_x"
HOME = {"notify_token": TOKEN, "notify_chat": "1", "notify_labels": ["person"],
        "notify_cooldown": 120, "notify_mode": "home"}
PERSON_TRACK = [{"id": 5, "first": 0.0, "last": 6.0, "frames": {"person": 9}, "longest_person_run": 9}]


def vector(*values):
    found = np.zeros(SIZE, np.float32)
    found[:len(values)] = values
    return (found / np.linalg.norm(found)).tolist()


STRANGER = vector(1.0)
OTHER = vector(0.0, 1.0)
GUSTAVO = vector(0.0, 0.0, 1.0)


class Inline:
    def __init__(self, target, args=(), kwargs=None, daemon=None):
        self.target, self.args, self.kwargs = target, args, kwargs or {}

    def start(self):
        self.target(*self.args, **self.kwargs)


class Timer:
    def __init__(self, interval, function, args=()):
        self.daemon = False

    def start(self):
        pass

    def cancel(self):
        pass


@pytest.fixture(autouse=True)
def world(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "FILE", tmp_path / "config.json")
    monkeypatch.setattr(faces, "FACE_DIR", tmp_path / "faces")
    monkeypatch.setattr(faces, "GALLERY_FILE", tmp_path / "faces" / faces.GALLERY_FILE.name)
    monkeypatch.setattr(faces, "face_quality", lambda image, face=None:
                        None if image is None else (0.9 if image.mean() > 100 else 0.1))
    monkeypatch.setattr(faces, "faces_in", lambda frame, sides=None, missed=None: frame)
    monkeypatch.setattr(people, "person_boxes", lambda frame: [(0, 0, 1000, 1000)])


@pytest.fixture
def sent(monkeypatch):
    notify.reset_incident()
    messages = []
    monkeypatch.setattr(notify, "_post", lambda text, image=None, settings=None, silent=False:
                        (messages.append(text), (True, "", None))[1])
    monkeypatch.setattr(notify.threading, "Thread", Inline)
    monkeypatch.setattr(notify.threading, "Timer", Timer)
    monkeypatch.setattr(notify, "_clock", lambda: 1000.0)
    yield messages
    notify.reset_incident()


@pytest.fixture
def gallery(tmp_path):
    return faces.Gallery(tmp_path / "faces" / faces.GALLERY_FILE.name)


def seen(embedding, crop, width=60):
    return {"box": (100, 100, width, width), "embedding": embedding, "score": 0.9, "crop": crop}


def scan(tmp_path, monkeypatch, gallery, frames, minutes=0, tracks=None):
    """One clip's face scan, its frames each a list of face views; the sightings it records."""
    start = START + timedelta(minutes=minutes)
    monkeypatch.setattr(faces, "_sampled_frames", lambda clip, moments=(): iter(frames))
    clip = tmp_path / "clips" / "Back" / start.strftime("%Y-%m-%d") / f"{start:%H-%M-%S}.mp4"
    clip.parent.mkdir(parents=True, exist_ok=True)
    clip.write_bytes(b"x")
    return start, faces._scan_clip(clip, "Back", start, gallery, (), tracks=tracks)


def after(start, found, people=1, best=None):
    return notify.after_scan("Back", start, found, True, False, None, best, HOME, people=people,
                             ended_at=start + timedelta(seconds=10))


def resident(gallery, embedding=GUSTAVO):
    person_id = gallery.add([embedding], "t.jpg", [GOOD])
    gallery.rename(person_id, "Gustavo")
    gallery.set_resident(person_id, True)
    return person_id


def test_add_keeps_only_the_views_at_the_cut_and_makes_no_entry_with_none(gallery):
    person_id = gallery.add([STRANGER, vector(1.0, 0.1), vector(1.0, 0.2)], "t.jpg", [POOR, GOOD, POOR])
    person = gallery.get(person_id)
    assert len(person["embeddings"]) == 1
    assert faces.cosine(person["embeddings"][0], vector(1.0, 0.1)) > 0.999
    assert len(list(gallery.view_dir.glob("*.jpg"))) == 1
    assert gallery.add([OTHER, OTHER], "t.jpg", [POOR, None]) is None
    assert len(faces.Gallery(gallery.path).people) == 1


def test_reinforce_below_the_cut_stores_nothing(gallery):
    person_id = resident(gallery)
    assert gallery.reinforce(person_id, vector(0.1, 0.0, 1.0), POOR) is False
    assert gallery.reinforce(person_id, vector(0.2, 0.0, 1.0), GOOD) is True
    assert len(faces.Gallery(gallery.path).get(person_id)["embeddings"]) == 2
    assert len(list(gallery.view_dir.glob("*.jpg"))) == 2


def test_the_cut_is_the_measured_clean_cut_rounded_up_past_the_highest_poor_view():
    assert faces.QUALITY_CUT == 0.40
    assert downloads.PINNED[downloads.EDIFFIQA][1] == downloads.EDIFFIQA_SHA256
    assert faces.QUALITY_MODEL.name == downloads.EDIFFIQA


def test_a_new_face_with_no_view_at_the_cut_is_a_sighting_of_no_entry(tmp_path, monkeypatch, gallery):
    _, [sighting] = scan(tmp_path, monkeypatch, gallery, [[seen(STRANGER, POOR)], [seen(STRANGER, POOR)]])
    assert sighting["person_id"] == "" and sighting["name"] == ""
    assert faces.Gallery(gallery.path).people == []
    [stored] = (tmp_path / "faces" / START.strftime("%Y-%m-%d")).glob("*.json")
    on_disk = json.loads(stored.read_text())
    assert on_disk["person_id"] == "" and "views" not in on_disk and "references" not in on_disk


def test_a_new_face_makes_an_entry_of_only_its_views_at_the_cut(tmp_path, monkeypatch, gallery):
    frames = [[seen(STRANGER, POOR, 90)], [seen(vector(1.0, 0.1), GOOD)], [seen(vector(1.0, 0.2), POOR)]]
    _, [sighting] = scan(tmp_path, monkeypatch, gallery, frames)
    person = faces.Gallery(gallery.path).get(sighting["person_id"])
    assert len(person["embeddings"]) == 1


def test_a_residents_sure_match_below_the_cut_is_named_and_stores_no_view(tmp_path, monkeypatch, gallery):
    person_id = resident(gallery)
    _, [sighting] = scan(tmp_path, monkeypatch, gallery, [[seen(GUSTAVO, POOR)]])
    assert sighting["person_id"] == person_id and sighting["name"] == "Gustavo"
    assert sighting["score"] >= faces.learn_threshold()
    assert len(faces.Gallery(gallery.path).get(person_id)["embeddings"]) == 1


def test_a_stranger_with_no_view_at_the_cut_sends_once_in_a_visit(tmp_path, monkeypatch, gallery, sent):
    for minutes in (0, 2):
        start, found = scan(tmp_path, monkeypatch, gallery,
                            [[seen(STRANGER, POOR)], [seen(vector(1.0, 0.05), POOR)]], minutes)
        after(start, found)
    assert len(sent) == 1 and sent[0].endswith("unknown face")
    assert faces.Gallery(gallery.path).people == []


def test_a_second_different_stranger_sends(tmp_path, monkeypatch, gallery, sent):
    start, found = scan(tmp_path, monkeypatch, gallery, [[seen(STRANGER, POOR)], [seen(STRANGER, POOR)]])
    after(start, found)
    start, found = scan(tmp_path, monkeypatch, gallery, [[seen(OTHER, POOR)], [seen(OTHER, POOR)]], 2)
    after(start, found)
    assert len(sent) == 2


def test_a_stranger_who_makes_an_entry_later_in_the_visit_is_the_same_face_again(tmp_path, monkeypatch, gallery,
                                                                                    sent):
    start, found = scan(tmp_path, monkeypatch, gallery, [[seen(STRANGER, POOR)], [seen(STRANGER, POOR)]])
    after(start, found)
    start, found = scan(tmp_path, monkeypatch, gallery, [[seen(STRANGER, GOOD)], [seen(STRANGER, GOOD)]], 2)
    assert found[0]["person_id"]
    after(start, found)
    assert len(sent) == 1


def test_a_residents_sure_match_below_the_cut_still_explains_one_body(tmp_path, monkeypatch, gallery, sent,
                                                                      caplog):
    resident(gallery)
    best = tmp_path / "best.jpg"
    best.write_bytes(b"jpg")
    start, found = scan(tmp_path, monkeypatch, gallery, [[seen(GUSTAVO, POOR)]])
    after(start, found)
    caplog.set_level("INFO")
    after(start + timedelta(minutes=2), [], best=best)
    assert sent == []
    assert any("skipped: visit (Gustavo recognized" in r.getMessage() for r in caplog.records)


def test_one_body_keeps_one_unnamed_sighting_with_or_without_an_entry(tmp_path, monkeypatch, gallery):
    frames = [[seen(STRANGER, GOOD), seen(OTHER, POOR)], [seen(STRANGER, GOOD), seen(OTHER, POOR)]]
    _, found = scan(tmp_path, monkeypatch, gallery, frames, tracks=PERSON_TRACK)
    assert len(found) == 1 and found[0]["person_id"]
    assert len(found[0]["references"]) == 2
    _, found = scan(tmp_path, monkeypatch, gallery, [[seen(vector(0, 0, 0, 1), POOR), seen(vector(0, 0, 0, 0, 1),
                                                                                           POOR)]] * 2,
                    minutes=1, tracks=PERSON_TRACK)
    assert [s["person_id"] for s in found] == [""]


def test_recordings_and_people_read_a_sighting_of_no_entry_as_an_unknown_face(tmp_path, monkeypatch, gallery):
    start, [sighting] = scan(tmp_path, monkeypatch, gallery, [[seen(STRANGER, POOR)], [seen(STRANGER, POOR)]])
    assert web._who_was_seen(start.date()) == {("Back", start.strftime("%Y-%m-%d"), start.strftime("%H-%M-%S")):
                                               ["unknown"]}
    assert [s["name"] for s in faces.list_sightings(start.date())] == ["Unknown"]
    assert notify._who(sighting) == "unknown face"
    assert notify.person_case(sighting) == "unknown_face"
    assert gallery.label("p_gone") == "?"
