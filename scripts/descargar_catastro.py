"""
Descarga la cartografía catastral INSPIRE de València (municipio 46900).
Contiene tres capas GML clave para el atlas de riesgo de incendio:

  - building.gml          → un polígono por edificio, con `numberOfDwellings`,
                            `numberOfBuildingUnits`, `currentUse`, año de
                            construcción. Base de la calculadora de riesgo.
  - buildingpart.gml      → un polígono por parte de edificio, con
                            `numberOfFloorsAboveGround`. Permite estimar
                            altura para cada huella.
  - otherconstruction.gml → construcciones auxiliares (cobertizos, garajes
                            exteriores...). No se usa por ahora.

Pipeline:
  1. Resuelve la URL del ZIP en el Atom feed de Catastro (provincia 46).
  2. Descarga el ZIP a `data/external/catastro/A.ES.SDGC.BU.46900.zip`.
  3. Lo descomprime y deja los GML listos para `extraer_alturas_ciudad.py`
     y `extraer_viviendas.py`.
"""
from __future__ import annotations

import sys
import zipfile
from pathlib import Path

import requests
import urllib3
from lxml import etree

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

ROOT = Path(__file__).resolve().parent.parent
EXT = ROOT / "data" / "external" / "catastro"
EXT.mkdir(parents=True, exist_ok=True)
PROCESSED = ROOT / "data" / "processed"
PROCESSED.mkdir(parents=True, exist_ok=True)

ATOM_46 = "https://www.catastro.hacienda.gob.es/INSPIRE/buildings/46/ES.SDGC.BU.atom_46.xml"
UA = "cendra-fetch/0.1 (+https://github.com/imartinsorribes/cendra)"
MUNICIPIO = "46900-VALENCIA"
ALTURA_PLANTA_M = 3.0


def resolver_url_zip() -> str:
    """Lee el Atom feed y devuelve la URL del ZIP del municipio."""
    r = requests.get(ATOM_46, headers={"User-Agent": UA}, timeout=60, verify=False)
    r.raise_for_status()
    root = etree.fromstring(r.content)
    ns = {"a": "http://www.w3.org/2005/Atom"}
    for entry in root.findall("a:entry", ns):
        title = (entry.find("a:title", ns).text or "").strip()
        if MUNICIPIO.split("-")[0] in title:
            for link in entry.findall("a:link", ns):
                if link.get("rel") in (None, "enclosure"):
                    href = link.get("href")
                    if href and href.endswith(".zip"):
                        return href
    raise RuntimeError(f"No se encontró ZIP para {MUNICIPIO} en el Atom feed")


def descargar(url: str, dst: Path) -> None:
    if dst.exists() and dst.stat().st_size > 1024:
        print(f"[skip] {dst.name} ya existe ({dst.stat().st_size // 1024 // 1024} MB)",
              file=sys.stderr)
        return
    print(f"[fetch] {url}", file=sys.stderr)
    with requests.get(url, headers={"User-Agent": UA}, timeout=300, stream=True,
                      verify=False) as r:
        r.raise_for_status()
        total = 0
        with dst.open("wb") as f:
            for chunk in r.iter_content(chunk_size=1024 * 1024):
                f.write(chunk)
                total += len(chunk)
                if total % (10 * 1024 * 1024) < 1024 * 1024:
                    print(f"  ... {total // 1024 // 1024} MB", file=sys.stderr)
    print(f"[ok] {dst.stat().st_size // 1024 // 1024} MB -> {dst}", file=sys.stderr)


def descomprimir(zip_path: Path) -> Path:
    """Extrae el ZIP y devuelve la ruta al GML 'building.gml' principal."""
    out_dir = zip_path.with_suffix("")
    out_dir.mkdir(exist_ok=True)
    with zipfile.ZipFile(zip_path) as z:
        z.extractall(out_dir)
        print(f"[zip] extraído en {out_dir.name}/", file=sys.stderr)
    # Buscar el GML de buildings (no buildingpart ni otherconstruction)
    candidatos = list(out_dir.glob("A.ES.SDGC.BU.*.building.gml"))
    if not candidatos:
        candidatos = list(out_dir.glob("*.building.gml"))
    if not candidatos:
        candidatos = list(out_dir.glob("*.gml"))
    if not candidatos:
        raise FileNotFoundError(f"No hay GML en {out_dir}")
    return candidatos[0]


def main() -> None:
    print(f"=== Catastro INSPIRE Buildings · {MUNICIPIO} ===", file=sys.stderr)
    url = resolver_url_zip()
    print(f"URL: {url}", file=sys.stderr)

    zip_path = EXT / f"A.ES.SDGC.BU.46900.zip"
    descargar(url, zip_path)

    gml = descomprimir(zip_path)
    print(f"GML principal: {gml.name}  ({gml.stat().st_size // 1024 // 1024} MB)",
          file=sys.stderr)

    # Lectura: aplazamos geopandas para no penalizar quien solo quiere
    # descargar. Se hace en `scripts/extraer_alturas.py`.
    print("\nDescarga completa. El parsing del GML se hace en "
          "scripts/extraer_alturas.py.", file=sys.stderr)


if __name__ == "__main__":
    main()
