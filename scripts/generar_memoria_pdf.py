"""Genera la memoria del Anexo II en PDF a partir del Markdown.

Pipeline en dos fases (sin LaTeX, solo Chrome headless + pandoc):
  1. Markdown  ->  HTML standalone con CSS de imprenta (pandoc + pypandoc)
  2. HTML      ->  PDF (Chrome headless con --print-to-pdf)

Salidas: docs/memoria/anexo-ii.html, docs/memoria/anexo-ii.pdf

Requisitos:
  pip install pypandoc-binary
  Chrome o Chromium instalado en una ruta estándar de Windows / Linux / macOS.

Uso:
  python scripts/generar_memoria_pdf.py
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "docs" / "memoria" / "anexo-ii.md"
HTML = ROOT / "docs" / "memoria" / "anexo-ii.html"
PDF = ROOT / "docs" / "memoria" / "anexo-ii.pdf"
CSS_REL = "estilo-imprenta.css"

CHROME_CANDIDATES = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/usr/bin/google-chrome",
    "/usr/bin/chromium",
    "/usr/bin/chromium-browser",
]


def _localizar_chrome() -> str | None:
    for c in CHROME_CANDIDATES:
        if Path(c).exists():
            return c
    # Última oportunidad: PATH
    for name in ("chrome", "chromium", "google-chrome", "msedge"):
        p = shutil.which(name)
        if p:
            return p
    return None


def md_a_html() -> None:
    import pypandoc
    pypandoc.convert_file(
        str(SRC),
        "html5",
        outputfile=str(HTML),
        extra_args=[
            "--standalone",
            "--metadata=title:cendra · Atlas paramétrico de riesgo de incendio en València · Anexo II",
            "--metadata=lang:es",
            "--toc", "--toc-depth=2",
            "--number-sections",
            "-c", CSS_REL,
        ],
    )
    print(f"  -> {HTML.relative_to(ROOT)} ({HTML.stat().st_size / 1024:.0f} KB)")


def html_a_pdf() -> None:
    chrome = _localizar_chrome()
    if not chrome:
        sys.exit("Error: no se ha encontrado Chrome / Chromium en este sistema. "
                 "Genera el HTML y abre `anexo-ii.html` en el navegador, "
                 "luego «Imprimir -> Guardar como PDF».")
    cmd = [
        chrome,
        "--headless",
        "--disable-gpu",
        "--no-sandbox",
        f"--print-to-pdf={PDF}",
        "--print-to-pdf-no-header",
        HTML.as_uri(),
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    kb = PDF.stat().st_size / 1024
    print(f"  -> {PDF.relative_to(ROOT)} ({kb:.0f} KB)")


def main() -> None:
    if not SRC.exists():
        sys.exit(f"No existe {SRC}")
    print(f"[1/2] {SRC.name} -> {HTML.name}")
    md_a_html()
    print(f"[2/2] {HTML.name} -> {PDF.name}")
    html_a_pdf()
    print("\nMemoria generada. Abre el PDF para verificarlo:")
    print(f"  start \"\" \"{PDF}\"")


if __name__ == "__main__":
    main()
