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
