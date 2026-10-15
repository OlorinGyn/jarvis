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
  (`http://192.168.0.19:8765` today — the M900's address is .19 now, not
  .18). If it still sleeps, the event log names the caller again. Once it
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
  (`http://192.168.0.19:8765` since 15/10; the address comes from DHCP).
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
  bench: each is the same picture as a sighting of the two dogs together. R53 step 2 migrates them to the new model as they are, so
  deleting them still matters, before or after. **The once-only settle waits
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
  is sure" shows production's table (77 of 80 sure at 0.30, 66 at 0.40, no
  wrong answer) — **choosing a threshold is the user's**, and the table is
  optimistic until R55 (ARCHITECTURE 10.15). A "hidden person" message for a
  scene with only residents and dogs goes to the architect, with its time.

## Decided, not yet done

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
choice in review 25 — Apache-2.0, nothing for the user to weigh — and the
user may still prefer MobileNet's 12 ms (ARCHITECTURE 20).
