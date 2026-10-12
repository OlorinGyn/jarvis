# J.A.R.V.I.S. — installing and running it

How to get the system running on a new machine, and how production runs.
For **how** it works, see [ARQUITETURA.md](ARQUITETURA.md).

---

## 1. What must be installed

Four things:

| Program | For |
|---|---|
| **git** | Downloading and updating the code |
| **uv** | Installing the dependencies and running the program |
| **The official Python 3.14** (python.org) | The interpreter. It must be the **signed** one, see 1.2 |
| **Visual C++ Redistributable** | OpenCV depends on it |

**There is no need to install ffmpeg, CUDA, PyTorch or codecs.** ffmpeg comes
packaged in the `imageio-ffmpeg` dependency; the rest are in `pyproject.toml`
and `uv` installs them.

`instalar.bat` takes care of `uv`, Python and the Redistributable on its own.

### 1.1 Why the Visual C++ Redistributable

Native libraries bring their own DLLs but **do not package Microsoft's C++
runtime** they depend on. On a clean Windows install that runtime is missing,
and the error looks like this — it appeared on the M900 when the project still
used PyTorch; today the DLL named would be OpenCV's:

```
OSError: [WinError 1114] A dynamic link library (DLL) initialization
routine failed. Error loading "...\torch\lib\c10.dll"
```

The message does not say what is missing. The fix:

```bat
winget install --id Microsoft.VCRedist.2015+.x64 -e
```

Or download <https://aka.ms/vs/17/release/vc_redist.x64.exe>. Restart after
installing.

On the development PC it was already there because of other programs, which
is why the problem only showed on the target machine.

### 1.2 Why the official Python, and not the one uv downloads

`uv` can download Python by itself, and the project used to rely on that.
Those binaries (from the *python-build-standalone* project) **are not
signed**. Windows 11's Smart App Control lets an unsigned binary through only
if Microsoft's cloud says it has a good reputation — and that verdict changes
over time.

It happened on the M900 on 09/10/2026, and the detail is what makes the
problem treacherous: the blocked Python was the **same file** that had run
normally on 29 and 30/09 — the `cpython-3.14.7` that `uv` downloaded on 29/09.
Nothing changed on disk; Windows' verdict about it did. The interpreter itself
was refused (`WinError 4551`), not even `python -c "print(1)"` ran, and the
program had no way to start again. Windows' `CodeIntegrity` log does not show
when the verdict turned: the M900 had not run J.A.R.V.I.S. between 30/09 and
09/10, and the first recorded block of `python.exe` is the attempt of 09/10.
(The blocks of 29/09 in the same log are something else: PyTorch DLLs loaded
by Python, the case in ARQUITETURA 7.11.)

The python.org Python is **signed by the Python Software Foundation**, and a
valid signature passes without depending on reputation. `pyproject.toml`
declares `python-preference = "system"`: `uv` uses the Python installed in
Windows when there is one, and only falls back to its own if there is none.
To install it by hand:

```bat
winget install --id Python.Python.3.14 -e --scope user
```

To check that the environment is on the signed Python:

```powershell
Get-AuthenticodeSignature .venv\Scripts\python.exe
```

It must say `Valid` and `CN=Python Software Foundation`. The same rule is why
the tests run as `uv run python -m pytest`: `uv run pytest` starts an unsigned
launcher that Smart App Control blocks (ARQUITETURA 19.5).

## 2. Step by step

```bat
git clone https://github.com/OlorinGyn/jarvis.git
cd jarvis
instalar.bat
```

`instalar.bat` does seven things:

1. Installs `uv` if missing (if it does, **close the window and run it
   again** — the PATH only updates in a new window)
2. Makes sure the Visual C++ Redistributable is there (see 1.1)
3. Installs the official Python 3.14, for the current user only (see 1.2)
4. `uv sync` — installs the dependencies from `uv.lock`, at the exact versions
   that were tested, and `jarvis` itself as a package (ARQUITETURA 3.1)
5. Downloads the vision models (~73 MB in all, see section 3)
6. Creates the **J.A.R.V.I.S.** shortcut on the Desktop, with the eye icon (a
   `.bat` cannot have its own icon; see ARQUITETURA 14)
7. Creates `.env` from `.env.example` and opens it in Notepad

Each step has its own error message. The first version lumped the model
download together with loading PyTorch and, when PyTorch failed, blamed the
internet connection — which was perfect.

Fill in `.env` and start from the Desktop shortcut, or:

```bat
jarvis.bat
```

To recreate only the shortcut:

```bat
powershell -ExecutionPolicy Bypass -File tools\criar_atalho.ps1
```

That starts the service — cameras, detection, recording, faces, dogs,
notifications — and opens the browser at `http://127.0.0.1:8765`, with the
tabs **Live**, **Recordings**, **People**, **Dogs** and **Settings**
(Notifications is its first part). Clicking the shortcut with the service already running only
opens the browser; it does not start a second one, which would fight over the
camera. The console that stays open is the service: stop it with `Ctrl+C` in
it, not with the X (ARQUITETURA 17.7).

The `.bat` only checks that `.env` exists and calls
`uv run python -m jarvis`, which goes straight to the signed Python instead of
the unsigned `jarvis.exe` that `uv` generates (section 1.2).

To start **only the service**, without opening the browser — what starting
with Windows uses (section 5):

```bat
jarvis_vigilancia.bat
```

**From a phone or another computer** on the same Wi-Fi: the console shows the
address, something like `http://192.168.0.18:8765`. The first time, Windows
asks whether Python may receive connections from the network; allow it.
Without that, only the computer itself opens the page. Reading is open to the
home network; changing anything from another device needs pairing it once
with the PIN set in Settings (ARQUITETURA 17.12).

To stop it from any terminal, without looking for the service's console:

```bat
uv run python -m jarvis --stop
```

What happened is in `logs\jarvis.log`.

**Since 09/10/2026 the copy that stays on is production, in `C:\JARVIS`**, and
this folder becomes the test copy. Running the commands above here starts the
test copy. See section 9.

## 3. What is downloaded automatically

None of this is in the repository, because they are large files that should
not be versioned:

| File | Size | Source |
|---|---|---|
| `models/yolo11s.onnx` | 36 MB | ultralytics/assets (official release) |
| `models/face_detection_yunet_2023mar.onnx` | 227 KB | opencv/opencv_zoo |
| `models/face_recognition_sface_2021dec.onnx` | 37 MB | opencv/opencv_zoo |

The models are downloaded by `people.ensure_model()` and
`faces.ensure_models()` the first time each layer runs. `instalar.bat` does it
ahead of time so the first event does not wait for the download.

## 4. Configuring the cameras

`.env` holds one camera per three lines. The label becomes the name on the
page and the name of the recordings' folder.

```
CAM_FRONT_IP=192.168.0.116
CAM_FRONT_USER=user
CAM_FRONT_PASSWORD=password
```

Three traps, all of which have already cost time in this project:

**The credentials are not the TP-Link account's.** Create a "Camera Account"
in the Tapo app: camera → gear → Advanced Settings → Camera Account.

**The camera does only two of three things at once:** Tapo Care, recording to
the SD card, and RTSP. With the first two on, RTSP is switched off silently —
the symptom is `DESCRIBE` answering `200 OK` and `SETUP` closing the
connection. **Turning recording off in the app is not enough: the card has to
be removed physically.** Or turn Tapo Care off. Details in ARQUITETURA 13.

**Reserve the IP by MAC on the router.** Without it the address changes on a
DHCP renewal and the system stops connecting.

## 5. Starting with Windows

Do not create the task by hand. `tools\production.ps1 -Action install`
(section 9) registers it with the settings that matter, and two of them are easy
to get wrong by hand:

- **No execution time limit.** The Task Scheduler default is 72 hours: it
  would kill the surveillance every three days.
- **A trigger every 5 minutes**, not "restart on failure", which only acts
  when the task fails to *start*, not when the program crashes later
  (ARQUITETURA 18.7).

The task runs production from `C:\JARVIS` without a console, whether or not
anyone is logged on.

## 6. Tuning for the M900

The M900 has 4 Skylake cores, far fewer than the development PC. The constants
that matter most, in order of impact:

| Constant | File | Effect |
|---|---|---|
| `HWACCEL` | `capture.py` | Hardware decoding. Empty by default. On the M900 try `"dxva2"` or `"qsv"` — Skylake's Quick Sync decodes H.264 in silicon and frees CPU |
| `ANALYSIS_FPS` | `capture.py` | 10 today. Lowering it to 6 cuts almost 40 % of the analysis work |
| `MIN_INTERVAL` | `people.py` | 0.25 s between YOLO runs. Raising it to 0.5 halves it |
| `MODEL_FILE` and `MODEL_URL` | `people.py` | `yolo11s.onnx`. Switching both to `yolo11n.onnx` is much faster and a little less accurate |

**Measure before changing anything.** Recording itself costs almost nothing,
because the camera's packets are copied without re-encoding (ARQUITETURA 5.1).
The cost is in decoding for analysis and in YOLO. `HWACCEL` only affects the
analysis output; recording never decodes. Measuring the M900 is backlog 4.

## 7. Updating

Production updates itself to a release tag with `production.ps1 -Action
update` (section 9.3). The test copy, from this folder:

```bat
git pull
uv sync
```

`uv sync` is only needed when the dependencies change, but running it always
does no harm. `uv run` also syncs on its own before running.

**Updating a copy from before 29/09/2026:** the code moved from the root to
`src/jarvis/` and `tools/`. `git pull` moves the files; if a `__pycache__/`
folder is left at the root, it can be deleted. `.env`, `models/`, `clips/` and
`faces/` stay where they are.

## 8. When something does not work

**`406 Not Acceptable` or `DESCRIBE failed`**

The camera accepts **a single RTSP session** on `stream1`. Check that no other
J.A.R.V.I.S. is running — production and the test copy use different streams
on purpose (ARQUITETURA 18.2) — or an orphaned ffmpeg:

```bat
tasklist | findstr ffmpeg
```

If the program was killed, ffmpeg may have survived and be holding the camera.

**"Timed out. Check the network and the camera's IP."**

Nothing answers at the IP in `.env`. Either the IP was never filled in, or the
router gave the camera another address. Confirm:

```powershell
Test-NetConnection 192.168.0.116 -Port 554
```

If it fails, find the current IP in the Tapo app (camera → gear → Device
Info) or in the router's client list, update `.env` and reserve the IP
(section 4). Tapo cameras have a MAC starting with `14-EB-B6`. The credentials
tell them apart: each camera accepts only its own Camera Account and answers
`401` to the others.

**It connects but no picture ever arrives ("no frame received")**

First of all, do the IP test above: old versions of `capture.py`, without
`-timeout`, showed this message for a wrong IP too (ARQUITETURA 5.7; the
story is in HISTORY 6).

RTSP is fine but ffmpeg does not deliver frames for analysis. Run:

```bat
uv run python tools/diagnostico.py Front
```

It tests five variants of the capture command, 14 seconds each, and reports
how many frames each delivered on this machine:

```
  OK atual (como o programa roda)        126.0 frames  1o em    2.6s  segmentos 3
  OK sem use_wallclock_as_timestamps     125.0 frames  1o em    3.0s  segmentos 3
  ...
O comando atual funciona nesta maquina.
```

(The tool's own text is still Portuguese: R10.) If the current command fails
and another variant delivers frames, it says which — that one should go into
`capture.py`. If none does, ffmpeg's error lines are shown with it, and it
reminds you to test the IP first. The test segments go to a temporary system
folder, deleted at the end.

The `segmentos` column separates the two cases: segments being recorded with
zero frames means the camera and the network are fine, and the problem is only
in the analysis output.

**A full diagnosis of one camera**

```bat
uv run python tools/probe_rtsp.py 192.168.0.116 user password stream1
```

It shows each step of the handshake. Expected: `200 OK` on all three:

```
DESCRIBE  -> RTSP/1.0 200 OK
SETUP     -> RTSP/1.0 200 OK
PLAY      -> RTSP/1.0 200 OK
```

If `DESCRIBE` passes and `SETUP` closes the connection, it is the two-of-three
rule of section 4.

**Lines `[h264 @ ...] error while decoding MB ...`**

Not a program error. It means the **camera** sent a damaged piece of picture:
a 16×16 px block (the "MB", macroblock) smeared for a fraction of a second,
until the next complete frame. Recording copies the camera's bytes without
re-encoding, so the damage came that way. Since the connection is TCP, the
network loses nothing on the way; the camera itself drops data when its Wi-Fi
chokes.

Since 30/09/2026 these lines no longer reach the terminal (ARQUITETURA 10.11).
To see whether a camera has a bad signal:

```bat
uv run python tools/verificar_clipes.py 2026-09-30
```

```
  Back   13-47-27  5 bloco(s) danificado(s)
  ...
2026-09-30:
  Back   8 de 68 clipes com dano
  Front  0 de 34 clipes com dano
```

If one camera has frequent damage and the other does not, check its signal in
the Tapo app (camera → gear → Device Info). What usually solves it: moving the
router closer or adding a repeater, and preferring the 2.4 GHz network, which
reaches farther than 5 GHz.

**The Live tab shows "no signal"**

The picture is marked after 5 s without a frame (ARQUITETURA 17.8). The camera's
reason is in the log (`logs\jarvis.log`; production's in
`C:\JARVIS\logs\jarvis.log`). The common ones:

| Text | What to do |
|---|---|
| Camera busy | Something else is using the camera. See below |
| Wrong credentials | Check the Camera Account in the Tapo app |
| Timed out. Check the network and the camera's IP | The camera changed address or is off. See "Timed out" above |

**"Camera busy" is the most frequent case on a new install.** The Tapo accepts
**one RTSP connection at a time** on `stream1`. If J.A.R.V.I.S. is running on
another machine — the development PC, say — on the same stream, the second one
does not connect. Close the other instance, the Tapo app, or an orphaned
ffmpeg (`tasklist | findstr ffmpeg`).

**Wrong or repeated faces on People**

First use the page: rename, "Belongs to…" to merge, and "Bad detection" for a
crop that is not a face (ARQUITETURA 17.10, 21). As a last resort, with the
program **stopped**:

```bat
uv run python tools/refazer_rostos.py
```

It moves the current `faces/` to `backups/faces_<date-time>/` and rebuilds
everything from the recorded clips. The names must be given again, but one
card per person is enough: their other faces get the name with it (ARQUITETURA
10.4). Once everything is right, the copy in `backups/` can be deleted.

**No face appears on People**

The expected behaviour in many events. A face goes in only when all of this
holds:

- the event had `person` among its labels;
- the face is **frontal** — profile, the back of the head and a lowered head
  are ignored (a side face can still reach the phone as a picture, never the
  gallery: ARQUITETURA 10.12);
- it is on a person YOLO sees in the same frame;
- if it is someone new, it appeared in at least 2 frames of the clip.

And it shows a few seconds after the event: the scan runs after the clip is
assembled, one at a time. Details in ARQUITETURA 10.9. At night, in infrared,
the face is usually ~44 px against the ideal ~112 px, and recognition is
unreliable (ARQUITETURA 10.5).

**`WinError 1114` or `Error loading ... .dll`**

The Visual C++ Redistributable is missing. See section 1.1.

**`WinError 4551: An Application Control policy has blocked this file`**

Windows 11's Smart App Control blocked a binary without a recognised
signature. It has happened three times:

| When | What was blocked | Way out |
|---|---|---|
| 29/09/2026 | PyTorch's DLLs | PyTorch removed, YOLO through `cv2.dnn` (ARQUITETURA 7.11) |
| 09/10/2026 | **Python itself**, the one `uv` downloads | the official signed Python (section 1.2) |
| 11/10/2026 | `.venv\Scripts\pytest.exe`, `uv`'s unsigned launcher | `uv run python -m pytest` (ARQUITETURA 19.5) |

If the message names `python.exe` or `uv` says `Failed to spawn: python`, it is
the second case: check the signature with `Get-AuthenticodeSignature
.venv\Scripts\python.exe`, and if it is not the Python Software Foundation's,
install the official Python and recreate the environment
(`Remove-Item .venv -Recurse` and `uv sync`). For any tool installed into
`.venv`, run it as `python -m <tool>`.

If it appears in another library, **do not turn Smart App Control off**
lightly — it is irreversible, it only comes back by reinstalling Windows. Look
for a signed alternative first. To see what was blocked, Windows records each
block in the `Microsoft-Windows-CodeIntegrity/Operational` log.

To check its state:

```bat
reg query "HKLM\SYSTEM\CurrentControlSet\Control\CI\Policy" /v VerifiedAndReputablePolicyState
```

`0x1` means on and blocking.

**The disk is filling up**

The real rate is **~300 MB a day** (measured 30/09/2026, ARQUITETURA 8.6).
Set an archive folder in **Settings → Archive** — an external drive — and
events older than 30 days move there; it deletes only there, when that drive
fills (ARQUITETURA 11). Without one, nothing is deleted: the
recordings are in `clips/<camera>/<date>/`, one folder per day, and old days
can be deleted by hand. The buffer in `clips/_buffer/` cleans itself, and
`backups/` holds only what the tools saved.

## 9. Production and test (since 09/10/2026)

How it works and why: ARQUITETURA 18.

### 9.1 The two copies

| | Production | Test copy |
|---|---|---|
| Folder | `C:\JARVIS` | this project folder |
| Runs | always, started by Windows | only when you start it |
| Version | the latest **release tag**, reviewed | whatever is being written |
| Cameras | `stream1`, 1080p, records in HD | `stream2`, 640x360 |
| Page | `http://127.0.0.1:8765` (from another computer: `http://192.168.0.18:8765`) | `http://127.0.0.1:8766` |
| Telegram | on | off, prefix `[TEST]` |
| Commands from the phone (`/home`, `/away`…) | read by a thread, the only reader of the bot | none: no token, so the reader only sleeps |
| Desktop | **J.A.R.V.I.S.** opens it | **J.A.R.V.I.S. (test)** starts it |

Both can run at once: the camera serves `stream1` to one client and `stream2` to
several (ARQUITETURA 18.2). Each copy has its own recordings, faces and
settings — a name given in the test copy does not reach production.

### 9.2 Day to day

| Want | Do |
|---|---|
| Look at the cameras | the **J.A.R.V.I.S.** desktop shortcut |
| Is production all right? | `powershell -ExecutionPolicy Bypass -File tools\production.ps1 -Action status` |
| Stop it on purpose | `... -Action stop` — stays stopped, even after a reboot, until `start` |
| Start it again | `... -Action start` |
| Are the recordings still readable? | `... -Action check` |
| What happened? | `C:\JARVIS\logs\jarvis.log` |
| Change what reaches the phone | the page's **Settings → Notifications**, or `/home`, `/away`, `/silent` to the bot (ARQUITETURA 22) |
| Set up or check Telegram | **Settings → Notifications**: token, Find chat, Send test (ARQUITETURA 12.6) |

Stopping production any other way (Task Manager, ending the task) skips the
clean shutdown, and a clip being assembled at that moment is lost. Within
5 minutes Windows starts it again anyway, unless it was stopped with `stop`.

### 9.3 Updating

Updates are run by Claude, on request, after an architect review has tagged a
release (PROCESS 3). Never automatic: a failed update at night is a night
without surveillance.

```bat
powershell -ExecutionPolicy Bypass -File tools\production.ps1 -Action update
```

It checks that every recording and face is readable before and after, and if
the new version fails anything, it puts the previous one back and says so on
Telegram.

### 9.4 Installing on a new machine

From the project folder, after `instalar.bat` and with the program closed:

```bat
powershell -ExecutionPolicy Bypass -File tools\production.ps1 -Action install
```

Windows asks once for administrator permission, to register the startup task.
Refusing it leaves production running now, but it will not come back after a
reboot; register it later from an administrator PowerShell with
`-Action register`. If an install fails half-way, delete `C:\JARVIS` and run it
again.

### 9.5 When something is wrong

| Symptom | Look at |
|---|---|
| The page does not open | `-Action status`; if it says HELD, `-Action start`; otherwise `C:\JARVIS\logs\jarvis.log` |
| Another computer gets nothing, and the log says `Invalid HTTP request received` | the browser is trying `https://`; type `http://192.168.0.18:8765` (ARQUITETURA 17.8) |
| A camera shows "no signal" | its last frame is over 5 s old; the reason is written under it, and the camera reconnects on its own |
| Telegram message "update ... FAILED" | the previous version is back; the message says whether it is running |
| Black console windows titled `...site-packages\imageio_ffmpeg\...`, two that stay and others that flash | production's ffmpeg, visible when production was started by `production.ps1` instead of by Windows (ARQUITETURA 18.7). **Do not close them**: closing one of the two that stay cuts that camera until it reconnects, and closing a flashing one loses the clip being assembled. **Gone since `v2026.10.10`** (R15): seen on an older version, they disappear after a reboot |
