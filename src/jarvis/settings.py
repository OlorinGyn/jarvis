"""Settings the user changes while the program runs.

Separate from .env on purpose: .env holds camera credentials, written once by
hand. This holds choices made in the interface, so it has to be readable and
writable at runtime.

See docs/ARQUITETURA.md section 11.
"""

import json
import os
import threading
import time

from . import ROOT, modes

FILE = ROOT / "config.json"
REPLACE_ATTEMPTS = 50
REPLACE_PAUSE = 0.01

_LOCK = threading.RLock()

DEFAULTS = {
    "archive_path": "",
    "archive_after_days": 30,
    "archive_min_free_gb": 10.0,
    "notify_token": "",
    "notify_chat": "",
    "notify_labels": ["person"],
    "notify_cooldown": 120,
    "notify_prefix": "",
    "notify_mode": modes.DEFAULT_MODE,
    "notify_modes": None,
    "write_pin": "",
}


def _stored():
    """Everything config.json holds, or an empty dict when it cannot be read.

    A read that meets the moment another thread replaces the file is refused
    by Windows, so it is retried for a moment instead of answering {}.
    """
    for attempt in range(REPLACE_ATTEMPTS):
        try:
            stored = json.loads(FILE.read_text(encoding="utf-8-sig"))
            break
        except PermissionError:
            if attempt == REPLACE_ATTEMPTS - 1:
                return {}
            time.sleep(REPLACE_PAUSE)
        except (OSError, ValueError):
            return {}
    return stored if isinstance(stored, dict) else {}


def load():
    """Current settings, with any missing key filled from DEFAULTS.

    The notification modes are always whole: a config.json from before them
    gets the defaults built from its notify_labels (backlog 25).
    """
    values = dict(DEFAULTS)
    stored = _stored()
    for key in DEFAULTS:
        if key in stored:
            values[key] = stored[key]
    values["notify_mode"] = modes.mode_of(values)
    values["notify_modes"] = modes.normalised(values["notify_modes"], values["notify_labels"])
    return values


def save(values):
    """Write the known settings back; keys this version does not know stay as they were.

    A newer version may have added keys. Dropping them here, after a rollback
    or from any older copy that saves, would erase what the user set there.
    """
    clean = {key: values.get(key, default) for key, default in DEFAULTS.items()}
    with _LOCK:
        kept = {key: value for key, value in _stored().items() if key not in DEFAULTS}
        _write(json.dumps({**clean, **kept}, indent=2))
    return clean


def _write(text):
    """Replace config.json whole, so a reader sees the old file or the new one, never half of it.

    On Windows os.replace fails while another thread has the file open to
    read it, so it is retried for a moment.
    """
    temporary = FILE.with_name(f"{FILE.name}.{os.getpid()}.{threading.get_ident()}.tmp")
    temporary.write_text(text, encoding="utf-8")
    try:
        for attempt in range(REPLACE_ATTEMPTS):
            try:
                os.replace(temporary, FILE)
                return
            except PermissionError:
                if attempt == REPLACE_ATTEMPTS - 1:
                    raise
                time.sleep(REPLACE_PAUSE)
    finally:
        temporary.unlink(missing_ok=True)


def update(**changes):
    """Change some settings and keep the rest; one writer at a time, so no change is lost."""
    with _LOCK:
        values = load()
        values.update(changes)
        return save(values)
