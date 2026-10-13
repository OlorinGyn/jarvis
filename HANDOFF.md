# Handoff - developer to architect

Developer session 16, 12/10/2026, night. The plan in BACKLOG 3, both items,
in order.

## 1. Items done

**Delete `jarvis_vigilancia.bat`** — `9096e8f`. A search of the repository
outside `docs/`, `.git` and `.venv` found no file naming it, so it went with
`git rm` and nothing else changed. The docs still name it (README, INSTALL,
ARCHITECTURE wherever the launchers are listed): those are the architect's.

**R7, `install.bat` checks the Python** — `e426c8b`. Closes R7.

- New `tools/check_python.ps1 -Path <exe>`: exits 0 and prints one line when
  the file's Authenticode signature is `Valid` and the signer's subject names
  the Python Software Foundation; otherwise prints the status and a pointer
  to `docs/INSTALL.md section 1.2` and exits 1. A missing file fails with
  "was not found" instead of a raw PowerShell error record.
- `install.bat`: right after `uv sync` succeeds (inside step 4), runs the
  script on `.venv\Scripts\python.exe`; on failure explains that step 3
  probably failed and stops (`pause`, `exit /b 1`).
- `production.ps1` `Sync`: the inline test (old line 128) now calls the same
  script on `pythonw.exe`, keeping its `throw` and message. The rule is
  written once. I chose the shared script over a one-line PowerShell in the
  `.bat` for that reason.

## 2. Data-format impact

None: no file under `clips/`, `faces/`, `config.json` or `.env` is read or
written by these changes. `check_data.py` not needed. `check_doc_refs.py`: 0
broken references (the new message names INSTALL 1.2).

## 3. Suggested documentation updates

- **README / INSTALL / ARCHITECTURE**: drop `jarvis_vigilancia.bat` from every
  list of launchers and from the R10 note about the one-release shim.
- **INSTALL 1.2** (and the install steps list, if it describes step 4): the
  installer now stops when the venv's Python is unsigned; the fix is the one
  1.2 already describes (official Python, recreate `.venv`).
- **ARCHITECTURE 19.5** or wherever `production.ps1`'s signature check is
  described: it now lives in `tools/check_python.ps1`, shared with the
  installer. Add the new tool to any tools list.
- **BACKLOG 2**: R7 closed; HISTORY 13.4's R7 text can point at `e426c8b`.

## 4. Worth explaining to the user

- **Authenticode** (`Get-AuthenticodeSignature`): Windows' code-signing
  check, the same idea as a signed JAR or a strong-named, Authenticode-signed
  .NET assembly. Smart App Control trusts signed binaries; `uv`'s own Python
  and its `.exe` launchers are unsigned.
- **Exit codes between `.bat` and PowerShell**: `exit 1` in a `.ps1` run with
  `powershell -File` becomes the process exit code, which `cmd` reads as
  `errorlevel`; `if errorlevel 1` means "1 or more". Inside PowerShell, `&
  script.ps1` sets `$LASTEXITCODE`, which `production.ps1` turns into a
  `throw` — like checking `Process.ExitCode` in C# and throwing.

## 5. Measurements (acceptance)

| File in this `.venv\Scripts` | Result | Exit |
|---|---|---|
| `python.exe` | signed by the PSF | 0 |
| `pythonw.exe` | signed by the PSF | 0 |
| `jarvis.exe` | `NotSigned` | 1 |
| `pytest.exe` | `NotSigned` | 1 |
| `missing.exe` | not found | 1 |

Through a test `.bat` with the same lines as `install.bat`: `python.exe` →
success branch, exit 0; `jarvis.exe` → failure branch, exit 1. Through
`production.ps1`'s call pattern (`& … | Out-Host; if ($LASTEXITCODE) { throw
}`): `pythonw.exe` passes, `jarvis.exe` throws. `production.ps1` parses with 0
errors and `-Action status` still runs. `install.bat` was not run end to end,
as the plan said. No Python changed, so the test suite was not run.

## 6. Where the review should look hardest

- `production.ps1` `Sync` during a real deploy: the only path not exercised
  end to end. It resolves the script through `$PSScriptRoot`, so it uses the
  development folder's `tools\check_python.ps1`, which is where
  `production.ps1` itself runs from.
- `tools/check_python.ps1` and the `production.ps1` edit have LF endings in
  the working copy (git warns it will write CRLF); `install.bat` kept CRLF.

## 7. Plan items not done

None.

## 8. Usage

| | 5-hour window | Weekly |
|---|---|---|
| Start | 60 % (resets 03:40 UTC) | 8 % |
| End | 61 % | 9 % |

Context at the end: about 81 k tokens.
