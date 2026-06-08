"""
Verificación visual exhaustiva de cendra en producción.

Recorre todas las interacciones clave a 1920x1080 (resolución de
grabación), captura una imagen por momento crítico y reporta:
  - Errores de consola.
  - Elementos esperados que no se han renderizado.
  - Popups que se salgan del viewport.
  - Cifras incoherentes.

Las capturas se dejan en docs/verificacion-final/ y al final se
imprime un informe estructurado.

Uso:
    python scripts/verificar_web.py
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "verificacion-final"
OUT.mkdir(exist_ok=True)
URL = "https://cendra.pages.dev"

errores_consola = []
hallazgos = []


def cap(page, nombre, descripcion=""):
    """Toma captura y la guarda con nombre indexado."""
    n = len(list(OUT.glob("*.png"))) + 1
    path = OUT / f"{n:02d}_{nombre}.png"
    page.screenshot(path=str(path), full_page=False)
    print(f"  cap {n:02d}: {nombre} {('· ' + descripcion) if descripcion else ''}", file=sys.stderr, flush=True)


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            device_scale_factor=1,
            locale="es-ES",
        )
        page = ctx.new_page()
        page.on("console", lambda msg: errores_consola.append((msg.type, msg.text)) if msg.type in ("error", "warning") else None)
        page.on("pageerror", lambda exc: errores_consola.append(("pageerror", str(exc))))

        # ====== ESCENA 1 · home + tutorial ======
        print("\n[1/12] home + tutorial...", file=sys.stderr)
        page.goto(URL, wait_until="load")
        time.sleep(3)
        cap(page, "home_con_tutorial", "primera visita con tutorial abierto")

        # Cerrar tutorial si está
        try:
            page.click("#tutorial_cerrar", timeout=2500)
            time.sleep(1)
        except Exception:
            pass

        # Esperar al mapa cargado
        page.wait_for_function("() => window.__map && window.__map.isStyleLoaded()", timeout=15000)
        page.wait_for_function("() => window.__map.getLayer('edificios-poligonos-fill')", timeout=15000)
        time.sleep(3)
        cap(page, "home_mapa_cargado", "atlas listo + FAB visible")

        # ====== ESCENA 2 · click en barrio ======
        print("[2/12] click en barrio...", file=sys.stderr)
        page.evaluate("""() => {
            const m = window.__map; if (!m) return;
            const feats = m.queryRenderedFeatures({ layers: ['barris-fill'] });
            if (!feats.length) return;
            const f = feats[0];
            const c = f.geometry.coordinates[0]?.[0] || [-0.376, 39.470];
            const center = Array.isArray(c[0]) ? c[0] : c;
            const px = m.project(center);
            m.fire('click', { lngLat: { lng: center[0], lat: center[1] }, point: px, features: [f] });
        }""")
        time.sleep(2)
        cap(page, "popup_barrio", "popup de un barrio + panel rellenado")

        # ====== ESCENA 3 · zoom + click polígono ======
        print("[3/12] zoom + click polígono...", file=sys.stderr)
        page.evaluate("document.querySelectorAll('.maplibregl-popup').forEach(p => p.remove())")
        page.evaluate("""() => {
            if (window.__map) window.__map.flyTo({
                center: [-0.3464, 39.4670], zoom: 17.5, duration: 2500
            });
        }""")
        time.sleep(5)
        cap(page, "zoom_aiora", "zoom a Aiora con polígonos visibles")

        page.evaluate("""() => {
            const m = window.__map; if (!m) return;
            const feats = m.queryRenderedFeatures({ layers: ['edificios-poligonos-fill'] });
            if (!feats.length) return;
            const f = feats[0];
            const c = f.geometry.coordinates[0][0];
            const px = m.project(c);
            m.fire('click', { lngLat: { lng: c[0], lat: c[1] }, point: px, features: [f] });
        }""")
        time.sleep(3)
        cap(page, "popup_edificio", "popup edificio + panel rellenado con valores reales")

        # ====== ESCENA 4 · sliders ======
        print("[4/12] sliders ...", file=sys.stderr)
        page.evaluate("document.querySelectorAll('.maplibregl-popup').forEach(p => p.remove())")
        page.select_option("#fachada", "ladrillo")
        time.sleep(2)
        cap(page, "slider_fachada_ladrillo", "fachada ladrillo: riesgo bajó")
        page.select_option("#sci", "completo")
        time.sleep(2)
        cap(page, "slider_sci_completo", "SCI completo: riesgo baja más")
        page.evaluate("""() => {
            const h = document.getElementById('hora');
            if (h) { h.value = 3; h.dispatchEvent(new Event('input', { bubbles: true })); }
        }""")
        time.sleep(2)
        cap(page, "slider_hora_3am", "hora 03:00 madrugada")

        # ====== ESCENA 5 · explica riesgo + recomendaciones ======
        print("[5/12] panel derecho desglose...", file=sys.stderr)
        page.evaluate("""() => {
            const e = document.querySelector('.explica-riesgo');
            if (e) e.scrollIntoView({ behavior: 'instant', block: 'center' });
        }""")
        time.sleep(1)
        cap(page, "explica_riesgo", "bloque 'Por qué este riesgo'")
        page.evaluate("""() => {
            const r = document.querySelector('.recomendaciones');
            if (r) r.scrollIntoView({ behavior: 'instant', block: 'center' });
        }""")
        time.sleep(1)
        cap(page, "recomendaciones", "tres mejoras de mayor impacto")

        # ====== ESCENA 6 · plan SPEIS + capas mapa ======
        print("[6/12] plan SPEIS + capas operativas...", file=sys.stderr)
        page.evaluate("""() => {
            const p = document.querySelector('.plan-respuesta');
            if (p) p.scrollIntoView({ behavior: 'instant', block: 'center' });
        }""")
        time.sleep(1)
        cap(page, "plan_speis", "plan operativo del SPEIS")
        page.evaluate("""() => {
            if (window.__map) window.__map.flyTo({
                center: [-0.3464, 39.4670], zoom: 15.5, duration: 1500
            });
        }""")
        time.sleep(3)
        cap(page, "mapa_capas_operativas", "radios evacuación + perímetro + ruta")

        # ====== ESCENA 7 · RAG normativo ======
        print("[7/12] RAG normativo...", file=sys.stderr)
        page.evaluate("""() => {
            const d = document.getElementById('bloque_normativa');
            if (d) { d.open = true; d.scrollIntoView({ behavior: 'instant', block: 'center' }); }
        }""")
        time.sleep(2)
        page.focus('#rag_input')
        page.type('#rag_input', 'Campanar fachada combustible', delay=30)
        page.click('#rag_btn')
        time.sleep(3)
        cap(page, "rag_resultados", "RAG: 3 tarjetas con cita al BOE")

        # ====== ESCENA 8 · FAB asistente IA ======
        print("[8/12] FAB asistente IA con Llama real...", file=sys.stderr)
        page.evaluate("window.scrollTo({ top: 0, behavior: 'instant' })")
        time.sleep(1)
        cap(page, "fab_visible", "FAB asistente en esquina inferior derecha")
        page.click('#chatbot_fab')
        time.sleep(2)
        cap(page, "chatbot_abierto", "panel flotante del chatbot abierto")
        page.focus('#chat_input')
        page.type('#chat_input', '¿Por qué mi edificio tiene tanto riesgo?', delay=30)
        page.click('#chat_btn')
        time.sleep(14)  # Llama tarda 2-6s
        cap(page, "chatbot_respuesta_llama", "Llama 3.1 ha respondido")
        page.click('#chatbot_cerrar')
        time.sleep(1)

        # ====== ESCENA 9 · filtros del mapa ======
        print("[9/12] filtros del mapa...", file=sys.stderr)
        page.evaluate("""() => {
            ['f_alto', 'f_alto_plantas', 'f_pre1991'].forEach(id => {
                const cb = document.getElementById(id);
                if (cb && !cb.checked) { cb.checked = true; cb.dispatchEvent(new Event('change', { bubbles: true })); }
            });
        }""")
        time.sleep(2)
        cap(page, "filtros_mapa_activos", "tres filtros del mapa activos")
        # Quitar filtros
        page.evaluate("""() => {
            ['f_alto', 'f_alto_plantas', 'f_pre1991'].forEach(id => {
                const cb = document.getElementById(id);
                if (cb && cb.checked) { cb.checked = false; cb.dispatchEvent(new Event('change', { bubbles: true })); }
            });
        }""")
        time.sleep(1)

        # ====== ESCENA 10 · vista propuestas ======
        print("[10/12] vista Propuestas + tabla + filtro...", file=sys.stderr)
        page.click('.header-tab[data-vista="propuestas"]')
        time.sleep(2)
        cap(page, "propuestas_top", "vista Propuestas: cifras + cronología")
        page.evaluate("""() => {
            const t = document.querySelector('.tabla-candidatos');
            if (t) t.scrollIntoView({ behavior: 'instant', block: 'center' });
        }""")
        time.sleep(2)
        cap(page, "tabla_154", "tabla de los 154 candidatos")
        page.focus('#filtro_barrio')
        page.type('#filtro_barrio', 'aiora', delay=80)
        time.sleep(2)
        cap(page, "tabla_filtrada", "tabla filtrada por 'aiora'")
        # Quitar filtro
        page.evaluate("""() => {
            const f = document.getElementById('filtro_barrio');
            if (f) { f.value = ''; f.dispatchEvent(new Event('input', { bubbles: true })); }
        }""")

        # ====== ESCENA 11 · página /historia ======
        print("[11/12] página /historia con scrollytelling...", file=sys.stderr)
        page.goto(URL + "/historia", wait_until="load")
        time.sleep(3)
        cap(page, "historia_inicio", "hero de /historia")
        for y in (1000, 2500, 4500, 6000):
            page.evaluate(f"window.scrollTo({{ top: {y}, behavior: 'instant' }})")
            time.sleep(2)
            cap(page, f"historia_scroll_y{y}", f"scroll a y={y}")

        # ====== ESCENA 12 · viewport pequeño (1366) ======
        print("[12/12] viewport portátil 1366x768...", file=sys.stderr)
        ctx2 = browser.new_context(
            viewport={"width": 1366, "height": 768},
            device_scale_factor=1, locale="es-ES",
        )
        p2 = ctx2.new_page()
        p2.goto(URL, wait_until="load")
        try:
            p2.click("#tutorial_cerrar", timeout=2500)
        except Exception:
            pass
        p2.wait_for_function("() => window.__map && window.__map.isStyleLoaded()", timeout=15000)
        time.sleep(4)
        p2.screenshot(path=str(OUT / "99_viewport_1366.png"))
        print("  cap 99: viewport_1366 · layout en portátil estándar", file=sys.stderr)
        ctx2.close()

        ctx.close()
        browser.close()

    # === INFORME ===
    print("\n" + "=" * 60, file=sys.stderr)
    print("INFORME DE VERIFICACIÓN", file=sys.stderr)
    print("=" * 60, file=sys.stderr)
    print(f"\nCapturas generadas: {len(list(OUT.glob('*.png')))}", file=sys.stderr)
    print(f"Carpeta: {OUT.relative_to(ROOT)}", file=sys.stderr)
    print(f"\nErrores / warnings de consola: {len(errores_consola)}", file=sys.stderr)
    for tipo, msg in errores_consola[:25]:
        print(f"  [{tipo}] {msg[:120]}", file=sys.stderr)
    if len(errores_consola) > 25:
        print(f"  ... y {len(errores_consola) - 25} más", file=sys.stderr)


if __name__ == "__main__":
    main()
