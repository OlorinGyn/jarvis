<img src="assets/jarvis.png" width="96" align="right" alt="">

# J.A.R.V.I.S.

Home surveillance with TP-Link Tapo cameras over RTSP. It detects motion,
decides whether it is a person or an animal, records the event without
re-encoding the camera's video, recognises faces and the household's dogs,
and sends what matters to the phone through Telegram — with Home, Away and
Silent modes that leave out the people and dogs who live there.

Everything runs as one service with a web page, from the same computer or any
device on the home network:

| Tab | What it does |
|---|---|
| **Live** | both cameras, live |
| **Recordings** | the events by day, with who appeared; plays and seeks each clip |
| **People** | the named people and the unnamed faces; name, merge, choose the views that recognise them |
| **Dogs** | the same for the household's dogs |
| **Settings** | first **Notifications** — what reaches the phone in each mode, and the Telegram setup — then pairing other devices, the archive, bad-detection reports |

From the phone, `/home`, `/away` and `/silent` sent to the bot switch the mode.

## Getting started

```bat
git clone https://github.com/OlorinGyn/jarvis.git
cd jarvis
install.bat
jarvis.bat
```

`install.bat` installs what is missing (including the signed official
Python, which Windows' Smart App Control requires), downloads the models and
creates `.env`, where each camera's IP and credentials go. `jarvis.bat` starts
the service and opens the page; `jarvis_headless.bat` starts only the
service. Details, and running it as an always-on production copy that starts
with Windows, in [docs/INSTALL.md](docs/INSTALL.md).

## Structure

```
src/jarvis/   the program
tests/        automatic tests: uv run python -m pytest
tools/        production, data checks, diagnosis, tuning, the EPUB
assets/       the icon
docs/         all the documentation
```

## Documentation

| Document | Contents |
|---|---|
| [INSTALL.md](docs/INSTALL.md) | Install, configure, run in production, troubleshoot |
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | How it works and why, layer by layer |
| [PYTHON.md](docs/PYTHON.md) | Python and the libraries, for someone coming from Java or C# |
| [CONTEXT.md](docs/CONTEXT.md) | The project's decisions, limitations and map — read first |
| [PROCESS.md](docs/PROCESS.md) | How the work is done: the user's rules, the developer and the architect |
| [BACKLOG.md](docs/BACKLOG.md) | The backlog, the open recommendations and the next sessions |
| [PENDING.md](docs/PENDING.md) | What waits for the user's decision |
| [HISTORY.md](docs/HISTORY.md) | Bugs fixed, every review, closed recommendations, the usage log |
