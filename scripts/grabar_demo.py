"""
Graba un vídeo demo de cendra siguiendo el guión de docs/guion-video.md.

El script:
  1. Arranca un servidor HTTP local en :8765 sirviendo web/.
  2. Abre Chromium en 1920x1080 con grabación de vídeo activada.
  3. Reproduce las 7 escenas del guión con tiempos exactos.
  4. Cierra todo y normaliza el WebM resultante a docs/video-demo.webm.

Los tiempos de cada escena coinciden con la duración pensada para la
narración en off (60 segundos totales). La persona usuaria comenta
encima del vídeo (con OBS, Loom o el editor que prefiera) usando el
guión de docs/guion-video.md como letra.

Uso:
    python scripts/grabar_demo.py
"""
from __future__ import annotations

import http.server
import shutil
import socketserver
import sys
import threading
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
WEB = ROOT / "web"
DOCS = ROOT / "docs"
DOCS.mkdir(exist_ok=True)

PUERTO = 8766
URL = f"http://localhost:{PUERTO}"


class _Server(socketserver.TCPServer):
    allow_reuse_address = True


def _arrancar_servidor():
    handler = http.server.SimpleHTTPRequestHandler

    class _Handler(handler):
        def __init__(self, *a, **kw):
            super().__init__(*a, directory=str(WEB), **kw)

        def log_message(self, *a, **kw):
            pass  # silenciar logs

    srv = _Server(("", PUERTO), _Handler)
    th = threading.Thread(target=srv.serve_forever, daemon=True)
    th.start()
    return srv


def _msg(t):
    print(f"[grabar] {t}", file=sys.stderr, flush=True)


def grabar():
    _msg("arrancando servidor local...")
    srv = _arrancar_servidor()
    time.sleep(0.5)

    # Carpeta temporal para el vídeo WebM (Playwright graba en WebM)
    out_dir = DOCS / "_video_temp"
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir()

    try:
        with sync_playwright() as p:
            _msg("lanzando Chromium...")
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                viewport={"width": 1920, "height": 1080},
                device_scale_factor=1,
                record_video_dir=str(out_dir),
                record_video_size={"width": 1920, "height": 1080},
                locale="es-ES",
            )
            page = context.new_page()

            # === Escena 1 (0-8 s) · Hook · home de cendra ====================
            _msg("escena 1: home...")
            page.goto(URL + "/index.html", wait_until="networkidle")
            # Cerrar el tutorial si aparece
            try:
                page.click("#tutorial_cerrar", timeout=2500)
            except Exception:
                pass
            page.wait_for_selector("#mapa", state="visible")
            time.sleep(2)  # esperar a que el mapa cargue del CDN
            time.sleep(6)  # 8 s totales

            # === Escena 2 (8-16 s) · zoom a Campanar / Aiora =================
            _msg("escena 2: zoom Aiora...")
            page.evaluate("""() => {
                if (window.__map) window.__map.flyTo({
                    center: [-0.3464, 39.4670],
                    zoom: 15.5, duration: 2000
                });
            }""")
            time.sleep(8)

            # === Escena 3 (16-26 s) · cambio a vista Propuestas ==============
            _msg("escena 3: vista Propuestas...")
            page.click('.header-tab[data-vista="propuestas"]')
            time.sleep(1.2)
            # Hacer scroll suave a la cifra de 154
            page.evaluate("""() => {
                const cifras = document.querySelector('.cifras-clave');
                if (cifras) cifras.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }""")
            time.sleep(9)

            # === Escena 4 (26-38 s) · click en candidato + explicador ========
            _msg("escena 4: click polígono + explicador...")
            page.click('.header-tab[data-vista="analisis"]')
            time.sleep(0.8)
            # Volar a un polígono concreto y simular click sobre él
            page.evaluate("""() => {
                if (!window.__map) return;
                window.__map.jumpTo({ center: [-0.3464, 39.4670], zoom: 17.5 });
            }""")
            time.sleep(3)  # esperar a que se carguen tiles + polígonos
            # Click programático en el primer polígono visible
            page.evaluate("""() => {
                const m = window.__map; if (!m) return;
                const feats = m.queryRenderedFeatures({ layers: ['edificios-poligonos-fill'] });
                if (!feats.length) return;
                const f = feats[0];
                const c = f.geometry.coordinates[0][0];
                const px = m.project(c);
                m.fire('click', { lngLat: { lng: c[0], lat: c[1] }, point: px, features: [f] });
            }""")
            time.sleep(9)

            # === Escena 5 (38-48 s) · cambiar fachada y ver caída ============
            _msg("escena 5: simulación fachada...")
            # Mostrar primero el slider de fachada
            page.evaluate("""() => {
                const sel = document.getElementById('fachada');
                if (sel) sel.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }""")
            time.sleep(2)
            # Cerrar popup si abrió
            page.evaluate("""() => {
                document.querySelectorAll('.maplibregl-popup').forEach(p => p.remove());
            }""")
            # Cambiar fachada de combustible a no combustible (ladrillo)
            page.select_option("#fachada", "ladrillo")
            time.sleep(8)

            # === Escena 6 (48-55 s) · tabla candidatos en Propuestas =========
            _msg("escena 6: tabla 154 + CSV...")
            page.click('.header-tab[data-vista="propuestas"]')
            time.sleep(0.8)
            # Hacer scroll a la tabla
            page.evaluate("""() => {
                const tbl = document.querySelector('.tabla-candidatos');
                if (tbl) tbl.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }""")
            time.sleep(3)
            # Resaltar el botón de descarga
            page.evaluate("""() => {
                const btn = document.getElementById('descargar_csv');
                if (!btn) return;
                btn.style.outline = '3px solid #b03a1d';
                btn.style.outlineOffset = '4px';
                btn.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }""")
            time.sleep(4)

            # === Escena 7 (55-60 s) · cierre con título + URL ================
            _msg("escena 7: cierre...")
            page.evaluate("""() => {
                window.scrollTo({ top: 0, behavior: 'smooth' });
            }""")
            time.sleep(5)

            _msg("cerrando contexto Playwright para guardar el WebM...")
            page.close()
            context.close()
            browser.close()

        # Mover el WebM resultante a docs/video-demo.webm
        webms = list(out_dir.glob("*.webm"))
        if not webms:
            _msg("ERROR: Playwright no generó ningún WebM")
            return
        dst = DOCS / "video-demo.webm"
        if dst.exists():
            dst.unlink()
        webms[0].rename(dst)
        kb = dst.stat().st_size / 1024
        _msg(f"OK -> {dst.relative_to(ROOT)} ({kb:.0f} KB)")

    finally:
        srv.shutdown()
        if out_dir.exists():
            shutil.rmtree(out_dir, ignore_errors=True)


if __name__ == "__main__":
    grabar()
