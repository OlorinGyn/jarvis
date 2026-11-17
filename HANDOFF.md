# HANDOFF — developer 32 (17/11/2026)

Plan: BACKLOG 3, "Developer 32: backlog 45 measured, then backlog 42". Both
done, in the plan's order. 440 tests pass, no comments in `src/` and
`tools/`, `check_data` reads every file, `check_doc_refs` exits 0.

## 1. What was done

### Backlog 45, step 1 — the quality cut measured, no rule built (`627c5bc`, `4ceecec`)

`tools/view_quality.py <folder> [--sheets DIR] [--verdicts FILE]`, run on a
copy of production's `faces/`, `dogs/` and the event JSONs of `clips/`
(`C:\JARVIS` only read; the copy, its `config.json` stripped to nothing, is
in this session's scratchpad, `...\scratchpad\prod`).

Per stored view, chosen and waiting:

- **faces** — YuNet run again on the stored 300 px photo (score, nose offset,
  eye spread / width), SCRFD's score, the face's width in its frame (the
  sighting's own when the photo is the sighting's — 140 of 266 chosen — and
  otherwise an estimate from the photo's resolution, `effective_side`:
  correlation 0.86 with the known widths), the frames of its sighting,
  sharpness (variance of the Laplacian over the face), day or night;
- **dogs** — the box in its frame (from the same-picture sighting),
  sharpness, day or night, YOLO on the crop padded twice its size (dogs
  found, best dog score, people found).

**Wrong, two ways.** (1) Flagged by leave-one-event-out: the nearest view
outside its own event is another known identity (named, or an unnamed entry
labelled in HISTORY 13.33; two visitors alike are not counted, they may be
one person split) at `MATCH_THRESHOLD`; for dogs, `dogs.match`'s rule over
the named dogs' other views names another dog. (2) **Read by eye, every
view**: leave-one-event-out found 13 flags, of which 9 were truly wrong
and 3 were good views of the user flagged only because their nearest
neighbour was one of his views misfiled in Izabel's entry. The rest of
the wrong views no matching can see. So I read all 324 face views and 139
dog views on contact sheets and wrote the verdicts to
`tools/view_quality_verdicts.json` — `poor` (head down / head-top, motion
blur, a damaged frame, a side view, two faces in the crop, very dark night
blur) or `other` (someone else's photo in the entry), plus `ok` for the 3
look-alike flags. **The verdicts are mine and strict; they are what the
review must check first** (sheets below).

**Faces: 324 views — 102 poor, 18 someone else's.** Per signal, views kept /
poor / someone else's:

| Signal | cuts → kept/poor/other |
|---|---|
| width (sighting's or estimated) | 40: 293/99/15 · 50: 197/60/6 · 60: 103/36/3 · 80: 17/5/1 · 100: 1/0/0 |
| frames | 2: 259/66/9 · 3: 188/35/3 · 5: 107/18/1 · 8: 71/11/0 |
| YuNet score | 0.85: 182/39/3 · 0.9: 66/6/0 · **0.92: 18/0/0** |
| SCRFD score | 0.6: 220/44/4 · 0.7: 143/22/2 · 0.8: 43/4/0 · **0.85: 5/0/0** |
| sharpness | 30: 149/26/10 · 50: 92/12/6 · 75: 56/6/1 · 100: 36/3/0 · 150: 12/1/0 |
| nose offset ≤ | 0.35: 228/67/8 · 0.2: 146/40/7 · 0.1: 78/16/7 (never clean) |
| eye spread ≥ | 0.35: 142/24/2 · 0.4: 81/9/1 · 0.45: 25/3/0 |

- **No single signal reaches 0 poor short of almost emptying the gallery**:
  YuNet ≥ 0.92 keeps 18 views (Gustavo 1, Izabel 1); SCRFD ≥ 0.85 keeps 5.
- **The best pair, SCRFD ≥ 0.70 and sharpness ≥ 75: 41 kept, 0 poor, 0
  someone else's.** Per named entry, day/night kept of today: Gustavo 3/49
  and 2/14, Izabel 4/72 and 0/3, Dhaniel 3/9 and 0/2, Heley 3/4, Luan 4/6,
  Manu 4/4, Natália 3/4; Ana Claudia, Fernanda, Bruno, Miguel 0.
  Other pairs with 0 poor: SCRFD ≥ 0.75 & sharpness ≥ 50 (40, 2 someone
  else's), SCRFD ≥ 0.6 & sharpness ≥ 100 (32), YuNet ≥ 0.9 & offset ≤ 0.15
  (31). Each pair is fitted to 102 labels: treat as optimistic.
- **Recognition, leave-one-event-out over the named and labelled views**
  (probes: every view with a known identity, the "someone else's" left out;
  sure = 0.40):

  | References | right, sure | right, probable | wrong (sure / probable) | no name |
  |---|---|---|---|---|
  | today's chosen views | 71 | 85 | 3 / 2 | 67 |
  | the pair's 41 views | 15 | 54 | 0 / 0 | 159 |
  | YuNet ≥ 0.92 (18) | 4 | 17 | 0 / 0 | 207 |
  | **only the 204 views read good by eye** | **58** | 91 | 0 / 1 | 78 |

**The reading:** the signals the photos carry do not measure what the eye
sees. A head down, a man in Izabel's entry, motion blur: each passes
detector and landmark scores that a clean frontal face also gets. A cut
measured to never fail on these signals keeps 41 of 324 and loses four in
five sure recognitions; the eye's own selection keeps most of them with no
wrong sure name. If the user's rule stands as "measured, never fails",
the pair above is the answer, at that price.

**Someone else's views (18):** 14 of the user's views in Izabel's entry
(HISTORY 13.33 counted four), a woman and another man in the user's, and
a printed face (a T-shirt) that formed an unnamed entry. These are a
filing problem, not a quality one — backlog 43's cleaning.

**Dogs: 139 views (79 named) — 5 poor, 3 someone else's.** Leave-one-event-
out names **no** dog view wrong at any cut. By eye: Aurora `fe6364` holds
two dogs; `96356a`, `1d75f1`, `b6b433` are night motion blurs; one unnamed
crop is only a tail; three unnamed crops are **people** (`c9e606`,
`902e6b`, `6402c4`). Per cut, kept/poor/other:

| Signal | cuts |
|---|---|
| box side | 100: 102/3/3 · **120: 81/0/2** · 150: 43/0/2 |
| sharpness | 20: 92/1/3 · **50: 52/0/2** · 100: 17/0/1 |
| YOLO dog score on the crop | **0.25: 63/0/2** · 0.8: 22/0/0 |

The lowest with no poor photo is box ≥ 120 px: Aurora keeps 10/25 by day
and 7/14 at night, Mirana 11/22 and 14/18; recognition (sure distance
default) right-sure 14 → 12, right-probable 34 → 28, no name 31 → 39, no
wrong either way. It is fitted on five poor views. Sharpness does not
separate at night (infrared views are soft: good dogs at 3–4, the blurs at
7–15), nor does sharpness divided by the contrast, nor the distance to the
dog's own other views. YOLO on a dog crop is unreliable both ways: it calls
good dogs "person" and one person crop "dog" at 0.79. The person crops are
YOLO's false dogs, not a photo's quality; the user would not name them.

**Contact sheets** (this session's scratchpad,
`C:\Users\gusta\AppData\Local\Temp\claude\cfd12769ca7e6402\4f81a05e-6961-46f5-ad0e-837530965492\scratchpad\sheets\`):
`faces_poor.jpg`, `faces_other.jpg`, `dogs_poor.jpg`, `dogs_other.jpg` (my
verdicts); `faces_kept.jpg` / `faces_dropped.jpg` and `dogs_kept.jpg` /
`dogs_dropped.jpg` (the best pair's split); `faces_flagged.jpg` (each
flagged view beside its nearest); `all_gustavo.jpg`, `all_izabel1.jpg`,
`all_izabel2.jpg`, `all_others1.jpg`, `all_others2.jpg` (every face view,
by entry, 150 px, what I read). The scratchpad is cleared by a reboot; the
tool writes them again in about a minute:
`uv run python tools/view_quality.py <copy> --sheets <dir>`.

### Backlog 42 (`c3b0dd2`)

Tests first, `tests/test_forget_unseen.py` (7 of 8 failed before).

- **(a)** `Gallery.forget_unseen(days=FORGET_DAYS, today=None)`: an unnamed
  entry whose `first_seen` is older than 60 days and that no sighting of
  the last 60 days' day folders points to leaves the gallery under the
  lock; its views, chosen and waiting, go to `dropped`, so `save()` deletes
  the photos after the write. Its sightings stay; `label()` already reads
  "?" for an id that is gone. A named entry is never touched.
  `Gallery.seen_since(since)` reads only the day folders from `since` on.
  `faces.keep_gallery(stop)` runs it at start and then every 24 h
  (`KEEP_SECONDS`) in a daemon thread, "gallery-keeper", started in
  `cameras.main()` beside "camera-watch": reading 60 days of sightings in
  the camera loop (as the `Housekeeper` does) would stall frames. A failure
  is logged as a warning and the loop goes on. A forgotten "Visitor N"
  keeps its number taken: `_next_visitor` already reads the header's
  counter, which `save()` keeps — the test forgets the highest visitor and
  the next is N+1.
- **(b)** `dogs.record`: a crop whose match is `probable` writes its
  sighting with `dog_id` `""`, `certainty` `"probable"` and `match` the
  name, keeps its photo in the day folder, and adds nothing to the
  gallery. `current_words` already words it "probably <name>" (and so does
  every older version). `record` returns only the ids stored; the log line
  counts the probable ones.

On production's copy: 35 unnamed face entries — none would go today
(production's faces start on 10/10); 12 would go in December and 23 in
January if not seen again. Dogs: 58 of the 157 sightings of 16–17/11 were
probable — those would no longer have become cards; the 36 with no name
still do.

## 2. Data format

- **Dog sightings**: `dog_id` may now be `""` with `certainty`
  `"probable"`. Additive in meaning: the field and its type are unchanged,
  every reader handles an id the gallery does not hold (`gallery.get` →
  None; `appearances` filters by equality). `check_data`: every file
  readable.
- **Face gallery**: entries leave it; no new field. A sighting may point to
  an id the gallery no longer holds — already the case after `take_out`.
- `tools/view_quality_verdicts.json`: a new versioned file, read only by the
  tool.

## 3. Documentation, suggested

- **ARCHITECTURE 10.17** (or a new 10.18, "The quality of a reference
  photo"): the measurement, the two tables, the reading; the verdict file
  and how to read it again.
- **ARCHITECTURE 10.x / 17.14**: `forget_unseen`, `seen_since`,
  `keep_gallery`, the "gallery-keeper" thread; `FORGET_DAYS`,
  `KEEP_SECONDS`.
- **ARCHITECTURE 20**: a probable crop stays a sighting with no card;
  `MAX_UNNAMED` now trims only crops nothing explains.
- **CONTEXT 9**: `tools/view_quality.py` and its verdicts in the map;
  **CONTEXT 10**: its command; the constants list gains `FORGET_DAYS`,
  `KEEP_SECONDS` (`faces.py`).
- **BACKLOG 1**: item 42 done; item 45 step 1 done, the cut waiting for its
  reading. Backlog 37's self-cleaning part closes with 42.

## 4. Worth explaining to the user

- **The variance of the Laplacian** as a sharpness measure, and why it
  fails at night: it measures edges, and an infrared picture has little
  contrast, so a sharp night dog scores lower than a blurred day one.
- **Estimating a photo's real resolution** (`effective_side`): shrink and
  enlarge again; the smallest side that rebuilds the photo almost as well
  as its own size is the side it was enlarged from. Like checking a JPEG
  for upscaling.
- **Overfitting a threshold to labels**: a pair of cuts chosen to dodge 102
  known bad photos looks perfect on them; the next month's photos are the
  real test. In Java terms, testing on the training set again — what R55
  fixed for the face table.
- `threading.Event.wait(timeout)` as a sleep that a stop interrupts — the
  daily loop ends at once when the service stops (PYTHON has the CameraWatch
  precedent).

## 5. Measurements

Above. Timing: `view_quality.py` on the copy, about 75 s (YuNet and SCRFD
on 324 photos, YOLO on 139 crops). `forget_unseen` reads 60 days of
sightings once a day — on production about 5,000 small JSONs, about a
second.

## 6. What the review should look at hardest

1. **My verdicts** (`faces_poor.jpg`, `faces_other.jpg`, `dogs_*.jpg`). 102
   poor of 324 is strict: I marked every head-down, side view, motion blur
   and two-faces crop. A softer reading changes every table; the tool
   reads the file again.
2. **Whether the user's rule can be met.** The cut that never fails on
   these signals costs most of recognition; the eye's own selection does
   not. That is a decision for the user, not a threshold.
3. `forget_unseen` racing a scan: a scan that matched an entry just before
   it is forgotten writes a sighting pointing nowhere ("?"). Harmless, I
   believe; the lock is held only for the removal.
4. `dog_id` `""` in sightings: any reader that treats an empty id as an
   error. I found none in `src/` or `tools/`.

## 7. Not done

Nothing of the plan. No rule from the measurement is built, as planned.

## 8. Usage

- Start: 5-hour window 1 %, weekly 12 %, context 78k.
- End: 5-hour window 21 %, weekly 14 %, context about 310k.
