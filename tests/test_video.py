"""Recordings play on the page: the clip is served with Range, and only from clips/ (backlog 5)."""

import pytest
from fastapi.testclient import TestClient

from jarvis import web

CLIP = bytes(range(256)) * 40


@pytest.fixture
def client(tmp_path, monkeypatch):
    folder = tmp_path / "Front" / "2026-10-10"
    folder.mkdir(parents=True)
    (folder / "15-50-37.mp4").write_bytes(CLIP)
    (tmp_path / "secret.mp4").write_bytes(b"x")
    monkeypatch.setattr(web, "CLIP_DIR", tmp_path)
    return TestClient(web.app)


def test_a_recording_is_served_whole(client):
    answer = client.get("/video/Front/2026-10-10/15-50-37.mp4")
    assert answer.status_code == 200
    assert answer.headers["content-type"] == "video/mp4" and answer.content == CLIP


def test_a_range_lets_the_browser_seek(client):
    answer = client.get("/video/Front/2026-10-10/15-50-37.mp4", headers={"Range": "bytes=1000-1099"})
    assert answer.status_code == 206
    assert answer.headers["content-range"] == f"bytes 1000-1099/{len(CLIP)}"
    assert answer.content == CLIP[1000:1100]


@pytest.mark.parametrize("path", ["/video/Front/2026-10-10/..%2F..%2Fsecret.mp4",
                                  "/video/..%2F/2026-10-10/15-50-37.mp4",
                                  "/video/Front/2026-10-10/secret.mp4",
                                  "/video/Front/2026-10-10/15-50-37.json"])
def test_nothing_outside_clips_is_served(client, path):
    assert client.get(path).status_code == 404
