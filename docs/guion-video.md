# Guión del vídeo de presentación · 3 minutos

> **Vídeo base ya grabado**: `docs/video-demo.webm` (19 MB · 3:00 · 1920×1080 · 25 fps)
> reproducido automáticamente por `scripts/grabar_demo.py` siguiendo
> este guión exacto. La pista de vídeo está; solo falta tu voz por
> encima.
>
> **Cómo añadirle voz** (por orden de sencillez):
> 1. **Canva** (en línea): «Crear un diseño» → «Vídeo» → subir el
>    WebM, añadir pista de audio nueva con tu micro, grabar leyendo
>    el guión, exportar como MP4. Tiene plantillas con cara
>    flotante en círculo si quieres salir tú también.
> 2. **DaVinci Resolve** (gratis, escritorio): importa el WebM,
>    pista de audio nueva, graba en directo o pega un MP3 ya
>    grabado, exporta H.264 1080p.
> 3. **OBS** o **Loom**: pones el WebM en pantalla completa y
>    grabas con tu micro en tiempo real comentando encima.
>
> **Si retoques algo del atlas y quieras regenerar el vídeo base**:
> `python scripts/grabar_demo.py`
>
> Las cifras totales: 480 palabras a ritmo natural (~2,7 palabras/segundo).
> Si vas muy justo de tiempo, recorta las frases entre paréntesis.

---

## CAPÍTULO 1 · 0:00 → 0:18 · Hook

**En pantalla**: home de cendra con el mapa de barrios de València
coloreado por riesgo (verde a brasa). La leyenda inferior izquierda
queda resaltada un segundo.

**Lo que dices**:
> «En febrero de 2024 ardió un edificio de catorce plantas en el
> barrio de Campanar de València. Diez personas murieron. La fachada
> de composite con núcleo combustible cubrió todo el bloque en
> menos de media hora. Esto es cendra: un atlas paramétrico que
> intenta entender qué pasó y cuántos edificios más en la ciudad
> podrían estar en una situación parecida.»

---

## CAPÍTULO 2 · 0:18 → 0:42 · Las cifras

**En pantalla**: cambio a la pestaña «Propuestas». Las seis cifras
clave (36.300 edificios, 154 candidatos, 10 capas, 6 parques, 1.923
hidrantes, 40 tests). Después scroll a la cronología histórica con
Lacrosse, Address, Grenfell, Mocejón y Campanar.

**Lo que dices**:
> «El atlas cruza 10 capas de datos abiertos del Ajuntament y del
> Catastro INSPIRE para analizar 36.300 edificios únicos de
> València. Con un criterio conservador —diez plantas o más,
> construidos entre 2000 y 2017— identifica 154 edificios que
> comparten lo que llamamos perfil Campanar. No es la primera
> vez que esto pasa en Europa: Lacrosse en 2014, Grenfell en 2017,
> Mocejón en 2022. Todos compartían el mismo material en fachada.»

---

## CAPÍTULO 3 · 0:42 → 1:18 · Tu edificio · click + sliders

**En pantalla**: vuelta a «Análisis», zoom hasta Aiora, click en un
polígono dorado del Catastro. El panel derecho se rellena con los
valores reales del edificio. Aparece el bloque «Por qué este
riesgo». Después se cambian los sliders: Fachada de combustible a
ladrillo, SCI a completo, hora a las 03:00.

**Lo que dices**:
> «Cualquier persona puede hacer click en su edificio y ver el
> riesgo simulado. El panel se rellena con los valores reales del
> Catastro y el modelo explica de dónde viene cada cifra: la
> fachada pesa el 30%, la edad el 25%, la altura el 15%. Si esta
> fachada se sustituyera por una no combustible, el riesgo baja
> a casi la mitad. Si además se completa el sistema contra
> incendios, baja todavía más. Y si simulamos que el incendio
> ocurre de madrugada, la exposición poblacional sube porque
> hay más gente dentro. Esa es la potencia del modelo paramétrico.»

---

## CAPÍTULO 4 · 1:18 → 1:45 · Plan operativo del SPEIS

**En pantalla**: scroll a las recomendaciones automáticas (tres
mejoras con mayor caída de riesgo). Después scroll al «Plan de
respuesta operativa». Vuelta al mapa con los círculos de
evacuación, perímetro y la ruta hasta el parque de bomberos
trazada por calles reales con OSRM.

**Lo que dices**:
> «cendra no se queda en el diagnóstico. Para cada edificio calcula
> las tres mejoras que más reducirían el riesgo, y propone un plan
> operativo del SPEIS: cuántos efectivos, cuántas dotaciones, qué
> caudal de agua y qué tiempo de control se necesitan. En el mapa
> aparece el radio de evacuación inmediata, el perímetro operativo
> y la ruta real por calles hasta el parque más cercano.»

---

## CAPÍTULO 5 · 1:45 → 2:12 · RAG normativo

**En pantalla**: bloque «Qué dice la normativa de tu edificio» se
despliega. Aparecen sugerencias de preguntas según el edificio
simulado. Se escribe «¿Qué pasó en Campanar y por qué afecta a mi
edificio?» y se pulsa Buscar. Aparecen tres tarjetas: investigación
judicial, RD 732/2019 post-Grenfell y CTE DB-SI SI 2.

**Lo que dices**:
> «Cuando alguien pregunta sobre la normativa de su edificio,
> cendra busca en un corpus curado del Código Técnico, la antigua
> NBE-CPI, el reglamento de instalaciones y la inspección técnica
> de la Comunitat Valenciana. Cada respuesta cita textualmente el
> artículo y enlaza al BOE. Es trazabilidad de verdad: cualquier
> persona técnica puede verificar la fuente.»

---

## CAPÍTULO 6 · 2:12 → 2:35 · Asistente con IA

**En pantalla**: bloque «Pregúntale al asistente con IA» con el
badge morado «con IA». Se escribe la pregunta «¿Por qué mi edificio
tiene tanto riesgo?» y aparece la respuesta del modelo Llama 3.1 8B.

**Lo que dices**:
> «Para preguntas más abiertas hay un asistente conversacional con
> el modelo Llama 3.1 8B alojado en Cloudflare Workers AI. Funciona
> en el plan gratuito y, lo importante, está blindado: solo usa los
> datos de la simulación y los pasajes normativos que ha
> encontrado el buscador. No inventa cifras, no señala edificios
> concretos y, si no sabe, lo dice.»

---

## CAPÍTULO 7 · 2:35 → 2:55 · Los 154 candidatos + CSV

**En pantalla**: vista «Propuestas» otra vez, scroll a la tabla
descargable. Se filtra por «aiora» y se ve cómo la tabla reacciona.
Se quita el filtro. El botón «Descargar CSV» aparece resaltado en
brasa.

**Lo que dices**:
> «La lista completa de los 154 candidatos está aquí: barrio,
> plantas, año, riesgo, tiempo de bomberos y referencia catastral.
> Es filtrable, ordenable y descargable como CSV. Cualquier
> técnico municipal puede usarla mañana para empezar las
> inspecciones de fachada.»

---

## CAPÍTULO 8 · 2:55 → 3:00 · Cierre con `/historia`

**En pantalla**: cambio a la página `/historia.html`, scroll rápido
por las siete escenas del scrollytelling (Campanar, edificio,
fuego, propagación, cronología, 154, CTA).

**Lo que dices**:
> «cendra punto pages punto dev. Datos abiertos del Ajuntament,
> código abierto bajo licencia MIT.»

---

## Notas de producción

- **Resolución**: el WebM está en 1920×1080. Exporta el MP4 final
  en 1080p también.
- **Audio**: voz limpia, sin música. Si quieres añadir música la
  pones muy baja (-25 dB) y que sea ambiental, no festiva.
- **Subtítulos**: añádelos en post para que el jurado pueda verlo
  sin sonido. Canva los genera automáticamente desde el audio.
- **Cara o no cara**: en Canva puedes meterte tú en un círculo en
  la esquina inferior derecha hablando. Sube credibilidad. No es
  obligatorio.
- **Cierre con frame fijo**: añade 2-3 segundos extra al final con
  un frame fijo de la URL y «cendra.pages.dev» en grande para que
  el jurado se quede con el dato.

## Si quieres hacer una versión más corta (60 s)

Mantén los capítulos 1, 3, 5 y 8. Recorta el resto. Te queda un
trailer rápido para Instagram, Twitter o LinkedIn.
