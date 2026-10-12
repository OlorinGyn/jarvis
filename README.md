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
instalar.bat
jarvis.bat
```

`instalar.bat` installs what is missing (including the signed official
Python, which Windows' Smart App Control requires), downloads the models and
creates `.env`, where each camera's IP and credentials go. `jarvis.bat` starts
the service and opens the page; `jarvis_vigilancia.bat` starts only the
service. Details, and running it as an always-on production copy that starts
with Windows, in [docs/INSTALACAO.md](docs/INSTALACAO.md).

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
| [INSTALACAO.md](docs/INSTALACAO.md) | Install, configure, run in production, troubleshoot |
| [ARQUITETURA.md](docs/ARQUITETURA.md) | How it works and why, layer by layer |
| [PYTHON.md](docs/PYTHON.md) | Python and the libraries, for someone coming from Java or C# |
| [CONTEXTO.md](docs/CONTEXTO.md) | The rules, decisions, backlog and plan — read first |
| [HISTORY.md](docs/HISTORY.md) | Bugs fixed, every review, closed recommendations |
