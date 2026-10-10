"""Web interface: live cameras and the recorded events, in the browser.

Runs uvicorn in a thread next to the Core. Recordings come from what is already
on disk, the JSON and thumbnails in clips/. Live video comes from
Core.live_view(), which only reads. The Core does not know the web exists.

See docs/ARQUITETURA.md sections 17 and 18.
"""

import logging
import re
import socket
import threading
import time
from datetime import date, datetime
from pathlib import Path

import cv2
import requests
import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from jarvis import ROOT
from jarvis.clips import CLIP_DIR, available_days, list_clips

HOST = "0.0.0.0"
PORT = 8765
STATIC_DIR = Path(__file__).with_name("static")
LIVE_FPS = 8
LIVE_QUALITY = 75
BOUNDARY = "frame"
LOOPBACK = {"127.0.0.1", "::1"}

SAFE_NAME = re.compile(r"^[A-Za-z0-9_-]+$")
SAFE_DAY = re.compile(r"^\d{4}-\d{2}-\d{2}$")
SAFE_THUMB = re.compile(r"^\d{2}-\d{2}-\d{2}(\.best)?\.jpg$")

logger = logging.getLogger(__name__)

app = FastAPI(title="J.A.R.V.I.S.", docs_url=None, redoc_url=None)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

_core = None
_on_stop = None
_stopping = threading.Event()
_started = time.time()


def local_url(port=PORT):
    return f"http://127.0.0.1:{port}"


def _parse_day(text):
    """A YYYY-MM-DD string as a date, or a 400 the browser can show."""
    try:
        return datetime.strptime(text, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        raise HTTPException(400, "invalid day, use YYYY-MM-DD")


def _event(entry):
    """What the page needs from one event, with URLs instead of disk paths.

    The picture is the best view of a person when the event has one; older
    events, and those without a person, show the frame that started them.
    """
    thumb = entry["thumbnail_path"]
    camera, day = thumb.parent.parent.name, thumb.parent.name
    best = entry.get("best_thumbnail")
    if isinstance(best, str) and SAFE_THUMB.match(best) and (thumb.parent / best).is_file():
        thumb = thumb.parent / best
    return {
        "camera": entry.get("camera", camera),
        "started_at": entry.get("started_at", ""),
        "time": entry.get("time", ""),
        "seconds": entry.get("seconds", 0),
        "labels": entry.get("labels", []),
        "confidence": entry.get("best_confidence", 0),
        "reason": entry.get("reason", ""),
        "thumbnail": f"/thumbnail/{camera}/{day}/{thumb.name}" if thumb.exists() else None,
    }


@app.get("/")
def index():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/icon.png")
def icon():
    return FileResponse(ROOT / "assets" / "jarvis.png", media_type="image/png")


@app.get("/api/cameras")
def cameras():
    """The cameras this program is watching; empty while they are still starting."""
    return _core.labels if _core is not None else []


@app.get("/api/status")
def status():
    """Cameras, when this server started, and how fresh each camera's last frame is.

    The page uses `started` to notice a restart; the production update script
    uses `frame_age` to decide whether the new version really sees the cameras.
    """
    ages = _core.frame_ages() if _core is not None else {}
    return {"cameras": cameras(), "started": _started,
            "frame_age": {k: (round(v, 1) if v is not None else None) for k, v in ages.items()}}


@app.get("/api/days")
def days():
    """Every day with recordings, newest first."""
    return [day.isoformat() for day in sorted(available_days(), reverse=True)]


@app.get("/api/events")
def events(day: str = None):
    """The events of one day, newest first. Without a day, today."""
    chosen = _parse_day(day) if day else date.today()
    return {"day": chosen.isoformat(), "events": [_event(e) for e in list_clips(chosen)]}


@app.get("/thumbnail/{camera}/{day}/{name}")
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


@app.get("/live/{camera}")
def live(camera: str):
    """MJPEG: the browser shows it in a plain <img>, no player needed."""
    if _core is None or camera not in _core.labels:
        raise HTTPException(404)
    return StreamingResponse(_mjpeg(camera),
                             media_type=f"multipart/x-mixed-replace; boundary={BOUNDARY}")


@app.post("/api/shutdown")
def shutdown(request: Request):
    """Stop the service cleanly. Only from this machine: the port is open to the LAN."""
    if request.client is None or request.client.host not in LOOPBACK:
        raise HTTPException(403, "shutdown is only accepted from this machine")
    if _on_stop is None:
        raise HTTPException(503, "not ready to stop")
    logger.info("Shutdown requested through the web.")
    _on_stop()
    return {"stopping": True}


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


def already_running(port=PORT):
    """Whether a J.A.R.V.I.S. is already serving on this port."""
    try:
        return requests.get(f"{local_url(port)}/api/cameras", timeout=2).ok
    except requests.RequestException:
        return False


def request_stop(port=PORT, timeout=120):
    """Ask the running service to stop, and wait until it has. Returns a message."""
    try:
        answer = requests.post(f"{local_url(port)}/api/shutdown", timeout=5)
    except requests.RequestException:
        return f"Nothing is running on port {port}."
    if not answer.ok:
        return f"The service refused to stop: {answer.status_code} {answer.text}"
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if not already_running(port) and _port_free(HOST, port):
            return "The service has stopped."
        time.sleep(1)
    return f"Asked to stop, but it was still running after {timeout} s."


def _port_free(host, port):
    """Whether nothing else is listening there, so a busy port fails politely."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        try:
            probe.bind((host, port))
        except OSError:
            return False
    return True


def _bind(host, port):
    """Take the port now, in this thread, or return None if someone has it.

    Exclusive on Windows: without SO_EXCLUSIVEADDRUSE a second process could
    bind the same port. Binding here, before uvicorn's thread starts, is what
    makes the port a lock: a check followed by a later bind left a window in
    which two launches both saw it free.
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
    try:
        sock.bind((host, port))
        sock.listen(64)
    except OSError:
        sock.close()
        return None
    return sock


def start(core=None, host=HOST, port=PORT, on_stop=None):
    """Serve the page in a background thread. Returns the server, or None.

    Called before the cameras open, so the port works as a lock: a second
    launch during the slow camera startup finds it taken and does not start.
    """
    global _on_stop
    sock = _bind(host, port)
    if sock is None:
        logger.warning("Web interface off: port %d is already in use.", port)
        return None
    _on_stop = on_stop
    _stopping.clear()
    attach(core)
    server = uvicorn.Server(uvicorn.Config(app, host=host, port=port, log_config=None,
                                          log_level="warning", access_log=False))
    threading.Thread(target=server.run, kwargs={"sockets": [sock]}, name="web",
                     daemon=True).start()
    logger.info("Web interface: %s", local_url(port))
    address = lan_address()
    if address and host == "0.0.0.0":
        logger.info("  from another device on the same network: http://%s:%d", address, port)
    return server


def attach(core):
    """Hand the Core to the web once the cameras are open."""
    global _core
    _core = core


def stop(server):
    """End the live streams, then ask uvicorn to finish."""
    _stopping.set()
    if server is not None:
        server.should_exit = True
