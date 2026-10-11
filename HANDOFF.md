# Handoff - developer to architect

Developer session 9, 11/10/2026, on the M900 (`Sasori`), following CONTEXTO
14.4. **Old conversation again** (context 659k at the start). Production
(`v2026.10.11`) was only read (`status`, healthy at the start and the end;
three clips copied from it). Nothing was pushed. No command started with
`cd`; `uv run pytest` before every commit.

**What went wrong in this session:** a call to the built-in browser pane
hung for over an hour with no answer, and the user found the session
stalled. The R28 change was intact and uncommitted; the rest of the
verification was done over plain HTTP. Meanwhile the 5-hour window went from
36% to 72% (the hang plus an architect session in parallel on the same
window), so the scope was cut: R30 part (b) and R29 are left for the next
session.

## 1. Items

| # | Item | Commit | State |
|---|---|---|---|
| 1 | R28 — no stale page; refusals say why | `a54f357` | done |
| 2 | R30 (a) — the face photo even from the side | `9fb8862` | done |
| 3 | R30 (b) — measure loosening the frontal limits | — | **not done**: needs named views (and budget) |
| 4 | R29 — dog grouping | — | **not done**: budget; note the architect changed its text in `aecedf7` during this session |

**R28.** `/` is built from `index.html` with `?v=<git describe>` on `app.js`
and `style.css`, sent with `Cache-Control: no-cache`; a middleware
(`never_stale`) adds the same header to `/static/*`. ETag revalidation gives
304 when unchanged. Refusals: `send()` already throws the server's `detail`
and every caller prints it; checked through 192.168.0.18 — an unpaired write
answers 403 "no PIN is set: on the M900 itself, open Settings and set one to
pair other devices".

**R30 (a).** `faces.nose_offset()`; `faces_in(frame, sides=None)` collects good
non-frontal faces (score ≥ `IDENTITY_SCORE`, width ≥ 36) with offset and crop;
`scan_clip` saves the best (smallest offset, then largest) as
`HH-MM-SS.side.jpg` beside the clip when nothing recognisable was recorded,
never into the gallery; `_assemble` sends `notify.side_face` ("face, side
view") in place of the best view, only after a sent event.

## 2. Data-format impact

New optional event file `HH-MM-SS.side.jpg` (moves with `base.*` on archive).
Nothing else. `check_data.py`: every file readable.

## 3. Suggested documentation updates

- **ARQUITETURA 17 (web)**: cache policy, versioned asset URLs, `never_stale`.
- **ARQUITETURA 10 / 12 (faces, notifications)**: side views, `nose_offset`,
  `.side.jpg`, the "face, side view" message and its place among the
  follow-ups (face > side view > best view).
- **ARQUITETURA 19 (data)**: `.side.jpg`.
- **CONTEXTO 14.4**: R30 (b) and R29 carry over.
- Built-in browser pane: a call can hang indefinitely — prefer HTTP checks.

## 4. Worth explaining to the user

- HTTP caching: `Cache-Control: no-cache` means "revalidate", not "do not
  store"; ETag and 304; cache-busting with a version in the URL.
- YuNet's five landmarks and how "frontal" is measured (nose offset, eye
  spread).

## 5. Measurements

- R28: before, no `Cache-Control` and unversioned URLs on all three files;
  after, `no-cache` on all three, `?v=v2026.10.11-2-g8ba01bc-dirty`, 304 on
  revalidation.
- R30 (a) on 10/10 Front 17:51:51, 15:50:37, 15:47:40: 0 recognisable faces,
  a side view kept each time (40, 59, 56 px; nose offsets 0.26-0.30 — so
  these failed on eye spread, not the nose); scans took 8-15 s.
- Tests: 48 pass (5 new).

## 6. What the review should look at hardest

1. The side view is chosen by nose offset, but these three failed on eye
   spread: the ranking may want both (R30 b's measurement will show).
2. The page's `?v=` uses `git describe`, which is `-dirty` in the test copy:
   edits there are covered by `no-cache` revalidation, not by the version.

## 7. Not done

R30 (b) and R29 (budget; R30 b also needs named views).

## 8. Usage

| | 5-hour window | Weekly | Context |
|---|---|---|---|
| Start | 36% (resets 12:20) | 64% | 659k tokens |
| End | 76% | 70% | ~700k tokens |

Most of the 40 points went to the hang and a parallel architect session;
R28 and R30 (a) themselves cost a few points each.
