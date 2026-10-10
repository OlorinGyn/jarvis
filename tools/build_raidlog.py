"""Print the raid log comic, docs/raidlog/raidlog.html, to one PDF per language.

Usage: uv run python tools/build_raidlog.py

The comic keeps English and Portuguese side by side in the same file; the page
shows one of them according to ?lang=. Edge in headless mode prints each, so
nothing has to be installed. See docs/CONTEXTO.md section 15.
"""

import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "docs" / "raidlog" / "raidlog.html"
LANGUAGES = {"en": "JARVIS - Raid Log (EN).pdf", "pt": "JARVIS - Raid Log (PT).pdf"}
EDGE_CANDIDATES = [
    Path(os.environ.get("ProgramFiles(x86)", "")) / "Microsoft/Edge/Application/msedge.exe",
    Path(os.environ.get("ProgramFiles", "")) / "Microsoft/Edge/Application/msedge.exe",
]


def find_edge():
    """Locate msedge.exe in its usual install folders."""
    for candidate in EDGE_CANDIDATES:
        if candidate.exists():
            return candidate
    raise SystemExit("Microsoft Edge not found.")


def print_pdf(edge, language, output):
    """Have Edge print the comic in one language."""
    output.unlink(missing_ok=True)
    with tempfile.TemporaryDirectory() as profile:
        subprocess.run([str(edge), "--headless", "--disable-gpu", "--no-pdf-header-footer",
                        f"--user-data-dir={profile}", "--virtual-time-budget=15000",
                        f"--print-to-pdf={output}", f"{SOURCE.as_uri()}?lang={language}"],
                       check=False, capture_output=True, stdin=subprocess.DEVNULL)
    if not output.exists():
        raise SystemExit(f"Edge did not write {output.name}.")
    print(f"{output.relative_to(ROOT)}  ({output.stat().st_size / 1024:.0f} KB)")


def main():
    edge = find_edge()
    for language, name in LANGUAGES.items():
        print_pdf(edge, language, SOURCE.with_name(name))
    return 0


if __name__ == "__main__":
    sys.exit(main())
