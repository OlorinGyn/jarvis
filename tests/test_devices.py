"""A device paired once with the PIN stays paired by cookie for 30 days that renew with use (R34)."""

import json
from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from jarvis import devices, settings, web

HEADER = {"X-Jarvis-Request": "1"}
PIN = {**HEADER, "X-Jarvis-Pin": "482913"}


@pytest.fixture(autouse=True)
def files(tmp_path, monkeypatch):
    config = tmp_path / "config.json"
    config.write_text(json.dumps({"write_pin": "482913"}), encoding="utf-8")
    monkeypatch.setattr(settings, "FILE", config)
    monkeypatch.setattr(devices, "FILE", tmp_path / "devices.json")


def remote():
    return TestClient(web.app, client=("192.168.0.50", 50000))


def local():
    return TestClient(web.app, client=("127.0.0.1", 50000))


def paired_token():
    answer = remote().post("/api/pair", headers=PIN)
    assert answer.status_code == 200
    cookie = answer.cookies.get(devices.COOKIE)
    assert cookie and "httponly" in answer.headers["set-cookie"].lower()
    return cookie


def with_cookie(token):
    client = remote()
    client.cookies.set(devices.COOKIE, token)
    return client


def test_a_paired_device_writes_without_the_pin_after_a_restart():
    token = paired_token()
    stored = json.loads(devices.FILE.read_text(encoding="utf-8"))["devices"]
    assert len(stored) == 1 and token not in json.dumps(stored)
    assert with_cookie(token).post("/api/pair", headers=HEADER).status_code == 200
    assert remote().post("/api/pair", headers=HEADER).status_code == 403


def test_the_cookie_still_needs_the_request_header():
    assert with_cookie(paired_token()).post("/api/pair").status_code == 403


def test_a_device_unused_for_30_days_is_asked_again(monkeypatch):
    token = paired_token()
    later = datetime.now() + timedelta(days=devices.DAYS + 1)
    monkeypatch.setattr(devices, "_now", lambda: later)
    assert with_cookie(token).post("/api/pair", headers=HEADER).status_code == 403


def test_every_write_renews_the_30_days(monkeypatch):
    token = paired_token()
    start = datetime.now()
    monkeypatch.setattr(devices, "_now", lambda: start + timedelta(days=20))
    assert with_cookie(token).post("/api/pair", headers=HEADER).status_code == 200
    monkeypatch.setattr(devices, "_now", lambda: start + timedelta(days=45))
    assert with_cookie(token).post("/api/pair", headers=HEADER).status_code == 200


def test_a_forgotten_device_is_refused():
    token = paired_token()
    listed = local().get("/api/settings").json()["devices"]
    assert len(listed) == 1
    assert remote().post(f"/api/devices/{listed[0]['id']}/forget", headers=PIN).status_code == 403
    assert local().post(f"/api/devices/{listed[0]['id']}/forget", headers=HEADER).status_code == 200
    assert with_cookie(token).post("/api/pair", headers=HEADER).status_code == 403


def test_changing_the_pin_forgets_every_device():
    token = paired_token()
    answer = local().post("/api/pin", headers=HEADER, json={"pin": "111222"})
    assert answer.json()["forgotten"] == 1
    assert with_cookie(token).post("/api/pair", headers=HEADER).status_code == 403


def test_the_device_list_is_only_shown_on_the_m900():
    paired_token()
    assert remote().get("/api/settings").json()["devices"] == []
    assert local().get("/api/settings").json()["devices"][0]["label"].startswith("192.168.0.50")
