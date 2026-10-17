# HANDOFF — developer session 29 (16/10/2026)

Item 7, part 1 finished, as BACKLOG 3 planned it: steps 0 to 4, in order,
except that step 3's code was committed while step 2's replay was still
running (both are independent; the measurements below are from the final
code).

## 1. What was done

### Steps 0 and 1 — `src/jarvis/tracks.py`, the first box joined (`7c6d4b1`)

One module, used by `tools/replay_tracks.py` and by the live loop:

- `Tracks` — one camera's `ByteTrackTracker`, ARCHITECTURE 7.16's
  parameters, with **its own ids**. `update(found, moment)` returns
  `(track id, detection)` for every detection; the id is `None` only for a
  box the tracker did not take (none with these parameters).
- `Record` — what a stretch of time saw: per track first/last moment,
  frames per label, the longest person run; `most_person_tracks()`; and
  `summary()`, the JSON form.
- `voted(labels)` — moved here from the tool, unchanged (a tie a person).

**How the first box is joined, and why this way.** The library spawns a
`ByteTrackTracklet` for every unmatched box and returns that box with
`tracker_id` −1; the tracklet gets its library id at its next match. The
spawned tracklet *object* is the same from birth to death, though, and is
in `tracker.tracks` right after the update that made it. So `Tracks.update`:

1. notes the tracklets it already knows;
2. after `tracker.update`, every returned box with a library id is found by
   that id among `tracker.tracks`; every box with −1 is matched to the
   tracklet the update just spawned whose state box equals it
   (`np.allclose`: the Kalman state is the initial box until the next
   predict);
3. the first time it sees a tracklet object it gives it the next id of its
   own counter (`dict` keyed by the tracklet object), and forgets tracklets
   the library pruned.

So the first box is credited at once, in the same update — no holding until
the next one, which matters live: an event that closes right after a body's
first box still has it. A box never matched again is simply a track of one
frame (`Back/2026-10-16/13-23-34`: now one person track in all three phases,
before none in two of them).

The alternatives, rejected: holding the box until the id appears (the plan's
first suggestion) needs the same tracklet bookkeeping plus a pending state,
and a box whose track dies unmatched would still need an id from somewhere;
allocating the *library's* id at spawn (or overriding `_spawn_new_tracks`)
would make every single box a confirmed track — `_get_alive_tracklets`
treats `tracker_id != -1` as mature — so a one-frame glitch would survive
misses for the whole buffer and could absorb a later box: the tracking
itself would change. Here the library's behaviour is untouched; only the
labels are counted differently. The comparison below confirms it: the
tracks are the same boxes as developer 28's, plus their first boxes.

**Thresholds 0 instead of the lowest live minimum.**
`track_activation_threshold` and `high_conf_det_threshold` are 0.0. The
detector already drops every box under its class minimum, so every box the
tracker receives is above the lowest minimum anyway: the result is the same
as 0.35, and a change of the minimums in Settings → Detection does not need
a new tracker. ARCHITECTURE 7.16's table should say so.

Tests: `tests/test_tracks.py` — a track of N boxes counts N labels (6 boxes:
person 2, dog 4, where the library alone counts 5); a body seen once is a
track of one frame; two bodies born in the same update each keep their own
first box; ids follow the body across two records and stay unique after a
gap; the longest person run (7 person then 11 dog → 7); seconds from the
record's start. `tests/test_replay_tracks.py` adjusted (no untracked box,
the first box counted).

### Step 2 — measured again with the first box joined (no commit; numbers in 5)

`replay_tracks.py` now prints each track's longest person run.

### Step 3 — tracks recorded live (`33ef04c`)

- `Camera` (cameras.py) holds one `Tracks` for the process's life, so ids
  are unique per camera and an id seen in two events is a walk joined
  across the cut. `Camera.detect` calls the detector and, **only when YOLO
  actually ran** on this frame (`SubjectDetector.last_run` moved — between
  runs `detect` returns the cached subjects), feeds the tracker the
  subjects the event gets (after R44, R46, duplicates and scenery), with
  `last_run` as the moment — the detector's own monotonic clock, the same
  one `EventRecorder.started` uses.
- A tracking failure is caught and logged ("Tracking failed on …") and that
  run goes untracked: recording must never stop the camera loop.
- `EventRecorder.update(frame, subjects, tracked=None)` adds `(moment,
  observed)` to the event's `Record` while recording, the starting frame
  included, and runs where YOLO found nothing too (they count for "at
  once").
- **Nothing that notifies or names changes**: `most_people`, the messages,
  the face scan read the same subjects as before.

Tests: an event records its tracks (JSON on disk equals the summary; a
person and a dog, three frames each, first second 0.0; `most_person_tracks`
1, nothing sent); an event fed no tracks writes neither key, and an old
event JSON still lists; `Camera.detect` feeds the tracker only when YOLO ran;
a tracker that raises leaves the subjects and logs. `test_on_off.py`'s fake
camera gained `detect`.

### Step 4 — the start on the M900 (no commit)

Measured with the test copy (`stream2`, port 8766) started three times by a
script that polls `/api/status`: answering after **6.8–7.4 s**, both
cameras' last frame under 5 s after **9.4–10.2 s**, against production's
90 s health check. A warm start (the `.venv` and the model cached); the
deploy's first start after a fresh `.venv` is the import warm-up's case
(ARCHITECTURE 18.7), not measured here.

## 2. Data format

The event JSON gains two **optional** keys, written only when the event saw
a track:

```json
"tracks": [
  {"id": 12, "first": 0.0, "last": 4.2, "frames": {"person": 7, "dog": 2}, "longest_person_run": 5}
],
"most_person_tracks": 1
```

- `id` — unique per camera for the service's life (restarts begin at 1
  again, so ids are only comparable between events of one run).
- `first`, `last` — seconds from the event's start (`started_at`, not the
  clip's start, which is `PRE_SECONDS` earlier), one decimal, never
  negative (the tracker's moment is a few ms before the recorder's).
- `frames` — YOLO runs of that track in this event, per label, the first
  box counted; labels other than person and dog (cat, bird…) appear as
  YOLO gave them, R44/R46's relabelling already applied.
- `longest_person_run` — the most consecutive person frames *among the
  track's own frames*: a run where the track was missed in between is not
  broken.
- `most_person_tracks` — the most tracks voted person (`voted`) in one YOLO
  run, the vote over the frames of this event; the number to set beside
  `most_people` (boxes at once).

Two keys rather than one: `most_person_tracks` is an event-level number like
`most_people`, which it mirrors. Nothing reads either key yet. Additive;
`uv run python tools/check_data.py`: **"Every file is readable by this
version."**

## 3. Suggested documentation

- **ARCHITECTURE 7.16** — "Nothing in `src/` uses it yet" is no longer
  true: `jarvis.tracks` runs live and records. The first-box limit (1) is
  solved; the method above. The thresholds row: 0, and why it equals the
  lowest minimum. The new numbers of section 5 replace or extend "What the
  numbers support"; the second limit (the resident carried into a dog) now
  has its run number.
- **ARCHITECTURE 8.4** — the two optional keys, after `people_thumbnail`
  ("optional since 16/10/2026").
- **ARCHITECTURE 19.2** (the files table) if it lists the JSON's keys.
- **ARCHITECTURE** — the live loop's order: motion → detector → tracker
  (only when YOLO ran) → recorder.
- `clips.py`'s and `tracks.py`'s docstrings point at ARCHITECTURE 7.16 and
  sections 5, 8, 19; `check_doc_refs.py` exits 0.

## 4. Worth explaining to the user

- **Object identity as a key** (PYTHON): `dict` keyed by the tracklet
  object. A class that does not define `__eq__`/`__hash__` hashes by
  identity, like Java's `Object.hashCode()` without an override, so the
  same object is the same key for its whole life — the trick that lets
  `Tracks` follow a tracklet before the library names it. Contrast with a
  `dict` keyed by `id(obj)`, which can be reused once the object dies.
- **`namedtuple._replace`** used in the test to move a box (`Detection` is
  immutable, like a C# `record` with `with`).
- **Reading a library's source before working around it**:
  `_spawn_new_tracks` and `_get_alive_tracklets` decided the method — the
  "obvious" fix, giving the id at spawn, would have changed which tracks
  survive.
- **A guard on a record-only feature**: `try/except Exception` with
  `logger.exception` in `Camera.detect`; why it is acceptable here (nothing
  depends on the result) and would not be around the detector itself.

## 5. Measurements

`replay_tracks.py`, lost buffer 3 s, three phases, on every clip of
ARCHITECTURE 7.16 (19 clips), on the M900; and the previous tool
(`dccf519`, first box −1) run again on the ten clips that matter, for a
side-by-side. Tracks are the same boxes in both runs; only the first boxes
are added.

**Update cost**: 0.03–0.34 ms median per update, as before.

### (a) R59's dog events — phases where no track is voted person

Developer 28's criterion (a dog event clears only when every person box is
in a dog-majority track; an untracked person box fails it):

| Event | Before (first box −1) | Now | Why |
|---|---|---|---|
| `Back/2026-10-15/20-54-37` | 2 of 3 | 2 of 3 | phase 1: the one person box (42×111, upright, 1.2 s before the dog's lying box) is now its own one-frame person track |
| `Back/2026-10-15/21-01-08` | 3 of 3 | 3 of 3 | the replay's YOLO never says person here |
| `Front/2026-10-15/22-00-19` | 2 of 3 | **3 of 3** | phase 1's person box joined the dog track (dog 20, cat 5, person 1) |
| `Front/2026-10-16/00-52-26` | 0 of 3 | 0 of 3 | person in every frame (runs 5, 7, 4) |
| `Back/2026-10-16/00-54-05` | 0 of 3 | **2 of 3** | phases 0 and 2: dog 4/person 2 and dog 3/person 2; phase 1 a person-only track of 4 |
| `Front/2026-10-16/14-51-12` | 1 of 3 | 1 of 3 | phases 0, 1: a two-frame track dog 1/person 1, a tie → person |

**11 of 18 phases cleared, against 8**; two events in every phase
(21-01-08, 22-00-19), against one. Every true person kept: in each of the
residents' events (`Back` 18-30-12, 18-42-31, 00-01-03, 00-05-30, 00-11-41,
13-23-34; `Front` 19-24-49, 19-41-18, 11-31-51, 21-47-33) every track with a
person frame is voted person, in every phase; `13-23-34`, the one-frame
person, is now a person track in all three phases (before, two had none).

### (b) Longest person run

- **Dog-majority tracks** with any person frame: the longest run is **1**
  in every one (22-00-19 ×3, 00-54-05 ×2, 14-51-12 phase 2, 19-25-05
  phase 0).
- **The resident carried into a dog** (`Front/2026-10-16/00-12-09`
  phase 2, track #3: dog 11, person 8, cat 1): run **8**.
- True people's own tracks: from 1 (the one-frame tracks) to 23.

So a rule "voted dog, but a run of N person frames keeps a person" keeps
the carried resident and still clears every dog-majority dog track for any
**N from 2 to 8**; **N = 2** is the cautious end, one more person frame than
any dog showed. Eight dog events and one carry case: small, say so.

What the run cannot fix is the other failure: **short tracks that start as
person**. The dog events still failing are a one-frame person track
(20-54-37 phase 1), a 1–1 tie (14-51-12 phases 0–1), and 00-52-26 whose
every frame is person. A one-frame person track is also a true person
(13-23-34 is the whole event; 00-05-30 begins with one at the frame's left
edge in every phase, 18-30-12 with one in phase 2; 19-24-49 phase 2 has two), so no rule on length alone
separates them.

### (c) R58 — tracks voted person at once against boxes at once

| Event | Boxes at once | Tracks at once, before | Tracks at once, now |
|---|---|---|---|
| `Front/2026-10-16/14-53-35` | 1, 2, 2 | 1, 1, 1 | 1, 2, 2 |
| `Front/2026-10-15/19-25-05` | 2, 2, 2 | 2, 1, 1 | 1, 2, 2 |
| `Front/2026-10-16/00-12-09` | 2, 2, 2 | 2, 2, 2 | 2, 2, 2 |
| `Front/2026-10-15/21-47-33` | 1, 1, 1 | 1, 1, 1 | 1, 1, 1 (the nested pair does not reproduce) |

**Joining the first box undoes most of R58's gain**: the false second body,
fixed before in 4 of the 5 phases with two boxes, is fixed now in 1. The reason is the
same as in (b): the second "person" is a short track whose first box is
person — 14-53-35 phase 1 a two-frame person track overlapping the
resident, phase 2 a 1–1 tie; 19-25-05 phases 1–2 one-frame person tracks.
Before, that first box was −1 and simply not counted, which looked like a
fix and was a blind spot — the same blind spot that dropped 13-23-34's real
person. Phase 0 of 19-25-05 goes the other way: its two-frame track starts
as dog, so it is now voted dog.

**What this supports for part 2**: the vote plus a run of N ≥ 2 for R59's
dog-majority tracks; for R58 and the remaining R59 failures, a track's
length alone cannot decide, so the next signal is the relation between a
short person track and a dog track near it in place and time (a body that
is a dog for 10 frames and "person" for 1 next to it) — to be measured on a
day of production's `tracks`, which step 3 now records.

### The live path on a real clip

No live event happened while the test copy ran (15 minutes; production had
none since 19:33 either), so the JSON was checked another way: a scratch
script ran `Front/2026-10-15/19-25-05.mp4` through `MotionDetector`,
`Camera.detect` and `EventRecorder` with the video's clock in place of
`time.monotonic`, messages and assembly stubbed. The event JSON came out
with 7 tracks (ids 1–7, `first` from 0.0, the one-frame person tracks and
the dog track with its one person frame as in 5a/5c) and
`most_person_tracks` 2 beside `most_people` 2. The first real event of the
test copy or of production after the release is still worth reading.

### Start (step 4)

9.4, 9.6 and 10.2 s from launch to both cameras fresh; 6.8–7.4 s to the
first `/api/status` answer.

## 6. What the review should look at hardest

- **`Tracks._born_from`** — matching a −1 box to the tracklet spawned from
  it by `np.allclose` of the state box. It relies on the state being the
  initial box until the next predict (true for `XYXYStateEstimator`); two
  identical boxes spawned in one update would be matched in order, which is
  harmless (the boxes are equal). With `track_activation_threshold` 0 every
  unmatched box spawns; if that changed, a −1 box with no tracklet returns
  `None` and is counted as untracked, not dropped.
- **`Camera.detect`'s "YOLO ran" test** — `last_run` changing. A clock that
  does not move between runs would skip feeding; `detect` sets `last_run =
  now` only when it runs, so a moved value means a run.
- **The record starts at `_start`** — runs before the event starts (YOLO ran
  on motion, found nothing) are not recorded, so a track that began before
  the event appears with `first` 0.0 and frames from the event only.
- **The broad `except Exception`** around the tracker in the camera loop.
- **R58's numbers** (5c): joining the first box made the count of person
  tracks worse on R58's two events; the review should agree that this is
  the honest number before part 2 is planned on it.

## 7. Not done

Nothing of the plan left out. Not planned and not done: acting on tracks
(part 2).

## 8. Usage

| | 5-hour window | Weekly | Context |
|---|---|---|---|
| Start | 0 % | 29 % | 77k tokens |
| End | 13 % | 30 % | 210k tokens |
