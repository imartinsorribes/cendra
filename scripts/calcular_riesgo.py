"""
Implementación del modelo paramétrico de riesgo de incendio.

Toda la metodología, justificación de pesos y validación viven en
`docs/modelo-riesgo.md`. Este script es la traducción ejecutable de
ese documento. Cualquier cambio de pesos o de tabla de mapeo debe
reflejarse aquí Y en el documento, en commits separados o
referenciándolos.

Uso desde la CLI:

    # Escenario canónico
    python scripts/calcular_riesgo.py --escenario campanar

    # Parámetros sueltos (todos requeridos si no hay escenario)
    python scripts/calcular_riesgo.py --plantas 14 --anio 2006 \
        --lon -0.398 --lat 39.485 --fachada composite-acmpe \
        --ite pendiente --sci parcial --cubierta mixto --hora 18

    # Sobrescribir un escenario canónico
    python scripts/calcular_riesgo.py --escenario campanar --hora 3 \
        --saturacion primero-ocupado
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PARQUES_PATH = ROOT / "data" / "raw" / "parques_bomberos.geojson"

# === Constantes del modelo v0.1 ============================================
# Ver docs/modelo-riesgo.md §4 para la justificación de los pesos.

W_VULN, W_EXP, W_RESP = 0.45, 0.30, 0.25  # pesos por defecto de las tres dimensiones
# Pesos cuando V_intrínseca está saturada por fachada×altura: la
# respuesta deja de ser eficaz porque el incendio se propaga más
# rápido de lo que puede contener; el resultado depende casi
# íntegramente del edificio y de la población expuesta.
W_VULN_FACHADA_CRIT, W_EXP_FACHADA_CRIT, W_RESP_FACHADA_CRIT = 0.75, 0.20, 0.05

# Pesos internos de V_intrínseca (§3.1)
W_VULN_INTERNAL = {
    "v_edad": 0.10,
    "v_altura": 0.15,
    "v_fachada": 0.30,
    "v_ite": 0.15,
    "v_sci": 0.20,
    "v_cubierta": 0.10,
}

# Pesos internos de E_exposición (§3.2)
W_EXP_INTERNAL = {
    "e_densidad": 0.40,
    "e_vulnerab": 0.35,
    "e_sensibles": 0.25,
}

# Pesos internos de R_respuesta (§3.3)
W_RESP_INTERNAL = {
    "r_tiempo": 0.65,
    "r_hidrante": 0.20,
    "r_acceso": 0.15,
}

# Tablas paramétricas (§3.1)
# Las fachadas SATE con núcleo combustible (EPS / XPS sin barrera
# cortafuegos) son una categoría adicional muy común en rehabilitaciones
# energéticas de la última década en València.
TABLA_FACHADA = {
    "ladrillo": 0,
    "mortero": 10,
    "vidrio": 30,
    "composite-cte": 60,
    "sate-combustible": 80,
    "composite-acmpe": 100,
}
TABLA_ITE = {"favorable": 0, "pendiente": 50, "desfavorable": 100}
TABLA_SCI = {"completo": 0, "parcial": 35, "extintores": 70, "ninguno": 100}
TABLA_CUBIERTA = {"tradicional": 0, "mixto": 40, "combustible": 100}

# Velocidad efectiva por hora del día (§3.3.1)
V_HORA_KMH: dict[int, float] = {
    **{h: 60.0 for h in range(0, 7)},    # madrugada 00-06
    **{h: 30.0 for h in [7, 8, 9]},      # punta mañana
    **{h: 45.0 for h in [10, 11, 12, 13]},
    **{h: 40.0 for h in [14, 15]},
    **{h: 40.0 for h in [16, 17, 18]},
    **{h: 30.0 for h in [19, 20]},       # punta tarde
    **{h: 50.0 for h in [21, 22, 23]},
}

T_MOVILIZACION_MIN = 1.0
FACTOR_TORTUOSIDAD = 1.3  # corrección distancia euclidiana → distancia ruta

# Escenarios canónicos (§5)
ESCENARIOS: dict[str, dict] = {
    "campanar": {
        # Reproducción del incidente del 22-feb-2024 a las 17:30 aprox.
        # Edificio Maravillas (Av. del Maestro Rodrigo 2, Campanar).
        "descripcion": "Incidente Campanar real (2024-02-22 ~17:30)",
        "lon": -0.3976,
        "lat": 39.4847,
        "plantas": 14,
        "anio": 2006,
        "fachada": "composite-acmpe",
        "ite": "pendiente",
        "sci": "parcial",
        "cubierta": "mixto",
        "hora": 17,
        "saturacion": "libre",
        "barrio_vuln": 55,
        "densidad": 65,
        "equip_sensibles": "ninguno",
    },
    "carmen": {
        # Edificio histórico tipo Ciutat Vella / El Carme, madrugada.
        "descripcion": "Edificio histórico Centro · madrugada",
        "lon": -0.3760,
        "lat": 39.4790,
        "plantas": 5,
        "anio": 1920,
        "fachada": "ladrillo",
        "ite": "pendiente",
        "sci": "ninguno",
        "cubierta": "combustible",
        "hora": 3,
        "saturacion": "libre",
        "barrio_vuln": 70,
        "densidad": 90,
        "equip_sensibles": "ninguno",
    },
    "quatre-carreres-nuevo": {
        # Edificio nuevo en Quatre Carreres, hora punta de la mañana.
        "descripcion": "Promoción nueva Quatre Carreres · hora punta",
        "lon": -0.3590,
        "lat": 39.4500,
        "plantas": 8,
        "anio": 2020,
        "fachada": "composite-cte",
        "ite": "favorable",
        "sci": "completo",
        "cubierta": "tradicional",
        "hora": 9,
        "saturacion": "libre",
        "barrio_vuln": 35,
        "densidad": 55,
        "equip_sensibles": "educativo",
    },
}


# === Funciones de los sub-factores conocidos ================================

def v_edad(anio: int) -> float:
    """Vulnerabilidad por año de construcción (§3.1).

    Los cortes están alineados con los hitos normativos españoles en
    seguridad contra incendios:
      - post-2017 → RIPCI revisado: muy bajo (0)
      - 2006-2017 → CTE DB-SI obligatorio: bajo (20)
      - 1991-2006 → NBE-CPI-91: medio (50)
      - pre-1991  → sin normativa formal: alto (100)
    """
    if anio > 2017:
        return 0.0
    if anio > 2006:
        return 20.0
    if anio > 1991:
        return 50.0
    return 100.0


def v_altura(plantas: int) -> float:
    """Vulnerabilidad por altura del edificio (§3.1).

    Función continua que captura el «efecto chimenea»: 7 puntos por
    planta, saturado a 100 en edificios ≥ 15 plantas.
    """
    return min(100.0, max(0.0, plantas * 7.0))


def r_tiempo(t_min: float) -> float:
    """Penalización por tiempo de llegada de bomberos (§3.3.2)."""
    if t_min <= 4:
        return 0.0
    if t_min <= 6:
        return 30.0
    if t_min <= 8:
        return 60.0
    if t_min <= 12:
        return 85.0
    return 100.0


def r_hidrante_default() -> float:
    """Valor intermedio mientras no se cruza con `hidrants.geojson`."""
    return 50.0


def r_acceso_default() -> float:
    """Valor intermedio mientras no se cruza con `fites_bombers.geojson`
    y el grafo de calles. Asume calle de tráfico rodado normal."""
    return 30.0


# === Geometría: distancia y selección de parque =============================

def haversine_m(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    """Distancia entre dos puntos lat/lon en metros sobre la esfera."""
    R = 6_371_000.0
    rlat1, rlat2 = math.radians(lat1), math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(rlat1) * math.cos(rlat2) * math.sin(dlon / 2) ** 2
    )
    return 2 * R * math.asin(math.sqrt(a))


def cargar_parques(path: Path = PARQUES_PATH) -> list[dict]:
    if not path.exists():
        raise FileNotFoundError(
            f"No existe {path}. Ejecuta antes "
            f"`python scripts/construir_parques_bomberos.py`."
        )
    data = json.loads(path.read_text(encoding="utf-8"))
    out = []
    for f in data["features"]:
        lon, lat = f["geometry"]["coordinates"]
        out.append({
            "nombre": f["properties"]["nombre"],
            "lon": lon,
            "lat": lat,
        })
    return out


def parque_mas_cercano(
    lon: float, lat: float, parques: list[dict],
    saturados: list[str] | None = None,
) -> tuple[dict, float]:
    """Devuelve (parque, distancia_m_euclidiana). Salta los nombres en
    `saturados`."""
    saturados = saturados or []
    candidatos = [
        (p, haversine_m(lon, lat, p["lon"], p["lat"]))
        for p in parques
        if p["nombre"] not in saturados
    ]
    if not candidatos:
        raise RuntimeError("Todos los parques marcados como saturados.")
    return min(candidatos, key=lambda x: x[1])


# === Dimensiones del modelo =================================================

def vulnerabilidad_intrinseca(
    plantas: int, anio: int,
    fachada: str, ite: str, sci: str, cubierta: str,
) -> tuple[float, dict]:
    """V_intrínseca (§3.1). Devuelve (puntuación, desglose)."""
    sub = {
        "v_edad": v_edad(anio),
        "v_altura": v_altura(plantas),
        "v_fachada": TABLA_FACHADA[fachada],
        "v_ite": TABLA_ITE[ite],
        "v_sci": TABLA_SCI[sci],
        "v_cubierta": TABLA_CUBIERTA[cubierta],
    }
    media_ponderada = sum(sub[k] * w for k, w in W_VULN_INTERNAL.items())

    # Saturación por fachada combustible amplificada por altura:
    # cuando la fachada se clasifica como `composite-acmpe`, el riesgo
    # estructural en edificios altos escala no linealmente por el
    # "efecto chimenea" demostrado en Campanar. El régimen «fachada
    # crítica» se activa siempre que la fachada combustible esté
    # presente — esto cambia los pesos de la combinación final, aunque
    # el valor concreto de V_intrínseca ya estuviera al máximo por
    # otros factores. El «piso» eleva V si la media ponderada no lo
    # alcanzaba.
    if sub["v_fachada"] >= 100:
        piso = sub["v_fachada"] * (1.0 + 0.5 * sub["v_altura"] / 100.0)
        piso = min(piso, 100.0)
        sub["__regla_aplicada__"] = (
            f"fachada combustible × altura (piso {piso:.1f})"
        )
        if piso > media_ponderada:
            media_ponderada = piso

    return round(media_ponderada, 1), sub


def factor_uso_ocupacion(uso: str | None, hora: int) -> float:
    """Probabilidad de ocupación efectiva del edificio según uso y hora.
    Modula E para reconocer que un edificio residencial a las 3 AM tiene
    más víctimas potenciales que un edificio de oficinas a la misma hora,
    y al revés a las 11:00."""
    if uso is None:
        return 1.0
    u = uso.lower()
    if "residential" in u or u.startswith("1_"):
        if 0 <= hora < 6:   return 1.0
        if 6 <= hora < 9:   return 0.85
        if 9 <= hora < 17:  return 0.45
        if 17 <= hora < 22: return 0.9
        return 1.0
    if "industrial" in u or u.startswith("3_"):
        return 0.9 if 8 <= hora < 18 else 0.1
    if "office" in u or "4_1" in u:
        return 0.95 if 8 <= hora < 19 else 0.1
    if "agriculture" in u or u.startswith("2_"):
        return 0.4 if 7 <= hora < 19 else 0.05
    return 0.6  # otros / desconocido


def exposicion(
    barrio_vuln: float = 50.0,
    densidad: float = 50.0,
    equip_sensibles: str = "ninguno",
    uso: str | None = None,
    hora: int = 12,
) -> tuple[float, dict]:
    """E_exposición (§3.2). Recibe los sub-factores ya escalados 0-100.
    Si se proporciona `uso` del edificio, modula el total por la
    probabilidad de ocupación a esa hora."""
    e_sensibles_tabla = {
        "residencia": 100,
        "hospital": 80,
        "educativo": 60,
        "ninguno": 0,
    }
    sub = {
        "e_densidad": densidad,
        "e_vulnerab": barrio_vuln,
        "e_sensibles": e_sensibles_tabla[equip_sensibles],
    }
    base = sum(sub[k] * w for k, w in W_EXP_INTERNAL.items())
    factor = factor_uso_ocupacion(uso, hora)
    total = base * factor
    sub["factor_ocupacion"] = round(factor, 2)
    return round(total, 1), sub


def respuesta(
    lon: float, lat: float, hora: int, saturacion: str,
    parques: list[dict],
) -> tuple[float, dict]:
    """R_respuesta (§3.3). Calcula tiempo de llegada y combina."""
    saturados: list[str] = []
    if saturacion == "primero-ocupado":
        p1, _ = parque_mas_cercano(lon, lat, parques)
        saturados = [p1["nombre"]]
    p_eff, d_euclid_m = parque_mas_cercano(lon, lat, parques, saturados=saturados)

    d_ruta_m = d_euclid_m * FACTOR_TORTUOSIDAD
    v_kmh = V_HORA_KMH[hora]
    t_viaje_min = (d_ruta_m / 1000.0) / v_kmh * 60.0
    t_llegada_min = T_MOVILIZACION_MIN + t_viaje_min

    sub = {
        "r_tiempo": r_tiempo(t_llegada_min),
        "r_hidrante": r_hidrante_default(),
        "r_acceso": r_acceso_default(),
    }
    total = sum(sub[k] * w for k, w in W_RESP_INTERNAL.items())

    detalle = {
        **sub,
        "parque_efectivo": p_eff["nombre"],
        "distancia_euclidiana_m": round(d_euclid_m),
        "distancia_ruta_estimada_m": round(d_ruta_m),
        "velocidad_efectiva_kmh": v_kmh,
        "tiempo_llegada_min": round(t_llegada_min, 1),
    }
    return round(total, 1), detalle


# === Combinación final ======================================================

def riesgo(
    lon: float, lat: float,
    plantas: int, anio: int,
    fachada: str, ite: str, sci: str, cubierta: str,
    hora: int, saturacion: str = "libre",
    barrio_vuln: float = 50.0, densidad: float = 50.0,
    equip_sensibles: str = "ninguno",
    uso: str | None = None,
    parques: list[dict] | None = None,
) -> dict:
    """Calcula el índice de riesgo (0-100) y devuelve el desglose completo."""
    if parques is None:
        parques = cargar_parques()

    V, sub_V = vulnerabilidad_intrinseca(plantas, anio, fachada, ite, sci, cubierta)
    E, sub_E = exposicion(barrio_vuln, densidad, equip_sensibles, uso, hora)
    R, sub_R = respuesta(lon, lat, hora, saturacion, parques)

    # Pesos dinámicos: si la fachada×altura saturó V_intrínseca, los
    # pesos cambian a la configuración «fachada crítica». Ver
    # docs/modelo-riesgo.md §4.
    fachada_critica = "__regla_aplicada__" in sub_V
    if fachada_critica:
        w_V, w_E, w_R = W_VULN_FACHADA_CRIT, W_EXP_FACHADA_CRIT, W_RESP_FACHADA_CRIT
    else:
        w_V, w_E, w_R = W_VULN, W_EXP, W_RESP

    total = w_V * V + w_E * E + w_R * R
    total = max(0.0, min(100.0, total))

    return {
        "riesgo_total": round(total, 1),
        "componentes": {
            "V_intrinseca": V,
            "E_exposicion": E,
            "R_respuesta": R,
        },
        "pesos": {
            "w_V": w_V,
            "w_E": w_E,
            "w_R": w_R,
            "regimen": "fachada-critica" if fachada_critica else "normal",
        },
        "subfactores_V": sub_V,
        "subfactores_E": sub_E,
        "subfactores_R": sub_R,
        "version_modelo": "0.1",
    }


# === Motor de recomendaciones, banda de confianza y plan operativo =========
# Estas funciones replican la lógica del modelo JS del frontend
# (`web/modelo.js`). Su existencia en Python permite (a) testear la
# lógica con pytest y (b) usarla en futuros batches o análisis.

_LABEL_FACHADA = {
    "ladrillo": "Ladrillo / mortero tradicional",
    "mortero": "Mortero",
    "vidrio": "Muro cortina de vidrio",
    "composite-cte": "Composite con cumplimiento CTE",
    "sate-combustible": "SATE con núcleo combustible (EPS/XPS)",
    "composite-acmpe": "Composite con núcleo combustible (ACM-PE)",
}
_LABEL_ITE = {"favorable": "Favorable", "pendiente": "Pendiente", "desfavorable": "Desfavorable"}
_LABEL_SCI = {"completo": "Completo", "parcial": "Parcial", "extintores": "Solo extintores", "ninguno": "Ninguno"}
_LABEL_CUBIERTA = {"tradicional": "Tradicional", "mixto": "Mixto", "combustible": "Combustible"}

_ORDENES_PARAM = {
    "fachada": ["ladrillo", "mortero", "vidrio", "composite-cte", "sate-combustible", "composite-acmpe"],
    "ite": ["favorable", "pendiente", "desfavorable"],
    "sci": ["completo", "parcial", "extintores", "ninguno"],
    "cubierta": ["tradicional", "mixto", "combustible"],
}

_VARS_MEJORABLES = [
    ("fachada", TABLA_FACHADA, _LABEL_FACHADA, "Fachada"),
    ("ite", TABLA_ITE, _LABEL_ITE, "ITE"),
    ("sci", TABLA_SCI, _LABEL_SCI, "Sistema contra incendios"),
    ("cubierta", TABLA_CUBIERTA, _LABEL_CUBIERTA, "Cubierta"),
]


def recomendaciones(base_input: dict, parques: list[dict] | None = None) -> dict:
    """Devuelve top-3 mejoras paramétricas ordenadas por delta del
    riesgo, junto con una nota si la fachada combustible domina."""
    baseline = riesgo(parques=parques, **base_input)["riesgo_total"]
    propuestas = []
    for campo, tabla, etiqueta_labels, etiqueta_campo in _VARS_MEJORABLES:
        actual = base_input[campo]
        score_actual = tabla[actual]
        mejor_delta = 0.0
        mejor_val = None
        mejor_riesgo = None
        for nuevo_val, nuevo_score in tabla.items():
            if nuevo_score >= score_actual:
                continue
            inp_mod = {**base_input, campo: nuevo_val}
            r = riesgo(parques=parques, **inp_mod)["riesgo_total"]
            d = baseline - r
            if d > mejor_delta:
                mejor_delta = d
                mejor_val = nuevo_val
                mejor_riesgo = r
        if mejor_val is not None:
            propuestas.append({
                "campo": campo,
                "etiqueta_campo": etiqueta_campo,
                "valor_actual": actual,
                "valor_propuesto": mejor_val,
                "label_actual": etiqueta_labels[actual],
                "label_propuesto": etiqueta_labels[mejor_val],
                "delta": round(mejor_delta, 1),
                "nuevo_riesgo": round(mejor_riesgo, 1),
            })
    propuestas.sort(key=lambda p: p["delta"], reverse=True)
    top = [p for p in propuestas if p["delta"] >= 0.1][:3]
    nota = None
    fachada_critica = base_input["fachada"] in ("composite-acmpe", "sate-combustible")
    if fachada_critica and len(top) < 3:
        nota = (
            "Mientras la fachada combustible persista, las otras mejoras "
            "paramétricas (ITE, SCI, cubierta) tienen efecto muy limitado: "
            "la vulnerabilidad estructural queda saturada por la fachada."
        )
    elif not top:
        nota = "Este edificio ya está en la mejor configuración paramétrica posible."
    return {"baseline": round(baseline, 1), "recomendaciones": top, "nota": nota}


def banda_confianza(base_input: dict, parques: list[dict] | None = None) -> dict:
    """Rango plausible variando los paramétricos UN escalón arriba/abajo."""
    mejor = dict(base_input)
    peor = dict(base_input)
    for campo, orden in _ORDENES_PARAM.items():
        try:
            i = orden.index(base_input[campo])
        except ValueError:
            continue
        if i > 0:
            mejor[campo] = orden[i - 1]
        if i < len(orden) - 1:
            peor[campo] = orden[i + 1]
    b = riesgo(parques=parques, **mejor)["riesgo_total"]
    w = riesgo(parques=parques, **peor)["riesgo_total"]
    return {"best": round(b, 1), "worst": round(w, 1)}


def plan_respuesta(plantas: int, fachada: str, hora: int = 12,
                   equip_sensibles: str = "ninguno") -> dict:
    """Estima el despliegue del SPEIS. Heurística no protocolo oficial."""
    plantas = max(1, int(plantas))
    fachada_critica = fachada in ("composite-acmpe", "sate-combustible")
    if plantas <= 3:
        dotaciones, efectivos = 1, 5
        vehiculos = ["BUL (bomba urbana ligera)"]
    elif plantas <= 8:
        dotaciones, efectivos = 2, 12
        vehiculos = ["BUL", "Autoescala"]
    elif plantas <= 14:
        dotaciones, efectivos = 3, 18
        vehiculos = ["BUL", "BUP", "Autoescala", "UEMSV (médico)"]
    else:
        dotaciones, efectivos = 4, 25
        vehiculos = ["BUL", "BUP", "Autoescala-jumbo", "UEMSV", "Mando intermedio"]
    if fachada_critica:
        dotaciones += 1
        efectivos += 7
        vehiculos.append("Refuerzo del Consorcio Provincial")
    if equip_sensibles in ("residencia", "hospital"):
        dotaciones += 1
        efectivos += 5
        vehiculos.append("UEMSV adicional (evacuación asistida)")
    if plantas <= 5:
        r_evac = 50
    elif plantas <= 10:
        r_evac = 75
    else:
        r_evac = 100
    caudal = round(dotaciones * 500 * 1.3)
    t_control = 8 + max(0, plantas - 5) * 4
    if fachada_critica:
        t_control *= 2
    t_control = min(240, t_control)
    return {
        "dotaciones": dotaciones,
        "efectivos": efectivos,
        "vehiculos": vehiculos,
        "radio_evacuacion_m": r_evac,
        "radio_perimetro_m": r_evac * 2,
        "caudal_lmin": caudal,
        "tiempo_control_min": int(t_control),
        "fachada_critica": fachada_critica,
    }


# === CLI ====================================================================

def construir_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Calcula el índice de riesgo de incendio según el modelo v0.1.",
    )
    ap.add_argument(
        "--escenario",
        choices=list(ESCENARIOS),
        help="Usa un escenario canónico como base. Los demás --flags lo sobrescriben.",
    )
    ap.add_argument("--plantas", type=int)
    ap.add_argument("--anio", type=int, help="Año de construcción del edificio.")
    ap.add_argument("--lon", type=float)
    ap.add_argument("--lat", type=float)
    ap.add_argument("--fachada", choices=list(TABLA_FACHADA))
    ap.add_argument("--ite", choices=list(TABLA_ITE))
    ap.add_argument("--sci", choices=list(TABLA_SCI))
    ap.add_argument("--cubierta", choices=list(TABLA_CUBIERTA))
    ap.add_argument("--hora", type=int, choices=range(24))
    ap.add_argument("--saturacion", choices=["libre", "primero-ocupado"], default=None)
    ap.add_argument("--barrio-vuln", type=float, dest="barrio_vuln")
    ap.add_argument("--densidad", type=float)
    ap.add_argument(
        "--equip-sensibles",
        choices=["residencia", "hospital", "educativo", "ninguno"],
        dest="equip_sensibles",
    )
    ap.add_argument(
        "--todos-escenarios",
        action="store_true",
        help="Ejecuta los tres escenarios canónicos y los compara.",
    )
    return ap


def cli() -> int:
    args = construir_parser().parse_args()

    if args.todos_escenarios:
        parques = cargar_parques()
        print("=== Comparativa de los escenarios canónicos ===\n")
        for nombre in ESCENARIOS:
            cfg = {k: v for k, v in ESCENARIOS[nombre].items() if k != "descripcion"}
            res = riesgo(parques=parques, **cfg)
            print(f"--- {nombre} · {ESCENARIOS[nombre]['descripcion']} ---")
            print(f"  Riesgo total: {res['riesgo_total']:5.1f} / 100")
            for k, v in res["componentes"].items():
                print(f"    {k:15s}: {v:5.1f}")
            print(f"  Parque efectivo:  {res['subfactores_R']['parque_efectivo']}")
            print(f"  Tiempo llegada:   {res['subfactores_R']['tiempo_llegada_min']} min")
            print()
        return 0

    cfg: dict = {}
    if args.escenario:
        cfg = {k: v for k, v in ESCENARIOS[args.escenario].items() if k != "descripcion"}

    for k in [
        "plantas", "anio", "lon", "lat", "fachada", "ite", "sci", "cubierta",
        "hora", "saturacion", "barrio_vuln", "densidad", "equip_sensibles",
    ]:
        v = getattr(args, k)
        if v is not None:
            cfg[k] = v

    requeridos = [
        "plantas", "anio", "lon", "lat", "fachada", "ite", "sci", "cubierta", "hora",
    ]
    falta = [k for k in requeridos if k not in cfg]
    if falta:
        print(f"ERROR: faltan parámetros: {falta}", file=sys.stderr)
        print("Sugerencia: usa --escenario {campanar|carmen|quatre-carreres-nuevo}",
              file=sys.stderr)
        return 2

    cfg.setdefault("saturacion", "libre")
    parques = cargar_parques()
    res = riesgo(parques=parques, **cfg)
    print(json.dumps(res, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(cli())
