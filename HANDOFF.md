# HANDOFF — developer 26 (16/10/2026): R59 and R58 measured, no rule built

Both items ended in the plan's "or none, and say so": every candidate rule
either leaves the false events or can lose a true person. One commit, the
measurement tool, so the numbers below can be reproduced and run again on
new reports.

## 1. Items

### R59 — the household's dogs reach the phone as people: measured, no rule built

**Where each `person` box came from.** The listed clips were copied from
production (`C:\JARVIS` only read) and replayed through the real detection
layers, YOLO on every frame with motion, in three detectors that each take
every third frame — the three phases a live camera's 0.3 s rhythm can fall
on (`tools/person_signals.py`, below). Every person box of the dog clips was
looked at as a crop: all 37 are Aurora or Mirana.

| Clip | Person boxes | YOLO | R44 | R46 |
|---|---|---|---|---|
| `Back/2026-10-15/20-54-37` | 1 | 1 | 0 | 0 |
| `Back/2026-10-15/21-01-08` | 0 (production's box not reproduced) | – | – | – |
| `Front/2026-10-15/22-00-19` | 3 | 3 | 0 | 0 |
| `Front/2026-10-16/00-52-26` | 19 | 19 | 0 | 0 |
| `Back/2026-10-16/00-54-05` | 8 | 7 | 1 | 0 |
| `Front/2026-10-16/14-51-12` | 3 | 3 | 0 | 0 |
| `Back/2026-10-15/20-59-24` ("unclear": Mirana, all three) | 3 | 3 | 0 | 0 |
| `Front/2026-10-16/00-12-09` (resident + Mirana) | 136 | 134 | 1 | 1 |

**The cause is YOLO itself**, not R46's chain: R47's bound would change
nothing. Two more events of the same kind, not in the architect's list,
turned up while checking R58: `Front/2026-10-15/19-25-05` (Aurora on her
hind legs, `person` 0.52, beside the resident) and `Front/2026-10-16/14-53-35`
(Aurora at the door, `person` 0.80, by day). The true-person clips have R44
and R46 boxes too (`00-11-41`: 2), so the relabels are not a dog marker.

**The candidate signals**, per kept person box (production's dog gallery
copied at about 16:20 on 16/10; it keeps changing, so the distances move a
little with a newer copy):

| Signal | Dog clips (37 boxes, all dogs) | True-person clips (376 boxes, 9 events) |
|---|---|---|
| DINOv2 distance to the nearest named dog | 0.21–0.52; sure 13, probable 18 | 0.30–0.75; **sure 2, probable 42** at night |
| Height / width | 0.64–3.11 | 1.30–6.02 |
| YOLO's own dog score at the spot | 0.00–0.63 (0.18 but for R44's box) | 0.00–0.65 |
| YOLO zoomed on the box: person ≥ 0.35 | 4 of 37 (all in `00-54-05`) | 322 of 376 |
| YOLO zoomed on the box: dog above person | 28 of 37 | 8 of 376 |

- **The dog gallery does not separate them at night.** In infrared a
  standing person is as close to Aurora or Mirana as the dogs' own boxes:
  `Back/2026-10-15/18-30-12` (a resident, faceless) has 1 sure and 13
  probable dog matches; two of the crops nearest a dog are a person standing
  alone (looked at). A rule on it would turn true people into dogs.
- **Shape and YOLO's dog score overlap** as the table shows.
- **YOLO's zoomed second opinion** — the box cut square with half its size
  of context and scaled to fill 640 px, so a 150 px dog is seen at 640
  instead of ~100 — was not in the list and is the best signal found, but
  not good enough:
  - **per box** it flips 8 true-person boxes (people with a dog at their
    feet, and two standing alone in `00-01-03` and `00-11-41`), which would
    become dog crops in the Dogs tab;
  - **per event** ("the event's person is a dog when no box is confirmed,
    zoomed person ≥ 0.35") it would clear 5 of the 6 dog events that replay with a person box and keep
    every true event — **but** `Front/2026-10-15/19-24-49`, the resident at
    night half hidden behind the car at the frame's edge, keeps only 2 of 16
    boxes confirmed (0.53 and 0.37). A shorter visit by someone crouching
    behind the car — the person the user most wants to hear about — would be
    lost. On full-resolution frames (what the face scan reads) it is worse:
    `19-24-49` keeps **0**. `00-54-05` (Mirana, dark) stays a person either
    way: zoomed, YOLO says person at 0.64–0.85.
  - **positive evidence only** ("a box is a dog when zoomed dog > zoomed
    person"), the safe direction, clears one event of seven
    (`22-00-19`) on analysis frames — `00-52-26` keeps 1 of 19 boxes as a
    person — and two on full-resolution frames.

**Why nothing was built.** The plan's condition is "without losing one true
person" (CONTEXT 3). The only rule that clears most false events does it by
requiring YOLO to confirm a person on a closer look, and the closer look
fails precisely on a partly hidden person at night. The safe rule clears one
or two of seven. Neither is worth its cost: the per-event rule would need
an extra YOLO run per person box in the live loop or a new pass in the scan.

### R58 — one body with two boxes: both rules measured, neither built

**No true two-person event exists in production's recordings.** All 4
events with `most_people` ≥ 2 since R42 (b) are false:

| Event | What the two boxes are |
|---|---|
| `Front/2026-10-15/21-47-33` | one body, the smaller box inside the larger (R58's case) |
| `Front/2026-10-16/00-12-09` | the resident and Mirana in a `person` box (R59) |
| `Front/2026-10-15/19-25-05` | the resident and Aurora on her hind legs (R59) — **not** "the user leaving with Izabel" |
| `Front/2026-10-16/14-53-35` | the resident and Aurora at the door (R59) |

To find true pairs, all **588 production events labelled `person`
(09–16/10)** were scanned with YOLO alone, one frame a second, for a frame
with two `person` boxes over the minimum height and not on the mat (the
scan is a throwaway script; the tool below measures a given clip). 40
events had one; the first such frame of 34 of them, looked at, is:

| What | Events | Intersection over the smaller box |
|---|---|---|
| One body, two boxes (a box taking in the car door, the pillar, a bag) | 17 | 0.96–1.00 for 14; 0.74 and 0.75 on a far, small person; 0.21 for one body cut in two |
| A person and an object (laundry on the line, a door, a shadow) | 9 | 0.00–0.72 |
| A person and a dog in a `person` box | 8 | 0.00–0.40 |
| **Two people** | **0** | – |

The other six had no such frame once the mat rule applied. The candidates
that looked like pairs (`Back/2026-10-13/11-21-49`, `12-56-02`, `12-56-54`,
`Front/2026-10-13/15-30-48`, `Back/2026-10-11/20-19-22`) are one woman and
the laundry, or one person and a door, zoomed to check.

**Rule (a), a box mostly inside another is the same body**, at 0.9: removes
15 of the 17 one-body cases (including R58's own `21-47-33`), none of the
person-with-dog ones. **Rule (b), a count holds only in two consecutive
runs**, on the replays (`person_signals.py` prints "again at the next run"):
removes `19-25-05` and `14-53-35` (blips of one run), not `00-12-09` (the
dog beside the resident lasts 0.6 s), and `21-47-33` does not reproduce two
boxes in the replay at all.

**Why nothing was built.** The plan keeps the rule that removes the false
ones "without losing a true pair", and a tie keeps today's count. With no
true pair in 588 events, neither rule can be shown to keep one; and rule
(a) has a known way to lose one — someone standing in front of or behind
another, the nearer box swallowing the other, a child beside an adult —
the hidden person the user's rule exists for. Rule (b) loses a second
person seen in only one run.

## 2. Commits

| Commit | What |
|---|---|
| `6e0a8eb` | `tools/person_signals.py`: per clip, every kept person box with its origin (YOLO, R44, R46), YOLO's dog score at the spot, height/width, DINOv2 distance and certainty against a dog gallery (read only, `--gallery`), YOLO's zoomed opinion; and every run with two or more people, with intersection over the smaller box and whether the count held at the next run |

No code under `src/` changed.

## 3. Data-format impact

None. The tool only reads clips and a dog gallery. `check_data.py` not run:
nothing read from or written to disk changed. Tests not run: no program code
changed.

## 4. Suggested documentation updates

- **BACKLOG 2, R59 and R58:** the measurements above, and their outcome —
  the user's decision is needed, since each remaining path trades against
  CONTEXT 3. Options the numbers support, for the architect to weigh:
  - R59: the per-event zoom rule, accepted knowingly with its `19-24-49`
    risk, or limited to events where the dog gallery also names a dog in
    the boxes; or wait for tracking (backlog 7), which would carry a dog's
    identity through YOLO's flips; or nothing, as CONTEXT 3 already accepts
    "the household's dogs taken for people" as a cost.
  - R58: rule (a) at 0.9 alone removes the commonest false pair (one body,
    two boxes), at the risk named above; production saw it once in two days.
  - a true two-person recording (the user leaving with Izabel) would make
    R58 measurable; none exists.
- **ARCHITECTURE 7.12 / 7.13 or a new 7.x:** the dog-as-person boxes come
  from YOLO itself, not R44/R46; the zoomed second opinion and why it fails
  on a half-hidden person at night.
- **ARCHITECTURE 22.3:** "Two boxes on one body are what NMS (0.45) and
  `drop_duplicates` remove" — not the nested case: one body's two boxes
  have IoU 0.33–0.43, under both; 17 of 34 two-box frames are that.
- **CONTEXT 9 (repository map) and 10 (commands):** `person_signals.py`.

## 5. Concepts worth explaining to the user

- **Intersection over the smaller box** against IoU: a small box wholly
  inside a big one has IoU = small area / big area, maybe 0.35, but
  intersection over the smaller = 1. That is why NMS and `drop_duplicates`
  never merge the nested boxes.
- **Letterboxing and resolution:** YOLO always sees 640 px, so a dog of
  150 px in a 960 px frame is seen at 100 px; zooming the box gives the
  network six times more pixels of it — and still did not settle it.
- **A "spy" wrapper** (`Recording`): an object with the same `setInput` and
  `forward` methods as the network, keeping the last output — duck typing,
  Python's answer to implementing an interface; the detector never knows.
- **Sampling phases:** a detector that runs every 0.3 s sees one frame in
  three; three detectors offset by one frame see what any live phase could.

## 6. Measurements

- Tool cost: about 26 s per 30 s clip on the M900 with production running
  (YOLO every frame with motion, DINOv2 and a zoomed YOLO per person box).
- The 588-event scan took about an hour in four processes; production's
  frames stayed fresh throughout (`status`: Back 0.0 s, Front 0.1 s).
- No live cost: nothing runs in the program.

## 7. What the review should look at hardest

- Whether the ground truth holds: every dog-clip crop was looked at; the
  true-person clips were taken as the architect listed them, and their
  zoom-flipped crops looked at. The 34 two-box frames were classified by
  eye from one frame each.
- `21-01-08`: production's `person` box is not reproduced by any phase of
  the replay; whatever made it there (a live frame decoded differently) is
  not measured.
- The 0.9 for rule (a) is read off 14 cases at 0.96–1.00; nothing between
  0.75 and 0.96 was seen.

## 8. Not done

Nothing of the plan was skipped; nothing was built, by the plan's own
condition, for both items.

## 9. Usage

| | 5-hour window | Weekly |
|---|---|---|
| Start | 10 % | 17 % |
| End | 40 % | 21 % |

Context at the end: about 232 k tokens.
