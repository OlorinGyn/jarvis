"""Choosing the 40 most different views keeps every view and spreads the kept ones (backlog 24)."""

import json

import numpy as np
import pytest
from fastapi.testclient import TestClient

from jarvis import dogs, faces, web

CROP = np.zeros((40, 40, 3), np.uint8)
HEADER = {"X-Jarvis-Request": "1"}


def near_copies(rng, count):
    base = rng.normal(size=128)
    return [(base + rng.normal(scale=0.02, size=128)).tolist() for _ in range(count)]


def varied(rng, count):
    return [rng.normal(size=128).tolist() for _ in range(count)]


@pytest.fixture
def crowded(tmp_path):
    """A person whose 40 views are near-copies, with 60 varied views waiting in the queue."""
    rng = np.random.default_rng(7)
    gallery = faces.Gallery(tmp_path / "gallery.json")
    person_id = gallery.add(near_copies(rng, 40), "t.jpg", [CROP] * 40)
    for embedding in varied(rng, 60):
        gallery.reinforce(person_id, embedding, CROP)
    return gallery, person_id


def as_set(person):
    return {json.dumps(e) for e in person["embeddings"]} | {json.dumps(w["embedding"]) for w in person["pending"]}


def test_the_kept_views_are_more_varied_and_nothing_is_lost(crowded):
    gallery, person_id = crowded
    before = faces.Gallery(gallery.path).get(person_id)
    proposal = gallery.spread_proposal(person_id)
    assert len(proposal["keep"]) == faces.MAX_EMBEDDINGS and len(proposal["views"]) == 100
    assert proposal["closest_now"] < 0.01 and proposal["closest_after"] > 0.5
    assert gallery.keep_spread(person_id, proposal["keep"], proposal["signature"])
    after = faces.Gallery(gallery.path).get(person_id)
    assert len(after["embeddings"]) == faces.MAX_EMBEDDINGS and len(after["pending"]) == 60
    assert as_set(after) == as_set(before)
    assert len(faces.views_of(after)) == len(after["embeddings"])
    photos = {v for v in faces.views_of(after)} | {w["view"] for w in after["pending"]}
    assert len(photos) == 100 and all(p for p in photos)


def test_the_favourite_photo_is_always_kept(crowded):
    gallery, person_id = crowded
    gallery.set_cover(person_id, 17)
    cover = gallery.get(person_id)["cover"]
    proposal = gallery.spread_proposal(person_id)
    assert 17 in proposal["keep"]
    assert gallery.keep_spread(person_id, proposal["keep"], proposal["signature"])
    assert faces.Gallery(gallery.path).get(person_id)["cover"] == cover


def test_a_stale_proposal_is_refused(crowded):
    gallery, person_id = crowded
    proposal = gallery.spread_proposal(person_id)
    gallery.reinforce(person_id, [0.5] * 128, CROP)
    assert not gallery.keep_spread(person_id, proposal["keep"], proposal["signature"])
    assert not gallery.keep_spread(person_id, proposal["keep"][:39], gallery.spread_proposal(person_id)["signature"])


def test_nothing_to_choose_when_every_view_fits(tmp_path):
    gallery = faces.Gallery(tmp_path / "gallery.json")
    person_id = gallery.add(varied(np.random.default_rng(1), 5), "t.jpg")
    assert gallery.spread_proposal(person_id) is None


def dog_view(infrared, tone):
    tones = [0.0] * dogs.TONE_BINS
    tones[tone] = 1.0
    colour = [0.0] * (dogs.HUE_BINS + dogs.SATURATION_BINS) if infrared else [1.0 / dogs.HUE_BINS] * dogs.HUE_BINS + [1.0 / dogs.SATURATION_BINS] * dogs.SATURATION_BINS
    return [1.0 if infrared else 0.0] + tones + colour


def test_a_dog_keeps_both_day_and_night(tmp_path):
    gallery = dogs.DogGallery(tmp_path / "gallery.json")
    dog_id = gallery.add([dog_view(False, 12)] * 40, "t.jpg")
    for _ in range(5):
        gallery.reinforce(dog_id, dog_view(False, 3))
    gallery.reinforce(dog_id, dog_view(True, 12))
    proposal = gallery.spread_proposal(dog_id)
    kept = [gallery.get(dog_id)["embeddings"][i] if i < 40 else gallery.get(dog_id)["pending"][i - 40]["embedding"]
            for i in proposal["keep"]]
    assert any(view[0] == 1.0 for view in kept)
    assert any(view[1 + 3] == 1.0 for view in kept)


def test_the_web_analyses_and_keeps(crowded, monkeypatch):
    gallery, person_id = crowded
    monkeypatch.setattr(faces, "GALLERY_FILE", gallery.path)
    client = TestClient(web.app, client=("127.0.0.1", 50000))
    proposal = client.get(f"/api/persons/{person_id}/spread").json()
    assert len(proposal["photos"]) == 100 and "views" not in proposal
    route = f"/api/persons/{person_id}/spread"
    assert client.post(route, json={"keep": proposal["keep"], "signature": "x"}, headers=HEADER).status_code == 409
    answer = client.post(route, json={"keep": proposal["keep"], "signature": proposal["signature"]}, headers=HEADER)
    assert answer.status_code == 200 and answer.json()["views"] == 40 and answer.json()["pending"] == 60
