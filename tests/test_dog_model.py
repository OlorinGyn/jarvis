"""R53 step 2: the dogs move from colour histograms to DINOv2-small, in a new gallery file."""

import hashlib
import json

import cv2
import numpy as np
import pytest

from jarvis import dogs, faces, reports

CROP = np.full((60, 40, 3), (40, 120, 200), np.uint8)


def histogram(infrared):
    return [1.0 if infrared else 0.0] + [1.0 / 16] * 16 + ([0.0] * 24 if infrared else [1.0 / 16] * 16 + [0.125] * 8)


def photo(folder, name):
    (folder / "views").mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(folder / "views" / name), CROP)
    return f"dogs\\views\\{name}"


@pytest.fixture
def old_gallery(tmp_path):
    """dogs/gallery.json as the histograms left it: a named resident by day and night, an unnamed crop."""
    folder = tmp_path / "dogs"
    aurora = {"id": "d_aurora01", "name": "Aurora", "resident": True, "first_seen": "2026-10-09T10:00:00",
              "thumbnail": "dogs/2026-10-09/10-00-00_aaaaaa.jpg",
              "embeddings": [histogram(False), histogram(True), histogram(False)],
              "views": [photo(folder, "a1.jpg"), photo(folder, "a2.jpg"), "dogs\\views\\gone.jpg"],
              "cover": "dogs\\views\\a2.jpg",
              "pending": [{"embedding": histogram(True), "view": photo(folder, "a3.jpg")}]}
    unnamed = {"id": "d_unnamed1", "name": "", "first_seen": "2026-10-10T10:00:00", "thumbnail": None,
               "embeddings": [histogram(False)], "views": [photo(folder, "u1.jpg")]}
    lost = {"id": "d_lost0001", "name": "", "first_seen": "2026-10-10T11:00:00", "thumbnail": None,
            "embeddings": [histogram(False)], "views": ["dogs\\views\\nowhere.jpg"]}
    path = folder / "gallery.json"
    path.write_text(json.dumps({"people": [aurora, unnamed, lost]}), encoding="utf-8")
    return path


def test_the_migration_writes_a_new_file_and_leaves_the_old_one_as_it_was(old_gallery, tmp_path):
    before = hashlib.sha1(old_gallery.read_bytes()).hexdigest()
    target = old_gallery.with_name(dogs.GALLERY_FILE.name)
    counts = dogs.migrate_gallery(target, backup_dir=tmp_path / "backups")
    assert hashlib.sha1(old_gallery.read_bytes()).hexdigest() == before
    assert counts["views"] == 6 and counts["kept"] == 4 and counts["no photo"] == 2
    assert counts["entries dropped"] == 1 and counts["people"] == 2
    data = json.loads(target.read_text(encoding="utf-8"))
    assert data["model"] == dogs.EMBEDDING_MODEL
    assert data["source"] == {"file": "gallery.json", "sha1": before}
    aurora = next(d for d in data["people"] if d["id"] == "d_aurora01")
    assert aurora["name"] == "Aurora" and aurora["resident"] and aurora["cover"] == "dogs\\views\\a2.jpg"
    assert aurora["views"] == ["dogs\\views\\a1.jpg", "dogs\\views\\a2.jpg"]
    assert [e[0] for e in aurora["embeddings"]] == [0.0, 1.0]
    assert aurora["pending"][0]["embedding"][0] == 1.0
    assert all(len(e) == dogs.DESCRIPTOR_SIZE for d in data["people"] for e in d["embeddings"])
    backup = next((tmp_path / "backups").iterdir())
    assert backup.name.startswith(f"dogs_{dogs.EMBEDDING_MODEL}_") and (backup / "gallery.json").is_file()


def test_the_migration_runs_again_only_when_the_old_file_changes(old_gallery, tmp_path):
    target = old_gallery.with_name(dogs.GALLERY_FILE.name)
    assert dogs.migrate_gallery(target, backup_dir=tmp_path / "backups")
    assert dogs.migrate_gallery(target, backup_dir=tmp_path / "backups") is None
    old_gallery.write_text(old_gallery.read_text(encoding="utf-8") + " ", encoding="utf-8")
    assert dogs.migrate_gallery(target, backup_dir=tmp_path / "backups")


def test_the_migrated_gallery_reads_and_matches(old_gallery, tmp_path):
    target = old_gallery.with_name(dogs.GALLERY_FILE.name)
    dogs.migrate_gallery(target, backup_dir=tmp_path / "backups")
    gallery = dogs.DogGallery(target)
    view = gallery.by_name("Aurora")["embeddings"][0]
    assert dogs.match(view, gallery)["name"] == "Aurora"
    assert dogs.DogGallery(target).model == dogs.EMBEDDING_MODEL


def test_a_dog_reported_before_the_switch_comes_back_described_again(tmp_path, monkeypatch):
    monkeypatch.setattr(reports, "REPORT_DIR", tmp_path / "reports")
    gallery = dogs.DogGallery(tmp_path / "dogs" / dogs.GALLERY_FILE.name)
    old = {"id": "d_reported", "name": "", "first_seen": "2026-10-12T10:00:00", "thumbnail": None,
           "embeddings": [histogram(True)], "views": [gallery._store_view(CROP)]}
    with faces._GALLERY_LOCK:
        gallery.load()
        gallery.people.append(old)
        gallery.save()
    path = reports.report_entry(gallery, "d_reported")
    assert dogs.DogGallery(gallery.path).get("d_reported") is None
    assert not list(gallery.view_dir.glob("*.jpg"))
    assert reports.undo(path, {"dog": gallery})
    back = dogs.DogGallery(gallery.path).get("d_reported")
    assert [len(e) for e in back["embeddings"]] == [dogs.DESCRIPTOR_SIZE]
    assert back["embeddings"][0][0] == 1.0


def test_an_entry_of_this_model_is_put_back_as_it_is(tmp_path):
    gallery = dogs.DogGallery(tmp_path / "dogs" / dogs.GALLERY_FILE.name)
    entry = {"id": "d_current1", "name": "", "embeddings": [[0.0] + [1.0] + [0.0] * 383], "views": [None]}
    assert gallery.refit(entry) is entry
