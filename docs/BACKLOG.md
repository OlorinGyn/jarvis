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
| ✓ | **31.** Detection sensitivity per label in Settings (decided 13/10, `45aa0e5`, review 21, `v2026.10.14`) | ARCHITECTURE 7.14 |
| ✓ | **28.** The 40 views manage themselves (decided 13/10, `6345a7d`, `47a2e6a`, review 20; released with R49 in `v2026.10.14`, review 23). The once-only `settle_waiting.py` waits until the user deletes the seven head-tops of Izabel in Gustavo's Waiting (`PENDING.md`) | ARCHITECTURE 17.14 |

**Waiting for the user's check on the M900:** items 25, 3, 29 and 30, in `PENDING.md`.

### Decided on 13/10/2026, to build

Asked by the user on the evening of 13/10, with the answers to the
architect's questions the same evening; the measurements behind them were
taken in production that evening.

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
    at all, but the top of a head (R49). **Since `v2026.10.14` the model is
    ArcFace** (thresholds 0.30 / 0.40): the table is computed on it, and
    means something once the labels are clean — the twelve head-tops deleted
    and the seven unnamed entries of Izabel named (`PENDING.md`). Even so, 12 unnamed
    face views fall between 0.363 and 0.45; dogs at today's thresholds are
    right in 31 of 33 probable matches, the 2 wrong ones at night. **What it
    cannot measure:** a stranger has no name, so the table shows confusion
    between the named, not with strangers — the unnamed column is the only
    hint, and the page says so. A lower sure threshold also means more views
    learned on their own (28).

### Decided on 14/10/2026, to build

34. **Analysis On and Off from the page** (decided; the user, 14/10/2026,
    during review 23: "on the screen where the status shows, it must be
    possible to switch it on and off there too"). The header that shows On
    or Off on every screen (ARCHITECTURE 22.7) becomes a switch, calling
    `analysis.set_on` as `/on` and `/off` do — same flag, same log line, same
    reminder while Off, and still never stored. A write from the network, so
    it goes through the write guard like every other change (ARCHITECTURE
    17.12). **Turning Off asks first** ("are you sure?"), since it stops all
    recording; **turning On is one click** (the user, 14/10/2026).
35. **Detection sensitivity as a slider, not numbers** (decided; the user,
    14/10/2026: "the sensitivity cannot be numeric — a kind of slider where
    the middle is our default value, and the number goes down to the left
    and up to the right, proportionally"). Each of backlog 31's three
    minimums (ARCHITECTURE 7.14) becomes a slider with no number on it: the
    middle is the default, the left end the lowest allowed minimum (0.20),
    the right end the highest (0.90), each half linear, so the middle is
    always the default whatever its value. The ends say in words what they
    do — left: more detections, more false alarms; right: fewer, stricter.
    `config.json` keeps storing the number, so nothing on disk changes.
    **The explanation stays, moved to where it belongs** (the user, the same
    day: "the explanation on the numbers screen was perfect; I want to know
    how the sliders work in the background"). Both of today's hints keep
    their substance — what the minimum is (how sure YOLO must be before
    motion counts as a person or an animal), lower finds more and more false
    ones, a change reaches the cameras within seconds without a restart, and
    what this does not fix (a person bending over) — and gain a "how it works"
    part that says what the slider moves underneath: the minimum
    confidence, the middle being the default, the ends 0.20 and 0.90, each
    half in proportion, with each slider's current value and default written
    in that text, not on the control.
36. **Notifications: the Telegram card beside "What reaches the phone"**
    (decided; the user, 14/10/2026). Two columns where the screen is wide
    enough, one under the other on a phone — the user opens the page from
    the phone's browser too (PROCESS 1, UX).

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

The closed ones, with their commits and texts: `HISTORY.md` 13.4. **R50 is
not used**, so that it is never read as the name of ArcFace R50, the face
model; R48 and R49 closed in review 23.

| # | Priority | Recommendation | State |
|---|---|---|---|
| R53 | **high — the user's report, 14/10** | The two dogs are told apart by colour histograms, which overlap: Mirana among Aurora's views, a person among Mirana's | open (below) |
| R51 | medium | A clip's face is matched by its heaviest view, not its best: a clip with sure views can be recorded "probably" | open (below) |
| R52 | low | The gallery migration runs before the log file and before the port is held | open (below) |
| R47 | low — a watch | R46's chain has no end: a real dog that takes a vanished person's place would stay a person | open (below) |
| R42 | medium — **the user's decision** | In Home, a resident's face plus a second person who never shows a face sends nothing | open |
| R30 | **high** | A face seen from the side is dropped, so many person events end without a face photo | (a) done `9fb8862`; (b) needs a second named person — **met on 13/10: Izabel** (HISTORY 13.12) |
| R12 | medium | Production and test copy on the same M900 double the CPU load | open (HISTORY 13.5) |
| R14 | low | Live MJPEG is encoded once per viewer | open (HISTORY 13.5) |
| R9 | verification | `python-preference = "system"` on the development PC | open (HISTORY 13.4) |

**R53 — The dogs' identity rests on colour histograms, which overlap (high,
the user's report, review 23).** The user sees Mirana among Aurora's views and
a person among Mirana's. A contact sheet of production's galleries on 14/10
shows it: Mirana in Aurora's Chosen (5) and Waiting (5), a man in Aurora's
Waiting (24), shoes and a hand, someone in red, dark clothing and Aurora in
Mirana's Waiting (25, 26, 22, 29) — the user deletes them (`PENDING.md`). By
leave-one-out with `dogs.distance`, 6 of Aurora's 40 chosen views and 5 of
Mirana's sit closer to the other dog than to their own; at night both are
grey, and a crop holding both dogs, or a person's dark shoes, describes as
whichever colour its fur mask caught. **Step 1, as R49's:** once the labels
are clean, a bench on a copy of `dogs/` — today's descriptor against learned
image embeddings that run through `cv2.dnn`, exported to ONNX once if needed
as AdaFace was (ARCHITECTURE 10.14): for instance DINOv2-small, a CLIP image
encoder, a MobileNet's last pooled layer. Per candidate: leave-one-out by
lighting, right and wrong over a threshold sweep, how far a person crop or a
crop of both dogs lands from each dog, cost on the M900, size and licence.
Nothing in the program changes in step 1.

**R51 — A clip's face is matched by its heaviest view, not its best
(medium, review 23).** `_group` keeps, for each face in a clip, the view with
the largest width × YuNet score, and `_scan_clip` matches only that view: its
score is the sighting's, decides "recognized" or "probably", and decides
whether anything is learned. Under ArcFace that view is often not the best
match. Gustavo's daytime clip `Back/2026-10-12/15-44-28`, scanned densely: 39
views on him, the heaviest at 0.349 — "probably Gustavo" — while his best
view scores 0.421 and 4 views pass 0.40. In Home it changes nothing (a
probable resident is silent too, ARCHITECTURE 22.2); in Away it is the
wording; and fewer views are learned, so Chosen renews more slowly (backlog
28). **What to measure before changing it:** the score of the best view, of
the second best and of the median of the three best, against the heaviest's,
on the four clips of developer 21 and on clips of both residents by day and
by night (`faces/<day>/*.json` names the clips), with each one's rate of
wrong best matches. A best-of-N score rises for a stranger too — the more
views, the likelier one crosses 0.30 — and no stranger has been measured, so
the choice that adds right answers with the least lift for one-off views
wins; the HANDOFF carries the table.

**R52 — The gallery migration runs before the log file and before the port is
held (low, review 23).** `cameras.main()` calls `migrate_gallery()` before
`web.start()` and before `log.to_file()`. Two consequences. (1) Production
runs under `pythonw.exe`, with no console, so the migration's line — views
kept, "no face", entries dropped, the backup folder — is written nowhere:
the one record of a non-additive change to the user's data is lost. (2) The
port is what keeps a second copy out (ARCHITECTURE 18.8), and for the ~25 s
of the migration it is not held: the 5-minute task trigger, or a click on
`jarvis.bat`, passes the already-running check and migrates too. The second
copy's write replaces the first's file with an equivalent one and then exits
at `web.start()`, so at worst what the first copy learned or the user did in
those seconds is lost; a collision of the two `.part` writes needs both to
finish within milliseconds of each other. **Fix:** log the result after
`log.to_file()`, and serialise the migration across processes —
`filelock`'s `FileLock` beside the gallery (pure Python, well regarded,
released by the operating system if the process dies; PROCESS 5.2), so the
second copy waits, finds the hash unchanged and does nothing. A test with two
threads standing in for two processes is enough for the lock; the log line is
read in `logs/jarvis.log` on the test copy.

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

**Review 23 is done, with a release:** developer 21's R49 step 2 — SCRFD and
ArcFace R50, the gallery migration, the models fetched before the stop — with
backlog 28 and 31, as `v2026.10.14` (HISTORY 13.24). R48 and R49 are closed.

**The user's instruction, 14/10:** use the whole 5-hour window that opens at
15:00 (Brasília), cycle after cycle; the weekly limit renews at 16:00. Each
review plans and starts the next developer session at once; the plans below
are already written so no cycle waits.

**Developer 22 (15:00): backlog 34 and 35, R52, R51, then R30 (b).**

0. **Backlog 34, 35 and 36 first** (section 1): the user asked for both during
   review 23, and both are small page changes. This puts them ahead of R30
   (b), which is high, on purpose: R30 (b) was parked until the model
   changed, and the user's requests are live. Tests as
   `tests/test_on_off.py` does for the bot, plus the write guard; for 35,
   the slider's mapping both ways (default in the middle, the ends at 0.20
   and 0.90) in `tests/`.
1. **R52** (section 2): the migration's line into `logs/jarvis.log`,
   and `filelock` around `migrate_gallery`. A new dependency: check that
   `filelock` is pure Python (no `.pyd`), as PROCESS 5.3 asks of anything
   new on the M900.
2. **R51** (section 2): the table first, the change only if it wins. Use
   `tools/face_tuning.py` or a script in the scratchpad; production's clips
   are readable from `C:\JARVIS\clips` without copying them all.
3. **R30 (b)** (HISTORY 13.12): with ArcFace, measure whether the frontal
   gate can be loosened. `is_frontal` rejects faces turned more than
   `MAX_NOSE_OFFSET` 0.35 or with an eye spread under `MIN_EYE_SPREAD` 0.38;
   on both residents' clips, score the three-quarter faces it rejects against
   the person's own Chosen, and loosen only as far as the right person still
   wins, with nothing wrong. `face_tuning.py` already prints both measures per
   face. Report the gain in faces per clip, and the cost (each face now costs
   ~0.13 s more, ARCHITECTURE 10.14).

**HANDOFF:** backlog 34, 35 and 36 as built, each checked at 375 px wide too (and whether Off asks first);
R51's table and the choice; R30 (b)'s per-limit table; the log
line as written by the test copy. If the session runs short, stop after a
coherent commit and say what is left.

**Developer 23 (after review 24): R53 step 1, then backlog 32 for faces.**
R53's bench (section 2) on a copy of production's `dogs/` taken after the
user's deletions — if they are not done, label the views listed in
`PENDING.md` as "not this dog" in the bench instead. Then backlog 32's table
for faces only: the face labels are clean since 14/10 (the head-tops
deleted, the unnamed entries named), and the dogs' half waits for R53's
model.

**Waits for the user:** R42; backlog 32 can be built now but means something
once the labels are clean (`PENDING.md`); the once-only settle of backlog 28.

**Not planned:** R47 is a watch. R14, R12 and R9 as before. Every other open
backlog item is **(proposto)**.
