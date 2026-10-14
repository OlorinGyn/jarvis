# Handoff - developer to architect

Developer session 17, 13/10/2026 (night). The plan of `docs/BACKLOG.md` 3,
in its order, all three items done: R46, backlog 30, backlog 29.

## 1. Items done

### R46 — a person who moves while bent over — `0a514c3`

**Cause, read on the clips.** When a person bends, YOLO's box changes shape
(tall to wide) and drifts: the first `dog` box has IoU 0.35–0.47 with the
person's last box, under `SAME_PERSON_IOU` 0.5, and the following `dog` boxes
chained off it but never renewed `recent_people`. The decisive fact: in the
same YOLO run **the person box disappears** — the dog box replaces it. A real
dog at someone's feet sits beside a person box that is still there.

**Fix, in `people.py`.** `SubjectDetector` keeps `last_people`, the person
boxes of the last run that saw people (within `RECENT_PERSON_SECONDS`). Each
run, `_people_replaced_by_dogs` finds the ones no current person box
continues (IoU ≥ `REPLACED_PERSON_IOU` = 0.3), and lets the most confident
`dog` box with IoU ≥ 0.3 against one take its place, one dog box per vanished
person. `_why_a_person` gives the reason (R44's first; trace reason for the
new one: "took the place of a person who vanished"). `_remember_people` puts
relabelled boxes into `recent_people` and `last_people`, so a long bend
stays a person. R44's rule is unchanged.

**Not a tracking library.** R46 left the choice open. Tracking proper is
backlog 7, still (proposto), and the well-regarded trackers (norfair,
supervision's ByteTrack) need scipy — a new compiled dependency under Smart
App Control. The rule is ~40 lines; if backlog 7 is decided, a tracker
replaces both R44 and R46 rules.

### Backlog 30 — Home silences a probable resident — `cfa286a`

- `modes.py`: cases `probable_resident_person` (after `resident_person`) and
  `probable_resident_dog` (after `resident_dog`); `PROBABLE_RESIDENT_CASES`.
  Defaults: on in Away (the dog one follows the older `notify_labels` like
  the other dog cases), off in Home and Silent. `CASE_NAMES` reworded:
  `known_person` is now 'Other known person, or "probably" someone else';
  `other_dog` 'Other dog (another name, probably another, unidentified)'.
- `notify.person_case`: a resident under `LEARN_THRESHOLD` is
  `probable_resident_person` (was `known_person`).
- `dogs.identify` returns `(words, certainty)` — `"sure"`, `"probable"` or
  `None` when the dog is not a Resident — instead of `(words, bool)`;
  `clips.DOG_CASES` maps it to the case.
- The Notifications help text on the page said 'a "probably …" is never left
  out'; now it says a probable resident has its own switch, off in Home.
- Tests: `tests/test_probable_resident.py` (new); in `tests/test_notify.py`
  the matrix, `person_case` and the Home face test changed by the decision
  (a probable Gustavo is now silent in Home; a probable Ana is still sent).

### Backlog 29 — `/on` and `/off` — `589cc13`

- `jarvis/analysis.py` (new): the On/Off flag, in memory only. `is_on`,
  `set_on` (returns whether it changed), `off_for` (seconds Off), `describe`.
- `cameras.Core.step`: always reads every frame (Live keeps working); when
  Off, skips motion and YOLO and calls `recorder.update(frame, [])`, so an
  open event ends after `POST_SECONDS` as if the motion had stopped
  ("subject left"). `_switch_analysis` follows the flag once per step: logs
  "Analysis On/Off", clears the drawn subjects, and coming back On gives
  each camera a fresh `MotionDetector` (the old background is stale; it is
  blind for `WARMUP_FRAMES`, as at start).
- `bot.py`: `/on`, `/off` in `COMMANDS` and `HELP`; replies say what Off
  means; `/mode` and the help end with "Analysis: On/Off."; `_remind` sends
  "Analysis has been Off for N h …" every `REMINDER_SECONDS` (3 h) while
  Off, to `notify_chat` only, counting from the moment it went Off.
- `/api/status` carries `analysis`; the header shows "On" (green) or "Off"
  (red badge) on every screen, updated by the page's health check. Checked
  in the test copy, desktop and 375 px wide.
- Tests: `tests/test_on_off.py` (new): Off drops frames before motion, an
  open event ends, coming back On relearns the background, a restart starts
  On (module reload), `/off` `/mode` `/on` from the configured chat, another
  chat cannot, the 3-hour reminder and its restart, the status. The clock is
  a fake `time` patched into `analysis` and `clips` with `monkeypatch`.
  `tests/test_bot.py`: the help test now expects the "Analysis: On." suffix.

## 2. Data-format impact

- `config.json`: two new keys inside each mode of `notify_modes`, filled by
  `modes.normalised` from their defaults — additive; a stored file keeps
  every switch it had. Tested with a config written without them.
- Off is never written anywhere.
- `dogs.identify`'s return shape changed, but it is in memory only, never
  stored.
- `tools/check_data.py`: "Every file is readable by this version."

## 3. Suggested documentation

- **ARCHITECTURE 7.12** (or a new 7.13): R46 — the vanished-person rule, the
  0.3 threshold, the chaining, the trace reason, the measurement below, and
  why not a tracker library yet.
- **ARCHITECTURE 22.2**: nine cases, not seven; the two probable-resident
  cases and their defaults; the rule ("only a sure match is the resident")
  stays, the default changed. The section title says "Seven cases".
- **ARCHITECTURE 22.5**: `/on`, `/off`, the reminder, the state in `/mode`.
- A new ARCHITECTURE section (or in 22) for Off: what stops, what does not,
  why it is not stored, the fresh motion detector on resume.
- **ARCHITECTURE 17**: the On/Off in the header; `/api/status` gains
  `analysis`.
- **ARCHITECTURE repository map / CONTEXT 9**: `analysis.py`.
- **ARCHITECTURE 7.12's measurement table** and `HISTORY` 13: the numbers in
  section 5.
- `BACKLOG.md`: R46 done, backlog 29 and 30 done.

## 4. Worth explaining to the user

- **Module-level state as a singleton** (`analysis.py`): a Python module is
  imported once per process, so its globals are the C# `static class` /
  Java static field. `global` is needed to rebind them inside a function. A
  `threading.Lock` guards the write; reading a bool needs none (the GIL).
  `importlib.reload` in the test re-runs the module, which is exactly "a
  restart".
- **A fake clock with `monkeypatch`**: replacing the module's `time` name
  with an object that has `monotonic()` — only that module sees it, unlike
  patching `time.monotonic` itself, which every module would see.
- **Greedy one-to-one matching** (`_people_replaced_by_dogs`): sorted by
  confidence, each person claimed once — the cheap cousin of the Hungarian
  algorithm a tracker like ByteTrack uses.
- **Importing helpers from another test module** (`from test_bot import
  Telegram`): pytest puts `tests/` on `sys.path` (rootdir "prepend" mode).

## 5. Measurements

R46, `replay`-equivalent with `--prime` (a scratch script counting kept boxes
per YOLO run), clips copied from production into this folder's `clips/`:

| Clips | dog boxes before → after | relabelled before → after (R44 + R46) |
|---|---|---|
| The five of R46 (bend) | **13 → 2** | 9 → 16 + 4 |
| Six true dogs with a person (HISTORY 13.16) | 202 → 202 | 0 → 0 |
| Six dogs alone (HISTORY 13.17) | 59 → 59 | 0 → 0 |

Per R46 clip after: `15-00-17` 6→0, `15-09-58` 0→0, `15-19-17` 5→0,
`14-46-29` 1→1, `Back 11-23-48` 1→1. The two left have no person before them
(Back 11-23-48 never sees a person; 14-46-29's is a 76×62 box 5 s after the
last person — likely one of the objects R46 counts). The architect counted
23 dog boxes in these clips; mine counts kept boxes per YOLO run, so 13.

Tests: 208 pass (`python -m pytest`), 176 at the start. No comments in
`src/` and `tools/`; `check_doc_refs` 0 broken.

## 6. Review hardest

- **R46's risk is the chain.** Once a dog box is relabelled, it renews the
  memory, so if a real dog ever takes a vanished person's place (a person
  steps out of view right over a lying dog), it stays a person while it
  keeps matching itself. None of the 12 true-dog clips showed it; there is no
  cap on the chain's length.
- **The event closed by `/off` finishes its pipeline**: clip assembled, face
  scan, follow-up messages — as any event that ended because motion stopped.
  I read "ends as if the motion had stopped" that way; if Off should also
  silence that last event's scan and messages, `clips._assemble` would check
  `analysis.is_on()`.
- `/off` while an event is open still records `POST_SECONDS` more of it.
- Backlog 30: a user who had turned `known_person` off in Away now gets
  probable residents in Away from the new case's default (on). Nobody has,
  as far as I know; mention it only if the review thinks it matters.
- The reminder counts from the moment Off was set, at the poller's ~1 min
  granularity (long poll); with the network down at the 3 h mark, the
  reminder goes when it comes back, and only one.

## 7. Plan items not done

None. Developer 18 (backlog 28, 32, 31) is next, as planned.

## 8. Usage

| | 5-hour window | Weekly | Context |
|---|---|---|---|
| Start | 12 % | 11 % | 70k |
| End | 21 % | 12 % | ~190k |

About 9 points: R46 ~4 (the two 7-minute replays), backlog 30 ~2, backlog 29
~3.
