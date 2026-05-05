# Registro de cambios

Todos los cambios relevantes de este proyecto se documentan aquí.
El formato sigue [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/)
y la numeración de versiones [Semantic Versioning](https://semver.org/lang/es/).

## [No publicado]

### Añadido
- Estructura inicial del repositorio.
- Pivote desde `ombrari` (atlas térmico peatonal): el proyecto anterior
  queda como referencia y código reutilizable en `../DECV/`.
- Repositorio `git` inicializado en la raíz.
- Scripts heredados de `ombrari` y adaptados:
  `fetch_catalogo_vlci.{py,ps1}`, `descargar_capas.py`,
  `descargar_catastro.py`, `extraer_alturas_ciudad.py`,
  `extraer_viviendas.py`. Se descartaron los scripts específicos del
  dominio térmico (cálculo solar, prescripciones de arbolado, limpieza
  de fuentes de agua, procesado de sombras).
- Volcado del catálogo CKAN de `opendata.vlci.valencia.es` en
  `data/raw/` (294 datasets, captura del 2026-05-14).
- Script propio `filtrar_catalogo_incendio.py` que clasifica los
  datasets por temas (núcleo, vulnerabilidad, equipamientos sensibles,
  edificación, contexto) y produce `docs/fuentes-encontradas.md`.
- Documento `docs/hallazgos-exploracion.md` con IDs verificados del
  MapServer del geoportal, datasets nucleares confirmados y la
  decisión metodológica sobre la capa de parques de bomberos.
- Ampliación de `descargar_capas.py` con todos los identificadores
  verificados: hidrantes, fites bombers, barris, edificis,
  equipamientos municipales, mayores, área de prioridad residencial,
  vulnerabilidad por barrios, hospitales, centros educativos y
  manzanas con población.

### Contexto
El proyecto arranca el 2026-05-14. La idea es construir un atlas de
riesgo de incendio urbano en València con **escenarios paramétricos**,
respondiendo a la pregunta abierta tras el incendio de Campanar de
febrero de 2024.

### Añadido (continuación del día 2026-05-14)
- Capa propia `data/raw/parques_bomberos.geojson` con los 6 parques
  del SPEIS de l'Ajuntament (Central, Campanar, Norte, Oeste, Centro
  Histórico, Saler/Devesa). Coordenadas geocodificadas con Nominatim
  de OpenStreetMap, direcciones verificadas con la web oficial
  Infociudad. Trazabilidad en `data/raw/parques_bomberos_FUENTES.md`.
- Script `scripts/construir_parques_bomberos.py` reproducible.
- Documento `docs/modelo-riesgo.md` (v0.1 y v0.1.1) con el diseño
  completo del modelo paramétrico: tres dimensiones (vulnerabilidad
  intrínseca, exposición poblacional, respuesta de emergencia), pesos
  justificados, modelización del tiempo de llegada de bomberos por
  hora del día y régimen dinámico de pesos cuando la fachada satura
  V_intrínseca.
- Script `scripts/calcular_riesgo.py` que implementa el modelo y
  soporta tres modos de uso (escenario canónico, parámetros sueltos,
  comparativa de los tres escenarios).
- Procesado del Catastro INSPIRE: 214.000 edificios con altura por
  planta (`extraer_alturas_ciudad.py`, gpkg de 72 MB) y 88 barrios
  con viviendas y población estimada
  (`extraer_viviendas.py`, CSV de 5 KB · 1.012.050 hab estimados en
  total).
- Descarga reproducible de 10 capas geoespaciales del portal CKAN
  (`descargar_capas.py`). La capa `edificis` se excluye a propósito
  (redundante con Catastro INSPIRE, ver comentario en el script).
- Documento `docs/inventario-datos.md` con el estado completo de
  todos los datos versionados, no versionados y procesados.
- Repositorio remoto en `https://github.com/imartinsorribes/cendra`
  (privado hasta el envío).

### Validación del modelo
- Test Campanar: riesgo 84,8 / 100 (umbral establecido ≥ 80) ✅
- Test sensibilidad de la fachada: Campanar real 84,8 → mismo edificio
  con fachada de ladrillo 33,6 → caída del 60 % (umbral ≥ 30 %) ✅
- Test sensibilidad horaria (edificio lejano Borbotó): riesgo 28,4
  a las 4:00 → 34,9 a las 8:00 (tiempo de llegada 7,7 → 14,4 min) ✅

### Cálculo batch del riesgo
- `scripts/calcular_riesgo_batch.py`: aplica el modelo a los 214.000
  edificios del Catastro INSPIRE bajo un escenario por defecto
  (paramétricos en valores medios). Spatial joins vectorizados +
  cálculo NumPy en unos 25 s sobre el gpkg completo.
- Salidas:
  - `data/processed/riesgo_edificios.gpkg`: una geometría + 8
    atributos numéricos por edificio (no versionado por tamaño).
  - `data/processed/riesgo_por_barrio.csv`: agregado de los 88
    barrios con riesgo medio / p75 / p90 + métricas auxiliares.
- Distribución del riesgo medio por barrio: media 36,5 · σ 5,1 ·
  rango 24,9-46,1. Top: RAFALELL-VISTABELLA, EL CALVARI, ELS ORRIOLS,
  EL PERELLONET — combinación de vulnerabilidad social y/o tiempo de
  llegada elevado.

### Dos bugs detectados al validar el batch
- El cruce entre barrios y vulnerabilidad estaba intentando hacerse
  por `codbarrio` (rango 1-8 dentro de distrito) contra `codbar`
  (rango 11-162, código compuesto). 0 matches. Cambiado a cruce por
  nombre normalizado: 84,5 % de los edificios reciben vulnerabilidad;
  el resto son pedanías sin datos publicados.
- El campo `ind_global` del dataset `Vulnerabilitat per barris 2021`
  está INVERTIDO: valor bajo = vulnerabilidad alta. Verificado contra
  el campo de etiqueta `vul_global`. Reescalado lineal corregido:
  `clip((3,9 - ind) / 2 × 100, 0, 100)`. La σ del riesgo entre
  barrios sube de 4,1 a 5,1 (modelo discrimina mejor). Top-10 ahora
  incluye EL CALVARI y ELS ORRIOLS, que el bug enmascaraba.

### Frontend web interactivo · `web/`
- `web/index.html`: estructura con panel lateral + mapa MapLibre +
  cuadro flotante con el resultado.
- `web/style.css`: paleta brasa/ceniza, layout grid responsivo,
  móvil en stack vertical.
- `web/modelo.js`: traducción literal del modelo Python a JS. MISMAS
  constantes, MISMA fórmula, MISMA regla de saturación por fachada.
  Comentario en cabecera advierte que ambos archivos viven en sync.
- `web/app.js`: inicializa MapLibre con base CARTO Positron, dibuja
  capa coroplética de barrios coloreada por riesgo medio, capa de
  parques de bomberos con tooltip, conecta los sliders al modelo con
  cálculo en vivo, propaga el contexto del barrio al hacer click,
  soporta los tres escenarios canónicos del documento.
- `web/data/barris_riesgo.geojson` (123 KB): geometría simplificada
  a 10 m con riesgo, densidad y vulnerabilidad por barrio.
- `web/data/parques_bomberos.geojson`: copia de la capa propia.
- `scripts/preparar_datos_web.py`: prepara y simplifica los GeoJSON
  que sirve el frontend.

### Auditoría de datos · `docs/validacion-datos.md`
- Script `scripts/validar_datos.py` que ejecuta una validación
  sistemática de todas las capas y derivados (counts, geometrías,
  CRS, bbox, outliers, edge cases del modelo).
- **Bug grave detectado y corregido**: sobreestimación poblacional del
  +27,9 % por aplicar el factor 2,4 hab/vivienda **principal habitada**
  del INE sobre el `numberOfDwellings` del Catastro INSPIRE (que
  cuenta TODAS las viviendas catastradas, incluidas vacías,
  secundarias y turísticas). Recalibrado a 1,88 hab/vivienda
  catastrada contra el padrón INE 2023 (791.413 hab). Tras la
  corrección la estimación queda a +0,17 % del padrón.
- Anomalías residuales documentadas:
  - 13 equipamientos y 4 mayores sin geometría (legítimo del
    dataset original, se filtran al cargar).
  - Capa `hospitales` con tipo `MultiPoint` (cosmético, se explota
    a Point al cargar).
  - 7 manzanas marginalmente fuera del bbox por 40 m en el límite
    sur del término.
  - 8 manzanas con polígonos auto-intersectantes (se aplica
    `make_valid` al cargar).
- Las 2 «torres» de >100 m del Catastro corresponden a edificios
  reales documentados (Torre de Francia y aledaños en Quatre
  Carreres).

### Hallazgos del arranque
- 130 de 294 datasets del portal CKAN matchean al menos un tema del
  dominio. Solo **2 datasets nucleares** (hidrantes y fites bombers).
- **No hay dataset oficial de parques de bomberos**, ni como dataset
  propio ni como subcategoría de `equipamients-municipals` (cuyas 19
  clases incluyen sanitarias, educativas, sociales y de policía,
  pero no bomberos). Se documentará una capa propia desde fuentes
  oficiales del SPEIS.
- Vulnerabilidad por barrios 2021 está disponible como GeoJSON
  directo: se incorporará al modelo como factor de impacto social.
