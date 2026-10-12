"""Build one EPUB from every markdown file in the project.

Usage: uv run python tools/make_epub.py

Produces docs/epub/JARVIS - Documentacao Completa.epub and nothing else: a
single book whose chapters are the documents, so cross references between them
stay one tap away on an e-reader. The .md files are never modified.

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
SAIDA = ROOT / "docs" / "epub" / "JARVIS - Documentacao Completa.epub"
CSS = ROOT / "tools" / "epub.css"

ORDEM = ["README.md", "docs/CONTEXT.md", "docs/ARCHITECTURE.md",
         "docs/INSTALL.md", "docs/PYTHON.md", "CLAUDE.md"]


def achar_pandoc():
    """Locate pandoc, which the winget install does not put on PATH."""
    encontrado = shutil.which("pandoc")
    if encontrado:
        return encontrado
    candidatos = [
        Path(os.environ.get("LOCALAPPDATA", "")) / "Pandoc" / "pandoc.exe",
        Path(r"C:\Program Files\Pandoc\pandoc.exe"),
    ]
    for caminho in candidatos:
        if caminho.exists():
            return str(caminho)
    raise SystemExit(
        "pandoc nao encontrado.\n"
        "Instale com: winget install --id JohnMacFarlane.Pandoc -e")


def reunir_documentos():
    """Every .md in the project, preferred ones first, new ones after."""
    todos = sorted(
        p for p in list(ROOT.glob("*.md")) + list((ROOT / "docs").glob("*.md"))
        if "epub" not in p.parts)

    ordenados = []
    for nome in ORDEM:
        caminho = ROOT / nome
        if caminho.exists():
            ordenados.append(caminho)
    for caminho in todos:
        if caminho not in ordenados:
            ordenados.append(caminho)
    return ordenados


def conferir(epub, documentos):
    """Compare what landed in the book against what the sources held."""
    tabelas = codigo = 0
    with zipfile.ZipFile(epub) as pacote:
        for nome in pacote.namelist():
            if nome.endswith(".xhtml"):
                pagina = pacote.read(nome).decode("utf-8", "replace")
                tabelas += pagina.count("<table")
                codigo += pagina.count("<pre")

    origem_tabelas = origem_codigo = 0
    for documento in documentos:
        texto = documento.read_text(encoding="utf-8")
        origem_tabelas += sum(1 for l in texto.splitlines() if l.lstrip().startswith("|---"))
        origem_codigo += texto.count("```") // 2

    print(f"  tabelas: {tabelas} (origem {origem_tabelas})")
    print(f"  codigo:  {codigo} (origem {origem_codigo})")
    return tabelas == origem_tabelas and codigo == origem_codigo


def main():
    pandoc = achar_pandoc()
    documentos = reunir_documentos()
    SAIDA.parent.mkdir(parents=True, exist_ok=True)

    for antigo in SAIDA.parent.glob("*.epub"):
        if antigo != SAIDA:
            antigo.unlink()

    print(f"{len(documentos)} documento(s), na ordem:")
    for documento in documentos:
        print(f"  {documento.relative_to(ROOT)}")

    comando = [pandoc, *[str(d) for d in documentos], "-o", str(SAIDA),
               "--from=gfm", "--to=epub3", "--toc", "--toc-depth=2",
               "--top-level-division=chapter", f"--css={CSS}",
               "--metadata", "title=J.A.R.V.I.S. - Documentacao Completa",
               "--metadata", "author=J.A.R.V.I.S.",
               "--metadata", "lang=pt-BR"]
    resultado = subprocess.run(comando, capture_output=True, text=True)
    if resultado.returncode or not SAIDA.exists():
        print(resultado.stderr[:600])
        raise SystemExit("falha ao gerar o epub")

    print(f"\n{SAIDA.relative_to(ROOT)}  ({SAIDA.stat().st_size / 1024:.0f} KB)")
    intacto = conferir(SAIDA, documentos)
    print("  " + ("nada se perdeu na juncao" if intacto
                  else "ATENCAO: a contagem divergiu, confira o resultado"))
    return 0 if intacto else 1


if __name__ == "__main__":
    sys.exit(main())
