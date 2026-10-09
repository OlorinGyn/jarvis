"""Logging to the console and, for the service itself, to a rotating file.

Running as a scheduled task there is no console, so print() would go nowhere.
Uncaught exceptions, in the main thread or any other, are logged too: a thread
that dies silently is how an unattended service stops recording unnoticed.

Only the service writes the file. `--stop` and a launch that finds the service
already running log to the console alone: on Windows, rotating a log that
another process holds open fails.

See docs/ARQUITETURA.md section 18.
"""

import logging
import sys
import threading
from logging.handlers import RotatingFileHandler

from jarvis import ROOT

LOG_DIR = ROOT / "logs"
LOG_FILE = LOG_DIR / "jarvis.log"
MAX_BYTES = 1_000_000
BACKUPS = 5


def setup():
    """Console logging and crash hooks. Safe to call twice."""
    root = logging.getLogger()
    if any(getattr(h, "jarvis_console", False) for h in root.handlers):
        return
    root.setLevel(logging.INFO)
    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(logging.Formatter("%(message)s"))
    console.jarvis_console = True
    root.addHandler(console)
    sys.excepthook = _log_uncaught
    threading.excepthook = _log_thread_crash


def to_file():
    """Also write logs/jarvis.log. Only the running service calls this."""
    root = logging.getLogger()
    if any(isinstance(h, RotatingFileHandler) for h in root.handlers):
        return
    LOG_DIR.mkdir(exist_ok=True)
    handler = RotatingFileHandler(LOG_FILE, maxBytes=MAX_BYTES, backupCount=BACKUPS,
                                  encoding="utf-8")
    handler.setFormatter(logging.Formatter(
        "%(asctime)s %(levelname)s %(threadName)s %(name)s: %(message)s"))
    root.addHandler(handler)


def _log_uncaught(kind, value, traceback):
    if issubclass(kind, KeyboardInterrupt):
        sys.__excepthook__(kind, value, traceback)
        return
    logging.getLogger("jarvis").critical("uncaught exception",
                                         exc_info=(kind, value, traceback))


def _log_thread_crash(args):
    logging.getLogger("jarvis").error(
        "thread %s died", args.thread.name if args.thread else "?",
        exc_info=(args.exc_type, args.exc_value, args.exc_traceback))
