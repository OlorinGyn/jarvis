"""A face seen only from the side still reaches the phone, in place of the best view (R30)."""

from datetime import datetime

import pytest

from jarvis import clips, faces, notify

START = datetime(2026, 10, 10, 15, 50, 37)


class Camera:
    label = "Front"

    def __init__(self, segment):
        self.segment = segment

    def covering(self, start, end):
        return [self.segment]


@pytest.fixture
def sent(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(clips, "ASSEMBLY_DELAY", 0)
    monkeypatch.setattr(clips, "_concat", lambda segments, destination: destination.write_bytes(b"x"))
    monkeypatch.setattr(faces, "scan_clip", lambda *a, **k: [])
    monkeypatch.setattr(notify, "load", lambda: {"notify_token": "x", "notify_chat": "1",
                                                 "notify_mode": "away", "notify_cooldown": 120})
    monkeypatch.setattr(notify, "side_face", lambda *a, **k: calls.append("side"))
    monkeypatch.setattr(notify, "best_view", lambda *a, **k: calls.append("best"))
    monkeypatch.setattr(notify, "faces_seen", lambda *a, **k: calls.append("faces"))
    return calls


def assemble(tmp_path, notified, side):
    destination = tmp_path / "15-50-37.mp4"
    if side:
        faces.side_view_path(destination).write_bytes(b"jpg")
    clips._assemble(Camera(tmp_path / "20261010-155030.mp4"), START, START, destination,
                    {"person"}, notified, tmp_path / "15-50-37.best.jpg")


def test_a_side_view_replaces_the_best_view(tmp_path, sent):
    assemble(tmp_path, notified=True, side=True)
    assert sent == ["side"]


def test_without_a_side_view_the_best_view_is_sent(tmp_path, sent):
    assemble(tmp_path, notified=True, side=False)
    assert sent == ["best"]


def test_neither_follows_an_event_that_was_not_notified(tmp_path, sent):
    assemble(tmp_path, notified=False, side=True)
    assert sent == []


def test_the_side_view_sits_beside_the_clip_and_moves_with_it():
    assert faces.side_view_path("clips/Front/2026-10-10/15-50-37.mp4").name == "15-50-37.side.jpg"
