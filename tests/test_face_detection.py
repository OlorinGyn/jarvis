"""Faces found on a smaller copy come back in full-frame coordinates, refined on the full frame (R31)."""

import numpy as np

from jarvis import faces


def face_at(x, y, w, h):
    """A YuNet row: box, five landmarks inside it, score."""
    landmarks = [x + 0.3 * w, y + 0.4 * h, x + 0.7 * w, y + 0.4 * h, x + 0.5 * w, y + 0.6 * h,
                 x + 0.35 * w, y + 0.8 * h, x + 0.65 * w, y + 0.8 * h]
    return np.array([x, y, w, h, *landmarks, 0.9], np.float32)


def test_a_face_found_small_is_refined_in_full_frame_coordinates(monkeypatch):
    frame = np.zeros((1080, 1920, 3), np.uint8)
    calls = []

    def detect_in(image):
        calls.append(image.shape[:2])
        if image.shape[1] == faces.DETECT_WIDTH:
            return np.array([face_at(400, 200, 30, 36)])
        return np.array([face_at(80, 80, 61, 73)])

    monkeypatch.setattr(faces, "_detect_in", detect_in)
    [face] = faces._detect(frame)
    margin = int(faces.REFINE_MARGIN * 72)
    left, top = 800 - margin, 400 - margin
    assert calls[0] == (540, 960)
    assert list(face[:4]) == [80 + left, 80 + top, 61, 73]
    assert np.allclose(face[4:14], face_at(80 + left, 80 + top, 61, 73)[4:14])


def test_a_face_that_vanishes_on_refinement_is_dropped(monkeypatch):
    frame = np.zeros((1080, 1920, 3), np.uint8)
    monkeypatch.setattr(faces, "_detect_in", lambda image: np.array([face_at(400, 200, 30, 36)])
                        if image.shape[1] == faces.DETECT_WIDTH else None)
    assert faces._detect(frame) is None


def test_a_small_frame_is_searched_as_it_is(monkeypatch):
    frame = np.zeros((480, 640, 3), np.uint8)
    seen = []
    monkeypatch.setattr(faces, "_detect_in", lambda image: seen.append(image.shape) or None)
    assert faces._detect(frame) is None and seen == [(480, 640, 3)]
