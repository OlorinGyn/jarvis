# Handoff - developer to architect

Developer session 12, 11/10/2026, 17:25–17:40, a new conversation started by
the architect. Plan: CONTEXTO 14.4 — R38 → R40 → R37 → R36. All four done, in
that order. 92 tests pass (83 at the start of the session; 79 before
`v2026.10.11.4`). No comments in `src/` or `tools/` (count 0).

## 1. Items done

### R38 — undo a report made by mistake (`2c2c943`)

- **Settings → Bad-detection reports**: every report, newest detection
  first, with its crop, verdict, camera, time, where it came from, and
  **Undo**.
  - A gallery report (face or dog crop): the entry goes back to its
    gallery with its views, queue, favourite and first-seen, the view
    photos go back to `faces/views/` or `dogs/views/`, and its sightings
    (JSON and crop) go back to their day folders. The report is deleted.
  - An event report ("Not a person" on a recording): the label leaves
    `reported_labels`, so the card shows it again. Refused (409) when the
    recording is no longer on this computer (archived).
- **Why a report now keeps more.** A report kept only the embeddings and
  one crop, and `take_out` deleted the view photos — nothing to put back.
  A new report keeps the **whole entry** (`entry` now has `name`, `views`,
  `pending`, `cover`, `thumbnail` too), the sighting file paths
  (`sighting_files`), and **copies of every photo** in a folder beside the
  JSON: `reports/<kind>/<stem>/` (view photos by their 12-hex names,
  sighting crops by theirs).
- **Older reports** (the two dog reports in production, 10/10): they come
  back with their embeddings, their sightings, and the report's crop as the
  photo — the view's photo when the entry had one view (both production
  reports do), else the entry's thumbnail; each sighting's crop is a copy of
  the report crop.
- New: `reports.undo`, `reports.find`, `Gallery.put_back`; routes
  `GET /api/reports`, `POST /api/reports/{kind}/{name}/undo`,
  `GET /report-photo/{kind}/{name}`. The write guard covers the POST as
  any other.

### R40 — the waiting views are shown and moved by the user (`4d9a190`)

- The person and dog pages show **Chosen (n of 40)** and **Waiting (n)**,
  each with its photos. Chosen tile: ★ favourite, × delete, ↓ move to
  Waiting. Waiting tile: ↑ move into Chosen, × delete.
- ↑ while Chosen is full is refused by the server with the hint "move one
  down or delete one first" (shown in the page's result line; the button's
  title says it too). ↓ is refused for the last chosen view, or when
  Waiting is full (`MAX_PENDING`, 100) — not to drop the oldest waiting
  photo silently.
- **Removing a chosen view no longer pulls the oldest waiting one.** The
  last chosen view cannot be deleted even when views wait: the user moves
  one up first (a person with no chosen view matches nobody).
- Analyse's proposal: **"Keep these 40, the rest waits"** and **"Keep these
  40, discard the rest"** (asks first; deletes the photos of the views not
  kept).
- `Gallery.demote_view`, `promote_view`, `remove_waiting`,
  `keep_spread(..., discard)`, and `_fix_cover` (the favourite fallback
  shared by every move). Routes `views/{i}/demote`, `pending/{i}/promote`,
  `pending/{i}/remove` for persons and dogs; the page JSON gains
  `pending_photos`. The page selects `.chosen-grid` and `.waiting-grid` by
  name, not "the first `.views-grid`" (the R39 lesson).
- A moved view goes to the **end** of the list it enters (↓ to the end of
  Waiting, ↑ to the end of Chosen).

### R37 — what a report actually was (`72924d7`)

- Each report in the Settings list has an optional **"Actually…"** choice:
  person, dog, other animal, nothing — minus the label the detector gave.
  Stored as a new optional key `"actually"`; "" clears it.
  `POST /api/reports/{kind}/{name}/actually`.
- Chosen in the list, not at report time: it works for the reports already
  made, and the report button stays one click and a confirm.

### R36 — the report race (`0daa7ff`)

- **Reproduced first**: a test reinforces the entry while the report is
  being made. Before the fix, the report had 1 embedding while the gallery
  had 2 at removal — the new view was removed, its photo deleted, and it
  was in no report.
- Fix: `take_out(entry_id, forget=False)` removes the entry **under the
  gallery lock** and returns it as it left (it returned a bool). The report
  is written from that entry, the photos copied, and only then deleted
  (`forget_views`). If writing the report raises, the entry is put back.
  A view a scan adds after the take-out is refused, as for any entry that
  is gone.

## 2. Data-format impact

All additive; `uv run python tools/check_data.py`: "Every file is readable
by this version" (214 events, 7 people, 22 dogs, 1 report in the test copy).

- Report JSON: `entry` gains keys (the whole gallery entry); new optional
  `sighting_files` and `actually`. A new sub-folder `reports/<kind>/<stem>/`
  with photo copies. `listing()` and `check_data` glob `*/*.json`, so the
  folder is not read as a report. Older reports read and undo.
- `check_data` now also checks `actually`, when present, is a valid choice.
- `gallery.json`: unchanged format. `pending` now also receives views the
  user moves down.
- Event JSON: `reported_labels` can shrink (Undo).

## 3. Suggested documentation updates

- **ARQUITETURA 21** (or where backlog 23 and 24 are described): Undo of a
  report and what a report keeps; the two grids and the four moves;
  "discard the rest"; the R36 order (take out under the lock, then report,
  then delete photos).
- **CONTEXTO 13.4**: R36, R37, R38, R40 done with these commits.
- **CONTEXTO 8**, backlog 23 text: "Nothing is learned from it" still holds;
  add that a report can be undone and can say what it actually was.
  Backlog 24: removing a view no longer pulls a waiting one.
- **README / user guide**, if it describes the person page: Chosen and
  Waiting.

## 4. Worth explaining to the user

- **Copy before delete, and the order of a two-step change** (R36): the old
  code took a snapshot, did slow work, then removed — anything that changed
  in between was lost. Taking out first, under the lock, then working on
  what was taken, is the same idea as a Java `synchronized` block that
  returns the removed object (`map.remove(key)` returns the value) instead
  of `get` then `remove`.
- `try / except Exception: put_back; raise` — like a C# `catch { undo;
  throw; }`: the bare `raise` re-throws the same exception with its stack.
- `shutil.copyfile` / `shutil.rmtree(ignore_errors=True)` — Python's
  `Files.copy` and a recursive delete that does not throw.
- JavaScript `new Option(text, value)` to fill a `<select>`.

## 5. Measurements

- R38: 34% → 38% of the 5-hour window (~4 points), including the browser
  check with copies of production's two reports (Undo of one in the test
  copy brought dog `d_ef5e7bbb` back with its photo and sighting).
- R40: 38% → 42% (~4), browser check of ↓ and ↑ on a person and the photo
  grid on a dog.
- R37: 42% → 43% (~1). R36: 43% → 44% (~1).
- Tests: 83 → 92.

## 6. What the review should look at hardest

1. **`reports._undo_entry` for old reports**: the crop becomes a view only
   when the entry had exactly one embedding; otherwise it is only the
   thumbnail (stored in `views/`, not deleted by a later `take_out` — a
   small leak). Is that the right call?
2. **R40 rule "the last chosen view cannot be deleted even with views
   waiting"** — a change from before, where the oldest waiting view filled
   in. It follows "the user picks", but check it fits what the user wants.
3. **↓ refused when Waiting is full (100)** instead of dropping the oldest
   waiting view as a scan does.
4. A scan that finds an entry being reported still writes its **sighting**
   pointing to the gone id (unchanged; the view itself is refused). Undo
   does not restore such a sighting, and it is an orphan either way.
5. The browser test server here was the web app alone on port 8767 (no
   Core), not the full test copy on 8766.
6. Test data changed in this folder only: `reports/dog/` holds copies of
   production's two reports; one was undone (dog `d_ef5e7bbb` is back in
   `dogs/gallery.json` here), the other has `actually: other animal`.
   Nothing under `C:\JARVIS` was touched.

## 7. Plan items not done

None. R30 (b) still waits for a second named person, as planned.

## 8. Usage

| | 5-hour window | Weekly | Context |
|---|---|---|---|
| Start (17:25) | 34% | 87% | 74k tokens |
| End (17:40) | 44% | 88% | 193k tokens |

The window resets at 22:20 local (01:20 UTC).
