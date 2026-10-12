"""R43: the page and the bot write config.json at once without losing each other's change."""

import json
import threading

import pytest

from jarvis import settings

ROUNDS = 200


@pytest.fixture(autouse=True)
def config(tmp_path, monkeypatch):
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"notify_token": "secret", "write_pin": "1234"}), encoding="utf-8")
    monkeypatch.setattr(settings, "FILE", path)
    return path


def test_two_writers_updating_different_keys_both_survive(config):
    failures = []

    def write(key, value_of):
        try:
            for index in range(ROUNDS):
                settings.update(**{key: value_of(index)})
        except Exception as problem:
            failures.append(problem)

    def read():
        for _ in range(ROUNDS):
            if settings.load()["notify_token"] != "secret":
                failures.append("a reader saw the token gone")

    threads = [threading.Thread(target=write, args=("notify_cooldown", lambda i: i)),
               threading.Thread(target=write, args=("notify_prefix", lambda i: f"p{i}")),
               threading.Thread(target=read)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    values = settings.load()
    assert failures == []
    assert values["notify_cooldown"] == ROUNDS - 1 and values["notify_prefix"] == f"p{ROUNDS - 1}"
    assert values["notify_token"] == "secret" and values["write_pin"] == "1234"
    assert [p.name for p in config.parent.iterdir()] == ["config.json"]


def test_a_key_from_a_newer_version_is_kept(config):
    config.write_text(json.dumps({"future_key": 7}), encoding="utf-8")
    settings.update(notify_prefix="x")
    assert json.loads(config.read_text(encoding="utf-8"))["future_key"] == 7
