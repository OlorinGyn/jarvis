"""Settings the user changes while the program runs.

Separate from .env on purpose: .env holds camera credentials, written once by
hand. This holds choices made in the interface, so it has to be readable and
writable at runtime.

See docs/ARQUITETURA.md section 11.
"""

import json

from . import ROOT

FILE = ROOT / "config.json"

DEFAULTS = {
    "archive_path": "",
    "archive_after_days": 30,
    "archive_min_free_gb": 10.0,
    "notify_token": "",
    "notify_chat": "",
    "notify_labels": ["person"],
    "notify_cooldown": 120,
    "notify_prefix": "",
    "write_pin": "",
}


def _stored():
    """Everything config.json holds, or an empty dict when it cannot be read."""
    try:
        stored = json.loads(FILE.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return {}
    return stored if isinstance(stored, dict) else {}


def load():
    """Current settings, with any missing key filled from DEFAULTS."""
    values = dict(DEFAULTS)
    stored = _stored()
    for key in DEFAULTS:
        if key in stored:
            values[key] = stored[key]
    return values


def save(values):
    """Write the known settings back; keys this version does not know stay as they were.

    A newer version may have added keys. Dropping them here, after a rollback
    or from any older copy that saves, would erase what the user set there.
    """
    clean = {key: values.get(key, default) for key, default in DEFAULTS.items()}
    kept = {key: value for key, value in _stored().items() if key not in DEFAULTS}
    FILE.write_text(json.dumps({**clean, **kept}, indent=2), encoding="utf-8")
    return clean


def update(**changes):
    values = load()
    values.update(changes)
    return save(values)
