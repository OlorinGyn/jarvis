"""Sends a phone notification when a person is recorded.

Telegram, over plain urllib. It pushes to the phone, carries the thumbnail so
the message is worth looking at, costs nothing, and needs no port opened on
this machine. Email would be slower and silent; a Windows toast is useless
when nobody is at the computer.

Sending happens in a thread: the network must never stall the capture loop.

See docs/ARQUITETURA.md section 12.
"""

import json
import mimetypes
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path

from .settings import load

API = "https://api.telegram.org/bot{token}/{method}"
TIMEOUT = 15
COOLDOWN_SECONDS = 120

_last_sent = {}
_lock = threading.Lock()


def _multipart(fields, file_field=None, file_path=None):
    """Build a multipart body by hand, so no HTTP library is needed."""
    boundary = f"----jarvis{uuid.uuid4().hex}"
    parts = []
    for name, value in fields.items():
        parts.append(
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="{name}"\r\n\r\n'
            f"{value}\r\n".encode("utf-8"))

    if file_field and file_path:
        path = Path(file_path)
        kind = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        parts.append(
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="{file_field}"; '
            f'filename="{path.name}"\r\n'
            f"Content-Type: {kind}\r\n\r\n".encode("utf-8"))
        parts.append(path.read_bytes())
        parts.append(b"\r\n")

    parts.append(f"--{boundary}--\r\n".encode("utf-8"))
    return b"".join(parts), f"multipart/form-data; boundary={boundary}"


def _call(token, method, fields, file_field=None, file_path=None):
    """One Telegram API call. Returns (ok, detail)."""
    url = API.format(token=token, method=method)
    try:
        if file_path:
            body, content_type = _multipart(fields, file_field, file_path)
            request = urllib.request.Request(url, data=body,
                                             headers={"Content-Type": content_type})
        else:
            body = urllib.parse.urlencode(fields).encode("utf-8")
            request = urllib.request.Request(url, data=body)
        with urllib.request.urlopen(request, timeout=TIMEOUT) as answer:
            payload = json.loads(answer.read().decode("utf-8"))
        return bool(payload.get("ok")), payload.get("description", "")
    except urllib.error.HTTPError as problem:
        try:
            detail = json.loads(problem.read().decode("utf-8")).get("description", "")
        except Exception:
            detail = str(problem)
        return False, detail
    except (urllib.error.URLError, OSError, ValueError) as problem:
        return False, str(problem)


def discover_chat(token):
    """Read the chat id from the last message someone sent to the bot."""
    ok, _ = True, None
    url = API.format(token=token, method="getUpdates")
    try:
        with urllib.request.urlopen(url, timeout=TIMEOUT) as answer:
            payload = json.loads(answer.read().decode("utf-8"))
    except (urllib.error.URLError, OSError, ValueError) as problem:
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
        return False, "notificacao nao configurada"

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

    quem = ", ".join(names) if names else ", ".join(labels)
    texto = f"{camera}: {quem}\n{time.strftime('%d/%m/%Y %H:%M:%S')}"
    threading.Thread(target=send, args=(texto, thumbnail, settings),
                     daemon=True).start()
    return True


def reset_cooldown():
    with _lock:
        _last_sent.clear()
