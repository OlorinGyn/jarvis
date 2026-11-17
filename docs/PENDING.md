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
- **Misfiled dog views** (R53): **done, 17/11** — the user said "delete
  them". Of the thirteen, ten had already left the current gallery
  (`gallery_dinov2_small.json`; Aurora and Mirana held 40 chosen, none
  waiting — the list was read from the old `gallery.json`, kept for a
  rollback). The three left, `257e9a` (Aurora) and `554245` (Mirana),
  both dogs in one crop, and `6b3d84` (Mirana), a dark dog from behind
  blurred in sunlight, were deleted through the page's own API, after a
  copy of `dogs/` in `C:\JARVIS\backups\misfiled_dogs_20261117-143202`.
  Gustavo's own five head-tops in his Chosen stay; backlog 45 decides
  them.
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

- **`v2026.10.16` on the phone and the M900** (backlog 40, R60): nothing
  the mode wants is dropped any more. **The chat will hold about twice the
  messages and the phone will ring less** — in the last 24 hours before it,
  100 messages instead of 54, 42 rings instead of 54 (ARCHITECTURE 12.11):
  the first message of an incident rings, another camera or more people at
  once ring, the rest arrive with no sound; at most one ring in 30 s, and a
  text "… — sent silently above" names what came inside. A camera with no
  picture for a minute sends "Back: no picture since HH:MM:SS", and its
  return "picture back"; the switch is in Settings → Notifications. The
  design is the architect's, from the user's principles: **the user may
  veto any part of it**, and a ring that should not have rung, or a silent
  message that should have, goes to the architect with its time.

- **`v2026.10.16.2` on the M900** (R61, item 7 part 1): nothing to see on
  the page. A camera back after an hour or more now reads "picture back,
  18 h 5 min without" instead of minutes. The release carries tracking's
  library, not used yet; its update ran the new warm-up before stopping
  production (ARCHITECTURE 18.7).

- **`v2026.10.16.3` on the M900** (item 7 part 1): nothing to see on the
  page, no message changes. Each new event's JSON records its tracks — what
  the next session measures R59's rule on, after a day of them.

- **`v2026.11.17` on the phone** (backlog 41, R63, R62): in Home **about a
  third of the messages** — 98 a day to 35 on the month. Per camera, person
  events less than 5 minutes apart are one visit: once you are recognised,
  a faceless person alone in that visit sends nothing (only a recording);
  after the visit's first message only news goes — more people at once, a
  face not yet seen in it; the household's dogs boxed as people send
  nothing. A stranger whose face shows, or who comes beside someone, still
  does. A message that fails to send is tried again for about two
  minutes, so a rare one may arrive twice. **What goes to the architect,
  with its time:** a stranger who did not reach the phone, or a message
  that clearly repeats one of the same visit. The log names every message
  not sent and why (`skipped: visit (…)`).

- **`v2026.11.17.2` on the phone and the M900** (backlogs 42 and 44): the
  Dogs tab stops filling with Aurora and Mirana — a crop that is probably
  one of them is a sighting that reads "probably Aurora" in Recordings and
  makes no card; a card is now a dog the gallery cannot place. New people
  read "Visitor N" on People and in the message ("Front: Visitor 12,
  unknown face"); renaming the card is naming them. A visitor not seen for
  60 days is forgotten with its photos, its recordings kept (the first
  ones in December). Since review 34, 14 of the user's photos are no
  longer in Izabel's entry, so "Izabel recognized" for the user should
  stop. **What goes to the architect:** a dog card that is clearly Aurora
  or Mirana, or "Izabel" named for the user, with its time.

## Decided, not yet done

- **The cleaning on production** (backlog 43, applied directly with a
  backup — the user's choice of 17/11): built; waits for backlog 45's
  quality cut, the user's answer to its two wrong moves (BACKLOG 3).
  The cut itself waits for one more measurement, a face-quality model
  (the user's choice in review 34, HISTORY 13.36); the 18 views of
  someone else are already gone.
- **Tracking** (16/10/2026) is work now: BACKLOG 1, item 7. Part 1 is
  done (`v2026.10.16.3`, ARCHITECTURE 7.16); part 2's first piece, R59's
  rule from the tracks, is done as backlog 41 (a) (`v2026.11.17`). Item 40
  is done (`v2026.10.16`).
- **Backlog 28's once-only settle on production** (`tools/settle_waiting.py`,
  the user's choice of 13/10: what the rule leaves is deleted): the dog
  views are gone (above), and the user said to run it on 17/11; held by
  the architect until backlog 45's cut, because the 40-view rule keeps
  the most varied views, not the best, and could drop an impeccable view
  for a poor one. The EPUB's documents were chosen by the user on 14/10/2026 —
ARCHITECTURE and PYTHON only — and `tools/make_epub.py` follows it (CONTEXT
10); the EPUB itself is built when the user asks.

## Open discussions

**Messages arrive late (the user, 18/10/2026: "it takes long to notify").**
In Home every message waits for the clip to close and its face scan:
median about 30 s from the event's start, minutes when scans queue behind
a busy visit (9 min at worst on 17–18/10; HISTORY 13.33). Backlog 41 cuts
the messages, not the scan (built, `v2026.11.17`). **The architect's next
step:** measure the delays on the month again and propose — the face checked
on the first closed segment while the event still records, and no scan for
an event whose visit can no longer change a message. Not work yet.

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
