# HANDOFF — developer session 37: item 7 part 2 measured

Plan: `docs/BACKLOG.md` 3, "Developer 37". Read-only on production
(`C:\JARVIS` read in place, nothing written there, `lower_priority`). No
program code changed; tools and their tests only. Month 10–18/11 (18/11
until 13:29), Home, the built path's messages.

## 1. What was done

**`cab34ea` — `tools/follow_body.py`, new, with `tests/test_follow_body.py`
(12 tests); `tools/replay_quick_pass.py` `built()` changed.**

- `replay_quick_pass.built()` now **returns** what it replayed (span,
  events, each event's messages sent, the full scan's sightings, the sure
  threshold) and takes `every` / `--messages` to print every event's
  messages, not only the differing ones. Its printed lines are unchanged.
- `follow_body.py` runs `built(..., aside=True)` and then:
  - **part 1** (always): `read_restarts` (the logs' `Starting N camera(s)`
    lines; a shared id counts only within one run, `run_of` by `bisect`),
    `classify` (the classes (a)/(b)/(c) of each faceless message),
    `consecutive` (pairs of consecutive person events of a camera, shared
    ids, gaps), `lifetimes` (each track by camera, run and id over all its
    events);
  - **part 2** (`--bind`, `--sample N`): `replayed_runs` replays the live
    loop's phase 0 — motion on every frame, `SubjectDetector` and a fresh
    `jarvis.tracks.Tracks` on every third — over the event's clip, or over
    the chain of clips from the naming event to the faceless one joined as
    one timeline (`replay_tracks.timeline`/`frames`); `bind` puts each
    cached face of the full scan (developer 35's cache) on the person box
    of the nearest run within 0.5 s that holds the face's centre;
    `saved_share` counts the scanned frames whose nearest run holds only
    person tracks already named sure; two contact sheets.

Closes the plan's steps 1–3 of developer 37. No recommendation closed.

## 2. Data-format impact

None. Nothing is written to `clips/`, `faces/`, `config.json` or `.env`;
the gallery is loaded, never saved. The only files written are the face
cache and the sheets under `%TEMP%\jarvis_quick_pass\` (11 events added to
the cache by `--detect`). `check_data.py` not needed (no reader or writer of
production files changed).

## 3. The numbers

`uv run python tools/follow_body.py C:\JARVIS --since 2026-11-10 --bind --sample 30`

The built replay itself: 1252 person events, decided by full scan 673,
quick face 370, deadline 209; person messages today 259, built 270; 28
events differ (2.2 %), p50/p90/p99 39/75/115 s — as review 38's run. Every
one of the 1252 events has tracks; 7 production restarts fall in the span.

### 3.1 Faceless person messages of the built path, by class

| day | (a) named earlier | (b) tracks > faces, resident | (c) neither | total |
|---|---|---|---|---|
| 10/11 | 1 | 3 | 31 | 35 |
| 11/11 | 0 | 1 | 21 | 22 |
| 12/11 | 1 | 2 | 10 | 13 |
| 13/11 | 0 | 1 | 17 | 18 |
| 14/11 | 0 | 1 | 14 | 15 |
| 15/11 | 0 | 3 | 24 | 27 |
| 16/11 | 0 | 1 | 36 | 37 |
| 17/11 | 1 | 3 | 37 | 41 |
| 18/11 (to 13:29) | 0 | 0 | 8 | 8 |
| **all** | **3** | **15** | **198** | **216** |

By kind: side or best view ("no face") 182 — (a) 1, (c) 181; hidden person
34 — (a) 2, (b) 15, (c) 17. **(a) and (b) together 18, 2.0 a day: above
the plan's one a day, so step 2 ran.**

Examples: (a) `Back/2026-11-10/12-03-19` hidden person ← named in
`Back/2026-11-10/12-02-19`; `Back/2026-11-12/15-03-33` no face ←
`Back/2026-11-12/15-02-32`; `Back/2026-11-17/10-58-13` hidden person ←
`Back/2026-11-17/10-57-12`. (b) `Front/2026-11-10/08-55-47`,
`Back/2026-11-10/17-56-39`, `Front/2026-11-10/23-35-08`. (c)
`Front/2026-11-10/00-47-47`, `Front/2026-11-10/01-16-39`,
`Back/2026-11-10/09-15-50`, all no face.

What decides it: **(c) is 92 %.** 181 of the 182 side/best-view messages
have no track that crossed from a named event — every (a) source is the
event right before, 60 s earlier (below).

### 3.2 Consecutive person events of a camera sharing a track id

| day | shared | apart | total |
|---|---|---|---|
| 10/11 | 15 | 286 | 301 |
| 11/11 | 1 | 88 | 89 |
| 12/11 | 5 | 41 | 46 |
| 13/11 | 2 | 87 | 89 |
| 14/11 | 0 | 36 | 36 |
| 15/11 | 11 | 229 | 240 |
| 16/11 | 0 | 103 | 103 |
| 17/11 | 14 | 283 | 297 |
| 18/11 | 0 | 49 | 49 |
| **all** | **48** | **1202** | **1250** |

Gap from the first event's end to the second's start: **shared** median
1 s, p90 1 s, max 3 s; **apart** median 34 s, p90 1760 s. Every shared
pair is one event cut by the event's length limit (the examples start 60 s
apart: `Back/2026-11-10/10-37-22 → 10-38-22`, `13-53-37 → 13-54-37` on
12/11, `17-52-26 → 17-53-27` on 17/11) — never a walk that left the view and
came back: the 3 s lost buffer cannot join those, as item 7's text already
says (the 0–7 s gaps of 15–16/10).

### 3.3 Person tracks living for minutes (item 40's loitering)

2088 person tracks (voted person over all their events); 46 in more than
one event.

| | across events, face | across, no face | one event, face | one event, no face |
|---|---|---|---|---|
| more than 2 min | 1 | 0 | 0 | 0 |
| more than 5 min | 0 | 0 | 0 | 0 |

The one: Back, run 39, id 3861, 3.9 min over 5 events
(`Back/2026-11-10/12-04-20` .. `12-08-21`), a resident sweeping (the
binding sheet's first row is the same morning). **No track lives 5 minutes;
a loitering rule on track age would never have fired this month.**

### 3.4 Part 2 — faces bound to replayed tracks, the 18 (a)+(b) events

Phase 0, lost 3 s, nearest run within 0.5 s, the face's centre inside the
person box (the smaller when two hold it). "Explained": every replayed
person track of the event has a face bound to it or carries a sure name
from the chain.

| event | class, kind | person tracks | with a face | named sure | explained | faces / unbound | frames saved |
|---|---|---|---|---|---|---|---|
| Back/2026-11-10/12-03-19 | (a) hidden | 5 | 2 | 1 | no | 8 / 1 | 26 of 272 |
| Back/2026-11-10/17-56-39 | (b) hidden | 7 | 3 | 2 | no | 12 / 0 | 22 of 271 |
| Back/2026-11-11/21-27-50 | (b) hidden | 3 | 1 | 1 | no | 36 / 12 | 73 of 309 |
| Back/2026-11-12/15-03-33 | (a) no face | 2 | 1 | 1 | **yes** | 1 / 0 | 0 of 115 |
| Back/2026-11-13/15-29-57 | (b) hidden | 1 | 1 | 1 | **yes** | 33 / 0 | 105 of 224 |
| Back/2026-11-14/01-01-19 | (b) hidden | 1 | 1 | 1 | **yes** | 12 / 0 | 27 of 163 |
| Back/2026-11-16/18-31-59 | (b) hidden | 3 | 1 | 1 | no | 15 / 0 | 19 of 124 |
| Back/2026-11-17/01-27-39 | (b) hidden | 4 | 2 | 1 | no | 21 / 14 | 19 of 183 |
| Back/2026-11-17/10-58-13 | (a) hidden | 3 | 1 | 1 | no | 9 / 1 | 186 of 270 |
| Back/2026-11-17/12-05-25 | (b) hidden | 3 | 2 | 2 | no | 34 / 0 | 127 of 218 |
| Back/2026-11-17/19-18-51 | (b) hidden | 5 | 1 | 1 | no | 5 / 0 | 13 of 306 |
| Front/2026-11-10/08-55-47 | (b) hidden | 3 | 1 | 1 | no | 16 / 0 | 111 of 265 |
| Front/2026-11-10/23-35-08 | (b) hidden | 1 | 1 | 1 | **yes** | 3 / 0 | 19 of 139 |
| Front/2026-11-12/13-49-58 | (b) hidden | 1 | 1 | 1 | **yes** | 19 / 0 | 28 of 137 |
| Front/2026-11-12/15-50-38 | (b) hidden | 1 | 1 | 1 | **yes** | 5 / 0 | 27 of 113 |
| Front/2026-11-15/02-17-40 | (b) hidden | 3 | 1 | 1 | no | 15 / 0 | 21 of 273 |
| Front/2026-11-15/16-56-11 | (b) hidden | 11 | 3 | 1 | no | 34 / 1 | 0 of 271 |
| Front/2026-11-15/19-47-59 | (b) hidden | 6 | 3 | 2 | no | 31 / 1 | 0 of 133 |

- **Explained: 6 of 18 — about 0.7 a message a day.** 1 of the 3 (a), 5 of
  the 15 (b).
- **The 5 (b) explained are one body in the replay** (one person track,
  with the face): the live run counted two person tracks at once, the
  replay's phase 0 one. They are R58's kind — a second box or a second
  short track on one body — more than a name following a body; tracks at
  once from a steadier tracker would answer them as well as a bound name.
- The 12 not explained have more replayed person tracks than tracks with a
  face: real second people (the sheet's second row: the resident with a
  box, then a dog beside him) and **fragments** — one walk the tracker cut
  into several ids (11 tracks on `Front/2026-11-15/16-56-11`). A rule
  "every person track named" would keep the hidden-person message on
  these, so they are not losses.
- Faces bound: 279 of 309 (90 %); 26 of the 30 unbound in two night events
  (`Back/2026-11-11/21-27-50` 12, `Back/2026-11-17/01-27-39` 14). One face
  sat inside two person boxes.

**The scan time "a named track not scanned again" would save:**
on the 18 events 823 of 3786 scanned frames (22 %); on **30 events with a
sure resident, evenly spread over the 297 of the month: 1184 of 5234
frames (23 %)**, 408 of 462 faces bound. Frames count, not seconds: every
scanned frame costs about the same (developer 35's cost fit).

### 3.5 Contact sheets

- `%TEMP%\jarvis_quick_pass\sheets\binding.jpg` — three clips, three runs
  each: the person boxes with their replayed ids (green) and each bound
  face with its identity and track (red). Every face sits on the right
  body: the resident sweeping (Back 10/11 12:03), the resident carrying a
  box and then close to the camera with a dog at his side (Back 10/11
  17:56, the face on #1 then #5), the resident at night (Back 11/11 21:27).
- `%TEMP%\jarvis_quick_pass\sheets\crossing.jpg` — three pairs that shared
  a live id, joined: the crossing track's last box before the cut and first
  after. **One body each**, same pose 0.3 s apart (Back 10/11 10:37→10:38,
  12/11 13:53→13:54, 17/11 17:52→17:53). The replay's id, not the live one
  (the live boxes are not on disk); the same tracker with the same
  parameters, so the live id is the same kind of join.

## 4. Suggested documentation updates

- **ARCHITECTURE 7.16**: a subsection "What part 2 adds over the visit,
  measured (developer 37)" with 3.1–3.4's tables in short, and that a
  shared id across events is, this month, only the 60-s cut.
- **BACKLOG item 7**: the measurement done; the numbers for the decision
  (below).
- **ARCHITECTURE, the tools list** (wherever `replay_quick_pass.py` is
  listed): `follow_body.py` and `--messages`.
- **BACKLOG item 40 / 12.11**: loitering by track age would not have fired
  in this month (no track lives 5 min; the buffer is 3 s).
- **HISTORY 14.3**: the usage below.

## 5. Concepts worth explaining to the user (PYTHON)

- `bisect.bisect_right(restarts, moment)`: binary search in a sorted list —
  "how many restarts before this moment" is the run number. Java's
  `Collections.binarySearch`, C#'s `List.BinarySearch`, but returning the
  insertion point directly.
- Set algebra for the classes: `ids & earlier_ids` (intersection),
  `persons <= (with_face | carried)` (subset of a union) — Java's
  `retainAll`/`containsAll` in one operator each.
- A closure as a strategy: `identity_of(gallery, sure)` returns a function
  `label_of(embedding)` that remembers `gallery` and `sure` — the role an
  anonymous class implementing an interface plays in Java, or a lambda
  capturing locals in C#.
- `min(candidates)` on tuples `(area, track_id)`: tuples compare element by
  element, so the smallest box wins without a comparator.
- Joining clips into one timeline with overlapping frames skipped
  (`replay_tracks.frames`, a generator): why a face from the second clip's
  pre-roll binds to a run read from the first clip.

## 6. Measurements and cost

- Part 1: 3 min 18 s (almost all of it the built replay over the cache).
- `--detect` for the 11 events since the last cache fill: about 3 min.
- Part 2: 1312 s (22 min) — 21 clips of the (a)/(b) chains, 30 sample
  clips, 6 clips of the crossing pairs: about 23 s per clip, YOLO on every
  third moving frame at below-normal priority. Production kept a 0.1 s
  frame at the start; it was not watched during the run.

## 7. What the review should look at hardest

1. **Time alignment** between the clip and the runs. The clips start at
   pts 0.000 (checked with ffmpeg on `Back/2026-11-17`), 1920×1080 at
   15 fps; the cache's `t` is showinfo's `pts_time` of the full-size frame;
   the replay reads the clip at `-r 10`, 960×540, frame *i* at *i*/10 s;
   the face box is scaled by 960/width (0.5). A joined chain places each
   clip at its `started_at − PRE_SECONDS`; the overlap keeps the earlier
   clip's frames, so `bind` takes the nearest run whatever clip it came
   from (`test_a_face_in_the_overlap_binds_to_the_earlier_videos_run_on_the_timeline`).
   The sheets agree, but only nine runs were looked at.
2. **Phase 0 only.** The live loop's phase is unknown; the 5 (b) events
   "explained" are the ones where phase 0 saw one person track and the live
   run two. Another phase might explain fewer or more; replay_tracks has all
   three if the architect wants the spread.
3. **"Every person track named or faced" counts replayed tracks over the
   event, not at once.** Fragments of one body count as separate tracks,
   which makes "explained" strict. That is how the live tracker would
   behave too, but the 12 "no" rows mix fragments with real second people;
   I did not separate them.
4. **(b)'s faces count** is the full scan's sightings (one per person
   found), against `most_person_tracks` from the live JSON.
5. Whether "sure resident in an earlier event" in (a) should also accept a
   naming event *after* the faceless one (it does not; a message cannot
   wait for it).

**For the design:** a name following the body would have changed about 6
messages in 9 days, 5 of them answerable by counting tracks at once
(R58's side); a walk cut by the 60-s limit already shares its id, while a
walk out of view and back never does. The bigger number is the scan:
about 23 % of a named event's scanned frames hold only already-named
tracks.

## 8. Not done

Nothing of the plan left. Not separated: fragments from real second people
in 3.4 (point 3 above).

## 9. Usage

| | 5-hour window | weekly | context |
|---|---|---|---|
| start | 46 % (resets 17:00) | 35 % | 76 k |
| end | 53 % | 36 % | 175 k |
