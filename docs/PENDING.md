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
  (`http://192.168.0.18:8765`).
- **Backlog 26 and 27 on the phone** (`v2026.10.12.2`): select many unnamed
  dogs and name them at once; Notifications is now inside Settings.
- **Misfiled dog views** (R53, 14/10): on Dogs, Aurora — Chosen 5
  (`89848c`, Mirana at the door) and 6 (`7221b7`, unclear: check it),
  Waiting 5 (`d6bb2c`, Mirana) and 24 (`f530c0`, a man); Mirana — Chosen 33
  (`6b3d84`, brown fur: check it), Waiting 22 (`6f8002`, dark clothing), 25
  (`557fa0`, shoes and a hand), 26 (`108df8`, someone in red) and 29
  (`cc29b3`, Aurora). Positions as listed on 14/10 at 12:30. **The
  once-only settle waits for these too**: it would put the Waiting ones into
  Chosen first. Done on the faces side: the seven head-tops deleted and the
  unnamed entries named (the user, 14/10). Gustavo's own five head-tops in
  his Chosen stay (they match Izabel at 0.29 at most); deleting them is
  optional.
- **`v2026.10.14` on the M900**: the next person events should name Gustavo
  and Izabel more often, sometimes as "probably" (R51); a face message that
  names the wrong person goes to the architect.
- **R42**: accept the corner, or count people with YOLO (recommended)
  (BACKLOG 2).

## Decided, not yet done

- **Backlog 28's once-only settle on production** (`tools/settle_waiting.py`,
  the user's choice of 13/10: what the rule leaves is deleted): the
  architect runs it after the misfiled dog views above are deleted (the
  faces are ready since 14/10). The EPUB's documents were chosen by the user on 14/10/2026 —
ARCHITECTURE and PYTHON only — and `tools/make_epub.py` follows it (CONTEXT
10); the EPUB itself is built when the user asks.

## Open discussions

**Asked on 14/10 at 12:55, to fill the window from 15:00** (an answer may
reach a cleared architect: read it against this list).
1. **R42**: (a) accept the corner, or (b) count people with YOLO
   (recommended).
2. **Backlog 34**: does switching Off ask "are you sure?" first
   (recommended: yes)?
3. **Which (proposto) items become work**: 1 zones per camera, 2 a warning
   when a camera goes down, 33 "Not a dog / Not a person" buttons on the
   Telegram message, 6 search and filter on Recordings. Each is a feature,
   so the user's decision (PROCESS 1).

None. The requests of 13/10/2026 (detection sensitivity, probable residents in
Home, `/on` and `/off`, the photos piling up, the 40 views managing themselves,
the "maybe" threshold) were answered by the user the same evening and are
backlog 28–32 and R46. The question about competitors was answered in the
conversation; its one new idea is backlog 33 (proposto).
