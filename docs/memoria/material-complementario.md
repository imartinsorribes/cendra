---
title: "cendra · material complementario del proyecto"
lang: es
---

# cendra · material complementario

Recursos adicionales del proyecto cendra que **no van adjuntos en este
envío** porque la sede electrónica del Ajuntament de València no
admite todos los formatos necesarios (especialmente `.mp4` y `.csv`).
Todos están publicados como recursos abiertos en el repositorio
público de GitHub y son accesibles sin necesidad de registro.

---

## 1 · Vídeo de demostración

Recorrido cronometrado de tres minutos por las ocho piezas clave del
atlas: contexto del incendio de Campanar, cifras del proyecto,
interfaz de simulación, plan operativo del SPEIS, RAG normativo,
asistente conversacional con IA, página de narrativa visual y
cronología internacional con los 154 candidatos.

- **Descarga directa**:
  <https://github.com/imartinsorribes/cendra/raw/main/docs/video-demo.mp4>
- **Datos**: 3 min 3 s · 1080p · 30 fps · H.264 · 57 MB · narración
  del autor en castellano, audio normalizado a -16 LUFS (EBU R128).
- **Guion del vídeo** (texto completo de la narración):
  <https://github.com/imartinsorribes/cendra/blob/main/docs/guion-voz.md>

---

## 2 · Dataset abierto de los 154 candidatos «perfil Campanar»

Lista priorizada y trazable de los 154 edificios residenciales de
València que cumplen el criterio del perfil temporal y de altura del
edificio que ardió en Campanar (≥ 10 plantas y construidos entre 2000
y 2017, correspondientes a la era del revestimiento de composite con
núcleo combustible).

- **Descarga directa del CSV**:
  <https://github.com/imartinsorribes/cendra/raw/main/data/processed/candidatos_campanar.csv>
- **Visor interactivo del dataset** (con filtro por barrio y
  descarga desde el atlas):
  <https://cendra.pages.dev> → pestaña «Propuestas» → tabla «Plan de
  inspección municipal».
- **Estructura**: 154 filas · 12 columnas (rank, barrio, plantas,
  año de construcción, altura en metros, uso del Catastro, riesgo
  del modelo, tiempo de llegada de bomberos en minutos, parque
  cercano, referencia catastral, longitud y latitud).
- **Licencia**: CC BY 4.0 con atribución al Ajuntament de València y
  al Catastro INSPIRE.

---

## 3 · Atlas web desplegado y accesible públicamente

La herramienta principal del proyecto, abierta a cualquier persona
sin registro:

- **Atlas en vivo**: <https://cendra.pages.dev>
- **Página de narrativa visual** sobre el incendio de Campanar:
  <https://cendra.pages.dev/historia>
- **Despliegue**: Cloudflare Pages con integración continua desde la
  rama `main` del repositorio. Cero coste de infraestructura.

---

## 4 · Código fuente abierto y reproducibilidad

Todo el código que produce los datos y la interfaz está publicado
bajo licencia MIT en GitHub:

- **Repositorio público**: <https://github.com/imartinsorribes/cendra>
- **Memoria técnica completa** (Anexo II en este envío, también
  disponible en GitHub):
  <https://github.com/imartinsorribes/cendra/blob/main/docs/memoria/anexo-ii.md>
- **Cuarenta tests automatizados**: cualquier persona puede clonar el
  repositorio, ejecutar `pytest tests/` y verificar que el modelo
  paramétrico, los cortes normativos, la sincronía Python ↔ JavaScript
  y las funciones auxiliares siguen pasando.
- **Archivo `CITATION.cff`** en la raíz del repositorio: permite a
  GitHub generar la cita bibliográfica correcta para reutilización
  académica.

---

## 5 · Asistente conversacional con IA (verificable en vivo)

El asistente conversacional alojado en Cloudflare Workers AI puede
probarse en directo desde el atlas:

- Entrar a <https://cendra.pages.dev>.
- Pulsar el botón circular morado de la esquina inferior derecha
  («Pregúntale al asistente con IA»).
- Escribir cualquier pregunta sobre el edificio simulado.

El modelo subyacente es **Llama 3.1 8B Instruct** alojado en el plan
gratuito de Cloudflare Workers AI. El prompt del sistema está
publicado en `functions/api/asistente.js` y le prohíbe expresamente
inventar cifras, listar edificios concretos por dirección o predecir
incendios. Si la pregunta cae fuera del contexto disponible, el
asistente debe responder «no tengo datos sobre eso».

---

## Apertura y reutilización

Todo el material listado en este documento se publica bajo:

- **Código**: licencia MIT.
- **Datos derivados (CSV, vídeo, memoria)**: licencia CC BY 4.0.

Esto permite que cualquier persona técnica del Ajuntament, de otros
ayuntamientos o de la comunidad académica reutilice el modelo, el
dataset o la interfaz citando la autoría.
