"""tools/replay_notifications.py reads a log's camera lines by their own words (R61 b)."""

import importlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
replay_notifications = importlib.import_module("replay_notifications")

LOG = """\
2026-10-16 16:00:00,100 INFO jarvis.notify: Notification Front person: sent
2026-10-16 16:00:20,100 INFO jarvis.notify: Notification Back: no picture since 15:59:10: sent
2026-10-16 16:00:40,100 INFO jarvis.notify: Notification Back person: sent silently
2026-10-16 16:10:00,100 INFO jarvis.notify: Notification Back: picture back, 10 min without: sent
"""


def test_a_camera_line_names_its_camera_without_the_colon(tmp_path):
    log = tmp_path / "jarvis.log"
    log.write_text(LOG, encoding="utf-8")
    found = replay_notifications.messages(log, None)
    assert [camera for _, camera, _, _ in found] == ["Front", "Back", "Back", "Back"]
    assert found[1][2] == "no picture since 15:59:10"


def test_a_camera_line_rings_as_camera_down_does(tmp_path, monkeypatch):
    log = tmp_path / "jarvis.log"
    log.write_text(LOG, encoding="utf-8")
    from jarvis import notify
    for name in ("_clock", "_send_logged"):
        monkeypatch.setattr(notify, name, getattr(notify, name))
    monkeypatch.setattr(notify.threading, "Timer", notify.threading.Timer)
    days = replay_notifications.replay(log, 120)
    notify.reset_incident()
    counts = next(iter(days.values()))
    assert counts["loud"] == 2 and counts["silent"] == 2 and counts["floor text"] == 1
