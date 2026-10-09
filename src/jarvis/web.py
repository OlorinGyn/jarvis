"""Web interface: a local page that lists the recorded events.

Runs uvicorn in a thread next to the Core. It only reads what is already on
disk, the JSON and thumbnails in clips/, so the Core does not know it exists,
just as it does not know about the window.

See docs/ARQUITETURA.md section 17.
"""

import re
import socket
import threading
from datetime import date, datetime
from pathlib import Path

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from jarvis import ROOT
from jarvis.clips import CLIP_DIR, available_days, list_clips

HOST = "127.0.0.1"
PORT = 8765
STATIC_DIR = Path(__file__).with_name("static")

SAFE_NAME = re.compile(r"^[A-Za-z0-9_-]+$")
SAFE_DAY = re.compile(r"^\d{4}-\d{2}-\d{2}$")
SAFE_THUMB = re.compile(r"^\d{2}-\d{2}-\d{2}\.jpg$")

app = FastAPI(title="J.A.R.V.I.S.", docs_url=None, redoc_url=None)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


def _parse_day(text):
    """A YYYY-MM-DD string as a date, or a 400 the browser can show."""
    try:
        return datetime.strptime(text, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        raise HTTPException(400, "dia invalido, use AAAA-MM-DD")


def _event(entry):
    """What the page needs from one event, with URLs instead of disk paths."""
    thumb = entry["thumbnail_path"]
    camera, day = thumb.parent.parent.name, thumb.parent.name
    return {
        "camera": entry.get("camera", camera),
        "started_at": entry.get("started_at", ""),
        "time": entry.get("time", ""),
        "seconds": entry.get("seconds", 0),
        "labels": entry.get("labels", []),
        "confidence": entry.get("best_confidence", 0),
        "reason": entry.get("reason", ""),
        "thumbnail": f"/miniatura/{camera}/{day}/{thumb.name}" if thumb.exists() else None,
    }


@app.get("/")
def index():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/icone.png")
def icon():
    return FileResponse(ROOT / "assets" / "jarvis.png", media_type="image/png")


@app.get("/api/dias")
def days():
    """Every day with recordings, newest first."""
    return [day.isoformat() for day in sorted(available_days(), reverse=True)]


@app.get("/api/eventos")
def events(dia: str = None):
    """The events of one day, newest first. Without a day, today."""
    day = _parse_day(dia) if dia else date.today()
    return {"dia": day.isoformat(), "eventos": [_event(e) for e in list_clips(day)]}


@app.get("/miniatura/{camera}/{day}/{name}")
def thumbnail(camera: str, day: str, name: str):
    """One event thumbnail. The checks keep requests inside clips/."""
    if not (SAFE_NAME.match(camera) and SAFE_DAY.match(day) and SAFE_THUMB.match(name)):
        raise HTTPException(404)
    path = (CLIP_DIR / camera / day / name).resolve()
    if not path.is_relative_to(CLIP_DIR.resolve()) or not path.is_file():
        raise HTTPException(404)
    return FileResponse(path, media_type="image/jpeg")


def _port_free(host, port):
    """Whether nothing else is listening there, so a busy port fails politely."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        try:
            probe.bind((host, port))
        except OSError:
            return False
    return True


def start(host=HOST, port=PORT):
    """Serve the page in a background thread. Returns the server, or None."""
    if not _port_free(host, port):
        print(f"Interface web desligada: a porta {port} ja esta em uso.")
        return None
    server = uvicorn.Server(uvicorn.Config(app, host=host, port=port,
                                          log_level="warning", access_log=False))
    threading.Thread(target=server.run, name="web", daemon=True).start()
    print(f"Interface web: http://{host}:{port}")
    return server


def stop(server):
    """Ask uvicorn to finish; the thread ends on its own."""
    if server is not None:
        server.should_exit = True
