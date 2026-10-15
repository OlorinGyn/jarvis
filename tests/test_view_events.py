"""R55: each view records its event, views stored before recover it, and the accuracy table leaves the probe's event out."""

import json
import os
from datetime import datetime

import cv2
import numpy as np
import pytest

from jarvis import dogs, faces, settings

EVENT = "Back/2026-10-14/11-05-41"


def unit(*values):
    vector = np.zeros(8, np.float32)
    vector[:len(values)] = values
    return (vector / np.linalg.norm(vector)).tolist()


def picture(seed):
    coarse = np.random.default_rng(seed).integers(0, 255, (6, 6, 3), np.uint8)
    return cv2.resize(coarse, (60, 60), interpolation=cv2.INTER_CUBIC)


@pytest.fixture(autouse=True)
def config(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "FILE", tmp_path / "config.json")


@pytest.fixture
def gallery(tmp_path):
    return faces.Gallery(tmp_path / "gallery.json")


def test_event_of_names_camera_day_and_time_wherever_the_clip_lives():
    assert faces.event_of("clips\\Back\\2026-10-14\\11-05-41.mp4") == EVENT
    assert faces.event_of("E:/archive/Back/2026-10-14/11-05-41.mp4") == EVENT
    assert faces.event_of(None) == "" and faces.event_of("x.mp4") == ""


def test_each_stored_view_keeps_its_event_through_moves(gallery):
    first = gallery.add([unit(1), unit(1, 0.1)], "t.jpg", [picture(1), picture(2)], EVENT)
    second = gallery.add([unit(0, 1)], "u.jpg", [picture(3)], "Front/2026-10-14/12-00-00")
    gallery.reinforce(first, unit(1, 0.2), picture(4), "Back/2026-10-14/13-00-00")
    person = faces.Gallery(gallery.path).get(first)
    assert faces.events_of(person) == [EVENT, EVENT, "Back/2026-10-14/13-00-00"]
    assert gallery.demote_view(first, 0)
    assert gallery.promote_view(first, 0)
    person = faces.Gallery(gallery.path).get(first)
    assert faces.events_of(person) == [EVENT, "Back/2026-10-14/13-00-00", EVENT]
    gallery.rename(first, "Ana")
    gallery.assign([second], first)
    person = faces.Gallery(gallery.path).get(first)
    assert faces.events_of(person)[-1] == "Front/2026-10-14/12-00-00"
    assert gallery.remove_view(first, 0)
    person = faces.Gallery(gallery.path).get(first)
    assert len(person["view_events"]) == len(person["embeddings"]) == 3


def test_a_view_stored_without_an_event_reads_as_unknown(gallery):
    person_id = gallery.add([unit(1)], "t.jpg", [picture(1)])
    person = faces.Gallery(gallery.path).get(person_id)
    assert "view_events" not in person and faces.events_of(person) == [""]


def test_accuracy_leaves_out_the_whole_event_of_each_probe(gallery):
    gallery.people = [
        {"id": "p_a", "name": "Ana", "embeddings": [unit(1, 0.1), unit(1, 0.15), unit(1, 0.9)],
         "views": ["a1.jpg", "a2.jpg", "a3.jpg"],
         "view_events": {"a1.jpg": EVENT, "a2.jpg": EVENT, "a3.jpg": "Back/2026-10-14/18-00-00"}},
        {"id": "p_b", "name": "Bia", "embeddings": [unit(0.3, 1), unit(0.2, 1)], "views": ["b1.jpg", None]},
    ]
    gallery.save()
    table = faces.accuracy(gallery, thresholds=(0.95,))
    row = table["rows"][0]
    assert table["views"] == 5 and table["unknown_events"] == 2
    assert row["named"] == 2 and row["wrong"] == 0
    gallery.people[0]["view_events"]["a2.jpg"] = "Back/2026-10-14/11-06-00"
    gallery.save()
    assert faces.accuracy(gallery, thresholds=(0.95,))["rows"][0]["named"] == 4


def test_unnamed_views_do_not_cross_toward_their_own_event(gallery):
    gallery.people = [
        {"id": "p_a", "name": "Ana", "embeddings": [unit(1), unit(0, 1)], "views": ["a1.jpg", "a2.jpg"],
         "view_events": {"a1.jpg": EVENT}},
        {"id": "p_c", "name": "", "embeddings": [unit(1, 0.1)], "views": ["c1.jpg"],
         "view_events": {"c1.jpg": EVENT}},
    ]
    gallery.save()
    assert faces.accuracy(gallery, thresholds=(0.9,))["rows"][0]["unnamed"] == 0
    del gallery.people[1]["view_events"]
    gallery.save()
    assert faces.accuracy(gallery, thresholds=(0.9,))["rows"][0]["unnamed"] == 1


def write_sighting(folder, day, name, image, clip, written=None):
    path = folder / day / f"{name}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(path.with_suffix(".jpg")), image, [cv2.IMWRITE_JPEG_QUALITY, 90])
    path.write_text(json.dumps({"clip": clip, "thumbnail": f"{name}.jpg"}), encoding="utf-8")
    if written:
        os.utime(path.with_suffix(".jpg"), (written, written))


def stored_view(gallery, image, written):
    view = gallery._store_view(image)
    photo = gallery.view_dir / faces.photo_name(view)
    os.utime(photo, (written, written))
    return view


def test_views_stored_before_recover_their_event_once(gallery, tmp_path):
    noon = datetime(2026, 10, 14, 12, 0, 0).timestamp()
    folder = tmp_path
    write_sighting(folder, "2026-10-14", "12-00-00_aaaaaa", picture(1), "clips\\Back\\2026-10-14\\12-00-00.mp4", noon)
    write_sighting(folder, "2026-10-14", "12-10-00_bbbbbb", picture(9), "clips\\Front\\2026-10-14\\12-10-00.mp4",
                   noon + 600)
    same = stored_view(gallery, picture(1), noon + 3000)
    together = stored_view(gallery, picture(2), noon + 0.5)
    lost = stored_view(gallery, picture(3), noon + 9000)
    gallery.people = [{"id": "p_a", "name": "", "embeddings": [unit(1), unit(1, 0.1), unit(1, 0.2)],
                       "views": [same, together, lost]}]
    gallery.save()
    counts = gallery.recover_events()
    assert counts == {"same picture": 1, "written together": 1, "not found": 1}
    person = faces.Gallery(gallery.path).get("p_a")
    assert faces.events_of(person) == ["Back/2026-10-14/12-00-00", "Back/2026-10-14/12-00-00", ""]
    assert faces.Gallery(gallery.path).recover_events() is None


def test_one_picture_in_two_events_falls_back_to_the_time_written(gallery, tmp_path):
    noon = datetime(2026, 10, 14, 12, 0, 0).timestamp()
    write_sighting(tmp_path, "2026-10-14", "12-00-00_aaaaaa", picture(1), "clips\\Back\\2026-10-14\\12-00-00.mp4", noon)
    write_sighting(tmp_path, "2026-10-14", "12-00-40_bbbbbb", picture(1), "clips\\Back\\2026-10-14\\12-00-40.mp4",
                   noon + 60)
    view = stored_view(gallery, picture(1), noon + 60.2)
    gallery.people = [{"id": "p_a", "name": "", "embeddings": [unit(1)], "views": [view]}]
    gallery.save()
    assert gallery.recover_events() == {"written together": 1}
    assert faces.events_of(faces.Gallery(gallery.path).get("p_a")) == ["Back/2026-10-14/12-00-40"]


def test_a_dog_crop_records_the_event_of_its_clip(tmp_path):
    gallery = dogs.DogGallery(tmp_path / "gallery.json")
    frame = np.full((200, 200, 3), (40, 90, 160), np.uint8)
    started = datetime(2026, 10, 14, 11, 5, 41)
    [dog_id] = dogs.record(frame, [(50, 50, 80, 80)], "Back", started, "clips/Back/2026-10-14/11-05-41.mp4", gallery)
    assert faces.events_of(dogs.DogGallery(gallery.path).get(dog_id)) == [EVENT]
