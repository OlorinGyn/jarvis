"""Devices paired once with the PIN, remembered by a cookie for 30 days that renew with use.

The PIN used to live in the browser's storage, which browsers clear (Safari
after 7 days unused, private windows, another address for the same M900).
Pairing now gives the device a random token in an HttpOnly cookie; the
server keeps only its SHA-256 hash in devices.json, with a label and the
last use. See docs/CONTEXTO.md, R34.
"""

import hashlib
import json
import secrets
import threading
from datetime import datetime, timedelta

from jarvis import ROOT

FILE = ROOT / "devices.json"
COOKIE = "jarvis_device"
DAYS = 30
LABEL_MAX = 80

_lock = threading.Lock()


def _hash(token):
    return hashlib.sha256(token.encode()).hexdigest()


def _now():
    return datetime.now()


def _load():
    try:
        data = json.loads(FILE.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return []
    devices = data.get("devices") if isinstance(data, dict) else None
    return devices if isinstance(devices, list) else []


def _save(devices):
    FILE.write_text(json.dumps({"devices": devices}, indent=2), encoding="utf-8")


def _alive(device, now):
    try:
        return now - datetime.fromisoformat(device["last_used"]) <= timedelta(days=DAYS)
    except (KeyError, TypeError, ValueError):
        return False


def pair(label):
    """Remember a new device and return the token for its cookie."""
    token = secrets.token_urlsafe(32)
    now = _now().isoformat(timespec="seconds")
    with _lock:
        devices = [d for d in _load() if _alive(d, _now())]
        devices.append({"hash": _hash(token), "label": str(label)[:LABEL_MAX],
                        "paired_at": now, "last_used": now})
        _save(devices)
    return token


def use(token):
    """Whether the token belongs to a device used in the last DAYS days; renews it if so."""
    if not token:
        return False
    wanted = _hash(token)
    with _lock:
        devices = _load()
        for device in devices:
            if secrets.compare_digest(device.get("hash", ""), wanted):
                if not _alive(device, _now()):
                    return False
                device["last_used"] = _now().isoformat(timespec="seconds")
                _save(devices)
                return True
    return False


def known(token):
    """Whether the token belongs to a valid device, without renewing it (for reads)."""
    if not token:
        return False
    wanted, now = _hash(token), _now()
    return any(secrets.compare_digest(d.get("hash", ""), wanted) and _alive(d, now) for d in _load())


def listing():
    """The paired devices still valid, for Settings: an id, the label and the dates."""
    now = _now()
    return [{"id": d["hash"][:12], "label": d.get("label", ""), "paired_at": d.get("paired_at", ""),
             "last_used": d.get("last_used", "")} for d in _load() if _alive(d, now)]


def forget(device_id=None):
    """Forget one device by its id, or every device when no id is given. Returns how many."""
    with _lock:
        devices = _load()
        kept = [d for d in devices if device_id and not d.get("hash", "").startswith(device_id)]
        _save(kept)
    return len(devices) - len(kept)
