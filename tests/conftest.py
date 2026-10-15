"""The dog network is a stand-in in every test, unless marked real_dog_model: no test downloads or loads 88 MB."""

import pytest

from dog_vectors import fake_embed
from jarvis import dogs


def pytest_configure(config):
    config.addinivalue_line("markers", "real_dog_model: runs DINOv2-small itself when models/ holds it")


@pytest.fixture(autouse=True)
def fake_dog_network(request, monkeypatch):
    if request.node.get_closest_marker("real_dog_model") is None:
        monkeypatch.setattr(dogs.Network, "embed", fake_embed)
