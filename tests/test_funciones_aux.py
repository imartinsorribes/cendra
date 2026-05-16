"""
Tests de las funciones auxiliares del modelo:
  - `recomendaciones()`
  - `banda_confianza()`
  - `plan_respuesta()`

Verifican que el comportamiento de las funciones cumple las
propiedades cualitativas documentadas en `docs/modelo-riesgo.md` §8.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from calcular_riesgo import (  # noqa: E402
    ESCENARIOS,
    banda_confianza,
    cargar_parques,
    plan_respuesta,
    recomendaciones,
)


@pytest.fixture(scope="module")
def parques():
    return cargar_parques()


def _esc(nombre: str) -> dict:
    return {k: v for k, v in ESCENARIOS[nombre].items() if k != "descripcion"}


# ---------------------------------------------------------------------------
# Recomendaciones
# ---------------------------------------------------------------------------

def test_recos_campanar_devuelve_fachada_como_top(parques):
    res = recomendaciones(_esc("campanar"), parques=parques)
    assert res["recomendaciones"], "Campanar debe tener al menos 1 recomendación"
    assert res["recomendaciones"][0]["campo"] == "fachada", (
        f"La primera recomendación debe ser fachada, fue "
        f"{res['recomendaciones'][0]['campo']}"
    )
    # Y debe haber nota explicativa por régimen FC
    assert res["nota"] is not None
    assert "fachada combustible" in res["nota"].lower()


def test_recos_carmen_devuelve_tres_distintas(parques):
    res = recomendaciones(_esc("carmen"), parques=parques)
    assert len(res["recomendaciones"]) == 3
    campos = [r["campo"] for r in res["recomendaciones"]]
    assert len(set(campos)) == 3, f"Recomendaciones duplicadas en campos: {campos}"


def test_recos_edificio_perfecto_sin_recomendaciones(parques):
    perfecto = dict(
        lon=-0.376, lat=39.47,
        plantas=2, anio=2024,
        fachada="ladrillo", ite="favorable", sci="completo", cubierta="tradicional",
        hora=12, saturacion="libre",
        barrio_vuln=20, densidad=20, equip_sensibles="ninguno",
    )
    res = recomendaciones(perfecto, parques=parques)
    assert len(res["recomendaciones"]) == 0
    assert res["nota"] is not None


def test_recos_deltas_son_positivos(parques):
    res = recomendaciones(_esc("quatre-carreres-nuevo"), parques=parques)
    for r in res["recomendaciones"]:
        assert r["delta"] > 0, f"Delta no positivo: {r}"
        assert r["nuevo_riesgo"] < res["baseline"], (
            f"Nuevo riesgo {r['nuevo_riesgo']} no menor que baseline {res['baseline']}"
        )


# ---------------------------------------------------------------------------
# Banda de confianza
# ---------------------------------------------------------------------------

def test_banda_best_menor_que_worst(parques):
    for esc in ESCENARIOS:
        b = banda_confianza(_esc(esc), parques=parques)
        assert b["best"] <= b["worst"], f"{esc}: best={b['best']} > worst={b['worst']}"


def test_banda_es_estrecha_no_extremos(parques):
    """La banda con un escalón nunca debe pasar de 0 a 100."""
    b = banda_confianza(_esc("quatre-carreres-nuevo"), parques=parques)
    span = b["worst"] - b["best"]
    assert span < 50, f"Banda demasiado ancha: {span} (best={b['best']} worst={b['worst']})"


# ---------------------------------------------------------------------------
# Plan de respuesta SPEIS
# ---------------------------------------------------------------------------

def test_plan_creciente_con_altura():
    p1 = plan_respuesta(2, fachada="ladrillo")
    p7 = plan_respuesta(7, fachada="ladrillo")
    p14 = plan_respuesta(14, fachada="ladrillo")
    p20 = plan_respuesta(20, fachada="ladrillo")
    assert p1["efectivos"] < p7["efectivos"] < p14["efectivos"] < p20["efectivos"]
    assert p1["dotaciones"] < p7["dotaciones"] < p14["dotaciones"] < p20["dotaciones"]


def test_plan_fachada_combustible_anyade_refuerzo():
    base = plan_respuesta(10, fachada="ladrillo")
    crit = plan_respuesta(10, fachada="composite-acmpe")
    assert crit["dotaciones"] == base["dotaciones"] + 1
    assert "Refuerzo del Consorcio Provincial" in crit["vehiculos"]
    assert crit["tiempo_control_min"] == base["tiempo_control_min"] * 2 or crit["tiempo_control_min"] == 240


def test_plan_equipamiento_sensible_anyade_uemsv():
    base = plan_respuesta(8, fachada="ladrillo", equip_sensibles="ninguno")
    con_res = plan_respuesta(8, fachada="ladrillo", equip_sensibles="residencia")
    assert con_res["dotaciones"] == base["dotaciones"] + 1
    assert any("UEMSV adicional" in v for v in con_res["vehiculos"])


def test_plan_radio_evacuacion_crece_con_altura():
    assert plan_respuesta(3, fachada="ladrillo")["radio_evacuacion_m"] == 50
    assert plan_respuesta(8, fachada="ladrillo")["radio_evacuacion_m"] == 75
    assert plan_respuesta(15, fachada="ladrillo")["radio_evacuacion_m"] == 100


def test_plan_caudal_tiene_margen_30():
    p = plan_respuesta(10, fachada="ladrillo")
    # 3 dotaciones × 500 L/min × 1.3 = 1950
    assert p["caudal_lmin"] == 1950


def test_plan_tope_tiempo_240():
    """Edificio gigante con fachada combustible no debe pasar de 240 min."""
    p = plan_respuesta(40, fachada="composite-acmpe")
    assert p["tiempo_control_min"] == 240
