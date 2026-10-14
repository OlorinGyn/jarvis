# J.A.R.V.I.S. — how the work is done

The rules of the work between the user, the developer and the architect,
whatever the item. What the project is and what was decided about it is
`CONTEXT.md`; the work itself — backlog, recommendations, the next
sessions — is `BACKLOG.md`; what is not work yet is `PENDING.md`; the past is
`HISTORY.md`. Split out of `CONTEXT.md` on 12/10/2026, when the user asked
that each document carry only what belongs to it; CONTEXT's old section
numbers point here.

---

## 1. How the user works — follow this

Rules the user set explicitly:

**No comments in code.** None. Every explanation lives in `docs/`; one-line
docstrings are accepted. Check before committing:

```bat
uv run python -c "import tokenize,pathlib; print(sum(sum(1 for t in tokenize.generate_tokens(tokenize.open(f).readline) if t.type==tokenize.COMMENT) for d in ('src','tools') for f in pathlib.Path(d).rglob('*.py')))"
```

It looks only at `src/` and `tools/`; `.venv` holds thousands of third-party
comments.

**Every change ends in a commit**, without being asked. The message explains
**why**, not only what. **The developer never updates documentation:** it
writes `HANDOFF.md`, and the architect integrates it (3.1, `CLAUDE.md`).

**Generated files must never break** (the user, 09/10/2026). A new version
reads everything an older one wrote. Changes are additive; anything else is
announced to the user first and ships with a migration. `tools/check_data.py`
proves it, and every production update runs it (ARCHITECTURE 19).

**Before committing, check that `.env` did not go in.** It holds the real
camera passwords, which once leaked into examples in the documentation and
had to be fixed. Check `models/`, `clips/`, `faces/`, `dogs/`, `reports/`,
`backups/` and `config.json` too — all are in `.gitignore`, but a careless
`git add -A` after touching it would take them.

**Explain the code, not only the result.** The user is learning Python and
OpenCV, coming from Java and C#. They asked for concise answers about options
and tangents, but **never** skimp on explaining code or a command — they
complained when that was cut too short. Each delivery's concepts go to
`PYTHON.md`.

**Language** (the user, 09/10/2026): only the conversation with the user is
in Portuguese. Code, identifiers, commits, documentation and every text the
program shows are in English; the raid log scripts are in both. The table is
in `CLAUDE.md`.

## 2. Resume routine — run this when opening the project

**This section is for Claude, not the user.** The user does not run setup
commands by hand and expects the context to leave any machine ready to
continue. Do it before answering, and report only the result.

### 2.1 Always

```bash
git pull --ff-only
uv sync
```

`git pull` first, because the project is edited on two machines. On a
conflict or divergence, stop and show the user instead of resolving it
alone. `uv sync` because dependencies change between commits.

**Pushing is Claude's job too**, and within Claude the architect's (09/10/2026):
the user no longer pushes or pulls by hand. Confirm against the server, not
the push output:

```bash
git push jarvis master
git ls-remote jarvis -h refs/heads/master
```

or `git rev-list --count jarvis/master..HEAD`. The local tracking ref goes
stale when the other machine pushes, and once made Claude claim there were
pending commits when there were none, and the opposite too. **The remote is
called `jarvis` on both machines** (on a new clone: `git remote rename origin
jarvis`).

**On the M900, check production too:**

```bat
powershell -ExecutionPolicy Bypass -File tools\production.ps1 -Action status
```

Every camera's last frame should be a few seconds old at most. Anything else —
HELD when nobody stopped it, not running, an old frame — goes to the user
before anything else, with the tail of `C:\JARVIS\logs\jarvis.log`.

**Record the usage at the start of the session** (section 4): plan usage
from `get_usage`. The architect writes a row in `HISTORY.md` 14.3 and fills it
in at the end; the developer keeps its numbers for `HANDOFF.md`.

**Check that Python still runs.** If `uv sync` or `uv run` fails with `Failed
to spawn: python` or `WinError 4551`, Smart App Control is blocking an
unsigned interpreter. The way out is in INSTALL 1.2 — the official Python
and a recreated `.venv` — and it is yours: do it before answering.

### 2.2 Check what the item in progress needs

Read `BACKLOG.md` 1 and 3 and find the item in progress. If it has a recorded
precondition, test it **now**, on this machine, and record the result in the
same commit as the next change. (The last one, `pydantic_core` loading under
Smart App Control, passed on both machines: HISTORY 12.2.)

### 2.3 Say where things stand

Then tell the user: where the work stopped, what comes next and whether a
precondition failed. Never ask them to run something you could run. Read the
**open** recommendations (`BACKLOG.md` 2): high-priority ones come before the next
backlog item unless the user says otherwise. The architect also reads
`PENDING.md`: what waits for the user goes into the answer. **If `BACKLOG.md` 3 holds a planned session
for your role, that is the plan** — the architect wrote it with the order and
the reasons. Follow it, and say so when you deviate.

### 2.4 What does not travel through git

| File | Why | Consequence |
|---|---|---|
| `.env` | camera credentials | each machine has its own; `install.bat` creates it if missing |
| `config.json` | the Telegram token and the PIN | **notifications start off on a new machine** |
| `models/` | ~73 MB | downloaded on first use |
| `clips/`, `faces/`, `dogs/`, `reports/` | recordings and galleries | local by nature |

If `config.json` is missing or has no `notify_token`, tell the user — it is
the only thing here that needs them, because the token is a credential only
they have. The chat is found in Settings → Notifications with Find chat.

---

## 3. Developer and architect — the review

### 3.1 How it works — agreed 09/10/2026

The user splits the work into two roles, as in a team:

| Role | Claude's mode | Does |
|---|---|---|
| **Developer** | `high` | implements, tests, commits locally, writes `HANDOFF.md` |
| **Architect** | `ultracode` | reviews, documents, manages the backlog, syncs with GitHub, tags releases |

The developer never edits documentation. At the end of a delivery it writes
`HANDOFF.md` — what changed, data-format impact, suggested documentation by
section, topics worth teaching, what to review hardest — and asks: *"Arquiteto,
precisamos da sua análise."* The architect decides what is worth documenting,
integrates it, empties the file, pushes, and tags a release when the code is
fit for production. Production only ever runs tags (ARCHITECTURE 18.7), named
`vYYYY.MM.DD`; a second release on the same day is `vYYYY.MM.DD.2` —
`production.ps1` sorts tags as versions. The developer's session is the `dev`
skill (`.claude/skills/dev/SKILL.md`), which the architect maintains. The
automatic handover between the two sessions is in `CLAUDE.md`.

**When to review** — any of:

- a backlog item or stage is finished;
- three or more code commits since the last review;
- any change in **concurrency** (threads, shared native objects), **network
  exposure**, **the user's files** (moving, deleting) or **credentials** —
  even one commit;
- before leaving the system running alone for days.

**The architect reviews the range since the last review** — the whole diff,
not the summary — and checks what the documentation claims against the code
and the real system (logs, files, measurements). It fixes on the spot what is
text or wrong documentation, and code only to fix what the review finds,
reproduced by a test first. What is left in code becomes a **recommendation**
(`BACKLOG.md` 2) for the developer. It writes the review's own section in `HISTORY.md`
13 and its row in 13.2 there. When the range or the review touches `docs/`,
`uv run python tools/check_doc_refs.py` must exit 0: every `<DOC> <section>`
reference lands on a heading (review 17).

**The developer reads the open recommendations** before starting (2.3). When
it implements one, it says so in `HANDOFF.md` with the commit; the architect
marks it done and moves its text to `HISTORY.md` 13.4. If it disagrees with
one, it does not ignore it: it writes why, and the user decides.

### 3.2 Review log

The table of every review is `HISTORY.md` 13.2. **The last review, 22, covers
up to `706883b`** (developer 20's handoff; no release); the next starts from
the commit after it.

### 3.3 Each review in full

`HISTORY.md` 13.3 to 13.23, one section per review (13.16 is the reading of
the bad-detection reports); the next one is 13.24.

---

## 4. Sessions and token budget

### 4.1 Why — decided by the user on 09/10/2026

The plan is **Claude Pro**: a limit that resets every **5 hours**, and a
weekly one. The user wants to learn how many developer and architect sessions
fit in one 5-hour window, so each session can be scoped to use it well
instead of stopping halfway. A row is a measurement, never a guess.

### 4.2 How to measure

At the start and the end of every session, read the plan usage with the
desktop app's `get_usage` (5-hour %, weekly %, reset) and the conversation's
context size. A session is one role's stint, even when two happen in one
conversation. The architect fills its row in `HISTORY.md` 14.3; the developer writes
its numbers in `HANDOFF.md`, and the architect copies them there.

What drives the cost: every turn re-sends the whole conversation, so a long
conversation makes every later step expensive (~50k of context are tool
definitions alone). **Start each session in a new conversation** — the resume
routine reads what it needs from disk, which is why the roles hand over
through files. Measured so far: a developer delivery costs 10–20 points of the
5-hour window and about 2 of the week; a review with its release and deploy,
5–10 and about 1.

### 4.3 Log

Every session's row, with what it cost: `HISTORY.md` 14.3.

---

## 5. Claude's biases — constraints the user never chose

This section exists because the user asked **"where can I find these biases
you may have created?"** The honest answer was: nowhere. `CONTEXT.md` 3 records
decisions, but a decision has an author. What was missing was a record of what
Claude started treating as a rule **with nobody having decided it**.

### 5.1 How these biases form

The pattern is always the same, and easy to miss:

1. A real constraint appears — environment, hardware, a concrete error.
2. Claude works around it. Right so far.
3. The workaround is repeated in later decisions **as if it were a goal**.
4. The documentation starts justifying it, and the accident becomes a
   principle.

Step 3 is invisible because step 2 was right. The warning sign is a
justification that describes a consequence as if it were an aim — "the
project stays at two dependencies" was exactly that.

### 5.2 How to audit

Look for justifications that cite neither a request from the user nor a
measurement:

- phrases like "so as not to bring in", "to keep", "instead of depending on",
  "avoids the dependency" in `docs/`;
- any number treated as a target (dependency count, file size, lines) that
  does not appear as a measurement;
- anything written by hand that exists ready-made in a well-regarded library.

The user's rule, 09/10/2026: **reusing code, especially well-regarded
libraries, is always the best path.** Application size is not a criterion;
the efficiency and quality of the dependencies are.

### 5.3 Log

**Dependency minimalism — corrected 09/10/2026.** PyTorch broke under Smart
App Control (an unsigned DLL, `WinError 4551`). Switching to `cv2.dnn` was
right. The mistake was generalising: "fewer dependencies" became a design
criterion, and Claude started writing by hand things that existed ready-made.
It cost a whole session debugging TLS to reimplement what `requests` already
delivers (ARCHITECTURE 12.5). The correct rule is narrower: **be wary of large
binary dependencies**, because that is what broke the deploy. A pure-Python or
data-only package does not have that problem and needs no justification.

**A HighGUI interface — recognised and corrected 09–10/10/2026.** The OpenCV
window was the natural path while the program was only a camera viewer. It
became `ui.py` with 616 lines and 60 primitive drawing calls, and OpenCV has
no widgets: no pasting, no video, no scrolling lists, no accents. It had
already bent decisions — the settings tab opened `config.json` in an editor
because a token could not be pasted into the window. Worse was what it
dragged along: **the surveillance loop rode on the window** — `cv2.waitKey`
set the pace and closing the window stopped recording. The user saw it
themselves when saying they would not always want to watch live. The core was
separated (ARCHITECTURE 15) and the window removed on 10/10 (`v2026.10.10.4`).
**A correction of merit:** when proposing this, Claude said the M900 spent CPU
drawing for nobody. True, but measured afterwards it was small — about 6 % of
a frame. The gain of the separation is not CPU; it is surveillance that does
not die with the window.

**No tests — never discussed, corrected 10/10/2026.** 2,600 lines and no
tests; Claude never proposed them and the user never refused. R6 added them;
there are 160 on 12/10 (ARCHITECTURE 19.5).

**SFace because it came with OpenCV — logged 14/10/2026.** YuNet and SFace
were chosen over InsightFace for being built into OpenCV (CONTEXT 3), and
measured only on good frontal faces. Nobody compared them with stronger
models on this house's cameras, which look down on heads. R49 is what it
cost: the top of a head passed as a face and drew wrong "sure" matches. The
user's answer: much better models will be used if they exist.

**Everything in one process — a consequence, not a choice.** Capture,
detection, recording, faces, the web and the Telegram poller share one Python
process, with threads for whatever must not block. It works with 2 cameras;
it was not assessed for more, and the GIL stands in the way. Only recorded;
not a problem today.

---

## 6. Raid log — the comic script of each release

**The user's idea, 10/10/2026, revised the same night.** Every release gets an
issue of a comic: the architect and the developer talking through what really
happened in that version, simplified. **The architect writes the script, not
the drawing**; the user draws it later with a tool made for comics. A first
issue was drawn here as SVG and printed to PDF, and the user replaced it with
scripts after seeing what a drawn issue costs in tokens.

Two files, and only two: `docs/raidlog/script.en.md` and
`docs/raidlog/script.pt.md`, the same story panel for panel — the one
document kept in both languages. Each opens with the series bible (cast,
style, the truth rule: simplified, never invented); a new issue is appended to
both when the architect tags a release, from that version's `HANDOFF.md`,
review and commits.

| Issue | Version | Title | Script |
|---|---|---|---|
| 1 | `v2026.10.09` | The First Night Shift / O Primeiro Turno da Noite | written |
| 2 | `v2026.10.10` | The Dog Who Wore a Person's Face / O Cachorro com Cara de Gente | written |
| 3 | `v2026.10.10.2` | The Watcher's Instruments / Os Instrumentos do Vigia | written |
| 4 | `v2026.10.10.3` | The House Gets a Front Desk / A Casa Ganha uma Recepção | written |
| 5 | `v2026.10.10.4` | The Lock and the Album / A Tranca e o Álbum | written |
| 6 | `v2026.10.10.5` | The Safety Net / A Rede de Proteção | written |
| 7 | `v2026.10.10.6` | The Favourite / A Favorita | written |
| 8 | `v2026.10.10.7` | Mirana and Aurora / Mirana e Aurora | written |
| 9 | `v2026.10.11`, `.2` and `.3` | The Front Desk Learns Manners / A Recepção Aprende Modos | written |
| 10 | `v2026.10.11.4` | The Evidence Box / A Caixa de Provas | written |
| 11 | `v2026.10.11.5` and `.6` | Second Chances / Segunda Chance | written |
| 12 | `v2026.10.12` | The House Learns Who Lives Here / A Casa Aprende Quem Mora Aqui | written |
| 13 | `v2026.10.12.2` | The Owner Is Not a Dog / O Dono Não É Cachorro | written |
| 14 | `v2026.10.12.3` | Every Name in English / Todo Nome em Inglês | written |
| 15 | `v2026.10.12.4` | The Signature at the Door / A Assinatura na Porta | written |
| 16 | `v2026.10.13` | The Off Switch / O Botão de Desligar | written |
