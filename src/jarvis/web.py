"""Web interface: live cameras and the recorded events, in the browser.

Runs uvicorn in a thread next to the Core. Recordings come from what is already
on disk, the JSON and thumbnails in clips/. Live video comes from
Core.live_view(), which only reads. The Core does not know the web exists.

See docs/ARCHITECTURE.md sections 17 and 18.
"""

import asyncio
import hmac
import json
import logging
import re
import socket
import subprocess
import threading
import time
from contextlib import asynccontextmanager
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

from jarvis import ROOT, analysis, archive, bot, devices, dogs, faces, modes, notify, reports, settings
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
SAFE_EVENT = re.compile(r"^\d{2}-\d{2}-\d{2}$")
SAFE_FACE = re.compile(r"^\d{2}-\d{2}-\d{2}_[0-9a-f]{6}\.jpg$")
SAFE_PERSON = re.compile(r"^p_[0-9a-f]{8}$")
SAFE_VIEW = re.compile(r"^[0-9a-f]{12}\.jpg$")
SAFE_DOG = re.compile(r"^d_[0-9a-f]{8}$")
SAFE_REPORT = re.compile(r"^\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}_[0-9a-f]{6}$")
NAME_MAX = 60
BATCH_MAX = 500
NOTIFY_LABELS = ("person", "dog", "cat", "bird", "horse", "sheep", "cow")
EDITABLE = {
    "notify_chat": str,
    "notify_prefix": str,
    "notify_labels": list,
    "notify_cooldown": float,
    "notify_mode": str,
    "notify_modes": dict,
    "archive_path": str,
    "archive_after_days": int,
    "archive_min_free_gb": float,
    **{key: float for key in settings.CONFIDENCE_KEYS},
}

logger = logging.getLogger(__name__)


def quiet_disconnects(loop, context):
    """Drop Windows' report of a browser that closed its connection (R32); pass on everything else."""
    if isinstance(context.get("exception"), ConnectionResetError):
        return
    loop.default_exception_handler(context)


@asynccontextmanager
async def _lifespan(_app):
    """Runs inside uvicorn's own event loop, the one whose handler must change."""
    asyncio.get_running_loop().set_exception_handler(quiet_disconnects)
    yield


app = FastAPI(title="J.A.R.V.I.S.", docs_url=None, redoc_url=None, lifespan=_lifespan)
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
    reported = reports.reported_labels(entry)
    labels = [label for label in entry.get("labels", []) if label not in reported]
    best = entry.get("best_thumbnail")
    if isinstance(best, str) and SAFE_THUMB.match(best) and (thumb.parent / best).is_file():
        thumb = thumb.parent / best
    return {
        "camera": entry.get("camera", camera),
        "started_at": entry.get("started_at", ""),
        "time": entry.get("time", ""),
        "seconds": entry.get("seconds", 0),
        "labels": labels,
        "confidence": entry.get("best_confidence", 0),
        "reason": entry.get("reason", ""),
        "thumbnail": f"/thumbnail/{camera}/{day}/{thumb.name}" if thumb.exists() else None,
        "video": _event_file(entry, camera, day, ".mp4", "video"),
        "side": _event_file(entry, camera, day, ".side.jpg", "thumbnail"),
        "people": (seen or {}).get((camera, day, entry["thumbnail_path"].stem), []),
        "animals": _animals({**entry, "labels": labels}, camera, day, dogs_seen),
        "report": f"/api/events/{camera}/{day}/{entry['thumbnail_path'].stem}/report",
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
            "analysis": analysis.describe(), "analysed_per_minute": per_minute,
            "frame_age": {k: (round(v, 1) if v is not None else None) for k, v in ages.items()}}


@app.post("/api/analysis")
def switch_analysis(payload: dict = Body(...)):
    """Switch analysis On or Off from the page, as /on and /off do from the phone; never stored."""
    wanted = payload.get("on")
    if not isinstance(wanted, bool):
        raise HTTPException(400, "on must be true or false")
    changed = analysis.set_on(wanted)
    if changed:
        logger.info("Web: analysis %s from the page", analysis.describe())
    return {"analysis": analysis.describe(), "changed": changed}


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


@app.post("/api/events/{camera}/{day}/{name}/report")
def report_event(camera: str, day: str, name: str, payload: dict = Body(...)):
    """Say one label of a recording is wrong: it leaves the card and is kept as a report."""
    if not (SAFE_NAME.match(camera) and SAFE_DAY.match(day) and SAFE_EVENT.match(name)):
        raise HTTPException(404)
    sidecar = (CLIP_DIR / camera / day / f"{name}.json").resolve()
    if not sidecar.is_relative_to(CLIP_DIR.resolve()) or not sidecar.is_file():
        raise HTTPException(404)
    label = payload.get("label")
    if not isinstance(label, str) or reports.report_event(sidecar, label) is None:
        raise HTTPException(400, "that label is not one of this recording's, or was already reported")
    return {"reported": label}


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
        "resident": bool(entry.get("resident")),
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
    """Named entries by name, then the unnamed ones, newest first, each with the matcher's guess."""
    named = [_card(e) for e in gallery.people if e["name"]]
    unnamed = []
    for entry in gallery.people:
        if not entry["name"]:
            card = _card(entry)
            card["guess"] = gallery.guess(entry)
            unnamed.append(card)
    return {
        "named": sorted(named, key=lambda c: c["name"].casefold()),
        "unnamed": sorted(unnamed, key=lambda c: c["first_seen"], reverse=True),
    }


def _ids(gallery, payload):
    """The entries a batch request names: a non-empty list of well-formed ids."""
    safe = SAFE_DOG if gallery.id_prefix == "d" else SAFE_PERSON
    ids = payload.get("ids")
    if (not isinstance(ids, list) or not 0 < len(ids) <= BATCH_MAX
            or not all(isinstance(i, str) and safe.match(i) for i in ids)):
        raise HTTPException(400, f"ids: a list of 1 to {BATCH_MAX} entries")
    return ids


def _assign(gallery, payload):
    """Join many unnamed entries to a named one ("to") or to a name ("name") at once."""
    ids = _ids(gallery, payload)
    target, name = payload.get("to"), payload.get("name")
    if (target is None) == (name is None):
        raise HTTPException(400, "either to (a named entry) or name")
    if name is not None and (not isinstance(name, str) or not name.strip()
                             or len(name.strip()) > NAME_MAX):
        raise HTTPException(400, f"a name of 1 to {NAME_MAX} characters")
    if target is not None:
        _entry_or_404(gallery, target)
    result = gallery.assign(ids, target, name or "")
    if result is None:
        raise HTTPException(409, "nothing to join: the entries were merged or reported meanwhile")
    return result


def _report_many(gallery, payload):
    """Report many unnamed entries as bad detections, one report each; the gone ones are skipped."""
    reported, gone = [], []
    for entry_id in dict.fromkeys(_ids(gallery, payload)):
        (reported if reports.report_entry(gallery, entry_id) else gone).append(entry_id)
    return {"reported": reported, "gone": gone}


def _page(gallery, entry_id):
    entry = _entry_or_404(gallery, entry_id)
    card = _card(entry)
    views = faces.views_of(entry)
    card["view_photos"] = [_photo_url(v) for v in views]
    card["pending_photos"] = [_photo_url(w.get("view")) for w in entry.get("pending") or []]
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


def _resident(gallery, entry_id, payload):
    _entry_or_404(gallery, entry_id)
    resident = payload.get("resident")
    if not isinstance(resident, bool):
        raise HTTPException(400, "resident must be true or false")
    if not gallery.set_resident(entry_id, resident):
        raise HTTPException(400, "only a named entry can be a resident")
    return _page(gallery, entry_id)


VIEWS_CHANGED = "the views changed: the page was refreshed"


def _shown(payload):
    """The photo name the page showed at the index it sends; None when it sent none (R41)."""
    view = (payload or {}).get("view")
    if view is not None and not isinstance(view, str):
        raise HTTPException(400, "view must be the photo name shown")
    return view


def _cover(gallery, entry_id, index, payload=None):
    _entry_or_404(gallery, entry_id)
    try:
        chosen = gallery.set_cover(entry_id, index, _shown(payload))
    except faces.ViewsChanged:
        raise HTTPException(409, VIEWS_CHANGED)
    if not chosen:
        raise HTTPException(400, "only a view with a photo can be the favourite")
    return _page(gallery, entry_id)


MOVES = {
    "remove": ("remove_view", "that view cannot be removed: it is the last chosen one; "
                              "move a waiting view up first"),
    "demote": ("demote_view", "that view cannot wait: it is the last chosen one, or the "
                              f"waiting views are full ({faces.MAX_PENDING}); delete one first"),
    "promote": ("promote_view", f"the chosen views are full ({faces.MAX_EMBEDDINGS}): "
                                "move one down or delete one first"),
    "remove-waiting": ("remove_waiting", "there is no such waiting view"),
}


def _move(gallery, entry_id, move, index, payload=None):
    """Delete a view, or move it between the chosen and the waiting ones."""
    _entry_or_404(gallery, entry_id)
    method, refusal = MOVES[move]
    try:
        moved = getattr(gallery, method)(entry_id, index, _shown(payload))
    except faces.ViewsChanged:
        raise HTTPException(409, VIEWS_CHANGED)
    if not moved:
        raise HTTPException(400, refusal)
    return _page(gallery, entry_id)


def _proposal(gallery, entry_id):
    _entry_or_404(gallery, entry_id)
    proposal = gallery.spread_proposal(entry_id)
    if proposal is None:
        raise HTTPException(400, "all the views fit: there is nothing to choose")
    proposal["photos"] = [_photo_url(view) for view in proposal.pop("views")]
    return proposal


def _keep_spread(gallery, entry_id, payload):
    _entry_or_404(gallery, entry_id)
    keep, signature = payload.get("keep"), payload.get("signature")
    if (not isinstance(keep, list) or not all(isinstance(i, int) for i in keep)
            or not isinstance(signature, str)):
        raise HTTPException(400, "a list of views to keep and the proposal's signature")
    if not gallery.keep_spread(entry_id, keep, signature, payload.get("discard") is True):
        raise HTTPException(409, "the views changed since the analysis: analyse again")
    return _page(gallery, entry_id)


def _report(gallery, entry_id):
    _entry_or_404(gallery, entry_id)
    if reports.report_entry(gallery, entry_id) is None:
        raise HTTPException(400, "only an unnamed crop can be reported as a bad detection")
    return {"reported": entry_id}


def _report_card(report):
    """One report as the Settings list shows it."""
    path = Path(report["path"])
    kind, stem = path.parent.name, path.stem
    return {
        "kind": kind,
        "verdict": report.get("verdict", ""),
        "source": report.get("source", ""),
        "camera": report.get("camera", ""),
        "at": report.get("at", ""),
        "reported_at": report.get("reported_at", ""),
        "photo": f"/report-photo/{kind}/{stem}.jpg" if report.get("crop") == f"{stem}.jpg" else None,
        "undo": f"/api/reports/{kind}/{stem}/undo",
        "actually": report.get("actually", ""),
        "choices": reports.choices(report),
        "describe": f"/api/reports/{kind}/{stem}/actually",
    }


@app.get("/api/reports")
def report_list():
    """Every bad-detection report, newest detection first, each with its Undo."""
    return [_report_card(r) for r in reports.listing()
            if SAFE_NAME.match(Path(r["path"]).parent.name) and SAFE_REPORT.match(Path(r["path"]).stem)]


@app.post("/api/reports/{kind}/{name}/undo")
def undo_report(kind: str, name: str):
    """Take back a report made by mistake: the crop returns to its tab, or the label to its card."""
    path = reports.find(kind, name) if SAFE_NAME.match(kind) and SAFE_REPORT.match(name) else None
    if path is None:
        raise HTTPException(404, "no such report")
    if not reports.undo(path, {"face": faces.Gallery(), "dog": dogs.DogGallery()}):
        raise HTTPException(409, "nothing to put back: the recording is no longer on this "
                                 "computer, or the entry or label is already there")
    return {"undone": name}


@app.post("/api/reports/{kind}/{name}/actually")
def describe_report(kind: str, name: str, payload: dict = Body(...)):
    """Say what a reported detection actually showed: a person, a dog, another animal or nothing."""
    path = reports.find(kind, name) if SAFE_NAME.match(kind) and SAFE_REPORT.match(name) else None
    if path is None:
        raise HTTPException(404, "no such report")
    actually = payload.get("actually")
    if not isinstance(actually, str) or not reports.set_actually(path, actually):
        raise HTTPException(400, "one of: " + ", ".join(reports.ACTUALLY) + ", other than the reported label")
    return {"actually": actually}


@app.get("/report-photo/{kind}/{name}")
def report_photo(kind: str, name: str):
    if not (SAFE_NAME.match(kind) and name.endswith(".jpg") and SAFE_REPORT.match(name[:-4])):
        raise HTTPException(404)
    return _crop_file(reports.REPORT_DIR, kind, name)


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


@app.post("/api/persons/{person_id}/resident")
def mark_resident(person_id: str, payload: dict = Body(...)):
    """Mark a named person as living here: the notification modes can then leave them out."""
    return _resident(faces.Gallery(), person_id, payload)


@app.post("/api/persons/{person_id}/views/{index}/cover")
def choose_cover(person_id: str, index: int, payload: dict = Body(default={})):
    """Make one view, which must have a photo, the person's picture on the People grid."""
    return _cover(faces.Gallery(), person_id, index, payload)


@app.post("/api/persons/{person_id}/views/{index}/remove")
def remove_view(person_id: str, index: int, payload: dict = Body(default={})):
    """Delete one chosen view; nothing takes its place unless the user moves a waiting one up."""
    return _move(faces.Gallery(), person_id, "remove", index, payload)


@app.post("/api/persons/{person_id}/views/{index}/demote")
def demote_view(person_id: str, index: int, payload: dict = Body(default={})):
    """Move one chosen view to the waiting ones."""
    return _move(faces.Gallery(), person_id, "demote", index, payload)


@app.post("/api/persons/{person_id}/pending/{index}/promote")
def promote_view(person_id: str, index: int, payload: dict = Body(default={})):
    """Move one waiting view into the chosen ones, while there is room."""
    return _move(faces.Gallery(), person_id, "promote", index, payload)


@app.post("/api/persons/{person_id}/pending/{index}/remove")
def remove_waiting(person_id: str, index: int, payload: dict = Body(default={})):
    """Delete one waiting view."""
    return _move(faces.Gallery(), person_id, "remove-waiting", index, payload)


@app.get("/api/persons/{person_id}/spread")
def person_spread(person_id: str):
    """Propose the 40 most different views of a person, out of their views and queue."""
    return _proposal(faces.Gallery(), person_id)


@app.post("/api/persons/{person_id}/spread")
def keep_person_spread(person_id: str, payload: dict = Body(...)):
    """Keep the proposed 40; every other view waits, or is deleted with "discard"."""
    return _keep_spread(faces.Gallery(), person_id, payload)


@app.post("/api/persons/assign")
def assign_persons(payload: dict = Body(...)):
    """Join the selected unnamed faces to a named person, or to a new name."""
    return _assign(faces.Gallery(), payload)


@app.post("/api/persons/report")
def report_persons(payload: dict = Body(...)):
    """Report the selected unnamed faces as bad detections."""
    return _report_many(faces.Gallery(), payload)


@app.post("/api/persons/{person_id}/report")
def report_person(person_id: str):
    """Say an unnamed face is not a face: it leaves the gallery and is kept as a report."""
    return _report(faces.Gallery(), person_id)


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


@app.post("/api/dogs/{dog_id}/resident")
def mark_resident_dog(dog_id: str, payload: dict = Body(...)):
    return _resident(dogs.DogGallery(), dog_id, payload)


@app.post("/api/dogs/{dog_id}/views/{index}/cover")
def choose_dog_cover(dog_id: str, index: int, payload: dict = Body(default={})):
    return _cover(dogs.DogGallery(), dog_id, index, payload)


@app.post("/api/dogs/{dog_id}/views/{index}/remove")
def remove_dog_view(dog_id: str, index: int, payload: dict = Body(default={})):
    return _move(dogs.DogGallery(), dog_id, "remove", index, payload)


@app.post("/api/dogs/{dog_id}/views/{index}/demote")
def demote_dog_view(dog_id: str, index: int, payload: dict = Body(default={})):
    return _move(dogs.DogGallery(), dog_id, "demote", index, payload)


@app.post("/api/dogs/{dog_id}/pending/{index}/promote")
def promote_dog_view(dog_id: str, index: int, payload: dict = Body(default={})):
    return _move(dogs.DogGallery(), dog_id, "promote", index, payload)


@app.post("/api/dogs/{dog_id}/pending/{index}/remove")
def remove_waiting_dog_view(dog_id: str, index: int, payload: dict = Body(default={})):
    return _move(dogs.DogGallery(), dog_id, "remove-waiting", index, payload)


@app.get("/api/dogs/{dog_id}/spread")
def dog_spread(dog_id: str):
    return _proposal(dogs.DogGallery(), dog_id)


@app.post("/api/dogs/{dog_id}/spread")
def keep_dog_spread(dog_id: str, payload: dict = Body(...)):
    return _keep_spread(dogs.DogGallery(), dog_id, payload)


@app.post("/api/dogs/assign")
def assign_dogs(payload: dict = Body(...)):
    """Join the selected unnamed crops to a named dog, or to a new name."""
    return _assign(dogs.DogGallery(), payload)


@app.post("/api/dogs/report")
def report_dogs(payload: dict = Body(...)):
    """Report the selected unnamed crops as bad detections."""
    return _report_many(dogs.DogGallery(), payload)


@app.post("/api/dogs/{dog_id}/report")
def report_dog(dog_id: str):
    return _report(dogs.DogGallery(), dog_id)


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
    values["notify_cases"] = [[case, modes.CASE_NAMES[case]] for case in modes.CASES]
    values["notify_mode_names"] = [[mode, modes.MODE_NAMES[mode]] for mode in modes.MODES]
    values["archive"] = jsonable_encoder(archive.summary())
    values["confidence_range"] = list(settings.CONFIDENCE_RANGE)
    values["confidence_defaults"] = {key: settings.DEFAULTS[key] for key in settings.CONFIDENCE_KEYS}
    return values


def _clean(key, value):
    """One setting from the page, checked and converted, or a 400."""
    kind = EDITABLE[key]
    if key == "notify_mode":
        if value in modes.MODES:
            return value
        raise HTTPException(400, f"notify_mode must be one of {', '.join(modes.MODES)}")
    if key == "notify_modes":
        return _clean_modes(value)
    if key in settings.CONFIDENCE_KEYS:
        if settings.confidence_valid(value):
            return round(float(value), 2)
        low, high = settings.CONFIDENCE_RANGE
        raise HTTPException(400, f"{key} must be a number from {low} to {high}")
    if kind is str and isinstance(value, str):
        return value.strip()
    if kind is list and isinstance(value, list) and all(v in NOTIFY_LABELS for v in value):
        return list(dict.fromkeys(value))
    if kind in (int, float) and isinstance(value, (int, float)) and not isinstance(value, bool):
        if value >= (1 if key == "archive_after_days" else 0):
            return kind(value)
    raise HTTPException(400, f"invalid value for {key}")


def _clean_modes(value):
    """The switches from the page: known modes and cases only, each true or false, merged over the current ones."""
    if not isinstance(value, dict) or not all(
            mode in modes.MODES and isinstance(switches, dict)
            and all(case in modes.CASES and isinstance(on, bool) for case, on in switches.items())
            for mode, switches in value.items()):
        raise HTTPException(400, "invalid value for notify_modes")
    current = settings.load()["notify_modes"]
    for mode, switches in value.items():
        current[mode].update(switches)
    return current


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
    """Find the chat from the last message sent to the bot, and keep it.

    While the command poller runs it is the only reader: a second getUpdates
    would steal its messages, so the chat comes from what it saw.
    """
    seen = bot.last_chat()
    if seen is None:
        chat, problem = notify.discover_chat(settings.load().get("notify_token") or "")
    else:
        chat, problem = seen, "" if seen else "no message received; send something to the bot first"
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
