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

- **Backlog 25's acceptance on the M900** (BACKLOG 1): in use since 13/10 —
  the user, Izabel, Mirana and Aurora are marked Resident and Home is on; the
  user's one remark (probable residents still reach the phone) became
  backlog 30. Not yet confirmed: that a person with no face does reach the
  phone in Home, and that `/away` from the phone changes the mode the page
  shows.
- **Backlog 29 and 30 on the M900** (`v2026.10.13`): `/off` from the phone —
  the header shows a red Off, nothing is recorded, a reminder comes after
  3 h — then `/on`; and in Home, a "probably Gustavo" or "probably Izabel"
  no longer reaches the phone. One reading to confirm: an event already open
  at `/off` still finishes and sends its follow-ups (ARCHITECTURE 22.7).
- **Backlog 3's acceptance**: open the page from a phone
  (`http://192.168.0.18:8765`).
- **Backlog 26 and 27 on the phone** (`v2026.10.12.2`): select many unnamed
  dogs and name them at once; Notifications is now inside Settings.
- **The twelve head-tops on Gustavo's page** (R49, 14/10/2026): deleting
  them now helps production today — without the five in Chosen, no face
  is matched to the wrong person (HISTORY 13.22). In **Waiting** the photos
  starting `c58c97`, `e18912`, `b3f8b9`, `69f368`, `1bbfa1`, `860372` and
  `eedcf9` (positions 11, 12, 17, 20, 21, 22 and 26 on 14/10); in **Chosen**
  positions 15, 16, 18, 19 and 31, photos starting `55edf5`, `e5bf9c`,
  `80936d`, `1f8419` and `dbc1b0`. R49's measurement uses a copy taken
  before, so nothing is lost. R48 and R49 themselves are decided (BACKLOG 2).
- **R49, two answers before step 2** (review 22, 14/10/2026; ARCHITECTURE
  10.14). (1) **Who is in the unnamed entries.** A contact sheet went to
  the user in review 22's conversation, with the entries lettered from
  `backups/r49_faces_20261014`: A `p_a8ef5acd`, B `p_385283de`, C
  `p_4e2d9f32` show a woman with long loose hair; D `p_6c76506e` and E
  `p_5bc580f7` grey hair tied back and a red top, like Izabel's photos; F
  `p_d26b745a` and G `p_c5ed26cc` unclear. If A–C are not Izabel, ArcFace at
  a 0.40 sure threshold learns two of their views as her. If they are, it
  recognises her where SFace cannot. Naming them on the People page answers
  it too. (2) **buffalo_l's licence**, "for non-commercial research purposes
  only". A private home system is non-commercial but not research. Yes means
  step 2 with SCRFD + ArcFace (BACKLOG 3). No means staying on SFace with the
  head-tops deleted by hand and R48's option (b), a plan made with the user.
- **R42**: accept the corner, or count people with YOLO (recommended)
  (BACKLOG 2).

## Decided, not yet done

None. The EPUB's documents were chosen by the user on 14/10/2026 —
ARCHITECTURE and PYTHON only — and `tools/make_epub.py` follows it (CONTEXT
10); the EPUB itself is built when the user asks.

## Open discussions

None. The requests of 13/10/2026 (detection sensitivity, probable residents in
Home, `/on` and `/off`, the photos piling up, the 40 views managing themselves,
the "maybe" threshold) were answered by the user the same evening and are
backlog 28–32 and R46. The question about competitors was answered in the
conversation; its one new idea is backlog 33 (proposto).
