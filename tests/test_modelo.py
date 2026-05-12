"""
Tests del modelo paramétrico de riesgo. Cubre:

  1. Los tres escenarios canónicos documentados en docs/modelo-riesgo.md
     dan resultados dentro de las franjas esperadas y en el orden
     correcto.
  2. Los tests de validación cualitativa del documento (sensibilidad a
     fachada, sensibilidad horaria con edificio lejano).
  3. Edge cases: edificios extremos, valores límite.

Ejecutar con:
    .venv/Scripts/python.exe -m pytest tests/test_modelo.py -v
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from calcular_riesgo import (  # noqa: E402
    ESCENARIOS,
    cargar_parques,
    riesgo,
    v_edad,
    v_altura,
)


@pytest.fixture(scope="module")
def parques():
    return cargar_parques()


# ---------------------------------------------------------------------------
# 1. Escenarios canónicos
# ---------------------------------------------------------------------------

def _calc(escenario: str, parques, **overrides):
    cfg = {k: v for k, v in ESCENARIOS[escenario].items() if k != "descripcion"}
    cfg.update(overrides)
    return riesgo(parques=parques, **cfg)


def test_campanar_en_franja_critica(parques):
    """Campanar real debe estar ≥ 80 (régimen fachada-crítica)."""
    r = _calc("campanar", parques)
    assert r["pesos"]["regimen"] == "fachada-critica"
    assert r["riesgo_total"] >= 80, (
        f"Campanar dio {r['riesgo_total']}, esperado ≥ 80"
    )


def test_orden_escenarios(parques):
    """Campanar > Carmen > Quatre Carreres."""
    campanar = _calc("campanar", parques)["riesgo_total"]
    carmen = _calc("carmen", parques)["riesgo_total"]
    qc = _calc("quatre-carreres-nuevo", parques)["riesgo_total"]
    assert campanar > carmen > qc, (
        f"Orden mal: campanar={campanar} carmen={carmen} qc={qc}"
    )


# ---------------------------------------------------------------------------
# 2. Sensibilidad a la fachada
# ---------------------------------------------------------------------------

def test_sensibilidad_fachada(parques):
    """Campanar con fachada de ladrillo debe bajar al menos un 30 %."""
    base = _calc("campanar", parques)["riesgo_total"]
    sin_acm = _calc("campanar", parques, fachada="ladrillo")["riesgo_total"]
    caida = (base - sin_acm) / base
    assert caida >= 0.30, (
        f"Caída solo del {caida*100:.1f}%, esperado ≥ 30%"
    )


# ---------------------------------------------------------------------------
# 3. Sensibilidad horaria
# ---------------------------------------------------------------------------

def test_sensibilidad_horaria_lejano(parques):
    """Edificio en Borbotó (lejos del parque): a las 8 punta debe dar
    más riesgo que a las 4 madrugada."""
    base = dict(
        lon=-0.382, lat=39.527, plantas=4, anio=1990,
        fachada="ladrillo", ite="favorable", sci="parcial", cubierta="tradicional",
        saturacion="libre",
        barrio_vuln=40, densidad=30, equip_sensibles="ninguno",
    )
    r4 = riesgo(parques=parques, hora=4, **base)["riesgo_total"]
    r8 = riesgo(parques=parques, hora=8, **base)["riesgo_total"]
    assert r8 > r4, f"Hora no discrimina: 4h={r4} 8h={r8}"


# ---------------------------------------------------------------------------
# 4. Funciones puras: v_edad y v_altura
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("anio,esperado", [
    (2020, 0),     # post-2017
    (2010, 20),    # 2006-2017
    (2006, 50),    # 2006 cae en 1991-2006 según la lógica > 1991, no > 2006
    (2000, 50),    # 1991-2006
    (1991, 100),   # justo el límite — > 1991 es false
    (1985, 100),   # pre-1991
    (1850, 100),
])
def test_v_edad_cortes_normativos(anio, esperado):
    assert v_edad(anio) == esperado, (
        f"v_edad({anio}) = {v_edad(anio)}, esperado {esperado}"
    )


@pytest.mark.parametrize("plantas,esperado_min,esperado_max", [
    (1, 7, 7),
    (3, 21, 21),
    (10, 70, 70),
    (14, 98, 98),
    (15, 100, 100),
    (30, 100, 100),
])
def test_v_altura_continua(plantas, esperado_min, esperado_max):
    v = v_altura(plantas)
    assert esperado_min <= v <= esperado_max, (
        f"v_altura({plantas}) = {v}, esperado entre {esperado_min} y {esperado_max}"
    )


# ---------------------------------------------------------------------------
# 5. Edge cases
# ---------------------------------------------------------------------------

def test_edificio_perfecto(parques):
    """Edificio nuevo con todo en su mejor configuración debe dar bajo."""
    r = riesgo(
        parques=parques,
        lon=-0.376, lat=39.47,
        plantas=2, anio=2024,
        fachada="ladrillo", ite="favorable", sci="completo", cubierta="tradicional",
        hora=12, saturacion="libre",
        barrio_vuln=20, densidad=20, equip_sensibles="ninguno",
    )
    assert r["riesgo_total"] < 25, (
        f"Edificio perfecto dio {r['riesgo_total']}, esperado < 25"
    )


def test_edificio_catastrofico(parques):
    """Edificio con todo en su peor configuración debe dar muy alto."""
    r = riesgo(
        parques=parques,
        lon=-0.382, lat=39.527,  # Borbotó, lejos
        plantas=20, anio=1900,
        fachada="composite-acmpe", ite="desfavorable", sci="ninguno",
        cubierta="combustible",
        hora=8, saturacion="primero-ocupado",
        barrio_vuln=100, densidad=100, equip_sensibles="residencia",
    )
    assert r["riesgo_total"] >= 85, (
        f"Edificio catastrófico dio {r['riesgo_total']}, esperado ≥ 85"
    )
    assert r["pesos"]["regimen"] == "fachada-critica"
