# Handoff - developer to architect

Developer session 3, 10/10/2026, about 13:45-14:20, on the M900 (`Sasori`),
following CONTEXTO 14.4. **Again in the old conversation**: the plan asked for a
new one, the developer asked, and the user chose to continue here (context
336k at the start). Production (`v2026.10.10.2`) was only read with
`production.ps1 -Action status`, healthy at the start and the end. Nothing
was pushed.

## 1. Items

| # | Item | Commit | State |
|---|---|---|---|
| 1 | R23 — pause the face scan while a camera records | `754fa45` | done, acceptance met |
| 2 | R18 — the dog on the mat as `person` | `13bb4d5` | done, **with one deviation**: ratio 2.0, not 2.5 |
| 3 | Backlog 3, stage 4 — People and Settings on the web | `ddc233a` | done, acceptance met; "Archive now" left out on purpose |

**R23.** As decided in 13.8. `faces._wait_while(busy, budget)` runs before each
frame of `_scan_clip()`: sleeps in `PAUSE_STEP_SECONDS` (0.2) steps while
`busy()` is true, at most `MAX_PAUSE_SECONDS` (600) per scan in total.
`scan_clip()` gained an optional `busy`. `clips` keeps every `EventRecorder` in
a `weakref.WeakSet` and passes `recording_now()` (any recorder recording), so
`faces` still knows nothing of cameras. The R22 line now reads
`... 11.7 s (2.0 s paused), ...`.

**R18.** In `SubjectDetector.detect()`, after "person too short":
`people.wide_at_bottom(box, frame_height)` — width more than
`WIDE_PERSON_RATIO` × height **and** bottom within `BOTTOM_EDGE_FRACTION` (3 %)
of the frame's bottom — drops the detection with the trace reason "wide at
the bottom edge". **Deviation: `WIDE_PERSON_RATIO = 2.0`, not 2.5.** Replaying
every person event showed the dog sitting up on the mat at 376-380 × 153-157
(ratio 2.42-2.48): at 2.5, 20 frames of `20-29-03` were still `person`. At
2.0 every drop in 25 events is the mat, and real persons measured 0.4-0.6
wide per tall, so the margin is still four times. Also: `tools/replay.py`
sends ffmpeg's stderr to `DEVNULL` (it printed "Broken pipe" whenever the
replay stopped reading early, as `--prime` does).

**Stage 4.** New routes in `web.py`:

| Route | Does |
|---|---|
| `GET /api/face-days` | days with sightings, newest first |
| `GET /api/people?day=` | that day's sightings: person_id, name, named, time, camera, score, reliable, face_width, thumbnail URL |
| `GET /face/<day>/<HH-MM-SS_xxxxxx>.jpg` | a face crop; `SAFE_DAY` + `SAFE_FACE`, then must resolve inside `faces/` |
| `POST /api/people/<p_xxxxxxxx>/name` `{name}` | `Gallery.rename`; 404 bad or unknown id, 400 empty or over 60 characters; returns `merged` |
| `GET /api/settings` | the settings **without the token**: `notify_token_set` instead, plus label choices and `archive.summary()` |
| `POST /api/settings` | partial update; each key checked (`EDITABLE` types, labels from YOLO's classes, numbers ≥ 0, `archive_after_days` ≥ 1, unknown keys 400); the token is write-only, never empty |
| `POST /api/notify/discover` | `discover_chat` with the stored token; saves the chat |
| `POST /api/notify/test` | sends "J.A.R.V.I.S.: test notification" |

Page: tabs People and Settings, plain HTML and JavaScript like the rest.
People has the day navigation of Recordings and a name field on every card.
Settings has two forms: Telegram, and the archive with its status. The token
field is a password field, emptied after saving; the page only says whether a
token is set. **"Archive now" is not there**: it would run `move_old()` in the
web thread while the `Housekeeper` may run it in the main loop — two movers on
the same files.

## 2. Data-format impact

None new. Names are written by the existing `Gallery.rename` (same
`gallery.json` format; non-ASCII as `\u` escapes, as `json.dumps` always did),
settings by `settings.update` (keeps unknown keys, R11). `check_data.py`
after the tests: 174 events, gallery and sightings, config.json 8 keys —
every file readable.

Test copy only: every event with a `person` label from 09/10 and 10/10 copied
from production into `clips/` (R18). The stage 4 test named a face and saved a
fake token; `faces/` and `config.json` were backed up before and restored
after.

## 3. Suggested documentation updates

- **ARQUITETURA 7 (YOLO filters)**: the wide-at-the-bottom-edge rule, its two
  constants, why both conditions, and why 2.0 (the sitting dog).
- **ARQUITETURA 10 / 12.10 (face scan)**: R23's pause, the constants, the
  WeakSet, the log line with the pause.
- **ARQUITETURA 17.8 (web)**: the routes above; stage 4 done; why the token is
  write-only; why "Archive now" is not on the web.
- **CONTEXTO 8**: backlog 3 complete as far as the web goes — the `--window`
  interface can be retired when the user agrees (17.3 kept it for comparison).
- **CONTEXTO 13.4**: R18 and R23 done.
- **CONTEXTO 14**: a third session carried in the old conversation; the costs
  per item below are inflated by 336-400k of context.

## 4. Worth explaining to the user

- Passing a function (`busy=recording_now`) as a parameter — Java's
  `BooleanSupplier`, C#'s `Func<bool>` — so `faces` does not depend on `clips`.
- `weakref.WeakSet`: a set that does not keep its members alive, like Java's
  `WeakHashMap` keys.
- FastAPI's `Body(...)` with a `dict`, and `HTTPException` for 400/404 —
  compare with ASP.NET's `[FromBody]` and `BadRequest()`.
- `fetch` with a JSON body, `<template>` and `cloneNode`, `FormData`-free forms.
- Why the token is write-only: anyone on the Wi-Fi can open the page (R4).

## 5. Measurements

**R23**, M900, production running (daytime), YOLO on 60 analysis frames:

| | mean | p90 |
|---|---|---|
| YOLO alone | 328 ms | 490 ms |
| during a dense scan | 564-614 ms | 722-887 ms |
| **scan paused (a camera records)** | **342 ms** | 506 ms |

Pause total logged; the ceiling holds (always busy, 1 s ceiling: paused
1.0 s, scan finished).

**R18**, `tools/replay.py --prime` logic on all 25 person events of 09/10 and
10/10 (both cameras), rule at 2.0:

| event | frames with a person kept | dropped by the rule |
|---|---|---|
| Front 20-29-03 | 0 (was 20 at 2.5, before the rule all) | 31, the dog |
| Front 20-29-52 | 0 | 8, the dog |
| Front 13-26-57 (10/10) | 0 | 2, the dog |
| Front 22-29-22 | 146, the user | 2, the dog |
| Front 23-34-13 | 48 | 8, the dog |
| Front 23-34-38 | 81 | 1 |
| Front 23-53-02 | 84 | 2 |
| every Back event, other Front events | unchanged | 0 |

Every dropped box is at x≈460, 320-400 wide, 100-160 high; checked on a
contact sheet of each event's strongest drop: the dog on the mat every time.
Front 13-28-06 and 13-29-18 (10/10) keep no person even without the rule
(in replay; production recorded them as person — a replay difference worth a
look with R17's trace, not caused by R18).

## 6. What the review should look at hardest

1. **R18's 2.0.** A deviation from the number in 13.8, justified above; the
   architect may prefer another value.
2. **Writes from the LAN.** R4 accepted that anyone on the Wi-Fi *sees* the
   cameras. Stage 4 lets them also rename faces and change settings
   (notification chat, labels, archive folder; not read the token). Shutdown
   is restricted to 127.0.0.1 for a similar reason. Restricting writes would
   block the user's other computer, which R4 wanted. A decision for the user.
3. **R23's pause and the scan lock.** While a scan is paused it still holds
   `_SCAN_LOCK`, so the next event's scan queues behind it — by design, but
   on a long busy evening face messages arrive late.
4. The `--window` interface still exists and now duplicates the web; retire it
   only with the user.

## 7. Not done

Nothing of the plan. "Archive now" was deliberately not ported (section 1).

## 8. Usage

| | 5-hour window | Weekly | Context |
|---|---|---|---|
| Start (~13:45) | 22% (resets 18:20) | 45% | 336k tokens |
| End (~14:20) | 34% | 46% | ~405k tokens |

Per item: R23 22→24, R18 24→26, stage 4 26→34. All in a conversation that
started at 336k of context.
