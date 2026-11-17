# HANDOFF — developer 34: backlog 45 step 3, the gate and the clean-up

Plan: `docs/BACKLOG.md` 3, developer 34, followed in its order; no deviation
in scope. Four commits, one per step.

## 1. Each item

### Step 1 — the read set (`7dcdb25`)

`tools/view_quality_verdicts.json`: every face and dog view of the 17/11
18:19 copy that held no verdict now says `"ok"`. The copy held **445 views
(306 faces, 139 dogs); 117 had a verdict, 328 were marked ok**. The file
also holds 18 verdicts of views no longer stored (the 18 "other" views
deleted from production on 17/11). `view_quality.py` on the copy printed
the same tables before and after: the only lines that differ are two
OpenCV warning timestamps and the timing line. No view marked ok was
flagged, so the "flag with no verdict counts as other" rule changed
nothing.

### Step 2 — the face gate (`4652f89`)

- `faces.face_quality(image, face=None)`: SCRFD on the photo, the face
  nearest its centre (`_central_face`, now shared with `embed_view`),
  `align_crop`, eDifFIQA(T); `None` with no image or no face. The tool
  imports it (`faces.face_quality(image, scrfd)`), so gate and measurement
  are one function; its own `quality_net`/`face_quality` and the
  `models/bench` path are gone. `_aligned_output(net, image, face)` is the
  blob both ArcFace and eDifFIQA take.
- `QUALITY_CUT = 0.40`, `QUALITY_MODEL = models/ediffiqa_tiny_jun2024.onnx`.
- `Gallery.admits(crop)`: `face_quality(crop) >= QUALITY_CUT`.
  `DogGallery.admits` takes every crop (a dog's gate is its box, in
  `dogs.record`) — without this override the dog gallery, which inherits
  `add`/`reinforce`, would have been gated by a face model.
- `Gallery.add` keeps only admitted views and returns **None** when none
  is admitted (no entry, no Visitor number taken). `Gallery.reinforce`
  returns **False** below the cut (nothing stored) or for an entry gone,
  True otherwise. No other path changed: merges, `assign`, the queue and
  the cleaning move views already stored.
- `_scan_clip`: a sure match below the cut is still a named sighting, no
  view kept (logged "a sure match below the quality cut: named, no view
  kept"); a new face with no admitted view is a sighting with
  `person_id` `""` (logged "a sighting of no entry"). `""` is never put in
  `seen_here`, so two different no-entry faces in one clip are two
  sightings. The recorded sighting of every **new** face carries, in memory
  only (never on disk), `views` (the group's embeddings) and `references`
  (the four `add` was given — what today's entry would have held).
- `notify`: the visit keeps `strangers`, the `references` of every new face
  it saw. `_again(visit, sighting)`: the entry is in the visit, or any of
  the face's `views` matches a remembered reference at `MATCH_THRESHOLD` —
  the same face again. It applies to every new face, with or without an
  entry: a stranger whose first event had only poor views (no entry) and
  whose second has a good one (an entry made now) would otherwise send
  twice, where today it matched the first event's entry and sent once.
  `faces_seen`'s `repeats` is now a list of sightings (compared by
  identity), not of ids.
- `_one_visitor`: on one person track, the unnamed sightings, entries and
  `""` alike, become one; real entries are merged as before; a `""`
  sighting joins the kept one and hands it its `views`/`references`.
- `Gallery.label("")` is "Unknown"; a gone id stays "?". Recordings
  (`web._who_was_seen`) already read a missing entry as "unknown".
- `downloads.py`: `EDIFFIQA` pinned in `PINNED` by SHA-256
  `9426c899cc0f01665240cb7d9e7f98e18e24e456c178326c771a43da289bfc6a`,
  URL `opencv_zoo/raw/main/models/face_image_quality_assessment_ediffiqa/
  ediffiqa_tiny_jun2024.onnx` (checked: 302 to 200, 7,272,678 bytes). It
  is on `main`, not a commit — `gh` is not installed here to look the
  commit up; the SHA-256 is the pin, and a changed file fails loudly.
  `production.ps1` runs `downloads.py` before stopping, so the model is
  fetched before the deploy stops anything. Here I copied it from
  `models/bench` into `models/` (same hash).
- `tests/conftest.py`: an autouse stand-in, every face photo passes
  (`face_quality` → 1.0), as the dog network has one; the gate's tests put
  their own in place.

### Step 3 — the dog gate (`745f016`)

`dogs.MIN_VIEW_BOX = 120`. In `dogs.record`, `max(box[2], box[3]) < 120`:
a sure match is named with no `reinforce`; an unmatched crop is a sighting
of no dog (`dog_id` `""`, `certainty` `""`) and makes no card; probable is
as before. Words, `identify` (the first message) and `current_words` are
untouched. The log line counts the small crops ("N under 120 px with no
view kept"). Four older tests used boxes of 4–80 px only because size did
not matter to them (`test_dogs`, `test_dog_sure_distance`,
`test_forget_unseen`, `test_view_events`); their boxes are now ≥ 120 px,
no assertion changed.

### Step 4 — the clean-up (`1b27565`)

`tools/clean_views.py <folder> [--apply] [--verdicts FILE]` — its own tool,
because `view_quality.py` only reads. Per view with a photo: verdict
poor/bad → "read poor", other → "read someone else's", both deleted; ok →
"read good", kept; no verdict → "unread, at the cut" kept, or "unread,
below the cut" / "unread, no face" deleted (a dog with no sighting found
has box 0, below the cut). A view whose photo file is missing is left
alone and reported. `Gallery.drop_views(names, best, dry_run)` in
`faces.py`, used for both galleries: one lock, one save, photos deleted
after the write; an entry left with no chosen view moves its queue up
(both named and unnamed — the queue is read good or at the cut); a named
entry with no queue keeps its best view by `best` (eDifFIQA for faces, the
box for dogs); an unnamed entry left with none is removed, sightings kept,
the Visitor counter untouched. Dry run by default; `--apply` refuses while
the folder's port answers, copies `faces/` and `dogs/` to
`backups/clean_views_<stamp>/`, then deletes. Running it twice deletes
nothing the second time.

## 2. Data-format impact

Additive only. A face sighting may now have `person_id` `""` — the value a
forgotten entry's sighting already read as; every reader takes an id the
gallery does not hold (`get` → None). A dog sighting may have `dog_id` `""`
with `certainty` `""` (before, `""` came only with `"probable"`):
`current_words` gives "unidentified dog"/"dog", as for a no-name dog. No
new field on disk; `views`/`references` live only in the scan's return
value. `check_data.py`: **"Every file is readable by this version"** on
this folder, and on the scratch copy after `--apply` (paths pointed at it):
faces 28 entries, 204 views = 204 files; dogs 55 entries, 127 views = 127
files; no named entry without a chosen view.

## 3. Suggested documentation updates

- **ARCHITECTURE 10.18**: "no rule is built yet" is now false — step 3:
  `face_quality` in `faces.py`, `QUALITY_CUT`, `admits`, the scan's two
  cases, the no-entry sighting; the dog gate; `clean_views.py` and its
  dry-run numbers below; the cost (5). The tool section: `view_quality.py`
  now imports the model from `faces`, `models/ediffiqa_tiny_jun2024.onnx`
  instead of `models/bench`.
- **ARCHITECTURE 12.14**: rule (c) — "a face whose entry the visit has
  already seen" becomes "a face the visit has already seen: its entry, or
  a new face whose views match one seen new" (`_again`, `strangers`).
- **ARCHITECTURE 10.17**: `_one_visitor` with `""` sightings.
- **ARCHITECTURE 10.14 / 19 (models)**: eDifFIQA(T) is now a production
  model, fetched by `downloads.py`, pinned; ~7 MB.
- **ARCHITECTURE 20**: `MIN_VIEW_BOX`; a `dog_id` `""` with no certainty.
- **CONTEXT 9**: `tools/clean_views.py`; **CONTEXT 10**: its command line,
  and `QUALITY_CUT` (faces.py), `MIN_VIEW_BOX` (dogs.py) in the tuning
  constants.
- **README**: eDifFIQA(T)'s CC-BY-4.0 attribution (Babnik et al., IEEE
  TBIOM 2024; OpenCV Zoo) — the plan already has it for review 36.
- **INSTALL** (models list), if it lists the files fetched.

## 4. Libraries and concepts worth explaining

- **Monkeypatching a module function vs. a method** (`conftest.py`):
  `monkeypatch.setattr(faces, "face_quality", ...)` works because
  `Gallery.admits` looks `face_quality` up in the module's globals at call
  time — Python binds names late, unlike a Java static import resolved at
  compile time. The tool calls `faces.face_quality(...)` through the
  module for the same reason.
- **Template-method override** (`DogGallery.admits`): the base class's
  `add`/`reinforce` call `self.admits`, and the subclass changes only that
  hook — like an overridable protected method in C#.
- **Identity vs. equality** (`id(s)`, `s is r` in `notify`): two sightings
  can be equal dicts and still be different faces; `is` compares the
  objects, like `ReferenceEquals` in C#.
- **`x or ""`** (`gallery.add(...) or ""`): `None` is falsy, so the
  expression gives the right-hand value — C#'s `??` for this case.

## 5. Measurements

- **The gate's cost on the M900**: `admits` (SCRFD at 320 + alignment +
  eDifFIQA) on 80 stored 300 px views, median **62.5 ms**, p90 68.4 ms. The
  10.18 figure of 9.8 ms was eDifFIQA alone with the face already found;
  SCRFD on the photo is most of it. A scan pays it once per sure match
  (~60 ms) and up to four times per new face (~250 ms), on scans of
  several seconds, off the live path.
- **Dry run on a fresh copy of production** (`C:\JARVIS` `faces/`,
  `dogs/`, `config.json` copied 17/11 19:07; the same 306 + 139 views as
  at 18:19, every one with a verdict, so nothing was judged by the cut;
  between the copies the user merged five unnamed entries into Dhaniel
  and Karol). Faces: 102 deleted (all read poor), 11 unnamed entries
  removed, none spared, 14 entries untouched.

  | Entry | chosen / waiting | deleted | chosen left |
  |---|---|---|---|
  | Gustavo Henrique Gomes | 38 / 23 | 14 | 31 |
  | Izabel | 26 / 35 | 11 | 16 |
  | Karol | 18 / 0 | 3 | 15 |
  | Ana Claudia | 12 / 0 | 4 | 8 |
  | Dhaniel | 13 / 0 | 7 | 6 |
  | Luan | 6 / 0 | 1 | 5 |
  | Visitor 9 | 18 / 0 | 17 | 1 |
  | Visitor 30, 14, 3, 7, 25, 32, 5 | — | 2, 1, 2, 3, 1, 2, 1 | 6, 4, 3, 2, 2, 1, 1 |
  | Visitor 10, 11, 12, 16, 18, 19, 27, 28, 31, 33, 6 | — | all (2–7 each) | removed |

  Dogs: 12 deleted (9 poor, 3 someone else's), Aurora 39 → 37, Mirana
  40 → 37, 7 unnamed dogs removed (one view each).

  Recognition, leave-one-event-out over the named views, sure at the
  folder's threshold (default 0.40 faces, 0.33 dogs), references = chosen
  views:

  | | right sure | right probable | wrong sure / probable | no name |
  |---|---|---|---|---|
  | faces, today | 79 | 92 | 1 / 2 | 78 |
  | faces, after the clean-up | **46** | 94 | **0 / 0** | 112 |
  | dogs, today | 14 | 34 | 0 | 31 |
  | dogs, after the clean-up | 13 | 34 | 0 | 32 |

  On the 18:19 copy the tool's "today" row is 72 / 89 / 1 / 2 / 71, the
  same as `view_quality.py` and ARCHITECTURE 10.18; the fresh copy has 17
  more named probes from the user's merges. "After" is below 10.18's "the
  views read good by eye" row (58 right sure) because there the waiting
  good views counted as references; here only what stays chosen does —
  `Gallery.match` reads only the chosen. Moving Gustavo's and Izabel's
  good waiting views up is the user's (or a later item's) choice.
- Tests: 446 → 471, all pass. The 12 face-gate tests error on the old
  code (no gate); of the 5 dog-gate tests, the 3 on the gate fail on the
  old code and the 2 that guard the messages pass on both, as they
  should.

## 6. What the review should look at hardest

- **`notify._again` and `strangers`**: the plan asked only that a later
  face *of no entry* matching a remembered one be "the same face again"; I
  apply it to every new face (entry or none), to keep the messages as
  today when a stranger's first event had no view at the cut and a later
  one does. `strangers` are only the `references` of new faces, so a face
  matched to an existing entry is decided by its id as before. Two
  different strangers within `MATCH_THRESHOLD` of each other in one visit
  would now be one — the same risk the gallery's own match already had.
- **`_one_visitor`** with `""`: the kept sighting takes the first unnamed
  sighting's place; on disk the `""` sightings stay `""`.
- **`drop_views` moves the queue up for named entries too** (the plan
  says "a named entry keeps its last view"); on production no named entry
  needs it — none loses every chosen view.
- **A dog view with no sighting found counts as box 0, below the cut**, and
  is deleted when unread; on production every view has a verdict, so it
  did not arise.
- The eDifFIQA URL is on `main`, pinned by hash only (1).
- `--apply` was run on scratch copies only. Production is untouched.

## 7. Not done

Nothing of the plan. Not measured: a replay of the month's scans through
the gate — `replay_visits.py` replays the stored sightings, which the gate
does not change; re-scanning a month of clips was out of scope. The
scan-level behaviour and the messages are covered by
`tests/test_quality_gate.py`.

## 8. Usage

- Start: 5-hour window 59 %, weekly 19 %.
- End: 5-hour window 74 %, weekly 21 %; context ~250k tokens.
