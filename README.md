# cendra VLC

> **¿Cuál es el riesgo de incendio de tu edificio?**  
> Atlas paramétrico de València con datos abiertos.

Proyecto para la **IV Convocatoria de Premios para proyectos de datos
abiertos y periodismo de datos del Ajuntament de València (2026)**,
categoría **datos abiertos** (procedimiento AD.TR.15).

## Por qué este proyecto

El 22 de febrero de 2024, un edificio residencial de 14 plantas en
**Campanar** se incendió por completo en pocas horas. Diez muertes,
veintenas de familias sin hogar. La investigación apunta a la
**combustibilidad de la fachada** (sistema de aluminio composite con
núcleo de polietileno) como factor crítico, sumada al diseño en
"efecto chimenea" y al tiempo de propagación del fuego.

València tiene **214.000 edificios** catalogados en Catastro. Cuántos
de ellos podrían comportarse como Campanar bajo condiciones similares
es la pregunta que el Ayuntamiento, la Generalitat, los bomberos y la
ciudadanía se hacen desde entonces.

Los datos clave para responderlo —materiales de fachada, sistemas de
protección contra incendios instalados, certificados ITE detallados—
**no son datos abiertos** y por buenas razones (privacidad, seguridad).
Pero **podemos construir una herramienta de simulación pública** que
combine los datos abiertos disponibles con escenarios paramétricos
sobre los datos que no lo son. Es lo que el Ayuntamiento necesita
para ordenar la inspección, los bomberos para optimizar respuesta y
la ciudadanía para entender el problema.

## El producto

Atlas web interactivo con tres capas combinadas:

1. **Mapa de edificios con factores conocidos** del Catastro:
   altura, año de construcción, uso, geometría 3D, densidad
   poblacional residencial estimada.
2. **Calculadora de escenarios paramétricos**: la persona usuaria
   puede introducir hipótesis sobre el edificio (tipo de fachada,
   sistema SCI, estado ITE) y la herramienta calcula el índice de
   riesgo resultante. El modelo está documentado y es auditable.
3. **Mapa de respuesta de bomberos**: tiempo de llegada estimado
   desde el parque más cercano, ubicación de los hidrantes
   municipales, equipamientos sensibles (residencias de mayores,
   centros sanitarios y escolares).

## Estructura

```
cendraVLC/
├── data/
│   ├── raw/           # descargas crudas del portal (CKAN)
│   ├── processed/     # derivados del análisis (CSV, GPKG)
│   └── external/      # Catastro INSPIRE, fuentes externas
├── scripts/           # pipelines reproducibles
├── docs/              # metodología, fuentes, memoria Anexo II
├── notebooks/         # análisis exploratorios
└── web/               # frontend desplegable estático
```

## Estado de los datos

A día de arranque (`2026-05-14`), lo que hay en el repositorio:

| Pieza | Estado | Cómo regenerarla |
|---|---|---|
| Volcado del catálogo CKAN | ✅ descargado (`data/raw/ckan_*.json`) | `python scripts/fetch_catalogo_vlci.py` |
| Inventario de fuentes relevantes | ✅ generado ([`docs/fuentes-encontradas.md`](docs/fuentes-encontradas.md)) | `python scripts/filtrar_catalogo_incendio.py` |
| Hallazgos de la exploración (IDs MapServer, ausencias, decisiones) | ✅ documentado ([`docs/hallazgos-exploracion.md`](docs/hallazgos-exploracion.md)) | (manual) |
| Capas geoespaciales del portal (hidrantes, fites bombers, barris, edificis, equipamientos, mayores, hospitales, centros educativos, vulnerabilidad, manzanas) | ⏳ pendiente de descarga | `python scripts/descargar_capas.py` |
| Parques de bomberos | ⚠️ no existe en el portal · capa propia a construir | (manual desde fuentes SPEIS) |
| Catastro INSPIRE Buildings 46900 | ⏳ pendiente de descarga (~540 MB de GML) | `python scripts/descargar_catastro.py` |
| Edificios 3D (altura por planta) | ⏳ depende de Catastro | `python scripts/extraer_alturas_ciudad.py` |
| Viviendas por barrio | ⏳ depende de Catastro + barrios | `python scripts/extraer_viviendas.py` |

Las descargas grandes (`data/raw/large/`, `data/external/`) no se
versionan: están en `.gitignore`. Cualquier persona puede reproducir
el pipeline desde cero con los scripts del repositorio.

## Pipeline reproducible

```bash
# 1. Catálogo del portal y filtrado por dominio
python scripts/fetch_catalogo_vlci.py
python scripts/filtrar_catalogo_incendio.py

# 2. Capas geoespaciales (barrios, vulnerabilidad, manzanas)
python scripts/descargar_capas.py

# 3. Catastro INSPIRE (edificios + número de plantas + viviendas)
python scripts/descargar_catastro.py
python scripts/extraer_alturas_ciudad.py
python scripts/extraer_viviendas.py

# 4. Modelo paramétrico (pendiente)
# python scripts/calcular_riesgo.py
```

## Continuidad con `ombrari`

Este proyecto pivota desde `ombrari` (atlas de justicia térmica
peatonal). Aquel queda **aparcado pero no borrado** como referencia
técnica. La parte del código directamente reutilizable —catálogo CKAN,
Catastro INSPIRE, extracción de viviendas y alturas— se ha copiado y
adaptado a este repositorio; el resto (cálculo solar, prescripciones
de arbolado) no aplica al dominio de incendio.

## Estado

Proyecto en arranque · 2026-05-14.

## Licencias

- Código bajo MIT (`LICENSE`).
- Datos derivados publicados en `data/processed/` bajo CC BY 4.0,
  citando como fuente los conjuntos del Ayuntamiento de València y de
  la Dirección General del Catastro.
- Visualizaciones y memoria (`docs/memoria/`) bajo CC BY 4.0.
