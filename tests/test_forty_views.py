"""Once Chosen holds 40 views, a new one enters only if it makes them more varied (backlog 28)."""

import importlib
import json
import sys
from pathlib import Path

import numpy as np
import pytest

from jarvis import dogs, faces
from queues import queue

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
settle_waiting = importlib.import_module("settle_waiting")

CROP = np.zeros((20, 20, 3), np.uint8)


def unit(rng):
    vector = rng.normal(size=128)
    return (vector / np.linalg.norm(vector)).tolist()


def photos(gallery):
    return {path.name for path in gallery.view_dir.glob("*.jpg")}


def named(person):
    return {Path(v).name for v in faces.views_of(person) if v}


@pytest.fixture
def full(tmp_path):
    """A person with 40 varied chosen views, the last two an identical pair."""
    rng = np.random.default_rng(5)
    views = [unit(rng) for _ in range(39)]
    gallery = faces.Gallery(tmp_path / "gallery.json")
    person_id = gallery.add(views + [list(views[-1])], "t.jpg", [CROP] * 40)
    return gallery, person_id, rng


def test_a_near_copy_is_discarded_with_its_photo(tmp_path):
    rng = np.random.default_rng(3)
    gallery = faces.Gallery(tmp_path / "gallery.json")
    person_id = gallery.add([unit(rng) for _ in range(40)], "t.jpg", [CROP] * 40)
    before = faces.Gallery(gallery.path).get(person_id)
    copy = (np.array(before["embeddings"][3]) + rng.normal(scale=0.001, size=128)).tolist()
    gallery.reinforce(person_id, copy, CROP)
    after = faces.Gallery(gallery.path).get(person_id)
    assert after["embeddings"] == before["embeddings"] and not after.get("pending")
    assert photos(gallery) == named(after)


def test_even_a_near_copy_replaces_an_identical_pair(full):
    gallery, person_id, rng = full
    before = faces.Gallery(gallery.path).get(person_id)
    copy = (np.array(before["embeddings"][3]) + rng.normal(scale=0.001, size=128)).tolist()
    gallery.reinforce(person_id, copy, CROP)
    assert faces.Gallery(gallery.path).get(person_id)["embeddings"][-1] == copy
    gallery.reinforce(person_id, list(before["embeddings"][3]), CROP)
    assert faces.Gallery(gallery.path).get(person_id)["embeddings"][-1] == copy


def test_a_varied_view_replaces_one_of_the_closest_pair(full):
    gallery, person_id, rng = full
    before = faces.Gallery(gallery.path).get(person_id)
    new = unit(rng)
    gallery.reinforce(person_id, new, CROP)
    after = faces.Gallery(gallery.path).get(person_id)
    assert len(after["embeddings"]) == faces.MAX_EMBEDDINGS and not after.get("pending")
    assert after["embeddings"][-1] == new
    assert after["embeddings"][:-1] == before["embeddings"][:38] + before["embeddings"][39:]
    assert photos(gallery) == named(after)


def test_the_favourite_is_never_the_one_replaced(full):
    gallery, person_id, rng = full
    assert gallery.set_cover(person_id, 38)
    cover = faces.Gallery(gallery.path).get(person_id)["cover"]
    gallery.reinforce(person_id, unit(rng), CROP)
    after = faces.Gallery(gallery.path).get(person_id)
    assert after["cover"] == cover and cover in faces.views_of(after)
    assert len(faces.views_of(after)) == faces.MAX_EMBEDDINGS


def test_a_merge_past_forty_keeps_forty_and_queues_nothing(tmp_path):
    rng = np.random.default_rng(9)
    gallery = faces.Gallery(tmp_path / "gallery.json")
    target = gallery.add([unit(rng) for _ in range(35)], "t.jpg", [CROP] * 35)
    source = gallery.add([unit(rng) for _ in range(12)], "s.jpg", [CROP] * 12)
    queue(gallery, source, [unit(rng) for _ in range(3)], CROP)
    gallery.rename(target, "Alpha")
    gallery.rename(source, "Alpha")
    merged = faces.Gallery(gallery.path)
    person = merged.by_name("Alpha")
    assert len(merged.people) == 1
    assert len(person["embeddings"]) == faces.MAX_EMBEDDINGS and not person.get("pending")
    assert photos(gallery) == named(person)


def dog_view(rng, infrared):
    vector = rng.normal(size=dogs.EMBEDDING_SIZE)
    return [1.0 if infrared else 0.0] + (vector / np.linalg.norm(vector)).tolist()


@pytest.fixture
def dog(tmp_path):
    """A dog with 36 day views and an identical day pair, then an identical night pair."""
    rng = np.random.default_rng(11)
    day = [dog_view(rng, False) for _ in range(37)]
    night = dog_view(rng, True)
    gallery = dogs.DogGallery(tmp_path / "gallery.json")
    dog_id = gallery.add(day + [list(day[-1]), night, list(night)], "t.jpg", [CROP] * 40)
    return gallery, dog_id, rng


def lightings(entry):
    return [view[0] for view in entry["embeddings"]]


def test_a_day_view_only_replaces_a_day_view(dog):
    gallery, dog_id, rng = dog
    gallery.reinforce(dog_id, dog_view(rng, False), CROP)
    after = gallery.get(dog_id)
    assert lightings(after).count(1.0) == 2 and len(after["embeddings"]) == 40
    assert len({json.dumps(view) for view in after["embeddings"]}) == 39


def test_a_night_copy_is_discarded_and_a_new_night_view_replaces_the_night_pair(dog):
    gallery, dog_id, rng = dog
    before = gallery.get(dog_id)["embeddings"]
    gallery.reinforce(dog_id, list(before[-1]), CROP)
    assert gallery.get(dog_id)["embeddings"] == before
    gallery.reinforce(dog_id, dog_view(rng, True), CROP)
    after = gallery.get(dog_id)
    assert lightings(after).count(1.0) == 2 and after["embeddings"][:38] == before[:38]
    assert photos(gallery) == named(after)


def test_a_first_night_view_counts_as_different(tmp_path):
    rng = np.random.default_rng(13)
    day = [dog_view(rng, False) for _ in range(39)]
    gallery = dogs.DogGallery(tmp_path / "gallery.json")
    dog_id = gallery.add(day + [list(day[0])], "t.jpg", [CROP] * 40)
    gallery.reinforce(dog_id, dog_view(rng, True), CROP)
    after = gallery.get(dog_id)
    assert lightings(after).count(1.0) == 1 and len(after["embeddings"]) == 40


@pytest.fixture
def waiting(tmp_path, monkeypatch):
    """Both galleries as older versions left them: full Chosen and a Waiting queue each."""
    monkeypatch.setattr(faces, "GALLERY_FILE", tmp_path / "faces" / "gallery.json")
    monkeypatch.setattr(dogs, "GALLERY_FILE", tmp_path / "dogs" / "gallery.json")
    monkeypatch.setattr(settle_waiting, "BACKUP_DIR", tmp_path / "backups")
    monkeypatch.setattr(settle_waiting.web, "already_running", lambda port: False)
    rng = np.random.default_rng(17)
    people = faces.Gallery()
    views = [unit(rng) for _ in range(39)]
    person_id = people.add(views + [list(views[0])], "t.jpg", [CROP] * 40)
    queue(people, person_id, [unit(rng) for _ in range(5)] + [list(views[5])], CROP)
    pack = dogs.DogGallery()
    dog_id = pack.add([dog_view(rng, False) for _ in range(40)], "t.jpg", [CROP] * 40)
    queue(pack, dog_id, [dog_view(rng, True), dog_view(rng, False)], CROP)
    return tmp_path, people, person_id, pack, dog_id


def snapshot(folder):
    return {path: path.read_bytes() for path in sorted(folder.rglob("*")) if path.is_file()}


def test_the_dry_run_changes_nothing(waiting, capsys):
    folder, *_ = waiting
    before = snapshot(folder)
    assert settle_waiting.main(["--dry-run"]) == 0
    assert snapshot(folder) == before
    printed = capsys.readouterr().out
    assert "6 waiting:" in printed and "2 waiting:" in printed


def test_the_real_run_backs_up_then_empties_every_queue(waiting):
    folder, people, person_id, pack, dog_id = waiting
    assert settle_waiting.main([]) == 0
    backup = next((folder / "backups").iterdir())
    assert (backup / "faces" / "gallery.json").exists() and (backup / "dogs" / "gallery.json").exists()
    for gallery, entry_id in ((faces.Gallery(), person_id), (dogs.DogGallery(), dog_id)):
        entry = gallery.get(entry_id)
        assert entry["pending"] == [] and len(entry["embeddings"]) == 40
        assert photos(gallery) == named(entry)
    assert not any(row for row in faces.Gallery().settle_waiting(dry_run=True))


def test_the_real_run_refuses_while_running(waiting, monkeypatch):
    folder, *_ = waiting
    monkeypatch.setattr(settle_waiting.web, "already_running", lambda port: True)
    before = snapshot(folder)
    assert settle_waiting.main([]) == 1
    assert snapshot(folder) == before
