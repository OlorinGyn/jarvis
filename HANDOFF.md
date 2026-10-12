# Handoff - developer to architect

Developer session 14 (12/10/2026, evening), the plan of CONTEXTO 14.4 in its
order: R44, backlog 26, backlog 27, then R43. All four done. 174 tests.

## 1. Items done

### R44 - a dog box where a person stood a moment ago is that person (`aa68bc4`)

- `people.py`: `SubjectDetector` keeps `recent_people`, the person boxes YOLO
  returned (after NMS, at `CONFIDENCE`, before any person rule) with their
  time, pruned to `RECENT_PERSON_SECONDS` = 2.0. A `dog` box (new
  `DOG_CLASS` = 16) that passed `ANIMAL_CONFIDENCE` and has IoU >=
  `SAME_PERSON_IOU` = 0.5 with one of them becomes `person`; then the person
  rules (too short, wide at the bottom edge) apply to it as to any person.
- Only boxes from earlier runs count: the current frame's person boxes are
  added after the loop (in the same frame NMS is class-agnostic, so a person
  and a dog on the same spot do not both survive anyway).
- Order chosen: the relabel comes **after** the animal-confidence check, so a
  dog box below 0.45 is still dropped as before instead of becoming a new
  person. The bent-over user is 0.62-0.81 (HISTORY 13.16), so nothing is lost.
- Trace for `replay.py`: "the person's box from a moment ago: dog 0.74 (...)",
  through the existing `_drop`, followed by the box kept as person. No
  change to `replay.py` was needed.
- Tests: `tests/test_person_as_dog.py` (4): relabelled, the small dog at the
  feet kept, the person must be recent, a relabelled box meets the person
  rules.

### Backlog 26 - select many unnamed crops, name or report them at once (`e1bcd44`)

- `faces.Gallery.assign(ids, target_id=None, full_name="")`: one lock, one
  load, one save. Skips ids that are no longer an unnamed entry (merged,
  named or reported meanwhile) and returns them as `gone`. With a name and no
  entry by that name, the first remaining id takes the name and the rest
  join it. `_absorb` runs once at the end (R29). Returns
  `{id, name, joined, gone, absorbed}` or None when there is nothing to join.
- `Gallery.guess(entry)` / `DogGallery.guess(entry)`: the named entry an
  unnamed one looks like. Dogs: `dogs.match` over its views, sure before
  probable, then the smallest distance. Faces: the named person with the best
  similarity at or above `MATCH_THRESHOLD`.
- `web.py`: `_grid` adds `guess` (an id or null) to each unnamed card;
  `POST /api/{dogs,persons}/assign` (`{"ids", "to"}` or `{"ids", "name"}`) and
  `POST /api/{dogs,persons}/report` (`{"ids"}`, one report per entry through
  `reports.report_entry`, answers `{reported, gone}`). Ids are checked against
  `SAFE_DOG`/`SAFE_PERSON`, 1 to `BATCH_MAX` = 500. Through the write guard.
- Page (`galleryTab`, so People and Dogs both): the unnamed grid is grouped
  by guess - "Looks like Aurora (12)", biggest group first, "No guess" last -
  each with "Select all". Tapping a photo selects it (green frame and a check
  mark); the name link still opens the entry's page. Shift-click selects the
  range from the last tapped photo, in display order. A bar fixed at the
  bottom while anything is selected: "N selected · Assign to… · or a new
  name · Bad detection · Clear". Each action asks once ("Join 7 photos to
  Aurora? A merge cannot be undone."). The selection survives a reload of the
  list, minus ids that left. "Belongs to…" and the per-card form stay.
- On a phone the unnamed groups show two columns, so many photos fit for
  selection.
- **Also fixed, found while checking at 375 px:** the tab bar did not wrap.
  With six tabs it was 545 px wide, so a phone laid the page out at 545 px
  and the fixed bar landed below the screen. `.tabs` now wraps.
- Tests: `tests/test_batch_assign.py` (8): three ids join a named dog (views,
  sightings and favourite follow), a gone id is skipped and named, a new name
  creates the entry, an existing name joins it, the batch report writes one
  report per entry and a repeat answers gone, bad requests (400/409/403), the
  grid's guesses, the same on faces.

### Backlog 27 - Notifications become the first part of Settings (`7c2237b`)

- `index.html`: the `#notifications` section is gone; its two panels (modes,
  Telegram) are the first part of Settings. Settings has a sub-navigation
  `Notifications · Other devices · Archive · Bad-detection reports`, each part
  a `div.settings[data-part]`, shown as `#settings/<part>` (`notifications`,
  `devices`, `archive`, `reports`); no part, or an unknown one, shows
  Notifications.
- `app.js`: `TABS` loses `notifications`; `SETTINGS_PARTS`; `showSettingsPart`;
  an old `#notifications…` hash is replaced (`location.replace`, no extra
  history entry) by `#settings/notifications`. The reports list is read only
  when its part is shown.
- Phones: a tighter header and tab padding so the five tabs fit on one line
  at 375 px.
- No text in the code said "the Notifications tab" except the docstring of
  `tests/test_modes_web.py`, now "Settings → Notifications". The bot's texts
  do not mention it.

### R43 - config.json replaced whole, one writer at a time (`565a34b`)

- `settings.py`: a module `RLock` held by `update` from `load` to `save` and
  by `save`; `_write` writes `config.json.<pid>.<thread>.tmp` and
  `os.replace`s it, retrying `PermissionError` 50 x 10 ms. `_stored` also
  retries a `PermissionError`: on Windows a read that meets the replace is
  refused, and without the retry it answered `{}` and the reader saw the
  defaults (the token empty).
- Reproduced first: two writers and a reader, 200 rounds each. Before: the
  reader saw the token gone ~190 of 200 times. With the lock and replace
  only: still 3-13 times (the refused open). With both retries: 8 of 8 runs
  clean.
- Tests: `tests/test_settings_writers.py` (2): the two writers and the
  reader; a key from a newer version is kept.

## 2. Data-format impact

None on disk. `config.json` has the same content; it is only written
differently (a temporary file appears for milliseconds next to it and is
always removed). The gallery API answers gain an optional `guess` on unnamed
cards (additive). `tools/check_data.py`: "Every file is readable by this
version."

## 3. Suggested documentation

- **ARQUITETURA, the detection section (where `SubjectDetector`'s rules are
  listed) and 20/21 (dogs, reports):** R44's rule, its constants, the order
  (after animal confidence, before the person rules), the trace text, and
  what it does not catch (the dark object at the bottom of Front; a bend with
  no person in the 2 s before).
- **ARQUITETURA 17.10/17.14/20 (the galleries):** the guess groups, selection,
  the action bar, `assign`/`report` batch endpoints and their answers; that
  `guess` is a hint and never names anything.
- **ARQUITETURA 22 (notifications) and the web page section:** Notifications
  lives in Settings, `#settings/<part>`, the redirect of `#notifications`.
- **ARQUITETURA 11 (settings):** the lock and the atomic replace, with the
  Windows retry on both sides and why.
- **CONTEXTO 8:** strike 26 and 27. **13.4:** R44 and R43 done.
- **INSTALACAO/README:** any text that says "the Notifications tab".
- **HISTORY 13.16:** the replay numbers below, beside the architect's.

## 4. Worth explaining to the user

- **`NamedTuple._replace`** (R44): a NamedTuple is immutable like a Java
  `record`; `_replace(label=...)` returns a copy with one field changed, as a
  `with` expression does on a C# record.
- **IoU** and why it separates the bending person from a dog at someone's
  feet: same box vs a small box inside a big one.
- **Lost update and torn reads** (R43): two read-modify-write cycles
  interleaving, and a reader seeing a truncated file; `threading.RLock` (like
  C#'s `lock`/Java's `ReentrantLock`, re-entrant because `update` calls
  `save`); write-to-temp-then-rename as the classic atomic file replace, and
  why Windows needs the retry (a file open by one thread cannot be replaced,
  and cannot be opened during the replace).
- **`dict.fromkeys(ids)`** to drop duplicates while keeping order (a
  `LinkedHashSet`).
- **Front end:** `location.replace` vs assigning `location.hash` (history
  entry or not); `MouseEvent.shiftKey` for range selection; `position: fixed`
  and why an overflowing header pushed it off a phone's screen (the layout
  viewport grows to the widest content).

## 5. Measurements

R44, `replay.py --prime` on the 10 clips of HISTORY 13.16, frames with each
label, with the rule disabled (`SAME_PERSON_IOU` = 2) → enabled:

| Clip | Kind | dog frames | person frames | relabelled YOLO runs |
|---|---|---|---|---|
| Front 12/10 11-28-48 | reported, bend | 298 → 289 | 191 → 197 | 3 |
| Front 12/10 12-39-56 | reported, bend | 18 → 9 | 61 → 67 | 3 (one then dropped as wide at the bottom edge) |
| Front 12/10 12-40-23 | reported, bend, no person before | 3 → 3 | 21 → 21 | 0 (expected) |
| Front 12/10 11-45-20 | reported, dark object | 12 → 12 | 66 → 66 | 0 (expected) |
| 6 true-dog clips with a person | | identical | identical | **0** |

11-28-48 still has many dog frames: Mirana is really there while the user
pets her. The replay counts frames, the architect's measurement counted
boxes, so the numbers are not the same unit.

Backlog 26 and 27 were checked in the built-in browser against the web app
alone (`uvicorn jarvis.web:app`, port 8767, no cameras) on this folder's
data, at desktop width and at 375 px: select, shift-range, Select all,
assign to a new name, assign through "Assign to…", batch report, People's
groups, every Settings part, the back button, the `#notifications`
redirect, no horizontal scroll at 375 px, no console errors. `dogs/`,
`faces/` and `reports/` were backed up before and restored after
(`diff -r` identical).

## 6. What the review should look at hardest

- R44: recording **every** YOLO person box, including those later dropped
  (too short, no motion overlap, wide at the bottom). I followed "a person
  box seen" literally; the architect's measurement may have used only kept
  ones. Also: a dog that walks exactly where a person stood within 2 s with a
  similar box size would be called a person - the measurement says 0 of 309,
  but it is the risk.
- 26: `_merge` rescans the sightings folder once per source entry
  (`_repoint_sightings`), all under the gallery lock; with 60 crops at once
  that is 60 scans while the clip thread waits. Fine on the M900's sizes,
  but worth a look.
- 26: `assign` treats an id that was **named** meanwhile as gone, not joined.
- 26: the face guess uses `MATCH_THRESHOLD` (0.363), which is lower than the
  learning threshold: groups of "Looks like X" may hold some wrong faces, by
  design a hint.
- R43: `save` called on its own still reads `_stored()` under the lock;
  `load()` is lock-free and relies on the replace being atomic plus the
  read retry.

## 7. Not done

Nothing from 14.4. R42 waits for the user's choice; R10's file names stay for
their own session.

## 8. Usage

- Start: 5-hour window 6 %, weekly 1 %, context 68k tokens (a new
  conversation; the window resets 03:40 on 13/10).
- After R44 + backlog 26: 18 %, weekly 3 %.
- After backlog 27: 20 %.
- End: 5-hour window 22 %, weekly 3 %, context 212k tokens.
- Session cost: ~16 points of the 5-hour window and ~2 of the week, for four
  items.
