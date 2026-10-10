# Handoff - developer to architect

Developer session 6, 10/10/2026, about 16:10-16:20, on the M900 (`Sasori`),
following CONTEXTO 14.4. **Old conversation again** (context 542k at the
start). Production (`v2026.10.10.5`) was only read: `production.ps1 -Action
status` at the start and the end (healthy) and a listing of its venv for R26.
Nothing was pushed. No command started with `cd`; `uv run pytest` before
every commit.

## 1. Items

| # | Item | Commit | State |
|---|---|---|---|
| 1 | Backlog 21 — favourite photo per person | `85dea38` | done |
| 2 | R26 — `--no-dev` in production's sync | `59d35fd` | done |

**Backlog 21.** `Gallery.set_cover(person_id, index)` stores the chosen view's
portable path as `cover`; only a view with a photo is accepted.
`faces.cover_of(person)` returns it only while it is still one of the person's
views. `remove_view` falls back to the first view with a photo when it removes
the favourite, or drops `cover` when no view has one. A merge keeps the
target's cover (the source and its cover disappear). Web: `POST
/api/persons/<id>/views/<i>/cover` (through the R24 guard), `cover_index` in
the person page; the grid uses the cover when its file exists, otherwise what
it showed before. Page: a star at the top-left of every view with a photo,
gold on the chosen one.

**R26.** `Sync` in `production.ps1` runs `uv sync --frozen --no-dev`.
Reproduced: `C:\JARVIS\.venv` has `pytest` and `httpx2`. A `--dry-run` of the
same command in the test copy lists exactly the dev packages to uninstall,
so the next deploy removes them from production too.

## 2. Data-format impact

`gallery.json`: optional `cover` per person (additive; an older version ignores
it). `check_data.py` checks it is a path: every file readable.

## 3. Suggested documentation updates

- **ARQUITETURA 10 / 17.10 (gallery, People)**: `cover`, `set_cover`,
  `cover_of`, the fallback rules, the star on the person page, the route.
- **ARQUITETURA 18 / 19 (production, data)**: `--no-dev`; `cover` in the list
  of optional gallery keys.
- **CONTEXTO 8 / 13.4**: backlog 21 and R26 done.

## 4. Worth explaining to the user

- `uv sync` makes the environment match the lock exactly, which is why adding
  `--no-dev` also removes what is already installed.
- `--dry-run` to see what a command would change before running it.

## 5. Measurements

29 tests pass (6 new: 5 gallery, 1 guard). R26: dry run lists 9 packages to
uninstall (pytest, httpx2 and their dependencies), nothing else.

## 6. What the review should look at hardest

1. The cover is a path, not an index, so it survives views being removed or
   reordered; `cover_of` ignores it once it no longer matches a view.
2. R26 takes effect only at the next deploy; production keeps the dev
   packages until then.

## 7. Not done

Nothing of the plan.

## 8. Usage

| | 5-hour window | Weekly | Context |
|---|---|---|---|
| Start (~16:10) | 81% (resets 18:20) | 53% | 542k tokens |
| End (~16:20) | 84% | 53% | ~560k tokens |

Per item: backlog 21 81→83, R26 83→84.
