"""Backlog 45 step 3: the clean-up, once — the eye's verdicts, the cut for what was never read, a named entry's last view."""

import importlib
import json
import sys
from pathlib import Path

import numpy as np
import pytest

from dog_vectors import descriptor
from jarvis import dogs, faces, web

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
clean_views = importlib.import_module("clean_views")

CROP = np.full((8, 8, 3), 128, np.uint8)


def vector(index):
    found = np.zeros(512)
    found[index] = 1.0
    return found.tolist()


@pytest.fixture
def folder(tmp_path):
    (tmp_path / "faces").mkdir()
    (tmp_path / "dogs").mkdir()
    return tmp_path


@pytest.fixture
def gallery(folder):
    return faces.Gallery(folder / "faces" / faces.GALLERY_FILE.name)


def photos(gallery, person_id):
    person = faces.Gallery(gallery.path).get(person_id)
    return [faces.photo_name(v) for v in faces.views_of(person)], [faces.photo_name(w["view"]) for w in
                                                                    person.get("pending") or []]


def test_drop_views_deletes_chosen_and_waiting_views_and_their_photos(gallery):
    person_id = gallery.add([vector(i) for i in range(4)], "t.jpg", [CROP] * 4)
    gallery.rename(person_id, "Ana")
    gallery.demote_view(person_id, 3)
    chosen, waiting = photos(gallery, person_id)
    [line] = gallery.drop_views([chosen[0], waiting[0]])
    assert photos(gallery, person_id) == (chosen[1:], [])
    assert line["deleted"] == 2 and not line["removed"]
    assert sorted(p.name for p in gallery.view_dir.glob("*.jpg")) == sorted(chosen[1:])


def test_a_dry_run_writes_nothing(gallery):
    person_id = gallery.add([vector(0), vector(1)], "t.jpg", [CROP] * 2)
    chosen, _ = photos(gallery, person_id)
    before = gallery.path.read_text()
    assert gallery.drop_views(chosen, dry_run=True)[0]["removed"]
    assert gallery.path.read_text() == before and len(list(gallery.view_dir.glob("*.jpg"))) == 2


def test_an_entry_left_with_no_chosen_view_moves_its_queue_up(gallery):
    person_id = gallery.add([vector(0), vector(1), vector(2)], "t.jpg", [CROP] * 3)
    gallery.rename(person_id, "Ana")
    gallery.demote_view(person_id, 2)
    chosen, waiting = photos(gallery, person_id)
    [line] = gallery.drop_views(chosen)
    assert photos(gallery, person_id) == (waiting, []) and line["moved up"] == 1


def test_a_named_entry_keeps_its_best_view_by_the_model(gallery):
    person_id = gallery.add([vector(0), vector(1), vector(2)], "t.jpg", [CROP] * 3)
    gallery.rename(person_id, "Ana")
    chosen, _ = photos(gallery, person_id)
    scores = {chosen[0]: 0.1, chosen[1]: 0.35, chosen[2]: 0.2}
    [line] = gallery.drop_views(chosen, lambda view: scores[faces.photo_name(view)])
    assert photos(gallery, person_id) == ([chosen[1]], []) and line["spared"] == chosen[1]
    assert line["deleted"] == 2
    assert [p.name for p in gallery.view_dir.glob("*.jpg")] == [chosen[1]]


def test_an_unnamed_entry_left_with_none_is_removed_its_sightings_kept_and_its_number_freed(gallery, folder):
    person_id = gallery.add([vector(0)], "t.jpg", [CROP])
    day = folder / "faces" / "2026-11-17"
    day.mkdir()
    (day / "x.json").write_text(json.dumps({"person_id": person_id}))
    chosen, _ = photos(gallery, person_id)
    [line] = gallery.drop_views(chosen)
    assert line["removed"] and faces.Gallery(gallery.path).get(person_id) is None
    assert json.loads((day / "x.json").read_text())["person_id"] == person_id
    assert not list(gallery.view_dir.glob("*.jpg"))
    other = gallery.add([vector(1)], "t.jpg", [CROP])
    assert gallery.get(other)["temporary_name"] == "Visitor 1"


def test_the_eye_decides_what_it_read_and_the_cut_what_it_never_read(tmp_path, monkeypatch):
    photo = tmp_path / "v.jpg"
    photo.write_bytes(b"x")
    for score, verdict, reason in ((0.9, "poor", "read poor"), (0.9, "other", "read someone else's"),
                                   (0.1, "ok", "read good"), (None, "ok", "read good"),
                                   (0.39, None, "unread, below the cut"), (0.40, None, "unread, at the cut"),
                                   (None, None, "unread, no face")):
        monkeypatch.setattr(faces, "face_quality", lambda image, face=None, s=score: s)
        assert clean_views.face_judgement(photo, verdict) == (reason, score)
    assert clean_views.dog_judgement(119, None) == "unread, below the cut"
    assert clean_views.dog_judgement(120, None) == "unread, at the cut"
    assert clean_views.dog_judgement(0, "ok") == "read good"
    assert clean_views.dog_judgement(300, "poor") == "read poor"
    assert [clean_views.goes(r) for r in ("read good", "unread, at the cut", "read poor", "unread, no face")] == [
        False, False, True, True]


def test_apply_refuses_while_the_service_answers(folder, gallery, monkeypatch):
    gallery.add([vector(0)], "t.jpg", [CROP])
    monkeypatch.setattr(web, "already_running", lambda port: True)
    assert clean_views.main([str(folder), "--apply"]) == 1
    assert not (folder / "backups").exists()


def test_apply_copies_both_galleries_first_then_deletes(folder, gallery, monkeypatch, tmp_path):
    person_id = gallery.add([vector(0), vector(1)], "t.jpg", [CROP] * 2)
    gallery.rename(person_id, "Ana")
    pack = dogs.DogGallery(folder / "dogs" / dogs.GALLERY_FILE.name)
    dog_id = pack.add([descriptor(1)], "d.jpg", [CROP])
    chosen, _ = photos(gallery, person_id)
    [dog_photo], _ = photos(pack, dog_id)
    verdicts = tmp_path / "verdicts.json"
    verdicts.write_text(json.dumps({chosen[0]: "poor", chosen[1]: "ok", dog_photo: "poor"}))
    monkeypatch.setattr(web, "already_running", lambda port: False)
    assert clean_views.main([str(folder), "--apply", "--verdicts", str(verdicts)]) == 0
    [backup] = (folder / "backups").iterdir()
    assert (backup / "faces" / "views" / chosen[0]).is_file() and (backup / "dogs" / "views" / dog_photo).is_file()
    assert photos(gallery, person_id) == ([chosen[1]], [])
    assert dogs.DogGallery(pack.path).people == []
