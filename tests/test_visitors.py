"""Backlog 44: every unnamed face entry gets "Visitor N", N never reused; one body's unnamed entries merge."""

import json
from datetime import datetime

import numpy as np
import pytest

from jarvis import dogs, faces, notify, people, settings, web

SIZE = 512
START = datetime(2026, 11, 17, 15, 44, 28)
CROP = np.zeros((8, 8, 3), np.uint8)


def vector(*values):
    found = np.zeros(SIZE, np.float32)
    found[:len(values)] = values
    return (found / np.linalg.norm(found)).tolist()


@pytest.fixture(autouse=True)
def config(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "FILE", tmp_path / "config.json")


@pytest.fixture
def gallery(tmp_path):
    return faces.Gallery(tmp_path / "faces" / faces.GALLERY_FILE.name)


def test_each_new_unnamed_entry_is_the_next_visitor_and_a_number_is_never_reused(gallery):
    first = gallery.add([vector(1)], "t.jpg")
    second = gallery.add([vector(0, 1)], "t.jpg")
    assert gallery.get(first)["temporary_name"] == "Visitor 1"
    assert gallery.get(second)["temporary_name"] == "Visitor 2"
    gallery.take_out(second)
    third = gallery.add([vector(0, 0, 1)], "t.jpg")
    assert faces.Gallery(gallery.path).get(third)["temporary_name"] == "Visitor 3"
    assert json.loads(gallery.path.read_text())["visitors"] == 3


def test_a_temporary_name_is_not_a_name(gallery):
    person_id = gallery.add([vector(1)], "t.jpg")
    person = gallery.get(person_id)
    assert person["name"] == "" and gallery.label(person_id) == "Unknown"
    sighting = {"person_id": person_id, "name": "", "temporary_name": "Visitor 1", "score": 0.9}
    assert notify.person_case(sighting) == "unknown_face"
    assert notify._who(sighting) == "Visitor 1, unknown face"
    assert notify._who({"name": "", "score": 0.9}) == "unknown face"


def test_naming_a_visitor_keeps_views_and_drops_the_temporary_name(gallery):
    person_id = gallery.add([vector(1), vector(1, 0.1)], "t.jpg")
    gallery.rename(person_id, "Ana")
    person = faces.Gallery(gallery.path).get(person_id)
    assert person["name"] == "Ana" and "temporary_name" not in person
    assert len(person["embeddings"]) == 2


def test_naming_many_visitors_at_once_drops_the_temporary_name(gallery):
    first = gallery.add([vector(1)], "t.jpg")
    second = gallery.add([vector(0, 1)], "t.jpg")
    result = gallery.assign([first, second], full_name="Bia")
    person = faces.Gallery(gallery.path).get(result["id"])
    assert person["name"] == "Bia" and "temporary_name" not in person


def test_existing_unnamed_entries_are_named_once_in_order_of_first_sighting(gallery):
    gallery.people = [
        {"id": "p_late", "name": "", "embeddings": [vector(1)], "first_seen": "2026-11-02T10:00:00"},
        {"id": "p_named", "name": "Ana", "embeddings": [vector(0, 1)], "first_seen": "2026-10-01T10:00:00"},
        {"id": "p_early", "name": "", "embeddings": [vector(0, 0, 1)], "first_seen": "2026-10-20T10:00:00"},
    ]
    gallery.save()
    assert gallery.name_visitors() == 2
    after = faces.Gallery(gallery.path)
    assert after.get("p_early")["temporary_name"] == "Visitor 1"
    assert after.get("p_late")["temporary_name"] == "Visitor 2"
    assert "temporary_name" not in after.get("p_named")
    assert gallery.name_visitors() == 0
    assert gallery.get(gallery.add([vector(0, 0, 0, 1)], "t.jpg"))["temporary_name"] == "Visitor 3"


def test_a_file_without_the_counter_continues_after_the_highest_visitor(gallery):
    gallery.people = [{"id": "p_a", "name": "", "embeddings": [vector(1)], "temporary_name": "Visitor 7"}]
    gallery.save()
    gallery.load()
    person_id = gallery.add([vector(0, 1)], "t.jpg")
    assert gallery.get(person_id)["temporary_name"] == "Visitor 8"


def test_dogs_get_no_temporary_name(tmp_path):
    dog_gallery = dogs.DogGallery(tmp_path / "dogs" / "gallery.json")
    dog_id = dog_gallery.add([[0.5] * 8], "t.jpg")
    assert "temporary_name" not in dog_gallery.get(dog_id)
    assert dog_gallery.name_visitors() == 0


def test_the_people_card_shows_the_temporary_name(gallery):
    person_id = gallery.add([vector(1)], "t.jpg")
    assert web._card(gallery.get(person_id))["temporary_name"] == "Visitor 1"


def view(embedding, marker):
    return {"box": (100, 100, 90, 90), "embedding": embedding, "score": 0.9, "crop": CROP + marker}


def scan(tmp_path, monkeypatch, gallery, tracks):
    monkeypatch.setattr(faces, "FACE_DIR", tmp_path / "faces")
    frames = [[view(vector(1), 1), view(vector(0, 1), 2)], [view(vector(1, 0.1), 3), view(vector(0, 1, 0.1), 4)]]
    monkeypatch.setattr(faces, "_sampled_frames", lambda clip, moments=(): iter(frames))
    monkeypatch.setattr(faces, "faces_in", lambda frame, sides=None, missed=None: frame)
    monkeypatch.setattr(people, "person_boxes", lambda frame: [(0, 0, 1000, 1000)])
    clip = tmp_path / "Back" / "2026-11-17" / "15-44-28.mp4"
    clip.parent.mkdir(parents=True)
    clip.write_bytes(b"x")
    found = faces._scan_clip(clip, "Back", START, gallery, (), tracks=tracks)
    gallery.load()
    return found


def body(track_id, frames=8):
    return {"id": track_id, "first": 0.0, "last": 4.0, "frames": {"person": frames}, "longest_person_run": frames}


def test_two_new_faces_on_one_body_are_one_visitor(tmp_path, monkeypatch, gallery):
    found = scan(tmp_path, monkeypatch, gallery, [body(1)])
    assert len(gallery.people) == 1
    person = gallery.people[0]
    assert person["temporary_name"] == "Visitor 1" and len(person["embeddings"]) == 4
    assert [s["person_id"] for s in found] == [person["id"]]
    assert found[0]["temporary_name"] == "Visitor 1"
    sightings = [json.loads(p.read_text()) for p in (tmp_path / "faces" / "2026-11-17").glob("*.json")]
    assert {s["person_id"] for s in sightings} == {person["id"]}


def test_two_bodies_keep_two_visitors(tmp_path, monkeypatch, gallery):
    found = scan(tmp_path, monkeypatch, gallery, [body(1), body(2)])
    assert len(gallery.people) == 2 and len(found) == 2


def test_an_untracked_event_keeps_two_visitors(tmp_path, monkeypatch, gallery):
    found = scan(tmp_path, monkeypatch, gallery, None)
    assert len(gallery.people) == 2 and len(found) == 2


def test_one_body_groups_find_unnamed_entries_sharing_an_event(tmp_path, gallery):
    clips = tmp_path / "clips"
    for key, tracks in (("Back/2026-11-10/10-00-00", [body(1)]), ("Back/2026-11-10/11-00-00", [body(1), body(2)])):
        path = clips / f"{key}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"tracks": tracks}))
    gallery.people = [
        {"id": "p_a", "name": "", "embeddings": [vector(1)], "views": ["a.jpg"],
         "view_events": {"a.jpg": "Back/2026-11-10/10-00-00"}},
        {"id": "p_b", "name": "", "embeddings": [vector(0, 1)], "views": ["b.jpg"],
         "view_events": {"b.jpg": "Back/2026-11-10/10-00-00"}},
        {"id": "p_c", "name": "", "embeddings": [vector(0, 0, 1)], "views": ["c.jpg"],
         "view_events": {"c.jpg": "Back/2026-11-10/11-00-00"}},
        {"id": "p_d", "name": "", "embeddings": [vector(0, 0, 0, 1)], "views": ["d.jpg"],
         "view_events": {"d.jpg": "Back/2026-11-10/11-00-00"}},
    ]
    assert faces.one_body_groups(gallery, clips) == [["p_a", "p_b"]]
