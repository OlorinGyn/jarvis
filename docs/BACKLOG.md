# J.A.R.V.I.S. — the work

The decided work, the single list: the backlog, the review's open
recommendations, and the plan of the next sessions. Both machines see it
through git. The developer reads it; the architect manages it and, while a
developer session runs, does not edit it (`CLAUDE.md`, "Parallel sessions").
What is not work yet — what waits for the user, open discussions — is
`PENDING.md`; how the work is done is `PROCESS.md`. Split out of
`CONTEXT.md` on 12/10/2026; CONTEXT's sections 8, 13.4 and 14.4 point here.

---

## 1. Backlog

**The project's single list.** Both machines see it through git. Each item
says where it came from:

- **(decided)** — the user asked for it or approved it
- **(proposto)** — Claude's suggestion, no decision from the user yet

Proposed items **are not a plan**. Never start one without asking. The
architecture review's recommendations are separate (section 2) and the
**high**-priority ones come before items here. The full text of every
finished item is in `HISTORY.md` 8.

### Done

| | Item | Where |
|---|---|---|
| ✓ | Tiered storage (decided) — to an external drive after 30 days | ARCHITECTURE 11 |
| ✓ | Phone notifications through Telegram, with a face and a name (decided) | ARCHITECTURE 12 |
| ✓ | Core without a window (decided) | ARCHITECTURE 15 |
| ✓ | **3.** The web interface, the only way in (decided 09/10) | ARCHITECTURE 17 |
| ✓ | **5.** Play recordings on the page (decided 11/10, `v2026.10.11.3`) | ARCHITECTURE 17.13 |
| ✓ | **9.** Undo a merge — closed by the user: a warning before every merge instead | — |
| ✓ | **15.** Animal re-ID — superseded by 22 | HISTORY 8 |
| ✓ | **17.** Production and test environments (decided 09/10) | ARCHITECTURE 18.7 |
| ✓ | **18.** The running version on the page (decided 10/10) | ARCHITECTURE 12.10 |
| ✓ | **19.** People by person; attach a face to a name; the waiting queue; rename (decided 10/10, `v2026.10.10.4`) | ARCHITECTURE 17.10 |
| ✓ | **20.** Who appears in each recording (decided 10/10) | ARCHITECTURE 17.10 |
| ✓ | **21.** A favourite photo per person (decided 10/10, `v2026.10.10.6`) | ARCHITECTURE 17.10 |
| ✓ | **22.** A Dogs tab: each household teaches its own dogs (decided 10/10, `v2026.10.10.7`); thresholds wait for ~10 named views per dog per lighting | ARCHITECTURE 20 |
| ✓ | **23.** Report a bad detection instead of deleting it, with Undo (decided 11/10, `v2026.10.11.4`) | ARCHITECTURE 21 |
| ✓ | **24.** "Choose the best 40" views; Chosen and Waiting (decided 11/10, `v2026.10.11.4`) | ARCHITECTURE 17.14 |
| ✓ | **25.** Residents, notification cases and the Home/Away/Silent modes, the Notifications tab, commands from the phone (decided 12/10, `v2026.10.12`) | ARCHITECTURE 22 |
| ✓ | **26.** Select many unnamed photos, name or report them at once (decided 12/10, `v2026.10.12.2`) | ARCHITECTURE 17.16 |
| ✓ | **27.** Notifications as the first part of Settings (decided 12/10, `v2026.10.12.2`) | ARCHITECTURE 22.4 |
| ✓ | **29.** `/on` and `/off` from the bot; Off never stored (decided 13/10, `v2026.10.13`) | ARCHITECTURE 22.7 |
| ✓ | **30.** Home silences a probable resident: two cases of their own (decided 13/10, `v2026.10.13`) | ARCHITECTURE 22.2 |
| ✓ | **31.** Detection sensitivity per label in Settings (decided 13/10, `45aa0e5`, review 21); **not released** — on `master` with 28, which waits for R48 | ARCHITECTURE 7.14 |

**Waiting for the user's check on the M900:** items 25, 3, 29 and 30, in `PENDING.md`.

### Decided on 13/10/2026, to build

Asked by the user on the evening of 13/10, with the answers to the
architect's questions the same evening; the measurements behind them were
taken in production that evening.

28. **The 40 views manage themselves** (decided). A view from a sure match,
    or brought by naming or merging, enters Chosen while it holds fewer than
    40. Once full, it enters only if it makes the 40 more varied: it replaces
    the chosen view whose nearest twin is closest, when the new view is
    farther from its own nearest chosen view than that pair is — never the
    favourite — and otherwise it is discarded with its photo. Waiting stops
    growing. Faces compare by cosine (higher is closer), dogs by
    `dogs.distance` (lower is closer, `None` between day and infrared: only
    the same lighting is compared, and a view with no same-lighting twin
    counts as different). **Why this rule and not "drop near-copies":** a
    face's waiting views are not near-copies (median cosine to the nearest
    chosen view 0.48 for the user, 0.44 for Izabel) while the chosen 40 hold
    identical pairs (1.00); a dog's waiting views are closer to the chosen
    (median distance 0.25 Aurora, 0.22 Mirana) than the chosen are to each
    other (0.34, 0.26). **Once, on production:** the existing Waiting queues
    (30, 35, 28 and 31 views) pass through the same rule and what is left is
    **deleted — the user chose this on 13/10 knowing it**. A tool with
    `--dry-run` that copies `faces/` and `dogs/` to `backups/` first; the
    architect runs it after the deploy. No format change: `pending` stays
    readable, and empties. **Built** (`6345a7d`, `47a2e6a`) and reviewed
    (review 20), **not released**: the rule lets a wrong-person view in first
    — R48 waits for the user.
32. **The "maybe" threshold, chosen from measured accuracy** (decided; the
    user: with a metric they set the threshold, without one the maybe stays
    as it is). Settings shows, for faces and for dogs, a table measured on
    the user's own named photos by leave-one-out — each named view matched
    against all the others: per threshold, how many named views would be
    recognised for sure and what share to the right one, and how many
    unnamed photos would cross it. The user sets the sure threshold from it
    (faces `LEARN_THRESHOLD` 0.45; dogs the sure distance 0.35 and ratio
    0.6), stored in `config.json`. Measured 13/10: faces are 99.3 % right at
    any threshold from 0.363 to 0.45 (1 error in 146 views) — **wrong,
    review 20**: 7 of Gustavo's views are Izabel's faces, counted as right by
    their label; at 0.45 at least 8 of 146 are wrong, and the table means
    something only on clean labels, with each view's exact copies left out of
    its own test; and review 21 found that those wrong views are not faces
    at all, but the top of a head (R49). Even so, 12 unnamed
    face views fall between 0.363 and 0.45; dogs at today's thresholds are
    right in 31 of 33 probable matches, the 2 wrong ones at night. **What it
    cannot measure:** a stranger has no name, so the table shows confusion
    between the named, not with strangers — the unnamed column is the only
    hint, and the page says so. A lower sure threshold also means more views
    learned on their own (28).

### Critical

Without these the system does not do its job well.

1. **Zones of interest per camera** (proposto) — today there is only a fixed
   mask over the camera's clock, in the code. Every competitor has drawable
   zones, and it is the biggest control over false positives there is.
   Mosquitoes, wall objects and sunlight have already cost time; a zone saying
   "only the garage matters" would have avoided almost all of it. Worth
   separating a **mask** (ignore the area) from a **required zone** (detect
   everything, but notify only when something enters it).
2. **System health** (proposto) — if a camera dies at 3 a.m., nothing warns.
   There is an automatic restart, but no record of how long it was down. A
   daily summary, or a "camera down" case among backlog 25's switches, would
   close it.

### Important

It works without them, but is incomplete.

4. **Measure the M900 running** (proposto) — CPU with both cameras in motion,
   and whether `HWACCEL` helps (INSTALL 6).
6. **Search and filter** (proposto) — with ~100 events a day, by date only is
   not enough. By person, camera, label.
7. **Tracking** (proposto) — keep identity across frames; it solves the person
   standing still and makes one clip match one person.
8. **Animal labels** (proposto) — accept a species only when it repeats within
   the event, instead of accumulating every YOLO hesitation.
10. **Audio** (proposto) — the cameras send PCM and `-an` drops it. Barking,
    shouting, breaking glass.

### Improvement

11. **A timeline** (proposto) — a grid of cards does not answer "what happened
    between 2 and 4 a.m.".
12. **Persist the static spots** (proposto) — the list starts empty on every
    run, so the night's first false clip is still recorded.
13. **An event database** (proposto) — SQLite instead of JSON files, once
    there is search.
14. **OpenVINO on the M900** (proposto) — `cv2.dnn` accepts that backend; it
    was the plan to win back the speed lost when leaving PyTorch.

33. **Report a bad detection from the phone** (proposto, 13/10/2026) — a
    "Not a dog" / "Not a person" button under each Telegram message, as
    commercial systems put actions in their notifications; one tap files the
    same report as the page (ARCHITECTURE 21), where the user sees the
    mistake first.

### Outside software

16. **A motion-triggered light at the Front** (proposto) — not code, but the
    biggest possible gain for faces at night (ARCHITECTURE 10.5).

### What competitors have that this does not (13/10/2026)

The user asked. Compared with Frigate, Blue Iris, UniFi Protect, Ring and
Nest, from the architect's knowledge up to mid-2026:

| Gap | Here |
|---|---|
| Zones per camera: ignore an area, or alert only when something enters it | 1 |
| Tracking: the label comes from the object's history, not one frame | 7; R44 and R46 cover the bend |
| Per-object filters: minimum score, size, ratio, the median score over the track | 31 |
| A warning when a camera goes down | 2 |
| A timeline and a review of alerts | 11 |
| Search by person or object; natural-language search; event descriptions by AI | 6 |
| Audio detection: barking, breaking glass, shouting | 10 |
| Actions inside the notification | 33 |
| Continuous 24/7 recording | — (this records by event) |
| Hardware acceleration | 14 |

### Deliberately out of scope

Competitors have these and they make **no** sense here: multiple users with
permissions, cloud or subscription, support for dozens of camera brands, PTZ,
two-way audio, number-plate reading, Home Assistant integration. They are
product features; this system is for one house with two cameras. If someone
proposes one, the answer is already here.

---

## 2. Recommendations, open

The closed ones, with their commits and texts: `HISTORY.md` 13.4.

| # | Priority | Recommendation | State |
|---|---|---|---|
| R49 | **highest — the user's, 14/10** | The top or the back of a head passes as a face; five such views of Gustavo are references in his Chosen | open (below): developer 20 measures stronger models |
| R48 | **high — decided 14/10** | The 40-view rule lets a wrong-person view in first; production's Waiting holds the top of Izabel's head as Gustavo's (R49) | decided: backlog 28 waits for R49; 31 waits with it |
| R47 | low — a watch | R46's chain has no end: a real dog that takes a vanished person's place would stay a person | open (below) |
| R42 | medium — **the user's decision** | In Home, a resident's face plus a second person who never shows a face sends nothing | open |
| R30 | **high** | A face seen from the side is dropped, so many person events end without a face photo | (a) done `9fb8862`; (b) needs a second named person — **met on 13/10: Izabel** (HISTORY 13.12) |
| R12 | medium | Production and test copy on the same M900 double the CPU load | open (HISTORY 13.5) |
| R14 | low | Live MJPEG is encoded once per viewer | open (HISTORY 13.5) |
| R9 | verification | `python-preference = "system"` on the development PC | open (HISTORY 13.4) |

**R49 — The top or the back of a head passes as a face (high, review 21,
14/10/2026).** R48's seven "faces of Izabel" are not faces: the contact sheet
shows the top or the back of her head, bent down or turned away, and five
views in Gustavo's Chosen are the same of him — 15, 16, 18, 19 and 31 on
the page, files `55edf5`, `e5bf9c`, `80936d`, `1f8419` and `dbc1b0`. YuNet
scored them 0.61–0.89 and placed landmarks that `is_frontal` (ARCHITECTURE
10) accepts: it checks that a face is not turned sideways, not that there is
a face. The top of one head looks like the top of another, so each of the
seven matched one of those five, at 0.475–0.509. **The recogniser itself
tells the two people apart:** between Gustavo's and Izabel's 40 chosen views
the median similarity is 0.05 and the highest 0.42, under `LEARN_THRESHOLD`;
each person's views sit at about 0.5 from their own mean and 0.1 from the
other's. Leave-one-out on the 146 kept faces, those five left out of the
references: 101 sure and right, **0 wrong**, 45 unrecognised — against 111,
7 and 28 today. **No measure tried tells a head-top from a face:** YuNet's
score, the eye-to-mouth height over the eye spread and the embedding's
length all overlap between the two. What is left to try: a face-quality
measure, a recogniser made for poor faces, or the user removing them by
hand. A different recogniser means new embeddings for every gallery — not
additive, the user's decision. **The user's decision, 14/10/2026:** R49
comes before everything else, and if much better models exist they will be
used, with a migration of every gallery (CONTEXT 3). Step 1 is developer
20's measurement (section 3); step 2, the switch and the migration, is
planned with its numbers. The user may delete the twelve views now: the
measurement uses a copy taken before (`backups/r49_faces_20261014/`).

**R48 — The 40-view rule lets a wrong-person view in first (high, the
user's decision, review 20).** Backlog 28 keeps what is most different, and a
face of the wrong person is the most different of all. Production's queues
show it is not rare: 7 of the 31 views in Gustavo's Waiting are Izabel's,
learned by "sure" matches (0.475–0.509 against `LEARN_THRESHOLD` 0.45)
through dark, head-down views of him. Settled as is, 6 enter his Chosen; with
the 7 deleted first, the settled galleries recognise 132 of the 146 kept faces
rightly against 120 today, with 9 wrong against 7 (HISTORY 13.21). No measure
on the embeddings tells the seven apart, so a guard in code cannot be written
from today's data. Options: **(a)** the user deletes the 7 from Gustavo's
Waiting (`PENDING.md`), then the architect releases 28 and runs the tool;
from then on a wrong sure match enters Chosen instead of waiting, and the
user sees it on the person's page; **(b)** as (a), and 28 changes so that past
40 only the user's naming and merging use the rule — a view a scan learns on
its own is deleted — until backlog 32 sets a sure threshold the user trusts;
**(c)** hold 28 until 32 is done. The architect recommends **(b)**: Waiting
stops growing as the user asked, no wrong match can enter a full Chosen, and
the user's own naming, which is right by definition, still renews the 40.
**Review 21:** the wrong views are head-tops (R49), and nothing stops a new
one being learned "sure" through another head-top of the person, so (b)
still holds until R49 is fixed. **Decided by the user, 14/10/2026:** "no
reason to change the screen's behaviour without doing R49" — backlog 28 is
not released before R49; the rule is read again then, with the new model's
numbers.

**R42 — In Home, a resident's face hides a second person with no face
(medium, the user's decision).** The faceless message goes only when the scan
found no face at all. If the user walks out with someone whose face is never
seen, the scan finds the user's face (silenced in Home) and nothing is sent —
against the user's own rule that a stranger in the dark must reach the phone.
The scan cannot tell one person from two by faces; YOLO can, by counting
person boxes in the same frame. Options: (a) accept the corner; (b) when the
person was held, every face found was silenced, and YOLO saw more people at
once than distinct faces were found, send the best view as
`faceless_person`. (b) costs a counter in `EventRecorder` and, when YOLO
counts a dog as a second person (R18), one extra message. The architect
recommends (b).

**R47 — R46's chain has no end (low, a watch, 13/10/2026).** Every
relabelled box renews both memories (ARCHITECTURE 7.13), so a real dog that
takes the place of a person who vanished — someone stepping out of view right
over a dog — stays a person while YOLO keeps seeing it within 0.3 of its last
box: the event says person, no dog crop is kept, and in Home a faceless-person
message goes out. None of the true-dog boxes in twelve clips did, and a cap
would cut the long bends R46 exists for. **Trigger:** a "not a person" report
whose `replay.py` trace shows "took the place of a person who vanished".
**Then:** bound the chain — for instance, a relabelled box renews the memory
only within some seconds of the last real person box, measured on R46's
bends (HISTORY 13.20). Since backlog 31, a person minimum set below 0.35
feeds the memories more boxes and lengthens the chain (ARCHITECTURE 7.14).

---

## 3. Next sessions

**Review 21 is done, without a release:** backlog 31 is reviewed and sits on
`master` with 28, and 28 waits for R49 (the user, 14/10). Production stays
on `v2026.10.13`; the next release carries R49, 28 and 31.

**Developer 20 (planned 14/10): R49, step 1 — measure; change nothing in
production.** The user's decision: R49 comes before everything, and much
better models will be used if they exist, even with new embeddings for every
gallery (CONTEXT 3). Read HISTORY 13.21 and 13.22 first.

- **The data.** `backups/r49_faces_20261014/`, a copy of production's
  `faces/` taken by the architect on 14/10 before the user deletes anything:
  `gallery.json` with Gustavo (40 Chosen, 31 Waiting) and Izabel (40, 35),
  and the photos in `views/`. A view's label is its person, except **the
  twelve head-tops, labelled "not a face"**: in Gustavo's Waiting the files
  starting `c58c97`, `e18912`, `b3f8b9`, `69f368`, `1bbfa1`, `860372` and
  `eedcf9` (the top of Izabel's head), in his Chosen `55edf5`, `e5bf9c`,
  `80936d`, `1f8419` and `dbc1b0` (the top of his). Each view is a context
  crop of 300 px with the face about 136 px wide — what a migration would
  embed again.
- **A benchmark tool,** `tools/face_bench.py`, kept in the repository. For
  each candidate pipeline, detect and embed every view, then report:
  (1) how many of the twelve head-tops it accepts as a face; (2) leave-one-out
  over the named views — each against the Chosen of both, its own exact
  copies left out — as sure right, sure wrong and none at the pipeline's own
  threshold, plus the closest cross-person pair against each person's own
  spread; (3) the cost per face on the M900 and the model's size. The
  baseline, YuNet + SFace with today's `is_frontal`, must reproduce review
  21's 111 / 7 / 28.
- **Candidates, the well-regarded first** (PROCESS 5): (1) InsightFace's
  `buffalo_l` — the SCRFD-10G detector, the ArcFace R50 recogniser, and its
  3D landmark model, whose head pitch sees the "head down" that `is_frontal`
  cannot. Its pretrained models are licensed for non-commercial research:
  a home system is non-commercial, but say it plainly in the HANDOFF.
  (2) AdaFace (CVPR 2022), made for poor faces; the length of its embedding
  before normalisation is a quality cue — a head-top should come out short.
  A trustworthy ONNX export or a one-off export; check its licence. (3) A
  face-quality model (CR-FIQA, MagFace) only if (1) and (2) still accept
  head-tops. Models only from their authors' releases. Run them with
  `cv2.dnn` when it loads them; otherwise `onnxruntime`, a new compiled
  dependency — check that it runs under Smart App Control (PROCESS 2.1)
  before building on it.
- **Not this session:** any change to `faces.py`, the galleries or the page.
  The switch and its migration — every gallery embedded again from its
  views, every older file still readable — are step 2, planned in the review
  with the user's choice.
- **HANDOFF:** the table per candidate, each licence, and the
  recommendation.

**Waits for the user:** R42; backlog 32 waits for R49 (its table means
something only on clean labels and on the final model).

**Not planned:** R30 (b) joins a later session — with a new detector it is
measured again anyway; R47 is a watch. R14, R12 and R9 as before. Every other
open backlog item is **(proposto)**.
