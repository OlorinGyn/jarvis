"""Sends a phone notification when a person is recorded.

Telegram, over requests. It pushes to the phone, carries the thumbnail so the
message is worth looking at, costs nothing, and needs no port opened on this
machine. Email would be slower and silent; a Windows toast is useless when
nobody is at the computer.

Sending happens in a thread: the network must never stall the capture loop.

See docs/ARQUITETURA.md section 12.
"""

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

_last_sent = {}
_lock = threading.Lock()


def _call(token, method, fields, file_field=None, file_path=None):
    """One Telegram API call. Returns (ok, detail)."""
    files = None
    if file_field and file_path:
        path = Path(file_path)
        files = {file_field: (path.name, path.read_bytes())}
    try:
        payload = requests.post(API.format(token=token, method=method),
                                data=fields, files=files,
                                timeout=TIMEOUT).json()
    except (requests.RequestException, ValueError) as problem:
        return False, str(problem)
    return bool(payload.get("ok")), payload.get("description", "")


def discover_chat(token):
    """Read the chat id from the last message someone sent to the bot."""
    try:
        payload = requests.get(API.format(token=token, method="getUpdates"),
                               timeout=TIMEOUT).json()
    except (requests.RequestException, ValueError) as problem:
        return "", str(problem)
    if not payload.get("ok"):
        return "", payload.get("description", "resposta inesperada")
    for update in reversed(payload.get("result", [])):
        message = update.get("message") or update.get("channel_post") or {}
        chat = message.get("chat") or {}
        if chat.get("id") is not None:
            return str(chat["id"]), ""
    return "", "nenhuma mensagem recebida; mande algo para o bot primeiro"


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


def _allowed(camera, labels, settings):
    """Whether this event should notify, honouring filters and the cooldown."""
    wanted = settings.get("notify_labels") or ["person"]
    if not any(label in wanted for label in labels):
        return False

    cooldown = float(settings.get("notify_cooldown", COOLDOWN_SECONDS))
    now = time.monotonic()
    with _lock:
        if now - _last_sent.get(camera, -cooldown) < cooldown:
            return False
        _last_sent[camera] = now
    return True


def event(camera, labels, thumbnail, names=None, settings=None):
    """Notify about a recorded event, in the background."""
    settings = settings or load()
    if not settings.get("notify_token") or not settings.get("notify_chat"):
        return False
    if not _allowed(camera, labels, settings):
        return False

    who = ", ".join(names) if names else ", ".join(labels)
    text = f"{camera}: {who}\n{time.strftime('%d/%m/%Y %H:%M:%S')}"
    threading.Thread(target=send, args=(text, thumbnail, settings),
                     daemon=True).start()
    return True


def faces_seen(camera, started_at, sightings, settings=None):
    """Follow up an event with each face the clip scan found, named when known.

    Runs in the clip-assembly thread, after the event, so it can block on the
    network without touching capture. Only called when the event's own
    notification went out, so the cooldown that silenced the first message
    silences this one too.
    """
    settings = settings or load()
    if not settings.get("notify_token") or not settings.get("notify_chat"):
        return 0
    sent = 0
    when = started_at.strftime("%H:%M:%S")
    for sighting in sightings[:MAX_FACES]:
        ok, _ = send(f"{camera} {when}: {_who(sighting)}", sighting.get("thumbnail_path"),
                     settings)
        sent += ok
    return sent


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
