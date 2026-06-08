---
title: "cendra · ficha del proyecto"
lang: es
---

# cendra · atlas paramétrico de riesgo de incendio en València

## Categoría del concurso

**Datos abiertos** (procedimiento `AD.TR.15`, convocatoria 2026,
premios para proyectos de datos abiertos y periodismo de datos del
Ajuntament de València).

## Autor

Iñaki Martín Sorribes · `imxrtins@gmail.com`

## Acceso al proyecto

- **Atlas desplegado y accesible públicamente**:
  <https://cendra.pages.dev>
- **Código fuente abierto en GitHub** (licencia MIT):
  <https://github.com/imartinsorribes/cendra>
- **Dataset abierto adjunto** (CSV con los 154 edificios identificados
  con «perfil Campanar»): incluido en este envío como
  `candidatos_campanar.csv`.
- **Memoria detallada del proyecto** (Anexo II): incluida en este
  envío como `anexo-ii.pdf`.

## Resumen del proyecto

cendra es un atlas paramétrico abierto que **estima el riesgo de
incendio de los edificios residenciales de València** cruzando diez
capas de datos abiertos publicadas por el propio Ajuntament y por el
Catastro INSPIRE.

A partir del incendio de Campanar (febrero de 2024, diez víctimas),
el atlas identifica de forma trazable los **154 edificios de la
ciudad que comparten el perfil temporal y de altura** del edificio
que ardió (10 plantas o más, construidos entre 2000 y 2017,
correspondientes a la era del revestimiento de composite con núcleo
combustible).

El proyecto se entrega como una **herramienta web interactiva** que
combina:

- Un **modelo paramétrico de tres dimensiones** (vulnerabilidad
  estructural · exposición poblacional · respuesta operativa del
  SPEIS) calibrado contra padrón INE.
- Una **interfaz de simulación** en la que cualquier persona puede
  consultar el riesgo de su edificio y comprobar cómo cambia al
  modificar fachada, sistema contra incendios, año de construcción
  o altura.
- Un **plan operativo del SPEIS por edificio** con radios de
  evacuación, perímetro, vehículos y ruta real por calles
  (calculada con OSRM).
- Un **buscador trazable del corpus normativo** (CTE DB-SI,
  NBE-CPI-91, RIPCI 2017, ITE Comunitat Valenciana, RD 732/2019
  post-Grenfell) que cita textualmente el artículo y enlaza al BOE.
- Un **asistente conversacional con IA** (Llama 3.1 8B alojado en
  Cloudflare Workers AI, plan gratuito) blindado para no inventar
  cifras ni señalar edificios concretos.
- Una **página de narrativa visual** (scrollytelling) que explica
  la cronología internacional de incendios de fachada combustible
  desde Lacrosse (2014) hasta Campanar (2024).

## Datos abiertos utilizados

Diez capas del portal de datos abiertos del Ajuntament de València
(`opendata.vlci.valencia.es`, CKAN) y del Catastro INSPIRE, cruzadas
mediante operaciones espaciales reproducibles documentadas en la
memoria. Toda la cadena de transformaciones está abierta en el
repositorio y cualquiera puede regenerar los derivados desde cero.

## Tecnologías

Python (GeoPandas) y JavaScript (MapLibre GL) para el modelo y la
interfaz; Cloudflare Pages para el hosting estático con despliegue
continuo desde el repositorio; Workers AI para el asistente
conversacional. Cero coste de infraestructura.

## Apertura y reutilización

- **Código bajo licencia MIT**.
- **Datos derivados bajo licencia CC BY 4.0** (atribución requerida
  al Ajuntament de València y al Catastro INSPIRE).
- **Pipeline 100 % reproducible**: cualquier persona puede regenerar
  todo el atlas desde cero ejecutando los scripts del repositorio.
- **Cuarenta tests automatizados** verifican el modelo paramétrico,
  los cortes normativos, la sincronía entre la versión Python (batch)
  y la versión JavaScript (frontend) y las funciones auxiliares.
- **CITATION.cff** en la raíz del repositorio permite a GitHub
  generar la cita bibliográfica correctamente para reutilización
  académica.

## Cómo puede el jurado verificar el proyecto

1. Abrir <https://cendra.pages.dev> en cualquier navegador y
   explorar el atlas durante unos minutos.
2. Descargar el CSV de los 154 candidatos desde la pestaña
   «Propuestas» o desde el adjunto de este envío.
3. Leer la memoria (Anexo II) para entender la metodología y la
   trazabilidad.
4. Si se desea, clonar el repositorio de GitHub y ejecutar
   `pytest tests/` para verificar que los 40 tests pasan.
