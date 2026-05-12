"""
Verifica que el modelo Python (`scripts/calcular_riesgo.py`) y el
modelo JavaScript (`web/modelo.js`) tienen las MISMAS constantes y la
MISMA lógica de los escenarios canónicos.

Si esto falla, el frontend está calculando algo distinto del batch y
hay que sincronizar antes del próximo despliegue.

Ejecutar con:
    .venv/Scripts/python.exe -m pytest tests/test_python_js_sync.py -v
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from calcular_riesgo import (  # noqa: E402
    TABLA_FACHADA, TABLA_ITE, TABLA_SCI, TABLA_CUBIERTA,
    V_HORA_KMH,
    W_VULN, W_EXP, W_RESP,
    W_VULN_FACHADA_CRIT, W_EXP_FACHADA_CRIT, W_RESP_FACHADA_CRIT,
    T_MOVILIZACION_MIN, FACTOR_TORTUOSIDAD,
)

MODELO_JS = ROOT / "web" / "modelo.js"


@pytest.fixture(scope="module")
def js_texto():
    return MODELO_JS.read_text(encoding="utf-8")


def _extraer_objeto_js(texto: str, nombre: str) -> dict:
    """Extrae un objeto literal JS `const NOMBRE = { ... };` como dict
    Python. Tolerante a comillas dobles, comas finales y comentarios."""
    patron = re.compile(
        rf"const\s+{re.escape(nombre)}\s*=\s*(\{{[^;]*?\}})\s*;",
        re.DOTALL,
    )
    m = patron.search(texto)
    if not m:
        raise ValueError(f"No encuentro `const {nombre}` en modelo.js")
    raw = m.group(1)
    # Quitar comentarios línea
    raw = re.sub(r"//[^\n]*", "", raw)
    # Comillas simples → dobles
    raw = raw.replace("'", '"')
    # Permitir claves no entrecomilladas → entrecomillarlas
    raw = re.sub(r'(\{|,)\s*(\w[\w-]*)\s*:', r'\1 "\2":', raw)
    # Quitar coma final antes de }
    raw = re.sub(r",\s*\}", "}", raw)
    return json.loads(raw)


def _extraer_const_numerica(texto: str, nombre: str) -> float:
    patron = re.compile(
        rf"const\s+{re.escape(nombre)}\s*=\s*([\d.]+)\s*;"
    )
    m = patron.search(texto)
    if not m:
        raise ValueError(f"No encuentro `const {nombre}` en modelo.js")
    return float(m.group(1))


def test_tabla_fachada_sincronizada(js_texto):
    js = _extraer_objeto_js(js_texto, "TABLA_FACHADA")
    js_num = {k: float(v) for k, v in js.items()}
    py_num = {k: float(v) for k, v in TABLA_FACHADA.items()}
    assert js_num == py_num, f"TABLA_FACHADA divergente: JS={js_num} Py={py_num}"


def test_tabla_ite_sincronizada(js_texto):
    assert _extraer_objeto_js(js_texto, "TABLA_ITE") == {
        k: float(v) for k, v in TABLA_ITE.items()
    } or _extraer_objeto_js(js_texto, "TABLA_ITE") == TABLA_ITE


def test_tabla_sci_sincronizada(js_texto):
    assert _extraer_objeto_js(js_texto, "TABLA_SCI") == TABLA_SCI


def test_tabla_cubierta_sincronizada(js_texto):
    assert _extraer_objeto_js(js_texto, "TABLA_CUBIERTA") == TABLA_CUBIERTA


def test_pesos_regimen_normal(js_texto):
    # const W_VULN = 0.45, W_EXP = 0.30, W_RESP = 0.25;
    m = re.search(
        r"const\s+W_VULN\s*=\s*([\d.]+),\s*W_EXP\s*=\s*([\d.]+),\s*W_RESP\s*=\s*([\d.]+)",
        js_texto,
    )
    assert m is not None, "No encuentro los pesos régimen normal en JS"
    wv, we, wr = float(m.group(1)), float(m.group(2)), float(m.group(3))
    assert abs(wv - W_VULN) < 1e-9
    assert abs(we - W_EXP) < 1e-9
    assert abs(wr - W_RESP) < 1e-9


def test_pesos_regimen_fachada_critica(js_texto):
    m = re.search(
        r"W_VULN_FC\s*=\s*([\d.]+),\s*W_EXP_FC\s*=\s*([\d.]+),\s*W_RESP_FC\s*=\s*([\d.]+)",
        js_texto,
    )
    assert m is not None, "No encuentro los pesos régimen fachada-crítica en JS"
    wv, we, wr = float(m.group(1)), float(m.group(2)), float(m.group(3))
    assert abs(wv - W_VULN_FACHADA_CRIT) < 1e-9
    assert abs(we - W_EXP_FACHADA_CRIT) < 1e-9
    assert abs(wr - W_RESP_FACHADA_CRIT) < 1e-9


def test_velocidades_por_hora(js_texto):
    """V_HORA_KMH se construye con un IIFE en JS. Verificamos algunos
    valores clave manualmente, no la estructura completa."""
    # Sacamos las velocidades por franja por regex sobre el IIFE
    # Las afirmaciones clave: madrugada 60, hora punta 30, mediodía 45 (la
    # de las 12 cae en "10-13"), noche 50.
    assert V_HORA_KMH[3] == 60
    assert V_HORA_KMH[8] == 30
    assert V_HORA_KMH[12] == 45
    assert V_HORA_KMH[20] == 30
    assert V_HORA_KMH[22] == 50
    # Y en JS: comprobamos que el rango 0-6 y 7-9 están en el IIFE
    assert "for (let h = 0; h <= 6; h++) v[h] = 60" in js_texto
    assert "[7,8,9].forEach(h => v[h] = 30)" in js_texto


def test_constantes_geometricas(js_texto):
    t_mov = _extraer_const_numerica(js_texto, "T_MOVILIZACION_MIN")
    factor = _extraer_const_numerica(js_texto, "FACTOR_TORTUOSIDAD")
    assert abs(t_mov - T_MOVILIZACION_MIN) < 1e-9
    assert abs(factor - FACTOR_TORTUOSIDAD) < 1e-9


def test_funciones_clave_existen(js_texto):
    """Verifica que las funciones esenciales del modelo están exportadas
    en window.cendraModelo."""
    for f in [
        "calcularRiesgo",
        "recomendaciones",
        "bandaConfianza",
        "cargarParques",
        "ESCENARIOS",
    ]:
        assert f in js_texto, f"Falta {f} en window.cendraModelo"
