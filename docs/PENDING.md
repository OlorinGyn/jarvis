# Pending — what is not work yet

What the conversations with the user leave open, kept here so that clearing a
conversation loses nothing (`CLAUDE.md`, "Clear, not compact"). The architect
owns this file and reads it at every resume; the developer does not use it.
It is kept apart from the documentation of the application and from the plan
the developer follows, so the architect can write it while a developer
session runs.

An item leaves this file when it becomes a decision (`CONTEXTO.md`), work
(the backlog) or is dropped with its reason (`HISTORY.md`). If the file only
grows, decisions are being postponed.

## Waiting for the user

- **Backlog 25's acceptance on the M900** (CONTEXTO 8). Until then production
  behaves as before: Away, people only.
- **R42**: accept the corner, or count people with YOLO (recommended)
  (CONTEXTO 13.4).
- **Which documents go into the EPUB** (12/10/2026). The user will read every
  document and say which go in. Already decided by them: a file that only
  holds what Claude and the developer exchange stays out. Today
  `tools/gerar_epub.py` takes every `.md` at the root and in `docs/`, so
  `PENDING.md`, `HISTORY.md` and `HANDOFF.md` would go in; when the list
  comes, `ORDEM` becomes the list of what goes in, not just the order.

## Decided, not yet done

- **Split the context documents by subject** (12/10/2026: the user asked that
  each document carry only what belongs to it, and left the format to the
  architect). Target:

  | File | Holds | Read at the resume by |
  |---|---|---|
  | README, ARQUITETURA, INSTALACAO, PYTHON | the application, as now | nobody; on demand |
  | `CONTEXTO.md` | what Claude must know about the project: decisions, limitations, measurements, repository map, commands | both roles |
  | `PROCESS.md` | how the work is done: the user's rules, the resume routine, reviews, handover, token budget, biases, raid log | both roles |
  | `BACKLOG.md` | decided work: the backlog, open recommendations, the next sessions' plan | both; the developer only reads it |
  | `PENDING.md` | this file | the architect |
  | `HISTORY.md` | the past, the usage log included | nobody; on demand |

  Moved sections keep their number in `CONTEXTO.md` with a pointer, as the
  moves to `HISTORY.md` did, so the references in the code still resolve.
  Done by the architect after review 16 and before the next developer
  session, so no plan moves under a running developer. Measure what each
  role's resume reads before and after.

## Open discussions

None.
