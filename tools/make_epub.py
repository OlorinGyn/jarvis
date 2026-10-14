"""Build one EPUB from the documents the user reads: ARCHITECTURE and PYTHON.

Usage: uv run python tools/make_epub.py

Produces docs/epub/JARVIS - Documentation.epub and nothing else: a single
book whose chapters are the documents, so cross references between them stay
one tap away on an e-reader. The .md files are never modified.

The EPUBs are not versioned and are not kept in sync; run this when you want a
fresh copy.
"""

import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "docs" / "epub" / "JARVIS - Documentation.epub"
CSS = ROOT / "tools" / "epub.css"

ORDER = ["docs/ARCHITECTURE.md", "docs/PYTHON.md"]


def find_pandoc():
    """Locate pandoc, which the winget install does not put on PATH."""
    found = shutil.which("pandoc")
    if found:
        return found
    candidates = [
        Path(os.environ.get("LOCALAPPDATA", "")) / "Pandoc" / "pandoc.exe",
        Path(r"C:\Program Files\Pandoc\pandoc.exe"),
    ]
    for path in candidates:
        if path.exists():
            return str(path)
    raise SystemExit(
        "pandoc not found.\n"
        "Install it with: winget install --id JohnMacFarlane.Pandoc -e")


def gather_documents():
    """The documents in ORDER, the user's list (14/10/2026); nothing else goes in."""
    return [ROOT / name for name in ORDER if (ROOT / name).exists()]


def verify(epub, documents):
    """Compare what landed in the book against what the sources held."""
    tables = code = 0
    with zipfile.ZipFile(epub) as package:
        for name in package.namelist():
            if name.endswith(".xhtml"):
                page = package.read(name).decode("utf-8", "replace")
                tables += page.count("<table")
                code += page.count("<pre")

    source_tables = source_code = 0
    for document in documents:
        text = document.read_text(encoding="utf-8")
        source_tables += sum(1 for l in text.splitlines() if l.lstrip().startswith("|---"))
        source_code += text.count("```") // 2

    print(f"  tables: {tables} (sources {source_tables})")
    print(f"  code:   {code} (sources {source_code})")
    return tables == source_tables and code == source_code


def main():
    pandoc = find_pandoc()
    documents = gather_documents()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    for old in OUTPUT.parent.glob("*.epub"):
        if old != OUTPUT:
            old.unlink()

    print(f"{len(documents)} document(s), in this order:")
    for document in documents:
        print(f"  {document.relative_to(ROOT)}")

    command = [pandoc, *[str(d) for d in documents], "-o", str(OUTPUT),
               "--from=gfm", "--to=epub3", "--toc", "--toc-depth=2",
               "--top-level-division=chapter", f"--css={CSS}",
               "--metadata", "title=J.A.R.V.I.S. - Documentation",
               "--metadata", "author=J.A.R.V.I.S.",
               "--metadata", "lang=en"]
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode or not OUTPUT.exists():
        print(result.stderr[:600])
        raise SystemExit("could not build the epub")

    print(f"\n{OUTPUT.relative_to(ROOT)}  ({OUTPUT.stat().st_size / 1024:.0f} KB)")
    intact = verify(OUTPUT, documents)
    print("  " + ("nothing was lost in the join" if intact
                  else "WARNING: the counts differ, check the result"))
    return 0 if intact else 1


if __name__ == "__main__":
    sys.exit(main())
