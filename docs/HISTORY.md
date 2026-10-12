# J.A.R.V.I.S. — history

What used to fill `CONTEXTO.md` and is no longer needed to resume work: the
bugs already fixed, old measurements, a solved incident, the long text of
finished backlog items, every review in full, the closed recommendations and
the old rows of the usage log. Moved here on 12/10/2026 (R33), so every
session's resume reads a short brief instead of about 25k tokens.

**Section numbers are the ones `CONTEXTO.md` had**, so an older reference such
as "CONTEXTO 13.6" is now "HISTORY 13.6". Read on demand, not at every resume.
From review 15 on, each review writes its own section here (13.16, 13.17…)
and its row in 13.2; a recommendation's text moves here from `CONTEXTO.md`
13.4 when it closes.

---

## 4. Bugs found and fixed — do not reintroduce

| Bug | Cause | Fix |
|---|---|---|
| The window did not close on X | HighGUI has no close event; the next `imshow` recreates the window | Check `getWindowProperty` **after** `waitKey` |
| The video stretched on resize | `WINDOW_KEEPRATIO` is 0 on the Win32 backend | Build an image of the window's exact size with `getWindowImageRect` and letterbox it |
| Clicking a card opened Documents | `subprocess` with a list quotes every argument with a space, and Explorer's `/select,` went inside the quotes | Pass a ready-made string on Windows |
| Face detection found nothing | Sampling read the clip's first frames, and the pre-recording makes the start come **before** the person arrives | Compute the step from the total frame count |
| A 44 px face was thrown away | `MIN_FACE_WIDTH` too high | Lower the floor and **mark** small faces instead of dropping them. Today the frontal-face test filters, not the width (ARQUITETURA 10.9) |
| The gallery ignored a test path | `def __init__(self, path=GALLERY_FILE)` freezes the value at definition time | `path=None` and resolve inside |
| Grey "Not Responding" window | The loop blocked reading the pipe; the first frame takes **2.45 s** | One reader thread per camera; the loop never blocks |
| "no signal" with no reason | ffmpeg's `stderr` went to `DEVNULL`, and the start-up `ok` checked `poll()` before the process had time to fail | Capture stderr, wait for a real first frame, translate known errors |
| False person detections | Wall objects under infrared | Minimum height (measured: false 36–86 px, real people 294–306 px, **18/18 right**) |
| Mosquitoes triggering recordings | Insects near the lens look big in IR | Temporal confirmation: only what stays 3 frames in the same place is reported (**83 % fewer triggers**) |
| "no frame received" on the M900, no error | `.env` with `.env.example`'s sample IPs; with no timeout ffmpeg waits for TCP forever, silently | `-timeout` on RTSP and a translation of `Error number -138` (section 6) |
| False daytime motion on Front | Patches of sun and leaf shadow; the camera's clock in the corner | Lighting filter by correlation with the background, and a mask over the clock: **99 → 15 frames**, person covered 262 → 258 of 273 (ARQUITETURA 6.7) |
| 14 "people" for 3 real ones; a name was not recognised later | Every unmatched face became a person (profiles, the back of a head, an arm); the same name created twins; it only learned from faces ≥ 80 px | Frontal-face filter + YOLO, joining by name, absorbing on naming, learning by similarity (ARQUITETURA 10.4, 10.9) |
| The program crashed right after an event (`buf.shape() == m.shape()`) | The face scan used the live loop's YOLO network, from another thread | A network of its own for background threads, and scans in a queue (ARQUITETURA 10.9) |
| Terminal full of `[h264] error while decoding MB` | The Back camera sending damaged blocks (Wi-Fi), printed by OpenCV's internal decoder during the face scan | The scan reads through our own ffmpeg with `-loglevel quiet`, 2× faster; `tools/verificar_clipes.py` measures the damage (ARQUITETURA 10.11) |
| Poor face photo | It was the recogniser's 112 px crop, enlarged twice | A crop of the original frame with hair and shoulders, 300 px (ARQUITETURA 10.10) |
| Scripts depended on the current folder | Relative paths (`Path("clips")`) | `ROOT` in the package; every path starts from the root (ARQUITETURA 3.2) |
| The M900 would not start, `Failed to spawn: python` (`WinError 4551`), 09/10 | Smart App Control started refusing the Python `uv` downloads (unsigned) — the same file that ran on 29–30/09; the reputation verdict changed on its own | The official Python signed by the PSF + `python-preference = "system"`; the `.bat` files call `python -m jarvis`, without the unsigned `jarvis.exe` (INSTALACAO 1.2) |

| A person arriving after an animal was never announced (R1) | Notification tried only on the event's first frame | One attempt per new label during the event, photo `HH-MM-SS.alert.jpg` (ARQUITETURA 12.8) |
| Two launches a moment apart brought up two copies (R2) | Port checked, then bound later in another thread | Port bound atomically in the main thread, `SO_EXCLUSIVEADDRUSE`, handed to uvicorn (ARQUITETURA 18.8) |
| Live picture froze when the service restarted (R3) | A dead MJPEG connection keeps its last frame | `frame_age`, "no signal" after 5 s, page reconnects when `started` changes (ARQUITETURA 17.8) |
| `config.json` saved with a BOM silently lost the token | `json.loads` on `utf-8` fails on the mark; `load()` returned defaults | Every JSON reader uses `utf-8-sig` (ARQUITETURA 19.3) |
| The production data gate always passed | PowerShell function output joins its return value | `\| Out-Host`; proven with a corrupted file (ARQUITETURA 18.9) |
| A crash would have ended production until the next reboot | "Restart on failure" only acts on a failed *start* | Task trigger every 5 min + ignore new; `HOLD` file for updates (ARQUITETURA 18.7) |

## 5. Reference measurements

Kept because conclusions change when the format changes.

| What | Value |
|---|---|
| The camera's original stream | 579 KB / 10 s (463 kbps) |
| Old re-encoding pipeline | 725 KB / 10 s, **worse quality** |
| Real storage (30/09, M900) | 102 events, 41 min of clips, **303 MB/day**, ~120 KB/s → ~110 GB/year |
| Storage at night (26/09, dev) | ~48 KB/s — the old ~5 GB/year estimate came from here and is wrong |
| Rolling buffer | 6 to 8 MB per camera |
| Free disk on the M900 (30/09) | 394 GB |
| YOLO inference (dev) | 50–62 ms |
| ONNX runtime, CPU against CPU (09/10) | `cv2.dnn` 37.8 ms, `onnxruntime` 34.6 ms — 1.09×, identical output |
| Motion after temporal confirmation | Front 8.7 % → 1.5 % of frames |
| A face at night | 44 px (~112 px wanted) |
| ffmpeg's first frame | ~2.5 s |
| The old window's loop | median 19.9 ms, worst 88.8 ms |
| Face scan per clip (M900) | 9 to 17 s, off the critical path; 45 ms per frame since R31 |
| Daytime faces on the M900 | 36 to 80 px, most below 60 |

## 6. Solved: the M900 got no frames (29/09/2026)

**Symptom:** on the M900, `FALHOU - nenhum frame recebido`, the panel showing
"no signal", no error message from ffmpeg. The same commit worked on the
development PC.

**Cause:** the cameras are at `192.168.0.116` (Front) and `192.168.0.42`
(Back), and the M900's `.env` pointed at `.10` and `.11`, where nothing
answers. Both machines are on the **same network**; `.10` and `.11` were the
sample values of `.env.example`, which `instalar.bat` copies to create `.env`.
The development PC's `.env`, not versioned, had the right IPs. With no
timeout, ffmpeg waits for the TCP connection forever and **writes nothing**.
The only line, even at `-loglevel verbose`, was `Starting connection attempt
to 192.168.0.10 port 554`.

**How it was found, in order:**

1. `tools/diagnostico.py --local` read 7776000 of 7776000 bytes: decoding,
   the pipe, the binary and the antivirus ruled out at once
2. The capture command by hand with a detailed log: zero frames **and zero
   segments**, so it did not even connect. The log stopped at the connection
   attempt
3. `Test-NetConnection` on port 554 failed too, and ARP showed both IPs as
   `Unreachable`: not ffmpeg — nobody was there
4. A sweep of the subnet on port 554 found three hosts; two with MAC
   `14-EB-B6` (TP-Link). The credentials identified each camera: each accepts
   only its own Camera Account and answers `401` to the other

**Lesson:** the `probe_rtsp.py` that "passed" takes the IP typed by hand, so it
did not test `.env`. On a new machine, **test the IP in `.env` first**. So it
does not happen again, `.env.example` now holds the text `ip-da-camera` instead
of an IP, and the program refuses to start while it is there.

**Fix:** `-timeout` on RTSP (ARQUITETURA 5.7). A wrong IP now shows in ~6 s as
a timeout telling you to check the network and the camera's IP.

**Still the user's:** reserve `.116` and `.42` by MAC on the M900's router.

## 8. Backlog items as they were decided

The full text of finished items, as each was decided and delivered. The
backlog itself is `CONTEXTO.md` section 8.

25. **Done 12/10 (`v2026.10.12`, ARQUITETURA 22); the acceptance on the M900 waits for the user** (mark the residents, then Home). **Residents, notification rules and modes** (decided by the user 12/10/2026, one developer delivery). The user, Mirana and Aurora live here; being told hundreds of times that they walk around the house is noise. Today (10/10 01:16 → 12/10, 143 messages) 73 were "person" at the start of an event, 34 named a face — **21 of them the user** — 10 a side view, 26 a best view; dogs do not notify at all (`notify_labels` is `["person"]`).
    - **(a) The Resident tag.** A switch **Resident** on the person and dog pages, named entries only; stored as an optional `"resident": true` in `gallery.json` (additive). Renaming keeps it; a merge keeps the target's, or sets it when either was a resident. The grid card shows it.
    - **(b) The cases, one switch each:** resident person recognised · other known person, or any "probably …" match · unknown face · person with no recognisable face (the side-view and best-view messages) · resident dog · other dog (probable, another name, unidentified) · other animals. Only a **sure** match counts as a resident — a "probably Gustavo" or "probably Aurora" is not silenced, so a weak match of a stranger is never hidden.
    - **(c) Modes:** **Home**, **Away**, **Silent**; one is active; each has its own switches, all editable. Defaults: Away — every person case on; Home — the two resident cases off, the rest as Away (a person with no recognisable face **notifies**: the user's choice, a stranger in the dark must reach the phone); Silent — all off. Animal switches start from today's `notify_labels`, so nothing new arrives until the user turns it on. **Recording never changes**: a mode only decides what reaches the phone. Stored as new optional keys in `config.json` (`notify_mode`, `notify_modes`); `notify_labels` stays for older versions.
    - **(d) The timing problem, and its rule.** A dog is named from the first frame (~100 ms), so a resident dog is silenced in the first message itself. A person is named only after the clip is assembled and scanned (section 3, "Rosto no clipe"). So: **when the active mode has any person case off, the person message waits for the face scan** and goes out once, saying who was found, or with the side or best view; when every person case is on (Away), today's immediate message and follow-ups stay. The camera and per-person cooldowns keep working. A mid-event arrival (`_notify_late`) follows the same rules.
    - **(e) A Notifications tab.** The switches as a table — cases in rows, the three modes in columns, the active mode chosen at the top — drawn as real on/off switches (`<input type="checkbox" role="switch">` and CSS, no library), fitting a phone. The Telegram setup (token, chat, find chat, test, prefix, cooldown) moves there from Settings.
    - **(f) Commands from the phone.** A thread in production asks Telegram for new messages (`getUpdates` long polling: an outgoing connection like sending, **no port opened**). Only the configured chat is obeyed; anything from another chat is ignored and logged. `/home`, `/away`, `/silent` switch the mode and answer with what it means; `/mode` shows the current one with tap buttons (inline keyboard); `setMyCommands` lists them in Telegram's "/" menu. The bot can change the mode and nothing else. Find chat must read through the same poller (two readers steal each other's updates); only production polls — the test copy has no token (checked 12/10), and a second poller on the same token gets a 409 from Telegram: log once and back off. Network failures never touch capture; R16's token redaction applies.
    - **Acceptance:** tests for the rules matrix (each case × mode), the held person message with a fake scan, the resident flag through rename and merge, the defaults built from an older `config.json`, the poller ignoring other chats; `check_data` reads the new keys. On the M900: the user, Mirana and Aurora marked Resident; in Home a recognised resident sends nothing and a person with no face does; `/away` from the phone changes the mode the page shows.

23. **Done 11/10 (`v2026.10.11.4`).** **Report a bad detection instead of deleting it** (decided 11/10/2026). Some unnamed crops are not even a dog, or not a face. Each unnamed face and dog crop (and a person or animal label on a Recordings event) gets **"Bad detection"**: the crop leaves the gallery and the tabs, and is kept as an example in a new folder `reports/<kind>/` — the crop plus a JSON with camera, time, clip, label, score, box and what the user said (`not a dog`, `not a face`, `not a person`). Nothing is learned from it automatically yet; it is the improvement process's evidence: `tools/replay.py` and the tuning tools can be pointed at it, and each review reads the new reports (a rule like R18 or R35 is then measured against what the user flagged). Replaces the plain Dismiss of R27, which deleted without a trace. Additive: new files only; `check_data` reads them. **Since `v2026.10.11.6` (R38, R37):** Settings lists the reports; each can be undone — the entry returns to its gallery with its photos and sightings, or the label to its recording — and can say what it actually was (person, dog, other animal, nothing).

24. **Done 11/10 (`v2026.10.11.4`).** **"Choose the best 40" for a person or a dog** (decided 11/10/2026). When a person or dog holds more than 40 views (the 40 kept plus the queue), their page gets an **Analyse** button: the software picks the 40 **most different** views — greedy farthest-point selection over the embeddings (cosine for faces, the Bhattacharyya distance for dogs, keeping day and night both represented), which covers angles and lighting instead of 40 near-copies — shows the proposal, and on confirmation keeps those 40 and moves the rest to the queue. Manual removal stays as it is. Tests: the selection spreads (minimum pairwise distance grows), nothing is lost (views + queue unchanged as a set). **Since `v2026.10.11.6` (R40):** the queue is shown as **Waiting** beside **Chosen**, views move between them by the user's hand only (removing a chosen view no longer pulls a waiting one), and the proposal can also discard the views it does not keep.

22. **Done in code 10/10 (`v2026.10.10.7`, ARQUITETURA 20); the thresholds wait for the user's names.** **11/10, first names:** Aurora 5 views (3 day, 2 infrared), Mirana 3 (day only) — checked on a sheet, all correct. `dog_tuning.py` on them: day 2 right-sure, 1 right-probable, 1 wrong-probable, 2 no name; infrared not measurable (Mirana has no infrared view). Too few to tune: about 10 per dog **per lighting** are needed. **A Dogs tab: each household teaches the system its own dogs** (decided 10/10/2026). The user confirmed the two-dog measurement (item 15) — the dark group is Mirana, the light one Aurora — and set the rule: **nothing about their dogs goes into the code.** The software is not only for this house; anyone must be able to teach it their own animals. So it mirrors People: (a) every dog detection keeps a crop cut out of its box (GrabCut) and an **appearance descriptor** computed from the fur pixels only — a normalised tone histogram, plus hue and saturation when the frame is in colour; (b) a **Dogs** tab next to People: a grid of named dogs, the unnamed crops with a name field and "Belongs to…", and a dog page with its views, favourite photo and calendar — the same screens and rules as items 19 and 21; (c) a dog gallery in its own folder, `dogs/` (`gallery.json` + `views/`), new files only, read by `check_data`; (d) matching by nearest neighbour against each named dog's views, **day views compared with day views and infrared with infrared**, and a name given only when the nearest dog is clearly closer than the second and within a distance limit — otherwise just "dog"; (e) the event's `animals` list, the Recordings card and the Telegram text use the names. **Notification rule (the user, 10/10):** the alert is about *a dog being there*, not about knowing which — so whenever a dog is detected and `dog` is among the alert labels, notify, and word it by certainty, the same three levels as faces (12.8): a clear match → the dog's name; a weak one → "probably <name>"; none → "unidentified dog". The thresholds start conservative and are tuned as the named views grow; if the patterns never firm up, the feature still works as "a dog was there", which is what exists today. Dogs that look alike stay "dog", which is the honest answer. Acceptance on this house's data: after the user names a few crops of each, production's past dog events are named correctly in most clear cases and at night, with no colour rule anywhere in the code. Supersedes item 15's model research.

21. **Done 10/10 (`v2026.10.10.6`).** **A favourite photo per person** (decided 10/10/2026). On the person's page the user picks which of the stored views is the photo shown on the People grid. Additive: an optional `cover` per person in `gallery.json`, the portable path of the chosen view's crop; the grid uses it when set and the file exists, otherwise today's `thumbnail`. When the favourite view is removed (`remove_view`) or merged away, `cover` falls back to the first view that has a photo. The write goes through the R24 guard; `check_data` and `tests/test_gallery.py` cover the new key.

19. **Done 10/10 (`v2026.10.10.4`, ARQUITETURA 17.10).** **People by person, not by day; attach a face to an existing name** (decided 10/10/2026, redesigned by the user the same day). The People tab today lists sightings by day. The user wants instead: **(a)** one screen with every **named** person (they fit on one screen), and a separate place for the unnamed faces; **(b)** clicking a person opens their page: first **the stored views that recognise them** (up to `MAX_EMBEDDINGS` = 40), then **a calendar of every recording they appear in**; **(c)** on an unnamed face, a "belongs to…" picker of existing names instead of typing — the merge itself already exists (`Gallery.rename` → `_merge`); **(d)** when a person already holds 40 views, new ones **wait in a queue** instead of being dropped (today `_merge` and `reinforce` drop them); on the person's page the user can **remove** one of the 40, and the oldest waiting view takes its place. This replaces the architect's earlier idea of replacing the most redundant view automatically: the user wants the choice. **Data, additive only:** a view today is a bare embedding with no picture, so to show the 40 the gallery must start keeping each view's face crop — an optional list aligned with `embeddings` (`null` for the views stored before, shown as "no photo"), plus an optional `pending` queue; `check_data` must read old and new. **(e) Rename a person** from their page (added by the user, 10/10). `Gallery.rename` already does it, but a new name that belongs to someone else **merges the two** — the page must say so and ask before doing it. **Fresh start (decided by the user, 10/10):** production's gallery holds only two named people and views without pictures, so when this version is deployed the architect **deletes** production's `faces/` — the user chose no backup — and the gallery restarts empty; the user names the two people again, and every view from then on has its picture. Clearing it before the deploy would be pointless: the running version would keep storing views without pictures until then. **Animals:** the user wants the same for the dogs; that needs item 15 first.

20. **Done 10/10 (`v2026.10.10.4`).** **Who appears in each recording** (decided 10/10/2026). On the Recordings tab, each event shows under its time the named people seen in it (`People: Gustavo; Izabel`, unknown faces as "unknown") and the animals (`Dogs: …` — today only the label and count, since dogs have no identity until item 15). The data exists: each face sighting records its `clip`; the event list can join on it, with no change on disk.

5. **Done 11/10 (`v2026.10.11.3`).** **Play the recordings on the page** (decided 11/10/2026: the user cannot watch a recording from another device — the web never had video, only the old window opened Explorer on the M900). A route `GET /video/<camera>/<day>/<HH-MM-SS>.mp4` with the same name checks as the thumbnails and HTTP **Range** support (Starlette's `FileResponse` answers ranges, so the browser can seek without downloading the whole clip); the clips are the camera's H.264 assembled with `+faststart`, which every browser plays in a `<video>` element. Clicking a card on Recordings (and a day on a person's or dog's calendar) opens a player on the page, with the event's best view, side face and faces beside it. Reading stays open to the home network, as R4 decided for the live view. Acceptance: a clip plays and seeks from 192.168.0.18 and from a phone; a request outside `clips/` is refused.

3. **The web interface, replacing HighGUI** (decided 09/10/2026) — the user
   approved it and added the deciding reason: they will not always want to
   watch live, and the software must run all the time with no user window.
   The bottom half (the core without a window) was already done; the client
   was missing. It serves a local page, and the browser becomes the toolkit:
   it plays video, scrolls lists, accepts accents, pastes text and opens on a
   phone. Delivered along with it, for free: remote access and items 5, 6 and
   11. **Stack: FastAPI + uvicorn**, chosen for MJPEG and HTTP Range, not
   taste. A plan in four stages, each with an acceptance criterion:
   ARQUITETURA 17.

   **The user's decision, 09/10/2026: the web is the only way in**, with one
   service running — *"I don't want two ways of getting in"*. It replaced the
   plan of keeping the window alongside to compare. Order:

   | | Step | State |
   |---|---|---|
   | ✓ | Stage 1 — the event list | done 09/10 (ARQUITETURA 17.6) |
   | ✓ | Stage 3 — live, local network, the shortcut opens service + browser | done 09/10 (ARQUITETURA 17.7) |
   | ✓ | Stage 4 — People and Settings on the web | done 10/10 (ARQUITETURA 17.9) |
   | ✓ | Start with Windows, no console | done by item 17 (production task), 09/10 |
   | ✓ | Remove the OpenCV window (`ui.py`, `--window`) | done 10/10 (ARQUITETURA 17.10) |
   | ✓ | Stage 2 — play the video on the page | done 11/10 (item 5) |

15. **Re-ID de animais** — **superseded by item 22** (the user's two-dog idea, generalised). History: **researched 10/10/2026, parked: no solution good enough for its cost now** (the user accepted that outcome in advance). *Measured:* the cheapest idea, telling the dogs apart by fur tone (works day and night in principle, since IR keeps white bright and black dark), failed on production's data: 168 dog detections in 89 events give a continuous spread of median tones from 7 to 249, with no clusters — a box holds the mat, the floor, sun and shade as much as the dog. *Read:* the models made for it are MegaDescriptor (WildlifeDatasets; Swin and EfficientNet variants on Hugging Face, best published for animals) and frozen DINOv2 with nearest-neighbour matching (weaker; a community dog model reports about 0.54 top-1 on whole-body dogs). Neither ships as ONNX: export needs PyTorch on the development PC, the run would be `onnxruntime` or a newer `cv2.dnn`, at an unmeasured CPU cost per crop on the M900. *What it would take:* a dog gallery the user labels by hand, a new model, and two or three sessions; expected to work on clear daytime views and poorly at night or with the dog lying down. Revisit only if knowing *which* dog becomes worth that. Today every event already says *that* a dog was there (item 20). **Reopened the same day with the user's idea — and it works on the data.** The house has two dogs, so the question is not *which dog in the world* but *which of the two*: keep the existing YOLO dog detection and tell the two apart with plain computer vision. Measured on production's clips: cutting the dog out of its box with OpenCV's GrabCut first, then taking the median tone of the fur pixels, splits 89 detections in 54 events into **a dark group (0–42, 42 detections) and a light group (150–210, 31)**, with 16 in between; **at night the split is clean** (2 dark, 14 light, none in between), since infrared keeps white fur bright and dark fur dark. A contact sheet of each group was sent to the user to confirm which dog is which. Proposed rule: tone below ~60 → the dark dog, above ~140 → the light one, in between → just "dog"; GrabCut on a handful of crops per event in the post-event scan costs little. Waits for the user: the two names and the confirmation of the sheet; then it is a small developer session (`people.py` or `faces.py`, the event's `animals` list, tests). A visiting dog would be named as one of the two — accepted by the user ("the only two dogs at home, most of the time"). The original item was a
    whole-body classifier (ARQUITETURA 10.8).

## 12.2 A precondition checked on 09/10/2026

Web interface (backlog 3, ARQUITETURA 17) depended on `pydantic_core`, compiled
Rust — the same kind of binary Smart App Control blocked in PyTorch:

```bash
uv run python -c "import pydantic_core, fastapi, uvicorn; print('ok')"
```

| Machine | Does `pydantic_core` load? |
|---|---|
| Dev (Windows) | yes, tested 09/10/2026 |
| M900 (deploy) | yes, tested 09/10/2026 — `pydantic_core` 2.50.0, after switching to the signed Python |

Had it failed, plan B was Flask with a threaded WSGI server, pure Python
(ARQUITETURA 17.2).

## 13. Architecture review

### 13.2 Review log

| # | Date | Range reviewed | Result |
|---|---|---|---|
| 1 | 09/10/2026 | `b3d9c94..456b613` — signed Python, web stages 1 and 3, the face in the notification | 2 documentation errors fixed; R1–R9 opened. During the review the user decided R4 (keep LAN access) and the language rule (R10), and asked for production and test environments (backlog 17, ARQUITETURA 18) |
| 2 | 09/10/2026 | `760d68e..67f7d23` — everything before production: logging, clean stop, per-install stream and port, R1–R3, R5, R8, `check_data`, `production.ps1` | 4 code problems fixed in `8a81084` (13.5); full production cycle tested including a forced rollback; HANDOFF integrated; R11–R14 opened; **first release `v2026.10.09` tagged** |
| 3 | 10/10/2026 | `87e736b`, developer session 1 — R15, R16, R10 in part, R19, R20, R11 | no code fixed: the diff, `check_data`, the comment check and the redaction and `select` expressions all checked out; HANDOFF integrated; R18 raised to high, R21–R22 opened; release `v2026.10.10` tagged |
| 4 | 10/10/2026 | `5d91305..1b8822d`, developer session 2 — R21 measured, backlog 18, R22, R17, R10 code part | no code fixed; R21's fix decided (R23); release `v2026.10.10.2` tagged |
| 5 | 10/10/2026 | `11c6663..5f3c356`, developer session 3 — R23, R18, web stage 4 | no code fixed; R18's 2.0 accepted; R24 opened for writes from the network; release `v2026.10.10.3` tagged |
| 6 | 10/10/2026 | `3a91964..5eb8964`, developer session 4 — R24, backlog 19 and 20, the window removed | no code fixed; R25 decided from the user's question about face messages; release `v2026.10.10.4`; production's gallery deleted at the deploy, as the user decided |
| 7 | 10/10/2026 | `5eb8964..0707670`, developer session 5 — R25, R6 | no code fixed; 23 tests pass; the new `httpx2` dependency checked as legitimate; backlog 21 added; release `v2026.10.10.5` |
| 8 | 10/10/2026 | `0707670..7bde4db`, developer session 6 — backlog 21, R26 | no code fixed; 29 tests pass; release `v2026.10.10.6` |
| 9 | 10/10/2026 | `v2026.10.10.6..ce81eed`, developer session 7 — backlog 22, parts 1 and 2 | no code fixed; 40 tests pass; R27 opened (unnamed dog entries grow without bound); release `v2026.10.10.7`; `dog_crops.py --days 1` run in production: 69 events, 77 crops, 78 unnamed entries for the user to name |
| 10 | 11/10/2026 | `v2026.10.10.7..8b019ea`, developer session 8 — R27, the dog tuning tool | no code fixed; 43 tests pass; the user's three reports investigated (13.11): R28, R29 opened; release `v2026.10.11` |
| 11 | 11/10/2026 | `8b019ea..db783cf`, developer session 9 — R28, R30 (a) | no code fixed; 48 tests pass; `a54f357` reached GitHub before this review by the architect's mistake (a push while the developer worked), no harm since production runs tags; release `v2026.10.11.2` |
| 12 | 11/10/2026 | `5675cfe..a4cc3a2`, developer session 10 — R34, backlog 5, R29 (the first automatic cycle) | no code fixed; 64 tests pass; R35 kept open on the developer's data; release `v2026.10.11.3` |
| 13 | 11/10/2026 | `a4cc3a2..c55e4c0`, developer session 11 (a new conversation) — backlog 23, 24, R31, R32; R35 and R30 (b) measured | no release code fixed; 79 tests pass; R35 closed, R36–R37 opened; release `v2026.10.11.4`. **The first deploy failed and rolled back on its own**: `--stop` returned while the old version still assembled a clip (22 s), the new one found both cameras busy. Fixed in `production.ps1` (`3ae5faa`: wait up to 180 s until no process runs from `C:\JARVIS`); the second deploy passed |
| 14 | 11/10/2026 | `1cea950..e03a083`, developer session 12 (scheduled cycle) — R38, R40, R37, R36; before it, R39 fixed by the architect (`76a5a9e`, release `v2026.10.11.5`) | no code fixed; 92 tests pass; `uv run pytest` found blocked by Smart App Control, docs moved to `python -m pytest`; R41 opened (low); release `v2026.10.11.6`, deployed at 17:46: 352 events, 36 face and 147 dog sightings, 2 reports read before and after, cameras ok 4 s after the start; production lists both old reports with their photos |
| 15 | 12/10/2026 | `v2026.10.11.6..e7df623`, developer session 13 — backlog 25 (a)–(f), R41 | **one code fix** (`5224983`): a held person with no face was silenced by a dog message of the same event, and got nothing when the clip failed to assemble; 160 tests pass; R42 (a decision for the user) and R43 opened; release `v2026.10.12` (13.15) |

### 13.3 Review 1 — what was fixed on the spot

- **The wrong story of the Python block** (INSTALACAO 1.2, sections 3 and 4 of
  CONTEXTO). It said a `uv sync` had switched Python to 3.14.7 and that
  Windows had already blocked it on 29/09. Both are false: 3.14.7 was
  downloaded on 29/09 and ran until 30/09 — Windows' verdict changed on the
  **same file** —, and the blocks of 29/09 in the event log were PyTorch DLLs
  loaded by Python. The mistake came from filtering the log by the word
  "python" without reading the whole message.
- **"The `Core` does not change"** (ARQUITETURA 17.4) no longer held after
  stage 3, which added `labels` and `live_view()`. Rewritten to what matters:
  the `Core` does not know about the web.
- **`jarvis_vigilancia.bat`** still told the user to use `jarvis.bat` to see
  the cameras.

A fact raised in the review: **the M900's last recording was from 30/09 at
22:54.** The system went nine days without running; the Python block only
showed when trying to start it again on 09/10.

### 13.4 Recommendations, closed

The open ones are in `CONTEXTO.md` 13.4. Each closed one, with its commit;
the text of R11 onwards is in the review section that opened it, below.

| | # | Priority | Recommendation | State |
|---|---|---|---|---|
| ✓ | R1 | **high** | Notify a person who appears in the middle of an event | done `760d68e` (ARQUITETURA 12.8) |
| ✓ | R2 | medium | A race at start-up: two launches in a row bring up two instances | done `760d68e`, made atomic in review 2 `8a81084` (ARQUITETURA 18.8) |
| ✓ | R3 | medium | The live view freezes without warning when the service restarts | done `760d68e` (ARQUITETURA 17.8) |
| ✓ | R4 | medium | Exposure on a Wi-Fi network classified as Public — **the user's decision** | decided 09/10: keep open to the LAN |
| ✓ | R5 | medium | "Recognised" with a low similarity | done `760d68e` (ARQUITETURA 12.8) |
| ✓ | R6 | medium | Automatic tests for the web routes and the notification locks | done `9e25534`: 23 tests, `uv run pytest` (ARQUITETURA 19.5) |
| ✓ | R8 | low | A network failure on the page is not shown to the user | done `760d68e` (ARQUITETURA 17.8) |
| ✓ | R11 | **high** | `settings.save()` drops keys it does not know | done `524b14f` (ARQUITETURA 19.2) |
| ✓ | R13 | verification | The startup task survives a reboot, and restarts after a crash | **reboot verified 10/10**: Windows up 00:58:07, task at 00:58:16, cameras ok 00:59:06, in session 0 with no window. **crash verified the same night**: the user ended Python in Task Manager about 01:01 (the task shows result 1, Task Manager's exit code); the 5-minute trigger at 01:06:10 started it again, cameras ok at 01:06:16. A crash costs at most ~5 min of recording |
| ✓ | R15 | **high** | ffmpeg opens console windows on the user's desktop | done `9eaa42c` (ARQUITETURA 18.7) |
| ✓ | R16 | **high** | Notification outcomes are never logged, and an error detail can carry the bot token | done `9ae537b` (ARQUITETURA 12.9) |
| ✓ | R17 | medium | No way to tell why something was *not* recorded: a replay tool | done `cc08df1` (ARQUITETURA 12.10) |
| ✓ | R18 | **high** since review 3 | The white dog lying on the Front mat is detected as `person` | done `13bb4d5`, ratio 2.0 after the replay (ARQUITETURA 12.10) |
| ✓ | R19 | **high** | The event's picture is its first frame, so it can show the dog instead of the person | done `085b3b6` (ARQUITETURA 12.9) |
| ✓ | R20 | **high** | The face scan samples too sparsely and misses short frontal moments | done `668588d` (ARQUITETURA 12.9) |
| ✓ | R21 | **high** | What the dense face scan costs live analysis on the M900 | measured `6ff6eda`: YOLO 1.6× slower during a scan; fix decided as R23 (13.8) |
| ✓ | R22 | medium | Nothing records where the dense scan looked | done `c5166d1` (ARQUITETURA 12.10) |
| ✓ | R23 | **high** | A face scan slows YOLO while an event may be happening | done `754fa45`: YOLO 342 ms with the scan paused, against ~590 ms (ARQUITETURA 12.10) |
| ✓ | R24 | **high** | Anyone on the Wi-Fi, or a web page they open, can now change settings and names | done `f2a7c3e` (ARQUITETURA 17.10) |
| ✓ | R25 | medium | A face found in an event that fell in the cooldown is never sent | done `74fd71e` (ARQUITETURA 12.10) |
| ✓ | R26 | low | Production installs the development tools (pytest, httpx2) | done `59d35fd` |
| ✓ | R27 | medium | Every dog not matched for sure becomes a new unnamed entry; the Dogs tab fills up | done `0b69a6b` (ARQUITETURA 20) |
| ✓ | R28 | **high** | Another computer runs an old copy of the page after every update, and a refused change fails without saying why | done `a54f357` (ARQUITETURA 21) |
| ✓ | R29 | medium | Naming a dog does not gather its look-alike crops, as naming a person does | done `49a17b8` (ARQUITETURA 21) |
| ✓ | R31 | medium | The face scan runs YuNet on full 1080p frames and halves live analysis outside events | done `d00b99f`: 137 → 45 ms per frame (ARQUITETURA 21) |
| ✓ | R32 | low | Browsers closing the live view log Windows asyncio errors (27 tracebacks) | done `ef464f8` |
| ✓ | R36 | low | A report can race a scan that reinforces the same entry, losing that one new view | done `0daa7ff`: taken out under the lock first (ARQUITETURA 21) |
| ✓ | R37 | low | A report says what it is not, never what it is (the user's own face filed as a dog) | done `72924d7`: "Actually…" in the Settings list (ARQUITETURA 21) |
| ✓ | R38 | **high** | A report made by mistake cannot be undone | done `2c2c943`: Settings → Bad-detection reports, with Undo; older reports undo too (ARQUITETURA 21) |
| ✓ | R39 | **high** | Person and dog pages showed no photos | fixed by the architect `76a5a9e`, release `v2026.10.11.5`: backlog 24 added a hidden proposal grid with the same class, and the page filled the first `.views-grid` it found — the hidden one. The tests cover the server only; a check of the page in a browser would have caught it |
| ✓ | R40 | **high** | Waiting views are hidden, and move into the chosen ones on their own | done `4d9a190`: Chosen and Waiting grids, ↓ ↑ × moves, Analyse can discard (ARQUITETURA 21) |
| ✓ | R33 | medium | The documentation had grown by appending: README stale, CONTEXTO read whole by every session | done 12/10 by the architect: CONTEXTO cut to a brief and this file; README, INSTALACAO, PYTHON and ARQUITETURA in English; ARQUITETURA reorganised by subject (text in 13.12) |
| ✓ | R41 | low | A view is moved by its position, which a full queue shifts when a scan adds one | done `f4fe810`: each move names the photo it was shown, 409 if it changed (ARQUITETURA 22.6) |
| ✓ | R34 | **high** | Devices have to type the PIN again and again | done `d6aa12e` (ARQUITETURA 21) |
| ✓ | R35 | medium | Aurora curled on the mat slips through R18 as `person` | closed without change: the five boxes a 1.5 ratio would drop were all people (ARQUITETURA 21); rare cases go to bad-detection reports |

**R1 — Notify a person who appears in the middle of an event (high).**
`EventRecorder._start()` tried to notify **only on the event's first frame**,
with that frame's labels. If the event began with a dog, `notify.event()`
refused (only `person` notified) and nobody tried again: the person arriving
seconds later **got no notification at all**, and so no second message with
the face either (ARQUITETURA 12.7), which depended on the first one having
gone out. On 30/09, 29 of the 85 events with a person also had an animal; in
every one where the animal came first, the person passed without a message
(the JSON does not keep the order, so how many cannot be said). Suggested fix:
in `update()`, while the event is not notified, try again when a label not yet
tried appears — at most one attempt per new label, so `config.json` is not
read every frame. The notification photo should be of the moment the person
appeared, not the event's thumbnail (which shows the dog), saved as
`<HH-MM-SS>.alert.jpg`, because the archive (`archive.py`) moves an event's
files with `glob(f"{base.name}.*")` and a name like `<HH-MM-SS>_alert.jpg`
would be left behind.

**R2 — A race at start-up (medium).** `main()` asked whether a J.A.R.V.I.S.
was already running (`web.already_running()`), but the port was only taken
after the cameras answered — up to 25 s per camera in `wait_ready()`. Two
clicks on the shortcut within that window brought up two instances, fighting
over each camera's single RTSP connection. Suggested fix: take the port
**before** opening the cameras (`web.start()` without a `Core`) and hand the
`Core` over later (`web.attach(core)`); until then `/api/cameras` answers
empty and the page must try again instead of showing "no cameras" forever.

**R3 — The live view freezes without warning (medium).** If the service
restarted or died, the MJPEG `<img>` stayed on its last frame with no sign
that it was no longer live — the worst kind of failure for surveillance.
Suggestion: the page polls `/api/cameras` every few seconds; with no answer,
it marks the images "no connection" and reconnects when the server returns
(changing the `src` with a new parameter so the browser does not reuse the
dead connection).

**R4 — Exposure on the network (medium, the user's decision).** The server
listens on `0.0.0.0` without a login, as decided (ARQUITETURA 17.4). But the
M900's Wi-Fi network is classified by Windows as **Public**, and the firewall
rule created applies to that profile. In practice any device on the same
Wi-Fi — visitors included — sees the cameras live and every recording.
Options: mark the network **Private** and restrict the rule to that profile;
or keep it as it is, knowing this. Not a technical decision: record the user's
choice here. **Decided on 09/10/2026:** the user keeps the port open to the
home network, to reach the interface from their other computer. Any device on
the same Wi-Fi can see the cameras; that is accepted. Closed.

**R5 — "Recognised" with a low similarity (medium).** The second message said
"<name> recognised" for any match above `MATCH_THRESHOLD` (0.363). With 40 px
faces, ARQUITETURA 10.4 already admits 0.37 can be chance — that is why
`LEARN_THRESHOLD` is 0.45. The message should reflect the difference: below
0.45, "probably <name>".

**R6 — Automatic tests (medium).** CONTEXTO 11 records the absence of tests as
a bias never discussed. This review added two cheap, valuable targets: the
thumbnail route's checks (the only barrier between the network and the files
on disk) and `notify`'s locks (`_allowed`, R1). FastAPI has `TestClient`; it
needs `httpx` as a development dependency. The check that day was a loose
script in the scratchpad, which does not stay in the repository.

**R7 — `instalar.bat` does not check the Python (low).** Step 3 installs the
official Python and ignores any error. If `winget` fails, `uv` falls back to
its own unsigned Python, and the problem of 09/10 returns without warning.
Suggestion: after `uv sync`, check the signature of `.venv\Scripts\python.exe`
and warn if it is not the Python Software Foundation's.

**R8 — A silent network failure on the page (low).** In `app.js`, a `fetch`
that failed (server down) became an error in the browser console and the list
stayed as it was. Show "No connection to J.A.R.V.I.S." in the summary.

**R9 — Check on the development PC.** `python-preference = "system"` was
tested only on the M900. On the dev PC, if another Python 3.14 is installed in
Windows, `uv` uses it; if not, it keeps its own. Next session there: run
routine 12.1, check which interpreter `.venv` uses and that `jarvis` starts.

### 13.5 Review 2 — what was fixed, and the new recommendations

Reviewed `760d68e..67f7d23` (the developer's pre-production delivery) against
the code and a real run, before the first release.

**Fixed by the architect in `8a81084`:**

- **R2 was only half fixed.** The port was checked in the main thread and bound
  later in uvicorn's; two launches a moment apart both saw it free. Now bound
  atomically with `SO_EXCLUSIVEADDRUSE` and handed to uvicorn. Tested: two
  launches at the same instant, one runs (ARQUITETURA 18.8).
- **Crash recovery would not have worked.** "Restart on failure" only acts when
  a task fails to start; a crash after starting would have ended the
  surveillance until the next reboot. Replaced by a 5-minute trigger with
  "ignore new", plus a `HOLD` file so the trigger cannot start production
  mid-update or after a deliberate stop (ARQUITETURA 18.7).
- **Updates needed admin.** Starting and stopping a scheduled task does; the
  script now stops through `--stop` and starts `pythonw.exe` directly, and only
  the task registration asks for elevation.
- **Several processes wrote `logs/jarvis.log`**, which Windows cannot rotate
  while another process holds it. Only the service writes it now.
- Smaller: `.env` written without a BOM; the test copy also loses
  `archive_path`; the rollback cannot skip its Telegram message; an em dash
  that PowerShell 5.1 read as a closing quote; unknown `config.json` keys are a
  warning in `check_data`, not a failure.

**Tested before tagging**, in a temporary folder: install, stop with hold, the
task's start refused while held, status, start, and an update to a version
broken on purpose — it failed the health check and rolled back on its own to
the previous version, both cameras fresh (ARQUITETURA 18.7).

**New recommendations:**

**R11 — `settings.save()` drops keys it does not know (high).** It keeps only
the keys in `DEFAULTS`. After a rollback, or any older version saving
`config.json` (the Ajustes tab, `discover_chat`), settings a newer version added
are erased. That breaks the user's rule from the other direction: the file stays
readable, but loses content. Fix: `save()` keeps unknown keys as they were.
Small, and should go in before any version adds a key that matters.

**R12 — Production and the test copy on the same M900 (medium).** Each runs
its own decode, MOG2 and YOLO. With both on, the 4-core Skylake carries double
the load, and production is the one that must not drop frames. Until backlog
item 4 measures it, run the test copy on the other computer, or briefly here.

**R13 — Verify the startup task (verification).** What only the real machine
can test: production comes back after a reboot with nobody logged on, and
within 5 minutes after its process is killed. Do both once after the first
install.

**R14 — Live MJPEG is encoded once per viewer (low).** Two browsers watching
encode every frame twice. Fine for one household; cache the last JPEG per camera
if it ever matters.

**R10 progress.** In English now: web routes and page, terminal and log
messages of the service, command-line flags, notification texts, CLAUDE.md, and
every section written since 09/10/2026. Still Portuguese: older documentation,
`capture.py` error messages (`TRANSLATIONS`, "FALHOU - ..."), `ui.py`,
`notify.discover_chat()`, and the Portuguese file names in `tools/` and the
`.bat` files.

### 13.6 The first night of production — 09/10/2026

The architect checked the install at 23:14, two hours after it went live.

**Healthy.** `status`: `v2026.10.09`, task ready, port 8765, both cameras'
last frame 0.0 s old. The task is S4U with the boot and 5-minute triggers, no
time limit, last result 0, no `HOLD`. The log has no warning or error since
the start at 20:20:55, and 19 events: 7 on Front, 12 on Back.

**What the user reported, and what was found:**

1. **Windows named "site-pack…" — two that stayed, others that flashed.**
   Production's ffmpeg. The install started production in the user's session
   (session 6), not through the task, and every console program started from
   `pythonw.exe` gets a window of its own (ARQUITETURA 18.7). The two that
   stay are the captures, the ones that flash are clip assembly and the face
   scan. Closing one kills that ffmpeg. → **R15.**
2. **"Not recorded going out for a delivery, nor coming back."** **It was
   recorded — both ways, in one event.** The user sent the trip exported from
   the Tapo app (two clips, 22:29:22 and 22:29:54). Production's
   `Front/2026-10-09/22-29-22.mp4` covers all of it and more, 56 s at 1080p:
   out of the door at 22:29:19, the gate, back with the order from 22:29:43,
   in at 22:29:57. What failed is everything the user *sees* of an event:
   - **The picture was the dog.** The event's thumbnail — the Recordings card
     and the Telegram photo — is the first analysis frame of the event. This
     one started a second before the user stepped out, on the dog lying on
     the mat detected as `person 0.72` (item 3). → **R19.**
   - **No face message.** Probed frame by frame (an architect's script, not in
     the repository): walking towards the camera for ~6 s, YuNet finds the
     face in almost every frame, but only **4 of ~90 frames** pass both
     `MIN_FACE_WIDTH` (36 px) and the frontal check — faces of 33–41 px while
     far, then turned towards the door and blurred when close (up to 77 px,
     not frontal). The scan reads **one frame in 14** (`MAX_SAMPLES` 60 spread
     over the 56 s clip) and hit none of the four. No sighting, so no face
     message. → **R20.**

   Also established while looking: **nothing recorded anything between
   30/09 22:54 and 09/10 20:21** — the test copy only ran for tests (its last
   clip is from 30/09), and production started at 20:20:55.

**Found while looking:**

3. **The white dog lying on the dark mat (or bed) at the bottom of the Front
   frame is detected as `person`** — 0.64 at 20:29:03, 0.72 at 22:29:22 (the
   thumbnails show the box around the dog and the mat). Each one records as a
   person event and notifies "person". → **R18.**
4. **Nobody can tell whether a notification went out.** `notify.event()` sends
   in a thread and throws the result away; a failed send leaves no trace. →
   **R16.**
5. **R13, crash test not run.** The architect tried to kill production's
   process to time the restart; Claude Code's auto mode refused it as
   interfering with a running workload. Left for the user: a reboot tests the
   boot trigger and, as a bonus, brings production back in session 0, without
   windows, until R15 ships.

**New recommendations:**

**R15 — ffmpeg console windows (high).** Start every subprocess in `src/` with
`creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)` — the flag only
exists on Windows, hence the `getattr`. Four places: `capture.py`
(`FFmpegCamera.start`), `clips.py` (`_concat`), `faces.py` (`_describe`,
`_sampled_frames`). Not `clips.reveal`, which opens Explorer on purpose. One
shared constant, not four copies. Acceptance: reproduce first — start the test
copy with `pythonw.exe -m jarvis --headless` from PowerShell
(`Start-Process`), and `Get-Process | Where-Object MainWindowTitle -like
'*ffmpeg*'` lists the windows; after the fix it lists nothing, also while a
clip is assembled. Production gets it with the next release.

**R16 — Log every notification outcome, without the token (high).** Log at
INFO, per attempt: camera, labels, and `sent`, `failed: <Telegram's
description>` or `skipped: cooldown`. Same for each face message of
`faces_seen`. **Security:** a `requests` exception message contains the URL,
and the URL contains the bot token (`/bot<token>/sendPhoto`). Redact it inside
`_call()`, before the detail reaches anyone — the log, a future Settings page,
a Telegram error — not at each caller. Acceptance: in the test copy, with a
wrong token and with the network cut, the log shows the failure and the token
appears nowhere (`Select-String` for the real token in `logs/` finds nothing).

**R17 — A replay tool: why was this not recorded? (medium).** First written as
high, when the trip looked like a miss; it was not (item 2), so it drops to
medium. Still wanted: R18 needs it, and so will the next real miss, which
today could only be diagnosed by hand, as item 2 was. Add
`tools/replay.py <video>`: it reads any video (a clip, or one exported from the
Tapo app), scales it to the analysis size the way `capture.py` does, feeds it
at `ANALYSIS_FPS` through the **real** `MotionDetector` and
`SubjectDetector`, and prints, per frame, what each layer kept and what it
dropped, and why — too small, not confirmed, lighting change, below
`MIN_PERSON_HEIGHT_FRACTION`, no motion overlap, static spot. If the classes
do not expose the reason, add an optional trace (a callback or a list) that
changes nothing when absent. `people.py` uses the clock (`MIN_INTERVAL`,
static spots): drive it with the video's time, not the wall clock, or a replay
faster than real time will decide differently from production. Acceptance: on
`Front/2026-10-09/20-29-03.mp4` it shows the dog detected as `person`; on
`20-23-07.mp4`, the person at the door; on `22-29-22.mp4`, the dog as
`person` in the first second, then the user.

**R18 — Dog on the mat as `person` (medium).** Do not tune before R17 shows
which frames and scores produce it. Candidate fixes, to choose with the data:
backlog item 1 (zones), or a rule against "persons" that never stand up in a
spot where a static object lives. Note that `notify_labels` is `person`, so
every one of these is a false alarm on the phone too.

**R19 — The event's picture should show the person (high).** Today the
thumbnail is the event's first analysis frame (`EventRecorder._start`), and
the first frame is whatever triggered the event — on 09/10 at 22:29, the dog.
The user looked at the event and saw no one. Direction: during the event, keep
the best view of a person in memory (confidence and box size; persons only,
falling back to the first frame when there is none), and at the end write it
as `HH-MM-SS.best.jpg`, with an optional `best_thumbnail` field in the event
JSON. **Additive, as the rule demands:** the first-frame `HH-MM-SS.jpg` stays
(it shows what triggered the event, which is what R18 needs), older events
without the field keep showing it, and the `base.*` name moves with the event
when archived. The page shows the best view when there is one. On the phone,
the first message must stay immediate, so it keeps the first frame; when the
event notified and the scan found no face, the follow-up message carries the
best view instead, so the phone always ends with a picture of the person.
Acceptance: on a copy of the 22:29 event in the test copy, the card shows the
user, and `check_data.py` reads old and new events.

**R20 — The face scan misses short frontal moments (high).** Measured on the
22:29 clip (item 2): 4 usable frames out of ~90, none of them sampled. One in
14 frames, spread evenly over the clip, is too coarse when a face is frontal
and large enough for a fraction of a second. Direction: sample densely where it
pays — the recorder already knows when persons were detected; pass those
moments to the scan and read every frame or every other one there, keeping the
sparse pass for the rest. Measure the cost on the M900 (YuNet on 1080p frames,
on the 4-core Skylake) and report it in `HANDOFF.md`. Acceptance: rescanning
a **copy** of `22-29-22.mp4` in the test copy finds the user's face. Never
write into `C:\JARVIS` from a test — copy the event into the test copy's
`clips/` first.

### 13.7 Review 3 — developer session 1

Reviewed `2ed3fb4..87e736b`, the whole diff, against the HANDOFF's claims.
Nothing needed fixing: the code does what the HANDOFF says, `check_data`
reads all 150 events, no comments, and the two pieces worth re-running by
hand behaved — the token is redacted both literal and `%3A`-encoded, and the
`select` expression for a person seen 36–44 s into the clip comes out as
`not(mod(n\,14))+(between(t\,34.50\,45.50))*not(mod(n\,2))`. The developer
reproduced every problem before fixing it, which is what the `dev` skill asks.
What changed is in ARQUITETURA 12.9, 18.7 and 19.2.

**What the review weighed hardest:**

1. **R20's cost is real and unmeasured where it matters.** A dense scan is
   ~45 s of multi-threaded DNN per event with a person, on the same 4 cores as
   live analysis. Capture drops frames rather than queueing them, so the cost
   would show as fewer analysed frames — and temporal confirmation counts
   frames, so a fast walker right after an event could go unconfirmed. On the
   first night, 9 of 19 events had a person label. Released anyway: the face
   message is what the user asked for, the sparse scan already took 12 s, and
   the measurement needs production-like load. → **R21.**
2. **R19 doubles R18's false alarms.** An event started by the dog on the mat
   (detected as `person`) now sends its first message with the dog and, with no
   face found, a follow-up with the best view — the dog again. → **R18 raised
   to high.**
3. **Where did the dense scan look?** Nothing logs or stores the spans, so the
   clock alignment (spans and segment names both use the PC clock, so it
   should hold) can only be confirmed by replay. → **R22.**

**R21 — Measure what the dense scan costs live analysis (high, verification).**
Count analysed frames per camera per minute — a counter in the `Core`, exposed
in `/api/status` and logged once a minute while a scan runs — and compare the
rate during a dense scan with the rate without one, on the M900 with
production's load. If it falls by more than a third, options in order of
cost: run the scan's DNN with fewer threads (`cv2.setNumThreads` is global, so
this needs care), run YuNet only on the head region of person boxes, or scan
with a lower priority.

**R22 — Log where the dense scan looked (medium).** One INFO line per scan:
the clip, the spans in seconds, frames read and time taken. Storing the spans
in the event JSON, as the developer proposed, would also let
`refazer_rostos.py` rescan densely; it is additive, so allowed, but not needed
until a rescan is.

**R10, left:** older documentation, `ui.py` (including its Telegram test text),
`cameras.build_camera_list()`'s `SystemExit`, `tools/diagnostico.py`, and the
Portuguese file names.
### 13.8 Review 4 — developer session 2

Reviewed `5d91305..1b8822d`. No code fixed. The trace hooks in `motion.py`
and `people.py` change no decision (the developer compared old and new on all
561 frames of the 22:29 clip); every module imports, `ui.py` included after
its translation; no comments; the version reads `v2026.10.10-12-g1b8822d` in
the test copy. Integrated into ARQUITETURA 12.10.

**R21's fix, decided by the architect — R23.** The developer measured that a
dense scan makes YOLO 1.6× slower and that fewer threads only make YOLO slower
still, and left the choice to the review. It is a design call, not the
user's. The options weighed:

| Option | Verdict |
|---|---|
| Fewer OpenCV threads for the scan | measured wrong: the setting is process-wide |
| YuNet only on head regions | cheaper scan, but needs person boxes per clip frame, aligned in time — complex, and the scan still overlaps events |
| Lower thread priority | does not reach OpenCV's shared worker threads |
| Wait to start the scan while a camera records (the developer's idea) | good, but a 45 s scan that has started still collides with the next event |
| **Pause the scan between frames while any camera records** | chosen: the collision only matters during an event, and this removes it wherever the event starts |

**R23 — Pause the face scan while any camera is recording (high).** Before
each frame, `_scan_clip()` asks a callable `busy()` and sleeps in short steps
while it is true; the ffmpeg feeding the pipe simply blocks meanwhile.
`clips` provides `busy()` — any `EventRecorder` recording — and passes it in,
so `faces` knows nothing of cameras. A ceiling, 10 minutes of pause per scan,
keeps a busy evening from starving it; the R22 log line gains the pause total.
The face message arrives later during long activity; the first message is
untouched. Acceptance: with the measurement of R21 repeated during an event,
YOLO's time is back to its unloaded value while the scan is paused.

**R18 — decided.** The user first chose to wait, then asked the architect to
set the rule. The replay's data: the dog's `person` boxes are 3.3–4.2× wider
than tall and their bottom touches the frame's bottom edge (y ≈ 538 of 540);
every real person seen was taller than wide (110–152 × 267–320). The rule, in
`SubjectDetector.detect()`: **drop a `person` whose box is more than
`WIDE_PERSON_RATIO` = 2.5× wider than tall and whose bottom lies within
`BOTTOM_EDGE_FRACTION` = 3 % of the frame's bottom**, with the trace reason
"wide at the bottom edge". Both conditions, not one: a wide box alone could be
a person lying on the lawn mid-frame — rare, but worth keeping; the mat is at
the bottom edge, where a standing person's box is always tall. The margin from
2.5 to the dog's 3.3 is deliberate. Acceptance: `tools/replay.py` drops the dog
on `20-29-03` and `22-29-22` and keeps the user; then replay **every** event
with a `person` label from 09/10 and 10/10 (copies, in the test copy) and list
each detection the rule changes — none may be a real person.
**Lesson worth keeping:** "give the scan fewer threads" sounded obviously
right and measured wrong. Measure before choosing, even the obvious.
### 13.9 Review 5 — developer session 3

Reviewed `11c6663..5f3c356`: R23, R18 and web stage 4. No code fixed. The new
routes check every input, the face route stays inside `faces/`, the page never
builds HTML from data (no `innerHTML`), and the token is write-only. Integrated
into ARQUITETURA 12.10 and 17.9. The three points the developer left open,
decided here rather than handed to the user:

1. **R18 at 2.0 instead of 2.5 — accepted.** The replay found the dog sitting
   up at 2.42–2.48; real persons measure 0.4–0.6.
2. **A paused scan keeps the lock — accepted.** Late face messages on a busy
   evening are the price of an undisturbed YOLO; the first message never waits.
3. **Writes from the network — R24.** R4 accepted that anyone on the Wi-Fi can
   *see* the cameras; stage 4 lets them also rename faces (and a merge cannot
   be undone yet) or point the notifications elsewhere. Restricting writes to
   the M900 would lock out the user's other computer, which R4 wanted to keep.
   There is also a second door: a web page the user opens could make the
   browser post to the service (cross-site request forgery). The solution
   keeps both the convenience and the safety:

**R24 — Guard every write (high).** (a) Every `POST` must carry a custom header
(`X-Jarvis-Request: 1`), which `app.js` adds; a foreign page cannot add it
without the browser first asking permission, and the service never grants it —
that closes the forgery door for free. (b) Writes from any address other than
127.0.0.1 need the device to be **paired once**: a PIN set on the M900's own
page, kept in `config.json` as `write_pin` (an additive key), typed once on
the other computer, remembered by that browser and sent with each write;
compared with `hmac.compare_digest`. With no PIN set, writes from the network
are refused with a message saying how to set one. Reading stays open, as R4
decided; shutdown stays local only. Acceptance: a write from the other
computer fails without the PIN and works after pairing; a `POST` without the
header fails even from 127.0.0.1; `check_data` reads the new key.

Released anyway as `v2026.10.10.3`: the user wants People on the web, the
exposure needs someone on the home Wi-Fi who knows the address, and R24 is
the next session's first item.
### 13.10 Review 6 — developer session 4, and the face messages

Reviewed `3a91964..5eb8964`. No code fixed: every path that touches a
person's `embeddings` goes through `_take` or `remove_view`, both inside the
gallery lock and both saving; imports, comments and `check_data` clean.
Integrated into ARQUITETURA 17.10 and 19.2. The threat model of R24 is
accepted as written there.

**"Fewer face messages — is that normal?" (the user, 10/10).** Measured on
production's log, from 13:31 to 15:15: 10 events with a person, 6 first
messages sent, 4 skipped by the cooldown, 21 face scans, **2 with a usable
face**, 1 face message and 4 best-view messages. Mostly normal: a face must be
frontal and at least 36 px wide, which daytime walkers seen from the gate
rarely are, and sightings per person event are about the same as on 30/09
(4 of 18 against 15 of ~85). R18 also removed the dog's false person events,
so there are fewer notifications overall. One part is a real gap: a face
message is only sent when the event's own first message went out, so a face
found in an event that fell in the 120 s cooldown is never announced — and a
face is the most valuable message there is.

**R25 — Send a found face even when its event was in the cooldown (medium,
decided by the architect).** The cooldown exists against repeated events, not
against faces, which are rare (2 of 21 scans). Rule: after the scan, send the
face message whether or not the event's first message went out, with its own
cooldown per person — the same person is not announced twice within
`notify_cooldown`. The best-view follow-up keeps today's rule (only after a
sent event), so the volume barely changes.
### 13.11 Review 10 — the user's three reports (11/10/2026)

**"The pages fail on the other computer."** Root cause found: the service
sends no cache instruction for the page, `app.js` or `style.css`, so a browser
may keep running a stale copy for hours after an update, by its own heuristic
on `Last-Modified` — and on 10/10 the routes changed in seven releases, so an
old `app.js` calls routes that no longer exist. A second, smaller cause: a
change refused by the R24 guard (an unpaired browser) fails without a visible
reason. Testing "another computer" needs no second machine: the M900's own
browser at `http://192.168.0.18:8765` is not 127.0.0.1, so the guard treats it
exactly as the other computer.

**R28 — The page is always current, and every refusal says why (high).**
`Cache-Control: no-cache` on `/` and `/static/*` (the browser revalidates by
ETag every load, a cheap 304 on the LAN), and the version from backlog 18 in
the asset URLs (`app.js?v=<version>`), so an update can never leave an old
script running. Every failed write shows the server's reason on the page; a
403 from the guard says "this device is not paired — enter the PIN in
Settings". Acceptance: after a deploy, a browser at 192.168.0.18 loads the new
script without a hard refresh; an unpaired write shows the message.

**"The Dogs tab should behave like People: favourite photo, 40 views,
grouping."** The first two exist — the Dogs tab is the same code as People
(ARQUITETURA 20) — and the other computer's stale page (R28) can hide them.
Grouping does not: naming a person gathers the unnamed faces that clearly
look like them (`_absorb`), but the developer turned it off for dogs.

**R29 — Naming a dog gathers its clear look-alikes (medium).** Enable
`_absorb` for dogs with the **sure** rule of `match` (distance and margin),
never the probable one, and only within the same lighting. A wrong grouping is
undone by Dismiss or a rename, as with people. **Widened by the user's idea (11/10):** every naming or merge re-examines all the unnamed crops against the dog's updated views, repeating until nothing more joins — a new view can make other crops recognisable — exactly as `Gallery.rename` already does for people (`_absorb` loops until no change). And past recordings must follow: today a dog sighting stores its words at recording time, so an event recorded as "unidentified dog" would keep saying so after its crop joins Mirana. Show the current name from the sighting's `dog_id` (sightings are repointed on merge, as for faces), keeping the stored certainty only for "probably".

**"Face detection seems much weaker."** The log shows no regression: scans run
and find faces when there are frontal ones (21:05 on 10/10: 58 face views),
and most person events at night have none — infrared faces are small. What
changed is visible, not measured: the gallery restarted empty on 10/10, so
every face is "unknown" until named again. To tell a regression from the
night, the user is asked for one or two events where their face was clearly
visible and no face came; `tools/replay.py` and the face probe then show which
filter dropped it.
### 13.12 Review 11 — a general review, and the missing face messages (11/10/2026)

The user asked, with no new feature in the queue, for a general review —
efficiency, performance, UX, documentation — and pointed at the person
notifications that are never followed by a face.

**The faces: found, then dropped as "not frontal".** Since 10/10 13:31, 43
person events: every one was scanned, 16 found a usable face, 27 did not. A
sheet of the 27 best views shows the night ones are what infrared allows, but
several daytime Front ones show a person close and well lit. Replaying three
of them (17:51:51, 15:50:37, 15:47:40) through YuNet: faces in 61 frames,
37–65 px wide, score about 0.8 — **and every one dropped by `is_frontal`**:
nose offset 0.47–1.01 against the 0.35 limit, eye spread 0.14–0.27 of the face
width against 0.38. Three-quarter and side views of someone walking to the
door. The filter is strict on purpose (an embedding of a profile describes
nobody, 10.9), but it also costs the user the face photo.

**R30 — Show the face even when it cannot be recognised (high).** Two parts.
(a) When a person event's scan keeps no recognisable face but YuNet saw faces
on a person (score ≥ 0.75, width ≥ 36 px), send the best of them — closest to
frontal, then largest — as a face photo ("face, side view"), **without adding
it to the gallery**; it replaces the best-view message for that event. (b)
Measure whether the frontal limits can be loosened for recognition: with the
user's views named, compute the match score of the three-quarter faces of
their own clips; loosen `MAX_NOSE_OFFSET` / `MIN_EYE_SPREAD` only as far as
the right person still wins.

**Performance — R31 (medium).** Outside events the scan is not paused, and
live analysis dropped to ~270 frames a minute per camera while one ran
(21:06 on 10/10), against ~580. YuNet runs on full 1080p frames (~143 ms
each). Run detection on the half-size frame and only the alignment on the
full-size crop, which should cut the scan's cost several times; measure
before and after with the R21 counter.

**Log noise — R32 (low).** 27 "Exception in callback
`_ProactorBasePipeTransport._call_connection_lost`" tracebacks at ERROR: Windows'
asyncio reporting a browser that closed the live view. Install a loop
exception handler that drops `ConnectionResetError` there, so ERROR means a
real problem.

**UX.** The main failure is R28 (stale page, silent refusals); not clicked
through beyond it. Worth a pass with the built-in browser after R28 lands.

**Documentation — R33 (medium, the architect's own).** README still describes
three OpenCV tabs and `jarvis.bat` opening a window; ARQUITETURA (2,909 lines)
and CONTEXTO (1,388) grew by dated appendices (12.9, 12.10, 17.9, 17.10, 20).
CONTEXTO is read by every session's resume routine — about 25k tokens each
time. Plan: README rewritten in English; CONTEXTO cut to the current brief
(rules, state, backlog, open recommendations, plan), with the review history
and usage log moved to a `docs/HISTORY.md` read on demand; ARQUITETURA
reorganised by subject with the dated sections folded in; and R10's
translation done along the way. To be done in a new conversation, where the
documents can be read whole without this one's 750k of context.
### 13.13 Pairing a device once (11/10/2026)

The user has to type the PIN again "all the time" on their devices and asked
for one validation, or at least 30 days per device. The page keeps the PIN in
`localStorage`, with no expiry of its own — but browsers do clear it: Safari
deletes script-written storage of a site unused for 7 days, private windows
and "clear data on close" settings drop it, and a different address
(`192.168.0.18` against the M900's name) is a different store. Re-typing the
PIN is the symptom; storing the secret in the page is the cause.

**R34 — Pair a device once, for 30 days that renew with use (high).** Pairing
with the PIN makes the server set a cookie — `HttpOnly`, `SameSite=Strict`,
`Max-Age` 30 days — holding a random device token; the server keeps only its
SHA-256 hash, with a label and the last use, in a new file `devices.json`
(additive). Every write from a paired device renews the 30 days, so a device
in use never asks again; one unused for 30 days asks once. A cookie set by the
server survives where `localStorage` does not (Safari's 7-day rule applies to
storage written by scripts). The custom header of R24 stays, so cross-site
forgery is still blocked; the PIN header keeps working as before. Settings on
the M900 lists the paired devices with "forget" (and changing the PIN forgets
them all). Acceptance: pair once through 192.168.0.18, close and reopen the
browser, write without typing anything; a forgotten device is refused; tests
for expiry and renewal.

### 13.14 Review 14 — developer session 12 (11/10/2026)

The scheduled cycle of 17:23: the architect started the developer on R38 →
R40 → R37 → R36 and reviewed `1cea950..e03a083` whole. No code fixed: the
lock order of R36 holds (`take_out` returns the entry under
`_GALLERY_LOCK`, the slow copies run outside it, `put_back` on failure), the
new routes check `kind` and the report name against `SAFE_NAME` and
`SAFE_REPORT` before touching a path, every new POST passes the write guard,
and Undo copies a photo back only where none exists. 92 tests pass,
`check_data` reads everything, no comments.

**Found while checking: `uv run pytest` no longer runs on the M900.**
Smart App Control blocks `.venv\Scripts\pytest.exe`, an unsigned launcher
(os error 4551); `uv run python -m pytest` runs the same tests through the
signed Python. The developer had already used the second form; the docs and
the `dev` skill now say so (ARQUITETURA 19.5).

**The developer's questions, decided.** (1) An old report undone with more
than one view keeps its crop as the entry's thumbnail, a file that a later
report does not delete: accepted, both production reports have one view. (2)
The last chosen view cannot be deleted even with views waiting: right — it
is the user's rule that they pick, and a person without a chosen view
matches nobody. (3) ↓ refused while Waiting holds 100, instead of dropping
the oldest as a scan does: right, the user did not ask to lose a photo. (4)
A scan that matches an entry while it is being reported still writes its
sighting: if the report is undone it counts again, otherwise the recording
card reads "unknown" — honest, no change. Also accepted: if writing a report
raises after its JSON exists, the entry goes back and the JSON stays; its
Undo answers 409.

**R41 — A view is moved by its position, which a full queue shifts (low).**
The four moves and the favourite address a view by its index in Chosen or
Waiting. A scan never reorders Chosen, but when Waiting holds 100 it drops
the oldest waiting view, so every waiting index shifts by one: a × clicked on
a page loaded before then deletes the neighbour, a photo the user did not
pick. It needs a full queue and a scan finishing while the user is on the
page. Fix: each move also sends the photo name it was shown ("" for a view
without one), and the server refuses with 409 — "the views changed: the page
was refreshed" — when the view at that index is no longer it, the check
`keep_spread` already makes with its signature. Acceptance: a test fills
Waiting, reads the page, lets a scan add a view, and a × on the old index is
refused.

### 13.15 Review 15 — developer session 13 (12/10/2026)

Backlog 25 and R41, reviewed whole (`v2026.10.11.6..e7df623`, 19 files). The
rules matrix, the defaults built from an older `config.json`, the resident
flag through rename and merge, the bot's chat check and the R41 check under
the lock all hold; every new POST passes the write guard; `check_data` reads
everything; no comments; 158 tests pass as delivered. Away is today's
behaviour, as the developer said: every person case on means nothing is held.
R41's corner (a stored view with no page URL would always answer 409) does not
occur: every view in production's two galleries and the test copy's has a URL.

**Fixed in the review (`5224983`), reproduced first by two tests.** (1) In a
mode that holds people, the faceless message checked the camera cooldown even
when the same event had already sent a message: Home with a dog switch on, a
dog announced a moment before, and the person with no recognisable face — the
case the user wants on the phone in Home — was skipped as "cooldown". Inside
one event it is a follow-up, as it always was in Away; the cooldown now
applies only when nothing of the event went out. (2) A held person whose clip
could not be assembled got no message at all; it now sends the best view. 160
tests pass.

**The developer's other points, decided.** `_notify_late` now records the new
labels even after a sent message: right, it is what lets a person arriving
after a dog's message be held. One switch for every non-dog animal, instead of
`notify_labels` per label: as backlog 25 (b) specified. A tap on a `/mode`
button has no date, so one made while production was down is obeyed at the
next start: accepted, it sets the mode the user tapped. `bot.py` against the
real Bot API is first exercised by this deploy: watch `jarvis.log` for
`Telegram commands:`.

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

**R43 — `config.json` is rewritten in place, with no lock, by two writers
(low).** `settings.update` reads, changes and writes the whole file with
`write_text`, which truncates first. Until 12/10 only the page wrote it; now
the bot does too (`/home`). A read that lands inside another write sees a
truncated file, `_stored()` answers `{}`, and an `update` that started from it
saves the defaults — **the token, the chat, the PIN and the archive path
erased**. It needs two writes within milliseconds of each other (a switch on
the page and a command from the phone at the same moment), so it is unlikely,
but the loss is silent. Fix: one lock around `update`, and write to a
temporary file then `os.replace` it — keeping in mind that on Windows
`os.replace` fails while another thread has the file open, so it needs a short
retry. Acceptance: a test where two threads update different keys many times
and both survive.

### 13.16 Reading the bad-detection reports (12/10/2026)

Asked by the user, who sees themselves "a lot" on the Dogs tab. Production
held 6 dog reports and no face report. Every one is "not a dog", every one is
on Front by day, and **every reported event also had `person`**. A sheet of
each crop beside its event showed two kinds:

| Kind | Reports | What the crop shows |
|---|---|---|
| The user bent over | 4 (15:36:08 on 10/10; 11:28:48, 12:39:56, 12:40:23 on 12/10) | bending into the car door, or over Mirana while petting her |
| A dark object at the bottom of the frame | 2 (17:45:14 on 10/10 — "Actually: nothing"; 11:45:20 on 12/10) | a still, dark shape at the bottom of Front, near the door |

**Measured on the clips** (YOLO replayed at 4 fps on the M900, a scratch
script beside `replay.py`): the 6 reported clips, 6 clips where a named dog
was matched for sure and a person was also in the event, and 6 with the dog
alone — 644 dog boxes in all. The true-dog clips with a person:
`Back/2026-10-12/12-40-35`, `Back/2026-10-12/13-59-03`, `Front/2026-10-11/16-20-00`,
`Front/2026-10-11/16-34-56`, `Front/2026-10-12/17-01-55`, `Front/2026-10-12/17-35-54`.

- **YOLO's own scores do not separate them.** The bent-over user is `dog` at
  0.62–0.81 (median 0.74, like real dogs at 0.68), and the `person` score in
  the same box is 0.00 at the median, at most 0.18: YOLO is sure.
- **Touching the bottom edge does not either**: true dogs do too (Aurora on
  the mat: 10 of 10 boxes in one clip).
- **A human face inside the box does not**: YuNet found none in the reported
  boxes (the head is down or away).
- **"Inside a recent person's box" does not**: a real dog at someone's feet is
  inside the person's box too (49 of 309 true boxes at ≥ 0.5).
- **The person's own box, a moment before, does.** IoU ≥ 0.5 with a person box
  seen in the previous 2 s: **9 of the 15 reported boxes, 0 of 309** true-dog
  boxes in events with a person (14 of 309 at ≥ 0.3). The bending user keeps
  almost the same box (IoU 0.90–0.99) while YOLO changes the class.

That became R44 (CONTEXTO 13.4). It leaves 3 reports: the two dark-object ones
(IoU 0.12 with any person) and one bend at 12:40:23 with no person seen in the
2 s before. The dark object is a candidate for using the reports themselves —
a reported box marks a place that is not a dog on that camera — but two
reports are too few to set a distance, and Aurora lies on a mat nearby. It
waits for more reports, which backlog 26's "Bad detection" on many crops at
once makes cheap to give.

## 14.3 Usage log, up to 12/10/2026 morning

The current rows are in `CONTEXTO.md` 14.3.

| # | Role | Effort | Date | Scope | 5-hour window | Weekly | Context |
|---|---|---|---|---|---|---|---|
| — | both | high / ultracode | 29/09–09/10 | everything before this table | not measured | — | one conversation since 29/09, compacted several times |
| A3 | architect | ultracode | 09/10 23:10–23:40 | finish review 2's docs, check production's first night, diagnose the windows, R15–R18, plan dev session 1 (to 23:25: 25%); then the user's Tapo videos — contact sheets, a frame-by-frame face probe, R19–R20, plan revised (+9 points); then pandoc, the EPUB and its checker, the `dev` skill (+3 points) | 0% → 37% at 23:46 (the window opened at 23:10 and resets at 04:10; the first 22% includes resuming a compacted conversation) | 30% → 32% | 106k → 223k tokens |
| A4 | architect | ultracode | 09/10 23:50 – 10/10 00:31 | user's Tapo videos already counted in A3; here: the raid log, issue 1 (6 pages of SVG, page renders checked as images), its tool and section 15 | 37% → 61%, **shared with developer session 1 running at the same time** in another conversation — its own numbers are in its HANDOFF | 32% → 35% | 223k → 314k tokens |
| D1 | developer | high | 10/10 00:00–00:30 | session 1: R15, R16, R10 in part, R19, R20, R11 (HANDOFF) | 39% → 52%: R15 3, R16 + R10 2, R19 4, R20 4, R11 and HANDOFF under 1 | 32% → 34% | 66k → 210k tokens |
| A5 | architect | ultracode | 10/10 00:52–01:00 | review 3, HANDOFF integrated, release `v2026.10.10` | 77% → 82%: review and docs, about 5 points | 37% → 37% | 404k → 445k tokens |
| A6 | architect | ultracode | 10/10 00:55–01:15 | production update to `v2026.10.10`, R13 reboot and crash checks, EPUB | 82% → 87% | 37% → 38% | 445k → 470k tokens — at this size every turn costs about a point, the strongest reason yet for a new conversation per session |
| D2 | developer | high | 10/10 04:10–04:40 | session 2: R21 measured, backlog 18, R22, R17, R10 code part; R18 deferred by the user | 0% → 11% (new window): R21 3, backlog 18 + R22 2, R17 3, R18 question + R10 3 | 39% → 41% | 241k → 330k tokens, carried over from session 1 |
| A7 | architect | ultracode | 10/10 13:25–13:35 | review 4, R23 decided, release `v2026.10.10.2`, comic scripts 2 and 3 (one failed shell append re-sent them) | 9% → 15% | 43% → 44% | 500k → 540k tokens, in the old conversation |
| D3 | developer | high | 10/10 13:45–14:20 | session 3: R23, R18, web stage 4 | 22% → 34%: R23 2, R18 2, stage 4 8 | 45% → 46% | 336k → 405k, old conversation again |
| A8 | architect | ultracode | 10/10 14:25–14:45 | backlog 19, review 5, R24, release and production `v2026.10.10.3`, script 4 | 35% → 38% | 47% → 47% | 557k → 580k tokens |
| D4 | developer | high | 10/10 14:35–15:30 | session 4: R24, backlog 19 and 20, window removed | 43% → 62%: R24 5, backlog 19 10, backlog 20 2, window 2 | 48% → 50% | 412k → 505k, old conversation |
| A9 | architect | ultracode | 10/10 15:35–15:55 | the face-message question, review 6, R25, release and deploy `v2026.10.10.4`, gallery deleted, script 5 | 64% → 68% | 50% → 51% | 610k → 645k tokens |
| D5 | developer | high | 10/10 15:40–15:50 | session 5: R25, R6 (23 tests) | see its HANDOFF; small | — | 509k at the start, old conversation |
| A10 | architect | ultracode | 10/10 16:00–16:50 | review 7, httpx2 check, backlog 21, release and deploy `v2026.10.10.5`, script 6 | 68% → 78% (shared with developer session 5 in the same window) | 51% → 52% | 650k → 663k tokens |
| D6 | developer | high | 10/10 16:10–16:20 | session 6: backlog 21, R26 | 81% → 84% | 53% → 53% | 542k → 560k, old conversation |
| A11 | architect | ultracode | 10/10 16:25–16:35 | review 8, release and deploy `v2026.10.10.6`, script 7 | 86% → about 89% | 53% → 53% | 669k → 680k tokens |
| D7 | developer | high | 10/10 evening | session 7: backlog 22 parts 1 and 2 | 10% → 23% (new window) | 56% → 57% | 564k → 635k, old conversation |
| A12 | architect | ultracode | 10/10 21:00–21:20 | review 9, R27, release and deploy `v2026.10.10.7`, dog crops in production, script 8 | 36% → ~43% | 59% → 60% | 705k → 720k tokens |
| D8 | developer | high | 11/10 morning | session 8: R27, dog tuning tool | 11% → 15% | 61% → 61% | 638k → 655k, old conversation |
| A13 | architect | ultracode | 11/10 morning | review 10: the three reports, R28, R29, release `v2026.10.11` | 29% → ~36% | 63% → 64% | 720k → 740k tokens |
| D9 | developer | high | 11/10 08:00–10:30 | session 9: R28, R30 (a); a built-in browser call hung for an hour | 36% → 76% (shared with the architect) | 64% → 70% | 659k → ?, old conversation |
| A14 | architect | ultracode | 11/10 09:30–10:50 | the side-view finding, general review, settings help, automatic handover, review 11, release `v2026.10.11.2` | shared window, ~81% → ~85% | 70% → 70% | 750k → 790k tokens |
| D10 | developer | high | 11/10 12:23–12:55 | session 10, started by the architect: R34, backlog 5, R29 | 0% → ~43% | 72% → 77% | old conversation |
| A15 | architect | ultracode | 11/10 12:55–13:10 | review 13, release and deploy `v2026.10.11.3`, script 9 | ~43% → 47% | 77% → 78% | 820k → 832k tokens. **The first automatic cycle cost ~47 points of the 5-hour window, ~43 of them the developer's old conversation** |
| D11 | developer | high | 11/10 13:00–14:50 | session 11, **a new conversation**: backlog 23, 24, R31, R32, R35 and R30 (b) measured | 47% → ~72% for six items | 78% → 81% | started light |
| A16 | architect | ultracode | 11/10 14:50–15:15 | review 14, release `v2026.10.11.4`, a rolled-back deploy diagnosed and fixed, script 10 | 72% → ~78% | 81% → 82% | 860k → 880k |
| D12 | developer | high | 11/10 17:25–17:40 | session 12, the scheduled cycle, a new conversation: R38, R40, R37, R36 (92 tests) | 34% → 44%: R38 4, R40 4, R37 1, R36 1 | 87% → 88% | 74k → 193k tokens |
| A17 | architect | ultracode | 11/10 17:38–17:50 | review 14, docs, comic script 11, release and deploy `v2026.10.11.6` | 45% → 53% | 88% → 89% | 78k → 180k tokens, a new conversation. **The whole scheduled cycle cost ~19 points of the 5-hour window (dev 10, architect 8) and ~2 of the week** |
| A18 | architect | ultracode | 12/10 10:50–11:00 | the notification cases counted from production's log, backlog 25 designed with the user, cycle started | 3% → 6% (new window) | 90% → 90% | 182k → 210k tokens, review 14's conversation |
