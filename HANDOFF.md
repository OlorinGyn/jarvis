# HANDOFF — developer 31 (17/11/2026): backlog 43 (steps 1–2), backlog 44

The plan of BACKLOG 3, in its order. Steps 1, 2 and 4 done; **step 3 not
built** — the dry run shows two wrong moves, the plan's stop; step 5
(backlog 42) left for developer 32, for the review's budget (section 7).
421 tests pass (388 + 33), no comments in `src/` and `tools/`,
`check_doc_refs` exits 0, `check_data` reads every file of the test copy.

## 1. Items done

**Backlog 43, the evidence and the tool — `7c80e4d`.**

- `faces.py`: `person_tracks(tracks)` counts the tracks voted person (the
  event JSON's `tracks`, `tracks.voted`), `None` for an event recorded
  without them; `sure_resident(gallery, sightings, sure)` is the one named
  resident whose sighting scored at or above `sure` (none or two → `None`);
  `evidence_owner` joins the two. `sightings_by_event(faces folder)` and
  `event_tracks(clips folder, event)` read what they need from any folder.
  `cleaning_moves(gallery, clips, sure)` gives one move per view — chosen
  **and waiting** — of an unnamed entry or a resident whose own event
  (`view_events`) names another resident; a named visitor's views are
  never moved, a view with no event stays.
- `Gallery.apply_cleaning(moves, dry_run=False)`: one lock, one load, one
  save; each view leaves its entry by its photo name (`_take_out_view`),
  carries its event and enters the resident through `_take` (the 40-view
  rule: chosen, replaced or discarded). A named entry never gives up its
  last chosen view ("last view kept"). An unnamed entry left with no chosen
  view moves its queue up, or with none leaves the gallery, its sightings
  repointed to the resident that took most of its views (the `repoints`
  `_merge` uses, applied at `save()`).
- `Gallery._forget_view` resolves a relative view against the gallery's
  own project folder (`self.path.parent.parent`) instead of `ROOT`: for
  ROOT's galleries nothing changes; a gallery opened from another folder
  (the tool on `C:\JARVIS` run from the test copy, or on a copy) now
  deletes its own discarded photos. Measured on the copy: 405 → 382 photos,
  the 16 replaced + 7 discarded.
- `tools/clean_gallery.py <folder> [--apply] [--sheets DIR]`. Reads
  `<folder>/faces`, `<folder>/clips`, the sure threshold from
  `<folder>/config.json` (default 0.40) and the port from `<folder>/.env`.
  The dry run prints every move, writes one contact sheet per destination
  (`to_<name>.jpg`, outside the folder: `--sheets` or a new temp folder),
  checks itself against HISTORY 13.33's labels (hard-coded in `LABELS`) and
  simulates the 40-view rule. `--apply` refuses while the port answers,
  copies `faces/` to `<folder>/backups/clean_gallery_<stamp>/faces`, then
  cleans, merges (backlog 44) and names the visitors.

**Backlog 44, "Visitor N" — `92e36a3`.**

- `Gallery.add` gives each new unnamed face entry `temporary_name`
  ("Visitor N"); `_next_visitor` takes N past both the header's counter
  (`"visitors"`, the last number given) and every temporary name held, so a
  number is never reused, also after a deletion and on a file whose counter
  is missing. `DogGallery.temporary_names = False`.
- `Gallery.name_visitors()` gives the unnamed entries without one theirs,
  in order of `first_seen`; run once per start in `cameras.main()` beside
  `recover_events` (logged "Temporary names given to N unnamed face
  entries"), and by the tool after `--apply`.
- `rename` and `assign` (with a new name) drop it; views and sightings stay.
  `person_case` is untouched (still `unknown_face`); `notify._who` reads
  "Visitor 12, unknown face"; the scan's sighting dicts carry
  `temporary_name`; `web._card` sends it; `app.js` shows
  `name || temporary_name || "Unknown"` on the card and the page.
- **The grouping.** `scan_clip(..., tracks=None)` now receives the event's
  `decided()` tracks from `clips._assemble`. `_one_visitor`: when a clip of
  one body (one track voted person) recorded two or more unnamed
  sightings, `Gallery.merge_unnamed(ids)` merges them into the first seen
  (`_merge`, so sightings are repointed), and the returned sightings keep
  one per entry — one "unknown face" message instead of two. For the
  entries that already exist, `one_body_groups(gallery, clips)` joins the
  unnamed entries sharing a one-body event into groups (transitively);
  the tool merges them on `--apply`.

## 2. Data format

All additive.

| File | Field | Older versions |
|---|---|---|
| `faces/gallery_arcface_w600k_r50.json`, per entry | `temporary_name` (string, unnamed entries only) | keep it (entries are written back whole) and ignore it |
| same file, header | `visitors` (int, last N given) | `save()` writes `{**header, model}`: kept |
| face sightings (`faces/<day>/*.json`) | unchanged; the in-memory dict passed to `notify` has `temporary_name` | — |

The cleaning and the merges **move** data (views between entries,
entries removed, sightings repointed) but write no new format.
`check_data` on the copy of production: before — 7212 events, galleries
`gallery.json` 10 and `gallery_arcface_w600k_r50.json` 52, 2545 face
sightings; after `--apply` — the same, the gallery 47 entries. (The copy
holds the event JSONs without their videos, so every event reads "video
missing" there, before and after; on the test copy itself
`check_data` passes whole.)

## 3. The dry run on a copy of production (17/11 13:41)

The copy: `C:\JARVIS\faces` whole and every event JSON of `C:\JARVIS\clips`
(7212, no videos), in the scratchpad; `C:\JARVIS` only read. Sure threshold
0.40 (production's `config.json` has no `face_sure_threshold`).

**23 moves, 19 events** — through the 40-view rule: 16 replace a chosen
view, 7 are discarded, 3 unnamed entries are left empty and removed.

| Labels (HISTORY 13.33) | Entries | Views | To that resident | To the other |
|---|---|---|---|---|
| Gustavo | 13 | 122 | 15 | 4 |
| Izabel | 3 | 6 | 4 | 0 |
| probably Gustavo | 3 | 12 | 0 | 0 |
| any other unnamed entry → a resident | | | **0** | |
| resident → the other resident | | | 0 | |

**Read by eye on the contact sheets**, the 4 "to the other":

- 2 are right: `b25919d31e4f.jpg` and `2fd2d205ec0c.jpg` of `p_208373ee`
  (the entry behind 103 messages, labelled Gustavo, which HISTORY 13.33
  says holds two of Izabel's views) are a woman, and go to Izabel.
- **2 are wrong**: `c1cbb25d1a6f.jpg` of `p_9d3c46dc` and
  `3225bc93eed1.jpg` of `p_ec19f444` — Gustavo with headphones — would go
  to Izabel, both from **`Back/2026-10-27/00-39-23`**. That event's "sure"
  Izabel is a **36 px face seen in 1 frame**, score 0.452 against the 0.40
  threshold: Gustavo matching the views of his that sit in Izabel's Chosen
  (HISTORY 13.33: "four of Gustavo's views in Izabel's"). The evidence
  trusts a sure match the mixed gallery itself made.

All 15 to Gustavo are him; the 4 of the Izabel entries are women. So: 21
right, 2 wrong. **Step 3 (the same rule at scan time) was not built**, as
the plan says. A variant measured, not built (the rule is the user's):

| The sure resident's sighting must have | Moves | Wrong | Right lost |
|---|---|---|---|
| (the rule as decided) | 23 | 2 | — |
| at least 2 frames (as `MIN_VIEWS_FOR_NEW` asks to form an entry) | 21 | 0 | 1 (`Front/2026-10-27/14-30-20`, Izabel 1 frame, 69 px) |
| a face at least 40 px wide | 21 | 0 | 1 (`Back/2026-10-29/19-23-39`, Gustavo 39 px) |

Per event, the sure sighting behind each move (resident, score, frames,
px): Gustavo 0.518/6/77, 0.407/11/49, 0.432/7/47, 0.402/3/43,
0.458/21/81, 0.447/22/51, 0.469/3/39, 0.474/6/43, 0.409/3/48,
0.459/9/48, 0.495/48/69, 0.467/6/52, 0.42/5/41, 0.486/3/52; Izabel
**0.452/1/36 (the wrong one)**, 0.406/10/47, 0.404/1/69, 0.445/2/45,
0.422/4/40. 23 moves is a small sample for choosing a rule.

**What the deploy would do on production** (the same copy, `--apply`):
52 → 49 entries (cleaning) → 47 (merges `p_0617ae61` + `p_cfb78815`,
`p_208373ee` + `p_d2fd6da4`; the third group, `p_9d3c46dc` +
`p_ec19f444`, is the wrong event above and is gone after the cleaning) →
42 unnamed entries named "Visitor 1"…"Visitor 42", counter 42. Applied
twice, the second run finds 0 moves.

**The grouping, measured against the labels** (step 4's condition):
before the cleaning 3 groups, after 2; every group is two entries
labelled Gustavo (or "probably Gustavo"), **none of two people labelled
different** — the merge was built. The third group is formed by the same
wrong event as the cleaning's, but both of its entries are Gustavo.

## 4. Suggested documentation

- **ARCHITECTURE 10** — a new section, "The evidence of one body" (backlog
  43): the rule, `cleaning_moves`/`apply_cleaning`, the last-view guard,
  the emptied entry repointed to the resident that took most, and the
  measured 21/2 with the 36 px night face; and "Visitor N" (backlog 44):
  the counter in the header, the start-time naming, `_one_visitor` at scan
  time, `one_body_groups`.
- **ARCHITECTURE 10.16** — `view_events` now also drives the cleaning and
  the grouping.
- **ARCHITECTURE 17.14** — the plan says the scan-time join would "wait in
  Waiting"; the 40-view rule since backlog 28 never queues on its own (a
  view is chosen, replaces or is discarded) — the cleaning uses `_take` as
  it is. Worth a sentence wherever step 3 is described.
- **ARCHITECTURE 12.14 / 22.3** — one body's two unnamed faces now send one
  "unknown face" message, not two; the message text with "Visitor N".
- **ARCHITECTURE 19** — the new optional fields; the tool beside
  `settle_waiting.py`.
- **CONTEXT 9** — `tools/clean_gallery.py` in the repository map.
- **HISTORY 13.33** — the dry run's numbers, and that the labels are
  per-entry while two labelled entries hold the other resident's views.
- **BACKLOG** — 44 done; 43 half (the cleaning, not the scan-time rule);
  42 not started.

## 5. Concepts worth explaining to the user

- **The walrus operator `:=`** (`if (found := VISITOR_PATTERN.fullmatch(...))`,
  `if person and ...`): assigns inside an expression, like C#'s
  `out var` in `if (dict.TryGetValue(k, out var v))`.
- **`re.fullmatch`** against `re.match`: the whole string must match, like
  anchoring `^...$`.
- **Union-find by sets** in `one_body_groups`: each id points at a shared
  `set`; joining two groups makes a new set and re-points every member —
  the simplest form of the disjoint-set structure. `{id(g): g ...}` dedups
  the groups by object identity (`id()` is Python's reference identity,
  like `ReferenceEquals`).
- **`Counter.most_common(1)`** to pick the resident that took most views.
- **PowerShell 5.1 and `git commit -m` with double quotes**: native
  arguments lose their inner quotes, so the message split into
  pathspecs; `git commit -F file` avoids it.

## 6. Measurements

- Dry run on the copy: 5.6 s wall clock for 52 entries, 2545 sightings,
  7212 events, including `uv run`, the imports and the contact sheets (the
  sighting index reads every sighting once).
- `_one_visitor` costs nothing unless a one-body clip has two unnamed
  faces; a merge rewrites the repointed sightings (one pass over the
  sighting files, as every merge already does).

## 7. What the review should look at hardest

1. **The two wrong moves and whether to apply.** The plan's criterion for
   step 2 ("any view of any other unnamed entry … must be 0") holds — 0 —
   but the 2 wrong moves come from labelled entries, not from visitors.
   Applying as is gives two of Gustavo's views to Izabel, deepening the
   very mix behind them. The variant of section 3 (≥ 2 frames) is one
   line in `sure_resident`; it is the user's rule to change.
2. **`_forget_view`'s base folder.** Any gallery whose relative view paths
   were written relative to `ROOT` but which lives elsewhere than
   `ROOT/<x>/` would now resolve them elsewhere — only the tests' tmp
   galleries do, and they store absolute paths.
3. **Repointing an emptied entry's sightings**: an unnamed entry's sighting
   that scored, say, 0.6 against that entry keeps its score when it points
   at the resident — so it reads as a *sure* resident sighting in
   Recordings and for any later evidence. The same is true of every merge
   since the gallery began (`_merge`), but the cleaning makes it common.
4. **`merge_unnamed` at scan time** runs inside the scan lock with the
   gallery lock: the repoint pass over every sighting file happens there.
5. The tool's label check counts "to the other" by entry label; mixed
   entries make that column need the contact sheets (section 3).

## 8. Not done

- **Backlog 43 step 3** (the same evidence at scan time): not built — the
  dry run has 2 wrong moves (section 3). The test file written for it was
  removed before committing.
- **Backlog 42** (unnamed faces forgotten after 60 days; probable dogs
  make no card): not started. It fit the window, but this session ended
  at 65 % and a review has cost ~17 points (A43); 82 % keeps the review
  under the 85 % stop. It is developer 32's, first, as the plan says.

## 9. Usage

| | 5-hour window | Weekly | Context |
|---|---|---|---|
| Start (13:33) | 51 % | 7 % | 77k |
| After backlog 43 | 61 % | 8 % | 188k |
| End | 65 % | 9 % | about 230k |
