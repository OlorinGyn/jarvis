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
}


def load():
    """Current settings, with any missing key filled from DEFAULTS."""
    values = dict(DEFAULTS)
    try:
        stored = json.loads(FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return values
    for key in DEFAULTS:
        if key in stored:
            values[key] = stored[key]
    return values


def save(values):
    """Write the settings back, keeping only known keys."""
    clean = {key: values.get(key, default) for key, default in DEFAULTS.items()}
    FILE.write_text(json.dumps(clean, indent=2), encoding="utf-8")
    return clean


def update(**changes):
    values = load()
    values.update(changes)
    return save(values)
