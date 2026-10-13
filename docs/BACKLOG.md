# J.A.R.V.I.S. — the work

The decided work, the single list: the backlog, the review's open
recommendations, and the plan of the next sessions. Both machines see it
through git. The developer reads it; the architect manages it and, while a
developer session runs, does not edit it (`CLAUDE.md`, "Parallel sessions").
What is not work yet — what waits for the user, open discussions — is
`PENDING.md`; how the work is done is `PROCESS.md`. Split out of
`CONTEXT.md` on 12/10/2026; CONTEXT's sections 8, 13.4 and 14.4 point here.

---

## 1. Backlog

**The project's single list.** Both machines see it through git. Each item
says where it came from:

- **(decided)** — the user asked for it or approved it
- **(proposto)** — Claude's suggestion, no decision from the user yet

Proposed items **are not a plan**. Never start one without asking. The
architecture review's recommendations are separate (section 2) and the
**high**-priority ones come before items here. The full text of every
finished item is in `HISTORY.md` 8.

### Done

| | Item | Where |
|---|---|---|
| ✓ | Tiered storage (decided) — to an external drive after 30 days | ARCHITECTURE 11 |
| ✓ | Phone notifications through Telegram, with a face and a name (decided) | ARCHITECTURE 12 |
| ✓ | Core without a window (decided) | ARCHITECTURE 15 |
| ✓ | **3.** The web interface, the only way in (decided 09/10) | ARCHITECTURE 17 |
| ✓ | **5.** Play recordings on the page (decided 11/10, `v2026.10.11.3`) | ARCHITECTURE 17.13 |
| ✓ | **9.** Undo a merge — closed by the user: a warning before every merge instead | — |
| ✓ | **15.** Animal re-ID — superseded by 22 | HISTORY 8 |
| ✓ | **17.** Production and test environments (decided 09/10) | ARCHITECTURE 18.7 |
| ✓ | **18.** The running version on the page (decided 10/10) | ARCHITECTURE 12.10 |
| ✓ | **19.** People by person; attach a face to a name; the waiting queue; rename (decided 10/10, `v2026.10.10.4`) | ARCHITECTURE 17.10 |
| ✓ | **20.** Who appears in each recording (decided 10/10) | ARCHITECTURE 17.10 |
| ✓ | **21.** A favourite photo per person (decided 10/10, `v2026.10.10.6`) | ARCHITECTURE 17.10 |
| ✓ | **22.** A Dogs tab: each household teaches its own dogs (decided 10/10, `v2026.10.10.7`); thresholds wait for ~10 named views per dog per lighting | ARCHITECTURE 20 |
| ✓ | **23.** Report a bad detection instead of deleting it, with Undo (decided 11/10, `v2026.10.11.4`) | ARCHITECTURE 21 |
| ✓ | **24.** "Choose the best 40" views; Chosen and Waiting (decided 11/10, `v2026.10.11.4`) | ARCHITECTURE 17.14 |
| ✓ | **25.** Residents, notification cases and the Home/Away/Silent modes, the Notifications tab, commands from the phone (decided 12/10, `v2026.10.12`) | ARCHITECTURE 22 |
| ✓ | **26.** Select many unnamed photos, name or report them at once (decided 12/10, `v2026.10.12.2`) | ARCHITECTURE 17.16 |
| ✓ | **27.** Notifications as the first part of Settings (decided 12/10, `v2026.10.12.2`) | ARCHITECTURE 22.4 |

**Waiting for the user's check on the M900:** items 25 and 3, in `PENDING.md`.

### Critical

Without these the system does not do its job well.

1. **Zones of interest per camera** (proposto) — today there is only a fixed
   mask over the camera's clock, in the code. Every competitor has drawable
   zones, and it is the biggest control over false positives there is.
   Mosquitoes, wall objects and sunlight have already cost time; a zone saying
   "only the garage matters" would have avoided almost all of it. Worth
   separating a **mask** (ignore the area) from a **required zone** (detect
   everything, but notify only when something enters it).
2. **System health** (proposto) — if a camera dies at 3 a.m., nothing warns.
   There is an automatic restart, but no record of how long it was down. A
   daily summary, or a "camera down" case among backlog 25's switches, would
   close it.

### Important

It works without them, but is incomplete.

4. **Measure the M900 running** (proposto) — CPU with both cameras in motion,
   and whether `HWACCEL` helps (INSTALL 6).
6. **Search and filter** (proposto) — with ~100 events a day, by date only is
   not enough. By person, camera, label.
7. **Tracking** (proposto) — keep identity across frames; it solves the person
   standing still and makes one clip match one person.
8. **Animal labels** (proposto) — accept a species only when it repeats within
   the event, instead of accumulating every YOLO hesitation.
10. **Audio** (proposto) — the cameras send PCM and `-an` drops it. Barking,
    shouting, breaking glass.

### Improvement

11. **A timeline** (proposto) — a grid of cards does not answer "what happened
    between 2 and 4 a.m.".
12. **Persist the static spots** (proposto) — the list starts empty on every
    run, so the night's first false clip is still recorded.
13. **An event database** (proposto) — SQLite instead of JSON files, once
    there is search.
14. **OpenVINO on the M900** (proposto) — `cv2.dnn` accepts that backend; it
    was the plan to win back the speed lost when leaving PyTorch.

### Outside software

16. **A motion-triggered light at the Front** (proposto) — not code, but the
    biggest possible gain for faces at night (ARCHITECTURE 10.5).

### Deliberately out of scope

Competitors have these and they make **no** sense here: multiple users with
permissions, cloud or subscription, support for dozens of camera brands, PTZ,
two-way audio, number-plate reading, Home Assistant integration. They are
product features; this system is for one house with two cameras. If someone
proposes one, the answer is already here.

---

## 2. Recommendations, open

The closed ones, with their commits and texts: `HISTORY.md` 13.4.

| # | Priority | Recommendation | State |
|---|---|---|---|
| R42 | medium — **the user's decision** | In Home, a resident's face plus a second person who never shows a face sends nothing | open |
| R30 | **high** | A face seen from the side is dropped, so many person events end without a face photo | (a) done `9fb8862`; (b) needs a **second named person** to test that the right one still wins (HISTORY 13.12) |
| R12 | medium | Production and test copy on the same M900 double the CPU load | open (HISTORY 13.5) |
| R7 | low | `install.bat` does not check that the Python is signed | partly: `production.ps1` checks it (HISTORY 13.4) |
| R14 | low | Live MJPEG is encoded once per viewer | open (HISTORY 13.5) |
| R9 | verification | `python-preference = "system"` on the development PC | open (HISTORY 13.4) |

**R42 — In Home, a resident's face hides a second person with no face
(medium, the user's decision).** The faceless message goes only when the scan
found no face at all. If the user walks out with someone whose face is never
seen, the scan finds the user's face (silenced in Home) and nothing is sent —
against the user's own rule that a stranger in the dark must reach the phone.
The scan cannot tell one person from two by faces; YOLO can, by counting
person boxes in the same frame. Options: (a) accept the corner; (b) when the
person was held, every face found was silenced, and YOLO saw more people at
once than distinct faces were found, send the best view as
`faceless_person`. (b) costs a counter in `EventRecorder` and, when YOLO
counts a dog as a second person (R18), one extra message. The architect
recommends (b).

---

## 3. Next sessions

**Review 17's cycle is done** (`v2026.10.12.3`, deployed at 21:20, every
file read before and after): R10 and R45 closed — every
file name, tool and launcher is in English, and a merge batch reads each
sighting once.

**Developer 16 (planned 12/10, night):** in this order —

1. **Delete `jarvis_vigilancia.bat`**, the shim developer 15 left for one
   release (it shipped in `v2026.10.12.3`). Nothing on the M900 calls it:
   the startup task runs `pythonw -m jarvis --headless` and the Desktop
   shortcut points at `jarvis.bat`. Check that no file in the repository names
   it except `docs/` (the architect updates those).
2. **R7** (low, text in `HISTORY.md` 13.4): `install.bat` checks, after
   `uv sync`, that `.venv\Scripts\python.exe` is signed by the Python
   Software Foundation, and stops with a clear message pointing at INSTALL 1.2
   when it is not. The same test as `production.ps1`'s
   (`Get-AuthenticodeSignature`, line 128: status `Valid` and the PSF in the
   subject); whether the `.bat` runs it as one PowerShell line or both call a
   small shared script is the developer's choice. **Acceptance:** the check
   passes on this folder's `.venv` (`python.exe` is `Valid`, PSF — checked by
   the architect), and fails on an unsigned file: `uv` writes unsigned
   launchers into `.venv\Scripts` (`jarvis.exe` and `pytest.exe` are
   `NotSigned`; ARCHITECTURE 19.5), so point it at one of those to prove the
   failure path.
   Do not run `install.bat` end to end: it installs software and writes a
   Desktop shortcut.

**Not planned:** R42 waits for the user's choice and R30 (b) for a second
named person. R14 stays open until a measurement says live encoding matters
(backlog 4, proposto); R12 is an operating rule, not code; R9 needs the
development PC. Every other open backlog item is **(proposto)** — 1 (zones),
2 (system health) and the rest of section 1. **After developer 16 the decided
work runs out**: the next cycle needs the user to choose.
