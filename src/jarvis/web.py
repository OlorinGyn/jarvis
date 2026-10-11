"""Web interface: live cameras and the recorded events, in the browser.

Runs uvicorn in a thread next to the Core. Recordings come from what is already
on disk, the JSON and thumbnails in clips/. Live video comes from
Core.live_view(), which only reads. The Core does not know the web exists.

See docs/ARQUITETURA.md sections 17 and 18.
"""

import hmac
import json
import logging
import re
import socket
import subprocess
import threading
import time
from urllib.parse import quote
from datetime import date, datetime
from pathlib import Path

import cv2
import requests
import uvicorn
from fastapi import Body, FastAPI, HTTPException, Request, Response
from fastapi.encoders import jsonable_encoder
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from jarvis import ROOT, archive, devices, dogs, faces, notify, settings
from jarvis.capture import NO_WINDOW
from jarvis.clips import CLIP_DIR, available_days, list_clips

HOST = "0.0.0.0"
PORT = 8765
STATIC_DIR = Path(__file__).with_name("static")
LIVE_FPS = 8
LIVE_QUALITY = 75
BOUNDARY = "frame"
LOOPBACK = {"127.0.0.1", "::1"}
REQUEST_HEADER = "X-Jarvis-Request"
PIN_HEADER = "X-Jarvis-Pin"
WRITE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
PIN_PATTERN = re.compile(r"^[0-9]{4,12}$")

SAFE_NAME = re.compile(r"^[A-Za-z0-9_-]+$")
SAFE_DAY = re.compile(r"^\d{4}-\d{2}-\d{2}$")
SAFE_THUMB = re.compile(r"^\d{2}-\d{2}-\d{2}(\.best|\.side)?\.jpg$")
SAFE_VIDEO = re.compile(r"^\d{2}-\d{2}-\d{2}\.mp4$")
SAFE_FACE = re.compile(r"^\d{2}-\d{2}-\d{2}_[0-9a-f]{6}\.jpg$")
SAFE_PERSON = re.compile(r"^p_[0-9a-f]{8}$")
SAFE_VIEW = re.compile(r"^[0-9a-f]{12}\.jpg$")
SAFE_DOG = re.compile(r"^d_[0-9a-f]{8}$")
NAME_MAX = 60
NOTIFY_LABELS = ("person", "dog", "cat", "bird", "horse", "sheep", "cow")
EDITABLE = {
    "notify_chat": str,
    "notify_prefix": str,
    "notify_labels": list,
    "notify_cooldown": float,
    "archive_path": str,
    "archive_after_days": int,
    "archive_min_free_gb": float,
}

logger = logging.getLogger(__name__)

app = FastAPI(title="J.A.R.V.I.S.", docs_url=None, redoc_url=None)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

_core = None
_on_stop = None
_stopping = threading.Event()
_started = time.time()


def _read_version():
    """The checked-out version, as git describes it; "unknown" when git cannot say."""
    try:
        result = subprocess.run(["git", "describe", "--tags", "--always", "--dirty"],
                                cwd=ROOT, capture_output=True, text=True, timeout=10,
                                stdin=subprocess.DEVNULL, creationflags=NO_WINDOW)
    except (OSError, subprocess.SubprocessError):
        return "unknown"
    return result.stdout.strip() if result.returncode == 0 and result.stdout.strip() else "unknown"


_version = _read_version()


def local_url(port=PORT):
    return f"http://127.0.0.1:{port}"


def _parse_day(text):
    """A YYYY-MM-DD string as a date, or a 400 the browser can show."""
    try:
        return datetime.strptime(text, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        raise HTTPException(400, "invalid day, use YYYY-MM-DD")


def _clip_key(clip):
    """(camera, day, HH-MM-SS) of a clip path, whichever slashes it was stored with."""
    parts = re.split(r"[\\/]", str(clip))
    if len(parts) < 3:
        return None
    return parts[-3], parts[-2], parts[-1].rsplit(".", 1)[0]


def _who_was_seen(day):
    """For each recording of a day, the people whose faces its clip scan found."""
    gallery = faces.Gallery()
    seen = {}
    for path in (faces.FACE_DIR / day.isoformat()).glob("*.json"):
        try:
            sighting = json.loads(path.read_text(encoding="utf-8-sig"))
        except (OSError, ValueError):
            continue
        key = _clip_key(sighting.get("clip", ""))
        person = gallery.get(sighting.get("person_id"))
        if key is None:
            continue
        name = (person or {}).get("name") or "unknown"
        names = seen.setdefault(key, [])
        if name not in names:
            names.append(name)
    for names in seen.values():
        names.sort(key=lambda n: (n == "unknown", n.casefold()))
    return seen


def _dogs_seen(day):
    """For each recording of a day, its dogs as they are named now (R29)."""
    seen, gallery = {}, dogs.DogGallery()
    for sighting in dogs.sightings_of(day):
        key = _clip_key(sighting.get("clip", ""))
        words = dogs.current_words(sighting, gallery)
        if key is not None and words not in seen.setdefault(key, []):
            seen[key].append(words)
    return seen


def _animals(entry, camera, day, dogs_seen):
    """The event's animal labels, with "dog" replaced by the dogs' names when there are any."""
    labels = [label for label in entry.get("labels", []) if label != "person"]
    named = (dogs_seen or {}).get((camera, day, entry["thumbnail_path"].stem))
    if "dog" in labels and named:
        labels = [label for label in labels if label != "dog"] + named
    return labels


def _event_file(entry, camera, day, suffix, route):
    """The URL of one of an event's files, when it exists on disk."""
    stem = entry["thumbnail_path"].stem
    path = entry["thumbnail_path"].with_name(f"{stem}{suffix}")
    return f"/{route}/{camera}/{day}/{path.name}" if path.is_file() else None


def _event(entry, seen=None, dogs_seen=None):
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
        "video": _event_file(entry, camera, day, ".mp4", "video"),
        "side": _event_file(entry, camera, day, ".side.jpg", "thumbnail"),
        "people": (seen or {}).get((camera, day, entry["thumbnail_path"].stem), []),
        "animals": _animals(entry, camera, day, dogs_seen),
    }


@app.middleware("http")
async def never_stale(request: Request, call_next):
    """The browser must revalidate the page's own files on every load.

    Without an instruction it may keep an old app.js for hours after an
    update and call routes that no longer exist (R28). A revalidation is a
    cheap 304 on the home network.
    """
    response = await call_next(request)
    if request.url.path.startswith("/static/"):
        response.headers["Cache-Control"] = "no-cache"
    return response


@app.get("/")
def index():
    """The page, with the running version in its script and style URLs, never cached."""
    version = quote(_version, safe="")
    html = (STATIC_DIR / "index.html").read_text(encoding="utf-8")
    for asset in ("/static/app.js", "/static/style.css"):
        html = html.replace(f'"{asset}"', f'"{asset}?v={version}"')
    return HTMLResponse(html, headers={"Cache-Control": "no-cache"})


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
    per_minute = _core.per_minute if _core is not None else {}
    return {"cameras": cameras(), "started": _started, "version": _version,
            "analysed_per_minute": per_minute,
            "frame_age": {k: (round(v, 1) if v is not None else None) for k, v in ages.items()}}


@app.get("/api/days")
def days():
    """Every day with recordings, newest first."""
    return [day.isoformat() for day in sorted(available_days(), reverse=True)]


@app.get("/api/events")
def events(day: str = None):
    """The events of one day, newest first. Without a day, today."""
    chosen = _parse_day(day) if day else date.today()
    seen, dogs_seen = _who_was_seen(chosen), _dogs_seen(chosen)
    return {"day": chosen.isoformat(),
            "events": [_event(e, seen, dogs_seen) for e in list_clips(chosen)]}


@app.get("/video/{camera}/{day}/{name}")
def video(camera: str, day: str, name: str):
    """One recording, with HTTP Range so the browser can seek without downloading it all."""
    if not (SAFE_NAME.match(camera) and SAFE_DAY.match(day) and SAFE_VIDEO.match(name)):
        raise HTTPException(404)
    path = (CLIP_DIR / camera / day / name).resolve()
    if not path.is_relative_to(CLIP_DIR.resolve()) or not path.is_file():
        raise HTTPException(404)
    return FileResponse(path, media_type="video/mp4")


@app.get("/thumbnail/{camera}/{day}/{name}")
def thumbnail(camera: str, day: str, name: str):
    """One event thumbnail. The checks keep requests inside clips/."""
    if not (SAFE_NAME.match(camera) and SAFE_DAY.match(day) and SAFE_THUMB.match(name)):
        raise HTTPException(404)
    path = (CLIP_DIR / camera / day / name).resolve()
    if not path.is_relative_to(CLIP_DIR.resolve()) or not path.is_file():
        raise HTTPException(404)
    return FileResponse(path, media_type="image/jpeg")


def _photo_url(stored):
    """The page URL of a stored crop (a sighting's or a view's, a face's or a dog's), or None."""
    if not stored:
        return None
    path = Path(stored)
    prefix = "/dog-" if path.parent.parent.name == "dogs" else "/"
    if path.parent.name == "views" and SAFE_VIEW.match(path.name):
        return f"{prefix}view/{path.name}"
    if SAFE_DAY.match(path.parent.name) and SAFE_FACE.match(path.name):
        return f"{prefix}{'photo' if prefix == '/dog-' else 'face'}/{path.parent.name}/{path.name}"
    return None


def _stored_file(stored):
    """A portable path from gallery.json as a real path."""
    path = Path(stored)
    return path if path.is_absolute() else ROOT / path


def _card(entry):
    """One person or dog as its grid lists them: the favourite, else the newest view with a photo."""
    cover = faces.cover_of(entry)
    if cover and not _stored_file(cover).is_file():
        cover = None
    photo = cover or next((v for v in reversed(faces.views_of(entry)) if v), None)
    return {
        "id": entry["id"],
        "name": entry["name"],
        "photo": _photo_url(photo or entry.get("thumbnail")),
        "views": len(entry["embeddings"]),
        "pending": len(entry.get("pending") or []),
        "first_seen": entry.get("first_seen", ""),
    }


def _appearances(folder, key, entry_id):
    """Every sighting of a person or dog, newest first: when, which camera."""
    found = []
    for path in Path(folder).glob("*/*.json"):
        try:
            sighting = json.loads(path.read_text(encoding="utf-8-sig"))
        except (OSError, ValueError):
            continue
        if sighting.get(key) == entry_id:
            at = sighting.get("at", "")
            found.append({"at": at, "day": at[:10], "time": sighting.get("time", ""),
                          "camera": sighting.get("camera", "")})
    found.sort(key=lambda a: a["at"], reverse=True)
    return found


def _entry_or_404(gallery, entry_id):
    safe = SAFE_DOG if gallery.id_prefix == "d" else SAFE_PERSON
    entry = gallery.get(entry_id) if safe.match(entry_id) else None
    if entry is None:
        raise HTTPException(404, "not found")
    return entry


def _grid(gallery):
    cards = [_card(e) for e in gallery.people]
    return {
        "named": sorted((c for c in cards if c["name"]), key=lambda c: c["name"].casefold()),
        "unnamed": sorted((c for c in cards if not c["name"]),
                          key=lambda c: c["first_seen"], reverse=True),
    }


def _page(gallery, entry_id):
    entry = _entry_or_404(gallery, entry_id)
    card = _card(entry)
    views = faces.views_of(entry)
    card["view_photos"] = [_photo_url(v) for v in views]
    cover = faces.cover_of(entry)
    card["cover_index"] = views.index(cover) if cover else None
    card["appearances"] = _appearances(gallery.path.parent, gallery.sighting_key, entry_id)
    return card


def _name(gallery, entry_id, payload, kind):
    name = payload.get("name")
    if not isinstance(name, str) or not name.strip() or len(name.strip()) > NAME_MAX:
        raise HTTPException(400, f"a name of 1 to {NAME_MAX} characters")
    entry = _entry_or_404(gallery, entry_id)
    other = gallery.by_name(name)
    if other is not None and other is not entry and payload.get("merge") is not True:
        raise HTTPException(409, f"{other['name']} already exists: saving merges the two "
                                 f"into one {kind}, which cannot be undone")
    merged = gallery.rename(entry_id, name)
    result = type(gallery)(gallery.path).by_name(name)
    return {"id": result["id"] if result else entry_id, "name": name.strip(), "merged": merged}


def _cover(gallery, entry_id, index):
    _entry_or_404(gallery, entry_id)
    if not gallery.set_cover(entry_id, index):
        raise HTTPException(400, "only a view with a photo can be the favourite")
    return _page(gallery, entry_id)


def _remove(gallery, entry_id, index):
    _entry_or_404(gallery, entry_id)
    if not gallery.remove_view(entry_id, index):
        raise HTTPException(400, "that view cannot be removed: it is the last one")
    return _page(gallery, entry_id)


def _crop_file(root, *parts):
    """A crop inside root, or a 404: the checks keep requests inside the folder."""
    root = Path(root).resolve()
    path = root.joinpath(*parts).resolve()
    if not path.is_relative_to(root) or not path.is_file():
        raise HTTPException(404)
    return FileResponse(path, media_type="image/jpeg")


@app.get("/api/persons")
def persons():
    """Named people by name, then the unnamed faces, newest first."""
    return _grid(faces.Gallery())


@app.get("/api/persons/{person_id}")
def person_page(person_id: str):
    """One person: the photo of each stored view, the queue, and every appearance."""
    return _page(faces.Gallery(), person_id)


@app.post("/api/persons/{person_id}/name")
def name_person(person_id: str, payload: dict = Body(...)):
    """Name or rename a person. A name someone else has merges the two, so it asks first."""
    return _name(faces.Gallery(), person_id, payload, "person")


@app.post("/api/persons/{person_id}/views/{index}/cover")
def choose_cover(person_id: str, index: int):
    """Make one view, which must have a photo, the person's picture on the People grid."""
    return _cover(faces.Gallery(), person_id, index)


@app.post("/api/persons/{person_id}/views/{index}/remove")
def remove_view(person_id: str, index: int):
    """Remove one stored view; the oldest queued view takes its place."""
    return _remove(faces.Gallery(), person_id, index)


@app.get("/face/{day}/{name}")
def face_thumbnail(day: str, name: str):
    if not (SAFE_DAY.match(day) and SAFE_FACE.match(name)):
        raise HTTPException(404)
    return _crop_file(faces.FACE_DIR, day, name)


@app.get("/view/{name}")
def view_photo(name: str):
    if not SAFE_VIEW.match(name):
        raise HTTPException(404)
    return _crop_file(faces.FACE_DIR / "views", name)


@app.get("/api/dogs")
def dog_grid():
    """Named dogs by name, then the unnamed crops, newest first."""
    return _grid(dogs.DogGallery())


@app.get("/api/dogs/{dog_id}")
def dog_page(dog_id: str):
    return _page(dogs.DogGallery(), dog_id)


@app.post("/api/dogs/{dog_id}/name")
def name_dog(dog_id: str, payload: dict = Body(...)):
    return _name(dogs.DogGallery(), dog_id, payload, "dog")


@app.post("/api/dogs/{dog_id}/views/{index}/cover")
def choose_dog_cover(dog_id: str, index: int):
    return _cover(dogs.DogGallery(), dog_id, index)


@app.post("/api/dogs/{dog_id}/views/{index}/remove")
def remove_dog_view(dog_id: str, index: int):
    return _remove(dogs.DogGallery(), dog_id, index)


@app.post("/api/dogs/{dog_id}/dismiss")
def dismiss_dog(dog_id: str):
    """Forget an unnamed dog crop the user does not want to name."""
    gallery = dogs.DogGallery()
    _entry_or_404(gallery, dog_id)
    if not gallery.dismiss(dog_id):
        raise HTTPException(400, "only an unnamed dog can be dismissed")
    return {"dismissed": dog_id}


@app.get("/dog-photo/{day}/{name}")
def dog_photo(day: str, name: str):
    if not (SAFE_DAY.match(day) and SAFE_FACE.match(name)):
        raise HTTPException(404)
    return _crop_file(dogs.DOG_DIR, day, name)


@app.get("/dog-view/{name}")
def dog_view(name: str):
    if not SAFE_VIEW.match(name):
        raise HTTPException(404)
    return _crop_file(dogs.DOG_DIR / "views", name)


def _is_local(request):
    """Whether the request comes from this machine itself."""
    return request.client is not None and request.client.host in LOOPBACK


def _write_refusal(request):
    """Why this write must be refused, or "" when it may go ahead.

    The header closes cross-site forgery: a foreign page cannot add it without
    a preflight the service never grants. From another device the paired PIN
    is also needed, since anyone on the Wi-Fi can open the page (R4, R24).
    """
    if request.headers.get(REQUEST_HEADER) != "1":
        return "writes are only accepted from the J.A.R.V.I.S. page"
    if _is_local(request):
        return ""
    if devices.use(request.cookies.get(devices.COOKIE)):
        return ""
    pin = (settings.load().get("write_pin") or "").strip()
    if not pin:
        return ("no PIN is set: on the M900 itself, open Settings and set one "
                "to pair other devices")
    offered = request.headers.get(PIN_HEADER, "")
    if not hmac.compare_digest(offered.encode(), pin.encode()):
        return "this device is not paired: enter the PIN in Settings, Other devices"
    return ""


@app.middleware("http")
async def guard_writes(request: Request, call_next):
    """Every write passes _write_refusal first; reading stays open (R4)."""
    if request.method in WRITE_METHODS:
        problem = _write_refusal(request)
        if problem:
            return JSONResponse({"detail": problem}, status_code=403)
        response = await call_next(request)
        token = request.cookies.get(devices.COOKIE)
        if token and not _is_local(request) and devices.known(token):
            _remember_device(response, token)
        return response
    return await call_next(request)


def _remember_device(response, token):
    """The pairing cookie: HttpOnly, same-site only, DAYS long, renewed with every write."""
    response.set_cookie(devices.COOKIE, token, max_age=devices.DAYS * 86400,
                        httponly=True, samesite="strict", path="/")


def _settings_view(request):
    """The settings for the page. The bot token never leaves: only whether it is set."""
    values = settings.load()
    token = values.pop("notify_token", "")
    values["notify_token_set"] = bool((token or "").strip())
    values["pin_set"] = bool((values.pop("write_pin", "") or "").strip())
    values["local"] = _is_local(request)
    values["paired"] = devices.known(request.cookies.get(devices.COOKIE))
    values["devices"] = devices.listing() if values["local"] else []
    values["notify_label_choices"] = list(NOTIFY_LABELS)
    values["archive"] = jsonable_encoder(archive.summary())
    return values


def _clean(key, value):
    """One setting from the page, checked and converted, or a 400."""
    kind = EDITABLE[key]
    if kind is str and isinstance(value, str):
        return value.strip()
    if kind is list and isinstance(value, list) and all(v in NOTIFY_LABELS for v in value):
        return list(dict.fromkeys(value))
    if kind in (int, float) and isinstance(value, (int, float)) and not isinstance(value, bool):
        if value >= (1 if key == "archive_after_days" else 0):
            return kind(value)
    raise HTTPException(400, f"invalid value for {key}")


@app.get("/api/settings")
def read_settings(request: Request):
    return _settings_view(request)


@app.post("/api/settings")
def write_settings(request: Request, payload: dict = Body(...)):
    """Change some settings. A token is only ever written, never read back."""
    changes = {}
    for key, value in payload.items():
        if key == "notify_token":
            if not isinstance(value, str) or not value.strip():
                raise HTTPException(400, "invalid value for notify_token")
            changes[key] = value.strip()
        elif key in EDITABLE:
            changes[key] = _clean(key, value)
        else:
            raise HTTPException(400, f"unknown setting {key}")
    if changes:
        settings.update(**changes)
    return _settings_view(request)


@app.post("/api/notify/discover")
def discover_chat():
    """Find the chat from the last message sent to the bot, and keep it."""
    chat, problem = notify.discover_chat(settings.load().get("notify_token") or "")
    if chat:
        settings.update(notify_chat=chat)
    return {"chat": chat, "error": problem}


@app.post("/api/pin")
def set_pin(request: Request, payload: dict = Body(...)):
    """Set or clear the PIN that pairs other devices. Only from this machine."""
    if not _is_local(request):
        raise HTTPException(403, "the PIN can only be set on the M900 itself")
    pin = payload.get("pin")
    if not isinstance(pin, str) or (pin and not PIN_PATTERN.match(pin)):
        raise HTTPException(400, "a PIN of 4 to 12 digits, or empty to remove it")
    settings.update(write_pin=pin)
    forgotten = devices.forget()
    return {"pin_set": bool(pin), "forgotten": forgotten}


@app.post("/api/pair")
def pair(request: Request, response: Response):
    """Pair this device: once the guard accepted the PIN, a cookie remembers it for DAYS days."""
    if _is_local(request) or devices.known(request.cookies.get(devices.COOKIE)):
        return {"paired": True}
    agent = request.headers.get("user-agent", "unknown browser")
    label = f"{request.client.host if request.client else '?'} - {agent}"
    _remember_device(response, devices.pair(label))
    return {"paired": True}


@app.post("/api/devices/{device_id}/forget")
def forget_device(request: Request, device_id: str):
    """Forget one paired device. Only from this machine."""
    if not _is_local(request):
        raise HTTPException(403, "devices can only be forgotten on the M900 itself")
    if not re.fullmatch(r"[0-9a-f]{12}", device_id) or not devices.forget(device_id):
        raise HTTPException(404, "no such device")
    return {"devices": devices.listing()}


@app.post("/api/notify/test")
def test_notification():
    ok, detail = notify.send("J.A.R.V.I.S.: test notification")
    return {"ok": ok, "detail": detail}


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
        answer = requests.post(f"{local_url(port)}/api/shutdown",
                               headers={REQUEST_HEADER: "1"}, timeout=5)
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
