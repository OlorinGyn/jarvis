# Handoff - developer to architect

Developer 22, 14/10/2026, 15:00-15:35. The plan of BACKLOG 3 in its order:
backlog 34, 35, 36, R52, R51, R30 (b). All done.

## 1. Items done

| Item | Commit | Closes |
|---|---|---|
| Analysis On/Off from the page header | `8828e5c` | backlog 34 |
| Detection sensitivity as sliders | `87a84fd` | backlog 35 |
| Telegram card beside What reaches the phone | `6295d57` | backlog 36 |
| Migration line in the log file, `filelock` around the migration | `50c836e` | R52 |
| A clip's face scored and learned by its best view | `734efa4` | R51 |
| Frontal gate: `MIN_EYE_SPREAD` 0.38 -> 0.30 | `fe0853b` | R30 (b) |

**Backlog 34.** The header's `#analysis` is now a `<button>`. A click posts
`{"on": bool}` to the new `POST /api/analysis`, which calls `analysis.set_on`
exactly as `/on` and `/off` do: the same in-memory flag, never stored, and
the bot's three-hourly reminder follows (tested). It logs
`Web: analysis Off from the page` (beside the Core's `Analysis Off`, as the
bot's `Telegram commands: analysis Off from the phone` does). It is a POST,
so `guard_writes` applies: refused without the header, and from another
device without the paired PIN (tested). **Off asks first** with `confirm()`
("Switch analysis Off? Nothing is recorded or sent until it is switched On
again; Live keeps working."); **On is one click**, no question — checked in
the browser. Answer: `{"analysis": "On"|"Off", "changed": bool}`; a non-boolean
`on` is a 400. A refused write shows `alert("Not done: …")`, since the header
has no result line. Checked at 375 px: the button sits beside the version,
41 x 32 px, red when Off, no horizontal scroll.

**Backlog 35.** Each of the three minimums is an `<input type="range">` with
no number, the ends saying in words "More detections, more false alarms" and
"Fewer, stricter". The mapping is in `settings.py`, so it is tested in
Python: `slider_position(value, default)` and `slider_value(position,
default)`, piecewise linear, position 0 = 0.20, `SLIDER_STEPS // 2` = the
default, `SLIDER_STEPS` = 0.90. `SLIDER_STEPS = 1000` so every two-decimal
value survives value -> position -> value (tested for defaults 0.20, 0.35,
0.45, 0.90): saving an untouched slider never moves a stored number. With
100 steps the right half of the person slider is 0.011 per step and a stored
0.40 would have become 0.41. The page reads `confidence_positions` and
`slider_steps` from `GET /api/settings` and saves with
`{"confidence_positions": {key: int}}`; the server turns positions into the
same numbers `config.json` already stores. The numeric keys are still
accepted (Back to the defaults uses them). The explanation stays beside the
sliders, always visible: the first hint (what the minimum is, left finds
more and more false ones, right is stricter, a change reaches the cameras in
seconds without a restart), a **How the sliders work** part (the minimum
confidence underneath, the middle is the default, the ends 0.20 and 0.90,
each half in proportion, then one line per slider: "Person: minimum 0.35 now,
default 0.35."), and the "what this does not fix" hint about a person bending
over. The current values in that text update on save, not while dragging:
showing them live would need the mapping in JavaScript too. Checked at 375 px
(slider on its own row, the two end texts under it) and on the desktop.

**Backlog 36.** CSS only: `#modes-panel` no longer spans the grid;
`.settings[data-part="notifications"]` has two columns, 3fr for the table and
`minmax(300px, 2fr)` for Telegram, `align-items: start`; under 860 px one
column. Checked at 1280 px (side by side) and 375 px (stacked, both 335 px
wide, no horizontal scroll). The pane's default width (~800 px) is one
column.

**R52.** `migrate_gallery` holds a `filelock.FileLock` on
`gallery_arcface_w600k_r50.json.lock` beside the gallery for the whole hash
check and rebuild (the work moved to `_migrate`), so a second copy waits,
finds the source hash unchanged and returns None. `cameras.main()` keeps the
result and logs it right after `log.to_file()`. The lock file is removed on
release (none left in `faces/`). `filelock` 4.1.2 is pure Python: no `.pyd`
or `.dll` in the package (PROCESS 5.3). Production gets it through
`uv sync` on the next update.

**R51.** `_scan_clip` calls the new `_best_view(gallery, group)`: every view
of the group is matched, and the best one — a person found, then a named
person, then the score, the same preference as `Gallery.match` — gives the
sighting its person and score, and is the view `reinforce` learns (with its
own crop) when it clears `LEARN_THRESHOLD`. Thumbnail, `face_width` and `box`
stay the heaviest view's: the clearest picture. A new unnamed entry is still
built from the heaviest and three others. Cost: one `Gallery.match` per view
instead of per group, well under 0.1 s for 40 views.

**R30 (b).** `MIN_EYE_SPREAD` 0.38 -> 0.30; `MAX_NOSE_OFFSET` stays 0.35.
The faces the eye-spread half rejected are mostly people looking down — at
the door, a phone — whose eyes are foreshortened. Tables below.

## 2. Data-format impact

None on disk. `config.json` still stores the three numbers; the page's API
gained `confidence_positions` (read and write) and `slider_steps` (read).
`faces/` gains a transient `.lock` file during a migration, deleted after.
`check_data.py`: "Every file is readable by this version" after each item.

To see R52's line on the test copy I forced a migration: stopped it, copied
`faces/` to the scratchpad, changed `source.sha1` in the ArcFace file, started
two copies one second apart, read the log, stopped, and restored `faces/`
byte for byte (`diff -r` clean). That left
`backups/faces_arcface_w600k_r50_20261014-151320` on the test copy.

## 3. Suggested documentation

- **ARCHITECTURE 22.7** (On/Off): the header switch, `POST /api/analysis`,
  Off asks first, On is one click, the log line; still never stored.
- **ARCHITECTURE 17.12** (write guard): `/api/analysis` among the guarded
  writes, if that section lists them.
- **ARCHITECTURE 7.14** (detection minimums): sliders, the mapping and
  `SLIDER_STEPS`, why 1000, the `confidence_positions` API, where the
  explanation sits.
- **ARCHITECTURE 10.14 / 10.x** (the scan): the best view decides and is
  learned (R51); `MIN_EYE_SPREAD` 0.30 with the R30 (b) table and why the
  offset stays 0.35.
- **ARCHITECTURE 19.1** (gallery migration): the file lock, a second copy
  waits and does nothing, and the line is now in `logs/jarvis.log`.
- **ARCHITECTURE 18.8** (one copy at a time): the ~25 s window R52 described
  is closed for the migration.
- **CONTEXT 10** (tuning constants): `SLIDER_STEPS` in `settings.py`.
- **PROCESS 5.3** (dependencies on the M900): `filelock` added, pure Python.
- **Settings page section** (wherever the page's screens are described):
  the Notifications screen in two columns.

## 4. Worth explaining to the user

- **`filelock`**: a lock between processes, not threads. `threading.Lock`
  (like C#'s `lock`/`Monitor`) only works inside one process; a lock file
  locked through the operating system (`msvcrt.locking` on Windows) is seen by
  every process, like a named `Mutex` in .NET. The `with FileLock(...)` block
  is a `try/finally` (Java's try-with-resources, C#'s `using`), and if the
  process dies Windows drops the lock with the handle.
- **Piecewise linear mapping**: two straight lines that meet at the default,
  so the middle of the slider is always the default even though 0.35 is not
  the middle of 0.20-0.90. Why 1000 steps: the rounding argument above.
- **`<input type="range">`** and **CSS grid** `grid-template-columns:
  minmax(0, 3fr) minmax(300px, 2fr)` with a `@media (max-width: 860px)` that
  turns it into one column: how the page adapts to a phone.
- **Leave-one-out** in the R51 measurement: scoring a clip's views against a
  gallery that learned from that same clip measures the gallery remembering
  itself (0.959); hiding the views written while the clip was scanned gave
  the honest 0.551.
- **`fetch` + `confirm()`** in `app.js`: the browser's own yes/no dialog
  stops the script until answered, which is why Off asks before the request.

## 5. Measurements

Both measurements ran on production's clips read in place (`C:\JARVIS\clips`)
against a copy of production's ArcFace gallery, scanned densely over the
whole clip (the sidecar does not keep the person moments). Scripts in the
developer's scratchpad: `collect.py`, `collect2.py`, `analyze.py`,
`faceless.py`, `pipeline.py`. **Leave-clip-out:** for each clip, stored views
whose photo file was written between the clip's start and 15 minutes after
its end are hidden, so a clip is never scored against what it taught.

**Clips.** Resident clips with exactly one named sighting, spread over the
days: Gustavo by day 6, Gustavo by night 6, Izabel by day 6 (she has no night
clips). For the stranger side, the 8 newest person clips with no sighting
were all night clips with no face at all, so **no real stranger was
measured**; the other resident stands in for one. Scan time 406 s for 26
clips, with production running.

**R51 table** — 24 face groups (139 views) whose views mostly match the
clip's resident. No view's best match was the other resident; 4 views
matched nobody.

| Method | Sure (>= 0.40) | Probably | None | Wrong person wins | Other resident's best | >= 0.30 |
|---|---|---|---|---|---|---|
| heaviest (before) | 11 | 12 | 1 | 0 | 0.243 | 0 |
| **best** (chosen) | **12** | 12 | **0** | 0 | 0.256 | 0 |
| second best | 9 | 15 | 0 | 0 | 0.243 | 0 |
| median of best 3 | 11 | 13 | 0 | 0 | 0.243 | 0 |

Groups that changed most: `Back/2026-10-12/13-58-05` heaviest 0.310, best
0.472 (probably -> sure); `Front/2026-10-12/22-36-42` 0.275 -> 0.371 (none ->
probably); `Back/2026-10-13/09-55-28` 0.416 -> 0.515; `Back/2026-10-10/15-41-19`
0.481 -> 0.551. Best of N lifts the other resident by 0.013 at most, and 0.256
still leaves 0.044 under `MATCH_THRESHOLD`.

**R30 (b) table, resident clips** — faces rejected today that a gate would
add, and what they match. 215 faces rejected: 151 by offset and spread, 63
by spread alone, 1 by offset alone.

| offset <= | spread >= | added | right resident | of which sure | other resident | nobody |
|---|---|---|---|---|---|---|
| 0.35 | 0.38 (today) | 0 | 0 | 0 | 0 | 0 |
| **0.35** | **0.30** | **58** | **48** | 14 | **0** | 10 |
| 0.35 | 0.20 | 62 | 52 | 15 | 0 | 10 |
| 0.5 | 0.30 | 82 | 67 | 22 | **1** | 14 |
| 0.7 | 0.20 | 122 | 96 | 27 | 2 | 24 |
| 1.0 | 0.20 | 132 | 103 | 29 | 2 | 27 |

**R30 (b), daytime person clips with no face sighting** (16, Front, 13/10,
15:08-17:45): today none of them has a face that passes.

| offset <= | spread >= | faces added | clips gaining a face (simulated scan) | matches |
|---|---|---|---|---|
| 0.35 | **0.30** | 10 | **2** | Izabel probably 8, sure 1, nobody 1 |
| 0.35 | 0.25 | 17 | 2 | adds **Gustavo probably 1** in her clip |
| 0.35 | 0.20 | 19 | 2 | as 0.25 |

The contact sheet of those faces: all the same woman looking down, Izabel,
real faces, not head-tops. The one "Gustavo 0.32" (spread 0.28,
`Front/2026-10-13/15-18-12`) is too blurred to tell who it is, in a clip of
Izabel's: that is why the limit stops at 0.30.

**The whole scan simulated** (group, best view, new entry if >= 2 views)
under 0.38 against 0.30: resident clips, sure sightings Gustavo 5 -> 7 and
Izabel 8 -> 11, probably 14 -> 15; new unknown entries 1 -> 1 (the same one);
no clip changes person. Faceless clips: 0 -> 2 with a face, both Izabel.

**Cost:** +58 faces over 18 resident clips is ~3 more embeddings per clip,
~0.4 s at 0.13 s each (ARCHITECTURE 10.14); +10 over 16 faceless clips.

## 6. Review hardest

- **R30 (b)'s sample.** Two residents, one camera afternoon for the faceless
  set, no stranger with a face. What could go wrong: a stranger looking down
  scoring "probably" a resident, silenced in Home. The other resident never
  reached 0.30 in 58 added faces, but that is two people. Worth a look at
  production's sightings with `face_width` small and a low score after a few
  days.
- **R51 and learning.** The view learned is now the best-matching one, which
  is the most like what is already stored: Chosen may become less varied
  than with the heaviest. `reinforce` already prefers views that make a
  person more varied past `MAX_EMBEDDINGS`; whether that is enough is a
  question for backlog 28's data.
- **The slider's mapping lives on the server only.** The page cannot show the
  number while dragging. If the architect wants that live, it means the same
  two functions in `app.js`, with no JavaScript runtime here to test them.
- **Static cache while developing.** `index()` stamps `app.js?v=<version>`;
  during development the version (`git describe … -dirty`) does not change
  between edits, so the browser kept the old script until a hard reload. Not a
  production problem (each release changes the tag).
- **`alert()`** for a refused On/Off write: the only place on the page that
  uses one. The header has no result line; a better place is a UX decision.

## 7. Not done

Nothing of the plan. Not measured: the person moments of each clip (the
sidecar does not keep them), so the dense scan here reads more frames than
production's scan does.

## 8. Usage

| | 5-hour window | Weekly |
|---|---|---|
| Start (15:00) | 0 % | 28 % |
| End (15:35) | 24 % | 31 % |

Context at the end: about 250k tokens.
