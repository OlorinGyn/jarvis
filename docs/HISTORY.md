# J.A.R.V.I.S. — history

What used to fill `CONTEXT.md` and is no longer needed to resume work: the
bugs already fixed, old measurements, a solved incident, the long text of
finished backlog items, every review in full, the closed recommendations and
the old rows of the usage log. Moved here on 12/10/2026 (R33), so every
session's resume reads a short brief instead of about 25k tokens.

**Section numbers are the ones `CONTEXT.md` had**, so an older reference to
CONTEXT's section 13.6 now means HISTORY 13.6. Read on demand, not at every
resume. From review 15 on, each review writes its own section here (13.16,
13.17…) and its row in 13.2; a recommendation's text moves here from
`BACKLOG.md` 2 when it closes.

---

## 4. Bugs found and fixed — do not reintroduce

| Bug | Cause | Fix |
|---|---|---|
| The window did not close on X | HighGUI has no close event; the next `imshow` recreates the window | Check `getWindowProperty` **after** `waitKey` |
| The video stretched on resize | `WINDOW_KEEPRATIO` is 0 on the Win32 backend | Build an image of the window's exact size with `getWindowImageRect` and letterbox it |
| Clicking a card opened Documents | `subprocess` with a list quotes every argument with a space, and Explorer's `/select,` went inside the quotes | Pass a ready-made string on Windows |
| Face detection found nothing | Sampling read the clip's first frames, and the pre-recording makes the start come **before** the person arrives | Compute the step from the total frame count |
| A 44 px face was thrown away | `MIN_FACE_WIDTH` too high | Lower the floor and **mark** small faces instead of dropping them. Today the frontal-face test filters, not the width (ARCHITECTURE 10.9) |
| The gallery ignored a test path | `def __init__(self, path=GALLERY_FILE)` freezes the value at definition time | `path=None` and resolve inside |
| Grey "Not Responding" window | The loop blocked reading the pipe; the first frame takes **2.45 s** | One reader thread per camera; the loop never blocks |
| "no signal" with no reason | ffmpeg's `stderr` went to `DEVNULL`, and the start-up `ok` checked `poll()` before the process had time to fail | Capture stderr, wait for a real first frame, translate known errors |
| False person detections | Wall objects under infrared | Minimum height (measured: false 36–86 px, real people 294–306 px, **18/18 right**) |
| Mosquitoes triggering recordings | Insects near the lens look big in IR | Temporal confirmation: only what stays 3 frames in the same place is reported (**83 % fewer triggers**) |
| "no frame received" on the M900, no error | `.env` with `.env.example`'s sample IPs; with no timeout ffmpeg waits for TCP forever, silently | `-timeout` on RTSP and a translation of `Error number -138` (section 6) |
| False daytime motion on Front | Patches of sun and leaf shadow; the camera's clock in the corner | Lighting filter by correlation with the background, and a mask over the clock: **99 → 15 frames**, person covered 262 → 258 of 273 (ARCHITECTURE 6.7) |
| 14 "people" for 3 real ones; a name was not recognised later | Every unmatched face became a person (profiles, the back of a head, an arm); the same name created twins; it only learned from faces ≥ 80 px | Frontal-face filter + YOLO, joining by name, absorbing on naming, learning by similarity (ARCHITECTURE 10.4, 10.9) |
| The program crashed right after an event (`buf.shape() == m.shape()`) | The face scan used the live loop's YOLO network, from another thread | A network of its own for background threads, and scans in a queue (ARCHITECTURE 10.9) |
| Terminal full of `[h264] error while decoding MB` | The Back camera sending damaged blocks (Wi-Fi), printed by OpenCV's internal decoder during the face scan | The scan reads through our own ffmpeg with `-loglevel quiet`, 2× faster; `tools/check_clips.py` measures the damage (ARCHITECTURE 10.11) |
| Poor face photo | It was the recogniser's 112 px crop, enlarged twice | A crop of the original frame with hair and shoulders, 300 px (ARCHITECTURE 10.10) |
| Scripts depended on the current folder | Relative paths (`Path("clips")`) | `ROOT` in the package; every path starts from the root (ARCHITECTURE 3.2) |
| The M900 would not start, `Failed to spawn: python` (`WinError 4551`), 09/10 | Smart App Control started refusing the Python `uv` downloads (unsigned) — the same file that ran on 29–30/09; the reputation verdict changed on its own | The official Python signed by the PSF + `python-preference = "system"`; the `.bat` files call `python -m jarvis`, without the unsigned `jarvis.exe` (INSTALL 1.2) |

| A person arriving after an animal was never announced (R1) | Notification tried only on the event's first frame | One attempt per new label during the event, photo `HH-MM-SS.alert.jpg` (ARCHITECTURE 12.8) |
| Two launches a moment apart brought up two copies (R2) | Port checked, then bound later in another thread | Port bound atomically in the main thread, `SO_EXCLUSIVEADDRUSE`, handed to uvicorn (ARCHITECTURE 18.8) |
| Live picture froze when the service restarted (R3) | A dead MJPEG connection keeps its last frame | `frame_age`, "no signal" after 5 s, page reconnects when `started` changes (ARCHITECTURE 17.8) |
| `config.json` saved with a BOM silently lost the token | `json.loads` on `utf-8` fails on the mark; `load()` returned defaults | Every JSON reader uses `utf-8-sig` (ARCHITECTURE 19.3) |
| The production data gate always passed | PowerShell function output joins its return value | `\| Out-Host`; proven with a corrupted file (ARCHITECTURE 18.9) |
| A crash would have ended production until the next reboot | "Restart on failure" only acts on a failed *start* | Task trigger every 5 min + ignore new; `HOLD` file for updates (ARCHITECTURE 18.7) |

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
sample values of `.env.example`, which `install.bat` copies to create `.env`.
The development PC's `.env`, not versioned, had the right IPs. With no
timeout, ffmpeg waits for the TCP connection forever and **writes nothing**.
The only line, even at `-loglevel verbose`, was `Starting connection attempt
to 192.168.0.10 port 554`.

**How it was found, in order:**

1. `tools/diagnose.py --local` read 7776000 of 7776000 bytes: decoding,
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

**Fix:** `-timeout` on RTSP (ARCHITECTURE 5.7). A wrong IP now shows in ~6 s as
a timeout telling you to check the network and the camera's IP.

**Still the user's:** reserve `.116` and `.42` by MAC on the M900's router.

## 8. Backlog items as they were decided

The full text of finished items, as each was decided and delivered. The
backlog itself is `BACKLOG.md` 1.

40. **Done 16/10 (`136e9b0`, `dcbdeb4`, `217b61d`, `dc86e89`, `v2026.10.16`; ARCHITECTURE 12.11, 12.12), except its "later, with tracking" part, which is backlog 7's.** **Notifications by incident** (decided 16/10: the user's principles,
    CONTEXT 3; which situations are risk was left to the architect, and the
    design is the architect's). Measured on production's log the same day:
    in Home, 33 messages in 24 hours, only 2 within 30 s of the one before
    — there the volume is the false ones (R59, R58) and residents with no
    face seen; before the modes, every case on as in Away, 91 of 389
    messages came within 30 s of the one before, 80 on one camera, mostly
    an event's immediate "person" and its follow-up. And today's intervals
    drop what they block (R60). Competitors drop or snooze (Frigate's
    cooldowns, Ring's Motion Frequency, Eufy's snooze); none merges. The
    design:
    - **An incident**, one for the house, opens with the first message
      sent while none is open and closes when no message was sent for
      `notify_cooldown` seconds — the page's field, 120 in production,
      whose meaning changes from "per camera, dropped" to "the incident's
      quiet window"; the key stays, so `config.json` does not change.
    - **Nothing is dropped.** Every message the mode wants goes out, **loud**
      or **silent** (Telegram's `disable_notification`: it arrives with no
      sound). Silent, not one message edited, so each photo stays on
      Telegram's servers — evidence off the M900 if it is stolen or broken
      in a break-in.
    - **Loud:** the incident's first message; a message from a camera other
      than the incident's last one (the user: "every time you see him in a
      different place it is worth a new notification"); more people at once
      than the incident had; a camera that stops delivering pictures, and
      its return.
    - **Silent:** everything else inside the incident — the next clips in
      the same place, the face or best view that follows a message.
    - **The floor, the user's number:** at most one loud message in 30 s
      across the house. A loud one that falls inside goes out silent at
      once, and at the 30 s mark one loud text says what came; several
      merge into that one.
    - **A camera with no picture** (backlog 2's first part, now decided
      here): no frame for a minute is a loud message, "Back: no picture
      since 16:32:10", and its return another, with how long it was out — a
      case of its own, on in Away and Home, off in Silent. Always a log
      line, which the outage of 14/10 did not leave. A black or covered
      picture waits for a measurement on night frames.
    - **Later, with tracking (item 7):** a person nobody accounts for still
      there after some minutes, once (loitering, as Frigate's zones and
      UniFi Protect's alarms have); and "the same place" becoming "the same
      body", so a new person on the same camera rings again.

32. **Done 15/10 (faces `9fc5592`, `v2026.10.14.3`; dogs `bc94747`, `v2026.10.15.2`; both by leave-one-event-out, R55 `cde3087`; ARCHITECTURE 10.15, 20).** **The "maybe" threshold, chosen from measured accuracy** (decided; the user: with a metric they set the threshold, without one the maybe stays as it is). Settings shows, for faces and for dogs, a table measured on the user's own named photos by leave-one-out — each named view matched against all the others: per threshold, how many named views would be recognised for sure and what share to the right one, and how many unnamed photos would cross it. The user sets the sure threshold from it (faces `LEARN_THRESHOLD` 0.45; dogs the sure distance 0.35 and ratio 0.6), stored in `config.json`. Measured 13/10: faces are 99.3 % right at any threshold from 0.363 to 0.45 (1 error in 146 views) — **wrong, review 20**: 7 of Gustavo's views are Izabel's faces, counted as right by their label; at 0.45 at least 8 of 146 are wrong, and the table means something only on clean labels, with each view's exact copies left out of its own test; and review 21 found that those wrong views are not faces at all, but the top of a head (R49). **Since `v2026.10.14` the model is ArcFace** (thresholds 0.30 / 0.40): the table is computed on it, and means something once the labels are clean — the twelve head-tops deleted and the seven unnamed entries of Izabel named (`PENDING.md`). Even so, 12 unnamed face views fall between 0.363 and 0.45; dogs at today's thresholds are right in 31 of 33 probable matches, the 2 wrong ones at night. **What it cannot measure:** a stranger has no name, so the table shows confusion between the named, not with strangers — the unnamed column is the only hint, and the page says so. A lower sure threshold also means more views learned on their own (28). **The faces' half is done** (`9fc5592`, `v2026.10.14.3`, ARCHITECTURE 10.15): production's table has no wrong answer from 0.30 to 0.60, which is optimistic until R55 leaves each view's whole event out. **The dogs' half** is planned (section 3): on DINOv2-small's distances (R53, `v2026.10.15`), born with R55's leave-one-event-out. **The user sets the sure distance only; the ratio to the second dog stays `SURE_RATIO` 0.6** (decided, UX, review 26): the bench showed the ratio is what keeps two-dog crops out of the sure answers (3 + 1 instead of 7 + 1 at 0.33, ARCHITECTURE 20) — a safety rule, not a preference — and one number to set reads better than a grid of two. **Built:** the faces' half in developer session 23; the dogs' in developer session 25, with R55: on production's copy of 15/10 the faces are named for sure 39 times in 80 at 0.40 by another visit (66 before R55), the dogs 44 of 56 by day and 9 of 24 at night at 0.33, every answer right at every row of both tables.

39. **Done 15/10 (`a9b8c32`, `v2026.10.15`, ARCHITECTURE 17.17).** **On a phone, an unnamed card is its photo and its name** (decided, UX, review 25). At 375 px an unnamed card was 309 px tall, and 137 px of it were the name, a name form and "Bad detection" — while tapping the photo already selects it, and the selection bar at the bottom names, assigns or reports one photo or many. Under 480 px: (a) unnamed cards on People and Dogs drop their own name form, their "Belongs to…" and their "Bad detection" — CSS only, the desktop keeps them; the hint above the unnamed list says "Tap photos to select them, then name or report them below" on a phone; (b) the accuracy table of Settings → Detection is hidden while nothing is measured, leaving its one sentence, on every width. Built in developer session 24: the Dogs tab at 375 px with production's 46 dogs 8,768 → 6,018 px, an unnamed card 349.5 → 231.5 px, two taps to name or report one photo.

38. **Done 14/10 (`03cde0e`, `v2026.10.14.3`, ARCHITECTURE 7.14).** **The default marked on each slider** (decided, UX, review 24). Backlog 35's sliders showed no mark where the default sits, so a slider moved and moved back could not be put on the default by eye. A `<datalist>` with one option at `slider_steps / 2`, named by each slider's `list` attribute, makes the browser draw a tick there; nothing else changes. Built in developer session 23; seen at 375 px with the thumb moved away.

37. **(a) and (b) done 14/10 (`b8a731b`, `v2026.10.14.3`, ARCHITECTURE 17.17).** **People and Dogs hold many photos gracefully** (decided, UX; the user, 14/10/2026: some households will never open the page, so the screens must cope with a great many photos, "and perhaps clean themselves now and then"). Designed in review 24 from production's counts on 14/10 (13.25): a person's Chosen (40) and Waiting (`MAX_PENDING` 100) are bounded by backlog 28, unnamed dogs by R27 (`MAX_UNNAMED` 60, 44 that day, about 7 new a day), **unnamed faces by nothing**; the sighting photos grow about 2.7 MB a day for faces and dogs together, next to ~300 MB of clips. The Dogs tab at 375 px was one column of 335 px cards, 46 of them about 9,100 px tall. The layout: (a) every `.people-grid` takes two columns under 480 px; (b) any list of photos that can pass 24 shows the newest 24 and a "Show 24 more (N left)" button — the unnamed groups, a person's or dog's Waiting, "Days they were seen" — while Chosen shows whole, headings keep the full count, the server keeps sending whole lists; (c) checked at 375 px and on the desktop with production's 46 dogs. Built in developer session 23, with Waiting shown newest first. Measured: 9,163 → 8,591 px; review 25 found the card's height, not the columns, makes the page long — backlog 39. **The self-cleaning part** deletes the user's data: the user's decision on the policy in `PENDING.md`.

36. **Done 14/10 (`6295d57`, `v2026.10.14.2`, ARCHITECTURE 22.4).** **Notifications: the Telegram card beside "What reaches the phone"** (decided by the user 14/10/2026). Two columns where the screen is wide enough, one under the other on a phone — the user opens the page from the phone's browser too (PROCESS 1, UX). Built in developer session 22 with CSS only: a 3fr / `minmax(300px, 2fr)` grid, one column under 860 px.

35. **Done 14/10 (`87a84fd`, `v2026.10.14.2`, ARCHITECTURE 7.14).** **Detection sensitivity as a slider, not numbers** (decided by the user 14/10/2026: "the sensitivity cannot be numeric — a kind of slider where the middle is our default value, and the number goes down to the left and up to the right, proportionally"). Each of backlog 31's three minimums became a slider with no number on it: the middle is the default, the left end the lowest allowed minimum (0.20), the right end the highest (0.90), each half linear, so the middle is always the default whatever its value. The ends say in words what they do — left: more detections, more false alarms; right: fewer, stricter. `config.json` keeps storing the number, so nothing on disk changed. **The explanation stays, moved to where it belongs** (the user, the same day: "the explanation on the numbers screen was perfect; I want to know how the sliders work in the background"): what the minimum is, lower finds more and more false ones, a change reaches the cameras within seconds without a restart, what this does not fix (a person bending over), and a "how it works" part — the minimum confidence underneath, the middle being the default, the ends 0.20 and 0.90, each half in proportion, each slider's current value and default in that text, not on the control. Built in developer session 22: the mapping in `settings.py` with `SLIDER_STEPS` = 1000, tested both ways.

34. **Done 14/10 (`8828e5c`, `v2026.10.14.2`, ARCHITECTURE 22.7).** **Analysis On and Off from the page** (decided by the user 14/10/2026, during review 23: "on the screen where the status shows, it must be possible to switch it on and off there too"). The header that shows On or Off on every screen became a switch calling `analysis.set_on` as `/on` and `/off` do — same flag, same reminder while Off, still never stored — through the write guard like every other change. **Turning Off asks first**, since it stops all recording; **turning On is one click** (the user, 14/10/2026). Built in developer session 22: `POST /api/analysis`, `confirm()` before Off, tests in `tests/test_on_off.py`.

30. **Done 13/10 (`v2026.10.13`, ARCHITECTURE 22.2).** **Home silences a probable resident** (decided by the user 13/10/2026: "I have not seen a wrong maybe"). Two new cases, `probable_resident_person` (a face matched as probable to a Resident) and `probable_resident_dog`, which until then fell under `known_person` and `other_dog`; defaults on in Away, off in Home and Silent. It changes ARCHITECTURE 22.2's default, not its rule: the switch undoes it with one tap. Additive in `config.json` (`modes.normalised` fills the new cases). Measured 13/10: 72 of 134 named face sightings were probable (the user 25, Izabel 47). Built in developer session 17 (`cfa286a`): `notify.person_case` and `dogs.identify` say how sure a resident is; tests in `tests/test_probable_resident.py`.

29. **Done 13/10 (`v2026.10.13`, ARCHITECTURE 22.7).** **On and Off from the bot** (decided by the user 13/10/2026). `/off`: J.A.R.V.I.S. stops processing images — no motion, no YOLO, no events, no recordings, no face scan, no messages — while capture keeps running, so Live and every other screen work normally. `/on` resumes. **It always starts On**: Off is not stored, so a restart, a crash or the 5-minute task bring it back On — Off is an occasional state. Every screen of the page shows On or Off; `/mode` and the command list show it too; while Off, the bot sends a reminder every 3 hours. Obeyed only from `notify_chat`, like the other commands. An event open at `/off` ends as if the motion had stopped. Built in developer session 17 (`589cc13`): `analysis.py`, `Core._switch_analysis`, the poller's `_remind`; tests in `tests/test_on_off.py`. The event open at `/off` finishes its pipeline — clip, face scan, follow-ups — as any event that ends because motion stopped.

26. **Done 12/10 (`v2026.10.12.2`, ARCHITECTURE 17.16).** **Select many unnamed crops and name them at once** (decided by the user 12/10/2026: in Unnamed dogs, select several photos and assign them to an animal, instead of "Belongs to…" one by one; the design is the architect's, as the user asked).
    - **(a) A grid with selection, not a table.** The user tells the dogs apart by the photo, so the photos stay large; a table would shrink them to row icons. The photo-app pattern: tap a photo to select it (a check mark and a frame), shift-click selects a range on a computer, Clear. Works by touch on a phone.
    - **(b) Grouped by the system's guess.** The unnamed crops are shown in groups by what the matcher thinks now — "Looks like Aurora (12)", "Looks like Mirana (8)", "No guess (5)" — from the same `dogs.match` the messages use (sure or probable), newest first inside each group, each group with "Select all". Usually most of a group is the right dog: select it, untick the wrong ones, assign. A hint, never an automatic name.
    - **(c) One action bar**, fixed at the bottom while anything is selected: "N selected · Assign to [named dog ▾] · or a new name · Bad detection · Clear". Assigning asks once ("Join 7 photos to Aurora? A merge cannot be undone"), as every merge does.
    - **(d) One request, one lock.** `POST /api/dogs/assign` with `{"ids": [...], "to": "<id>"}` or `{"ids": [...], "name": "..."}` merges every entry under one gallery lock and one save, gathers look-alikes once (R29), and answers how many joined and which ids were gone (merged or reported meanwhile: skipped, not an error). `POST /api/dogs/report` with ids writes one report per entry (backlog 23 unchanged). Unnamed entries are addressed by id, which is stable, so R41's problem does not arise. Through the write guard like every POST.
    - **(e) The same on People's Unnamed faces**, since both tabs are one component (`galleryTab`); "Belongs to…" stays on each card for a single one.
    - Data: nothing new. **Acceptance:** tests — three ids assigned to a named dog (views, sightings and favourite follow), one id already gone is skipped and named in the answer, a new name creates the entry, the batch report writes one report per entry; checked in the built-in browser at desktop width and at 375 px.

27. **Done 12/10 (`v2026.10.12.2`, ARCHITECTURE 22.4).** **Notifications as a part of Settings** (decided by the user 12/10/2026: a Notifications tab is not ideal; make it a subsection of Settings). Settings gets a sub-navigation at its top — **Notifications · Other devices · Archive · Bad-detection reports** — with Notifications first, each part reachable as `#settings/<part>` so a link and the back button land on it. The tab bar loses Notifications; an old `#notifications` link opens `#settings/notifications`. Texts that say "the Notifications tab" say "Settings → Notifications". No server change. **Acceptance:** checked in the built-in browser at desktop width and at 375 px.

25. **Done 12/10 (`v2026.10.12`, ARCHITECTURE 22); the acceptance on the M900 waits for the user** (mark the residents, then Home). **Residents, notification rules and modes** (decided by the user 12/10/2026, one developer delivery). The user, Mirana and Aurora live here; being told hundreds of times that they walk around the house is noise. Today (10/10 01:16 → 12/10, 143 messages) 73 were "person" at the start of an event, 34 named a face — **21 of them the user** — 10 a side view, 26 a best view; dogs do not notify at all (`notify_labels` is `["person"]`).
    - **(a) The Resident tag.** A switch **Resident** on the person and dog pages, named entries only; stored as an optional `"resident": true` in `gallery.json` (additive). Renaming keeps it; a merge keeps the target's, or sets it when either was a resident. The grid card shows it.
    - **(b) The cases, one switch each:** resident person recognised · other known person, or any "probably …" match · unknown face · person with no recognisable face (the side-view and best-view messages) · resident dog · other dog (probable, another name, unidentified) · other animals. Only a **sure** match counts as a resident — a "probably Gustavo" or "probably Aurora" is not silenced, so a weak match of a stranger is never hidden.
    - **(c) Modes:** **Home**, **Away**, **Silent**; one is active; each has its own switches, all editable. Defaults: Away — every person case on; Home — the two resident cases off, the rest as Away (a person with no recognisable face **notifies**: the user's choice, a stranger in the dark must reach the phone); Silent — all off. Animal switches start from today's `notify_labels`, so nothing new arrives until the user turns it on. **Recording never changes**: a mode only decides what reaches the phone. Stored as new optional keys in `config.json` (`notify_mode`, `notify_modes`); `notify_labels` stays for older versions.
    - **(d) The timing problem, and its rule.** A dog is named from the first frame (~100 ms), so a resident dog is silenced in the first message itself. A person is named only after the clip is assembled and scanned (section 3, "Rosto no clipe"). So: **when the active mode has any person case off, the person message waits for the face scan** and goes out once, saying who was found, or with the side or best view; when every person case is on (Away), today's immediate message and follow-ups stay. The camera and per-person cooldowns keep working. A mid-event arrival (`_notify_late`) follows the same rules.
    - **(e) A Notifications tab.** The switches as a table — cases in rows, the three modes in columns, the active mode chosen at the top — drawn as real on/off switches (`<input type="checkbox" role="switch">` and CSS, no library), fitting a phone. The Telegram setup (token, chat, find chat, test, prefix, cooldown) moves there from Settings.
    - **(f) Commands from the phone.** A thread in production asks Telegram for new messages (`getUpdates` long polling: an outgoing connection like sending, **no port opened**). Only the configured chat is obeyed; anything from another chat is ignored and logged. `/home`, `/away`, `/silent` switch the mode and answer with what it means; `/mode` shows the current one with tap buttons (inline keyboard); `setMyCommands` lists them in Telegram's "/" menu. The bot can change the mode and nothing else. Find chat must read through the same poller (two readers steal each other's updates); only production polls — the test copy has no token (checked 12/10), and a second poller on the same token gets a 409 from Telegram: log once and back off. Network failures never touch capture; R16's token redaction applies.
    - **Acceptance:** tests for the rules matrix (each case × mode), the held person message with a fake scan, the resident flag through rename and merge, the defaults built from an older `config.json`, the poller ignoring other chats; `check_data` reads the new keys. On the M900: the user, Mirana and Aurora marked Resident; in Home a recognised resident sends nothing and a person with no face does; `/away` from the phone changes the mode the page shows.

23. **Done 11/10 (`v2026.10.11.4`).** **Report a bad detection instead of deleting it** (decided 11/10/2026). Some unnamed crops are not even a dog, or not a face. Each unnamed face and dog crop (and a person or animal label on a Recordings event) gets **"Bad detection"**: the crop leaves the gallery and the tabs, and is kept as an example in a new folder `reports/<kind>/` — the crop plus a JSON with camera, time, clip, label, score, box and what the user said (`not a dog`, `not a face`, `not a person`). Nothing is learned from it automatically yet; it is the improvement process's evidence: `tools/replay.py` and the tuning tools can be pointed at it, and each review reads the new reports (a rule like R18 or R35 is then measured against what the user flagged). Replaces the plain Dismiss of R27, which deleted without a trace. Additive: new files only; `check_data` reads them. **Since `v2026.10.11.6` (R38, R37):** Settings lists the reports; each can be undone — the entry returns to its gallery with its photos and sightings, or the label to its recording — and can say what it actually was (person, dog, other animal, nothing).

24. **Done 11/10 (`v2026.10.11.4`).** **"Choose the best 40" for a person or a dog** (decided 11/10/2026). When a person or dog holds more than 40 views (the 40 kept plus the queue), their page gets an **Analyse** button: the software picks the 40 **most different** views — greedy farthest-point selection over the embeddings (cosine for faces, the Bhattacharyya distance for dogs, keeping day and night both represented), which covers angles and lighting instead of 40 near-copies — shows the proposal, and on confirmation keeps those 40 and moves the rest to the queue. Manual removal stays as it is. Tests: the selection spreads (minimum pairwise distance grows), nothing is lost (views + queue unchanged as a set). **Since `v2026.10.11.6` (R40):** the queue is shown as **Waiting** beside **Chosen**, views move between them by the user's hand only (removing a chosen view no longer pulls a waiting one), and the proposal can also discard the views it does not keep.

22. **Done in code 10/10 (`v2026.10.10.7`, ARCHITECTURE 20); the thresholds wait for the user's names.** **11/10, first names:** Aurora 5 views (3 day, 2 infrared), Mirana 3 (day only) — checked on a sheet, all correct. `dog_tuning.py` on them: day 2 right-sure, 1 right-probable, 1 wrong-probable, 2 no name; infrared not measurable (Mirana has no infrared view). Too few to tune: about 10 per dog **per lighting** are needed. **A Dogs tab: each household teaches the system its own dogs** (decided 10/10/2026). The user confirmed the two-dog measurement (item 15) — the dark group is Mirana, the light one Aurora — and set the rule: **nothing about their dogs goes into the code.** The software is not only for this house; anyone must be able to teach it their own animals. So it mirrors People: (a) every dog detection keeps a crop cut out of its box (GrabCut) and an **appearance descriptor** computed from the fur pixels only — a normalised tone histogram, plus hue and saturation when the frame is in colour; (b) a **Dogs** tab next to People: a grid of named dogs, the unnamed crops with a name field and "Belongs to…", and a dog page with its views, favourite photo and calendar — the same screens and rules as items 19 and 21; (c) a dog gallery in its own folder, `dogs/` (`gallery.json` + `views/`), new files only, read by `check_data`; (d) matching by nearest neighbour against each named dog's views, **day views compared with day views and infrared with infrared**, and a name given only when the nearest dog is clearly closer than the second and within a distance limit — otherwise just "dog"; (e) the event's `animals` list, the Recordings card and the Telegram text use the names. **Notification rule (the user, 10/10):** the alert is about *a dog being there*, not about knowing which — so whenever a dog is detected and `dog` is among the alert labels, notify, and word it by certainty, the same three levels as faces (12.8): a clear match → the dog's name; a weak one → "probably <name>"; none → "unidentified dog". The thresholds start conservative and are tuned as the named views grow; if the patterns never firm up, the feature still works as "a dog was there", which is what exists today. Dogs that look alike stay "dog", which is the honest answer. Acceptance on this house's data: after the user names a few crops of each, production's past dog events are named correctly in most clear cases and at night, with no colour rule anywhere in the code. Supersedes item 15's model research.

21. **Done 10/10 (`v2026.10.10.6`).** **A favourite photo per person** (decided 10/10/2026). On the person's page the user picks which of the stored views is the photo shown on the People grid. Additive: an optional `cover` per person in `gallery.json`, the portable path of the chosen view's crop; the grid uses it when set and the file exists, otherwise today's `thumbnail`. When the favourite view is removed (`remove_view`) or merged away, `cover` falls back to the first view that has a photo. The write goes through the R24 guard; `check_data` and `tests/test_gallery.py` cover the new key.

19. **Done 10/10 (`v2026.10.10.4`, ARCHITECTURE 17.10).** **People by person, not by day; attach a face to an existing name** (decided 10/10/2026, redesigned by the user the same day). The People tab today lists sightings by day. The user wants instead: **(a)** one screen with every **named** person (they fit on one screen), and a separate place for the unnamed faces; **(b)** clicking a person opens their page: first **the stored views that recognise them** (up to `MAX_EMBEDDINGS` = 40), then **a calendar of every recording they appear in**; **(c)** on an unnamed face, a "belongs to…" picker of existing names instead of typing — the merge itself already exists (`Gallery.rename` → `_merge`); **(d)** when a person already holds 40 views, new ones **wait in a queue** instead of being dropped (today `_merge` and `reinforce` drop them); on the person's page the user can **remove** one of the 40, and the oldest waiting view takes its place. This replaces the architect's earlier idea of replacing the most redundant view automatically: the user wants the choice. **Data, additive only:** a view today is a bare embedding with no picture, so to show the 40 the gallery must start keeping each view's face crop — an optional list aligned with `embeddings` (`null` for the views stored before, shown as "no photo"), plus an optional `pending` queue; `check_data` must read old and new. **(e) Rename a person** from their page (added by the user, 10/10). `Gallery.rename` already does it, but a new name that belongs to someone else **merges the two** — the page must say so and ask before doing it. **Fresh start (decided by the user, 10/10):** production's gallery holds only two named people and views without pictures, so when this version is deployed the architect **deletes** production's `faces/` — the user chose no backup — and the gallery restarts empty; the user names the two people again, and every view from then on has its picture. Clearing it before the deploy would be pointless: the running version would keep storing views without pictures until then. **Animals:** the user wants the same for the dogs; that needs item 15 first.

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
   ARCHITECTURE 17.

   **The user's decision, 09/10/2026: the web is the only way in**, with one
   service running — *"I don't want two ways of getting in"*. It replaced the
   plan of keeping the window alongside to compare. Order:

   | | Step | State |
   |---|---|---|
   | ✓ | Stage 1 — the event list | done 09/10 (ARCHITECTURE 17.6) |
   | ✓ | Stage 3 — live, local network, the shortcut opens service + browser | done 09/10 (ARCHITECTURE 17.7) |
   | ✓ | Stage 4 — People and Settings on the web | done 10/10 (ARCHITECTURE 17.9) |
   | ✓ | Start with Windows, no console | done by item 17 (production task), 09/10 |
   | ✓ | Remove the OpenCV window (`ui.py`, `--window`) | done 10/10 (ARCHITECTURE 17.10) |
   | ✓ | Stage 2 — play the video on the page | done 11/10 (item 5) |

15. **Re-ID de animais** — **superseded by item 22** (the user's two-dog idea, generalised). History: **researched 10/10/2026, parked: no solution good enough for its cost now** (the user accepted that outcome in advance). *Measured:* the cheapest idea, telling the dogs apart by fur tone (works day and night in principle, since IR keeps white bright and black dark), failed on production's data: 168 dog detections in 89 events give a continuous spread of median tones from 7 to 249, with no clusters — a box holds the mat, the floor, sun and shade as much as the dog. *Read:* the models made for it are MegaDescriptor (WildlifeDatasets; Swin and EfficientNet variants on Hugging Face, best published for animals) and frozen DINOv2 with nearest-neighbour matching (weaker; a community dog model reports about 0.54 top-1 on whole-body dogs). Neither ships as ONNX: export needs PyTorch on the development PC, the run would be `onnxruntime` or a newer `cv2.dnn`, at an unmeasured CPU cost per crop on the M900. *What it would take:* a dog gallery the user labels by hand, a new model, and two or three sessions; expected to work on clear daytime views and poorly at night or with the dog lying down. Revisit only if knowing *which* dog becomes worth that. Today every event already says *that* a dog was there (item 20). **Reopened the same day with the user's idea — and it works on the data.** The house has two dogs, so the question is not *which dog in the world* but *which of the two*: keep the existing YOLO dog detection and tell the two apart with plain computer vision. Measured on production's clips: cutting the dog out of its box with OpenCV's GrabCut first, then taking the median tone of the fur pixels, splits 89 detections in 54 events into **a dark group (0–42, 42 detections) and a light group (150–210, 31)**, with 16 in between; **at night the split is clean** (2 dark, 14 light, none in between), since infrared keeps white fur bright and dark fur dark. A contact sheet of each group was sent to the user to confirm which dog is which. Proposed rule: tone below ~60 → the dark dog, above ~140 → the light one, in between → just "dog"; GrabCut on a handful of crops per event in the post-event scan costs little. Waits for the user: the two names and the confirmation of the sheet; then it is a small developer session (`people.py` or `faces.py`, the event's `animals` list, tests). A visiting dog would be named as one of the two — accepted by the user ("the only two dogs at home, most of the time"). The original item was a
    whole-body classifier (ARCHITECTURE 10.8).

## 12.2 A precondition checked on 09/10/2026

Web interface (backlog 3, ARCHITECTURE 17) depended on `pydantic_core`, compiled
Rust — the same kind of binary Smart App Control blocked in PyTorch:

```bash
uv run python -c "import pydantic_core, fastapi, uvicorn; print('ok')"
```

| Machine | Does `pydantic_core` load? |
|---|---|
| Dev (Windows) | yes, tested 09/10/2026 |
| M900 (deploy) | yes, tested 09/10/2026 — `pydantic_core` 2.50.0, after switching to the signed Python |

Had it failed, plan B was Flask with a threaded WSGI server, pure Python
(ARCHITECTURE 17.2).

## 13. Architecture review

### 13.2 Review log

| # | Date | Range reviewed | Result |
|---|---|---|---|
| 1 | 09/10/2026 | `b3d9c94..456b613` — signed Python, web stages 1 and 3, the face in the notification | 2 documentation errors fixed; R1–R9 opened. During the review the user decided R4 (keep LAN access) and the language rule (R10), and asked for production and test environments (backlog 17, ARCHITECTURE 18) |
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
| 16 | 12/10/2026 | `v2026.10.12..a53aa84`, developer session 14 — R44, backlog 26 and 27, R43 | no release code fixed; `.gitignore` now covers R43's temporary file; R44 replayed on six dog-alone clips (no box relabelled); 174 tests pass; R45 opened (low); release `v2026.10.12.2` (13.17) |
| 17 | 12/10/2026 | `v2026.10.12.2..f4489a0`, developer session 15 — R10's file names and the tools' text, R45 | no code fixed; 176 tests pass; the new `check_doc_refs.py` exits 0 after rewording three historical lines; `.gitignore`'s last Portuguese comments translated; R10 and R45 closed; release `v2026.10.12.3`, deployed at 21:20: 477 events, 55 face and 205 dog sightings, 6 reports read before and after; cameras ok 3 s after the start (13.18) |
| 18 | 12/10/2026 | `v2026.10.12.3..9866a9b`, developer session 16 — the `jarvis_vigilancia.bat` shim removed, R7 | no code fixed, one message added: `install.bat`'s `uv sync` failure now points at INSTALL 1.2; the signature check run against production's own `.venv` in `production.ps1`'s call pattern; 176 tests pass; R7 closed, nothing opened; release `v2026.10.12.4`, deployed at 21:36: 478 events, 55 face and 206 dog sightings, 6 reports read before and after; `Sync`'s new check passed on `pythonw.exe`; about 9 s stopped, cameras ok 3 s after the start (13.19) |
| 19 | 13/10/2026 | `v2026.10.12.4..594fbc6`, developer session 17 — R46, backlog 30 and 29 | no code fixed; R46 replayed on `15-00-17` (no dog left) and on two true dogs with a person (nothing relabelled); 208 tests pass, `check_data` reads every file; R46 closed, R47 opened (low, a watch); release `v2026.10.13`, deployed at 22:22: 913 events, 200 face and 363 dog sightings, 18 reports read before and after; about 10 s stopped, cameras ok 3 s after the start, `/api/status` says `"analysis": "On"` (13.20) |
| 20 | 13–14/10/2026 | `v2026.10.13..212179e`, developer session 18 — backlog 28 | no code fixed: the rule does what item 28 says; 216 tests pass, `check_data` reads every file. **Not released**: on a copy of production's galleries the rule would have put 6 of Izabel's faces, misfiled in Gustavo's Waiting by wrong "sure" matches, into his Chosen; the once-only tool was not run and R48 waits for the user (13.21) |
| 21 | 14/10/2026 | `0f68445..865eb7f`, developer session 19 — backlog 31 | no code fixed; 234 tests pass, `check_data` reads every file; at the defaults the detector decides as before on R46's three clips, replayed old against new. **Not released**: 31 waits on `master` with 28. The user's objection to R48 led to its cause: the seven wrong views and five of Gustavo's references are the top of a head, not a face — R49 (13.22) |
| 22 | 14/10/2026 | `865eb7f..706883b`, developer session 20 — R49 step 1, `tools/face_bench.py` | no code fixed; 234 tests pass; the SCRFD decoding and every model's preprocessing checked against their authors', the baseline reproduced, the alignment measured (OpenCV's `alignCrop` is the least-squares fit, LMEDS is not); the unnamed entries checked as a possible third person — the user: all are Izabel, and InsightFace if it is the best; no release; developer 21 planned with R49 step 2 (13.23) |
| 23 | 14/10/2026 | `706883b..70d3fce`, developer session 21 — R49 step 2: SCRFD + ArcFace R50, the migrated gallery, models before the stop | **one code fix** (`d07c09e`): `FetchModels` aborted on a tag without `downloads.py` instead of skipping it; 240 tests pass; the scan and the stored photos embed alike (0.97–0.99); R48 and R49 closed, R51 and R52 opened; **release `v2026.10.14`** (R49, backlog 28 and 31), deployed at 12:07: 955 events, 202 face and 393 dog sightings, 18 reports read before and after; the models fetched before the stop; 173 of 173 views migrated in about 23 s; about 36 s stopped, cameras ok 3 s after the start; the migration's line is not in the log (R52). The once-only settle waits for the user (13.24) |
| 24 | 14/10/2026 | `70d3fce..099d547`, developer session 22 — backlog 34, 35, 36, R52, R51, R30 (b) | no code fixed; 269 tests pass, `check_data` reads every file, no comments; the page checked at 375 px and 1280 px (Off asks, On does not; no horizontal scroll); the slider's round trip checked for six defaults; `filelock` has no binary; R30, R51 and R52 closed, R54 opened (a watch: no stranger measured); backlog 37 designed from production's counts, 38 added; **release `v2026.10.14.2`**, deployed at 15:50: 976 events, 206 face and 412 dog sightings, 18 reports read before and after; `filelock` installed by `uv sync`; no migration ran (the hash unchanged), no lock file left; about 10 s stopped, cameras ok 3 s after the start (13.25) |
| 25 | 14/10/2026 | `18b268c..72e9527`, developer session 23 — R42 (b), backlog 37 (a, b) and 38, R53 step 1, backlog 32 for faces | no code fixed; 284 tests pass, `check_data` reads every file, no comments; the page checked at 375 px and 1024 px (two columns, the selection bar, the accuracy table 301 px of 301, no horizontal scroll); R53's bench run again for DINOv2 and MobileNet on the M900, same numbers; R42 closed; R53 step 2 decided: DINOv2-small; R55, R56 and R57 opened; backlog 39 (decided, UX) added; **release `v2026.10.14.3` tagged, its deploy rolled back on its own**: both cameras left the network between 16:32 and 16:39 — a power cut, the user said the next day — nothing to do with the release; the M900 lost power at 17:13, booted at 21:47 and was put to sleep by Windows 50 s later, asleep until 15:58 on 15/10; **deployed on 15/10 at 16:05**: 977 events, 206 face and 413 dog sightings, 18 reports read before and after; about 10 s stopped, cameras ok 3 s after the start (13.26) |
| 26 | 15/10/2026 | `bd44c66..756ac12`, developer session 24 — R53 step 2, backlog 39, R56, R57 | no code fixed, one installer message corrected (the models' size); 296 tests pass, `check_data` reads both dog galleries, no comments; the model's pinned SHA-256 checked against Hugging Face's record; two of production's dog reports undone on a scratch copy (both back with 385-number descriptors); the page at 375 px and 1024 px; the live-loop cost found higher than the histograms', not lower, and the documentation corrected; R53, R56 and R57 closed, nothing opened; **release `v2026.10.15`**, deployed at 16:53: 979 events, 206 face and 413 dog sightings, 18 reports read before and after; the model fetched before the stop; 205 of 205 dog views migrated in 21.7 s; about 35 s stopped, cameras ok 3 s after the start; the 44 unnamed dogs' guesses all right on a contact sheet (13.27) |
| 27 | 15/10/2026 | `8ba7da3..e700b05`, developer session 25 — R55, backlog 32 for dogs | no code fixed; 313 tests pass, `check_data` reads every file, no comments, `check_doc_refs` 0; the event recovery run again on the review's own copy of production's galleries (times kept): the same 81 + 57 face views and 205 dog views, none unknown, and the same face table; overlapping events of one camera measured (3 of 39 sure views at 0.40, no wrong answer, no dog pair): the event stays the unit; the dog panel at 375 px and 1024 px with production's table; R55 closed, backlog 32 done for both halves, nothing opened; **release `v2026.10.15.2`**, deployed at 17:27: 979 events, 206 face and 413 dog sightings, 18 reports read before and after; about 11 s stopped, cameras ok 3 s after the start; the first start recovered 81 + 57 face and 205 dog events, none unknown, and the live tables matched the copy's (13.28) |
| 28 | 16/10/2026 | `a672890..655faa6`, developer session 26 — R59 and R58 measured | no code fixed, no program code changed, no release; `person_signals.py` read (it only reads); the four two-person events in production's JSON checked, none two people; ARCHITECTURE 22.3 corrected (nested boxes survive NMS and `drop_duplicates`); R59 and R58 wait for tracking; R60 opened (the cooldowns drop what they block); backlog 7 (tracking) and 40 (notifications by incident) decided by the user the same day (13.29) |
| 29 | 16/10/2026 | `0cf58f9..7670811`, developer session 27 — R60, backlog 40: notifications by incident, a camera with no picture | no code fixed; 328 tests pass, `check_data` reads every file, no comments, `check_doc_refs` 0; the replay run again on production's log (741 messages, 220 loud and 17 floor texts at 120 s); no send ever failed there and at most 9 messages fall in a minute; the page checked at 375 px and about 1000 px; tracking's library probed on the M900 for the plan (Roboflow's `trackers` imports under Smart App Control); R60 closed, R61 opened (low); **release `v2026.10.16`** (13.30) |
| 30 | 16/10/2026 | `0d4eeab..dccf519`, developer session 28 — R61, `trackers` and the deploy's warm-up, tracks measured (item 7 part 1) | no code fixed; 338 tests pass, no comments, `check_doc_refs` 0; every release tag holds `.python-version`, the warm-up's imports run locally (55 modules, none failing); the library's first box with −1 read in its source; the HANDOFF's hardlink explanation corrected — the project copies (ARCHITECTURE 18.7); R61 closed; **release `v2026.10.16.2`** (13.31) |

### 13.3 Review 1 — what was fixed on the spot

- **The wrong story of the Python block** (INSTALL 1.2, sections 3 and 4 of
  CONTEXT). It said a `uv sync` had switched Python to 3.14.7 and that
  Windows had already blocked it on 29/09. Both are false: 3.14.7 was
  downloaded on 29/09 and ran until 30/09 — Windows' verdict changed on the
  **same file** —, and the blocks of 29/09 in the event log were PyTorch DLLs
  loaded by Python. The mistake came from filtering the log by the word
  "python" without reading the whole message.
- **"The `Core` does not change"** (ARCHITECTURE 17.4) no longer held after
  stage 3, which added `labels` and `live_view()`. Rewritten to what matters:
  the `Core` does not know about the web.
- **`jarvis_headless.bat`** still told the user to use `jarvis.bat` to see
  the cameras.

A fact raised in the review: **the M900's last recording was from 30/09 at
22:54.** The system went nine days without running; the Python block only
showed when trying to start it again on 09/10.

### 13.4 Recommendations, closed

The open ones are in `BACKLOG.md` 2. Each closed one, with its commit;
the text of R11 onwards is in the review section that opened it, below.

| | # | Priority | Recommendation | State |
|---|---|---|---|---|
| ✓ | R1 | **high** | Notify a person who appears in the middle of an event | done `760d68e` (ARCHITECTURE 12.8) |
| ✓ | R2 | medium | A race at start-up: two launches in a row bring up two instances | done `760d68e`, made atomic in review 2 `8a81084` (ARCHITECTURE 18.8) |
| ✓ | R3 | medium | The live view freezes without warning when the service restarts | done `760d68e` (ARCHITECTURE 17.8) |
| ✓ | R4 | medium | Exposure on a Wi-Fi network classified as Public — **the user's decision** | decided 09/10: keep open to the LAN |
| ✓ | R5 | medium | "Recognised" with a low similarity | done `760d68e` (ARCHITECTURE 12.8) |
| ✓ | R6 | medium | Automatic tests for the web routes and the notification locks | done `9e25534`: 23 tests, `uv run pytest` (ARCHITECTURE 19.5) |
| ✓ | R8 | low | A network failure on the page is not shown to the user | done `760d68e` (ARCHITECTURE 17.8) |
| ✓ | R11 | **high** | `settings.save()` drops keys it does not know | done `524b14f` (ARCHITECTURE 19.2) |
| ✓ | R13 | verification | The startup task survives a reboot, and restarts after a crash | **reboot verified 10/10**: Windows up 00:58:07, task at 00:58:16, cameras ok 00:59:06, in session 0 with no window. **crash verified the same night**: the user ended Python in Task Manager about 01:01 (the task shows result 1, Task Manager's exit code); the 5-minute trigger at 01:06:10 started it again, cameras ok at 01:06:16. A crash costs at most ~5 min of recording |
| ✓ | R15 | **high** | ffmpeg opens console windows on the user's desktop | done `9eaa42c` (ARCHITECTURE 18.7) |
| ✓ | R16 | **high** | Notification outcomes are never logged, and an error detail can carry the bot token | done `9ae537b` (ARCHITECTURE 12.9) |
| ✓ | R17 | medium | No way to tell why something was *not* recorded: a replay tool | done `cc08df1` (ARCHITECTURE 12.10) |
| ✓ | R18 | **high** since review 3 | The white dog lying on the Front mat is detected as `person` | done `13bb4d5`, ratio 2.0 after the replay (ARCHITECTURE 12.10) |
| ✓ | R19 | **high** | The event's picture is its first frame, so it can show the dog instead of the person | done `085b3b6` (ARCHITECTURE 12.9) |
| ✓ | R20 | **high** | The face scan samples too sparsely and misses short frontal moments | done `668588d` (ARCHITECTURE 12.9) |
| ✓ | R21 | **high** | What the dense face scan costs live analysis on the M900 | measured `6ff6eda`: YOLO 1.6× slower during a scan; fix decided as R23 (13.8) |
| ✓ | R22 | medium | Nothing records where the dense scan looked | done `c5166d1` (ARCHITECTURE 12.10) |
| ✓ | R23 | **high** | A face scan slows YOLO while an event may be happening | done `754fa45`: YOLO 342 ms with the scan paused, against ~590 ms (ARCHITECTURE 12.10) |
| ✓ | R24 | **high** | Anyone on the Wi-Fi, or a web page they open, can now change settings and names | done `f2a7c3e` (ARCHITECTURE 17.10) |
| ✓ | R25 | medium | A face found in an event that fell in the cooldown is never sent | done `74fd71e` (ARCHITECTURE 12.10) |
| ✓ | R26 | low | Production installs the development tools (pytest, httpx2) | done `59d35fd` |
| ✓ | R27 | medium | Every dog not matched for sure becomes a new unnamed entry; the Dogs tab fills up | done `0b69a6b` (ARCHITECTURE 20) |
| ✓ | R28 | **high** | Another computer runs an old copy of the page after every update, and a refused change fails without saying why | done `a54f357` (ARCHITECTURE 21) |
| ✓ | R29 | medium | Naming a dog does not gather its look-alike crops, as naming a person does | done `49a17b8` (ARCHITECTURE 21) |
| ✓ | R31 | medium | The face scan runs YuNet on full 1080p frames and halves live analysis outside events | done `d00b99f`: 137 → 45 ms per frame (ARCHITECTURE 21) |
| ✓ | R32 | low | Browsers closing the live view log Windows asyncio errors (27 tracebacks) | done `ef464f8` |
| ✓ | R36 | low | A report can race a scan that reinforces the same entry, losing that one new view | done `0daa7ff`: taken out under the lock first (ARCHITECTURE 21) |
| ✓ | R37 | low | A report says what it is not, never what it is (the user's own face filed as a dog) | done `72924d7`: "Actually…" in the Settings list (ARCHITECTURE 21) |
| ✓ | R38 | **high** | A report made by mistake cannot be undone | done `2c2c943`: Settings → Bad-detection reports, with Undo; older reports undo too (ARCHITECTURE 21) |
| ✓ | R39 | **high** | Person and dog pages showed no photos | fixed by the architect `76a5a9e`, release `v2026.10.11.5`: backlog 24 added a hidden proposal grid with the same class, and the page filled the first `.views-grid` it found — the hidden one. The tests cover the server only; a check of the page in a browser would have caught it |
| ✓ | R40 | **high** | Waiting views are hidden, and move into the chosen ones on their own | done `4d9a190`: Chosen and Waiting grids, ↓ ↑ × moves, Analyse can discard (ARCHITECTURE 21) |
| ✓ | R33 | medium | The documentation had grown by appending: README stale, CONTEXT read whole by every session | done 12/10 by the architect: CONTEXT cut to a brief and this file; README, INSTALL, PYTHON and ARCHITECTURE in English; ARCHITECTURE reorganised by subject (text in 13.12) |
| ✓ | R44 | **high** | The user bending over becomes a "dog": a crop in the Dogs tab and a `dog` label | done `aa68bc4`: a dog box where a person stood in the last 2 s is that person (ARCHITECTURE 7.12; 13.16 below) |
| ✓ | R43 | low | `config.json` is rewritten in place, with no lock, by two writers | done `565a34b`: one lock, write then replace, retries on Windows (ARCHITECTURE 11.6) |
| ✓ | R41 | low | A view is moved by its position, which a full queue shifts when a scan adds one | done `f4fe810`: each move names the photo it was shown, 409 if it changed (ARCHITECTURE 22.6) |
| ✓ | R34 | **high** | Devices have to type the PIN again and again | done `d6aa12e` (ARCHITECTURE 21) |
| ✓ | R35 | medium | Aurora curled on the mat slips through R18 as `person` | closed without change: the five boxes a 1.5 ratio would drop were all people (ARCHITECTURE 21); rare cases go to bad-detection reports |
| ✓ | R10 | **high** | Everything except the conversation in English | done: the code and the program's text by 10/10, every document's text on 12/10 by the architect (R33), the file names and the last two tools' text in `f855a9e` and `aa6e243`; the old `--sem-janela` and `--janela` flags stay as aliases (13.18 below) |
| ✓ | R45 | low | A merge finds its sightings by reading every one, once per entry merged | done `351bc23`: one pass per save with an `{old: new}` map; a batch of 5 reads each sighting once instead of 5 times (ARCHITECTURE 17.16; 13.17 below) |
| ✓ | R7 | low | `install.bat` does not check that the Python is signed | done `e426c8b`: `tools/check_python.ps1`, run by `install.bat` after `uv sync` and by `production.ps1` on every deploy (ARCHITECTURE 18.7, INSTALL 1.2; 13.19 below) |
| ✓ | R46 | **high** | A person who moves while bent over is still filed as a dog: R44 caught 9 of 32 boxes | done `0a514c3`: a dog box that takes the place of a person who vanished from the same run is that person, and relabelled boxes renew the memory (ARCHITECTURE 7.13; 13.20 below) |
| ✓ | R48 | **high** | The 40-view rule lets a wrong-person view in first | closed in review 23: under ArcFace no wrong-person view reaches `LEARN_THRESHOLD` (closest pair 0.313 against 0.40), so backlog 28 shipped with R49 in `v2026.10.14`; the seven misfiled views still wait for the user before the once-only tool runs (13.24) |
| ✓ | R49 | **highest** | The top or the back of a head passes as a face and draws wrong "sure" matches | done `94f4fbc`, `v2026.10.14`: SCRFD + ArcFace R50 and a migrated gallery; a head-top still passes as a face, but matches no one else (ARCHITECTURE 10.14; HISTORY 13.24) |
| ✓ | R30 | **high** | A face seen from the side is dropped, so many person events end without a face photo | (a) done `9fb8862`: the side view as a picture (ARCHITECTURE 10.12); (b) done `fe0853b`, `v2026.10.14.2`: `MIN_EYE_SPREAD` 0.38 → 0.30, measured on both residents under ArcFace (ARCHITECTURE 10.12; 13.25 below) |
| ✓ | R51 | medium | A clip's face is matched by its heaviest view, not its best | done `734efa4`, `v2026.10.14.2`: every view matched, the best decides and is learned; sure 11 → 12, none 1 → 0, nothing wrong (ARCHITECTURE 10.3; 13.25 below) |
| ✓ | R52 | low | The gallery migration runs before the log file and before the port is held | done `50c836e`, `v2026.10.14.2`: a `filelock` around the migration, its line after `log.to_file()` (ARCHITECTURE 10.14; 13.25 below) |
| ✓ | R42 | **high** | In Home, a resident's face plus a second person who never shows a face sends nothing | (b), the user's decision of 14/10: done `747042b`, `v2026.10.14.3`: YOLO's most people at once against the distinct faces found; the best view goes out as `faceless_person` (ARCHITECTURE 22.3; 13.26 below) |
| ✓ | R53 | **high** — the user's report | The two dogs are told apart by colour histograms, which overlap | done in two steps: the bench `bed651d` (review 25), DINOv2-small `8d762d6`, `v2026.10.15`, with a migrated gallery; every bench view named right, no person crop named (ARCHITECTURE 20; 13.27 below) |
| ✓ | R56 | low | The hidden-person message shows the best single view, which may be the resident alone | done `a6818e4`, `v2026.10.15`: the frame where the people were counted, `HH-MM-SS.people.jpg` (ARCHITECTURE 22.3; 13.27 below) |
| ✓ | R57 | low | `production.ps1 -Action update` stops a production whose cameras are down | done `e2165c0`, `v2026.10.15`: refuses unless `-Force`, and every failure says which part failed (ARCHITECTURE 18.7; 13.27 below) |
| ✓ | R55 | medium | The accuracy tables leave out only exact copies: a view's own event vouches for it | done `cde3087`, `v2026.10.15.2`: each view records its event (`view_events`), the views stored before recovered at start, both tables leave out the probe's whole event (ARCHITECTURE 10.15, 10.16; 13.28 below) |
| ✓ | R60 | **high** | The per-camera and per-face cooldowns drop what they block: a held faceless person can never reach the phone | done `136e9b0`, `v2026.10.16`, with backlog 40: nothing is dropped, a message rings or arrives silently by the house's incident; reproduced first by `test_a_held_faceless_person_inside_the_quiet_window_still_reaches_the_phone` (ARCHITECTURE 12.11; 13.30 below) |
| ✓ | R61 | low | Item 40's three small things: the floor renews a closed incident, the replay tool misreads camera lines, the return counts minutes only | done `f549760`, `v2026.10.16.2`: the floor renews only an open incident, the camera lines parsed by their own words and forced as live, "18 h 5 min without"; each reproduced by a test first (ARCHITECTURE 12.11, 12.12; 13.31 below) |

**R1 — Notify a person who appears in the middle of an event (high).**
`EventRecorder._start()` tried to notify **only on the event's first frame**,
with that frame's labels. If the event began with a dog, `notify.event()`
refused (only `person` notified) and nobody tried again: the person arriving
seconds later **got no notification at all**, and so no second message with
the face either (ARCHITECTURE 12.7), which depended on the first one having
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
listens on `0.0.0.0` without a login, as decided (ARCHITECTURE 17.4). But the
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
faces, ARCHITECTURE 10.4 already admits 0.37 can be chance — that is why
`LEARN_THRESHOLD` is 0.45. The message should reflect the difference: below
0.45, "probably <name>".

**R6 — Automatic tests (medium).** PROCESS 5 records the absence of tests as
a bias never discussed. This review added two cheap, valuable targets: the
thumbnail route's checks (the only barrier between the network and the files
on disk) and `notify`'s locks (`_allowed`, R1). FastAPI has `TestClient`; it
needs `httpx` as a development dependency. The check that day was a loose
script in the scratchpad, which does not stay in the repository.

**R7 — `install.bat` does not check the Python (low).** Step 3 installs the
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
the resume routine (PROCESS 2.1), check which interpreter `.venv` uses and
that `jarvis` starts.

### 13.5 Review 2 — what was fixed, and the new recommendations

Reviewed `760d68e..67f7d23` (the developer's pre-production delivery) against
the code and a real run, before the first release.

**Fixed by the architect in `8a81084`:**

- **R2 was only half fixed.** The port was checked in the main thread and bound
  later in uvicorn's; two launches a moment apart both saw it free. Now bound
  atomically with `SO_EXCLUSIVEADDRUSE` and handed to uvicorn. Tested: two
  launches at the same instant, one runs (ARCHITECTURE 18.8).
- **Crash recovery would not have worked.** "Restart on failure" only acts when
  a task fails to start; a crash after starting would have ended the
  surveillance until the next reboot. Replaced by a 5-minute trigger with
  "ignore new", plus a `HOLD` file so the trigger cannot start production
  mid-update or after a deliberate stop (ARCHITECTURE 18.7).
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
the previous version, both cameras fresh (ARCHITECTURE 18.7).

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
   `pythonw.exe` gets a window of its own (ARCHITECTURE 18.7). The two that
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
What changed is in ARCHITECTURE 12.9, 18.7 and 19.2.

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
`rebuild_faces.py` rescan densely; it is additive, so allowed, but not needed
until a rescan is.

**R10, left:** older documentation, `ui.py` (including its Telegram test text),
`cameras.build_camera_list()`'s `SystemExit`, `tools/diagnose.py`, and the
Portuguese file names.
### 13.8 Review 4 — developer session 2

Reviewed `5d91305..1b8822d`. No code fixed. The trace hooks in `motion.py`
and `people.py` change no decision (the developer compared old and new on all
561 frames of the 22:29 clip); every module imports, `ui.py` included after
its translation; no comments; the version reads `v2026.10.10-12-g1b8822d` in
the test copy. Integrated into ARCHITECTURE 12.10.

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
into ARCHITECTURE 12.10 and 17.9. The three points the developer left open,
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
Integrated into ARCHITECTURE 17.10 and 19.2. The threat model of R24 is
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
(ARCHITECTURE 20) — and the other computer's stale page (R28) can hide them.
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
three OpenCV tabs and `jarvis.bat` opening a window; ARCHITECTURE (2,909 lines)
and CONTEXT (1,388) grew by dated appendices (12.9, 12.10, 17.9, 17.10, 20).
CONTEXT is read by every session's resume routine — about 25k tokens each
time. Plan: README rewritten in English; CONTEXT cut to the current brief
(rules, state, backlog, open recommendations, plan), with the review history
and usage log moved to a `docs/HISTORY.md` read on demand; ARCHITECTURE
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
the `dev` skill now say so (ARCHITECTURE 19.5).

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

That became R44 (13.4, closed in review 16). It leaves 3 reports: the two dark-object ones
(IoU 0.12 with any person) and one bend at 12:40:23 with no person seen in the
2 s before. The dark object is a candidate for using the reports themselves —
a reported box marks a place that is not a dog on that camera — but two
reports are too few to set a distance, and Aurora lies on a mat nearby. It
waits for more reports, which backlog 26's "Bad detection" on many crops at
once makes cheap to give.

**R44 as it was opened (high).** `SubjectDetector` keeps the person boxes of
the last 2 s; a `dog` box with IoU ≥ `SAME_PERSON_IOU` = 0.5 against any of
them is **relabelled `person`** (then the person rules — minimum height, the
mat — apply as to any person), so no `dog` label, no dog crop and no dog
message come from it, and the person's own message is unaffected. Trace
reason in `replay.py`: "the person's box from a moment ago". Acceptance: a
test with a person box followed 1 s later by a `dog` box in the same place
(relabelled) and a small dog box at the person's feet (kept); `replay.py` on
the four reported clips (`Front/2026-10-12/11-28-48`, `11-45-20`, `12-39-56`,
`12-40-23`) and the six true-dog clips with a person: the reported boxes
change, the true dogs do not. Done in developer session 14 (13.17).

### 13.17 Review 16 — developer session 14 (12/10/2026)

R44, backlog 26 and 27 and R43, reviewed whole (`v2026.10.12..a53aa84`, 15
files). 174 tests pass (`python -m pytest`), `check_data` reads every file
(no format changed: `guess` is a field of an answer, and `config.json` keeps
its content), no comments in the code. Both new POST routes pass the write
guard and check every id against the id pattern; the page writes every name
with `textContent`, so a name cannot inject HTML.

**R44, checked beyond the delivery.** The developer replayed the reported
clips and the six true-dog clips with a person. Not the dog alone: a dog that
YOLO calls `person` for one run (R18) would have its next 2 s of dog boxes
relabelled. Replayed here with `--prime` on six of production's dog-only
events of 12/10 (`Front` 20-05-07 and 11-28-05; `Back` 20-04-05, 16-27-50,
10-59-19, 10-58-35): 174 dog frames, **no box relabelled**. The developer's
table, frames per label with the rule off (`SAME_PERSON_IOU` = 2) → on:

| Clip | Kind | dog frames | person frames | relabelled YOLO runs |
|---|---|---|---|---|
| Front 12/10 11-28-48 | reported, bend | 298 → 289 | 191 → 197 | 3 |
| Front 12/10 12-39-56 | reported, bend | 18 → 9 | 61 → 67 | 3 (one then dropped as wide at the bottom edge) |
| Front 12/10 12-40-23 | reported, bend, no person before | 3 → 3 | 21 → 21 | 0 (expected) |
| Front 12/10 11-45-20 | reported, dark object | 12 → 12 | 66 → 66 | 0 (expected) |
| 6 true-dog clips with a person | | identical | identical | **0** |

The replay counts frames and 13.16 counted boxes, so the two are not the same
unit. Recording every person box YOLO returned, kept or later dropped, is
accepted: the replays show no cost, and the bending user's earlier box may be
one a person rule drops.

**Fixed in the review.** `.gitignore` held `config.json` but not R43's
temporary `config.json.<pid>.<thread>.tmp`: a crash between the write and the
replace would leave the Telegram token and the PIN in an untracked file that
`git add .` would commit. `config.json.*` added; `git check-ignore` confirms.

**The developer's other points, decided.** An id named meanwhile is answered
as gone, not joined: right, the user named it on purpose. The face guess at
`MATCH_THRESHOLD`: accepted, it is a hint and the merge asks first. `load()`
without the lock: accepted, the atomic replace and the read retry are enough
for a reader. `assign` with `to` an unnamed entry answers 409 "merged or
reported meanwhile", a wrong reason; the page never sends it (its list holds
named entries only), so no change. The scan per merged entry became R45.

**R45 — A merge finds its sightings by reading every one (low).**
`_repoint_sightings` reads every sighting file of the gallery's folder to
rewrite those that pointed at the merged entry — once per entry merged, under
the gallery lock, while the clip thread waits to add its sightings. Sightings
are never pruned: production has 205 dog sightings after four days (about 50 a
day), so in a year a batch of 60 photos would read about a million files.
Nothing today. Fix: one pass per batch with an `{old: new}` map. Bounding the
scan by the entry's `first_seen` is **not** safe: `tools/dog_crops.py` gives
crops to old events, so an entry made today can have sightings dated days
before. Acceptance: a test where a batch of several entries reads each
sighting file once.

### 13.18 Review 17 — developer session 15 (12/10/2026)

R10's file names and the tools' text, and R45, reviewed whole
(`v2026.10.12.2..f4489a0`, three code commits, 53 files counting the
documents). 176 tests pass, `check_data` reads every file (no format
changed), no comments in the code.

**R45, checked against every caller.** `_merge` now only records
`{old: new}`; `save()` repoints the sightings in one pass, then writes
`gallery.json` — the same order as before. Every caller of `_merge`
(`rename`, `assign`, `Gallery._absorb`, `DogGallery._absorb`) runs under the
lock and ends in `save()`; their early returns all come before the first
merge. `load()` empties the map, so an operation that raised before saving
never repoints anything. A chain collapses when it is recorded, and an entry
is never merged into itself (`rename` and `_absorb` skip it; `assign` takes
only unnamed sources and a named target). A failure between the sightings and
`gallery.json` leaves the same state as before the change.

**R10, checked.** No old name is left outside the record of the rename
itself. The renamed tools passed an AST check for names used but never bound
(the translation renamed most identifiers): none. The `.bat` files keep CRLF
in the working tree and LF in the index, as before (`core.autocrlf`). The
code holds no Portuguese but the `--sem-janela` and `--janela` flags, kept on
purpose as aliases. R10 is closed.

**Fixed in the review (text only).** The three historical lines the new
`check_doc_refs.py` flagged, so it exits 0; `.gitignore`'s five Portuguese
comments (patterns unchanged, the ignored list identical); R9's pointer to the
old "routine 12.1"; this file's header, which still sent closing
recommendations' text from CONTEXT's old section 13.4 instead of BACKLOG 2.

**The developer's points, decided.** Historical sentences here now carry the
new names (`CONTEXT.md` where the file was `CONTEXTO.md` then): accepted, a
reference that works is worth more than the name of the time, and the rename
commit records it. The `jarvis_vigilancia.bat` shim goes in the next release
(developer 16). `jarvis_headless.bat` names port 8765: production's port; the
test copy is the exception, accepted. `check_doc_refs.py` joins every review
that touches `docs/` (PROCESS 3.1). Its limit: it checks only references that
name their document — "13.16 below" or a bare "section 11" are not checked.

### 13.19 Review 18 — developer session 16 (12/10/2026)

The shim removed and R7, reviewed whole (`v2026.10.12.3..9866a9b`, two code
commits, five files). No Python changed: 176 tests pass, no data format
touched, so `check_data` was not needed.

**R7, checked where it runs.** `tools/check_python.ps1` was run against
production's own `.venv` in the exact pattern `Sync` uses — `&`, `| Out-Host`,
then `$LASTEXITCODE` — under `$ErrorActionPreference = 'Stop'` and with
`$LASTEXITCODE` preset to 99, so a stale value could not pass for a fresh
one: `pythonw.exe` and `python.exe` pass and reset it to 0; `jarvis.exe`
(`NotSigned`) and a missing file throw. `$PSScriptRoot` inside `Sync` is
`production.ps1`'s own folder — the development folder, the same one `$DevDir`
comes from — so the caller and the check always come from the same commit;
the update and the rollback both reach it through `SwitchTo`. `-and`
short-circuits before reading the subject of an unsigned file's `$null`
certificate. The `.ps1` files are LF in the working copy and in the index;
PowerShell reads either, and the `.bat` files keep CRLF on disk as review 17
recorded. The deploy of `v2026.10.12.4` runs `Sync` end to end, the one path
the developer could not exercise: it printed `pythonw.exe is signed by the
Python Software Foundation.` and the update went on (13.2's row).

**Fixed in the review (one message).** R7 has two halves. When Smart App
Control already blocks `uv`'s own Python, `uv sync` itself fails (`Failed to
spawn: python`, `WinError 4551`) and the new check after it never runs; the
installer then said only "could not install the dependencies". It now names
those two errors and INSTALL 1.2. The block was run in `cmd` with errorlevel 1
and stops as before; `install.bat` keeps CRLF.

**The shim.** No file outside `docs/` names `jarvis_vigilancia.bat`; CONTEXT 9,
ARCHITECTURE 3's tree and PYTHON 34 updated, while the raid log and 13.18
keep it as history. R7 is closed; nothing opened. **The decided work has run
out**: the next cycle waits for the user (`PENDING.md`).

### 13.20 Review 19 — developer session 17 (13/10/2026)

R46, backlog 30 and backlog 29, reviewed whole (`v2026.10.12.4..594fbc6`,
three code commits, 17 files, +544 −53). 208 tests pass (176 before);
`check_data` reads every file; no comments in `src/` and `tools/`. No code
fixed.

**R46, checked on the clips.** `replay.py --prime` itself, not the
developer's counting script, on `Front/2026-10-13/15-00-17`: 555 frames with
a subject, all person, no dog; 9 boxes relabelled, 7 by R44 ("the person's
box from a moment ago") and 2 by the new rule ("took the place of a person
who vanished"). On two of HISTORY 13.16's true dogs with a person,
`Front/2026-10-11/16-20-00` and `Back/2026-10-12/12-40-35`: 99 and 164 dog
frames, not one box relabelled by either rule. The developer's numbers for
all twelve true-dog clips: unchanged.

**The rule, read for what it risks.** The greedy match is one dog box per
vanished person, the most confident first, and only dog boxes are offered; a
dog box under `ANIMAL_CONFIDENCE` can claim a person and is still dropped, as
before. What the developer flagged is real: **every relabelled box renews
both memories, so the chain has no end** — a real dog that took a vanished
person's place would stay a person while YOLO keeps seeing it within 0.3 of
its last box, and a relabelled box dropped afterwards (too short, the mat)
renews it too. In Home that means a "person with no recognisable face"
message for a dog. None of the true-dog boxes did. A cap on the chain would
cut the long bends R46 exists for, so nothing changes without evidence:
**R47 (low, a watch)** — a "not a person" report whose replay shows "took the
place of a person who vanished" is the trigger to bound the chain (for
instance by time since the last real person box). The reports list in
Settings is where it would show.

**Why not a tracker.** The developer chose ~40 lines over norfair or
supervision: both need scipy, a large compiled dependency never tried under
Smart App Control. That is PROCESS 5's narrower rule, not the old bias;
backlog 7 stays (proposto) and would replace 7.12 and 7.13 if decided.

**Backlog 30.** `modes.defaults` adds both probable cases off in Home and
Silent; `normalised` fills them into a stored file. Production's
`config.json`, read for this review: Home is active, `notify_labels` is
`["person"]`, Away has `known_person` on. After the deploy: Home silences a
probable resident person (the user's request), Away sends it, and the
probable resident dog is off in both, like every dog case there.
`dogs.identify` now reads the gallery entry for any certainty — `match`
gives `dog_id` only with a certainty, so an unidentified dog stays
`other_dog`.

**Backlog 29.** `Core.step` reads every frame and skips motion and YOLO while
Off; the page's header is refreshed by the 5-second health check on every
screen; `set_on`'s lock covers check-then-set. Two readings of the decision,
both kept: the event open at `/off` **finishes its pipeline** (clip, face
scan, follow-ups), which is what "ends as if the motion had stopped" means
for any event; and the reminder has **one attempt per 3-hour mark** —
`_reply` logs a failure and does not raise, so a reminder lost to the network
waits for the next mark (the handoff said it would go when the network came
back; ARCHITECTURE 22.7 says what the code does). Retrying on every poll
would spam the log while Telegram refuses.

**Documentation.** ARCHITECTURE 7.13 (new), 22.2 (nine cases), 22.5,
22.7 (new), the file tree, `/api/status` and 19.5's count; CONTEXT 9 and 10;
PYTHON 36 and 37. R46 closed, R47 opened. The plan goes on: developer 18,
backlog 28 then 32 and 31 (`BACKLOG.md` 3).

### 13.21 Review 20 — developer session 18 (13–14/10/2026)

Backlog 28 reviewed whole (`v2026.10.13..212179e`, two code commits, 11 files
of code and tests, +429 −86). 216 tests pass; `check_data` reads every file;
no comments in `src/` and `tools/`; `check_doc_refs` exits 0. **No code fixed,
no release.** The session was interrupted overnight by a dropped connection in
the middle of the measurements below and resumed on 14/10.

**The code, read against the decision.** `replaced_view` is the literal
reading of item 28: the new view's nearest chosen view *includes* the
candidate, so a view whose only near twin is the candidate is discarded —
and with that reading the closest pair in Chosen can never shrink (every pair
with the new view is farther than the old minimum). The dogs' candidate
restriction keeps the day/night balance; a chosen view with no same-lighting
twin is never a candidate, so a dog's only night view stays. The favourite is
excluded by index, and `cover_of` guarantees it is in `views`. Deleting in
`save()` after the write is safe because `load()` empties `dropped` — an
exception half-way leaves stale entries that the next `load()` drops, so at
worst a photo stays unused. `settle_waiting`'s `id()` count is sound: every
object compared is alive at once (the queue holds the waiting ones), so no
two share an id. `add()` calls `_take` outside the lock, but on a new entry
of at most 40 views, which never drops anything. The web builds a new
`Gallery` per request, so no instance is shared between threads.

**The rule, measured on production's data.** A copy of `C:\JARVIS`'s
`faces/` and `dogs/`, settled with the tool's own `settle_waiting`, gave the
developer's numbers (faces 22 and 20 enter, dogs 1 and 5). The question was
what the new 40 recognise, so every face the system kept — 146, Chosen and
Waiting — was matched against the named Chosen views, each probe without
itself or its exact copies:

| Gallery | Sure, right | Sure, wrong | Maybe, right | Maybe, wrong | None |
|---|---|---|---|---|---|
| Today (`v2026.10.13`) | 111 | 7 | 9 | 0 | 19 |
| Settled as is | 95 | 7 | 34 | 5 | 5 |
| The 7 deleted first, then settled | 105 | 5 | 27 | 4 | 5 |

The 7 wrong are not what the labels say: a contact sheet of every view
showed **7 of the 31 views in Gustavo's Waiting are Izabel's faces** — head
down, from above, several in her red top. Each matched Gustavo's Chosen at
0.475–0.509, above `LEARN_THRESHOLD` 0.45, through one of five dark or
head-down views of him (Chosen 15–19 and 31 on the page), so the scan
learned them as his. While they waited they recognised nobody. **The rule
lets them in first**, because a view of the wrong person is by nature the
most different: settled as is, 6 of the 7 enter Gustavo's Chosen, and from
then on Izabel's head-down faces match her own photos stored as Gustavo. No
measure on the embeddings separates them from his genuine waiting views —
similarity to the second and third nearest view and the count above 0.363
interleave the seven with his 24 genuine waiting views — and none is closer to Izabel's
Chosen than to his. Izabel's 75 views hold no face of Gustavo; the dogs'
queues hold no view nearer the other dog, and the dogs' leave-one-out is the
same before and after (24 sure right, 0 wrong; probable 31 → 35 right,
2 wrong).

**What this changes.** (1) The once-only tool was **not run**: the user
decided to delete what is left knowing it, not to put another person's faces
into Chosen. (2) The release is held: from a full Chosen the same wrong
"sure" matches would now enter instead of waiting. (3) The accuracy measured
on 13/10 for backlog 32 — "99.3 %, 1 error in 146 views" — counted those 7 as
right, because their label says Gustavo: at 0.45 at least 8 of the 146 are
wrong. **R48** (high, the user's decision) holds the options; the 7 views are
in `PENDING.md` by their position on the page.

**Documentation.** ARCHITECTURE 10.4, 17.10, 17.14 (the rule and what it
cannot tell), 19.2, 19.5, 20, 22.6 and the file tree; CONTEXT 9 and 10;
PYTHON 38. Developer 19 is planned with backlog 31 alone; 32 waits for R48
(`BACKLOG.md` 3).

### 13.22 Review 21 — developer session 19 (14/10/2026)

Backlog 31 reviewed whole (`0f68445..865eb7f`, one code commit, 8 files of
code and tests, +236 −16). 234 tests pass (216 before); `check_data` reads
every file; no comments in `src/` and `tools/`; `check_doc_refs` exits 0.
**No code fixed, no release.**

**The code, read against the decision.** Three optional keys in
`config.json`, older files read today's values, a stored value outside
0.20–0.90 falls back to its default on read and is refused by the page with
a 400. NaN and infinity, which Python's JSON reader accepts, fail the range
test too. YOLO runs at the lowest minimum and each label is cut afterwards;
greedy NMS keeps every box above a floor the same whatever the floor, so
the boxes that reach the rules are exactly those the old code gave whenever
the person minimum is the lowest — the defaults. The detector reads the
settings at most every 2 s of the monotonic clock, only when there is motion;
`settings._stored` already retries a read that meets a replace, so the new
reader on each camera thread adds no failure. One small thing left as is:
`check_data`'s settings line returns on the first warning, so a file with
both an unknown key and a bad confidence shows only the confidence warning —
both are warnings, the file is readable either way.

**The developer's claim, checked on the clips.** `replay.py --prime` on R46's
three clips, run twice — with `0f68445`'s `people.py` loaded in its place, and
with the new one: `Front/2026-10-13/15-00-17` identical line for line (1287
lines); `Front/2026-10-11/16-20-00` and `Back/2026-10-12/12-40-35` the same
decisions and totals (99 and 164 dog frames), with only the order of the
reasons swapped on three lines, because the below-confidence drops are now
written before the others. A weak dog box no longer reaches
`_people_replaced_by_dogs`; since dogs are matched the most confident first
and a weak one was dropped afterwards anyway, no relabelling changes — what
the replays show.

**The user's objection to R48, and what it found.** Told that the seven
views could not be told apart, the user answered that the two of them look
nothing alike, and that if the software cannot separate them nothing built
so far makes sense. Measured on production's `gallery.json`: between
Gustavo's and Izabel's 40 chosen views the median cosine is 0.05 and the
highest 0.42, under `LEARN_THRESHOLD`; each person's views are about 0.5 from
their own mean and 0.1 from the other's — the recogniser separates their
faces well. A contact sheet of the seven, of the Gustavo views they matched
and of Izabel's chosen settled it: **the seven are the top or the back of
Izabel's head**, and the views they matched, 15, 16, 18, 19 and 31 of
Gustavo's Chosen, are the top of his. YuNet found a "face" in each (score
0.61–0.89) and `is_frontal`, which tests that a face is not turned sideways,
passed them. Leave-one-out on the 146 kept faces with those five out of the
references: 101 sure and right, 0 wrong, 45 none, against 111, 7 and 28.
Requiring two matching views instead of one cut errors only with many right
answers (2 views at 0.45: 68 right, 1 wrong). No simple cue separates a
head-top from a face on these views: YuNet's score (medians 0.82 and 0.71
against 0.84–0.88), the eye-to-mouth height over the eye spread (1.2–2.8 on
head-tops, 0.8–4.6 on faces) and the embedding's length (5.4–7.8 against
4.4–10.7) all overlap. **R49 (high)** holds it; the twelve views go to the
user in `PENDING.md`. What review 20 said — no measure on the embeddings
tells the seven apart — stays true of those views, and was read, rightly,
as a claim about the faces; the next explanation to the user starts from the
pictures.

**The EPUB.** The user chose its documents: ARCHITECTURE and PYTHON only.
`tools/make_epub.py`'s `ORDER` is now that list and nothing else joins
(CONTEXT 10).

**Documentation.** ARCHITECTURE 7.1, 7.12, 7.14 (new), 12.10 and 22.4;
CONTEXT 10; PYTHON 17.4 and 39; BACKLOG 1, 2 (R48, R49, R47) and 3; PENDING.
No developer session planned: R48 and R49 wait for the user.

**The user's answer, the same morning:** no reason to change the screen's
behaviour without R49 — backlog 28 waits for it — and R49 is the top
priority; if much better models exist, they will be used. CONTEXT 3's
"YuNet and SFace, not InsightFace" was reopened with that reason, and its
old one logged as a bias (PROCESS 5.3). Production's `faces/` was copied to
`backups/r49_faces_20261014/` so the user can delete the twelve head-tops
now and the measurement keeps them; developer 20 is planned with R49's
measurement (BACKLOG 3).

### 13.23 Review 22 — developer session 20 (14/10/2026)

R49 step 1 reviewed whole (`865eb7f..706883b`, one code commit: the new
`tools/face_bench.py`, 523 lines; nothing in `src/`). 234 tests pass; no
comments in `src/` and `tools/`; `check_doc_refs` exits 0. **No code fixed,
no release.** The measurement and its table are in ARCHITECTURE 10.14.

**The code, read against insightface's own.** `Scrfd.detect` matches
insightface's `scrfd.py`: input scaled by 1/128 around 127.5 in RGB, anchor
centres from `np.mgrid` with each centre repeated once per anchor, boxes and
landmarks as distances from the centre times the stride, NMS at 0.4. Two
differences are too small to matter. It divides by the float scale where
insightface divides by the rounded one, and OpenCV's NMS measures areas
without insightface's +1. The 3D landmark model's pose follows
`landmark.py`. Its `z` is not rescaled by the inverse transform, which does
not matter: only the first two rows of the fitted 3×4 matrix give the
rotation. The colour orders and normalisations of ArcFace, AdaFace and
MagFace match their authors' loaders. The leave-one-out could have favoured
the stored embeddings, which skip a reference with the same embedding as
the probe while a re-embedded pipeline skips only the same bytes. It does
not: no two views share an embedding without sharing their bytes, and no
two different photos are above 0.99. The stored baseline reproduces review
21's 111 / 7 / 9 / 0 / 19.

**Alignment, measured.** `arcface_crop` fits the five points with
`estimateAffinePartial2D` and LMEDS. Least squares (Umeyama), which is what
insightface's scikit-image call computes, was run on SCRFD-at-320's points.
Its totals barely move: zero-wrong 0.275 → 125 both, sure right at 0.40 88
→ 89. But 19 of the 146 embeddings differ, with a cosine as low as 0.57.
LMEDS drops points it judges outliers. OpenCV's own
`FaceRecognizerSF.alignCrop`, fed SCRFD's points in YuNet's 15-number row,
gives the least-squares crop pixel for pixel on all 146 views: same
template, no transform written by hand. Step 2 uses it.

**Only two people, checked against a third.** The developer flagged it: the
separation is measured on Gustavo and Izabel alone. The backup holds seven
unnamed entries, 22 views. Under ArcFace every one matches Izabel best, up
to 0.546. Under SFace, today's matcher, they split between Izabel (up to
0.400) and Gustavo (up to 0.405). A contact sheet shows two kinds. Three
entries, 11 views, are a woman with long loose hair, sometimes with glasses.
Two entries show grey hair tied back and a red top, like Izabel's photos,
and two are unclear. If the long-haired woman is someone else, ArcFace at a
0.40 sure threshold would learn two of her views as Izabel (0.546, 0.469),
and six more would be "probably Izabel" at 0.30. SFace at 0.45 learns none,
since 0.372 is her highest to Izabel. At 0.363 it calls two of them
"probably Gustavo" and up to three "probably Izabel". Named as her own person, both models give all 11 of her
views to her: her other views beat Izabel's every time. If she is Izabel,
ArcFace recognises her where SFace cannot. The architect cannot tell from
the pictures, and the answer decides whether 0.40 is safe. It went to the
user (`PENDING.md`).

**The licence, checked.** InsightFace's README, read 14/10/2026, confirms
the developer's quote. The code is MIT. The training data and the models
trained on it are "for non-commercial research purposes only". An update
dated 2025-11-24 sends licensing of the open recognition models, buffalo_l
named, to recognition-oss-pack@insightface.ai. That is the user's call too.

**Documentation.** ARCHITECTURE 10.14 (new) and the file tree; CONTEXT 3
(PyTorch imported under Smart App Control, not needed), 9 and 10; PYTHON 40;
BACKLOG 2 (R49) and 3; PENDING.

**The user's answers, the same hour.** All seven unnamed entries are Izabel,
the long-haired ones with her hair down. Asked whether InsightFace is
certainly the best: "if it is, we use it". The honest answer was that it is
the best of what was measured, by far, and that one stronger candidate from
the same author was not measured: `antelopev2`'s R100, trained on
Glint360K, in the same release and under the same licence, about twice as
slow. Developer 21 measures it first, with the 22 views of Izabel as extra
probes and OpenCV's alignment, keeps R50 unless R100 is clearly better, and
then makes the switch and the migration. The migration writes a new gallery
file, so that an automatic rollback to `v2026.10.13` still reads the old one
(BACKLOG 3).

### 13.24 Review 23 — developer session 21 (14/10/2026)

R49 step 2 reviewed whole (`706883b..70d3fce`, two code commits, 13 files of
code, tools and tests, +568 −147). 240 tests pass (234 before); no comments
in `src/` and `tools/`; `check_doc_refs` exits 0. **One code fix**
(`d07c09e`), two recommendations opened, **release `v2026.10.14`**.

**The code, read against the plan.** The six points are done as planned,
with one deliberate change the HANDOFF argues well: SCRFD runs on the square
`context_crop` saves (2.2 × the face) rather than on `_refine`'s region, so
the migration and the scan embed the same framing. Checked on four real
clips: the same face embedded from the frame and from its saved 300 px JPEG
gives cosine 0.97–0.99 (median per clip), so the bench's numbers, taken on
the photos, hold for the scan. Lock order is right: `refit` takes
`_SCAN_LOCK` and releases it before `put_back` takes `_GALLERY_LOCK`, the
order a scan uses. Undo copies the report's photos back before `put_back`
embeds them. `Gallery.save` keeps the header, so `source` survives; a dog
gallery writes no `model`. Every reader of the face gallery follows
`GALLERY_FILE`; `rebuild_faces.py` moves the whole `faces/` aside as before,
`gallery.json` included — a rollback after a rebuild finds no gallery, as
before this release. `SAME_FACE_THRESHOLD` 0.35 and `LEARN_THRESHOLD` 0.40
are both above the closest cross pair. Two corners left as they are: a
report from before the switch whose views have no photo would come back with
no embeddings (production has no face report), and the SCRFD detection
nearest the face's centre could, in a square holding two faces where SCRFD
misses the right one, be the neighbour's.

**The fix: `FetchModels` aborted instead of skipping.** The HANDOFF says an
old tag was "skipped". In the script's own context it threw: under
`$ErrorActionPreference = 'Stop'`, Windows PowerShell 5.1 turns the redirected
stderr of `git show` into a terminating error. Reproduced with the function in
a script with the same preamble; fixed as `CurrentVersion` already does it,
and probed again against `v2026.10.13` (skipped) and `HEAD` (runs, "nothing
to fetch"). Nothing would have broken, but a manual update back to a release
from before R49 was impossible (ARCHITECTURE 18.7, PYTHON 41).

**What the review measured.** Production's `faces/` copied and migrated
again: 173 of 173 views kept, 31.8 s with production and a second
measurement running. Four clips scanned densely against it: no view's best
named match was the other person. Nine of Gustavo's views matched an unnamed
entry best, `p_62e42af6`, at up to 0.391: four views from 11:05 today, a
bearded man with a headset — by the contact sheet, Gustavo himself, unnamed
because SFace did not know him with it (`PENDING.md`). The scan recorded his
daytime clip as "probably Gustavo" at 0.349, its heaviest view, while its
best view scores 0.421: **R51**. The migration runs before `log.to_file()`
and before the port is held, so production's log never gets its line, and a
second launch in those ~25 s migrates too: **R52**.

**Backlog 28 read again (R48).** On the bench and on the four clips, no
wrong-person view reaches 0.40; the closest pair is 0.313. The mechanism R48
was about — a wrong "sure" match entering a full Chosen first — did not occur
under ArcFace, so 28 ships with R49 and R48 closes. What remains is data: the
seven head-tops of Izabel already in Gustavo's Waiting. Settled under ArcFace
on the migrated copy, 6 of them still enter his Chosen, because the rule
never asks whose a view is; with the seven deleted first, none does. The
once-only tool waits for the user (`PENDING.md`). The five head-tops of
Gustavo in his Chosen match Izabel at 0.29 at most, under `MATCH_THRESHOLD`.

**The `alignCrop` question** (HANDOFF 6). SFace's 37 MB stay loaded only for
OpenCV's alignment. Kept: it is the library's own least-squares fit,
pixel-identical to insightface's on all 146 views (13.23), and OpenCV's
`estimateAffinePartial2D` offers only RANSAC and LMEDS. Size is not a
criterion (PROCESS 5.2).

**Documentation.** ARCHITECTURE 10.2 (rewritten), 10.3, 10.4, 10.5, 10.14
(step 2: R100, the migration, the cost), 12.8, 17.14, 18.7, 19.1, 19.2, 19.4,
the tree; CONTEXT 3, 9 and 10; INSTALL 3; PYTHON 41; BACKLOG 1, 2 and 3;
PENDING.

### 13.25 Review 24 — developer session 22 (14/10/2026)

Developer 22 reviewed whole (`70d3fce..099d547`: six code commits, 14 files
of code, tests, `pyproject.toml` and `uv.lock`, +477 −31; the range also holds
review 23's own `d07c09e` and documents). 269 tests pass
(240 before); no comments in `src/` and `tools/`; `check_data` reads every
file; `check_doc_refs` exits 0. **No code fix**, three recommendations
closed, one opened, **release `v2026.10.14.2`**.

**The code, read against the plan.** Backlog 34: `POST /api/analysis` is a
write, so `guard_writes` refuses it without the header and from an unpaired
device, as for every other write; it calls the same `analysis.set_on` as the
bot, so the reminder and the Core's log line follow. In the test copy, with
`confirm` replaced, a click Off asked once and a click On asked nothing.
Backlog 35: the mapping is in Python and the page only moves positions;
every two-decimal value from 0.20 to 0.90 survives the round trip for
defaults 0.20, 0.25, 0.35, 0.45, 0.50 and 0.90 (checked here, not only in
the tests); a three-decimal value, which only a hand edit can store, is
rounded on the next Save — harmless. Backlog 36: CSS only. R52: the lock
wraps the hash check and the rebuild, `cameras.main()` logs after
`log.to_file()`, and `filelock` 4.1.2 ships no `.pyd` or `.dll`. R51:
`_best_view` keeps `Gallery.match`'s preference across views; the crop
learned is the matched view's own (`views` and `crops` are appended
together in `_group`). R30 (b): one constant, measured.

**The page, at phone and desktop width** (PROCESS 1, the architect's since
14/10). At 1280 px Notifications is two columns and Detection one panel of
three sliders; at 375 px the sliders take their own rows with the end texts
under them, Notifications stacks (both panels 335 px), the header button is
39 × 32 px beside the version, and the page scrolls only vertically
(`scrollWidth` 375). One text in ARCHITECTURE 22.4 was wrong and is fixed:
the five Settings tabs wrap to two lines on a phone, they do not fit in one.
Two small UX decisions: the sliders show no mark where the default sits, so
backlog 38 adds a tick; the `alert()` for a refused header write stays —
it only happens on an unpaired device.

**What the review weighed hardest: the stranger.** R51 and R30 (b) both
raise a resident's chances, and both were measured on the two residents
only. R51 applies `Gallery.match`'s "a named person wins" across all of a
group's views: a stranger has N chances to cross 0.30 against a resident,
and a returning stranger whose views match their own unnamed entry far
better still reads "probably <resident>" if one view crosses — silent in
Home, against the rule the user set this morning (CONTEXT 3). The evidence
at hand is reassuring — best of N lifted the other resident by 0.013, to
0.256 — and production has no stranger with a face to measure (its gallery
holds 2 named entries and no unnamed one). So the change ships, and **R54**
watches it, with a trigger and the two rules to measure if it fires.

**Production read.** `v2026.10.14` since 12:07: 6 face scans, one "probably
Gustavo" silenced in Home, no error or warning in the log. The nine misfiled
dog views of `PENDING.md` are all still there, so developer 23's R53 bench
labels them itself.

**Backlog 37, designed** (BACKLOG 1). Production's counts on 14/10: faces —
2 named entries, 80 chosen and 58 waiting views, sightings 17, 23, 18, 142
and 6 a day from 10/10 (13/10's 142 include the evening's rescan); dogs — 2
named, 44 unnamed of 1 view each (`MAX_UNNAMED` 60), sightings 15–134 a day;
the two folders 8.1 and 7.8 MB in six days. The Dogs tab at 375 px is 9,148
px tall for 46 cards. Everything that grows is bounded except unnamed faces,
so the layout pages long lists at 24 and folds every grid to two columns on a
phone, and the one cleaning rule proposed is the dogs' cap for faces —
the user's decision (`PENDING.md`).

**Closed: R30, R51 and R52.** Their texts as they were open:

**R30 (b)** — loosen the frontal gate once a second named person exists:
waited since review 11 (13.12) for Izabel and then for ArcFace; done with
the measurements in ARCHITECTURE 10.12.

**R51 — A clip's face is matched by its heaviest view, not its best
(medium, review 23).** `_group` keeps, for each face in a clip, the view with
the largest width × YuNet score, and `_scan_clip` matches only that view: its
score is the sighting's, decides "recognized" or "probably", and decides
whether anything is learned. Under ArcFace that view is often not the best
match. Gustavo's daytime clip `Back/2026-10-12/15-44-28`, scanned densely: 39
views on him, the heaviest at 0.349 — "probably Gustavo" — while his best
view scores 0.421 and 4 views pass 0.40. In Home it changes nothing (a
probable resident is silent too, ARCHITECTURE 22.2); in Away it is the
wording; and fewer views are learned, so Chosen renews more slowly (backlog
28). **What to measure before changing it:** the score of the best view, of
the second best and of the median of the three best, against the heaviest's,
on the four clips of developer 21 and on clips of both residents by day and
by night (`faces/<day>/*.json` names the clips), with each one's rate of
wrong best matches. A best-of-N score rises for a stranger too — the more
views, the likelier one crosses 0.30 — and no stranger has been measured, so
the choice that adds right answers with the least lift for one-off views
wins; the HANDOFF carries the table.

**R52 — The gallery migration runs before the log file and before the port is
held (low, review 23).** `cameras.main()` calls `migrate_gallery()` before
`web.start()` and before `log.to_file()`. Two consequences. (1) Production
runs under `pythonw.exe`, with no console, so the migration's line — views
kept, "no face", entries dropped, the backup folder — is written nowhere:
the one record of a non-additive change to the user's data is lost. (2) The
port is what keeps a second copy out (ARCHITECTURE 18.8), and for the ~25 s
of the migration it is not held: the 5-minute task trigger, or a click on
`jarvis.bat`, passes the already-running check and migrates too. The second
copy's write replaces the first's file with an equivalent one and then exits
at `web.start()`, so at worst what the first copy learned or the user did in
those seconds is lost; a collision of the two `.part` writes needs both to
finish within milliseconds of each other. **Fix:** log the result after
`log.to_file()`, and serialise the migration across processes —
`filelock`'s `FileLock` beside the gallery (pure Python, well regarded,
released by the operating system if the process dies; PROCESS 5.2), so the
second copy waits, finds the hash unchanged and does nothing. A test with two
threads standing in for two processes is enough for the lock; the log line is
read in `logs/jarvis.log` on the test copy.

**Documentation.** ARCHITECTURE 7.14 (the sliders), 10.3 (the best view),
10.9 and 10.12 (the gate), 10.14 (the lock), 18.7, 19.5, 22.4 and 22.7;
CONTEXT 10; PYTHON 42; BACKLOG 1, 2 and 3; PENDING; HISTORY 8.

**Release.** `v2026.10.14.2` deployed at 15:50 with `production.ps1`: every
file read before and after (976 events, 206 face and 412 dog sightings, 18
reports), `filelock` 4.1.2 installed, the signed `pythonw.exe` checked; no
migration ran, since `gallery.json` is unchanged, and no `.lock` is left in
`faces/`. About 10 s stopped; both cameras' last frame 0.1 s old right after.
Raid log 18.

### 13.26 Review 25 — developer session 23 (14/10/2026)

Developer 23 reviewed whole (`18b268c..72e9527`: five code commits and the
HANDOFF, 13 files, +1,120 −36, of which `tools/dog_bench.py` 356 and tests
184). 284 tests pass (269 before); no comments in `src/` and `tools/`;
`check_data` reads every file; `check_doc_refs` exits 0. **No code fix**,
R42 closed, R55, R56 and R57 opened, backlog 39 added, R53 step 2
decided, **release `v2026.10.14.3` tagged; its deploy rolled back**, for a
reason outside the release (below).

**R42 (b), read against the user's rule.** The count is taken where it
should be: `_consider_view` sees the subjects `detect` returns, after NMS
(0.45), `drop_duplicates` and the static-scenery suppression, so a split
detection or a suppressed shape does not count; the maximum is per frame,
reset in `_start`, and read when the assembly thread is created. The
condition in `after_scan` asks for **every** face silenced — a face that
reached the phone, or an unknown face, accounts for the scene — and `found`
holds distinct people, since `_scan_clip` skips a second group matching a
person already seen. `_faceless` moved the side view's and best view's rules
without changing them: their tests pass untouched. What the user accepted
with "if it errs, it errs", now written down (ARCHITECTURE 22.3): a dog
relabelled by R44 or R46, or called a person by YOLO, costs one message; and
**two residents leaving together with only one face seen** send one too — the
system cannot tell that scene from a stranger's. The one weakness is the
picture: the best single view, so the phone may show the resident alone
under "2 people seen" — **R56**.

**Backlog 32 for faces.** The threshold reaches all four places it should
— the case, the words, learning in the scan and gathering on naming — and
nowhere else decides "probably" (the page only shows what the scan wrote).
`learn_threshold()` reads `config.json` once per scan, per naming and per
notification; `load()` and `learn_threshold` each fall back to 0.40 on a bad
value; `_clean` refuses anything outside 0.30–0.60. The table is honest
about strangers and says so on the page; it is **not** honest about near
copies: leave-one-out removes cosine ≥ 0.9999, but the views of one event are
consecutive frames of one face, and they vouch for each other. Production's
table has no wrong answer from 0.30 to 0.60, while the two residents' closest
pair is 0.313 (ARCHITECTURE 10.14): the low end of the table is exactly where
a leave-one-**event**-out could differ. Views do not record their event, so
**R55** records it and makes the table — this one and the dogs' to come —
leave the whole event out.

**R53 step 1, run again.** DINOv2 and MobileNet on the M900: 103/103 by day
and 46/46 at night for both, 123 and 12.8 ms a crop, every person crop at
the 95th percentile of right answers or beyond — the developer's numbers.
The bench's labels and its copy detection (the 16×16 grey thumbnail found the
four gallery views that are two-dog sighting crops) were read in the code.
**The choice for step 2 is DINOv2-small** (ARCHITECTURE 20): tied on every
measurement; its features are trained without labels to tell images apart,
where MobileNet's pooled layer is trained to put a breed into one class — the
wrong prior for two dogs of one breed in some other house; its licence covers
the weights; and ~150 ms is below today's GrabCut. The plan is BACKLOG 3.

**The page, at phone and desktop width.** The test copy at 375 px: the Dogs
tab two columns (171.5 px each), no horizontal scroll (`scrollWidth` 375);
tapping two photos brings up the selection bar at the bottom with a name
field, Save, Bad detection and Clear; Settings → Detection's new panel fits
(the table 301 px of 301) and, with no named views, shows thirteen rows of
0/0 under "Name at least two photos". At 1024 px: Detection's two panels side
by side, Dogs five columns. **Two UX decisions (backlog 39):** an unnamed
card at 375 px is 309 px tall, its caption 137 px of it — the name, a name
form and "Bad detection" — which the selection bar already does for one photo
or many, so on a phone the card keeps only its photo and name; and the
accuracy table is hidden while nothing is measured.

**Closed: R42.** Its text as it was open:

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
counts a dog as a second person (R18), one extra message. **Decided by the
user, 14/10/2026: (b).** "If it errs, it errs": someone hiding beside a
resident must reach the phone, so a person the system cannot account for
always wins over silence in Home (CONTEXT 3).

**Documentation.** ARCHITECTURE 7.14, 8.4, 10.2, 10.15 (new), 17.17 (new),
19.2, 20, 22.2 and 22.3; CONTEXT 3, 9 and 10; PYTHON 43; BACKLOG 1, 2 and 3;
PENDING; HISTORY 8; `.claude/launch.json` added so the built-in browser
starts the test copy by name.

**The deploy, rolled back — the cameras, not the release.** `production.ps1
-Action update` at 16:39: every file read before (977 events, 206 face and
413 dog sightings, 18 reports), no model to fetch, the service stopped,
`v2026.10.14.3` checked out and every file read again — then both cameras
"FAILED - Timed out" at the start, so the health check (every camera with a
frame under 5 s old, 90 s to get there) failed, and the script rolled back to
`v2026.10.14.2`, where both timed out the same way. Production's last event
was at 16:32:20, so the cameras left between 16:32 and 16:39. Read at 16:45:
neither camera answers ping or port 554, neither is in the ARP table, and a
sweep of 192.168.0.1–254 finds no host with RTSP open — so no new address
either; the M900 is on `KankuroNet_5G` since 09:53 with no disconnection,
reaches the router and the internet, and sees `KankuroNet` (2.4 GHz, the
cameras' band) at 100 %. Both cameras gone at once points to their power or
their side of the Wi-Fi, which only the user can look at; a push went to the
user's phone at 16:48, and Telegram already had the script's "update FAILED;
rolled back" message. The release does not touch capture (`capture.py` and
`cameras.py` are unchanged in the range), and the test copy started for the
page check, which reads `stream2` beside production as it always has
(INSTALL 9), was stopped before production's 16:32 event. Production keeps
running and retries each camera every 5 s (`RESTART_SECONDS`, ARCHITECTURE
5.8), so frames come back on their own with the cameras; the same tag is
deployed then.

**What it was, and the 18 hours after (15/10).** The user, the next day: a
power cut, and the computer was off too. Windows' System log tells the rest.
The M900 lost power at 17:13:30 ("the previous system shutdown … was
unexpected"); it came back at 21:47:33, on its own; production's boot task
started the service, and both cameras were "ok" at 21:48:10. **At 21:48:26
the M900 went to sleep**: event 187 names `winlogon.exe` calling
`SetSuspendState`, event 566 gives the reason `ScreenOffGracePeriod`, and
event 42 "Sleep Reason: Application API". Nobody was logged on — the machine
had booted by itself — so it sat at the sign-in screen, whose display turns
off after a minute, and Windows put it to sleep, although its own "sleep
after" on mains power is "never" (`STANDBYIDLE` AC 0). It slept until 15:58
on 15/10, when someone woke it ("the system has returned from a low power
state", the clock jumping from 21:48 to 15:58): **18 hours with no
recording and no message**, and Telegram's commands back at 15:59. A
scheduled task running as the user without a logon (`S4U`, boot trigger)
keeps nothing awake. Which hidden power setting makes the sign-in screen
sleep is for the user to decide and test (`PENDING.md`): it is a system
setting, never changed by Claude. `v2026.10.14.3` was deployed at 16:05 with
`production.ps1`: every file read before and after (977 events, 206 face
and 413 dog sightings, 18 reports), no model to fetch, about 10 s stopped,
both cameras "ok" 3 s after the start.

Two things the outage showed. **Nothing in the log** says a camera was lost:
from 16:32 to the shutdown at 16:39 there is no line, and a running service
whose ffmpeg restarts every 5 s writes nothing — backlog 2's gap ("if a camera
dies at 3 a.m., nothing warns"), now with a real case for the user. And
**`production.ps1` stopped a production whose cameras may already have been
down**, rolled back for a fault that was not the release's, and ended with
"Running again: False" about a service that was running: **R57**.

### 13.27 Review 26 — developer session 24 (15/10/2026)

Developer 24 reviewed whole (`bd44c66..756ac12`: four code commits and the
HANDOFF; 25 files besides it, +738 −219, of which tests +287). 296 tests
pass (284 before), the one that runs the real DINOv2 file included; no
comments in `src/` and `tools/`; `check_data` reads every file, both dog
galleries among them; `check_doc_refs` exits 0. **No code fix.** One
installer message corrected: `install.bat` said the models were ~73 MB,
stale since R49; they are ~340 MB. R53, R56 and R57 closed; nothing
opened.

**R53 step 2, read against the plan's six points** (BACKLOG 2 as it was).

1. **The file.** Downloaded at a pinned commit and kept only with its
   SHA-256. The review asked Hugging Face's API for that commit: the LFS
   SHA-256 of `onnx/model.onnx` is the pinned one, 88,532,934 bytes, and
   `base_model` is `facebook/dinov2-small`; the M900's copy hashes the same.
   The repository's card states no licence; the weights are Apache-2.0, and
   a format conversion carries their terms (ARCHITECTURE 20). The check
   against the developer's own export passed: cosine ≥ 0.99999988 on all
   167 bench crops, where the plan asked 0.9999.
2. **The descriptor** is the bench's, on the crop that is also stored as
   the view's photo; `is_infrared` still judges the region before it is
   shrunk. Two `Network` objects, each with its lock. **Lock order checked:**
   `describe` finishes before any gallery lock is taken, and the migration
   and Undo describe before `_GALLERY_LOCK` too, so no thread holds a
   network's lock while waiting for the gallery's or the reverse — the
   faces' deadlock rule (PYTHON 41) holds.
3. **Distance and thresholds.** `match`, `guess`, `_absorb` and backlog
   28's `replaced_view` (through `distances`) all go through the two
   functions; `distance` is `None` across sizes, so a histogram left
   anywhere is never compared with an embedding. Sure (0.33, 0.6) sits
   under the 0.337 the plan named as its ceiling; probable (0.39, 0.8)
   0.059 under the nearest person crop, where the plan asked 0.05.
4. **The migration** is the faces' code, parameterised, not a copy. The
   infrared flag carried from the old descriptor is the right call: it was
   judged on the whole widened region of the frame. **Undo, on real
   reports:** every dog report production holds (18) has 41-number
   entries; two of them, one in today's form and one from 10/10 that kept
   only one crop, were undone on a scratch copy and came back with
   385-number descriptors. The first attempt put the scratch gallery
   outside the project root, and Undo copied one view photo into the test
   copy's `dogs/views/` — `reports._stored` resolves a stored path against
   the project root, as it should for a real gallery; the photo was
   referenced by nothing and was removed, and the check was run again with
   the root pointed at the scratch folder. Production was only read.
5. **Everything that reads dogs** keeps working: `check_data` checks each
   file at its own size, Waiting included; the tools that write the gallery
   migrate first; the histogram code lives on only in `dog_bench.py`.
6. **Measured**, all on the M900: the migration of production's copy (205
   of 205 views, 29.5 s), `identify` in the live loop, the sweep, and where
   the thirteen misfiled views land (ARCHITECTURE 20).

**The live loop, the developer's question.** `identify` costs 121 ms a dog
and 243 ms for two, against the histograms' 37 and 72 ms there: GrabCut's
cost follows the box, and a dog in a 960×540 frame is small. Review 25's
reason for DINOv2 said "~150 ms is below today's GrabCut" — true of the
bench's 320 px crops, not of the live loop; ARCHITECTURE 20 now says so.
The cost is paid once per dog event, the loop takes the newest frame
(ARCHITECTURE 5.4) so nothing queues, and the first message's dog name is
the point of paying it there. **Accepted**; moving it off the loop would
delay the name or need a second message. One corner, recorded and not a
recommendation: on a machine whose `models/` lacks the file and that has no
dog gallery to migrate, the first dog makes `Network.embed` download 88.5
MB inside the analysis loop. `install.bat` (through `faces.ensure_models`)
and `production.ps1` fetch it ahead, and the startup migration does on any
machine with a dog gallery, so only a machine that never saw a dog and was
installed before this release meets it, once.

**The developer's other questions.** The ~30 s migration at the first
start runs inside the 90 s health check (the deploy measured it, below).
The rule "rebuild when the old file changed" drops what the new version
learned if an older one ran in between — inherited from the faces, where
it was decided (ARCHITECTURE 10.14), and accepted for dogs the same way.
The thresholds rest on a leave-one-out that keeps a view's own event —
R55, planned next. R57 refusing when production does not answer at all is
right: an update is not the tool to revive a dead service, and `-Force`
is there, named in the refusal. R56's text without ", best view" is right:
the words were only true of the old picture. `dogs.migrate_gallery`
calling `faces.migrate_gallery` by attribute is now in ARCHITECTURE 10.14.

**R56 and R57, read.** `_consider_view` keeps the frame each time the count
**rises**, so the frame kept is the first with the most people;
`.people.jpg` is written only when `most_people` ≥ 2, which is the only
case the message can fire (it needs more people than at least one face);
the best view stays the fallback; the archive moves `base.*`, so nothing
had to learn the new file. In `production.ps1`, the refusal comes before
`CheckData`, `FetchModels`, `Hold` and `StopService`, so "nothing was
changed" is literally true; `$back` starts as a reason, so a rollback that
throws before its health check still says what happened.

**The page, at phone and desktop width.** The test copy at 375 px: an
unnamed dog card is its photo, "Unnamed dog" and its count of views; the
hint reads "Tap photos to select them, then name or report them below.";
one tap brings the bar with the name field, Save, Bad detection and Clear;
Settings → Detection's face table is hidden with nothing measured, its
sentence kept; no horizontal scroll (`scrollWidth` 375). At 1024 px every
unnamed card keeps its name form and "Bad detection", the long hint shows,
the phone hint does not. The test copy was stopped with `--stop` after the
check; the two ffmpeg left running were production's.

**PYTHON 44** corrects one line of the HANDOFF: DINOv2-small's patches are
14 px, a 16×16 grid of them at 224 px — not 16 px patches.

**Documentation.** ARCHITECTURE 2 (the diagram and the cost table), 3,
8.4, 10.2, 10.14, 17.17, 18.7, 19.2, 20, 22.1 and 22.3; CONTEXT 3, 9 and
10; INSTALL 3; PYTHON 44; PROCESS 2.4, 3.2, 3.3 and 6; BACKLOG 1, 2 and 3;
PENDING; HISTORY 8, 13.2, 13.4 and 14.3.

**The deploy.** `production.ps1 -Action update` at 16:52: the new
first step found both cameras delivering frames; every file read before
(979 events, 206 face and 413 dog sightings, 18 reports); `FetchModels`
downloaded `dinov2_small.onnx` and the hash matched, before anything
stopped; the service stopped at 16:53:11, the new version read every file
again, and on its first start **migrated production's dog gallery: 46
entries, 205 of 205 views kept, 21.7 s**, its line in `logs/jarvis.log`
after the log file opened, the backup in
`backups/dogs_dinov2_small_20261015-165321`; both cameras "ok" at 16:53:46
— about 35 s stopped, the migration inside it. `gallery.json`'s SHA-1 is
the backup's, untouched. `-Action check` afterwards reads both dog
galleries, 46 dogs each.

**What the new model says about production's own photos.** The 44 unnamed
dogs, read from the running service's Dogs list a minute after the start,
grouped by their "Looks like" guess and laid out on one contact sheet: **22
guessed Aurora, and all 22 are the white dog; 17 guessed Mirana, and all 17
are the black dog**; 5 have no guess — two crops of a person, one crop
holding both dogs, and two of the white dog that it would not name. Under
the histograms the same list was three groups of 18, 10 and 16
(ARCHITECTURE 17.17). Not a measurement with labels — the photos are
unnamed — but the first look at the model on photos the bench did not
label.

**Closed: R53, R56 and R57.** Their texts as they were open:

**R53 — The dogs' identity rests on colour histograms, which overlap (high,
the user's report, review 23).** The user sees Mirana among Aurora's views
and a person among Mirana's. By leave-one-out with `dogs.distance`, 6 of
Aurora's 40 chosen views and 5 of Mirana's sat closer to the other dog than
to their own; at night both are grey, and a crop holding both dogs, or a
person's dark shoes, describes as whichever colour its fur mask caught.
Step 1 (`bed651d`) benched learned embeddings; step 2, decided in review
25, replaces the histograms with DINOv2-small: the model downloadable by
production with a pinned SHA-256 and checked against the local export; the
stored crop padded square, 224 px, ImageNet-normalised, no GrabCut; two
`cv2.dnn.Net` objects; 1 − cosine, thresholds from the bench; the
migration to `dogs/gallery_dinov2_small.json` as the faces', with Undo
describing pre-switch reports again; every tool that reads dogs kept
working; measured on a copy of production's `dogs/`.

**R56 — The hidden person's picture is the best single view (low, review
25).** R42 (b)'s message says "2 people seen, 1 face found, best view", and
the picture is the event's best view — chosen by one person's confidence ×
height, so it may be the resident alone. Then: when `most_people` rises,
keep that frame with the person boxes drawn, as an optional
`HH-MM-SS.people.jpg` beside the event, and send it instead of the best
view for the hidden-person message only. Additive.

**R57 — An update with the cameras already down (low, review 25).** At
16:39 on 14/10 both cameras had left the network. `Update` never asked
whether the cameras deliver frames, so it stopped production, failed the
health check on cameras no release could reach, rolled back, failed again,
and ended with "Running again: False" while the service was running. Then:
read `/api/status` once before `Hold` and `StopService`; refuse unless
`-Force`; let the failure messages say which part failed.

### 13.28 Review 27 — developer session 25 (15/10/2026)

Developer 25 reviewed whole (`8ba7da3..e700b05`: two code commits and the
HANDOFF; 12 files besides it, +768 −105, of which tests +290). 313 tests
pass (296 before); no comments in `src/` and `tools/`; `check_data` reads
every file; `check_doc_refs` exits 0. **No code fix.** R55 closed, backlog
32 done for both halves; nothing opened.

**R55, read against the plan.** The event is keyed by the view's photo name,
never by position, so an older version's moves cannot misalign it; the
review read every path that moves a view. Inside an entry (demote, promote,
spread, the 40-view rule) the photo stays, and so does its key; `_merge`
carries the source's keys; `take_out` returns the entry whole, keys
included, so a report's Undo puts them back; `save()` prunes keys whose
photo left. A view moved by a path that does not carry its key is found
again by the recovery at the next start, which only ever looks at views with
no key. `faces.event_of` takes the clip's last three parts, and the sightings
store the same clip through `_portable`, so recovered and recorded events
are one string. The dogs' `accuracy` is `match`'s rule computed in one
product per probe: per dog the nearest view, then the two smallest — the
same "second" `match` uses, infinite when one dog has no view in that
lighting.

**The recovery, run again by the review** on its own copy of production's
`faces/` and `dogs/` (`cp -p`, times kept; `C:\JARVIS` only read): faces
81 by the same picture and 57 written together, dogs 205 by the same
picture, none unknown — the developer's numbers — and the face table the
same, 69 / 60 / 39 / 15 named for sure at 0.30 / 0.35 / 0.40 / 0.45, no
wrong answer.

**The developer's first question: overlapping events.** Of the 69 views
named for sure at 0.30, 8 found their nearest reference in an event of the
same camera less than 180 s away — four reciprocal pairs, 37, 153 and 165 s
apart; only the first is a pre-roll overlap, the others the person coming
back. Leaving those neighbours out as well: 60 → 59 at 0.35, 39 → 36 at
0.40, 15 → 11 at 0.45, still no wrong answer; the dogs have no such pair.
Too small to change the rule (ARCHITECTURE 10.15).

**The mtime rule.** It is the only evidence for 57 face views, and it holds
on production's own files; production's first start of this release is the
moment it counts, and its log line is read below. Recorded as the rule's
weakness in ARCHITECTURE 10.16.

**The unnamed column leaves out exact copies and its own event too.**
Accepted: an unnamed view meets the gallery, in use, as a new visit would —
without twins of its own visit.

**The test copy's dog gallery recovered at 17:04:42.** The test copy's log
has no start between 16:42 and 17:11, and the 17:11 start logged no
recovery for either gallery, so something outside the service ran the new
code on the test copy's galleries before it — most likely one of the
developer's measurement runs. It wrote what the next start would have
written, on the test copy's data. Not pursued.

**Read and left as they are.** `guess` reads `config.json` once per unnamed
entry of the Dogs list (60 at most, microseconds each), within the plan's
"once per operation". `_Reference` turns a zero descriptor into distance
1.0 where `dogs.distance` says `None`; DINOv2 never returns one.

**The page.** The test copy has no named dog, so the review served
production's table (computed on its copy) to the test copy's page in the
built-in browser: at 375 px the dog table is 301 px in a 335 px panel, no
horizontal scroll, Day and Night with the share beneath; at 1024 px the dog
panel sits in the left column, the face panel in the right. The explanation
above each table is long on a phone (about 13 lines); it reads as the
faces' does, and stays.

**The deploy, 17:27.** `production.ps1 -Action update`: every file read
before and after (979 events, 206 face and 413 dog sightings, 18 reports),
the service stopped about 11 s, both cameras ok 3 s after the start. The
first start logged the recovery — faces `{'same picture': 81, 'written
together': 57}`, dogs `{'same picture': 205}` — the copy's numbers, on the
original files. Production's own `/api/accuracy/faces` and `/dogs` gave the
tables above: 39 of 80 at 0.40; 44 + 9 at 0.33; no wrong answer, no unknown
event.

**Closed: R55.** Its text as it was open:

**R55 — The accuracy tables leave out only exact copies (medium, review
25).** Backlog 32's table, and R53's bench, leave each view out with its exact
copies (cosine ≥ 0.9999 for faces), but the views of one event are
consecutive frames of the same face or dog, and they vouch for each other: a
probe's twin from its own event is still among the references. Production's
face table has no wrong answer from 0.30 to 0.60, and the two residents'
closest pair is 0.313 (ARCHITECTURE 10.14), so the low end, where the user
would lower the threshold, is where a leave-one-**event**-out could differ.
Views do not record their event; sightings do (`clip`). **Then:** record
each view's event, additively and keyed by the view's photo — for instance
`view_events: {"<12hex>.jpg": "Front/2026-10-14/12-00-00"}` in the entry —
so no move by an older version can misalign it; recover the event of the
views stored before, by matching each view photo to its sighting crop (the
16×16 grey thumbnail of `dog_bench.py` found such pairs); and make
`faces.accuracy`, and the dogs' table to come, leave out every reference of
the probe's event. Views whose event cannot be recovered fall back to
today's rule and are counted on the page. Measure on production's galleries
the table before and after.

### 13.29 Review 28 — developer session 26 (16/10/2026)

Developer 26 reviewed whole (`a672890..655faa6`, two commits: the tool and
the HANDOFF; `tools/person_signals.py`, 181 lines). No program code
changed, so no tests run and no release; no comments in `src/` and
`tools/`; `check_doc_refs` exits 0. **No code fix.** R59 and R58 measured,
no rule built — both wait for tracking (backlog 7); R60 opened from the
architect's reading of production's log the same afternoon; backlog 7 and
40 decided by the user.

**The tool, read.** It only reads: `DogGallery(path)` loads the file and
writes nothing on construction (`faces.Gallery.load`), and the clips are
decoded by `replay.frames`. Three `SubjectDetector`s share one wrapped
network (`Recording`, PYTHON 46); each moving frame forces its detector's
run (`last_run = -inf`), so `network.output` is always that run's. The
relabelled boxes are found in the detector's own trace by the same reasons
`replay.py` prints. A box's DINOv2 distance is against whatever gallery is
named; the developer used a copy of production's taken at 16:20.

**The ground truth, checked.** The four events with `most_people` ≥ 2 in
production's JSON since R42 (b) are the four the HANDOFF lists, each with
its `.people.jpg`; none is two people. The cause the developer found —
YOLO drew every dog's `person` box — matches the architect's reading of
the sent pictures that opened R59 (ARCHITECTURE 22.3). The crops
themselves — the 37 dog boxes, the night person crops nearest a dog — were
looked at by the developer, not again by the review.

**The decision.** Both rules fail the plan's condition, which is the
user's (CONTEXT 3): R59's per-event zoom would lose a person crouching
behind the car at night, R58's rule (a) a person standing behind another,
and neither has a true case to show it keeps one. Building nothing was
right. Both are answered by the tracking the user asked for today: a
track's label voted over its frames, and a count of tracks — the
HANDOFF's own suggestion.

**What the documentation claimed and was wrong.** ARCHITECTURE 22.3 said
NMS and `drop_duplicates` remove two boxes on one body before anything is
counted; nested boxes survive both (IoU 0.33–0.43). Corrected.

**Also today, outside the review** (the same conversation, before the
handover): the user's two requests — follow the body once a face names it,
and notifications that never lose a risk and never shout — measured on
production's log and written as backlog 7 and 40; reading `notify._faceless`
for item 40 found that the cooldowns drop what they block (R60).

### 13.30 Review 29 — developer session 27 (16/10/2026)

Developer 27 reviewed whole (`0cf58f9..7670811`, four code commits and the
HANDOFF: `notify.py` rewritten around the incident, `outage.py` new, the
tenth case in `modes.py`, the camera watch started in `cameras.main`, the
page's field, 34 new tests, `tools/replay_notifications.py`). 328 tests
pass, `check_data` reads every file, no comments in `src/` and `tools/`,
`check_doc_refs` exits 0. **No code fix; release `v2026.10.16`.** R60
closed, R61 opened.

**R60 as it was opened (review 28).** `notify._faceless` sent a held
person's only message when the camera's cooldown ran out, and otherwise
logged "no face: skipped: cooldown" and returned: nothing reached the
phone. So in Home a stranger whose clip came within `notify_cooldown`
(120 s) of any message sent on that camera — a resident's faceless message,
a dog — was lost, against CONTEXT 3; a face inside its person's cooldown
was dropped the same way. Seen in production only on the residents' own
walks (`00:01:35`, `00:03:17` on 16/10), but nothing in the code told those
from a stranger. Reproduced by the developer's test first: at the commit
before, the second held person returned 0.

**The rule, read against the design** (backlog 40, section 8). Every
sending path — `event`, `faces_seen`, `side_face`, `best_view`,
`hidden_person` and the new `camera_down` — asks `_loud`, and none drops a
message; `_cooled_down`, `_claim` and `_last_sent` are gone, and
`_faceless` no longer checks a cooldown. `event()` decides before it starts
its thread, so two events a frame apart cannot both ring. `_loud` reads
`_incident["camera"]` only when `fresh` and `force` are both false, and
only then is the key there — Python's `or` stops at the first true
operand; it holds, though a reordering would raise `KeyError`.
`_end_of_floor` copies and empties `held_back` under the lock and sends
outside it; a timer that had already fired and waits on the lock while
`reset_incident` runs finds the list empty and sends nothing. The floor's
text is sent outside `_loud`, so it does not move the incident's camera.

**Measured again, not taken from the HANDOFF.** The replay on production's
log gave the HANDOFF's numbers plus one line written after it ran: 741
messages, 220 loud and 17 floor texts at 120 s; since 15/10 20:00, 97
messages and 39 + 1 rings. In the whole log no send ever failed, and the
densest stretches, now that nothing is dropped, are 2 messages in a second,
4 in ten and 9 in a minute — far under Telegram's limits for one chat, so
sending everything costs no refusals. `capture.py` logs nothing when ffmpeg
restarts, so the log cannot tell how often a camera went silent for a
minute: the watch's lines from this release are the first measurement.

**Looked at and accepted.** While analysis is Off the watch still reports a
camera down: Off stops what is analysed, and the cameras still feed Live
(ARCHITECTURE 12.12). The floor's text keeps the settings of the first
message it names. The incident's camera follows silent messages and the
camera-down text too, so a person on Front right after "Back: no picture"
rings as another camera — right: a new place. In Home the chat receives
about twice what it did (100 against 54 in the last 24 hours) while the
phone rings less (42 against 54): the user's principle chose it, and R59
and R58 — tracking — are what will take the false ones out.

**R61 — three small things in item 40 (low, review 29).** (a) The floor's
text renews `_incident["last_sent"]` even when the incident had already
closed, which can happen only with a quiet window under 30 s: the next
message then belongs to an incident that should have ended. (b)
`tools/replay_notifications.py`'s pattern reads a camera-down line's camera
as `Back:` — its subject is the whole text — so a log from `v2026.10.16` on
counts it as a third camera and a ring. (c) The return text counts minutes
only: the 18 hours the M900 slept on 14–15/10 would read "1080 min
without". **Then:** renew the incident only while it is open; parse the
camera-down lines by their own words; from an hour on, "18 h 5 min
without". Each by a test first.

**The page.** Settings → Notifications in the built-in browser at 375 px
(`scrollWidth` 375 of 375) and about 1000 px: the field reads "Quiet window
of an incident, seconds" with its hint below, and the new row "Camera with
no picture, and its return" is on in Home and Away, off in Silent. The hint
is long for a phone but reads; kept.

**For the next plan: tracking's library on the M900** (backlog 7). The
design named ByteTrack "e.g. through `supervision`": `supervision` 0.31 no
longer has it; Roboflow's `trackers` 2.6.1 (Apache-2.0) does,
`ByteTrackTracker`, with SORT, OC-SORT and BoT-SORT beside it. It needs
`supervision` (MIT), `scipy`, `matplotlib`, `av` (PyAV, with FFmpeg's
libraries, BSD) and `pillow` — no second OpenCV: `supervision` falls back
to numpy when none is installed, and the project's `opencv-python`
satisfies it. In a throwaway environment with the signed python.org
Python, every one of them imported under Smart App Control; **the first
import took 89 s**, Smart App Control's first look at each new DLL, and the
next 4.2 s. One update with two boxes costs 0.35 ms. Its defaults are not
this project's: a box under `track_activation_threshold` 0.7 starts no
track, so the second test box, at 0.6, got none.

### 13.31 Review 30 — developer session 28 (16/10/2026)

Developer 28 reviewed whole (`0d4eeab..dccf519`: R61 in `notify.py`,
`outage.py` and `replay_notifications.py`; `trackers` added and
`production.ps1`'s `WarmUp`; `tools/replay_tracks.py`; 10 new tests). 338
tests pass, no comments in `src/` and `tools/`, `check_doc_refs` exits 0;
nothing read from or written to disk changed. **No code fix; release
`v2026.10.16.2`.** R61 closed. Plan step 4, recording tracks live, was not
reached: the developer stopped after step 3 at 83 % of the window, as the
plan allowed.

**R61, read against its tests.** `_end_of_floor` renews the incident only
when `last_loud − last_sent < quiet`, the exact negation of `_loud`'s
`now − last_sent >= quiet` that opens a fresh one, so the two agree on when
an incident is open; the test fails at the commit before (one timer, the
third message silent) and passes after (a second timer: it rang). The
replay's camera lines now drop the colon only when the text starts with the
camera words, and are forced loud as `camera_down` is live. `_duration`
gives "6 min", "1 h", "18 h 5 min".

**The warm-up, read and partly run.** Every release tag, 40 of them, holds
`.python-version`, so `git archive` of the three paths cannot fail on a
missing one. `Invoke-ProdGit` throws on a non-zero exit, `Expand-Archive`
stops on its own, and the catch only warns. The import loop, run here on
the test copy's environment (with the two dev packages): 55 top-level
modules, none failing, 8.1 s; `trackers` pulls `scipy.optimize`, so the
Hungarian algorithm's DLL is among those warmed. Accepted: a module that
prints when imported would add lines to the "imported in N s" message.
**One explanation corrected.** The HANDOFF said `uv` hardlinks from its
cache, so the real `.venv` would land the very files Smart App Control had
just seen. `pyproject.toml` has `link-mode = "copy"` since the move to
`src/` (ARCHITECTURE 3.1): every sync copies. The measurement stands — a
fresh `.venv` of already-seen files imported everything in 9.1 s against
89 s the first time ever — so what Smart App Control remembers follows the
bytes, not the file, and the warm-up works for that reason. ARCHITECTURE
18.7 says so. The update path itself runs for the first time with this
release.

**The tracker, read in its source.** `trackers/core/bytetrack/tracker.py`
spawns every new track with `tracker_id` −1 and allocates the id at its
next match, whatever `minimum_consecutive_frames` says — the developer's
first limit, confirmed. The tool's parameters are this project's
(ARCHITECTURE 7.16's table) and its `--join` timeline may be off by up to a
segment, which does not change (c): gaps of 7–9 s defeat a constant-velocity
prediction at any buffer. Its reading of (a) counts an untracked person box
as a person, the safe side. **The plan for part 2 changes from these
numbers:** the vote alone clears two of seven dog events in some phases;
the first box joined to its track and a run of person frames must be
measured first (BACKLOG 3).

**Not looked at:** the page did not change.

## 14.3 Usage log

Every session's row: what it covered and what it cost. How to measure is
`PROCESS.md` 4; until 12/10/2026 the newest rows lived in the 14.3 section
of `CONTEXT.md`.

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
| D13 | developer | high | 12/10 10:58–11:17 | session 13: backlog 25 (a)–(f), R41 (158 tests) | 6% → 23%: (a)–(d) 9, (e) 3, (f) 2, R41 3 | 90% → 92% | 73k → 252k tokens, a new conversation |
| A19 | architect | ultracode | 12/10 11:17–11:30 | review 15, one code fix, docs, script 12, release and deploy `v2026.10.12` | 25% → 34% | 93% → 94% | 108k → 215k tokens, a new conversation |
| A20 | architect | ultracode | 12/10 11:30–12:45 | R33 and R10's documents, asked by the user: CONTEXT cut to a brief (1632 → 740 lines) and `HISTORY.md`; README, INSTALL, PYTHON (1–22) and ARCHITECTURE (1–17.7, ~2,400 lines) in English; ARCHITECTURE reorganised by subject; every cross-reference checked by script | 34% → 54% | 94% → 97% | 215k → 443k tokens, the same conversation. **Translating ~4,000 lines cost about 20 points of the window and 2 of the week** — far less than feared |
| A21 | architect | ultracode | 12/10 afternoon–evening | the user's three requests: the 6 dog reports read and measured (two YOLO replays, 644 boxes; HISTORY 13.16), R44, backlog 26 and 27 designed, developer 14 planned and started | 54% → window reset → 4% | 97% → 0% (the weekly read 0 % at the end, its reset still shown for 14/10) | 443k → 490k tokens, the same conversation |
| D14 | developer | high | 12/10 evening | session 14: R44, backlog 26 and 27, R43 (174 tests) | 6% → 22%: R44 + 26 12, 27 2, R43 and HANDOFF 2 | 1% → 3% | 68k → 212k tokens, a new conversation |
| A22 | architect | ultracode | 12/10 20:07–20:50 | the user's question, clear or compact: "clear, not compact" and `PENDING.md`; review 16, release and deploy `v2026.10.12.2`, raid log 13; CONTEXT split into CONTEXT, PROCESS and BACKLOG (the developer's resume ~10.3k → ~8.0k tokens, the architect's ~11.1k); developer 15 planned and started | 12% → 40%, shared with developer 14 until 20:17 (22% at its end): about 17 points for this session | 2% → 6% | 72k → 280k tokens, a new conversation |
| D15 | developer | high | 12/10 20:46–21:08 | session 15: R10's file names and the tools' text, `check_doc_refs.py`, R45 (176 tests) | 42% → 49%: R10 6, R45 1, HANDOFF under 1 | 6% → 7% | 70k → ≈175k tokens, a new conversation |
| A23 | architect | ultracode | 12/10 21:08–21:25 | review 17, HANDOFF integrated, `check_doc_refs.py` to 0, PYTHON 32–34, raid log 14, release and deploy `v2026.10.12.3`, developer 16 planned | 51% → 60% | 7% → 8% | 68k → 205k tokens, a new conversation |
| D16 | developer | high | 12/10 night | session 16: the shim removed, R7 (`tools/check_python.ps1`) | 60% → 61% | 8% → 9% | ≈81k tokens at the end, a new conversation |
| A24 | architect | ultracode | 12/10 21:28–21:40 | review 18, one installer message, HANDOFF integrated, PYTHON 35, raid log 15, release and deploy `v2026.10.12.4`; no plan left to hand over | 62% → 68% | 9% → 9% | 68k → 165k tokens, a new conversation |
| A25 | architect | ultracode | 13/10 21:26–22:15 | the user's six requests and one idea: 18 dog reports read (a contact sheet), five reported clips replayed, the galleries' redundancy and the face and dog accuracy measured by leave-one-out; four questions answered; backlog 28–33, R46, competitors table; developer 17 planned and started | 3% → 12% (new window) | 10% → 11% | 167k → 250k tokens, review 18's conversation |
| D17 | developer | high | 13/10 night | session 17: R46, backlog 30 and 29 (208 tests) | 12% → 21%: R46 ~4 (two 7-minute replays), backlog 30 ~2, backlog 29 ~3 | 11% → 12% | 70k → ~190k tokens, a new conversation |
| A26 | architect | ultracode | 13/10 22:14–22:30 | review 19: three replays (one R46 clip, two true dogs), HANDOFF integrated, ARCHITECTURE 7.13 and 22.7, PYTHON 36–37, R47, raid log 16, release and deploy `v2026.10.13`; developer 18 planned and started | 23% → 32% | 13% → 14% | 92k → 205k tokens, a new conversation |
| D18 | developer | high | 13/10 night | session 18: backlog 28 — the rule, the vectorised dog matrix, `settle_waiting.py` (216 tests) | 34% → 40% | 14% → 15% | ~163k tokens at the end, a new conversation |
| A27 | architect | ultracode | 13/10 22:36 – 14/10 10:15 | review 20: production's galleries copied and settled, three recognition measurements, contact sheets of 146 faces, R48; HANDOFF integrated, PYTHON 38; no release; developer 19 planned. The connection dropped overnight mid-measurement and the session resumed in the morning | 42% → unknown at the drop; 0% → 7% in the new window | 15% → 17% | 91k → about 230k tokens, a new conversation |
| D19 | developer | high | 14/10 morning | session 19: backlog 31 — three minimums in Settings, read without a restart (234 tests) | 7% → 14% | 17% → 18% | 125k tokens at the end, a new conversation |
| A28 | architect | ultracode | 14/10 10:05–10:40 | two questions from the user (where the work stands, the decisions waiting), then review 21: three clips replayed old against new, the user's objection to R48 measured — cross-person similarity, a contact sheet, leave-one-out without the five head-tops, three quality cues — R49; the EPUB list; the user's answer: R49 first, better models allowed — CONTEXT 3 reopened, production's faces copied, developer 20 planned | 14% → 25% (the questions before the review cost under a point) | 18% → 19% | 84k → 208k tokens, the conversation the user opened this morning |
| D20 | developer | high | 14/10 morning | session 20: R49 step 1 — `tools/face_bench.py`, eleven pipelines measured, AdaFace and MagFace exported to ONNX once | 25% → 35% | 19% → 21% | 188k tokens at the end, a new conversation |
| A29 | architect | ultracode | 14/10 11:05–11:20 | review 22: `face_bench.py` read against insightface's code, the baseline and SCRFD + ArcFace run again, the alignment measured three ways, the unnamed entries matched and a contact sheet, the licence read; HANDOFF integrated, ARCHITECTURE 10.14, PYTHON 40; no release; the user's two answers, the release assets read, developer 21 planned and started | 38% → 50% at the commit | 21% → 22% | 97k → 246k tokens, a new conversation |
| D21 | developer | high | 14/10 late morning | session 21: R49 step 2 — R100 measured, SCRFD + ArcFace R50 in `faces.py`, the gallery migration, `downloads.py` and `FetchModels` (240 tests) | 50% → 66% | 22% → 25% | about 245k tokens at the end, a new conversation |
| A30 | architect | ultracode | 14/10 11:50–12:25 | review 23: the diff read whole, `FetchModels` fixed and probed, production's gallery migrated again, the scan-against-photo gap and the wrong-best matches measured on four clips, backlog 28 settled on the ArcFace copy; HANDOFF integrated, PYTHON 41, raid log 17; release and deploy `v2026.10.14`; the user's request recorded as backlog 34; no handover (the window at 85 %) | 67% → about 86% | 25% → 27% | 67k → about 300k tokens, a new conversation |
| D22 | developer | high | 14/10 15:00–15:35 | session 22: backlog 34, 35, 36, R52, R51 (measured leave-clip-out), R30 (b) (measured on production's clips) (269 tests) | 0% → 24% (new window) | 28% → 31% | about 250k tokens at the end, a new conversation |
| A31 | architect | ultracode | 14/10 15:37–16:05 | review 24: the diff read whole, the page at 375 and 1280 px in the built-in browser, the slider's round trip, production's gallery, log and misfiled dog views read, backlog 37 designed from production's counts, R54; HANDOFF integrated, PYTHON 42, raid log 18; release and deploy `v2026.10.14.2`; developer 23 planned | 26% → 41% (the measurements, the page check and backlog 37's design cost more than a plain review) | 31% → 33% | 96k → about 265k tokens, a new conversation |
| D23 | developer | high | 14/10 afternoon | session 23: R42 (b), backlog 37 (a, b) and 38, R53 step 1 — `tools/dog_bench.py`, three models exported to ONNX once — backlog 32 for faces (284 tests) | 40% → 60% | 33% → 2% (the weekly window reset at 19:00 UTC mid-session) | 76k → about 285k tokens, a new conversation |
| A32 | architect | ultracode | 14/10 16:20–16:55 | review 25: the diff read whole, the page at 375 and 1024 px in the built-in browser (the test copy started from the new `.claude/launch.json`), R53's bench run again for two models, production's misfiled dog views read; HANDOFF integrated, ARCHITECTURE 10.15 and 17.17, PYTHON 43, raid log 19; R53 step 2 decided, R55–R57, backlog 39; release `v2026.10.14.3` tagged and its deploy rolled back on a camera outage, diagnosed (ping, ARP, a subnet sweep, the Wi-Fi events) and pushed to the user's phone; no handover (a deploy rolled back, the window at 82 %) | 61% → 82% (the diagnosis of the outage cost about 4) | 2% → 5% | 74k → about 320k tokens, a new conversation |
| A33 | architect | ultracode | 15/10 16:00–16:10 | resumed after the power cut, in review 25's conversation: production's 18 silent hours traced in the System log (a sleep by `winlogon.exe` at the sign-in screen 50 s after the boot), two live frames checked, `v2026.10.14.3` deployed; PENDING and HISTORY 13.26; developer 24 started | 6% → about 12% (new window; the conversation was already ~320k) | 6% → 6% | 321k → about 360k tokens |
| D24 | developer | high | 15/10 16:10–16:40 | session 24: R53 step 2 — DINOv2-small, the pinned download, the dog migration — backlog 39, R56, R57 (296 tests) | 12% → 33%: R53 step 2 12, backlog 39 4, R56 2, R57 and HANDOFF 3 | 6% → 9% | about 309k tokens at the end, a new conversation |
| A34 | architect | ultracode | 15/10 16:40–17:10 | review 26: the diff read whole, the model's hash against Hugging Face, Undo of real reports on a scratch copy, the page at 375 and 1024 px; HANDOFF integrated, ARCHITECTURE 20 rewritten, PYTHON 44, raid log 20; release and deploy `v2026.10.15`, the unnamed dogs' guesses checked on a contact sheet; developer 25 planned and started | 33% → about 56% | 9% → 12% | 105k → about 330k tokens, a new conversation (started by the developer's handover) |
| D25 | developer | high | 15/10 16:55–17:16 | session 25: R55 — `view_events`, the recovery, leave-one-event-out — and backlog 32 for dogs (313 tests) | 56% → 72%: R55 9, backlog 32 for dogs 7 | 12% → 14% | about 245k tokens at the end, a new conversation |
| A35 | architect | ultracode | 15/10 17:17–17:35 | review 27: the diff read whole, the recovery and the face table run again on a copy, overlapping events measured, the dog panel at 375 and 1024 px with production's table served to the test copy; HANDOFF integrated, ARCHITECTURE 10.15–10.16, 19.2 and 20, PYTHON 45, raid log 21; release and deploy `v2026.10.15.2`; nothing planned to hand over | 74% → 84% | 15% → 16% | 74k → 224k tokens, a new conversation (started by the developer's handover) |
| A36 | architect | ultracode | 16/10 15:30–15:50 | the user's report, many notifications in Home: production's log since 15/10 16:00, the 31 sent pictures on a contact sheet and zoomed, the dog gallery tried on the false person boxes, the hold's delay measured, quiet periods simulated; the user kept the rule (CONTEXT 3); R58, R59; developer 26 planned and started | 4% → 10% (new window) | 17% → 17% | 229k → 288k tokens, review 27's conversation |
| D26 | developer | high | 16/10 15:50–18:45 | session 26: R59 and R58 measured — every listed clip replayed in three phases, 588 production events scanned for two people (about an hour, four processes) — `person_signals.py`, no rule built | 10% → 40%, shared with A37 from 16:15 | 17% → 21% | about 232k tokens at the end, a new conversation |
| A37 | architect | ultracode | 16/10 16:15–19:20 | resumed; the user's two requests — follow the body once a face names it, notifications that never lose a risk and never shout — measured on production's log (29 and 33 messages, the cooldown's drops, loud and silent replayed), competitors searched, backlog 7 and 40 written, R60; then review 28, no release; developer 27 planned | 14% → 48%, shared with D26 until 18:45: about 8 points before the review, 8 for it | 18% → 22% | 100k → 270k tokens, a new conversation |
| D27 | developer | high | 16/10 evening | session 27: R60 by a test, backlog 40 — the incident, the floor, the camera watch, the page — and `replay_notifications.py` (328 tests) | 49% → 58% | 23% → 24% | 179k tokens at the end, a new conversation |
| A38 | architect | ultracode | 16/10 19:27–19:50 | review 29: the diff read whole, the replay run again, the log's bursts and failures, the page at 375 and 1000 px, tracking's library probed under Smart App Control; HANDOFF integrated, ARCHITECTURE 12.11–12.12 and 22.2, PYTHON 47, raid log 22; release and deploy `v2026.10.16`; developer 28 planned | 60% → 74% | 24% → 26% | 110k → about 260k tokens, a new conversation (started by the developer's handover) |
| D28 | developer | high | 16/10 evening | session 28: R61 by three tests, `trackers` and `WarmUp`, `replay_tracks.py`, tracks measured on 25 events (item 7 part 1, step 4 not reached) (338 tests) | 75% → 84%, about 45 minutes of it waiting on two replays | 26% → 27% | 82k → about 205k tokens, a new conversation |
| A39 | architect | ultracode | 16/10 23:15–ACEND | review 30: the diff read whole, the warm-up's imports run, every tag checked for `.python-version`, the tracker's first box read in the library; HANDOFF integrated, ARCHITECTURE 7.16, 12.11–12.12 and 18.7, PYTHON 48, raid log 23; release and deploy `v2026.10.16.2`; developer 29 planned | 86% → ACUSE | 27% → ACWEEK | 74k → ACCTX, a new conversation (started by the developer's handover) |
