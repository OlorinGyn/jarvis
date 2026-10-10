# J.A.R.V.I.S. Raid Log — comic script (English)

One issue per release: the architect and the developer talking through what
really happened in that version, simplified. The Portuguese script,
`script.pt.md`, tells the same story panel for panel. The drawing is done
elsewhere, with a tool made for comics.

## Series bible

**Truth rule.** The dialogue is simplified, never invented in substance. Every
boss is a real bug or limit of that version, every ability a real feature,
every Owner quote a real decision of the user.

| Character | Look | Voice |
|---|---|---|
| **J.A.R.V.I.S.** | small round navy robot, one big glowing cyan eye (the app icon), short antenna with a yellow tip, stubby arms and legs | its own log lines, in a dark terminal balloon with cyan monospace text |
| **Front** and **Back** | two flying eye-drones, small navy spheres with a cyan eye and a propeller — the two cameras | none |
| **The Dev** | a beaver in a yellow hard hat | plain white balloons; builds things |
| **The Architect** | an owl with round gold glasses | plain white balloons; works at night, carries a lantern or a scroll |
| **The Owner** | **never drawn**; a voice from outside the panel | gold balloon tagged "THE OWNER" |
| **Bosses** | each drawn as what it is (a gate, a ghost, a clock…) | black balloons, red capital letters |

**Style:** bold black outlines, flat colours, halftone dots, comic lettering.
Night scenes in deep blue; danger in dark red; indoor scenes in warm cream.
Verbatim system output (log lines, error messages, `person 0.72`, the camera
names Front and Back) is lettered exactly as the system prints it.

**Each issue:** a cover, three or four chapters of up to six panels, and a
closing card. It ends on a cliffhanger that the next issue opens with.

---

## Issue #1 — The First Night Shift

`v2026.10.09` · 24 Sep – 9 Oct 2026 · 52 commits · 2 cameras · 1 house

### Cover

Night. A purple house on a hill under a full moon. J.A.R.V.I.S. stands on the
roof ridge, eye glowing. Front and Back hover left and right of the house,
each casting a pale cone of light to the ground, labelled FRONT and BACK. The
owl peeks in from the bottom left, the beaver from the bottom right.
Title: **J.A.R.V.I.S.** — ribbon: **RAID LOG** — badge: **ISSUE #1**.
Band at the bottom: **The First Night Shift**.

### Chapter 1 — The Gate of Signatures

**Panel 1 (wide).** A warm room. The beaver at a desk with a monitor and a
small black tower labelled M900; a coffee mug steaming. On a shelf, the two
drones, asleep, labelled FRONT and BACK.
CAPTION: 24 September 2026. Two Tapo cameras, one Lenovo M900 — and a builder.
DEV: Motion, YOLO, clips… it all runs on the big PC. Now, on the M900—

**Panel 2.** Dark red. A stone gate with iron bars and a blue shield marked
SAC (Smart App Control). The beaver, small, carries a huge orange backpack
labelled PyTorch.
BOSS (the gate): UNSIGNED DLLs SHALL NOT PASS!
DEV: But PyTorch is only two gigabytes…

**Panel 3.** Bright sky, green grass. The PyTorch backpack lies tossed aside
with motion lines. The beaver proudly holds a small green tool labelled
cv2.dnn, sparkling.
DEV: Then we travel light: YOLO through OpenCV's own dnn. No PyTorch at all.

**Panel 4.** Night. J.A.R.V.I.S. at the left casts a pale beam; a swarm of
mosquitoes buzzes inside it.
CAPTION: 26 Sep. The first night outside.
BOSS (the swarm): BZZZ! EVERY WING IS AN INTRUDER!
J.A.R.V.I.S.: Seen for several frames in a row, or it never happened.

**Panel 5.** Night. The gate again, its arch now glowing open. The beaver
holds up a scroll: "python.org — SIGNED: PSF", with a red wax seal. The owl
appears for the first time, beside the gate.
CAPTION: 9 Oct. After nine quiet days, the gate rises again — this time
against uv's own Python.
BOSS (the gate): SIGNED. YOU MAY PASS.
ARCHITECT: First review, first finding: our own chronicle was wrong. Read the
whole log line, not just the word "python".

### Chapter 2 — Eyes, Faces and Paper Planes

**Panel 1.** Dark red. The two drones tug at a single pink brain labelled NET
between them; lightning bolts. The beaver below.
CAPTION: Two threads, one neural net.
BOSS: buf.shape() == m.shape()… CRASH!
DEV: Each thread gets its own brain. Faces wait their turn.

**Panel 2.** Warm room. J.A.R.V.I.S. under a fan of three face cards; the
middle card has a yellow tag: OWNER.
THE OWNER: Name a face once — and know it every time after.
J.A.R.V.I.S.: gallery: merged by name.

**Panel 3.** Night. Two paper planes fly along a dashed line from the house to
a phone. On the phone: a photo with "Front: person", then a face with
"Front 20:23: probably Owner". The owl stands below the phone.
CAPTION: Then the phone learned to ring.
ARCHITECT: Below 0.45 it says "probably". Humility is a feature.

**Panel 4.** Warm room. A big browser window, address
`http://<M900>:8765`, two live tiles (FRONT, BACK) with red LIVE dots, cards
below. The beaver beside it with a wrench.
THE OWNER: I don't want two ways in. Everything on the web, one service.
DEV: FastAPI + MJPEG: the browser is the window now.

**Panel 5 (wide).** Left: another computer, labelled PC 2, its screen red with
"Invalid HTTP request". A dashed red arc labelled https:// with a red X; a
solid green arrow labelled http:// reaching the house on the right, where
J.A.R.V.I.S. stands. The owl in the middle.
CAPTION: From the other computer: an error.
ARCHITECT: Your browser knocked with https://. This house answers http://.
THE OWNER: Typed http:// — it works!

### Chapter 3 — Twins, Oaths and Curses

**Panel 1.** Night. A big J.A.R.V.I.S. with a badge "PROD · stream1 · HD" and
a small twin with a badge "[TEST] · stream2 · 640×360".
THE OWNER: One copy always on guard. Another one to train.
CAPTION: The camera gives stream1 to one viewer — stream2 to many.

**Panel 2.** Daylight. A grey stone tablet engraved GENERATED / FILES /
NEVER / BREAK. The owl with a chisel.
THE OWNER: Never break what an older version wrote.
ARCHITECT: Carved. check_data reads every file before and after each update.

**Panel 3.** Purple dark. A scroll labelled config.json; a ghost rises from it
with "U+FEFF" on its belly. The beaver with a magnifying glass.
BOSS (the ghost): HIDDEN AT BYTE ZERO, I MADE YOUR WHOLE CONFIG VANISH!
DEV: utf-8-sig. I see you now.

**Panel 4.** Night. The owl with a lantern. Two identical J.A.R.V.I.S. reach
for one yellow helmet labelled PORT 8765.
CAPTION: Review 2, late at night.
ARCHITECT: Two launches at the same instant both saw the port free. Take it in
one move: SO_EXCLUSIVEADDRUSE.

**Panel 5.** Dark red. An angry clock monster with "72h" on its face. The owl
below.
BOSS (the clock): EVERY THREE DAYS, I END THE WATCH!
ARCHITECT: Time limit: none. And for crashes, a drumbeat every 5 minutes.

**Panel 6.** A blue PowerShell window: `PS> .\production.ps1`, then in red
"The string is missing the terminator: '." A tiny yellow em dash with eyes and
legs runs across it, giggling. The beaver at the right.
BOSS (the em dash): HEE HEE! POWERSHELL 5.1 READS ME AS A CLOSING QUOTE!
DEV: ASCII only. Goodbye, em dash.

### Chapter 4 — The First Night Shift

**Panel 1.** Dusk, purple to pink. A big yellow luggage tag reading
v2026.10.09. The beaver cheers; the owl stands proud.
ARCHITECT: First release. Production only ever runs tags.

**Panel 2.** Dark red. J.A.R.V.I.S. tumbles; a crossed-out sign reads BROKEN;
big yellow rewind arrows ◀◀.
CAPTION: Dress rehearsal: an update broken on purpose.
J.A.R.V.I.S.: health check failed. rolling back… Front: fresh. Back: fresh.

**Panel 3 (wide).** Night, stars, moon. J.A.R.V.I.S. on the roof ridge; Front
and Back hover out with cones of light.
CAPTION: 9 October, 20:20:55. Production goes live.
J.A.R.V.I.S.: Starting 2 camera(s) on stream1… / Back: ok / Front: ok /
Surveillance running.
J.A.R.V.I.S.: first night: 19 events, 0 errors.

**Panel 4.** Grey infrared look. A dark silhouette walks out carrying a
delivery box; a white husky follows. A drone above with a red REC dot.
CAPTION: 22:29. The Owner steps out for a delivery…
J.A.R.V.I.S.: event: Front. 56 s — out, the gate, and back.

**Panel 5.** Dramatic close-up: J.A.R.V.I.S.'s huge eye fills the left side,
staring at a thumbnail on the right — the white dog lying on a dark mat inside
a green box labelled "person 0.72".
J.A.R.V.I.S.: …person?
CAPTION (black bar): TO BE CONTINUED — ISSUE #2: THE DOG WHO WORE A PERSON'S
FACE

### Closing card — Raid Log, Issue #1

**Abilities unlocked**
- **Patient Eyes** — motion by MOG2, believed only when it lasts several
  frames; YOLO11 through cv2.dnn, no PyTorch.
- **Memory for Faces** — YuNet finds, SFace recognises; a face named once is
  named forever.
- **Paper Planes** — Telegram with the photo, then the face and the name, and
  "probably" when unsure.
- **A Window Anywhere** — one web page for live view and recordings, on any
  computer in the house.
- **Never Sleeps** — a service with no window, started by Windows, back within
  5 minutes of a crash.
- **Twin Training** — production in HD on stream1, a test copy on stream2.
- **Oath of Unbroken Scrolls** — every file an older version wrote is read
  again before and after each update.
- **Time-Turner** — an update that fails its health check puts the old
  version back on its own.

**Bosses defeated:** The Gate of Signatures (Smart App Control, twice) · The
Mosquito Swarm · The Two-Headed Net (one model, two threads) · The False
Chronicle (our own history, wrong) · The Invisible BOM · The Twin Who Started
Twice · The 72-Hour Curse · The Em Dash.

**Still lurking:** black windows that open on their own (R15) · the dog on the
mat (R18) · a face that passed too fast (R20).

**The Owner's decrees**
- "Everything on the web, one service." — no second way in, 9 Oct
- "Keep the door open to the home network." — reach it from the other
  computer, R4
- "One copy on guard, another to train." — production and test, backlog 17
- "Never break what was written before." — additive changes, or a migration
- "Only our conversation stays in Portuguese." — code, docs and screens in
  English
- "The Dev builds. The Architect writes it down." — HANDOFF.md between them

**The party:** The Dev — Claude, high; builds, tests, hands over. The
Architect — Claude, ultracode; reviews at night, keeps the books.
J.A.R.V.I.S. — two eyes, one house, guided by the Owner's every decision.

**Numbers:** 16 days · 52 commits · 2 reviews · 1 release · first night: 19
events.

**Next:** Issue #2 — The Dog Who Wore a Person's Face (`v2026.10.10`).

---

## Issue #2 — The Dog Who Wore a Person's Face

`v2026.10.10` · 10 Oct 2026, one long night

### Cover

Close-up of a phone screen showing a notification photo: the white dog asleep
on its dark mat, a green box around it labelled "person 0.72". Reflected in
the screen, J.A.R.V.I.S.'s eye, puzzled. Badge: **ISSUE #2**.

### Chapter 1 — The Case of the Missing Owner

**Panel 1.** Night, the house. The owl at a desk, lantern lit, logs unrolled.
THE OWNER: I went out for a delivery and came back. It didn't catch me —
not going, not coming back!
ARCHITECT: Production's first night: 19 events, no errors. Let's look.

**Panel 2.** The Owner's desktop: two black console windows stay open, others
flash and vanish. Their titles read "…site-packages\imageio_ffmpeg…".
THE OWNER: And these windows keep popping up.
ARCHITECT: Those are the cameras' ffmpeg. Don't close them — you'd cut a
camera.

**Panel 3.** The owl watches two videos side by side: the Tapo app's clip and
production's clip. Same scene: the Owner leaving, the gate, coming back with
a box.
ARCHITECT: You were recorded. Both ways. Fifty-six seconds.

**Panel 4.** The event card in the browser: the picture is the dog on the mat.
ARCHITECT: But the picture is the first frame of the event — and the dog
started it, wearing a person's label.

**Panel 5.** A filmstrip of ninety frames; only four glow green.
ARCHITECT: And your face was frontal and big enough in only 4 of 90 frames.
The scan read one in fourteen. It missed them all.

### Chapter 2 — The Builder's Night

**Panel 1.** The beaver with a lamp on the hard hat, five tasks pinned on a
board.
DEV: Windows first. CREATE_NO_WINDOW on every ffmpeg.
BOSS (a swarm of tiny black windows): WE OPEN WHEN WE PLEASE!
DEV: Not anymore.

**Panel 2.** A paper plane trailing a long URL; inside the URL, a glowing key.
BOSS (the key): EVERY ERROR MESSAGE CARRIES ME — /bot<token>/!
DEV: Redacted where you enter. And every message now leaves a line in the log.

**Panel 3.** J.A.R.V.I.S. flips through frames like a photographer and picks
one: the Owner, standing, carrying the box.
J.A.R.V.I.S.: best view: person, standing. Saved as .best.jpg.

**Panel 4.** The scan grows dense around the moments a person was seen: the
frames glow where the Owner walks.
J.A.R.V.I.S.: face found. probably Owner.

**Panel 5.** A scroll labelled config.json, safe under a glass dome.
DEV: And settings this version doesn't know are kept, not erased.

### Chapter 3 — Two Ways to Fall

**Panel 1.** Production on the roof, a new tag: v2026.10.10. No windows on the
desktop below.
CAPTION: 00:56. The update takes ten seconds.

**Panel 2.** The house goes dark, then the lights come back.
CAPTION: 00:58. The Owner reboots the machine.
J.A.R.V.I.S.: Back: ok. Front: ok. (59 s after Windows)

**Panel 3.** The Owner's hand (only the hand) clicks "End task" on "Python" in
Task Manager. J.A.R.V.I.S. collapses.
CAPTION: 01:01. The Owner pulls the plug on purpose.

**Panel 4.** A big drum labelled "every 5 minutes" beats; J.A.R.V.I.S. stands
up again.
CAPTION: 01:06. The drumbeat brings it back.
ARCHITECT: Reboot or crash: it comes back on its own.

**Panel 5.** The owl looks at a stopwatch reading "45 s" over the scan's
thinking cloud, while the drones keep watching outside.
ARCHITECT: Forty-five seconds of thinking per face scan… on the same four
cores that watch the cameras?
CAPTION (black bar): TO BE CONTINUED — ISSUE #3: THE WATCHER'S INSTRUMENTS

### Closing card — Raid Log, Issue #2

**Abilities unlocked:** **Silent Machinery** — no console windows (R15) ·
**Sealed Lips** — the bot token never reaches text (R16) · **The Best Side** —
the event's picture is its best view of a person (R19) · **Patient Reader** —
the face scan reads densely where a person was seen (R20) · **Long Memory** —
settings a newer version added survive an older one (R11) · **Unbreakable** —
back after a reboot and after a crash (R13).

**Bosses defeated:** The Window Swarm · The Key in the URL · The Missed Face.

**Still lurking:** the dog on the mat, now two false messages per event (R18) ·
the cost of a 45 s scan (R21).

**The Owner's decrees:** "Prepare the Dev's session; you set the priorities,
tell me the criteria." · "Count how many sessions fit in one token window." ·
"Show me the running version somewhere." · "Weigh the cost before drawing."

**Numbers:** 6 fixes · 1 release · 1 reboot and 1 crash, both survived.

**Next:** Issue #3 — The Watcher's Instruments (`v2026.10.10.2`).

---

## Issue #3 — The Watcher's Instruments

`v2026.10.10.2` · 10 Oct 2026, before dawn

### Cover

The beaver at a workbench building instruments: a frame counter with a
needle, a magnifying lens on a tripod, a small brass plate engraved with a
version number. J.A.R.V.I.S. watches, curious. Badge: **ISSUE #3**.

### Chapter 1 — Measure Before You Choose

**Panel 1.** A dial labelled "frames per minute" on J.A.R.V.I.S.'s chest; the
needle barely moves while the scan runs.
DEV: Quiet scene: 584 frames a minute, 578 during a scan. Fine.

**Panel 2.** A second dial labelled YOLO: the needle swings into the red.
DEV: But YOLO goes from 280 to 454 milliseconds while a scan runs.

**Panel 3.** The beaver turns a knob labelled "threads: 1"; both dials get
worse.
DEV: Fewer threads for the scan? The knob is shared — YOLO gets slower too.
CAPTION: It sounded obviously right. It measured wrong.

**Panel 4.** The owl at night with a list of five options, four crossed out.
ARCHITECT: The scan pauses between frames whenever a camera is recording. The
collision only matters during an event — so that is where we remove it.

### Chapter 2 — Instruments

**Panel 1.** A small brass plate in the corner of the web page reads
v2026.10.10.2.
THE OWNER: I want to see the running version somewhere.
DEV: git describe, once at startup. Production shows its tag.

**Panel 2.** A logbook: "face scan 22-29-22.mp4: dense 7.3-15.7 s, 36.3-42.1 s,
162 frames, 23.1 s, 3 face view(s)".
J.A.R.V.I.S.: now I write down where I looked.

**Panel 3.** The replay machine: the 22:29 clip runs through it; a ticker
prints reasons — "too short", "static spot", "no motion overlap".
DEV: Every frame, and why it was kept or dropped.

**Panel 4.** On the replay screen: the dog's box, very wide, touching the
bottom edge; beside it the Owner's box, tall and narrow.
DEV: The dog is three or four times wider than tall. Every real person is
taller than wide.
THE OWNER: Let it sleep for now. Later.

**Panel 5.** The owl hands the beaver's drawings back as a written script.
THE OWNER: Don't draw the comic. Write the script — I'll draw it with a proper
tool.
ARCHITECT: Cheaper, and only the script needs to know what really happened.

**Panel 6.** Night. The dog still asleep on the mat, one eye half open. A
green box flickers around it.
CAPTION (black bar): TO BE CONTINUED — ISSUE #4

### Closing card — Raid Log, Issue #3

**Abilities unlocked:** **The Pulse** — frames analysed per minute, in
`/api/status` (R21) · **Name Plate** — the running version on the page
(backlog 18) · **The Logbook** — where every face scan looked (R22) · **The
Replay** — `tools/replay.py`, why each frame was kept or dropped (R17) ·
**Plain Speech** — the code speaks English, the old window included (R10).

**Bosses defeated:** The Obvious Wrong Answer (fewer threads).

**Still lurking:** the dog on the mat (R18, waiting on the Owner) · the scan
that collides with events (R23, decided, to build).

**The Owner's decrees:** "Show the running version." · "Write the comic's
script, not the drawing." · "Before handing me a decision, look for a better
solution."

**Next:** Issue #4.

---

## Issue #4 — The House Gets a Front Desk

`v2026.10.10.3` · 10 Oct 2026, afternoon

### Cover

Inside the browser window, J.A.R.V.I.S. stands behind a small reception desk.
Behind it, two new doors with signs: PEOPLE and SETTINGS. The dog sleeps on
its mat in front of the desk, finally without a green box. Badge: **ISSUE #4**.

### Chapter 1 — Stepping Aside

**Panel 1.** The face scan, drawn as a librarian reading a pile of frames,
stops and puts a bookmark in when a drone's red REC light comes on.
DEV: While any camera records, the scan waits between frames.

**Panel 2.** The YOLO dial from Issue #3 swings back out of the red.
DEV: 590 milliseconds during a scan. 342 with the scan paused — almost as
fast as alone.

**Panel 3.** The replay screen: the white dog sitting up on the mat, its box
labelled "2.4".
DEV: The dog sits up, and the box stops being so wide. 2.5 missed it.
ARCHITECT: Real people measure 0.4 to 0.6. Make it 2.0 — still four times the
margin.

**Panel 4.** The dog yawns on the mat; no box around it. J.A.R.V.I.S. gives a
thumbs-up.
J.A.R.V.I.S.: wide at the bottom edge — dropped. Every drop in 25 events: the
mat.

### Chapter 2 — The Front Desk

**Panel 1.** The PEOPLE door opens on a wall of face cards, each with a name
field.
DEV: People on the web. Type a name; the same name twice merges the two.

**Panel 2.** The SETTINGS door: a small safe with a coin slot labelled TOKEN —
things go in, nothing comes out.
DEV: The token can be written, never read back. Anyone on the Wi-Fi can open
this page.

**Panel 3.** Two movers carrying the same box in opposite directions, labelled
"web" and "Housekeeper".
DEV: And no "Archive now" button: two movers on the same files is how boxes
get lost.

**Panel 4.** The Owner's gold balloon comes in from off-panel, pointing at an
unnamed face card.
THE OWNER: Sometimes my own face comes in unnamed. I want to say "this one is
me too" — and the same for the dogs.
ARCHITECT: Faces, yes: the merge already exists, it needs a picker. Dogs need
a new layer first.

**Panel 5.** Night. The owl walks past the front desk and stops: no lock on
the door, a key hanging from the hook for anyone.
ARCHITECT: Anyone on the Wi-Fi can rename a face here… or a web page you open
can do it for them.
CAPTION (black bar): TO BE CONTINUED — ISSUE #5: THE LOCK ON THE FRONT DESK

### Closing card — Raid Log, Issue #4

**Abilities unlocked:** **Good Manners** — the face scan steps aside during
events (R23) · **The Sleeping Dog** — a wide "person" at the bottom edge is
the mat (R18) · **Front Desk** — People and Settings on the web (stage 4) ·
**One-Way Safe** — the token is write-only.

**Bosses defeated:** The Collision · The Dog Who Sat Up.

**Still lurking:** the unlocked front desk (R24) · a merge cannot be undone
(backlog 9) · no identity for the dogs (item 15).

**The Owner's decrees:** "You set the rule for the dog." · "A face of mine
that was missed should join my name — and the same for the dogs."

**Next:** Issue #5 — The Lock on the Front Desk.
