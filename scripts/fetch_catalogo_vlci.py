"""
Equivalente Python de `scripts/fetch_catalogo_vlci.ps1`. Descarga
reproducible del catálogo CKAN del portal de datos abiertos de
València (`opendata.vlci.valencia.es`).

Se ofrece la versión Python para entornos sin PowerShell (Linux, macOS,
CI). Las dos versiones generan archivos byte-equivalentes.

Uso:
    python scripts/fetch_catalogo_vlci.py
"""
from __future__ import annotations

import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "raw"
OUT.mkdir(parents=True, exist_ok=True)

BASE = "https://opendata.vlci.valencia.es"
UA = "cendra-fetch/0.1 (+https://github.com/imartinsorribes/cendra)"

ENDPOINTS: list[tuple[str, str]] = [
    (f"{BASE}/api/3/action/package_search?rows=1000&start=0", "ckan_package_search_0.json"),
    (f"{BASE}/api/3/action/package_list", "ckan_package_list.json"),
    (f"{BASE}/api/3/action/group_list?all_fields=true", "ckan_group_list.json"),
    (f"{BASE}/api/3/action/organization_list?all_fields=true", "ckan_organization_list.json"),
    (f"{BASE}/catalog.xml", "ckan_catalog_dcat.xml"),
]


def fetch(url: str, dst: Path) -> None:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    print(f"[fetch] {url} -> {dst}", file=sys.stderr)
    with urllib.request.urlopen(req, timeout=120) as resp, dst.open("wb") as f:
        while chunk := resp.read(64 * 1024):
            f.write(chunk)


def main() -> None:
    for url, name in ENDPOINTS:
        fetch(url, OUT / name)
    print("OK", file=sys.stderr)


if __name__ == "__main__":
    main()
