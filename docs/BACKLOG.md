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
| ✓ | **28.** The 40 views manage themselves (decided 13/10, `6345a7d`, `47a2e6a`, review 20; released with R49 in `v2026.10.14`, review 23). The once-only `settle_waiting.py` waits for the misfiled dog views to be deleted; the faces' side is ready since 14/10 (`PENDING.md`) | ARCHITECTURE 17.14 |
| ✓ | **34.** Analysis On and Off from the page header; Off asks first, On is one click (decided 14/10, `8828e5c`, review 24, `v2026.10.14.2`) | ARCHITECTURE 22.7 |
| ✓ | **35.** Detection sensitivity as sliders, the default in the middle, the explanation beside them (decided 14/10, `87a84fd`, review 24, `v2026.10.14.2`) | ARCHITECTURE 7.14 |
| ✓ | **36.** Notifications: the Telegram card beside "What reaches the phone" (decided 14/10, `6295d57`, review 24, `v2026.10.14.2`) | ARCHITECTURE 22.4 |

**Waiting for the user's check on the M900:** items 25, 3, 29, 30, 34, 35 and 36, in `PENDING.md`.

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

Items 34, 35 and 36 are done (above, review 24); their full text is in
`HISTORY.md` 8.

37. **People and Dogs hold many photos gracefully** (decided, UX; the user,
    14/10/2026: some households will never open the page, so the screens
    must cope with a great many photos, "and perhaps clean themselves now
    and then"). **Designed in review 24** from production's counts on 14/10
    (HISTORY 13.25). What grows, and what is already bounded: a person's
    Chosen (40) and Waiting (`MAX_PENDING` 100) are bounded by backlog 28;
    unnamed dogs by R27 (`MAX_UNNAMED` 60, 44 today, 1 view each, ~7 a day);
    **unnamed faces have no bound at all**; the sighting photos in
    `faces/<day>/` and `dogs/<day>/` grow about 2.7 MB a day together, next
    to ~300 MB of clips. What a phone shows today: the Dogs tab at 375 px is
    one column of 335 px cards, 46 of them make a page about 9,100 px tall.
    **The layout (decided, UX — the architect's, PROCESS 1):**
    (a) every `.people-grid` takes two columns under 480 px, named cards
    included, as the "Looks like" groups already do (`style.css`);
    (b) any list of photos that can pass 24 shows the newest 24 and a
    "Show 24 more (N left)" button under it — the unnamed groups on People
    and Dogs, a person's or dog's Waiting, "Days they were seen" — while
    Chosen (at most 40) shows whole; the heading keeps the full count, and
    images stay `loading="lazy"`; the server keeps sending whole lists (at
    most a few hundred small items), so this is the page's work only;
    (c) checked at 375 px and on the desktop with production's 46 dogs. **The
    self-cleaning part** deletes the user's data, so it is the user's
    decision on the policy proposed in `PENDING.md`: unnamed faces bounded
    as unnamed dogs already are.
38. **The default marked on each slider** (decided, UX, review 24). Backlog
    35's sliders show no mark where the default sits, so a slider moved and
    moved back cannot be put on the default by eye. A `<datalist>` with one
    option at `slider_steps / 2`, named by the slider's `list` attribute,
    makes the browser draw a tick there; nothing else changes. Check it at
    375 px.

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
model; R48 and R49 closed in review 23, R30, R51 and R52 in review 24.

| # | Priority | Recommendation | State |
|---|---|---|---|
| R53 | **high — the user's report, 14/10** | The two dogs are told apart by colour histograms, which overlap: Mirana among Aurora's views, a person among Mirana's | open (below) |
| R54 | medium — a watch | Best of N and the looser frontal gate give a stranger more chances to read "probably <resident>", silent in Home | open (below) |
| R47 | low — a watch | R46's chain has no end: a real dog that takes a vanished person's place would stay a person | open (below) |
| R42 | **high — decided 14/10: (b)** | In Home, a resident's face plus a second person who never shows a face sends nothing | decided: count people with YOLO; developer 23 |
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
counts a dog as a second person (R18), one extra message. **Decided by the
user, 14/10/2026: (b).** "If it errs, it errs": someone hiding beside a
resident must reach the phone, so a person the system cannot account for
always wins over silence in Home (CONTEXT 3).

**R54 — Best of N and a looser gate give a stranger more chances to pass
as a resident (medium, a watch, review 24).** R51 matches every view of a
face group and keeps the best, with `Gallery.match`'s preference — a named
person first, then the score; R30 (b) lets more looking-down faces in. Both
are measured only on the two residents (ARCHITECTURE 10.3, 10.12): the other
resident's best rose by 0.013, never reaching 0.30. What nobody measured is a
stranger: N views are N chances to cross `MATCH_THRESHOLD` against a
resident, and a returning stranger whose views match their own unnamed entry
at 0.6 is recorded "probably <resident>" by one view at 0.30 — silent in
Home, against the user's rule that an unknown person always reaches the
phone (CONTEXT 3). Production holds no stranger with a face yet (2 named
entries, 0 unnamed, 14/10). **Trigger:** a "probably Gustavo" or "probably
Izabel" sighting whose photo is someone else, reported by the user or seen in
a review. **Then:** measure, on that clip, the two cross-view rules that keep
R51's gain for residents — the score alone deciding across views (a named
match only wins within one view, as `Gallery.match` does), or a resident
needing two views over the threshold — and keep the one that names the
stranger right without losing a resident's sure sighting of R51's table.

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

**Review 24 is done, with a release:** developer 22's backlog 34, 35 and 36,
R52, R51 and R30 (b), as `v2026.10.14.2` (HISTORY 13.25). R30, R51 and R52
are closed; R54 is a watch; backlog 37 is designed and 38 added.

**Developer 23: R42 (b), backlog 37's layout and 38, R53 step 1, then
backlog 32 for faces.**

1. **R42 (b)** (section 2), decided by the user: a counter of how many people
   YOLO saw at once in the held person's frames, compared with the distinct
   faces the scan found; when every face found was silenced and YOLO saw
   more people, the best view goes out as `faceless_person`. Tests for the
   hidden-person case and for a dog counted as a person (R18). The counter
   belongs to the event, so check what `clips/` stores: a new optional field
   in the event's JSON is fine, anything else is not (CLAUDE.md).
2. **Backlog 37's layout, (a) and (b), and backlog 38** (section 1): page
   work only. Check at 375 px and on the desktop with production's numbers —
   46 dogs: move the test copy's own `dogs/` aside, copy production's in for
   the check, and put the test copy's back after; only read `C:\JARVIS`.
3. **R53 step 1** (section 2): the bench on a copy of production's `dogs/`.
   **The user has not deleted the misfiled views yet** (checked 14/10 in
   review 24: all nine are still there), so the bench labels the views listed
   in `PENDING.md` as "not this dog" itself, and never deletes them. Export
   a candidate to ONNX once in a throwaway environment if needed, as AdaFace
   was (ARCHITECTURE 10.14); nothing in the program changes in step 1.
4. **Backlog 32 for faces only**, if the session has room: the face labels
   are clean since 14/10; the dogs' half waits for R53's model.

**HANDOFF:** R42 (b) as built and its tests; 37 and 38 checked at 375 px,
with the Dogs tab's page height before and after; R53's table per candidate
(right and wrong by lighting over a threshold sweep, a person crop's and a
two-dog crop's distance to each dog, cost on the M900, size, licence). If the
session runs short, stop after a coherent commit and say what is left.

**Waits for the user:** the policy for unnamed faces (backlog 37,
`PENDING.md`); the misfiled dog views, before the once-only settle of
backlog 28; the checks on the M900 (`PENDING.md`).

**Not planned:** R54 and R47 are watches. R14, R12 and R9 as before. Every
other open backlog item is **(proposto)**.
