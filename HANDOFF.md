# Handoff - developer to architect

Developer session 10, 11/10/2026, on the M900 (`Sasori`), started by the
architect's automatic handover. **Old conversation** (context 706k at the
start). Production (`v2026.10.11.2`) was only read: `status` (healthy), its
galleries (counts and the dog tuning tool, read-only), three clips copied
earlier. Nothing was pushed. No command started with `cd`; `uv run pytest`
before every commit. Closed at the architect's request before R35.

## 1. Items

| # | Item | Commit | State |
|---|---|---|---|
| 1 | R34 — pair a device once, 30 days renewed with use | `d6aa12e` | done |
| 2 | Backlog 5 — play the recordings on the page | `63dad6c` | done |
| 3 | R29 — naming a dog gathers its sure look-alikes; past recordings follow | `49a17b8` | done (out of order: done while R35's replay ran) |
| 4 | R35 — R18's ratio 2.0 → 1.5 | — | **not done**: replay stopped at 54 of 93 events; it already shows drops that may be people (section 5) |

**R34.** New `devices.py`: `pair(label)` → random token, only its SHA-256 kept
in `devices.json` (new, gitignored) with label (address + browser),
`paired_at`, `last_used`; `use(token)` checks and renews; `known(token)` checks
without renewing (reads); `listing()`, `forget(id | all)`. Guard: a valid
`jarvis_device` cookie counts as paired (the `X-Jarvis-Request` header is still
required); every write from a paired device re-sets the cookie (`HttpOnly`,
`SameSite=Strict`, `Max-Age` 30 days). `/api/pair` creates the device after the
PIN was accepted; `/api/pin` forgets every device; `POST
/api/devices/<id>/forget` (local only). `/api/settings` gains `paired` and, on
the M900 only, `devices`. Page: the PIN is sent once to pair and no longer
stored; Settings › Other devices lists devices with Forget.

**Backlog 5.** `GET /video/<camera>/<day>/<HH-MM-SS>.mp4` (same name checks,
inside `clips/`; Starlette's `FileResponse` answers Range). Events gain
`video` and `side`; the thumbnail route also serves `.side.jpg`. A card with a
video opens a player over the page (×, Esc, click outside), with time,
people, animals and the side-view face.

**R29.** `DogGallery._absorb` gathers unnamed crops whose views match the dog
**sure** (`match`), never probable, same lighting only, repeating until
nothing joins. `dogs.current_words(sighting, gallery)`: a past sighting shows
its dog's current name (sightings are repointed on merge); the stored
"probable" only while the crop is unnamed. Used by `/api/events`.

## 2. Data-format impact

New `devices.json` (optional, read by `check_data`). Events: optional
`.side.jpg` now served. Dogs: crops may be merged automatically on naming
(same files as before). `check_data.py`: every file readable.

## 3. Suggested documentation updates

- **ARQUITETURA 17 (web)**: R34 (cookie, `devices.json`, renewal, forget,
  PIN change), the video route and player, `video`/`side` on events.
- **ARQUITETURA 20 (Dogs)**: `_absorb` for dogs, `current_words`.
- **ARQUITETURA 19 (data)**: `devices.json`.
- **CONTEXTO 13.4**: R34, R29, backlog 5 done; R35 open with the finding below.

## 4. Worth explaining to the user

- HttpOnly / SameSite cookies, and why a server-set cookie outlives
  script-written storage; storing only a hash of the token.
- HTTP Range requests (206 Partial Content) and why seeking needs them.

## 5. Measurements

- R34 through 192.168.0.18 (HTTP, not the browser pane): pair → cookie
  `HttpOnly; Max-Age=2592000`; a new session with only the cookie writes;
  the M900 lists it; forgotten → 403.
- Backlog 5: a real clip (10/10 17:51:51, 3.2 MB): Range → 206 with the
  requested bytes; outside `clips/` → 404. `HEAD` answers 405 (GET-only
  route; `<video>` does not need it).
- **R35 partial replay at 1.5 (54 of 93 person events):** 5 events lose one
  "person" each that 2.0 kept — Front 09/10 23:34:13 (0.64, ~380×240),
  23:53:02 (0.37, ~440×300), 10/10 15:12:59 (0.51, ~400×220), 15:14:15
  (0.50, ~420×200), 15:36:08 (0.52, ~440×280). These boxes are 200-300 high,
  much taller than the dog's 100-160: possibly a person with the dog, or
  bending over the mat. **Not checked visually**; 1.5 must not ship until
  they are. Script: scratchpad `r35_sweep.py` (from the R18 sweep).
- Dog tuning on production's names (Aurora 14, Mirana 11 views), current
  thresholds: 16 right-sure, **0 wrong-sure**, 4 right-probable, 1
  wrong-probable (night), 4 no name; no grid point gave a wrong sure, 0.45/0.7
  gives 19 right-sure. Too few views to change anything yet.
- Faces: production's gallery now has "Gustavo Henrique Gomes" with 31 views,
  enough to start R30 (b).
- Tests: 64 pass (16 new).

## 6. What the review should look at hardest

1. R35's five new drops (above) before any ratio change.
2. R34: a stolen cookie is a paired device for up to 30 days of use; the
   M900's Forget and a PIN change are the remedies.
3. R29: a wrong sure match now merges silently on naming (undo: Dismiss or
   rename).

## 7. Not done

R35 (finding above), R30 (b), R31, R32, dog thresholds — stopped at the
architect's request (budget).

## 8. Usage

| | 5-hour window | Weekly | Context |
|---|---|---|---|
| Start | 0% (new window, resets 17:20) | 72% | 706k tokens |
| End | ~43% | 77% | ~765k tokens |

R34 0→34 (shared with an architect session in parallel), backlog 5 34→36,
R29 and the partial R35 replay 36→41.
