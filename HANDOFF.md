# Handoff - developer to architect

Developer session 5, 10/10/2026, about 15:40-15:50, on the M900 (`Sasori`),
following CONTEXTO 14.4. **Old conversation again** (context 509k at the
start). Production (`v2026.10.10.4`) was only read with `production.ps1
-Action status`, healthy at the start and the end. Nothing was pushed. No
shell command started with `cd` (the skill's new rule).

## 1. Items

| # | Item | Commit | State |
|---|---|---|---|
| 1 | R25 — send a found face even after a cooldown | `74fd71e` | done |
| 2 | R6 — automatic tests | `9e25534` | done: 23 tests, `uv run pytest` |

**R25.** `clips._assemble` calls `notify.faces_seen` whenever the scan found a
face, whether or not the event's first message went out. `_cooled_down(key,
settings)` now takes any key: the camera for events, `("face", person_id)` for
faces, in the same table, so `reset_cooldown` clears both and the person's
cooldown is `notify_cooldown`. `faces_seen` also checks that `person` is a
wanted label (before, the event's own message did that). The best-view
follow-up keeps its rule: only after a sent event.

**R6.** `tests/` with three files, pytest config in `pyproject.toml`
(`testpaths`), `pytest` and `httpx2` in the `dev` dependency group (this
Starlette's `TestClient` asks for `httpx2`, not `httpx`). All tests run on
temporary folders (`tmp_path`, `settings.FILE` monkeypatched) and replace
`notify.send`, so nothing touches real data or the network.

- `test_gallery.py` (8): photo per view; old persons as "no photo" staying
  aligned when reinforced; queue past 40; queue cap drops the oldest with its
  file; remove pulls the oldest waiting view; last view kept; merge keeps
  alignment, queues the overflow and carries the source's queue; files on disk
  always equal views plus queue.
- `test_web_guard.py` (7): `TestClient(client=("127.0.0.1", …))` and a LAN
  address — no header refused locally; no PIN set; PIN only set locally;
  wrong/missing/headerless PIN refused, right one writes; GETs open and free of
  the token and the PIN; settings validated per key; shutdown local only.
- `test_notify.py` (8): redaction (literal and `%3A`), wanted labels, camera
  cooldown, no token, R25's face after a cooldown, per-person cooldown, no
  faces when people are not wanted, "probably" below `LEARN_THRESHOLD`.

## 2. Data-format impact

None. `check_data.py`: every file readable.

**Dependencies:** `pytest` and `httpx2` are a dev group. `uv sync` installs the
dev group by default, and `production.ps1` runs `uv sync --frozen`, so
production will get them too (pure Python, harmless, a few MB). Use
`uv sync --frozen --no-dev` there if that matters.

## 3. Suggested documentation updates

- **ARQUITETURA 12 (notifications)**: R25's rule — faces always, one cooldown
  per person, best view only after a sent event; `_cooled_down` keys.
- **CONTEXTO 2 / 10 (rules and commands)**: `uv run pytest` next to
  `check_data`; the comment check could include `tests/`.
- **CONTEXTO 11 (biases)**: the "no tests" bias is answered for the riskiest
  parts.
- **CONTEXTO 13.4**: R6 and R25 done.

## 4. Worth explaining to the user

- pytest: plain `assert`, fixtures (`tmp_path`, `monkeypatch`) — JUnit/xUnit
  without classes; `monkeypatch.setattr` as a scoped mock.
- `TestClient`: calls the FastAPI app in-process, no port, with a chosen
  client address.
- Mutation checking: break the code on purpose and see a test fail — how I
  found that the first merge test missed the source's queue.
- A tuple as a dictionary key (`("face", person_id)`).

## 5. Measurements

R25, with stubs: an event with `notified=False` and a face found made no
call to `faces_seen` before the fix, one after; the same person twice in a row
was sent twice before, "skipped: cooldown" the second time after.

R6: 23 passed in about 3 s. Mutations: breaking the merge's queue transfer,
the header check and the per-person cooldown each made its tests fail (the
first needed a new test, now included).

## 6. What the review should look at hardest

1. **R25's volume.** Faces are now announced after cooldown events too, at
   most once per person per `notify_cooldown`. Unknown faces have their own
   `person_id` each, so two different unknowns are two messages.
2. **Dev dependencies in production** (section 2).
3. The tests cover rules, not the camera pipeline; the replay tool remains
   the way to check detection.

## 7. Not done

Nothing of the plan.

## 8. Usage

| | 5-hour window | Weekly | Context |
|---|---|---|---|
| Start (~15:40) | 70% (resets 18:20) | 51% | 509k tokens |
| End (~15:50) | 74% | 52% | ~540k tokens |

Per item: R25 70→72, R6 72→74.
