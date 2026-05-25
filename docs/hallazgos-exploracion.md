# Hallazgos de la exploración del catálogo · 2026-05-14

Notas manuales que complementan a [`fuentes-encontradas.md`](fuentes-encontradas.md)
(generado automáticamente). Aquí queda lo que requiere interpretación
humana: identificación de IDs concretos del MapServer del geoportal,
ausencias significativas, decisiones metodológicas.

## 1. Datasets nucleares confirmados

Dos datasets del catálogo CKAN se relacionan directamente con la
respuesta a incendios. Ambos están publicados por el propio Ajuntament
de València bajo licencia CC BY 4.0.

### 1.1 Hidrantes municipales

- **Dataset**: `hidrants-per-als-bombers`
- **Endpoint estable (GeoJSON)**:
 `https://geoportal.valencia.es/server/rest/services/OPENDATA/UrbanismoEInfraestructuras/MapServer/222/query?where=1=1&outFields=*&f=geojson`
- **Última actualización portal**: 2026-02-19
- **Volumen esperado**: ~1.923 hidrantes municipales según
 documentación previa.
- **Uso en el modelo**: factor "distancia al hidrante más cercano".
 Cuanto mayor la distancia, mayor el riesgo de propagación una vez
 iniciado el incendio.

### 1.2 Fites Bombers (postes flexibles)

- **Dataset**: `fites-bombers-hitos-bomberos`
- **Endpoint estable (GeoJSON)**:
 `https://geoportal.valencia.es/server/rest/services/OPENDATA/Trafico/MapServer/239/query?where=1=1&outFields=*&f=geojson`
- **Última actualización portal**: 2026-02-18
- **Descripción**: postes de material elastómero que flexionan 90º
 para permitir el paso de vehículos de bomberos a calles
 semipeatonalizadas.
- **Uso en el modelo**: marcador de calles preparadas para acceso de
 emergencia; complementario al análisis de tiempo de respuesta.

## 2. Ausencia significativa · parques de bomberos

**No existe en el catálogo CKAN un dataset con la ubicación de los
parques de bomberos de València.** Comprobado en dos sentidos:

1. El filtrado por keywords (`bomber|incendi|emergència|protecció civil`)
 solo devuelve hidrantes y fites; ningún punto de servicio.
2. El dataset `equipamients-municipals-equipamientos-municipales`
 tiene 2.915 puntos clasificados en 19 categorías (`clase`):
 `Bienestar Social`, `Instalaciones educativas`, `Instalaciones
 sanitarias`, `Policía`, `Bibliotecas`, `Mercados`, `Museos`,
 `Centros juveniles`, `Oficinas municipales`, `Puntos de venta EMT`,
 `Teatros`, `Archivos`, `Alojamiento`, `Correos`, `Oficina
 información turística`, `Zonas de escolarización`, `Sin clase Mapa`,
 `invisible`, e `Instalaciones deportivas`. **Ninguna clase corresponde
 a parques de bomberos.**

### Decisión metodológica

El proyecto construirá una **capa propia** `data/raw/parques_bomberos.geojson`
con la ubicación de los parques del Servicio de Prevención, Extinción de
Incendios y Salvamento (SPEIS) del Ajuntament de València más los
parques del Consorcio Provincial dentro del término municipal. Las
fuentes serán:

- Web oficial del SPEIS de l'Ajuntament de València.
- Memoria anual del SPEIS (datos públicos pero no abiertos).
- Consorcio Provincial de Bomberos de València.

Cada punto llevará atributos: nombre del parque, dirección, año de
puesta en servicio (si es público), fuente concreta del dato y fecha
de consulta. La capa irá acompañada de un archivo `FUENTES.md` con la
trazabilidad. Esto cumple con el criterio 3 de la convocatoria
(trazabilidad) y con el 4 (apertura de datos derivados que el portal
no ofrece).

## 3. Datasets clave para el modelo: IDs y endpoints

Tabla de los identificadores del MapServer del geoportal, ya
verificados con `?f=json` para cada uno. Esto entra directamente en
`scripts/descargar_capas.py`.

| Capa | Servicio MapServer | Layer ID | Fichero salida | Uso en el modelo |
|---|---|---:|---|---|
| Hidrantes | UrbanismoEInfraestructuras | 222 | `hidrants.geojson` | Distancia al hidrante |
| Fites bombers | Trafico | 239 | `fites_bombers.geojson` | Accesibilidad emergencia |
| Edificios municipales | UrbanismoEInfraestructuras | 112 | `edificis.geojson` | Geometría base |
| Barris | UrbanismoEInfraestructuras | 224 | `barris.geojson` | Agregación territorial |
| Equipamientos municipales | SociedadBienestar | 1 | `equipamientos.geojson` | Equipamientos sensibles (filtrar por `clase`) |
| Residencias mayores | SociedadBienestar | 24 | `majors.geojson` | Vulnerabilidad poblacional |
| Área Prioridad Residencial | Trafico | 1 | `area_prioridad_residencial.geojson` | Calles con tráfico limitado |

Endpoints legacy (no MapServer numérico, GeoJSON estático):

| Capa | Endpoint | Fichero salida | Uso |
|---|---|---|---|
| Vulnerabilidad por barrios 2021 | `opendata.vlci.valencia.es/.../vulnerabilidad-por-barrios.geojson` | `vulnerabilitat_barris.geojson` | Factor de impacto social |
| Hospitales y centros sanitarios 2024 | `opendata.vlci.valencia.es/.../hospitales.geojson` | `hospitales.geojson` | Equipamientos sensibles |
| Centros educativos | `opendata.vlci.valencia.es/.../centros-educativos-en-valencia.geojson` | `centros_educativos.geojson` | Equipamientos sensibles |
| Manzanas con población | `geoportal.valencia.es/apps/OpenData/UrbanismoEInfraestructuras/MANZANAS.json` | `manzanas_poblacion.geojson` | Densidad poblacional residencial |

## 4. Hallazgo lateral · "Recursos socials dirigits a majors"

El dataset `recursos-socials-dirigits-a-majors` está publicado pero
con un endpoint legacy (`/apps/OpenData/SociedadBienestar/SS_MAYORES.json`)
y también vía WFS. Combinado con `majors-mayores` (MapServer/24) cubre
**residencias y centros de día para personas mayores**, que son los
equipamientos de máxima vulnerabilidad en caso de incendio
(movilidad reducida, dependencia, dificultad de evacuación). Conviene
descargar ambos y deduplicar por coordenadas.

## 5. Limitaciones reconocidas del catálogo

- **No hay tiempo de respuesta histórico** de los bomberos a
 intervenciones. Solo el dataset `Número de incidències` (`is_sct_230307`,
 formato CSV) pero su contexto no se ha verificado.
- **No hay padrón a nivel manzana** ni a nivel edificio. La densidad
 poblacional se estimará desde Catastro INSPIRE (`numberOfDwellings`)
 con el factor 2,4 hab/vivienda (INE Encuesta Continua de Hogares
 València 2021).
- **No hay datos de ITE** (Inspección Técnica de Edificios) abiertos.
 Es el motivo principal de pasar a un modelo paramétrico donde la
 persona usuaria propone el escenario "ITE realizada / pendiente".
- **No hay materiales de fachada** abiertos. Igual que ITE, entra como
 variable paramétrica.
