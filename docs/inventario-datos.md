# Inventario de datos · estado al 2026-05-14

Resumen del estado de las descargas y procesados. Las capas grandes y
los GML del Catastro no se versionan (`.gitignore`); este documento
sirve como referencia reproducible. Cualquier persona puede regenerar
todo ejecutando los scripts indicados.

## 1. Catálogo CKAN · `data/raw/`

| Archivo | Origen | Estado |
|---|---|---|
| `ckan_package_search_0.json` | `opendata.vlci.valencia.es/api/3/action/package_search?rows=1000` | ✅ 3,6 MB · 294 datasets |
| `ckan_package_list.json` | `…/package_list` | ✅ 11 KB |
| `ckan_group_list.json` | `…/group_list?all_fields=true` | ✅ 15 KB |
| `ckan_organization_list.json` | `…/organization_list?all_fields=true` | ✅ 1,4 KB |

Reproducible con: `python scripts/fetch_catalogo_vlci.py`

## 2. Capas geoespaciales · `data/raw/large/` (no versionadas)

| Capa | Endpoint | Volumen | Uso en el modelo |
|---|---|---|---|
| `hidrants.geojson` | MapServer/UrbanismoEInfraestructuras/222 | 0,69 MB · ~1.923 hidrantes | R_hidrante (distancia al hidrante más cercano) |
| `fites_bombers.geojson` | MapServer/Trafico/239 | 0,08 MB | R_acceso (calles preparadas para vehículos de emergencia) |
| `barris.geojson` | MapServer/UrbanismoEInfraestructuras/224 | 0,33 MB · 88 barrios | Agregación territorial |
| `equipamientos.geojson` | MapServer/SociedadBienestar/1 | 1,11 MB · 2.915 puntos | E_sensibles (filtrar por `clase`) |
| `majors.geojson` | MapServer/SociedadBienestar/24 | 0,05 MB · 151 puntos | E_sensibles (residencias / centros de día) |
| `area_prioridad_residencial.geojson` | MapServer/Trafico/1 | 0,02 MB · 3 polígonos | Contexto: APR (acceso restringido) |
| `vulnerabilitat_barris.geojson` | opendata.vlci · dataset 2021 | 0,16 MB · 70 polígonos | E_vulnerab (índice de vulnerabilidad social) |
| `hospitales.geojson` | opendata.vlci · dataset 2024 | 0,03 MB · 62 puntos | E_sensibles |
| `centros_educativos.geojson` | opendata.vlci · dataset | 0,28 MB · 534 puntos | E_sensibles |
| `manzanas_poblacion.geojson` | geoportal.valencia.es/apps/OpenData/UrbanismoEInfraestructuras/MANZANAS.json | 11,35 MB · 4.913 polígonos | Densidad poblacional precisa |

Reproducible con: `python scripts/descargar_capas.py`

## 3. Catastro INSPIRE Buildings · `data/external/catastro/` (no versionado)

Origen: Atom feed de la Dirección General del Catastro
`https://www.catastro.hacienda.gob.es/INSPIRE/buildings/46/ES.SDGC.BU.atom_46.xml`,
municipio 46900-VALENCIA.

| Archivo | Volumen | Contenido |
|---|---|---|
| `A.ES.SDGC.BU.46900.zip` | ~163 MB | ZIP comprimido del Atom feed |
| `A.ES.SDGC.BU.46900/building.gml` | ~340 MB | un polígono por edificio principal · `numberOfDwellings`, `numberOfBuildingUnits`, `currentUse` |
| `A.ES.SDGC.BU.46900/buildingpart.gml` | ~530 MB | un polígono por parte de edificio · `numberOfFloorsAboveGround` |
| `A.ES.SDGC.BU.46900/otherconstruction.gml` | (no se usa) | construcciones auxiliares |

Reproducible con: `python scripts/descargar_catastro.py`

## 4. Capas propias derivadas · `data/raw/`

| Archivo | Cómo se construye | Estado |
|---|---|---|
| `parques_bomberos.geojson` | `scripts/construir_parques_bomberos.py` · Nominatim + datos verificados de `valencia.es/cas/bomberos/parques/` | ✅ 6 parques · ver `parques_bomberos_FUENTES.md` |

## 5. Procesados · `data/processed/` (versionado salvo `.gpkg`)

| Archivo | Origen | Estado |
|---|---|---|
| `edificios_3d_valencia.gpkg` | `extraer_alturas_ciudad.py` sobre `buildingpart.gml` | ✅ 72 MB · 214.000 edificios reales · altura media 13,1 m · máxima 108 m (no versionado, regenerable) |
| `viviendas_por_barrio.csv` | `extraer_viviendas.py` sobre `building.gml` × `barris.geojson` | ✅ 88 barrios · 1.012.050 hab estimados (factor INE 2,4 hab/vivienda) |
| `catalogo_incendio.csv` | `filtrar_catalogo_incendio.py` sobre el dump CKAN | ✅ 130 datasets clasificados en 5 temas |

## 6. Documentos

| Archivo | Contenido |
|---|---|
| `docs/fuentes-encontradas.md` | Filtrado automático del catálogo CKAN por temas del dominio |
| `docs/hallazgos-exploracion.md` | IDs verificados del MapServer y ausencias significativas |
| `docs/modelo-riesgo.md` | Diseño del modelo paramétrico v0.1.1 |
| `data/raw/parques_bomberos_FUENTES.md` | Trazabilidad de la capa manual de parques |

## 7. Lo que aún no está

- **Cálculo batch de riesgo** para los 214.000 edificios: requiere el
  cruce de `edificios_3d_valencia.gpkg` con `parques_bomberos.geojson`,
  `hidrants.geojson` y `vulnerabilitat_barris.geojson`. Script
  `scripts/calcular_riesgo_batch.py` pendiente.
- **Frontend web**: aún no.
- **Año de construcción por edificio**: el Catastro INSPIRE no expone
  este campo de forma estructurada en sus GML; habría que extraerlo de
  la consulta SOAP de Catastro o cruzar con el censo del padrón. Por
  ahora el modelo usa el año como parámetro de escenario.
