# HANDOFF — developer session 38: backlogs 47 and 48

Plan: `docs/BACKLOG.md` 3, "Developer 38", followed in its order (48, then
47's server, then 47's page). No production data touched: the only
deletions ran on this folder's test copy, whose `faces/` and `dogs/` were
copied aside first and restored byte for byte afterwards (`diff -rq`
clean).

## 1. What was done

**`4e67fc4` — backlog 48: "Visitor N" takes the smallest free number.**

- `faces.Gallery._next_visitor` now returns the smallest N ≥ 1 that no
  entry's `temporary_name` holds: a set of held numbers and
  `next(n for n in itertools.count(1) if n not in held)`. Its callers
  (`add`, `name_visitors`) still call it under `_GALLERY_LOCK` after a
  `load()`; unchanged. In `name_visitors` each entry gets its name before
  the next is computed, so one pass never hands out a number twice.
- The header's `"visitors"` counter is neither read nor written any more;
  the `VISITORS_KEY` constant went with it (nothing else used it). A file
  that has it keeps it as it is (`header` is carried through `save()`).
- Tests (`tests/test_visitors.py`): the gap case of the plan (2, 3, 4, 21
  held → 1, then 5); a number freed by naming (`rename`), merging
  (`merge_unnamed`) and deleting (`take_out`) given again; the old counter
  left in the file unread (34 in the header, Visitor 1 given); a file
  without the counter gets none written. Three older tests asserted the
  backlog 44 rule "never reused" and were turned to the new rule:
  `test_visitors` (the first test), `test_clean_views`
  (`..._its_sightings_kept_and_its_number_freed`) and `test_forget_unseen`
  (`test_a_forgotten_visitors_number_is_given_again`).

**`72798fc` — backlog 47, server.**

- `web._delete_many(gallery, payload)`: each id of `_ids()` (so the same
  1..`BATCH_MAX` well-formed list check as assign and report), once each,
  through `gallery.take_out` — the entry leaves, its view photos are
  erased (chosen and waiting, `_all_views`). A named or unknown id comes
  back in `gone`, the way `_report_many` answers: `{"deleted": [...],
  "gone": [...]}`. When something left, one log line:
  `Deleted N unnamed face entries from the page: Visitor 21, …` (dogs:
  `unnamed dog entries`, named by id, since dogs have no temporary name).
- `web._delete(gallery, id)`: 404 for an unknown id, 400 "only an unnamed
  entry can be deleted" for a named one, else `{"deleted": id}`.
- Routes: `POST /api/persons/delete`, `POST /api/persons/{id}/delete`,
  `POST /api/dogs/delete`, `POST /api/dogs/{id}/delete`, each beside its
  `report` twin. The write guard is the `guard_writes` middleware, so they
  get it like every POST (tested: 403 from an unpaired address, 403
  without the page's header).
- `DogGallery` does not override `take_out`, `forget_views` or
  `_forget_view`; its `view_dir` is `dogs/views`. Checked by test: a dog
  deleted, its photos gone, the named dog's photos kept.
- Recordings: `take_out` does what `forget_unseen` does to an entry (out
  of `people`, its views erased, sightings and thumbnails untouched), so
  Recordings reads both alike. Tested: one event, one deleted and one
  forgotten entry, `_who_was_seen` gives `["unknown"]`.
- Tests: `tests/test_delete_entries.py`, 7 tests (unnamed face deleted
  with photos gone and sightings/thumbnails kept and the log line; deleted
  reads as forgotten; named refused 400 and unknown 404; a mixed list
  with a duplicate and an unknown id; a freed number given again; a dog;
  the write guard). Five fail on the code before this commit (the other
  two — Recordings and the guard — hold for any route).

**`f12d35a` — backlog 47, page.**

- `index.html`: "Delete" (`report select-delete`) after "Bad detection"
  in both tabs' selection bars; the phone hint now says "name, report or
  delete them below".
- `app.js`: the unnamed card gets a "Delete" beside its "Bad detection";
  both now sit in a `div.card-actions`. The bar's Delete and the card's
  ask with `confirm()` and item 47's text:
  - People, bar: "Delete 3? Their photos are erased; their recordings
    stay. If they come back, they appear as a new visitor."
  - People, card: "Delete Visitor 21? Their photos … new visitor."
  - Dogs: "Delete 1? Its photos are erased; its recordings stay." (plural:
    "Their …"), no visitor sentence.
  Then `loadList()`, and the list's result line: "Deleted 3." plus
  "N already gone or named." when the server skipped some.
- `style.css`: `.card-actions` (flex, wrap, gap 6 px; its buttons
  `flex: 1 1 auto`). The buttons reuse `.report`, the page's destructive
  style (muted, `--alarm` on hover). The phone rule
  `.unnamed-grid .report { display: none }` comes later in the file and
  still hides both on the card, so a phone reaches Delete through the bar,
  as it reaches Bad detection.

## 2. Data format

- `faces/gallery_*.json`: **additive, nothing removed.** The `"visitors"`
  counter in the header is left as found and no longer updated. A rollback
  to `v2026.11.18` computes max(counter, held) + 1, which is above every
  held number, so it can never hand out a number someone holds; it just
  resumes counting from the old counter.
- Deleting writes nothing new: it is `take_out`, the same write the
  60-day forgetting and the report already make.
- `tools/check_data.py`: "Every file is readable by this version."

## 3. Suggested documentation updates

- **ARCHITECTURE 10.17** (temporary names): the rule is now the smallest
  free number (backlog 48); the counter in the header stays in old files,
  unread, and why (the rollback). The accepted price: two "Visitor 5"
  messages in Telegram on different weeks may be two people.
- **ARCHITECTURE 10.19** (forgetting): Delete from the page does at once
  what forgetting does; same `take_out`, same reading in Recordings.
- **ARCHITECTURE, the web API section**: the four `delete` routes, their
  answer `{"deleted", "gone"}`, 400/404 for the one-entry form.
- **ARCHITECTURE, the page / gallery tabs**: Delete in the bar and on the
  wide card, the confirm texts, phones through the bar.
- **ARCHITECTURE 12** (log lines): `Deleted N unnamed face|dog entries
  from the page: …`.
- **BACKLOG 1**: strike 47 and 48.
- **README** (if it lists what the People/Dogs tabs do): Delete.

## 4. Worth explaining to the user

- **`itertools.count(1)` with `next()`** — an endless counter (like a
  `for (int n = 1; ; n++)` in Java/C#) consumed lazily: `next(n for n in
  itertools.count(1) if n not in held)` stops at the first free one. The
  `held` is a **set**, so `n not in held` is O(1), like a `HashSet<int>`.
- **`dict.fromkeys(ids)`** as an ordered de-duplicate (a
  `LinkedHashSet` in Java): the batch handles a repeated id once.
- **FastAPI middleware** — why the new routes needed no guard code: the
  `@app.middleware("http")` function runs before every request, like an
  ASP.NET Core middleware or a servlet filter.
- **`confirm()` in the browser** — the blocking yes/no dialog; why the
  page tests replaced `window.confirm` to read its text.

## 5. Measurements

- Tests: 531 after backlog 48 (+4 net), 538 after 47 (+7); all pass,
  ~27 s. Comment count 0. `check_doc_refs.py` 0 broken. (`node` is not
  installed here, so `app.js` was checked by loading it in the browser:
  no console error.)
- Page, on the test copy (`stream2`, port 8766), with three fake unnamed
  faces added for the test (the test copy's face gallery had none; the
  copy was restored afterwards):
  - 1280 px: the bar holds count, Assign to…, name, Save, Bad detection,
    Delete, Clear on one row; the card shows Bad detection and Delete side
    by side.
  - 375 px: no horizontal scroll (`scrollWidth` 375). The People bar
    wraps to three rows, 137 px tall — the list's `.selecting` padding is
    140 px, so the last row of cards still clears it, by 3 px. The Dogs
    bar (no Assign to…, nothing named) is two rows, 94 px.
  - Done through the page: the bar deleted 2 faces ("Deleted 2."), the
    card deleted 1 ("Delete Visitor 21?" asked first), the bar deleted 1
    dog. The log lines:
    `Deleted 2 unnamed face entries from the page: Visitor 25, Visitor 29`,
    `Deleted 1 unnamed face entries from the page: Visitor 21`,
    `Deleted 1 unnamed dog entries from the page: d_8ceeb97c`.
- Screenshots (this machine, scratchpad of the session):
  - `C:\Users\gusta\AppData\Local\Temp\claude\cfd12769ca7e6402\6b181545-f0c8-4037-a85a-aee5d96e288e\scratchpad\shots\desktop-people-bar.jpg`
  - `C:\Users\gusta\AppData\Local\Temp\claude\cfd12769ca7e6402\6b181545-f0c8-4037-a85a-aee5d96e288e\scratchpad\shots\desktop-people-cards-and-bar.jpg`
  - `C:\Users\gusta\AppData\Local\Temp\claude\cfd12769ca7e6402\6b181545-f0c8-4037-a85a-aee5d96e288e\scratchpad\shots\375px-people-bar.jpg`
  - `C:\Users\gusta\AppData\Local\Temp\claude\cfd12769ca7e6402\6b181545-f0c8-4037-a85a-aee5d96e288e\scratchpad\shots\375px-dogs-bar.jpg`
  The 375 px Dogs shot reads "1 selected" though `Select all` had just
  run (the bar's text read 22 a moment before); it was taken before the
  repaint. Not a defect I could reproduce.

## 6. What the review should look at hardest

- **Delete racing a face scan that matches the same entry** (10.19's race,
  now at a click). The scan thread computes a match, then calls
  `reinforce(person_id, …)`; if Delete runs in between, `reinforce`
  reloads under the lock, finds the entry gone, erases the photo it just
  stored and returns False — the same path a forgotten entry takes. The
  sighting the scan writes still names the deleted id, so it reads as
  "unknown" in Recordings. I did not test this race, nor whether a new
  Visitor forms for that clip; worth confirming nothing between `match`
  and `reinforce` assumes the entry still exists (the Telegram message
  names it by the `temporary_name` read at match time).
- **Delete while the entry's page is open on another device.** Its next
  write (name, cover, move a view) answers 404 "not found"; reloading the
  page shows "This person no longer exists; it may have been merged." —
  the merge wording, not "deleted". Not tested on two devices; I left the
  wording, the review decides.
- **The 3 px margin** of the People bar on a phone (137 px against the
  140 px padding): a longer translation or a larger system font would put
  the bar over the last cards. Perhaps the padding should follow the
  bar's real height.
- The numbers freed by naming: a named person's old Visitor number is
  given to the next stranger at once. That is the plan's rule, but the
  Telegram chat may show "Visitor 1" for Ana last week and for a stranger
  today.

## 7. Not done

Nothing of the plan left out.

## 8. Usage

- Start: 5-hour window 69 %, weekly 38 %.
- End: 5-hour window 75 %, weekly 39 % (resets 20:00 and 19:00 UTC);
  context 152 k tokens at the last reading.
