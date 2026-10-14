# Handoff - developer to architect

Developer session 19, 14/10/2026. Plan: `docs/BACKLOG.md` 3, "Developer 19" —
backlog 31 alone. Done in full, no deviation.

## 1. What was done

**Backlog 31 — detection sensitivity per label in Settings.** Commit
`45aa0e5`.

- `settings.py`: three new optional keys, `confidence_person` (0.35),
  `confidence_dog` (0.45), `confidence_animal` (0.45); `CONFIDENCE_KEYS`,
  `CONFIDENCE_RANGE = (0.20, 0.90)` and `confidence_valid()`. `load()` replaces
  a stored value that is not a number inside the range (hand edit, a bool, a
  string) by its default, so a bad value never breaks the read.
- `people.py`: `CONFIDENCE` and `ANIMAL_CONFIDENCE` now come from
  `settings.DEFAULTS` (one source for the defaults). `minimum_confidences()`
  maps every wanted class id to its minimum: person, dog, and every other
  animal to `confidence_animal`. `SubjectDetector(load_settings=settings.load)`
  rereads them at most every `SETTINGS_REFRESH_SECONDS` (2.0, monotonic clock,
  not the replay's `now`). `_raw_detections(net, frame, floor=CONFIDENCE)`
  takes the floor as a parameter; the detector passes the lowest of the three.
  Boxes below their own label's minimum are dropped (trace: `person below
  confidence` / `animal below confidence`) **before** the R46 logic sees them:
  `_people_replaced_by_dogs`, the loop and `_remember_people` all get the
  accepted list.
- `web.py`: the three keys in `EDITABLE`; `_clean` rejects anything outside
  the range with a 400 that names it and stores the value rounded to 2
  decimals; `/api/settings` also returns `confidence_range` and
  `confidence_defaults`, so the page holds no copy of the numbers.
- Page: a new **Settings → Detection** sub-tab (between Notifications and
  Other devices) with the three inputs (step 0.05, min/max from the API),
  Save, "Back to the defaults", and the R46 sentence the plan asked for.
- `tools/check_data.py`: a stored confidence the program ignores is reported
  as a warning, not a failure (the read falls back, so the data is readable).
- `tests/test_person_as_dog.py`: its fake `_raw_detections` takes the new
  `floor` argument, and its detector reads `settings.DEFAULTS` instead of the
  machine's real `config.json` — it had been depending on whatever the local
  file held.

## 2. Data-format impact

Additive only: three new optional keys in `config.json`. An older file reads
today's values (tested); an older version that saves keeps the keys it does
not know (`settings.save` already does). Nothing in `clips/`, `faces/`,
`dogs/`, `reports/` changes. `uv run python tools/check_data.py`: "Every file
is readable by this version" (235 events, 7 people, 22 dogs, `config.json` 11
keys before the browser test; the test copy's `config.json` now holds the
three keys at their defaults).

## 3. Suggested documentation

- **ARCHITECTURE 7** (detection; 7.1 or a new subsection beside 7.13): the
  three minimums, the network floor = the lowest of them, the order (each
  label's minimum, then R46's relabelling, so the relabelled boxes are
  judged by YOLO's own class — a bent person called dog at 0.40 is dropped
  when the dog minimum is 0.45, exactly as before), the 2 s reread.
- **ARCHITECTURE 11** (settings / `config.json`): the three keys, the range,
  the fallback on a bad stored value.
- **ARCHITECTURE 17** (the page): the Detection sub-tab.
- **CONTEXT 10**, tuning constants: `CONFIDENCE` and `ANIMAL_CONFIDENCE` are
  now defaults taken from `settings.DEFAULTS`; the live values are in
  Settings. Add `SETTINGS_REFRESH_SECONDS`.
- **ARCHITECTURE 12.10** (`replay.py`): a replay uses the current settings,
  so its trace follows what the user set; the new reason `person below
  confidence` appears only when the person value is above the floor.
- BACKLOG 1: strike 31.

## 4. Worth explaining to the user

- **Dependency injection with a default argument**:
  `SubjectDetector(load_settings=settings.load)`. In Python a function is an
  object and can be a default parameter value; the tests pass
  `lambda: dict(settings.DEFAULTS)`. The Java/C# equivalent is a constructor
  taking a `Supplier<Settings>` / `Func<Settings>` with an overload that
  supplies the real one.
- **Polling with a time-to-live** instead of an event: the detector does not
  learn of the change; it asks again every 2 s. Simple, also catches a
  hand edit of `config.json`, and costs ~0.23 ms per read.
- **Why greedy NMS lets the floor go lower safely**: `cv2.dnn.NMSBoxes`
  keeps a box only if no *higher-scored* box overlaps it, so adding weaker
  boxes can never remove a stronger one.
- `**{key: float for key in ...}`: a dict comprehension unpacked inside a dict literal
  (`EDITABLE`), like a spread `{...a}` in JavaScript.

## 5. Measurements

- Tests: 234 passed (216 before; 18 new in
  `tests/test_detection_sensitivity.py`).
- `settings.load()`: 230.5 µs per call on the M900 (2000 calls); at one read
  per 2 s per camera, negligible.
- Comment check 0; `check_doc_refs.py` 0 broken.
- Browser test on the test copy (port 8766, stream2): the sub-tab shows
  0.35/0.45/0.45 and 0.20–0.90; Dog 0.6 saved and landed in `config.json`;
  a POST of 0.95 answered 400 "confidence_dog must be a number from 0.2 to
  0.9"; "Back to the defaults" restored them. No error in the service log.

## 6. Look hardest at

- **The defaults keep today's output exactly** — the claim in the commit.
  Persons: raw floor 0.35 = person minimum, unchanged. Dogs 0.35–0.45: they
  used to enter `_people_replaced_by_dogs` and then be dropped; now they are
  dropped first. My argument that this changes nothing: dogs are matched
  most-confident first, so a weak dog only took a vanished person no stronger
  dog took, and was dropped anyway. Worth a `replay.py` run on R46's bends
  (HISTORY 13.20) to confirm no trace changes at the defaults.
- **A lowered person value feeds R46's memory**: with the person minimum at
  0.25, person boxes 0.25–0.35 now renew `recent_people`/`last_people`, so
  more dog boxes can be relabelled as persons. Consistent (the user asked to
  count them as people), but it widens R47's chain.
- `person_boxes()` (the face scan's bodies) and `tools/dog_crops.py` still use
  the constant defaults, not the settings — deliberate: they are not live
  detection. Say if they should follow.
- Relabelled boxes are judged by YOLO's class (dog minimum), not the person
  minimum. Judging them as persons would change behaviour at the defaults
  (a bent person at 0.38 would start to count), so I kept today's order.

## 7. Not done

Nothing of the plan.

## 8. Usage

- Start: 5-hour window 7 %, weekly 17 % (resets 18:00Z / 19:00Z).
- End: 5-hour window 14 %, weekly 18 %; context 125 k tokens.
