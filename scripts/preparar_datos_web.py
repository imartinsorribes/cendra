"""
Prepara los GeoJSON optimizados que sirve el frontend en `web/data/`.

  - `web/data/parques_bomberos.geojson`: copia de la capa propia.
  - `web/data/barris_riesgo.geojson`: barrios oficiales del Ajuntament
    enriquecidos con el riesgo medio del batch (`riesgo_por_barrio.csv`),
    su densidad de población y el índice de vulnerabilidad. Coordenadas
    en EPSG:4326. Las propiedades se reducen a las que el mapa necesita
    para no inflar el payload.

Uso:
    python scripts/preparar_datos_web.py
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import geopandas as gpd
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
RAW_LARGE = ROOT / "data" / "raw" / "large"
PROCESSED = ROOT / "data" / "processed"
WEB_DATA = ROOT / "web" / "data"
WEB_DATA.mkdir(parents=True, exist_ok=True)


def copiar_parques() -> None:
    shutil.copyfile(
        RAW / "parques_bomberos.geojson",
        WEB_DATA / "parques_bomberos.geojson",
    )
    print(f"  → {(WEB_DATA / 'parques_bomberos.geojson').relative_to(ROOT)}",
          file=sys.stderr)


def construir_barris_riesgo() -> None:
    barris = gpd.read_file(RAW_LARGE / "barris.geojson").to_crs("EPSG:4326")
    riesgo = pd.read_csv(PROCESSED / "riesgo_por_barrio.csv")

    # Cruzar por nombre
    barris = barris.merge(
        riesgo.rename(columns={"barrio": "nombre"}),
        on="nombre", how="left",
    )

    # Quedarnos con propiedades clave para el mapa
    cols_props = [
        "codbarrio", "nombre",
        "n_edificios", "riesgo_medio", "riesgo_p75", "riesgo_p90",
        "altura_media", "plantas_media",
        "dist_parque_media", "tiempo_llegada_medio",
        "densidad", "vulnerab",
    ]
    barris_out = barris[cols_props + ["geometry"]].copy()
    barris_out = barris_out.rename(columns={"nombre": "barrio"})

    # Para el coroplético se necesita el numérico; rellenar NaN suavemente
    for c in ["riesgo_medio", "riesgo_p75", "riesgo_p90"]:
        barris_out[c] = barris_out[c].fillna(0).round(1)

    # Simplificar geometría para reducir tamaño (tolerancia: ~10 m)
    # 10 m ≈ 0.0001° de latitud
    barris_out["geometry"] = barris_out.geometry.simplify(0.0001, preserve_topology=True)

    out = WEB_DATA / "barris_riesgo.geojson"
    barris_out.to_file(out, driver="GeoJSON")
    kb = out.stat().st_size / 1024
    print(
        f"  → {out.relative_to(ROOT)} ({kb:.0f} KB, {len(barris_out)} barrios)",
        file=sys.stderr,
    )

    # Pequeño informe de la distribución
    print("\nDistribución del riesgo por barrio:", file=sys.stderr)
    print(barris_out["riesgo_medio"].describe().to_string(), file=sys.stderr)
    print("\nTop 10 barrios por riesgo medio:", file=sys.stderr)
    top = barris_out.nlargest(10, "riesgo_medio")[
        ["barrio", "riesgo_medio", "n_edificios", "tiempo_llegada_medio"]
    ]
    print(top.to_string(index=False), file=sys.stderr)


def main() -> None:
    print("[1/2] copiar parques_bomberos.geojson", file=sys.stderr)
    copiar_parques()
    print("[2/2] construir barris_riesgo.geojson", file=sys.stderr)
    construir_barris_riesgo()


if __name__ == "__main__":
    main()
