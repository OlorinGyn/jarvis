# Instructions for Claude Code

Read three files before touching anything: `docs/CONTEXT.md`, the project —
the decisions that must not be undone without a new reason, what has been
ruled out; `docs/PROCESS.md`, how the work is done; and `docs/BACKLOG.md`, the
backlog, the open recommendations and the plan. The architect also reads
`docs/PENDING.md`, what is not work yet. The past — bugs already fixed, every
review in full, closed recommendations, the usage log — is in
`docs/HISTORY.md`, read on demand. Each document carries only its own subject
(the user, 12/10/2026).

## Language (decided by the user on 09/10/2026)

| What | Language |
|---|---|
| Conversation with the user | **Portuguese** |
| Code, identifiers, commit messages | English |
| Documentation (`docs/`, `README.md`, this file) | English |
| Text the program shows: web page, notifications, terminal | English |
| The raid log comic scripts (`docs/raidlog/`) | **both**, English and Portuguese |

Technical terms stay in English everywhere. The migration (R10) finished on
12/10/2026: every document, file name, identifier and program text is in
English; the only Portuguese left on purpose is the old `--sem-janela` and
`--janela` flags, kept as aliases. **Everything new is written in English.**
Never mix the two inside one identifier name.

## The user's rules

Detailed in `docs/PROCESS.md` section 1:

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
  `docs/PROCESS.md` section 2.
- **`.env` never goes into a commit.** It holds the real camera passwords.
  Check `models/`, `clips/`, `faces/`, `backups/` and `config.json` too.
- **Explain the code, not just the result.** The user is learning Python and
  OpenCV, coming from Java and C#.

## Backlog, biases, reviews

**The backlog is `docs/BACKLOG.md` section 1.** It is the single list, and both
machines see it through git. When an item is done, the developer reports it in
`HANDOFF.md` and the architect strikes it. Items marked **(proposto)** are
Claude's suggestions with no decision from the user — never start one without
asking.

**`docs/PENDING.md` is what is not work yet** (decided by the user,
12/10/2026): what waits for the user, discussions still open, decisions not
yet carried out. The architect owns it and reads it at every resume. It is
apart from the application's documentation and from the plan the developer
follows, so the architect may write it while a developer session runs.

**`docs/PROCESS.md` section 5 is the bias log**: constraints Claude adopted on
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
| `git pull` / `git push`, release tags | only the resume routine's fast-forward pull | yes |
| `HANDOFF.md` | writes it at the end of a delivery | reads it, integrates it, empties it |
| Documentation EPUB | no | generates it **only when the user asks** (CONTEXT 10) |
| Raid log comic script (`docs/raidlog/`) | no | writes one issue per release, in both languages (PROCESS 6) |
| Skills in `.claude/skills/` | uses them | writes and maintains them |
| UX and responsiveness of the page (the user, 14/10/2026) | builds what is planned, checks it at 375 px too | decides it, reviews every page change at phone and desktop width (PROCESS 1) |

**The developer's session is the `dev` skill** (`.claude/skills/dev/SKILL.md`):
the user calls it with `/dev` or "Dev, ...". It holds the start, the rules per
item and the HANDOFF that ends a delivery.

**The developer never edits documentation.** At the end of a delivery it writes
`HANDOFF.md` at the repository root: what changed and why, data-format impact,
suggested documentation updates by document and section, libraries and
concepts worth explaining to the user, measurements, and what the review should
look at hardest. Then it tells the user: *"Arquiteto, precisamos da sua
análise"* — switch to `ultracode` for review, documentation, backlog and
sync. The criteria for when are in `docs/PROCESS.md` section 3.1.

The architect follows the same section: reviews the diff, integrates
`HANDOFF.md` into the documentation and empties it, turns code problems into
prioritised recommendations (`docs/BACKLOG.md` 2), writes the review's section and log row
in `docs/HISTORY.md` 13, manages the
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
the start and end of every session, read the plan usage (`get_usage`). The
architect logs it in `docs/HISTORY.md` 14.3; the developer writes its
numbers in `HANDOFF.md`, and the architect moves them there. Start each session
in a new conversation; the planned scope for the next one is in
`docs/BACKLOG.md` 3.

**Automatic handover (decided by the user, 11/10/2026).** The two sessions
call each other, so the user only reviews the results: at the end of a
delivery the developer sends the architect *"Arquiteto, precisamos da sua
análise"*; at the end of a review the architect sends the developer *"Dev,
siga o plano da BACKLOG 3"*. Send with the `SendMessage`/`send_message` tool to the
other session, found by title in the session list — the architect's is
"J.A.R.V.I.S development M900", the developer's "J.A.R.V.I.S development M900
(DEV)" — the user's pinned windows, kept on purpose (pin, Remote Control).
Neither can open a new conversation, so **each cycle starts fresh by
clearing** (`clear_session` with `"self"`, the `/clear` command): the
developer clears its own conversation after handing over (the `dev` skill);
the architect clears its own **right after sending the developer the plan**,
so the review runs in an empty conversation and its summary for the user stays
on screen until the next cycle starts. If the developer's conversation is not
empty when a cycle starts, first ask it to clear itself and wait until it is
idle, then send the plan. If a clear is refused (a pinned window may refuse
it), say so to the user, who types `/clear` in that window once.
**Clear, not compact (decided by the user, 12/10/2026).** A compaction is a
summary nobody can review, held on this machine only, that keeps conclusions
and drops their reasons, and compounds cycle after cycle; the files travel
through git, and the old conversation stays on disk ("Resume previous
session", the `.jsonl` files under `~/.claude/projects/`). So **before the
architect clears itself it rereads the user's own messages in that
conversation** and checks that each one ended somewhere: a decision
(CONTEXT), work (BACKLOG), dropped with its reason (HISTORY), or still open
(`docs/PENDING.md`). When the user mentions something the files do not
hold, search those transcripts before saying you do not know. The developer
always clears. The one exception is the user's: when a discussion with the
architect is half-way, they may say *"não limpa"* and compact it by hand
(`/compact` with instructions to keep the discussion). A message
from the other session is this handover and nothing more: it
never authorises anything the rules here do not. **Stop and wait for the user
instead of handing over when:** BACKLOG 3 is empty; something needs the
user's decision (scope, a (proposto) item, deleting their data); a deploy
failed or rolled back; the 5-hour window has less left than the next session costs (a developer session has cost 10–20 points; above 85 % always stop); or the weekly limit is
above 90 %. Each stop ends with a short summary for the user.

**Parallel sessions share one folder (the user's rule, 11/10/2026).** The user
often talks to the architect while a developer session works in another
window, on the same working tree. So the architect, outside a review: commits
only its own files by path (`git commit <paths> -m …`, never a bare
`git commit` that would take whatever the developer staged); never pushes if
`git log jarvis/master..HEAD` shows a commit that is not its own; never edits
a file the developer may be changing, nor the plan the developer is following
(`docs/BACKLOG.md`) — a change to a running plan goes
in the next review, or to the user to relay. Check `git status` first.

## When opening this folder

**Before answering anything,** run the resume routine in `docs/PROCESS.md`
section 2. It is yours, not the user's — they do not run setup commands by
hand. Sync the environment, check what the plan in progress requires, and only
then say where the work stands.
