# J.A.R.V.I.S. — project context

This file lets a new Claude Code session continue the work without losing
what was decided, tested and ruled out. **Read it before touching anything.**
It is the brief; the past lives in `HISTORY.md`, read on demand.

| Document | For |
|---|---|
| `ARQUITETURA.md` | How the system works and why, layer by layer |
| `INSTALACAO.md` | Installing and running on a new machine, troubleshooting |
| `PYTHON.md` | Python and the libraries, for someone coming from Java and C# |
| `HISTORY.md` | Bugs already fixed, old measurements, every review in full, closed recommendations, old usage rows |
| **this file** | The rules, the current state, the backlog, the open recommendations, the plan |

Section numbers here are stable on purpose: `CLAUDE.md`, the `dev` skill and
the code point at them. A section whose content moved to `HISTORY.md` keeps
its number with a pointer.

---

## 1. The project

Home surveillance with two outdoor TP-Link **Tapo C310** cameras over RTSP.
The system detects motion, decides whether it is a person or an animal,
records the event without re-encoding, recognises faces and the household's
dogs, and sends what matters to the user's phone through Telegram. The only
interface is a web page served by the service itself: **Live**,
**Recordings**, **People**, **Dogs**, **Notifications** and **Settings**.

**Two machines:**

| | Development | Production |
|---|---|---|
| Machine | Ryzen 9 7950X, 64 GB, RTX 4080 | Lenovo M900, i5 Skylake 4 cores, 16 GB |
| Path | `D:\Personal Projects\J.A.R.V.I.S\jarvis` | `C:\Personal Projects\jarvis` (this folder: the test copy) |

**Production runs on the M900 since 09/10/2026**, from `C:\JARVIS`, a clone
checked out at a **release tag**, started with Windows by a scheduled task
and changed only by `tools/production.ps1` (ARQUITETURA 18.7). Every release
is deployed the same way — every file read before and after with the new
code, rolled back on its own if anything fails; the current one is the last
row of `HISTORY.md` 13.2 and section 13.2 below. The folder above is the test
copy, on `stream2` and port 8766, with no Telegram token (INSTALACAO 9).

**The RTX 4080 is deliberately ignored.** Nothing here is trained, and
developing on the same CPU path the M900 uses avoids divergence between the
machines.

## 2. How the user works — follow this

Rules the user set explicitly:

**No comments in code.** None. Every explanation lives in `docs/`; one-line
docstrings are accepted. Check before committing:

```bat
uv run python -c "import tokenize,pathlib; print(sum(sum(1 for t in tokenize.generate_tokens(tokenize.open(f).readline) if t.type==tokenize.COMMENT) for d in ('src','tools') for f in pathlib.Path(d).rglob('*.py')))"
```

It looks only at `src/` and `tools/`; `.venv` holds thousands of third-party
comments.

**Every change ends in a commit**, without being asked. The message explains
**why**, not only what. **The developer never updates documentation:** it
writes `HANDOFF.md`, and the architect integrates it (13.1, `CLAUDE.md`).

**Generated files must never break** (the user, 09/10/2026). A new version
reads everything an older one wrote. Changes are additive; anything else is
announced to the user first and ships with a migration. `tools/check_data.py`
proves it, and every production update runs it (ARQUITETURA 19).

**Before committing, check that `.env` did not go in.** It holds the real
camera passwords, which once leaked into examples in the documentation and
had to be fixed. Check `models/`, `clips/`, `faces/`, `dogs/`, `reports/`,
`backups/` and `config.json` too — all are in `.gitignore`, but a careless
`git add -A` after touching it would take them.

**Explain the code, not only the result.** The user is learning Python and
OpenCV, coming from Java and C#. They asked for concise answers about options
and tangents, but **never** skimp on explaining code or a command — they
complained when that was cut too short. Each delivery's concepts go to
`PYTHON.md`.

**Language** (the user, 09/10/2026): only the conversation with the user is
in Portuguese. Code, identifiers, commits, documentation and every text the
program shows are in English; the raid log scripts are in both. The table is
in `CLAUDE.md`.

## 3. Decisions taken — do not undo without a new reason

**Python, not C++.** OpenCV's Python bindings call the same compiled C++, with
microseconds of overhead per call. The real time is in decoding and inference,
both native. The vision ecosystem is Python-first.

**ffmpeg, not `cv2.VideoCapture`.** `VideoCapture` hands out decoded frames,
which forces **re-encoding** to save. Measured: the old pipeline made files
**25 % larger than the camera's original, with three generations of loss**.
One ffmpeg process per camera serves two outputs — `-c copy` segments (a byte
copy) and 960×540 frames for analysis (ARQUITETURA 5.1, 5.2).

**No PyTorch.** Windows 11's **Smart App Control** blocks binaries without a
recognised signature, and PyTorch's DLLs are unsigned (`WinError 4551`).
Turning it off is **irreversible** without reinstalling Windows. YOLO runs
through `cv2.dnn` on the official `yolo11s.onnx`, which also removed ~2.5 GB of
dependencies. Measured 09/10/2026 on the same blob, CPU against CPU:
`cv2.dnn` 37.8 ms, `onnxruntime` 34.6 ms, identical output — another ONNX
runtime would buy nothing; the real loss was GPU to CPU, which the M900 cannot
undo (ARQUITETURA 7.11). The low dependency count that followed is **not a
merit of the project** (section 11).

**The official signed Python, not the one `uv` downloads.** Smart App Control
lets an unsigned Python run only while Microsoft's cloud gives it a good
reputation — a verdict that changes on its own. On 09/10/2026 it blocked the
very interpreter that had run on 29–30/09, with nothing changed on disk. The
python.org build is signed by the PSF and always passes; `pyproject.toml`
says `python-preference = "system"`, and the `.bat` files call
`uv run python -m jarvis` instead of the unsigned `jarvis.exe`. The rule: **on
the M900 every executable in the path must be signed** — reputation is no
guarantee. The same reason makes the tests run as `python -m pytest`
(ARQUITETURA 19.5, INSTALACAO 1.2).

**A web interface with FastAPI.** `http.server` was considered and dropped: it
is single-threaded, so live MJPEG would block everything, and it has no HTTP
Range, which `<video>` needs to seek. `pydantic_core` (compiled Rust) loads
under Smart App Control on both machines (HISTORY 12.2). The web is the only
way in, by the user's decision (ARQUITETURA 17).

**No compressing the videos.** Built and removed. Measured on a real file: zip
saves **0.2 %**, bzip2 and lzma make the file **bigger**. H.264 is already
entropy-coded (ARQUITETURA 8.7).

**One RTSP connection per camera.** The Tapo accepts one session on `stream1`;
a second gets `406 Not Acceptable`. That is why one ffmpeg makes both outputs.

**Faces in the clip, not live.** A 60 px face in 1080p becomes 30 px in the
960×540 analysis frames, and the recogniser wants ~112 px. `scan_clip()` runs
on the assembled clip at full resolution, off the critical path. This is also
why a person's name is known only seconds after the event (ARQUITETURA 22.3).

**YuNet and SFace, not InsightFace.** Both built into OpenCV, no new
dependency. Measured: similarity **1.000** for the same face and **0.045** for
different faces, with a 0.363 threshold.

**Nothing about this house's dogs in the code** (the user, 10/10/2026). Each
household teaches the system its own dogs on the Dogs tab (ARQUITETURA 20).

## 4. Bugs found and fixed — do not reintroduce

Moved to `HISTORY.md` 4: each bug with its cause and fix. Read it before
changing capture, motion, the face scan, notifications or production.

## 5. Reference measurements

Moved to `HISTORY.md` 5. Measurements behind a current rule stay beside the
rule in `ARQUITETURA.md`.

## 6. Solved: the M900 got no frames (29/09/2026)

Moved to `HISTORY.md` 6. The lesson that still applies: on a new machine,
test the camera IP in `.env` first (INSTALACAO 8).

## 7. Known and accepted limitations

- **Face recognition at night is unreliable.** Infrared gives ~44 px faces:
  finding a face works, telling whose it is does not. **The biggest possible
  gain is not software: a motion-triggered light** takes the camera out of
  infrared (backlog 16).
- **Only the household's dogs are named**, and only when the user has named
  enough views; two dogs that look alike stay "dog", the honest answer. Other
  animals are only labels (`cat`, `bird`…), and YOLO's hesitation between
  species accumulates in `labels` (ARQUITETURA 7.1).
- **A person standing still for ~12 s is suppressed** by the static-scene
  suppression until they move again.
- **No archive configured in production.** Recordings grow ~300 MB/day in
  `clips/`; the archive (ARQUITETURA 11) moves them to an external drive after
  30 days only when `archive_path` is set, and production's is empty. The
  rolling buffer in `clips/_buffer/` cleans itself.
- **No undo of a merge** on People or Dogs (closed by the user, backlog 9): a
  warning comes before every merge.

## 8. Backlog

**The project's single list.** Both machines see it through git. Each item
says where it came from:

- **(decided)** — the user asked for it or approved it
- **(proposto)** — Claude's suggestion, no decision from the user yet

Proposed items **are not a plan**. Never start one without asking. The
architecture review's recommendations are separate (13.4) and the
**high**-priority ones come before items here. The full text of every
finished item is in `HISTORY.md` 8.

### Done

| | Item | Where |
|---|---|---|
| ✓ | Tiered storage (decided) — to an external drive after 30 days | ARQUITETURA 11 |
| ✓ | Phone notifications through Telegram, with a face and a name (decided) | ARQUITETURA 12 |
| ✓ | Core without a window (decided) | ARQUITETURA 15 |
| ✓ | **3.** The web interface, the only way in (decided 09/10) | ARQUITETURA 17 |
| ✓ | **5.** Play recordings on the page (decided 11/10, `v2026.10.11.3`) | ARQUITETURA 17.13 |
| ✓ | **9.** Undo a merge — closed by the user: a warning before every merge instead | — |
| ✓ | **15.** Animal re-ID — superseded by 22 | HISTORY 8 |
| ✓ | **17.** Production and test environments (decided 09/10) | ARQUITETURA 18.7 |
| ✓ | **18.** The running version on the page (decided 10/10) | ARQUITETURA 12.10 |
| ✓ | **19.** People by person; attach a face to a name; the waiting queue; rename (decided 10/10, `v2026.10.10.4`) | ARQUITETURA 17.10 |
| ✓ | **20.** Who appears in each recording (decided 10/10) | ARQUITETURA 17.10 |
| ✓ | **21.** A favourite photo per person (decided 10/10, `v2026.10.10.6`) | ARQUITETURA 17.10 |
| ✓ | **22.** A Dogs tab: each household teaches its own dogs (decided 10/10, `v2026.10.10.7`); thresholds wait for ~10 named views per dog per lighting | ARQUITETURA 20 |
| ✓ | **23.** Report a bad detection instead of deleting it, with Undo (decided 11/10, `v2026.10.11.4`) | ARQUITETURA 21 |
| ✓ | **24.** "Choose the best 40" views; Chosen and Waiting (decided 11/10, `v2026.10.11.4`) | ARQUITETURA 17.14 |
| ✓ | **25.** Residents, notification cases and the Home/Away/Silent modes, the Notifications tab, commands from the phone (decided 12/10, `v2026.10.12`) | ARQUITETURA 22 |

**Waiting for the user's check on the M900:** item 25 — mark the user, Mirana
and Aurora Resident, choose Home, and confirm that a recognised resident sends
nothing, a person with no face does, and `/away` from the phone changes the
mode the page shows. Item 3 — open the page from a phone
(`http://192.168.0.18:8765`).

### Critical

Without these the system does not do its job well.

1. **Zones of interest per camera** (proposto) — today there is only a fixed
   mask over the camera's clock, in the code. Every competitor has drawable
   zones, and it is the biggest control over false positives there is.
   Mosquitoes, wall objects and sunlight have already cost time; a zone saying
   "only the garage matters" would have avoided almost all of it. Worth
   separating a **mask** (ignore the area) from a **required zone** (detect
   everything, but notify only when something enters it).
2. **System health** (proposto) — if a camera dies at 3 a.m., nothing warns.
   There is an automatic restart, but no record of how long it was down. A
   daily summary, or a "camera down" case among backlog 25's switches, would
   close it.

### Important

It works without them, but is incomplete.

4. **Measure the M900 running** (proposto) — CPU with both cameras in motion,
   and whether `HWACCEL` helps (INSTALACAO 6).
6. **Search and filter** (proposto) — with ~100 events a day, by date only is
   not enough. By person, camera, label.
7. **Tracking** (proposto) — keep identity across frames; it solves the person
   standing still and makes one clip match one person.
8. **Animal labels** (proposto) — accept a species only when it repeats within
   the event, instead of accumulating every YOLO hesitation.
10. **Audio** (proposto) — the cameras send PCM and `-an` drops it. Barking,
    shouting, breaking glass.

### Improvement

11. **A timeline** (proposto) — a grid of cards does not answer "what happened
    between 2 and 4 a.m.".
12. **Persist the static spots** (proposto) — the list starts empty on every
    run, so the night's first false clip is still recorded.
13. **An event database** (proposto) — SQLite instead of JSON files, once
    there is search.
14. **OpenVINO on the M900** (proposto) — `cv2.dnn` accepts that backend; it
    was the plan to win back the speed lost when leaving PyTorch.

### Outside software

16. **A motion-triggered light at the Front** (proposto) — not code, but the
    biggest possible gain for faces at night (ARQUITETURA 10.5).

### Deliberately out of scope

Competitors have these and they make **no** sense here: multiple users with
permissions, cloud or subscription, support for dozens of camera brands, PTZ,
two-way audio, number-plate reading, Home Assistant integration. They are
product features; this system is for one house with two cameras. If someone
proposes one, the answer is already here.

## 9. Repository map

```
src/jarvis/
  __init__.py     ROOT, the project root
  __main__.py     python -m jarvis
  cameras.py      the Core (surveillance, no window), main(), run_headless
  capture.py      one ffmpeg per camera: original segments + analysis frames
  motion.py       layer 1: MOG2 + temporal confirmation
  people.py       layer 2: YOLO through cv2.dnn, people and animals
  clips.py        layer 3: events, lossless assembly, metadata, the held person
  faces.py        layer 4: YuNet + SFace, the gallery, naming
  dogs.py         the dog gallery: crops, appearance descriptor, matching
  archive.py      layer 5: moves to the external drive, deletes only there when full
  settings.py     settings editable from the page (config.json)
  notify.py       Telegram messages: thumbnail, face, cooldowns, the cases
  modes.py        notification cases, the Home/Away/Silent modes and their switches
  bot.py          commands from the phone: long polling, switches the mode only
  reports.py      bad-detection reports and their Undo
  devices.py      paired devices for the write guard
  log.py          logging: console, crash hooks, logs/jarvis.log for the service
  web.py          the web interface: FastAPI in a thread beside the Core
  static/         the page: index.html, style.css, app.js
  geometry.py     Detection type and box utilities
tests/            pytest: python -m pytest (ARQUITETURA 19.5)
tools/
  production.ps1  production on the M900: install, update, start, stop, status, check
  check_data.py   reads every file on disk with the current code (ARQUITETURA 19)
  replay.py       why each frame of a video was kept or dropped (ARQUITETURA 12.10)
  face_tuning.py, dog_tuning.py, dog_crops.py   measure thresholds; crop past dog events
  diagnostico.py  capture diagnosis (variants, and --local without a camera)
  probe_rtsp.py   raw RTSP diagnosis (DESCRIBE → SETUP → PLAY)
  refazer_rostos.py  rebuilds faces/ from the recorded clips
  verificar_clipes.py  counts damaged blocks per camera on one day
  gerar_epub.py, epub.css   every .md into one EPUB for an e-reader
  gerar_icone.py, criar_atalho.ps1   the icon and the desktop shortcut
assets/           jarvis.ico and a PNG preview (generated, but versioned)
docs/             ARQUITETURA, INSTALACAO, PYTHON, HISTORY and this file
docs/raidlog/     the comic script of each release, English and Portuguese (section 15)
CLAUDE.md         instructions for Claude Code (roles, language, rules)
.claude/skills/dev/SKILL.md  the developer's session: /dev or "Dev, ..."
HANDOFF.md        developer → architect notes; empty between deliveries
instalar.bat      install on a new machine
jarvis.bat        start the service and open the browser
jarvis_vigilancia.bat  service only, no browser (--headless)
```

Structure explained in ARQUITETURA 3. Not versioned: `.env` (credentials),
`config.json` (Telegram token, PIN), `models/` (~73 MB, downloaded on
demand), `clips/`, `faces/`, `dogs/`, `reports/`, `devices.json`, `backups/`
(copies the tools make before touching data), `logs/` and `HOLD`.

**Outside the repository:** `C:\JARVIS` on the M900 is production — a clone
of the same GitHub repository at a release tag, with its own `.env`,
`config.json` and data. Never edit it by hand; `tools/production.ps1` is the
only thing that changes it (ARQUITETURA 18.7).

## 10. Useful commands

Production, on the M900 (prefix every line with
`powershell -ExecutionPolicy Bypass -File`):

```bat
tools\production.ps1 -Action status      version, task, port, age of each camera's last frame
tools\production.ps1 -Action update      to the latest release tag; rolls back on its own if it fails
tools\production.ps1 -Action stop        stays stopped, even after a reboot, until start
tools\production.ps1 -Action start       releases the hold and starts
tools\production.ps1 -Action check       tools/check_data.py against production's data
C:\JARVIS\logs\jarvis.log                what production did
http://127.0.0.1:8765                    production's page (another computer: http://192.168.0.18:8765)
```

Test copy and tools, from this folder:

```bat
jarvis.bat                                              test copy: service + browser (port 8766 here)
uv run python -m jarvis --headless                      service only, no browser
uv run python -m jarvis --stop                          stop the copy running from this folder, cleanly
uv run python tools/check_data.py                       can the current code read every file on disk?
uv run python -m pytest                                 the automatic tests (not `uv run pytest`: ARQUITETURA 19.5)
uv run python tools/replay.py <video> [--prime]         why each frame was kept or dropped
uv run python tools/diagnostico.py Front                test capture variants
uv run python tools/diagnostico.py --local              test ffmpeg without a camera
uv run python tools/probe_rtsp.py <ip> <user> <pw> stream1   raw RTSP
powershell Test-NetConnection <ip> -Port 554            does the camera answer on that IP?
uv run python tools/refazer_rostos.py                   rebuild faces/ (stop the program first)
uv run python tools/verificar_clipes.py [YYYY-MM-DD]    image damage coming from the cameras
uv run python tools/gerar_epub.py                       the documentation as an EPUB
tasklist | findstr ffmpeg                               look for an orphaned ffmpeg
```

**The documentation EPUB.** `tools/gerar_epub.py` joins every `.md` of the
project into one EPUB in `docs/epub/`, one chapter per document, so the
cross-references stay a tap away on the reader. New documents join on their
own (the `ORDEM` list sets the known ones' order; anything else goes at the
end). The `.md` files are never changed, EPUBs are not versioned, and the
script checks at the end that the count of tables and code blocks matches the
sources, including tables nested in list items. It needs pandoc
(`winget install --id JohnMacFarlane.Pandoc -e`, found even off the PATH;
installed on the M900, 3.12.1). `tools/epub.css` keeps it readable on 7
inches: code at 0.68em with forced wrapping. **The architect's job, only when
the user asks** ("gere o epub", decided 10/10/2026): only the user reads it.

Tuning constants: `capture.py` (`ANALYSIS_FPS`, `HWACCEL`, `SEGMENT_SECONDS`,
`SOCKET_TIMEOUT_SECONDS`), `people.py` (`MIN_INTERVAL`,
`MIN_PERSON_HEIGHT_FRACTION`, `ANIMAL_CONFIDENCE`), `motion.py` (`MIN_AREA`,
`CONFIRM_FRAMES`, `LIGHTING_CORRELATION`), `faces.py` (`MATCH_THRESHOLD`,
`LEARN_THRESHOLD`, `IDENTITY_SCORE`, `MIN_VIEWS_FOR_NEW`), `notify.py`
(`MAX_FACES`), `bot.py` (`LONG_POLL_SECONDS`, `STALE_SECONDS`).

---

## 11. Claude's biases — constraints the user never chose

This section exists because the user asked **"where can I find these biases
you may have created?"** The honest answer was: nowhere. Section 3 records
decisions, but a decision has an author. What was missing was a record of what
Claude started treating as a rule **with nobody having decided it**.

### 11.1 How these biases form

The pattern is always the same, and easy to miss:

1. A real constraint appears — environment, hardware, a concrete error.
2. Claude works around it. Right so far.
3. The workaround is repeated in later decisions **as if it were a goal**.
4. The documentation starts justifying it, and the accident becomes a
   principle.

Step 3 is invisible because step 2 was right. The warning sign is a
justification that describes a consequence as if it were an aim — "the
project stays at two dependencies" was exactly that.

### 11.2 How to audit

Look for justifications that cite neither a request from the user nor a
measurement:

- phrases like "so as not to bring in", "to keep", "instead of depending on",
  "avoids the dependency" in `docs/`;
- any number treated as a target (dependency count, file size, lines) that
  does not appear as a measurement;
- anything written by hand that exists ready-made in a well-regarded library.

The user's rule, 09/10/2026: **reusing code, especially well-regarded
libraries, is always the best path.** Application size is not a criterion;
the efficiency and quality of the dependencies are.

### 11.3 Log

**Dependency minimalism — corrected 09/10/2026.** PyTorch broke under Smart
App Control (an unsigned DLL, `WinError 4551`). Switching to `cv2.dnn` was
right. The mistake was generalising: "fewer dependencies" became a design
criterion, and Claude started writing by hand things that existed ready-made.
It cost a whole session debugging TLS to reimplement what `requests` already
delivers (ARQUITETURA 12.5). The correct rule is narrower: **be wary of large
binary dependencies**, because that is what broke the deploy. A pure-Python or
data-only package does not have that problem and needs no justification.

**A HighGUI interface — recognised and corrected 09–10/10/2026.** The OpenCV
window was the natural path while the program was only a camera viewer. It
became `ui.py` with 616 lines and 60 primitive drawing calls, and OpenCV has
no widgets: no pasting, no video, no scrolling lists, no accents. It had
already bent decisions — the settings tab opened `config.json` in an editor
because a token could not be pasted into the window. Worse was what it
dragged along: **the surveillance loop rode on the window** — `cv2.waitKey`
set the pace and closing the window stopped recording. The user saw it
themselves when saying they would not always want to watch live. The core was
separated (ARQUITETURA 15) and the window removed on 10/10 (`v2026.10.10.4`).
**A correction of merit:** when proposing this, Claude said the M900 spent CPU
drawing for nobody. True, but measured afterwards it was small — about 6 % of
a frame. The gain of the separation is not CPU; it is surveillance that does
not die with the window.

**No tests — never discussed, corrected 10/10/2026.** 2,600 lines and no
tests; Claude never proposed them and the user never refused. R6 added them;
there are 160 on 12/10 (ARQUITETURA 19.5).

**Everything in one process — a consequence, not a choice.** Capture,
detection, recording, faces, the web and the Telegram poller share one Python
process, with threads for whatever must not block. It works with 2 cameras;
it was not assessed for more, and the GIL stands in the way. Only recorded;
not a problem today.

---

## 12. Resume routine — run this when opening the project

**This section is for Claude, not the user.** The user does not run setup
commands by hand and expects the context to leave any machine ready to
continue. Do it before answering, and report only the result.

### 12.1 Always

```bash
git pull --ff-only
uv sync
```

`git pull` first, because the project is edited on two machines. On a
conflict or divergence, stop and show the user instead of resolving it
alone. `uv sync` because dependencies change between commits.

**Pushing is Claude's job too**, and within Claude the architect's (09/10/2026):
the user no longer pushes or pulls by hand. Confirm against the server, not
the push output:

```bash
git push jarvis master
git ls-remote jarvis -h refs/heads/master
```

or `git rev-list --count jarvis/master..HEAD`. The local tracking ref goes
stale when the other machine pushes, and once made Claude claim there were
pending commits when there were none, and the opposite too. **The remote is
called `jarvis` on both machines** (on a new clone: `git remote rename origin
jarvis`).

**On the M900, check production too:**

```bat
powershell -ExecutionPolicy Bypass -File tools\production.ps1 -Action status
```

Every camera's last frame should be a few seconds old at most. Anything else —
HELD when nobody stopped it, not running, an old frame — goes to the user
before anything else, with the tail of `C:\JARVIS\logs\jarvis.log`.

**Record the usage at the start of the session** (section 14): plan usage
from `get_usage`. The architect writes a row in 14.3 and fills it in at the
end; the developer keeps its numbers for `HANDOFF.md`.

**Check that Python still runs.** If `uv sync` or `uv run` fails with `Failed
to spawn: python` or `WinError 4551`, Smart App Control is blocking an
unsigned interpreter. The way out is in INSTALACAO 1.2 — the official Python
and a recreated `.venv` — and it is yours: do it before answering.

### 12.2 Check what the item in progress needs

Read section 8 and 14.4 and find the item in progress. If it has a recorded
precondition, test it **now**, on this machine, and record the result in the
same commit as the next change. (The last one, `pydantic_core` loading under
Smart App Control, passed on both machines: HISTORY 12.2.)

### 12.3 Say where things stand

Then tell the user: where the work stopped, what comes next and whether a
precondition failed. Never ask them to run something you could run. Read the
**open** recommendations (13.4): high-priority ones come before the next
backlog item unless the user says otherwise. **If 14.4 holds a planned session
for your role, that is the plan** — the architect wrote it with the order and
the reasons. Follow it, and say so when you deviate.

### 12.4 What does not travel through git

| File | Why | Consequence |
|---|---|---|
| `.env` | camera credentials | each machine has its own; `instalar.bat` creates it if missing |
| `config.json` | the Telegram token and the PIN | **notifications start off on a new machine** |
| `models/` | ~73 MB | downloaded on first use |
| `clips/`, `faces/`, `dogs/`, `reports/` | recordings and galleries | local by nature |

If `config.json` is missing or has no `notify_token`, tell the user — it is
the only thing here that needs them, because the token is a credential only
they have. The chat is found on the Notifications tab with Find chat.

---

## 13. Architecture review

### 13.1 How it works — agreed 09/10/2026

The user splits the work into two roles, as in a team:

| Role | Claude's mode | Does |
|---|---|---|
| **Developer** | `high` | implements, tests, commits locally, writes `HANDOFF.md` |
| **Architect** | `ultracode` | reviews, documents, manages the backlog, syncs with GitHub, tags releases |

The developer never edits documentation. At the end of a delivery it writes
`HANDOFF.md` — what changed, data-format impact, suggested documentation by
section, topics worth teaching, what to review hardest — and asks: *"Arquiteto,
precisamos da sua análise."* The architect decides what is worth documenting,
integrates it, empties the file, pushes, and tags a release when the code is
fit for production. Production only ever runs tags (ARQUITETURA 18.7), named
`vYYYY.MM.DD`; a second release on the same day is `vYYYY.MM.DD.2` —
`production.ps1` sorts tags as versions. The developer's session is the `dev`
skill (`.claude/skills/dev/SKILL.md`), which the architect maintains. The
automatic handover between the two sessions is in `CLAUDE.md`.

**When to review** — any of:

- a backlog item or stage is finished;
- three or more code commits since the last review;
- any change in **concurrency** (threads, shared native objects), **network
  exposure**, **the user's files** (moving, deleting) or **credentials** —
  even one commit;
- before leaving the system running alone for days.

**The architect reviews the range since the last review** — the whole diff,
not the summary — and checks what the documentation claims against the code
and the real system (logs, files, measurements). It fixes on the spot what is
text or wrong documentation, and code only to fix what the review finds,
reproduced by a test first. What is left in code becomes a **recommendation**
(13.4) for the developer. It writes the review's own section in `HISTORY.md`
13 and its row in 13.2 there.

**The developer reads the open recommendations** before starting (12.3). When
it implements one, it says so in `HANDOFF.md` with the commit; the architect
marks it done and moves its text to `HISTORY.md` 13.4. If it disagrees with
one, it does not ignore it: it writes why, and the user decides.

### 13.2 Review log

The table of every review is `HISTORY.md` 13.2. **The last review, 15, covers
up to the `v2026.10.12` release commit**; the next starts from the commit
after it.

### 13.3 Each review in full

`HISTORY.md` 13.3 to 13.15, one section per review; the next one is 13.16.

### 13.4 Recommendations, open

The closed ones, with their commits and texts: `HISTORY.md` 13.4.

| # | Priority | Recommendation | State |
|---|---|---|---|
| R42 | medium — **the user's decision** | In Home, a resident's face plus a second person who never shows a face sends nothing | open |
| R30 | **high** | A face seen from the side is dropped, so many person events end without a face photo | (a) done `9fb8862`; (b) needs a **second named person** to test that the right one still wins (HISTORY 13.12) |
| R43 | low | `config.json` is rewritten in place with no lock, and now has two writers | open |
| R12 | medium | Production and test copy on the same M900 double the CPU load | open (HISTORY 13.5) |
| R7 | low | `instalar.bat` does not check that the Python is signed | partly: `production.ps1` checks it (HISTORY 13.4) |
| R14 | low | Live MJPEG is encoded once per viewer | open (HISTORY 13.5) |
| R9 | verification | `python-preference = "system"` on the development PC | open (HISTORY 13.4) |
| R10 | **high** | Everything except the conversation in English | in progress 12/10 with R33: CONTEXTO and HISTORY in English; README, INSTALACAO, PYTHON and ARQUITETURA next; then the Portuguese **file names** |
| R33 | medium | The documentation grew by appending | in progress 12/10: CONTEXTO cut to this brief, the past in `HISTORY.md` |

**R42 — In Home, a resident's face hides a second person with no face
(medium, the user's decision).** The faceless message goes only when the scan
found no face at all. If the user walks out with someone whose face is never
seen, the scan finds the user's face (silenced in Home) and nothing is sent —
against the user's own rule that a stranger in the dark must reach the phone.
The scan cannot tell one person from two by faces; YOLO can, by counting
person boxes in the same frame. Options: (a) accept the corner; (b) when the
person was held, every face found was silenced, and YOLO saw more people at
once than distinct faces were found, send the best view as
`faceless_person`. (b) costs a counter in `EventRecorder` and, when YOLO
counts a dog as a second person (R18), one extra message. The architect
recommends (b).

**R43 — `config.json` is rewritten in place, with no lock, by two writers
(low).** `settings.update` reads, changes and writes the whole file with
`write_text`, which truncates first. Until 12/10 only the page wrote it; now
the bot does too (`/home`). A read that lands inside another write sees a
truncated file, `_stored()` answers `{}`, and an `update` that started from it
saves the defaults — **the token, the chat, the PIN and the archive path
erased**. It needs two writes within milliseconds of each other, so it is
unlikely, but the loss is silent. Fix: one lock around `update`, and write to
a temporary file then `os.replace` it — on Windows `os.replace` fails while
another thread has the file open, so it needs a short retry. Acceptance: a
test where two threads update different keys many times and both survive.

**R10, what is left — the file names.** The documents and the program's text
are in English. Still Portuguese: the documents' own names (`ARQUITETURA.md`,
`INSTALACAO.md`, `CONTEXTO.md` → `ARCHITECTURE.md`, `INSTALL.md`,
`CONTEXT.md`), the tools (`diagnostico.py`, `refazer_rostos.py`,
`verificar_clipes.py`, `gerar_icone.py`, `gerar_epub.py`, `criar_atalho.ps1`)
and the launchers (`instalar.bat`, `jarvis_vigilancia.bat` — the second may be
what the startup task or the desktop shortcut calls, so a rename keeps the old
name working for one release). A developer item: every reference — `CLAUDE.md`,
the `dev` skill, docstrings, `gerar_epub.py`'s order, the shortcut and the
scheduled task — changes in the same commit, checked by script.

---

## 14. Sessions and token budget

### 14.1 Why — decided by the user on 09/10/2026

The plan is **Claude Pro**: a limit that resets every **5 hours**, and a
weekly one. The user wants to learn how many developer and architect sessions
fit in one 5-hour window, so each session can be scoped to use it well
instead of stopping halfway. A row is a measurement, never a guess.

### 14.2 How to measure

At the start and the end of every session, read the plan usage with the
desktop app's `get_usage` (5-hour %, weekly %, reset) and the conversation's
context size. A session is one role's stint, even when two happen in one
conversation. The architect fills its row here; the developer writes its
numbers in `HANDOFF.md`, and the architect copies them here.

What drives the cost: every turn re-sends the whole conversation, so a long
conversation makes every later step expensive (~50k of context are tool
definitions alone). **Start each session in a new conversation** — the resume
routine reads what it needs from disk, which is why the roles hand over
through files. Measured so far: a developer delivery costs 10–20 points of the
5-hour window and about 2 of the week; a review with its release and deploy,
5–10 and about 1.

### 14.3 Log

Rows before 12/10 11:00: `HISTORY.md` 14.3.

| # | Role | Effort | Date | Scope | 5-hour window | Weekly | Context |
|---|---|---|---|---|---|---|---|
| A18 | architect | ultracode | 12/10 10:50–11:00 | the notification cases counted from production's log, backlog 25 designed with the user, cycle started | 3% → 6% (new window) | 90% → 90% | 182k → 210k tokens, review 14's conversation |
| D13 | developer | high | 12/10 10:58–11:17 | session 13: backlog 25 (a)–(f), R41 (158 tests) | 6% → 23%: (a)–(d) 9, (e) 3, (f) 2, R41 3 | 90% → 92% | 73k → 252k tokens, a new conversation |
| A19 | architect | ultracode | 12/10 11:17–11:30 | review 15, one code fix, docs, script 12, release and deploy `v2026.10.12` | 25% → 34% | 93% → 94% | 108k → 215k tokens, a new conversation |

### 14.4 Next sessions

**The cycle of 12/10 is done** (review 15, `v2026.10.12`, deployed at 11:27:
407 events, 40 face and 177 dog sightings, 2 reports read before and after;
cameras ok 3 s after the start; no `Telegram commands:` trouble logged). As
the user set it: no hand back. Weekly usage 94 % after review 15, with the
reset on 14/10 at 16:00; above 90 % the cycle stops anyway.

**Waiting for the user:**

- **Backlog 25's acceptance on the M900** (section 8). Until then production
  behaves as before: Away, people only.
- **R42**: accept the corner, or count people with YOLO (recommended).

**Next developer session, when the weekly allows:** R43 (low); R42 if the
user picks (b); R10's file names. R30 (b) still waits for a second named
person.

**Waiting for the user, not planned:** every other open backlog item is
**(proposto)** — 1 (zones), 2 (system health) and the rest of section 8.

---

## 15. Raid log — the comic script of each release

**The user's idea, 10/10/2026, revised the same night.** Every release gets an
issue of a comic: the architect and the developer talking through what really
happened in that version, simplified. **The architect writes the script, not
the drawing**; the user draws it later with a tool made for comics. A first
issue was drawn here as SVG and printed to PDF, and the user replaced it with
scripts after seeing what a drawn issue costs in tokens.

Two files, and only two: `docs/raidlog/script.en.md` and
`docs/raidlog/script.pt.md`, the same story panel for panel — the one
document kept in both languages. Each opens with the series bible (cast,
style, the truth rule: simplified, never invented); a new issue is appended to
both when the architect tags a release, from that version's `HANDOFF.md`,
review and commits.

| Issue | Version | Title | Script |
|---|---|---|---|
| 1 | `v2026.10.09` | The First Night Shift / O Primeiro Turno da Noite | written |
| 2 | `v2026.10.10` | The Dog Who Wore a Person's Face / O Cachorro com Cara de Gente | written |
| 3 | `v2026.10.10.2` | The Watcher's Instruments / Os Instrumentos do Vigia | written |
| 4 | `v2026.10.10.3` | The House Gets a Front Desk / A Casa Ganha uma Recepção | written |
| 5 | `v2026.10.10.4` | The Lock and the Album / A Tranca e o Álbum | written |
| 6 | `v2026.10.10.5` | The Safety Net / A Rede de Proteção | written |
| 7 | `v2026.10.10.6` | The Favourite / A Favorita | written |
| 8 | `v2026.10.10.7` | Mirana and Aurora / Mirana e Aurora | written |
| 9 | `v2026.10.11`, `.2` and `.3` | The Front Desk Learns Manners / A Recepção Aprende Modos | written |
| 10 | `v2026.10.11.4` | The Evidence Box / A Caixa de Provas | written |
| 11 | `v2026.10.11.5` and `.6` | Second Chances / Segunda Chance | written |
| 12 | `v2026.10.12` | The House Learns Who Lives Here / A Casa Aprende Quem Mora Aqui | written |
