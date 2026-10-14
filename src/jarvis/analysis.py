"""Whether J.A.R.V.I.S. analyses what the cameras see: On or Off, switched from the phone.

Off stops everything after capture: motion, YOLO, events, recordings, face
scans and messages, while the cameras keep feeding Live. It is held in memory
only, so every start, crash or restart is On. See docs/HISTORY.md section 8,
backlog 29.
"""

import threading
import time

_lock = threading.Lock()
_on = True
_changed = time.monotonic()


def is_on():
    """Whether frames are analysed now."""
    return _on


def set_on(wanted):
    """Switch analysis on or off. Returns True when the state changed."""
    global _on, _changed
    with _lock:
        if _on == bool(wanted):
            return False
        _on = bool(wanted)
        _changed = time.monotonic()
    return True


def off_for():
    """Seconds since analysis was switched off; 0 while it is on."""
    return 0.0 if _on else time.monotonic() - _changed


def describe():
    """One word for the page, the bot and the logs."""
    return "On" if _on else "Off"
