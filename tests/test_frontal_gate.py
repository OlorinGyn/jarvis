"""R30 (b): a face looking down, eyes closer than 0.38 of the box but at least 0.30, is recognised."""

import numpy as np

from jarvis import faces


def face(spread, offset, width=100.0, score=0.9):
    left = 50.0 - spread * width / 2
    right = 50.0 + spread * width / 2
    nose = 50.0 + offset * spread * width
    return np.array([0, 0, width, width, left, 40, right, 40, nose, 60, 40, 80, 60, 80, score], np.float32)


def test_a_face_looking_down_passes_the_gate():
    assert faces.is_frontal(face(spread=0.32, offset=0.2))
    assert faces.is_frontal(face(spread=0.30, offset=0.0))


def test_closer_eyes_or_a_turned_head_still_fail():
    assert not faces.is_frontal(face(spread=0.28, offset=0.0))
    assert not faces.is_frontal(face(spread=0.40, offset=0.4))
    assert not faces.is_frontal(face(spread=0.40, offset=0.0, score=0.5))
