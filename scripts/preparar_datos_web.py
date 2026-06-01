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


def construir_edificios_todos() -> None:
    """Exporta los TOP-10.000 edificios de mayor riesgo como un GeoJSON
    minimizado para que el frontend pueda mostrarlos en el mapa y la
    usuaria pueda hacer click en cualquiera para usar datos reales.

    Servir los 214.000 enteros sería ~47 MB, prohibitivo para un atlas
    estático. Los 10.000 cubren bien la geografía urbana sin saturar el
    navegador. Cuando la usuaria hace click en un punto del mapa que NO
    es uno de estos edificios, el frontend simula con los valores
    medios del barrio (información que sí está siempre disponible).

    Estrategia de tamaño:
      - Solo el centroide (un Point) en lugar del polígono
      - Coordenadas redondeadas a 5 decimales (~1,1 m de precisión)
      - Atributos abreviados a 1-2 letras (r=riesgo, p=plantas, h=altura,
        a=año, u=uso, b=barrio, t=tiempo bomberos, k=parque cercano,
        i=localId)
      - JSON sin espacios ni indentación
    """
    gpkg = PROCESSED / "riesgo_edificios.gpkg"
    if not gpkg.exists():
        print("  [skip] riesgo_edificios.gpkg ausente. "
              "Ejecuta antes calcular_riesgo_batch.py.", file=sys.stderr)
        return
    edif_full = gpd.read_file(gpkg, layer="riesgo")
    n_top = min(10000, len(edif_full))
    edif = edif_full.nlargest(n_top, "riesgo").reset_index(drop=True)
    pts = edif.geometry.representative_point().to_crs("EPSG:4326")

    features = []
    cols = edif.columns
    for i in range(len(edif)):
        row = edif.iloc[i]
        x, y = pts.iloc[i].x, pts.iloc[i].y
        prop = {
            "r": round(float(row["riesgo"]), 1),
            "p": int(row["plantas"]) if "plantas" in cols else None,
            "h": int(row["altura_m"]) if "altura_m" in cols else None,
        }
        # Año solo si es válido
        if "anio_construccion" in cols:
            a = row["anio_construccion"]
            if pd.notna(a):
                prop["a"] = int(a)
        if "uso" in cols and pd.notna(row["uso"]) and row["uso"]:
            prop["u"] = str(row["uso"])
        if "barrio" in cols and pd.notna(row["barrio"]) and row["barrio"]:
            prop["b"] = str(row["barrio"])
        if "tiempo_llegada_min" in cols:
            t = row["tiempo_llegada_min"]
            if pd.notna(t):
                prop["t"] = round(float(t), 1)
        if "parque_cercano" in cols and pd.notna(row["parque_cercano"]):
            prop["k"] = str(row["parque_cercano"])
        if "localId" in cols and pd.notna(row["localId"]):
            prop["i"] = str(row["localId"])
        # Limpiar Nones
        prop = {k: v for k, v in prop.items() if v is not None}
        features.append({
            "type": "Feature",
            "properties": prop,
            "geometry": {"type": "Point", "coordinates": [round(x, 5), round(y, 5)]},
        })

    out = WEB_DATA / "edificios_top_riesgo.geojson"
    out.write_text(
        json.dumps({"type": "FeatureCollection", "features": features},
                   separators=(",", ":"), ensure_ascii=False),
        encoding="utf-8",
    )
    mb = out.stat().st_size / 1024 / 1024
    print(
        f"  → {out.relative_to(ROOT)} ({mb:.1f} MB, {len(features):,} edificios "
        f"top-riesgo en formato compacto)",
        file=sys.stderr,
    )

    # Borrar el fichero edificios_todos si existía de generaciones previas
    todos = WEB_DATA / "edificios_todos.geojson"
    if todos.exists():
        todos.unlink()
        print(f"  borrado legacy {todos.name}", file=sys.stderr)


def main() -> None:
    print("[1/4] copiar parques_bomberos.geojson", file=sys.stderr)
    copiar_parques()
    print("[2/4] copiar hidrants.geojson (para hidrantes operativos en el plan SPEIS)",
          file=sys.stderr)
    copiar_hidrantes()
    print("[3/4] construir barris_riesgo.geojson", file=sys.stderr)
    construir_barris_riesgo()
    print("[4/4] construir edificios_todos.geojson + edificios_top_riesgo.geojson",
          file=sys.stderr)
    construir_edificios_todos()


if __name__ == "__main__":
    main()
