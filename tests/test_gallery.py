"""The gallery keeps each view's photo aligned with its embedding, and moves views between Chosen and Waiting."""

import numpy as np
import pytest

from jarvis import faces
from queues import queue

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


@pytest.fixture
def queued(gallery, monkeypatch):
    """A person with three chosen views (0, 1, 2) and two waiting (3, 4)."""
    monkeypatch.setattr(faces, "MAX_EMBEDDINGS", 3)
    person_id = gallery.add([embedding(0), embedding(1), embedding(2)], "t.jpg", [CROP] * 3)
    queue(gallery, person_id, [embedding(3), embedding(4)], CROP)
    return person_id


def chosen_and_waiting(gallery, person_id):
    person = reloaded(gallery, person_id)
    assert_aligned(person)
    assert len(photos(gallery)) == len(stored_photos(person))
    return [e[0] for e in person["embeddings"]], [w["embedding"][0] for w in person.get("pending") or []]


def test_deleting_a_chosen_view_pulls_nothing_from_waiting(gallery, queued):
    assert gallery.remove_view(queued, 0)
    assert chosen_and_waiting(gallery, queued) == ([1.0, 2.0], [3.0, 4.0])


def test_a_chosen_view_moves_down_and_a_waiting_one_moves_up(gallery, queued):
    assert gallery.demote_view(queued, 1)
    assert chosen_and_waiting(gallery, queued) == ([0.0, 2.0], [3.0, 4.0, 1.0])
    person = reloaded(gallery, queued)
    moved = person["pending"][-1]["view"]
    assert moved and moved not in faces.views_of(person)
    assert gallery.promote_view(queued, 0)
    assert chosen_and_waiting(gallery, queued) == ([0.0, 2.0, 3.0], [4.0, 1.0])


def test_moving_up_is_refused_while_chosen_is_full(gallery, queued):
    assert not gallery.promote_view(queued, 0)
    assert not gallery.promote_view(queued, 9)
    assert chosen_and_waiting(gallery, queued) == ([0.0, 1.0, 2.0], [3.0, 4.0])


def test_moving_down_is_refused_for_the_last_chosen_view_or_a_full_queue(gallery, queued, monkeypatch):
    monkeypatch.setattr(faces, "MAX_PENDING", 2)
    assert not gallery.demote_view(queued, 0)
    monkeypatch.setattr(faces, "MAX_PENDING", 100)
    assert gallery.demote_view(queued, 0) and gallery.demote_view(queued, 0)
    assert not gallery.demote_view(queued, 0)
    assert not gallery.remove_view(queued, 0)
    assert chosen_and_waiting(gallery, queued) == ([2.0], [3.0, 4.0, 0.0, 1.0])


def test_deleting_a_waiting_view_deletes_its_photo(gallery, queued):
    assert gallery.remove_waiting(queued, 1)
    assert not gallery.remove_waiting(queued, 1)
    assert chosen_and_waiting(gallery, queued) == ([0.0, 1.0, 2.0], [3.0])


def test_moving_the_favourite_down_falls_back_to_a_chosen_photo(gallery, queued):
    assert gallery.set_cover(queued, 2)
    assert gallery.demote_view(queued, 2)
    person = reloaded(gallery, queued)
    assert person["cover"] == faces.views_of(person)[0]


def test_the_last_view_with_nothing_queued_is_kept(gallery):
    person_id = gallery.add([embedding(0)], "t.jpg", [CROP])
    assert not gallery.remove_view(person_id, 0)
    assert not gallery.remove_view(person_id, 5)
    assert len(reloaded(gallery, person_id)["embeddings"]) == 1


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


def one_hot(position):
    vector = [0.0] * 128
    vector[position] = 1.0
    return vector


def test_only_a_named_entry_can_be_a_resident(gallery):
    person_id = gallery.add([one_hot(0)], "t.jpg", [CROP])
    assert not gallery.set_resident(person_id, True)
    gallery.rename(person_id, "Alpha")
    assert gallery.set_resident(person_id, True)
    assert reloaded(gallery, person_id)["resident"] is True
    assert gallery.set_resident(person_id, False)
    assert "resident" not in reloaded(gallery, person_id)


def test_renaming_keeps_the_resident_flag(gallery):
    person_id = gallery.add([one_hot(0)], "t.jpg", [CROP])
    gallery.rename(person_id, "Alpha")
    gallery.set_resident(person_id, True)
    gallery.rename(person_id, "Beta")
    assert reloaded(gallery, person_id)["resident"] is True


@pytest.mark.parametrize("source_resident, target_resident", [(True, False), (False, True), (False, False)])
def test_a_merge_is_a_resident_when_either_was(gallery, source_resident, target_resident):
    target = gallery.add([one_hot(0)], "t.jpg", [CROP])
    source = gallery.add([one_hot(1)], "s.jpg", [CROP])
    gallery.rename(target, "Alpha")
    gallery.rename(source, "Beta")
    gallery.set_resident(target, target_resident)
    gallery.set_resident(source, source_resident)
    gallery.rename(source, "Alpha")
    merged = faces.Gallery(gallery.path).by_name("Alpha")
    assert merged["id"] == target
    assert bool(merged.get("resident")) == (source_resident or target_resident)
