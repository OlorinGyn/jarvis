# Pending — what is not work yet

What the conversations with the user leave open, kept here so that clearing a
conversation loses nothing (`CLAUDE.md`, "Clear, not compact"). The architect
owns this file and reads it at every resume; the developer does not use it.
It is kept apart from the documentation of the application and from the plan
the developer follows, so the architect can write it while a developer
session runs.

An item leaves this file when it becomes a decision (`CONTEXT.md`), work
(`BACKLOG.md`) or is dropped with its reason (`HISTORY.md`). If the file only
grows, decisions are being postponed.

## Waiting for the user

- **After a power cut the M900 goes to sleep at the sign-in screen**
  (HISTORY 13.26): on 14/10 it booted by itself at 21:47, production started
  and both cameras were ok, and 50 s later Windows (`winlogon.exe`, reason
  `ScreenOffGracePeriod`) put it to sleep — 18 hours unwatched, until someone
  woke it at 15:58 on 15/10. "Sleep after: never" does not cover the sign-in
  screen with nobody logged on. **A system setting, so the user's to apply**;
  the likely ones are two hidden power settings — "System unattended sleep
  timeout" (`SUB_SLEEP`, `7bc4a2f9-d8fc-4469-b07b-33eb785aaca0`, 2 minutes
  by default) and "Console lock display off timeout" (`SUB_VIDEO`,
  `8ec4b3a5-6868-48c2-be75-4f3044be88a7`) — each made visible with
  `powercfg -attributes <subgroup> <setting> -ATTRIB_HIDE` and set to 0 on
  mains power with `powercfg -setacvalueindex SCHEME_CURRENT <subgroup>
  <setting> 0`, then `powercfg -setactive SCHEME_CURRENT`, in an
  administrator PowerShell. **The test that settles it:** restart the M900,
  do not sign in, and after five minutes open the page from the phone
  (`http://192.168.0.18:8765` at 16:40 on 15/10 — the M900's address
  moves with DHCP: .19 for some hours that day, .18 again). If it still
  sleeps, the event log names the caller again. Once it
  holds, the architect writes it into INSTALL for any new machine.
- **Backlog 25's acceptance on the M900** (BACKLOG 1): in use since 13/10 —
  the user, Izabel, Mirana and Aurora are marked Resident and Home is on; the
  user's one remark (probable residents still reach the phone) became
  backlog 30. Not yet confirmed: that a person with no face does reach the
  phone in Home, and that `/away` from the phone changes the mode the page
  shows.
- **Backlog 29 and 30 on the M900** (`v2026.10.13`): `/off` from the phone —
  the header shows a red Off, nothing is recorded, a reminder comes after
  3 h — then `/on`; and in Home, a "probably Gustavo" or "probably Izabel"
  no longer reaches the phone. One reading to confirm: an event already open
  at `/off` still finishes and sends its follow-ups (ARCHITECTURE 22.7).
- **Backlog 3's acceptance**: open the page from a phone
  (`http://192.168.0.18:8765` at 16:40 on 15/10; the address comes from
  DHCP).
- **Backlog 26 and 27 on the phone** (`v2026.10.12.2`): select many unnamed
  dogs and name them at once; Notifications is now inside Settings.
- **Misfiled dog views** (R53, 14/10): thirteen, all still in production
  at review 25 (14/10, 17:30). Positions as the page shows them from
  `v2026.10.14.3` on — Chosen in stored order, **Waiting newest first** (the
  photo names start with the six characters given):
  - **Aurora** — Chosen 5 (`89848c`, both dogs at the door) and 6
    (`7221b7`, a person with a bag); Waiting 11 (`f530c0`, a man), 19
    (`257e9a`, both dogs), 28 (`282a53`, both dogs) and 30 (`d6bb2c`,
    Mirana) — of 34, so 28 and 30 are behind "Show 10 more".
  - **Mirana** — Chosen 31 (`6b3d84`, brown fur in sunlight: unclear, check
    it) and 37 (`583bd4`, both dogs); Waiting 19 (`cc29b3`, both dogs), 22
    (`108df8`, someone in red), 23 (`557fa0`, shoes and a hand), 26
    (`6f8002`, dark clothing) and 46 (`554245`, both dogs) — of 47, so 46
    is behind "Show 23 more".
  `257e9a`, `282a53`, `583bd4` and `554245` were found by developer 23's
  bench: each is the same picture as a sighting of the two dogs together.
  **Since `v2026.10.15` the new model sees each of them right** — every
  person crop is no dog, the Mirana filed under Aurora is "probably
  Mirana", no two-dog crop is sure (ARCHITECTURE 20) — but they were
  migrated as they are and still sit in the galleries, **four of them in
  Chosen** (`89848c`, `7221b7`, `6b3d84`, `583bd4`), where every match is
  measured against them. Deleting them still matters. **The once-only settle waits
  for these too**: it would put the Waiting ones into Chosen first. Done on
  the faces side: the seven head-tops deleted and the unnamed entries named
  (the user, 14/10). Gustavo's own five head-tops in his Chosen stay (they
  match Izabel at 0.29 at most); deleting them is optional.
- **`v2026.10.14` on the M900**: the next person events should name Gustavo
  and Izabel more often, sometimes as "probably" (R51); a face message that
  names the wrong person goes to the architect. Read in review 24: 6 face
  scans from 12:07 to 15:40, one "probably Gustavo" silenced in Home, no error
  in the log.
- **`v2026.10.14.2` on the phone and the M900** (backlog 34–36): the header's
  On button switches analysis Off after asking, and On with one tap (from the
  phone only once it is paired with the PIN); Settings → Detection shows
  sliders with the explanation beside them; Settings → Notifications puts
  Telegram beside the table on a wide screen. A note to the architect if a
  slider's ends, or anything on the phone, reads wrong.
- **`v2026.10.14.3` on the phone and the M900** (R42 (b), backlog 37, 38 and
  32 for faces): in Home, leaving with someone whose face the camera does
  not see sends "2 people seen, 1 face found, best view" — the picture may
  show only you (R56); People and Dogs show two columns on the phone and
  long lists 24 at a time, Waiting newest first; each detection slider has a
  tick at its default; Settings → Detection → "Face recognition: when a name
  is sure" shows production's table — **choosing a threshold is the user's**;
  since `v2026.10.15.2` it leaves each view's whole event out (below). A "hidden person" message for a
  scene with only residents and dogs goes to the architect, with its time.

- **`v2026.10.15` on the phone and the M900** (R53, backlog 39, R56,
  R57): the dogs are told apart by DINOv2-small — messages and the Dogs tab
  should name Aurora and Mirana right more often, at night too, and a
  person's shoes or clothing should never be named a dog; a dog message
  that names the wrong dog goes to the architect, with its time. The
  hidden-person message ("2 people seen, 1 face found") now shows the frame
  where the people were counted, boxes drawn. On the phone an unnamed card
  on People and Dogs is its photo and its name: tap photos, then name or
  report them in the bar at the bottom.

- **`v2026.10.15.2` on the phone and the M900** (R55, backlog 32 for
  dogs): Settings → Detection now holds two tables, both measured leaving
  each photo's whole visit out — a visit's frames vouched for each other
  and made the faces' table look better than it is. **The faces' numbers
  dropped and that is the honest picture:** at 0.40, 39 of 80 named views
  are named for sure by another visit (66 before), still no wrong answer at
  any threshold (ARCHITECTURE 10.15). **The new dog table** — at the
  default 0.33, 44 of 56 by day and 9 of 24 at night, all right; 26 unnamed
  crops would be named. **Choosing the face threshold and the dog distance
  is the user's**; the defaults hold until then. A note to the architect if
  either table reads wrong on the phone.

## Decided, not yet done

- **Tracking: once a face names a body, follow the body** (backlog 7, the
  user, 16/10/2026). The user's words: once one frame recognised them, stop
  caring about the face and follow the object — turning around does not
  make them someone else, nobody teleports into their place. Today the
  name belongs to the event, not the body: one good frame already names the
  whole clip, but the name dies when YOLO loses the body for 5 s and the
  event closes, and with two people nobody knows which body is whom.
  Measured on the 29 person messages of 15/10 16:00 to 16/10 15:00
  (production's log): **4** were one walk cut into two clips 0–7 s apart,
  the user recognised in one and not the other (`Back/2026-10-15/18-42-31`,
  `Front/2026-10-15/19-41-18`, `Front/2026-10-16/00-30-11`,
  `Front/2026-10-16/14-19-58`) — what tracking fixes; 7 dogs (R59) and 2
  false "2 people" (R58), which a track's label history and one track per
  body would help; **14** had no frame recognising anyone nearby — the
  backyard at night, six clips from 00:01 to 00:12 — which tracking cannot
  name; 2 had the user recognised 24 s and 3 min earlier on that camera,
  reachable only by a rule of time, which the architect advised against: it
  would hide a stranger arriving right after a resident (CONTEXT 3). The
  identity must follow the body, never the clock; across a gap of a few
  seconds it is an inference, so the gap a track survives is measured, not
  guessed. To plan in the next review, after R59: a well-regarded tracker
  (ByteTrack, e.g. through `supervision`), each face of the clip scan bound
  to a track by the frame's time, a named track not scanned again while
  other tracks still are, and the track surviving the event boundary.
- **Notifications by incident** (the user's principles, CONTEXT 3; which
  situations are risk was left to the architect, 16/10/2026). The design
  below is the architect's; the user may veto any part.
  **Measured** in production's log: in Home, 15/10 16:00 to 16/10 16:15,
  33 messages, only 2 within 30 s of the one before — the volume there is
  the false ones (R59, R58) and residents with no face seen, which no rate
  rule removes. Before the modes, every case on as in Away (10/10 to 12/10
  18:00), 187 messages; from 10/10 to 15/10, 91 of 389 came within 30 s of
  the one before, 80 on the same camera — mostly an event's immediate
  "person" and its face or best-view follow-up 20–40 s later. **A hole
  found the same day:** the per-camera cooldown (120 s, ARCHITECTURE 12.3)
  drops what it blocks — a held faceless person on a camera that sent
  anything in the last 2 minutes logs "no face: skipped: cooldown" and never
  reaches the phone (`notify._faceless`), so a stranger arriving right after
  a resident's faceless message is lost, against CONTEXT 3.
  **Competitors** (searched 16/10): Frigate has a global and a per-camera
  cooldown — a rate limit that drops — and its phone apps dedupe to one
  notification per review item; its zones take a loitering time. UniFi
  Protect's Alarm Manager has loitering among its triggers and "Ignore
  Repeated Actions" within a timespan. Ring's Motion Frequency snoozes a
  camera 1–2 minutes after an event (battery models), with Modes and Motion
  Schedules. Hikvision raises a video-tampering alarm. Eufy offers only a
  snooze of 30 min to 12 h. Each drops or snoozes; none merges.
  **The design:**
  1. **An incident** opens with the first message while the house is quiet
     and stays open while messages follow within 3 minutes. Replayed on the
     log: 187 → 75 loud before the modes; 33 → 28 in Home.
  2. **Loud** (a push with sound): the incident's first message; the
     incident on another camera (the user's "new place"); more people at
     once than the incident had; a person nobody accounts for still there
     after N minutes, once (loitering, N to measure); a camera with no
     picture — offline, black or covered — once when it goes and once when
     it returns (backlog 2, the real case of 14/10).
  3. **Silent** (Telegram's `disable_notification`: it arrives, with no
     sound): everything else the mode sends today inside an open incident —
     the next clips in the same place, the face or best view that completes
     a message. Silent messages and not edits of one message, because each
     photo then stays on Telegram's servers: evidence off the M900 if it is
     stolen or broken in a break-in.
  4. **The floor:** at most one loud message in 30 s across the house; one
     that falls inside waits for the 30 s mark and goes merged with any
     other. **Nothing is dropped**; this replaces the per-camera cooldown.
  5. **With tracking** (above), "the same place" becomes "the same body":
     a new person on a camera inside an open incident is a new loud
     message, not a silent one.
  **Order** for the next review: after R59 and R58, the incidents and the
  camera-down message before tracking — they need no track, and a real
  break-in is where the frequency matters; then tracking.
- **Backlog 28's once-only settle on production** (`tools/settle_waiting.py`,
  the user's choice of 13/10: what the rule leaves is deleted): the
  architect runs it after the misfiled dog views above are deleted (the
  faces are ready since 14/10). The EPUB's documents were chosen by the user on 14/10/2026 —
ARCHITECTURE and PYTHON only — and `tools/make_epub.py` follows it (CONTEXT
10); the EPUB itself is built when the user asks.

## Open discussions

**Self-cleaning People and Dogs — the architect's proposal, review 24**
(backlog 37; the user, 14/10: "perhaps clean themselves now and then").
Measured on production on 14/10: most of it already cleans itself. A
person's or dog's Chosen keeps 40 views and Waiting at most 100 (backlog
28); unnamed dogs keep the newest 60 (R27; 44 today, about 7 new a day); the
sighting photos grow about 2.7 MB a day for faces and dogs together, next to
~300 MB of clips, and are the record of who came — kept. **The one list with
no bound is unnamed faces**: every stranger seen with two or more views
becomes an entry, forever (none today: the old gallery's 8 unnamed entries
were Izabel, named on 14/10).
**Proposal:** the dogs' rule for faces — keep the newest 60 unnamed faces;
past that, the oldest is forgotten with its view photos; a named person is
never touched. What it costs: a stranger last seen 60 strangers ago is no
longer recognised as "the same unnamed face" when they come back, and their
old sightings read "?" on Recordings, as a forgotten dog's do. **The user
decides**: yes, a different number, a rule by age (unnamed and not seen for
N days) instead, or no cleaning.

**The (proposto) items** — 1 zones per camera, 2 a warning when a camera
goes down, 33 buttons on the Telegram message, 6 search and filter: the user
liked all of them and will discuss them later (14/10). Still not work until
then.

The requests of 13/10/2026 (detection sensitivity, probable residents in
Home, `/on` and `/off`, the photos piling up, the 40 views managing
themselves, the "maybe" threshold) were answered by the user the same evening
and are backlog 28–32 and R46. The questions of 14/10 at 12:55 were answered
the same day: R42 (b) and backlog 34's Off-asks-first. R42 (b) is built
(`v2026.10.14.3`); R53 step 2's model, DINOv2-small, was the architect's
choice in review 25 — Apache-2.0, nothing for the user to weigh — built in
`v2026.10.15`. It costs about 120 ms a dog in the live loop on the M900,
where MobileNet, tied on every measurement, would cost about 12; the user
may still prefer it (ARCHITECTURE 20).
