# Handoff — developer to architect

Written by the developer (`high`) at the end of a delivery. The architect
(`ultracode`) integrates it into the documentation and empties this file. See
`CLAUDE.md`, "Developer and architect".

## Delivery: everything production needs before it is installed — 09/10/2026

The user asked for everything required before installing production, a strict
rule that no version may break files written by an older one, and to be taught
how to run the program before installation.

**Commits to review:** `760d68e` and the one carrying this file. The last
review (CONTEXTO 13.2) covered up to `456b613`; `113bac5` and `f811003` in
between are architect commits (documentation only). **Not pushed** — pushing is
the architect's now.

### 1. What changed

| Change | Files | Why |
|---|---|---|
| `CAM_STREAM` in `.env` (default `stream1`) | `cameras.py` | the test copy uses `stream2`, which the camera serves to several clients (ARQUITETURA 18.2) |
| `WEB_PORT` in `.env` (default 8765) | `cameras.py`, `web.py` | production 8765, test copy 8766 |
| `notify_prefix` in `config.json` | `settings.py`, `notify.py` | test notifications marked `[TEST]` |
| Logging to `logs/jarvis.log`, rotating 1 MB x 5, plus uncaught exceptions in any thread | new `log.py`; `print` replaced in `cameras.py`, `clips.py`, `web.py` | a scheduled task has no console |
| Clean stop without Ctrl+C: `POST /api/shutdown`, loopback only; `python -m jarvis --stop` waits until the service is gone | `web.py`, `cameras.py` | ending a scheduled task kills the process without the `finally` that assembles pending clips |
| R1: notification retried once per new label during an event; photo of that moment saved as `HH-MM-SS.alert.jpg`, deleted if nothing was sent | `clips.py` | a person arriving after a dog was never announced |
| R2: the web takes the port before the cameras open; `web.attach(core)` afterwards | `cameras.py`, `web.py` | two launches during the slow startup brought up two copies |
| R3: live view shows "no signal" for a frame older than 5 s; page reconnects when the server's start time changes | `capture.py` (`frame_age`), `cameras.py`, `web.py` (`/api/status`), `app.js` | a dead stream looked like a quiet scene |
| R5: "probably X" below `LEARN_THRESHOLD` (0.45) | `notify.py` | weak matches were announced as certain |
| R8: red "No connection to J.A.R.V.I.S." banner when the server stops answering | `app.js`, `index.html`, `style.css` | failures were silent |
| `/api/status`: cameras, server start time, seconds since each camera's last frame | `web.py`, `cameras.py` (`frame_ages`) | used by the page (R3) and by the update script's health check |
| JSON read as `utf-8-sig` (BOM accepted) | `clips.py`, `faces.py`, `settings.py` | a `config.json` saved with a BOM by an editor was silently ignored, token included (found while testing, section 5) |
| `tools/check_data.py` | new | reads every event, sighting, the gallery and `config.json` with the current code; exit 1 if any is unreadable |
| `tools/production.ps1` (`install`, `update`, `status`, `start`, `stop`, `check`) | new | ARQUITETURA 18.3 |
| Web routes, page text, terminal output, CLI flags moved to English (part of R10) | `web.py`, `static/*`, `cameras.py` | renaming after production is installed would break bookmarks and the startup task |
| `logs/` ignored | `.gitignore` | |
| Process rule and "generated files must never break" | `CLAUDE.md` | user decision, mid-delivery; the developer's only documentation edit, so the next session follows it. Please review the wording |

**Renamed (old names still work where something may depend on them):**

| Old | New | Old still works? |
|---|---|---|
| `--sem-janela` | `--headless` | yes (alias) |
| `--janela` | `--window` | yes (alias) |
| — | `--stop` | new |
| `/api/dias`, `/api/eventos?dia=` | `/api/days`, `/api/events?day=` (response keys `day`, `events`) | no — only the bundled page used them |
| `/miniatura/...`, `/ao-vivo/...`, `/icone.png` | `/thumbnail/...`, `/live/...`, `/icon.png` | no, same reason |

### 2. Files on disk — compatibility

**Nothing breaking.** Every change is additive:

| What | Change | Older version reading it |
|---|---|---|
| `clips/<cam>/<day>/HH-MM-SS.alert.jpg` | new, optional | ignores it; the archive moves it with the event (`glob(f"{base.name}.*")`) |
| `.env` `CAM_STREAM`, `WEB_PORT` | new, optional | ignores them (`build_camera_list` only takes `CAM_*_IP`) |
| `config.json` `notify_prefix` | new, optional | `settings.load()` ignores unknown keys, but **`settings.save()` drops them** — an older version saving would erase the prefix |
| `logs/` | new folder | — |
| Reading JSON as `utf-8-sig` | more tolerant | — |

`tools/check_data.py` on the M900 data: **149 events, 7 people, 20 face
sightings, `config.json` with 7 keys — all readable.**

**Suggest a new ARQUITETURA section 19, "Files on disk"** — the code already
points to it (docstrings in `clips.py` and `tools/check_data.py`): one table per
file (path, writer, readers, fields, optional fields and since when), the
compatibility rule, `check_data.py`, the BOM finding, and the `save()` drops
unknown keys caveat above.

### 3. Suggested documentation updates

| Document, section | Update |
|---|---|
| ARQUITETURA 12 (notification) | R1 and `.alert.jpg`; R5 wording; `notify_prefix`; messages now English ("X recognized", "probably X", "unknown face") |
| ARQUITETURA 15.5, INSTALACAO 2 | run modes: no flag = service + browser, `--headless`, `--window`, `--stop`; old flags are aliases |
| ARQUITETURA 17.6–17.7 | new route names; `/api/status`; R2 (port before cameras, `attach`); R3 (stale frame, page reconnect, `started`); R8 banner; page now in English, labels shown as the system names them (no translation table anymore) |
| ARQUITETURA 18 | 18.4 is implemented; document `production.ps1` and the task design (section 4 below); test copy configuration; the desktop shortcut becomes a `.url` to production |
| ARQUITETURA 19 (new) | section 2 above |
| INSTALACAO | "how to run before installation" (section 6 below); production install and update steps; `logs/jarvis.log` as the first place to look; troubleshooting quotes old Portuguese messages that are now English ("Interface web desligada...", "O J.A.R.V.I.S. ja esta rodando", "Vigilancia rodando") |
| CONTEXTO 13.4 | R1, R2, R3, R5, R8 done; R7 partly (`production.ps1` checks the signature, `instalar.bat` still does not) |
| CONTEXTO 4 (bugs) | the two `production.ps1` bugs caught in testing (section 5) |
| CONTEXTO 8 | backlog 17 progress; R10 progress (what moved to English) |

### 4. Production design decisions taken in code — please review

- The task runs `C:\JARVIS\.venv\Scripts\pythonw.exe -m jarvis --headless`
  directly: no console, and no uv trampoline. `pythonw.exe` there is signed by
  the PSF (checked).
- Trigger at startup, logon type **S4U** (runs whether or not anyone is logged
  on, without storing a password). Registering it needs an administrator
  PowerShell, so **the user runs the install**.
- `ExecutionTimeLimit` set to zero. **The Task Scheduler default is 72 hours**:
  left alone, it would kill the surveillance every three days.
- Restart on failure every minute, up to 999 times; `MultipleInstances
  IgnoreNew`. A clean `--stop` exits with code 0, so it does not trigger a
  restart.
- Install **copies** `models/`, `clips/`, `faces/`, `.env`, `config.json` from
  the development folder (originals stay). Then the development folder becomes
  the test copy: `CAM_STREAM=stream2`, `WEB_PORT=8766`, Telegram token removed
  there, prefix `[TEST]`. Desktop: `J.A.R.V.I.S.` (a `.url`) opens production;
  the old shortcut becomes `J.A.R.V.I.S. (test)`.
- Update: data check with the current code, clean stop, `git checkout --force
  <tag>`, `uv sync --frozen`, signature check, data check with the new code,
  start, health check (every camera's last frame under 5 s within 90 s).
  Anything failing → back to the previous version, plus a Telegram message.
- The install assumes **the test copy lives in this folder on the M900**. The
  user has not answered ARQUITETURA 18.5 yet (test on the M900 or the other
  computer; who runs updates). If the answer is "the other computer", only
  `ConfigureTestCopy` changes.

### 5. Measurements and tests

| Test | Result |
|---|---|
| R1: dog, then person, with `notify.event` stubbed | 2 attempts (`dog` refused, `person` sent with `.alert.jpg`); when nothing is sent, no `.alert.jpg` is left |
| R5 | "Izabel recognized" (0.62), "probably Izabel" (0.38), "unknown face" |
| `CAM_STREAM` | `stream1` by default, `stream2` when set |
| Shutdown from a LAN address | 403 |
| R2: second launch 3 s into the first's camera startup | it left; exactly 2 ffmpeg running |
| `--stop` | clean path in the log ("Shutdown requested" → "Assembling pending clips" → "Stopped."), about 3 s |
| R3: `live_view` with frame age 1 s / 10 s | live picture / no-signal panel |
| `production.ps1 install -SkipTask` into a temp folder (clone from the local repo) | 31 s; data copied, environment on the signed Python, both cameras fresh; `status`, `stop` and `check` worked; folder removed afterwards |
| `check` with one event JSON corrupted | exit 1 naming the file; intact or restored: exit 0 |

**Bugs caught in my own script while testing — worth a learning note:**

1. `CheckData` always "passed". In PowerShell, everything a command prints
   inside a function joins the function's return value: it returned the
   script's output lines plus `$true/$false`, and a non-empty array is truthy.
   The data gate the user asked for did not gate. Fixed with `| Out-Host`, and
   proven with a corrupted file.
2. A helper named `Git` shadowed `git.exe` — PowerShell names are
   case-insensitive — so the helper would have called itself forever. Renamed
   `Invoke-ProdGit`.

**BOM finding:** restoring a test file with PowerShell's
`Set-Content -Encoding UTF8` added a byte-order mark, and the program could no
longer read it (`json.loads` with `utf-8`). The check caught it. That is how
`config.json` edited in an editor could have silently lost the token; reading
as `utf-8-sig` now accepts both.

### 5a. Reported by the user after the delivery: LAN access, "Invalid HTTP request"

Locally the page worked; from the other computer the service logged bursts of
`WARNING uvicorn.error: Invalid HTTP request received.` (3-4 per second, the
pattern of a browser opening parallel connections). Reproduced here: an
`https://127.0.0.1:8765/` request produces exactly that warning, `http://`
answers 200. Cause: the other computer's browser tried **HTTPS** (typed without
the scheme, or "Always use secure connections" is on); the server speaks only
HTTP. Told the user to type `http://192.168.0.18:8765` explicitly, or click
through the browser's warning, or turn that browser setting off.

For INSTALACAO troubleshooting. Possible follow-up for the architect to weigh:
HTTPS on the LAN needs a certificate the browser trusts; self-signed means a
warning on every visit, so not recommended now. The user has not yet confirmed
access works with `http://`.

### 6. How to run before installation (for INSTALACAO)

Everything runs from this folder, on `stream1`, port 8765:

| Want | Command |
|---|---|
| service + browser | `jarvis.bat` or the desktop shortcut |
| service only | `jarvis_vigilancia.bat`, or `uv run python -m jarvis --headless` |
| stop cleanly | Ctrl+C in its console, or `uv run python -m jarvis --stop` from any terminal |
| old OpenCV window | `uv run python -m jarvis --window` |
| what happened | `logs\jarvis.log` |
| are old files readable | `uv run tools/check_data.py` |

### 7. Learning topics worth a place in PYTHON.md (or a PowerShell note)

- `logging` instead of `print`: logger per module (`getLogger(__name__)`),
  handlers, `RotatingFileHandler`, lazy `%s` formatting, `sys.excepthook` and
  `threading.excepthook`. C# parallel: `ILogger` and sinks.
- `threading.Event` as a stop signal handed across threads by callback
  (`on_stop`), instead of a global flag.
- FastAPI `Request.client` and why the shutdown route is loopback-only when the
  port is open to the LAN; 403 vs 503.
- PowerShell traps from section 5, plus `$ErrorActionPreference = 'Stop'` turning
  a native program's stderr into an exception, and `$LASTEXITCODE`.
- Task Scheduler: S4U, the 72-hour default, restart-on-failure.
- `utf-8-sig` and the BOM.
- Release tags, `git checkout <tag>` (detached HEAD), `uv sync --frozen`.

### 8. What the review should look at hardest

1. **`tools/production.ps1` paths never executed:** `RegisterTask` (needs
   admin), `Update` between two real versions, **the rollback path**,
   `ConfigureTestCopy`, `DesktopShortcut`. Installing with `-SkipTask` skips the
   last two on purpose.
2. **Downgrade vs `check_data`:** unknown `config.json` keys count as a
   problem, so an update to an *older* tag after a newer one added a key fails
   the "after" check and rolls back to the newer one. Probably right, maybe
   too strict — warning instead of failure?
3. **Concurrency:** `live_view` and `frame_ages` read camera state from the web
   threads; `_on_stop` runs in a web worker thread and only sets an `Event`.
4. **R10 is partial:** still Portuguese — `capture.py` error messages
   (`TRANSLATIONS`, "FALHOU - ..."), `ui.py`, `notify.discover_chat()` messages,
   `.bat` and `tools/` file names and their output.
5. **Before installing:** review, tag a release (e.g. `v2026.10.09`), **push
   the tag** (production clones from GitHub), the user's answers to
   ARQUITETURA 18.5, then the user runs, in an administrator PowerShell:
   `powershell -ExecutionPolicy Bypass -File tools\production.ps1 -Action install`.
