# HANDOFF — developer session 36 (18/11/2026)

Plan: BACKLOG 3, "Developer 36: backlog 46 built". Steps 1–6 done, in the
plan's order except one thing: the code was written before its tests, not
after them (step "tests first"). The tests were then checked by mutation:
breaking the quick passes' priority and the follow-up's dedupe each makes
them fail (details in 6).

## 1. What was built

### `6c9d645` feat(backlog 46): a quick face pass decides the message, the full scan follows

**The quick pass, `faces.quick_scan(clip, camera, started_at, moments, tracks, gallery=None)`**
→ `(sightings, side_views)`. It reads `QUICK_FRAMES = 24` frames and writes
nothing: no thumbnail, no sighting file, no gallery change.

- **Frame choice: by frame number, from the full scan's own rates.**
  `_selection`'s arithmetic moved into `_rates(total, fps, moments)` →
  `(step, windows, dense)`. `_selection`'s output is unchanged.
  `quick_picks(total, fps, moments)` walks `n = 0..total`, keeps the frames
  the full scan reads (`n % step == 0`, or inside a window and
  `n % dense == 0`, up to the same frame limit), takes those inside the
  windows (all of them when there are no windows), and picks 24 with
  `faces.evenly`, the middle of each equal share. That is the tool's
  `spread_pick`, moved. A frame's time is taken as `n / fps`. ffmpeg then
  decodes only those frames with `select=eq(n\,a)+eq(n\,b)+…`, so there is
  no extra ffmpeg pass to learn the timestamps.
  Checked on 10 production clips, copied to the scratchpad: every frame
  read, by showinfo's `pts_time`, lies inside the logged windows (238
  frames, 0 outside). `t − n/fps` measured −0.02…+0.22 s on six clips.
- It stops after the first face on a person that matches an entry at the
  user's sure threshold: `faces.sure_stop`, moved from the tool. Its
  `found` attribute tells the log line whether the stop fired.
- `faces.quick_sightings` gives the sightings the tool's `dry_found` gave:
  a new face gets `person_id ""` and keeps its `views` and `references`,
  and one body's unnamed faces become one sighting with nothing merged.
  Each sighting carries `picture`, its face crop as JPEG bytes.
  `_one_visitor` now logs "merged" only when it really merges, not for a
  merge the quick pass only pretends.
- Log line: `  quick pass HH-MM-SS.mp4: 18 of 24 frames, 2.9 s, stopped at a sure face, 1 face(s), 0 side view(s)`.

**The turns, `faces.Turns` (`_TURNS`), replace `_SCAN_LOCK`.** A
`threading.Condition` guards three things: `_busy` (someone is running the
networks now), `_quick` (a FIFO deque of tickets for the quick passes that
are waiting) and `_full` (a Lock, one full scan at a time).
- `quick()`: the caller joins the deque and waits until nobody is busy and
  its ticket is at the head. It then holds the networks for the whole pass:
  describe, gallery load, ffmpeg, the networks and the matching.
- `turn()`: waits until nobody is busy **and no quick pass waits**, then
  holds the networks for one step.
- `full()`: the full scan's slot, held from start to end, pauses included.
  Full scans still run one at a time, as before.
- The full scan calls `observe(..., turn=_TURNS.turn)`, so it takes one
  turn per frame, covering `faces_in` and `person_boxes`. The pause
  (`_wait_while`) and the read of the next frame from ffmpeg happen
  outside the turn. Matching plus recording (gallery load, `matches`,
  `_record`, `_one_visitor`) run inside **one** turn, so the scan never
  steps aside in the middle of a write. The ffmpeg read and the pause hold
  no turn, so a quick pass runs then.
- `scanning()` is `_TURNS.active()`: `_busy`, or a full scan's slot taken.
  It is true through a full scan's pause, as it was with the lock.
  `_embed_photo` takes `_TURNS.turn()` where it took the lock.
- There is no nesting: nothing that runs inside a turn takes another one.
  `gallery.add` and `reinforce` use `face_quality` with no turn, and refit
  and migration run outside scans.

**The message, `clips._person_messages`**, called from `_assemble` once the
clip exists. When it does not, `after_scan([], …)` runs as before.
1. The quick pass runs, in the assembly thread.
2. **A face** → `after_scan(quick sightings, sent_faces=sent)` at once.
   Then the full scan runs in the same thread, then `notify.follow_up`.
3. **No face** → the full scan starts in a worker thread named
   `scan <camera> <stem>`, and the assembly thread waits with
   `worker.join(QUICK_DEADLINE_SECONDS = 45.0)`. The 45 s count from the
   end of the quick pass ("from that moment").
   - If the worker has set `scan["found"]` → `after_scan(full sightings)`,
     exactly as before, and nothing else.
   - Otherwise (the deadline): `faces.save_side_view(clip, quick_sides)`
     when the quick pass saw a side view, then `after_scan([])`, which
     sends the side view or the best view. The thread then waits for the
     worker and calls `follow_up`.
   - Only the assembly thread decides: the worker only fills a dict. Even
     when the full scan ends right at the deadline, exactly one of the two
     paths runs.
4. The full scan is `scan_clip`, unchanged, and keeps the views, sightings,
   side view and gallery alone. The one exception: at the deadline the
   quick pass's side view is written as `HH-MM-SS.side.jpg` (it is the
   message's picture). If the full scan then finds no face and has side
   views of its own, it overwrites that file, as before. If it finds faces,
   the quick pass's file stays, and the page shows the side view the phone
   got.

**The follow-up, `notify.follow_up(camera, started_at, found, sent, held, settings, people, ended_at)`.**
- `sent` holds the faces the event's message sent. `faces_seen` now fills
  it (`sent_faces`) with each face it tries to deliver: `wanted[:MAX_FACES]`,
  after the mode and visit skips.
- A full-scan face is "the same" when `_again` matches it against
  `{"faces": sent's ids, "strangers": sent's references}`: the same entry,
  or for a face with no entry the same views. Log line:
  `Notification Back face, X: skipped: sent by the quick pass`.
- Then the visit, as `after_scan`: in Home with the person held, faces the
  visit has seen are repeats. `_remember` adds every full-scan face, and
  `visit["sent"]` is set when one goes out. `faces_seen` sends the rest by
  their case.
- It never sends a faceless message (no side view, best view or hidden
  person), in any mode.

**notify accepts a picture in memory.** `_post` and `_call` take `image` as
`bytes` and send it as `face.jpg` (`PICTURE_NAME`). A retry keeps the bytes
in its closure, so no temporary file is needed. `faces_seen` sends
`thumbnail_path or picture`.

**Log lines for the architect's measurement**, all in the assembly thread:
- `  message Back 12-00-00.mp4: decided by the quick pass, 1 face(s); quick pass 2.1 s, done 2.5 s after the clip`
  (or `decided by the full scan, N face(s)` / `the deadline, no face`)
- `  follow-up Back 12-00-00.mp4: 1 of the full scan's 2 face(s) sent, 63.0 s after the clip`

"After the clip" means after the clip was assembled. The event's start is
the `HH-MM-SS` in the name. **`read_scans` in the tool pairs a scan line
with the next `Notification … sent` line of the same thread. That no longer
holds when the full scan runs in the worker (the no-face path).** Measure
the new delays from the `message`/`follow-up` lines plus the event's start,
not from that pairing.

### `5e3a668` feat(backlog 46): replay the shipped quick-pass path on the cached month

`tools/replay_quick_pass.py --built [--aside]` runs `clips._person_messages`
itself on every person event since `--since`:
- `faces.quick_scan` and `scan_clip` are answered from developer 35's cache
  (`%TEMP%\jarvis_quick_pass`). The quick frames come from the built
  `evenly` and `sure_stop`, and the sightings from `quick_sightings`.
- An event is late when its full scan ends more than 45 s after its quick
  pass, on the `--queue` schedule (quick passes first, full scans at their
  logged seconds, cost.json's fit). A late event's fake full scan sleeps
  0.4 s against a 0.2 s deadline, so the real `join` takes the deadline path.
- `--aside` gives a quick pass only the quick passes ahead of it to wait
  for, which is what the turns do. Without it, the quick pass waits for the
  whole full scan running, as review 37's simulation did.
- `SideView` stands in for the side-view file: it "exists" once a pass of
  the replay kept one.
- `spread_pick`, `sure_stop` and `dry_found` are now `faces`' functions, so
  `--compare` and `--cost` also run the shipped code. `contact_sheets`
  reads the JPEG `picture`.
- Nothing is written to production: the gallery is read-only, the send is
  replaced, and the side view is a flag in a set.

Closes backlog 46's build. The architect deploys it and measures it on
production.

## 2. Data-format impact

None. Every file keeps its format. One case writes an existing kind of file
in a new situation: `HH-MM-SS.side.jpg` from the quick pass at the deadline,
beside faces the full scan may then find. `check_data.py`: "Every file is
readable by this version."

## 3. Suggested documentation updates

- **ARCHITECTURE 10.3** (the scan): the quick pass; `_rates` and
  `quick_picks` (choice by frame number, the 0.22 s estimate, 238/0 on
  production); `Turns` replacing `_SCAN_LOCK` (quick FIFO first, the full
  scan per frame, matching plus recording in one turn, `scanning()`).
  Section 1's text above can be taken as is.
- **ARCHITECTURE 22.3 / 12.x** (person messages): the three paths (quick
  face, full within 45 s, deadline), the follow-up's dedupe and its "never
  faceless", the visit remembering the full scan's faces, and the picture
  sent from memory.
- **ARCHITECTURE** wherever `_SCAN_LOCK` is named: it is now `_TURNS`.
- **HISTORY 13.39 or the review's section**: the built replay's numbers (5).
- **BACKLOG 1, item 46**: built; production measurement pending.

## 4. Concepts worth explaining to the user

- **`threading.Condition` and `wait_for`**: a lock plus "sleep until this
  predicate is true; wake me when someone calls `notify_all`". It is Java's
  `synchronized` + `wait()`/`notifyAll()` in a `while (!cond) wait();`
  loop; `wait_for` is that loop. C#: `Monitor.Wait/PulseAll`.
- **`@contextmanager`**: a generator whose `yield` splits the code into
  "on entry" and "on exit" (the `finally` always runs), so `with
  _TURNS.quick():` works like C#'s `using` or Java's try-with-resources,
  without a class with `__enter__`/`__exit__`.
- **A deque of tickets for FIFO fairness**: Python's `Lock` promises no
  order to the threads waiting on it; the ticket at the head of the deque
  says whose turn it is.
- **`Thread.join(timeout)` as a deadline**: it returns after at most N
  seconds whether or not the thread ended; checking a result the thread
  fills in tells which happened. Only one thread decides, so there is no
  race between "the scan ended" and "the deadline passed".
- **`__fspath__`** (the replay's `SideView`): any object can be a path for
  `Path(obj)` / `open(obj)` by implementing it. It is like implementing an
  interface; here the path it gives changes with state.
- **Function attributes** (`stop.found`): a Python function is an object
  and can carry fields. It works like a lambda that captures a mutable
  holder.
- **Sending bytes in a multipart upload**: `requests` takes
  `files={"photo": (name, bytes)}`, so no file on disk is needed.

## 5. Measurements

**The real quick pass on 10 production clips** (copies, production
gallery read-only, its mtime checked unchanged): 1.4–2.9 s. Two stopped at
Izabel's sure face after 16 and 18 frames; eight read all 24 and found no
face.

**The built path on the cached month** (`--since 2026-11-10`, 1,234 person
events, 3 not in the cache; today's production gallery and config):

| Variant | Decided by | Events differing from today | Of them, the full scan's face sent as follow-up | Start → sent, median / p90 / p99 |
|---|---|---|---|---|
| today (the log, review 37) | — | — | — | 40 / 147 / 507 s |
| review 37's "else full, D 45 s" (its simulation) | — (218 at the deadline) | 54 (4.4 %) | 29 | 40 / 86 / 167 s |
| **built, `--built`** (a quick pass waits for the whole full scan running) | quick face 362, full scan 726, deadline 146 | 26 (2.1 %) | 8 | 40 / 101 / 195 s |
| **built, `--built --aside`** (as the turns behave) | quick face 362, full scan 665, deadline 207 | 28 (2.3 %) | 9 | **39 / 74 / 115 s** |

Person messages: today 259, built 270 (`--aside`).

**These rows are not review 37's, and I could not reproduce that row.** The
architect's "else full, D 45 s" was a scratch replay that is not in the
repository. Three reasons may explain the gap:
- (a) today's gallery is not this morning's;
- (b) 1,234 events against 1,222, a later end;
- (c) the deadline here counts from the end of the quick pass, not from the
  clip being ready.

In `--built` without `--aside`, (c) makes things worse: a quick pass that
waited behind a full scan's 30 s starts its 45 s late, which is why p90 is
101 s. With `--aside`, as the build behaves, the quick pass is about 2 s
long and the tail falls well below the architect's estimate: p99 115 s.
The architect wrote "the measured delays are an upper bound", and the
`--aside` row is that point measured.

**The 28 differing events (`--aside`), by class:**
- **The follow-up carries the face (9).** In 6 of them a "hidden person"
  comes before the face: the quick pass found a face the mode silences or
  the visit already had, YOLO saw more people than that, so `after_scan`
  sent "hidden person"; the full scan's other face follows (Front 10/11
  14:55:25, Back 15/11 02:47:43, Back 16/11 20:31:17…). In the other 3 a
  deadline side view comes before the face (Front 15/11 16:14:30 and
  17:35:21, Back 18/11 02:29:55).
- **A faceless message disappears (7).** The quick pass's resident face
  explains the body, or the visit's cascade changes (Back 17/11 09:59:53
  and 12:25:05, Front 17/11 15:18:51…).
- **A faceless message appears (6).** The 24 frames missed a face or saw a
  side view, and the deadline sent it (Back 13/11 15:02:36, the headphones
  case of review 37; Back 10/11 12:03:19 and 23:43:15 as "hidden person").
- **"Hidden person" becomes a side or best view (2).** Back 10/11 09:25:06
  and 13/11 18:37:58.
- **An unknown face only the quick pass sends (3).** Front 15/11 02:19:32,
  Back 15/11 19:58:44, Back 17/11 09:00:11. The full scan's grouping of
  more views did not send it.
- **Different certainty (1).** Front 15/11 02:24:11: the quick pass's
  "probably Karol" against the full scan's "Karol recognized". The full
  scan's match is then skipped as the same entry.

The full list is in the tool's output: `--built --aside`, lines starting
with four spaces.

**Tests:** 513 pass (487 before, +25 in `tests/test_quick_pass.py`, +1 in
`test_replay_quick_pass.py`). Comments in `src/` and `tools/`: 0.
`check_doc_refs`: 0.

## 6. What to look at hardest

1. **The turns** (`faces.Turns`):
   - Is there any path that takes a turn while holding one? That would
     deadlock. I found none: refit and migration run outside scans, and
     `gallery.add` does not embed.
   - `turn()` refuses while a quick pass waits. A steady stream of quick
     passes would therefore starve full scans. With ~2 s each and one per
     event, I judge that harmless.
   - The mutation checks: dropping `and not self._quick` from `turn()`
     fails `test_a_quick_pass_arriving_after_a_waiting_frame_still_goes_first`
     on every run. Dropping the ticket order is caught only now and then:
     `Condition` wakes waiters roughly in order anyway, so FIFO among quick
     passes is not reliably testable.
2. **The deadline's race** (`_person_messages`): the decision is
   `"found" in scan` after `join(45)`, made in one thread. A full scan
   ending just after that check gives a faceless message plus a follow-up,
   never two decided messages.
3. **The follow-up's dedupe** (`notify.follow_up`):
   - It dedupes against what was attempted (`wanted[:MAX_FACES]`), not
     against every quick sighting. So a probable resident the mode
     silenced in the quick message can still be sent later as a sure
     match, as today's full scan would send it.
   - A gap: a quick "new face" (no entry) that the full scan matches to an
     **existing** entry made in between by another event's full scan
     carries no views. `_again` cannot tell it is the same face. It is
     rare, since the gallery would have to change within those seconds.
4. **Gallery reads during writes:** `Gallery.load` is not atomic against
   `save`. The quick pass loads inside its own turn, and the full scan
   records inside its turn, so the two never overlap. The page's writes
   are not covered, as before this change.
5. **The two replay rows against review 37's row** (5): the counts are
   lower, and I could not rebuild the architect's scratch simulation to
   compare like with like.

## 7. Not done

Nothing in the plan is left undone. The production measurement after a day
of use is the architect's (step 6).

## 8. Usage

- 5-hour window: 8 % at the start → 23 % before this HANDOFF.
- Weekly: 30 % → 32 %.
- Context: about 250k tokens at the end, in a new conversation.
