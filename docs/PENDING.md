# Pending — what is not work yet

What the conversations with the user leave open, kept here so that clearing a
conversation loses nothing (`CLAUDE.md`, "Clear, not compact"). The architect
owns this file and reads it at every resume; the developer does not use it.
It is kept apart from the documentation of the application and from the plan
the developer follows, so the architect can write it while a developer
session runs.

An item leaves this file when it becomes a decision (`CONTEXT.md`), work
(`BACKLOG.md`) or is dropped with its reason (`HISTORY.md`). If the file only
grows, decisions are being postponed.

## Waiting for the user

- **What comes next** (12/10/2026, after review 18). The decided work has run
  out, so no developer session is planned (BACKLOG 3). The user chooses: R42
  below, or a **(proposto)** backlog item — the architect would start with 1
  (zones per camera, the biggest control over false positives) or 2 (system
  health: a camera down at 3 a.m. warns nobody today).
- **Backlog 25's acceptance on the M900** (BACKLOG 1): mark the user, Mirana
  and Aurora Resident, choose Home, and confirm that a recognised resident
  sends nothing, a person with no face does, and `/away` from the phone
  changes the mode the page shows. Until then production behaves as before:
  Away, people only.
- **Backlog 3's acceptance**: open the page from a phone
  (`http://192.168.0.18:8765`).
- **Backlog 26 and 27 on the phone** (`v2026.10.12.2`): select many unnamed
  dogs and name them at once; Notifications is now inside Settings.
- **R42**: accept the corner, or count people with YOLO (recommended)
  (BACKLOG 2).
- **Which documents go into the EPUB** (12/10/2026). The user will read every
  document and say which go in. Already decided by them: a file that only
  holds what Claude and the developer exchange stays out. Today
  `tools/make_epub.py` takes every `.md` at the root and in `docs/`, so
  `PROCESS.md`, `BACKLOG.md`, `PENDING.md`, `HISTORY.md` and `HANDOFF.md` would
  go in; when the list comes, `ORDER` becomes the list of what goes in, not
  just the order.

## Decided, not yet done

None. (The split of the context documents was done on 12/10/2026.)

## Open discussions

**The user's requests of 13/10/2026, evening** (pasted list, then one idea),
with what the architect measured in production the same evening. Waiting for
the user's answers before any becomes work:

1. **Sensitivity for people and dogs**, and **"many bad detections"**. 12 dog
   reports since the deploy of 12/10 (18 in all, none of faces). Of the 12:
   7 a person bending or crouching, 3 objects (a helmet, a cloth, clothing on
   a back), 2 animals at night on infrared. Replaying `Front/2026-10-13/15-00-17`
   and `15-19-17` (the same woman bending, five reports): YOLO calls her `dog`
   at 0.47–0.86; R44 relabelled 5 boxes and missed 17, because she moves while
   bent — the box shifts 50–100 px between YOLO runs, so its IoU with her last
   person box falls to 0.40–0.50 — and a relabelled box does not renew the
   2 s memory. A score slider does not separate them (HISTORY 13.16: bent
   0.62–0.81, real dogs median 0.68). Proposed: R44 extended — a relabelled
   box renews the memory and a moving box is matched — or tracking (backlog 7),
   measured on these reports; the slider as well, since the user asked, with
   the data shown beside it.
2. **Home silences "probably <resident>"** ("I have not seen a wrong maybe").
   It reverses ARCHITECTURE 22.2's rule that only a sure match counts as a
   resident. Today 72 of 134 named face sightings were probable (the user 25,
   Izabel 47); dogs 42 probable, 70 sure. Proposed: a new case
   `probable_resident` with its own switch per mode, off in Home, on in Away.
3. **`/on` and `/off` in the bot**: off stops J.A.R.V.I.S., the process keeps
   running and waits for `/on`. Open: what stops, and whether off survives a
   restart.
4. **People and Dogs fill with photos too fast.** Each named person and dog
   holds 40 chosen views and 28–35 waiting; 27 unnamed dogs (probable dogs
   become unnamed crops) and 7 unnamed faces.
5. **What competitors have that this does not** — answered in the
   conversation; the gaps map to backlog 1, 2, 6, 7, 10, 11 and 14, plus one
   new idea: report a bad detection from the Telegram message itself.
6. **The idea: the software manages the 40 views of sure matches; the user
   only handles the really uncertain maybes and the unidentified.** Measured:
   a face's waiting views are *not* near-copies (median cosine to the nearest
   chosen view 0.48 and 0.44), while the chosen 40 already hold identical pairs
   (1.00); a dog's waiting views are closer to the chosen ones (median
   distance 0.25 and 0.22) than the chosen are to each other (0.34 and 0.26).
   So the rule is "a new view enters only if it makes the 40 more varied,
   replacing the view with the closest twin", not a fixed similarity cut.

Also: Izabel was named on 13/10, so R30 (b)'s precondition — a second named
person — is met.
