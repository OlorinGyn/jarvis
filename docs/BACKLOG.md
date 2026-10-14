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
    any threshold from 0.363 to 0.45 (1 error in 146 views) — **wrong,
    review 20**: 7 of Gustavo's views are Izabel's faces, counted as right by
    their label; at 0.45 at least 8 of 146 are wrong, and the table means
    something only on clean labels, with each view's exact copies left out of
    its own test — but 12 unnamed
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
| R48 | **high — the user's decision** | The 40-view rule lets a wrong-person view in first; production's Waiting holds Izabel's faces as Gustavo's | open (below); holds backlog 28's release |
| R47 | low — a watch | R46's chain has no end: a real dog that takes a vanished person's place would stay a person | open (below) |
| R42 | medium — **the user's decision** | In Home, a resident's face plus a second person who never shows a face sends nothing | open |
| R30 | **high** | A face seen from the side is dropped, so many person events end without a face photo | (a) done `9fb8862`; (b) needs a second named person — **met on 13/10: Izabel** (HISTORY 13.12) |
| R12 | medium | Production and test copy on the same M900 double the CPU load | open (HISTORY 13.5) |
| R14 | low | Live MJPEG is encoded once per viewer | open (HISTORY 13.5) |
| R9 | verification | `python-preference = "system"` on the development PC | open (HISTORY 13.4) |

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
bends (HISTORY 13.20).

---

## 3. Next sessions

**Review 20 is done, without a release:** backlog 28 is on `master` and
waits for R48, so the next release carries whatever the user decides there.
Production stays on `v2026.10.13`.

**Developer 19 (planned 14/10):** backlog 31 alone — detection sensitivity
per label in Settings. It is decided and does not touch the galleries, so it
does not wait for R48. As item 31 says: YOLO's minimum confidence for person,
dog and other animals (today `CONFIDENCE` 0.35 and `ANIMAL_CONFIDENCE` 0.45),
stored in `config.json` as new optional keys (older files keep today's
values), applied without a restart, and the page says what it cannot fix —
a person bending over is called `dog` as confidently as a real dog (R46), so
raising the dog value cuts real dogs first. Tests for the defaults, a stored
value, a value out of range, and the change reaching the detector without a
restart; `check_data` on the result.

**Waits for the user:** R48, and with it backlog 28's release and backlog 32
(its table means something only on clean labels).

**Not planned:** R42 waits for the user's choice; R30 (b) can now be measured
with Izabel and joins a later session; R47 is a watch. R14, R12 and R9 as
before. Every other open backlog item is **(proposto)**.
