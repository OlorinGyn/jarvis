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

**Waiting for the user's check on the M900:** items 25, 3, 29, 30, 34–40 and 32, in `PENDING.md`.

### Decided on 16/10/2026, to build

Item 40 is done (above, review 29); its full text is in `HISTORY.md` 8. Item 7,
tracking, decided the same day, is under Important.

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
7. **Tracking** (decided by the user, 16/10/2026) — "once one frame
   recognised me, you do not want my face any more, only the object":
   turning around does not make the user someone else, and nobody
   teleports into their place. Today the name belongs to the event, not
   the body: one good frame names the whole clip, but the name dies when
   YOLO loses the body for 5 s and the event closes, and with two people
   nobody knows which body is whom. Measured on the 29 person messages of
   15–16/10: 4 were one walk cut into two clips 0–7 s apart, the user
   recognised in one and not the other (`Back/2026-10-15/18-42-31`,
   `Front/2026-10-15/19-41-18`, `Front/2026-10-16/00-30-11`,
   `Front/2026-10-16/14-19-58`); 14 had no frame recognising anyone, which
   tracking cannot name. The identity follows the body, never the clock: a
   time rule ("Gustavo was here a minute ago") would hide a stranger
   arriving right after a resident (CONTEXT 3). **It is also R59's and
   R58's answer** (section 2): a body YOLO calls a dog in most of its
   frames is a dog, and two boxes nested for a whole track's life are one
   body. The design, for the session that builds it: a well-regarded
   tracker (ByteTrack, from Roboflow's `trackers` — probed on the M900 in
   review 29, HISTORY 13.30) in the live loop; each
   face of the clip scan bound to a track by the frame's time; a named
   track not scanned again while other tracks still are; the track
   surviving the event boundary, for a gap measured on the four clips
   above, not guessed; the loitering message of item 40 (a person nobody
   accounts for still there after some minutes, once); and "the same
   place" of item 40's incident becoming "the same body", so a new person
   on the same camera rings again (ARCHITECTURE 12.11). **Part 1 done
   (developers 28 and 29, reviews 30 and 31, `v2026.10.16.3`,
   ARCHITECTURE 7.16):** `trackers` is a dependency, deployed with its
   imports warmed before the stop; `src/jarvis/tracks.py` gives every track
   an id from its first box and runs in the live loop, and each event's
   JSON records its tracks (ARCHITECTURE 8.4), acting on nothing. The vote
   with a run of 2 person frames clears dog-majority tracks without losing
   a true person; a short track that starts as person — R58's false bodies,
   the rest of R59 — needs another signal, and no buffer joins a walk whose
   body left the view for 7–9 s — appearance or place will have to. **Part
   2** acts on tracks, R59 first (section 3).
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
review 29, R61 in review 30; R62 opened in review 31.

| # | Priority | Recommendation | State |
|---|---|---|---|
| R59 | **high** — the user's report | The household's dogs reach the phone as people, boxed `person` by YOLO | measured, no rule; item 7 part 2 builds it (section 3) |
| R58 | medium | One body with two boxes counts as two people, and the hidden-person message fires | measured, no rule; waits for item 7 part 2 — tracks at once are no better than boxes once the first box counts (ARCHITECTURE 7.16) |
| R62 | low | A tracker that failed on every run would fill the log in minutes | open (below); with item 7 part 2 |
| R54 | medium — a watch | Best of N and the looser frontal gate give a stranger more chances to read "probably <resident>", silent in Home | open (below) |
| R47 | low — a watch | R46's chain has no end: a real dog that takes a vanished person's place would stay a person | open (below) |
| R12 | medium | Production and test copy on the same M900 double the CPU load | open (HISTORY 13.5) |
| R14 | low | Live MJPEG is encoded once per viewer | open (HISTORY 13.5) |
| R9 | verification | `python-preference = "system"` on the development PC | open (HISTORY 13.4) |

**Measured by developer 26, no rule built (HISTORY 13.29).** R59: YOLO
itself drew every dog's `person` box (37 of 37 looked at; R44 one, R46
none), so R47's bound would change nothing; the dog gallery, the box's
shape and YOLO's dog score overlap with true people at night, and YOLO run
again on the zoomed box, the best signal, would lose a person half hidden
behind the car at night (ARCHITECTURE 7.15). R58: none of 588 production
events with a person holds two people, so neither counting rule can be
shown to keep a true pair; rule (a) at 0.9 would remove 15 of 17 one-body
cases, and could swallow a person standing behind another (ARCHITECTURE
22.3). **Both wait for tracking** (item 7): the label voted over a track's
frames, and a count of tracks instead of boxes. A recording of two people
together would make R58 measurable (`PENDING.md`). Their text as opened:

**R59 — The household's dogs reach the phone as people (high, the user's
report, 16/10/2026).** "Many notifications in Home": 31 in 23 hours, read
one by one (ARCHITECTURE 22.3). About 6 were Aurora or Mirana in a `person`
box (0.40–0.88), five of them at night, each sent as a faceless person —
the case the user keeps on in Home for every event (CONTEXT 3). The clips,
in production's `clips/`: `Back/2026-10-15/20-54-37` (likely), `Back/
2026-10-15/21-01-08`, `Front/2026-10-15/22-00-19`, `Front/2026-10-16/
00-52-26`, `Back/2026-10-16/00-54-05` (likely), `Front/2026-10-16/14-51-12`
(by day), and the dog counted as a second person in `Front/2026-10-16/
00-12-09` (R58); `Back/2026-10-15/20-59-24` is unclear. The architect's
quick probe on the sent pictures — boxes drawn, not the clean frames — had
the dog gallery name only one (Mirana at 0.256). Not known: whether YOLO
itself said `person`, or R44 or R46 relabelled a dog box (ARCHITECTURE 7.12,
7.13) — R47's trigger. **Then:** replay each clip (`tools/replay.py`) and
say, box by box, where the `person` came from. From R46's chain: R47's bound
is the fix. From YOLO: measure on these clips, and on the residents' true
faceless events of the same days (`Back/2026-10-15/18-30-12` and
`18-42-31`, `Back/2026-10-16/00-01-03`, `00-05-30` and `00-11-41`,
`Front/2026-10-15/19-24-49` and `19-41-18`, `Front/2026-10-16/11-31-51`,
`Back/2026-10-16/13-23-34`), the candidate signals — the dog gallery's
match on the box in the clean frame, YOLO's own dog score in that box, the
box's shape — and build the rule that turns these into dogs **without
losing one true person**: an unknown person always reaches the phone in
Home (CONTEXT 3). A dog so found is a dog by its own case (`resident_dog`,
off in Home). Measure its cost on the M900 if it runs in the live loop.
Copies only; `C:\JARVIS` is read, never written.

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

**R62 — A tracker that failed on every run would flood the log (low,
review 31).** `Camera.detect` logs a traceback each time `Tracks.update`
raises, and the camera goes on (ARCHITECTURE 7.16). A failure that
repeats — a bad state inside the library, carried from run to run — would
write one about three times a second per camera, and `logs/jarvis.log`
keeps 1 MB × 6: the history every review reads (messages, outages, scans)
would be gone in minutes. Not seen: the tests and the 19 replayed clips
never raised. **Then,** with item 7 part 2, when the tracks start to act:
log a camera's first failure with its traceback and then at most a line a
minute with a count, and decide whether a failed tracker is replaced by a
fresh one — keeping the id counter, so ids stay unique. A run or an event
with no tracks falls back to today's behaviour, the boxes — never to "no
person".

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

**Review 31 is done** (HISTORY 13.32): developer 29 finished item 7's
part 1 — the first box joined, measured again, tracks recorded live; no
code fix; **`v2026.10.16.3` released and deployed** at 21:45 on 16/10.

**Developer 30: tracking (item 7), part 2 — R59's rule from the tracks.**
**Precondition: 24 hours of production with `tracks`**, so not before
about 21:45 on 17/10 — a night and a day, the dogs' hours and the
residents'. Earlier, stop at the resume and say so. Only the R59 piece of
part 2: the name following the track, the incident by body, the
loitering message and R58's count are sessions after, from what this one
measures.

1. **Read the day.** A tool, `tools/day_tracks.py`, read-only: every
   production event JSON with `tracks` since the release, per camera —
   events with a person-voted track; events whose every person frame sits
   in tracks voted dog with no run of 2 person frames (the rule's
   candidates); short person tracks (at most 2 frames) alive at the same
   seconds as a dog-voted track; `most_person_tracks` against
   `most_people`. Then the truth by eye, as review 28 did: each candidate
   event's `.best.jpg` or `.jpg`, a dog or a person; and for the day's
   faceless-person messages in production's log (`C:\JARVIS\logs`), which
   ones the rule would have turned into a dog event, and whether each was
   a dog. Run one candidate clip through `replay_tracks.py` and say
   whether the live tracks look like one of its phases.
2. **The place of a short person track** — the JSON holds no boxes, so
   replay the clips of step 1's short person tracks (`replay_tracks.py`
   gives boxes): for each one beside a dog-voted track at the same moment,
   the overlap with the dog's box (IoU and intersection over the smaller)
   and their sizes, on the dogs' and on the true people's — a resident
   walking with the dogs, `Back/2026-10-16/13-23-34`, the edge track of
   `Back/2026-10-16/00-05-30`. Say whether any value separates them, or
   that none does.
3. **The rule, by tests first, only where steps 1 and 2 support it.** At
   the held faceless-person decision in Home (`notify.after_scan`): the
   tracks are complete by then, so no delay is added, and the immediate
   messages of other modes do not change. An event whose every person
   frame sits in tracks voted dog with no run of 2 person frames — plus
   step 2's signal, if one separated — is a dog event, by its own case
   (`resident_dog`, off in Home), not a faceless person. The tests: the
   carried resident (`Front/2026-10-16/00-12-09`'s run of 8) stays a
   person; a person seen once still reaches the phone; a dog-majority
   track is a dog; an event with no `tracks`, or a run the tracker failed,
   decides as today. R62 with it: a camera's first failure logged with its
   traceback, then a line a minute.
4. **Measure the rule** on the day of step 1 and on the 19 clips of
   ARCHITECTURE 7.16: messages it removes, each one a dog; every true
   person kept. If the session runs short, stop after step 2 with a
   coherent commit — the rule waits for the numbers, not the other way.

Copies only; `C:\JARVIS` is read, never written. **HANDOFF:** the day's
counts, the place measurement and what it supports, the rule as built (or
why not), its measured effect.

**Waits for the user:** choosing the sure threshold for faces and the sure
distance for dogs from the two tables in Settings → Detection (the defaults
hold until then); the policy for unnamed faces (backlog 37, `PENDING.md`);
a recording of two people together (R58); the misfiled dog views, thirteen,
before the once-only settle of backlog 28 — the new model sees them right,
but four sit in Chosen, where every match is measured against them; the
M900 sleeping at the sign-in screen; the checks on the M900,
`v2026.10.16` among them (`PENDING.md`).

**Not planned:** R54 and R47 are watches. R59 and R62 are developer 30's;
R58 waits for part 2's later sessions. R14, R12 and R9 as before. Every other open backlog item is
**(proposto)**.
