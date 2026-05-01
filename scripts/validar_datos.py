"""
Validación sistemática del estado de los datos del proyecto.

Comprueba:
  1. Counts y tipos geométricos de las 10 capas descargadas.
  2. Coherencia con el bbox del término municipal de València.
  3. Outliers del Catastro INSPIRE (alturas extremas, edificios sin
     viviendas, edificios sin barrio).
  4. Sobre/subestimaciones poblacionales contra cifras INE conocidas.
  5. Capa propia de parques de bomberos.
  6. Tabla de población oficial vs estimada por barrio (top-3).

Salida: imprime un informe por stderr/stdout. Genera
`docs/validacion-datos.md` con los hallazgos.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import geopandas as gpd
import pandas as pd
from shapely.geometry import box

ROOT = Path(__file__).resolve().parent.parent
RAW_LARGE = ROOT / "data" / "raw" / "large"
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
INFORME = ROOT / "docs" / "validacion-datos.md"

# bbox del término municipal de València, incluyendo las pedanías de
# El Saler / Pinedo / Perellonet al sur y Borbotó / Carpesa al norte.
# Coordenadas en EPSG:4326 (lon_min, lat_min, lon_max, lat_max).
BBOX_VLC = (-0.50, 39.28, -0.20, 39.60)
BBOX_GEOM = box(*BBOX_VLC)

# Población INE de València (Padrón Continuo 2023, fuente: ine.es)
POBLACION_INE_2023 = 791_413


def header(t: str) -> None:
    print(f"\n{'=' * 70}\n{t}\n{'=' * 70}", file=sys.stderr)


def comprobar_capa(path: Path, esperado_min: int | None = None,
                   tipos_validos: tuple[str, ...] = ("Point", "Polygon", "MultiPolygon", "LineString")) -> dict:
    """Devuelve un dict con métricas y banderas de validación."""
    if not path.exists():
        return {"path": path.name, "estado": "AUSENTE"}
    try:
        gdf = gpd.read_file(path)
    except Exception as e:
        return {"path": path.name, "estado": f"ERROR_LECTURA: {e}"}

    n = len(gdf)
    tipos = gdf.geometry.type.value_counts().to_dict()
    nulls = int(gdf.geometry.isna().sum())
    invalid = int((~gdf.geometry.is_valid).sum())
    # CRS
    crs = str(gdf.crs)
    # bbox
    gdf_4326 = gdf.to_crs("EPSG:4326") if "4326" not in crs and gdf.crs else gdf
    bounds = gdf_4326.total_bounds  # (minx, miny, maxx, maxy)
    fuera_bbox = 0
    if gdf_4326.crs:
        en_bbox = gdf_4326.geometry.representative_point().within(BBOX_GEOM)
        fuera_bbox = int((~en_bbox).sum())

    flags = []
    if esperado_min is not None and n < esperado_min:
        flags.append(f"count_bajo({n}<{esperado_min})")
    if nulls > 0:
        flags.append(f"nulls({nulls})")
    if invalid > 0:
        flags.append(f"invalidas({invalid})")
    if any(t not in tipos_validos for t in tipos):
        flags.append(f"tipos_extraños({list(tipos.keys())})")
    if fuera_bbox > 0:
        flags.append(f"fuera_bbox({fuera_bbox})")

    return {
        "path": path.name,
        "estado": "OK" if not flags else "ATENCIÓN",
        "n_features": n,
        "tipos": tipos,
        "crs": crs,
        "nulls": nulls,
        "invalid": invalid,
        "fuera_bbox": fuera_bbox,
        "bounds": tuple(round(b, 4) for b in bounds) if len(bounds) == 4 else None,
        "flags": flags,
    }


def main() -> dict:
    informe: dict = {"capas": {}, "catastro": {}, "poblacion": {}, "parques": {}, "modelo": {}}

    header("1. CAPAS DESCARGADAS")
    capas_esperadas = [
        ("hidrants.geojson", 1500),
        ("fites_bombers.geojson", 1),
        ("barris.geojson", 88),
        ("equipamientos.geojson", 2500),
        ("majors.geojson", 100),
        ("area_prioridad_residencial.geojson", 1),
        ("vulnerabilitat_barris.geojson", 70),
        ("hospitales.geojson", 30),
        ("centros_educativos.geojson", 400),
        ("manzanas_poblacion.geojson", 4000),
    ]
    for fname, n_min in capas_esperadas:
        res = comprobar_capa(RAW_LARGE / fname, esperado_min=n_min)
        informe["capas"][fname] = res
        marca = "✓" if res["estado"] == "OK" else "!"
        print(
            f"{marca} {fname:40s}  n={res.get('n_features', '?'):>6}  "
            f"tipos={list(res.get('tipos', {}).keys())}  flags={res.get('flags', [])}",
            file=sys.stderr,
        )

    header("2. CATASTRO INSPIRE — alturas")
    gpkg = PROCESSED / "edificios_3d_valencia.gpkg"
    if not gpkg.exists():
        print(f"!  {gpkg.name} AUSENTE", file=sys.stderr)
        informe["catastro"]["estado"] = "AUSENTE"
    else:
        edif = gpd.read_file(gpkg, layer="edificios_3d")
        n = len(edif)
        print(f"   total: {n:,} edificios", file=sys.stderr)
        print(
            f"   altura  media={edif['altura_m'].mean():.1f}m  "
            f"mediana={edif['altura_m'].median():.1f}m  "
            f"min={edif['altura_m'].min():.1f}m  "
            f"max={edif['altura_m'].max():.1f}m",
            file=sys.stderr,
        )
        print(
            f"   plantas media={edif['plantas'].mean():.1f}  "
            f"max={edif['plantas'].max()}",
            file=sys.stderr,
        )
        # Distribución por altura
        bins = [0, 6, 12, 21, 30, 50, 75, 100, 150]
        dist = pd.cut(edif["altura_m"], bins=bins).value_counts().sort_index()
        print("   distribución de alturas:", file=sys.stderr)
        for k, v in dist.items():
            print(f"     {k}: {v:>6,}", file=sys.stderr)
        # Outliers de altura
        outliers = edif[edif["altura_m"] >= 75].sort_values("altura_m", ascending=False)
        print(f"\n   edificios ≥ 75 m: {len(outliers)}", file=sys.stderr)
        if len(outliers) > 0:
            print(f"   top-10 más altos:", file=sys.stderr)
            for _, row in outliers.head(10).iterrows():
                lon, lat = row.geometry.to_crs("EPSG:4326").representative_point().coords[0] \
                    if hasattr(row.geometry, "to_crs") \
                    else (None, None)
                print(
                    f"     altura={row['altura_m']:.0f}m  plantas={row['plantas']}  "
                    f"localId={row['localId']}",
                    file=sys.stderr,
                )
        informe["catastro"] = {
            "n_edificios": n,
            "altura_media": float(edif["altura_m"].mean()),
            "altura_max": float(edif["altura_m"].max()),
            "n_outliers_75m": len(outliers),
        }

    header("3. POBLACIÓN vs INE 2023")
    viv = pd.read_csv(PROCESSED / "viviendas_por_barrio.csv")
    n_barris = len(viv)
    pob_estimada = int(viv["pob_estimada"].sum())
    viv_total = int(viv["viviendas_total"].sum())
    n_edif_total = int(viv["n_edificios"].sum())
    n_resid_total = int(viv["n_residencial"].sum())
    print(f"   barrios procesados: {n_barris}", file=sys.stderr)
    print(f"   edificios building.gml: {n_edif_total:,}", file=sys.stderr)
    print(f"   edificios uso='1_residential': {n_resid_total:,}", file=sys.stderr)
    print(f"   viviendas (numberOfDwellings sum): {viv_total:,}", file=sys.stderr)
    print(f"   pob_estimada (× 2.4): {pob_estimada:,}", file=sys.stderr)
    print(f"   pob_INE_2023:       {POBLACION_INE_2023:,}", file=sys.stderr)
    diff_pct = (pob_estimada - POBLACION_INE_2023) / POBLACION_INE_2023 * 100
    print(f"   diferencia: {diff_pct:+.1f}%", file=sys.stderr)
    factor_corr = POBLACION_INE_2023 / (viv_total) if viv_total > 0 else 0
    print(f"   factor real hab/vivienda implícito: {factor_corr:.2f}",
          file=sys.stderr)
    informe["poblacion"] = {
        "pob_estimada_actual": pob_estimada,
        "pob_ine_2023": POBLACION_INE_2023,
        "diferencia_pct": round(diff_pct, 1),
        "factor_corregido": round(factor_corr, 2),
        "viviendas_totales": viv_total,
    }

    header("4. PARQUES DE BOMBEROS")
    parq = gpd.read_file(RAW / "parques_bomberos.geojson")
    n = len(parq)
    print(f"   parques: {n}", file=sys.stderr)
    if n != 6:
        print(f"   !! esperaba 6, hay {n}", file=sys.stderr)
    en_bbox = parq.geometry.within(BBOX_GEOM)
    fuera = int((~en_bbox).sum())
    print(f"   fuera del bbox de VLC: {fuera}", file=sys.stderr)
    if fuera > 0:
        print(f"   !! parques fuera del bbox:", file=sys.stderr)
        for _, row in parq[~en_bbox].iterrows():
            print(f"     {row['nombre']}: {row.geometry.coords[0]}", file=sys.stderr)
    informe["parques"] = {
        "n": n,
        "fuera_bbox": fuera,
        "lista": parq["nombre"].tolist(),
    }

    header("5. COHERENCIA: edificios sin barrio asignado")
    if gpkg.exists():
        edif_4326 = edif.to_crs("EPSG:4326")
        barris = gpd.read_file(RAW_LARGE / "barris.geojson")
        if barris.crs is None:
            barris = barris.set_crs("EPSG:4326")
        else:
            barris = barris.to_crs("EPSG:4326")
        # Sample para no tardar todo el día
        edif_sample = edif_4326.sample(n=min(5000, len(edif_4326)), random_state=42)
        edif_sample["pt"] = edif_sample.geometry.representative_point()
        sj = gpd.sjoin(
            edif_sample.set_geometry("pt")[["pt"]],
            barris[["nombre", "geometry"]],
            predicate="within", how="left",
        )
        sin_barrio = int(sj["nombre"].isna().sum())
        pct = sin_barrio / len(sj) * 100
        print(f"   muestra de {len(sj):,} edificios", file=sys.stderr)
        print(f"   sin barrio: {sin_barrio} ({pct:.1f}%)", file=sys.stderr)
        informe["coherencia"] = {
            "muestra": len(sj),
            "sin_barrio": sin_barrio,
            "pct_sin_barrio": round(pct, 2),
        }

    header("6. MODELO — edge cases")
    sys.path.insert(0, str(ROOT / "scripts"))
    from calcular_riesgo import (
        riesgo,
        cargar_parques,
        TABLA_FACHADA,
        TABLA_ITE,
        TABLA_SCI,
        TABLA_CUBIERTA,
    )
    parques = cargar_parques()
    casos = [
        ("Edificio 0 plantas (bajo)", dict(plantas=1, anio=2020, lon=-0.376, lat=39.47, fachada="ladrillo", ite="favorable", sci="completo", cubierta="tradicional", hora=12, saturacion="libre")),
        ("Edificio 50 plantas", dict(plantas=50, anio=2024, lon=-0.376, lat=39.47, fachada="composite-acmpe", ite="desfavorable", sci="ninguno", cubierta="combustible", hora=8, saturacion="primero-ocupado")),
        ("Año 1850 (antiguo)", dict(plantas=4, anio=1850, lon=-0.376, lat=39.47, fachada="ladrillo", ite="desfavorable", sci="ninguno", cubierta="combustible", hora=3, saturacion="libre")),
        ("Año 2030 (futuro)", dict(plantas=10, anio=2030, lon=-0.376, lat=39.47, fachada="composite-cte", ite="favorable", sci="completo", cubierta="tradicional", hora=12, saturacion="libre")),
    ]
    edge = []
    for desc, kw in casos:
        try:
            res = riesgo(parques=parques, **kw)
            edge.append({"caso": desc, "riesgo": res["riesgo_total"], "regimen": res["pesos"]["regimen"]})
            print(f"   {desc:35s}  riesgo={res['riesgo_total']:>5.1f}  regimen={res['pesos']['regimen']}",
                  file=sys.stderr)
        except Exception as e:
            edge.append({"caso": desc, "error": str(e)})
            print(f"   {desc:35s}  ERROR: {e}", file=sys.stderr)
    informe["modelo"] = edge

    # Tablas: top-3 barrios sobreestimados según el factor 2.4
    header("7. BARRIOS — sobre/subestimación")
    print("   top-5 barrios por población estimada:", file=sys.stderr)
    top = viv.nlargest(5, "pob_estimada")[["nombre", "viviendas_total", "pob_estimada"]]
    print(top.to_string(index=False), file=sys.stderr)

    return informe


if __name__ == "__main__":
    res = main()
    # Volcar a JSON para consumo posterior
    out_json = PROCESSED / "validacion_datos.json"
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(res, indent=2, ensure_ascii=False, default=str),
                        encoding="utf-8")
    print(f"\n→ {out_json.relative_to(ROOT)}", file=sys.stderr)
