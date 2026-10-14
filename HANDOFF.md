# HANDOFF — developer 23 (14/10/2026)

The plan in BACKLOG 3 was done whole, in its order: R42 (b), backlog 37 (a, b)
and 38, R53 step 1, and backlog 32 for faces.

## 1. Items done

**R42 (b), `747042b`: a person hiding beside a silenced resident reaches the
phone.** Closes R42.
- `EventRecorder` (`clips.py`) keeps `most_people`: the most person boxes in
  one analysis frame (`_consider_view`, reset in `_start`). It goes to
  `_assemble` as `people=` (passed as a Thread kwarg), and to
  `notify.after_scan(..., people=)`.
- `after_scan`: when faces were found, the person was held, **every** face
  found had its case switched off (`modes.allowed(person_case(...))` false
  for all), `people > len(found)` and a best view exists, the best view goes
  out as `faceless_person`, text `"<camera> HH:MM:SS: 2 people seen, 1 face
  found, best view"` (new `notify.hidden_person`).
- The faceless rules (switch, then the camera cooldown when held and nothing
  went out, else only after a sent event) moved into one helper, `_faceless`,
  now shared by the side view, the best view and the hidden person. The
  behaviour of the first two is unchanged (their tests pass untouched).
- Faces are already distinct per person: `_scan_clip` skips a second group
  matching a `person_id` already seen, so `len(found)` is the distinct-face
  count.
- Tests (`tests/test_notify.py`): the hidden person; as many people as
  silenced faces sends nothing; a face that reached the phone accounts for
  the scene; the faceless switch and the cooldown; people counted at once,
  not summed over the event; a dog taken for a person (R18) costs exactly one
  extra message; the whole path through a fake scan. `Inline` in the tests
  now takes `kwargs` and has `join()`; `test_on_off.py`'s `_assemble` stub
  takes `**kwargs`.

**Backlog 37 (a) and (b), `b8a731b`.** Page only.
- (a) The `@media (max-width: 480px)` rule now targets every `.people-grid`,
  not only `.guess-group .people-grid`: named cards are two columns too.
- (b) `paged(container, items, render, shown, key)` in `app.js`: it renders
  the first 24 and a `button.more` "Show 24 more (N left)" (the last press
  says "Show 7 more (7 left)") that appends the next 24 before itself. It is
  used for each unnamed "Looks like" group, Waiting and "Days they were
  seen" (months). How far a list was opened is kept per tab in a `Map`
  (keys `group:<title>`, `waiting:<id>`, `days:<id>`), so naming one photo
  and the list's reload no longer collapse it. Headings keep the full
  count. **Waiting is now shown newest first** (it is stored oldest first,
  by `append`); each tile keeps its stored index for its ↑ and × routes.
- `.more` spans the grid (`grid-column: 1 / -1`), centred.

**Backlog 38, `03cde0e`.** One `<datalist id="slider-default">` in the
Detection form, its option set to `slider_steps / 2` by `showDetection`, and
`list="slider-default"` on the three sliders. Chrome draws a faint tick
under the track's middle. Seen at 375 px only with the thumb moved away: at
the default the thumb covers it, as it should.

**R53 step 1, `bed651d`: `tools/dog_bench.py`.** Nothing in the program
changed. Results in section 5.
- Data: `backups/r53_dogs_20261014`, a copy of `C:\JARVIS\dogs` (only read).
- Labels, as the plan asked, without deleting anything. I looked at each of
  the nine views in `PENDING.md`: `7221b7` (a person with a bag), `f530c0`
  (the man), `6f8002`, `557fa0` and `108df8` are **person** crops;
  `89848c` and `cc29b3` hold **both dogs**; `d6bb2c` is **Mirana** (black)
  filed under Aurora; `6b3d84` (brown fur in sunlight, probably Mirana) is
  **left out** as unclear.
- Two-dog probes: 11 sighting crops from clips where the two dogs' boxes
  overlap by at least 15 % of the smaller box, chosen by eye on a contact
  sheet. **Four of them are also gallery views** (the same picture saved
  twice, different bytes): `282a53` (Aurora), `257e9a` (Aurora), `583bd4`
  (Mirana), `554245` (Mirana). The tool finds such copies by a 16×16 grey
  thumbnail and labels the gallery view "both". These four are misfiled too:
  each holds both dogs. **For the user's list** (`PENDING.md`).
- Leave-one-out: each view against every other labelled view of the same
  lighting (the program never compares day with night), exact and
  near-exact copies left out.
- Candidates, exported to ONNX once in a throwaway venv in the session
  scratchpad (torch 2.14.1 CPU, torchvision 0.29.1, transformers 5.19, the
  official Python 3.14). The models and the export script are in
  `models/bench/dogs/` (ignored by git; `export.py` is the script). Each
  runs through `cv2.dnn` with output equal to PyTorch's (cosine 1.0 on a
  fixed random input):
  - DINOv2-small: `pooler_output`, the CLS token after the last LayerNorm.
  - CLIP ViT-B/32: `image_embeds`. It fails on OpenCV 5's new engine and
    runs only with `engine=cv2.dnn.ENGINE_CLASSIC`. onnxslim did not help.
  - MobileNetV3-Large: ImageNet V2 weights, the 960-d average pool before
    the classifier.
- Preprocessing for the learned candidates: the crop padded square with
  black, 224 px, RGB, each model's mean and std. Distance = 1 − cosine.

**Backlog 32 for faces, `9fc5592`.** The dogs' half waits for R53's model.
- `settings.py`: `face_sure_threshold` (default 0.40), `FACE_SURE_RANGE`
  (0.30–0.60; the low end is `MATCH_THRESHOLD`), `face_sure_valid`. `load()`
  falls back to the default on a bad value.
- `faces.py`: `LEARN_THRESHOLD` now **is**
  `settings.DEFAULTS["face_sure_threshold"]` (one place for 0.40; `faces`
  now imports `settings`, with no cycle: `settings` imports only `modes`).
  `learn_threshold(values=None)` returns the user's choice. It is used for
  learning a view in `_scan_clip` (read once per scan) and in `_absorb` on
  naming. `notify.person_case` and `_who` take `settings` and use it too.
- `faces.accuracy(gallery, thresholds)`: a numpy leave-one-out over the
  named people's **Chosen** embeddings. A copy is a reference with cosine ≥
  0.9999 to the probe, and it is left out. The best reference decides the
  name, as `Gallery.match`'s max-over-views does. For each threshold it
  counts named / right / wrong, plus the unnamed views whose best named
  score crosses it.
- `GET /api/accuracy/faces`: the table plus `current`, `default` and
  `range`; the current value is always one of its rows. The setting is
  saved through `POST /api/settings`, validated in `_clean`.
- The page: a "Face recognition: when a name is sure" panel in Settings →
  Detection. Its table has Threshold (a radio button), Sure (n/N), Right
  (%), Wrong and Unnamed; the current row is highlighted. It has Save,
  "Back to the default", and the paragraph on what the table cannot measure
  (strangers). It loads when the Detection part opens.
- Tests: `tests/test_sure_threshold.py` (8).

## 2. Data-format impact

All additive. `tools/check_data.py`: "Every file is readable by this
version" after each commit (276 → 284 tests passing).
- `clips/…/HH-MM-SS.json`: a new optional `most_people` (an int, written
  only when a person was seen). Older code ignores it; nothing reads it yet.
- `config.json`: a new optional `face_sure_threshold`. Older versions keep
  unknown keys on save (`settings.save`), so a rollback does not erase it.
  Absent, it reads as 0.40, today's behaviour.

## 3. Suggested documentation updates

- **CONTEXT 3** already states R42 (b) as decided; mark it built.
  **CONTEXT 10**: `faces.py` tuning list — `LEARN_THRESHOLD` is now the
  default of `face_sure_threshold`; add `SURE_SWEEP` and `COPY_SIMILARITY`;
  `settings.py` gains `FACE_SURE_RANGE`. Repository map: `tools/dog_bench.py`.
- **ARCHITECTURE 22** (notifications): the hidden-person message, its
  condition, its text, and that it shares the faceless switch and cooldown;
  `most_people` in the event JSON (ARCHITECTURE 8 / 19's list of fields).
- **ARCHITECTURE 17.14 / 17.10** (People and Dogs pages): two columns under
  480 px, the 24-at-a-time lists, Waiting newest first.
- **ARCHITECTURE 7.14**: the default tick on the sliders.
- **ARCHITECTURE 10.x** (the face thresholds) and **22.2**: the sure
  threshold is the user's, from the accuracy table; what it changes (four
  places); what it cannot measure.
- **ARCHITECTURE 20** (dogs): R53's bench, its method and table, CLIP's
  `ENGINE_CLASSIC` finding.
- **BACKLOG**: R42 closed; 37 (a, b) and 38 done; 32 faces done, dogs
  pending; R53 step 1 done, with step 2 to decide.
- **PENDING**: the four gallery views that are two-dog crops (above); `6b3d84`
  still unclear.

## 4. Libraries and concepts worth explaining to the user

- **`threading.Thread(target, args, kwargs)`**: arguments passed by keyword
  to the thread's function, like a C# lambda capturing named parameters.
- **Leave-one-out** as a measurement (backlog 32, R53). It cross-validates
  with no training: each sample is tested against all the others. Leave out
  the near-copies, or the score is inflated.
- **Learned image embeddings vs histograms** (R53): a histogram counts
  colours, so anything dark looks like Mirana. A network trained on images
  (DINOv2 self-supervised, CLIP on image-text pairs, MobileNet on ImageNet
  classes) maps shape and texture to a vector, and similar things land
  close. Cosine distance on those vectors.
- **ONNX export** (`torch.onnx.export`) and why PyTorch is needed only once,
  in a throwaway environment. Also `cv2.dnn`'s two engines in OpenCV 5: the
  new graph engine and `ENGINE_CLASSIC`.
- **`<datalist>` on `<input type="range">`**: the browser draws tick marks
  for its options.
- **Lazy pagination on the client**: the server sends the whole list and the
  page decides how much to draw; `Element.before(...nodes)` appends without
  re-rendering what is already there.
- **numpy matrix cosine**: normalise the rows, then `A @ A.T` gives every
  pair's similarity at once (the `accuracy` function), instead of a double
  loop.

## 5. Measurements

**Backlog 37, Dogs tab with production's 46 dogs** (production's `dogs/`
copied in, the test copy's put back after; `C:\JARVIS` only read):

| | Before (prod, `v2026.10.14.2`) | After |
|---|---|---|
| Dogs tab page height at 375 px | 9,163 px | 8,591 px |
| Named cards per row at 375 px | 1 | 2 |
| Horizontal overflow at 375 px | none | none |
| Aurora's page (34 waiting), height at 375 px | — | 6,390 px with 24 shown; 7,201 px with all 34 |
| Desktop (1024 px) | 5 columns | 5 columns (unchanged) |

**The gain is small, and why matters for the design.** The "Looks like"
groups already had two columns. Each unnamed card is 350 px tall at 375 px:
a 170 px photo, then the name row, the name form, "Bad detection" and
"Belongs to…" stacked. With 44 unnamed in three groups (18, 10, 16), none
passes 24, so (b) does not trigger on today's Dogs list. It does trigger on
both dogs' Waiting (34 and 47). **The card's height is what makes the page
long**, not the column count: a UX decision for the architect.

**R53 step 1** (`uv run python tools/dog_bench.py`; the M900, 149 labelled
views: Aurora 40 day / 28 night, Mirana 63 / 18; 13 two-dog crops; 5 person
crops):

| Candidate | Day: nearest right | Night: nearest right | Wrong when naming 90 % of views (day / night) | Person crops named a dog at that threshold | Two-dog crops named | Cost per crop (M900) | Size | Licence |
|---|---|---|---|---|---|---|---|---|
| Histogram (today) | 98/103 | 42/46 | 2 / 3 | 5 of 5 | 12 of 13 | ~1,200 ms (GrabCut on a 320 px crop) | — | ours |
| DINOv2-small | **103/103** | **46/46** | 0 / 0 | 0 of 5 | 9 of 13 | 124–171 ms | 88 MB | Apache-2.0 |
| CLIP ViT-B/32 | 100/103 | 42/46 | 2 / 2 | 0 of 5 | 10 of 13 | ~102 ms | 352 MB | MIT |
| MobileNetV3-Large | **103/103** | **46/46** | 0 / 0 | 0 of 5 | 7 of 13 | **12 ms** | **12 MB** | BSD-3 code; ImageNet-trained weights |

- Right before the first wrong (a threshold sweep from the closest match
  up): histogram 91 of 103 by day and 26 of 46 by night. DINOv2 and
  MobileNet have no wrong answer at all, so every view (103, 46) is named.
- Median distance of a right answer, against how far the person crops sit:
  - MobileNet: day 0.174; every person crop is at the 97th–100th percentile
    of right answers or beyond.
  - DINOv2: day 0.182; person crops at the 95th–100th.
  - Histogram: day 0.206; person crops at the 12th–87th percentile, inside
    the right answers. That is the user's report.
- Two-dog crops are named the dog that fills more of the crop by every
  candidate. That is arguably right (it is in the picture), but the second
  dog is missed. The ratio of the nearest dog's distance to the second's
  spreads from 0.24 to 0.99 for every candidate, so a ratio rule (as today's
  0.6 and 0.8) would cut only the evenly mixed ones.
- The full per-crop numbers: run the tool, or `--json FILE`.

**Backlog 32 on production's face gallery** (`faces.accuracy`, read-only on
`C:\JARVIS\faces\gallery_arcface_w600k_r50.json`): 80 named Chosen views
(2 × 40), 0 unnamed views. **0 wrong at every threshold from 0.30 to
0.60**:

| Threshold | 0.30 | 0.35 | 0.40 (today) | 0.45 | 0.50 | 0.55 | 0.60 |
|---|---|---|---|---|---|---|---|
| Named for sure, of 80 | 77 | 73 | 66 | 39 | 23 | 12 | 4 |

## 6. What the review should look at hardest

1. **R42 (b)'s count is per analysis frame at 960×540.** Anything YOLO
   calls a person counts, and so does R46's relabelled box, since it is a
   person `Detection`. Two person boxes on one body (a split detection)
   would also fire. The NMS in `people.py` should prevent that; worth a look
   at `replay.py` traces of crowded events. **The best view sent is the one
   where a single person shows best** (`confidence × height`), not
   necessarily the frame with the most people. The phone may then show only
   the resident. A "crowd view" (the frame with `most_people`) would be the
   better picture, but it needs another file or another kept frame, so I
   did not build it without a decision.
2. **Waiting newest first** changes what the user sees: the order of the
   tiles was oldest first until now.
3. **R53: the leave-one-out is optimistic.** Views of one event are
   different frames, not copies, so a view's own event may still be in its
   gallery. A leave-one-**event**-out needs each view's clip, which views do
   not record (sightings do). The person crops and the two-dog crops are the
   honest part of the table. Only two dogs, very different in colour (white
   and black): the histogram's failure is at night and on dark non-dogs. A
   household with two dogs of one colour is where learned embeddings should
   matter most, and nothing here measures it.
4. **R53, MobileNetV3's weights licence**: torchvision's code is BSD-3; the
   weights come from ImageNet, whose terms are non-commercial research. This
   is the same class of question the user already accepted for InsightFace
   (CONTEXT 3). DINOv2 is Apache-2.0, weights included.
5. **Backlog 32: the table counts only Chosen views**, as matching does.
   "Exact copies" are cosine ≥ 0.9999, which per review 20 is what was
   asked. Near-copies (consecutive frames) still help each other, so 0
   wrong overstates certainty. And `learn_threshold()` reads `config.json`
   once per scan, once per naming and once per notification: cheap, but new
   I/O on those paths.
6. I could not see the accuracy table filled on the page. The test copy's
   two named people have no embeddings, and when I put production's face
   gallery in the test copy to look, the built-in browser's reload was
   refused ("Sensitive-Source Provenance"), so I put it back at once.
   Checked instead: the API in tests, the numbers above in Python, and the
   layout at 375 px with the widest values injected into the cells (301 px
   of 301, no overflow).

## 7. Items of the plan not done

None. Backlog 32's dogs half waits for R53's model, as planned.

## 8. Usage

| | 5-hour window | Weekly | Context |
|---|---|---|---|
| Start | 40 % (reset 23:00) | 33 % | 76 k |
| End | 60 % | 2 % (the weekly window reset at 19:00, mid-session) | ~285 k |

The session cost 20 points of the 5-hour window.
