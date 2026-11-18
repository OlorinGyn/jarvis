# HANDOFF — developer session 35: backlog 46's measurement

Nothing that runs on production changed in this session. The scan was only
refactored, and the tool reads production in place without writing to it.

## 1. Items done

**Step 1: the scan's finding is reusable without writing.** Commit `3e10c31`.
`faces._scan_clip` is now three pieces:

- `observe(frames, busy, sides, stop)`: frames → face observations. It
  contains the old loop: the pause, `faces_in`, the person check and the side
  views. A new `stop(kept)` callback ends the reading after a frame.
- `matches(gallery, observations)`: a generator that groups the observations,
  picks the best view, matches each group against the gallery and applies the
  three skips: a single-view unknown face, a person already seen here, and a
  new face equal to an earlier new face. It writes nothing. The caller sets
  `match["person_id"]` after each yield, and the skips read that value.
- `_record(...)`: the thumbnail, `add`/`reinforce`, and the sighting file.

`sighting_of` builds a sighting's fields, and `_one_visitor` takes an optional
`merge`. The behaviour and the log lines are unchanged. Its tests are in
`tests/test_scan_split.py` (5).

**Step 2: `tools/replay_quick_pass.py`.** Commit `d7c0b56`, extended in
`08e3d8b`. It is read-only like `replay_visits.py`: the gallery is loaded and
never saved, and nothing goes to `C:\JARVIS`. The cache lives in
`%TEMP%\jarvis_quick_pass`. The tool runs at below-normal priority (R12) and
has five modes:

| Mode | What it does |
|---|---|
| `--detect` | Reads each person event's clip once, with the same frame selection the scan used. The dense windows are taken from production's log line. It caches every frame's faces (box, embedding, score, crop) and side flag, keyed by pts. |
| `--compare` | Replays the full scan and the quick passes per event through `matches` → `_one_visitor`, then through `notify.after_scan` with the visit (`replay_visits.replay`, `visits=True`). Prints identities, faces found and every differing message, and writes contact sheets. |
| `--cost N` | Times real quick passes (ffmpeg plus networks) on N events. |
| `--bench S` | Times live YOLO per frame, alone and while a pass runs beside it. |
| `--queue` | The queue simulation. |

Its tests are in `tests/test_replay_quick_pass.py` (9).

**How the quick pass picks its frames.** The developer's choice:

- It uses the frames inside the person windows: the dense windows the full
  scan used, or all sampled frames when there were none.
- It picks N of them spread evenly, the middle frame of each equal share. A
  person crossing the yard is seen at several points, not only at the start.
- It reads them in time order and stops after the first frame with a sure
  face (score ≥ `learn_threshold`, 0.4).
- Frames are chosen by real pts (ffmpeg `showinfo`) and decoded with
  `select=eq(pts\,P)+…`. Mapping frame numbers to time through the fps went
  wrong on camera pts jitter: a frame at 10.79 s fell outside its window.
  Selecting by pts was checked to give byte-identical frames.

**Variant added after the first run: "quick N else full".** The quick pass
decides the message only when it found a face. When it found none, the
event's message waits for the full scan. Section 5 explains why.

The step 3 (cost), step 4 (queue) and step 5 (span) measurements are in
section 5. This closes backlog 46's measurement. The build is for the
architect to decide.

## 2. Data-format impact

None. No file is read or written differently. The tool writes only its cache
and sheets under `%TEMP%`. `uv run python tools/check_data.py` reports "Every
file is readable by this version." The full suite passes (487), there are no
comments in the code, and `check_doc_refs` finds 0 broken references.

## 3. Suggested documentation updates

- **ARCHITECTURE, the face scan section:**
  - the split `observe` / `matches` / `_record`;
  - the `stop` callback;
  - `matches` as a generator whose skips read what the caller sets;
  - `_one_visitor`'s `merge`.
- **CONTEXT, the repository map:** `tools/replay_quick_pass.py`, with what it
  reads and that it never writes.
- **HISTORY:** this measurement, and the decision on backlog 46 that follows
  from it.
- **BACKLOG 46:** the result against criteria (a)–(c) below.

## 4. Libraries and concepts worth explaining

- **Generators with state shared with the caller.** `matches` yields a dict,
  and the caller sets `person_id` on it before asking for the next one. The
  generator then reads that value to apply its skips. The C# equivalent is an
  `IEnumerable` built with `yield return`, whose loop body mutates the item
  just returned. In Java it is an `Iterator` whose `next()` sees changes to
  the previous element.
- **`contextlib.closing`.** It turns a generator into a `with` block, so its
  `finally` (killing ffmpeg) runs even when the caller stops early. It plays
  the role of `using` in C# or try-with-resources in Java.
- **ffmpeg's `select` and `showinfo` filters, and pts.** pts is the
  presentation timestamp of a frame. The camera's timestamps are irregular,
  so "frame n ↔ n / fps" is wrong. The real pts is read from showinfo, and
  frames are selected with `eq(pts\,P)`.
- **`threading.Condition`.** A thread reads ffmpeg's stderr while the main
  thread reads stdout, and each frame waits for its pts line.
- **Discrete-event queue simulation.** One worker that is not preempted, as
  `_SCAN_LOCK` is. Jobs are taken FIFO, or quick jobs first. The simulation
  is validated by replaying today's FIFO against the log before it is trusted
  for the "after" rows.
- **`ctypes` and `SetPriorityClass`.** Calls the Win32 API directly. Child
  ffmpeg processes inherit the priority.

## 5. Measurements

**Span.** Production's events since 10/11 00:00, read in place with no write:

- 1222 person events with a clip, all joined to a scan log line.
- 543 of them had face views and were read again.
- The other 679 had 0 face views, so neither pass can find a face. Their side
  flag is taken from production's side file, assumed the same for both passes.

**Fidelity.** On the 7 events of 18/11 checked first, the cached detection
reproduced production's frames (within ±1, from the 0.1 s rounding of the
logged windows) and the same face-view count. The listings of
`C:\JARVIS\faces` and the clips, with their mtimes, were the same before and
after a run.

### (a) Messages: quick pass against the full scan, 1222 events

The sure threshold is 0.4. The gallery has 21 entries.

| Pass | Frames read (median) | Stopped on a sure face | Same identities | Faces found: both / full only / quick only | Person messages (full: 256) | Events whose messages differ |
|---|---|---|---|---|---|---|
| quick 8 | 8 | 127 of 543 | 828 | 233 / 289 / 0 | 271 | **126** (10 %) |
| quick 24 | 24 | 229 of 543 | 910 | 362 / 160 / 0 | 257 | **101** (8 %) |
| quick 8 else full | 8 | 127 | 1117 | 522 / 0 / 0 | 245 | **27** (2 %) |
| quick 24 else full | 24 | 229 | 1070 | 522 / 0 / 0 | 242 | **42** (3 %) |

The differences by class. "No face" means a side view or a best view.

| Class | q8 | q24 | q8 else full | q24 else full |
|---|---|---|---|---|
| Quick sends "no face" where the full scan stays quiet (a resident it recognised) | 53 | 35 | 5 | 6 |
| Quick sends a face or "hidden person" where the full scan stays quiet | 2 | 5 | 2 | 5 |
| The full scan sends a face; quick sends nothing (it stopped on a resident) — the follow-up would carry it | 22 | 22 | 11 | 18 |
| The full scan sends "no face" or "hidden person"; quick sends nothing | 14 | 15 | 4 | 6 |
| The full scan sends a face; quick sends "no face" or "hidden person" | 19 | 15 | 3 | 6 |
| Other kinds differ; mostly the full scan's "hidden person" against quick's "no face" | 16 | 9 | 2 | 1 |

What the contact sheets show (`%TEMP%\jarvis_quick_pass\sheets\quick_*.jpg`,
one row per differing event):

- **"No face" for a resident.** Gustavo's or Izabel's face is visible in only
  a few frames of the clip, and 8 or 24 spread frames miss them. This is the
  real cost of the quick pass deciding alone: about 4–6 extra "best view"
  messages a day.
- **"The full scan sends a face, quick sends nothing."** Here the full scan's
  "unknown face" is often a resident's own face at a bad angle. Izabel looking
  down, on 10/11 at 09-01-31, 09-25-26 and 10-06-00, is the clearest case. On
  15/11 there were guests, and the full scan itself is noisy there (Fernanda,
  Luan, Glaucia). Quick passes would be right more often than not in this
  class. Under the design, the follow-up from the full scan sends it anyway,
  as today.
- **A false stranger from the quick pass.** One case only: Back 15/11
  19-58-44. A single view of Gustavo with headphones becomes "face, unknown
  face", where the full scan's best view recognised him.
- Several of the "none / none" rows are the visit cascading: one earlier
  message, sent or not, changes `_again`/`_remember` for the next event.

### (b) Delays: start → sent of each event's first message after its scan

There are 722 events with a message after the scan. The clip counts as ready
at the event's end + 5.7 s, the 5th percentile of end → scan start.

| Row | Median | p90 | p99 |
|---|---|---|---|
| Log | 40 s | 147 s | 507 s |
| FIFO replay (today); error against the log: median 1 s, p90 4 s | 39 s | 140 s | 503 s |
| **quick 8 first, no pause** | **28 s** | **71 s** | **155 s** |
| quick 8 first, with pause | 31 s | 84 s | 160 s |
| **quick 24 first, no pause** | **29 s** | **72 s** | **167 s** |
| quick 24 first, with pause | 36 s | 89 s | 169 s |
| quick 8 else full, no pause | 39 s | 126 s | 529 s |
| quick 8 else full, with pause | 50 s | 239 s | 803 s |
| quick 24 else full, no pause | 40 s | 124 s | 547 s |
| quick 24 else full, with pause | 54 s | 222 s | 884 s |
| The full scans' follow-ups, quick 8 / quick 24, no pause | 42 / 43 s | 148 / 157 s | 530 / 549 s |

Notes on the simulation:

- The full scans keep their logged duration, pause included. I also tried
  modelling their pause from the recording spans: it missed the log by 5 s at
  the median and 62 s at p90 (pessimistic), so it is printed only as a check.
- The same busy model is used for the quick pass's pause, so the "with pause"
  rows are pessimistic too.
- A paused quick pass holds the single worker, and that is why the "else full,
  with pause" rows get worse than today.

### (c) Cost on the M900 (step 3)

The quick passes were real, with ffmpeg and the networks, on 40 events spread
over the span:

| Pass | Median | p90 | Fit |
|---|---|---|---|
| quick 8 | 1.5 s | 2.0 s | 1.41 s + 0.003 s × frames read |
| quick 24 | 2.1 s | 3.2 s | 1.49 s + 0.046 s × frames read |
| full scan (same events, cached detection) | 14.6 s | 37.3 s | |

About 1.4 s is fixed: ffmpeg opening the clip and decoding up to the last
chosen frame.

YOLO per live frame, measured with production running beside it, over 60 s
per row:

| Beside | Median | p90 | Slowdown |
|---|---|---|---|
| nothing | 248 ms | 266 ms | — |
| quick 8, run back to back | 531 ms | 727 ms | 2.1× |
| quick 24, run back to back | 454 ms | 707 ms | 1.8× |
| full scan | 441 ms | 613 ms | 1.8× (R21 measured 1.6×) |

A quick pass costs live analysis as much per second as a full scan, a little
more for quick 8, whose time is mostly ffmpeg decoding. It lasts about 1.5–2
s per event instead of about 15 s, roughly a tenth of a full scan's harm.

### The developer's recommendation

1. **Criteria (a) and (b) are not met together by any variant.**
   - When the quick pass decides alone, the delays fall a lot: p90 from 147 s
     to 71 s, p99 from 507 s to 155 s. But 8–10 % of events change message,
     most of them extra "best view" messages for residents. That is not
     "almost no message differently".
   - When the quick pass decides only on a face (else full), the messages
     barely change: 27 events, 2 %. But the delays stay as today, because
     most messages are "no face" or "hidden person" and wait for the full
     scan.

   I would not build backlog 46 as specified.
2. **If the architect builds it anyway, the size should be 24, with no
   pause.**
   - 24 frames changes 25 fewer messages than 8 when deciding alone, with the
     same delay (p90 72 s against 71 s) and 0.6 s more work.
   - The pause adds 3–7 s at the median and holds the worker. The live cost of
     1.5–2 s at 1.8× is small next to the full scan that R23 protects against.
3. **A cheaper direction the numbers point at.**
   - Three quarters of the wait is the queue behind other events' full scans.
   - "Quick first" only helps because it jumps that queue.
   - An event whose message does not depend on faces could jump it without
     any quick pass: a dog-only event or a "hidden person" decided by the
     tracks. This is untested here, only an observation.

## 6. What the review should look at hardest

- **Does `matches` match the old loop?** Above all: the skips reading
  `person_id` after each yield; `new_here` getting references only for new
  faces; the order by weight.
  - `test_the_scan_records_what_matches_found` covers the pairing, and the
    whole suite passed unchanged.
  - The 18/11 replay reproduced production's face-view counts.
- **The dry `_one_visitor`.** It uses `merge=lambda ids: ids[0]` instead of
  `merge_unnamed`, and a new face gets `person_id=""` with its memory views.
  It approximates the merge without writing.
- **The 0-view assumption.** 679 events are not read again. Their side flag
  is production's, assumed identical for both passes.
- **The ready-offset calibration.** The 5th percentile of end → scan start
  is 5.7 s, against the code's `ASSEMBLY_DELAY` 6 s and `POST_SECONDS` 5 s.
  The FIFO replay reproduces the log within 1 s at the median and 4 s at p90.
- **The bench ran beside production's own load, at below-normal priority.**
  Production's scan runs at normal priority in the same process as the live
  loop, so read the ratios, not the absolute milliseconds.

## 7. Items of the plan not done

None. The build is not part of this session (BACKLOG 3).

## 8. Usage

| | 5-hour window | Weekly |
|---|---|---|
| Start | 17 % | 25 % |
| Before the reset at 06:20Z | 28 % | |
| New window, at the end | 5 % | 27 % |

The detection ran 2.5 h in the background and cost nothing while it ran. The
session cost about 16 points across the two windows. Context at the end:
about 135k tokens. It was compacted once, during the detection.

## Appendix: every differing message

Each line gives the event, then the full scan's messages and identities, then
the quick pass's messages and identities.

<details><summary>quick 24 — 101 events</summary>

```
Back/2026-11-10/00-47-04: full [] | ('sure Gustavo Henrique Gomes',)  quick ['Back best view'] | ('none',)
Back/2026-11-10/08-59-45: full [] | ('none',)  quick ['Back side view'] | ('none',)
Back/2026-11-10/09-01-31: full ['Back face, unknown face'] | ('probable Izabel', 'unknown face')  quick [] | ('probable Izabel',)
Back/2026-11-10/09-25-06: full ['Back hidden person'] | ('probable Izabel',)  quick ['Back side view'] | ('none',)
Back/2026-11-10/09-25-26: full ['Back face, unknown face'] | ('sure Izabel', 'unknown face')  quick [] | ('sure Izabel',)
Back/2026-11-10/10-06-00: full ['Back face, unknown face'] | ('sure Gustavo Henrique Gomes', 'sure Izabel', 'unknown face')  quick [] | ('probable Izabel', 'sure Gustavo Henrique Gomes')
Front/2026-11-10/10-24-40: full [] | ('probable Gustavo Henrique Gomes',)  quick ['Front side view'] | ('none',)
Back/2026-11-10/10-26-28: full ['Back best view'] | ('none',)  quick [] | ('none',)
Front/2026-11-10/10-30-24: full [] | ('probable Gustavo Henrique Gomes',)  quick ['Front side view'] | ('none',)
Front/2026-11-10/10-30-36: full ['Front side view'] | ('none',)  quick [] | ('none',)
Back/2026-11-10/10-36-34: full ['Back face, Visitor 2, unknown face'] | ('sure Gustavo Henrique Gomes', 'unknown face Visitor 2')  quick [] | ('probable Gustavo Henrique Gomes',)
Back/2026-11-10/11-54-33: full [] | ('sure Izabel',)  quick ['Back best view'] | ('none',)
Back/2026-11-10/11-59-25: full ['Back face, unknown face'] | ('probable Izabel', 'unknown face')  quick [] | ('probable Izabel',)
Back/2026-11-10/12-02-19: full ['Back face, unknown face'] | ('sure Izabel', 'unknown face')  quick [] | ('probable Izabel',)
Back/2026-11-10/12-03-19: full [] | ('sure Izabel', 'unknown face')  quick ['Back hidden person'] | ('probable Izabel',)
Back/2026-11-10/12-38-54: full [] | ('probable Izabel',)  quick ['Back side view'] | ('none',)
Back/2026-11-10/14-23-56: full ['Back side view'] | ('none',)  quick [] | ('none',)
Front/2026-11-10/14-55-25: full ['Front face, unknown face'] | ('sure Izabel', 'unknown face')  quick ['Front hidden person'] | ('sure Izabel',)
Front/2026-11-10/15-34-51: full ['Front face, Visitor 4, unknown face'] | ('sure Izabel', 'unknown face Visitor 4')  quick [] | ('sure Izabel',)
Front/2026-11-10/15-38-47: full ['Front face, probably Dhaniel'] | ('probable Dhaniel', 'sure Izabel')  quick [] | ('none',)
Back/2026-11-10/16-02-40: full ['Back face, unknown face'] | ('sure Izabel', 'unknown face')  quick [] | ('sure Izabel',)
Back/2026-11-10/17-38-09: full [] | ('probable Gustavo Henrique Gomes',)  quick ['Back side view'] | ('none',)
Back/2026-11-10/17-56-09: full [] | ('probable Gustavo Henrique Gomes',)  quick ['Back best view'] | ('none',)
Front/2026-11-10/23-31-00: full [] | ('probable Gustavo Henrique Gomes',)  quick ['Front best view'] | ('none',)
Back/2026-11-10/23-32-38: full [] | ('sure Izabel',)  quick ['Back best view'] | ('none',)
Back/2026-11-10/23-43-15: full [] | ('probable Gustavo Henrique Gomes', 'probable Izabel')  quick ['Back hidden person'] | ('probable Gustavo Henrique Gomes',)
Back/2026-11-11/00-54-12: full ['Back hidden person'] | ('probable Gustavo Henrique Gomes',)  quick ['Back best view'] | ('none',)
Back/2026-11-11/14-09-48: full ['Back face, unknown face'] | ('sure Gustavo Henrique Gomes', 'unknown face')  quick ['Back hidden person'] | ('sure Gustavo Henrique Gomes',)
Back/2026-11-11/17-05-20: full [] | ('probable Gustavo Henrique Gomes',)  quick ['Back side view'] | ('none',)
Back/2026-11-11/17-05-54: full ['Back best view'] | ('none',)  quick [] | ('none',)
Back/2026-11-11/21-25-10: full [] | ('none',)  quick ['Back best view'] | ('none',)
Back/2026-11-11/21-42-37: full [] | ('probable Gustavo Henrique Gomes',)  quick ['Back side view'] | ('none',)
Back/2026-11-11/22-47-08: full ['Back face, unknown face'] | ('sure Gustavo Henrique Gomes', 'unknown face')  quick [] | ('probable Gustavo Henrique Gomes',)
Back/2026-11-12/13-53-37: full ['Back face, unknown face'] | ('probable Gustavo Henrique Gomes', 'unknown face')  quick ['Back hidden person'] | ('probable Gustavo Henrique Gomes',)
Back/2026-11-12/15-52-28: full [] | ('none',)  quick ['Back best view'] | ('none',)
Front/2026-11-12/16-58-47: full [] | ('probable Gustavo Henrique Gomes',)  quick ['Front best view'] | ('none',)
Back/2026-11-13/15-02-36: full [] | ('sure Gustavo Henrique Gomes',)  quick ['Back side view'] | ('none',)
Back/2026-11-13/18-37-47: full ['Back face, Visitor 4, unknown face'] | ('sure Gustavo Henrique Gomes', 'unknown face Visitor 4')  quick [] | ('probable Gustavo Henrique Gomes',)
Back/2026-11-13/18-37-58: full ['Back hidden person'] | ('probable Gustavo Henrique Gomes',)  quick ['Back best view'] | ('none',)
Front/2026-11-14/01-18-43: full [] | ('probable Gustavo Henrique Gomes',)  quick ['Front best view'] | ('none',)
Front/2026-11-14/14-21-16: full [] | ('probable Gustavo Henrique Gomes',)  quick ['Front side view'] | ('none',)
Front/2026-11-14/14-52-12: full [] | ('sure Gustavo Henrique Gomes',)  quick ['Front best view'] | ('none',)
Front/2026-11-14/22-34-21: full [] | ('probable Gustavo Henrique Gomes',)  quick ['Front best view'] | ('none',)
Front/2026-11-14/22-39-21: full ['Front best view'] | ('none',)  quick [] | ('none',)
Front/2026-11-15/02-19-32: full [] | ('probable Gustavo Henrique Gomes',)  quick ['Front face, unknown face'] | ('unknown face',)
Front/2026-11-15/02-24-11: full ['Front face, Karol recognized'] | ('sure Gustavo Henrique Gomes', 'sure Karol')  quick ['Front face, probably Karol'] | ('probable Gustavo Henrique Gomes', 'probable Karol')
Back/2026-11-15/02-47-43: full ['Back face, Karol recognized'] | ('sure Gustavo Henrique Gomes', 'sure Karol')  quick ['Back hidden person'] | ('sure Gustavo Henrique Gomes',)
Front/2026-11-15/03-28-32: full ['Front face, unknown face'] | ('sure Gustavo Henrique Gomes', 'unknown face')  quick ['Front hidden person'] | ('probable Gustavo Henrique Gomes',)
Front/2026-11-15/16-14-30: full ['Front face, unknown face'] | ('unknown face',)  quick ['Front side view'] | ('none',)
Back/2026-11-15/16-21-27: full [] | ('sure Gustavo Henrique Gomes',)  quick ['Back side view'] | ('none',)
Back/2026-11-15/17-04-12: full ['Back face, probably Fernanda'] | ('probable Fernanda',)  quick [] | ('none',)
Back/2026-11-15/17-17-24: full ['Back face, probably Glaucia'] | ('probable Glaucia', 'sure Fernanda')  quick ['Back face, Fernanda recognized'] | ('sure Fernanda',)
Back/2026-11-15/17-20-50: full ['Back face, unknown face', 'Back face, probably Luan'] | ('probable Luan', 'sure Fernanda', 'unknown face')  quick [] | ('probable Fernanda',)
Back/2026-11-15/17-33-20: full ['Back face, unknown face'] | ('probable Gustavo Henrique Gomes', 'probable Izabel', 'sure Fernanda', 'sure Luan', 'unknown face')  quick [] | ('probable Gustavo Henrique Gomes', 'sure Fernanda')
Front/2026-11-15/17-35-21: full ['Front face, probably Fernanda'] | ('probable Fernanda', 'probable Izabel')  quick ['Front side view'] | ('none',)
Front/2026-11-15/19-47-44: full ['Front face, Luan recognized'] | ('sure Gustavo Henrique Gomes', 'sure Luan')  quick ['Front best view'] | ('none',)
Front/2026-11-15/19-47-59: full ['Front hidden person'] | ('probable Luan', 'sure Gustavo Henrique Gomes')  quick ['Front face, Luan recognized'] | ('sure Luan',)
Back/2026-11-15/19-54-47: full [] | ('probable Gustavo Henrique Gomes',)  quick ['Back best view'] | ('none',)
Back/2026-11-15/19-55-48: full ['Back best view'] | ('none',)  quick [] | ('none',)
Back/2026-11-15/19-58-44: full [] | ('sure Gustavo Henrique Gomes',)  quick ['Back face, unknown face'] | ('unknown face',)
Back/2026-11-15/21-39-36: full ['Back face, unknown face'] | ('sure Gustavo Henrique Gomes', 'unknown face')  quick [] | ('sure Gustavo Henrique Gomes',)
Back/2026-11-15/22-22-30: full [] | ('sure Gustavo Henrique Gomes',)  quick ['Back side view'] | ('none',)
Back/2026-11-16/00-47-46: full [] | ('probable Gustavo Henrique Gomes',)  quick ['Back best view'] | ('none',)
Back/2026-11-16/00-48-38: full ['Back best view'] | ('none',)  quick [] | ('none',)
Back/2026-11-16/01-00-41: full ['Back hidden person'] | ('probable Gustavo Henrique Gomes',)  quick ['Back side view'] | ('none',)
Back/2026-11-16/13-52-55: full [] | ('probable Gustavo Henrique Gomes',)  quick ['Back side view'] | ('none',)
Back/2026-11-16/13-53-13: full ['Back best view'] | ('none',)  quick [] | ('none',)
Back/2026-11-16/14-20-55: full [] | ('probable Gustavo Henrique Gomes',)  quick ['Back side view'] | ('none',)
Back/2026-11-16/19-28-18: full [] | ('probable Gustavo Henrique Gomes',)  quick ['Back best view'] | ('none',)
Back/2026-11-16/19-28-38: full ['Back best view'] | ('none',)  quick [] | ('none',)
Front/2026-11-16/20-22-29: full ['Front face, probably Bruno'] | ('probable Bruno',)  quick ['Front best view'] | ('none',)
Back/2026-11-16/20-31-17: full ['Back face, probably Miguel'] | ('probable Gustavo Henrique Gomes', 'probable Miguel')  quick ['Back hidden person'] | ('sure Gustavo Henrique Gomes',)
Front/2026-11-16/20-33-57: full ['Front face, probably Natália'] | ('probable Natália', 'sure Gustavo Henrique Gomes')  quick ['Front best view'] | ('none',)
Front/2026-11-16/21-09-21: full ['Front hidden person'] | ('probable Gustavo Henrique Gomes',)  quick ['Front best view'] | ('none',)
Back/2026-11-16/22-02-12: full ['Back face, unknown face'] | ('unknown face',)  quick [] | ('none',)
Back/2026-11-16/23-08-43: full ['Back face, unknown face'] | ('sure Gustavo Henrique Gomes', 'unknown face')  quick [] | ('sure Gustavo Henrique Gomes',)
Back/2026-11-16/23-25-44: full [] | ('probable Gustavo Henrique Gomes',)  quick ['Back side view'] | ('none',)
Back/2026-11-17/01-28-50: full ['Back face, unknown face'] | ('probable Gustavo Henrique Gomes', 'unknown face')  quick [] | ('none',)
Front/2026-11-17/08-58-23: full ['Front face, unknown face', 'Front face, probably Ana Claudia'] | ('probable Ana Claudia', 'unknown face')  quick ['Front best view'] | ('none',)
Back/2026-11-17/09-00-11: full [] | ('sure Izabel',)  quick ['Back face, unknown face'] | ('unknown face',)
Back/2026-11-17/09-05-27: full ['Back hidden person'] | ('probable Izabel',)  quick [] | ('probable Izabel', 'unknown face')
Back/2026-11-17/09-19-33: full ['Back face, unknown face'] | ('probable Izabel', 'unknown face')  quick [] | ('probable Izabel',)
Back/2026-11-17/09-59-53: full ['Back best view'] | ('none',)  quick [] | ('none',)
Back/2026-11-17/11-38-17: full ['Back side view'] | ('none',)  quick [] | ('none',)
Back/2026-11-17/12-25-05: full ['Back best view'] | ('none',)  quick [] | ('none',)
Back/2026-11-17/13-54-47: full [] | ('none',)  quick ['Back side view'] | ('none',)
Front/2026-11-17/14-24-39: full [] | ('none',)  quick ['Front side view'] | ('none',)
Front/2026-11-17/14-27-22: full ['Front hidden person'] | ('probable Izabel',)  quick ['Front side view'] | ('none',)
Front/2026-11-17/14-59-25: full ['Front face, unknown face'] | ('probable Izabel', 'unknown face')  quick [] | ('none',)
Front/2026-11-17/15-18-20: full [] | ('probable Izabel',)  quick ['Front best view'] | ('none',)
Front/2026-11-17/15-18-51: full ['Front side view'] | ('none',)  quick [] | ('none',)
Back/2026-11-17/15-50-51: full ['Back face, Dhaniel recognized'] | ('sure Dhaniel', 'sure Izabel')  quick [] | ('sure Izabel',)
Back/2026-11-17/16-14-40: full [] | ('sure Izabel',)  quick ['Back side view'] | ('none',)
Front/2026-11-17/20-11-39: full ['Front face, unknown face'] | ('sure Gustavo Henrique Gomes', 'unknown face')  quick [] | ('sure Gustavo Henrique Gomes',)
Front/2026-11-17/20-30-18: full [] | ('none',)  quick ['Front best view'] | ('none',)
Back/2026-11-17/21-06-02: full [] | ('probable Gustavo Henrique Gomes',)  quick ['Back side view'] | ('none',)
Back/2026-11-17/21-06-26: full ['Back best view'] | ('none',)  quick [] | ('none',)
Back/2026-11-17/21-46-17: full ['Back face, unknown face'] | ('unknown face',)  quick ['Back side view'] | ('none',)
Front/2026-11-17/23-45-05: full ['Front face, unknown face'] | ('unknown face',)  quick ['Front best view'] | ('none',)
Front/2026-11-18/00-05-59: full [] | ('sure Gustavo Henrique Gomes',)  quick ['Front best view'] | ('none',)
Back/2026-11-18/02-29-55: full ['Back face, unknown face'] | ('probable Gustavo Henrique Gomes', 'unknown face')  quick ['Back side view'] | ('none',)
```

</details>

<details><summary>quick 8 — 126 events</summary>

```
Back/2026-11-10/00-47-04: full [] | ('sure Gustavo Henrique Gomes',)  quick ['Back best view'] | ('none',)
Back/2026-11-10/08-59-45: full [] | ('none',)  quick ['Back side view'] | ('none',)
Back/2026-11-10/09-01-31: full ['Back face, unknown face'] | ('probable Izabel', 'unknown face')  quick [] | ('none',)
Front/2026-11-10/09-05-52: full [] | ('sure Izabel',)  quick ['Front best view'] | ('none',)
Back/2026-11-10/09-25-06: full ['Back hidden person'] | ('probable Izabel',)  quick ['Back side view'] | ('none',)
Back/2026-11-10/09-25-26: full ['Back face, unknown face'] | ('sure Izabel', 'unknown face')  quick [] | ('sure Izabel',)
Back/2026-11-10/10-06-00: full ['Back face, unknown face'] | ('sure Gustavo Henrique Gomes', 'sure Izabel', 'unknown face')  quick [] | ('probable Izabel', 'sure Gustavo Henrique Gomes')
Front/2026-11-10/10-24-40: full [] | ('probable Gustavo Henrique Gomes',)  quick ['Front side view'] | ('none',)
Front/2026-11-10/10-30-24: full [] | ('probable Gustavo Henrique Gomes',)  quick ['Front side view'] | ('none',)
Front/2026-11-10/10-30-36: full ['Front side view'] | ('none',)  quick [] | ('none',)
Back/2026-11-10/10-36-34: full ['Back face, Visitor 2, unknown face'] | ('sure Gustavo Henrique Gomes', 'unknown face Visitor 2')  quick [] | ('probable Gustavo Henrique Gomes',)
Back/2026-11-10/11-54-33: full [] | ('sure Izabel',)  quick ['Back best view'] | ('none',)
Back/2026-11-10/11-59-25: full ['Back face, unknown face'] | ('probable Izabel', 'unknown face')  quick [] | ('none',)
Back/2026-11-10/12-02-19: full ['Back face, unknown face'] | ('sure Izabel', 'unknown face')  quick [] | ('none',)
Back/2026-11-10/12-03-19: full [] | ('sure Izabel', 'unknown face')  quick ['Back best view'] | ('none',)
Back/2026-11-10/12-38-54: full [] | ('probable Izabel',)  quick ['Back side view'] | ('none',)
Back/2026-11-10/14-23-56: full ['Back side view'] | ('none',)  quick [] | ('none',)
Back/2026-11-10/14-41-05: full [] | ('sure Izabel',)  quick ['Back side view'] | ('none',)
Front/2026-11-10/14-55-25: full ['Front face, unknown face'] | ('sure Izabel', 'unknown face')  quick ['Front best view'] | ('none',)
Front/2026-11-10/15-34-51: full ['Front face, Visitor 4, unknown face'] | ('sure Izabel', 'unknown face Visitor 4')  quick [] | ('sure Izabel',)
Front/2026-11-10/15-38-47: full ['Front face, probably Dhaniel'] | ('probable Dhaniel', 'sure Izabel')  quick [] | ('none',)
Back/2026-11-10/16-02-40: full ['Back face, unknown face'] | ('sure Izabel', 'unknown face')  quick ['Back side view'] | ('none',)
Back/2026-11-10/17-38-09: full [] | ('probable Gustavo Henrique Gomes',)  quick ['Back side view'] | ('none',)
Back/2026-11-10/17-56-09: full [] | ('probable Gustavo Henrique Gomes',)  quick ['Back best view'] | ('none',)
Back/2026-11-10/17-56-39: full ['Back hidden person'] | ('sure Gustavo Henrique Gomes',)  quick ['Back best view'] | ('none',)
Front/2026-11-10/18-44-42: full [] | ('sure Gustavo Henrique Gomes',)  quick ['Front best view'] | ('none',)
Front/2026-11-10/23-31-00: full [] | ('probable Gustavo Henrique Gomes',)  quick ['Front best view'] | ('none',)
Back/2026-11-10/23-32-38: full [] | ('sure Izabel',)  quick ['Back best view'] | ('none',)
Front/2026-11-10/23-35-08: full ['Front hidden person'] | ('sure Gustavo Henrique Gomes',)  quick ['Front side view'] | ('none',)
Back/2026-11-10/23-43-15: full [] | ('probable Gustavo Henrique Gomes', 'probable Izabel')  quick ['Back hidden person'] | ('probable Gustavo Henrique Gomes',)
Back/2026-11-11/00-54-12: full ['Back hidden person'] | ('probable Gustavo Henrique Gomes',)  quick ['Back best view'] | ('none',)
Back/2026-11-11/12-44-33: full [] | ('sure Gustavo Henrique Gomes',)  quick ['Back best view'] | ('none',)
Back/2026-11-11/14-09-48: full ['Back face, unknown face'] | ('sure Gustavo Henrique Gomes', 'unknown face')  quick ['Back hidden person'] | ('sure Gustavo Henrique Gomes',)
Back/2026-11-11/14-51-42: full [] | ('sure Gustavo Henrique Gomes',)  quick ['Back side view'] | ('none',)
Back/2026-11-11/17-05-20: full [] | ('probable Gustavo Henrique Gomes',)  quick ['Back best view'] | ('none',)
Back/2026-11-11/17-05-54: full ['Back best view'] | ('none',)  quick [] | ('none',)
Back/2026-11-11/21-24-55: full [] | ('sure Gustavo Henrique Gomes',)  quick ['Back best view'] | ('none',)
Back/2026-11-11/21-42-37: full [] | ('probable Gustavo Henrique Gomes',)  quick ['Back best view'] | ('none',)
Back/2026-11-11/22-47-08: full ['Back face, unknown face'] | ('sure Gustavo Henrique Gomes', 'unknown face')  quick [] | ('none',)
Back/2026-11-12/13-53-37: full ['Back face, unknown face'] | ('probable Gustavo Henrique Gomes', 'unknown face')  quick ['Back side view'] | ('none',)
Front/2026-11-12/15-50-38: full ['Front hidden person'] | ('sure Gustavo Henrique Gomes',)  quick ['Front side view'] | ('none',)
Back/2026-11-12/15-52-28: full [] | ('none',)  quick ['Back best view'] | ('none',)
Front/2026-11-12/16-53-06: full [] | ('sure Gustavo Henrique Gomes',)  quick ['Front side view'] | ('none',)
Front/2026-11-13/13-56-49: full [] | ('probable Gustavo Henrique Gomes',)  quick ['Front side view'] | ('none',)
Back/2026-11-13/15-02-36: full [] | ('sure Gustavo Henrique Gomes',)  quick ['Back best view'] | ('none',)
Back/2026-11-13/18-37-47: full ['Back face, Visitor 4, unknown face'] | ('sure Gustavo Henrique Gomes', 'unknown face Visitor 4')  quick [] | ('none',)
Back/2026-11-13/18-37-58: full ['Back hidden person'] | ('probable Gustavo Henrique Gomes',)  quick ['Back best view'] | ('none',)
Back/2026-11-13/19-51-00: full [] | ('sure Gustavo Henrique Gomes',)  quick ['Back side view'] | ('none',)
Back/2026-11-13/20-29-40: full [] | ('sure Gustavo Henrique Gomes',)  quick ['Back best view'] | ('none',)
Front/2026-11-14/01-18-43: full [] | ('probable Gustavo Henrique Gomes',)  quick ['Front best view'] | ('none',)
Back/2026-11-14/13-12-55: full [] | ('sure Gustavo Henrique Gomes',)  quick ['Back side view'] | ('none',)
Front/2026-11-14/14-21-16: full [] | ('probable Gustavo Henrique Gomes',)  quick ['Front side view'] | ('none',)
Front/2026-11-14/14-52-12: full [] | ('sure Gustavo Henrique Gomes',)  quick ['Front best view'] | ('none',)
Front/2026-11-14/22-34-21: full [] | ('probable Gustavo Henrique Gomes',)  quick ['Front best view'] | ('none',)
Front/2026-11-14/22-39-21: full ['Front best view'] | ('none',)  quick [] | ('none',)
Front/2026-11-15/02-24-11: full ['Front face, Karol recognized'] | ('sure Gustavo Henrique Gomes', 'sure Karol')  quick ['Front best view'] | ('none',)
Front/2026-11-15/02-31-18: full [] | ('sure Karol',)  quick ['Front face, Karol recognized'] | ('sure Karol',)
Back/2026-11-15/02-47-43: full ['Back face, Karol recognized'] | ('sure Gustavo Henrique Gomes', 'sure Karol')  quick ['Back hidden person'] | ('sure Gustavo Henrique Gomes',)
Front/2026-11-15/03-28-32: full ['Front face, unknown face'] | ('sure Gustavo Henrique Gomes', 'unknown face')  quick ['Front best view'] | ('none',)
Front/2026-11-15/16-14-30: full ['Front face, unknown face'] | ('unknown face',)  quick ['Front side view'] | ('none',)
Back/2026-11-15/16-21-27: full [] | ('sure Gustavo Henrique Gomes',)  quick ['Back best view'] | ('none',)
Front/2026-11-15/16-55-11: full ['Front face, Luan recognized', 'Front face, Fernanda recognized'] | ('sure Fernanda', 'sure Luan')  quick ['Front face, Fernanda recognized'] | ('sure Fernanda',)
Back/2026-11-15/17-04-12: full ['Back face, probably Fernanda'] | ('probable Fernanda',)  quick [] | ('none',)
Back/2026-11-15/17-17-24: full ['Back face, probably Glaucia'] | ('probable Glaucia', 'sure Fernanda')  quick ['Back face, Fernanda recognized'] | ('sure Fernanda',)
Back/2026-11-15/17-20-50: full ['Back face, unknown face', 'Back face, probably Luan'] | ('probable Luan', 'sure Fernanda', 'unknown face')  quick [] | ('probable Fernanda',)
Back/2026-11-15/17-33-20: full ['Back face, unknown face'] | ('probable Gustavo Henrique Gomes', 'probable Izabel', 'sure Fernanda', 'sure Luan', 'unknown face')  quick [] | ('probable Gustavo Henrique Gomes', 'sure Fernanda')
Front/2026-11-15/17-34-51: full [] | ('sure Izabel',)  quick ['Front side view'] | ('none',)
Front/2026-11-15/17-35-21: full ['Front face, probably Fernanda'] | ('probable Fernanda', 'probable Izabel')  quick ['Front side view'] | ('none',)
Front/2026-11-15/19-47-44: full ['Front face, Luan recognized'] | ('sure Gustavo Henrique Gomes', 'sure Luan')  quick ['Front best view'] | ('none',)
Front/2026-11-15/19-47-59: full ['Front hidden person'] | ('probable Luan', 'sure Gustavo Henrique Gomes')  quick ['Front face, probably Luan'] | ('probable Luan',)
Front/2026-11-15/19-50-31: full ['Front face, probably Fernanda', 'Front face, Visitor 34, unknown face'] | ('probable Fernanda', 'unknown face Visitor 34')  quick ['Front face, probably Fernanda'] | ('probable Fernanda',)
Back/2026-11-15/19-54-47: full [] | ('probable Gustavo Henrique Gomes',)  quick ['Back best view'] | ('none',)
Back/2026-11-15/19-55-48: full ['Back best view'] | ('none',)  quick [] | ('none',)
Back/2026-11-15/21-39-36: full ['Back face, unknown face'] | ('sure Gustavo Henrique Gomes', 'unknown face')  quick [] | ('none',)
Back/2026-11-15/22-22-30: full [] | ('sure Gustavo Henrique Gomes',)  quick ['Back best view'] | ('none',)
Back/2026-11-15/23-26-33: full [] | ('sure Gustavo Henrique Gomes',)  quick ['Back side view'] | ('none',)
Back/2026-11-16/00-47-46: full [] | ('probable Gustavo Henrique Gomes',)  quick ['Back best view'] | ('none',)
Back/2026-11-16/00-48-38: full ['Back best view'] | ('none',)  quick [] | ('none',)
Back/2026-11-16/01-00-41: full ['Back hidden person'] | ('probable Gustavo Henrique Gomes',)  quick ['Back side view'] | ('none',)
Back/2026-11-16/13-52-55: full [] | ('probable Gustavo Henrique Gomes',)  quick ['Back side view'] | ('none',)
Back/2026-11-16/13-53-13: full ['Back best view'] | ('none',)  quick [] | ('none',)
Back/2026-11-16/14-20-55: full [] | ('probable Gustavo Henrique Gomes',)  quick ['Back side view'] | ('none',)
Front/2026-11-16/17-30-53: full [] | ('probable Gustavo Henrique Gomes',)  quick ['Front side view'] | ('none',)
Back/2026-11-16/19-28-18: full [] | ('probable Gustavo Henrique Gomes',)  quick ['Back best view'] | ('none',)
Back/2026-11-16/19-28-38: full ['Back best view'] | ('none',)  quick [] | ('none',)
Front/2026-11-16/20-15-04: full ['Front face, Bruno recognized'] | ('probable Gustavo Henrique Gomes', 'sure Bruno')  quick ['Front side view'] | ('none',)
Back/2026-11-16/20-20-37: full ['Back face, Miguel recognized'] | ('sure Gustavo Henrique Gomes', 'sure Miguel')  quick ['Back best view'] | ('none',)
Front/2026-11-16/20-22-29: full ['Front face, probably Bruno'] | ('probable Bruno',)  quick ['Front best view'] | ('none',)
Back/2026-11-16/20-31-17: full ['Back face, probably Miguel'] | ('probable Gustavo Henrique Gomes', 'probable Miguel')  quick ['Back hidden person'] | ('sure Gustavo Henrique Gomes',)
Front/2026-11-16/20-33-57: full ['Front face, probably Natália'] | ('probable Natália', 'sure Gustavo Henrique Gomes')  quick ['Front best view'] | ('none',)
Front/2026-11-16/21-09-21: full ['Front hidden person'] | ('probable Gustavo Henrique Gomes',)  quick ['Front best view'] | ('none',)
Back/2026-11-16/22-02-12: full ['Back face, unknown face'] | ('unknown face',)  quick [] | ('none',)
Back/2026-11-16/23-08-43: full ['Back face, unknown face'] | ('sure Gustavo Henrique Gomes', 'unknown face')  quick [] | ('sure Gustavo Henrique Gomes',)
Back/2026-11-16/23-25-44: full [] | ('probable Gustavo Henrique Gomes',)  quick ['Back side view'] | ('none',)
Back/2026-11-17/01-28-50: full ['Back face, unknown face'] | ('probable Gustavo Henrique Gomes', 'unknown face')  quick [] | ('none',)
Front/2026-11-17/08-58-23: full ['Front face, unknown face', 'Front face, probably Ana Claudia'] | ('probable Ana Claudia', 'unknown face')  quick ['Front best view'] | ('none',)
Back/2026-11-17/09-19-33: full ['Back face, unknown face'] | ('probable Izabel', 'unknown face')  quick [] | ('probable Izabel',)
Back/2026-11-17/09-59-53: full ['Back best view'] | ('none',)  quick [] | ('none',)
Back/2026-11-17/10-58-13: full ['Back hidden person'] | ('probable Izabel',)  quick ['Back side view'] | ('none',)
Front/2026-11-17/11-28-39: full [] | ('sure Gustavo Henrique Gomes',)  quick ['Front side view'] | ('none',)
Back/2026-11-17/11-38-17: full ['Back side view'] | ('none',)  quick [] | ('none',)
Back/2026-11-17/12-25-05: full ['Back best view'] | ('none',)  quick [] | ('none',)
Back/2026-11-17/13-54-47: full [] | ('none',)  quick ['Back side view'] | ('none',)
Front/2026-11-17/14-22-18: full [] | ('sure Gustavo Henrique Gomes',)  quick ['Front side view'] | ('none',)
Front/2026-11-17/14-27-22: full ['Front hidden person'] | ('probable Izabel',)  quick ['Front best view'] | ('none',)
Back/2026-11-17/14-36-55: full [] | ('sure Izabel',)  quick ['Back side view'] | ('none',)
Front/2026-11-17/14-59-25: full ['Front face, unknown face'] | ('probable Izabel', 'unknown face')  quick [] | ('none',)
Front/2026-11-17/15-18-20: full [] | ('probable Izabel',)  quick ['Front best view'] | ('none',)
Front/2026-11-17/15-18-51: full ['Front side view'] | ('none',)  quick [] | ('none',)
Front/2026-11-17/15-38-31: full [] | ('probable Gustavo Henrique Gomes', 'probable Izabel')  quick ['Front side view'] | ('none',)
Front/2026-11-17/15-42-47: full ['Front side view'] | ('none',)  quick [] | ('none',)
Back/2026-11-17/15-50-51: full ['Back face, Dhaniel recognized'] | ('sure Dhaniel', 'sure Izabel')  quick [] | ('probable Izabel',)
Back/2026-11-17/15-51-49: full [] | ('none',)  quick ['Back best view'] | ('none',)
Back/2026-11-17/16-14-40: full [] | ('sure Izabel',)  quick ['Back best view'] | ('none',)
Back/2026-11-17/19-18-51: full ['Back hidden person'] | ('sure Gustavo Henrique Gomes',)  quick ['Back best view'] | ('none',)
Front/2026-11-17/20-11-39: full ['Front face, unknown face'] | ('sure Gustavo Henrique Gomes', 'unknown face')  quick [] | ('sure Gustavo Henrique Gomes',)
Front/2026-11-17/20-30-18: full [] | ('none',)  quick ['Front best view'] | ('none',)
Back/2026-11-17/21-06-02: full [] | ('probable Gustavo Henrique Gomes',)  quick ['Back side view'] | ('none',)
Back/2026-11-17/21-06-26: full ['Back best view'] | ('none',)  quick [] | ('none',)
Back/2026-11-17/21-06-58: full ['Back hidden person'] | ('probable Gustavo Henrique Gomes',)  quick ['Back best view'] | ('none',)
Back/2026-11-17/21-46-17: full ['Back face, unknown face'] | ('unknown face',)  quick ['Back best view'] | ('none',)
Front/2026-11-17/22-15-12: full [] | ('sure Gustavo Henrique Gomes',)  quick ['Front best view'] | ('none',)
Front/2026-11-17/22-20-08: full ['Front face, unknown face'] | ('unknown face',)  quick [] | ('none',)
Front/2026-11-17/23-45-05: full ['Front face, unknown face'] | ('unknown face',)  quick ['Front best view'] | ('none',)
Front/2026-11-18/00-05-59: full [] | ('sure Gustavo Henrique Gomes',)  quick ['Front best view'] | ('none',)
Back/2026-11-18/02-29-55: full ['Back face, unknown face'] | ('probable Gustavo Henrique Gomes', 'unknown face')  quick ['Back best view'] | ('none',)
```

</details>

<details><summary>quick 24 else full — 42 events</summary>

```
Back/2026-11-10/08-59-45: full [] | ('none',)  quick ['Back side view'] | ('none',)
Back/2026-11-10/09-01-31: full ['Back face, unknown face'] | ('probable Izabel', 'unknown face')  quick [] | ('probable Izabel',)
Back/2026-11-10/09-25-26: full ['Back face, unknown face'] | ('sure Izabel', 'unknown face')  quick [] | ('sure Izabel',)
Back/2026-11-10/10-06-00: full ['Back face, unknown face'] | ('sure Gustavo Henrique Gomes', 'sure Izabel', 'unknown face')  quick [] | ('probable Izabel', 'sure Gustavo Henrique Gomes')
Back/2026-11-10/10-26-28: full ['Back best view'] | ('none',)  quick [] | ('none',)
Back/2026-11-10/10-36-34: full ['Back face, Visitor 2, unknown face'] | ('sure Gustavo Henrique Gomes', 'unknown face Visitor 2')  quick [] | ('probable Gustavo Henrique Gomes',)
Back/2026-11-10/11-59-25: full ['Back face, unknown face'] | ('probable Izabel', 'unknown face')  quick [] | ('probable Izabel',)
Back/2026-11-10/12-02-19: full ['Back face, unknown face'] | ('sure Izabel', 'unknown face')  quick [] | ('probable Izabel',)
Back/2026-11-10/12-03-19: full [] | ('sure Izabel', 'unknown face')  quick ['Back hidden person'] | ('probable Izabel',)
Back/2026-11-10/14-23-56: full ['Back side view'] | ('none',)  quick [] | ('none',)
Front/2026-11-10/14-55-25: full ['Front face, unknown face'] | ('sure Izabel', 'unknown face')  quick ['Front hidden person'] | ('sure Izabel',)
Front/2026-11-10/15-34-51: full ['Front face, Visitor 4, unknown face'] | ('sure Izabel', 'unknown face Visitor 4')  quick [] | ('sure Izabel',)
Back/2026-11-10/16-02-40: full ['Back face, unknown face'] | ('sure Izabel', 'unknown face')  quick [] | ('sure Izabel',)
Back/2026-11-10/23-43-15: full [] | ('probable Gustavo Henrique Gomes', 'probable Izabel')  quick ['Back hidden person'] | ('probable Gustavo Henrique Gomes',)
Back/2026-11-11/14-09-48: full ['Back face, unknown face'] | ('sure Gustavo Henrique Gomes', 'unknown face')  quick ['Back hidden person'] | ('sure Gustavo Henrique Gomes',)
Back/2026-11-11/21-25-10: full [] | ('none',)  quick ['Back best view'] | ('none',)
Back/2026-11-11/22-47-08: full ['Back face, unknown face'] | ('sure Gustavo Henrique Gomes', 'unknown face')  quick [] | ('probable Gustavo Henrique Gomes',)
Back/2026-11-12/13-53-37: full ['Back face, unknown face'] | ('probable Gustavo Henrique Gomes', 'unknown face')  quick ['Back hidden person'] | ('probable Gustavo Henrique Gomes',)
Back/2026-11-12/15-52-28: full [] | ('none',)  quick ['Back best view'] | ('none',)
Back/2026-11-13/18-37-47: full ['Back face, Visitor 4, unknown face'] | ('sure Gustavo Henrique Gomes', 'unknown face Visitor 4')  quick [] | ('probable Gustavo Henrique Gomes',)
Front/2026-11-15/02-19-32: full [] | ('probable Gustavo Henrique Gomes',)  quick ['Front face, unknown face'] | ('unknown face',)
Front/2026-11-15/02-24-11: full ['Front face, Karol recognized'] | ('sure Gustavo Henrique Gomes', 'sure Karol')  quick ['Front face, probably Karol'] | ('probable Gustavo Henrique Gomes', 'probable Karol')
Back/2026-11-15/02-47-43: full ['Back face, Karol recognized'] | ('sure Gustavo Henrique Gomes', 'sure Karol')  quick ['Back hidden person'] | ('sure Gustavo Henrique Gomes',)
Front/2026-11-15/03-28-32: full ['Front face, unknown face'] | ('sure Gustavo Henrique Gomes', 'unknown face')  quick ['Front hidden person'] | ('probable Gustavo Henrique Gomes',)
Back/2026-11-15/17-17-24: full ['Back face, probably Glaucia'] | ('probable Glaucia', 'sure Fernanda')  quick [] | ('sure Fernanda',)
Back/2026-11-15/17-20-50: full ['Back face, unknown face', 'Back face, probably Luan'] | ('probable Luan', 'sure Fernanda', 'unknown face')  quick [] | ('probable Fernanda',)
Back/2026-11-15/17-33-20: full ['Back face, unknown face'] | ('probable Gustavo Henrique Gomes', 'probable Izabel', 'sure Fernanda', 'sure Luan', 'unknown face')  quick [] | ('probable Gustavo Henrique Gomes', 'sure Fernanda')
Back/2026-11-15/19-58-44: full [] | ('sure Gustavo Henrique Gomes',)  quick ['Back face, unknown face'] | ('unknown face',)
Back/2026-11-15/21-39-36: full ['Back face, unknown face'] | ('sure Gustavo Henrique Gomes', 'unknown face')  quick [] | ('sure Gustavo Henrique Gomes',)
Back/2026-11-16/20-31-17: full ['Back face, probably Miguel'] | ('probable Gustavo Henrique Gomes', 'probable Miguel')  quick ['Back hidden person'] | ('sure Gustavo Henrique Gomes',)
Back/2026-11-16/23-08-43: full ['Back face, unknown face'] | ('sure Gustavo Henrique Gomes', 'unknown face')  quick [] | ('sure Gustavo Henrique Gomes',)
Back/2026-11-17/09-00-11: full [] | ('sure Izabel',)  quick ['Back face, unknown face'] | ('unknown face',)
Back/2026-11-17/09-05-27: full ['Back hidden person'] | ('probable Izabel',)  quick [] | ('probable Izabel', 'unknown face')
Back/2026-11-17/09-19-33: full ['Back face, unknown face'] | ('probable Izabel', 'unknown face')  quick [] | ('probable Izabel',)
Back/2026-11-17/09-59-53: full ['Back best view'] | ('none',)  quick [] | ('none',)
Back/2026-11-17/11-38-17: full ['Back side view'] | ('none',)  quick [] | ('none',)
Back/2026-11-17/12-25-05: full ['Back best view'] | ('none',)  quick [] | ('none',)
Back/2026-11-17/13-54-47: full [] | ('none',)  quick ['Back side view'] | ('none',)
Front/2026-11-17/14-24-39: full [] | ('none',)  quick ['Front side view'] | ('none',)
Back/2026-11-17/15-50-51: full ['Back face, Dhaniel recognized'] | ('sure Dhaniel', 'sure Izabel')  quick [] | ('sure Izabel',)
Front/2026-11-17/20-11-39: full ['Front face, unknown face'] | ('sure Gustavo Henrique Gomes', 'unknown face')  quick [] | ('sure Gustavo Henrique Gomes',)
Front/2026-11-17/20-30-18: full [] | ('none',)  quick ['Front best view'] | ('none',)
```

</details>

<details><summary>quick 8 else full — 27 events</summary>

```
Back/2026-11-10/08-59-45: full [] | ('none',)  quick ['Back side view'] | ('none',)
Back/2026-11-10/09-25-26: full ['Back face, unknown face'] | ('sure Izabel', 'unknown face')  quick [] | ('sure Izabel',)
Back/2026-11-10/10-06-00: full ['Back face, unknown face'] | ('sure Gustavo Henrique Gomes', 'sure Izabel', 'unknown face')  quick [] | ('probable Izabel', 'sure Gustavo Henrique Gomes')
Back/2026-11-10/10-36-34: full ['Back face, Visitor 2, unknown face'] | ('sure Gustavo Henrique Gomes', 'unknown face Visitor 2')  quick [] | ('probable Gustavo Henrique Gomes',)
Back/2026-11-10/14-23-56: full ['Back side view'] | ('none',)  quick [] | ('none',)
Front/2026-11-10/15-34-51: full ['Front face, Visitor 4, unknown face'] | ('sure Izabel', 'unknown face Visitor 4')  quick [] | ('sure Izabel',)
Back/2026-11-10/23-43-15: full [] | ('probable Gustavo Henrique Gomes', 'probable Izabel')  quick ['Back hidden person'] | ('probable Gustavo Henrique Gomes',)
Back/2026-11-11/14-09-48: full ['Back face, unknown face'] | ('sure Gustavo Henrique Gomes', 'unknown face')  quick ['Back hidden person'] | ('sure Gustavo Henrique Gomes',)
Back/2026-11-12/15-52-28: full [] | ('none',)  quick ['Back best view'] | ('none',)
Back/2026-11-15/02-47-43: full ['Back face, Karol recognized'] | ('sure Gustavo Henrique Gomes', 'sure Karol')  quick ['Back hidden person'] | ('sure Gustavo Henrique Gomes',)
Front/2026-11-15/16-55-11: full ['Front face, Luan recognized', 'Front face, Fernanda recognized'] | ('sure Fernanda', 'sure Luan')  quick ['Front face, Fernanda recognized'] | ('sure Fernanda',)
Front/2026-11-15/16-57-12: full [] | ('probable Gustavo Henrique Gomes', 'sure Luan')  quick ['Front face, Luan recognized'] | ('probable Gustavo Henrique Gomes', 'sure Luan')
Back/2026-11-15/17-17-24: full ['Back face, probably Glaucia'] | ('probable Glaucia', 'sure Fernanda')  quick [] | ('sure Fernanda',)
Back/2026-11-15/17-20-50: full ['Back face, unknown face', 'Back face, probably Luan'] | ('probable Luan', 'sure Fernanda', 'unknown face')  quick [] | ('probable Fernanda',)
Back/2026-11-15/17-33-20: full ['Back face, unknown face'] | ('probable Gustavo Henrique Gomes', 'probable Izabel', 'sure Fernanda', 'sure Luan', 'unknown face')  quick [] | ('probable Gustavo Henrique Gomes', 'sure Fernanda')
Front/2026-11-15/19-50-31: full ['Front face, probably Fernanda', 'Front face, Visitor 34, unknown face'] | ('probable Fernanda', 'unknown face Visitor 34')  quick ['Front face, probably Fernanda'] | ('probable Fernanda',)
Back/2026-11-16/20-31-17: full ['Back face, probably Miguel'] | ('probable Gustavo Henrique Gomes', 'probable Miguel')  quick ['Back hidden person'] | ('sure Gustavo Henrique Gomes',)
Back/2026-11-16/23-08-43: full ['Back face, unknown face'] | ('sure Gustavo Henrique Gomes', 'unknown face')  quick [] | ('sure Gustavo Henrique Gomes',)
Back/2026-11-17/09-19-33: full ['Back face, unknown face'] | ('probable Izabel', 'unknown face')  quick [] | ('probable Izabel',)
Back/2026-11-17/09-59-53: full ['Back best view'] | ('none',)  quick [] | ('none',)
Back/2026-11-17/11-38-17: full ['Back side view'] | ('none',)  quick [] | ('none',)
Back/2026-11-17/12-25-05: full ['Back best view'] | ('none',)  quick [] | ('none',)
Back/2026-11-17/13-54-47: full [] | ('none',)  quick ['Back side view'] | ('none',)
Back/2026-11-17/15-50-51: full ['Back face, Dhaniel recognized'] | ('sure Dhaniel', 'sure Izabel')  quick [] | ('probable Izabel',)
Back/2026-11-17/15-51-49: full [] | ('none',)  quick ['Back best view'] | ('none',)
Front/2026-11-17/20-11-39: full ['Front face, unknown face'] | ('sure Gustavo Henrique Gomes', 'unknown face')  quick [] | ('sure Gustavo Henrique Gomes',)
Front/2026-11-17/20-30-18: full [] | ('none',)  quick ['Front best view'] | ('none',)
```

</details>
