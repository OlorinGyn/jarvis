"""Commands from the phone: the Telegram bot switches the notification mode, and nothing else.

A thread asks Telegram for new messages with getUpdates long polling: an
outgoing connection like sending, so no port is opened on this machine.
Only the configured chat is obeyed; anything else is ignored and logged.
Find chat reads the chats this poller saw, because two readers of the same
bot steal each other's messages, and Telegram answers 409 to the second.
Network trouble is logged once and retried, slower each time; capture
never waits on it. See docs/HISTORY.md section 8, backlog 25 (f).
"""

import json
import logging
import threading
import time

import requests

from . import modes, settings
from .notify import API, _redact

LONG_POLL_SECONDS = 50
IDLE_SECONDS = 30
FIRST_BACKOFF = 5
MAX_BACKOFF = 300
CONFLICT_BACKOFF = 120
STALE_SECONDS = 120
COMMANDS = [
    ("home", "Home mode: leave out the people and dogs who live here"),
    ("away", "Away mode: send every person"),
    ("silent", "Silent mode: send nothing"),
    ("mode", "Show the current mode"),
]
HELP = "Commands: /home, /away, /silent switch the mode; /mode shows it."

logger = logging.getLogger(__name__)


def _api(token, method, fields, timeout):
    """One Telegram call. Returns (payload, problem): payload None when the network failed."""
    try:
        response = requests.post(API.format(token=token, method=method), data=fields,
                                 timeout=timeout)
        return response.json(), ""
    except (requests.RequestException, ValueError) as problem:
        return None, _redact(str(problem), token)


def _command(text):
    """The command word of a message: "/away@jarvis_bot now" is "away"; "" when it is not a command."""
    words = (text or "").strip().split()
    if not words or not words[0].startswith("/"):
        return ""
    return words[0][1:].split("@")[0].casefold()


def _keyboard(current):
    """One tap button per mode, the active one marked."""
    return json.dumps({"inline_keyboard": [[
        {"text": ("● " if mode == current else "") + modes.MODE_NAMES[mode], "callback_data": f"mode:{mode}"}
        for mode in modes.MODES]]})


class Poller:
    """Reads the bot's messages in a thread and obeys the configured chat."""

    def __init__(self, call=_api, load=settings.load, update=settings.update):
        self.call = call
        self.load = load
        self.update = update
        self.offset = None
        self.chats = {}
        self.commands_for = None
        self.trouble = ""
        self.backoff = FIRST_BACKOFF
        self.stopping = threading.Event()
        self.thread = None

    def start(self):
        self.thread = threading.Thread(target=self.run, name="telegram", daemon=True)
        self.thread.start()
        return self

    def stop(self):
        self.stopping.set()

    @property
    def running(self):
        return self.thread is not None and self.thread.is_alive()

    def last_chat(self):
        """The chat that wrote to the bot most recently, as Find chat wants it; "" when none."""
        if not self.chats:
            return ""
        return max(self.chats, key=self.chats.get)

    def run(self):
        while not self.stopping.is_set():
            try:
                self.poll_once()
            except Exception as problem:
                self._wait_after(f"unexpected: {type(problem).__name__}")

    def poll_once(self):
        """One long poll: read what arrived, obey it, or wait after trouble."""
        values = self.load()
        token = (values.get("notify_token") or "").strip()
        if not token:
            self.stopping.wait(IDLE_SECONDS)
            return
        if self.commands_for != token:
            self._register_commands(token)
        fields = {"timeout": LONG_POLL_SECONDS,
                  "allowed_updates": json.dumps(["message", "callback_query"])}
        if self.offset is not None:
            fields["offset"] = self.offset
        payload, problem = self.call(token, "getUpdates", fields, LONG_POLL_SECONDS + 10)
        if not isinstance(payload, dict):
            self._wait_after(f"network: {problem or 'unexpected answer'}")
            return
        if not payload.get("ok"):
            if payload.get("error_code") == 409:
                self._wait_after("another program reads this bot's messages (409); "
                                 "only production should", CONFLICT_BACKOFF)
            else:
                self._wait_after(_redact(payload.get("description", "unexpected answer"), token))
            return
        if self.trouble:
            logger.info("Telegram commands: reading again")
        self.trouble, self.backoff = "", FIRST_BACKOFF
        for update in payload.get("result") or []:
            self.offset = update.get("update_id", 0) + 1
            try:
                self.handle(update, token, values)
            except Exception as problem:
                logger.warning("Telegram commands: an update could not be handled: %s",
                               _redact(str(problem), token))

    def _wait_after(self, problem, seconds=None):
        """Log a problem once, not on every retry, and wait longer each time it repeats."""
        if problem != self.trouble:
            logger.warning("Telegram commands: %s", problem)
            self.trouble = problem
        wait = seconds or self.backoff
        self.backoff = min(self.backoff * 2, MAX_BACKOFF)
        self.stopping.wait(wait)

    def _register_commands(self, token):
        """List the commands in Telegram's "/" menu, once per token."""
        commands = json.dumps([{"command": name, "description": text} for name, text in COMMANDS])
        payload, _ = self.call(token, "setMyCommands", {"commands": commands}, 15)
        if isinstance(payload, dict) and payload.get("ok"):
            self.commands_for = token

    def handle(self, update, token, values):
        """Obey one update from the configured chat; remember every chat for Find chat."""
        message = update.get("message") or {}
        callback = update.get("callback_query") or {}
        source = message or callback.get("message") or {}
        chat = str((source.get("chat") or {}).get("id", ""))
        if not chat:
            return
        self.chats[chat] = time.monotonic()
        wanted = (values.get("notify_chat") or "").strip()
        if chat != wanted:
            logger.info("Telegram commands: ignored a message from chat %s, not the configured one", chat)
            if callback:
                self.call(token, "answerCallbackQuery", {"callback_query_id": callback.get("id")}, 15)
            return
        if callback:
            self._tapped(callback, token, chat, values)
        elif time.time() - message.get("date", 0) <= STALE_SECONDS:
            self._obey(_command(message.get("text")), token, chat, values)

    def _obey(self, command, token, chat, values):
        if command in modes.MODES:
            self._switch(command, token, chat)
        elif command == "mode":
            current = modes.mode_of(values)
            self._reply(token, chat, f"Current mode: {modes.describe(current, values)}",
                        _keyboard(current))
        elif command:
            self._reply(token, chat, HELP)

    def _tapped(self, callback, token, chat, values):
        data = callback.get("data") or ""
        mode = data.split(":", 1)[1] if data.startswith("mode:") else ""
        self.call(token, "answerCallbackQuery",
                  {"callback_query_id": callback.get("id"),
                   "text": f"{modes.MODE_NAMES[mode]} is on" if mode in modes.MODES else ""}, 15)
        if mode in modes.MODES:
            self._switch(mode, token, chat)

    def _switch(self, mode, token, chat):
        """Make a mode active and say what it means."""
        self.update(notify_mode=mode)
        logger.info("Telegram commands: mode set to %s from the phone", mode)
        self._reply(token, chat, f"Mode set. {modes.describe(mode, self.load())}")

    def _reply(self, token, chat, text, keyboard=None):
        fields = {"chat_id": chat, "text": text[:4096]}
        if keyboard:
            fields["reply_markup"] = keyboard
        payload, problem = self.call(token, "sendMessage", fields, 15)
        if not isinstance(payload, dict) or not payload.get("ok"):
            logger.warning("Telegram commands: the answer was not sent: %s",
                           problem or (payload if isinstance(payload, dict) else {}).get("description", ""))


_poller = None


def start():
    """Start reading the bot's commands. Production only: main() calls it, the tests never do."""
    global _poller
    _poller = Poller().start()
    return _poller


def stop():
    if _poller is not None:
        _poller.stop()


def last_chat():
    """The chat the running poller saw last; None when no poller runs here."""
    if _poller is None or not _poller.running:
        return None
    return _poller.last_chat()
