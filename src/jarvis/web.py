"""Web interface: live cameras and the recorded events, in the browser.

Runs uvicorn in a thread next to the Core. Recordings come from what is already
on disk, the JSON and thumbnails in clips/. Live video comes from
Core.live_view(), which only reads. The Core does not know the web exists.

See docs/ARQUITETURA.md section 17.
"""

import re
import socket
import threading
import time
from datetime import date, datetime
from pathlib import Path

import cv2
import requests
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from jarvis import ROOT
from jarvis.clips import CLIP_DIR, available_days, list_clips

HOST = "0.0.0.0"
PORT = 8765
LOCAL_URL = f"http://127.0.0.1:{PORT}"
STATIC_DIR = Path(__file__).with_name("static")
LIVE_FPS = 8
LIVE_QUALITY = 75
BOUNDARY = "frame"

SAFE_NAME = re.compile(r"^[A-Za-z0-9_-]+$")
SAFE_DAY = re.compile(r"^\d{4}-\d{2}-\d{2}$")
SAFE_THUMB = re.compile(r"^\d{2}-\d{2}-\d{2}\.jpg$")

app = FastAPI(title="J.A.R.V.I.S.", docs_url=None, redoc_url=None)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

_core = None
_stopping = threading.Event()


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


@app.get("/api/cameras")
def cameras():
    """The cameras this program is watching."""
    return _core.labels if _core is not None else []


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


def _mjpeg(label):
    """Endless JPEGs of one camera, each announced by the multipart boundary."""
    interval = 1 / LIVE_FPS
    while not _stopping.is_set():
        view = _core.live_view(label)
        ok, jpeg = cv2.imencode(".jpg", view, [cv2.IMWRITE_JPEG_QUALITY, LIVE_QUALITY])
        if ok:
            data = jpeg.tobytes()
            yield (f"--{BOUNDARY}\r\nContent-Type: image/jpeg\r\n"
                   f"Content-Length: {len(data)}\r\n\r\n").encode() + data + b"\r\n"
        time.sleep(interval)


@app.get("/ao-vivo/{camera}")
def live(camera: str):
    """MJPEG: the browser shows it in a plain <img>, no player needed."""
    if _core is None or camera not in _core.labels:
        raise HTTPException(404)
    return StreamingResponse(_mjpeg(camera),
                             media_type=f"multipart/x-mixed-replace; boundary={BOUNDARY}")


def lan_address():
    """This machine's address on the home network, for opening on the phone.

    Connecting a UDP socket sends nothing; it only makes Windows pick the
    interface it would use to go out, and that interface's address is ours.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as probe:
        try:
            probe.connect(("8.8.8.8", 80))
            return probe.getsockname()[0]
        except OSError:
            return None


def already_running():
    """Whether a J.A.R.V.I.S. is already serving here."""
    try:
        return requests.get(f"{LOCAL_URL}/api/cameras", timeout=2).ok
    except requests.RequestException:
        return False


def _port_free(host, port):
    """Whether nothing else is listening there, so a busy port fails politely."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        try:
            probe.bind((host, port))
        except OSError:
            return False
    return True


def start(core=None, host=HOST, port=PORT):
    """Serve the page in a background thread. Returns the server, or None."""
    global _core
    if not _port_free(host, port):
        print(f"Interface web desligada: a porta {port} ja esta em uso.")
        return None
    _core = core
    _stopping.clear()
    server = uvicorn.Server(uvicorn.Config(app, host=host, port=port,
                                          log_level="warning", access_log=False))
    threading.Thread(target=server.run, name="web", daemon=True).start()
    print(f"Interface web: {LOCAL_URL}")
    address = lan_address()
    if address and host == "0.0.0.0":
        print(f"  no celular, na mesma rede: http://{address}:{port}")
    return server


def stop(server):
    """End the live streams, then ask uvicorn to finish."""
    _stopping.set()
    if server is not None:
        server.should_exit = True
