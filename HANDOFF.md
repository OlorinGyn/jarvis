# Handoff - developer to architect

Developer session 2, 10/10/2026, about 04:10-04:40, on the M900 (`Sasori`),
following CONTEXTO 14.4. **Run in the same conversation as developer session 1**
(the user called `/dev` there again), so the context started at 240k tokens.
Production (`v2026.10.10`) was only read with `production.ps1 -Action status`,
healthy at the start and the end. Nothing was pushed.

## 1. Items

| # | Item | Commit | State |
|---|---|---|---|
| 1 | R21 — analysed frames per minute | `6ff6eda` | measured; the fix is **not** chosen, see below |
| 2 | Backlog 18 — running version on the page | `9aa83f1` | done |
| 3 | R22 — log where each face scan looked | `c5166d1` | done |
| 4 | R17 — `tools/replay.py` | `cc08df1` | done, acceptance met on all three clips |
| 5 | R18 — dog on the mat as `person` | — | **not done: the user decided to leave it for later** |
| 6 | R10, code part — `ui.py`, `archive.py`, `build_camera_list()` | `c6df155` | done |

**R21.** `Core` counts analysed frames per camera; every 60 s `_tally()` turns
them into `per_minute`, served as `analysed_per_minute` in `/api/status`, and
logs `analysed per minute during a face scan: Back n, Front n` when a scan ran
in that minute (`faces.scanning()` = `_SCAN_LOCK.locked()`). The measurement
(section 5) says a quiet scene loses 1-2 %, but **YOLO runs 1.6x slower during
a dense scan** (about 38 % fewer runs with motion), past the "one third" of
R21. The first option, fewer threads, is ruled out by measurement:
`cv2.setNumThreads` is process-global and slows YOLO itself (472 ms at 2
threads, 772 ms at 1, against 280 ms at 4). The other two (YuNet only on head
regions; lower priority) are not cheap: the scan would need person boxes,
and YOLO costs more than YuNet; OpenCV's worker threads are shared, so a
thread priority does not reach them. **I stopped and left the choice to the
review.** A proposal that fits what was measured: the scan waits while any
camera is recording (YOLO runs mostly during events), with a ceiling on the
wait so a busy evening cannot starve it.

**Backlog 18.** `web._read_version()` runs `git describe --tags --always
--dirty` once at import (`CREATE_NO_WINDOW`, stdin from `DEVNULL`, 10 s
timeout), `"unknown"` on any failure. Served as `version` in `/api/status`,
shown muted at the right of the header (`#version`, with a CSS rule so the
"No connection" banner keeps its place).

**R22.** `faces._scan_clip()` logs one INFO line per scan:
`face scan <clip>: dense 7.3-15.7 s, 36.3-42.1 s, 162 frames, 23.1 s, 3 face view(s)`
(or `dense none`). Spans are not stored in the event JSON, as review 3 said.

**R17.** `tools/replay.py <video> [--start] [--end] [--all] [--prime]`.
`MotionDetector` and `SubjectDetector` gained `trace` (a list, `None` by
default) filled by `_drop(reason, ...)`; `SubjectDetector.detect()` gained an
optional `now`, so MIN_INTERVAL and the static spots follow the video's time.
Reasons: too small, few changed pixels, lighting change, not confirmed (n/3),
whole frame changed, warming up; animal below confidence, person too short, no
motion overlap, duplicate, static spot; and "YOLO not run" inside
MIN_INTERVAL. `--prime` learns the background from the first 6 s first: a
fresh MOG2 is blind for 6 s, exactly where an event's pre-roll ends.

**R10.** `ui.py` text and its Portuguese identifiers; the view "Ajustes" is now
"Settings", the weekday row S M T W T F S; the Telegram test text. Also
`archive.py`'s two "not ready" reasons (shown on that screen) and
`build_camera_list()`'s `SystemExit`. `PLACEHOLDER_IP = "ip-da-camera"` stays:
it is compared against `.env`, so it is data, not text.

## 2. Data-format impact

None on disk. `/api/status` gained two optional fields, `version` and
`analysed_per_minute`; `production.ps1` reads only `frame_age`.
`check_data.py` was not needed (nothing read from or written to disk changed);
last run in this conversation: every file readable.

Test copy only: `clips/Front/2026-10-09/20-23-07.*` and `20-29-03.*` copied from
production for R17.

## 3. Suggested documentation updates

- **ARQUITETURA 7 (motion, YOLO)**: the optional `trace` and `now`; the drop
  reasons, which are also the clearest list of what each layer filters.
- **ARQUITETURA 10 / 12.9 (face scan)**: the R22 log line; `faces.scanning()`.
- **ARQUITETURA 17 (web)**: `version` and `analysed_per_minute` in
  `/api/status`; the version in the header.
- **ARQUITETURA 18 / CONTEXTO 10 (useful commands)**: `tools/replay.py`, with
  `--prime`, and what it showed (section 5).
- **CONTEXTO 13.4**: R17, R22, backlog 18 done; R21 measured, fix open; R10
  code part done — left: older docs, `tools/diagnostico.py`, Portuguese file
  names; R18 deferred by the user (10/10, during this session).
- **CONTEXTO 11 (biases)**, maybe: "fewer threads for the scan" sounded
  obviously right and measured wrong.

## 4. Worth explaining to the user

- `threading.Lock.locked()` — asking whether a lock is held without taking it.
- Why one thread pool for all `cv2.dnn` networks means two networks running at
  once share four cores, and why `setNumThreads` cannot give each its own.
- `subprocess.run(..., timeout=...)` and catching `SubprocessError`, and
  `git describe` (tag, commits since, hash, `-dirty`).
- The trace pattern: an optional list a class appends to only when someone
  set it — no cost and no behaviour change otherwise. Python's equivalent of
  injecting an optional listener in Java.
- Passing the clock in (`now=None`) so code can be replayed deterministically.
- argparse, Python's `CommandLineParser`.

## 5. Measurements

**R21**, M900, production running alongside, test copy cameras (stream2),
the real `Core` in-process, dense scans of the 22:29 copy back to back:

| | analysed frames per minute, per camera |
|---|---|
| quiet scene, no scan (2 min) | 584-587 |
| quiet scene, dense scans (4 min, 45 s each) | 575-583 |

YOLO (`_raw_detections`, 960x540 frames of the 22:29 clip, 60 frames):

| OpenCV threads | alone | during a dense scan |
|---|---|---|
| 4 (default) | 280 ms (p90 295) | **454 ms (p90 527)** |
| 2 | 472 ms | 601 ms |
| 1 | 772 ms | 876 ms |

**R22**, on the 22:29 copy: sparse 60 frames 8.8 s, 0 views; dense on two
spans, 162 frames 23.1 s, 3 views.

**R17**: replay at about 20 frames/s (561 frames in ~28 s). Old and new
`motion.py`/`people.py` gave identical results on all 561 frames of the 22:29
clip (same video clock for both). What it shows — the data R18 will need:

| clip | the dog on the mat | real persons |
|---|---|---|
| 20-29-03 | `person` 0.53-0.68, box ~390x109-118 at y≈420, kept | — |
| 20-23-07 | `person` 0.36-0.44, 339x55-61, dropped "too short" | 110-152 x 267-320, 0.38-0.91 |
| 22-29-22 (`--prime`) | 0.57 at 389x92 dropped "too short" (5.3 s); **0.47 at 389x119 kept** (5.6 s) | from 6.5 s, up to 0.91 at 152x315 |

The dog's box is 3-4x wider than tall and touches the bottom edge; every real
person seen is taller than wide. A small static `person` 23x23 at (180,143)
and 34x39 at (695,156) shows up in many frames and is always dropped as too
short. The rule options the user was offered for R18: wide + touching the
bottom edge; wide anywhere; or wait (chosen).

## 6. What the review should look at hardest

1. **R21's fix.** The numbers are above; which option, if any, is a design
   call. Note the quiet-scene number says little: the counter cannot show
   YOLO's slowdown, because YOLO only runs on motion, and the test copy had
   none at 04:00.
2. **`--prime`** primes MOG2 on frames that already contain the event; the
   background then holds whatever was there, which production's long-learned
   background would not. Good enough to reproduce 22:29; worth saying in the
   docs.
3. `ui.py` was translated by exact string and identifier substitution; all
   four views render, but the window was not clicked through (`--window`
   needs the cameras and the desktop).

## 7. Not done

- **R18**: the user chose to leave it for later (asked in this session, with
  the replay's data and two rule options).
- **R21's fix**: measured, option 1 ruled out, choice left to the review.

## 8. Usage

| | 5-hour window | Weekly | Context |
|---|---|---|---|
| Start (~04:10) | 0% (the window had just reset; resets 09:10) | 39% | 241k tokens |
| End (~04:40) | 11% | 41% | ~330k tokens |

Per item: R21 0→3 (two 5-minute measurements), backlog 18 and R22 3→5, R17
5→8, R18 question and R10 8→11. Much of each step's cost is the 240k context
carried over from developer session 1.
