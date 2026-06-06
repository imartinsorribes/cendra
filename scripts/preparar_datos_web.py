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


_TOP_EDIFICIOS_CACHE: gpd.GeoDataFrame | None = None
N_TOP_EDIFICIOS = 2000


def _cargar_top_unicos() -> gpd.GeoDataFrame | None:
    """Devuelve los TOP-N edificios únicos (deduplicados por
    `localId_base`) ordenados por riesgo descendente. Lo cachea para que
    `construir_edificios_todos` y `construir_edificios_poligonos` partan
    EXACTAMENTE del mismo conjunto: así los números que muestra cada
    cluster coinciden con los polígonos que aparecen al hacer zoom."""
    global _TOP_EDIFICIOS_CACHE
    if _TOP_EDIFICIOS_CACHE is not None:
        return _TOP_EDIFICIOS_CACHE
    gpkg = PROCESSED / "riesgo_edificios.gpkg"
    if not gpkg.exists():
        return None
    edif = gpd.read_file(gpkg, layer="riesgo")
    edif["localId_base"] = edif["localId"].str.split("_part").str[0]
    # Para cada localId_base, nos quedamos con la fila de mayor riesgo
    # (sort + drop_duplicates keep="first"). Después tomamos los top N
    # únicos. Esta es la lista canónica que usan ambas funciones.
    edif = (
        edif.sort_values("riesgo", ascending=False)
        .drop_duplicates(subset="localId_base", keep="first")
        .reset_index(drop=True)
    )
    n = min(N_TOP_EDIFICIOS, len(edif))
    _TOP_EDIFICIOS_CACHE = edif.head(n).copy()
    return _TOP_EDIFICIOS_CACHE


def _quitar_crs_obsoleto(path: Path) -> None:
    """GeoPandas / Fiona inyectan un bloque `crs` heredado del estándar
    GeoJSON 2008 (`urn:ogc:def:crs:OGC:1.3:CRS84`). RFC 7946 lo desaprueba
    porque asume WGS84 implícito. MapLibre lo ignora pero los validadores
    estrictos lo marcan como warning. Lo eliminamos en sitio."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if "crs" in data:
            data.pop("crs")
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
    except Exception as e:
        print(f"  [warn] no pude limpiar crs en {path.name}: {e}", file=sys.stderr)


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
    _quitar_crs_obsoleto(out)
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
    """Exporta los TOP-2.000 edificios de mayor riesgo como un GeoJSON
    minimizado de puntos para que el frontend pueda agruparlos en
    clusters a zoom bajo. Los mismos 2.000 son los que tienen polígono
    real en `edificios_top_poligonos.geojson`, así que los números que
    muestra cada cluster coinciden con los polígonos que aparecerán al
    hacer zoom hasta la calle.

    Servir los 214.000 enteros sería ~47 MB, prohibitivo para un atlas
    estático. Los 2.000 cubren los hotspots reales sin saturar el
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
    edif = _cargar_top_unicos()
    if edif is None:
        print("  [skip] riesgo_edificios.gpkg ausente. "
              "Ejecuta antes calcular_riesgo_batch.py.", file=sys.stderr)
        return
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
        # Usamos localId_base (sin sufijo _partN) para que el id coincida
        # con el de los polígonos en `edificios_top_poligonos.geojson`.
        # Así un click en un punto y un click en su polígono devuelven la
        # misma referencia al frontend.
        if "localId_base" in cols and pd.notna(row["localId_base"]):
            prop["i"] = str(row["localId_base"])
        # Bandera «candidato Campanar»: edificios construidos en la era
        # del composite ACM-PE (2000-2017) con ≥10 plantas. Son los
        # edificios que el Ayuntamiento debería priorizar para
        # inspección de fachada (sin estigmatizarlos: NO sabemos si
        # tienen ACM-PE, pero cumplen el perfil temporal).
        if "candidato_campanar" in cols and bool(row["candidato_campanar"]):
            prop["c"] = 1
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


def construir_edificios_poligonos() -> None:
    """Exporta la geometría POLIGONAL real (huella catastral) de los
    TOP-2000 edificios únicos de mayor riesgo.

    Hasta v0.2 sacábamos 500 polígonos pero el Catastro INSPIRE
    desglosa cada edificio en buildingparts (`localId` con sufijo
    `_partN`). Eso provocaba que un mismo edificio físico apareciera
    varias veces en el mapa (varios polígonos solapados). Ahora
    deduplicamos por `localId_base` y por agrupación geométrica
    (unimos las partes que pertenecen al mismo edificio).

    Resultado: una huella por edificio real, no varias por sus
    partes catastrales.
    """
    representantes = _cargar_top_unicos()
    if representantes is None:
        return

    # Para cada edificio del top, unimos las geometrías de TODAS sus
    # buildingparts (mismas localId_base) para tener la huella completa
    # del Catastro, no solo la de la parte representante.
    gpkg = PROCESSED / "riesgo_edificios.gpkg"
    edif_completo = gpd.read_file(
        gpkg, layer="riesgo",
        columns=["localId", "geometry"],
    )
    edif_completo["localId_base"] = edif_completo["localId"].str.split("_part").str[0]
    ids_top = set(representantes["localId_base"])
    partes = edif_completo[edif_completo["localId_base"].isin(ids_top)]
    geom_unida = (
        partes.groupby("localId_base", as_index=False)["geometry"]
        .agg(lambda g: g.unary_union)
    )

    # Sustituir geometría del representante por la unión de todas sus partes
    rep = representantes.merge(geom_unida, on="localId_base", suffixes=("", "_unida"))
    rep["geometry"] = rep["geometry_unida"]
    rep = rep.drop(columns=["geometry_unida"])

    top = (
        gpd.GeoDataFrame(rep, geometry="geometry", crs=representantes.crs)
        .to_crs("EPSG:4326")
    )

    cols = ["riesgo", "plantas", "altura_m", "anio_construccion",
            "barrio", "candidato_campanar", "uso", "tiempo_llegada_min",
            "parque_cercano", "localId_base", "geometry"]
    cols_disp = [c for c in cols if c in top.columns]
    out = top[cols_disp].copy()
    out = out.rename(columns={
        "riesgo": "r", "plantas": "p", "altura_m": "h",
        "anio_construccion": "a", "barrio": "b",
        "candidato_campanar": "c", "uso": "u",
        "tiempo_llegada_min": "t", "parque_cercano": "k",
        "localId_base": "i",
    })
    if "c" in out.columns:
        out["c"] = out["c"].fillna(False).astype(int)
    # Simplificar geometría a ~1 m para reducir tamaño del GeoJSON
    out["geometry"] = out.geometry.simplify(0.00001, preserve_topology=True)
    out_path = WEB_DATA / "edificios_top_poligonos.geojson"
    out.to_file(out_path, driver="GeoJSON", coordinate_precision=5)
    _quitar_crs_obsoleto(out_path)
    kb = out_path.stat().st_size / 1024
    print(
        f"  → {out_path.relative_to(ROOT)} ({kb:.0f} KB, "
        f"{len(out):,} polígonos únicos del top de riesgo)",
        file=sys.stderr,
    )

    # Puntos y polígonos cubren exactamente el mismo conjunto (los 2.000
    # edificios únicos de mayor riesgo). Los puntos sirven para que el
    # clustering muestre hotspots a zoom bajo; al hacer zoom hasta zoom
    # 14 los polígonos toman el relevo. Si en algún momento decidimos
    # ampliar la cobertura, hay que subir n_top en construir_edificios_todos
    # y construir_edificios_poligonos juntos para mantener la coherencia.


def _fila_lista(row, pt_4326) -> dict:
    """Helper: convierte una fila del gpkg en dict para la lista
    JSON del frontend."""
    ref = str(row.get("localId", "") or "").split("_part")[0]
    return {
        "lon": round(pt_4326.x, 5),
        "lat": round(pt_4326.y, 5),
        "barrio": str(row.get("barrio", "") or ""),
        "plantas": int(row.get("plantas", 0) or 0),
        "anio": int(row["anio_construccion"]) if pd.notna(row.get("anio_construccion")) else None,
        "altura_m": int(row.get("altura_m", 0) or 0),
        "uso": str(row.get("uso", "") or ""),
        "riesgo": round(float(row["riesgo"]), 1),
        "candidato_campanar": bool(row.get("candidato_campanar", False)),
        "ref": ref,
        "tiempo_llegada_min": round(float(row.get("tiempo_llegada_min", 0)), 1),
        "parque_cercano": str(row.get("parque_cercano", "") or ""),
    }


def construir_lista_top_critical() -> None:
    """Genera un JSON con DOS rankings de edificios para el panel:

      - `top_riesgo`: TOP 20 con mayor índice de riesgo del modelo bajo
        el escenario base. Suelen ser pedanías y zonas urbanas densas
        con tiempo de bomberos elevado.

      - `top_candidatos_campanar`: TOP 20 entre los edificios con
        perfil temporal del incidente Campanar (≥10 plantas y
        construcción 2000-2017, era del composite ACM). Son los que
        DEBERÍAN inspeccionarse prioritariamente, aunque su riesgo
        en el modelo «escenario base» NO sea máximo (porque el modelo
        no asume fachada combustible por defecto).

    La distinción entre ambos rankings es metodológicamente importante:
    el primero es el ranking PASIVO del modelo, el segundo es la
    pregunta proactiva «¿dónde está la próxima Campanar latente?».
    """
    gpkg = PROCESSED / "riesgo_edificios.gpkg"
    if not gpkg.exists():
        return
    edif = gpd.read_file(gpkg, layer="riesgo")

    # Agrupar por localId base (sin _part) para no listar varias partes
    # del mismo edificio. Nos quedamos con la fila de mayor riesgo de
    # cada edificio único.
    edif["localId_base"] = edif["localId"].str.split("_part").str[0]
    edif = edif.sort_values("riesgo", ascending=False)
    edif = edif.drop_duplicates(subset="localId_base", keep="first")

    pts_all = edif.geometry.representative_point().to_crs("EPSG:4326")

    def _construir_top(subset, n=20):
        sub = subset.head(n)
        items = []
        for rank, idx in enumerate(sub.index, start=1):
            pt = pts_all.loc[idx]
            row = sub.loc[idx]
            item = _fila_lista(row, pt)
            item["rank"] = rank
            items.append(item)
        return items

    top_riesgo = _construir_top(edif, n=20)

    candidatos = edif[edif["candidato_campanar"] == True]  # noqa: E712
    top_campanar = _construir_top(candidatos, n=20)

    n_total_cand = int((edif["candidato_campanar"] == True).sum())  # noqa: E712

    salida = {
        "top_riesgo": top_riesgo,
        "top_candidatos_campanar": top_campanar,
        "n_total_candidatos_campanar": n_total_cand,
        "n_total_edificios": int(len(edif)),
    }
    out_path = WEB_DATA / "edificios_top_lista.json"
    out_path.write_text(
        json.dumps(salida, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )
    kb = out_path.stat().st_size / 1024
    print(
        f"  → {out_path.relative_to(ROOT)} ({kb:.0f} KB) · "
        f"{n_total_cand:,} candidatos Campanar entre "
        f"{len(edif):,} edificios únicos",
        file=sys.stderr,
    )

    # Lista COMPLETA de los 154 candidatos perfil Campanar para
    # poderla mostrar en la página de «Propuestas» y exportarla a CSV.
    full = []
    for rank, idx in enumerate(candidatos.index, start=1):
        pt = pts_all.loc[idx]
        row = candidatos.loc[idx]
        item = _fila_lista(row, pt)
        item["rank"] = rank
        full.append(item)
    full_path = WEB_DATA / "candidatos_campanar_completo.json"
    full_path.write_text(
        json.dumps(full, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )
    kb = full_path.stat().st_size / 1024
    print(
        f"  → {full_path.relative_to(ROOT)} ({kb:.0f} KB) · "
        f"lista completa de {len(full)} candidatos para tabla y CSV",
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
    print("[4/5] construir edificios_top_riesgo.geojson (puntos)",
          file=sys.stderr)
    construir_edificios_todos()
    print("[5/6] construir edificios_top_poligonos.geojson (huellas reales)",
          file=sys.stderr)
    construir_edificios_poligonos()
    print("[6/6] construir edificios_top_lista.json (top-30 más críticos)",
          file=sys.stderr)
    construir_lista_top_critical()


if __name__ == "__main__":
    main()
