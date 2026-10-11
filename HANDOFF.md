# Handoff - developer to architect

Developer session 8, 11/10/2026 (morning), on the M900 (`Sasori`), following
CONTEXTO 14.4. **Old conversation again** (context 638k at the start; the
5-hour window had just reset). Production (`v2026.10.10.7`) was only read:
`production.ps1 -Action status` at the start and the end (healthy) and its
dog gallery (counts, and the tuning tool, which only reads). Nothing was
pushed. No command started with `cd`; `uv run pytest` before every commit.

## 1. Items

| # | Item | Commit | State |
|---|---|---|---|
| 1 | R27 — cap the unnamed dog entries, "Dismiss" | `0b69a6b` | done |
| 2 | Tune the dog thresholds | `ba22178` (the measurement tool) | **blocked: production has 96 dog entries, 0 named.** The leave-one-out tool is written and checked, ready for when the user names crops |

**R27.** `DogGallery.add` trims after adding: only the newest `MAX_UNNAMED`
(60) unnamed dogs are kept (oldest first out, by gallery order); named dogs
are never touched; dropped entries' view and queued photos are deleted.
Sightings stay (calendars and Recordings keep history; their `dog_id` may
then point to nobody, which `label` shows as "?"). `DogGallery.dismiss`
forgets one unnamed dog and its photos, refusing a named one. `POST
/api/dogs/<id>/dismiss` (through the guard) and a "Dismiss" button under each
unnamed dog crop.

**Tuning tool.** `tools/dog_tuning.py [--gallery PATH]`: leave-one-out over
every named view, matched exactly as a new crop; counts per lighting
right-sure, right-probable, wrong, no name; then a grid of sure distance ×
ratio. A deviation in timing only: the plan's item 2 is the tuning itself,
which still needs the names; the tool is the half that did not.

## 2. Data-format impact

None. The cap deletes files the gallery itself created (views, queued
views). `check_data.py`: every file readable.

**For the deploy:** production holds 96 unnamed crops; the first new dog crop
after the deploy trims them to the newest 60.

## 3. Suggested documentation updates

- **ARQUITETURA (Dogs section)**: `MAX_UNNAMED`, trimming, dismiss;
  `dog_tuning.py` and how to read it.
- **CONTEXTO 13.4**: R27 done. **14.4**: tuning still waits for names; the
  next step is "name a few crops of each dog by day and at night, then run
  `uv run tools/dog_tuning.py`" (in production: `--gallery C:\JARVIS\dogs\gallery.json`,
  read-only).

## 4. Worth explaining to the user

- Leave-one-out validation: test each example against all the others, the
  honest way to measure a classifier on few labels.

## 5. Measurements

R27: 120 uncertain dogs gave 120 entries and 120 photos before, 60 and 60
after. Page: dismissing one crop left 19 of 20. Tests: 43 pass (3 new).
Tuning tool on a synthetic gallery: 8 of 8 right and sure.

## 6. What the review should look at hardest

1. `MAX_UNNAMED` = 60 deletes unnamed crops the user may still have wanted to
   name; the newest are kept, which are the most relevant.
2. Trim runs on every `add`, reading and writing `gallery.json` once more
   per uncertain dog (small).

## 7. Not done

Threshold tuning: no named dogs yet.

## 8. Usage

| | 5-hour window | Weekly | Context |
|---|---|---|---|
| Start | 11% (new window, resets 12:20) | 61% | 638k tokens |
| End | 15% | 61% | ~655k tokens |

Per item: R27 11→15, tuning tool under 1.
