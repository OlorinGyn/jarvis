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
| ✓ | **32.** The sure threshold chosen from measured accuracy: faces (decided 13/10, `9fc5592`, review 25, `v2026.10.14.3`), dogs' sure distance (`bc94747`, review 27, `v2026.10.15.2`), both measured by leave-one-event-out (R55) | ARCHITECTURE 10.15, 20 |
| ✓ | **39.** On a phone, an unnamed card is its photo and its name; the empty accuracy table hidden (decided, UX, `a9b8c32`, review 26, `v2026.10.15`) | ARCHITECTURE 17.17 |
| ✓ | **40.** Notifications by incident: nothing dropped, loud or silent, one ring in 30 s at most; a camera with no picture, and its return (decided 16/10, `136e9b0`–`dc86e89`, review 29, `v2026.10.16`); its "later, with tracking" part is item 7's | ARCHITECTURE 12.11, 12.12 |
| ✓ | **41.** Notifications by visit in Home: dog tracks, a resident explains one body, then only news — 98 messages a day to 35 on the month (decided 17/11, `071e55b`, review 32 `7709f94`, `v2026.11.17`); with R63, a failed send tried again | ARCHITECTURE 12.13, 12.14 |
| ✓ | **44.** New people under "Visitor N"; one body's unnamed faces merged (decided 17/11, `92e36a3`, review 33, `v2026.11.17.2`) | ARCHITECTURE 10.17 |
| ✓ | **42.** The photos manage themselves: an unnamed face unseen for 60 days forgotten, a probable dog makes no card (decided 17/11, `c3b0dd2`, review 34, `v2026.11.17.2`); closes backlog 37's self-cleaning part | ARCHITECTURE 10.19 |
| ✓ | **43.** The residents' galleries cleaned by the evidence of one body — closed by the user 18/11, not applied: after item 45 its dry run on production moved 3 views, all wrong, and item 45's gate already does its scan-time step's job | ARCHITECTURE 10.17 |
| ✓ | **45.** Reference photos only of impeccable quality: the eye cleaned what was stored, a cut guards what enters — eDifFIQA(T) ≥ 0.40 for a face view, the box ≥ 120 px for a dog view (decided 17/11, `4652f89`–`1b27565`, review 36 `bf3d6f9`, `v2026.11.17.3`; applied on production 17/11 19:23) | ARCHITECTURE 10.18 |
| ✓ | **46.** The message decided by a quick face pass of 24 frames, the full scan's message waiting at most 45 s, what the full scan finds later as a follow-up (decided 18/11, `6c9d645`, `5e3a668`, review 38 `3767102`, `v2026.11.18`); its measurement on production after a day of use is section 3's | ARCHITECTURE 10.20, 12.15 |
| ✓ | **7.** Tracking (decided 16/10): part 1, every event's tracks recorded (`v2026.10.16.3`, reviews 30–31); part 2's dog rule as backlog 41 (a) (`v2026.11.17`); the rest — the name following the body, the loitering message, "the same body" in the incident — **closed by the user 18/11 as measured** (developer 37, review 39): 1 message in nine days over the visit | ARCHITECTURE 7.16 |

**Waiting for the user's check on the M900:** items 25, 3, 29, 30, 34–42, 44, 45 and 32, in `PENDING.md`.

### Decided on 17/11/2026, to build

After a month left alone (HISTORY 13.33). The user's three answers are in
CONTEXT 3. Items 41, 42 and 44 are done (above, reviews 32 to 34); their
full text is in `HISTORY.md` 8.

Items 43 and 45 are closed (above, review 36 and the user's answer of
18/11); their full text is in `HISTORY.md` 8.

### Decided on 18/11/2026, to build

Item 46 is done (above, review 38), its production measurement in
section 3; its full text is in `HISTORY.md` 8.

47. **Delete an unnamed entry** (decided 18/11, the user: "delete
    items in the No guess section — visitors who came that I do not want
    to keep, only discard") — a face that is a real person, so not a bad
    detection, and not worth keeping. **Delete** does at once what the
    60-day forgetting does (backlog 42, ARCHITECTURE 10.19): the entry
    leaves the gallery and its view photos are erased; its recordings,
    sightings and thumbnails stay, and Recordings reads them as it reads
    a forgotten entry's. If the person comes back, a new entry forms — a
    new "Visitor N". No undo: it asks first ("Delete 3? Their photos are
    erased; their recordings stay. If they come back they appear as a
    new visitor."). **Where (decided, UX):** the unnamed list's selection
    bar, beside "Bad detection" — so "Select all" on the No guess group
    and Delete empties it — and on each unnamed card beside its "Bad
    detection" where the card shows one (a wide screen). Any unnamed
    entry, in any group; a named entry is never deleted this way. People
    and Dogs alike, since the list is one component: a neighbour's dog
    passing is the same case.
48. **"Visitor N" takes the smallest free number** (decided 18/11, the
    user: "I do not want Visitor N to reach large values, we are at 34;
    reuse the numbers no longer in use") — a number is free when no entry holds it: named, merged,
    reported, deleted (47) or forgotten (42). Existing entries keep their
    numbers; on production on 18/11 they hold 2, 3, 4, 21, 25, 29, 30 and
    34, so the next new face is Visitor 1, then 5. The price, accepted
    with the request: a "Visitor 5" in the Telegram chat last week and
    one today may be two people. The page is not affected — Recordings
    never shows the temporary name, and a gone entry's sighting reads as
    one (ARCHITECTURE 10.17, 10.19).

### Decided on 16/10/2026, to build

Item 40 is done (above, review 29); its full text is in `HISTORY.md` 8. Item 7,
tracking, decided the same day, is closed (above, 18/11) and its text there too.

### Decided on 13/10/2026, to build

Items 28–32 are done (above); their full text is in `HISTORY.md` 8.

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
2. **System health** (proposto) — **its first part is done:** a camera with
   no picture for a minute, and its return, reach the phone and the log
   since `v2026.10.16` (item 40, ARCHITECTURE 12.12). What is left: a black
   or covered picture, which still delivers frames, and a daily summary
   (frames, events, messages, outages).

### Important

It works without them, but is incomplete.

4. **Measure the M900 running** (proposto) — CPU with both cameras in motion,
   and whether `HWACCEL` helps (INSTALL 6).
6. **Search and filter** (proposto) — with ~100 events a day, by date only is
   not enough. By person, camera, label.
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
| A warning when a camera goes down | 40, `v2026.10.16`; the rest in 2 |
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
in review 25, R53, R56 and R57 in review 26, R55 in review 27, R60 in
review 29, R61 in review 30, R59, R62 and R63 in review 32.

| # | Priority | Recommendation | State |
|---|---|---|---|
| R58 | medium — a watch | One body with two boxes counts as two people, and the hidden-person message fires | measured, no rule: tracks at once are no better than boxes once the first box counts; 5 such messages in nine days of November (ARCHITECTURE 7.16); item 7 part 2 closed 18/11, so a watch — trigger: a false "hidden person" the user reports |
| R54 | medium — a watch | Best of N and the looser frontal gate give a stranger more chances to read "probably <resident>", silent in Home | open (below) |
| R47 | low — a watch | R46's chain has no end: a real dog that takes a vanished person's place would stay a person | open (below) |
| R12 | medium | Production and test copy on the same M900 double the CPU load | open (HISTORY 13.5) |
| R14 | low | Live MJPEG is encoded once per viewer | open (HISTORY 13.5) |
| R9 | verification | `python-preference = "system"` on the development PC | open (HISTORY 13.4) |

**Measured by developer 26, no rule built (HISTORY 13.29).** R58: none of 588 production
events with a person holds two people, so neither counting rule can be
shown to keep a true pair; rule (a) at 0.9 would remove 15 of 17 one-body
cases, and could swallow a person standing behind another (ARCHITECTURE
22.3). It waited for tracking (item 7): a count of tracks instead of
boxes — and item 7 part 2 closed on 18/11 without one, so it is a watch. **R58 is measurable
since 17/10:** production now holds true pairs — 13 events of 17–18/10
count two or more person tracks at once; two read by eye, both true:
`Back/2026-10-17/19-50-59` (two people on the porch at night) and
`Front/2026-10-17/05-33-16` (two at the door, plus two boxes side by side
at the gate that may be one body). Its text as opened:

**R58 — One body with two boxes counts as two people (medium,
16/10/2026).** R42 (b)'s hidden-person message fired twice in those 23
hours, both false. `Front/2026-10-15/21-47-33`: one person coming through
the door, two `person` boxes (0.70 and 0.42), the smaller inside the larger
— IoU about 0.4, under NMS's 0.45 and `drop_duplicates`'
`SAME_SUBJECT_IOU` 0.5 — so `most_people` was 2. `Front/2026-10-16/
00-12-09`: the resident and a dog in a `person` box (R59). **Then:**
measure, on these two events and on the true two-person events (events
with `most_people` ≥ 2 in their JSON whose picture shows two people — the
user leaving with Izabel), two rules for counting people at once: (a) a
box mostly inside another — intersection over the smaller box's area at or
above some value — is the same body; (b) a count holds only when seen in
more than one analysis frame. Keep the one that removes the false ones
without losing a true pair; a person in front of another also makes one box
sit inside the other, and the user's rule is that one extra message beats a
hidden person (CONTEXT 3), so a tie keeps today's count.

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

**Review 39 is done** (HISTORY 13.41): developer 37's measurement of
item 7 part 2 reviewed — `tools/follow_body.py` read whole, its part 1
run again on production (the same classes), the binding and crossing
sheets read, the joined clips' time alignment checked. No code fixed, no
release. What part 2 adds over the visit is small (ARCHITECTURE 7.16);
**the user closed it as measured**, and chose to wait for the reading
below before planning more; then asked for backlogs 47 and 48
(developer 38, below).

**Next, the architect's: backlog 46 measured on production after a day of
use** (from 19/11 about 13:00). From the log's `message` and `follow-up`
lines (ARCHITECTURE 12.15), with each event's start from its name: start →
sent, median / p90 / p99, against today's 40 / 147 / 507 s and the
replay's 39 / 74 / 115 s; how many messages the quick face, the full scan
and the deadline decided (the replay: 29 %, 54 %, 17 %); the follow-ups
sent and skipped as "sent by the quick pass"; `analysed per minute during
a face scan` against before; and any `quick pass failed`, `person message
failed` or `face scan failed` line. Far from the replay, or a stranger
sent twice, is a recommendation. The same reading says whether the scan
queue still delays messages — if it does, a named track not scanned
again (23 % of a named event's frames, ARCHITECTURE 7.16) comes back as
a proposal.

**Developer 38: backlogs 47 and 48** (the user's request, 18/11, after
choosing to wait for the reading above for anything else). Both small,
both in the gallery and the page; the order below.

1. **Backlog 48 first** — `faces.Gallery._next_visitor` returns the
   smallest N ≥ 1 that no entry's `temporary_name` holds. Every caller
   already holds `_GALLERY_LOCK` after a `load()` (`add`,
   `name_visitors`); keep it so. **Data format:** the header's
   `"visitors"` counter is no longer read; leave it in the file as it is
   — never removed — so a rollback to `v2026.11.18` (max of counter and
   held, plus one) still gives a number no entry holds. Tests: the
   smallest free number after a gap (2, 3, 4, 21 held → 1, then 5); a
   number freed by naming, merging and deleting is given again; a file
   without the counter.
2. **Backlog 47's server** — `POST /api/persons/delete` and
   `POST /api/dogs/delete` with `{"ids": [...]}`, beside `/report`, and
   the one-entry form `POST /api/persons/{id}/delete` and
   `/api/dogs/{id}/delete`. Each id through the gallery's `take_out`
   (photos erased, the entry gone); a named or unknown id is skipped and
   reported back as gone, the way `_report_many` answers. The same write
   guard as every other POST (paired devices). The log names what left:
   "Deleted N unnamed face entries from the page: Visitor 21, …" — the
   temporary name or the id. Check that the dog gallery's `take_out`
   does the same for a dog (`DogGallery` inherits it), and that a
   deleted entry's sightings read in Recordings exactly as a forgotten
   one's (10.19). Tests: an unnamed entry deleted, its view files gone,
   its sightings and thumbnails kept; a named id refused; a mixed list.
3. **Backlog 47's page** — "Delete" in the selection bar beside "Bad
   detection" (`index.html`, both tabs) and on the unnamed card beside
   its "Bad detection" (`app.js`), each with the confirm of item 47's
   text (the count, and "a new visitor" only on People); after it,
   `loadList()` and a line in the list's result ("Deleted 3."). Style it
   as the page's other destructive buttons are. **Check at 375 px and at
   desktop width** with the built-in browser on the test copy: the bar
   must still fit and wrap cleanly with one more button, and a phone
   user reaches Delete through the bar. Screenshots of both widths in
   the HANDOFF.
4. **Before committing**, `tools/check_data.py` (the gallery's reader
   and writer changed), the full test suite, the comment count. **No
   production data touched**: no deletion on `C:\JARVIS`, only on the
   test copy.
5. **HANDOFF:** what changed, the data-format note (the counter kept,
   unused), the screenshots, what the review should read hardest — the
   delete racing a face scan that matches the same entry (10.19's race,
   now at the user's click), and a delete while the entry's page is open
   on another device.

**Waits for the user:** choosing the sure threshold for
faces and the sure distance for dogs from the two tables in Settings →
Detection (the defaults hold until then); the M900 sleeping at the
sign-in screen; the checks on the M900, `v2026.11.18` among them
(`PENDING.md`).

**Not planned:** R54, R47 and R58 are watches. R14, R12 and R9 as
before. Every other open backlog item is
**(proposto)**.
