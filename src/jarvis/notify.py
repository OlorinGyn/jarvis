"""Sends a phone notification when a person is recorded.

Telegram, over requests. It pushes to the phone, carries the thumbnail so the
message is worth looking at, costs nothing, and needs no port opened on this
machine. Email would be slower and silent; a Windows toast is useless when
nobody is at the computer.

Sending happens in a thread: the network must never stall the capture loop.

See docs/ARQUITETURA.md section 12.
"""

import logging
import re
import threading
import time
from pathlib import Path

import requests

from .faces import LEARN_THRESHOLD
from .settings import load

API = "https://api.telegram.org/bot{token}/{method}"
TIMEOUT = 15
COOLDOWN_SECONDS = 120
MAX_FACES = 3
TOKEN_IN_URL = re.compile(r"bot\d+(?::|%3A)[\w-]+", re.IGNORECASE)

_last_sent = {}
_lock = threading.Lock()
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


def send(text, image=None, settings=None):
    """Send one notification now. Returns (ok, detail)."""
    settings = settings or load()
    token = (settings.get("notify_token") or "").strip()
    chat = (settings.get("notify_chat") or "").strip()
    if not token or not chat:
        return False, "notifications not configured"
    prefix = (settings.get("notify_prefix") or "").strip()
    if prefix:
        text = f"{prefix} {text}"

    if image and Path(image).exists():
        return _call(token, "sendPhoto",
                     {"chat_id": chat, "caption": text[:1024]},
                     "photo", image)
    return _call(token, "sendMessage", {"chat_id": chat, "text": text[:4096]})


def _wanted(labels, settings):
    """Whether any of these labels is one the user asked to be notified about."""
    wanted = settings.get("notify_labels") or ["person"]
    return any(label in wanted for label in labels)


def _cooled_down(key, settings):
    """Whether the last notification for key (a camera, or a person's face) is old enough, claiming the slot if so."""
    cooldown = float(settings.get("notify_cooldown", COOLDOWN_SECONDS))
    now = time.monotonic()
    with _lock:
        if now - _last_sent.get(key, -cooldown) < cooldown:
            return False
        _last_sent[key] = now
    return True


def event(camera, labels, thumbnail, names=None, settings=None):
    """Notify about a recorded event, in the background."""
    settings = settings or load()
    if not settings.get("notify_token") or not settings.get("notify_chat"):
        return False
    if not _wanted(labels, settings):
        return False
    subject = f"{camera} {', '.join(labels)}"
    if not _cooled_down(camera, settings):
        logger.info("Notification %s: skipped: cooldown", subject)
        return False

    who = ", ".join(names) if names else ", ".join(labels)
    text = f"{camera}: {who}\n{time.strftime('%d/%m/%Y %H:%M:%S')}"
    threading.Thread(target=_send_logged, args=(subject, text, thumbnail, settings),
                     daemon=True).start()
    return True


def _send_logged(subject, text, image, settings):
    """Send, and leave the outcome in the log: the only trace of whether it arrived."""
    ok, detail = send(text, image, settings)
    if ok:
        logger.info("Notification %s: sent", subject)
    else:
        logger.warning("Notification %s: failed: %s", subject, detail)
    return ok


def faces_seen(camera, started_at, sightings, settings=None):
    """Announce each face the clip scan found, named when known.

    Runs in the clip-assembly thread, after the event, so it can block on the
    network without touching capture. Sent whether or not the event's own
    message went out: the camera's cooldown is against repeated events, and a
    face is rare and the most useful message (R25). Each person has a cooldown
    of their own instead, so the same face is not announced twice in a row.
    """
    settings = settings or load()
    if not settings.get("notify_token") or not settings.get("notify_chat"):
        return 0
    if not _wanted(["person"], settings):
        return 0
    sent = 0
    when = started_at.strftime("%H:%M:%S")
    for sighting in sightings[:MAX_FACES]:
        who = _who(sighting)
        subject = f"{camera} face, {who}"
        person = sighting.get("person_id")
        if person and not _cooled_down(("face", person), settings):
            logger.info("Notification %s: skipped: cooldown", subject)
            continue
        sent += _send_logged(subject, f"{camera} {when}: {who}",
                             sighting.get("thumbnail_path"), settings)
    return sent


def side_face(camera, started_at, image, settings=None):
    """Follow up an event whose scan saw a face only from the side: a picture, not a name (R30)."""
    settings = settings or load()
    if not settings.get("notify_token") or not settings.get("notify_chat"):
        return False
    when = started_at.strftime("%H:%M:%S")
    return _send_logged(f"{camera} side view", f"{camera} {when}: face, side view",
                        str(image), settings)


def best_view(camera, started_at, image, settings=None):
    """Follow up an event whose clip showed no face with its best view of the person.

    The first message carries the frame that started the event, which is
    often not the person. Only after a sent event, unlike faces_seen.
    """
    settings = settings or load()
    if not settings.get("notify_token") or not settings.get("notify_chat"):
        return False
    when = started_at.strftime("%H:%M:%S")
    return _send_logged(f"{camera} best view", f"{camera} {when}: no face seen, best view",
                        str(image), settings)


def _who(sighting):
    """Name the face, and say so when the match is too weak to be sure.

    A match only needs MATCH_THRESHOLD (0.363), the value OpenCV recommends for
    sharp 112 px faces. Ours are 40-60 px, where a weak match can be chance;
    LEARN_THRESHOLD is the bar the gallery already trusts to learn from.
    """
    name = sighting.get("name") or ""
    if not name:
        return "unknown face"
    if sighting.get("score", 0) < LEARN_THRESHOLD:
        return f"probably {name}"
    return f"{name} recognized"


def reset_cooldown():
    with _lock:
        _last_sent.clear()
