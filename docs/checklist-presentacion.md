# Checklist final — convocatoria AD.TR.15

Plazo oficial de presentación: **08/05/2026 a 08/06/2026** (ambos
inclusive). Procedimiento `AD.TR.15` en sede electrónica del
Ajuntament de València. Doble categoría (datos abiertos y
periodismo de datos), tres premios en cada una: 5.000 € · 3.000 €
· 2.000 €.

Fuente oficial: <https://sede.valencia.es/sede/registro/procedimiento/AD.TR.15?lang=1>

## Tramitación en sede.valencia.es (lo crítico)

### 1. Verificar identificación (HACER YA si no se ha hecho)

- [ ] Entrar a <https://sede.valencia.es> e identificarse con
  Cl@ve PIN, Cl@ve Permanente, Cl@ve Móvil o certificado digital
  FNMT. Si Cl@ve no funciona, sacar FNMT con cita presencial
  (2-7 días hábiles, hacerlo ya).
- [ ] Una vez dentro, buscar el procedimiento `AD.TR.15` o
  «Premios datos abiertos» y confirmar que se llega al formulario
  (sin presentar nada todavía).

### 2. Descargar y rellenar los anexos oficiales

Los tres PDFs oficiales (verificados, todos devuelven 200):

| Documento | Enlace | Qué hay que hacer |
|---|---|---|
| **Formulario de solicitud** | <https://sede.valencia.es/sede/descarga/doc/DOCUMENT_1_20230005314292> | Rellenar datos personales, categoría («datos abiertos»), título del proyecto («cendra: atlas paramétrico de riesgo de incendio en València»), datos de contacto. Firmar. |
| **Declaración responsable** (el Anexo I) | <https://sede.valencia.es/sede/descarga/doc/DOCUMENT_1_20240007668181> | Marcar que no se ha recibido subvención previa del Ayuntamiento por el mismo objeto, que no se está incurso en causas de prohibición, etc. Firmar. |
| **Bases reguladoras** (leer) | <https://sede.valencia.es/sede/descarga/doc/DOCUMENT_1_20260010001722> | Leer una vez para no llevarse sorpresas (sobre todo el apartado de documentación obligatoria según tipo de solicitante). |

### 3. Documentación del proyecto (ya generada por cendra)

| Documento | Dónde está |
|---|---|
| Memoria resumen (el Anexo II) | `docs/memoria/anexo-ii.pdf` (286 KB) |
| URL del proyecto desplegado | <https://cendra.pages.dev> |
| Dataset abierto adjunto | `data/processed/candidatos_campanar.csv` (17 KB) |
| Código fuente | GitHub release v0.3.0 (cuando sea público) |

### 4. Subir todo a sede.valencia.es

- [ ] Entrar al procedimiento AD.TR.15 con Cl@ve.
- [ ] Rellenar el formulario telemático.
- [ ] Subir el PDF del formulario de solicitud firmado.
- [ ] Subir el PDF de la declaración responsable firmada.
- [ ] Subir el PDF de la memoria (`docs/memoria/anexo-ii.pdf`).
- [ ] Indicar la URL del proyecto: `https://cendra.pages.dev`.
- [ ] Adjuntar (opcional pero recomendado) el CSV del dataset.
- [ ] Firmar y registrar la solicitud. Guardar el justificante.

## GitHub (lo opcional pero suma puntos en el eje 4 «apertura»)

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
