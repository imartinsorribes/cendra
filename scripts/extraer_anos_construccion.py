"""
Extrae el año de construcción de cada edificio del Catastro INSPIRE.

El campo `beginning` del GML `building.gml` contiene la fecha del
primer registro catastral del edificio. Para más del 99 % de los
edificios coincide con la fecha real de construcción; para una
minoría (edificios reformados profundamente) el campo `end` marca
el año del último cambio. El modelo de riesgo usa `beginning`
(antigüedad estructural) que es lo relevante para vulnerabilidad
ante incendio.

Salida:
  data/processed/anos_construccion.csv  ·  ~36.000 filas
    cols: localId, anio_construccion, anio_ultima_reforma, uso

Cruce con `edificios_3d_valencia.gpkg`: por
  buildingpart.localId.split('_part')[0]  ==  building.localId
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

import fiona

ROOT = Path(__file__).resolve().parent.parent
GML = (ROOT / "data" / "external" / "catastro"
       / "A.ES.SDGC.BU.46900" / "A.ES.SDGC.BU.46900.building.gml")
OUT = ROOT / "data" / "processed" / "anos_construccion.csv"


def anio(fecha_iso: str | None) -> int | None:
    if not fecha_iso:
        return None
    try:
        return int(fecha_iso[:4])
    except (ValueError, TypeError):
        return None


def main() -> None:
    if not GML.exists():
        sys.exit(f"falta {GML}")
    OUT.parent.mkdir(parents=True, exist_ok=True)

    n = 0
    with fiona.open(GML) as src, OUT.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(
            f,
            fieldnames=["localId", "anio_construccion", "anio_ultima_reforma", "uso"],
        )
        w.writeheader()
        for feat in src:
            p = feat["properties"]
            w.writerow({
                "localId": p.get("localId") or "",
                "anio_construccion": anio(p.get("beginning")) or "",
                "anio_ultima_reforma": anio(p.get("end")) or "",
                "uso": p.get("currentUse") or "",
            })
            n += 1
            if n % 5000 == 0:
                print(f"  ... {n} edificios", file=sys.stderr)

    print(f"\n  total: {n} edificios → {OUT.relative_to(ROOT)}", file=sys.stderr)

    # Distribución del año
    import pandas as pd
    df = pd.read_csv(OUT)
    df["anio_construccion"] = pd.to_numeric(df["anio_construccion"], errors="coerce")
    print(f"\n  años de construcción válidos: "
          f"{df['anio_construccion'].notna().sum():,} de {len(df):,}",
          file=sys.stderr)
    print(f"  rango: {int(df['anio_construccion'].min())} - "
          f"{int(df['anio_construccion'].max())}", file=sys.stderr)
    print("\n  distribución por décadas:", file=sys.stderr)
    decadas = (df["anio_construccion"] // 10 * 10).value_counts().sort_index()
    for k, v in decadas.items():
        if v >= 100:
            print(f"    {int(k)}s: {v:>6,}", file=sys.stderr)


if __name__ == "__main__":
    main()
