# Handoff - developer to architect

Developer session 18, 13/10/2026 (night): backlog 28 alone, as BACKLOG 3
planned it.

## 1. Items done

**Backlog 28 — the 40 views manage themselves.** Closed by two commits:

- `6345a7d` perf(dogs): `DogGallery.distances` in numpy instead of a Python
  loop. Needed by the rule below, which builds the 41×41 matrix under the
  gallery lock every time a full dog takes a view: 36 ms per view before,
  0.5 ms after (development PC), equal to `distance()` within 1e-15 on
  production's 167 dog descriptors. Bhattacharyya for every pair at once is
  `sqrt(1 - sqrt(A) @ sqrt(A).T)` per histogram block
  (`_bhattacharyya_matrix`); day against infrared stays `inf`, the diagonal 0.
- `47a2e6a` feat(galleries): the rule, the page text, the once-only tool and
  the tests.
  - `faces.replaced_view(matrix, favourite)`: the last row of a distance
    matrix is the new view, the others the 40 chosen. The candidate is the
    chosen view whose nearest twin is closest, never the favourite; it is
    replaced only when the new view's distance to its own nearest chosen
    view is larger than the candidate's. Ties go to the older view (lower
    index). Works in distances for both galleries: faces are `1 - cosine`
    (the existing `Gallery.distances`), dogs are `dogs.distance`.
  - **Dogs and lighting**: candidates are restricted to chosen views
    comparable with the new one (same lighting) when there is any, so a day
    view replaces a day view and a night view a night view. A view with no
    same-lighting twin has an infinite nearest distance — "counts as
    different" — and replaces the closest pair of the other lighting (the
    first night view of a dog seen only by day enters). A chosen view with
    no same-lighting twin is never a candidate.
  - `Gallery._take` now returns `"chosen"`, `"replaced"` or `"discarded"`
    and never appends to `pending`. Waiting only grows by the user's ↓
    (`demote_view`, still capped by `MAX_PENDING`). `add`, `reinforce` and
    `_merge` (rename, assign, absorb) all pass through it, so a merge past
    40 follows the rule too, including the source's waiting views.
  - **Photos are deleted after the save**: `_take` lists the photos of views
    that leave in `self.dropped` (reset by `load()`, like `repoints`), and
    `save()` deletes them after writing `gallery.json`. A failed write leaves
    an unused photo, never a view without one; a dry run that never saves
    deletes nothing.
  - `Gallery.settle_waiting(dry_run)`: passes every waiting view, oldest
    first, through `_take` and empties `pending`, under the gallery lock.
    Per entry: waiting, entered (waiting views that ended in Chosen),
    discarded, pushed_out (chosen views deleted to make room).
  - `tools/settle_waiting.py [--dry-run]`: both galleries. `--dry-run`
    writes nothing. A real run refuses (exit 1) while this folder's
    J.A.R.V.I.S. answers on its port (`WEB_PORT` in `.env`, else 8765),
    because it is a separate process and `_GALLERY_LOCK` is only a thread
    lock; then it copies `faces/` and `dogs/` whole to
    `backups/waiting_<date-time>/` before touching anything.
  - The page's hints (People and Dogs): Chosen now says how a full Chosen
    takes a new view; Waiting says "Moved down from Chosen" instead of
    "Seen after Chosen was full".

## 2. Data-format impact

None. `pending` stays a readable optional list; nothing new is written.
After the tool it is `[]` per entry that had a queue. An older version
reading the result sees ≤ 40 views and an empty queue. `check_data.py`:
"Every file is readable by this version" on the test copy, and on a copy of
production's `faces/` and `dogs/` after a real run of the tool.

## 3. Suggested documentation updates

- **ARCHITECTURE 17.14**: the rule replaces "views seen after Chosen was
  full wait"; Waiting is now only what the user moved down; "↓ while
  Waiting holds 100 — refused rather than dropping the oldest waiting photo
  as a scan does" no longer has a "scan does" half. "Analyse" (backlog 24)
  still works, but after the tool nobody will have more than 40 unless they
  move views down.
- **ARCHITECTURE 17.10** (People by person): "`pending`, views waiting once
  a person holds 40 (`MAX_PENDING` 100, oldest dropped with its file)" and
  "`Gallery._take()` is the one place that stores or queues a view" are
  out of date.
- **ARCHITECTURE 10.4**, last line: "more wait in a queue the user manages".
- **ARCHITECTURE 22.6**: "a scan that finds Waiting full drops the oldest,
  shifting every position by one" — a scan no longer shifts Waiting; another
  tab's move still can (the test now uses that: `test_view_moves.py`).
- **ARCHITECTURE 19.2**: `faces/views/` "one face crop per stored or queued
  view"; and the tests paragraph (`test_gallery.py` "the queue past 40 and
  its cap" is gone; new `test_forty_views.py`; 216 tests in about 13 s).
- **ARCHITECTURE 20** (dogs): the vectorised distance matrix.
- **CONTEXT 9** (repository map): `tools/settle_waiting.py`, once-only.
- **HISTORY**: the dry-run numbers below, for when the architect runs it.

## 4. Worth explaining to the user (PYTHON.md)

- **Vectorising a pairwise loop**: 820 Python calls become one matrix
  product. `np.sqrt(A) @ np.sqrt(A).T` gives every Bhattacharyya
  coefficient at once — the Java/C# analogue is replacing a nested `for`
  over pairs with a BLAS call; boolean masks (`matrix[empty, :] = 1.0`,
  `np.where(infrared[:, None], tone, colour)`) replace the `if`s, and
  broadcasting (`infrared[:, None] != infrared[None, :]`) builds the
  "different lighting" matrix without a loop.
- **`np.inf` as "cannot be compared"**: `min` and `>` keep working, and
  `np.isfinite` picks the comparable ones — no `None` checks in the rule.
- **`id()` as identity**: `settle_waiting` counts which embeddings survived
  by object identity, since equal lists could be different views (Java's
  `==` on references vs `equals`).
- **Delete after commit**: `save()` writes the JSON and only then deletes
  the photos, the same order as a database commit followed by file cleanup.
- **Loading a script as a module in a test**: `importlib.import_module`
  after putting `tools/` on `sys.path`, since `tools/` is not a package.

## 5. Measurements

- Rule cost per view past 40: faces 0.6 ms, dogs 0.5 ms (36 ms before
  `6345a7d`), development PC.
- **Dry run on a copy of production's `faces/` and `dogs/`** (13/10, 22:30;
  production itself untouched, only read):

  | Entry | Waiting | Enter Chosen | Deleted from Waiting | Chosen views deleted |
  |---|---|---|---|---|
  | Gustavo Henrique Gomes | 31 | 22 | 9 | 22 |
  | Izabel | 35 | 20 | 15 | 20 |
  | Aurora | 29 | 1 | 28 | 1 |
  | Mirana | 31 | 5 | 26 | 5 |

  It matches BACKLOG 28's measurement: faces' waiting views are varied and
  the chosen 40 held identical pairs, so most enter; dogs' waiting views are
  closer to the chosen than the chosen to each other, so few do. The dry run
  left every byte as it was (md5 of every file before and after). The real
  run on the copy: 0.1 s, every queue empty, ≤ 40 views each, the favourite
  kept, no reference to a missing photo, second dry run "nothing waiting".
  On the scratch copy the deleted photos stayed on disk (66 faces, 60
  dogs — exactly the deleted count), because `_forget_view` resolves the
  relative paths in `gallery.json` against `ROOT` and refuses a file
  outside its own `views/`; with the tool run from `C:\JARVIS` they resolve
  to production's folder and are deleted. The tests prove the deletion on
  galleries in temporary folders.
- Tests: 216 passed in about 13 s (208 before; 4 tests of the old queue
  removed, 11 new, 1 rewritten).

## 6. What the review should look at hardest

- **`replaced_view`'s reading of the rule**: the new view's distance is to
  its nearest chosen view *including* the candidate itself (the text says
  "its own nearest chosen view"), so a new view whose only near twin is the
  candidate is discarded. The alternative — measure after removing the
  candidate — would let a view in that only replaces its own twin.
- **The dogs' candidate restriction** (same lighting first, then any): my
  reading of "only the same lighting is compared"; it keeps the day/night
  balance a dog already has.
- **Deletion moved into `save()`**: every `save()` now deletes what
  `self.dropped` holds. Only `_take` fills it, and `load()` empties it, so a
  method that loads after `_take` and before `save` would lose deletions
  (leaving files, not breaking references). `add()` calls `_take` before its
  `load()`, but a new entry is never full, so nothing is dropped there.
- **The tool's running check** is by HTTP on this folder's port only. It
  must be run from `C:\JARVIS` with production stopped
  (`production.ps1 -Action stop`, run, `-Action start`); the test copy on
  8766 does not share production's files.
- `tests/queues.py` writes `pending` straight to disk, the way older
  versions left it, since nothing in the code queues on its own any more.

## 7. Plan items not done

None. The once-only run on production is the architect's, after the deploy
(BACKLOG 3): from `C:\JARVIS`, stop, `--dry-run`, real run, start.

## 8. Usage

| | 5-hour window | Weekly |
|---|---|---|
| Start | 34 % | 14 % |
| End | 40 % | 15 % |

Context at the end: about 163 k tokens.
