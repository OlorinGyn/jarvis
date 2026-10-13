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

- **Backlog 25's acceptance on the M900** (BACKLOG 1): mark the user, Mirana
  and Aurora Resident, choose Home, and confirm that a recognised resident
  sends nothing, a person with no face does, and `/away` from the phone
  changes the mode the page shows. Until then production behaves as before:
  Away, people only.
- **Backlog 3's acceptance**: open the page from a phone
  (`http://192.168.0.18:8765`).
- **Backlog 26 and 27 on the phone** (`v2026.10.12.2`): select many unnamed
  dogs and name them at once; Notifications is now inside Settings.
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

None.
