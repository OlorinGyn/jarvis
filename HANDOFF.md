# Handoff - developer to architect

Developer session 15, 12/10/2026, planned in `docs/BACKLOG.md` 3. Both items
of the plan are done, in the planned order.

## 1. Items done

### R10 — the file names and the two tools' text (closes R10)

- **`f855a9e` — the renames, with `git mv`.** `git show --stat` records each
  one as a rename, so `git log --follow` keeps the history:

  | Old | New |
  |---|---|
  | `docs/ARQUITETURA.md`, `docs/INSTALACAO.md`, `docs/CONTEXTO.md` | `docs/ARCHITECTURE.md`, `docs/INSTALL.md`, `docs/CONTEXT.md` |
  | `tools/diagnostico.py`, `refazer_rostos.py`, `verificar_clipes.py` | `tools/diagnose.py`, `rebuild_faces.py`, `check_clips.py` |
  | `tools/gerar_icone.py`, `gerar_epub.py`, `criar_atalho.ps1` | `tools/make_icon.py`, `make_epub.py`, `create_shortcut.ps1` |
  | `instalar.bat`, `jarvis_vigilancia.bat` | `install.bat`, `jarvis_headless.bat` |

  Every reference changed in the same commit: the docstrings in `src/` and
  `tools/`, `make_epub.py`'s order list, `production.ps1`'s Smart App Control
  message ("See INSTALL 1.2"), `CLAUDE.md`, the `dev` skill, `README.md` and
  every document in `docs/`. The short names in references changed too
  (`ARQUITETURA 18.7` → `ARCHITECTURE 18.7`, `CONTEXTO 10` → `CONTEXT 10`),
  including in `HISTORY.md`. Exceptions on purpose: in `BACKLOG.md`, the R10
  row, R10's paragraph and section 3 still use the old names, since they
  describe this rename; the architect strikes them.
  The file trees in `ARCHITECTURE.md` 3 and `CONTEXT.md` 9 and the command
  list in `CONTEXT.md` 10 were realigned after the names got shorter.
- **The code's references to CONTEXTO's moved sections** now point where the
  text lives: backlog 22, 23 and 25 (f) → `HISTORY.md` 8 (`dogs.py`,
  `reports.py`, `modes.py`, `bot.py`, `dog_crops.py`, `dog_tuning.py`); R34 →
  `HISTORY.md` 13.13 (`devices.py`); R17 → `HISTORY.md` 13.6 (`replay.py`);
  R30 (b) → `BACKLOG.md` 2 (`face_tuning.py`).
- **`jarvis_vigilancia.bat` stays one release as a two-line shim** that calls
  `jarvis_headless.bat`. Nothing on the M900 calls it (the startup task runs
  `pythonw -m jarvis --headless` itself; the only `.lnk` on the Desktop is the
  test copy's, pointing at `jarvis.bat`), but the development PC was not
  checked. Since the shim is a new file at the old path, git shows
  `jarvis_headless.bat` as added, not renamed. **Delete the shim in the
  release after the next one.**
- **`tools/check_doc_refs.py` (new)** is the check the plan asked for: every
  `<DOC> <section>` reference (`ARCHITECTURE 18.7`, `docs/INSTALL.md section
  8`, `` `PROCESS.md` 3 ``, `sections 5, 8 and 19`) in the documents,
  `README.md`, `CLAUDE.md`, the skills, `src/` and `tools/` must land on a
  numbered heading of that document. The documents are discovered from
  `docs/*.md`, so it follows any future rename. It found 278 references; the
  same **3 fail before and after the rename**, all wording in `HISTORY.md`,
  none introduced here:
  - line 10: `"CONTEXT 13.6" is now "HISTORY 13.6"` — a historical mention of
    an old section number;
  - line 269: `(ARCHITECTURE 7.12, 13.16 below)` — `13.16` is HISTORY's own
    section, but the list reads as ARCHITECTURE's; "HISTORY 13.16" or
    "13.16 below" in its own parentheses would fix it;
  - line 1025: `CONTEXT.md 14.3` — where the usage rows used to live.
  Rewording those three lines makes the check exit 0.
- **`aa6e243` — the text in English.** `install.bat`, `jarvis.bat` and
  `jarvis_headless.bat` print English; `jarvis_headless.bat` passes
  `--headless` instead of `--sem-janela` (which `cameras.py` still accepts,
  `HEADLESS_FLAGS`). `diagnose.py` text and identifiers in English (`comando`
  → `command`, `tentar` → `attempt`, `teste_local` → `local_test`,
  `testar_variantes` → `try_variants`...). The other renamed tools moved to
  English with them: `rebuild_faces.py`, `check_clips.py` (`[YYYY-MM-DD]`),
  `make_icon.py`, `create_shortcut.ps1` (the shortcut's description is now
  "J.A.R.V.I.S. home surveillance"), and `make_epub.py` (`ORDEM` → `ORDER`,
  `SAIDA` → `OUTPUT`...). **The EPUB is now `docs/epub/JARVIS -
  Documentation.epub`, `lang=en`**; the script still deletes any other
  `.epub` in that folder, so the old Portuguese-named one goes on the next
  run. Which documents it carries is unchanged and still waits for the user.

### R45 — one pass over the sightings per batch (closes R45)

- **`351bc23`.** `Gallery._merge` no longer rewrites sightings. It records
  `{old id: new id}` in `self.repoints`; `save()` hands the whole map to
  `_repoint_sightings` — one pass over the folder — and then writes
  `gallery.json`, the same order as before (sightings first). A chain (a into
  b, then b into c) is resolved when it is recorded, so every sighting points
  at the last entry. `load()` resets the map, so a merge from an operation
  that raised before saving is never applied to the sightings. `DogGallery`
  inherits it unchanged. Not bounded by `first_seen`, as the recommendation
  said.

## 2. Data-format impact

None. Sightings, `gallery.json` and every other file keep their format; only
when the sightings are rewritten changed. `check_data.py` on the test copy:
224 events, 7 people and 20 face sightings, 22 dogs and 23 dog sightings,
1 report, `config.json` 11 keys — "Every file is readable by this version."

Production: `production.ps1` refers to no renamed file except in a message
string, and builds its own Desktop `.url`, so an update to a tag with these
commits needs nothing special. `C:\JARVIS` will get the new file names at
checkout.

## 3. Suggested documentation updates

- **`ARCHITECTURE.md` 3 (file layout) and `CONTEXT.md` 9 (repository map):**
  add `tools/check_doc_refs.py`, and `jarvis_vigilancia.bat` as "old name,
  calls `jarvis_headless.bat`; removed after one release". `ARCHITECTURE.md`
  3's `docs/` tree lists only five documents and calls `CONTEXT.md` "rules,
  decisions, backlog, plan" — out of date since the split (PROCESS, BACKLOG,
  PENDING are missing).
- **`CONTEXT.md` 10 (commands):** `uv run python tools/check_doc_refs.py` —
  run after moving or renumbering a section. And the EPUB's new file name.
- **`PROCESS.md` 3.1 or the architect's review checklist:** run
  `check_doc_refs.py` in every review that touches `docs/`.
- **`ARCHITECTURE.md` 15 / 17 tables that mention `jarvis_headless.bat`
  (`--headless`; "the old `--sem-janela` still works"):** still true.
- **`ARCHITECTURE.md` (gallery / sightings section, wherever merges are
  explained, near 17.10 / 20):** merges now repoint sightings once per save.
- **`HISTORY.md` lines 10, 269, 1025:** the three references the check
  flags (section 1).
- **`BACKLOG.md`:** strike R10 and R45; the R10 row and paragraph still name
  the old files.
- **`.gitignore`** still has Portuguese comments (`rostos detectados e
  galeria`, `copias de seguranca...`, `modelos ONNX...`, `epub gerados...`,
  `registro do programa...`). Not touched: outside the plan. A one-minute
  item if you want R10 fully closed.
- `jarvis_headless.bat` says "To see the cameras: http://127.0.0.1:8765",
  but the test copy listens on 8766. Pre-existing; the `.bat` cannot know the
  port without reading `.env`. Left as it was.

## 4. Worth explaining to the user

- **`git mv` and rename detection.** Git does not store renames: it stores
  snapshots and, when showing history, guesses that a deleted file and an
  added one with ≥ 50 % similar content are the same file. That is why the
  renames went in one commit with almost no content change, and the
  translation in a separate one — translated `diagnose.py` would no longer
  look 50 % similar. `git log --follow docs/ARCHITECTURE.md` walks across the
  rename. (Java/C#: like an IDE's "Rename file" refactoring, except the VCS
  infers it afterwards.)
- **Deferring work to a single flush (R45).** `_merge` no longer does the
  I/O; it records intent in a dict, and `save()` applies it once — the same
  idea as a Unit of Work / `DbContext.SaveChanges()` in Entity Framework,
  where changes accumulate and one call writes them. The dict comprehension
  `{old: target if new == source else new for old, new in ...}` rewrites the
  map so chains collapse.
- **`monkeypatch.setattr(faces.Path, "read_text", counting)`** in the new
  test: pytest replaces a method on a class for the duration of one test, to
  count calls — like a Mockito spy, but on the real class, undone
  automatically (`monkeypatch.undo()` does it early).
- **Batch files and `%~dp0`** — "the drive and folder of this script", so a
  `.bat` works from any current folder; `call other.bat %*` runs another
  batch and comes back, passing every argument. Without `call`, cmd would
  jump to the other file and never return.

## 5. Measurements

- R45: a batch of 5 unnamed crops with 6 sighting files — each file read
  **5 times before, 1 time after** (measured by running the new test against
  the old `faces.py`). In general: N entries merged → N passes before, 1
  after.
- Tests: 174 → **176 passed** (`uv run python -m pytest`, ~63 s).
- Comments in code: 0.
- `diagnose.py --local`: 7776000 of 7776000 bytes decoded.
- `check_clips.py 2026-10-12`: Back 0 of 2, Front 0 of 6 clips damaged.
- `jarvis_vigilancia.bat` → `jarvis_headless.bat` started the test copy
  (port 8766 listening within 2 s, both cameras ok) and `--stop` stopped it
  cleanly.
- `check_doc_refs.py`: 278 references found, 3 broken before and after.

## 6. Review hardest

- **The bulk rename in `HISTORY.md` and the other documents.** It was a
  word-boundary `sed` of `ARQUITETURA`/`INSTALACAO`/`CONTEXTO` and the file
  names. Historical sentences in `HISTORY.md` now say `CONTEXT.md` where the
  file was `CONTEXTO.md` at the time; I judged a working reference more
  useful than the old name. Revert any you want verbatim.
- **`save()` now does the sightings' I/O.** Every caller of `_merge`
  (`rename`, `assign`, `_absorb`) already ends in `save()` under the lock; a
  caller that merged and did not save would now leave sightings pointing at a
  removed entry (before, they were repointed even without a save). There is
  none today.
- **`self.repoints` is set in `load()`.** Any code that builds a Gallery
  without `__init__`/`load()` would fail in `_merge`; none does.
- The `.bat` files were rewritten whole (CRLF kept in the working tree).
  `install.bat` was not run end to end — it installs software and creates a
  Desktop shortcut; only its text changed.

## 7. Not done

Nothing of the plan. Not started, as planned: R42 (the user's decision), R30
(b) (needs a second named person), and the (proposto) items.

## 8. Usage

| | 5-hour window | Weekly | Context |
|---|---|---|---|
| Start (≈ 20:46) | 42 % | 6 % | 70k tokens |
| After R10 | 48 % | 7 % | 151k |
| End | 49 % | 7 % | ≈ 175k |

R10 cost about 6 points, R45 about 1, this handoff under 1. The window resets
at 00:40 (03:40 UTC).
