"""
Prepara los GeoJSON optimizados que sirve el frontend en `web/data/`.

  - `web/data/parques_bomberos.geojson`: copia de la capa propia.
  - `web/data/barris_riesgo.geojson`: barrios oficiales del Ajuntament
    enriquecidos con el riesgo medio del batch (`riesgo_por_barrio.csv`),
    su densidad de población y el índice de vulnerabilidad.
  - `web/data/edificios_top_riesgo.geojson`: TOP-2000 edificios de
    mayor riesgo del batch, geometría centrada y simplificada. Sirve
    como capa de hotspots en el mapa para que se vean a nivel calle.

Coordenadas en EPSG:4326. Las propiedades se reducen a las que el
mapa necesita para no inflar el payload.

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


def copiar_hidrantes() -> None:
    """Copia los 1.923 hidrantes municipales al frontend para que el plan
    de respuesta pueda mostrar los 3 más cercanos a cualquier edificio."""
    src = RAW_LARGE / "hidrants.geojson"
    if not src.exists():
        print("  [skip] hidrants.geojson ausente en data/raw/large/",
              file=sys.stderr)
        return
    dst = WEB_DATA / "hidrants.geojson"
    shutil.copyfile(src, dst)
    kb = dst.stat().st_size / 1024
    print(f"  → {dst.relative_to(ROOT)} ({kb:.0f} KB)", file=sys.stderr)


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


def construir_edificios_top() -> None:
    """Extrae los TOP-2000 edificios de mayor riesgo como puntos
    (centroide) para mostrar como hotspots en el mapa."""
    gpkg = PROCESSED / "riesgo_edificios.gpkg"
    if not gpkg.exists():
        print("  [skip] riesgo_edificios.gpkg ausente. "
              "Ejecuta antes calcular_riesgo_batch.py.", file=sys.stderr)
        return
    edif = gpd.read_file(gpkg, layer="riesgo")
    n_top = min(2000, len(edif))
    top = edif.nlargest(n_top, "riesgo").copy()
    # Sólo el centroide para que sea ligero
    top["geometry"] = top.geometry.representative_point()
    top = top.to_crs("EPSG:4326")
    cols = [
        "localId", "plantas", "altura_m", "anio_construccion",
        "barrio", "parque_cercano", "tiempo_llegada_min",
        "dist_parque_m", "dist_hidrante_m",
        "V_intrinseca", "E_exposicion", "R_respuesta", "riesgo",
        "geometry",
    ]
    cols_disp = [c for c in cols if c in top.columns]
    top_out = top[cols_disp].copy()
    out = WEB_DATA / "edificios_top_riesgo.geojson"
    top_out.to_file(out, driver="GeoJSON")
    kb = out.stat().st_size / 1024
    print(
        f"  → {out.relative_to(ROOT)} ({kb:.0f} KB, {len(top_out)} edificios)",
        file=sys.stderr,
    )
    print(
        f"  rango de riesgo en el top: "
        f"{top_out['riesgo'].min():.1f} - {top_out['riesgo'].max():.1f}",
        file=sys.stderr,
    )


def main() -> None:
    print("[1/4] copiar parques_bomberos.geojson", file=sys.stderr)
    copiar_parques()
    print("[2/4] copiar hidrants.geojson (para hidrantes operativos en el plan SPEIS)",
          file=sys.stderr)
    copiar_hidrantes()
    print("[3/4] construir barris_riesgo.geojson", file=sys.stderr)
    construir_barris_riesgo()
    print("[4/4] construir edificios_top_riesgo.geojson", file=sys.stderr)
    construir_edificios_top()


if __name__ == "__main__":
    main()
