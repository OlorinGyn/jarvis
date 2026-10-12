# Handoff - developer to architect

Developer session 13, 12/10/2026, started by the architect ("Dev, siga o plano
da 14.4"). Plan: backlog 25 (a) → (f), then R41 if there was room. All done,
in that order. 158 tests pass (92 at the start of session 12's review, 97 at
the start of this one).

## 1. Items done

| Commit | Item | What and why |
|---|---|---|
| `3fae548` | 25 (a) | **Resident tag.** `Gallery.set_resident` (named entries only, refused for unnamed), optional `"resident": true` in `gallery.json`, removed when switched off. `_merge` makes the target a resident when the source was, so a rename that merges keeps it either way; a plain rename never touches it. Switch on the person and dog pages (hidden while unnamed), a "Resident" badge on the grid card. The face scan's result now carries `resident`, so the notifier needs no gallery reload. Shared by People and Dogs through the base `Gallery`. |
| `7b33be1` | 25 (b), (c), (d) | **Cases, modes, the held person message.** New `modes.py`: the seven cases, the three modes, the defaults, `normalised`, `allowed`, `holds_person`, `describe`. `settings.load()` always returns whole `notify_mode`/`notify_modes`. `notify.event` takes `(words, case)` parts and returns `(sent, held)`; `notify.after_scan` sends every post-scan message (faces by case; with no face, the side view or best view as `faceless_person`). `notify.person_case`: only a **sure** (`score >= LEARN_THRESHOLD`) match of a resident is `resident_person`; a "probably" match of a resident is `known_person`. `dogs.identify` replaces `words_for`: (words, resident) per dog, resident only on a sure match. `clips.EventRecorder` keeps `person_held`; `_notify_late` applies the same rules, and also marks the hold when a person arrives after a message already went out (a dog's). |
| `593ebac` | 25 (e) | **Notifications tab.** Table: cases × modes, each cell `<input type="checkbox" role="switch">` styled in CSS; the active mode as a segmented radio group at the top; the active column tinted. Each switch posts `{"notify_modes": {mode: {case: bool}}}` at once; the server merges it over the stored switches and refuses unknown modes/cases and non-booleans. The Telegram form moved here from Settings; the old per-label checkboxes are gone (`notify_labels` is still accepted by the API, but nothing on the page edits it). Checked in the built-in browser at desktop width and at 375 px (fits, no horizontal scroll). |
| `a1061f9` | 25 (f) | **Commands from the phone.** New `bot.py`: `Poller` thread, `getUpdates` long polling (50 s), `allowed_updates` message + callback_query. Only `notify_chat` is obeyed; another chat is logged ("ignored a message from chat N") and its taps answered empty. `/home`, `/away`, `/silent` → `settings.update(notify_mode=…)` and a reply from `modes.describe`; `/mode` → the current mode with an inline keyboard (`mode:<name>` callbacks); any other `/command` → help; plain text → nothing. `setMyCommands` once per token. Commands older than 120 s are not obeyed (`STALE_SECONDS`), so a restart does not replay yesterday's `/away`. Trouble (network, 409, any other refusal, an unexpected exception) is logged once per distinct problem and retried with backoff 5 → 300 s; a 409 waits 120 s each time. `main()` starts it after the cameras open and stops it on exit; without a token it only sleeps (30 s) and re-reads the config. **Find chat** now reads the chats the running poller saw (`bot.last_chat()`), falling back to the old direct `getUpdates` when no poller runs (the test copy). |
| `f4fe810` | R41 | **A view move names the photo it was shown.** `faces.ViewsChanged` and `_check_view`: `remove_view`, `demote_view`, `promote_view`, `remove_waiting` and `set_cover` take `expected=None` and check it **inside `_GALLERY_LOCK`**, so a scan cannot slip in between check and change. The web routes take an optional body `{"view": "<name>"}` and answer 409 "the views changed: the page was refreshed"; the page sends the name from each tile's photo URL ("" for a view without a photo) and reloads the person on a 409. Reproduced first: the acceptance test answered 200 and deleted the neighbour before the fix. |

## 2. Data-format impact

All additive:

- `faces/gallery.json`, `dogs/gallery.json`: optional `"resident": true` per entry. An older version ignores it; it survives an older version's saves because the entry dict is written back whole.
- `config.json`: new optional keys `notify_mode` (`"home"`/`"away"`/`"silent"`) and `notify_modes` (`{mode: {case: bool}}`). `notify_labels` stays and is still read: it builds the default switches when `notify_modes` is absent. An older version keeps the new keys on save: `settings.save` in `v2026.10.11.6` already keeps every key it does not know. Note: once this version saves any setting, `notify_modes` is written in full.
- `check_data.py` now also checks `resident` is a bool, `notify_mode` is a known mode, `notify_modes` is a dict of dicts of bools, and that the modes can be built. Result on the test copy: **every file readable** (214 events, 7 people, 22 dogs, 1 report, config.json 11 keys after the page tests wrote the two new ones). Not run against production's data: run it in `C:\JARVIS` at deploy as usual.

## 3. Suggested documentation updates

- **CONTEXTO 8**, backlog 25: done, with the commits; R41 in 13.14 closed.
- **ARQUITETURA 12** (notifications): a new subsection for the modes — the seven cases, the defaults table (Away all person cases on; Home = Away minus the two resident cases; Silent all off; animals from `notify_labels`), the timing rule and how `after_scan` decides (a held person's faceless message answers to the camera cooldown; a held face message claims it). And one for the bot: long polling, one reader, 409, stale commands, the command list.
- **ARQUITETURA 17** (web): the Notifications tab; the move routes' optional `view` body and the 409.
- **ARQUITETURA 19** (data formats): `resident`, `notify_mode`, `notify_modes`.
- **INSTALACAO** (Telegram setup): Find chat is now on the Notifications tab, and works while production polls.
- Production checklist for the deploy (acceptance on the M900): mark the user, Mirana and Aurora Resident; in Home a recognised resident sends nothing and a person with no face does; `/away` from the phone changes the mode the page shows; look in `jarvis.log` for `Telegram commands:` lines (one warning at most if anything goes wrong).

## 4. Worth explaining to the user

- **Long polling** (`getUpdates` with `timeout`): the request stays open until a message arrives or 50 s pass, so the phone's command arrives in about a second with no port opened — the opposite direction of a webhook. Java/C# analogy: a blocking `take()` on a queue, but over HTTP.
- **Why only one reader**: Telegram hands each update to whoever asks first and forgets it after the next `offset`; a second reader gets 409. That is why Find chat now asks the poller instead of Telegram.
- **`threading.Event.wait(seconds)`** as an interruptible sleep: `stop()` sets the event and the thread wakes at once. Like `CountDownLatch.await(timeout)`.
- **Optimistic concurrency** (R41): the client sends what it saw, the server refuses when it changed — the same idea as an ETag / `If-Match` or a row version in Entity Framework.
- **`role="switch"` on a checkbox** + `appearance: none` and a `::before` knob: a real form control (keyboard, screen reader) drawn as a switch, no library.
- Tuples as multiple return values (`sent, held = notify.event(...)`), like a C# `(bool sent, bool held)` tuple.

## 5. Measurements

- Tests: 97 at the start → **158** (+61): the rules matrix alone is 21 (7 cases × 3 modes); `test_bot.py` 12; `test_modes_web.py` 10; `test_view_moves.py` 4; resident in `test_gallery.py` 5; the rest in `test_notify.py`.
- Diff `57101a7..f4fe810`: 19 files, +1459 / −135.
- No CPU measurement: the poller is one idle HTTP connection; the dog matching at event start costs what `words_for` cost before (same GrabCut, same place).

## 6. What the review should look at hardest

1. **The held-person rules in `notify.after_scan` and `clips`.** In particular: (i) a held message with faces claims the camera cooldown only when something was sent — a clip whose only face is a silenced resident claims nothing; (ii) **if the scan finds a resident's face and a second person in the same clip has no recognisable face, nothing is sent**: the scan cannot tell, and the faceless message only goes when there are no faces at all. This contradicts the spirit of "a stranger in the dark must reach the phone" in one corner; decide if it is acceptable or needs a rule (e.g. persons counted by YOLO vs faces found). (iii) A held person whose clip assembly fails (no segments) sends nothing at all — today's code had the same gap for follow-ups, but now it is the person's only message.
2. **Away is today's behaviour?** I believe yes: all person cases on → not held → immediate message, faces always (per-person cooldown), side/best only after a sent event. One difference: `faces_seen` now filters before taking the first 3 faces (`MAX_FACES`), so a silenced resident no longer uses up one of the three slots.
3. **`bot.py` against the real Bot API**: it could not be exercised here — the test copy has no token by design. The form fields (`allowed_updates` and `reply_markup` as JSON strings, `commands` for `setMyCommands`) follow the Bot API docs, but the first real run is the deploy. Watch `jarvis.log` right after it.
4. `_notify_late` now updates `notify_tried` even after a sent message (it used to return first); harmless, but it changes the old early return.
5. R41: a view whose stored path does not match `SAFE_VIEW` gets no photo URL, so the page sends "" while the server sees a name → always 409 for that view. Every view is stored by `_store_view` (12 hex), so I believe it cannot happen; the check could instead compare against `_photo_url`.
6. `notify_labels` is no longer editable on the page. If the user wanted "other animals" to mean only cats, that granularity is gone (one switch for every non-dog animal), as backlog 25 (b) specified.

## 7. Not done

Nothing from the plan. R30 (b) still waits for a second named person (14.4).
The test copy's `config.json` now holds `notify_mode: "away"` and the default
`notify_modes` (written by the page tests); everything else as before.

## 8. Usage

| | 5-hour window | Weekly | Context |
|---|---|---|---|
| Start (≈14:00) | 6 % | 90 % | 73k |
| After 25 (a)–(d) | 15 % | 91 % | 191k |
| After 25 (e) | 18 % | 92 % | 220k |
| After 25 (f) | 20 % | 92 % | 236k |
| End (after R41) | 23 % | 92 % | 252k |

About 17 points of the 5-hour window and 2 of the week for the whole of
backlog 25 plus R41: (a)–(d) 9, (e) 3, (f) 2, R41 3.
