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
