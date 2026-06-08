# Guión del vídeo de presentación · 3 min 30 s

> **Vídeo base ya grabado**:
> - `docs/video-demo.mp4` (40 MB · 3:30 · 1920×1080 · **30 fps** · H.264 CRF 20) ← úsalo aquí
> - `docs/video-demo.webm` (24 MB · misma duración · VP8 25 fps) ← original sin post-proceso
>
> Generado automáticamente por `scripts/grabar_demo.py` contra el
> atlas en producción (`cendra.pages.dev`). El asistente
> conversacional con Llama 3.1 8B responde **de verdad** en este
> vídeo: no es un mock. Los `flyTo` del mapa van a duración 3-3,5 s
> para que se vean fluidos en grabación; el WebM se reencoda
> después a MP4 H.264 30 fps con `ffmpeg` (vía `imageio-ffmpeg`).
>
> El MP4 es el archivo que conviene usar en cualquier editor
> (Canva, DaVinci, Premiere); el WebM queda como original
> regenerable.
>
> **Cómo añadirle voz** (por orden de sencillez):
> 1. **Canva** (en línea): «Crear un diseño» → «Vídeo» → subir el
>    WebM, añadir pista de audio nueva con tu micro, grabar leyendo
>    el guión, exportar como MP4. Tiene plantilla para meterte tú
>    en círculo en la esquina si quieres salir también en cámara.
> 2. **DaVinci Resolve** (gratis, escritorio): importa el WebM,
>    pista de audio nueva, graba en directo o pega un MP3
>    pregrabado, exporta H.264 1080p.
> 3. **OBS** o **Loom**: pones el WebM en pantalla completa y
>    grabas con tu micro en tiempo real comentando.
>
> **Si retoques algo del atlas y quieras regenerar el vídeo**:
>
> ```bash
> python scripts/grabar_demo.py            # contra producción (recomendado)
> python scripts/grabar_demo.py --local    # contra localhost
> ```
>
> Total: ~620 palabras a ritmo natural (≈ 2,7 palabras/segundo).
> Si vas justo de tiempo, recorta las frases entre paréntesis.

---

## CAPÍTULO 1 · 0:00 → 0:18 · Hook

**En pantalla**: home de cendra con el mapa de barrios de València
coloreado por riesgo (verde a brasa). La leyenda inferior izquierda
queda resaltada un instante para que se vea bien la escala.

**Lo que dices**:
> «En febrero de 2024 ardió un edificio de catorce plantas en el
> barrio de Campanar de València. Diez personas murieron. La
> fachada de composite con núcleo combustible cubrió todo el
> bloque en menos de media hora. Esto es cendra: un atlas
> paramétrico que intenta entender qué pasó y cuántos edificios
> más en la ciudad podrían estar en una situación parecida.»

---

## CAPÍTULO 2 · 0:18 → 0:48 · Las cifras

**En pantalla**: cambio a la pestaña «Propuestas». Aparecen las seis
cifras clave (36.300 edificios, 154 candidatos, 10 capas, 6 parques,
1.923 hidrantes, 40 tests). Después scroll a la cronología histórica
internacional con Lacrosse, Address, Grenfell, Mocejón y Campanar.

**Lo que dices**:
> «El atlas cruza 10 capas de datos abiertos del Ajuntament y del
> Catastro INSPIRE para analizar 36.300 edificios únicos de
> València. Con un criterio conservador —diez plantas o más,
> construidos entre el año 2000 y 2017— identifica 154 edificios
> que comparten lo que llamamos perfil Campanar. No es la primera
> vez que esto pasa en Europa: Lacrosse en Melbourne en 2014,
> Address en Dubai en 2015, Grenfell en Londres en 2017 con 72
> víctimas, Mocejón en Toledo en 2022 y Campanar en 2024. Todos
> compartían el mismo material en fachada.»

---

## CAPÍTULO 3 · 0:48 → 1:38 · Tu edificio · click + sliders

**En pantalla**: vuelta a la pestaña «Análisis», zoom hasta el
barrio de Aiora, click en un polígono dorado del Catastro. El panel
derecho se rellena con los valores reales del edificio. Aparece
resaltado el panel y el bloque «Por qué este riesgo». Después se
ven los sliders cambiando uno a uno con outline brasa: Fachada de
combustible a ladrillo, SCI de parcial a completo, hora a las 03:00.

**Lo que dices**:
> «Cualquier persona puede hacer click en su edificio y ver el
> riesgo simulado. El panel se rellena con los valores reales del
> Catastro y el modelo explica de dónde viene cada cifra: el
> régimen de fachada crítica, qué subfactor pesa más y, lo más
> importante, cómo se propagaría el fuego con esta fachada.
>
> Y la potencia está en simular: si esta fachada combustible se
> sustituyera por una de ladrillo no combustible, el riesgo
> baja casi a la mitad en directo. Si además se completa el
> sistema contra incendios, baja todavía más. Y si cambiamos
> la hora a la madrugada, vemos que la exposición poblacional
> sube porque hay más gente dentro del edificio. Esa es la
> potencia del modelo paramétrico: 36.300 escenarios distintos
> en una sola página.»

---

## CAPÍTULO 4 · 1:38 → 2:08 · Plan operativo del SPEIS

**En pantalla**: scroll al bloque de recomendaciones automáticas
(las tres mejoras con mayor caída de riesgo) y al «Plan de
respuesta operativa». Después vuelta al mapa con los círculos de
evacuación, perímetro operativo y la ruta hasta el parque de
bomberos trazada por calles reales con OSRM.

**Lo que dices**:
> «cendra no se queda en el diagnóstico. Para cada edificio
> calcula las tres mejoras que más reducirían el riesgo, y
> propone un plan operativo del SPEIS: cuántos efectivos, cuántas
> dotaciones, qué caudal de agua y qué tiempo de control se
> necesitan según la altura y el régimen del incendio. En el mapa
> aparece el radio de evacuación inmediata, el perímetro operativo
> y la ruta real por calles hasta el parque más cercano,
> calculada con OSRM.»

---

## CAPÍTULO 5 · 2:08 → 2:38 · RAG normativo

**En pantalla**: bloque «Qué dice la normativa de tu edificio» se
despliega. Aparecen sugerencias de preguntas adaptadas al edificio
simulado. Se escribe en directo «¿Qué pasó en Campanar y por qué
afecta a mi edificio?» y se pulsa Buscar. Aparecen tres tarjetas
con el resultado: investigación judicial, RD 732/2019 post-Grenfell
y CTE DB-SI SI 2.

**Lo que dices**:
> «Cuando alguien pregunta sobre la normativa de su edificio,
> cendra busca en un corpus curado del Código Técnico, la
> antigua NBE-CPI, el reglamento de instalaciones y la
> inspección técnica de la Comunitat Valenciana. La búsqueda
> es BM25 puro en JavaScript, sin librerías y sin enviar nada
> a ningún servidor externo. Cada respuesta cita textualmente
> el artículo y enlaza al BOE o al DOGV. Es trazabilidad de
> verdad: cualquier persona técnica puede verificar la fuente.»

---

## CAPÍTULO 6 · 2:38 → 3:18 · Asistente con IA · widget flotante

**En pantalla**: aparece el botón flotante rojo-morado del asistente
abajo a la derecha, se hace click y se abre el panel flotante con
cabecera degradada. Se escribe en directo la pregunta «¿Por qué mi
edificio tiene tanto riesgo y qué bajaría más la cifra?». **Llama
3.1 responde realmente desde Cloudflare Workers AI** con los
valores exactos del modelo y la sugerencia de qué slider tocar.

**Lo que dices**:
> «Para preguntas más abiertas, en la esquina aparece el botón
> del asistente conversacional. Detrás está Llama 3.1 8B, un
> modelo open source de Meta alojado en Cloudflare Workers AI,
> que entra en el plan gratuito hasta diez mil peticiones al día.
> Lo importante es que está blindado: solo usa los datos de tu
> simulación y los pasajes normativos que ha recuperado el
> buscador. No inventa cifras, no señala edificios concretos y,
> si no sabe, lo dice. Aquí tenemos a Llama explicando con los
> valores exactos del modelo por qué este edificio tiene tanto
> riesgo y proponiendo qué slider tocar para bajarlo.»

---

## CAPÍTULO 7 · 3:18 → 3:38 · Los 154 candidatos + CSV

**En pantalla**: vista «Propuestas» otra vez, scroll a la tabla
descargable de los 154. Se filtra por «aiora» y se ve cómo la
tabla reacciona en directo. Se quita el filtro. El botón
«Descargar CSV» aparece resaltado en brasa.

**Lo que dices**:
> «La lista completa de los 154 candidatos está aquí: barrio,
> plantas, año, riesgo, tiempo de bomberos y referencia
> catastral. Es filtrable, ordenable y descargable como CSV.
> Cualquier técnico municipal puede usarla mañana para empezar
> las inspecciones de fachada.»

---

## CAPÍTULO 8 · 3:38 → 3:49 · Cierre con `/historia`

**En pantalla**: cambio a la página `/historia.html`, scroll por
las siete escenas del scrollytelling (Campanar, edificio, fuego,
propagación, cronología, 154, CTA final).

**Lo que dices**:
> «cendra punto pages punto dev. Datos abiertos del Ajuntament,
> código abierto bajo licencia MIT.»

---

## Notas de producción

- **Resolución**: el WebM está en 1920×1080. Exporta el MP4 final
  en 1080p también.
- **Audio**: voz limpia, sin música. Si quieres meter música
  ambiental ponla a -25 dB.
- **Subtítulos**: añádelos en post para que el jurado pueda verlo
  sin sonido. Canva los genera automáticamente desde el audio.
- **Cara o no cara**: en Canva puedes meterte tú en un círculo en
  la esquina inferior derecha hablando. Sube credibilidad. No es
  obligatorio.
- **Cierre con frame fijo**: añade 2-3 segundos extra al final con
  un frame fijo de la URL en grande para que el jurado se quede
  con el dato.

## Versión corta (60 s)

Mantén los capítulos 1, 3, 5 (RAG normativo) y 6 (asistente IA).
Recorta el resto. Te queda un trailer rápido para Instagram,
Twitter o LinkedIn donde se entiende la innovación.

---

## Opción alternativa · grabarlo tú con OBS (calidad estudio)

Si prefieres un vídeo con **calidad máxima** (8000 kb/s, 60 fps,
cero lag en `flyTo`) y no te importa los 15 minutos de tu tiempo,
esta es la receta:

1. Instala **OBS Studio** (gratis · <https://obsproject.com>).
2. Settings → Video → Output (Scaled) Resolution **1920×1080**,
   FPS **60**.
3. Settings → Output → Recording → Format **MP4** · Encoder **x264**
   · Bitrate **8000 kb/s** · Preset **veryfast**.
4. Sources → **Display Capture** → tu monitor.
5. Abre Chrome / Edge a pantalla completa en
   `https://cendra.pages.dev`. Modo incógnito para que no
   aparezcan extensiones ni autocompletados.
6. Pulsa **Start Recording** en OBS y sigue el guión de arriba
   capítulo por capítulo con calma. Si te equivocas en una toma,
   espera 3 segundos y rehazla; cortarás luego.
7. Stop Recording. Carga el MP4 resultante en Canva o DaVinci y
   añade voz encima como en la opción A.

**Ventajas frente al script automatizado**:
- 60 fps, suavidad nativa.
- Bitrate alto, las cifras del panel se leen perfectamente.
- Cero lag de `flyTo`.

**Desventajas**:
- Tienes que ir tú clicando, así que cualquier error de UI lo
  graba (los descartas en post). El script automático no falla
  nunca.
