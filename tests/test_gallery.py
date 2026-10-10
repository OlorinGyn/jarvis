"""The gallery keeps each view's photo aligned with its embedding, and queues what does not fit."""

import numpy as np
import pytest

from jarvis import faces

CROP = np.zeros((40, 40, 3), np.uint8)


def embedding(value):
    return [float(value)] * 128


@pytest.fixture
def gallery(tmp_path):
    return faces.Gallery(tmp_path / "gallery.json")


def reloaded(gallery, person_id):
    return faces.Gallery(gallery.path).get(person_id)


def assert_aligned(person):
    assert len(person.get("views") or []) <= len(person["embeddings"])
    assert len(faces.views_of(person)) == len(person["embeddings"])


def photos(gallery):
    return sorted(gallery.view_dir.glob("*.jpg"))


def stored_photos(person):
    return [v for v in faces.views_of(person) if v] + [w["view"] for w in person.get("pending", []) if w["view"]]


def test_add_stores_one_photo_per_view(gallery):
    person_id = gallery.add([embedding(1), embedding(2)], "t.jpg", [CROP, None])
    person = reloaded(gallery, person_id)
    assert_aligned(person)
    assert [bool(v) for v in faces.views_of(person)] == [True, False]
    assert len(photos(gallery)) == 1


def test_a_person_stored_before_views_reads_as_no_photo(gallery):
    gallery.people = [{"id": "p_00000001", "name": "Old", "embeddings": [embedding(1)] * 3}]
    gallery.save()
    person = reloaded(gallery, "p_00000001")
    assert faces.views_of(person) == [None, None, None]
    gallery.reinforce("p_00000001", embedding(2), CROP)
    person = reloaded(gallery, "p_00000001")
    assert_aligned(person)
    assert [bool(v) for v in faces.views_of(person)] == [False, False, False, True]


def test_views_past_the_limit_wait_in_a_queue(gallery):
    person_id = gallery.add([embedding(0)], "t.jpg", [CROP])
    for value in range(1, faces.MAX_EMBEDDINGS + 5):
        gallery.reinforce(person_id, embedding(value), CROP)
    person = reloaded(gallery, person_id)
    assert_aligned(person)
    assert len(person["embeddings"]) == faces.MAX_EMBEDDINGS
    assert len(person["pending"]) == 5
    assert len(photos(gallery)) == len(stored_photos(person))


def test_the_queue_is_capped_and_its_dropped_photos_deleted(gallery, monkeypatch):
    monkeypatch.setattr(faces, "MAX_EMBEDDINGS", 2)
    monkeypatch.setattr(faces, "MAX_PENDING", 3)
    person_id = gallery.add([embedding(0)], "t.jpg", [CROP])
    for value in range(1, 10):
        gallery.reinforce(person_id, embedding(value), CROP)
    person = reloaded(gallery, person_id)
    assert [w["embedding"][0] for w in person["pending"]] == [6.0, 7.0, 8.0, 9.0][-3:]
    assert len(photos(gallery)) == len(stored_photos(person))


def test_removing_a_view_pulls_the_oldest_waiting_one(gallery, monkeypatch):
    monkeypatch.setattr(faces, "MAX_EMBEDDINGS", 3)
    person_id = gallery.add([embedding(0), embedding(1), embedding(2)], "t.jpg", [CROP] * 3)
    gallery.reinforce(person_id, embedding(3), CROP)
    gallery.reinforce(person_id, embedding(4), CROP)
    assert gallery.remove_view(person_id, 0)
    person = reloaded(gallery, person_id)
    assert_aligned(person)
    assert [e[0] for e in person["embeddings"]] == [1.0, 2.0, 3.0]
    assert [w["embedding"][0] for w in person["pending"]] == [4.0]
    assert len(photos(gallery)) == len(stored_photos(person))


def test_the_last_view_with_nothing_queued_is_kept(gallery):
    person_id = gallery.add([embedding(0)], "t.jpg", [CROP])
    assert not gallery.remove_view(person_id, 0)
    assert not gallery.remove_view(person_id, 5)
    assert len(reloaded(gallery, person_id)["embeddings"]) == 1


def test_a_merge_keeps_every_view_aligned_and_queues_the_overflow(gallery, monkeypatch):
    monkeypatch.setattr(faces, "MAX_EMBEDDINGS", 4)
    target = gallery.add([embedding(0), embedding(1), embedding(2)], "t.jpg", [CROP, None, CROP])
    source = gallery.add([embedding(5), embedding(6)], "s.jpg", [None, CROP])
    gallery.rename(target, "Alpha")
    gallery.rename(source, "Alpha")
    merged = faces.Gallery(gallery.path)
    assert len(merged.people) == 1
    person = merged.by_name("Alpha")
    assert_aligned(person)
    assert [e[0] for e in person["embeddings"]] == [0.0, 1.0, 2.0, 5.0]
    assert [bool(v) for v in faces.views_of(person)] == [True, False, True, False]
    assert [(w["embedding"][0], bool(w["view"])) for w in person["pending"]] == [(6.0, True)]
    assert len(photos(gallery)) == len(stored_photos(person))


def test_a_merge_also_carries_the_source_queue(gallery, monkeypatch):
    monkeypatch.setattr(faces, "MAX_EMBEDDINGS", 2)
    target = gallery.add([embedding(0), embedding(1)], "t.jpg", [CROP, CROP])
    source = gallery.add([embedding(5), embedding(6)], "s.jpg", [CROP, CROP])
    gallery.reinforce(source, embedding(7), CROP)
    gallery.rename(target, "Alpha")
    gallery.rename(source, "Alpha")
    person = faces.Gallery(gallery.path).by_name("Alpha")
    assert_aligned(person)
    assert [w["embedding"][0] for w in person["pending"]] == [5.0, 6.0, 7.0]
    assert len(photos(gallery)) == len(stored_photos(person))


def test_the_favourite_must_be_a_view_with_a_photo(gallery):
    person_id = gallery.add([embedding(0), embedding(1)], "t.jpg", [None, CROP])
    assert not gallery.set_cover(person_id, 0)
    assert not gallery.set_cover(person_id, 9)
    assert gallery.set_cover(person_id, 1)
    person = reloaded(gallery, person_id)
    assert faces.cover_of(person) == faces.views_of(person)[1]


def test_removing_the_favourite_falls_back_to_the_first_view_with_a_photo(gallery):
    person_id = gallery.add([embedding(0), embedding(1), embedding(2)], "t.jpg", [None, CROP, CROP])
    gallery.set_cover(person_id, 2)
    first_photo = faces.views_of(reloaded(gallery, person_id))[1]
    assert gallery.remove_view(person_id, 2)
    assert faces.cover_of(reloaded(gallery, person_id)) == first_photo


def test_removing_the_only_photo_clears_the_favourite(gallery):
    person_id = gallery.add([embedding(0), embedding(1)], "t.jpg", [CROP, None])
    gallery.set_cover(person_id, 0)
    assert gallery.remove_view(person_id, 0)
    person = reloaded(gallery, person_id)
    assert "cover" not in person and faces.cover_of(person) is None


def test_a_merge_keeps_the_target_favourite(gallery):
    target = gallery.add([embedding(0)], "t.jpg", [CROP])
    source = gallery.add([embedding(5)], "s.jpg", [CROP])
    gallery.set_cover(target, 0)
    gallery.set_cover(source, 0)
    kept = faces.views_of(reloaded(gallery, target))[0]
    gallery.rename(target, "Alpha")
    gallery.rename(source, "Alpha")
    assert faces.cover_of(faces.Gallery(gallery.path).by_name("Alpha")) == kept


def test_a_favourite_that_is_no_longer_a_view_is_ignored():
    assert faces.cover_of({"embeddings": [embedding(0)], "views": ["a.jpg"], "cover": "b.jpg"}) is None
    assert faces.cover_of({"embeddings": [embedding(0)]}) is None
