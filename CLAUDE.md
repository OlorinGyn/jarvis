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
- **Every change ends in a commit plus updated documentation**, without being
  asked. The message explains why.
- **Pushing is your job, not the user's** (agreed 09/10/2026). When a feature
  is done or commits pile up, push — and **confirm against the server**, not the
  `push` output: `git ls-remote` or `git rev-list --count jarvis/master..HEAD`.
  The local cache lies after a push from the other machine. Pulling is part of
  the resume routine, `docs/CONTEXTO.md` section 12.
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

**Developer and architect (agreed 09/10/2026).** The user develops with Claude
in `high` and reviews with Claude in `ultracode`, like an architect reviewing a
developer's work. While developing, **tell the user when there is enough for a
review** and ask them to switch to `ultracode` and run the code review — the
criteria are in `docs/CONTEXTO.md` section 13.1. While reviewing, follow the
same section: fix documentation on the spot, turn code problems into
prioritised recommendations (13.4) and update the log (13.2). Open
high-priority recommendations come before the backlog.

## When opening this folder

**Before answering anything,** run the resume routine in `docs/CONTEXTO.md`
section 12. It is yours, not the user's — they do not run setup commands by
hand. Sync the environment, check what the plan in progress requires, and only
then say where the work stands.
