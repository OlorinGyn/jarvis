"""The Notifications tab and the Resident switch, through the page's own API."""

import json

import numpy as np
import pytest
from fastapi.testclient import TestClient

from jarvis import dogs, faces, modes, settings, web

HEADER = {"X-Jarvis-Request": "1"}


@pytest.fixture(autouse=True)
def config(tmp_path, monkeypatch):
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"notify_labels": ["person"]}), encoding="utf-8")
    monkeypatch.setattr(settings, "FILE", path)
    return path


@pytest.fixture
def client():
    return TestClient(web.app, client=("127.0.0.1", 50000))


def test_the_page_gets_every_case_and_mode(client):
    values = client.get("/api/settings").json()
    assert [case for case, _ in values["notify_cases"]] == list(modes.CASES)
    assert [mode for mode, _ in values["notify_mode_names"]] == list(modes.MODES)
    assert values["notify_mode"] == "away" and values["notify_modes"] == modes.defaults(["person"])


def test_one_switch_changes_and_the_rest_stays(client, config):
    answer = client.post("/api/settings", headers=HEADER,
                         json={"notify_modes": {"home": {"other_animal": True}}})
    assert answer.status_code == 200
    stored = json.loads(config.read_text(encoding="utf-8"))["notify_modes"]
    expected = modes.defaults(["person"])
    expected["home"]["other_animal"] = True
    assert stored == expected


@pytest.mark.parametrize("payload", [{"notify_mode": "party"},
                                     {"notify_modes": {"home": {"other_animal": "yes"}}},
                                     {"notify_modes": {"party": {}}},
                                     {"notify_modes": {"home": {"nonsense": True}}},
                                     {"notify_modes": []}])
def test_bad_modes_are_refused(client, payload):
    assert client.post("/api/settings", headers=HEADER, json=payload).status_code == 400


def test_the_active_mode_changes(client):
    assert client.post("/api/settings", headers=HEADER, json={"notify_mode": "silent"}).json()["notify_mode"] == "silent"
    assert settings.load()["notify_mode"] == "silent"


@pytest.mark.parametrize("kind, gallery_class, module", [("persons", faces.Gallery, faces),
                                                         ("dogs", dogs.DogGallery, dogs)])
def test_the_resident_switch_needs_a_name(client, tmp_path, monkeypatch, kind, gallery_class, module):
    path = tmp_path / kind / "gallery.json"
    monkeypatch.setattr(module, "GALLERY_FILE", path)
    gallery = gallery_class()
    size = dogs.DESCRIPTOR_SIZE if kind == "dogs" else 128
    entry = gallery.add([[0.0] + [1.0] * (size - 1)], "t.jpg", [np.zeros((20, 20, 3), np.uint8)])
    route = f"/api/{kind}/{entry}/resident"
    assert client.post(route, headers=HEADER, json={"resident": True}).status_code == 400
    gallery.rename(entry, "Alpha")
    assert client.post(route, headers=HEADER, json={"resident": "yes"}).status_code == 400
    page = client.post(route, headers=HEADER, json={"resident": True}).json()
    assert page["resident"] is True
    assert client.get(f"/api/{kind}").json()["named"][0]["resident"] is True
