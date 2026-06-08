"""
Graba el vídeo demo de cendra siguiendo el guión extendido (docs/guion-video.md).

Duración objetivo: ~3:30 min. Cubre 8 capítulos:
  - Cifras del proyecto.
  - El mapa coroplético con su leyenda agrandada.
  - Click en un edificio del Catastro + simulación paramétrica.
  - Manipulación de sliders (plantas, año, fachada) con caída del riesgo.
  - Bloque «Por qué este riesgo» y «Cómo bajaría más».
  - Plan operativo del SPEIS (radios, ruta, hidrantes).
  - RAG normativo con sugerencias y resultados con cita al BOE.
  - Asistente conversacional REAL con Llama 3.1 8B en Workers AI
    (FAB esquina inferior derecha + panel flotante).
  - Tabla de los 154 candidatos Campanar con filtro y descarga CSV.
  - Página /historia con scrollytelling.
  - Cierre con la URL.

Por defecto graba CONTRA PRODUCCIÓN (cendra.pages.dev) para que el
asistente con IA conteste de verdad con Llama. Para grabar contra
el servidor local (útil cuando hay cambios sin desplegar todavía):

    python scripts/grabar_demo.py --local

Para acelerar las primeras pruebas (sin grabar) durante desarrollo:

    python scripts/grabar_demo.py --dry-run
"""
from __future__ import annotations

import argparse
import glob
import http.server
import os
import shutil
import socketserver
import subprocess
import sys
import threading
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
WEB = ROOT / "web"
DOCS = ROOT / "docs"
DOCS.mkdir(exist_ok=True)

PUERTO = 8767
URL_LOCAL = f"http://localhost:{PUERTO}"
URL_PROD = "https://cendra.pages.dev"


class _Server(socketserver.TCPServer):
    allow_reuse_address = True


def _arrancar_servidor():
    class _Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *a, **kw):
            super().__init__(*a, directory=str(WEB), **kw)

        def log_message(self, *a, **kw):
            pass

    srv = _Server(("", PUERTO), _Handler)
    th = threading.Thread(target=srv.serve_forever, daemon=True)
    th.start()
    return srv


def _msg(t):
    print(f"[grabar] {t}", file=sys.stderr, flush=True)


def _localizar_ffmpeg() -> str | None:
    """Busca un ffmpeg con soporte de H.264. El ffmpeg que viene con
    Playwright solo trae VP8, así que preferimos el de imageio-ffmpeg
    (build completo) o el del sistema."""
    try:
        import imageio_ffmpeg
        p = imageio_ffmpeg.get_ffmpeg_exe()
        if p and Path(p).exists():
            return p
    except Exception:
        pass
    sysff = shutil.which("ffmpeg")
    if sysff:
        return sysff
    # Último recurso: el ffmpeg recortado de Playwright (solo VP8).
    candidatos = [
        Path(p) for p in glob.glob(
            str(Path.home() / "AppData/Local/ms-playwright/ffmpeg*/ffmpeg-win64.exe")
        )
    ]
    for c in candidatos:
        if c.exists():
            return str(c)
    return None


def _convertir_a_mp4(webm: Path, mp4: Path) -> bool:
    """Re-encoda el WebM (VP8 25fps ~890kbps) a MP4 H.264 30fps 4000kbps.
    H.264 da mejor compresión a la misma calidad y es universalmente
    compatible con editores de vídeo (Canva, DaVinci, Premiere)."""
    ffmpeg = _localizar_ffmpeg()
    if not ffmpeg:
        _msg("ffmpeg no encontrado, salto la conversión a MP4")
        return False
    if mp4.exists():
        mp4.unlink()
    cmd = [
        ffmpeg, "-y", "-loglevel", "warning",
        "-i", str(webm),
        # Re-encode con H.264 a 30 fps. No usamos minterpolate (muy
        # lento, ~5 min para un vídeo de 4 min); el filtro fps simple
        # con duplicación frame-to-frame es suficiente.
        "-vf", "fps=30",
        "-c:v", "libx264",
        "-preset", "fast",           # equilibrio velocidad/calidad
        "-crf", "20",                # 18-23 = visualmente sin pérdida
        "-pix_fmt", "yuv420p",       # máxima compatibilidad
        "-movflags", "+faststart",   # primer frame visible al instante
        "-an",                       # sin audio
        str(mp4),
    ]
    _msg(f"convirtiendo a MP4 30 fps con ffmpeg (1-2 min)...")
    try:
        subprocess.run(cmd, check=True, capture_output=True, timeout=600)
    except subprocess.CalledProcessError as e:
        _msg(f"ffmpeg falló: {e.stderr.decode()[:500]}")
        return False
    except subprocess.TimeoutExpired:
        _msg("ffmpeg timeout")
        return False
    kb = mp4.stat().st_size / 1024
    try:
        rel = mp4.relative_to(ROOT)
    except ValueError:
        rel = mp4
    _msg(f"OK -> {rel} ({kb:.0f} KB)")
    return True


# Script JS que monkey-patchea fetch para mockear /api/asistente
# (en local no hay binding AI). Devuelve respuesta convincente
# basada en el contexto que pasa el frontend.
MOCK_ASISTENTE = """
() => {
  const fetchOrig = window.fetch;
  window.fetch = async function(url, opts) {
    if (typeof url === 'string' && url.includes('/api/asistente')) {
      const body = JSON.parse(opts?.body || '{}');
      const c = body.contexto || {};
      const r = c.riesgo_total ?? '?';
      const reg = c.regimen === 'fachada-critica'
        ? 'régimen de fachada crítica'
        : 'régimen normal';
      // Mensaje plausible que el modelo daría con el contexto
      const respuesta =
        `Tu edificio simulado tiene riesgo ${r} sobre 100 en ${reg}. ` +
        `La pieza que más pesa es la fachada (${c.fachada}); ` +
        `si la cambiaras a una no combustible, el riesgo bajaría notablemente. ` +
        `Prueba a mover el slider y verás el efecto en directo.`;
      await new Promise(r => setTimeout(r, 1200));  // simular latencia red
      return new Response(JSON.stringify({
        respuesta,
        modelo: '@cf/meta/llama-3.1-8b-instruct (mock local)',
      }), { status: 200, headers: { 'Content-Type': 'application/json' } });
    }
    return fetchOrig.call(this, url, opts);
  };
}
"""


def grabar(dry_run: bool = False, local: bool = False):
    if local:
        _msg("arrancando servidor local...")
        srv = _arrancar_servidor()
        time.sleep(0.5)
        url_base = URL_LOCAL
    else:
        _msg("apuntando a producción cendra.pages.dev")
        srv = None
        url_base = URL_PROD

    out_dir = DOCS / "_video_temp"
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir()

    try:
        with sync_playwright() as p:
            _msg("lanzando Chromium 1920x1080...")
            browser = p.chromium.launch(headless=True)
            context_args = dict(
                viewport={"width": 1920, "height": 1080},
                device_scale_factor=1,
                locale="es-ES",
            )
            if not dry_run:
                context_args["record_video_dir"] = str(out_dir)
                context_args["record_video_size"] = {"width": 1920, "height": 1080}
            context = browser.new_context(**context_args)
            page = context.new_page()

            # Solo mockear el asistente cuando se graba contra local
            # (en producción Llama 3.1 responde de verdad).
            if local:
                page.add_init_script(MOCK_ASISTENTE)

            # ====================================================
            # Capítulo 1 (0:00 - 0:20) · Hook y carga del atlas
            # ====================================================
            _msg("cap. 1: hook + carga inicial...")
            page.goto(url_base + "/index.html", wait_until="load")
            # Cerrar tutorial
            try:
                page.click("#tutorial_cerrar", timeout=2500)
            except Exception:
                pass
            # Esperar al mapa: dejar tiempo generoso porque el basemap
            # CDN puede tardar 3-5 s en cargar
            page.wait_for_function(
                "() => window.__map && window.__map.isStyleLoaded()",
                timeout=15000,
            )
            page.wait_for_function(
                "() => window.__map && window.__map.getLayer('edificios-poligonos-fill')",
                timeout=15000,
            )
            time.sleep(3)  # respiración para que se vea el mapa cargado
            # Pasar el cursor sobre la leyenda
            page.evaluate("""() => {
                const leg = document.getElementById('leyenda');
                if (leg) leg.style.boxShadow = '0 0 0 3px rgba(176, 58, 29, 0.4)';
            }""")
            time.sleep(4)
            page.evaluate("""() => {
                const leg = document.getElementById('leyenda');
                if (leg) leg.style.boxShadow = '';
            }""")
            time.sleep(3)

            # ====================================================
            # Capítulo 2 (0:20 - 0:45) · Las cifras (Propuestas)
            # ====================================================
            _msg("cap. 2: cifras en Propuestas...")
            page.click('.header-tab[data-vista="propuestas"]')
            time.sleep(2.5)
            # Scroll a las cifras
            page.evaluate("""() => {
                const c = document.querySelector('.cifras-clave');
                if (c) c.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }""")
            time.sleep(8)
            # Scroll a la cronología histórica
            page.evaluate("""() => {
                const c = document.querySelector('.cronologia');
                if (c) c.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }""")
            time.sleep(10)

            # ====================================================
            # Capítulo 3 (0:45 - 1:25) · Tu edificio · click + sliders
            # ====================================================
            _msg("cap. 3: click polígono + manipulación sliders...")
            page.click('.header-tab[data-vista="analisis"]')
            time.sleep(2)
            # Volar a una zona con polígonos. Duración alta (3,5 s) para
            # que el flyTo sea suave a 25 fps en la grabación de WebM.
            page.evaluate("""() => {
                if (window.__map) window.__map.flyTo({
                    center: [-0.3464, 39.4670], zoom: 17, duration: 3500
                });
            }""")
            time.sleep(6)
            # Click programático en un polígono visible. El popup
            # minimalista nuevo aparece a la derecha del polígono con
            # los 4 datos identificativos (bomberos, año, uso, ref) y
            # el polígono queda resaltado con borde azul.
            page.evaluate("""() => {
                const m = window.__map; if (!m) return;
                const dl = m._delegatedListeners.click;
                const h = dl.find(d => d.layers && d.layers.includes('edificios-poligonos-fill'))?.listener;
                const feats = m.queryRenderedFeatures({ layers: ['edificios-poligonos-fill'] });
                if (!feats.length || !h) return;
                const f = feats[0];
                const c = f.geometry.coordinates[0][0];
                const px = m.project(c);
                h({ lngLat: { lng: c[0], lat: c[1] }, point: px, features: [f] });
            }""")
            time.sleep(8)  # respiramos para que se vea bien el popup nuevo
            # Cerrar popup para ver mejor el panel
            page.evaluate("""() => {
                document.querySelectorAll('.maplibregl-popup').forEach(p => p.remove());
            }""")
            time.sleep(1)
            # Hacer scroll al panel derecho para que se vea el explicador
            page.evaluate("""() => {
                const el = document.querySelector('.explica-riesgo');
                if (el) el.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }""")
            time.sleep(6)
            # Resaltar el número grande del riesgo y la cifra V para que
            # se vea bien que CAMBIA cuando manipulemos los sliders
            page.evaluate("""() => {
                const num = document.getElementById('riesgo_total');
                if (num) {
                    num.style.transition = 'transform 0.4s, color 0.4s';
                    num.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }
                // Resaltar el panel de resultado con un borde brasa sutil
                const panel = document.querySelector('.resultado-panel');
                if (panel) panel.style.boxShadow = '0 0 0 3px rgba(176, 58, 29, 0.25)';
            }""")
            time.sleep(2)
            # Cambiar slider Fachada para mostrar caída de riesgo
            page.evaluate("""() => {
                const f = document.getElementById('fachada');
                if (f) {
                    f.style.outline = '3px solid #b03a1d';
                    f.style.outlineOffset = '3px';
                    f.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }
            }""")
            time.sleep(2.5)
            page.select_option("#fachada", "ladrillo")
            time.sleep(4.5)
            # Cambiar SCI (el outline brasa lo movemos al SCI)
            page.evaluate("""() => {
                const f = document.getElementById('fachada');
                if (f) { f.style.outline = ''; f.style.outlineOffset = ''; }
                const s = document.getElementById('sci');
                if (s) {
                    s.style.outline = '3px solid #b03a1d';
                    s.style.outlineOffset = '3px';
                    s.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }
            }""")
            time.sleep(2)
            page.select_option("#sci", "completo")
            time.sleep(4.5)
            # Quitar outline del SCI antes de seguir
            page.evaluate("""() => {
                const s = document.getElementById('sci');
                if (s) { s.style.outline = ''; s.style.outlineOffset = ''; }
            }""")
            # Cambiar la hora para mostrar que también se modula por hora
            page.evaluate("""() => {
                const h = document.getElementById('hora');
                if (!h) return;
                h.scrollIntoView({ behavior: 'smooth', block: 'center' });
                h.value = 3;
                h.dispatchEvent(new Event('input', { bubbles: true }));
            }""")
            time.sleep(4)

            # ====================================================
            # Capítulo 4 (1:25 - 1:55) · Plan SPEIS + recomendaciones
            # ====================================================
            _msg("cap. 4: plan operativo SPEIS...")
            # Restaurar fachada a combustible para ver plan FC
            page.select_option("#fachada", "composite-acmpe")
            time.sleep(3)
            # Scroll al bloque de recomendaciones
            page.evaluate("""() => {
                const el = document.querySelector('.recomendaciones');
                if (el) el.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }""")
            time.sleep(7)
            # Scroll al plan de respuesta
            page.evaluate("""() => {
                const el = document.querySelector('.plan-respuesta');
                if (el) el.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }""")
            time.sleep(8)
            # Activar toggle del despliegue en mapa para mostrar radios
            page.evaluate("""() => {
                const t = document.getElementById('f_plan_mapa');
                if (t && !t.checked) { t.checked = true; t.dispatchEvent(new Event('change', { bubbles: true })); }
            }""")
            time.sleep(2)
            # Volar a ver los círculos (duración alta para suavidad)
            page.evaluate("""() => {
                if (window.__map) window.__map.flyTo({
                    center: [-0.3464, 39.4670], zoom: 15.5, duration: 3000
                });
            }""")
            time.sleep(6)

            # ====================================================
            # Capítulo 5 (1:55 - 2:25) · RAG normativo
            # ====================================================
            _msg("cap. 5: RAG normativo...")
            # Abrir bloque y scrollear
            page.evaluate("""() => {
                const det = document.getElementById('bloque_normativa');
                if (det) { det.open = true; det.scrollIntoView({ behavior: 'smooth', block: 'center' }); }
            }""")
            time.sleep(4)
            # Mostrar primero una sugerencia haciendo hover
            time.sleep(3)
            # Escribir en el buscador
            page.evaluate("""() => {
                const inp = document.getElementById('rag_input');
                if (inp) inp.value = '';
            }""")
            page.focus('#rag_input')
            page.type('#rag_input', '¿Qué pasó en Campanar y por qué afecta a mi edificio?', delay=35)
            time.sleep(1)
            page.click('#rag_btn')
            time.sleep(7)
            # Scroll para ver los resultados
            page.evaluate("""() => {
                const r = document.querySelector('.rag-resultados');
                if (r) r.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }""")
            time.sleep(7)

            # ====================================================
            # Capítulo 6 (2:25 - 3:05) · Asistente IA (widget flotante)
            # ====================================================
            _msg("cap. 6: asistente con IA flotante...")
            # Volver al inicio del scroll para que se vea el mapa con
            # el FAB del chatbot en la esquina inferior derecha
            page.evaluate("window.scrollTo({ top: 0, behavior: 'smooth' });")
            time.sleep(2.5)
            # Click sobre el FAB del chatbot para abrir el panel flotante
            page.click('#chatbot_fab')
            time.sleep(3)
            # Escribir pregunta y enviar (Llama 3.1 responde en producción)
            page.focus('#chat_input')
            page.type('#chat_input', '¿Por qué mi edificio tiene tanto riesgo y qué bajaría más la cifra?', delay=45)
            time.sleep(1.5)
            page.click('#chat_btn')
            # En producción Llama tarda 2-6 s; en local con mock 1-2 s.
            # Damos margen generoso para ambos.
            time.sleep(14)
            page.evaluate("""() => {
                const t = document.getElementById('chat_turnos');
                if (t) t.scrollTop = t.scrollHeight;
            }""")
            time.sleep(4)
            # Cerrar el panel flotante para mostrar el resto del atlas
            page.click('#chatbot_cerrar')
            time.sleep(2)

            # ====================================================
            # Capítulo 7 (2:50 - 3:15) · 154 candidatos + CSV
            # ====================================================
            _msg("cap. 7: 154 candidatos + CSV...")
            page.click('.header-tab[data-vista="propuestas"]')
            time.sleep(2)
            page.evaluate("""() => {
                const t = document.querySelector('.tabla-candidatos');
                if (t) t.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }""")
            time.sleep(5)
            # Filtrar por «aiora»
            page.focus('#filtro_barrio')
            page.type('#filtro_barrio', 'aiora', delay=80)
            time.sleep(4)
            # Borrar filtro
            page.evaluate("""() => {
                const f = document.getElementById('filtro_barrio');
                if (f) { f.value = ''; f.dispatchEvent(new Event('input', { bubbles: true })); }
            }""")
            time.sleep(2)
            # Resaltar botón CSV
            page.evaluate("""() => {
                const b = document.getElementById('descargar_csv');
                if (!b) return;
                b.style.outline = '3px solid #b03a1d';
                b.style.outlineOffset = '4px';
                b.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }""")
            time.sleep(6)

            # ====================================================
            # Capítulo 8 (3:15 - 3:35) · /historia + cierre
            # ====================================================
            _msg("cap. 8: /historia + cierre...")
            page.goto(url_base + "/historia.html", wait_until="load")
            time.sleep(4)
            # Scrollear despacio por la historia
            for y in (400, 1200, 2400, 3600, 4800, 6000):
                page.evaluate(f"window.scrollTo({{ top: {y}, behavior: 'smooth' }});")
                time.sleep(2.4)
            # Volver al inicio
            page.evaluate("window.scrollTo({ top: 0, behavior: 'smooth' });")
            time.sleep(3)

            _msg("cerrando contexto para guardar el WebM...")
            page.close()
            context.close()
            browser.close()

        if dry_run:
            _msg("dry-run completado, sin grabar.")
            return
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

        # Post-proceso: convertir el WebM a MP4 H.264 30 fps con
        # interpolación. El resultado se ve más suave y es compatible
        # con cualquier editor de vídeo (Canva no traga WebM bien).
        mp4 = DOCS / "video-demo.mp4"
        _convertir_a_mp4(dst, mp4)

    finally:
        if srv is not None:
            srv.shutdown()
        if out_dir.exists():
            shutil.rmtree(out_dir, ignore_errors=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true",
                        help="Ejecuta sin grabar (para iterar el guión).")
    parser.add_argument("--local", action="store_true",
                        help="Grabar contra localhost en lugar de cendra.pages.dev.")
    args = parser.parse_args()
    grabar(dry_run=args.dry_run, local=args.local)
