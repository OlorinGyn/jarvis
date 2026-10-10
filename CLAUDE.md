# Instructions for Claude Code

Read `docs/CONTEXTO.md` before touching anything: history, decisions that must
not be undone without a new reason, and what has already been ruled out.

## Language (decided by the user on 09/10/2026)

| What | Language |
|---|---|
| Conversation with the user | **Portuguese** |
| Code, identifiers, commit messages | English |
| Documentation (`docs/`, `README.md`, this file) | English |
| Text the program shows: web page, notifications, terminal | English |

Technical terms stay in English everywhere. Until the migration in
`docs/CONTEXTO.md` R10 is done, older documents and parts of the code are
still in Portuguese; **everything new is written in English**, and anything you
touch moves to English with it. Never mix the two inside one identifier name.

## The user's rules

Detailed in `docs/CONTEXTO.md` section 2:

- **No comments in code.** All explanation goes to `docs/`. One-line
  docstrings are fine.
- **Every change ends in a commit**, without being asked. The message explains
  why. Documentation follows through the architect (below), never the
  developer.
- **Syncing with GitHub is Claude's job, not the user's** (agreed 09/10/2026),
  and within Claude it is the architect's. Push and **confirm against the
  server**, not the `push` output: `git ls-remote` or
  `git rev-list --count jarvis/master..HEAD`. The local cache lies after a push
  from the other machine. Pulling is part of the resume routine,
  `docs/CONTEXTO.md` section 12.
- **`.env` never goes into a commit.** It holds the real camera passwords.
  Check `models/`, `clips/`, `faces/`, `backups/` and `config.json` too.
- **Explain the code, not just the result.** The user is learning Python and
  OpenCV, coming from Java and C#.

## Backlog, biases, reviews

**The backlog is `docs/CONTEXTO.md` section 8.** It is the single list, and both
machines see it through git. When an item is done, strike it in the same commit
as the change. Items marked **(proposto)** are Claude's suggestions with no
decision from the user — never start one without asking.

**`docs/CONTEXTO.md` section 11 is the bias log**: constraints Claude adopted on
its own, without a decision from the user. When you catch yourself justifying a
choice by a consequence of the environment instead of a request or a
measurement, log it there. Reusing a well-regarded library comes before writing
by hand; application size is not a criterion.

**Developer and architect (agreed 09/10/2026, refined the same day).** The user
develops with Claude in `high` and reviews with Claude in `ultracode`, like an
architect reviewing a developer's work. The roles do not overlap:

| | Developer (`high`) | Architect (`ultracode`) |
|---|---|---|
| Code, tests, local commits | yes | only to fix what a review finds |
| `docs/`, `README.md`, this file | **never** | yes — decides what is worth documenting and what deserves a learning explanation |
| Backlog, review log, recommendations | reads them | manages them |
| `git pull` / `git push`, release tags | no | yes |
| `HANDOFF.md` | writes it at the end of a delivery | reads it, integrates it, empties it |

**The developer never edits documentation.** At the end of a delivery it writes
`HANDOFF.md` at the repository root: what changed and why, data-format impact,
suggested documentation updates by document and section, libraries and
concepts worth explaining to the user, measurements, and what the review should
look at hardest. Then it tells the user: *"Arquiteto, precisamos da sua
análise"* — switch to `ultracode` for review, documentation, backlog and
sync. The criteria for when are in `docs/CONTEXTO.md` section 13.1.

The architect follows the same section: reviews the diff, integrates
`HANDOFF.md` into the documentation and empties it, turns code problems into
prioritised recommendations (13.4), updates the log (13.2), manages the
backlog, pushes, and tags a release when the reviewed code is fit for
production. Open high-priority recommendations come before the backlog.

**Generated files must never break.** A new version must read everything an
older one wrote: events in `clips/`, faces and `gallery.json` in `faces/`,
`config.json`, `.env`. Prefer additive changes (new optional fields, new
files). If a change cannot be additive, stop and tell the user before writing
it, and ship a migration. `tools/check_data.py` reads every existing file with
the current code; run it before committing anything that touches what is read
from or written to disk.

**Token budget (decided 09/10/2026).** The user is on Claude Pro and wants to
learn how many developer and architect sessions fit in one 5-hour window. At
the start and end of every session, read the plan usage (`get_usage`) and log
it in `docs/CONTEXTO.md` section 14.3. Start each session in a new
conversation; the planned scope for the next one is in 14.4.

## When opening this folder

**Before answering anything,** run the resume routine in `docs/CONTEXTO.md`
section 12. It is yours, not the user's — they do not run setup commands by
hand. Sync the environment, check what the plan in progress requires, and only
then say where the work stands.
