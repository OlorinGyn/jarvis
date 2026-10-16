# J.A.R.V.I.S. — project context

This file lets a new Claude Code session continue the work without losing
what was decided, tested and ruled out about the project. **Read it, with
`PROCESS.md` and `BACKLOG.md`, before touching anything.** The past lives in
`HISTORY.md`, read on demand.

| Document | For |
|---|---|
| `ARCHITECTURE.md` | How the system works and why, layer by layer |
| `INSTALL.md` | Installing and running on a new machine, troubleshooting |
| `PYTHON.md` | Python and the libraries, for someone coming from Java and C# |
| `PROCESS.md` | How the work is done: the user's rules, the resume routine, reviews, the token budget, biases, the raid log |
| `BACKLOG.md` | The work: the backlog, the open recommendations, the next sessions |
| `PENDING.md` | What is not work yet: what waits for the user, open discussions, decisions not yet carried out — the architect's |
| `HISTORY.md` | Bugs already fixed, old measurements, every review in full, closed recommendations, the usage log |
| **this file** | The project: what it is, decisions, limitations, the repository map, commands |

Section numbers here are stable on purpose: the code points at them. A
section whose content moved elsewhere keeps its number with a pointer.

---

## 1. The project

Home surveillance with two outdoor TP-Link **Tapo C310** cameras over RTSP.
The system detects motion, decides whether it is a person or an animal,
records the event without re-encoding, recognises faces and the household's
dogs, and sends what matters to the user's phone through Telegram. The only
interface is a web page served by the service itself: **Live**,
**Recordings**, **People**, **Dogs** and **Settings** (Notifications first).

**Two machines:**

| | Development | Production |
|---|---|---|
| Machine | Ryzen 9 7950X, 64 GB, RTX 4080 | Lenovo M900, i5 Skylake 4 cores, 16 GB |
| Path | `D:\Personal Projects\J.A.R.V.I.S\jarvis` | `C:\Personal Projects\jarvis` (this folder: the test copy) |

**Production runs on the M900 since 09/10/2026**, from `C:\JARVIS`, a clone
checked out at a **release tag**, started with Windows by a scheduled task
and changed only by `tools/production.ps1` (ARCHITECTURE 18.7). Every release
is deployed the same way — every file read before and after with the new
code, rolled back on its own if anything fails; the current one is the last
row of `HISTORY.md` 13.2 and `PROCESS.md` 3.2. The folder above is the test
copy, on `stream2` and port 8766, with no Telegram token (INSTALL 9).

**The RTX 4080 is deliberately ignored.** Nothing here is trained, and
developing on the same CPU path the M900 uses avoids divergence between the
machines.

## 2. How the user works — moved to `PROCESS.md` 1 (12/10/2026)

## 3. Decisions taken — do not undo without a new reason

**Python, not C++.** OpenCV's Python bindings call the same compiled C++, with
microseconds of overhead per call. The real time is in decoding and inference,
both native. The vision ecosystem is Python-first.

**ffmpeg, not `cv2.VideoCapture`.** `VideoCapture` hands out decoded frames,
which forces **re-encoding** to save. Measured: the old pipeline made files
**25 % larger than the camera's original, with three generations of loss**.
One ffmpeg process per camera serves two outputs — `-c copy` segments (a byte
copy) and 960×540 frames for analysis (ARCHITECTURE 5.1, 5.2).

**No PyTorch.** Windows 11's **Smart App Control** blocks binaries without a
recognised signature, and PyTorch's DLLs are unsigned (`WinError 4551`).
Turning it off is **irreversible** without reinstalling Windows. YOLO runs
through `cv2.dnn` on the official `yolo11s.onnx`, which also removed ~2.5 GB of
dependencies. Measured 09/10/2026 on the same blob, CPU against CPU:
`cv2.dnn` 37.8 ms, `onnxruntime` 34.6 ms, identical output — another ONNX
runtime would buy nothing; the real loss was GPU to CPU, which the M900 cannot
undo (ARCHITECTURE 7.11). The low dependency count that followed is **not a
merit of the project** (`PROCESS.md` 5). On 14/10/2026 PyTorch 2.14 CPU
imported under Smart App Control on the M900, in a throwaway environment used
once to export two face models to ONNX (ARCHITECTURE 10.14). The program
still does not need it: `cv2.dnn` ran every model measured.

**The official signed Python, not the one `uv` downloads.** Smart App Control
lets an unsigned Python run only while Microsoft's cloud gives it a good
reputation — a verdict that changes on its own. On 09/10/2026 it blocked the
very interpreter that had run on 29–30/09, with nothing changed on disk. The
python.org build is signed by the PSF and always passes; `pyproject.toml`
says `python-preference = "system"`, and the `.bat` files call
`uv run python -m jarvis` instead of the unsigned `jarvis.exe`. The rule: **on
the M900 every executable in the path must be signed** — reputation is no
guarantee. The same reason makes the tests run as `python -m pytest`
(ARCHITECTURE 19.5, INSTALL 1.2).

**A web interface with FastAPI.** `http.server` was considered and dropped: it
is single-threaded, so live MJPEG would block everything, and it has no HTTP
Range, which `<video>` needs to seek. `pydantic_core` (compiled Rust) loads
under Smart App Control on both machines (HISTORY 12.2). The web is the only
way in, by the user's decision (ARCHITECTURE 17).

**No compressing the videos.** Built and removed. Measured on a real file: zip
saves **0.2 %**, bzip2 and lzma make the file **bigger**. H.264 is already
entropy-coded (ARCHITECTURE 8.7).

**One RTSP connection per camera.** The Tapo accepts one session on `stream1`;
a second gets `406 Not Acceptable`. That is why one ffmpeg makes both outputs.

**Faces in the clip, not live.** A 60 px face in 1080p becomes 30 px in the
960×540 analysis frames, and the recogniser wants ~112 px. `scan_clip()` runs
on the assembled clip at full resolution, off the critical path. This is also
why a person's name is known only seconds after the event (ARCHITECTURE 22.3).

**YuNet and SFace, not InsightFace — reopened by the user, 14/10/2026.**
Chosen because both are built into OpenCV, no new dependency, and measured
then at similarity **1.000** for the same face and **0.045** for different
faces, with a 0.363 threshold — on good frontal faces. R49 showed what that
measurement could not: YuNet takes the top or the back of a head for a face,
and those views drew wrong "sure" matches. **The user's decision:** if much
better models exist, they will be used, even though new models mean new
embeddings for every gallery — with a migration, as for any change that is
not additive. "No new dependency" was PROCESS 5's bias, not a reason.
**Measured and decided, 14/10/2026** (ARCHITECTURE 10.14). InsightFace's
SCRFD detector and ArcFace recogniser beat every other candidate on this
house's photos. The user's answer was "if it is the best, we use it". That
accepts InsightFace's licence for its models, "for non-commercial research
purposes only", for a private home system. **Switched, 14/10/2026
(`v2026.10.14`):** YuNet still finds the faces; SCRFD places the points and
ArcFace R50 from `buffalo_l` recognises. R100 from `antelopev2` was measured
and is not better here — it needs a higher threshold before nothing is wrong,
and is twice as slow (ARCHITECTURE 10.14). The gallery moved to a new file so
a rollback still reads the old one (ARCHITECTURE 19.1).

**An unknown person always reaches the phone in Home** (the user,
14/10/2026). A face not known, or a person YOLO saw beside known faces whose
own face never showed, is notified even when a resident is in the scene:
"if it errs, it errs" — one extra message is better than someone hiding
beside the user going unannounced (R42 (b), built in `v2026.10.14.3`:
YOLO's count of people at once against the faces found, ARCHITECTURE 22.3).
**Reconfirmed by the user, 16/10/2026,** after "many notifications in Home":
31 messages in 23 hours, none a stranger — the residents with no face seen
(the backyard at night, the back of a head), the household's dogs taken for
people, and two false "2 people" (ARCHITECTURE 22.3). Shown the example of
four messages in eleven minutes for one walk in the backyard, and offered
one message per camera per 15 minutes, no faceless message in Home, or the
front camera only, the user chose **every faceless person still reaches the
phone in Home**; only the false ones go (R58, R59).

**Notifying is a weighing: risk never lost, nobody shouted at** (the user,
16/10/2026). An event that may mean risk must never be lost, and a message
every ten seconds is unbearable: **more than one notification in 30 s means
something is wrong.** A subject seen in a new place — at the Front, then at
the Back — deserves a new message; the same subject in the same place does
not. The user left to the architect which situations count as risk, looking
at the competitors; the design is in `PENDING.md`, "Decided, not yet done".

**Nothing about this house's dogs in the code** (the user, 10/10/2026). Each
household teaches the system its own dogs on the Dogs tab (ARCHITECTURE 20).

**Dogs are told apart by DINOv2-small, not by colour** (R53, the user's
report of 14/10; the architect's choice in review 25, built in
`v2026.10.15`). The colour histograms put Mirana among Aurora's views and a
person among Mirana's. DINOv2-small, a network trained without labels to
tell images apart, named every view of the bench right by day and at night
and no person crop; MobileNetV3 tied it and was not chosen because it is
trained to put every dog of a breed into one class — the opposite of what
two dogs of one breed need. Apache-2.0 weights; ~120 ms a dog on the M900.
The gallery moved to a new file so a rollback still reads the old one
(ARCHITECTURE 20).

## 4. Bugs found and fixed — do not reintroduce

Moved to `HISTORY.md` 4: each bug with its cause and fix. Read it before
changing capture, motion, the face scan, notifications or production.

## 5. Reference measurements

Moved to `HISTORY.md` 5. Measurements behind a current rule stay beside the
rule in `ARCHITECTURE.md`.

## 6. Solved: the M900 got no frames (29/09/2026)

Moved to `HISTORY.md` 6. The lesson that still applies: on a new machine,
test the camera IP in `.env` first (INSTALL 8).

## 7. Known and accepted limitations

- **Face recognition at night is unreliable.** Infrared gives ~44 px faces:
  finding a face works, telling whose it is does not. **The biggest possible
  gain is not software: a motion-triggered light** takes the camera out of
  infrared (backlog 16).
- **Only the household's dogs are named**, and only when the user has named
  enough views; two dogs that look alike stay "dog", the honest answer. Other
  animals are only labels (`cat`, `bird`…), and YOLO's hesitation between
  species accumulates in `labels` (ARCHITECTURE 7.1).
- **A person standing still for ~12 s is suppressed** by the static-scene
  suppression until they move again.
- **No archive configured in production.** Recordings grow ~300 MB/day in
  `clips/`; the archive (ARCHITECTURE 11) moves them to an external drive after
  30 days only when `archive_path` is set, and production's is empty. The
  rolling buffer in `clips/_buffer/` cleans itself.
- **No undo of a merge** on People or Dogs (closed by the user, backlog 9): a
  warning comes before every merge.

## 8. Backlog — moved to `BACKLOG.md` 1 (12/10/2026)

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
  faces.py        layer 4: YuNet, SCRFD + ArcFace, the gallery and its migration, naming
  downloads.py    the face and dog models' files, fetched once, the dogs' pinned by SHA-256; standard library only (production.ps1 runs it)
  dogs.py         the dog gallery: crops, the DINOv2-small descriptor, matching, its migration
  archive.py      layer 5: moves to the external drive, deletes only there when full
  settings.py     settings editable from the page (config.json)
  notify.py       Telegram messages: thumbnail, face, cooldowns, the cases
  modes.py        notification cases, the Home/Away/Silent modes and their switches
  bot.py          commands from the phone: long polling, switches the mode and On/Off only
  analysis.py     analysis On or Off, in memory only: /on and /off (ARCHITECTURE 22.7)
  reports.py      bad-detection reports and their Undo
  devices.py      paired devices for the write guard
  log.py          logging: console, crash hooks, logs/jarvis.log for the service
  web.py          the web interface: FastAPI in a thread beside the Core
  static/         the page: index.html, style.css, app.js
  geometry.py     Detection type and box utilities
tests/            pytest: python -m pytest (ARCHITECTURE 19.5); conftest.py swaps the dog network for a stand-in, dog_vectors.py builds descriptors at chosen distances
tools/
  production.ps1  production on the M900: install, update, start, stop, status, check
  check_data.py   reads every file on disk with the current code (ARCHITECTURE 19)
  replay.py       why each frame of a video was kept or dropped (ARCHITECTURE 12.10)
  face_tuning.py, dog_tuning.py, dog_crops.py   measure thresholds; crop past dog events
  face_bench.py   candidate face pipelines on a copy of faces/ (R49; models in models/bench)
  dog_bench.py    dog descriptors against learned embeddings on a copy of dogs/ (R53; models in models/bench/dogs)
  diagnose.py     capture diagnosis (variants, and --local without a camera)
  probe_rtsp.py   raw RTSP diagnosis (DESCRIBE → SETUP → PLAY)
  rebuild_faces.py rebuilds faces/ from the recorded clips
  settle_waiting.py once: the Waiting queues older versions left, through the 40-view rule
  check_clips.py  counts damaged blocks per camera on one day
  make_epub.py, epub.css   every .md into one EPUB for an e-reader
  check_doc_refs.py  every "<DOC> <section>" reference lands on a heading
  make_icon.py, create_shortcut.ps1   the icon and the desktop shortcut
  check_python.ps1  is this python.exe the signed python.org build? (install.bat, production.ps1)
assets/           jarvis.ico and a PNG preview (generated, but versioned)
docs/             ARCHITECTURE, INSTALL, PYTHON; this file, PROCESS, BACKLOG, PENDING, HISTORY
docs/raidlog/     the comic script of each release, English and Portuguese (PROCESS 6)
CLAUDE.md         instructions for Claude Code (roles, language, rules)
.claude/skills/dev/SKILL.md  the developer's session: /dev or "Dev, ..."
HANDOFF.md        developer → architect notes; empty between deliveries
install.bat       install on a new machine
jarvis.bat        start the service and open the browser
jarvis_headless.bat service only, no browser (--headless)
```

Structure explained in ARCHITECTURE 3. Not versioned: `.env` (credentials),
`config.json` (Telegram token, PIN), `models/` (~340 MB, downloaded on
demand), `clips/`, `faces/`, `dogs/`, `reports/`, `devices.json`, `backups/`
(copies the tools make before touching data), `logs/` and `HOLD`.

**Outside the repository:** `C:\JARVIS` on the M900 is production — a clone
of the same GitHub repository at a release tag, with its own `.env`,
`config.json` and data. Never edit it by hand; `tools/production.ps1` is the
only thing that changes it (ARCHITECTURE 18.7).

## 10. Useful commands

Production, on the M900 (prefix every line with
`powershell -ExecutionPolicy Bypass -File`):

```bat
tools\production.ps1 -Action status      version, task, port, age of each camera's last frame
tools\production.ps1 -Action update      to the latest release tag; rolls back on its own if it fails;
                                         refuses while the cameras deliver no frames (-Force overrides)
tools\production.ps1 -Action stop        stays stopped, even after a reboot, until start
tools\production.ps1 -Action start       releases the hold and starts
tools\production.ps1 -Action check       tools/check_data.py against production's data
C:\JARVIS\logs\jarvis.log                what production did
http://127.0.0.1:8765                    production's page (another computer: the M900's DHCP address, which moves — .18, .19 for some hours on 15/10, .18 again at 16:40)
```

Test copy and tools, from this folder:

```bat
jarvis.bat                                              test copy: service + browser (port 8766 here)
uv run python -m jarvis --headless                      service only, no browser
uv run python -m jarvis --stop                          stop the copy running from this folder, cleanly
uv run python tools/check_data.py                       can the current code read every file on disk?
uv run python -m pytest                                 the automatic tests (not `uv run pytest`: ARCHITECTURE 19.5)
uv run python tools/replay.py <video> [--prime]         why each frame was kept or dropped
uv run python tools/diagnose.py Front                   test capture variants
uv run python tools/diagnose.py --local                 test ffmpeg without a camera
uv run python tools/probe_rtsp.py <ip> <user> <pw> stream1   raw RTSP
powershell Test-NetConnection <ip> -Port 554            does the camera answer on that IP?
uv run python tools/rebuild_faces.py                    rebuild faces/ (stop the program first)
uv run python tools/settle_waiting.py [--dry-run]       once: old Waiting queues through the 40-view rule (stop the program first; R48)
uv run python tools/check_clips.py [YYYY-MM-DD]         image damage coming from the cameras
uv run python tools/face_bench.py [--pipelines ...]     face models compared on a copy of faces/ (ARCHITECTURE 10.14)
uv run python tools/dog_bench.py [--candidates ...]     dog descriptors compared on a copy of dogs/ (ARCHITECTURE 20)
uv run python tools/make_epub.py                        the documentation as an EPUB
uv run python tools/check_doc_refs.py                   every "<DOC> <section>" reference lands on a heading
tasklist | findstr ffmpeg                               look for an orphaned ffmpeg
```

**The documentation EPUB.** `tools/make_epub.py` joins **only
`docs/ARCHITECTURE.md` and `docs/PYTHON.md`** — the user's choice, 14/10/2026:
how the program works and what it teaches; the process, the backlog, the
history and what Claude exchanges stay out — into one EPUB,
`docs/epub/JARVIS - Documentation.epub`, one chapter per document, so the
cross-references stay a tap away on the reader. `ORDER` is the list of what
goes in: a new document joins only when the user asks. The `.md` files are never changed, EPUBs are not versioned, and the
script checks at the end that the count of tables and code blocks matches the
sources, including tables nested in list items. It needs pandoc
(`winget install --id JohnMacFarlane.Pandoc -e`, found even off the PATH;
installed on the M900, 3.12.1). `tools/epub.css` keeps it readable on 7
inches: code at 0.68em with forced wrapping. **The architect's job, only when
the user asks** ("gere o epub", decided 10/10/2026): only the user reads it.

Tuning constants: `capture.py` (`ANALYSIS_FPS`, `HWACCEL`, `SEGMENT_SECONDS`,
`SOCKET_TIMEOUT_SECONDS`), `people.py` (`MIN_INTERVAL`,
`MIN_PERSON_HEIGHT_FRACTION`, `SAME_PERSON_IOU`, `REPLACED_PERSON_IOU`,
`SETTINGS_REFRESH_SECONDS`; `CONFIDENCE` and `ANIMAL_CONFIDENCE` are only the
defaults since backlog 31 — the live minimums are in Settings → Detection,
ARCHITECTURE 7.14), `motion.py` (`MIN_AREA`,
`CONFIRM_FRAMES`, `LIGHTING_CORRELATION`), `faces.py` (`MATCH_THRESHOLD`,
`LEARN_THRESHOLD` — since backlog 32 only the default of the user's sure
threshold, ARCHITECTURE 10.15 — `SURE_SWEEP`, `COPY_SIMILARITY`, `SAME_FACE_THRESHOLD`, `IDENTITY_SCORE`, `MAX_NOSE_OFFSET`,
`MIN_EYE_SPREAD`, `MIN_VIEWS_FOR_NEW`, `LANDMARK_SIZE`, `LANDMARK_SCORE`;
`TINY_SIDE`, `SAME_PICTURE`, `WRITTEN_TOGETHER_SECONDS`: recovering each
view's event, ARCHITECTURE 10.16),
`dogs.py` (`SURE_DISTANCE` — since backlog 32 only the default of the
user's sure distance — `SURE_RATIO`, `PROBABLE_DISTANCE`, `PROBABLE_RATIO`,
`SURE_SWEEP`, `COPY_DISTANCE`, `MARGIN`, `CROP_SIDE`, `MAX_UNNAMED`,
`DECIMALS`; ARCHITECTURE 20),
`settings.py` (`CONFIDENCE_RANGE`, `SLIDER_STEPS`: the detection sliders,
ARCHITECTURE 7.14; `FACE_SURE_RANGE`, 10.15; `DOG_SURE_RANGE`, 20), `app.js` (`PAGE_STEP`, 17.17), `notify.py` (`MAX_FACES`), `bot.py` (`LONG_POLL_SECONDS`,
`STALE_SECONDS`, `REMINDER_SECONDS`).

---

## 11. Claude's biases — moved to `PROCESS.md` 5 (12/10/2026)

## 12. Resume routine — moved to `PROCESS.md` 2 (12/10/2026)

## 13. Architecture review — moved (12/10/2026)

How a review works: `PROCESS.md` 3. The open recommendations (13.4): `BACKLOG.md` 2. Every review in full and the closed recommendations: `HISTORY.md` 13.

## 14. Sessions and token budget — moved (12/10/2026)

Why and how to measure (14.1, 14.2): `PROCESS.md` 4. The log (14.3): `HISTORY.md` 14.3. The next sessions (14.4): `BACKLOG.md` 3.

## 15. Raid log — moved to `PROCESS.md` 6 (12/10/2026)

