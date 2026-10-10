# Handoff - developer to architect

Developer session 4, 10/10/2026, about 14:35-15:30, on the M900 (`Sasori`),
following CONTEXTO 14.4. **Still the old conversation** (the user chose it last
time and called `/dev` here again): context 412k at the start. Production
(`v2026.10.10.3`) was only read with `production.ps1 -Action status`, healthy
at the start and the end. Nothing was pushed.

## 1. Items

| # | Item | Commit | State |
|---|---|---|---|
| 1 | R24 — guard every write | `f2a7c3e` | done, acceptance met |
| 2 | Backlog 19 — People by person | `c60ee43` | done |
| 3 | Backlog 20 — who appears in each recording | `9587046` | done |
| 4 | Remove the OpenCV window | `c0cee37` | done; `--window`/`--janela` kept for one release |

**R24.** A FastAPI middleware (`guard_writes`) runs `_write_refusal()` on every
POST/PUT/PATCH/DELETE: (a) `X-Jarvis-Request: 1` is required, from anywhere,
127.0.0.1 included; (b) from any other address, `X-Jarvis-Pin` must equal
`write_pin` (`hmac.compare_digest`). `POST /api/pin` sets or clears the PIN
(4-12 digits) and is refused unless local; `POST /api/pair` is a no-op write
that answers only once the guard let it through. `write_pin` is a new key in
`settings.DEFAULTS` (additive); `/api/settings` never returns it, only
`pin_set` and `local`. `app.js` sends both headers; the PIN lives in the
browser's `localStorage`. Settings has a third panel, "Other devices": on the
M900 it sets the PIN, elsewhere it pairs. `request_stop()` sends the header.
`production.ps1` always stops a service with the same version's `--stop`
(also in a rollback), so the header cannot lock it out.

**Backlog 19.** Gallery, additive: `views` (aligned with `embeddings`, the
portable path of each view's crop in `faces/views/<12hex>.jpg`, `None` for
views stored before) and `pending` (views waiting once a person holds 40;
`MAX_PENDING` 100, oldest dropped with its file). `Gallery._take()` is the
one place that stores or queues a view; `add`, `reinforce` and `_merge` all go
through it (merge used to drop the overflow). `remove_view()` frees a slot and
pulls the oldest waiting view; it refuses the last view with nothing queued.
`views_of(person)` pads old persons with `None`. The scan keeps every crop of
a group (`group["crops"]`), so each stored view has its own. Routes:
`/api/persons`, `/api/persons/<id>` (view photos and appearances),
`/view/<file>`, `POST /api/persons/<id>/name {name, merge}` (409 when the name
belongs to someone else and `merge` is not true), `POST
/api/persons/<id>/views/<i>/remove`. The day-based `/api/people` and
`/api/face-days` are gone with the old tab. Page: grid of the named, the
unnamed with a name field and a "Belongs to…" picker (merge after a
confirm), the person page `#people/<id>` with rename, the views and a month
calendar whose days open Recordings.

**Backlog 20.** `/api/events` reads the day's sightings once (`_who_was_seen`),
keyed by `(camera, day, HH-MM-SS)` of the clip path — split on either slash,
because sightings stored Windows backslashes — and adds `people` (current
names, unnamed as "unknown", named first) and `animals` (labels other than
person) to each event. The card shows `People: …; … · Animals: …`.

**Window removal.** `ui.py` deleted; from `cameras.py`: `run_window`,
`window_size`, `WINDOW`, `REDRAW_SECONDS`, `Camera.status`, the `Core`'s
`draw`/`panels`/`mosaic`. `make_panel` stays (the web's live view). The
window flags log "The OpenCV window was removed; the interface is the web
page: <url>" and start as usual.

## 2. Data-format impact

- `config.json`: new optional key `write_pin` (written once the PIN is set, or
  by any save, as `""`). Older versions keep it (R11).
- `faces/gallery.json`: optional `views` and `pending` per person; crops in a
  new folder `faces/views/`. An older version ignores both keys and only ever
  appends embeddings, so after a rollback the alignment still holds (the new
  views it adds get `None`); a rollback merge drops the source's queue.
- `faces/views/` is skipped by everything that walks `faces/` by day
  (`days_with_faces` parses folder names as dates; `_repoint_sightings` looks
  for `*/*.json`, and `views/` holds only JPEGs).
- `check_data.py` now checks `views` and `pending`. It passed on the test
  copy's old gallery and on a new one written by a real scan, and on events
  (174) and `config.json`.

**For the deploy (CONTEXTO 14.4):** the architect deletes production's
`faces/`; the new gallery then fills with views that have photos. The PIN is
unset after the deploy: writes from the user's other computer are refused
until it is set on the M900 itself (Settings, Other devices).

## 3. Suggested documentation updates

- **ARQUITETURA 17 (web)**: R24 (middleware, headers, PIN, pairing, why the
  header defeats cross-site forgery); the People routes and page; `people`/
  `animals` on events; the window gone; the `<template>` link pitfall below.
- **ARQUITETURA 10 (faces)**: `views`, `pending`, `faces/views/`, `_take`,
  `remove_view`, the queue cap; merge no longer drops views.
- **ARQUITETURA 19 (data)**: the new optional keys and folder, and the
  rollback reasoning above.
- **ARQUITETURA 9 (the OpenCV window)**: historical now; `ui.py` is gone.
- **CONTEXTO 8**: backlog 19 and 20 done; backlog 3 complete; 9 (undo a
  merge) matters more now that merging is one click.
- **CONTEXTO 10 / README**: `--window` no longer opens a window.
- **CONTEXTO 13.4**: R24 done.

## 4. Worth explaining to the user

- Middleware: code that wraps every request, like a servlet `Filter` or
  ASP.NET middleware; why a custom header stops cross-site forgery (CORS
  preflight); `hmac.compare_digest` and timing attacks.
- `localStorage`, and why the PIN is per browser.
- Parallel lists kept aligned by index (`embeddings` / `views`), and
  `views_of` padding with `None` so old files still read.
- HTTP 409 Conflict as "ask the user first", then resend with `merge: true`.
- `<template>` content lives in an inert document: setting `a.href = "#x"`
  there resolves against `about:blank` — use `setAttribute`.
- `re.split(r"[\\/]", ...)` for paths stored on Windows.

## 5. Measurements

R24 on the test copy (network side through the M900's own LAN address,
192.168.0.18:8766): no header 403 even from 127.0.0.1; no PIN set 403; PIN
from the network refused; bad PIN format 400; missing or wrong PIN 403; right
PIN 200, including a settings write; pairing through the page works; GETs
stay open; the PIN is in no reply.

Backlog 19 on the test copy (faces and config backed up and restored): the
old gallery shows 3 and 8 views as "no photo"; with an empty gallery a real
dense scan of the 22:29 copy created a person with 2 views, both with
photos, named from the page; renaming to an existing name gave 409, then
merged (Izabel 8 → 12 views), removing a view 12 → 11; 45 reinforcements of
one person: 40 views + 7 queued, removal pulls one from the queue; the files
in `faces/views/` matched views plus queue exactly.

Backlog 20: 13 of 139 events of 30/09 show people.

## 6. What the review should look at hardest

1. **R24's threat model.** The PIN travels in clear over HTTP on the home
   network and sits in `localStorage`; good against a guest's phone and a
   forged request, not against someone sniffing the Wi-Fi. `write_pin` is
   plaintext in `config.json`, like the bot token.
2. **Gallery alignment.** Every path that touches `embeddings` must keep
   `views` aligned; I routed them all through `_take` and `remove_view`.
   `rename`'s `_absorb` merges via `_merge`, so it is covered. Worth a
   second look, and worth a test (R6).
3. **Merges are one click away now** ("Belongs to…", rename) and cannot be
   undone (backlog 9). The page confirms each one.
4. `--window` users: the bat files never used it; only someone typing it.

## 7. Not done

Nothing of the plan. Not added: storing the person spans (R22 left it), and
a way to set the PIN other than from the M900's own page.

## 8. Usage

| | 5-hour window | Weekly | Context |
|---|---|---|---|
| Start (~14:35) | 43% (resets 18:20) | 48% | 412k tokens |
| End (~15:30) | 62% | 50% | ~505k tokens |

Per item: R24 43→48, backlog 19 48→58, backlog 20 58→60, window removal
60→62. A fourth session in the same conversation: every turn carried
400-500k of context.
