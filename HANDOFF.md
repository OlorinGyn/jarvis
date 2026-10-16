# HANDOFF — developer 27: item 40 (notifications by incident) with R60

The plan of BACKLOG 3 was followed in its order, all six steps, no deviation.

## 1. Items done

**R60 + item 40 steps 2–3 — `136e9b0`** (`src/jarvis/notify.py`, `tests/test_notify.py`).
R60 reproduced first: `test_a_held_faceless_person_inside_the_quiet_window_still_reaches_the_phone`
(two held faceless scans on Front, 0 s apart, in Home) failed at HEAD — the
second returned 0. It passes now, the second arriving silent. Closes **R60**.

The rule as built:
- `_incident` (module dict, under `_lock`): `last_sent`, `camera`, `people`.
  Opened by a message when none is open or `now - last_sent >= notify_cooldown`;
  every message sent updates `last_sent`, `camera`, `people = max(...)`.
- `_loud(camera, people, what, settings, force=False)` decides. **Loud:** the
  incident's first message; a camera other than the incident's last; more
  people than the incident's maximum; `force` (camera_down). **Silent:** the rest.
- **The floor**, `LOUD_FLOOR_SECONDS = 30`, across the house, kept in `_floor`
  (`last_loud`, `held_back`, `timer`), separate from the incident so a short
  quiet window cannot bypass it. A loud message within 30 s of the last loud
  goes out silent at once and its text is appended to `held_back`; the first
  one starts a `threading.Timer` for `last_loud + 30 - now`; at the mark
  `_end_of_floor` sends one loud text: `"Back 21:03:10: person — sent silently above"`,
  or `"… — and N more, sent silently above"` when several merged. That text
  counts as a loud (resets `last_loud`) and as sent (renews the incident).
- People: an event counts 1 when its parts hold a person that is not held,
  else 0 (one `person` part per event, whatever the count — `_message_parts`);
  after the scan, `max(people, 1)` from `after_scan`'s `people` (YOLO's
  `most_people`), passed to `faces_seen`, `side_face`, `best_view`;
  `hidden_person` uses its own `people`.
- **Nothing drops any more:** `_cooled_down`, `_claim`, `_last_sent` are gone;
  `event()` returns `(True, held)` whenever it has words; `_faceless` no longer
  checks a cooldown (a held person's message always goes; a non-held follow-up
  still needs a sent event). `send()` takes `silent` → Telegram's
  `disable_notification: "true"`. Log: `sent` / `sent silently`.
- `COOLDOWN_SECONDS` renamed `QUIET_SECONDS`; `reset_cooldown()` → `reset_incident()`
  (tests only). The config key `notify_cooldown` is unchanged.
- `_faceless` now takes a zero-argument callable instead of `(image, *extra)`,
  so each path builds its own call with `people` (`test_side_view` still
  patches `side_face`/`best_view` by name — the lambdas resolve them at call time).

**Item 40 step 4, camera with no picture — `dcbdeb4`** (`src/jarvis/outage.py` new,
`modes.py`, `notify.py`, `cameras.py`, `tests/test_outage.py`).
- `outage.CameraWatch(ages)`: a daemon thread started in `cameras.main` after
  `Core`, `stop.wait(CHECK_SECONDS = 5)` loop reading `core.frame_ages()` — a
  thread of its own so a stalled core loop does not hide a dead camera.
  `CAMERA_DOWN_SECONDS = 60`, `GRACE_SECONDS = 60` from the watch's start
  (after `start_cameras`' `wait_ready`). A camera that never delivered counts
  from the watch's start.
- Texts: `"Back: no picture since HH:MM:SS"` (wall time of the last frame),
  `"Back: picture back, N min without"` (N rounded, at least 1). A
  `logger.warning("Camera …")` for both, whatever the mode.
- `notify.camera_down(camera, text)`: the case `camera_down`, sent with
  `force=True` — loud, but through the floor (two cameras dropping together
  give one ring and one floor text).
- `modes.CAMERA_CASES = ("camera_down",)`, added to `CASES`; `defaults()` on
  in Away and Home, off in Silent; name "Camera with no picture, and its
  return". `tests/test_face_model.py`'s fake `Core` gained `frame_ages()`.

**Item 40 step 5, the page — `217b61d`** (`static/index.html`). The field is
"Quiet window of an incident, seconds", with a hint: nothing dropped, what
rings, the 30 s floor. The new switch needed no page code (the table comes
from `modes.CASES`). Checked on the test copy at 375 px (no horizontal scroll,
`scrollWidth` 375) and on a desktop: the row shows Home on, Away on, Silent off.

**Item 40 step 6, the measurement — `dc86e89`** (`tools/replay_notifications.py`).

## 2. Data-format impact

None on disk. `config.json` gains nothing: `camera_down` is filled into a stored
`notify_modes` by `modes.normalised` (test `test_an_older_config_gets_the_new_switch`);
it is written only when the user next saves the modes, additively.
`check_data.py`: "Every file is readable by this version."

## 3. Suggested documentation updates

- **ARCHITECTURE 12** (notifications): the incident replaces the per-camera
  and per-face cooldowns — opening, closing, loud/silent rules, the floor and
  its timer, `disable_notification`, the log words; the camera watch
  (`outage.py`), its thresholds and texts; `notify_cooldown`'s new meaning.
- **ARCHITECTURE** modes section / HISTORY 8 (backlogs 25, 30): the tenth
  case, `camera_down`, and that it is not a person or animal case
  (`holds_person` ignores it).
- **INSTALL / user guide**, if it describes the Telegram field: the new label.
- **BACKLOG 1**: item 40 done except its "Later, with tracking" part; backlog 2's
  first part (camera with no picture) done; R60 closed.
- **ARCHITECTURE 19** (tools): `tools/replay_notifications.py`.

## 4. Worth explaining to the user

- `threading.Timer` — a `Thread` subclass that runs a function once after a
  delay, cancellable (Java's `ScheduledExecutorService.schedule`, C#'s
  `System.Threading.Timer` with no period).
- `Event.wait(timeout)` as a sleep that a stop interrupts at once — the watch's
  loop; better than `time.sleep` in a thread that must stop.
- Injecting the clock (`_clock = time.monotonic`, `CameraWatch(clock=…)`) so tests
  move time by hand — like passing a `Clock`/`TimeProvider` in Java/.NET.
- A lambda as a deferred call (`_faceless(…, lambda: best_view(…))`): late
  binding of global names, why `monkeypatch` still reaches the patched
  function.
- `dict` unpacking to add an optional field: `{"chat_id": …, **quiet}`.

## 5. Measurements

Production log `C:\JARVIS\logs\jarvis.log` (read only), 10/10 01:16 to 16/10
19:20, replayed by `tools/replay_notifications.py` through `notify._loud`:

| Range | quiet | sent before | once dropped | now sent | loud | silent | floor texts |
|---|---|---|---|---|---|---|---|
| all | 120 | 449 | 291 | 740 | 219 | 521 | 17 |
| all | 180 | 449 | 291 | 740 | 191 | 549 | 16 |
| before the modes (to 13/10 11:26) | 120 | 259 | 100 | 359 | 105 | 254 | 6 |
| since the modes | 120 | 190 | 191 | 381 | 115 | 266 | 11 |
| last 24 h (Home) | 120 | 54 | 46 | 100 | 41 | 59 | 1 |
| last 24 h (Home) | 180 | 54 | 46 | 100 | 31 | 69 | 1 |

Rings = loud + floor texts. Of the 46 once dropped in the last 24 h, **44 are
"no face" (held faceless persons, R60)** and 2 faces; since the modes, 178 of
191. So in Home the phone **rang** 54 times before and would ring 42 at 120 s,
but **receives** 100 messages instead of 54: the dropped faceless messages were
hiding volume — mostly the residents' walks and the dogs as people (R59, R58).
The architect's sketch counted sent lines only; this counts the dropped ones too.

Under-count: an event once dropped by the camera cooldown left `notified`
false, so its best-view follow-up was never attempted and is not in the log;
the new rule sends both. `people` per logged line is inferred from the
subject (hidden person = 2).

Tests: 328 passed (`uv run python -m pytest`); comment check 0;
`check_doc_refs` 0 broken.

## 6. Look hardest at

- **Concurrency.** `_loud` runs in the capture thread (`event`) and the clip
  threads; the floor's `Timer` runs `_end_of_floor` in its own thread, taking
  `_lock` and sending outside it. `_lock` is not reentrant: nothing under it
  may call back into notify. `reset_incident` cancels the timer.
- The floor's held-back text uses the **settings of the first held message**,
  captured when the timer started.
- The incident's `camera` follows every message, silent ones included, and the
  camera_down message too: a person on Front right after "Back: no picture"
  rings as another camera.
- `GRACE_SECONDS` counts from the watch's start, after `start_cameras` waited
  for the streams: a camera still dead then is reported at about one minute.
- Volume in Home roughly doubles in messages received (section 5) — the
  user's "many notifications in Home" will look worse in the chat, though
  quieter in sound, until R59/R58 (tracking).
- Not tested live: a real camera outage (needs cutting a stream); only by
  unit tests with a hand clock.

## 7. Not done

Nothing of the plan. Item 40's "Later, with tracking" part is item 7's.

## 8. Usage

- Start: 5-hour window 49 %, weekly 23 %.
- End: 5-hour window 58 %, weekly 24 %; context 179 k tokens.
- This session: about 9 points of the 5-hour window.
