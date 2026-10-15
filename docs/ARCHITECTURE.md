# J.A.R.V.I.S. — Architecture

How the system works and, above all, **why** each decision was taken. The
code has no comments; all the reasoning is here. For the language and the
libraries, see [PYTHON.md](PYTHON.md).

**Where each subject is.** The sections follow the pipeline, then the
interface, production and data:

| Subject | Sections |
|---|---|
| Capture, motion, YOLO, recording | 5, 6, 7, 8 |
| Faces: scan, gallery, recognition, side view | 10 |
| Dogs: crops, descriptor, matching | 20 |
| Archive to an external drive | 11 |
| Telegram notifications | 12 |
| Residents, the Home/Away/Silent modes, commands from the phone | 22 |
| The core without a window | 15 |
| The web page: routes, tabs, pairing, video, the gallery pages | 17 |
| Bad-detection reports | 21 |
| Production and test copies on the M900 | 18 |
| Files on disk, `check_data`, the tests | 19 |

---

## 1. What the system does

It watches Tapo cameras on the local network, notices **motion**, decides
whether that motion is a **person or an animal**, records a **video** of the
event and, when there is a person, looks for **faces** and says whose they
are; dogs are named the same way. What reaches the phone depends on the active
mode (section 22).

Person detection is deliberately independent of the face: someone in a mask,
a helmet or with their back turned is still detected as a human and recorded.
The face is one more layer, run afterwards, on the clip (section 10).

## 2. Pipeline

```
     RTSP (network)
         │
         ▼
   ┌────────────┐
   │ capture.py │  one ffmpeg per camera, two outputs
   └──┬──────┬──┘
      │      └── -c copy ──► 4 s segments (the original packets)
      │                                    │
      │ 960x540 frames (bgr24 over a pipe) │
      ▼                                    │
   ┌───────────┐                           │
   │ motion.py │  MOG2 + confirmation      │
   └─────┬─────┘                           │
         │ motion boxes                    │
         ▼                                 │
   ┌───────────┐                           │
   │ people.py │  YOLO11: person/animal    │
   └─────┬─────┘                           │
         │ Detection(x,y,w,h,conf,label)   │
         ▼                                 ▼
   ┌───────────────────────────────────────────────┐
   │ clips.py   concat -c copy + thumbnail + JSON  │──► notify.py (first message)
   └────────────┬──────────────────┬───────────────┘
                │ 1080p clip       │ metadata
                ▼                  │
         ┌───────────┐             │
         │ faces.py  │  YuNet +    │──► notify.py (faces, side or best view)
         │ dogs.py   │  ArcFace;   │
         └─────┬─────┘  DINOv2     │
               │ galleries         │
               ▼                   ▼
         ┌─────────────────────────────────┐
         │  web.py   the page, six tabs    │
         └─────────────────────────────────┘
```

The saved video **never passes through Python**: it goes from the camera's
packets straight to disk. Python only sees small frames, to decide when to
record.

The central logic is a **cost funnel**: each layer is more expensive than the
one before and runs only if the one before found something.

| Layer | Cost | Frequency |
|---|---|---|
| Capture + decode | low | every frame |
| MOG2 + lighting filter | ~3 ms | every frame |
| YOLO11 | 50–62 ms (dev) | only with motion, at most 4×/s per camera |
| Recording | ~2 ms | only with a person or an animal |
| Dog naming (DINOv2-small) | ~120 ms per dog (M900) | once per dog event, in the live loop (section 20) |
| Faces | 9–17 s per clip (M900) | only on clips with a person, off the live loop |

## 3. File layout

```
jarvis/
├── src/jarvis/           the program, as a Python package
│   ├── __init__.py       ROOT: the project root, the base of every path
│   ├── __main__.py       allows `python -m jarvis`
│   ├── cameras.py        the Core (surveillance) + run_headless (section 15)
│   ├── capture.py        one ffmpeg per camera: original segments + frames
│   ├── motion.py         layer 1: motion detection
│   ├── people.py         layer 2: people and animals
│   ├── clips.py          layer 3: events, lossless assembly, metadata
│   ├── faces.py          layer 4: face detection, embedding, gallery
│   ├── dogs.py           the dog gallery and matching (section 20)
│   ├── archive.py        layer 5: moves to the external drive (section 11)
│   ├── notify.py         Telegram messages (section 12)
│   ├── modes.py          the notification cases and modes (section 22)
│   ├── bot.py            commands from the phone (22.5)
│   ├── analysis.py       analysis On or Off, the bot's /on and /off (22.7)
│   ├── reports.py        bad-detection reports (section 21)
│   ├── devices.py        paired devices for the write guard (17.12)
│   ├── settings.py       config.json, settings that change while running
│   ├── web.py            the web interface: a FastAPI server (section 17)
│   ├── static/           the page: HTML, CSS and JavaScript
│   ├── log.py            logging to the console and logs/jarvis.log (18.7)
│   └── geometry.py       the Detection type and box utilities (IoU)
├── tests/                pytest (19.5)
├── tools/                tools, outside the program
│   ├── production.ps1    install, update, status, stop, start production (18.7)
│   ├── check_data.py     reads every file on disk with the current code (19.4)
│   ├── replay.py         why each frame of a video was kept or dropped (12.10)
│   ├── face_tuning.py, dog_tuning.py   measure the matching thresholds
│   ├── face_bench.py     candidate face pipelines on a copy of faces/ (10.14)
│   ├── dog_crops.py      crops past dog events into the dog gallery (20)
│   ├── diagnose.py       variants of the capture command; --local without a camera
│   ├── probe_rtsp.py     raw RTSP (DESCRIBE → SETUP → PLAY)
│   ├── rebuild_faces.py  rebuilds faces/ from the clips
│   ├── settle_waiting.py once: the old Waiting queues through the 40-view rule (17.14)
│   ├── check_clips.py    image damage coming from the cameras
│   ├── make_epub.py      joins the .md files into an EPUB for an e-reader
│   ├── check_doc_refs.py every "<DOC> <section>" reference lands on a heading
│   ├── make_icon.py      draws the icon (section 14)
│   ├── create_shortcut.ps1 the Desktop shortcut with the icon
│   └── check_python.ps1  is a python.exe the signed python.org build (18.7, INSTALL 1.2)
├── assets/               jarvis.ico and a PNG preview (generated, versioned)
├── docs/
│   ├── ARCHITECTURE.md   how it works and why
│   ├── INSTALL.md        installing and running on a new machine
│   ├── PYTHON.md         Python and the libraries, for Java/C# developers
│   ├── CONTEXT.md        the project: decisions, limits, repository map, commands
│   ├── PROCESS.md        how the work is done: rules, resume, reviews, budget
│   ├── BACKLOG.md        the work: backlog, open recommendations, next sessions
│   ├── PENDING.md        what is not work yet: waiting for the user, open discussions
│   ├── HISTORY.md        bugs fixed, every review, closed recommendations
│   └── raidlog/          the comic script of each release
├── install.bat           install on a new machine (run once)
├── jarvis.bat            the service and the browser (the Desktop shortcut points here)
├── jarvis_headless.bat   the service only: records, notifies and serves the page
├── CLAUDE.md             working rules, read by every Claude Code session
├── HANDOFF.md            developer to architect, emptied after each review
├── README.md             introduction and links to docs/
├── .env.example          configuration template, versioned
│
│   ── from here down, nothing is versioned ──
├── .env                  the cameras' IPs and credentials
├── config.json           settings, the Telegram token, the PIN (each machine its own)
├── devices.json          paired devices (17.12)
├── models/               ONNX of YOLO, the face models and DINOv2-small (~340 MB, downloaded; 10.2)
├── clips/                recordings
│   ├── _buffer/          rolling segments per camera, deleted on their own
│   └── Front/2026-09-26/19-17-30.{mp4,jpg,json}
├── faces/                faces and the gallery
│   ├── gallery_arcface_w600k_r50.json   known and unknown people (10.14)
│   ├── gallery.json      the same under SFace, kept for a rollback
│   ├── views/            one crop per stored view
│   └── 2026-09-28/21-42-00_a1b2c3.{jpg,json}
├── dogs/                 the same for dogs (section 20)
├── reports/              bad-detection reports (section 21)
├── backups/              copies the tools make before touching data
├── logs/                 jarvis.log and its rotations (19.2)
└── HOLD                  only while production is held (18.7)
```

Production is a second clone, `C:\JARVIS`, with this same layout (18.7).

The root holds only what the user opens or edits (the `.bat` files, `.env`),
the entrance to the documentation (`README.md`, `CLAUDE.md`) and what the
tools require there (`pyproject.toml`, `uv.lock`, `.python-version`,
`.gitignore`).

Data generated by the program lives in its own folders, never loose at the
root. That is why `tools/rebuild_faces.py` keeps the old `faces/` in
`backups/faces_<date-time>/`, and `tools/diagnose.py` writes its test
segments to a temporary system folder that disappears when it finishes.

### 3.1 The project is an installable package

`pyproject.toml` declares a `[build-system]` with `uv_build` and a command:

```toml
[project.scripts]
jarvis = "jarvis.cameras:main"
```

`uv sync` installs the package in **editable mode**: `.venv` points at
`src/jarvis/` instead of copying the files, so editing the code takes effect
at once, without reinstalling. The program is started as
`uv run python -m jarvis`, which runs the same `main()` through the signed
Python; the `jarvis.exe` that `uv` generates for the command above is
unsigned and blocked on the M900 (INSTALL 1.2).

The modules import each other by the package name (`from jarvis.capture
import FFmpegCamera`), like a `namespace` in C# or a `package` in Java. See
PYTHON.md.

**This reversed an old decision, for a reason.** Until September 2026 there
was `package = false`, because the backend `uv init` picked **rebuilt and
reinstalled `jarvis` on every `uv run`**. With `uv_build` that no longer
happens: measured on the M900, the second `uv run` says `Requirement already
installed` and builds nothing. With the modules loose at the root, each script
depended on being run from the right folder, and the root piled up files of
different kinds — code, tools, history.

`link-mode = "copy"` solves the other old symptom: on the development PC the
`uv` cache is on C: and the project on D:, and a hardlink does not cross
volumes.

### 3.2 Paths start from the root, not the current folder

`jarvis/__init__.py` defines `ROOT = Path(__file__).resolve().parents[2]`: the
file is in `src/jarvis/`, two levels below the root. `models/`, `clips/`,
`faces/` and `.env` are always `ROOT / ...`.

They used to be relative (`Path("clips")`), which means "relative to the
folder the command was run from". Running from another folder created a new
`clips/` in the wrong place or did not find `.env`.

The paths **stored** in the face JSON files stay relative to the root
(`faces\2026-09-28\...`), so the project folder can move.

## 4. Configuration — `.env`

One camera = three lines. The label becomes the displayed name and the clips'
folder.

```
CAM_FRONT_IP=192.168.0.116
CAM_FRONT_USER=<camera-account-user>
CAM_FRONT_PASSWORD=<camera-account-password>
```

`build_camera_list()` scans the keys for the pattern `CAM_<X>_IP` and builds
the RTSP URL. Adding a third camera needs no code change. `CAM_STREAM` and
`WEB_PORT` are optional (18.7): the test copy uses `stream2` and port 8766.

`.env.example` holds `ip-da-camera` instead of an IP, and
`build_camera_list()` stops the program with an instruction if it finds that
text. The template used to hold real-looking IPs (`.10`, `.11`); on the M900
they stayed in `.env` without anyone noticing, and the symptom was a "no frame
received" with no error (5.7). Without the check, the sample text would only
give `I/O error`.

The password goes through `urllib.parse.quote()` because characters such as
`@ : / #` are structural in a URL and would break the parsing.

---

## 5. The capture layer — `capture.py`

### 5.1 Why ffmpeg and not OpenCV

This layer was rewritten on 26/09/2026. The previous version used
`cv2.VideoCapture`, which forced re-encoding the video to save it — OpenCV
hands out decoded frames, never the original packets.

The measurement behind the switch, 10 s of the Back camera:

| What was recorded | Size | Quality |
|---|---|---|
| **The camera's original stream** | **579 KB** | **perfect** |
| Old pipeline (mp4v → H.264 CRF 26) | 725 KB | 3 generations of loss |
| Re-encoded at high quality (CRF 18) | 1919 KB | nearly perfect |
| Lossless H.264 | 5089 KB | perfect |

The old file was **25 % larger than the original, at worse quality**. It spent
CPU to make both worse: the camera already delivers H.264 at 463 kbps from a
hardware encoder, and already-compressed material resists compressing again.

**About zip-style compression:** not worth it. On the original stream, which
is what is recorded today, the measured gain is 0.2 % — and two of the three
methods make the file bigger. See 8.7, including why an old measurement said
5–11 %.

### 5.2 One connection, two outputs

The camera accepts **a single RTSP session** (on `stream1`; 18.2). Tested:
with OpenCV connected, a second client gets `406 Not Acceptable` and opens
nothing.

That forces the architecture: one ffmpeg process per camera has to serve both
purposes at once.

```
                    ┌─ -c copy ──────────► 4 s segments on disk
RTSP ──► ffmpeg ────┤                       (original packets, untouched)
                    └─ rawvideo 960x540 ──► pipe:1 ──► Python (analysis)
```

It is the architecture real NVRs use; Frigate does exactly this.

Gains over the previous version:

| | Before | Now |
|---|---|---|
| Quality on disk | 3 generations of loss | identical to the camera |
| Size | 72 KB/s | **48 KB/s** |
| 1080p decoding | in Python | only in ffmpeg, once |
| RAM per camera | ~180 MB (frame buffer) | ~0 |
| Pre-recording | frames in memory | segments already on disk |

The CPU and RAM gains are exactly what the M900 needs.

### 5.3 Analysis frames

`ANALYSIS_WIDTH/HEIGHT = 960x540` and `ANALYSIS_FPS = 10`. ffmpeg resizes and
delivers `bgr24`, which is exactly the layout numpy and OpenCV expect:

```python
frame = np.frombuffer(data, np.uint8).reshape(ANALYSIS_HEIGHT, ANALYSIS_WIDTH, 3)
```

Each frame is `960 * 540 * 3 = 1,555,200` bytes, and the reader asks for
exactly that amount. Measured in practice: ~8 fps, because the loop spends
time between reads.

`np.frombuffer` returns a **read-only** array (it points at the pipe's
bytes), which is why there is a `.copy()` — without it, any drawing on the
frame would fail (PYTHON 20).

**What it means for the face layer:** 960×540 is enough for motion and for
YOLO, but a face that is 60 px in 1080p is 30 px here, too little for the
recogniser. That is why faces are looked for in the **recorded clip**, in
1080p, and not in the analysis frames (10.1).

### 5.4 Reading in a thread: the loop never waits

The first version read the pipe inside the interface loop (then the OpenCV
window's). A pipe's `read()` **blocks** until the whole frame arrives, and at
start-up ffmpeg takes a few seconds to negotiate RTSP and fill its buffer.

Measured: **the first frame takes 2.45 s**. During that time `waitKey` was
not called, and Windows marked the window **"Not Responding"**, showing a grey
rectangle that was never drawn.

Now each camera has a **reader thread** that drains the pipe without stopping
and keeps the newest frame. The loop takes whatever is ready:

```python
def read(self):
    """Return the newest frame not yet analysed, or None. Never blocks."""
    with self._lock:
        frame, self._pending = self._pending, None
    return frame
```

The important detail is `_pending` becoming `None` on reading. Without it the
same frame would be analysed several times, inflating the MOG2 warm-up and the
temporal confirmation count with repeated frames. `_latest` keeps the last
frame separately, for drawing.

Since the GIL is released while reading the pipe, that thread really does run
in parallel — the case described in PYTHON.md 14.1.

Measured after the change, start-up included (with the window, then):

| | |
|---|---|
| Median loop interval | 19.9 ms |
| Worst interval | 88.8 ms |
| The "Not Responding" limit | ~5000 ms |

### 5.5 The rolling segment buffer

Segments are named by time (`-strftime 1`), which makes choosing them
trivial. `covering(start, end)` returns the **whole** segments that intersect
the requested window:

```python
following = found[index + 1][0] if index + 1 < len(found) else datetime.max
if following > start and stamp < end:
```

Since whole segments are kept, the pre-recording comes free: the segment
before the event already holds the person approaching. In exchange the clip
has up to 4 s extra at each end, which is exactly what is wanted.

`prune()` deletes segments older than `BUFFER_SECONDS = 240`, **never the
newest** — ffmpeg is still writing it. While an event is open, `protect_from`
stops its segments from being deleted. Measured on 30/09/2026 on the M900: 6
to 8 MB per camera, about 60 segments.

### 5.6 Hardware decoding

`HWACCEL` adds `-hwaccel <value>` to the ffmpeg command. It is empty, because
the right value depends on the machine.

It matters only for the **analysis output**: recording copies packets and
never decodes. On the M900, with Skylake's Quick Sync, `"dxva2"` or `"qsv"`
takes the 1080p decode off the CPU. See INSTALL.md section 6.

### 5.7 ffmpeg's errors become readable text

The first version sent ffmpeg's `stderr` to `DEVNULL`. The consequence: a
camera that **never connected** looked identical to one that was merely quiet
— the panel said "no signal" and the reason was thrown away.

It showed at deployment: on the M900 both cameras said `ok` at start-up and
then stayed at "no signal" forever, with no clue. The cause was the
development PC running at the same time and holding the sessions.

Three changes:

**`stderr` is captured** by a thread that keeps the last lines. It must be
drained continuously: a full error pipe would block ffmpeg.

**The start-up `ok` became honest.** It used to check `process.poll()` right
after `Popen`, which is always true — the process has not had time to fail.
Now `wait_ready()` waits for a real **first frame**, up to `STARTUP_SECONDS`,
and returns the reason when none comes.

**The messages are translated.** ffmpeg says `Server returned 4XX Client
Error, but not one of 40{0,1,3,4}`, which is the 406 and helps nobody.
`TRANSLATIONS` maps the known cases to instructions:

| ffmpeg | Text shown |
|---|---|
| `401` | Wrong credentials. Check the Camera Account in the Tapo app. |
| `not one of 40` / `406` | Camera busy. It accepts one RTSP connection at a time. |
| `Connection refused` | Connection refused. Check the IP and that the camera is on. |
| `timed out` | Timed out. Check the network and the camera's IP. |
| `Error number -138` | The same, adding that the router may have given it a new IP |
| `No route to host` | Camera unreachable on the network. Check the IP. |
| `404` | Invalid stream path. Expected /stream1 or /stream2. |

An unknown error passes through raw, instead of becoming a generic message
that hides information.

**Every connection has a deadline: `-timeout`.** Without it, an IP where
nothing exists leaves ffmpeg waiting for the TCP connection forever, **writing
no error**. That is what happened on the M900: the cameras are at `.116` and
`.42`, and `.env` there pointed at `.10` and `.11` — the sample values of
`.env.example`, from which `install.bat` creates `.env`. The panel only said
"no frame received", and the investigation chased decoding, the pipe and the
antivirus before anyone ran `Test-NetConnection`. The only log line, even at
`-loglevel verbose`, was `Starting connection attempt` (HISTORY 6).

With `-timeout` (in microseconds, `SOCKET_TIMEOUT_SECONDS` in `capture.py`)
ffmpeg gives up in ~6 s. On Windows the error comes out as `Error number
-138`, the C library's `ETIMEDOUT`, without the words "timed out" — hence its
own row in the table. The same deadline applies to reads: a camera that stops
sending data for 5 s brings the process down, and the automatic restart (5.8)
reconnects.

The old window showed that text on the "no signal" panel; today it goes to the
log, and the page's Live view marks a camera "no signal" after 5 s without a
frame (17.8).

### 5.8 Automatic restart

If ffmpeg dies (network drop, camera rebooting), `read()` returns `None` and
the process is recreated after `RESTART_SECONDS`. The last frame stays in
place meanwhile, and the application does not fall over.

Since OpenCV no longer captures, the environment variable
`OPENCV_FFMPEG_CAPTURE_OPTIONS` disappeared, along with the fragility of an
assignment that had to come before `import cv2` (PYTHON.md 2.2). TCP transport
is now an explicit ffmpeg argument (`-rtsp_transport tcp`). The only variable
left is `OPENCV_LOG_LEVEL`, and it only silences a warning (10.11).

---

## 6. The motion layer — `motion.py`

### 6.1 Why MOG2

| Algorithm | Assessment |
|---|---|
| Frame differencing | Simple, but catches only the **edges** of what moves and fires on any change of light. |
| **MOG2** | **Chosen.** Learns the background and adapts. Marks shadows separately, which matters a lot outdoors. Fast and built into OpenCV. |
| KNN | Equivalent, second place. A one-line switch if MOG2 fails. |
| GSOC | Better with busy backgrounds, but much slower and needs `opencv-contrib-python`. |

**How MOG2 works:** it does not store a background image. For each pixel it
keeps several statistical distributions ("mixtures of Gaussians"), so a pixel
can have more than one normal look — a swaying leaf, for instance. A pixel
that matches none of them is motion.

### 6.2 The steps of `detect()`

1. **Shrink to 640 px wide.** Motion does not need full resolution; the
   smaller image is ~9× cheaper.
2. **Gaussian blur.** Without it, sensor noise and compression artefacts
   become thousands of "moving" pixels.
3. **`subtractor.apply()`** compares with the model **and updates the
   model**. That is why it must run on every frame, warm-up included —
   otherwise the model never learns.
4. **Threshold at 200.** The mask uses 255 for motion, 127 for shadow, 0 for
   background. Cutting at 200 drops the shadows.
5. **Blank the camera's clock.** The Tapo writes the date and time in the
   top-left corner, and the digits change every second. `OVERLAY_BOX`
   (fractions of the image) zeroes that strip of the mask.
6. **Drop the frame if more than 50 % "changed".** That is not an object
   moving: it is a cloud, the sun or the camera switching to night mode.
7. **Opening and dilation.** Opening erases isolated dots; dilation grows
   what is left, joining one person's fragments into a single blob. It is also
   why the box is a little larger than the object.
8. **Contours + `boundingRect`.** Blobs with an area under `MIN_AREA` are
   ignored. The coordinates go back to the original frame's scale.
9. **Lighting filter.** A blob whose content still looks like the background
   is light changing, not an object. See 6.7.
10. **Temporal confirmation.** See 6.3 — nothing is reported before it
    persists.

### 6.3 Temporal confirmation (the filter against insects)

The real problem measured in the field: at night the infrared lights up
insects near the lens, which become **large, bright** blobs. A 30 s
measurement on the Front camera showed 12 blobs with an area above 3200 —
larger than a distant person. So **raising `MIN_AREA` would never solve it**:
size does not separate an insect from a person.

What separates them is **persistence**. A person stays roughly in the same
place for several frames; an insect appears, jumps and is gone.

`_confirm()` implements a mini tracker:

- Each blob becomes a `_Candidate` with a hit counter (`hits`) and a miss
  counter (`misses`).
- On each frame, the new blobs are matched to the existing candidates by
  **largest overlap**. A match gets `hits += 1`.
- A candidate with no match gets `misses += 1` and is dropped after
  `FORGET_FRAMES`.
- Only a candidate that reached `CONFIRM_FRAMES` hits is reported.

Cost: a person is reported 3 frames (~0.3 s) after appearing. Since the clip
starts `PRE_SECONDS` (6 s) before the event (8.2), nothing useful is lost in
the video.

**Known limitation:** an insect hovering at exactly the same spot for several
frames ends up confirmed. YOLO rejects that case.

It is also the seed of the *tracking* that may come later (backlog 7).

### 6.4 Warm-up

`WARMUP_FRAMES = 60` (~6 s at 10 fps). Before that everything is "new" and the
detector would report the whole scene.

### 6.5 Tuning

| Constant | Effect |
|---|---|
| `MIN_AREA` | Raising it ignores small or distant objects. |
| `CONFIRM_FRAMES` | Raising it demands more persistence: less noise, more delay. |
| `FORGET_FRAMES` | How long a candidate survives while missing (occlusion). |
| `OPEN_ITERATIONS` | Raising it erases more isolated dots. |
| `varThreshold` | Raising it makes it less sensitive to variation. |
| `DETECT_WIDTH` | Raising it helps distant objects, costs CPU. |
| `MAX_MOTION_FRACTION` | Tolerance to global changes of lighting. |
| `LIGHTING_CORRELATION` | Lowering it drops more lighting changes, but starts to lose people (6.7). |
| `OVERLAY_BOX` | The camera clock's region, ignored. |

**To be even less sensitive:** raise `CONFIRM_FRAMES` to 5. To recover distant
people, lower `MIN_AREA` back to 400 — temporal confirmation already holds the
noise back by itself.

### 6.6 Measured results

An A/B test on **exactly the same live frames**, 404 frames per camera, at
night:

| Camera | Frames with motion (before) | After | Reduction |
|---|---|---|---|
| Back | 2.5 % | 1.2 % | 50 % |
| Front | 8.7 % | 1.5 % | **83 %** |

Total boxes on Front: **54 → 6**.

Since YOLO only runs with motion, that means about **6× fewer inferences** on
Front. Lowering the sensitivity here costs no performance: it improves it.

### 6.7 Sunlight is not motion

**The problem, measured by day on the M900.** Front showed yellow boxes with
nobody in the scene. In 4 minutes of buffer, 99 of 2671 frames had motion,
almost all in one 12 s burst with up to 15 boxes spread over the wall, the
gate and the ground. The image's mean brightness barely changed (89 → 92): it
was not the whole scene darkening but **patches of sun** appearing and
brightening on parts of the wall, plus the shadow of the leaves swaying on the
ground. Step 6 does not catch that, because the total changed area stays well
below 50 %.

MOG2 marks as motion any pixel that became different from the background. It
cannot tell "something else appeared here" from "the same thing got
brighter".

**The idea.** Light changes brightness, not content: the edges, the plaster's
texture, the gate's pattern stay in the same place. A person changes the
content. **Normalised cross-correlation** measures exactly that:

```python
a = a - a.mean()
b = b - b.mean()
correlation = (a * b).sum() / sqrt((a * a).sum() * (b * b).sum())
```

Subtracting the mean removes "brighter or darker"; dividing by the norms
removes "more or less contrast". What is left is 1.0 for the same pattern and
close to 0 for unrelated ones. In Java it would be a loop over two arrays;
with NumPy each line works on the whole patch at once (PYTHON.md 15.4).

For each blob, `_raw_boxes()` compares the current frame with
`subtractor.getBackgroundImage()` — the background MOG2 itself learned — and
drops the blob if the correlation is above `LIGHTING_CORRELATION`.

**Only the pixels that changed.** The first version compared the whole
rectangle. But a person's rectangle is largely untouched background, which
pulls the correlation up, and the person was dropped together with the light.
The current version compares only the pixels the mask marked as changed,
before dilation (`changed`).

**Measured** on the same frames: 4 minutes of Front with nobody, and the 10
recorded clips with a person (273 frames where YOLO sees the person):

| Version | Frames with motion and nobody | Person covered by motion |
|---|---|---|
| No filter | 99 | 262 |
| Whole rectangle, 0.75 | 1 | 216 |
| Changed pixels only, 0.85 | 39 | 261 |
| Changed pixels only, 0.75 | 22 | 259 |
| **Changed pixels only, 0.65** | **15** | **258** |
| Changed pixels only, 0.55 | 14 | 245 |

0.65 cuts 85 % of the false motion and loses 4 of 273 person frames. Below
that the gain ends and the loss grows. Every clip still triggers a recording.

The background is only computed when there is some blob, so a still frame pays
nothing extra.

---

## 7. The subject layer — `people.py`

### 7.1 What YOLO does here

YOLO11 was trained on whole bodies: shape, posture, limbs, proportions. **It
has no notion of a face.** That is why a mask, a helmet, a hood or a person
with their back turned are still detected.

COCO has 80 classes. These are watched:

```python
PERSON_CLASS = 0
CLASS_NAMES = {0: "person", 14: "bird", 15: "cat", 16: "dog",
               17: "horse", 18: "sheep", 19: "cow"}
```

That is: `person`, `bird`, `cat`, `dog`, `horse`, `sheep`, `cow`. Bear,
elephant and zebra exist in COCO and were left out as implausible here —
including them would only create exotic false positives.

Animals use a higher confidence threshold by default (0.45 against 0.35 for
a person), because scene objects are mistaken for animals more easily than
for people. Since backlog 31 the three minimums — person, dog, the other
animals — are set in Settings → Detection (7.14).

**Observed on 30/09/2026, still not handled:** events labelled `cat`, `cow`,
`sheep` and `bird` in a house with a dog and people. Most likely YOLO
hesitating between species for the same dog, frame to frame. Since `labels`
accumulates everything that appeared in the event (8.4), one hesitation is
enough to enter the label. It does not change what is recorded, only the
card's text (backlog 8).

### 7.2 The `Detection` type

Detections stopped being anonymous tuples and became a `NamedTuple` in
`geometry.py`:

```python
Detection(x, y, w, h, confidence, label)
```

It is still a tuple (indexable, unpackable), so `d[:4]` is still the box, but
it now carries the label and exposes `d.is_person`. That let the same pipeline
handle people and animals without duplicating code (PYTHON 5.4).

`drop_duplicates` merges only boxes **of the same label** — a dog beside a
person overlaps a lot, and before, one of the two would have been dropped.

### 7.3 Knowing it is a dog, and which

| Goal | State |
|---|---|
| Detect that there is a dog | Works (COCO class 16) |
| Know *which* dog | The household's dogs, by the look of their fur, once the user names some views (section 20); the face layer cannot do it (10.8) |
| Know *which* person | The face layer, YuNet + SCRFD + ArcFace (section 10) |

### 7.4 A design decision: the whole frame, not a crop

The first version cropped the frame to the motion region and ran YOLO only on
that crop. A test showed the flaw:

- A 192×192 crop, the person filling almost all of it.
- YOLO got "person" right, but **the returned box was limited to the crop**:
  153×115 instead of the whole body.

That is a structural ceiling, not a tuning matter. Worse: if the motion caught
only the legs, the cropped box would **never** contain the head — and the face
layer uses precisely the body's box to confirm a face belongs to a person
(10.9).

**The solution:** YOLO runs on the whole frame. Motion serves as (a) a trigger
and (b) a relevance filter. Retested with the same tiny blob: the full box
`120,202 → 1109,712`, confidence 0.92, matching the ground truth.

### 7.5 Throttle

YOLO costs 50 to 62 ms per inference on the development PC (7.11). Running it
on every frame would eat the budget and stall the video. `MIN_INTERVAL = 0.25`
limits it to 4 runs per second per camera, **reusing the previous answer** in
between.

Evidence it works, measured still with PyTorch: the frame rate stayed at
12.7 fps before and after adding YOLO. On the M900 the number to watch is CPU
use with both cameras in motion at once (backlog 4).

### 7.6 The overlap filter

`REQUIRE_MOTION_OVERLAP = True` drops detected people that touch no motion
box. That ties the answer to the event that triggered it.

**Known limitation:** someone who stops moving is absorbed into the
background model and is no longer reported. The solution is *tracking*
(backlog 7).

### 7.7 `drop_duplicates` and IoU

Two boxes can describe the same person. "The same" is measured by **IoU**
(*Intersection over Union*): the shared area divided by the combined area. 0 =
no overlap, 1 = identical. Above 0.5 they are treated as one, keeping the more
confident.

`iou()` lives in `geometry.py`, shared with the motion tracker, which uses
`overlap_area()` from the same module to match candidates across frames.

### 7.8 Static-scenery suppression

**The problem seen in the field (26/09/2026):** the Front camera recorded two
clips marked `person left`. Re-analysing the videos, YOLO pointed at a person
in 100 % of the frames, at 0.80 confidence — and **exactly the same box** in
both clips, recorded 90 s apart: 68×82 px at (1391, 311).

It was a fixed object on the wall. A second spot at (364, 285) did the same.

The telling detail: **in the daytime clips of the same framing YOLO detects no
person at all.** The false positive is specific to infrared, which turns the
object into a dark silhouette against the light wall.

**The solution:** a scenery object does not move; a person does.
`_reject_scenery` keeps a list of spots where detections keep appearing:

- Two boxes are "the same place" when their centres are within
  `STATIC_CENTRE_TOLERANCE` px and their sizes differ by less than
  `STATIC_SIZE_TOLERANCE`. Matching by centre (not IoU) was needed because the
  second object's box **wobbled in size** — 73×65, 68×68, 71×74 — and never
  reached a high IoU, although the centre stayed put.
- The count is **consecutive**: any cycle where the spot does not reappear
  resets `hits`. Without that, someone who stands still, walks and comes back
  would keep adding hits over time.
- On reaching `STATIC_HITS` cycles in a row, the spot becomes scenery and is
  ignored.
- Spots leave the list after `STATIC_TTL` without appearing.

**Result on the real clip:** both objects were learned as two spots and
silenced from cycle 49 on. A person who moves every 10 cycles is still
detected.

**A conscious cost:** someone absolutely still for ~12 s (50 cycles at 4/s) is
suppressed. Acceptable because the clip already captured that person
arriving, and any movement frees them at once. To be more conservative, raise
`STATIC_HITS`.

**A start-up cost:** the list starts empty on every run, so the program
records one clip of the static object before learning it. Persisting the list
on disk would solve it (backlog 12).

### 7.9 A minimum height for a person

On the night of 26/09/2026 the Front camera recorded **19 events**, of which
only 3 were real people. The other 16 were little boxes on the wall above the
car, at confidences between 0.36 and 0.79 — high enough to pass the threshold.

Static-scenery suppression (7.8) **does not catch that case**: the false
positives come minutes apart, so the consecutive count resets between events
and never reaches 50 cycles.

Measuring the boxes of all 18 thumbnails settled it:

| | Box height | Height/width ratio |
|---|---|---|
| **Real people** (3) | 294–306 px | 1.55–2.32 |
| **False positives** (15) | **36–86 px** | 0.91–1.59 |

Height separates the two groups with a **3.4×** margin (86 against 294). The
ratio overlaps (1.59 against 1.55) and was dropped as a criterion.

```python
MIN_PERSON_HEIGHT_FRACTION = 0.20
```

A fraction of the frame's height, not absolute pixels, so it survives changes
to `ANALYSIS_HEIGHT`. At 540 px that is 108 px: 26 % above the largest false
positive and 2.7× below the smallest real person.

**Checked against the 18 real recordings: 18 right, 0 wrong.**

Two honest caveats:

- **It is specific to the scene.** In a scene where people appear small in the
  distance, 108 px would drop real people. Here the garage is narrow, and even
  at the back a person is over 150 px.
- **It applies only to `person`.** Animals are naturally lower than they are
  wide, and the same floor would reject a legitimate dog.

**The dog lying on the mat (R18, 10/10/2026)** needed a second rule for
`person`, a width-to-height ratio of 2.0, measured with the replay tool
(12.10). **R35 (11/10/2026)** checked whether 1.5 would also catch Aurora
curled up on the mat: the five boxes it would drop were all people —
crouching at the door, bending, sitting below the camera — so the ratio stays
at 2.0, and the rare curled-up dog goes to the bad-detection reports
(section 21).

### 7.10 One model, several cameras

`@lru_cache(maxsize=1)` on `load_model()` guarantees a single YOLO instance for
the live loop, shared by the cameras. It is the opposite of `MotionDetector`:

| Component | State | Instances |
|---|---|---|
| `MotionDetector` | that camera's background model | **one per camera** |
| `SubjectDetector` | throttle, last result and static scenery | one per camera |
| The live loop's YOLO network (`load_model`) | internal buffers | **one, main thread only** |
| The background YOLO network (`load_background_model`) | internal buffers | one, the face scan only |

Sharing between cameras works because they all run on the same thread, one
after the other. Sharing between **threads** brought the program down: see
10.9 and PYTHON 14.2.

### 7.11 Why OpenCV and not PyTorch

YOLO runs through `cv2.dnn` on the ONNX export, not through `ultralytics`. The
switch was forced by a deployment problem on 29/09/2026.

**The symptom:** on the target machine, and hours later on the development PC
too, PyTorch stopped loading:

```
OSError: [WinError 4551] An Application Control policy has blocked this
file. Error loading "...\torch\lib\shm.dll"
```

**The cause:** Windows 11's **Smart App Control**, which blocks binaries
without a signature Microsoft recognises. PyTorch's DLLs are not signed.
Confirmed in the registry:

```
HKLM\SYSTEM\CurrentControlSet\Control\CI\Policy
    VerifiedAndReputablePolicyState = 1    (on, blocking)
```

**Why not turn Smart App Control off:** it is **irreversible**. Once off, it
only comes back by reinstalling Windows. Trading the system's security for a
dependency is a high and permanent price.

**The way out:** Ultralytics publishes the official `yolo11s.onnx` in the
same release the `.pt` came from, and OpenCV — whose DLLs are signed and pass
— runs that ONNX without any PyTorch.

Gains besides unblocking:

| | Before | After |
|---|---|---|
| Dependencies | opencv, ultralytics, torch, torchvision + 38 | **opencv, imageio-ffmpeg** |
| Weight | ~2.5 GB | ~90 MB |
| Inference (dev) | 24 ms | **50–62 ms** |

The cost looked real: about 2× slower. **Measured on 09/10/2026, it was the
hardware, not the library:** PyTorch's 24 ms were on the GPU; CPU against CPU,
on the same blob, `cv2.dnn` takes 37.8 ms and `onnxruntime` 34.6 ms, with
identical output. Another ONNX runtime would buy nothing; the M900 has no GPU
to win back. `cv2.dnn` accepts an OpenVINO backend, the remaining path to
speed (backlog 14). The dependency count above is a consequence, not a goal
(PROCESS 5).

**What had to be written by hand.** `ultralytics` did the pre- and
post-processing under the hood; now they are explicit (PYTHON 17):

- `_letterbox()` fits the frame into a 640 square without distorting it,
  keeping the scale to undo it later
- The output is `(1, 84, 8400)`: 8400 candidate boxes, each with 4 geometry
  numbers and 80 per-class scores. Transposing and walking it gives the
  detections
- `cv2.dnn.NMSBoxes` removes the overlapping boxes of one detection

It was exactly the work pointed to, at the start of the project, as the cost
of using C++ instead of Python. It showed up anyway — for a reason nobody
foresaw.

**The class names** came from `model.names`. Without ultralytics,
`CLASS_NAMES` lists only the seven that matter, and filtering by class uses
that same dictionary.

### 7.12 A dog where a person stood a moment ago (R44, 12/10/2026)

When the user bends over — at the car door, petting the dog — YOLO can change
its mind about the same body and call it `dog` at 0.6–0.8, with no `person`
score left in that box. The crop landed in the Dogs tab and the event got a
`dog` label: 4 of the first 6 dog reports (HISTORY 13.16). YOLO's scores, the
bottom edge and a face inside the box do not separate it from a real dog.
**Where a person stood a moment before** does: the bending body keeps almost
the same box (IoU 0.90–0.99, 7.7), while a dog at someone's feet is a small
box inside a big one, with a low IoU.

So `SubjectDetector` keeps `recent_people`: every `person` box YOLO returned in
the last `RECENT_PERSON_SECONDS` = 2.0, with its time — as YOLO gave it, before
any person rule. A `dog` box (`DOG_CLASS` = 16) that passed
the dog minimum (7.14) and has IoU ≥ `SAME_PERSON_IOU` = 0.5 with one of them
**becomes a `person`**, and then meets the person rules like any other
(minimum height, the mat, 7.9). The order matters: the relabel comes after the
animal threshold, so a weak dog box is still dropped instead of becoming a new
person. Only earlier runs count — the current frame's people are added after
the loop, and within one frame the non-maximum suppression already keeps one
box per spot — and each camera has its own `SubjectDetector`, so one camera's
person never relabels another's dog. `replay.py` prints it as "the person's
box from a moment ago", followed by the box kept as a person.

Measured with `replay.py --prime`: the two reported bends with a person seen
before lose dog frames (298 → 289 and 18 → 9; the first still has many because
the dog really is there while the user pets her); the six true-dog clips with
a person and six with the dog alone do not change — no box relabelled.
**What it does not catch:** the dark object at the bottom of Front (two
reports) and a bend with no person seen in the 2 s before (one); they wait for
more reports. **The risk it takes:** a dog walking into the very box a person
left less than 2 s earlier, at a similar size, would be called a person; 0 of
309 true-dog boxes did.

### 7.13 A dog box that takes a vanished person's place (R46, 13/10/2026)

R44 was not enough. Of the 12 dog reports after its deploy, 7 were a person
bending or crouching; replayed, five of them still kept dog boxes. The trace
of `Front/2026-10-13/15-00-17` showed why: a woman cleaning **moves while
bent**. The box changes shape — tall to wide — and drifts 50–100 px between
YOLO runs, so the first `dog` box has IoU 0.35–0.47 with her last person box,
under `SAME_PERSON_IOU`; and a relabelled box did not renew `recent_people`,
so a bend longer than 2 s became a dog again.

**What tells it from a dog at someone's feet:** in the same YOLO run, **the
person box is gone** — the dog box replaced it. A real dog beside a person
sits next to a person box that is still there. So `SubjectDetector` also keeps
`last_people`, the person boxes of the last run that saw any, with its time
(`last_people_seen`). Each run, before the loop, `_people_replaced_by_dogs`:

1. takes the **vanished** people: last run's person boxes, if that run was
   less than `RECENT_PERSON_SECONDS` ago, that no person box of this run
   continues (IoU ≥ `REPLACED_PERSON_IOU` = 0.3);
2. goes through this run's `dog` boxes, the most confident first; each one
   claims the vanished person it overlaps most, if their IoU is ≥ 0.3, and a
   claimed person is not offered again — **one dog box per vanished
   person** (PYTHON 37).

A claimed dog box becomes a person exactly as in 7.12: after the animal
threshold, before the person rules. `_why_a_person` tries R44's reason first
("the person's box from a moment ago"), then the new one, which `replay.py`
prints as "took the place of a person who vanished". `_remember_people` puts
every relabelled box into both memories, so **a long bend renews itself**
for as long as YOLO keeps seeing it.

Measured by the developer with `--prime`, counting kept boxes per YOLO run:

| Clips | dog boxes before → after | relabelled before → after (R44 + R46) |
|---|---|---|
| The five R46 bends | 13 → 2 | 9 → 16 + 4 |
| Six true dogs with a person (HISTORY 13.16) | 202 → 202 | 0 → 0 |
| Six dogs alone (HISTORY 13.17) | 59 → 59 | 0 → 0 |

Review 19 replayed `15-00-17` with `replay.py` itself: 555 frames with a
subject, every one a person, no dog; 9 boxes relabelled, 7 by R44 and 2 by
R46. And two of the true dogs with a person, `Front/2026-10-11/16-20-00` and
`Back/2026-10-12/12-40-35`: 99 and 164 dog frames, nothing relabelled
(HISTORY 13.20). The two dog boxes left (`14-46-29`, `Back 11-23-48`)
have no person before them — the objects of R46's count, which wait for more
reports.

**Not a tracking library, yet.** Tracking proper is backlog 7, still
(proposto). The well-regarded trackers — norfair, supervision's ByteTrack —
need scipy, a large compiled dependency never tried under Smart App Control
(PROCESS 5: be wary of large binaries, not of dependencies). If backlog 7 is
decided, a tracker replaces 7.12 and 7.13 both.

**The risk it takes: the chain has no end** (R47). A real dog that takes the
place of a person who vanished — someone stepping out of view right over a
dog, with IoU ≥ 0.3 — stays a person while YOLO keeps finding it within 0.3
of its last box, since every relabelled box renews the memory. The event
would say person, the dog crop would not be kept, and in Home a "person with
no recognisable face" message would go out. None of the true-dog boxes of
the twelve clips above did. A relabelled box later dropped by a person rule
(too short, the mat) renews the memory too.

### 7.14 How sure YOLO must be, per label (backlog 31, 14/10/2026)

The user's request: set YOLO's minimum confidence in Settings, apart for a
person, a dog and the other animals, without a restart. **Settings →
Detection** holds three numbers, kept in `config.json` as new optional keys:

| Key | Default | Applies to |
|---|---|---|
| `confidence_person` | 0.35 | `person` |
| `confidence_dog` | 0.45 | `dog` |
| `confidence_animal` | 0.45 | `bird`, `cat`, `horse`, `sheep`, `cow` |

The defaults are the old `CONFIDENCE` and `ANIMAL_CONFIDENCE`, which now take
their values from `settings.DEFAULTS` — one place for the numbers — and an
older `config.json` reads them. The range is `CONFIDENCE_RANGE` = 0.20–0.90.
The page refuses anything outside it with a 400 that names the key and
stores the value rounded to two decimals; `settings.load()` replaces a stored
value outside it — a hand edit, a string, `true` — by its default, so a bad
value never breaks a read, and `check_data` reports it as a warning. The page
reads the range and the defaults from `/api/settings`, so the numbers live
only in `settings.py`.

**Sliders, not numbers (backlog 35, 14/10/2026).** The user's words: "the
sensitivity cannot be numeric — a kind of slider where the middle is our
default value". Each minimum is an `<input type="range">` with no number on
it; its ends say in words what they do — "More detections, more false
alarms" on the left, "Fewer, stricter" on the right. The middle is always the
default, whatever its value: the mapping is **piecewise linear**, two straight
lines that meet at the default (PYTHON 42).

| Position (of `SLIDER_STEPS` = 1000) | Minimum confidence |
|---|---|
| 0 | 0.20, the low end of `CONFIDENCE_RANGE` |
| 0 → 500 | in proportion from 0.20 to the default |
| 500 | the default (0.35 for a person, 0.45 for a dog or another animal) |
| 500 → 1000 | in proportion from the default to 0.90 |
| 1000 | 0.90, the high end |

So the two halves have different slopes: for a person, the left half covers
0.15 and the right half 0.55. `settings.slider_position(value, default)` and
`settings.slider_value(position, default)` are the two directions; they live
in Python, where `tests/test_detection_sensitivity.py` checks them, and the
page never computes the mapping itself. `GET /api/settings` adds
`confidence_positions` (each minimum as a position) and `slider_steps`; Save
posts `{"confidence_positions": {key: position}}`, which the server checks (a
whole number from 0 to 1000, a known key) and turns back into the numbers
`config.json` has always stored — **nothing on disk changed**. The numeric
keys are still accepted: Back to the defaults uses them.

**Why 1000 steps.** Save sends all three sliders, touched or not, so an
untouched slider must give back exactly the number it was shown. With 100
steps the right half of the person slider moves 0.011 per step, and a stored
0.40 would come back as 0.41. With 1000, every two-decimal value from 0.20 to
0.90 survives value → position → value for any default (checked for 0.20,
0.25, 0.35, 0.45, 0.50 and 0.90 in review 24). A value with three decimals —
only a hand edit could store one — is rounded to two on the next Save.

**The explanation stays beside them** (the user, the same day: "the
explanation on the numbers screen was perfect; I want to know how the sliders
work in the background"): what the minimum is and what each direction does,
always visible; a **How the sliders work** part with the mapping in words and
one line per slider — "Person: minimum 0.35 now, default 0.35." — refreshed
on Save, not while dragging (that would need the mapping in JavaScript too);
and what no slider fixes, below. On a phone each slider takes its own row and
the two end texts sit under it.

**How the detector uses them.** YOLO runs once with the lowest of the three
as its floor — the network's own cut and the NMS's — and each box is then
held to its own label's minimum; a box under it is dropped as "person below
confidence" or "animal below confidence" in `replay.py`'s trace. A lower floor
is safe because greedy NMS (PYTHON 17.4) suppresses a box only in favour of a
stronger one: adding weaker boxes never removes a stronger box. The minimums
come **before** R44's and R46's relabelling (7.12, 7.13): a `dog` box is
judged by the dog minimum, as YOLO named it, so a bend called dog at 0.40 is
still dropped at the default 0.45, as before. Judging a relabelled box by the
person minimum instead would change today's output.

**Without a restart.** Each camera's `SubjectDetector` takes `load_settings`
(by default `settings.load`) and calls it again when its copy is older than
`SETTINGS_REFRESH_SECONDS` = 2.0 of the monotonic clock — not the replay's
`now` — and only when there is motion to judge. A read costs 0.23 ms on the
M900. Asking again, rather than being told, also catches a hand edit of
`config.json` (PYTHON 39).

**At the defaults nothing changes.** Review 21 replayed R46's three clips
(`Front/2026-10-13/15-00-17`, `Front/2026-10-11/16-20-00`,
`Back/2026-10-12/12-40-35`) with the detector before and after: the same
decisions and the same totals on every frame. Only the order of the reasons
on three lines differs, because the below-confidence drops are now written
first.

**What it leaves alone.** The face scan's bodies (`person_boxes`, 10) and
`tools/dog_crops.py` keep the default numbers: they are not live detection.
`replay.py` reads the settings of the folder it runs in, so a replay follows
what is set now, not what was set when the clip was recorded. And the page
says what no number fixes: a person bending over is called `dog` as
confidently as a real dog, so moving the dog slider right cuts real dogs first. A
lower person value feeds R44's and R46's memories with more boxes, which
lengthens R47's chain.

**The default, marked (backlog 38, 14/10/2026).** A slider moved and moved
back could not be put on the default by eye. One `<datalist id="slider-default">`
in the form holds a single `<option>`, set to `slider_steps / 2` by
`showDetection`, and each slider names it in its `list` attribute; the
browser draws a tick under the track there (PYTHON 43). At the default the
thumb covers the tick, as it should.

---

## 8. The recording layer — `clips.py`

### 8.1 Nothing is re-encoded

The clip is assembled by concatenating **whole segments** from the buffer with
ffmpeg's `concat` in `-c copy` mode:

```
ffmpeg -f concat -safe 0 -i list.txt -c copy -movflags +faststart out.mp4
```

`-c copy` means "copy the packets, do not decode or re-encode". The result is
bit for bit what the camera produced — no better quality is possible, since
the camera is the source. `+faststart` puts the index at the start of the file,
so a browser can play and seek it while it downloads (17.13).

**Checked:** the assembled clip comes out at **1920×1080, h264, 270 frames in
18 s**, while analysis runs at 960×540. Had it been re-encoded from the
analysis frames, the video would come out at 960×540.

### 8.2 When the event starts and ends

- It starts on the first frame with a detected subject. At that moment the
  **thumbnail** is saved and the time is recorded.
- `POST_SECONDS = 5.0` — the event closes after 5 s with nobody. Detection
  flickers, and stopping at once would split one event into dozens of files.
- `MAX_SECONDS = 60.0` — a hard ceiling.
- `PRE_SECONDS = 6.0` — how far back to ask for when choosing segments.

### 8.3 The assembly delay

ffmpeg only finishes a segment when the next one starts. Assembling the clip
at once would take the incomplete last segment, so assembly runs in a
**thread** that waits `ASSEMBLY_DELAY = SEGMENT_SECONDS + 2` seconds before
concatenating. The same thread then runs the face scan and the post-scan
messages (10.1, 22.3).

The metadata, though, is written **at once**, so the recording appears on the
Recordings tab immediately; the video materialises a few seconds later.

`wait_for_jobs()` is called on exit so no assembly is left half done.

### 8.4 The files of an event

```
19-17-30.mp4     the video, assembled from the original segments
19-17-30.jpg     the first frame in which the subject appeared
19-17-30.json    metadata
```

Optional companions, all sharing the base name so the archive moves them
together: `.best.jpg` (the best view of a person), `.alert.jpg` (the photo of
a late notification), `.side.jpg` (a side face), `.people.jpg` (the frame
where two or more people were counted, 22.3) — the full table is 19.2.

The thumbnail comes from the analysis frame (960×540) reduced to
`THUMB_WIDTH = 480` — no practical loss, since it is always shown small.

The `.json` exists so the Recordings tab **never has to open a video**:

```json
{
  "camera": "Front",
  "started_at": "2026-09-26T19:52:06",
  "time": "19:52:06",
  "seconds": 12.1,
  "labels": ["dog", "person"],
  "best_confidence": 0.88,
  "video": "19-52-06.mp4",
  "thumbnail": "19-52-06.jpg",
  "reason": "subject left"
}
```

`labels` accumulates everything that appeared during the event, not only on
the first frame. `most_people`, **optional since 14/10/2026** and written
only when a person was seen, is the most person boxes YOLO kept in one
analysis frame of the event — what the face scan's count is weighed against
(22.3, R42 (b)). `people_thumbnail`, **optional since 15/10/2026**, names the
`.people.jpg` written when that count reached two or more (22.3, R56).

One JSON per clip is deliberately simple and inspectable — the next step is
SQLite, once there is search by person and period (backlog 13).

### 8.5 The thumbnail is the only one with boxes drawn

The **video** is never touched, so there is no way to soil it. The
**thumbnail** gets the boxes on purpose, because its job is to be leafed
through by a human.

That was an explicit precaution in the old version (the recorder received the
clean frame); now it is a consequence of the architecture, which is better: it
does not depend on anyone remembering.

### 8.6 Storage

The rate depends on what the camera sees: a still scene compresses a lot, a
scene with people in daylight compresses little. Two measurements:

| Measurement | Rate |
|---|---|
| An 18 s night clip, dev, 26/09 | ~48 KB/s |
| **Every clip of 30/09 on the M900** (day and night) | **~120 KB/s** |

30/09 is the realistic reference: **102 events, 41 minutes of clips, 303 MB**.
At that pace:

| Period | Space |
|---|---|
| Per day | ~300 MB |
| Per month | ~9 GB |
| Per year | **~110 GB** |

An earlier estimate in this section said ~5 GB a year. It used the night rate
and assumed 5 minutes of activity a day; the real house has 8 times more. At
that volume an archive stopped being optional: section 11.

The rolling buffer costs extra and does not grow: 6 to 8 MB per camera (5.5).

### 8.7 Zip archiving: built, measured and removed

Clips stay on disk as loose `.mp4` files. **There is no compression**, and
that is a measured decision, not an oversight.

On 26/09/2026 zip archiving was built in full — packing the clip, deleting the
`.mp4`, unpacking on access, a `ZIP` badge on the card — and then removed,
because measuring the real file showed it does nothing:

| Method | 1302 KB of mp4 becomes | Gain |
|---|---|---|
| deflate | 1299 KB | **0.2 %** |
| bzip2 | 1304 KB | **−0.2 %** (bigger) |
| lzma | 1313 KB | **−0.9 %** (bigger) |

**Why:** H.264 is already entropy-coded. The redundancy a general-purpose
compressor looks for was removed by the codec. Two of the three methods make a
**bigger** file, because the container's overhead beats the saving.

The cost was real: losing the double-click to watch, and extracted `.mp4`
files piling up beside the `.zip` files. In exchange for 2.6 KB per recording.

**Beware of old numbers.** An earlier measurement said 5–11 %, and it was right
**for the old format**: that file was re-encoded at CRF 26 and still had slack.
Today's files come from the camera's hardware encoder and are much tighter.
The conclusion changed with the format — if the format changes again, measure
again before concluding.

**What really reduces disk use** in this project, in order of impact:

1. Not recording what is not an event — done (motion, the lighting filter,
   temporal confirmation, static-scenery suppression).
2. Not re-encoding — done (5.1). The old file was 25 % larger than the
   original, and worse.
3. **Moving old recordings off the disk** — the archive (section 11) moves them
   to an external drive after 30 days; production has none configured yet.
   With ~300 MB a day, the M900's 394 GB free (30/09/2026) last about three and
   a half years — less with more cameras or more motion.
4. Compressing — 0.2 %, dropped.

---

## 9. The old OpenCV window — `ui.py` (removed 10/10/2026)

Until `v2026.10.10.4` the interface was an OpenCV HighGUI window: one numpy
image per frame, with a side menu (Live, Records, People, Settings), a
letterboxed live view or a grid of cards, and a calendar. HighGUI has **no
widgets** — no button, list, scroll, text field or layout manager — so every
rectangle and letter was drawn by hand, clicks arrived as raw coordinates, and
the keyboard came through `waitKey`. It grew to 616 lines and 60 drawing calls
and was replaced by the web page (section 17); why that was a bias and not a
decision is in PROCESS 5.3. The full text of this section is in git, up to
tag `v2026.10.10.3`.

What it taught, and still applies:

- **The loop must not ride on a window** (section 15): `waitKey` set the pace
  and closing the window stopped recording.
- **A window has no close event** in HighGUI; checking
  `getWindowProperty` *after* `waitKey` was the only way to notice the X
  (HISTORY 4).
- **`WINDOW_KEEPRATIO` is 0 on Win32**, so the picture stretched until the
  image was built at the window's exact size and letterboxed (HISTORY 4).
- **`cv2.putText` only draws ASCII** (Hershey fonts have no accents) — one of
  the reasons for the web, where accents, pasting and video come free.
- **Redraw only when something changed**: an immediate-mode interface keeps no
  state, so the old one rebuilt the screen only on a new frame or an input.

## 10. The face layer — `faces.py`

### 10.1 It runs on the clip, not live

A face that is 60 px in the original 1080p is 30 px in the 960×540 analysis
frames. The recogniser wants ~112 px. Recognising faces in the analysis frames
simply does not work.

That is why `scan_clip()` runs **on the assembled clip**, in the same thread
that assembles it (8.3). Gains:

- The original resolution, the best available
- Off the critical path: it steals no CPU from live analysis (and since R23 it
  pauses while any camera is recording: 12.10)
- It runs only when the event had `person` among its labels

The cost is that the face appears on People, and a person's name reaches the
phone, some seconds after the event (22.3).

### 10.2 YuNet finds, SCRFD places the points, ArcFace recognises

Since R49 step 2 (14/10/2026, 10.14). Until then YuNet's own five points fed
SFace, and the head-tops YuNet takes for faces drew wrong "sure" matches.

| Role | Model | Size |
|---|---|---|
| Find faces in the frame, and the `is_frontal` gate (10.9) | `cv2.FaceDetectorYN` (YuNet) | 227 KB |
| Place the five points, in the square around each face | InsightFace's SCRFD-10G (`det_10g.onnx`), through `cv2.dnn` | 17 MB |
| Align them onto the 112×112 template | `cv2.FaceRecognizerSF.alignCrop` (SFace's object, its model loaded only for this) | 37 MB |
| Make the embedding | ArcFace R50 (`w600k_r50.onnx`), through `cv2.dnn` | 167 MB |

For each frontal face, `embed(frame, box)` cuts **the same square
`context_crop` saves as the view's photo** (`_square`, 2.2 × the face, kept
inside the frame) and hands it to `embed_view`: SCRFD runs at 320
(`LANDMARK_SIZE`, score ≥ 0.2 `LANDMARK_SCORE`), the detection nearest the
face's centre gives the five points, `alignCrop` fits them by least squares,
and ArcFace returns **512 numbers**. Comparison is by cosine; embeddings of
different lengths compare as 0.0. The scan and the stored photo embed alike:
on four real clips the same face from the frame and from its saved 300 px
JPEG gave cosine 0.97–0.99 (median). A face SCRFD does not find in its square
is dropped and counted: the scan's log line ends with "N without landmarks".

| Threshold | Value | Why (10.14) |
|---|---|---|
| `MATCH_THRESHOLD` | 0.30 | the first round value above the last wrong answer of the sweep |
| `LEARN_THRESHOLD` | 0.40 | 0.09 above the closest pair of two different people (0.313); since backlog 32 only the default of the user's sure threshold (10.15) |
| `SAME_FACE_THRESHOLD` | 0.35 | above that pair too; about as many groups per clip as SFace at 0.40 |

YuNet and SFace come from `opencv/opencv_zoo`; SCRFD and ArcFace from
InsightFace's `buffalo_l.zip` release (289 MB), of which `downloads.py` keeps
the two files in `models/buffalo_l/` and deletes the zip. `downloads.py` uses
the standard library only and imports nothing from `jarvis`, so
`production.ps1` can run it from the release it is about to deploy (18.7).
**Since 15/10/2026 it also fetches the dogs' model** (section 20), the one
file it pins: `PINNED` maps `dinov2_small.onnx` to a URL **at a fixed
commit** of its Hugging Face repository and to its SHA-256; `_fetch_pinned`
downloads to `<name>.part`, hashes it in 1 MB blocks (`sha256`, PYTHON 44)
and keeps it only on a match — a wrong hash deletes the `.part` and raises,
so nothing half-trusted lands in `models/`. The face files are still fetched
by URL with no hash; their sources are release assets that do not move.
InsightFace's models are "for non-commercial research purposes only" — the
user accepted it for this house (CONTEXT 3).

### 10.3 One face per person per event

A clip has dozens of frames of the same person. `_group()` joins the
observations by the embeddings' own similarity (`SAME_FACE_THRESHOLD = 0.35`)
and keeps, of each group, the **heaviest** view — the one with the largest
`width × score`, the largest and sharpest picture. It gives the sighting its
thumbnail, `face_width` and `box`, and a new unnamed entry is built from it
and three others.

**The best-matching view decides who it is (R51, 14/10/2026).** Under ArcFace
the heaviest view is often not the one the recogniser knows best: Gustavo's
daytime clip `Back/2026-10-12/15-44-28` had 39 views of him, the heaviest at
0.349 — "probably" — while his best scored 0.421. `_best_view(gallery,
group)` matches **every** view of the group and keeps the best by the same
preference as `Gallery.match`: a person found, then a named person, then the
score. That view gives the sighting its person and score, and it is the view
`reinforce` learns, with its own crop, when it clears `LEARN_THRESHOLD`.
Measured by the developer on 24 groups (139 views) of both residents' clips,
leave-clip-out — the views a clip itself taught hidden from its own test, or
the gallery only remembers itself (0.959 against an honest 0.551; PYTHON 42):

| Method | Sure (≥ 0.40) | Probably | None | Wrong person | Other resident's best |
|---|---|---|---|---|---|
| heaviest (before) | 11 | 12 | 1 | 0 | 0.243 |
| **best** (chosen) | **12** | 12 | **0** | 0 | 0.256 |
| second best | 9 | 15 | 0 | 0 | 0.243 |
| median of the best 3 | 11 | 13 | 0 | 0 | 0.243 |

Best of N lifts the other resident by 0.013 at most, 0.044 under
`MATCH_THRESHOLD`. **What it raises, and nobody measured:** a stranger has N
chances instead of one to cross 0.30 against a resident, and a named match
wins over a far better unnamed one, so a returning stranger whose views match
their own unnamed entry at 0.6 needs only one view at 0.30 against a resident
to be recorded as "probably" that resident — silent in Home. No stranger with
a face is in production's data yet; review 24 left it as a watch (R54). Cost:
one `Gallery.match` per view, well under 0.1 s for 40 views.

If two groups of the same clip match the same person in the gallery, only the
heavier becomes a sighting (`seen_here`). And `list_sightings()` shows one card
per person per clip, because after a merge (10.4) two old cards can point at
the same person.

The result: an event with one person gives one sighting, not thirty.

### 10.4 The name is a reference, not a label

The goal of People: **name a person once and have them recognised on their
own from then on.**

`faces/gallery_arcface_w600k_r50.json` (10.14) keeps the people, each with a list of embeddings (the
reference "views"). Each sighting becomes a `.jpg` + `.json` pair in
`faces/<date>/` that points at the person by `person_id`. The name is resolved
when shown, so naming a person renames **all** their sightings, past and
future.

**How it was, and why it did not work.** Measured on the M900 over 15 minutes
of use: **14 "people"**, each with **one** view, for 3 real people. Three
causes:

1. Every face that matched nobody became a new person — profiles, the backs of
   heads and an arm included (10.9).
2. Giving the same name to two cards created **two** people with that name;
   each kept only its own view.
3. A person only learned new views from faces of 80 px or more, and the
   cameras deliver 40 to 60 px. In practice nobody learned anything.

**How it is today.**

| Moment | What happens |
|---|---|
| A new face that matches nobody | Becomes an unknown **only if it appeared in 2+ frames** of the clip (`MIN_VIEWS_FOR_NEW`), already with up to 4 views |
| A face that matches (≥ `MATCH_THRESHOLD` 0.30) | The sighting gets that person. Above `LEARN_THRESHOLD` (0.40) the view is **learned** |
| It matches a named person and an unknown one | The **named** one wins: the name is what the user asked the system to learn |
| The user names a card | `rename()` gives the name and **absorbs** every similar unknown (≥ `LEARN_THRESHOLD`) |
| The user gives a name that already exists | The two people **become one**, adding up their views — the page warns first |

Absorbing and merging (`_merge`) move the views to the named person and
rewrite the `person_id` of the old sightings. The rewrite waits for `save()`:
each merge records `{old id: new id}`, and the save reads the sighting files
once for the whole operation, however many entries it merged (R45). Up to `MAX_EMBEDDINGS = 40`
views per person; past that, a new view enters only in place of one of the
two most alike, or is deleted (17.14, backlog 28).

Measured on the same set of clips with the new pipeline: **3 people**. Naming
one card of the older lady absorbed her other identity and put the name on 3
cards; naming one card of the user named the other camera's too.

`LEARN_THRESHOLD` is higher than the matching one on purpose. With 40 px
faces a weak similarity can be chance, and **learning** from chance would
contaminate everyone's reference from then on. Showing a wrong name can be
corrected; learning wrong spreads. For the same reason a match below
`LEARN_THRESHOLD` is announced as "probably <name>" (R5), and only a sure
match counts as a resident (22.2). Under SFace the two were 0.363, OpenCV's
value for sharp faces, and 0.45; under ArcFace 0.30 and 0.40 (10.2).

**Two instances of the gallery.** The web and the clip-scanning thread each
have their own `Gallery`. If one saved the copy it loaded earlier, it would
erase what the other did — a name just given would vanish. Every write
reloads the file under `_GALLERY_LOCK` before changing it.

**No undo of a merge**, by the user's decision (backlog 9): the page warns
before every merge, and a yes goes ahead. A real mess is rebuilt with
`tools/rebuild_faces.py`, which sets the current `faces/` aside and rebuilds
everything from the clips — the names must be given again, one card per
person.

### 10.5 The reality of night infrared

Tested on the real night clip, where YOLO detects the person at 0.92:

| Measure | Value |
|---|---|
| The face YuNet finds | **44 px wide** |
| The width the recogniser wants | ~112 px |

The face is detected, but an embedding taken from 44 px is unreliable. The
solution was not to drop it but to **mark** it:

```python
MIN_FACE_WIDTH = 36
GOOD_FACE_WIDTH = 80
```

Below 36 px a face does not enter at all; below 80 it is marked small (the old
window showed its width in red). Until September 2026 small faces **never**
entered the references, so as not to contaminate the gallery. In practice that
prevented any learning, because by day the cameras deliver 40 to 60 px too
(10.4). Today what protects the gallery is the quality filter (10.9) and
`LEARN_THRESHOLD`, not the width.

The honest expectation: good identification by day and at short distance; at
night the system detects that there *is* a face, but saying whose will be
unreliable. The biggest gain is a motion-triggered light (backlog 16).

### 10.6 Two bugs the test revealed

**Sampling in the wrong place.** The first version read the clip's first
frames. Since there is pre-recording (8.2), the start of the clip is precisely
**before** the person arrives — and the result was zero faces in a clip that
clearly had a person. Now the step is computed from the total frame count,
spreading the samples over the whole clip:

```python
step = max(total // MAX_SAMPLES, SAMPLE_EVERY)
```

(Since R20 the scan also looks densely at the moments a person was seen:
12.9.)

**A floor too high.** `MIN_FACE_WIDTH` was 55 and silently dropped the 44 px
face. The detector was right; the filter was wrong.

### 10.7 Naming

The old window had no text field: a prompt was drawn by hand and the keys came
through `waitKey`, with `q` no longer quitting while typing. The web page has
real forms: a name field on each unnamed card, "Belongs to…" to attach a face
to an existing name, and rename on the person's page (17.9, 17.10).

### 10.8 Animals: why this layer cannot do it

The face recogniser is trained only on human faces. A dog has no face YuNet can detect, and
even if it had, the embedding would mean nothing.

Telling *which* dog needs another layer, on the **whole body** and not the
face. Two paths were weighed:

| Path | Accuracy | Cost |
|---|---|---|
| A classifier trained on photos of the household's own dogs | Good for a few known dogs | ~50–100 crops per dog |
| A generic animal re-ID embedding (MegaDescriptor) | Lower | Only downloading the model |

What was built is a third, simpler one — the dog cut out of its box and
described by the tone and colour of its fur, matched against the views the
user named — in section 20. The People pattern (cards with a crop, a name
given once, merging identities) serves the dogs unchanged. At night a dark dog
becomes a silhouette in infrared; accuracy will always be well below human
faces.

### 10.9 Only frontal faces, and only on a person

A sheet with the 19 sightings of the first 15 minutes on the M900 showed that
several **were not even faces**: an arm (106 px, marked reliable), profiles,
the backs of heads. A profile's embedding describes nobody — and each one
became a new "person".

72 detected faces in the 10 recorded clips were measured, with three numbers
taken from YuNet's own detection, which returns 5 points: the eyes, the tip of
the nose and the corners of the mouth.

| Measure | A frontal face | Profile, back of the head, car mirror, patch of sun |
|---|---|---|
| YuNet's confidence | 0.81 to 0.92 | often 0.6 to 0.7 |
| Nose off the eyes' centre (÷ the distance between the eyes) | up to 0.3 | 0.5 to 2.3 |
| Distance between the eyes ÷ box width | 0.38 to 0.50 | 0.1 to 0.33 |

`is_frontal()` demands all three: confidence ≥ `IDENTITY_SCORE` (0.75), the
nose at most `MAX_NOSE_OFFSET` (0.35) off, and the eyes at least
`MIN_EYE_SPREAD` apart — 0.38 until 14/10/2026, **0.30 since** (R30 (b),
10.12). In a profile the nose goes to the side and the eyes almost overlap. A face that fails only these limits can still reach the
phone as a picture, never the gallery (10.12).

Four false ones were left on Front, small (36 to 42 px), passing all three —
one was a patch of sun on the ground. So, on the frames where a frontal face
appears, `scan_clip()` also runs YOLO (`people.person_boxes()`) and accepts the
face only if its centre lies **in the upper half of a person's body**. YOLO
runs only on those few frames, so the cost is small: each clip takes 9 to 17 s
on the M900, off the critical path.

**One network per thread, one scan at a time.** In the first version
`person_boxes()` used `load_model()`, the same network as the live loop. The
scan runs on the thread that assembles the clip (8.3), so the two threads
called `net.forward()` on the same object at the same time. A `cv2.dnn.Net`
keeps internal buffers between calls and cannot do that: the program crashed
with `buf.shape() == m.shape()` in the middle of live analysis, right after an
event.

The fix: `load_background_model()` loads a **second copy** of the network
(~40 MB more memory), used only off the main loop. And `scan_clip()` runs
under `_SCAN_LOCK`: each event assembles its clip in its own thread, and two
events in a row would also fight over the face networks, which are shared. The
scans queue up, which also avoids two heavy scans at once on the M900's CPU.

Tested with the main loop running inferences while 4 scans ran in parallel:
the old code reproduces the exact error; the new one passes with no error.

In C# the situation is the same as a non-thread-safe object shared without a
`lock`. Python has the GIL, but it only protects the interpreter: OpenCV
releases the GIL inside its C++ code, and two calls really do run in parallel
(PYTHON 14.2).

`MAX_SAMPLES` went from 30 to 60 frames per clip: with the filter, fewer faces
are left per frame, and more samples give more chance of a good view and of
reaching the 2 an unknown needs.

### 10.10 The card's photo

The thumbnail used to be SFace's aligned 112 px crop, enlarged to 160. That
crop is for the recogniser, not for a person to look at: it is cut tight (no
hair, no chin) and, from a 45 px face, it is already enlarged once — enlarging
it for the card blurred it a second time.

Today `context_crop()` cuts straight from the original frame a square
`THUMB_CONTEXT` (2.2) times the face's size, with hair and shoulders, and saves
it at 300 px with cubic interpolation. The page shows it smaller. The embedding
still comes from the aligned crop; only the photo changed.

### 10.11 The clip is read by ffmpeg, not by OpenCV

`scan_clip()` used to read the clip with `cv2.VideoCapture`. OpenCV carries an
ffmpeg of its own, and that decoder prints straight to the terminal each
damaged block it finds (`[h264 @ ...] error while decoding MB 52 20`). On a day
when Back's Wi-Fi was bad, the terminal filled with those lines, which look
like a program error but are only the camera's faulty video (INSTALL 8).

`OPENCV_FFMPEG_LOGLEVEL`, which should silence that, **has no effect** in
OpenCV 5.0 — tested. So reading moved to **our** ffmpeg, the same as
`capture.py`, with `-loglevel quiet`:

```
ffmpeg -i clip.mp4 -vf "select=not(mod(n\,STEP))" -fps_mode passthrough
       -frames:v 60 -pix_fmt bgr24 -f rawvideo pipe:1
```

The `select` filter lets through only one in every `STEP` frames (`n` is the
frame number, `mod` the remainder). `-fps_mode passthrough` stops ffmpeg from
duplicating frames to "fill in" the dropped ones. The backslash in `\,` is
there because a comma separates filters in `-vf`'s language.

A bonus: `VideoCapture` decoded and handed **every** frame to Python to throw
most away; ffmpeg drops them before the pipe. Measured on a 577-frame clip:
**3.3 s → 1.6 s**, with the same 60 frames (a mean difference of 2 in 255 per
pixel, from the colour conversion done by another library). Scanning the clips
of 29/09 gave the same 3 people with the same similarities.

Size and frame count come from `_describe()`, which runs `ffmpeg -i clip` with
no output: it prints the video's header and stops, decoding nothing. Opening
with `VideoCapture` just to ask the size already decoded the start and printed
its damage.

The warning `setPreferableTarget ... not supported by the new graph engine`,
which OpenCV prints when loading the face detector, is silenced by
`OPENCV_LOG_LEVEL=ERROR` in `jarvis/__init__.py`. That file runs before any of
the program's `import cv2`, which is when OpenCV reads the variable
(PYTHON 2.2).

### 10.12 The face seen from the side (R30, 11/10/2026)

When a person event's scan keeps no recognisable face, `faces_in(frame,
sides)` also collects the good non-frontal faces (score ≥ `IDENTITY_SCORE`,
width ≥ 36 px), and the scan saves the best — smallest nose offset, then
largest — as `HH-MM-SS.side.jpg` beside the clip, **never into the gallery**.
The message after the scan is, in order of preference: the recognised face,
else "face, side view", else the best view of the person (12.9, 22.3). On the
three daytime clips of 10/10 that had no face, each now gives a side view
(40–59 px); they had failed on the eye spread, not the nose.

Part (b), loosening the frontal limits for recognition, was measured on
11/10 and not done: side faces of the one named person matched 55–100 % of
the time, but with a single named person nothing showed that a stranger's
side face would not match too. It waited for a second named person — Izabel,
13/10 — and for ArcFace.

**Done on 14/10/2026: `MIN_EYE_SPREAD` 0.38 → 0.30, `MAX_NOSE_OFFSET` stays
0.35.** On both residents' clips, read in place from production and scanned
densely, 215 faces were rejected: 151 by both limits, 63 by the eye spread
alone, 1 by the offset alone. The eye-spread-only ones are mostly people
**looking down** — at the door, at a phone — whose eyes are foreshortened,
not turned. Each candidate gate scored against both residents' Chosen:

| Offset ≤ | Spread ≥ | Faces added | Right resident | Of which sure | Other resident | Nobody |
|---|---|---|---|---|---|---|
| 0.35 | 0.38 (before) | 0 | 0 | 0 | 0 | 0 |
| **0.35** | **0.30** | **58** | **48** | 14 | **0** | 10 |
| 0.35 | 0.20 | 62 | 52 | 15 | 0 | 10 |
| 0.5 | 0.30 | 82 | 67 | 22 | **1** | 14 |
| 0.7 | 0.20 | 122 | 96 | 27 | 2 | 24 |

Loosening the offset is what lets the wrong resident in, so it stays. On 16
daytime person clips of Front with no face sighting (13/10, 15:08–17:45), 0.30
gives 2 of them a face, both Izabel looking down (8 probably, 1 sure); 0.25
also adds "Gustavo probably 0.32" in one of her clips, on a face too blurred
to tell — which is why the limit stops at 0.30. The whole scan simulated
under the new gate: sure sightings Gustavo 5 → 7 and Izabel 8 → 11, no clip
changes person, the same one new unnamed entry. Cost: about 3 more
embeddings per resident clip, ~0.4 s at 0.13 s each (10.14). **The sample's
limit:** two people and one afternoon of one camera, no stranger with a face
— the same watch as R51's (10.3, R54).

### 10.13 A cheaper face scan (R31, 11/10/2026)

YuNet finds faces on a 960-px copy of the frame, and each face is refined on
the full 1080p frame, where the alignment needs the detail: 45 ms per frame
instead of 137, with 6 % fewer frontal face frames on 455 test frames — a face
is seen in many frames of an event, so the loss per event is smaller. Outside
events the scan no longer halves live analysis.

### 10.14 Stronger face models, measured and switched (R49, 14/10/2026)

**Why.** YuNet takes the top or the back of a head for a face, `is_frontal`
passes it, and under SFace those views drew wrong "sure" matches (R49). The
user allowed much better models, with a migration of every gallery
(CONTEXT 3). Step 1 only measures: nothing in the program changed.

**The tool.** `tools/face_bench.py` reads a copy of production's `faces/`
(`backups/r49_faces_20261014`: Gustavo and Izabel, 146 views, twelve of them
head-tops labelled by hand) and runs each candidate pipeline over every
300 px view — what a migration would embed again. Per pipeline: head-tops
accepted as a face; leave-one-out against both people's Chosen, each probe's
exact copies (same JPEG bytes or same embedding) left out, **today** (146
probes against all 80 Chosen) and **clean** (134 faces against the 75 Chosen
that are faces); a threshold sweep 0.20–0.60 with the first threshold at
which nothing is wrong; how far apart the two people sit; cost on the M900
and model size. Every model runs through `cv2.dnn` — no new dependency.
`--pipelines` picks some, `--json` saves every number; a pipeline whose model
is missing from `models/bench` is skipped.

| Pipeline, on the 300 px views | Head-tops accepted | Faces rejected | Clean: no wrong from → right, of 134 | Closest cross pair | Detect / embed ms | MB |
|---|---|---|---|---|---|---|
| stored: YuNet + SFace on the clip, today | 12 | 0 | 0.375 → 110 | 0.498 | — | 37 |
| YuNet + `is_frontal` + SFace again | 0 | 95 | 0.200 → 38 | 0.288 | 30 / 15 | 37 |
| **SCRFD-10G at 320 + ArcFace R50** (from buffalo_l) | 12 | 0 | **0.275 → 125** | 0.313 | 53 / 67 | 182 |
| buffalo_l whole: SCRFD at 640, score ≥ 0.5, 3D pose | 2 | 27 | 0.200 → 106 | 0.276 | 220 / 130 | 319 |
| YuNet + ArcFace R50 | 12 | 3 | 0.475 → 36 | 0.478 | 26 / 68 | 167 |
| SCRFD + SFace | 12 | 0 | 0.550 → 22 | 0.538 | 233 / 15 | 265 |
| AdaFace IR-101, on YuNet / on SCRFD | 12 | 3 / 0 | 0.475 → 34 / 0.500 → 44 | 0.597 / 0.505 | 26 or 204 / 125 | 249–265 |
| MagFace iResNet50, on YuNet / on SCRFD | 12 | 3 / 0 | never / 0.600 → 32 | 0.760 / 0.640 | 26 or 204 / 68 | 167–183 |

The tool prints every row, eleven pipelines and the stored baseline, which
reproduces review 21's 111 / 7 / 28.

**What it shows.**

1. **No candidate tells a head-top from a face.** SCRFD's score is the best
   cue and still overlaps (head-tops 0.22–0.65: at ≥ 0.5 it keeps 2 of 12
   and loses 27 of 134 faces). The 3D landmark model fits a face pose onto
   the top of a head (11 of 12 at pitch ≥ −20°). The embedding's length,
   AdaFace's and MagFace's quality cue, overlaps for all three recognisers.
   CR-FIQA has no licence in its repository and was not used.
2. **Under ArcFace a head-top stops being dangerous** — on these two people.
   Every head-top's best match is its owner; the highest to the other person
   is 0.29. "Today", head-tops kept among the references, has 0 sure wrong
   against SFace's 7.
3. **The recogniser that wins is ArcFace aligned on SCRFD's landmarks.**
   Both are needed: ArcFace on YuNet's points gets 36, SFace on SCRFD's 22.
   Better points give a better-aligned crop. SCRFD fed the 300 px view at
   320 beats 640.
4. **AdaFace and MagFace are worse here**, with each one's better colour
   order; AdaFace's export matched PyTorch at cosine 1.0.
5. **Today's gate cannot run again on the views.** YuNet + `is_frontal`
   rejects 95 of 134 faces on the 300 px JPEG that passed on the clip. Any
   gate in a migration must be measured on the views.

**The review's two findings** (HISTORY 13.23). **Alignment:** the tool maps
the five points with `cv2.estimateAffinePartial2D` and LMEDS, which may drop
a point as an outlier; insightface fits all five by least squares. OpenCV's
own `FaceRecognizerSF.alignCrop`, given SCRFD's points in YuNet's row layout,
is that least-squares fit onto the same 112 px template — pixel-identical to
it on all 146 views. LMEDS differs on 19 views, cosine as low as 0.57, though
the totals barely move (sure right 88 → 89 at 0.40). The switch uses
`alignCrop`. **Only two people:** the gallery's seven unnamed entries, 22
views, all match Izabel best under ArcFace, up to 0.546. Three of them, 11
views, show a woman with long loose hair, who could have been a third person
that ArcFace confuses with Izabel. **The user's answer: all 22 are Izabel**,
the long-haired ones with her hair down. So they are 22 more test views of
her, the hardest ones. Matched against the clean Chosen, ArcFace (0.30 /
0.40) gets 8 sure right, 10 maybe right, 4 none and nothing wrong. SFace
(0.363 / 0.45) gets no sure match, at most 5 maybe right, and two "probably
Gustavo" (0.405, 0.385). There is still no stranger to measure, because the
gallery holds none.

**Cost.** The scan embeds every frontal face of every sampled frame — up to
360 frames a clip, 300 of them dense where a person was seen (12.9). About
120 ms a face instead of 20 makes a long person event's scan seconds longer.
It runs off the live path (10.1) and pauses while a camera records, but step
2 measures it on real clips.

**Licences**, the user's to weigh. InsightFace's code is MIT; its pretrained
models, buffalo_l included, are "for non-commercial research purposes only",
and since 24/11/2025 its README sends licensing of its open recognition
models to recognition-oss-pack@insightface.ai (read 14/10/2026). AdaFace's
code is MIT and its weights were trained on WebFace12M (research only).
MagFace's code is Apache-2.0 and its weights were trained on MS1MV2 (research
only). YuNet and SFace are MIT and Apache-2.0.

**Filling `models/bench`** (ignored by git, about 1.7 GB with the downloads):
`buffalo_l.zip` from
`github.com/deepinsight/insightface/releases/download/v0.7/buffalo_l.zip`,
unzipped into `models/bench/buffalo_l/`; `antelopev2.zip` (361 MB) from the
same release into `models/bench/antelopev2/`; `meanshape_68.pkl` from the
insightface repository (`python-package/insightface/data/objects/`); AdaFace
IR-101 from `huggingface.co/minchul/cvlface_adaface_ir101_webface12m` and
MagFace iResNet50 from its README's Google Drive link, each exported once to
ONNX in a throwaway venv with PyTorch 2.14 CPU (`torch.onnx.export`,
`dynamo=False`, opset 17, strict weight loading) as
`models/bench/adaface_ir101_webface12m.onnx` and
`models/bench/magface/magface_iresnet50.onnx`.

**Step 2: R100 measured, R50 kept (developer 21, 14/10/2026).** The bench
gained `antelopev2`'s ArcFace R100, trained on Glint360K
(`scrfd320+glint`); its SCRFD is buffalo_l's file byte for byte, so only the
recogniser differs. Every ArcFace, AdaFace and MagFace pipeline now aligns
with `alignCrop`. The seven unnamed entries, 22 views of Izabel by the user's
word, are probes and never references; the second sweep adds them to the
clean 134.

| SCRFD at 320 + | Clean 134: no wrong from → right | Clean + 22: no wrong from → right | The 22 at 0.30 / 0.40: sure / maybe / none | Closest cross pair | Embed ms | MB |
|---|---|---|---|---|---|---|
| **ArcFace R50** (`w600k_r50`) | **0.275 → 125** | **0.275 → 144 of 156** | 8 / 10 / 4, nothing wrong | **0.313** | **70** | 182 |
| ArcFace R100 (`glintr100`) | 0.350 → 114 | 0.350 → 126 of 156 | 8 / 11 / 3; two maybe wrong on the clean set at 0.30 | 0.562 | 129 | 265 |
| stored SFace, before | 0.375 → 110 | 0.425 → 103 of 156 | 0 / 4 / 16, 2 maybe wrong | 0.498 | — | 37 |

The rule was R100 only if clearly more right at zero wrong; it is the other
way round, and R100 is twice as slow. **R50 it is.** The sweep on clean + 22:
0.25 gives 151 right and 1 wrong, 0.275 144 / 0, 0.30 139 / 0, 0.40 97 / 0.
Hence `MATCH_THRESHOLD` 0.30 and `LEARN_THRESHOLD` 0.40 (10.2) — with no
stranger in the data, erring towards fewer sure matches.

**The migration: a new file, so a rollback still reads the old one.** The
embeddings go from 128 to 512 numbers — not additive (19.1). So the gallery
moved to a new file, `faces/gallery_arcface_w600k_r50.json` (`GALLERY_FILE`,
the model's name in the file name and in a `model` field), and
`faces/gallery.json` (`LEGACY_GALLERY_FILE`) is **never written** by this
version: `v2026.10.13`, restored by an automatic rollback, finds it as it
was. `migrate_gallery()` runs in `cameras.main()`, after the `HOLD` and
already-running checks and before the web and the cameras, **holding a lock
file** (R52, below):

1. It copies both files to `backups/faces_arcface_w600k_r50_<stamp>/`.
2. `refit_entry` embeds every chosen and waiting view again from its photo
   in `faces/views/`, keeping ids (so the sightings in `faces/<day>/` still
   point right), names, favourites, residents and thumbnails.
3. A view with no photo, or where SCRFD finds no face, leaves the new file;
   its photo stays on disk. A person left with no chosen view gets waiting
   ones moved up. An unnamed entry left with nothing is dropped; a named one
   is kept, even empty, so its name survives.
4. It writes through `<file>.part` and a rename, with `"source": {"file",
   "sha1"}` of `gallery.json`. `Gallery.save` keeps every top-level key
   besides `people`, so `source` survives every later save.

It runs again only when `gallery.json`'s SHA-1 changes, which only an older
version can do — after a rollback. Then **the most recently used gallery
wins**: what the user did on the old version is kept, and the replaced new
file, with whatever the new version learned before the rollback, is in the
backup. Merging the two is not attempted: the old file cannot say which of
its differences are new. What a rollback loses: views and unnamed entries
the new version learned (their sightings then read "?"), and photos of views
deleted on the new version (the old file still lists them: a broken image).
Nothing becomes unreadable.

**One copy at a time, and its line in the log (R52, 14/10/2026).** Review 23
found two gaps. The migration ran before `log.to_file()`, and production runs
under `pythonw.exe` with no console, so its line — views kept, "no face",
entries dropped, the backup folder — was written nowhere: the one record of
a non-additive change to the user's data was lost. And the port is what
keeps a second copy out (18.7), but for the ~25 s of a migration nothing held
it: the 5-minute task trigger or a click on `jarvis.bat` passed the
already-running check and migrated too. Now `migrate_gallery` holds a
`filelock.FileLock` on `gallery_arcface_w600k_r50.json.lock`, beside the
gallery, for the whole hash check and rebuild (`_migrate`): a second copy
waits on the lock, then finds the source's hash unchanged and returns None,
and exits at `web.start()` as before. `cameras.main()` keeps the result and
logs it right after `log.to_file()`. The lock is the operating system's
(`msvcrt.locking` on Windows), so it is seen by every process, released if
the holder dies, and its file is removed on release — none is left in
`faces/`. `filelock` 4.1.2 is pure Python, no `.pyd` or `.dll` (PROCESS 5.3);
production gets it through `uv sync` (PYTHON 42). The developer forced a
migration on the test copy and started two copies a second apart: one
migrated, the other waited and did nothing, and the line was in
`logs/jarvis.log`.

A bad-detection report taken before the switch holds 128-number embeddings:
Undo restores its photos first, and `put_back` embeds the entry again from
them (`refit`; since 15/10/2026 a dog entry of histograms too, section 20).
`refit` runs **before** `_GALLERY_LOCK` is taken, because a scan holds
`_SCAN_LOCK` and then takes the gallery lock — the opposite order would
deadlock (PYTHON 41).

**The dogs migrate the same way (R53 step 2, 15/10/2026).** The code is
shared, not copied: `migrate_gallery(target, source, backup_dir, model=,
refit=)` and `refit_entry(entry, folder, tally, embed=)` take the model's
name and the function that rebuilds an entry or embeds one photo, and
`dogs.migrate_gallery` passes its own (section 20) — functions passed as
values, PYTHON 43. The backup folder is now `<gallery folder>_<model>_<stamp>`:
still `faces_arcface_w600k_r50_…` for faces, `dogs_dinov2_small_…` for dogs.
`embed` receives the **old** embedding too, which the faces ignore and the
dogs read for their infrared flag. One consequence the review noted: since
`dogs.migrate_gallery` calls `faces.migrate_gallery` by attribute, a test
that replaces the faces' function replaces the dogs' too. `cameras.main()`
runs the faces' migration and then the dogs', and logs each line after
`log.to_file()`.

**Measured on the M900.** A copy of production's `faces/` on 14/10: 10
entries, 173 views, 173 kept, nothing dropped, 24 s with production running
beside (32 s in review 23, with another measurement running too). The test
copy's `gallery.json`, from 29/09, before views had photos, kept none of its
25 views: the two named people stay, empty, and the five unnamed entries go.
**Any installation with views that have no photo loses those views** — the
development PC's may be one.

**What the scan costs** (`scan_clip` on four production clips, dense over the
whole clip, old code against new): 52.4 → 66.6 s for 110 face views, 13.9 →
17.7, 27.9 → 32.0 and 11.6 → 12.8 s — about +0.13 s per face view (SCRFD 57
ms and ArcFace 70 ms against SFace's ~15), +8 % to +27 % a clip, 0 faces
without landmarks. **What it recognises there:** no view's best named match was
the other person, in the developer's check and again in review 23's. Sure matches are rarer on clips than on the stored views:
Gustavo's daytime clip has 4 of 39 views at ≥ 0.40 (dense sampling, review
23), and the scan recorded him "probably", at 0.349 — the group's heaviest
view, not its best (0.421). Since R51 the best view decides (10.3).

### 10.15 The sure threshold is the user's (backlog 32, 14/10/2026)

**What the user asked** (13/10): with a measurement they set the threshold;
without one, the "probably" stays as it is. So Settings → Detection has a
panel, "Face recognition: when a name is sure", with a table measured on the
user's own named photos and a radio button per row.

**What the threshold decides — four places.** It is stored as the optional
`face_sure_threshold` in `config.json` (0.30–0.60, `FACE_SURE_RANGE`; the low
end is `MATCH_THRESHOLD`, below which nothing is a match at all), and
`faces.learn_threshold(values=None)` returns it, or `LEARN_THRESHOLD`, now
`settings.DEFAULTS["face_sure_threshold"]`, when it is absent or invalid:

1. `notify.person_case`: a resident at or above it is `resident_person`,
   below it `probable_resident_person` (22.2);
2. `notify._who`: "Gustavo recognized" or "probably Gustavo";
3. `_scan_clip`: a match at or above it **teaches** the gallery that view
   (`reinforce`), read once per scan;
4. `Gallery._absorb`: naming a person **merges** every unnamed entry that
   reaches it — and a merge cannot be undone (backlog 9).

So a lower threshold names more and learns more on its own, and gathers more
when naming. The panel says so.

**The table — `faces.accuracy(gallery, thresholds)`.** Leave-one-out over the
named people's **Chosen** embeddings, as matching uses them: the rows are
normalised and one matrix product gives every pair's cosine (PYTHON 43); each
probe's own row and its exact copies — cosine ≥ `COPY_SIMILARITY` 0.9999 —
are masked out, and the best remaining reference decides the name, as
`Gallery.match`'s max over views does. Per threshold of `SURE_SWEEP` (0.300
to 0.600 by 0.025), plus the current value: how many views would be named
for sure, how many to the right person and how many to the wrong one, and how
many views of unnamed entries would cross it toward someone named.
`GET /api/accuracy/faces` answers the table with `current`, `default` and
`range`; the choice is saved through `POST /api/settings`, validated by
`_clean` and rounded to three decimals.

**Production's table on 14/10** (developer 23, read-only on
`C:\JARVIS\faces`): 80 Chosen views of the two residents, no unnamed entry,
**no wrong answer at any threshold**:

| Threshold | 0.30 | 0.35 | 0.40 (default) | 0.45 | 0.50 | 0.55 | 0.60 |
|---|---|---|---|---|---|---|---|
| Named for sure, of 80 | 77 | 73 | 66 | 39 | 23 | 12 | 4 |

**What it cannot measure, and why it is optimistic.** A stranger has no name,
so the table shows confusion between the people the user named, never with
strangers; the Unnamed column is the only hint, and the page says so. And
only exact copies are left out: the views of one event are consecutive
frames of the same face, not copies, so a probe's twin from its own event is
still among the references and makes the match look surer than a new event
would. The closest pair of the two residents is 0.313 (10.14) — a threshold
near 0.30 is where a leave-one-**event**-out could find wrong answers this
table cannot. Views do not record their event; R55 (BACKLOG 2) is that
measurement.

---

## 11. Tiered storage — `archive.py`

### 11.1 Three tiers, deletion last

```
clips/ (the program's disk)  --30 days-->  external drive  --only when full-->  delete the oldest
```

**Nothing is deleted from `clips/`.** What was recorded leaves only by being
moved to the archive. Deletion exists only on the external drive, of the
oldest event, and only when free space falls below the limit.

The rejected alternative was deleting by age straight from the recordings. At
~300 MB a day the disk would fill, but deleting recent material to solve that
trades one problem for a worse one.

### 11.2 Copy, check, then delete

Moving between disks is not atomic. `_move_event()` copies every file of the
event, **checks the size of each**, and only then removes the originals.

An interrupted copy — the drive unplugged halfway — leaves the original
intact and deletes what had already gone. Better a duplicate than a gap.

Tested by simulating a failure on an event's second copy: the original stays.

### 11.3 The drive unplugged

It is the normal case, not the exception: an external drive spends most of its
time unplugged. `destination_state()` answers whether it can be written now,
and every operation stops at once if not, deleting nothing and saying why.

### 11.4 Configuration on the page

**Settings → Archive** shows the three tiers with real numbers — how many
events, how much they take, how much is left on each disk — with a field for
the folder (on the M900 itself), the age to move and the free-space floor. The
old window used a native folder dialog through `tkinter`; the web page takes
the path as text, which is why the field says "Folder on this computer".

The choices live in `config.json` at the root, **not** in `.env`. The split is
on purpose: `.env` holds credentials written once by hand, while this changes
at run time from the page. `config.json` is not versioned.

| Key | Default | What it does |
|---|---|---|
| `archive_path` | empty | The external drive's folder; empty turns archiving off |
| `archive_after_days` | 30 | The age to move |
| `archive_min_free_gb` | 10 | Below this, delete the oldest on the drive |

Production's `archive_path` is empty (checked 12/10/2026): nothing is archived
yet, and nothing is deleted.

### 11.5 When it runs

`Housekeeper.tick()` is called from the main loop and acts only every
`CHECK_SECONDS = 1800`. Events younger than `PROTECT_MINUTES = 10` are never
touched, because the clip's assembly happens in a thread and may still be
running.

### 11.6 One writer at a time, and the whole file (R43, 12/10/2026)

Since 12/10 two threads write `config.json` — the page and the Telegram bot
(`/home`, 22.5) — and `settings.update` is a read-modify-write. Two of them
interleaving lose one change (a *lost update*); a read that lands inside a
write sees a truncated file (a *torn read*), `_stored()` answers `{}`, and an
update that starts from it saves the defaults: the token, the chat, the PIN
and the archive path erased, silently. Reproduced with two writers and a
reader, 200 rounds each: the reader saw the token gone about 190 times in 200.

Two classic pieces fix it (PYTHON 31). A module `threading.RLock`, held by
`update` from the read to the write and by `save`. And the file is never
rewritten in place: `_write` writes `config.json.<pid>.<thread>.tmp` beside it
and `os.replace`s it, so a reader gets the old file or the new one. On Windows
a file open in one thread cannot be replaced, nor opened while it is being
replaced, so the replace and the read both retry `PermissionError`
50 × 10 ms. With the lock and the replace alone the reader still lost the
token 3–13 times; with both retries, 8 runs of 8 were clean. `load()` takes
no lock: it relies on the atomic replace and the read retry. The temporary
name is in `.gitignore`, so a copy left behind by a crash, which holds the
token, never reaches a commit.

---

## 12. Notifications — `notify.py`

### 12.1 Why Telegram

Without a notification the system answers *"who was here?"* and never *"is
someone there now?"* — it is a recorder, not surveillance.

| | Telegram | E-mail | Windows toast |
|---|---|---|---|
| Reaches the phone | immediate push | inbox | no |
| Sends the thumbnail | yes | attachment | no |
| New dependency | none | SMTP + an app password | — |
| Exposes the machine | no | no | — |

The API is plain HTTP and sending uses `requests`. The first version used the
standard library's `urllib` and built the photo's `multipart/form-data` by
hand, in twenty lines, so as not to bring in a new dependency. That was a
mistake — see 12.5 and PROCESS 5. Receiving commands uses the same API in
the other direction, by long polling (22.5).

### 12.2 Notify at the start of the event, not at the end

The notification fires in `_start()`, on the first frame with a detected
subject — not when the clip closes. The difference matters: closing the event
waits for the person to leave plus `POST_SECONDS`, and assembly takes a few
more seconds after that. Notifying at the start, the message arrives while the
person is still there.

The cost is not having the face's name, which only comes from the post-event
scan. For "is someone there", knowing at once is worth more than knowing who.
The "who" comes later, in a second message (12.7). **Since 12/10/2026** a mode
that leaves anyone out holds the person's message until the scan, so it can
say who it was (22.3); Away keeps this immediate message.

### 12.3 Silence is mandatory

Two locks prevent the flood that would make the feature unbearable:

- **What is sent at all.** `notify_labels` started as `["person"]`: animals
  did not notify, or every cat at dawn would become a message. Since 12/10/2026
  each mode has a switch per case (22.2), built from `notify_labels` at first.
- **A minimum interval per camera.** `notify_cooldown = 120` seconds, counted
  **per camera**: someone walking about in front does not make twenty
  messages, but an event on Back during Front's quiet still gets through.
  Faces have their own per-person interval (12.10).

### 12.4 It never stalls capture

Sending runs in a thread. A slow network or Telegram being down cannot hold
the capture loop, and every failure comes back as `(False, reason)` instead of
an exception.

### 12.5 The missing certificate root

On the first attempt to validate the token, this:

```
[SSL: CERTIFICATE_VERIFY_FAILED] self-signed certificate in certificate chain
```

It looked like an antivirus intercepting HTTPS. **It was not.** `github.com`
and `google.com` verified normally — only Telegram failed.

The chain `api.telegram.org` presents ends at **"Go Daddy Root Certificate
Authority - G2"**, and this machine's store had only **Starfield** roots. The
Go Daddy G2 root was not installed.

The browser works because **Windows downloads missing roots on demand**,
through CryptoAPI itself. Python does not trigger that mechanism:
`ssl.enum_certificates` only sees what is already cached locally. Loading
Windows' whole store went from 39 to 52 CAs and still failed, because the root
simply was not there to load.

The fix is `certifi`, Mozilla's set of roots — 121 certificates, the Go Daddy
G2 among them. It is a data file, not code, and it guarantees the same
behaviour on both machines instead of depending on what each Windows decided to
download.

**Two lessons, and the second matters more than the first.**

The first: an SSL error does not necessarily mean interception. Test another
site before blaming an antivirus.

The second: **this problem should never have existed.** `requests` already
depends on `certifi` and uses it by default —
`requests.utils.DEFAULT_CA_BUNDLE_PATH` points at `certifi.where()`. The bug
only appeared because the first version avoided `requests` to keep the
dependency count low, and that count was never the user's decision. The real
cost of that saving was not the twenty lines of `multipart` — it was a whole
session of TLS debugging to reinstall, by hand, a guarantee the library gives
for free. Sending today uses `requests` and does not import `certifi`
directly.

### 12.6 Configuration

**Since 12/10/2026 this lives on the web page, in Settings → Notifications** (22.4);
the OpenCV window and its config editor are gone (17.10):

1. **Bot token** — paste the token from `@BotFather` and save; the page never
   shows it back, only whether one is set
2. Send any message to the bot in Telegram
3. **Find chat** — takes the chat of the last message the bot received and
   saves it. While production's command poller runs, the chat comes from what
   the poller saw, since a second reader would steal its messages (22.5)
4. **Send test** — confirms it reaches the phone

What is sent, and when, is the active mode's switches on the same tab (22.2).

`config.json` is not versioned, and the token is a credential: whoever has it
can send messages through the bot.

### 12.7 The second message: the face and the name

The user's request on 09/10/2026: besides the event's thumbnail, the photo of
the face alone and, if the person is known, the name in the message.

The face only exists after the event — the clip has to close, be assembled and
be scanned (10.1), some 20 to 40 s after the person appears. So it cannot go
in the first message without delaying it, and 12.2 still holds:

| Message | When | Photo | Text |
|---|---|---|---|
| 1st | on the first frame with a person | the event's thumbnail, with the box | `Back: person` and the time |
| 2nd | after the face scan | the face's crop (10.10) | `Back 15:20:54: <name> recognized`, `probably <name>` or `unknown face` |

One photo per person found in the clip, at most `MAX_FACES = 3`.

**The path.** `EventRecorder._start()` keeps what `notify.event()` returned
in `self.notified`, and that value travels with the assembly thread, which
calls `notify.after_scan()` once the scan returns (22.3). `scan_clip()`
returns, besides what it writes into the sighting's JSON, the photo's path
(`thumbnail_path`), the person's current name (`name`, empty if nobody gave
one) and whether they are a resident. The name comes from the gallery at that
moment, so someone named yesterday appears with a name today.

**How the second relates to the first** changed twice. At first it only went
out if the first had; since R25 (12.10) a face goes out even when its event
fell in the camera's cooldown, with a cooldown per person instead, so a face
is never lost to a busy camera. Since 12/10/2026 the active mode decides each
face by its case (22.3).

**It stalls nothing.** The post-scan messages run on the clip's assembly
thread, which is already in the background and already waits for the scan;
the capture loop never sees the network.

Tested on 09/10/2026 with two clips of 29/09 and a copy of the gallery: both
messages arrived, one naming the user and another naming Izabel, each with the
face's crop.

### 12.8 A person who arrives after an animal, and other changes (09/10/2026)

**The bug (review 1, R1).** The notification was attempted only on an event's
first frame, with that frame's labels. An event that began with a dog was not
announced — only `person` notifies — and nothing tried again, so a person
arriving seconds later passed in silence, and never got the face message of
12.7 either, which depends on the first message having gone out. On 30/09, 29
of the 85 events with a person also had an animal.

**The fix.** `EventRecorder.update()` calls `_notify_late()` on every frame of
an open event. While the event has not been announced, each label not yet
tried gets **one** attempt — so `config.json` is not read every frame:

```python
new = {s.label for s in subjects} - self.notify_tried
```

The photo is of that moment, not the event thumbnail (which shows the dog),
saved as `HH-MM-SS.alert.jpg`; if nothing was sent, it is deleted. The name
matters: see 19.2.

**Wording (R5).** The face message says `X recognized` only when the match is
at least `LEARN_THRESHOLD` (0.40) — the bar the gallery already trusts to learn
from (10.4). Between `MATCH_THRESHOLD` (0.30) and 0.40 it says `probably X`;
no name, `unknown face`. Messages are in English since 09/10/2026 (CLAUDE.md).

**`notify_prefix`** in `config.json`, empty by default, is put in front of every
message. The test copy uses `[TEST]` (18.7).

### 12.9 The picture, the face that passes fast, and a trace of every message (10/10/2026)

Developer session 1 answered what the first night of production showed
(HISTORY 13.6): the user went out and came back, was recorded, and still
believed they were not, because the event's picture was the dog and no face
message came.

**The event's picture is its best view of a person (R19).** While an event is
open, `EventRecorder._consider_view()` keeps a copy of the frame where a person
scores best, `confidence × box height` — height so that a person standing beats
a dog lying down even when the detector calls the dog a person. At the end it
is written as `HH-MM-SS.best.jpg`, and the event JSON gains the optional
`best_thumbnail`. The page shows it when present; older events, and events with
no person, keep showing the first frame, which is also kept on disk because it
shows what triggered the event. `frame.copy()` matters: a numpy array is a
reference to a buffer the capture keeps reusing.

**The phone ends with a picture of the person.** The first message still goes
at the start with the first frame — speed beats beauty there. After the clip
is scanned, a notified event gets either the face messages (12.7) or, when no
face was found, one more message with the best view — unless the best view is
the very frame already sent.

**Faces that are frontal for a fraction of a second (R20).** On the 22:29 clip
only 4 or 5 of ~840 frames held a face that was both frontal and at least
36 px wide, and one frame in fourteen missed them all. The recorder now notes
the wall-clock spans when a person was seen (a gap over
`PERSON_GAP_SECONDS` = 2 opens a new span); `_assemble` turns them into
seconds into the clip, counted from the first segment's name, which is the PC
clock at the moment ffmpeg opened it — the same clock the spans use. The scan
then reads every `DENSE_EVERY` = 2nd frame inside those spans widened by
`DENSE_MARGIN_SECONDS` = 1.5, plus the old sparse pass elsewhere, at most
`MAX_DENSE_SAMPLES` = 300 extra frames. All of it is one ffmpeg `select`
expression — `n` is the frame number, `t` its time, `+` is a logical or:

```
not(mod(n\,14))+(between(t\,34.50\,45.50))*not(mod(n\,2))
```

Measured on the M900 on that clip: sparse, 60 frames, 12 s, no face; dense,
300 frames, **45 s**, the user found as "probably" (41 px, 0.421). YuNet costs
~143 ms per 1080p frame there. `tools/rebuild_faces.py` does not know the
spans, so a rescan stays sparse. **Open:** what 45 s of multi-threaded DNN
does to live analysis on 4 cores (R21).

**Every message leaves a line in the log (R16).** `Notification <camera>
<labels>: sent` and `skipped: cooldown` at INFO, `failed: <detail>` at
WARNING, so a check for warnings finds a failed send. `_allowed()` became
`_wanted()` and `_cooled_down()` to tell the two skips apart; a label nobody
asked for stays silent. **The token never reaches text:** a `requests`
exception quotes the URL, and the URL holds the token (`/bot<token>/…`).
`_redact()` removes it inside `_call()` and `discover_chat()`, the only places
the token can enter a string, so no caller has to remember.

### 12.10 Watching the watcher (10/10/2026)

Developer session 2 added the instruments that 12.9 lacked.

**Frames analysed per minute (R21).** The `Core` counts analysed frames per
camera; every 60 s `_tally()` turns them into `analysed_per_minute`, served by
`/api/status`, and logs the numbers when a face scan ran in that minute
(`faces.scanning()` asks `_SCAN_LOCK.locked()` — whether a lock is held,
without taking it). Measured on the M900: a quiet scene barely notices a dense
scan (584 → 575–583 frames a minute), but **YOLO runs 1.6× slower during one**
(280 → 454 ms), because every `cv2.dnn` network in the process shares one pool
of worker threads. Giving the scan fewer threads does not help:
`cv2.setNumThreads` is process-wide and slowed YOLO itself (472 ms at 2
threads, 772 ms at 1). The decision is in HISTORY 13.8 (R23).

**Where each scan looked (R22).** One INFO line per scan:
`face scan 22-29-22.mp4: dense 7.3-15.7 s, 36.3-42.1 s, 162 frames, 23.1 s, 3 face view(s)`.

**`tools/replay.py` (R17).** Plays any video through the real
`MotionDetector` and `SubjectDetector` and prints why each candidate was kept
or dropped. Both classes gained an optional `trace` list, `None` by default —
when nobody set it, nothing is recorded and nothing changes (the Python version
of an optional listener in Java); the old and new code gave identical results
on all 561 frames of the 22:29 clip. `SubjectDetector.detect()` gained an
optional `now`, so `MIN_INTERVAL` and the static spots follow the video's
clock instead of the wall clock. The reasons are the clearest list of what each
layer filters: too small, few changed pixels, lighting change, not confirmed
(n/3), whole frame changed, warming up; animal below confidence, person too
short, no motion overlap, duplicate, static spot; since backlog 31 also
person below confidence (7.14). `--prime` teaches MOG2 the
background from the first 6 s first, because a fresh MOG2 is blind for 6 s —
exactly where an event's pre-roll ends. The primed background already holds
whatever was in the scene, which production's long-learned one would not:
good enough to reproduce an event, not identical to production.

**The running version (backlog 18).** `web._read_version()` runs
`git describe --tags --always --dirty` once at startup: production shows its
tag (`v2026.10.10`), the test copy something like `v2026.10.10-12-g1b8822d`,
"12 commits after that tag" — which also tells the two pages apart. Served as
`version` in `/api/status` and shown muted at the right of the header;
`unknown` if git cannot answer, never an error.
**The scan steps aside during events (R23, 10/10/2026).** Before each frame,
`_scan_clip()` calls `_wait_while(busy, budget)`: while `busy()` is true it
sleeps in 0.2 s steps, at most `MAX_PAUSE_SECONDS` = 600 per scan, and the
ffmpeg feeding the pipe simply blocks. `busy` is a function passed in —
Java's `BooleanSupplier`, C#'s `Func<bool>` — so `faces` knows nothing of
cameras: `clips.recording_now()` asks every `EventRecorder`, kept in a
`weakref.WeakSet` (a set that does not keep its members alive, like the keys of
Java's `WeakHashMap`). Measured: YOLO 328 ms alone, ~590 ms during a dense
scan, **342 ms while the scan is paused**. A paused scan still holds
`_SCAN_LOCK`, so on a long busy evening the face messages arrive late; the
first message of each event never waits.

**The dog on the mat (R18).** `SubjectDetector.detect()` drops a `person`
whose box is more than `WIDE_PERSON_RATIO` = 2.0× wider than tall **and**
whose bottom lies within `BOTTOM_EDGE_FRACTION` = 3 % of the frame's bottom
(`people.wide_at_bottom()`, trace reason "wide at the bottom edge"). Both
conditions: a wide box mid-frame could be a person lying down, and a standing
person whose feet touch the edge is always tall. The architect had specified
2.5; the replay of all 25 person events showed the dog **sitting up** on the
mat at 2.42–2.48, so 2.0 — real persons measure 0.4–0.6, still a fourfold
margin. Every box the rule drops in those events is the mat.

**A found face is always announced (R25, 10/10/2026).** The face message used to go out only after the event's own first message, so a face found in an event that fell in the 120 s cooldown was never sent — and faces are rare (2 of 21 scans that afternoon). Now `faces_seen` runs whenever the scan found a face; `_cooled_down(key, settings)` takes any key, the camera for events and `("face", person_id)` for faces, in the same table, so the same person is not announced twice within `notify_cooldown`. The best-view follow-up keeps its rule: only after a sent event.

---

## 13. An important limit of the Tapo cameras

**The camera supports only two of these three functions at once:**

1. Tapo Care (cloud)
2. Recording to the SD card
3. NVR / NAS / ONVIF / **RTSP**

With Tapo Care + SD on, RTSP is switched off silently. The symptom is odd:
`DESCRIBE` answers `200 OK` normally (it is only metadata), but `SETUP` closes
the connection without even asking for authentication.

**Turning recording off in the app is not enough — the card has to be removed
physically.** The alternative: turn Tapo Care off.

`probe_rtsp.py` diagnoses it by showing each step of the handshake:

```
uv run python tools/probe_rtsp.py <ip> <user> <password> stream1
```

---

## 14. The icon and the shortcut

**A `.bat` has no icon of its own.** Windows draws a file's icon by its type,
and every `.bat` uses the same one. What can have an icon is a **shortcut**
(`.lnk`), which points at the `.bat` and keeps the path of an `.ico`.
`tools/create_shortcut.ps1` creates that shortcut on the Desktop through the COM
object `WScript.Shell` — the same one Windows uses for "Create shortcut".
`install.bat` runs the script in its step 6.

**The icon is code.** `tools/make_icon.py` draws a robotic eye with NumPy,
with no drawing program:

| Layer | How |
|---|---|
| Steel casing | A circle whose brightness varies with the angle (`cos`), simulating light from the top left |
| Segmented ring and screws | 12 sectors alternating by angle; 12 small circles |
| Iris | A radial gradient from near-white cyan in the centre to blue at the edge, with 36 rays and two thin rings |
| Pupil | A 6-blade shutter: the radius grows within each sector, which gives the helical outline |
| Highlight | A white circle off centre |

Each layer is a **mask** from 0 to 1 per pixel, computed at once over the
whole image from two maps: each pixel's distance from the centre and its
angle. `edge()` turns "inside the circle of radius R" into that mask, with a
2 px transition so the edge is not jagged. In Java it would be a double loop
over x and y; here each line works on the million pixels at once.

The drawing is made at 1024 px and reduced with `INTER_AREA` to the 7 sizes
Windows uses (16 to 256). The `.ico` is written by hand: a 6-byte header, a
16-byte entry per size, and each image as PNG — the format Windows accepts
since Vista. OpenCV reads and writes PNG but not `.ico`, and `struct.pack`
does it in ~20 lines.

Pillow would do it in two lines. It is kept by hand because it is a
single-use tool, off the critical path and already tested — not to save a
dependency (PROCESS 5). If Pillow comes in for another reason, switch.

To change the drawing, edit the colours and radii in `make_icon.py`, run
`uv run python tools/make_icon.py` and then `create_shortcut.ps1` again
(Windows caches icons; if the old one keeps showing, restart Explorer).

---

## 15. The core and the interface — surveillance without a window

### 15.1 The problem: recording rode on the window

Until 09/10/2026 `main()` was a single loop, and the window set its pace:

```python
key = cv2.waitKey(15) & 0xFF
...
if cv2.getWindowProperty(WINDOW, cv2.WND_PROP_VISIBLE) < 1:
    break
```

`cv2.waitKey` is not just "read a key" — it is the function that pumps
HighGUI's event queue, and it set the beat of everything else. Detection,
recording, faces and notifications ran **inside** that loop. Closing the
window ended the surveillance.

For a camera viewer that was right. For a security system it is not: nobody
keeps a window open 24 hours a day, and it is precisely when nobody is looking
that recording matters most.

### 15.2 The separation

`cameras.py` got separate pieces, and the dependency points one way only:

| Piece | What it is | Knows about the interface? |
|---|---|---|
| `Core` | capture, motion, subjects, recording, archive | **no** |
| `run_headless` | only calls `Core.step()` in a loop | no |
| `run_window` | drew, read the keyboard and mouse — **removed 10/10/2026** | yes |

`Core.step()` is one pass over every camera and returns `True` if any frame
was new. Today `main()` is:

```python
core = Core(start_cameras(env))
web.attach(core)
bot.start()
...
try:
    run_headless(core, stop)
finally:
    bot.stop()
    web.stop(server)
    core.close()
```

The `finally` is what guarantees a pending clip is assembled and the streams
closed, whatever the reason for leaving — `Ctrl+C`, `--stop` from the web, or
an exception. The web server was started before the cameras, holding the port
(R2, 18.8), and is handed the `Core` with `attach`.

**A Python detail:** functions are values, as with a C# delegate, without
declaring a type. The old `main()` chose the loop with
`(run_headless if headless else run_window)(core)`; the parentheses around the
conditional are required, or the ternary `if` would swallow the call.

### 15.3 The pace, without waitKey

Without a window there is no `waitKey`, so the loop needs a pace of its own:

```python
while not stop.is_set():
    if not core.step():
        time.sleep(IDLE_SLEEP)
```

It sleeps **only when no new frame came**. If one did, it processes the next
pass at once. That is better than the old loop, which paid `waitKey`'s 15 ms on
every iteration, frame or not. Measured: 2,995 passes in 15 s, 300 with a new
frame — that is, 10 fps per camera, and the rest of the time asleep instead of
spinning. `stop` is a `threading.Event` the web sets on `--stop` (PYTHON 24).

### 15.4 `draw`, and what it saves

The `Core` builds panels only if `draw=True`:

```python
self.panels = {cam.label: make_panel(None, cam.label, PANEL_HEIGHT)
               for cam in streams} if draw else {}
```

Measured on the development PC: `make_panel` costs **0.43 ms per camera** and
the mosaic (`np.hstack`) **0.41 ms**, **1.27 ms** in all with two cameras, of
about 20 ms per frame. About 6 %. Worth saving, but **not the reason for the
change** — the reason is 15.1. The service runs with `draw=False`; the live
view on the page builds its panel only when a browser asks (17.7).

### 15.5 How to run it

| Want | Command |
|---|---|
| Use J.A.R.V.I.S. | `jarvis.bat` or the shortcut: service + browser (17.7) |
| Only the service, opening nothing | `jarvis_headless.bat` (`--headless`; the old `--sem-janela` still works) |
| Stop it from any terminal | `uv run python -m jarvis --stop` |
| See it in a browser or on a phone | `http://127.0.0.1:8765`, or the network address it prints |

`--window` (and `--janela`) only log the page's address since the window was
removed. `Ctrl+C` in the terminal becomes `KeyboardInterrupt` in Python, which
`run_headless` catches; `--stop` asks through the web and the loop leaves the
same way. In both cases `main()`'s `finally` closes everything in order.
Production runs as a scheduled task with no console, started with Windows
(18.7).

---

## 16. Current state

**Running in production on the M900**, release `v2026.10.12` (12/10/2026):

| What | Section |
|---|---|
| Capture by ffmpeg, recording without re-encoding, connection timeout | 5 |
| Motion with the lighting filter, the clock mask and temporal confirmation | 6 |
| People and animals by YOLO, static scenery, minimum height, the dog on the mat | 7 |
| Events with pre-recording, thumbnail, best view and metadata | 8 |
| Faces: frontal and on a person, a name that becomes a reference, the side view | 10 |
| The household's dogs, named by the look of their fur | 20 |
| Tiered storage to an external drive (not configured in production) | 11 |
| Telegram messages with the face and the name, per-camera and per-person intervals | 12 |
| Residents, the Home/Away/Silent modes, commands from the phone | 22 |
| The web page: Live, Recordings with video, People, Dogs, Settings (Notifications first); pairing other devices | 17 |
| Bad-detection reports, with Undo | 21 |
| Production in `C:\JARVIS` as a startup task, reviewed releases, update with rollback | 18 |
| Every file ever written stays readable; `check_data.py` proves it; 160 tests | 19 |

The accepted limitations, the backlog and the plan live in one place:
[CONTEXT.md](CONTEXT.md), sections 7, 8 and 14.4. The bugs already fixed are
in [HISTORY.md](HISTORY.md) 4.

## 17. The web interface

Decided on 09/10/2026 (backlog 3) and finished on 11/10/2026: the web page is
the **only** way in. The user's turn of direction on the first day: *"I don't
want two ways of getting in; if possible everything on the web, with one
service running."* The original plan kept the OpenCV window beside the web to
compare; the window was removed on 10/10 (17.10). The stages were done in the
order 1 → 3 → 4 → remove the window and start with Windows → 2.

### 17.1 Why, in one sentence

Surveillance already ran without a window (section 15), but there was no way
to **look** at a core without a window. The web closes that loop and, in
passing, brings accents, video playback, scrolling, pasting and access from a
phone — everything HighGUI lacks.

### 17.2 The stack, and why not the standard library

**FastAPI + uvicorn.** Two requirements decide it, and neither is about taste:

| Requirement | Why `http.server` will not do |
|---|---|
| Live video (MJPEG) | A response that never ends. `http.server` is single-threaded; one viewer would block everything else |
| Dragging the video's bar | `<video>` needs HTTP Range. `FileResponse` does it; by hand it is easy to get wrong |

The first idea in that session was `http.server` "with no new dependency" —
the bias of PROCESS 5 coming back through the back door, and it was dropped.

**A risk checked:** FastAPI brings `pydantic`, whose core is compiled Rust —
the same kind of binary Smart App Control blocked in PyTorch (7.11). It loads
on both machines (HISTORY 12.2). Had it failed, the plan was Flask with a
threaded WSGI server, pure Python, rather than abandoning the web.

### 17.3 The four stages

Each ended in a commit that worked on its own.

**Stage 1 — the server and the event list.** `web.py` running uvicorn in a
thread beside the `Core`, serving a page that lists the events by reading the
JSON files already in `clips/` (17.6).

**Stage 2 — playback.** `FileResponse` on the `.mp4` files and a `<video>` on
the page: watch an event and drag the bar without an external player (17.13).

**Stage 3 — live.** `StreamingResponse` with MJPEG from the frames the `Core`
already has in memory: both cameras live in the browser, and on a phone over
the local network (17.7).

**Stage 4 — People and Settings.** The screens that suffered most from
HighGUI: where the 46-character token could not be pasted and a name with an
accent could not be typed (17.9).

### 17.4 Decisions already taken, not to be reopened

- **The local network only.** No port open to the internet. The Telegram
  messages are what cross the network; commands from the phone come back the
  same way, by an outgoing connection (22.5). Reading is open to the home
  network (R4); writing needs the M900 itself or a paired device (17.12).
- **The web reads what already exists.** The JSON files in `clips/` remain the
  source. An event database (backlog 13) is independent and comes later, if
  ever.
- **The `Core` does not know about the web.** Just as it did not know there was
  a window: whoever serves reads the `Core`. Stage 3 added two read-only
  accessors to it, `labels` and `live_view()` (17.7) — the `Core` does not
  import `web` and does not change its behaviour because someone is looking.
- **No frontend framework.** Plain HTML and JavaScript are enough to list,
  filter and play video. React here would be the opposite of useful reuse:
  weight with no problem to justify it.

### 17.5 What it closes on the backlog

Items 5 (playback, done) and the remote access came almost for free; 6
(search and filter) and 11 (a timeline) become cheap, because the browser
already does the heavy part of each.

### 17.6 Stage 1, as built

**Acceptance met on the M900:** `http://127.0.0.1:8765` showed the 139 events
of 30/09 (Front 44, Back 95), with thumbnail, time, camera, duration and label.

**Where it runs.** `main()` in `cameras.py` starts the web server before the
cameras (R2) and hands it the `Core` afterwards. The server runs in a
*daemon* thread:

```python
server = uvicorn.Server(uvicorn.Config(app, host=host, port=port,
                                      log_level="warning", access_log=False))
threading.Thread(target=server.run, name="web", daemon=True).start()
```

uvicorn installs its `Ctrl+C` handlers only when it runs on the main thread,
so in a background thread it does not steal `Ctrl+C` from `run_headless`. On
exit, `main()`'s `finally` calls `web.stop()`, which only sets `should_exit` —
uvicorn ends on its own at the next turn of its loop. Being a *daemon*, the
thread does not hold the process either if something goes wrong.

**What it served at first** (the routes were renamed to English on 10/10,
R10):

| Route | Returns |
|---|---|
| `/` | `static/index.html`, with the running version in the asset URLs (17.11) |
| `/static/...` | the page's CSS and JavaScript (`StaticFiles`) |
| `/icon.png` | `assets/jarvis.png`, without duplicating the file |
| `/api/days` | days with recordings, newest first |
| `/api/events?day=YYYY-MM-DD` | the day's events, read from `clips.list_clips()`; without `day`, today |
| `/thumbnail/<camera>/<day>/<HH-MM-SS>.jpg` | the event's thumbnail |

The API returns **URLs, not disk paths**: `_event()` swaps `thumbnail_path`
for `/thumbnail/...`. The page never knows where the files are.

**Nobody leaves `clips/`.** The thumbnail route takes three pieces of the
address. Each must match a strict regular expression (letters and `-`/`_`;
`YYYY-MM-DD`; `HH-MM-SS.jpg`), and the final path, after `resolve()`, must lie
inside `CLIP_DIR` (`is_relative_to`). Tested: five attempts to get out with
`..` and `%2F` came back 404, and an invalid `day` comes back 400. Every route
added since follows the same pattern.

**A busy port brings nothing down.** `_port_free()` tries the port before
uvicorn. If another instance is already serving, the web interface is
switched off with a message and surveillance carries on — the interface is
optional and recording is not. Since R2 the port is taken atomically (18.8).

**The page.** Plain HTML, CSS and JavaScript in `src/jarvis/static/`, no
framework (17.4). The JavaScript fetches `/api/events` and builds the cards
from a `<template>`. The ◀ ▶ arrows jump to the previous or next day **with
recordings**, using `/api/days`. On today's date the list refreshes every 15 s,
and stops when the tab is not visible (`document.hidden`).

Events already moved to the external drive (section 11) are not listed.

### 17.7 Stage 3, as built: live, and one entry point

**Acceptance met on the M900:** both cameras live on the **Live** tab, with
their name, detection boxes and `REC` while recording, at ~8 frames per
second.

**MJPEG.** Each camera is an HTTP response that never ends:
`multipart/x-mixed-replace`, a sequence of JPEGs separated by a boundary line
(`--frame`). The browser swaps the image on each part that arrives, and shows
it in an ordinary `<img>` — no player, no video JavaScript. It is why
`http.server` was dropped (17.2): one viewer would hold its only thread
forever.

```python
yield (f"--{BOUNDARY}\r\nContent-Type: image/jpeg\r\n"
       f"Content-Length: {len(data)}\r\n\r\n").encode() + data + b"\r\n"
```

`_mjpeg()` is an ordinary *generator*; `StreamingResponse` consumes it on a
thread from the server's pool, one per viewer. It sleeps `1 / LIVE_FPS`
between frames and stops when `web.stop()` sets `_stopping` — without that, an
open browser would hold up the program's shutdown. Each viewer encodes its own
JPEGs (R14, open).

**Where the picture comes from.** `Core.live_view(label)` builds the panel **at
the time of the request**, from what the `Core` already has: the last analysis
frame (`stream.latest`), the last detections (`subjects.subjects`) and whether
it is recording. It reuses `make_panel`, which resizes into a new array before
drawing, so the original frame is never touched — important, because it is
read by the web's thread while the `Core`'s loop goes on in the main one.

Nobody looking, nobody pays: the `Core` runs with `draw=False`, and the panel
only exists while a browser asks. The page closes the streams when it leaves
the Live tab or the browser is minimised (`document.hidden`), by removing the
images' `src`.

The camera's label moved down to `LABEL_Y = 62`: at `y = 34` it sat on the
clock the Tapo itself writes in the corner.

**The local network.** `HOST = "0.0.0.0"` listens on every interface, and the
program prints the address for a phone (`lan_address()`: connecting a UDP
socket sends nothing, it only makes Windows choose the outgoing interface,
whose address is ours). The first time, Windows asks in the firewall whether
`python.exe` may receive connections; without allowing it, only this machine
opens the page. The M900's network is classified as **Public**, and the rule
applies to that profile — accepted by the user (R4).

**One entry point.** `main()` in `cameras.py` has two modes:

| Command | Does |
|---|---|
| `python -m jarvis` (`jarvis.bat` and the shortcut) | service + opens the browser on the page |
| `python -m jarvis --headless` (`jarvis_headless.bat`) | only the service; what starts with Windows |

Before opening any camera, `web.already_running()` asks `/api/cameras` whether
a J.A.R.V.I.S. is already serving. If so, the second one does not start: it
only opens the browser (or says so) and exits. Tested: with the service up, a
second launch left in 3 s and the cameras kept the first instance's two ffmpeg
processes. Without it, clicking the shortcut twice would make the second fight
over each camera's single RTSP connection.

**Stopping** from the console is `Ctrl+C`. Closing the console with the X
skips `main()`'s `finally` — Windows kills the process, and a clip being
assembled would be lost. Production has no console at all (18.7).

### 17.8 Current state of the web, after the pre-production delivery (09/10/2026)

17.6 and 17.7 record how stages 1 and 3 were built; some names there have
changed since. This is the current state.

**Routes** (renamed to English while nothing outside the page depended on them):

| Route | Returns |
|---|---|
| `/` | the page |
| `/static/...`, `/icon.png` | CSS, JavaScript, icon |
| `/api/cameras` | camera names; empty while they are still starting |
| `/api/status` | `cameras`, `started` (when this server started), `frame_age` (seconds since each camera's last frame, `null` if none ever arrived); later `version` (12.10), `analysed_per_minute` and `analysis`, `"On"` or `"Off"` (22.7) |
| `/api/days` | days with recordings, newest first |
| `/api/events?day=YYYY-MM-DD` | `{day, events}`; without `day`, today |
| `/thumbnail/<cam>/<day>/<HH-MM-SS>.jpg` | an event thumbnail, same checks as before (17.6) |
| `/live/<cam>` | MJPEG (17.7) |
| `POST /api/shutdown` | clean stop; **only from 127.0.0.1** — the port is open to the LAN, and anyone on the Wi-Fi could otherwise switch the surveillance off. 403 from anywhere else |

**Command line:**

| Command | Does |
|---|---|
| `python -m jarvis` | service plus browser (`jarvis.bat`, the shortcut) |
| `python -m jarvis --headless` | service only (`jarvis_headless.bat`, the startup task) |
| `python -m jarvis --stop` | asks a running service to stop, waits until it is gone |
| `python -m jarvis --window` | the old OpenCV window, temporary |

`--sem-janela` and `--janela` still work as aliases.

**The port is the lock (R2).** The web binds its port before the cameras open,
atomically (18.8), so a second launch during the slow camera startup finds it
taken. `web.attach(core)` hands the `Core` over once the cameras are up; until
then `/api/cameras` answers with an empty list.

**No frozen pictures (R3).** `FFmpegCamera.frame_age` says how old the last
frame is. `Core.live_view()` draws "no signal" instead of a picture older than
`STALE_SECONDS` (5 s): a stopped camera must not look like a quiet scene. The
page asks `/api/status` every 5 s; if `started` changes — the service
restarted — it reopens the streams, because a broken MJPEG connection would
otherwise sit on its last frame forever.

**Failures are visible (R8).** If `/api/status` stops answering, a red "No
connection to J.A.R.V.I.S." appears at the top and the live pictures are
replaced by the same message; everything reconnects on its own.

**The page is in English**, and labels are shown as the system names them
(`person`, `dog`) — the Portuguese translation table is gone with the language
decision.

**HTTPS from another computer.** The server speaks plain HTTP. A browser that
tries `https://` first — typed without the scheme, or with "always use secure
connections" on — gets nothing, and the service logs `Invalid HTTP request
received` several times a second. Reproduced on 09/10/2026: an `https://`
request produces exactly that line, `http://` answers 200. The user confirmed
`http://192.168.0.18:8765` works from the other computer. HTTPS on a home
network would need a certificate the browser trusts; a self-signed one means a
warning on every visit, so it is not worth it now.

---

### 17.9 Stage 4: People and Settings on the web (10/10/2026)

The page gained the two tabs that only the OpenCV window had.

| Route | Does |
|---|---|
| `GET /api/face-days`, `GET /api/people?day=` | days with faces; that day's sightings with the gallery's current names |
| `GET /face/<day>/<HH-MM-SS_xxxxxx>.jpg` | one face crop; name checked by pattern, then must resolve inside `faces/` |
| `POST /api/people/<p_xxxxxxxx>/name` | `Gallery.rename`: the same name on another face merges them (10.4) |
| `GET` / `POST /api/settings` | read, or change some keys; each one type-checked, labels limited to YOLO's classes, unknown keys refused |
| `POST /api/notify/discover`, `POST /api/notify/test` | find the chat, send a test |

**The token is write-only.** The page can set it but never read it back —
only `notify_token_set` — because anyone on the Wi-Fi can open the page (R4).
**"Archive now" was left out on purpose:** it would move files from the web
thread while the `Housekeeper` may be moving the same files in the main loop.
Writes from the network are guarded by R24 (HISTORY 13.9).
### 17.10 The lock, People by person, who appears, and the window gone (10/10/2026)

**Every write is guarded (R24).** A FastAPI middleware — code that wraps every
request, like a servlet `Filter` or ASP.NET middleware — refuses any
`POST`/`PUT`/`PATCH`/`DELETE` unless (a) it carries `X-Jarvis-Request: 1`, even
from 127.0.0.1, and (b) from any other address, `X-Jarvis-Pin` equals
`write_pin`, compared with `hmac.compare_digest` (constant time, so the
comparison does not leak how many digits matched). The header defeats
cross-site forgery: a foreign page cannot add a custom header without the
browser first asking the server (a CORS preflight), and this server never says
yes. The PIN (4–12 digits) is set only from the M900's own page (Settings,
Other devices) and typed once on each other device, which keeps it in
`localStorage`. Threat model, honestly: good against a guest's phone and a
forged request; not against someone sniffing the Wi-Fi, since the PIN travels
in clear over HTTP, and it sits in plain text in `config.json`, like the token.
`--stop` sends the header, and `production.ps1` always stops a service with
that same version's `--stop`, so the guard cannot lock it out.

**People by person (backlog 19).** A grid of the named, the unnamed with a name
field and a "Belongs to…" picker, and a person page (`#people/<id>`) with
rename, the stored views and a month calendar of their recordings. The gallery
gained two optional keys per person: `views`, aligned by index with
`embeddings`, holding the path of each view's face crop in `faces/views/`
(`None` for views stored before, padded by `views_of()`), and `pending`, the
Waiting views (until 13/10 the overflow past 40; since backlog 28 only what the
user moves down, `MAX_PENDING` 100). `Gallery._take()` is the one place that
stores a view — `add`, `reinforce` and `_merge` all go through it, and past 40
it applies 17.14's rule. `remove_view()` frees a slot and refuses a person's
last view. A rename to a name that
belongs to someone else answers **409 Conflict**, which the page turns into
"this will merge with X — continue?" and resends with `merge: true`. After a
rollback, an older version ignores both keys and only appends embeddings, so
the alignment holds (its new views just get `None`). **The favourite photo (backlog 21):** a star on each view with a photo sets the person's optional `cover` — the view's crop path, not its index, so it survives views being removed or reordered; `cover_of()` ignores it once it no longer matches a view, and removing the favourite falls back to the first view with a photo. A merge keeps the target's cover.

**Who appears (backlog 20).** `/api/events` reads the day's sightings once,
keyed by camera, day and clip time, and adds `people` (current names; unnamed
as "unknown") and `animals` to each event; the card shows them under the time.
Sightings stored Windows paths, so the clip path is split on either slash.

**The OpenCV window is gone.** `ui.py` and every drawing path in `cameras.py`
were deleted; `--window`/`--janela` now log where the web page is and start
as usual, for one release. A pitfall met on the way: content inside a
`<template>` lives in an inert document, where `a.href = "#x"` resolves against
`about:blank` — use `setAttribute`.

### 17.11 The page is never stale (R28, 11/10/2026)

`/` is built from `index.html` with the running version in the asset URLs (`app.js?v=<git describe>`) and sent with `Cache-Control: no-cache`; a middleware, `never_stale`, adds the same header to `/static/*`. `no-cache` means *revalidate*, not *do not store*: the browser asks with the file's ETag every load and gets a cheap 304 when nothing changed — so an update can never leave an old script running on another computer. Every refused write now shows the server's reason, e.g. an unpaired device: "no PIN is set: on the M900 itself, open Settings and set one to pair other devices". The M900's own browser at 192.168.0.18 counts as another device, which is how this was tested.

### 17.12 Pairing a device once (R34, 11/10/2026)

Pairing with the PIN makes the server set a cookie — `HttpOnly` (no script can read it), `SameSite=Strict` (never sent by another site), 30 days — holding a random token; `devices.json` keeps only its SHA-256 hash, a label and the last use, and every write from that device renews the 30 days. A cookie set by the server survives where the page's `localStorage` did not. The M900's Settings lists the paired devices with "forget"; the R24 header still blocks forged requests.

### 17.13 Playing a recording (backlog 5, 11/10/2026)

`GET /video/<camera>/<day>/<HH-MM-SS>.mp4`, with the thumbnail's name checks and a resolve inside `clips/`; Starlette's `FileResponse` answers HTTP **Range** requests (206), so the browser seeks without downloading the clip. Clicking a card opens a player on the page; a day on a person's or dog's calendar leads there.

### 17.14 The views of a person or dog: the best 40, Chosen and Waiting (backlog 24, R40)

"Analyse" on a person or dog with more than 40 views proposes the 40 that are most different — greedy farthest-point selection: start from one view, then always add the view farthest from everything already chosen — and on confirmation keeps them and either queues the rest or, with the second button, deletes them (R40). 0.03 s for 100 face views, 0.28 s for 140 dog views; on test data the closest pair kept went from identical to clearly different.

The user's rule: waiting photos only make sense if they can be compared with the chosen ones. A person or dog page shows two grids — **Chosen**, up to 40, the views that recognise them, and **Waiting**, the views the user moved down (up to 100), which recognise nobody — until backlog 28 (13/10) also the views seen after Chosen was full. A chosen view has ★ (favourite), × (delete) and ↓ (move to the end of Waiting); a waiting one has ↑ (move to the end of Chosen) and ×. Nothing moves on its own any more: deleting a chosen view used to pull the oldest waiting one in, and now leaves the place free — the next view a scan learns fills it, or the user moves one up. Refusals say why (R28): ↑ while Chosen holds 40, ↓ or × on the last chosen view (a person with no view matches nobody), ↓ while Waiting holds 100 — refused rather than dropping a waiting photo the user did not ask to drop. Every move keeps `embeddings` aligned with `views`, and `pending` entries carry their own embedding and photo, so a view keeps its photo wherever it goes; `_fix_cover` moves the favourite to the first chosen photo when the favourite leaves Chosen. The moves address a view by its position in the list; since 12/10 each also names the photo it was shown (R41, 22.6).

**The 40 manage themselves (backlog 28, 13/10/2026).** A view from a sure match, or brought by naming or merging, enters Chosen while it holds fewer than 40. Once full, `faces.replaced_view` decides: the candidate is the chosen view whose nearest twin is closest — never the favourite; the new view replaces it only when its own nearest chosen view (the candidate included) is farther than that pair, and is otherwise discarded. Ties go to the older view. So the closest pair in Chosen can only grow: a face's identical pairs (cosine 1.00, from repeated scans of one clip) are the first to go. Faces measure `1 - cosine`, dogs `dogs.distance`; for dogs the candidates are the chosen views of the **same lighting** when there is one, so a day view replaces a day view, and a view with no same-lighting twin counts as infinitely different — the first night view of a dog seen only by day enters, and the only night view is never replaced by a day one. A view that leaves goes into `Gallery.dropped`, and `save()` deletes its photo **after** writing the gallery file: a failed write leaves an unused photo, never a view without one. `load()` empties `dropped`, like `repoints`. 0.6 ms per face view, 0.5 ms per dog view. `tools/settle_waiting.py [--dry-run]` passes the queues older versions left through the same rule once, oldest first, and empties them; a real run refuses while this folder's J.A.R.V.I.S. answers on its port, and first copies `faces/` and `dogs/` to `backups/waiting_<date-time>/`.

**What the rule cannot tell (review 20, R48).** The rule keeps what is most different, and a view of the **wrong person** is, by nature, the most different. Production's queues on 13/10 held 7 faces of Izabel in Gustavo's Waiting, learned by "sure" matches (cosine 0.475–0.509, above `LEARN_THRESHOLD` 0.45) through dark, head-down views of him; while they waited they recognised nobody, but the once-only tool would have put 6 of them into his Chosen. No measure of the embeddings separates them from his genuine views (HISTORY 13.21), so the tool was not run and the release waited for the user (`BACKLOG.md` 2, R48). **Read again under ArcFace (review 23):** no wrong-person view reached `LEARN_THRESHOLD` on the bench or on real clips — the closest pair of the two people is 0.313, against 0.40 — so the rule shipped with R49. The seven views already misfiled in Gustavo's Waiting stay misfiled: settled under ArcFace, 6 of them still enter his Chosen, because the rule never asks whose a view is. The once-only tool waits until the user deletes them (`PENDING.md`).

### 17.15 Quiet disconnects (R32, 11/10/2026)

A browser closing the live view made Windows' asyncio log a traceback at ERROR
— 27 of them in one day (`_ProactorBasePipeTransport._call_connection_lost`).
A loop exception handler now drops the `ConnectionResetError` there, so ERROR
in the log means a real problem.

### 17.16 Many unnamed photos at once (backlog 26, 12/10/2026)

The user's request: name or report the unnamed crops of the Dogs tab many at a
time, instead of one "Belongs to…" per photo. People gets it too, since both
tabs are the same `galleryTab` factory (20).

- **Grouped by a guess.** `_grid` adds `guess` to each unnamed card: the named
  entry it looks like. For a dog, `dogs.match` over its views, sure before
  probable, then the nearest; for a face, the named person with the best
  similarity at or above `MATCH_THRESHOLD`. The page groups the unnamed grid as
  "Looks like Aurora (12)", biggest first, "No guess" last, each with
  **Select all**. A guess is a hint and never names anything; the face guess
  uses the matching threshold, lower than the learning one, so a group may
  hold a wrong face.
- **Selecting.** Tapping a photo selects it (a green frame and a check mark);
  the name link still opens the entry. Shift-click selects the range from the
  last photo tapped, in display order. While anything is selected, a bar stays
  at the bottom of the screen: "N selected · Assign to… · or a new name · Bad
  detection · Clear". Each action asks once ("Join 7 photos to Aurora? A merge
  cannot be undone."). The selection survives a reload of the list, minus the
  photos that left. On a phone the unnamed groups show two columns.
- **One request each.** `POST /api/{dogs,persons}/assign` with `{"ids", "to"}`
  or `{"ids", "name"}` runs `Gallery.assign` under one lock, one load and one
  save. Ids that are no longer unnamed — merged, named or reported meanwhile —
  are skipped and answered as `gone`; with a new name the first remaining
  photo takes it and the rest join it; the look-alikes are gathered once at
  the end (R29). `POST /api/{dogs,persons}/report` writes one report per entry
  (21) and answers `{reported, gone}`. Both take 1 to `BATCH_MAX` = 500
  well-formed ids and pass the write guard (17.12).
- **Found on the way:** with six tabs the tab bar did not wrap, so a phone laid
  the page out 545 px wide — the layout viewport grows to the widest content —
  and the bar fixed to the bottom fell below the screen. The tabs wrap now.

**The sightings, once per batch (R45, 12/10/2026).** Joining a photo
rewrites the sightings that pointed at it, and sightings are never pruned
(about 50 dog sightings a day on the M900). Each photo joined used to scan
every day folder, under the gallery lock; now the whole batch is one scan, at
the save (10.4). Measured: a batch of five reads each sighting file once
instead of five times. Bounding the scan by the entry's `first_seen` would
not be safe: `tools/dog_crops.py` gives today's entries sightings of older
days.

### 17.17 Many photos on a phone (backlog 37, 14/10/2026)

The user's concern: some households will never open the page, so People and
Dogs must cope with a great many photos. What is bounded and what is not is
in BACKLOG 1, item 37; this is the layout.

- **Two columns on a phone.** Under 480 px every `.people-grid` takes two
  columns — named cards, a person's Chosen and Waiting — as the "Looks like"
  groups already did.
- **24 at a time.** `paged(container, items, render, shown, key)` in `app.js`
  draws the first 24 (`PAGE_STEP`) and a button "Show 24 more (N left)"
  spanning the grid; a press appends the next ones **before** the button
  (`Element.before`, PYTHON 43), so nothing already drawn is drawn again. It
  pages each unnamed group, a person's or dog's Waiting and "Days they were
  seen". How far a list was opened is kept per tab in a `Map` (keys
  `group:<title>`, `waiting:<id>`, `days:<id>`), so naming one photo, which
  reloads the list, does not fold it back. Chosen, at most 40, is drawn
  whole; headings keep the full count; the server still sends whole lists.
- **Waiting, newest first.** It is stored oldest first (views are appended),
  and the page now reverses it; each tile keeps its stored index for its ↑
  and × requests.

**Measured with production's 46 dogs** (developer 23, at 375 px): the Dogs
tab 9,163 → 8,591 px; named cards one → two per row; Aurora's page, 34
waiting, 6,390 px with 24 shown, 7,201 with all; no horizontal scroll;
desktop unchanged at five columns. **The gain is small, and the reason is
the card**: none of today's three unnamed groups (18, 10 and 16 dogs) passes
24, and an unnamed card is 309 px tall at 172 px wide — a 170 px photo, then
the name, a name form and "Bad detection" stacked (review 25, on the test
copy). On a phone the selection bar at the bottom (17.16) already does what
the card's form and button do, for one photo or many: backlog 39 (decided,
UX) drops them from the card on a phone.

**On a phone an unnamed card is its photo and its name (backlog 39,
15/10/2026).** Under 480 px, `.unnamed-grid .naming`, `.belongs` and
`.report` are `display: none` — CSS only, so the desktop keeps every card's
name form, "Belongs to…" list and "Bad detection". The hint above the
unnamed list holds two spans, `.wide-only` (the long text) and `.phone-only`
("Tap photos to select them, then name or report them below."); the base
rule `.phone-only { display: none }` comes **before** the media query that
shows it, because at equal specificity the later rule wins (PYTHON 44).
Naming or reporting one photo is two taps: the photo, then the bar's "Assign
to…" (it fires on `change`) or "Bad detection". Measured by developer 24 at
375 px with production's 46 dogs: the Dogs tab **8,768 → 6,018 px**, an
unnamed card 349.5 → 231.5 px; desktop (1024 px) unchanged. Review 26 saw it
at 375 px and on the desktop on the test copy. Settings → Detection hides
the accuracy table (backlog 32, 10.15) while nothing is measured
(`views` 0), on every width, and keeps its one sentence.

---

## 18. Production and test (designed and built 09/10/2026)

Written in English: the user decided on 09/10/2026 that documentation moves to
English (CONTEXT R10). Older sections are still in Portuguese until then.

### 18.1 What the user asked for

> "My proposal is to have a service already installed on my machine, running
> constantly. [...] Have the production version always running, with an update
> process for it, and meanwhile we run in a test environment to evolve the
> version."

Today there is one copy of the program, and it is also the one being edited.
Every change goes live the moment it is saved, and testing a change means
stopping the surveillance.

### 18.2 The camera limit, measured

The obstacle the user anticipated is real, but narrower than assumed. Measured
on 09/10/2026 on the Front camera, a second client started 3 s after the first:

| First client | Second client | Result |
|---|---|---|
| `stream1` | `stream1` | second refused (`406`, "not one of 40{0,1,3,4}") |
| `stream1` | `stream2` | **both deliver** (151 and 76 frames) |
| `stream2` | `stream2` | **both deliver** |

| Stream | Codec | Resolution | Frame rate |
|---|---|---|---|
| `stream1` | H.264 | 1920x1080 | 15 fps |
| `stream2` | H.264 | 640x360 | 15 fps |

Same on the Back camera. So the Tapo C310 allows **one** client on the HD stream
and several on the SD stream at the same time. The September finding
("the camera accepts a single RTSP session", 5.2) was only ever tested on
`stream1`.

### 18.3 The design

**Two installations, each with its own data:**

| | Production | Test |
|---|---|---|
| Where | its own clone, `C:\JARVIS`, outside the project folder | the development checkout |
| Code | a **release tag**, never a working copy | whatever is being written |
| Camera stream | `stream1`, 1080p, records in HD | `stream2`, 640x360 |
| Web port | 8765, open to the home network (decided, R4) | 8766 |
| `clips/`, `faces/`, `config.json` | its own | its own; separate already, because every path hangs off `ROOT` (3.2) |
| Telegram | on | off by default, or prefixed `[TEST]` |
| Runs as | Task Scheduler task at boot, no console | by hand |

Both read the same cameras at once thanks to 18.2. The test copy can run on the
M900 or on the development machine; the cameras are on the network either way.

**What 640x360 costs the test copy:** motion, YOLO, recording, the web and the
notifications all work, but a face that is 45 px in 1080p is 15 px here — face
recognition cannot be tested live. For that, test against recorded HD clips
(see 18.6).

**Releases.** Production only ever runs a tagged commit, and a commit only gets
a tag after the architect review (PROCESS 3) has covered it. That ties the
two workflows together: nothing unreviewed reaches the machine that guards the
house.

**Updating production**, one command (`tools/update_production.ps1`, to be
written):

1. Fetch tags into `C:\JARVIS` and remember the tag currently running.
2. Stop the service **gracefully**, so a clip being assembled is not lost.
3. Check out the new tag and run `uv sync`.
4. Start the Task Scheduler task.
5. Health check: within 60 s, `/api/cameras` lists every camera and the live
   view delivers frames.
6. On failure, check out the previous tag, `uv sync`, start again, and say so
   on Telegram. On success, report the new version on Telegram.

### 18.4 What the code needs before this works

| Change | Why |
|---|---|
| Stream per installation in `.env` (`CAM_STREAM`, default `stream1`) | `STREAM` is a constant in `cameras.py` today |
| Web port per installation (`WEB_PORT`, default 8765) | `PORT` is a constant in `web.py` |
| A graceful stop that is not Ctrl+C | a scheduled task has no console; ending the task kills the process without running the `finally` in `main()` (17.7) |
| Logging to a file with rotation instead of `print` | with no console, `print` goes nowhere |
| Notification prefix per installation | so a test event is never mistaken for a real one |

The graceful stop has two reasonable forms: a `POST /api/shutdown` that only
accepts connections from `127.0.0.1`, or a stop file the main loop checks every
pass. The endpoint is simpler to call from the update script; the file works
even if the web thread is stuck.

### 18.5 Open decisions for the user

- Does the test copy run on the M900 next to production, or on the development
  machine? Recommendation: development machine — it is where the code is
  written and it has the CPU to spare; the M900 only runs production.
- Who runs the update? Recommendation: Claude, on request, after a review —
  never automatically, because an automatic update that fails at 3 a.m. is a
  night without surveillance.

**Where they stand (09/10/2026).** Who updates: **Claude, on request, after a
review** — that is how the user asked for the first release, and how
`update` is meant to be run. Where the test copy runs: not decided; the install
turns the development folder on the M900 into the test copy, which only runs
when started. Moving it to the other computer later means configuring that
checkout the same way (`CAM_STREAM=stream2`, `WEB_PORT=8766`, no token).

### 18.6 Later

A **file source**: point the test copy at a folder of recorded clips instead of
a camera, and replay them through the whole pipeline. It makes face
recognition testable at full resolution and makes any bug reproducible with
the exact footage that caused it.

### 18.7 As built (09/10/2026)

Everything in 18.4 is implemented. Production lives in `C:\JARVIS`, a clone of
the GitHub repository checked out at a release tag, and is driven by one
script, run from the development folder:

```bat
powershell -ExecutionPolicy Bypass -File tools\production.ps1 -Action <action>
```

| Action | Does | Needs admin |
|---|---|---|
| `install` | clone, copy data, `uv sync`, check data, start, health check, Telegram, turn the development folder into the test copy, desktop shortcut, register the startup task | only for the task, which it asks for on its own |
| `update` | update to the newest release tag (or `-Tag vX`), with checks and rollback | no |
| `status` | version, task, held or not, seconds since each camera's last frame | no |
| `stop` | stop cleanly **and hold**: the task will not start it again | no |
| `start` | release the hold, start, health check | no |
| `check` | run `tools/check_data.py` against production's data | no |
| `register` | register the startup task only | **yes** |

**The startup task** runs `C:\JARVIS\.venv\Scripts\pythonw.exe -m jarvis
--headless` directly: no console and no uv in the way. `pythonw.exe` there is
the venv launcher of the signed python.org build, so Smart App Control lets it
run (INSTALL 1.2); `Sync` refuses to finish if it is not. The test —
signature `Valid` and the Python Software Foundation in the signer — lives in
`tools/check_python.ps1`, which `install.bat` runs on `.venv\Scripts\python.exe`
too (R7, 12/10/2026): one rule, written once. `production.ps1` finds it through
`$PSScriptRoot`, so it is always the copy beside the `production.ps1` that is
running, in the development folder.

| Setting | Value | Why |
|---|---|---|
| Logon type | S4U | runs whether or not anyone is logged on, with no password stored. Registering it is what needs admin |
| Triggers | at startup, **and every 5 min** | see below |
| Multiple instances | ignore new | the 5-minute trigger does nothing while it runs |
| Execution time limit | none | **the Task Scheduler default is 72 hours**: left alone it would kill the surveillance every three days |

**Why a 5-minute trigger.** The first version relied on "restart on failure".
The review found that this setting only acts when the task *fails to start*,
not when the program, once started, exits with an error — so a crash would
have ended the surveillance until the next reboot. A trigger every 5 minutes
with "ignore new" is the reliable form: running, nothing happens; crashed, it
is back within 5 minutes. A second copy cannot slip in either way, because
`main()` itself refuses to start next to a running one (17.7, 18.8).

**Why a `HOLD` file.** Starting and stopping a scheduled task needs admin
rights, and updates run without them. So the script never touches the task: it
stops the service through `--stop` and starts it directly with `pythonw.exe`.
That leaves one problem — the 5-minute trigger could start production in the
middle of an update, on half-switched code. `main()` therefore refuses to start
while `C:\JARVIS\HOLD` exists. `update` creates it before stopping and
`start` removes it; `stop` leaves it in place, which is what "stop" should mean.

**Models before the stop (R49, 14/10/2026).** A release that needs new
models must not wait on the network while production is stopped. After the
"before" data check, `FetchModels` reads `src/jarvis/downloads.py` **from the
target tag** with `git show`, writes it to `%TEMP%` and runs it with
production's current Python against `C:\JARVIS\models`; it fails the update
before anything changed if the download fails, and skips a tag that has no
such file. Review 23 found that skip broken: under `$ErrorActionPreference =
'Stop'`, Windows PowerShell 5.1 turns a redirected stderr line of a native
command into a terminating error, so `git show` of a missing path threw
instead of reaching `$LASTEXITCODE` — an update to `v2026.10.13` would have
aborted. It now lowers the preference around the call, as `CurrentVersion`
already did (`d07c09e`; PYTHON 41). **A gap in the guarantee above, closed:**
the first start of a release that migrates the gallery spends about 25 s in
`migrate_gallery()` before the web answers, and a second launch in that
window (the 5-minute trigger) passed the already-running check and migrated
too. Since R52 the migration holds a lock file, so the second copy waits and
then finds nothing to do (10.14).

**Two ways production starts, and they do not look the same** (seen on the
first night, 09/10/2026):

| Started by | Runs in | Visible? | At logoff |
|---|---|---|---|
| the task (boot, or the 5-minute trigger) | session 0, as S4U | nothing | keeps running |
| `production.ps1` (`install`, `update`, `start`) | the logged-on user's session | **every ffmpeg it starts gets a console window** | ends with the session; the 5-minute trigger starts it again in session 0 |

The windows come from how Windows treats console programs. `pythonw.exe` has
no console, and a console program started from a process without one gets a
**new** console window of its own. ffmpeg is a console program, so the user
saw two windows that stayed (one capture per camera, titled with the ffmpeg
path under `site-packages\imageio_ffmpeg`) and others that flashed (clip
assembly and the face scan). Closing one kills that ffmpeg. The fix is in the
code, not the script: every subprocess now starts with `CREATE_NO_WINDOW` (R15,
10/10/2026) — C#'s `ProcessStartInfo.CreateNoWindow`. Checking it taught two
things: a `conhost.exe` child is not a sign of a window (Windows creates one
with the flag too, and with Windows Terminal the window belongs to
`WindowsTerminal.exe`); what works is `AttachConsole(pid)` then
`GetConsoleWindow()`, NULL without a window. And a script under `pythonw.exe`
that captures a subprocess's output needs `stdin=subprocess.DEVNULL`, or it
dies silently on an invalid handle.

**An update**, in order, and where it stops:

0. **Are the cameras delivering frames now?** (R57, 15/10/2026.) One read
   of `/api/status`: if the service does not answer, or any camera's last
   frame is `$FreshSeconds` or older, refuse — "Not updating: … The cameras
   are not delivering frames now; nothing was changed." — unless `-Force`
   is given, for a release that fixes capture or a crash at startup. On
   14/10 an update during a camera outage stopped a working production,
   failed the health check on cameras no release could reach, and rolled
   back (HISTORY 13.26).
1. Check the data with the **current** version. Unreadable already → refuse,
   nothing changed.
2. Hold, stop cleanly.
3. `git checkout --force <tag>`, `uv sync --frozen --no-dev` (since 10/10/2026: production carries no test tools, and the sync removes them if present), signature check (`tools/check_python.ps1` on `pythonw.exe`).
4. Check the data with the **new** version.
5. Release, start, health check: within 90 s every camera's last frame must be
   under 5 s old (`/api/status`, `frame_age`).
6. Any failure in 3–5 → hold, stop, check out the previous version, sync,
   start, health check, and a Telegram message saying the update failed and
   what is running.

**Each failure says which part failed** (R57). `FrameProblem` makes one
read and returns `$null` or the reason — "the service is not answering on
port N", or "the service answers, but cameras deliver no frames (Back no
frame yet, Front last frame 63 s ago)"; `WaitForFrames` polls it for
`$HealthSeconds` (90) and returns the last reason. A function that returns
a reason or `$null` instead of `$true`/`$false` (PYTHON 44). `install`,
`start`, `update` and the rollback all print it, and the rollback ends with
"rolled back to X, running, every camera delivering frames" or "…, which is
not healthy after 90 s: <reason>" — never again "Running again: False" of a
service that was running without frames. Tested by developer 24 with a
throwaway clone as `-ProdDir` pointed at the test copy: stopped, one camera
at a wrong address, the same with `-Force`, and both cameras live.

**Tested before the first release**, in a temporary folder with
`-SkipTask` (no task, no shortcut, no Telegram):

| Test | Result |
|---|---|
| install | clone, copy, sync and both cameras fresh in about 30 s |
| `stop` | clean stop, `HOLD` created |
| what the task would do while held | "Held: ... Not starting." |
| `status` | version, held, not answering |
| `start` | hold released, running |
| update to a version broken on purpose | failed the health check, rolled back by itself; `status` afterwards showed the previous version with both cameras fresh (0.0 s and 0.1 s) |

What only the real install can test: registering the task (admin), the shortcut,
turning the development folder into the test copy, and a reboot.

### 18.8 What the review changed (09/10/2026)

The developer's first version was reviewed before the first release (CONTEXT
13.2, review 2). Besides the task design above:

- **The port as an atomic lock.** The first version checked whether the port
  was free and bound it a moment later, in uvicorn's thread; two launches a
  moment apart could both see it free. `web._bind()` now binds it in the main
  thread with `SO_EXCLUSIVEADDRUSE` (without it, Windows lets a second process
  bind the same port) and hands the bound socket to uvicorn
  (`Server.run(sockets=[...])`). If the port is taken, `main()` waits up to 5 s
  for a J.A.R.V.I.S. to answer there and leaves if one does; if nothing
  answers, another program has the port and the surveillance runs without the
  web rather than not at all. Tested: two launches at the same instant, one
  runs.
- **Only the service writes `logs/jarvis.log`.** `--stop` and a duplicate
  launch log to the console only: on Windows, rotating a log that another
  process holds open fails.
- **`.env` written without a BOM** by the install script; with one, the first
  key of the file would silently stop matching (19.3).
- **The test copy also loses `archive_path`**: two copies moving recordings
  into the same external drive would fight over it.

### 18.9 PowerShell traps met while building this

Worth knowing for anyone touching `tools/production.ps1`:

| Trap | What happened |
|---|---|
| Everything a function prints is part of its return value | `CheckData` returned the check's output lines plus `$true`/`$false`; a non-empty array is truthy, so **the data gate always passed**. Fixed with `\| Out-Host`, proven with a corrupted file |
| Names are case-insensitive | a helper named `Git` shadowed `git.exe` and would have called itself forever |
| Windows PowerShell 5.1 reads a `.ps1` without BOM as ANSI | an em dash in a message became a closing quote, and the script stopped parsing. The script is ASCII-only now |
| `$ErrorActionPreference = 'Stop'` turns a native program's stderr into an exception | `git describe` on an untagged commit aborted `status` |
| `Start-Process -Wait` waits for every process the child started too | a test harness hung on the service the install left running (the script itself only waits on the elevated registration, which starts nothing) |

---

## 19. Files on disk, and keeping them readable

### 19.1 The rule

Decided by the user on 09/10/2026: **a new version must never break files
written by an older one.** The recordings, the face gallery and the names given
to it are the system's memory; a version that cannot read them has thrown that
memory away.

So changes to anything below are **additive**: new optional fields, new files.
A field is never renamed, removed or given a new meaning. If a change cannot be
additive, the developer stops and tells the user before writing it, and ships a
migration with it (CLAUDE.md). **The precedent, 14/10/2026:** new face
embeddings could not be additive, so they went into a **new file** built from
the old one, which stays untouched for a rollback (10.14).

### 19.2 What is on disk

| File | Written by | Read by | Content |
|---|---|---|---|
| `clips/<cam>/<day>/HH-MM-SS.mp4` | `clips._concat` | the user, the face scan, `tools/check_clips.py` | the camera's own H.264, never re-encoded (8.1) |
| `clips/<cam>/<day>/HH-MM-SS.jpg` | `EventRecorder._start` | Records, web, notification | first frame with the subject, boxes drawn (8.5) |
| `clips/<cam>/<day>/HH-MM-SS.json` | `EventRecorder._write_metadata` | Records, web, archive, `check_data` | `camera`, `started_at`, `time`, `seconds`, `labels`, `best_confidence`, `video`, `thumbnail`, `reason`; `best_thumbnail` **optional since 10/10/2026**; `most_people` **optional since 14/10/2026**; `people_thumbnail` **optional since 15/10/2026** (8.4) |
| `clips/<cam>/<day>/HH-MM-SS.alert.jpg` | `EventRecorder._notify_late` | the Telegram message | **optional, since 09/10/2026**: only when the notification went out after the event began (12.8) |
| `clips/<cam>/<day>/HH-MM-SS.best.jpg` | `EventRecorder.stop` | web, the follow-up message | **optional, since 10/10/2026**: the best view of a person in the event (12.9) |
| `clips/<cam>/<day>/HH-MM-SS.side.jpg` | `scan_clip` | the follow-up message | **optional, since 11/10/2026**: the best face seen from the side when none was recognisable (10.12) |
| `clips/<cam>/<day>/HH-MM-SS.people.jpg` | `EventRecorder.stop` | the hidden-person message | **optional, since 15/10/2026**: the frame where two or more people were counted, boxes drawn (22.3, R56) |
| `clips/_buffer/<cam>/*.mp4` | ffmpeg | `covering()` | rolling segments, deleted on their own (5.5) |
| `faces/gallery_arcface_w600k_r50.json` | `Gallery.save`, `migrate_gallery` | People, the face scan | **since 14/10/2026** (10.14): `gallery.json`'s schema with 512 floats per embedding, plus `model` and `source` (`file`, `sha1`) at the top |
| `faces/gallery.json` | `Gallery.save` until `v2026.10.13`; **never written since** | `v2026.10.13` after a rollback, `migrate_gallery`, `check_data` | `people`: `id`, `name`, `embeddings` (128 floats each), `thumbnail`, `first_seen`; `views`, `pending` and `cover` **optional since 10/10/2026** (17.10); `resident` (only ever `true`) **optional since 12/10/2026** (22.1) |
| `dogs/gallery_dinov2_small.json` | `DogGallery.save`, `dogs.migrate_gallery` | the Dogs tab, matching | **since 15/10/2026** (section 20): `gallery.json`'s schema with 385 floats per descriptor (the infrared flag, then DINOv2-small's 384), plus `model` and `source` (`file`, `sha1`) at the top |
| `dogs/` (`gallery.json`, `views/`, `<day>/*.json` + crops) | `dogs.py`; `gallery.json` **never written since 15/10/2026** | the Dogs tab, matching, `check_data`; `gallery.json`: `v2026.10.14.3` after a rollback, `dogs.migrate_gallery`, `check_data` | **since 10/10/2026** (section 20); `gallery.json`'s descriptors are the 41-number histograms; entries take the optional `resident` like faces **since 12/10/2026**; dog sightings: `dog_id`, `camera`, `at`, `time`, `infrared`, `clip`, `thumbnail`, `certainty`, `match`, `words` |
| `models/dinov2_small.onnx` | `downloads.py` | `dogs.Network` | **since 15/10/2026**: 88.5 MB, kept only with its pinned SHA-256 (10.2) |
| `faces/views/<12hex>.jpg` | `Gallery._store_view` | the person page | **since 10/10/2026**: one face crop per chosen or waiting view; a view that leaves is deleted after the save (17.14) |
| `faces/<day>/<HH-MM-SS>_<id>.json` + `.jpg` | `scan_clip` | People, `check_data` | `person_id`, `camera`, `at`, `time`, `score`, `frames`, `face_width`, `reliable`, `clip`, `thumbnail` |
| `reports/<kind>/<stem>.json` + `.jpg` | `reports._write` | Settings → Bad-detection reports, `check_data`, each review | **since 11/10/2026** (section 21): `kind`, `verdict`, `source`, `reported_at`, `label`, `camera`, `at`, `time`, `clip`, `score`, `box`, `crop`; a gallery report adds `entry` and `sightings`, an event report `event`. **Optional since 11/10 (R38, R37):** `entry` holds the whole gallery entry (older reports: only `id`, `first_seen`, `embeddings`), `sighting_files`, `actually` |
| `reports/<kind>/<stem>/` | `reports._keep_copies` | Undo | **since 11/10/2026 (R38)**: copies of the entry's view photos (`<12hex>.jpg`) and of its sightings' crops (`HH-MM-SS_<id>.jpg`); absent in older reports |
| `devices.json` | `web` (pairing) | the write guard | **since 11/10/2026 (R34)**: each paired device's token SHA-256 hash, label and last use |
| `config.json` | `settings.save` | everything that reads settings | `archive_*`, `notify_*`; `notify_prefix` **since 09/10/2026**; `write_pin` **since 10/10/2026** (17.10); `notify_mode` and `notify_modes` **since 12/10/2026** (22.2), written whole once this version saves any setting; `face_sure_threshold` **since 14/10/2026** (10.15), absent until the user saves one; `notify_labels` is still read, to build the default switches. Since 10/10/2026 `save()` keeps keys it does not know, so an older version never erases a newer one's settings (R11) |
| `.env` | the user | `cameras.main` | `CAM_<LABEL>_IP/_USER/_PASSWORD`; `CAM_STREAM`, `WEB_PORT` **optional since 09/10/2026** |
| `logs/jarvis.log` (+ `.1` to `.5`) | `log.to_file` | the user | 1 MB each, the oldest is dropped |
| `HOLD` | `tools/production.ps1` | `cameras.main` | present while production is held (18.7) |

Every event file shares the basename `HH-MM-SS`, and that is load-bearing: the
archive moves an event with `glob(f"{base.name}.*")` (11.2). That is why the
late alert photo is `HH-MM-SS.alert.jpg` and not `HH-MM-SS_alert.jpg` — the
second name would be left behind when the event moves to the external drive.

### 19.3 Two traps already met

**`settings.save()` drops keys it does not know.** It keeps only the keys in
`DEFAULTS`. An older version saving `config.json` erases settings a newer one
added. Harmless as long as production only moves forward, but it is the reason
`check_data` warns about unknown keys.

**A byte-order mark makes JSON unreadable.** PowerShell's
`Set-Content -Encoding UTF8` and some editors start a UTF-8 file with the three
bytes `EF BB BF`. `json.loads` on a string read as `utf-8` fails on them — and
`settings.load()` swallowed the error and returned the defaults, so a
`config.json` saved that way **silently lost the Telegram token**. Found on
09/10/2026 when a test restore added a BOM and `check_data` caught it. Every
JSON reader now opens files as `utf-8-sig`, which accepts both; writing is
unchanged (no BOM).

### 19.4 `tools/check_data.py`

Reads every event, face sighting, both face galleries — `gallery.json` at
128 numbers and the current model's file at 512, each when present — and
`config.json` **with the current code**, the way the program reads them (including `web._event`, what
the page shows), plus the archive folder if one is configured and reachable.
Exit code 1 if any file cannot be read.

```bat
uv run tools/check_data.py
```

On the M900 on 09/10/2026: 149 events, 7 people, 20 sightings, all readable.

It is part of every production update, before and after switching versions
(18.7): the update is refused if the data is already unreadable, and rolled
back if the new version cannot read it. Proven with a deliberately corrupted
event JSON (exit 1) and the restored file (exit 0).

Unknown keys in `config.json` are a **warning**, not a failure: the file is
still readable, and failing would block going back to an older version.

### 19.5 Automatic tests (10/10/2026)

`uv run python -m pytest` runs the tests in `tests/` (R6; 23 on 10/10, 92 in about 16 s on 11/10, 160 in about 14 s on 12/10, 208 in about 16 s on 13/10, 216 in about 13 s that night, 269 in about 15 s on 14/10 after developer 22): the gallery's view alignment (`test_gallery.py`: a photo per view, old views without one, moves between Chosen and Waiting, merges), the 40-view rule (`test_forty_views.py`: the closest pair loses one, never the favourite, a near-copy discarded with its photo, the dogs' lighting, a merge past 40, `settle_waiting.py`'s dry run changing no byte), the write guard (`test_web_guard.py`: FastAPI's `TestClient` as 127.0.0.1 and as a LAN address), the notification rules (`test_notify.py`: redaction, both cooldowns, every case in every mode, the held person message with a fake scan), the Telegram commands against a fake Bot API (`test_bot.py`), the modes through the web (`test_modes_web.py`) and the view moves' check (`test_view_moves.py`). Every test works on temporary folders and replaces `notify.send`, so nothing touches real data or the network. `pytest` and `httpx2` are development dependencies only; `httpx2` is the successor of `httpx` that this Starlette's `TestClient` imports first (checked 10/10: same author, Pydantic's repository).

**Why `python -m pytest` and not `uv run pytest` (11/10/2026).** On the M900, `uv run pytest` fails with *"An Application Control policy has blocked this file (os error 4551)"*: it starts `.venv\Scripts\pytest.exe`, a small launcher `uv` writes for each installed command, and that launcher is not signed, so Smart App Control blocks it (INSTALL 1.2, the same reason the project uses the official Python). `python -m pytest` asks the signed `python.exe` to run the `pytest` package itself — the same tests, no unsigned file in the way. Use it for any tool installed into `.venv`.

---

## 20. Dogs: each household teaches its own (10/10/2026)

**The rule (the user's):** nothing about any particular dog lives in the code.
The software is for any house; the user names their dogs on the **Dogs** tab,
and the system learns from those names.

**The descriptor: DINOv2-small (R53 step 2, 15/10/2026).** `dogs.describe`
cuts the YOLO box widened by `MARGIN` (10 %), clipped to the frame, and
shrinks it so its longer side is at most `CROP_SIDE` (320 px): that crop is
both the view's stored photo and what the network sees, so a live crop and
its photo describe alike. `_blob` pads it square with black, resizes it to
224 px (`INTER_AREA`), turns BGR into RGB and normalises it with ImageNet's
mean and standard deviation — exactly what the bench embedded (step 1,
below). DINOv2-small is a vision transformer: it cuts the image into a 16×16
grid of 14 px patches and adds one extra **CLS** token that attends to all
of them; the CLS token's vector in the last layer is the image's summary
(PYTHON 44). The ONNX file has one output, `last_hidden_state` (1, 257,
384), and the descriptor is its token 0 — what Hugging Face calls
`pooler_output`, which the file does not expose because only the graph's
leaves are outputs. Descriptor = the infrared flag + those 384 numbers,
unit length, rounded to 6 decimals (`DECIMALS`): 385 numbers
(`DESCRIPTOR_SIZE`). `is_infrared` still judges the region before it is
shrunk: the mean channel difference is 3.98 on every night clip and 15–24
by day, so 8 is safe. **No GrabCut**: the network looks at the whole crop,
and the bench showed it tells the two dogs apart without cutting out the
floor.

**Two copies of the network.** `dogs.LIVE` serves `identify`, in the
analysis loop, for the first message's words; `dogs.STORED` serves
`record`, in the assembly thread, the migration and Undo. Each is a
`Network` with its own lock, loaded on first use (about 1 s): a
`cv2.dnn.Net` keeps buffers between calls and must never run in two threads
at once (`people.load_background_model`). Two cameras' loops share `LIVE`
and wait for each other on its lock, at most once per dog event.

**The distance.** `dogs.distance` is 1 − cosine within one lighting, and
`None` between day and infrared — never compared — **or between
descriptors of different sizes**, so a histogram is never compared with an
embedding. `DogGallery.distances` gives every pair at once for the
farthest-point choice of 40 views (backlog 28): rows normalised, one matrix
product `1 − X @ Xᵀ`, ∞ across lightings (PYTHON 43).

**The thresholds, from the bench's sweep** (developer 24, on the copy of
14/10: 103 day and 46 night views, leave-one-out with exact copies left
out). `match` takes the nearest named dog: **sure** within `SURE_DISTANCE`
0.33 and at most `SURE_RATIO` 0.6× the second nearest; **probable** within
`PROBABLE_DISTANCE` 0.39 and 0.8×; otherwise nobody — the margin to the
second is what lets it honestly say "I don't know". Each cell is right /
wrong / person crops named / two-dog crops named, day | night:

| distance | ratio 0.6 | 0.7 | 0.8 | 1.0 |
|---|---|---|---|---|
| 0.30 | 85/0/0/3 \| 28/0/0/1 | 85/0/0/5 \| 32/0/0/1 | 85/0/0/6 \| 32/0/0/1 | 85/0/0/6 \| 32/0/0/1 |
| **0.33** | **89/0/0/3 \| 30/0/0/1** | 90/0/0/5 \| 36/0/0/1 | 90/0/0/7 \| 38/0/0/1 | 90/0/0/8 \| 38/0/0/1 |
| 0.337 | 89/0/0/3 \| 30/0/0/1 | 91/0/0/5 \| 36/0/0/1 | 91/0/0/7 \| 38/0/0/1 | 91/0/0/8 \| 38/0/0/1 |
| **0.39** | 92/0/0/3 \| 30/0/0/1 | 94/0/0/5 \| 38/0/0/1 | **96/0/0/8 \| 42/0/0/1** | 96/0/0/10 \| 42/0/0/1 |

Sure sits under 0.337, the distance that names 90 % of the day views, and
its ratio 0.6 keeps two-dog crops out of the sure answers (3 + 1 instead of
7 + 1) at no cost in right views. That matters because a sure answer
**teaches** the gallery and gathers crops (R29): a two-dog crop named sure
would be a new misfiled view. Probable sits 0.059 under the nearest person
crop (0.449): 96/103 and 42/46 named, none wrong, no person. No answer is
wrong anywhere in the sweep, which is **optimistic** while each view's own
event stays among the references (R55, BACKLOG 2). `tools/dog_tuning.py` on
the migrated copy agrees: 0 wrong at every point of its grid.

**The gallery.** `DogGallery` subclasses `faces.Gallery` — the same views,
queue and favourite photo, in `dogs/`, with ids `d_…` — by overriding class
attributes (`id_prefix`, `sighting_key`, `model`): the same code with
different constants, the way a Java subclass overrides a constant. Naming
gathers only the crops that match **for sure** (R29, below). The page reuses
one JavaScript factory, `galleryTab(...)`, for People and Dogs.

**The wording (the user's rule).** A dog alerts because a dog is there,
whenever `dog` is an alert label; certainty only changes the words: the name,
"probably <name>", or "unidentified dog" (plain "dog" while nothing is named).
The first message names the dogs of the triggering frame, once per dog event
and once more if "dog" arrives late; the Recordings card shows the event's
best dog frame, so the two can differ. A sure match reinforces that dog with
one more view; anything less becomes an unnamed crop (R27 caps them).
`tools/dog_crops.py [--days N]` gives crops to events recorded before the
feature (~21 s per event on the M900).

**What naming costs the live loop** (developer 24, M900, 960×540 frames,
real dog boxes, 80 named views): `identify` **121 ms median per dog** (max
207), **243 ms with two** (max 456); `match` alone 2.6 ms. The histograms
took 37 and 72 ms there, because GrabCut's cost follows the box and a dog in
a 960×540 frame is small; the ~1,200 ms of the bench's table (step 1, below)
was on the stored 320 px crops. So in the live loop DINOv2 is about 85 ms
**dearer** per dog, not cheaper. At 10 analysis frames a second that skips
one to three frames once per dog event; nothing queues, since the loop
takes the newest frame (5.4). Accepted in review 26.

**Keeping the Dogs tab small (R27, 11/10/2026).** `DogGallery.add` keeps only the newest `MAX_UNNAMED` = 60 unnamed dogs; named dogs are never touched, and a dropped entry's photos go with it. Sightings stay, so calendars keep their history (a dropped `dog_id` reads as "?"). Each unnamed crop had a **Dismiss**, replaced on 11/10 by **Bad detection** (section 21). `tools/dog_tuning.py [--gallery PATH]` measures the thresholds by **leave-one-out** — each named view matched against all the others, the honest test with few labels — and prints right-sure, right-probable, wrong and no-name per lighting, then a grid of thresholds; it only reads, so it can run on production's gallery (since 15/10/2026 `dogs/gallery_dinov2_small.json`, its default).

**Dogs gather their look-alikes (R29, 11/10/2026).** Naming or merging a dog re-examines every unnamed crop against the dog's updated views with the *sure* rule only, same lighting only, repeating until nothing joins; past recordings show the dog's current name from `dog_id` instead of the words frozen when they were recorded.

**Colour histograms against learned embeddings (R53 step 1, 14/10/2026).**
The user saw Mirana among Aurora's views and a person among Mirana's. A
histogram counts colours, so at night, when both dogs are grey, and on
anything dark — shoes, clothing — it says whichever dog its fur mask caught.
`tools/dog_bench.py` compares today's descriptor with three learned image
embeddings on `backups/r53_dogs_20261014`, a copy of production's `dogs/`
(only read). Nothing in the program changed.

- **Labels, nothing deleted.** Of the nine views `PENDING.md` lists as
  misfiled, five are a person, two hold both dogs, one is Mirana filed under
  Aurora, one (`6b3d84`) is left out as unclear. Eleven sighting crops of
  scenes where the two dogs' boxes overlap are the two-dog probes; four of
  them are also gallery views — the same picture saved twice, found by a
  16×16 grey thumbnail — so those four views hold both dogs too. In all:
  Aurora 40 day / 28 night, Mirana 63 / 18, 13 two-dog crops, 5 person crops.
- **Leave-one-out per lighting**, as the program never compares day with
  night: each view against every other, its exact and near-exact copies left
  out; the nearest dog's name, and a threshold sweep.
- **The candidates**, each exported once to ONNX in a throwaway environment
  (PyTorch 2.14.1 CPU, as AdaFace was, 10.14) into `models/bench/dogs/`, and
  checked through `cv2.dnn` against PyTorch's output (cosine 1.0): the stored
  crop padded square with black, 224 px, RGB, each model's mean and standard
  deviation; distance = 1 − cosine. CLIP fails on OpenCV 5's new graph
  engine and runs only with `engine=cv2.dnn.ENGINE_CLASSIC` (PYTHON 43).

| Candidate | Nearest dog right, day / night | Wrong when naming 90 % (day / night) | Person crops named a dog there | Two-dog crops named | ms per crop, M900 | MB | Licence |
|---|---|---|---|---|---|---|---|
| Histogram, today | 98/103 / 42/46 | 2 / 3 | 5 of 5 | 12 of 13 | ~1,200 (GrabCut) | — | ours |
| **DINOv2-small** (the CLS token) | **103/103 / 46/46** | 0 / 0 | 0 of 5 | 9 of 13 | 123–171 | 88 | Apache-2.0, code and weights |
| CLIP ViT-B/32 image encoder | 100/103 / 42/46 | 2 / 2 | 0 of 5 | 10 of 13 | ~102 | 352 | MIT |
| MobileNetV3-Large, pooled | **103/103 / 46/46** | 0 / 0 | 0 of 5 | 7 of 13 | **12** | **12** | BSD-3 code; weights trained on ImageNet |

Review 25 ran DINOv2 and MobileNet again on the M900 and got the same
numbers (123 and 12.8 ms). Where a person crop lands is the telling part:
under the histogram, inside the right answers (their 12th to 87th
percentile) — the user's report; under DINOv2 and MobileNet, at the 95th
percentile or beyond. At the threshold that names 90 % of the views (DINOv2
0.337 by day, 0.363 at night; MobileNet 0.287 and 0.344) no person crop is
named, and the nearest one sits about 0.11 further. A two-dog crop is named
the dog that fills more of it, by every candidate: arguably right, but the
second dog is missed.

**What the bench cannot say.** The leave-one-out is optimistic: views of one
event are different frames, so a view's own event may still be among the
references, and a leave-one-event-out needs each view's clip, which views do
not record (R55). And the two dogs are white and black. A household with two
dogs of one colour, or of one breed, is where the choice matters most, and
nothing here measures it.

**The choice for step 2 (review 25): DINOv2-small.** It ties MobileNet on
everything measured. It wins on what was not: DINOv2 is trained without
labels to tell images apart, while MobileNet's pooled layer is trained to
put every dog of a breed into one ImageNet class — ImageNet has 120 dog
breeds — which is the opposite of what two Labradors in one house need
(CONTEXT 3: each household teaches its own dogs). Its licence covers the
weights, with nothing for the user to weigh. Its cost, ~150 ms per crop,
is below GrabCut's on the bench's 320 px crops — but not in the live loop,
where GrabCut ran on small boxes (above).

**The model's file (R53 step 2).** `downloads.py` fetches
`onnx-community/dinov2-small`'s `onnx/model.onnx` at a pinned commit
(`8b1f705a…`) and keeps it only with the pinned SHA-256 (10.2): 88,532,934
bytes, `models/dinov2_small.onnx`. Against the developer's own export from
step 1, its CLS token gave cosine **≥ 0.99999988 on all 167 bench crops**
(the plan asked ≥ 0.9999), so no export of ours had to be published.
Review 26 checked Hugging Face's own record of that commit: the file's LFS
SHA-256 is the pinned one, and `base_model` is `facebook/dinov2-small`.
**The licence:** the weights are Meta's `facebook/dinov2-small`,
Apache-2.0; the ONNX file is a format conversion by the `onnx-community`
organisation (for Transformers.js), whose card states no licence of its
own, and a conversion of Apache-2.0 weights carries Apache-2.0's terms.
Nothing for the user to weigh in a private home system.

**The migration** is the faces' (10.14), shared: `dogs.migrate_gallery`
writes `dogs/gallery_dinov2_small.json` (`GALLERY_FILE`, with `model` and
`source`); `dogs/gallery.json` (`LEGACY_GALLERY_FILE`) is **never written**
again, so `v2026.10.14.3`, restored by a rollback, reads it as it was.
Every chosen and waiting view is described again from its photo in
`dogs/views/`, keeping ids (the sightings point by `dog_id`), names,
favourites, residents and thumbnails; a backup first
(`backups/dogs_dinov2_small_<stamp>`), the `FileLock`, its line in the log
after `log.to_file()`, and a rerun only when `gallery.json`'s SHA-1
changes. **The infrared flag is carried from the old descriptor**, not
judged again on the stored JPEG: it was judged on the whole widened region
of the frame, the better evidence. `tools/dog_crops.py` and
`tools/settle_waiting.py` run the migration first, since a tool that wrote
the new file before the program's first migration would have its work
replaced by it. **Measured on a copy of production's `dogs/`** (46 entries,
2 named, 124 chosen + 81 waiting = 205 views): **205 kept, nothing dropped,
29.5 s**; the old file's SHA-1 unchanged; a second run does nothing; the new
file is 1,735 KB against 251 KB. The test copy's real start with that copy:
30.2 s, inside the 90 s health check (18.7).

**Undo of a report taken before the switch.** A dog report holds the entry
as it left — 41-number histograms in every report production holds on
15/10. `DogGallery.refit` describes the entry again from its photos when its
sizes are not 385, as faces' `put_back` does (10.14). Review 26 undid two of
production's real reports on a scratch copy — one from 12/10 with its
copies, and the older form from 10/10 that kept only one crop — and both
came back with 385-number descriptors.

**Where the thirteen misfiled views land** (`PENDING.md`; each against the
clean views of each dog, near-copies under 0.01 left out): the five person
crops are no dog; the Mirana filed under Aurora (`d6bb2c`) is "probably
Mirana"; of the six two-dog crops five are "probable" one dog or the
other and one is no dog, none sure; `6b3d84`, unclear, is no dog. The new model sees them right — but
they are still **in** the galleries, four of them in Chosen, where every
match is measured against them. Deleting them is the user's (`PENDING.md`).

**Until `v2026.10.14.3`: colour histograms.** `fur_mask` cut the dog out of
its box with OpenCV's GrabCut (a graph cut over colour models of "inside"
and "outside"), and 41 numbers described the fur: the infrared flag, 16 tone
bins, and 16 hue + 8 saturation bins by day; the mean Bhattacharyya
distance compared them (sure 0.35, probable 0.5). Without GrabCut the box's
mat, floor, sun and shade had smeared every tone together. It worked while
the dogs were one white and one black by day, and failed at night and on
anything dark (R53). `fur_mask`, the histograms and the distance now live
only in `tools/dog_bench.py` (`histogram_describe`, `histogram_distance`),
as the bench's baseline; the bench also gained `--limits` for the ratio
sweep above.

---

## 21. Bad-detection reports — `reports.py` (11/10/2026)

**Where the rest of this section went.** Until 12/10/2026 this section
collected every fix of the general review of 11/10; each now lives with its
subject: the page never stale (R28) 17.11 · pairing a device (R34) 17.12 ·
playing a recording (backlog 5) 17.13 · the 40 most different views and
Chosen and Waiting (backlog 24, R40) 17.14 · quiet disconnects (R32) 17.15 ·
the side face (R30) 10.12 · a cheaper face scan (R31) 10.13 · dogs gathering
their look-alikes (R29) 20 · the ratio kept at 2.0 (R35) 7.9.

### 21.1 Report, do not delete (backlog 23)

Every unnamed face or dog card, and every label of a recording in the player, has "Bad detection": the crop leaves the gallery (or the label the card) and is kept in `reports/<kind>/` — the crop and a JSON with `kind` (face, dog), `source` (gallery, event), `verdict` ("not a dog"), label, score, box, camera, time and clip; gallery entries also keep their embeddings and sightings. Nothing learns from it yet: it is the evidence every rule change is measured against. Not versioned (it holds the household's images).

### 21.2 Undo, and "Actually…" (R38, R37)

Settings lists every report, newest detection first, with its crop, verdict, camera, time and origin, and two controls. **Undo** puts back what the report took: a gallery report returns the entry to its gallery as it left — views, waiting views, favourite, first seen — copies its view photos back to `views/` and its sightings (JSON and crop) to their day folders; an event report takes the label out of `reported_labels`, so the card shows it again (refused with 409 when the recording was archived off this computer). The report is then deleted. For that, a report now keeps the whole entry, the sighting file names (`sighting_files`) and copies of every photo in `reports/<kind>/<stem>/` — the old `take_out` deleted the view photos, leaving nothing to restore. The two reports written before (production, 10/10) undo too: embeddings and sightings come back, and the report's crop stands in for every photo — as the view when the entry had one view, which both have, else as the entry's thumbnail. **Actually…** is an optional choice per report — person, dog, other animal, nothing, minus the label the detector gave — stored as `actually`; it is set in the list rather than at report time, so it works for reports already made and the report button stays one click. Reports remain evidence, never trained on.

### 21.3 A report holds exactly what left the gallery (R36)

The first version copied the entry, wrote the report (slow: files copied), then removed the entry by id — a view a scan added in between was removed with the entry, its photo deleted, and in no report. Now `Gallery.take_out` removes the entry **under the gallery lock and returns it**, the report is written from that object, the photos copied, and only then deleted (`forget_views`); if writing raises, `put_back` returns the entry. A scan that matches the entry after it left is refused like any vanished entry. The same idea as Java's `map.remove(key)`, which hands back the removed value, instead of `get` followed by `remove` (PYTHON 26).

## 22. Residents, notification modes and commands from the phone (12/10/2026)

Backlog 25, decided by the user on 12/10/2026 and built in developer session
13. The reason was counted in production's log: from 10/10 01:16 to 12/10,
143 messages, 73 of them "person" at the start of an event and 34 naming a
face — 21 of those the user. Being told hundreds of times that the people who
live here walk around the house is noise; a mode decides what reaches the
phone, and **recording never changes**.

### 22.1 The Resident tag

A named person or dog can be marked **Resident** on its page (the switch is
hidden while the entry has no name). Stored as an optional `"resident": true`
on the entry in the face or dog gallery (19.2), and removed —
not set to `false` — when switched off. A plain rename keeps it; a merge makes
the target a resident when either side was one (`Gallery._merge`). The grid
card shows a "Resident" badge. The face scan copies the flag into each
sighting it returns, so the notifier needs no second read of the gallery.

### 22.2 Nine cases, three modes

`modes.py` holds the rules as data. Each message belongs to one **case**:

| Case | When |
|---|---|
| `resident_person` | a face matched **for sure** (score ≥ the sure threshold, 0.40 unless the user chose another, 10.15) to a person marked Resident |
| `probable_resident_person` | a face matched as "probably …" (score under the sure threshold) to a person marked Resident — since backlog 30 |
| `known_person` | any other named face, sure or "probably …" |
| `unknown_face` | a face with no name |
| `faceless_person` | a person with no recognisable face: the side-view or best-view message; since R42 (b), also a person hiding beside silenced faces (22.3) |
| `resident_dog` | a dog matched for sure to a dog marked Resident |
| `probable_resident_dog` | a "probably <name>" of a dog marked Resident — since backlog 30 |
| `other_dog` | any other dog: another name, "probably" another, unidentified |
| `other_animal` | cats, birds and every other animal label |

**Only a sure match is the resident.** A stranger who looks a little like the
user gets "probably Gustavo", so on 12/10 every "probably …" went to
`known_person` and was never silenced. **Since backlog 30 (13/10/2026) a
probable resident has a case of its own**, so whether it is silenced is the
user's switch and not a rule in the code. The user's reason: "I have not seen
a wrong maybe", and in Home most of the residents' messages were probable —
measured on 13/10, 72 of 134 named face sightings (the user 25, Izabel 47).
The rule is the same; the default changed, and one tap undoes it. If the dog
matching fails, the dog is `other_dog`, never the resident.

`notify.person_case` makes the person's choice from the face scan's
sighting; `dogs.identify` returns, with each dog's words, `"sure"` or
`"probable"` when the dog matched is a Resident and `None` otherwise, and
`clips.DOG_CASES` turns that into the case.

One **mode** is active — **Home**, **Away** or **Silent** — and each mode has
its own switch per case, all editable. The defaults:

| | Away | Home | Silent |
|---|---|---|---|
| Person cases | all on | all on except `resident_person` and `probable_resident_person` | off |
| `resident_dog`, `probable_resident_dog` | from `notify_labels` | off | off |
| `other_dog` | from `notify_labels` | from `notify_labels` | off |
| `other_animal` | from `notify_labels` | from `notify_labels` | off |

"From `notify_labels`" means on only if the older setting listed that label —
production's lists only `person`, so no animal message appears until the user
turns one on. A person with no recognisable face is on in Home: the user's
choice, since a stranger in the dark must reach the phone.

Stored as two optional keys in `config.json`: `notify_mode` and
`notify_modes` (`{mode: {case: bool}}`). `settings.load()` always returns both
whole — `modes.normalised` fills every missing mode and case from the
defaults and drops anything it does not know — so an older `config.json`
behaves exactly as before: Away with today's switches. A case added later
starts at its own default: production's file, written before backlog 30,
gets both probable cases off in Home, the person one on in Away and the dog
one off there (its `notify_labels` is `["person"]`). Someone who had turned
`known_person` off in Away would now get probable residents there, from the
new case's default; production had not.

### 22.3 The timing rule: a person waits for the face scan

A dog is named from the first frame (about 100 ms of matching), so a resident
dog is left out of the very first message. A person is named only after the
clip is assembled and scanned (CONTEXT 3, "Rosto no clipe"), seconds after
the event ends. So:

- **If every person case is on** (Away), nothing changes: the immediate
  "person" message, then the face, side-view or best-view follow-ups.
- **If any person case is off** (Home, Silent, or a custom mode), the person
  is **held**: the first message goes out without them (or not at all), and
  the person's only message comes after the scan — each face by its case,
  or, with no face, the side view or best view as `faceless_person`.

`notify.event(camera, parts, photo)` takes `(words, case)` pairs — a person's
case is `None`, unknown until the scan — and returns `(sent, held)`.
`EventRecorder` keeps `person_held`; a person arriving mid-event
(`_notify_late`, 12.8) is held the same way, even after a dog's message went
out. `notify.after_scan` sends everything that follows the scan:

- faces: each by its case, three at most, each person with their own
  cooldown; a silenced resident no longer uses up one of the three places;
  when the person was held and a face went out, it claims the camera's
  cooldown, as a first message would;
- no face: `faceless_person`, if on. A follow-up when the event already sent
  a message, held or not; when the person was held and nothing of the event
  went out, it is the first message and answers to the camera cooldown.

**Fixed in review 15 (`5224983`).** The first version checked the camera
cooldown for every held faceless message, so in Home with a dog switch on, a
dog message sent a moment earlier in the *same* event silenced the person with
no face. And a held person whose clip could not be assembled (no segments)
got no message at all, since the assembly returned before the scan; it now
sends the best view. Both were reproduced by a test first.

**Someone hiding beside a resident (R42 (b), 14/10/2026).** Until then, in
Home, if the scan found a resident's face and a second person never showed
one, nothing was sent: the faceless message went only when no face was found
at all. The scan cannot tell one person from two by faces; YOLO can, by
counting person boxes in one frame. The user's rule: "if it errs, it errs" —
someone the system cannot account for always wins over silence (CONTEXT 3).

- `EventRecorder._consider_view` keeps `most_people`, the most person boxes
  in one analysis frame of the event — **at once, never summed** over the
  event, so two people passing one after the other count as one. It is
  reset in `_start`, written to the event's JSON (8.4) and handed to
  `_assemble` and `after_scan` as `people=`.
- `after_scan` sends a picture as `faceless_person` when the scan found
  faces, the person was **held**, **every** face found was silenced by its
  case, and `people` is greater than the faces found. Text: "Front
  14:02:11: 2 people seen, 1 face found" (`notify.hidden_person`; until
  `v2026.10.14.3` it ended ", best view"). The faces found are distinct
  people: `_scan_clip` skips a second group that matches a person already
  seen.
- One helper, `_faceless`, now holds the faceless rules for the side view,
  the best view and the hidden person alike: the `faceless_person` switch;
  then, when the person was held and nothing of the event went out, the
  camera's cooldown, as a first message; otherwise only after a sent event.
- **What it costs, accepted by the user:** anything YOLO keeps as a person
  counts — a dog relabelled by R44 or R46 (7.12, 7.13), or YOLO calling a dog
  a person (R18) — and costs one extra message. So do two residents leaving
  together with one face seen: the system cannot tell that from a stranger.
  Two boxes on one body are what NMS (0.45) and `drop_duplicates` remove
  before anything is counted.
- **The picture is the frame where the people were counted** (R56,
  15/10/2026). Until then it was the best single view, chosen by one
  person's confidence × height, and the phone could show only the resident
  under "2 people seen" — the message existing for the person not in it.
  Now `_consider_view` keeps the frame and its subjects (`people_view`)
  each time the count of persons in one frame **rises**, so the frame kept
  is the first one with the most people; `stop()` writes it, boxes drawn as
  on the thumbnail (8.5), as `HH-MM-SS.people.jpg` **only when
  `most_people` ≥ 2** — the only case this message can fire, since it needs
  more people than at least one face found — names it in the event's JSON
  (`people_thumbnail`, 8.4) and hands it to `after_scan` as `people_view=`.
  The best view stays the fallback when that file is missing. The base name
  is shared, so the archive moves it with the event (19.2).

### 22.4 Notifications, the first part of Settings

**Since backlog 27 (12/10/2026, the user's)** Notifications is not a tab of its
own: Settings has a sub-navigation — Notifications · Detection (7.14, since
backlog 31) · Other devices · Archive · Bad-detection reports — and each part is shown as `#settings/<part>`; no part,
or an unknown one, shows Notifications. An old `#notifications` link is
replaced by `#settings/notifications` with `location.replace`, which adds no
history entry, so Back does not bounce. The reports list is read only when its
part is shown. On a 375 px phone the five tabs wrap to two lines (checked in
review 24); none is cut.

The part itself: the active mode as three radio buttons at the top, and a table with the cases in rows and the modes in
columns, the active column tinted. Each cell is a real form control —
`<input type="checkbox" role="switch">` — drawn as a switch by CSS alone
(PYTHON 29). Flipping one posts `{"notify_modes": {mode: {case: bool}}}` at
once; the server refuses unknown modes, unknown cases and anything that is
not `true` or `false`, and merges the change over the stored switches. The
Telegram form (token, chat, Find chat, test, prefix, cooldown) sits **beside
it** where the screen is wide enough, below it on a phone (backlog 36,
14/10/2026, the user's): the part is a grid of `minmax(0, 3fr)` for the table
and `minmax(300px, 2fr)` for Telegram, `align-items: start`, and one column
under 860 px — so the app's pane at its default width (~800 px) shows one
column too (PYTHON 42). The older per-label checkboxes are gone:
`notify_labels` is still read, only to build the defaults.

### 22.5 Commands from the phone — `bot.py`

A thread in production reads the bot's messages with **long polling**:
`getUpdates` with `timeout=50` keeps the request open until a message arrives
or 50 s pass (PYTHON 27). It is an outgoing connection like sending, so **no
port is opened** on the M900.

| Command | Does |
|---|---|
| `/on`, `/off` | switches analysis On or Off (22.7) and says what that means |
| `/home`, `/away`, `/silent` | makes that mode active and answers with what it sends |
| `/mode` | shows the active mode, with one tap button per mode, and "Analysis: On" or "Off" |
| any other `/command` | the list of commands, and the same On or Off |

`setMyCommands` lists them in Telegram's "/" menu, once per token. The bot
changes the mode and analysis On or Off, and **nothing else**. Only the configured `notify_chat` is
obeyed; a message from any other chat is logged ("ignored a message from chat
N") and its taps answered empty. A command older than 120 s is ignored, so a
restart does not replay yesterday's `/away` (Telegram keeps unread updates for
24 h). A tap on a mode button has no date and is obeyed whenever it arrives:
at worst, it sets the mode the user tapped.

**One reader per bot.** Telegram hands each update to whoever asks and forgets
it once the next `offset` is confirmed; a second program polling the same bot
gets **409 Conflict**. So Find chat, which used to call `getUpdates` itself,
now asks the running poller for the chat it saw last (`bot.last_chat()`), and
only falls back to `getUpdates` when no poller runs. The test copy has no
token, so its poller only sleeps; if a token were pasted there, one of the two
would get 409, log it once and back off for two minutes.

Trouble — network, 409, a refusal, an unexpected exception — is logged once
per distinct problem as `Telegram commands: …` and retried after 5 s,
doubling up to 5 minutes. Capture never waits on it, and the token is
redacted from every line (R16).

### 22.6 A move names the photo it was shown (R41)

The four view moves and the favourite address a view by its position, and a
scan that replaces a chosen view (17.14) shifts every later position by one, as
another tab's move does. Each move now also sends the name of the photo the page showed at that
position (`{"view": "<name>"}`, "" for a view without a photo); the gallery
compares it **inside its lock** and raises `ViewsChanged`, which the server
answers with 409 "the views changed: the page was refreshed", and the page
reloads the person. Without the field the move behaves as before. Checked on
production's galleries: every stored view has a page URL, so the name the
page sends always matches a stored one (PYTHON 28).

### 22.7 Analysis On and Off — `analysis.py` (backlog 29, 13/10/2026)

The user asked to switch J.A.R.V.I.S. off from the phone for a while without
stopping the cameras. `/off` stops everything after capture: motion, YOLO,
events, recordings, the face scan and messages. Capture keeps running, so
Live and every other screen work as before, and the rolling buffer keeps
being written and cleaned (5.5). `/on` resumes.

**Held in memory only, on purpose.** `analysis.py` is a module with one flag
and four functions — `is_on`, `set_on` (returns whether the state changed),
`off_for` (seconds Off) and `describe` ("On" or "Off") — and no file. So
every start begins On: a restart, a crash, the production task's trigger
every 5 minutes (18.7). Off is an occasional state; an Off that survived a
reboot would be a camera system recording nothing with nobody noticing. A
module's globals exist once per process — the C# static class (PYTHON 36).

**What `Core.step` does while Off.** It still reads every camera's frame —
Live depends on it — but skips motion and YOLO and calls
`recorder.update(frame, [])`. The recorder is told nothing was seen, so an
event open at `/off` ends after `POST_SECONDS` exactly as if the motion had
stopped, and then **finishes as any event does**: clip assembled, face scan,
its follow-up messages. That is the decision's "ends as if the motion had
stopped" read literally: `/off` stops what would start, not what was already
on its way. The per-minute count of analysed frames stops (12.10).
`_switch_analysis` follows the flag once per step: it logs "Analysis On" or
"Analysis Off", clears the subjects drawn on Live, and on the way back On
gives each camera a **fresh `MotionDetector`** — the old background is
minutes or hours stale, so motion relearns it, blind for `WARMUP_FRAMES` as
at start (6.4).

**The reminder.** While Off, the bot's poller sends the configured chat
"Analysis has been Off for N h: nothing is recorded or sent. /on resumes
it." every `REMINDER_SECONDS` = 3 h, counted from the moment it went Off. It
is checked before each long poll, so it leaves within a minute of the mark.
Each mark gets one attempt: a reminder lost to a network failure waits for
the next one. Only `notify_chat` can switch analysis, as with the modes.

**On the page.** `/api/status` carries `analysis`, and the header shows "On"
in green or a red "Off" badge on every screen, refreshed by the 5-second
health check (17.8).

**Switched from the page too (backlog 34, 14/10/2026).** The user, during
review 23: "on the screen where the status shows, it must be possible to
switch it on and off there too". The header's `#analysis` is a `<button>`: a
click posts `{"on": bool}` to `POST /api/analysis`, which calls
`analysis.set_on` exactly as `/on` and `/off` do — the same flag, still never
stored, and the bot's 3-hour reminder follows — and logs `Web: analysis Off
from the page` beside the Core's `Analysis Off`. The answer is `{"analysis":
"On"|"Off", "changed": bool}`; anything but a boolean `on` is a 400. It is a
write, so the write guard applies (17.12, R24): refused without the page's
header, and from another device without the paired PIN — tested in
`tests/test_on_off.py`. **Turning Off asks first** with the browser's
`confirm()` — "Switch analysis Off? Nothing is recorded or sent until it is
switched On again; Live keeps working." — since it stops all recording;
**turning On is one click** (the user, 14/10/2026; PYTHON 42). A refused
write shows `alert("Not done: …")`, the page's only `alert`, because the
header has no result line; review 24 kept it, since it happens only on a
device that is not paired. On a 375 px phone the button sits beside the
version, 39 × 32 px.
