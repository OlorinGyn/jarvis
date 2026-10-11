# Handoff - developer to architect

Developer session 11, 11/10/2026, 13:00-13:55. Plan: CONTEXTO 14.4, followed
in order; every item done or measured.

## 1. Items

| Item | Commits | What and why |
|---|---|---|
| Backlog 23 | `b3fb302`, `5f3dbd9` | "Bad detection" replaces R27's Dismiss, for unnamed faces as well as dogs, and for each label of a recording (buttons "Not a person", "Not a dog"… in the player). New module `reports.py`: an unnamed entry leaves the gallery (`Gallery.take_out`, which replaces `DogGallery.dismiss`), its sightings and their crops are deleted, and `reports/face/` or `reports/dog/` gets the card's photo plus a JSON: kind, verdict, source (`gallery`/`event`), reported_at, label, camera, at, time, clip, score, box, the entry's embeddings and every sighting. A rejected event label goes to `reports/<label>/` with the best view and the whole event JSON; the event's JSON gains `reported_labels` and the card stops showing that label (`labels` on disk keeps what the detector said). `reports/` is git-ignored like `faces/`. Routes: `POST /api/persons/{id}/report`, `POST /api/dogs/{id}/report` (the old `/dismiss` is gone), `POST /api/events/{camera}/{day}/{HH-MM-SS}/report` with `{"label": …}`. |
| Backlog 24 | `cdc27d6` | "Analyse" on a person's or dog's page when views + queue exceed 40. `faces.spread()` is greedy farthest-point selection over a distance matrix: `Gallery.distances` is 1 − cosine for faces; `DogGallery.distances` is `dogs.distance` (Bhattacharyya), with day against infrared set to **infinity**, so whichever lighting is not yet chosen is always the farthest and both are always kept. The favourite photo is the starting point, so it is always kept. `GET …/spread` returns the proposal (which of all the views stay, a SHA-1 signature of the embeddings, and the closest pair kept now and after); `POST …/spread` with `keep` and `signature` applies it, or answers 409 when the gallery changed meanwhile. The page shows every view, those that would leave faded, and "Keep these 40". |
| R35 | none | Looked at the five events first, as planned. **Every box at a ratio of 1.5–2.0 at the bottom edge in them is a real person** (see 5), so 1.5 is unsafe, and so is the alternative: a height condition (boxes under a third of the frame) would drop a person's head and shoulders in the bottom-right corner, 55–101 px tall (0.10–0.19 of the 540 px analysis frame), in 15:12:59 and 15:14:15. No code changed. |
| R30 (b) | `afefe20` | New tool `tools/face_tuning.py`: for the clips of each named person, every good face on a person (frontal or not), banded by nose offset and eye spread, scored against that person; faces from person clips with no named person give the other side. **Limits unchanged**: see 5. |
| R31 | `d00b99f` | `faces._detect()`: YuNet runs on a copy at most `DETECT_WIDTH` = 960 px wide, and each face found is detected again on a full-size region around it (`REFINE_MARGIN` = 1.0 face size, `_refine`), so the landmarks used by `alignCrop` keep full-size precision. The refinement matters: with landmarks only scaled up from 960 px, the embeddings moved (median cosine 0.60 to the full-size ones). |
| R32 | `ef464f8` | A FastAPI lifespan installs `web.quiet_disconnects` as the exception handler of uvicorn's own event loop: `ConnectionResetError` is dropped, everything else goes to the default handler. Reproduced first: production's log has 27 `_call_connection_lost` tracebacks, all `ConnectionResetError` [WinError 10054]. |

## 2. Data format

All additive. New files: `reports/<kind>/<YYYY-MM-DD_HH-MM-SS>_<hex6>.json` and
`.jpg`. New optional keys: `reported_labels` (list) in an event's JSON; `box`
(`[x, y, w, h]` in the frame the detector saw: full size for faces, analysis
size for dogs) in new face and dog sightings. Backlog 24 only reorders
`embeddings`, `views`, `pending` and moves `cover` within them. Deleted on the
user's click: an unnamed entry's view photos, sightings and sighting crops
(their data is copied into the report first).

`check_data.py` reads the reports (`reports.REQUIRED_KEYS`, crop present) and
checks `reported_labels`; on this copy: 214 events, 7 people, 20 face
sightings, 21 dogs, 22 dog sightings, 0 reports — "Every file is readable by
this version." 79 tests pass (64 before); no comments in `src/` or `tools/`.

## 3. Suggested documentation

- CONTEXTO 8: backlog 23 and 24 done; 13.4 table: R31, R32 done; R35 and
  R30 (b) measured, no change (texts below).
- ARQUITETURA 20 (dogs) and 17.10 (People): Bad detection instead of Dismiss;
  Analyse and the farthest-point selection; a new section for `reports/` as
  the evidence store (what a report holds, how a review should read it).
- ARQUITETURA 12.10 (R18): the five R35 boxes and why neither rule is safe.
- ARQUITETURA, the face scan (10.9 / 21): detection at 960 px plus refinement,
  with the measurement; `face_tuning.py` beside `dog_tuning.py` in the map
  (CONTEXTO 9) and the commands (CONTEXTO 10).
- ARQUITETURA 19 (data compatibility): the new files and keys above.

## 4. Worth explaining to the user

- **Greedy farthest-point selection** (backlog 24): start from one view,
  repeatedly add the view whose nearest chosen view is farthest. A classic
  2-approximation for covering a set, the same idea as k-center clustering;
  `np.minimum` keeps every view's distance to the chosen set in one vector,
  so each step is O(n).
- **Infinity as "not comparable"**: putting `np.inf` in the matrix instead of
  writing a special case for day and night is what guarantees both lightings.
- **Coarse to fine detection** (R31): find on a small image, measure on the
  big one. Common in vision: the cost of a detector grows with the pixels,
  while precision is only needed where something was found.
- **asyncio event-loop exception handler and FastAPI lifespan** (R32): for a
  Java/C# programmer, like a thread pool's uncaught-exception handler, and an
  `async with` that runs once at server start inside the server's own loop.
- **`asynccontextmanager`**: a generator turned into a `with` block, the
  Python form of a `try/finally` around startup and shutdown.

## 5. Measurements

- Backlog 24: analysis takes 0.03 s for 100 face views, 0.28 s for 140 dog
  views (worst case: 40 + a full queue of 100). Test data: 40 near-copies
  plus 60 varied views; the closest pair kept goes from 0.00 to 0.83.
- R35, probe over the five events (copies in the scratchpad), boxes of ratio
  1.5–2.0 touching the bottom edge: 23:34:13 one box (1.58, 244 px, a person
  crouching at the door, the dog behind), 23:53:02 one (1.51, 300 px, a person
  bending), 15:12:59 five (1.56–2.00, 86–220 px, a person sitting below the
  camera), 15:14:15 two (1.61–1.89, 55–75 px, the same person's head in the
  corner), 15:36:08 one (1.52, 299 px, a person by the car door). All people.
- R30 (b), production's copy, one named person (G., 38 views), 24 clips:
  frontal band (offset ≤ 0.35, spread ≥ 0.38) 102 faces, 94 % above the
  match threshold, median 0.489. Beyond it: offset 0.35–0.5 / spread
  0.2–0.3, 22 faces, 55 %, 0.379; offset 0.5–0.7 / spread 0.2–0.3, 22 faces,
  82 %, 0.440; offset 0.7–1.0, 24 faces, 85–100 %, ~0.43; offset > 1.0
  (profile), 26 faces, 50–67 %, ~0.42. **The 15 newest person clips with no
  named person held no face at all**, so nothing shows a stranger's side face
  would not match too, and with one named person "the right person still
  wins" cannot be tested. Not loosened.
- R31, 455 sampled frames of 8 clips of the named person, same frames both
  ways: full size 137 ms per frame, 65 frontal and 27 side faces, 92 %
  recognised, median 0.478; 960 px + refinement 45 ms, 61 and 26, 93 %,
  0.474; 1280 px + refinement 75 ms, 60 frontal, 97 %, 0.501. Not measured:
  live analysis per minute (R21's counter) while a scan runs in the test copy.

## 6. Look hardest at

- R31 loses 4 of 65 frontal face *frames* (6 %). Per event it is probably
  less (a face is seen in many frames), but this was not measured per event.
  Raising `DETECT_WIDTH` costs time without finding more on this sample.
- `reports.report_entry` checks "unnamed" outside the gallery lock, writes the
  report, then `take_out` checks again under the lock and the report is taken
  back if it fails. A scan that reinforces the entry in between loses that
  one new view with the entry. Rare; worth a look.
- Reporting deletes sighting files. A recording that had only that face now
  shows no "People:" line, which is the intent.
- `_event` builds the report URL from the event's own `HH-MM-SS`; the route
  rechecks every part and resolves inside `clips/`.

## 7. Not done

Nothing of the plan. Proposed next steps, for the architect to decide:

- R35: with backlog 23 in production, wait for the user's "Not a person"
  reports on the curled dog, then measure a rule that needs evidence of a dog
  (a `dog` box overlapping the wide box in the same frame or event) instead of
  shape alone.
- R30 (b): rerun `face_tuning.py` once a second person is named, or with
  negative examples; until then the limits should stay.
- R31: measure R21's live-analysis counter during a scan in the test copy.

## 8. Usage

| | 5-hour window | Weekly | Context |
|---|---|---|---|
| Start, 13:00 | 50 % | 78 % | 71k tokens, new conversation |
| After backlog 23 | 60 % | 79 % | |
| After backlog 24 | 64 % | 80 % | |
| After R35 | 65 % | 80 % | |
| After R32, R30 (b), R31 | 71 % | 81 % | 233k tokens |
| End, 13:55 | 71 % | 81 % | 238k tokens |

Per item, roughly: backlog 23 10 points, backlog 24 4, R35 1, R32 + R30 (b)
+ R31 6 (two long measurements ran in the background).
