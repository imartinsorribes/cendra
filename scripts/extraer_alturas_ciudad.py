"""
Extrae los edificios 3D del catastro para toda Valencia (no solo Ruzafa).
Salida: data/processed/edificios_3d_valencia.gpkg

Solo hace falta correrlo una vez. Después, procesar_ciudad.py carga
directamente este gpkg sin tocar el GML de 537 MB.
"""
from __future__ import annotations

import sys
from pathlib import Path

import fiona
import geopandas as gpd
from shapely.geometry import shape
from shapely.validation import make_valid

ROOT = Path(__file__).resolve().parent.parent
GML = (ROOT / "data" / "external" / "catastro" / "A.ES.SDGC.BU.46900"
       / "A.ES.SDGC.BU.46900.buildingpart.gml")
OUT = ROOT / "data" / "processed" / "edificios_3d_valencia.gpkg"
ALTURA_PLANTA = 3.0


def main():
    if not GML.exists():
        sys.exit(f"falta {GML}")

    print("streaming catastro buildingpart de toda valencia...", file=sys.stderr)
    geoms, plantas, ids = [], [], []
    n = 0
    invalid = 0
    with fiona.open(GML) as src:
        for f in src:
            n += 1
            try:
                g = shape(f["geometry"])
                if not g.is_valid:
                    g = make_valid(g)
            except Exception:
                invalid += 1
                continue
            nfa = f["properties"].get("numberOfFloorsAboveGround")
            if nfa is None or nfa <= 0:
                continue
            geoms.append(g)
            plantas.append(int(nfa))
            ids.append(f["properties"].get("localId") or "")
            if len(geoms) % 10000 == 0:
                print(f"  ...{len(geoms)} edificios procesados", file=sys.stderr)

    print(f"  total: {len(geoms)} de {n} ({invalid} inválidas)", file=sys.stderr)

    g = gpd.GeoDataFrame(
        {"localId": ids, "plantas": plantas},
        geometry=geoms, crs="EPSG:25830",
    )
    g["altura_m"] = g["plantas"].clip(lower=1) * ALTURA_PLANTA
    g["geometry"] = g.geometry.force_2d()

    print(f"alturas: media={g['altura_m'].mean():.1f}m  "
          f"mediana={g['altura_m'].median():.1f}m  max={g['altura_m'].max():.1f}m",
          file=sys.stderr)

    g.to_file(OUT, layer="edificios_3d", driver="GPKG", mode="w")
    print(f"ok -> {OUT}", file=sys.stderr)


if __name__ == "__main__":
    main()
