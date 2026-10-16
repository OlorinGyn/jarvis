# HANDOFF — developer 28: R61, and tracking (item 7) part 1 measured

The plan of BACKLOG 3 was followed in its order through step 3. **Step 4
(recording tracks in the live loop) was not started:** the 5-hour window was
at 83 % when step 3's numbers came in, and the plan says to stop after step 3
with a coherent commit when the session runs short. One addition to the plan:
after the first run, the tool gained each track's vote and a count of the
tracks voted person, because step 3 (a) and (b) could not be answered from
label counts alone (`fe17a07`).

## 1. Items done

**R61 — `f549760`** (`src/jarvis/notify.py`, `src/jarvis/outage.py`,
`tools/replay_notifications.py`; tests in `test_notify.py`, `test_outage.py`,
new `test_replay_notifications.py`). Each part was reproduced by a failing
test first.
- (a) `_end_of_floor` renewed `_incident["last_sent"]` whenever an incident
  existed. It now renews it only while the incident is still open:
  `_floor["last_loud"] - _incident["last_sent"] < notify_cooldown`. Test:
  `test_the_floor_text_does_not_reopen_an_incident_that_closed`. Quiet window
  10 s; Front at 0, Back at 5 is held back; the floor fires at 30, after the
  incident closed at 15; Back at 35 must open a new incident. At HEAD it was
  silent and nothing was held back (one timer); now it is held back (two
  timers).
- (b) `messages()` strips the colon from a camera line's camera when its text
  starts with `CAMERA_WORDS` ("no picture since", "picture back"). `replay()`
  passes `force=True` for those lines, as `camera_down` does live. Tests: a
  fake log with two camera lines. The camera is now "Back" and not "Back:",
  and there is one floor text, not two.
- (c) `_duration(minutes)` in `outage.py` gives "6 min", "1 h" or
  "18 h 5 min". Parametrised test.

Closes **R61**.

**Item 7 step 1, the dependency — `99e7933`** (`pyproject.toml`, `uv.lock`,
`tools/production.ps1`).
- `uv add trackers` brings `trackers` 2.6.1, `supervision` 0.31.0, `scipy`
  1.18.1, `matplotlib` 3.11.2, `pillow` 13.0.0, `av`, `rich`, `pyyaml`,
  `tqdm` and small packages. There is no second OpenCV: `opencv-python`
  5.0.0.93 stays the only one.
- `production.ps1` gains `WarmUp $target`, called in `Update` after
  `FetchModels` and **before** `Hold`/`StopService`. It runs
  `git archive --format=zip` of the target's `pyproject.toml`, `uv.lock` and
  `.python-version` into `%TEMP%\jarvis_warmup`, then
  `uv sync --frozen --no-dev --no-install-project`. It then runs a small
  script (`$WarmUpScript`) that imports every top-level module of
  `importlib.metadata.packages_distributions()` once and prints the seconds.
  The folder is deleted at the end.
- A failure only prints a warning and the update goes on: the real `Sync`
  after the stop would fail on its own and roll back as before.
- Why this works: uv hardlinks from its cache, so the real sync into
  `C:\JARVIS\.venv` after the stop lands the same files that Smart App
  Control has just seen.

**Item 7 step 2, the replay — `4d3c6b3`, `fe17a07`**
(`tools/replay_tracks.py`, `tests/test_replay_tracks.py`).
- YOLO runs as in `person_signals.py`: every frame with motion, through three
  phase `SubjectDetector`s. Each phase's kept detections, every label, are
  stored as `(video, time, detections)`.
- Then one `ByteTrackTracker` per phase runs on them, once for each
  `--lost` value. YOLO runs once and the buffer sweep is cheap.
- `--join` places several events on one timeline at `started_at − PRE_SECONDS`
  and skips a later video's frames that the one before already covered.
- Per track it reports life, frames by label, dog share, the vote, the
  largest box, "nested" when it sat at least 0.8 inside another track's box
  (`inside_smaller` from `person_signals`), and the clips it spans.
- Per phase it reports the most tracks at once, the most person boxes at
  once, the most tracks voted person at once, the boxes left untracked by
  label, and the median update cost.

## 2. Data format

None. No file read from or written to disk changed. `tracks` in the event
JSON was step 4 and was not built. `check_data.py` was not needed.

## 3. Suggested documentation updates

- **CONTEXT 9** (repository map): `tools/replay_tracks.py`, "the live
  detector's boxes through a ByteTrack tracker per phase: what each track saw
  (item 7)". **CONTEXT 10**:
  `uv run python tools/replay_tracks.py <video>... [--join] [--lost 3 ...]`.
- **ARCHITECTURE 18.7** (production updates): the warm-up step, and why. The
  first import of a new binary package under Smart App Control can take tens
  of seconds, and `HealthSeconds` is 90. So the target's environment is built
  in `%TEMP%` and imported while the old version still records; the hardlinks
  from uv's cache carry what Smart App Control has seen.
- **ARCHITECTURE 12.11 / 12.12**: the floor's text renews only an open
  incident; the return of a camera reads "18 h 5 min without".
- **ARCHITECTURE 7.15 or a new 7.16**, "Tracks": the numbers of section 5
  below, the parameters, and the two limits found: the first box of every
  track is returned untracked, and the Kalman filter's constant velocity
  carries a track away during a gap.
- **INSTALL**: the dependency list, if it names them.
- **BACKLOG 1 item 7**: part 1 measured; part 2 needs what section 6 lists.

## 4. Concepts worth explaining to the user (PYTHON.md)

- **Multi-object tracking, ByteTrack.** The tracker does not look at the
  image. It keeps a Kalman filter per object, a constant-velocity model of the
  box, much like a physics-step predictor in a game loop. At each update it
  predicts where every box should be, then matches the predictions to the new
  detections by IoU with the Hungarian algorithm (`scipy`), in two rounds:
  confident detections first, weak ones second. ByteTrack's idea is that
  second round, which keeps a track alive through frames where YOLO hesitates.
- **The library's units.** `lost_track_buffer` is counted in "30 FPS frames"
  whatever `frame_rate` says, so 3 s is `90`. With `timestamp=` passed to
  `update`, the budget becomes seconds (`lost_track_buffer / 30`) and the
  Kalman step becomes `elapsed × frame_rate`. A good example of reading the
  source (`trackers/core/base.py`) before trusting a parameter's name.
- **`supervision.Detections`**: a struct of parallel numpy arrays (`xyxy`,
  `confidence`, `class_id`, `data`) — column-oriented, like a DataFrame
  without pandas. Indexing it with an array of indices (`detections[idx]`)
  reorders every column at once, which is why the tool keeps the label in
  `data` rather than relying on order.
- **PowerShell and native programs**: `git archive -o file` instead of piping
  bytes (PS 5.1's pipeline turns bytes into text). The function sets
  `$ErrorActionPreference = 'Continue'` locally, so a line on stderr does not
  become a terminating error. And testing one function of a script that runs
  an action when it loads: parse it with
  `[System.Management.Automation.Language.Parser]::ParseFile` and define only
  its functions.

## 5. Measurements

All on this M900, with copies of production's events in `clips/`
(`C:\JARVIS` only read). Parameters, and why:

| Parameter | Value | Why |
|---|---|---|
| `track_activation_threshold` | 0.35 | the lowest live minimum (Settings → Detection; production uses the defaults 0.35 / 0.45 / 0.45). The library's 0.7 would start no track for the night's people |
| `high_conf_det_threshold` | 0.35 | the same. A new track spawns only from a high detection, so the library's 0.6 would keep a 0.40 person from ever starting one. The detector already drops everything under its minimums, so ByteTrack's low round is empty |
| `frame_rate` | 10/3 | one phase sees every third analysis frame (`ANALYSIS_FPS` 10) |
| `lost_track_buffer` | seconds × 30 | the library's unit; 3 s by default, swept 1–8 s for (c) |
| `minimum_consecutive_frames` | 1 | a track gets its id at its second matched box; 2 would delay it one more |

**The first import (step 1).**
- In a fresh `.venv` built by `uv sync` from the cache: **9.1 s**, then
  **5.0 s** for the second. Review 29's 89 s was the first time Smart App
  Control ever saw these files.
- `WarmUp` run alone against a tree with the new lock: **26.7 s** in all,
  **15.6 s** of it the imports of every package. All of it happens before the
  stop.
- A bad version name: a warning, and the update continues.

**(a) R59 — the vote over a track's frames** (dog only with more dog than
person frames, a tie a person). Seven dog events, three phases each:

| Event | What the vote does |
|---|---|
| `Back/2026-10-15/20-54-37` | YOLO's person box is in phase 1 only, and that box is a track's first box, untracked. The other phases have no person box at all |
| `Back/2026-10-15/21-01-08` | no person box in the replay at all (the 1 of 7 developer 26 also could not reproduce) |
| `Front/2026-10-15/22-00-19` | the person frame sits in dog tracks (dog 18, cat 7, person 1): **voted dog** in phases 0 and 2; in phase 1 the person box is untracked |
| `Front/2026-10-16/00-52-26` | **voted person** in all three phases: YOLO says person in 6 of 6 frames. The vote cannot fix it |
| `Back/2026-10-16/00-54-05` | dog 4 person 1 → voted dog in phases 0 and 2, but each also has one untracked person box; phase 1: a person track of 3 frames |
| `Front/2026-10-16/14-51-12` (day) | phases 0 and 1: a one-frame person track (voted person); phase 2: dog 2 person 1, voted dog |
| `Front/2026-10-16/00-12-09` (resident + dog) | the resident's tracks voted person. In phase 2 one track took the resident (10.7–13.5 s) and then the dog (15.3–18.3 s): dog 11, person 7, **voted dog**. The event keeps a person only through a second resident track |

- True people (`Back/2026-10-15/18-30-12`, `Back/2026-10-16/00-01-03`,
  `00-05-30`, `00-11-41`, `13-23-34`, `Front/2026-10-15/19-24-49`,
  `Front/2026-10-16/11-31-51`, plus the R58 events): **every track with a
  person frame was voted person**. The mixed ones were 1–1 (a tie) and
  7 person to 1 dog.
- `18-42-31` and `19-41-18` were run joined (c) and hold only person tracks.
- The resident half hidden behind the car (`19-24-49`) kept 1–4-frame person
  tracks, all voted person.
- `13-23-34`: the resident is one box in phases 0 and 1, untracked, and a
  1-frame track in phase 2.

**What (a) supports.** The vote keeps every true person a person here. It
clears a dog event only when every person box of the event falls inside a
dog-majority track. As measured, that holds for **22-00-19 in 2 of 3
phases** and **14-51-12 in 1 of 3**, and never for 00-52-26.

**Two limits decide the rest:**
1. **The library returns a track's first box untracked (−1).** A person seen
   once, or the first frame of a dog track that YOLO called person, has no
   vote. 20-54-37, 00-54-05 and 22-00-19's phase 1 fail only through such a
   box. Part 2 needs the first box joined to its track: hold its label until
   the next update, or read the track's history. A true person seen once
   (13-23-34) must still reach the phone.
2. **A track can carry a resident into a dog** (00-12-09, phase 2, 3 s
   buffer). The person frames of that track would turn into dog. A rule
   "voted dog → no person" must not drop a track that has many person frames
   of its own. For instance, keep a person when a run of N consecutive person
   frames exists, measured.

**(b) R58 — tracks at once against boxes at once**

| Event | Person boxes at once | Tracks voted person at once (phases 0/1/2) |
|---|---|---|
| `Front/2026-10-15/21-47-33` (one body, two boxes live) | **1** — the nested pair does not reproduce in the replay | 1/1/1; the body is two tracks in sequence in phases 0 and 1 (1.5–3.9 s, 4.8–8.1 s) |
| `Front/2026-10-16/00-12-09` (resident + dog) | 2 | 2/2/2 — at 17.8–18.2 s two short person tracks side by side, not nested ≥ 0.8. Not fixed |
| `Front/2026-10-15/19-25-05` | 2 | 2/1/1 |
| `Front/2026-10-16/14-53-35` | 1/2/2 | **1/1/1** — the second box is a dog track (dog 14, cat 3) |

So the count of person-voted tracks fixes **14-53-35 in every phase** and
**19-25-05 in 2 of 3**. It does not fix 00-12-09, and 21-47-33 cannot be
judged from the replay.

**(c) The boundary — four walks cut in two, `--join`, buffers 1, 2, 3, 5, 8 s**

| Pair | Gap from the last box of event 1 to the first of event 2 | Joined? |
|---|---|---|
| `Back/2026-10-15/18-42-31` + `18-42-40` | 6.9 s, same spot (boxes at x 671 and 706) | **no, at any buffer up to 8 s** |
| `Front/2026-10-15/19-41-18` + `19-41-33` | 8.4 s | no |
| `Front/2026-10-16/00-30-11` + `00-30-18` | none: the person stays in view across the stitch | **yes, at every buffer**, the track spans both |
| `Front/2026-10-16/14-19-40` + `14-19-58` | 9.0 s | no |

- 18-42 is not joined even with a buffer longer than its gap. The Kalman
  filter keeps moving the predicted box at the walk's last speed, so after
  7 s the prediction is far from where the person came back.
  `test_a_gap_longer_than_the_buffer_starts_a_new_track` shows the same: only
  a still body is joined at 8 s.
- What a longer buffer joined wrongly: at 8 s, 00-30's dog box at 15.3 s and a
  person box at 21.6 s became one track (dog 1, person 1). At 3 s, 00-12-09's
  resident and dog in phase 2 (above).
- Production's events, consecutive person → person pairs on one camera: 624.
  - 119 start within 3 s of the previous event's end, which is within ~8 s
    of its last box (the event ends `POST_SECONDS`, 5 s, after it).
  - 213 within 8 s.
  - Which of those are one person is not known.

**What (c) supports.** ByteTrack's buffer does not bridge the cut events: a
gap of 7–9 s with the body out of view defeats the constant-velocity
prediction, whatever the buffer. Joining the walk across events needs
appearance (re-identification) or a rule of "the same place within N s",
not a longer buffer. The buffer of 3 s already joined a resident to a dog
once.

**(d) Cost.** The median of one `update` on this M900 is **0.03–0.33 ms**,
against a YOLO run of tens of milliseconds. One tracker per camera adds
nothing measurable to the live loop.

## 6. What the review should look at hardest

- `WarmUp` in `production.ps1`. It ran here as an isolated function (the
  AST trick), never inside a real `-Action update`, which only production
  can run.
  - Check the zip of three paths: every release tag has `.python-version`?
    If not, `git archive` fails and only a warning follows.
  - Check that importing every top-level module has no side effect worth
    fearing. `pylab` and `mpl_toolkits` are imported; all of it runs under
    `-W ignore`, with errors swallowed.
- `_end_of_floor`'s new condition uses the settings the timer was created
  with, which is also where the quiet window was read when the floor
  started.
- The timeline of `--join` assumes a video starts exactly at
  `started_at − PRE_SECONDS`. It really starts at a segment boundary at or
  before that, so (c)'s gaps can be off by up to a segment.
- The interpretation of (a): "cleared" counts untracked person boxes as
  persons, the safe side.

## 7. Not done

- **Step 4** (one tracker per camera in the live loop, an optional `tracks`
  in each event's JSON). Not started: the window was at 83 % after step 3,
  and the plan allows stopping here. Section 5's limits also bear on it: the
  JSON's frames per label would miss every track's first box unless that box
  is attributed.

## 8. Usage

| | 5-hour window | Weekly | Context |
|---|---|---|---|
| Start | 75 % (reset 23:30) | 26 % | 82 k |
| End | 84 % | 27 % | ~205 k |

About 9 points of the 5-hour window and 1 of the week, with ~45 minutes of
the session spent waiting for two background replays of 25 and 9 events.
