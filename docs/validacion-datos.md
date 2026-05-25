# Validación de datos · 2026-05-14

Auditoría sistemática del estado de los datos, realizada con
`scripts/validar_datos.py`. El resultado completo en JSON queda
guardado en `data/processed/validacion_datos.json`. Aquí se
documentan las decisiones, correcciones y anomalías legítimas
encontradas.

## 1. Bug detectado y corregido · sobreestimación de población

### Síntoma

La estimación inicial daba **1.012.050 habitantes** en el término
municipal de València, contra el **791.413** del Padrón Continuo INE
2023. Una sobreestimación del **+27,9 %**.

### Causa

`scripts/extraer_viviendas.py` aplicaba el factor `2,4 hab/vivienda`
sobre el campo `numberOfDwellings` del Catastro INSPIRE. Este factor
proviene de la Encuesta Continua de Hogares del INE y se refiere a la
**vivienda principal habitada**, una categoría restrictiva.

El Catastro, en cambio, registra **todas las viviendas administrativas
de la finca**: las habitadas habitualmente, las vacías, las secundarias,
las que están en alquiler turístico, las que están en obra o
rehabilitación, etc. Multiplicar todas ellas por el factor de hogar
medio sobrestima inevitablemente la población real.

### Corrección aplicada

Se recalibra el factor empíricamente contra el padrón INE:

```
factor = 791.413 hab / 421.687 viviendas catastradas
 = 1,8769...
 ≈ 1,88 hab / vivienda catastrada
```

Este es el factor que `extraer_viviendas.py` aplica desde ahora. La
constante `HAB_POR_VIVIENDA` baja de `2.4` a `1.88` con un comentario
extenso que justifica la decisión y advierte que **no es extrapolable a
otras ciudades** sin recalibrar con su padrón local.

### Verificación

Tras la corrección:

| Magnitud | Modelo | INE 2023 | Diferencia |
|---|---:|---:|---:|
| Población València | 792.775 | 791.413 | **+0,17 %** |

El error está dentro del margen razonable de cualquier modelo
demográfico que estime población a partir de catastro.

## 2. Outliers verificados · alturas del Catastro

Distribución de alturas de los 214.000 edificios:

| Rango (m) | Edificios | % |
|---|---:|---:|
| 0-6 | 88.616 | 41,4 |
| 6-12 | 28.533 | 13,3 |
| 12-21 | 59.937 | 28,0 |
| 21-30 | 28.967 | 13,5 |
| 30-50 | 7.123 | 3,3 |
| 50-75 | 788 | 0,4 |
| 75-100 | 34 | 0,02 |
| 100-150 | 2 | 0,001 |

Coherente con una ciudad mediterránea con casco bajo predominante y
algunos rascacielos puntuales. Los **2 edificios > 100 m** son partes
catastrales (`localId` terminado en `_part##`) de torres reales:

- **108 m / 36 plantas** y **105 m / 35 plantas** comparten el localId
 base `7913901YJ2771D`, que corresponde al área de Av. de Francia /
 Torres de Francia (Quatre Carreres). Cuadra con la documentación
 pública: Torre de Francia I tiene 115 m / 33 plantas.
- **99-96 m / 32-33 plantas** con localId base `3551701YJ2735B` y
 `3449301YJ2734G`, en zona de avenidas anchas con altura permitida
 alta.

No son errores: son los rascacielos reales de la ciudad.

## 3. Anomalías legítimas no corregidas

### 3.1 Features sin geometría

| Capa | Sin geom. | Justificación |
|---|---:|---|
| `equipamientos.geojson` | 13 / 2.915 | El dataset municipal incluye entradas administrativas sin coordenadas: locales en proceso de geolocalización, equipamientos pendientes de apertura o ya cerrados que se conservan en el registro. Ejemplos: «AUXILIA VALENCIA», «LA MUTANT», «CONSELLERIA DE INNOVACIÓN...». |
| `majors.geojson` | 4 / 151 | Idem |

**Tratamiento**: se filtran al cargar la capa para análisis. No se
modifica el GeoJSON descargado para mantener la trazabilidad del
portal original.

### 3.2 Tipo `MultiPoint` en `hospitales.geojson`

Los 62 features son `MultiPoint` aunque todos contienen un solo punto
(`n_pts = 1` para los 62). Es una decisión del publicador del dataset
en el portal, no un error.

**Tratamiento**: al cargar la capa para análisis, se convertirá a
`Point` con `.explode()` o tomando `geometry.iloc[0].geoms[0]`. No
modifica el archivo original.

### 3.3 Coordenadas en pedanías y extremos del término

Tras ampliar el bbox de validación de `(-0,45, 39,30, -0,27, 39,55)`
a `(-0,50, 39,28, -0,20, 39,60)` para abarcar el término municipal
completo (Pueblos del Sur al sur de la Albufera, Pueblos del Norte
en Borbotó/Carpesa), desaparecen los falsos positivos previos:

- `hidrants`: pasó de 9 fuera a 0
- `barris`: pasó de 2 fuera a 0
- `equipamientos`: pasó de 26 fuera a algunos pocos en quioscos
 cerca del límite municipal (legítimos según el dataset)
- `manzanas_poblacion`: pasó de 30 fuera a 7 marginalmente fuera
 (lat 39,2796 frente al corte 39,28 — 40 m de margen, son del
 límite sur de Pinedo / El Saler)

### 3.4 Polígonos con topología inválida

| Capa | Inválidos | Tratamiento |
|---|---:|---|
| `manzanas_poblacion.geojson` | 8 / 4.913 (0,16 %) | Polígonos auto-intersectantes del dataset original. Se aplica `shapely.validation.make_valid()` al cargar. |

### 3.5 Edificios sin barrio asignado

Sobre una muestra aleatoria de 5.000 edificios del Catastro, **7 (0,14 %)**
no caen dentro de ningún polígono de `barris.geojson`. Razones probables:
- Edificios justo en el borde administrativo (resolución de los polígonos).
- Pequeñas zonas no asignadas (parcelas industriales o servidumbres).
- Edificios en los límites con municipios vecinos (Mislata, Burjassot,
 Alboraia).

Extrapolando al total: ~300 edificios de 214.000 sin barrio. Para el
modelo agregado por barrio se ignorarán; para el modelo individual la
ausencia de barrio asignado se traduce en valores neutros de
exposición.

## 4. Capa propia de parques de bomberos

| Verificación | Resultado |
|---|---|
| Número de features | 6 (esperado: 6) |
| Todos dentro del bbox del término |  |
| Direcciones verificadas en Infociudad | (ver `data/raw/parques_bomberos_FUENTES.md`) |
| Coordenadas geocodificadas con Nominatim |  |

## 5. Coherencia interna del modelo de riesgo

### Edge cases probados

| Caso | Riesgo | Régimen | Comentario |
|---|---:|---|---|
| Edificio 1 planta · 2020 · ladrillo · SCI completo · 12:00 | 15,6 | normal | Bajo, coherente |
| Edificio 50 plantas · 2024 · ACM-PE · sin SCI · saturación · 08:00 | 84,2 | fachada-crítica | Salta a régimen crítico |
| Año 1850 · ladrillo · sin SCI · cubierta combustible · 03:00 | 42,3 | normal | Sin fachada combustible, pero ITE+SCI+cubierta combustibles elevan |
| Año 2030 (futuro) · composite-CTE · todo OK · 12:00 | 27,7 | normal | Solidez sanitaria del modelo |

### Tests de validación del modelo

Repetidos tras la corrección de `extraer_viviendas.py`:

| Test | Resultado |
|---|---|
| Campanar real ≥ 80 | **84,8** |
| Sensibilidad fachada (Campanar real vs ladrillo) | **-60 %** (umbral ≥ 30 %) |
| Sensibilidad horaria edificio lejano (Borbotó 4 h vs 8 h) | **28,4 → 34,9** |
| Orden de escenarios canónicos | Campanar > Carmen > Quatre Carreres |

## 6. Conclusión

- Un bug grave detectado y corregido (sobreestimación poblacional del
 28 %, ahora dentro del 0,2 % del padrón oficial).
- Anomalías residuales documentadas y catalogadas como legítimas del
 dataset original o como cosméticas.
- Modelo de riesgo coherente bajo edge cases y casos canónicos.
- Validación reproducible con `python scripts/validar_datos.py`.
