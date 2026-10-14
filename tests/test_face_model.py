"""The switch to SCRFD + ArcFace: the gallery migration, old reports, and the models (R49, ARCHITECTURE 10.14)."""

import io
import json
import zipfile

import cv2
import numpy as np
import pytest

from jarvis import downloads, faces

SIZE = faces.EMBEDDING_SIZE


def photo(folder, name, value):
    """A stored view photo; value 0 stands for a photo in which SCRFD finds no face."""
    path = folder / "views" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(path), np.full((30, 30, 3), value, np.uint8))
    return f"faces\\views\\{name}"


@pytest.fixture
def embedder(monkeypatch):
    """embed_view without the networks: a vector from the photo's brightness, None for a black one."""
    def fake(image, centre=None):
        level = float(image.mean())
        return None if level < 1 else np.full(SIZE, level, np.float32)
    monkeypatch.setattr(faces, "embed_view", fake)


@pytest.fixture
def old_gallery(tmp_path):
    folder = tmp_path / "faces"
    people = [
        {"id": "p_named", "name": "Ana", "embeddings": [[0.1] * 128, [0.2] * 128, [0.3] * 128],
         "views": [photo(folder, "a1.jpg", 50), photo(folder, "a2.jpg", 0), None],
         "cover": "faces\\views\\a2.jpg",
         "pending": [{"embedding": [0.4] * 128, "view": photo(folder, "a3.jpg", 80)}]},
        {"id": "p_moved", "name": "", "embeddings": [[0.5] * 128],
         "views": [photo(folder, "b1.jpg", 0)],
         "pending": [{"embedding": [0.6] * 128, "view": photo(folder, "b2.jpg", 90)}]},
        {"id": "p_gone", "name": "", "embeddings": [[0.7] * 128], "views": [photo(folder, "c1.jpg", 0)]},
    ]
    path = folder / "gallery.json"
    path.write_text(json.dumps({"people": people}), encoding="utf-8")
    return path


def test_the_migration_builds_a_new_file_and_leaves_the_old_one(tmp_path, old_gallery, embedder):
    before = old_gallery.read_bytes()
    target = old_gallery.with_name(faces.GALLERY_FILE.name)
    counts = faces.migrate_gallery(target, backup_dir=tmp_path / "backups")
    assert old_gallery.read_bytes() == before
    assert counts["views"] == 7 and counts["kept"] == 3
    assert counts["no photo"] == 1 and counts["no face"] == 3
    assert counts["moved up"] == 1 and counts["entries dropped"] == 1
    data = json.loads(target.read_text(encoding="utf-8"))
    assert data["model"] == faces.EMBEDDING_MODEL and data["source"]["file"] == "gallery.json"
    ana, moved = data["people"]
    assert [ana["id"], moved["id"]] == ["p_named", "p_moved"]
    assert ana["views"] == ["faces\\views\\a1.jpg"] and len(ana["embeddings"][0]) == SIZE
    assert ana["cover"] == "faces\\views\\a1.jpg"
    assert [len(w["embedding"]) for w in ana["pending"]] == [SIZE]
    assert moved["views"] == ["faces\\views\\b2.jpg"] and moved["pending"] == []
    assert (old_gallery.parent / "views" / "a2.jpg").is_file()
    [backup] = (tmp_path / "backups").iterdir()
    assert (backup / "gallery.json").read_bytes() == before


def test_the_migration_runs_once_and_again_only_when_the_old_file_changes(tmp_path, old_gallery, embedder):
    target = old_gallery.with_name(faces.GALLERY_FILE.name)
    assert faces.migrate_gallery(target, backup_dir=tmp_path / "backups")
    gallery = faces.Gallery(target)
    gallery.set_resident("p_named", True)
    assert json.loads(target.read_text(encoding="utf-8"))["source"]
    assert faces.migrate_gallery(target, backup_dir=tmp_path / "backups") is None
    old = json.loads(old_gallery.read_text(encoding="utf-8"))
    old["people"][0]["name"] = "Ana Maria"
    old_gallery.write_text(json.dumps(old), encoding="utf-8")
    assert faces.migrate_gallery(target, backup_dir=tmp_path / "backups")
    assert faces.Gallery(target).get("p_named")["name"] == "Ana Maria"
    kept = [b / target.name for b in (tmp_path / "backups").iterdir() if (b / target.name).is_file()]
    assert any(json.loads(p.read_text(encoding="utf-8"))["people"][0].get("resident") for p in kept)


def test_nothing_to_migrate_without_an_old_file(tmp_path):
    assert faces.migrate_gallery(tmp_path / "faces" / faces.GALLERY_FILE.name) is None


def test_an_entry_from_the_old_model_is_embedded_again_when_put_back(tmp_path, embedder):
    folder = tmp_path / "faces"
    gallery = faces.Gallery(folder / faces.GALLERY_FILE.name)
    entry = {"id": "p_back", "name": "", "embeddings": [[0.1] * 128],
             "views": [photo(folder, "d1.jpg", 60)]}
    assert gallery.put_back(entry)
    back = faces.Gallery(gallery.path).get("p_back")
    assert [len(e) for e in back["embeddings"]] == [SIZE]


def test_embeddings_of_different_models_never_match():
    assert faces.cosine([1.0] * 128, [1.0] * SIZE) == 0.0


def test_the_models_come_from_the_release_and_the_zip_is_deleted(tmp_path, monkeypatch):
    bundle = io.BytesIO()
    with zipfile.ZipFile(bundle, "w") as archive:
        for name in (downloads.SCRFD, downloads.ARCFACE, "genderage.onnx"):
            archive.writestr(name, b"x" * 2048)
    asked = []

    def fake_download(url, target):
        asked.append(url)
        target = str(target)
        with open(target, "wb") as handle:
            handle.write(bundle.getvalue() if url == downloads.BUFFALO_URL else b"y" * 2048)

    monkeypatch.setattr(downloads.urllib.request, "urlretrieve", fake_download)
    fetched = downloads.fetch(tmp_path)
    assert set(fetched) == {downloads.YUNET, downloads.SFACE, downloads.SCRFD, downloads.ARCFACE}
    assert sorted(p.name for p in (tmp_path / downloads.BUFFALO_FOLDER).iterdir()) == sorted(downloads.BUNDLED)
    assert not list(tmp_path.glob("*.zip")) and not list(tmp_path.rglob("*.part"))
    asked.clear()
    assert downloads.fetch(tmp_path) == [] and asked == []
