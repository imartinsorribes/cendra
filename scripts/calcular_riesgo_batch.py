"""
Aplica el modelo de `calcular_riesgo.py` a los 214.000 edificios del
Catastro INSPIRE bajo un escenario por defecto.

Por qué un escenario por defecto y no «el escenario real de cada
edificio»: el Catastro INSPIRE no expone abiertamente la fachada, el
estado de la ITE, el SCI ni la cubierta. Tampoco el año de construcción
en su GML (sí existe en otros endpoints pero no son abiertos al mismo
nivel). Estos cuatro factores quedan **paramétricos** y los gestiona
el frontend; en el batch fijamos un valor «medio» documentado para
poder hablar de la geografía del riesgo conocido.

Salidas:
  data/processed/riesgo_edificios.gpkg   · 1 polígono por edificio · 8 atributos numéricos
  data/processed/riesgo_por_barrio.csv   · agregado de los 88 barrios

Tiempos aproximados (Ryzen, gpkg de 72 MB en SSD):
  - sjoin barrio:                ~10 s
  - sjoin_nearest parque (6):    ~3 s
  - sjoin_nearest hidrante (~2k): ~5 s
  - cálculo vectorizado:         ~2 s
  - escritura gpkg:              ~10 s
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from calcular_riesgo import (  # noqa: E402
    FACTOR_TORTUOSIDAD,
    T_MOVILIZACION_MIN,
    TABLA_CUBIERTA,
    TABLA_FACHADA,
    TABLA_ITE,
    TABLA_SCI,
    V_HORA_KMH,
    W_EXP,
    W_EXP_FACHADA_CRIT,
    W_RESP,
    W_RESP_FACHADA_CRIT,
    W_VULN,
    W_VULN_FACHADA_CRIT,
    r_tiempo,
    v_altura,
    v_edad,
)

# === Escenario por defecto del batch =======================================
# Valores «medianos» de los paramétricos. El frontend permitirá variarlos
# y recalcular en vivo.
DEFAULT_ANIO = 1990  # V_edad = 30
DEFAULT_FACHADA = "composite-cte"  # 60
DEFAULT_ITE = "pendiente"  # 50
DEFAULT_SCI = "parcial"  # 35
DEFAULT_CUBIERTA = "mixto"  # 40
DEFAULT_HORA = 12  # 45 km/h
DEFAULT_R_ACCESO = 30.0  # calle normal (placeholder)


# === Carga de datos =========================================================

def cargar_edificios() -> gpd.GeoDataFrame:
    gpkg = ROOT / "data" / "processed" / "edificios_3d_valencia.gpkg"
    if not gpkg.exists():
        raise FileNotFoundError(
            f"No existe {gpkg}. Ejecuta antes "
            f"`python scripts/extraer_alturas_ciudad.py`."
        )
    g = gpd.read_file(gpkg, layer="edificios_3d")
    # Aseguramos CRS métrico UTM 30N (oficial para España peninsular)
    if g.crs and g.crs.to_epsg() != 25830:
        g = g.to_crs("EPSG:25830")
    return g


def cargar_capa(nombre: str) -> gpd.GeoDataFrame:
    p = ROOT / "data" / "raw" / "large" / f"{nombre}.geojson"
    g = gpd.read_file(p)
    if g.crs is None:
        g = g.set_crs("EPSG:4326")
    return g.to_crs("EPSG:25830")


def cargar_parques() -> gpd.GeoDataFrame:
    p = ROOT / "data" / "raw" / "parques_bomberos.geojson"
    g = gpd.read_file(p).to_crs("EPSG:25830")
    return g


# === Cálculos vectorizados ==================================================

def calc_V_intrinseca_vectorizado(plantas: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """V_intrínseca para todos los edificios bajo el escenario por defecto.

    Devuelve (V, fachada_critica_flag) — el flag se usa para decidir
    el régimen de pesos."""
    # V_edad fija (DEFAULT_ANIO)
    v_e = v_edad(DEFAULT_ANIO)  # escalar
    # V_altura vectorizado: plantas → 0/10/40/70/100
    v_a = np.select(
        [plantas <= 3, plantas <= 7, plantas <= 12, plantas > 12],
        [10.0, 40.0, 70.0, 100.0],
        default=10.0,
    )
    v_f = TABLA_FACHADA[DEFAULT_FACHADA]
    v_i = TABLA_ITE[DEFAULT_ITE]
    v_s = TABLA_SCI[DEFAULT_SCI]
    v_c = TABLA_CUBIERTA[DEFAULT_CUBIERTA]

    V = (
        0.10 * v_e
        + 0.15 * v_a
        + 0.30 * v_f
        + 0.15 * v_i
        + 0.20 * v_s
        + 0.10 * v_c
    )

    # Régimen «fachada crítica»: V_fachada >= 100 (no aplica en el escenario
    # por defecto pero dejamos la lógica preparada para reusar la función
    # con otros paramétricos)
    fachada_crit = np.full(plantas.shape, v_f >= 100, dtype=bool)
    if v_f >= 100:
        piso = np.minimum(v_f * (1.0 + 0.5 * v_a / 100.0), 100.0)
        V = np.maximum(V, piso)

    return V, fachada_crit


def calc_E_exposicion_vectorizado(
    densidad_hab_km2: np.ndarray, ind_vulnerab_norm: np.ndarray,
) -> np.ndarray:
    """E_exposición para todos los edificios.
    `ind_vulnerab_norm` ya viene reescalado a 0-100.
    `densidad` se normaliza por percentiles dentro de este mismo array."""
    # Densidad → percentil sobre la distribución
    valid = ~np.isnan(densidad_hab_km2)
    rank = np.full(densidad_hab_km2.shape, 50.0)
    if valid.any():
        valores = densidad_hab_km2[valid]
        rank_valid = pd.Series(valores).rank(pct=True).values * 100
        rank[valid] = rank_valid
    e_dens = rank

    e_vul = np.where(np.isnan(ind_vulnerab_norm), 50.0, ind_vulnerab_norm)
    e_sens = 0.0  # placeholder hasta integrar capas de equipamientos sensibles

    E = 0.40 * e_dens + 0.35 * e_vul + 0.25 * e_sens
    return E


def calc_R_respuesta_vectorizado(
    dist_parque_m: np.ndarray, dist_hidrante_m: np.ndarray,
) -> np.ndarray:
    """R_respuesta bajo DEFAULT_HORA y saturación 'libre'."""
    d_ruta = dist_parque_m * FACTOR_TORTUOSIDAD
    v_kmh = V_HORA_KMH[DEFAULT_HORA]
    t_min = T_MOVILIZACION_MIN + (d_ruta / 1000.0) / v_kmh * 60.0

    # r_tiempo vectorizado
    r_t = np.select(
        [t_min <= 4, t_min <= 6, t_min <= 8, t_min <= 12],
        [0.0, 30.0, 60.0, 85.0],
        default=100.0,
    )

    # r_hidrante por distancia (en metros)
    r_h = np.select(
        [dist_hidrante_m < 50, dist_hidrante_m < 100, dist_hidrante_m < 200],
        [0.0, 30.0, 70.0],
        default=100.0,
    )

    r_a = DEFAULT_R_ACCESO

    R = 0.65 * r_t + 0.20 * r_h + 0.15 * r_a
    return R, t_min, r_t, r_h


# === Pipeline principal =====================================================

def main() -> None:
    t0 = time.time()

    print("[1/8] cargar Catastro 3D…", file=sys.stderr)
    edif = cargar_edificios()
    n = len(edif)
    print(f"  {n:,} edificios cargados", file=sys.stderr)

    # Centroide del edificio (más rápido y suficiente para joins de proximidad)
    edif["pt"] = edif.geometry.representative_point()

    print("[2/8] sjoin: asignar barrio…", file=sys.stderr)
    barris = cargar_capa("barris")
    barris_simple = barris[["codbarrio", "nombre", "geometry"]].rename(
        columns={"nombre": "barrio"}
    )
    edif_pt = edif.set_geometry("pt")[["pt"]].copy()
    edif_pt.crs = edif.crs
    j_barrio = gpd.sjoin(
        edif_pt, barris_simple, predicate="within", how="left"
    ).drop(columns="index_right")
    edif["barrio"] = j_barrio["barrio"].values
    edif["codbarrio"] = j_barrio["codbarrio"].values
    print(
        f"  barrios distintos: {edif['barrio'].nunique()} · sin barrio: "
        f"{edif['barrio'].isna().sum()}",
        file=sys.stderr,
    )

    print("[3/8] anejar densidad poblacional por barrio…", file=sys.stderr)
    viv = pd.read_csv(ROOT / "data" / "processed" / "viviendas_por_barrio.csv")
    edif = edif.merge(
        viv[["nombre", "densidad_hab_km2"]],
        left_on="barrio",
        right_on="nombre",
        how="left",
    ).drop(columns=["nombre"])

    print("[4/8] anejar índice de vulnerabilidad por barrio…", file=sys.stderr)
    vuln = cargar_capa("vulnerabilitat_barris")
    # Cruzamos por codbarrio (barris) ↔ codbar (vulnerabilidad).
    # Forzamos ambos a Int64 nullable para evitar el conflicto str/int
    # que provoca el sjoin previo (153 edificios sin barrio quedan NaN).
    vuln_simple = vuln[["codbar", "ind_global"]].copy()
    vuln_simple["codbar"] = pd.to_numeric(vuln_simple["codbar"], errors="coerce").astype("Int64")
    # ind_global está en escala 1-3 según el dataset. Lo reescalamos a
    # 0-100 conservativamente: 1→25, 2→50, 3→75 (margen arriba y
    # abajo para casos extremos).
    vuln_simple["ind_vulnerab_norm"] = (vuln_simple["ind_global"].astype(float) - 1) / 2 * 100
    edif["codbarrio"] = pd.to_numeric(edif["codbarrio"], errors="coerce").astype("Int64")
    edif = edif.merge(
        vuln_simple[["codbar", "ind_vulnerab_norm"]],
        left_on="codbarrio",
        right_on="codbar",
        how="left",
    ).drop(columns=["codbar"])
    print(
        f"  vulnerabilidad ind_global media: "
        f"{edif['ind_vulnerab_norm'].mean():.1f}",
        file=sys.stderr,
    )

    print("[5/8] sjoin_nearest: parque de bomberos más cercano…", file=sys.stderr)
    parq = cargar_parques()
    edif_pt2 = edif.set_geometry("pt")[["pt"]].copy()
    edif_pt2.crs = edif.crs
    j_parq = gpd.sjoin_nearest(
        edif_pt2,
        parq[["nombre", "geometry"]].rename(columns={"nombre": "parque_cercano"}),
        how="left",
        distance_col="dist_parque_m",
    )
    edif["parque_cercano"] = j_parq["parque_cercano"].values
    edif["dist_parque_m"] = j_parq["dist_parque_m"].values
    print(
        f"  dist parque  media={edif['dist_parque_m'].mean():.0f}m  "
        f"max={edif['dist_parque_m'].max():.0f}m",
        file=sys.stderr,
    )

    print("[6/8] sjoin_nearest: hidrante más cercano…", file=sys.stderr)
    hidr = cargar_capa("hidrants")
    j_hidr = gpd.sjoin_nearest(
        edif_pt2,
        hidr[["geometry"]],
        how="left",
        distance_col="dist_hidrante_m",
    )
    # Puede haber duplicados si varios hidrantes están a igual distancia
    j_hidr = j_hidr.groupby(j_hidr.index)["dist_hidrante_m"].min()
    edif["dist_hidrante_m"] = j_hidr.reindex(edif.index).values
    print(
        f"  dist hidrante  media={edif['dist_hidrante_m'].mean():.0f}m  "
        f"max={edif['dist_hidrante_m'].max():.0f}m",
        file=sys.stderr,
    )

    print("[7/8] calcular V, E, R y riesgo total (vectorizado)…", file=sys.stderr)
    V, fachada_crit = calc_V_intrinseca_vectorizado(edif["plantas"].values)
    E = calc_E_exposicion_vectorizado(
        edif["densidad_hab_km2"].values, edif["ind_vulnerab_norm"].values
    )
    R, t_llegada, r_t, r_h = calc_R_respuesta_vectorizado(
        edif["dist_parque_m"].values, edif["dist_hidrante_m"].values
    )

    edif["V_intrinseca"] = V
    edif["E_exposicion"] = E
    edif["R_respuesta"] = R
    edif["tiempo_llegada_min"] = t_llegada
    edif["fachada_critica"] = fachada_crit

    # Combinación con régimen condicional
    riesgo = np.where(
        fachada_crit,
        W_VULN_FACHADA_CRIT * V + W_EXP_FACHADA_CRIT * E + W_RESP_FACHADA_CRIT * R,
        W_VULN * V + W_EXP * E + W_RESP * R,
    )
    edif["riesgo"] = np.clip(riesgo, 0, 100).round(1)

    print(
        f"  riesgo  media={edif['riesgo'].mean():.1f}  "
        f"mediana={edif['riesgo'].median():.1f}  "
        f"min={edif['riesgo'].min():.1f}  max={edif['riesgo'].max():.1f}",
        file=sys.stderr,
    )

    print("[8/8] escribir salidas…", file=sys.stderr)
    # Limpiar geometría auxiliar
    edif_out = edif.set_geometry("geometry").drop(columns=["pt"])
    # Reducir a las columnas útiles
    cols = [
        "localId", "plantas", "altura_m", "barrio", "codbarrio",
        "densidad_hab_km2", "ind_vulnerab_norm",
        "parque_cercano", "dist_parque_m", "dist_hidrante_m",
        "tiempo_llegada_min", "V_intrinseca", "E_exposicion", "R_respuesta",
        "fachada_critica", "riesgo",
        "geometry",
    ]
    edif_out = edif_out[cols]

    out_gpkg = ROOT / "data" / "processed" / "riesgo_edificios.gpkg"
    out_gpkg.unlink(missing_ok=True)
    edif_out.to_file(out_gpkg, layer="riesgo", driver="GPKG")
    print(f"  → {out_gpkg.relative_to(ROOT)}", file=sys.stderr)

    # Agregado por barrio
    agg = (
        edif_out.groupby("barrio")
        .agg(
            n_edificios=("riesgo", "count"),
            riesgo_medio=("riesgo", "mean"),
            riesgo_p75=("riesgo", lambda s: float(s.quantile(0.75))),
            riesgo_p90=("riesgo", lambda s: float(s.quantile(0.90))),
            altura_media=("altura_m", "mean"),
            plantas_media=("plantas", "mean"),
            dist_parque_media=("dist_parque_m", "mean"),
            tiempo_llegada_medio=("tiempo_llegada_min", "mean"),
            densidad=("densidad_hab_km2", "first"),
            vulnerab=("ind_vulnerab_norm", "first"),
        )
        .round(2)
        .sort_values("riesgo_medio", ascending=False)
        .reset_index()
    )
    out_csv = ROOT / "data" / "processed" / "riesgo_por_barrio.csv"
    agg.to_csv(out_csv, index=False)
    print(f"  → {out_csv.relative_to(ROOT)}", file=sys.stderr)

    print(
        f"\nTop-10 barrios por riesgo medio:\n"
        f"{agg.head(10)[['barrio', 'n_edificios', 'riesgo_medio', 'altura_media', 'tiempo_llegada_medio']].to_string(index=False)}",
        file=sys.stderr,
    )
    print(f"\nTOTAL: {time.time() - t0:.0f}s", file=sys.stderr)


if __name__ == "__main__":
    main()
