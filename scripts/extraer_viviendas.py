"""
Saca viviendas por barrio del catastro INSPIRE (building.gml, NO el
buildingpart que ya usamos para alturas).

Building.gml trae el campo numberOfDwellings por edificio. Sumando por
barrio y multiplicando por un factor empírico de población por
vivienda catastrada se obtiene una estimación razonable de población
residencial por barrio.

Salida:
  data/processed/viviendas_por_barrio.csv

El factor 1.88 hab/vivienda **catastrada** se calibra contra el
padrón INE 2023 de València (791.413 habitantes en el término
municipal). El Catastro registra TODAS las viviendas administrativas
de la finca (incluidas vacías, secundarias, en alquiler turístico,
en obra). El tamaño medio del hogar INE de 2.4 hab/vivienda se refiere
a la vivienda **principal habitada**, una categoría mucho más
restrictiva, por lo que multiplicarlo por el numberOfDwellings del
Catastro sobreestima la población en un ~28 %. Ver
`docs/validacion-datos.md` §1 para la trazabilidad de la calibración.

Fuentes:
  - building.gml: Dirección General del Catastro (datos.gob.es)
  - barris.geojson: portal de datos abiertos del Ajuntament
  - factor 1.88 hab/vivienda catastrada: calibrado empíricamente
    contra el Padrón Municipal de Habitantes INE 2023 (válido para
    València ciudad, no extrapolable a otras ciudades sin recalibrar)
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
       / "A.ES.SDGC.BU.46900.building.gml")
BARRIS = ROOT / "data" / "raw" / "large" / "barris.geojson"
OUT_CSV = ROOT / "data" / "processed" / "viviendas_por_barrio.csv"

# Factor empírico hab / vivienda catastrada para València ciudad.
# Calibrado contra Padrón INE 2023: 791.413 hab / 421.687 viviendas
# del Catastro INSPIRE → 1.877. Redondeado a 1.88.
HAB_POR_VIVIENDA = 1.88


def main():
    if not GML.exists():
        sys.exit(f"falta {GML}")

    print("leer edificios principales (building.gml)", file=sys.stderr)
    geoms, dwellings, units, uses = [], [], [], []
    n = 0
    bad = 0
    with fiona.open(GML) as src:
        for f in src:
            n += 1
            try:
                g = shape(f["geometry"])
                if not g.is_valid:
                    g = make_valid(g)
            except Exception:
                bad += 1
                continue
            d = f["properties"].get("numberOfDwellings", 0) or 0
            u = f["properties"].get("numberOfBuildingUnits", 0) or 0
            cu = f["properties"].get("currentUse") or ""
            geoms.append(g)
            dwellings.append(int(d))
            units.append(int(u))
            uses.append(cu)
            if n % 5000 == 0:
                print(f"  ...{n} edif. procesados", file=sys.stderr)

    edif = gpd.GeoDataFrame(
        {"viviendas": dwellings, "unidades": units, "uso": uses},
        geometry=geoms, crs="EPSG:25830",
    )
    print(f"  total: {len(edif)} ({bad} inv.)  viviendas suma: "
          f"{edif['viviendas'].sum():,}  residenciales: "
          f"{(edif['uso']=='1_residential').sum():,}", file=sys.stderr)

    print("cargar barris y spatial join", file=sys.stderr)
    barris = gpd.read_file(BARRIS).to_crs("EPSG:25830")
    barris["area_km2"] = barris.geometry.area / 1e6

    # representative_point para evitar problemas con bordes (edificio
    # justo en el limite). Si quisieramos exactitud, intersect area.
    edif["pt"] = edif.geometry.representative_point()
    edif_pt = edif.set_geometry("pt")[["viviendas", "unidades", "uso", "pt"]]
    edif_pt = edif_pt.set_geometry("pt")
    edif_pt.crs = "EPSG:25830"

    j = gpd.sjoin(edif_pt, barris[["nombre", "geometry"]],
                  predicate="within", how="left")
    agg = j.groupby("nombre").agg(
        viviendas_total=("viviendas", "sum"),
        unidades_total=("unidades", "sum"),
        n_edificios=("uso", "count"),
        n_residencial=("uso", lambda s: (s == "1_residential").sum()),
    ).reset_index()

    out = barris.merge(agg, on="nombre", how="left").fillna({
        "viviendas_total": 0, "unidades_total": 0,
        "n_edificios": 0, "n_residencial": 0,
    })
    out["pob_estimada"] = (out["viviendas_total"] * HAB_POR_VIVIENDA).round().astype(int)
    out["densidad_hab_km2"] = (out["pob_estimada"] / out["area_km2"]).round().astype(int)

    print(f"\ntop 10 barrios por poblacion estimada:", file=sys.stderr)
    print(out.nlargest(10, "pob_estimada")[
        ["nombre", "area_km2", "viviendas_total", "pob_estimada", "densidad_hab_km2"]
    ].round(2).to_string(index=False), file=sys.stderr)

    print(f"\ntop 10 menos densos (pedanias/huerta):", file=sys.stderr)
    print(out.nsmallest(10, "densidad_hab_km2")[
        ["nombre", "area_km2", "viviendas_total", "pob_estimada", "densidad_hab_km2"]
    ].round(2).to_string(index=False), file=sys.stderr)

    cols = ["nombre", "area_km2", "viviendas_total", "unidades_total",
            "n_edificios", "n_residencial", "pob_estimada", "densidad_hab_km2"]
    out[cols].to_csv(OUT_CSV, index=False)
    print(f"\nok -> {OUT_CSV.name}", file=sys.stderr)
    print(f"poblacion total estimada valencia: {out['pob_estimada'].sum():,}",
          file=sys.stderr)


if __name__ == "__main__":
    main()
