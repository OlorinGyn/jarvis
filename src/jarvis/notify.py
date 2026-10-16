"""Sends a phone notification when a person is recorded.

Telegram, over requests. It pushes to the phone, carries the thumbnail so the
message is worth looking at, costs nothing, and needs no port opened on this
machine. Email would be slower and silent; a Windows toast is useless when
nobody is at the computer.

Sending happens in a thread: the network must never stall the capture loop.
Nothing the mode wants is dropped: the house's incident decides whether each
message rings or arrives silently.

See docs/ARCHITECTURE.md section 12.
"""

import logging
import re
import threading
import time
from pathlib import Path

import requests

from . import modes
from .faces import learn_threshold
from .settings import load

API = "https://api.telegram.org/bot{token}/{method}"
TIMEOUT = 15
QUIET_SECONDS = 120
LOUD_FLOOR_SECONDS = 30
MAX_FACES = 3
TOKEN_IN_URL = re.compile(r"bot\d+(?::|%3A)[\w-]+", re.IGNORECASE)

_incident = {}
_floor = {"last_loud": None, "held_back": [], "timer": None}
_lock = threading.Lock()
_clock = time.monotonic
logger = logging.getLogger(__name__)


def _redact(text, token):
    """Remove the bot token from text that may quote the request URL."""
    if token:
        text = text.replace(token, "<token>")
    return TOKEN_IN_URL.sub("bot<token>", text)


def _call(token, method, fields, file_field=None, file_path=None):
    """One Telegram API call. Returns (ok, detail), the detail never holding the token."""
    try:
        files = None
        if file_field and file_path:
            path = Path(file_path)
            files = {file_field: (path.name, path.read_bytes())}
        payload = requests.post(API.format(token=token, method=method),
                                data=fields, files=files,
                                timeout=TIMEOUT).json()
    except (requests.RequestException, ValueError, OSError) as problem:
        return False, _redact(str(problem), token)
    return bool(payload.get("ok")), _redact(payload.get("description", ""), token)


def discover_chat(token):
    """Read the chat id from the last message someone sent to the bot."""
    try:
        payload = requests.get(API.format(token=token, method="getUpdates"),
                               timeout=TIMEOUT).json()
    except (requests.RequestException, ValueError) as problem:
        return "", _redact(str(problem), token)
    if not payload.get("ok"):
        return "", _redact(payload.get("description", "unexpected answer"), token)
    for update in reversed(payload.get("result", [])):
        message = update.get("message") or update.get("channel_post") or {}
        chat = message.get("chat") or {}
        if chat.get("id") is not None:
            return str(chat["id"]), ""
    return "", "no message received; send something to the bot first"


def send(text, image=None, settings=None, silent=False):
    """Send one notification now, with no sound when silent. Returns (ok, detail)."""
    settings = settings or load()
    token = (settings.get("notify_token") or "").strip()
    chat = (settings.get("notify_chat") or "").strip()
    if not token or not chat:
        return False, "notifications not configured"
    prefix = (settings.get("notify_prefix") or "").strip()
    if prefix:
        text = f"{prefix} {text}"
    quiet = {"disable_notification": "true"} if silent else {}

    if image and Path(image).exists():
        return _call(token, "sendPhoto",
                     {"chat_id": chat, "caption": text[:1024], **quiet},
                     "photo", image)
    return _call(token, "sendMessage", {"chat_id": chat, "text": text[:4096], **quiet})


def configured(settings):
    """Whether a token and a chat are set: nothing is sent without both."""
    return bool(settings.get("notify_token") and settings.get("notify_chat"))


def _loud(camera, people, what, settings, force=False):
    """Whether a message rings, by the house's incident; one held back by the floor goes out silent.

    The incident opens with a message sent while none is open and closes
    when nothing was sent for notify_cooldown seconds. A message rings when
    it opens one, comes from another camera than the last, counts more
    people at once than the incident had, or is forced. At most one rings in
    LOUD_FLOOR_SECONDS; the others are named by one loud text at its end.
    """
    quiet = float(settings.get("notify_cooldown", QUIET_SECONDS))
    now = _clock()
    with _lock:
        fresh = not _incident or now - _incident["last_sent"] >= quiet
        if fresh:
            _incident.clear()
            _incident["people"] = 0
        loud = force or fresh or camera != _incident["camera"] or people > _incident["people"]
        _incident.update(last_sent=now, camera=camera, people=max(people, _incident["people"]))
        if not loud:
            return False
        last = _floor["last_loud"]
        if last is not None and now - last < LOUD_FLOOR_SECONDS:
            _floor["held_back"].append(what)
            if _floor["timer"] is None:
                timer = threading.Timer(last + LOUD_FLOOR_SECONDS - now, _end_of_floor, args=(settings,))
                timer.daemon = True
                _floor["timer"] = timer
                timer.start()
            return False
        _floor["last_loud"] = now
        return True


def _end_of_floor(settings):
    """At the floor's end, one loud text naming what went out silently inside it."""
    with _lock:
        held_back = list(_floor["held_back"])
        _floor.update(held_back=[], timer=None)
        if not held_back:
            return False
        _floor["last_loud"] = _clock()
        quiet = float(settings.get("notify_cooldown", QUIET_SECONDS))
        if _incident and _floor["last_loud"] - _incident["last_sent"] < quiet:
            _incident["last_sent"] = _floor["last_loud"]
    more = len(held_back) - 1
    tail = f"and {more} more, sent silently above" if more else "sent silently above"
    return _send_logged(f"floor, {len(held_back)} held back", f"{held_back[0]} — {tail}", None,
                        settings)


def _deliver(camera, people, subject, text, image, settings):
    """Send one message now, loud or silent as the incident says."""
    silent = not _loud(camera, people, text, settings)
    return _send_logged(subject, text, image, settings, silent)


def event(camera, parts, thumbnail, settings=None):
    """Notify about a recorded event, in the background. Returns (sent, held).

    parts are (words, case) for each subject; a person's case is None, since
    who it is is known only after the face scan. When the active mode has
    any person case off, the person is held for the scan instead (backlog
    25 (d)): held says so, and the words go out without them.
    """
    settings = settings or load()
    if not configured(settings):
        return False, False
    switches = modes.active(settings)
    held = any(case is None for _, case in parts) and modes.holds_person(settings)
    words = [w for w, case in parts if (case is None and not held) or (case and switches.get(case))]
    if not words:
        return False, held
    people = int(any(case is None for _, case in parts) and not held)
    subject = f"{camera} {', '.join(words)}"
    silent = not _loud(camera, people, f"{camera} {time.strftime('%H:%M:%S')}: {', '.join(words)}",
                       settings)
    text = f"{camera}: {', '.join(words)}\n{time.strftime('%d/%m/%Y %H:%M:%S')}"
    threading.Thread(target=_send_logged, args=(subject, text, thumbnail, settings, silent),
                     daemon=True).start()
    return True, held


def holds_person(settings=None):
    """Whether a person seen now waits for the face scan under the active mode."""
    settings = settings or load()
    return configured(settings) and modes.holds_person(settings)


def _send_logged(subject, text, image, settings, silent=False):
    """Send, and leave the outcome in the log: the only trace of whether it arrived."""
    ok, detail = send(text, image, settings, silent=silent)
    if ok:
        logger.info("Notification %s: %s", subject, "sent silently" if silent else "sent")
    else:
        logger.warning("Notification %s: failed: %s", subject, detail)
    return ok


def faces_seen(camera, started_at, sightings, settings=None, people=1):
    """Announce each face the clip scan found, named when known, if the active mode wants its case.

    Runs in the clip-assembly thread, after the event, so it can block on the
    network without touching capture. Sent whether or not the event's own
    message went out, since a face is rare and the most useful message (R25);
    people is the most persons seen at once, for the incident.
    """
    settings = settings or load()
    if not configured(settings):
        return 0
    sent = 0
    when = started_at.strftime("%H:%M:%S")
    wanted = []
    for sighting in sightings:
        case = person_case(sighting, settings)
        if modes.allowed(case, settings):
            wanted.append(sighting)
        else:
            logger.info("Notification %s face, %s: skipped: %s mode", camera, _who(sighting, settings),
                        modes.mode_of(settings))
    for sighting in wanted[:MAX_FACES]:
        who = _who(sighting, settings)
        sent += _deliver(camera, people, f"{camera} face, {who}", f"{camera} {when}: {who}",
                         sighting.get("thumbnail_path"), settings)
    return sent


def after_scan(camera, started_at, found, held, notified, side_view=None, best=None,
               settings=None, people=0, people_view=None):
    """Every message a finished face scan sends. Returns how many went out.

    Faces are announced each by its case. With no face, the side view, else
    the best view, is the faceless-person case: a follow-up after a sent
    event, as before, held or not; or, when the person was held and nothing
    of the event went out, the person message itself. people is the most persons
    YOLO saw in one frame: when the held person's faces were all silenced and
    YOLO saw more people than faces, the frame where YOLO counted them,
    people_view, goes out as the same case (R42 (b), R56); the best view when
    that frame was not kept.
    """
    settings = settings or load()
    if not configured(settings):
        return 0
    seen = max(people, 1)
    if found:
        sent = faces_seen(camera, started_at, found, settings, seen)
        silenced = not any(modes.allowed(person_case(s, settings), settings) for s in found)
        picture = people_view if people_view and Path(people_view).exists() else best
        if held and silenced and people > len(found) and picture:
            return sent + _faceless(camera, held, notified, settings,
                                    lambda: hidden_person(camera, started_at, picture, people,
                                                          len(found), settings))
        return sent
    side = Path(side_view) if side_view and Path(side_view).exists() else None
    if side is None and not best:
        return 0
    if side is not None:
        return _faceless(camera, held, notified, settings,
                         lambda: side_face(camera, started_at, side, settings, seen))
    return _faceless(camera, held, notified, settings,
                     lambda: best_view(camera, started_at, best, settings, seen))


def _faceless(camera, held, notified, settings, message):
    """Send one faceless-person message if its switch is on: the held person's own, or a follow-up."""
    if not modes.allowed("faceless_person", settings):
        logger.info("Notification %s no face: skipped: %s mode", camera, modes.mode_of(settings))
        return 0
    if not held and not notified:
        return 0
    return int(bool(message()))


def side_face(camera, started_at, image, settings=None, people=1):
    """Follow up an event whose scan saw a face only from the side: a picture, not a name (R30)."""
    settings = settings or load()
    if not configured(settings):
        return False
    when = started_at.strftime("%H:%M:%S")
    return _deliver(camera, people, f"{camera} side view", f"{camera} {when}: face, side view",
                    str(image), settings)


def best_view(camera, started_at, image, settings=None, people=1):
    """Follow up an event whose clip showed no face with its best view of the person.

    The first message carries the frame that started the event, which is
    often not the person. Only after a sent event, unlike faces_seen.
    """
    settings = settings or load()
    if not configured(settings):
        return False
    when = started_at.strftime("%H:%M:%S")
    return _deliver(camera, people, f"{camera} best view", f"{camera} {when}: no face seen, best view",
                    str(image), settings)


def hidden_person(camera, started_at, image, people, faces, settings=None):
    """Send the frame where YOLO saw more people than the scan found faces (R42 (b), R56)."""
    settings = settings or load()
    if not configured(settings):
        return False
    when = started_at.strftime("%H:%M:%S")
    found = f"{faces} face{'s' if faces != 1 else ''} found"
    return _deliver(camera, people, f"{camera} hidden person",
                    f"{camera} {when}: {people} people seen, {found}", str(image), settings)


def camera_down(camera, text, settings=None):
    """Tell the phone a camera lost its picture, or got it back: loud, as the camera_down case."""
    settings = settings or load()
    if not configured(settings):
        return False
    if not modes.allowed("camera_down", settings):
        logger.info("Notification %s: skipped: %s mode", text, modes.mode_of(settings))
        return False
    silent = not _loud(camera, 0, text, settings, force=True)
    return _send_logged(text, text, None, settings, silent)


def person_case(sighting, settings=None):
    """Which switch a face answers to: a resident, sure or probable, another name, or unknown.

    A weak match to a resident has a case of its own, so whether it is
    silenced is the user's switch and not a rule in the code.
    """
    if not sighting.get("name"):
        return "unknown_face"
    if sighting.get("resident"):
        sure = sighting.get("score", 0) >= learn_threshold(settings)
        return "resident_person" if sure else "probable_resident_person"
    return "known_person"


def _who(sighting, settings=None):
    """Name the face, and say so when the match is too weak to be sure.

    A match only needs MATCH_THRESHOLD, where nothing measured was wrong; ours
    are 40-60 px faces, where a weak match can be chance. LEARN_THRESHOLD is
    the bar the gallery already trusts to learn from (ARCHITECTURE 10.14), as
    the user set it in Settings (backlog 32).
    """
    name = sighting.get("name") or ""
    if not name:
        return "unknown face"
    if sighting.get("score", 0) < learn_threshold(settings):
        return f"probably {name}"
    return f"{name} recognized"


def reset_incident():
    """Forget the incident and the floor, cancelling a pending loud text."""
    with _lock:
        _incident.clear()
        if _floor["timer"] is not None:
            _floor["timer"].cancel()
        _floor.update(last_loud=None, held_back=[], timer=None)
