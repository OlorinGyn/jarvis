# Handoff - developer to architect

Developer session 1, 10/10/2026, about 00:00-00:30, on the M900 (`Sasori`),
following CONTEXTO 14.4 in its order. Production (`C:\JARVIS`, v2026.10.09)
was not touched: only `production.ps1 -Action status`, at the start and the
end, both healthy (both cameras 0.0-0.1 s). Nothing was pushed.

## 1. Items done

| # | Item | Commit | Closes |
|---|---|---|---|
| 1 | No console windows | `9eaa42c` | R15 |
| 2 | Notification outcomes in the log, token redacted | `9ae537b` | R16 (+ R10 for `discover_chat`) |
| 3 | Camera error advice and "Unknown" in English | `f475fdc` | R10, the part in `capture.py`, `notify.py`, `faces.py` |
| 4 | The event's picture is its best view of a person | `085b3b6` | R19 |
| 5 | Dense face scan where persons were seen | `668588d` | R20 |
| 6 | `settings.save()` keeps unknown keys | `524b14f` | R11 |

**R15.** `capture.NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)`, passed
as `creationflags` at the four call sites (`FFmpegCamera.start`,
`clips._concat`, `faces._describe`, `faces._sampled_frames`). Not
`clips.reveal`.

**R16.** `_redact()` removes the token (literal, plus a `bot<digits>:<key>`
pattern, also `%3A`-encoded) from every detail `_call()` and
`discover_chat()` return, so no caller can leak it. `event()`,
`faces_seen()` and the new `best_view()` send through `_send_logged()`, which
logs `Notification <camera> <labels>: sent` (INFO), `skipped: cooldown` (INFO)
or `failed: <detail>` (**WARNING**, not INFO as R16 says: so a failed send
shows up when the log is checked for warnings). `_allowed()` was split into
`_wanted()` and `_cooled_down()` to tell the two skips apart; a label nobody
asked for stays silent, as before. A thumbnail that cannot be read is now a
failed send instead of a dead thread.

**R10.** `capture.TRANSLATIONS`, `wait_ready()`'s "FALHOU - ..." (now
"FAILED - ..."), `notify.discover_chat()` messages, `Gallery.label()`'s
"Desconhecido" (now "Unknown"). Nothing parsed those strings (checked
`tools/`, `.bat`, `static/`).

**R19.** `EventRecorder._consider_view()` keeps a copy of the frame where a
person scores best, `confidence * box height` (standing beats lying down), and
`stop()` writes it as `HH-MM-SS.best.jpg` plus `"best_thumbnail"` in the event
JSON. `web._event()` serves it when the file exists; `SAFE_THUMB` accepts
`.best.jpg`. The first Telegram message keeps the first frame. In `_assemble`,
when the event notified and the scan found no face (or the scan raised), the
follow-up is the best view via `notify.best_view()`, unless the best view is
the very frame that was already sent (`moment == sent_moment`).

**R20.** `EventRecorder._note_person()` keeps wall-clock spans of person
sightings (gap over `PERSON_GAP_SECONDS` = 2 opens a new one). `_assemble`
turns them into seconds into the clip with `_clip_moments()`, counted from the
first segment's name (`SEGMENT_FORMAT`). `faces._selection()` builds the
ffmpeg `select` expression: the old sparse pass, plus every `DENSE_EVERY` (2)
frames inside the spans widened by `DENSE_MARGIN_SECONDS` (1.5) and merged,
capped at `MAX_DENSE_SAMPLES` (300) by coarsening the step. `scan_clip()` gained
an optional `moments=()`; `tools/refazer_rostos.py` still calls it without,
so a rescan stays sparse.

**R11.** `save()` rereads the file and keeps every key not in `DEFAULTS`;
`load()` still returns only known keys.

## 2. Data-format impact

All additive:

- New optional file per event, `HH-MM-SS.best.jpg`, only when a person was
  detected. Moves with the event on archive (`archive.py` globs `base.*`).
- New optional event JSON field `best_thumbnail` (the file name). Events
  without it show the first frame, as before. An older version ignores it.
- `config.json` may now keep keys this version does not know. Note: the
  version in production still drops them on save; R11 only protects once it
  is released.
- No change to `faces/`, `gallery.json`, `.env`.

`uv run python tools/check_data.py` before each data commit: **150 events,
gallery 7 persons, 20 sightings, config.json 8 keys, every file readable.**

Test data changed in the test copy (not production): `clips/Front/2026-10-09/22-29-22.*`
copied from production; its JSON was given `best_thumbnail` and a
`22-29-22.best.jpg` made by the replay below, to simulate what the new code
would have written. A sighting the R20 replay wrote into `faces/2026-10-10/`
was removed (it pointed at a scratch clip); `gallery.json` was not modified.

## 3. Suggested documentation updates

- **ARQUITETURA 5 / 8 / 19** (event files and format): `HH-MM-SS.best.jpg`,
  `best_thumbnail`; the follow-up message rule; `clips.py` docstring already
  lists the file.
- **ARQUITETURA 10** (faces): dense sampling around person spans, the three
  constants, the measurements in section 5 of this file, and that rescans with
  `refazer_rostos.py` stay sparse.
- **ARQUITETURA 11** (settings): `save()` keeps unknown keys.
- **ARQUITETURA 12** (notifications): the log lines and their levels; the token
  redaction in `_call()`; `best_view()` as the follow-up when there is no
  face; `_wanted()` / `_cooled_down()`.
- **ARQUITETURA 18.7**: windows are gone with `CREATE_NO_WINDOW` once released;
  remove or reword the "production started in the user's session gets
  windows" caveat after the release reaches production.
- **CONTEXTO 13.4**: R11, R15, R16, R19, R20 done (commits above). R10 progress:
  still Portuguese are `ui.py` (including its Telegram test message
  "teste de notificacao"), `cameras.build_camera_list()`'s `SystemExit`
  ("Preencha ... no .env"), `tools/diagnostico.py`, the Portuguese file names.
- **CONTEXTO 13.6 / 4 (testing knowledge)**: to detect a console window, the
  presence of a `conhost.exe` child is **not** a signal — Windows creates one
  under `CREATE_NO_WINDOW` too, and with Windows Terminal as the default
  terminal the visible window belongs to `WindowsTerminal.exe`. What works:
  from a process with no console, `AttachConsole(pid)` then
  `GetConsoleWindow()`, which is NULL without a window. Also: a script run
  under `pythonw.exe` that calls `subprocess` with captured output needs
  `stdin=subprocess.DEVNULL`, or it dies silently on an invalid handle.
- **CONTEXTO 14.3**: the usage row (section 8 below).

## 4. Worth explaining to the user

- `subprocess` `creationflags` and `CREATE_NO_WINDOW`: C#'s
  `ProcessStartInfo.CreateNoWindow`. Why a console program started from
  `pythonw.exe` gets a window, and why `conhost.exe` still exists without one.
- `getattr(obj, name, default)`: reading an attribute that may not exist,
  like `?.` plus `??` in C#.
- `logging.getLogger(__name__)`: one logger per module, handlers inherited from
  the root, like SLF4J's `LoggerFactory.getLogger(...)`.
- Regex substitution for redaction (`re.compile`, `.sub`), and why the
  redaction belongs at the one place the secret enters text.
- ffmpeg's `select` filter: `n` and `t`, `mod`, `between`, and `+` as a
  logical OR; `\,` escaping inside a filter graph.
- numpy arrays are references: why `_consider_view` stores `frame.copy()`.
- `{**a, **b}` dict merging and which side wins (R11).

## 5. Measurements

**R15**, every ffmpeg of the test copy checked with
`AttachConsole`/`GetConsoleWindow`, while a `pythonw` process assembled clips
and scanned faces for 20 s: before, 6 of 10 ffmpeg processes had a window;
after, 0 of 11. Capture: 0 of 2. The same 20 s of work ran 10 rounds instead
of 6 once no window had to be created.

**R16**, fake token with the real token's shape, test copy's `logs/`:
wrong token gives `failed: Unauthorized`; "network cut", simulated with a dead
HTTPS proxy in that process only (the M900's network was not touched), gave a
detail holding the token before the fix, `/bot<token>/sendPhoto` after.
Cooldown logged. Real token (read in-process, never printed): found in no
file of the test copy's `logs/` nor of `C:\JARVIS\logs`.

**R19**, the 22:29 clip replayed at 10 fps, 960x540, paced in real time,
through the real `MotionDetector`, `SubjectDetector` and `EventRecorder`
(camera and notify stubbed): the replay split it into two events; both
`.best.jpg` show the user (22:29:20 leaving, 22:29:55 returning), the first
frames show the dog as `cat` and a half-cut figure at the door. On the copied
event in the test copy, the Recordings card shows the user (checked in the
browser, port 8766).

**R20**, M900, production running alongside:

| | frames read | usable faces | time | found |
|---|---|---|---|---|
| every frame (reference) | 844 | 5: frames 113, 585, 605, 606, 608 | 121 s, **143 ms/frame** | — |
| sparse, before | 60 | 0 | 12 s | nothing |
| dense step 4 (cap 150) | 182 | 1 | 33 s | one unnamed match, 79 px |
| **dense step 2 (cap 300), shipped** | 300 | 3 | **45 s** | **Gustavo Henrique Gomes**, 2 views, 41 px, score 0.421 ("probably"), plus the unnamed one |

Person spans for that table came from the first event of an end-to-end replay
(real detectors, real recorder, real scan) whose fake segment was named with
the replay's wall-clock start. The later events of that replay are not valid:
the scan running concurrently slowed the file replay behind the wall clock,
which production cannot do (capture drops frames instead).

## 6. What the review should look at hardest

1. **R20's CPU cost on the M900.** Up to 360 frames of YuNet on 1080p, ~45-55 s
   of OpenCV DNN, which is multi-threaded, per event with a person (notified or not),
   competing with live analysis on 4 cores. Its effect on the live frame rate
   was **not measured**. And on the Front camera the dog detected as `person`
   (R18) keeps the spans open, so "dense where persons were seen" became most
   of the clip. Options if it matters: `cv2.setNumThreads` during the scan,
   running YuNet only on head regions of the person boxes, or fixing R18 first.
2. **Clock alignment in R20.** Spans are `datetime.now()` at analysis time;
   the clip starts at the first segment's name, second resolution, wall clock
   via `-use_wallclock_as_timestamps`. The 1.5 s margin is meant to absorb
   analysis latency and the truncated second. Verified only by replay, not by
   a live event; nothing logs the moments, so the first production events
   cannot confirm it either. Worth a log line, or storing the spans.
3. **R19's score**, `confidence * height`: a standing dog or a tall false
   positive could still win. On the 22:29 clip person boxes were 259-314 px
   high, the dog 166-174.
4. **One more Telegram message** per notified event with no face (the best
   view). It is what R19 asked for; check it does not double the first message
   too often (it is skipped only when it is the same frame).
5. `ui.py` (OpenCV window) still shows the first frame: untouched because it
   is still Portuguese and out of scope.

## 7. Not done

Every item of the plan was done. Nothing outside it was started.

**Proposed** (needs the user, not started): store the person spans as an
optional field in the event JSON, so `refazer_rostos.py` and a future replay
can rescan densely and the review can check the clock alignment.

## 8. Usage

| | 5-hour window | Weekly | Context |
|---|---|---|---|
| Start (~00:00) | 39% (resets 04:10) | 32% | 66k tokens |
| End (~00:30) | 52% | 34% | ~210k tokens |

Per item, 5-hour window: R15 39→42, R16 + R10 42→44, R19 44→48, R20 48→52,
R11 and this handoff under 1 point.
