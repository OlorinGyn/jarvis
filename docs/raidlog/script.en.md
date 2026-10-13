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

---

## Issue #5 — The Lock and the Album

`v2026.10.10.4` · 10 Oct 2026, late afternoon

### Cover

The owl fits a small keypad lock on the front desk's door. Behind the desk,
J.A.R.V.I.S. holds open a photo album full of face crops. Badge: **ISSUE #5**.

### Chapter 1 — The Lock

**Panel 1.** The beaver at the workbench, raising a paw every few seconds;
above him a pile of little "May I?" cards.
DEV: May I? … May I? … May I?
THE OWNER: Five times in a row! This is absurd!

**Panel 2.** The owl reads a long scroll of commands, every one starting with
`cd`.
ARCHITECT: 124 commands began with a cd into the folder we were already in.
That is what kept asking. Not anymore.

**Panel 3.** A foreign web page tries to slip a note under the front desk's
door; the door only opens for notes stamped "X-Jarvis-Request".
DEV: Every change must carry our stamp. A strange page can't stamp it.

**Panel 4.** A guest's phone at the desk is refused; the Owner's other
computer types a short PIN once and is let in.
DEV: From another device, a PIN — set on the M900, typed once.

### Chapter 2 — The Album

**Panel 1.** The People page: a neat grid of named faces; below, a row of
unnamed ones, each with a "Belongs to…" button.
DEV: People by person now. And an unknown face can join a name with a click.

**Panel 2.** The Owner's page open like an album: rows of face photos, one
marked with a small trash can; a short queue of photos waits at the edge.
DEV: Forty views. Remove one, and the next one waiting takes its place.

**Panel 3.** A rename box: "Izabel" typed over "Gustavo"; a yellow warning
pops up: "This will merge with Izabel — continue?"
DEV: A name that belongs to someone else asks first. 409: conflict.

**Panel 4.** A recording card on the Recordings tab, with a new line:
"People: Gustavo · Animals: dog".
J.A.R.V.I.S.: now every recording says who was there.

**Panel 5.** Two movers wheel the old OpenCV window out of the house like an
old TV set.
CAPTION: The old window retires. The web page is the only door.

**Panel 6.** The Owner's hand sweeps the old face cards off the table.
THE OWNER: Delete the old faces. I'll register us again — with photos this
time.

**Panel 7.** The owl studies a chart: 21 face scans, 2 with a face, 1 message.
THE OWNER: Fewer face messages lately… is it just me?
ARCHITECT: Partly faces are rare by day. But one of them was lost to the
cooldown.
CAPTION (black bar): TO BE CONTINUED — ISSUE #6

### Closing card — Raid Log, Issue #5

**Abilities unlocked:** **The Stamp and the PIN** — every write guarded (R24) ·
**The Album** — People by person, 40 views with photos and a queue
(backlog 19) · **Roll Call** — who appears in each recording (backlog 20) ·
**One Door** — the OpenCV window retired.

**Bosses defeated:** The Hundred "May I?"s · The Forged Note.

**Still lurking:** a face lost to the cooldown (R25) · a merge cannot be
undone (backlog 9) · no tests guard the album (R6).

**The Owner's decrees:** "People by person, with all my photos." · "Let me
rename a person." · "Delete the old faces, no backup." · "Stop asking me for
permission."

**Next:** Issue #6.

---

## Issue #6 — The Safety Net

`v2026.10.10.5` · 10 Oct 2026, early evening

### Cover

Under J.A.R.V.I.S.'s photo album, the beaver stretches a big safety net with
23 knots, each knot a tiny green check mark. Badge: **ISSUE #6**.

### Chapter 1 — The Lost Face, Found

**Panel 1.** A face card stuck behind a turnstile labelled "cooldown 2 min".
ARCHITECT: The turnstile is for repeated events, not for faces. Faces are
rare.

**Panel 2.** The turnstile now has a side gate marked with a face icon; the
card goes through. A small timer per person hangs on the gate.
DEV: A found face always goes out — but the same person only once per
cooldown.

### Chapter 2 — The Net

**Panel 1.** The beaver ties knots in the net: "40 views", "the queue",
"merge", "the lock", "cooldowns".
DEV: Twenty-three tests. They run in three seconds, on folders that vanish
after.

**Panel 2.** A suspicious package arrives at the door labelled "httpx2". The
owl inspects it with a magnifier: the sender is the same as the old "httpx",
and Starlette itself asked for it.
ARCHITECT: A name one character away from a famous one is how fake packages
look. This one is real.

**Panel 3.** The Owner's gold balloon from off-panel, pointing at the album.
THE OWNER: I want to pick which of the forty photos is my favourite — the one
on the People page.
CAPTION (black bar): NEXT — ISSUE #7

### Closing card — Raid Log, Issue #6

**Abilities unlocked:** **No Face Left Behind** — a found face is always
announced, once per person per cooldown (R25) · **The Safety Net** — 23
automatic tests (R6).

**Bosses defeated:** The Turnstile · The Look-Alike Package (a false alarm,
checked).

**Still lurking:** a merge cannot be undone (backlog 9).

**The Owner's decrees:** "Let me choose my favourite photo." (backlog 21)

**Next:** Issue #7.

---

## Issue #7 — The Favourite

`v2026.10.10.6` · 10 Oct 2026, evening

**Panel 1.** The person page: forty face photos; the Owner's hand taps a small
star on one of them, and it turns gold.
THE OWNER: This one. That's how I want to appear on the People page.
DEV: The star remembers the photo itself, not its place in the row — so it
stays right when other views come and go.

**Panel 2.** A moving van leaves the house with boxes labelled "pytest" and
"httpx2".
DEV: And production stops carrying the test tools. --no-dev.

**Panel 3.** The Owner, on the street, typing on the phone.
THE OWNER: No undo button. Just warn me before a merge, and if I say yes, go.
ARCHITECT: That warning was already there. Nothing to build.

**Closing card.** Abilities: **The Favourite** — a chosen photo per person
(backlog 21) · **Light Luggage** — production without test tools (R26).
Decrees: "Let me pick my favourite photo." · "No undo; warn me and go on
yes." Next: Issue #8.
---

## Issue #8 — Mirana and Aurora

`v2026.10.10.7` · 10 Oct 2026, night

**Panel 1.** The owl holds up a sheet of dog crops in two rows, one dark, one
white. The Owner's gold balloon from off-panel.
THE OWNER: First row is Mirana, the black one. Second is Aurora, the white
one. But careful — this software isn't only for me.

**Panel 2.** The Owner's balloon grows bigger.
THE OWNER: No colour rule in the code. Give me a Dogs tab, and I'll teach it
my dogs. Anyone else teaches it theirs.

**Panel 3.** The beaver at the workbench with a pair of scissors cutting a dog
out of its box — the mat and the floor fall away.
DEV: GrabCut: the dog, not the box. Then a fingerprint of its fur — tones,
and colours by day.

**Panel 4.** Two scales, one labelled DAY, one labelled NIGHT; a dog's
fingerprint is only ever weighed on its own scale.
DEV: Day against day, infrared against infrared. Never mixed.

**Panel 5.** Three phone notifications side by side: "Front: Mirana",
"Front: probably Aurora", "Front: unidentified dog".
THE OWNER: A dog alerts because a dog is there. How sure we are just changes
the words.

**Panel 6.** The new Dogs tab, full of unnamed crops piling up off the edge
of the screen; the owl frowns.
ARCHITECT: Every dog it isn't sure about becomes a new card. Thirty a day…
CAPTION (black bar): NEXT — ISSUE #9

**Closing card.** Abilities: **The Kennel** — a Dogs tab where each household
names its own dogs (backlog 22) · **Three Words** — name, probably name,
unidentified dog. Lurking: the pile of unnamed cards (R27); thresholds not yet
tested on real names. Decrees: "No colour rule in the code." · "Notify when
there is a dog; certainty only changes the words."
---

## Issue #9 — The Front Desk Learns Manners

`v2026.10.11` → `v2026.10.11.3` · 11 Oct 2026

**Panel 1.** The Owner's other computer shows an old, yellowed copy of the
page; a calendar on its wall still reads "10 Oct".
THE OWNER: The screens fail on my other computer.
ARCHITECT: Your browser kept yesterday's script. Seven releases later, it was
calling doors that no longer exist.

**Panel 2.** Every page now carries a small stamp with the version; the
browser checks it at the door each visit.
DEV: No-cache means "ask first", not "don't keep". A quick 304, and never stale.

**Panel 3.** A person walks past the camera, face turned to the door; the
detector draws the face, then a stern filter stamps "NOT FRONTAL".
THE OWNER: Plenty of person alerts, hardly any faces.
ARCHITECT: The face was there in 61 frames — all from the side.

**Panel 4.** A phone shows "Front: face, side view" with a clear side photo.
DEV: The side view goes to your phone. It never teaches the gallery.

**Panel 5.** A visitor badge (a cookie) hangs on the Owner's laptop, a
calendar showing "30 days" beside it.
THE OWNER: Stop asking me for the PIN on every device.
DEV: Pair once. Thirty days, renewed every time you use it.

**Panel 6.** A small cinema screen opens inside the Recordings card; the
Owner watches a clip from the sofa on the phone.
THE OWNER: And I can't watch the recordings from another device.
DEV: There never was a video door. Now there is — and it can seek.

**Panel 7.** The owl wakes at a set time and sends a paper plane to the
beaver's workshop; later the beaver sends one back.
CAPTION: 12:23. The first cycle that ran itself.

**Closing card.** Abilities: **Always Fresh** (R28) · **Side View** (R30 a) ·
**The Badge** — pair a device once (R34) · **The Cinema** — recordings play on
the page (item 5) · **The Pack** — naming a dog gathers its look-alikes (R29) ·
**Self-Starting** — the developer and the architect hand over by themselves.
Lurking: Aurora curled on the mat still passes as a person now and then (R35).
Decrees: "Look at every person alert without a face." · "Pair once, or 30
days." · "Let me watch from any device." · "Start the next session yourselves."
---

## Issue #10 — The Evidence Box

`v2026.10.11.4` · 11 Oct 2026, afternoon

**Panel 1.** The Dogs tab; among the crops, one is clearly the Owner. The
Owner's hand presses a red button: "Bad detection".
THE OWNER: Some of these aren't even dogs. One is me.
DEV: Don't delete it — report it. It goes into the evidence box, with where it
came from and what you said.

**Panel 2.** The owl drops five photos on the table: people crouching,
bending, sitting by the camera.
ARCHITECT: A lower ratio would have called all five of these "the dog on the
mat". They're people. The rule stays.

**Panel 3.** The beaver lays out a hundred face photos and picks forty, each
as different from the others as it can.
DEV: Analyse: the forty most different views. Angles and light, not forty
copies.

**Panel 4.** A stopwatch: 137 ms becomes 45 ms. The drones keep watching
outside, undisturbed.
DEV: Find the face on a small copy, refine it on the big one. Three times
faster.

**Panel 5.** The owl holds two face cards — "Gustavo" and an empty one with a
question mark.
ARCHITECT: Side faces match you most of the time. To know they wouldn't match a
stranger, I need a second name.

**Closing card.** Abilities: **The Evidence Box** (backlog 23) · **The Best
Forty** (backlog 24) · **Quick Eyes** — a cheaper face scan (R31) · **Quiet
Log** (R32). Decided against: a lower dog-on-the-mat ratio (R35). Lurking: a
report never says what the thing really was (R37). Decrees: "Report it, don't
delete it — and remember which screen it came from."
## Issue #11 — Second Chances

`v2026.10.11.5` and `v2026.10.11.6` · 11 Oct 2026, evening

**Panel 1.** Night, deep blue. At the door of the house, the old J.A.R.V.I.S.
is still carrying out a box labelled CLIP while the new one waits on the step;
Front and Back hover above both, each with a small sign: BUSY. A stopwatch in
the corner reads 22 s.
CAPTION: The first deploy of `v2026.10.11.4`. The old version was still
assembling a clip when the new one asked for the cameras.
ARCHITECT: It rolled itself back. From now on the update waits until nothing
runs from C:\JARVIS — up to three minutes.

**Panel 2.** A person's page: empty frames where the photos should be.
Below it, a closed drawer, light leaking out of it, full of photos.
BOSS (the drawer): SAME NAME, FIRST FOUND!
ARCHITECT: Two grids with the same class, and the page filled the first one —
the hidden one. The tests only looked at the server.

**Panel 3.** The beaver builds two shelves, CHOSEN (40) above and WAITING
below, with ↑ and ↓ arrows painted between them.
THE OWNER: Waiting photos only make sense if I can compare them with the
chosen ones.
DEV: Side by side, then. Nothing moves between them on its own any more — you
pick.

**Panel 4.** The evidence box of the last issue, open. A dog card flies out of
it back into the album, trailing its photos and its sightings like a kite's
tail.
CAPTION: Some of that afternoon's reports were mistakes.
DEV: Undo. It goes back with its views, its favourite, its sightings. The box
now keeps a copy of every photo, so there's something to put back.

**Panel 5.** A report card showing the Owner's face, filed as "not a dog". A
small menu opens beside it: "Actually…" — person.
DEV: And a report can finally say what it really was.

**Panel 6.** The beaver slams a drawer shut, an entry safe inside; a drone
arrives a moment too late with one more photo and bumps into the closed
drawer.
DEV: Take it out first, under the lock, then write the report. A scan that
arrives late finds the door closed — and loses nothing.

**Panel 7.** Dark red. The stone gate of issue #1, the blue SAC shield again,
now blocking a tiny figure labelled `pytest.exe`. The owl walks around the
gate holding a scroll: `python -m pytest`.
BOSS (the gate): UNSIGNED LAUNCHERS SHALL NOT PASS!
ARCHITECT: Then the signed Python runs the tests itself. Ninety-two, green.

**Closing card.** Abilities: **Second Chances** — Undo a report (R38) ·
**Chosen and Waiting** (R40) · **"Actually…"** (R37) · **The Closed Door**
(R36) · **The Patient Deploy**. Bosses defeated: **The Hidden Grid** (R39) ·
**The Impatient Update** · **The Gate of Signatures**, again. Lurking: when
Waiting is full, a click aimed at one photo can land on its neighbour (R41).
Decrees: "Waiting photos only make sense if I can compare them with the chosen
ones."

## Issue #12 — The House Learns Who Lives Here

`v2026.10.12` · 12 Oct 2026, morning

**Panel 1.** Warm cream, indoors. A phone on the table buried under a pile of
message bubbles spilling onto the floor, most of them reading "Gustavo
recognized". The owl counts them with a scroll that unrolls off the panel.
CAPTION: Two days of production: 143 messages. 34 named a face — 21 of them
the Owner.
ARCHITECT: The house keeps announcing the people who live in it.

**Panel 2.** The beaver pins a small gold badge, RESIDENT, on three cards: the
Owner's (a silhouette, never drawn), Mirana (dark fur) and Aurora (light fur).
DEV: Named entries only. And only a sure match counts — "probably Gustavo"
still rings, because that might be someone else.

**Panel 3.** A big switchboard on the wall: seven rows of switches, three
columns lettered HOME, AWAY, SILENT. The HOME column is lit.
THE OWNER: A person with no recognisable face notifies at home too. A stranger
in the dark must reach the phone.
DEV: Recording never changes. A mode only decides what reaches the phone.

**Panel 4.** Split panel. Left: a dog walks in and a stopwatch reads 0.1 s,
a tag already on its collar: AURORA. Right: a person walks in, and the drone
Front carries the clip off to a workbench with an hourglass on it.
DEV: A dog has a name from the first frame. A person only after the clip is
scanned. So in Home, the person's message waits for the scan.

**Panel 5.** Night, deep blue. The Owner's hand (only the hand) types `/away`
on the phone. A long fishing line runs from J.A.R.V.I.S.'s antenna up to a
cloud marked TELEGRAM; the line twitches, and the lamp on the switchboard jumps
to AWAY.
DEV: No port opened. We ask, and Telegram holds the line until something
arrives.
BOSS (a second fishing line, tangled in the first): TWO READERS? 409!

**Panel 6.** Dark red. The owl, lantern raised, finds a clock-shaped boss
sitting on the camera's message slot. Behind it, a dim figure with no face
waits at the door, unannounced; a dog bubble has already flown off to the
phone.
BOSS (the clock): THE DOG TOOK THE SLOT. COME BACK IN TWO MINUTES.
ARCHITECT: Same event, same visit. The person's message is a follow-up — the
cooldown is for the next event, not this one. And if the clip fails to build,
the best view still goes.

**Panel 7.** The person page from issue #11, Waiting full. A cursor aims × at
one photo while a drone slides a new photo in, pushing the row one step left.
The × now carries a little name tag; the server holds up a sign: 409.
DEV: The page says which photo it saw. If it moved, nothing is deleted — the
page reloads.

**Closing card.** Abilities: **Resident** (backlog 25a) · **Home, Away,
Silent** (25b–d) · **The Switchboard** — the Notifications tab (25e) ·
**Commands from the Phone** (25f) · **The Named Click** (R41). Bosses
defeated: **The Borrowed Cooldown** · **The Silent Failed Clip** · **The
Shifting Neighbour** (R41). Lurking: at home, the Owner walks out with someone
whose face is never seen — and the scan, finding only the Owner, says nothing
(R42); and two hands writing `config.json` at the same instant (R43). Decrees:
"A stranger in the dark must reach the phone."

## Issue #13 — The Owner Is Not a Dog

`v2026.10.12.2` · 12 Oct 2026, evening

**Panel 1.** Warm cream, indoors. The Dogs tab on a big screen: rows of dog
photos, and among them a crop that is plainly a person's back bent at a car
door — a silhouette, never drawn — tagged `dog 0.74`. Two more like it.
THE OWNER: I keep showing up in the Dogs tab.

**Panel 2.** The owl opens the evidence box from issue #10: six dog reports.
Four photos are the same bent silhouette. A gauge on the box reads
`person 0.00`.
ARCHITECT: Four of six are you, bending over. And YOLO is sure — no person
score left in that box at all.

**Panel 3.** Close-up, two transparent boxes laid one over the other: a
`person` box, faded, stamped "2 s ago", and the `dog` box now — almost the
same rectangle. Beside it, a small real dog at someone's feet: a little box
inside a big one, barely overlapping.
ARCHITECT: But the box did not move. Two seconds ago, this exact box was a
person. A dog at your feet never sits in your box like that.

**Panel 4.** The beaver fits a small hourglass to J.A.R.V.I.S.'s side, filled
with tiny person boxes instead of sand.
DEV: Every person box of the last two seconds stays in memory. A dog box on
top of one of them is that person.
J.A.R.V.I.S.: `the person's box from a moment ago: dog 0.74`

**Panel 5.** Night, deep blue. The owl, lantern raised, runs a film strip of
Mirana and Aurora alone in the yard through a small projector. A counter on
the projector: `relabelled: 0`.
ARCHITECT: And a real dog with nobody around? Six clips, 174 dog frames. Not
one renamed.

**Panel 6.** The unnamed photos, now sorted into piles with signs: "Looks like
Aurora (12)", "No guess". The beaver taps photos and they light up with green
frames; a bar along the bottom reads "7 selected · Assign to… · Bad detection
· Clear".
THE OWNER: Select many photos and give them to one dog — not "Belongs to…" one
by one.
DEV: Grouped by what the matcher guesses. Only a hint: the name is still
yours.

**Panel 7.** A filing cabinet labelled SETTINGS; the beaver slides a drawer
labelled NOTIFICATIONS into its top slot, beside DEVICES, ARCHIVE and
REPORTS. On a phone in the corner, a tab bar too wide for the screen pushes
the bottom bar off the edge.
THE OWNER: A Notifications tab isn't ideal. Make it part of Settings.
DEV: And on the phone the tabs wrap now — the bar had fallen off the screen.

**Panel 8.** Dark red. Two hands — one from the web page, one from a Telegram
cloud — tug at the same sheet of paper, `config.json`, tearing it. The boss is
the torn half, waving.
BOSS (the torn page): HALF A FILE! THE TOKEN IS GONE!
DEV: Write a whole new copy, then swap it in at once. One writer at a time.
ARCHITECT (holding up a forgotten copy found under the desk, the key still in
it): And this copy holds the token. It never goes to git.

**Closing card.** Abilities: **The Two-Second Memory** (R44) · **Select Many**
(backlog 26) · **The Settings Drawer** (backlog 27) · **The Whole-File Swap**
(R43). Bosses defeated: **The Bent-Over Dog** (R44) · **Half a File** (R43) ·
**The Runaway Tab Bar**. Lurking: the Owner walking out at home with someone
who never shows a face still waits for the Owner's choice (R42); and every
merge reads every sighting ever written — a pile that grows by fifty a day
(R45). Decrees: "Notifications belongs in Settings."

## Issue #14 — Every Name in English

`v2026.10.12.3` · 12 Oct 2026, night

**Panel 1.** Warm cream, indoors. A shelf of thick books whose spines still
read ARQUITETURA, INSTALACAO, CONTEXTO, and a row of toolboxes stencilled
`diagnostico`, `refazer_rostos`, `gerar_epub`. The beaver, a label maker in
hand.
THE OWNER: Everything but our conversation in English.
DEV: The pages are English since this morning. The covers aren't.

**Panel 2.** The beaver peels ARQUITETURA off a spine and presses on
ARCHITECTURE. A golden thread — the book's history — runs from the old label
into the new one, unbroken.
DEV: Just the new name in this commit, nothing else. Git still knows it's the
same book.
ARCHITECT: And translate the toolboxes in the next one. A file that changes
its name and its words at once looks like a stranger.

**Panel 3.** A corridor of signposts pointing at book pages — "ARCHITECTURE
18.7", "INSTALL 1.2", "PROCESS 3". A small inspector robot walks along
tapping each one; three signs glow red, all on the HISTORY shelf.
J.A.R.V.I.S.: `3 broken reference(s)`
DEV: The same three before the rename and after. Old sentences, not mine.

**Panel 4.** Night, deep blue. The owl, lantern raised, rewrites three lines
in the HISTORY book. The inspector's lamp turns green.
J.A.R.V.I.S.: `0 broken reference(s)`
ARCHITECT: Now the inspector walks this corridor in every review.

**Panel 5.** An old door labelled `jarvis_vigilancia.bat`; behind it a short
corridor to a new door, `jarvis_headless.bat`. The beaver hangs a sign on the
old one: MOVED — ONE MORE RELEASE.
DEV: Anything still knocking on the old door gets walked to the new one. One
release, then the old door goes.

**Panel 6.** Dark red. The boss of issue #13's last card rises: a mountain of
sighting cards with eyes, fifty more falling on top every day. Five ghostly
beavers climb it at once, each carrying one photo.
BOSS (the pile): READ ME AGAIN! AND AGAIN! AND AGAIN!
DEV: Five photos for Aurora, five climbs through every card ever written.

**Panel 7.** The beaver at the foot of the pile writes on a clipboard —
"a → Aurora, b → Aurora, c → Aurora…" — then climbs once with a stamp. The
pile shrinks back to a heap.
DEV: Each merge just writes down who moved where. The save climbs once.
ARCHITECT: Five reads became one. And a chain — a into b, then b into c —
lands every card straight on c.

**Closing card.** Abilities: **The New Covers** (R10) · **The Signpost
Inspector** (`check_doc_refs.py`) · **One Climb** (R45). Bosses defeated:
**The Endless Pile** (R45) · **The Portuguese Covers** (R10). Lurking: the
Owner walking out at home with someone who never shows a face still waits for
the Owner's choice (R42); zones and a health watch are only proposals; and
after one more session the decided work runs out — the next page is the
Owner's to write.

## Issue #15 — The Signature at the Door

`v2026.10.12.4` · 12 Oct 2026, night

**Panel 1.** Warm cream, indoors. The old door from issue #14, labelled
`jarvis_vigilancia.bat`, its MOVED sign gathering dust. The beaver listens at
it with a stethoscope; silence. Behind him, the door to `jarvis_headless.bat`
stands open.
DEV: One release, and nobody knocked. The startup task never used it; the
shortcut points at `jarvis.bat`.
SFX: CLUNK — the old door comes off its hinges.

**Panel 2.** Dark red. The stone gate of issue #1, the blue shield marked SAC.
On the road, a figure in a Python costume — a green snake suit with a zip
down the back — and no wax seal. Behind it, a crate labelled `winget` lies
broken open.
CAPTION: When the official Python fails to install, uv quietly brings its own.
BOSS (the costume): I RAN YESTERDAY! THE GATE KNOWS ME!
DEV: Until the day it doesn't — that's how 9 October started.

**Panel 3.** The beaver builds a small booth with a magnifying glass on a
stand, labelled `check_python.ps1`. Two roads lead to it: one marked
`install.bat`, one marked `production.ps1`.
DEV: One booth, two roads. The rule lives in one place.
ARCHITECT (off panel): Like moving shared code into a library instead of
copying it twice.

**Panel 4.** At the booth, two small grey figures without seals — `jarvis.exe`
and `pytest.exe` — are turned back; a tall figure with a gold wax seal stamped
PSF is waved through.
J.A.R.V.I.S.: `ERROR: C:\JARVIS\.venv\Scripts\jarvis.exe is not the signed python.org build (signature: NotSigned).`
J.A.R.V.I.S.: `python.exe is signed by the Python Software Foundation.`

**Panel 5.** Night, deep blue. The owl, lantern raised, walks the road the
booth cannot see: before it, the costume has already fallen at the gate, and
the old sign there reads only "could not install the dependencies". The owl
nails a new sign under it: WinError 4551? → INSTALL 1.2.
ARCHITECT: Your booth catches the costume the gate still lets through. When the
gate already stops it, the traveller never reaches the booth — so the gate gets
a signpost too.

**Panel 6.** The M900 at night, two drones hovering. A parcel marked
`v2026.10.12.4` passes through the booth on the production road; the stamp
glows green.
J.A.R.V.I.S.: `pythonw.exe is signed by the Python Software Foundation.`
J.A.R.V.I.S.: `Production is running v2026.10.12.4.`
CAPTION: Ten seconds of pause; both cameras back three seconds later.

**Closing card.** Abilities: **The Seal Booth** (R7, `check_python.ps1`) ·
**The Signpost at the Gate** (the installer's `uv sync` message). Bosses
defeated: **The Python in Costume** (R7) · **The Old Door** (the shim).
Lurking: the decided work is done. The next page is blank, and only the Owner
can write on it — zones, a health watch, or the second person who never shows
a face (R42).
