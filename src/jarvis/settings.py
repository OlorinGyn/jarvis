"""Settings the user changes while the program runs.

Separate from .env on purpose: .env holds camera credentials, written once by
hand. This holds choices made in the interface, so it has to be readable and
writable at runtime.

See docs/ARCHITECTURE.md section 11.
"""

import json
import os
import threading
import time

from . import ROOT, modes

FILE = ROOT / "config.json"
REPLACE_ATTEMPTS = 50
REPLACE_PAUSE = 0.01
CONFIDENCE_KEYS = ("confidence_person", "confidence_dog", "confidence_animal")
CONFIDENCE_RANGE = (0.20, 0.90)
SLIDER_STEPS = 1000
FACE_SURE_KEY = "face_sure_threshold"
FACE_SURE_RANGE = (0.30, 0.60)
DOG_SURE_KEY = "dog_sure_distance"
DOG_SURE_RANGE = (0.20, 0.39)

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
    "confidence_person": 0.35,
    "confidence_dog": 0.45,
    "confidence_animal": 0.45,
    "face_sure_threshold": 0.40,
    "dog_sure_distance": 0.33,
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
    for key in CONFIDENCE_KEYS:
        if not confidence_valid(values[key]):
            values[key] = DEFAULTS[key]
    if not face_sure_valid(values[FACE_SURE_KEY]):
        values[FACE_SURE_KEY] = DEFAULTS[FACE_SURE_KEY]
    if not dog_sure_valid(values[DOG_SURE_KEY]):
        values[DOG_SURE_KEY] = DEFAULTS[DOG_SURE_KEY]
    return values


def face_sure_valid(value):
    """True for a face sure threshold the page may set: a number inside FACE_SURE_RANGE (backlog 32)."""
    low, high = FACE_SURE_RANGE
    return isinstance(value, (int, float)) and not isinstance(value, bool) and low <= value <= high


def dog_sure_valid(value):
    """True for a dog sure distance the page may set: a number inside DOG_SURE_RANGE (backlog 32)."""
    low, high = DOG_SURE_RANGE
    return isinstance(value, (int, float)) and not isinstance(value, bool) and low <= value <= high


def confidence_valid(value):
    """True for a detection confidence the detector accepts: a number inside CONFIDENCE_RANGE."""
    low, high = CONFIDENCE_RANGE
    return isinstance(value, (int, float)) and not isinstance(value, bool) and low <= value <= high


def slider_position(value, default):
    """Where a minimum confidence sits on its slider: the default in the middle, each half linear to its end."""
    low, high = CONFIDENCE_RANGE
    middle = SLIDER_STEPS / 2
    if value <= default:
        share = (value - low) / (default - low) if default > low else 1.0
        return round(share * middle)
    share = (value - default) / (high - default) if high > default else 0.0
    return round(middle + share * middle)


def slider_value(position, default):
    """The minimum confidence a slider position stands for, the inverse of slider_position."""
    low, high = CONFIDENCE_RANGE
    middle = SLIDER_STEPS / 2
    if position <= middle:
        return round(low + (default - low) * position / middle, 2)
    return round(default + (high - default) * (position - middle) / middle, 2)


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
