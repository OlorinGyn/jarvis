"""Print the raid log comic, docs/raidlog/raidlog.html, to a PDF beside it.

Usage: uv run python tools/build_raidlog.py

Uses Microsoft Edge in headless mode, which every Windows machine here has,
so the comic needs no extra dependency. See docs/CONTEXTO.md section 15.
"""

import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "docs" / "raidlog" / "raidlog.html"
OUTPUT = SOURCE.with_name("JARVIS - Raid Log.pdf")
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


def main():
    edge = find_edge()
    OUTPUT.unlink(missing_ok=True)
    with tempfile.TemporaryDirectory() as profile:
        subprocess.run([str(edge), "--headless", "--disable-gpu", "--no-pdf-header-footer",
                        f"--user-data-dir={profile}", "--virtual-time-budget=15000",
                        f"--print-to-pdf={OUTPUT}", SOURCE.as_uri()],
                       check=False, capture_output=True, stdin=subprocess.DEVNULL)
    if not OUTPUT.exists():
        raise SystemExit("Edge did not write the PDF.")
    print(f"{OUTPUT.relative_to(ROOT)}  ({OUTPUT.stat().st_size / 1024:.0f} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
