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

**Waiting for the user's check on the M900:** items 25 and 3, in `PENDING.md`.

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
    readable, and empties.
29. **On and Off from the bot** (decided). `/off`: J.A.R.V.I.S. stops
    processing images — no motion, no YOLO, no events, no recordings, no face
    scan, no messages — while capture keeps running, so Live and every other
    screen work normally. `/on` resumes. **It always starts On**: Off is not
    stored, so a restart, a crash or the 5-minute task bring it back On — Off
    is an occasional state. Every screen of the page shows On or Off; `/mode`
    and the command list show it too; while Off, the bot sends a reminder
    every 3 hours. Obeyed only from `notify_chat`, like the other commands.
    An event open at `/off` ends as if the motion had stopped.
30. **Home silences a probable resident** (decided; the user: "I have not
    seen a wrong maybe"). Two new cases, `probable_resident_person` (a face
    matched as probable to a Resident) and `probable_resident_dog`, which
    today fall under `known_person` and `other_dog`; defaults on in Away, off
    in Home and Silent. It changes ARCHITECTURE 22.2's default, not its rule:
    the switch undoes it with one tap. Additive in `config.json`
    (`modes.normalised` fills the new cases). Measured 13/10: 72 of 134 named
    face sightings were probable (the user 25, Izabel 47).
31. **Detection sensitivity** (decided). In Settings, per label — person,
    dog, other animals — YOLO's minimum confidence (today `CONFIDENCE` 0.35
    and `ANIMAL_CONFIDENCE` 0.45), stored in `config.json` (additive) and
    applied without a restart. The page says what it does not fix: a person
    bending over is called `dog` as confidently as a real dog (R46), so
    raising the dog value cuts real dogs first.
32. **The "maybe" threshold, chosen from measured accuracy** (decided; the
    user: with a metric they set the threshold, without one the maybe stays
    as it is). Settings shows, for faces and for dogs, a table measured on
    the user's own named photos by leave-one-out — each named view matched
    against all the others: per threshold, how many named views would be
    recognised for sure and what share to the right one, and how many
    unnamed photos would cross it. The user sets the sure threshold from it
    (faces `LEARN_THRESHOLD` 0.45; dogs the sure distance 0.35 and ratio
    0.6), stored in `config.json`. Measured 13/10: faces are 99.3 % right at
    any threshold from 0.363 to 0.45 (1 error in 146 views), but 12 unnamed
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
| Tracking: the label comes from the object's history, not one frame | 7, and R46 |
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
| R46 | **high** | A person who moves while bent over is still filed as a dog: R44 caught 9 of 32 boxes | open (below) |
| R42 | medium — **the user's decision** | In Home, a resident's face plus a second person who never shows a face sends nothing | open |
| R30 | **high** | A face seen from the side is dropped, so many person events end without a face photo | (a) done `9fb8862`; (b) needs a second named person — **met on 13/10: Izabel** (HISTORY 13.12) |
| R12 | medium | Production and test copy on the same M900 double the CPU load | open (HISTORY 13.5) |
| R14 | low | Live MJPEG is encoded once per viewer | open (HISTORY 13.5) |
| R9 | verification | `python-preference = "system"` on the development PC | open (HISTORY 13.4) |

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

**R46 — A person who moves while bent over is still filed as a dog (high,
13/10/2026).** 12 dog reports since the deploy of 12/10: 7 a person bending
or crouching, 3 objects (a helmet, a cloth, clothing on a back), 2 animals at
night. `replay.py --prime` on five of them (`Front/2026-10-13/15-00-17`,
`15-09-58`, `15-19-17`, `14-46-29`, `Back/2026-10-13/11-23-48`): 23 boxes
still kept as `dog`, 9 relabelled by R44. The cause, read in the trace of
`15-00-17`: the woman cleaning moves while bent, the box shifts 50–100 px
between YOLO runs, so its IoU with her last person box falls to 0.40–0.50,
under `SAME_PERSON_IOU` = 0.5; and a relabelled box does not renew
`recent_people`, so a long bend outlives the 2 s memory. YOLO is as sure as
of a real dog (0.47–0.86 here; HISTORY 13.16: 0.62–0.81 against a median of
0.68), so no score threshold separates them. **Fix:** keep the person's
identity across frames — a relabelled box renews the memory, and a moving box
is matched (against where the person's box is heading, or by chaining) — or
tracking proper (backlog 7; a well-regarded pure-Python tracker is preferred
to writing one, PROCESS 5). **Acceptance:** the five clips above lose most of
their `dog` boxes; the twelve true-dog clips of HISTORY 13.16 (six with a
person, six alone) keep theirs, none relabelled; tests for a moving bend and
for a dog at a person's feet.

---

## 3. Next sessions

**Review 18's cycle is done** (`v2026.10.12.4`, deployed 12/10 at 21:36).
On 13/10 the user decided backlog 28–32, and the architect opened R46 from
the day's reports (sections 1 and 2 above).

**Developer 17 (planned 13/10, night):** in this order —

1. **R46** (high): the bent person who moves. Measure first with
   `replay.py --prime` on the five clips in R46, then fix, then measure
   again; the acceptance is in R46.
2. **Backlog 30**: the two probable-resident cases. Small; tests beside
   `tests/test_modes_web.py`.
3. **Backlog 29**: `/on` and `/off`. Capture never stops; analysis does.
   Tests for: Off drops frames before motion, an open event ends, a restart
   starts On, the 3-hour reminder (with the clock patched in the test,
   `monkeypatch`, PYTHON 33).

**Developer 18 (next):** backlog 28 with its once-only tool (run by the
architect on production), then 32 and 31 — 28 touches the user's files, so it
gets its own review.

**Not planned:** R42 waits for the user's choice; R30 (b) can now be measured
with Izabel and joins a later session. R14, R12 and R9 as before. Every other
open backlog item is **(proposto)**.
