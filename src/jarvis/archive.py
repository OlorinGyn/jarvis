"""Moves old recordings to a second disk, and only deletes as a last resort.

Three tiers. Recording always lands in clips/ on the program's disk. Events
older than archive_after_days move to the folder the user picked, normally an
external drive. Nothing is ever deleted from clips/; deletion happens only in
the archive, oldest first, and only when that drive runs out of room.

Copy, verify, then delete: an interrupted move leaves the original intact
rather than a half-written file on the far side.

See docs/ARQUITETURA.md section 11.
"""

import shutil
import time
from datetime import datetime, timedelta
from pathlib import Path

from . import ROOT
from .clips import CLIP_DIR
from .settings import load

PROTECT_MINUTES = 10
CHECK_SECONDS = 1800


def events(directory):
    """Every recorded event as (when, basename, files, bytes), oldest first."""
    found = []
    for sidecar in Path(directory).glob("*/*/*.json"):
        try:
            when = datetime.strptime(f"{sidecar.parent.name} {sidecar.stem}",
                                     "%Y-%m-%d %H-%M-%S")
        except ValueError:
            continue
        base = sidecar.with_suffix("")
        files = [p for p in base.parent.glob(f"{base.name}.*") if p.is_file()]
        found.append((when, base, files, sum(p.stat().st_size for p in files)))
    found.sort(key=lambda event: event[0])
    return found


def destination_state(path):
    """Whether the archive folder can be written to right now, and its room."""
    if not path:
        return {"ready": False, "reason": "nenhuma pasta configurada"}
    folder = Path(path)
    try:
        folder.mkdir(parents=True, exist_ok=True)
        usage = shutil.disk_usage(folder)
    except OSError:
        return {"ready": False, "reason": "pasta indisponivel (HD desconectado?)"}
    return {"ready": True, "reason": "", "free": usage.free, "total": usage.total,
            "path": folder}


def _move_event(files, source_root, destination_root):
    """Copy an event across, confirm it arrived, then drop the original."""
    copied = []
    for origin in files:
        target = destination_root / origin.relative_to(source_root)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(origin, target)
        if target.stat().st_size != origin.stat().st_size:
            for partial in copied + [target]:
                partial.unlink(missing_ok=True)
            return False
        copied.append(target)

    for origin in files:
        origin.unlink(missing_ok=True)
    return True


def _drop_empty_folders(directory):
    for day in sorted(Path(directory).glob("*/*"), reverse=True):
        if day.is_dir() and not any(day.iterdir()):
            day.rmdir()


def move_old(settings=None):
    """Send events past their age to the archive."""
    settings = settings or load()
    state = destination_state(settings["archive_path"])
    if not state["ready"]:
        return {"moved": 0, "bytes": 0, "skipped": state["reason"]}

    cutoff = datetime.now() - timedelta(days=int(settings["archive_after_days"]))
    protected = datetime.now() - timedelta(minutes=PROTECT_MINUTES)
    moved = carried = 0

    for when, _, files, size in events(CLIP_DIR):
        if when > cutoff or when > protected:
            continue
        if _move_event(files, CLIP_DIR, state["path"]):
            moved += 1
            carried += size

    if moved:
        _drop_empty_folders(CLIP_DIR)
    return {"moved": moved, "bytes": carried, "skipped": ""}


def free_space(settings=None):
    """Delete the oldest archived events until the drive has room again."""
    settings = settings or load()
    state = destination_state(settings["archive_path"])
    if not state["ready"]:
        return {"removed": 0, "bytes": 0, "skipped": state["reason"]}

    wanted = float(settings["archive_min_free_gb"]) * 1024 ** 3
    if state["free"] >= wanted:
        return {"removed": 0, "bytes": 0, "skipped": ""}

    removed = released = 0
    for _, _, files, size in events(state["path"]):
        if state["free"] + released >= wanted:
            break
        for path in files:
            path.unlink(missing_ok=True)
        removed += 1
        released += size

    if removed:
        _drop_empty_folders(state["path"])
    return {"removed": removed, "bytes": released, "skipped": ""}


def summary(settings=None):
    """What the Ajustes screen shows: where things are and how much room is left."""
    settings = settings or load()
    state = destination_state(settings["archive_path"])
    here = events(CLIP_DIR)
    local_usage = shutil.disk_usage(CLIP_DIR if CLIP_DIR.exists() else ROOT)

    report = {
        "local_events": len(here),
        "local_bytes": sum(event[3] for event in here),
        "local_free": local_usage.free,
        "oldest": here[0][0] if here else None,
        "archive_ready": state["ready"],
        "archive_reason": state["reason"],
        "archive_path": settings["archive_path"],
        "after_days": int(settings["archive_after_days"]),
        "min_free_gb": float(settings["archive_min_free_gb"]),
    }
    if state["ready"]:
        there = events(state["path"])
        report.update(archive_events=len(there),
                      archive_bytes=sum(event[3] for event in there),
                      archive_free=state["free"],
                      archive_total=state["total"])
    return report


class Housekeeper:
    """Runs the archive work on a timer, so the main loop can call it freely."""

    def __init__(self, interval=CHECK_SECONDS):
        self.interval = interval
        self.last_run = 0.0

    def tick(self):
        """Returns a summary when it actually ran, otherwise None."""
        now = time.monotonic()
        if now - self.last_run < self.interval:
            return None
        self.last_run = now
        settings = load()
        return {"moved": move_old(settings), "freed": free_space(settings)}
