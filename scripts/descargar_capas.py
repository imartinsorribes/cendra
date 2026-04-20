"""
Descarga las capas geoespaciales del portal de datos abiertos del
Ayuntamiento de València (CKAN / ArcGIS REST en geoportal.valencia.es)
necesarias para el atlas de riesgo de incendio urbano.

Las capas grandes se guardan en `data/raw/large/` (ignorado por git) y
las pequeñas en `data/raw/`. El script es reproducible: si lo vuelves a
ejecutar, regenera lo que falte y deja en paz lo que ya está descargado.

Los identificadores del MapServer fueron verificados el 2026-05-14
contra los metadatos del propio servicio (`?f=json`). Ver
`docs/hallazgos-exploracion.md` para la trazabilidad de cada elección.

Endpoints ArcGIS REST paginan con `resultOffset` y `resultRecordCount`.
La cabecera de respuesta `exceededTransferLimit` indica si quedan más
features por descargar.

Capa ausente del portal: **parques de bomberos**. Se construirá a mano
en `data/raw/parques_bomberos.geojson` desde fuentes oficiales (SPEIS
del Ajuntament + Consorcio Provincial), ver el documento de hallazgos.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "raw" / "large"
OUT.mkdir(parents=True, exist_ok=True)

UA = "cendra-fetch/0.1 (+https://github.com/imartinsorribes/cendra)"
PAGE_SIZE = 1000  # máximo habitual del MapServer

# Capas con su MapServer/layer del geoportal y nombre de archivo de salida.
CAPAS_ARCGIS: list[tuple[str, str, int, str]] = [
    # (clave, base_url, layer_id, fichero_salida)
    # --- Núcleo del modelo ---
    ("hidrants", "UrbanismoEInfraestructuras", 222, "hidrants.geojson"),
    ("fites_bombers", "Trafico", 239, "fites_bombers.geojson"),
    # --- Geometría base ---
    ("barris", "UrbanismoEInfraestructuras", 224, "barris.geojson"),
    ("edificis", "UrbanismoEInfraestructuras", 112, "edificis.geojson"),
    # --- Equipamientos sensibles ---
    # `equipamientos` clase 'Instalaciones sanitarias', 'Bienestar Social',
    # 'Instalaciones educativas' son las relevantes para nuestro modelo.
    ("equipamientos", "SociedadBienestar", 1, "equipamientos.geojson"),
    ("majors", "SociedadBienestar", 24, "majors.geojson"),
    # --- Contexto de tráfico (acceso de emergencia) ---
    ("area_prioridad_residencial", "Trafico", 1, "area_prioridad_residencial.geojson"),
]

# Recursos servidos como archivo estático (legacy /apps/OpenData/... o
# /dataset/.../download/...).
CAPAS_LEGACY: list[tuple[str, str, str]] = [
    (
        "vulnerabilitat_barris",
        "https://opendata.vlci.valencia.es/dataset/ca18278b-d040-4274-b9c7-c1a9daae54b9/"
        "resource/fd2ca0dc-5344-4aad-8934-2077a0bb120d/download/vulnerabilidad-por-barrios.geojson",
        "vulnerabilitat_barris.geojson",
    ),
    (
        "hospitales",
        "https://opendata.vlci.valencia.es/dataset/c389b148-0fad-46b2-8c7b-f5c5aa866a65/"
        "resource/82588e44-2ba8-4038-9bc9-5fb1ce2428d2/download/hospitales.geojson",
        "hospitales.geojson",
    ),
    (
        "centros_educativos",
        "https://opendata.vlci.valencia.es/dataset/11436f0c-082b-4e5b-9659-005f5b528bde/"
        "resource/938e34b7-bb7d-4b0c-8176-3602d47ebd6a/download/centros-educativos-en-valencia.geojson",
        "centros_educativos.geojson",
    ),
    (
        "manzanas_poblacion",
        "https://geoportal.valencia.es/apps/OpenData/UrbanismoEInfraestructuras/MANZANAS.json",
        "manzanas_poblacion.geojson",
    ),
]


def url_query(base: str, layer_id: int, offset: int) -> str:
    return (
        f"https://geoportal.valencia.es/server/rest/services/OPENDATA/{base}/"
        f"MapServer/{layer_id}/query?"
        f"where=1%3D1&outFields=*&f=geojson&outSR=4326&"
        f"resultOffset={offset}&resultRecordCount={PAGE_SIZE}"
    )


def descargar_arcgis(clave: str, base: str, layer_id: int, dst: Path) -> int:
    """Descarga paginada una capa de ArcGIS REST → GeoJSON único."""
    features: list[dict] = []
    offset = 0
    crs = None
    while True:
        url = url_query(base, layer_id, offset)
        r = requests.get(url, headers={"User-Agent": UA}, timeout=120)
        r.raise_for_status()
        data = r.json()
        if "features" not in data:
            print(f"  [!] respuesta inesperada en offset {offset}: {list(data.keys())}",
                  file=sys.stderr)
            break
        batch = data["features"]
        features.extend(batch)
        crs = crs or data.get("crs")
        exceeded = data.get("exceededTransferLimit", False) or len(batch) >= PAGE_SIZE
        print(f"  [{clave}] offset={offset:>6}  +{len(batch):>4}  total={len(features)}",
              file=sys.stderr)
        if not exceeded:
            break
        offset += len(batch)
        time.sleep(0.2)  # cortesía con el servidor

    out = {"type": "FeatureCollection", "crs": crs, "features": features}
    dst.write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
    return len(features)


def descargar_legacy(clave: str, url: str, dst: Path) -> int:
    r = requests.get(url, headers={"User-Agent": UA}, timeout=300)
    r.raise_for_status()
    dst.write_bytes(r.content)
    try:
        data = json.loads(r.content)
        n = len(data.get("features", []))
    except Exception:
        n = -1
    return n


def main() -> None:
    print(f"=== Descarga geoespacial en {OUT} ===", file=sys.stderr)
    total = 0
    for clave, base, layer_id, fname in CAPAS_ARCGIS:
        dst = OUT / fname
        if dst.exists() and dst.stat().st_size > 1024:
            print(f"[skip] {clave} ya existe ({dst.stat().st_size // 1024} KB)", file=sys.stderr)
            continue
        try:
            n = descargar_arcgis(clave, base, layer_id, dst)
            print(f"[ok]   {clave}: {n} features -> {dst.name}", file=sys.stderr)
            total += n
        except Exception as e:
            print(f"[ERR]  {clave}: {e}", file=sys.stderr)

    for clave, url, fname in CAPAS_LEGACY:
        dst = OUT / fname
        if dst.exists() and dst.stat().st_size > 1024:
            print(f"[skip] {clave} ya existe ({dst.stat().st_size // 1024} KB)", file=sys.stderr)
            continue
        try:
            n = descargar_legacy(clave, url, dst)
            print(f"[ok]   {clave}: {n} features -> {dst.name}", file=sys.stderr)
            total += max(n, 0)
        except Exception as e:
            print(f"[ERR]  {clave}: {e}", file=sys.stderr)

    print(f"\nTotal features descargados: {total}", file=sys.stderr)


if __name__ == "__main__":
    main()
