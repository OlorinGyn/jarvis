"""Stand-ins in every test: the dog network unless marked real_dog_model, and the face quality model.

No test downloads or loads 88 MB; and every face photo passes the quality cut
unless a test puts its own face_quality in place (backlog 45).
"""

import pytest

from dog_vectors import fake_embed
from jarvis import dogs, faces


def pytest_configure(config):
    config.addinivalue_line("markers", "real_dog_model: runs DINOv2-small itself when models/ holds it")


@pytest.fixture(autouse=True)
def fake_dog_network(request, monkeypatch):
    if request.node.get_closest_marker("real_dog_model") is None:
        monkeypatch.setattr(dogs.Network, "embed", fake_embed)


@pytest.fixture(autouse=True)
def impeccable_faces(monkeypatch):
    monkeypatch.setattr(faces, "face_quality", lambda image, face=None: 1.0)
