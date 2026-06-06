# Checklist del día de la presentación (5 jun 2026)

Última fecha de revisión: 6 jun 2026.

## Antes de la presentación

- [ ] **Hacer el repositorio público** en GitHub
  - <https://github.com/imartinsorribes/cendra/settings>
  - Sección «Danger Zone» → «Change repository visibility» → Public
  - Confirma que los enlaces del README y de la vista «Propuestas»
    (`https://github.com/imartinsorribes/cendra`) responden 200.

- [ ] **Crear el release v0.3.0 con el dataset adjunto**
  - <https://github.com/imartinsorribes/cendra/releases/new>
  - Tag: `v0.3.0` (ya empujado al remoto, debería aparecer en el desplegable).
  - Title: `v0.3.0 · Atlas + dataset abierto de candidatos Campanar`
  - Description: copia del bloque «Notas del release» que está al
    final de este checklist.
  - Adjuntar `data/processed/candidatos_campanar.csv` arrastrándolo a
    la zona «Attach binaries by dropping them here».
  - Adjuntar también `docs/memoria/anexo-ii.pdf` para que el jurado
    pueda descargar la memoria sin clonar el repo.
  - Marcar como «Latest release» y publicar.

- [ ] **Verificar el deploy** en `https://cendra.pages.dev`
  - El último commit del `main` debe estar reflejado (Cloudflare Pages
    suele tardar ~1-2 min después del push).
  - Probar en una pestaña de incógnito para evitar caché del navegador.

- [ ] **Probar en móvil con datos** (no Wi-Fi del Ajuntament)
  - Tiempo de carga aceptable (< 5 s para ver el primer riesgo).
  - El mapa carga sin clavarse.
  - El cambio entre vistas Análisis ↔ Propuestas es fluido.

- [ ] **Comprobar los tests** localmente: `python -m pytest tests/ -q`
  (deben pasar los 40 en menos de 2 s).

- [ ] **Repasar la memoria** del Anexo II
  (`docs/memoria/anexo-ii.md`): que las cifras (36.300 edificios únicos,
  154 candidatos Campanar, 1.923 hidrantes, 6 parques, 40 tests) sean
  consistentes con lo que dice la web.

## Material para llevar

- [ ] La URL `cendra.pages.dev` impresa o en una nota visible.
- [ ] Un dispositivo de respaldo (móvil o tablet) por si la presentación
  principal falla.
- [ ] El CSV de los 154 candidatos descargado offline
  (`web/data/candidatos_campanar_completo.json` o exportarlo desde la
  vista Propuestas) por si quieren los datos sin acceso a internet.

## Demo en vivo (si la hay): camino sugerido

1. Abrir `cendra.pages.dev`. Cerrar el tutorial de bienvenida.
2. Mostrar el mapa coroplético por barrios (Aiora, Calvari, Sant Antoni
   en rojo brasa).
3. Hacer zoom hasta zoom 16 sobre Campanar / Aiora: aparecen los
   polígonos del Catastro con los bordes dorados de los candidatos.
4. Click en un polígono dorado: rellena los sliders con los valores
   reales del edificio. Mostrar el bloque «Por qué este riesgo» y la
   línea «Cómo se propagaría».
5. Cambiar el slider «Fachada» de combustible a no combustible: el
   riesgo cae del rango 60-70 al rango 35-45. Aquí es donde se ve el
   valor del modelo paramétrico.
6. Pulsar «Resetear simulación» → vuelve al centro de València.
7. Cambiar a vista «Propuestas».
8. Mostrar la cronología (Lacrosse, Address, Grenfell, Mocejón,
   Campanar) y la tabla de los 154 candidatos. Filtrar por barrio
   (`marxal`, `aiora`) y descargar el CSV.

## Después de la presentación

- [ ] Si gana, agradecer y subir un commit con la nota.
- [ ] Mantener el repo público y la web online: el atlas tiene valor
  más allá del concurso.

---

## Notas del release v0.3.0 (copiar al crear el release en GitHub)

```markdown
# cendra v0.3.0 · Atlas + dataset abierto de candidatos Campanar

Atlas paramétrico de riesgo de incendio para los edificios residenciales de
València, construido íntegramente con datos abiertos del Ajuntament y del
Catastro INSPIRE. Web interactiva en https://cendra.pages.dev.

## Qué incluye este release

- **`candidatos_campanar.csv`** — los 154 edificios de València que cumplen
  el perfil Campanar (≥10 plantas, construidos entre 2000 y 2017, era del
  composite con núcleo combustible). Incluye coordenadas, referencia
  catastral, plantas, año, riesgo del modelo y tiempo estimado de llegada
  de bomberos. CSV abierto, descargable y reutilizable.
- **`anexo-ii.pdf`** — memoria del Anexo II del concurso con la
  metodología, el modelo paramétrico, las fuentes de datos y la
  validación.

## Características de esta versión

- 36.300 edificios únicos analizados (de 214.000 buildingParts del
  Catastro INSPIRE).
- 2.000 polígonos del Catastro renderizados en el mapa, con click para
  simulación inmediata.
- Modelo paramétrico de riesgo en tres dimensiones (V/E/R) con régimen
  «fachada crítica» derivado de Grenfell y Campanar.
- Plan de respuesta operativa del SPEIS por edificio (efectivos, caudal,
  perímetro, rutas reales por calles vía OSRM).
- Vista «Propuestas» con cronología histórica, tabla descargable de los
  154 candidatos y plan de acción municipal.
- 40 tests automatizados (`pytest tests/`).
- Hosting estático en Cloudflare Pages.

## Reproducción

Cualquier persona puede regenerar todos los datos desde cero siguiendo
las instrucciones del [README](https://github.com/imartinsorribes/cendra#pipeline-reproducible).

## Licencia

Código bajo MIT. Datos derivados bajo CC BY 4.0 (atribución requerida al
Ajuntament de València y al Catastro INSPIRE).
```
