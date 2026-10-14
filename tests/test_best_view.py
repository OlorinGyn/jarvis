"""R51: a clip's face is scored, and learned, by its best-matching view, not its heaviest."""

from datetime import datetime

import numpy as np

from jarvis import faces, people

SIZE = 512
START = datetime(2026, 10, 12, 15, 44, 28)


def vector(*values):
    found = np.zeros(SIZE, np.float32)
    found[:len(values)] = values
    return (found / np.linalg.norm(found)).tolist()


KNOWN = vector(1.0)
HEAVIEST = vector(0.33, (1 - 0.33 ** 2) ** 0.5)
BEST = vector(0.45, 0.6, (1 - 0.45 ** 2 - 0.6 ** 2) ** 0.5)
CROP = np.zeros((8, 8, 3), np.uint8)


def view(embedding, width, marker):
    return {"box": (100, 100, width, width), "embedding": embedding, "score": 0.9,
            "crop": CROP + marker}


def scan(tmp_path, monkeypatch, frames):
    monkeypatch.setattr(faces, "FACE_DIR", tmp_path / "faces")
    monkeypatch.setattr(faces, "_sampled_frames", lambda clip, moments=(): iter(frames))
    monkeypatch.setattr(faces, "faces_in", lambda frame, sides=None, missed=None: frame)
    monkeypatch.setattr(people, "person_boxes", lambda frame: [(0, 0, 1000, 1000)])
    gallery = faces.Gallery(tmp_path / "faces" / faces.GALLERY_FILE.name)
    person_id = gallery.add([KNOWN], tmp_path / "thumb.jpg")
    gallery.rename(person_id, "Gustavo")
    clip = tmp_path / "15-44-28.mp4"
    clip.write_bytes(b"x")
    return person_id, gallery, faces._scan_clip(clip, "Back", START, gallery, ())


def test_a_sure_view_makes_the_sighting_sure_though_a_larger_view_is_weaker(tmp_path, monkeypatch):
    assert faces.cosine(HEAVIEST, BEST) >= faces.SAME_FACE_THRESHOLD
    person_id, gallery, [sighting] = scan(tmp_path, monkeypatch, [[view(HEAVIEST, 120, 1)], [view(BEST, 60, 2)]])
    assert sighting["person_id"] == person_id
    assert round(sighting["score"], 2) == 0.45
    assert sighting["face_width"] == 120


def test_the_view_learned_is_the_one_that_matched(tmp_path, monkeypatch):
    person_id, gallery, _ = scan(tmp_path, monkeypatch, [[view(HEAVIEST, 120, 1)], [view(BEST, 60, 2)]])
    gallery.load()
    learned = gallery.get(person_id)["embeddings"]
    assert len(learned) == 2
    assert faces.cosine(learned[-1], BEST) > 0.999


def test_a_lone_view_scores_as_before(tmp_path, monkeypatch):
    person_id, gallery, [sighting] = scan(tmp_path, monkeypatch, [[view(HEAVIEST, 120, 1)]])
    assert round(sighting["score"], 2) == 0.33
    gallery.load()
    assert len(gallery.get(person_id)["embeddings"]) == 1
