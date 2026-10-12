"""Check that every "<DOC> <section>" reference lands on a heading of that document.

Usage: uv run python tools/check_doc_refs.py

The documents are every docs/*.md; each is referred to by its upper-case name,
as in "ARCHITECTURE 18.7", "docs/INSTALL.md section 8" or "`PROCESS.md` 3".
References are looked for in the documentation, README.md, CLAUDE.md, the
skills, src/ and tools/. Exits 1 when any reference points nowhere.
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NUMBER = r"\d+(?:\.\d+)*"
HEADING = re.compile(rf"^#+\s+({NUMBER})[.\s]")


def documents():
    """Each document's upper-case name and the section numbers of its headings."""
    found = {}
    for path in sorted((ROOT / "docs").glob("*.md")):
        lines = path.read_text(encoding="utf-8").splitlines()
        found[path.stem] = {m.group(1) for m in map(HEADING.match, lines) if m}
    return found


def sources():
    """Every file whose text may refer to a document's section."""
    paths = [ROOT / "README.md", ROOT / "CLAUDE.md"]
    paths += sorted((ROOT / "docs").rglob("*.md"))
    paths += sorted((ROOT / ".claude").rglob("*.md"))
    for folder in ("src", "tools"):
        paths += sorted((ROOT / folder).rglob("*.py"))
        paths += sorted((ROOT / folder).rglob("*.ps1"))
    return [p for p in paths if p.exists()]


def reference_pattern(names):
    """A regex for "<DOC>[.md][`] [section[s]] N[, N and N]"."""
    alternatives = "|".join(sorted(map(re.escape, names), key=len, reverse=True))
    numbers = rf"{NUMBER}(?:(?:,\s*|\s+and\s+){NUMBER})*"
    return re.compile(rf"\b({alternatives})(?:\.md)?`?,?\s+(?:sections?\s+)?({numbers})\b")


def broken_references(docs):
    """Every (file, line, reference) whose section is not a heading of its document."""
    pattern = reference_pattern(docs)
    broken = []
    for path in sources():
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            for match in pattern.finditer(line):
                name = match.group(1)
                for section in re.findall(NUMBER, match.group(2)):
                    if section not in docs[name]:
                        broken.append((path.relative_to(ROOT), number, f"{name} {section}"))
    return broken


def main():
    docs = documents()
    broken = broken_references(docs)
    for path, line, reference in broken:
        print(f"{path}:{line}: {reference} is not a heading")
    print(f"{len(broken)} broken reference(s) to {', '.join(docs)}")
    return 1 if broken else 0


if __name__ == "__main__":
    sys.exit(main())
