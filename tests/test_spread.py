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


def test_discarding_the_rest_deletes_the_views_not_kept(crowded):
    gallery, person_id = crowded
    proposal = gallery.spread_proposal(person_id)
    assert gallery.keep_spread(person_id, proposal["keep"], proposal["signature"], discard=True)
    after = gallery.get(person_id)
    assert len(after["embeddings"]) == faces.MAX_EMBEDDINGS and after["pending"] == []
    assert {path.name for path in gallery.view_dir.glob("*.jpg")} == {
        web._stored_file(view).name for view in faces.views_of(after)}


def test_the_web_moves_views_between_chosen_and_waiting(crowded, monkeypatch):
    gallery, person_id = crowded
    monkeypatch.setattr(faces, "GALLERY_FILE", gallery.path)
    client = TestClient(web.app, client=("127.0.0.1", 50000))
    route = f"/api/persons/{person_id}"
    page = client.get(route).json()
    assert len(page["view_photos"]) == 40 and len(page["pending_photos"]) == 60
    refused = client.post(f"{route}/pending/0/promote", headers=HEADER)
    assert refused.status_code == 400 and "full" in refused.json()["detail"]
    page = client.post(f"{route}/views/0/demote", headers=HEADER).json()
    assert (page["views"], page["pending"]) == (39, 61)
    page = client.post(f"{route}/pending/60/promote", headers=HEADER).json()
    assert (page["views"], page["pending"]) == (40, 60)
    page = client.post(f"{route}/pending/0/remove", headers=HEADER).json()
    assert (page["views"], page["pending"]) == (40, 59)
    page = client.post(f"{route}/views/0/remove", headers=HEADER).json()
    assert (page["views"], page["pending"]) == (39, 59)
    assert client.post(f"{route}/pending/99/remove", headers=HEADER).status_code == 400
    proposal = client.get(f"{route}/spread").json()
    page = client.post(f"{route}/spread", json={"keep": proposal["keep"], "signature": proposal["signature"],
                                                "discard": True}, headers=HEADER).json()
    assert (page["views"], page["pending"]) == (40, 0)
