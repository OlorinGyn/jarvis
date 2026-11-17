# HANDOFF — developer 30 (17/11/2026)

The plan of BACKLOG 3, "Developer 30", in its order: R63, backlog 41, the
month replayed, R62. All four done; 384 tests (348 before).

## 1. Items done

### R63 — a failed send is tried again (`ac24be1`)

- `notify._call` returns `(ok, detail, wait)`: `wait` is `None` when trying
  again cannot help, else the seconds to wait — Telegram's `retry_after` on a
  429, 0 (the policy's pause) for a time-out, a refused or reset connection,
  a 5xx or an answer that is not JSON. Any other 4xx, and a photo that cannot
  be read, is not retried.
- `notify._post` is one attempt (the old body of `send`); `send` keeps its
  `(ok, detail)` and stays one attempt — the page's test button.
- `_send_logged` makes the first attempt **on the caller's thread**, as
  before, so the camera watch and the assembly threads keep their timing and
  their return values; a failure that may pass starts `_retry` in a daemon
  thread of its own: pauses `RETRY_PAUSES = (5, 15, 30, 60)`, five attempts in
  about 110 s. Every failed attempt leaves a WARNING line:
  `Notification Back best view: failed, attempt 1 of 5, trying again in 5 s: <detail>`,
  the last `…attempt 5 of 5, gave up: …`, a 4xx `…failed, attempt N, not tried again: …`;
  a success after a failure `…: sent, attempt 2` (or `sent silently, attempt 2`).
- The loud/silent decision is made once, before the first attempt; a retry
  keeps it.
- Written by hand, not urllib3's `Retry` (already installed under requests):
  urllib3 logs its retries with the request URL, which holds the bot token,
  and Telegram's `retry_after` is in the JSON body. Logged as a bias candidate
  only if the architect disagrees (PROCESS 5).
- Tests: `tests/test_retry.py` (11) — a fake Telegram at `requests.post` that
  fails once by a read time-out, a 500, a refused connection or a non-JSON
  502, then answers; the growing pause and the give-up line; 429 waiting 7 s;
  400 not retried; the same fields and photo on every attempt; the token never
  in the log; the test button one attempt. The fixtures of `test_notify.py`
  and `test_outage.py` now stub `_post` instead of `send`.

### Backlog 41 — notifications by visit (`071e55b`), R59's rule with it

In `notify.after_scan`, only when `held` and the mode is Home:

- **(a)** `tracks.dog_only(summary)`: every track with person frames is voted
  dog and its `longest_person_run` < `PERSON_RUN` (2). Such an event with no
  face sends no person message (`skipped: dog tracks`) and **does not extend
  the visit**. No tracks (`None` or `[]`) → not a dog event, as today. An
  event whose scan found faces is not judged by (a): a face is a person, and
  an unknown face always reaches the phone.
- **The visit**: per camera, `_visits[camera]`, under `_visit_lock` (its own,
  not `_lock`, which `_loud` takes while delivering). An event joins when its
  start is less than `VISIT_SECONDS` (300) after the visit's end and its end
  less than 300 s before the visit's start; otherwise a new visit replaces it
  — except a scan finishing late for an event older than the current visit,
  which gets a throwaway visit and leaves the current one alone. The visit
  holds start, end, the last sure resident recognised (name, time), whether
  it sent, the most people at once, and the face entries (`person_id`) seen.
  Decision and update happen in one step under the lock; sending after.
- **(b)** a **sure** resident (`resident_person` case) recognised in the
  visit, this event or an earlier one, same camera, explains one body: a
  faceless message (best or side view) of an event with at most one person at
  once is not sent — `skipped: visit (Gustavo recognized at 12:00:05)`. A
  probable match explains nothing; two people never.
- **(c)** once the visit has sent (any message, a face or faceless one), a
  faceless or hidden-person message goes only with more people at once than
  the visit has seen (`skipped: visit (no news, 1 person at once)`), and a
  face only when its entry was not yet seen in the visit
  (`Notification Front face, unknown face: skipped: visit (the same face again)`).
- Unchanged: Away and Silent; the case switches; the incident and the floor;
  faces found are announced by their case. `reset_incident` forgets the
  visits too.
- `clips._assemble` passes `ended_at=end` and `tracks=` to `after_scan`;
  `EventRecorder.stop` hands the tracks over (see R62 for `decided()`).
- **Reading of the plan's test "the same event with two people at once still
  sends the hidden person"**: a faceless event with two people sends its
  faceless message (best view) as today — the hidden-person text is for an
  event with faces found; both cases are tested
  (`test_two_people_at_once_are_never_explained_by_a_name`,
  `test_the_hidden_person_beside_a_resident_still_reaches_the_phone`).
- Tests: `tests/test_visits.py` (20), one per rule and its edges (the
  5-minute boundary exactly, the other camera, a probable resident, Away, a
  late scan, threads, the assembly wiring). Three tests of `test_notify.py`
  that sent the same scan twice now put the second in a later visit.

### The month replayed — `tools/replay_visits.py` (`a044b6b`)

Read-only over `C:\JARVIS`: event JSONs, face sightings (`faces/*/*.json`,
names and resident flags from today's gallery), and the four logs. Each
logged message is joined to its event by the face scan line's clip name on
the same assembly thread (the map reset at each "Starting"). Each person
event then goes through **`notify.after_scan` itself**, Home, held, twice —
visit off (`VISIT_SECONDS = -inf`, `dog_only` false) and on — with
`_send_logged` replaced by a list and the floor's timer never fired.

    uv run python tools/replay_visits.py C:\JARVIS --since 2026-10-16T21:28

### R62 — a failing tracker (`dfd38de`)

- `tracks.Failures(label, clock)`: the first failure with its traceback;
  later ones counted, at most one WARNING a minute
  (`Tracking failed 180 more time(s) on Front in the last 60 s`); a failure
  after a quiet minute has its traceback again.
- **Decided: a failed tracker is replaced** — `Tracks.restart()` builds a
  fresh `ByteTrackTracker`, forgets the id map and keeps `next_id`, so ids stay
  unique. A bad state then lasts one run.
- `Camera.detect` returns `(moment, None)` for a failed run; `Record.add`
  counts it in `untracked_runs`; `Record.decided()` is the summary, or `None`
  when a run went untracked, so the notification decides by the boxes, never
  "no person". The event JSON gets `untracked_runs` only when above 0.
- Tests in `tests/test_tracks.py` (5 new, 1 changed).

## 2. Data-format impact

One new optional field in the event JSON, `untracked_runs` (an int, only
when a tracking run failed). Nothing else written changes; nothing read
changes. `tools/check_data.py`: "Every file is readable by this version."

## 3. Suggested documentation updates

- **ARCHITECTURE 12** (notify): the retry policy (R63) — first attempt on the
  caller's thread, retries in their own, pauses, which failures, the log
  lines; `send` one attempt for the test button.
- **ARCHITECTURE 12.11 / 22.3**: the visit (backlog 41) — the three rules as
  built, their order, the lock, the late-scan case, "sure resident only",
  "a dog event does not extend the visit", the log lines; Home only.
- **ARCHITECTURE 7.16**: tracks now act — `dog_only`, `PERSON_RUN`,
  `Failures`, `restart()`, `decided()`; **8.4**: `untracked_runs`.
- **ARCHITECTURE 22.x or HISTORY 13.33**: the replay's numbers (section 5).
- **BACKLOG**: R63, R62 and R59's rule closed; item 41 done; item 7 part 2's
  R59 piece done.
- **CONTEXT 3**: the visit is built (`v…` at the release).

## 4. Worth explaining to the user

- **Retry with backoff** — the pattern behind every reliable client, and why
  a time-out is retried even though it may duplicate (idempotency: Telegram's
  sendPhoto is not idempotent, a duplicate is the accepted price).
- **Why the first attempt stays inline**: callers keep their return value and
  timing; the slow path goes to a thread — like `Task.Run` for the retries
  while the caller gets a result now.
- **A module-level dict under a `threading.Lock`** as per-camera state (Java's
  `synchronized` block; the GIL does not make a read-decide-write atomic).
- **Decide under the lock, act outside it** — never hold a lock across the
  network, and why `_lock` and `_visit_lock` are separate (a non-reentrant
  `Lock` taken twice on one thread deadlocks; the test fixture hit exactly
  that with a timer that fired inline).
- **Monkeypatching module globals** for tests (`notify._post`, `_sleep`,
  `threading.Thread`) — and that `notify.threading` *is* the `threading`
  module, so patching it patches it everywhere.
- **A replay that runs the shipped function** instead of re-implementing the
  rule, validated by reproducing the log exactly before measuring the change.

## 5. Measurements

The month, 16/10 21:28 → 17/11 13:06, 31.7 days, 5,989 events, 4,106 with a
person:

| | messages | a day |
|---|---|---|
| log, all (sent + failed, floor and camera texts too) | 3,104 | 98 |
| log, about a person, every one joined to its event | 3,024 | 95 |
| replay, visit off | 3,024 — **no event differs in kind from the log** | 95 |
| replay, visit on, person messages | **1,027** | **32** |
| all, with the visit (80 floor and camera texts kept as they were) | 1,107 | **35** |

By kind, off → on: best view 1,816 → 464, side view 558 → 140, hidden person
181 → 89, faces 469 → 334. Not sent, by rule: best view no news 680, best
view resident 658, side view resident 266, side view no news 152, the same
face again 139 (135 messages; the rest were beyond `MAX_FACES`), hidden
person no news 92, dog tracks 14.

**Against the review** (96 → 34, HISTORY 13.33): 98 → 35 here. The 2 a day
more on each side are the 76 failed sends, counted here as messages (with
R63 they would mostly arrive) and not in the review's 3,020 sent. The
review's "R59's dog tracks alone, 95" matches: 14 dog-track messages here
(the review said 12; it counted R59's best views, this counts every
faceless message of a dog event). **Faces of a non-resident dropped: 135,
every one the same face entry again in its visit** — Home silences the
residents' faces, so every face message is a non-resident's; per the review
most of those "unknown faces" are the user's own bad views (item 43). The
floor's 72 texts would mostly go and are not simulated here.

## 6. What the review should look at hardest

- `after_scan`'s decision block: `quiet` uses `visit["sent"]` and `people`
  **before** this event is added; `resident` **after** (this event's own
  resident counts, but only matters with no faces found). Check that a
  stranger's face, or a second body, can never be silenced.
- `planned` sets `visit["sent"]` before the send; a send that fails (and is
  retried) still counts as the visit's first message — intended.
- The late-scan rule in `_visit` (a throwaway visit), and events that overlap
  by the end computed from `seconds - PRE_SECONDS`.
- `_retry` threads: unbounded in number if Telegram is down for long (one per
  failed message, each alive ≤ ~2 min). Fine at today's rate; a cap may be
  wanted.
- `dog_only` ignores detections the tracker did not give an id to; in
  `Tracks.update` every detection gets one with the thresholds at 0, but an
  untracked person frame would not stop (a). Failed runs are covered by
  `decided()`.

## 7. Not done

Nothing of the plan. Not checked live: the test copy was not started against
the cameras (the change is in the notification decision, covered by the
tests and the month's replay through the same function).

## 8. Usage

- Start: 5-hour window 20 %, weekly 3 % (resets 20:20 and 18/11 19:00 UTC);
  context 77k tokens.
- After R63 26 %, after backlog 41 30 %, after the replay 33 %, after R62
  34 %.
- End: 5-hour window 35 %, weekly 5 %; context about 230k tokens.
