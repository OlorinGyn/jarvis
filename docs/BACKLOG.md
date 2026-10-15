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
| ✓ | **37 (a, b).** People and Dogs on a phone: two columns, long lists 24 at a time, Waiting newest first (decided, UX, `b8a731b`, review 25, `v2026.10.14.3`); the self-cleaning part waits for the user (`PENDING.md`) | ARCHITECTURE 17.17 |
| ✓ | **38.** The default marked on each slider (decided, UX, `03cde0e`, review 25, `v2026.10.14.3`) | ARCHITECTURE 7.14 |
| ✓ | **32, for faces.** The sure threshold chosen from measured accuracy (decided 13/10, `9fc5592`, review 25, `v2026.10.14.3`); the dogs' half is planned for developer 25, after R55 | ARCHITECTURE 10.15 |
| ✓ | **39.** On a phone, an unnamed card is its photo and its name; the empty accuracy table hidden (decided, UX, `a9b8c32`, review 26, `v2026.10.15`) | ARCHITECTURE 17.17 |

**Waiting for the user's check on the M900:** items 25, 3, 29, 30, 34–39 and 32, in `PENDING.md`.

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
    **The faces' half is done** (`9fc5592`, `v2026.10.14.3`, ARCHITECTURE
    10.15): production's table has no wrong answer from 0.30 to 0.60, which
    is optimistic until R55 leaves each view's whole event out. **The dogs'
    half** is planned (section 3): on DINOv2-small's distances (R53,
    `v2026.10.15`), born with R55's leave-one-event-out. **The user sets the
    sure distance only; the ratio to the second dog stays `SURE_RATIO` 0.6**
    (decided, UX, review 26): the bench showed the ratio is what keeps
    two-dog crops out of the sure answers (3 + 1 instead of 7 + 1 at 0.33,
    ARCHITECTURE 20) — a safety rule, not a preference — and one number to
    set reads better than a grid of two.

### Decided on 14/10/2026, to build

Items 34–39 are done (above, reviews 24 to 26); their full text is in
`HISTORY.md` 8.

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
   There is an automatic restart, but no record of how long it was down.
   **A real case, 14/10 16:32–16:39:** both cameras left the network and the
   log holds no line about it (HISTORY 13.26). A
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
model; R48 and R49 closed in review 23, R30, R51 and R52 in review 24, R42
in review 25, R53, R56 and R57 in review 26.

| # | Priority | Recommendation | State |
|---|---|---|---|
| R55 | medium | The accuracy tables leave out only exact copies: a view's own event vouches for it | open (below) |
| R54 | medium — a watch | Best of N and the looser frontal gate give a stranger more chances to read "probably <resident>", silent in Home | open (below) |
| R47 | low — a watch | R46's chain has no end: a real dog that takes a vanished person's place would stay a person | open (below) |
| R12 | medium | Production and test copy on the same M900 double the CPU load | open (HISTORY 13.5) |
| R14 | low | Live MJPEG is encoded once per viewer | open (HISTORY 13.5) |
| R9 | verification | `python-preference = "system"` on the development PC | open (HISTORY 13.4) |

**R55 — The accuracy tables leave out only exact copies (medium, review
25).** Backlog 32's table, and R53's bench, leave each view out with its exact
copies (cosine ≥ 0.9999 for faces), but the views of one event are
consecutive frames of the same face or dog, and they vouch for each other: a
probe's twin from its own event is still among the references. Production's
face table has no wrong answer from 0.30 to 0.60, and the two residents'
closest pair is 0.313 (ARCHITECTURE 10.14), so the low end, where the user
would lower the threshold, is where a leave-one-**event**-out could differ.
Views do not record their event; sightings do (`clip`). **Then:** record
each view's event, additively and keyed by the view's photo — for instance
`view_events: {"<12hex>.jpg": "Front/2026-10-14/12-00-00"}` in the entry —
so no move by an older version can misalign it; recover the event of the
views stored before, by matching each view photo to its sighting crop (the
16×16 grey thumbnail of `dog_bench.py` found such pairs); and make
`faces.accuracy`, and the dogs' table to come, leave out every reference of
the probe's event. Views whose event cannot be recovered fall back to
today's rule and are counted on the page. Measure on production's galleries
the table before and after.

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

**Review 26 is done:** developer 24's R53 step 2, backlog 39, R56 and R57,
tagged `v2026.10.15` (HISTORY 13.27). R53, R56 and R57 are closed; nothing
was opened.

**Developer 25: R55, then backlog 32 for dogs.**

1. **R55** (section 2), the session's core. Record each view's event
   additively, keyed by the view's photo (`view_events`), in the shared
   gallery code so faces and dogs both get it; recover the event of the
   views stored before — a dog view's photo is the same picture as its
   sighting crop (developer 23's bench found such pairs by a 16×16 grey
   thumbnail), and for faces find out first which stored image a view
   photo matches; make `faces.accuracy` leave out every reference of the
   probe's event, falling back to today's rule, counted on the page, for a
   view whose event is unknown. Measure on copies of production's
   galleries (only read `C:\JARVIS`): how many views' events are recovered
   per gallery, and production's face table before and after. Additive in
   both galleries: an older version must still read them (CLAUDE.md); run
   `tools/check_data.py` before every commit that touches them.
2. **Backlog 32 for dogs** (section 1), born with R55's rule: Settings →
   Detection gains the dogs' table beside the faces', measured by
   leave-one-event-out on DINOv2's distances, per lighting as the bench
   does — per sure distance, the named views named for sure, by day and at
   night, the share right, and the unnamed crops that would cross it, at
   the fixed ratio `SURE_RATIO`. Rows from 0.20 to `PROBABLE_DISTANCE`
   (0.39), at a step that keeps the table readable at 375 px. The user's
   sure distance is stored in `config.json` as the faces' is (additive,
   absent until saved, refused outside its range) and read once per
   operation, never per comparison: `_absorb` matches every unnamed crop.
   It must reach every place the sure rule decides — `record`'s
   reinforcement, `_absorb`'s gathering, `guess` and the first message —
   and nowhere else. Check the panel at 375 px and on the desktop.

**HANDOFF:** R55 as built — how each gallery's events were recovered, how
many views fell back, production's face table before and after; backlog 32
for dogs — production's dog table at the defaults, from a copy, and the page
at both widths. If the session runs short, stop after R55 with a coherent
commit and say what is left.

**Then, not planned yet:** nothing decided waits behind these two.

**Waits for the user:** the policy for unnamed faces (backlog 37,
`PENDING.md`); the misfiled dog views, thirteen, before the once-only
settle of backlog 28 — the new model sees them right, but four sit in
Chosen, where every match is measured against them; the M900 sleeping at
the sign-in screen; the checks on the M900 (`PENDING.md`).

**Not planned:** R54 and R47 are watches. R14, R12 and R9 as before. Every
other open backlog item is **(proposto)**.
