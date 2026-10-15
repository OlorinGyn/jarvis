# HANDOFF — developer 25: R55, then backlog 32 for dogs

Both items of the plan in `docs/BACKLOG.md` 3 are done, in its order.

## 1. Items done

### R55 — the accuracy table leaves out each probe's whole event (`cde3087`, closes R55)

- **`view_events`** in every gallery entry, faces and dogs alike (the shared
  `faces.Gallery`): `{"<12hex>.jpg": "Back/2026-10-14/11-05-41"}`, keyed by
  the view's photo name, so a move never misaligns it. `faces.event_of(clip)`
  makes the event from the clip's last three path parts (camera/day/time),
  so an archived clip is the same event.
- **Filled when a view is stored:** `Gallery.add(..., event)` and
  `Gallery.reinforce(..., event)`; `_scan_clip` and `dogs.record` pass
  `event_of(clip)`. `_merge` carries the source's events into the target;
  `save()` prunes the keys whose photo left the entry's views and queue.
  Demote, promote, spread, put back (report Undo) keep them by construction.
- **Recovered for views stored before:** `Gallery.recover_events()`, run at
  every start in `cameras.main()` beside the migrations, looks only at views
  with no key. Rule 1, the same picture: a sighting photo of the same size
  whose 16×16 grey thumbnail differs by < 1.0 on average, all of one event.
  Rule 2, written together: the sighting photos written within 2 s of the
  view photo (mtime), all of one event. A view found by neither is written as
  `""`, so it is tried once. Only the sighting folders of the photo's day and
  the days beside it are read. The counts are logged ("Events of the face
  views stored before …").
- **`faces.accuracy`** leaves out every reference of the probe's event
  (`_left_out`), and the exact copies as before; a probe whose event is
  unknown leaves out only its copies and is counted in the new field
  `unknown_events`. The unnamed column follows the same rule. The page says
  "each leaving out its own event" and, when there are any, how many views
  have no known event; the face panel's explanation was updated to match.
- `tools/check_data.py` checks `view_events` (a dict of strings to strings)
  in both galleries (`check_view_events`).

### Backlog 32 for dogs (`bc94747`)

- `config.json` key **`dog_sure_distance`**, default 0.33 (`dogs.SURE_DISTANCE`
  now reads `settings.DEFAULTS`), range `settings.DOG_SURE_RANGE` (0.20,
  0.39 = `PROBABLE_DISTANCE`, a test ties them), refused outside it by the
  page's POST and read as the default by `load()`.
- `dogs.sure_distance()` is read **once per operation** and passed to
  `match(descriptor, gallery, sure)` in the four places of the plan:
  `record` (once per call, before the loop over boxes), `_absorb` (once per
  naming), `guess` (once per entry) and `identify` (the first message).
  `match` without `sure` uses the module constant, so `tools/dog_tuning.py`,
  which patches `SURE_DISTANCE`, still works.
- `dogs.accuracy(gallery, distances)`: leave-one-event-out on DINOv2's
  distances, per lighting, at the fixed `SURE_RATIO`, through a small
  `_Reference` matrix (one product per probe, `np.minimum.at` per dog). Rows
  `SURE_SWEEP` 0.20–0.38 by 0.02 plus 0.39, plus the current choice.
- `/api/accuracy/dogs` and a second panel in Settings → Detection: Distance,
  Day (`sure/views` and, smaller below, the share right), Night (same),
  Wrong, Unnamed. The face and dog panels now share one script
  (`surePanel` in `app.js`); `#accuracy-table` became the class
  `.accuracy-table`, and the panels' result, summary and default button are
  found by class inside their form.

## 2. Data-format impact

Additive only.

- Gallery entries (`faces/gallery_arcface_w600k_r50.json`,
  `dogs/gallery_dinov2_small.json`): optional `view_events`. Checked against
  `v2026.10.15` itself (a worktree of the tag on a copy of production's
  galleries with the keys): it loads both, saves after `set_resident` and
  `trim`, and all 138 + 205 keys survive, since entries are written back
  whole. An older version's merge would not carry the keys into the target:
  those views fall back to "unknown", never to a wrong event.
- `config.json`: optional `dog_sure_distance`.
- `check_data.py`: "Every file is readable by this version." on the test
  copy, and no problem on the copies of production's galleries after the
  recovery.

## 3. Suggested documentation

- **ARCHITECTURE 10.15** (faces' table): leave-one-event-out, `view_events`,
  `unknown_events`, the before/after numbers below; the old "optimistic
  until R55" note can go.
- **ARCHITECTURE 20** (dogs): `dog_sure_distance`, `sure_distance()` read
  once per operation and where, the dogs' table and its numbers, and why the
  ratio is not on the page.
- **ARCHITECTURE 19.1** or wherever the galleries' format is listed: the
  `view_events` field, its key, and `recover_events` at start (the two rules,
  `""` for tried, the day window).
- **CONTEXT 10** tuning constants: `faces.TINY_SIDE`, `SAME_PICTURE`,
  `WRITTEN_TOGETHER_SECONDS`; `dogs.SURE_SWEEP`, `COPY_DISTANCE`;
  `settings.DOG_SURE_RANGE`.
- **BACKLOG**: R55 closed; backlog 32 done for both halves. **PENDING**: the
  user's check of the dog panel on the M900 joins item 32's.

## 4. Worth explaining to the user

- **Leave-one-out and its leak**: why a probe's twin from the same event made
  the table look better than it is — in Java terms, testing on the training
  set. The dog result shows when it does not matter: one crop per dog per
  event leaves nothing to leak.
- **`np.minimum.at(per_dog, owners, distances)`**: an unbuffered "group by
  owner, keep the minimum" in one call, like a `Collectors.groupingBy` with
  `minBy`, without a Python loop.
- **A perceptual comparison instead of bytes**: the 16×16 grey thumbnail
  (`cv2.resize` with `INTER_AREA`, which averages) finds one picture saved
  twice at different JPEG qualities, where a SHA-1 would differ.
- **File mtime as evidence** (`Path.stat().st_mtime`): what it can prove here
  and its weakness (any copy without `-p`, any rewrite, changes it).
- **A closure as a small object** in `app.js`: `surePanel({...})` keeps
  `fallback` private and returns `{ load }`, like an anonymous class
  instance in Java.

## 5. Measurements (copies of production's `faces/` and `dogs/`, taken 15/10 ~17:00; `C:\JARVIS` only read)

**Recovery:** faces 138 views — 81 by the same picture, 57 written together,
0 unknown; dogs 205 views — 205 by the same picture; 0.75 s and 0.78 s, a
second run None. Checked against the 83 face views that are byte-identical
to a sighting photo: 81 agree; the 2 others are one picture in **two**
sightings of two different clips (17:45:14 and 17:45:51 on 10/10; 12:56:54
and 12:57:54 on 13/10), resolved by the time written, rightly.

**Faces' table, production's copy (80 named views, 0 unnamed), sure / wrong:**

| Threshold | Before (copies left out) | After (event left out) |
|---|---|---|
| 0.300 | 77 / 0 | 69 / 0 |
| 0.350 | 73 / 0 | 60 / 0 |
| 0.400 (today) | 66 / 0 | 39 / 0 |
| 0.450 | 39 / 0 | 15 / 0 |
| 0.500 | 23 / 0 | 4 / 0 |
| 0.550 | 12 / 0 | 0 / 0 |
| 0.600 | 4 / 0 | 0 / 0 |

Still no wrong answer at any threshold; what was optimistic was the
coverage: at today's 0.40 a view of a resident is named for sure by another
event's view 39 times in 80, not 66.

**Dogs' table, production's copy (56 day views, 24 night, 44 unnamed),
identical by event and by copies only:** sure day/night (all 100 % right),
unnamed crossing — 0.20: 21/2, 8; 0.24: 35/2, 15; 0.28: 39/5, 21; 0.30:
40/7, 24; **0.33 (today): 44/9, 26**; 0.36: 44/9, 28; 0.39: 46/9, 28. No
wrong answer anywhere in the range. Computed in ~40 ms.

**Page:** checked in the built-in browser on the test copy with production's
galleries swapped in (and restored after, the test copy's own backed up in
`backups/dev25_test_galleries/`): at 375 px the dog table is 301 px in a
335 px panel, no horizontal scroll; on the desktop it sits in the settings
column at 442 px. Choosing 0.30 and Save wrote it ("Now 0.30"), "Back to the
default" returned 0.33. The face panel kept its styles after the
id-to-class change.

**Tests:** 313 pass (304 + 9 new in `test_dog_sure_distance.py`; R55's 8 in
`test_view_events.py`); 0 comments; `check_doc_refs` 0 broken.

## 6. What the review should look at hardest

- **Overlapping clips.** One picture sat in two sightings of two clips 37 s
  and 60 s apart: a clip's pre-roll covers the previous event's frames. So
  leave-one-event-out still keeps a twin when two events overlap. Worth
  measuring how often a named view's nearest reference is from an
  overlapping clip of the same camera; if it matters, the rule could treat
  events of one camera whose spans overlap as one.
- **The mtime rule** for the 57 face views. It is the only evidence for the
  non-best views; the 2-s window held on production (nearest ≤ 0.1 s, next
  other event ≥ 6 s), but a copy of `faces/` without preserved times would
  turn it into "not found" or, worse, a wrong match if all photos got the
  same time. Recovery runs only once per view, so production's first start
  of this version is the moment that counts.
- **The unnamed column now leaves out exact copies** too (it did not
  before), and its own event: a deliberate symmetry with the probes.
- **The test copy's dog gallery got its events at 17:04:42**, before this
  session ever started the service with the new code, and I could not tie it
  to any command of mine (the test suite does not touch it — checked). If
  the architect ran something in this folder then, that explains it.
- `recover_events` runs under the gallery lock at start, before the web and
  the cameras; with a large backlog of old sightings it reads three days of
  photos per distinct day — fine at today's size (0.8 s).

## 7. Not done

Nothing of the plan.

## 8. Usage

| | 5-hour window | Weekly |
|---|---|---|
| Start | 56 % (reset 23:59) | 12 % |
| After R55 | 65 % | 13 % |
| End | 72 % | 14 % |

Context at the end: ~245k tokens (24 % of 1M).
