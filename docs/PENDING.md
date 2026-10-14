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
- **R48 — backlog 28 is built but held** (review 20, 14/10/2026): choose
  (a), (b) — recommended — or (c) in BACKLOG 2. Whatever the choice, first
  delete on Gustavo's page, in **Waiting**, the seven faces of Izabel: the
  photos starting `c58c97`, `e18912`, `b3f8b9`, `69f368`, `1bbfa1`, `860372`
  and `eedcf9`, which on 14/10 were at Waiting positions 11, 12, 17, 20, 21,
  22 and 26 (the picture sent in the conversation of review 20). Then the
  architect releases 28 and runs `settle_waiting.py`.
- **R42**: accept the corner, or count people with YOLO (recommended)
  (BACKLOG 2).
- **Which documents go into the EPUB** (12/10/2026). The user will read every
  document and say which go in. Already decided by them: a file that only
  holds what Claude and the developer exchange stays out. Today
  `tools/make_epub.py` takes every `.md` at the root and in `docs/`, so
  `PROCESS.md`, `BACKLOG.md`, `PENDING.md`, `HISTORY.md` and `HANDOFF.md` would
  go in; when the list comes, `ORDER` becomes the list of what goes in, not
  just the order.

## Decided, not yet done

None. (The split of the context documents was done on 12/10/2026.)

## Open discussions

None. The requests of 13/10/2026 (detection sensitivity, probable residents in
Home, `/on` and `/off`, the photos piling up, the 40 views managing themselves,
the "maybe" threshold) were answered by the user the same evening and are
backlog 28–32 and R46. The question about competitors was answered in the
conversation; its one new idea is backlog 33 (proposto).
