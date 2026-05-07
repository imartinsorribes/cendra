# cendra VLC

> **¿Cuál es el riesgo de incendio de tu edificio?**  
> Atlas paramétrico de València con datos abiertos.
>
> 🌐 **Atlas público**: <https://cendra.pages.dev>

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

Inventario completo y trazable en [`docs/inventario-datos.md`](docs/inventario-datos.md).

| Pieza | Estado |
|---|---|
| Volcado del catálogo CKAN | ✅ 294 datasets descargados (`data/raw/ckan_*.json`) |
| Inventario de fuentes relevantes | ✅ [`docs/fuentes-encontradas.md`](docs/fuentes-encontradas.md), 130 datasets clasificados |
| Hallazgos de la exploración | ✅ [`docs/hallazgos-exploracion.md`](docs/hallazgos-exploracion.md) |
| 10 capas geoespaciales del portal | ✅ descargadas (hidrantes, fites bombers, barris, equipamientos, mayores, área prioridad residencial, vulnerabilidad, hospitales, centros educativos, manzanas) |
| Parques de bomberos | ✅ capa propia con 6 parques del SPEIS verificados ([`data/raw/parques_bomberos.geojson`](data/raw/parques_bomberos.geojson) + [`FUENTES.md`](data/raw/parques_bomberos_FUENTES.md)) |
| Catastro INSPIRE Buildings 46900 | ✅ descargado (~163 MB ZIP, 3 GML descomprimidos) |
| Edificios 3D | ✅ procesado: 214.000 edificios con altura (media 13,1 m, máx 108 m) |
| Viviendas por barrio | ✅ procesado: 88 barrios, 1.012.050 hab estimados ([`data/processed/viviendas_por_barrio.csv`](data/processed/viviendas_por_barrio.csv)) |
| Modelo paramétrico de riesgo v0.1.1 | ✅ diseñado e implementado ([`docs/modelo-riesgo.md`](docs/modelo-riesgo.md) · [`scripts/calcular_riesgo.py`](scripts/calcular_riesgo.py)) |
| Validación y auditoría de datos | ✅ ([`docs/validacion-datos.md`](docs/validacion-datos.md) · [`scripts/validar_datos.py`](scripts/validar_datos.py)) |
| Cálculo batch sobre los 214k edificios | ✅ ([`data/processed/riesgo_edificios.gpkg`](data/processed/riesgo_edificios.gpkg) · gpkg no versionado) + agregado por barrio ([`data/processed/riesgo_por_barrio.csv`](data/processed/riesgo_por_barrio.csv)) |
| Frontend web interactivo | ✅ ([`web/`](web/) · HTML + MapLibre + modelo en JS + calculadora paramétrica + capa de los 2.000 edificios de mayor riesgo) |
| Memoria Anexo II del concurso | ✅ ([`docs/memoria/anexo-ii.md`](docs/memoria/anexo-ii.md)) |
| Configuración de despliegue público | ✅ ([`docs/despliegue.md`](docs/despliegue.md)) |
| Despliegue efectivo | ✅ <https://cendra.pages.dev> (Cloudflare Pages, despliegue continuo desde `main`) |

Las descargas grandes (`data/raw/large/`, `data/external/`) no se
versionan: están en `.gitignore`. Cualquier persona puede reproducir
el pipeline desde cero con los scripts del repositorio.

## Pipeline reproducible

```bash
# 1. Catálogo del portal y filtrado por dominio
python scripts/fetch_catalogo_vlci.py
python scripts/filtrar_catalogo_incendio.py

# 2. Capas geoespaciales (barrios, vulnerabilidad, manzanas, etc.)
python scripts/descargar_capas.py

# 3. Catastro INSPIRE (edificios + número de plantas + viviendas)
python scripts/descargar_catastro.py
python scripts/extraer_alturas_ciudad.py
python scripts/extraer_viviendas.py

# 4. Capa propia de parques de bomberos
python scripts/construir_parques_bomberos.py

# 5. Validar todos los datos (counts, geometrías, edge cases)
python scripts/validar_datos.py

# 6. Cálculo batch del riesgo sobre los 214.000 edificios
python scripts/calcular_riesgo_batch.py

# 7. Preparar GeoJSONs optimizados que sirve el frontend
python scripts/preparar_datos_web.py

# 8. Levantar el frontend localmente
python -m http.server 8000 --directory web
# y abrir http://localhost:8000
```

## Uso del modelo

Cálculo aislado desde la CLI:

```bash
# Escenario canónico (campanar | carmen | quatre-carreres-nuevo)
python scripts/calcular_riesgo.py --escenario campanar

# Comparativa de los tres escenarios
python scripts/calcular_riesgo.py --todos-escenarios

# Parámetros libres
python scripts/calcular_riesgo.py --plantas 14 --anio 2006 \
    --lon -0.398 --lat 39.485 --fachada composite-acmpe \
    --ite pendiente --sci parcial --cubierta mixto --hora 18
```

Desde el frontend la calculadora es reactiva: se hace clic en un
barrio, se mueven los sliders de plantas y año, se elige fachada /
ITE / SCI / cubierta y se ve cómo cambia el índice en tiempo real.

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
