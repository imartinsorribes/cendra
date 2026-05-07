# Anexo II · Memoria del proyecto cendra VLC

**Atlas paramétrico de riesgo de incendio residencial en València
con datos abiertos.**

> ¿Cuál es el riesgo de incendio de tu edificio?

---

## 0. Datos identificativos

| | |
|---|---|
| **Título del proyecto** | cendra VLC · Atlas paramétrico de riesgo de incendio residencial en València |
| **Categoría de la convocatoria** | Datos abiertos (procedimiento AD.TR.15) |
| **Edición** | IV Convocatoria de Premios para proyectos de datos abiertos y periodismo de datos del Ajuntament de València · 2026 |
| **Modalidad** | Individual |
| **Repositorio del código** | <https://github.com/imartinsorribes/cendra> |
| **URL pública del proyecto** | <https://cendra.pages.dev> |
| **Licencias** | Código fuente: MIT · Datos derivados: CC BY 4.0 · Memoria y documentación: CC BY 4.0 |

---

## 1. Por qué este proyecto

El 22 de febrero de 2024, un edificio residencial de 14 plantas en el
barrio de Campanar de València se incendió por completo en pocas horas.
Diez personas murieron, veintenas de familias perdieron su hogar y la
ciudad asumió una pregunta colectiva que no había estado en la agenda
pública: **¿cuántos edificios más podrían comportarse como aquel?**

Los informes técnicos posteriores identificaron tres factores
combinados: un sistema de fachada de aluminio composite con núcleo
combustible (tipo ACM-PE), un diseño constructivo que favoreció el
«efecto chimenea» y un tiempo de propagación del fuego que **superó
la capacidad de respuesta** de cualquier servicio operativo de
bomberos.

La pregunta tiene una respuesta científica que el Ayuntamiento, la
Conselleria, los bomberos y la ciudadanía necesitan poder explorar de
forma transparente, sin estigmatizar a edificios concretos y sin
exigir datos que por motivos legítimos (privacidad, seguridad) no
pueden ser abiertos.

**cendra VLC** propone esa respuesta con tres movimientos:

1. **Construir un modelo paramétrico** del riesgo de incendio
   residencial: en lugar de etiquetar a un edificio específico como
   «de alto riesgo», la herramienta deja a la persona usuaria
   introducir hipótesis sobre los datos no abiertos (fachada, ITE,
   sistema contra incendios, cubierta) y calcular qué riesgo
   resultaría bajo ese supuesto.
2. **Cruzar todo lo que sí es abierto**: 214.000 edificios del
   Catastro INSPIRE de València con su altura y año de construcción
   reales, los 1.923 hidrantes municipales, los 6 parques operativos
   del SPEIS, los 70 índices oficiales de vulnerabilidad social por
   barrio, los 62 centros sanitarios, los 534 centros educativos y
   los recursos sociales del Ajuntament.
3. **Modelar la respuesta de emergencia** en función de la hora del
   día, la distancia al parque más cercano y la posibilidad de que
   ese parque esté saturado en otra intervención. El modelo recoge
   explícitamente el aprendizaje de Campanar: en escenarios de
   fachada combustible en edificios altos, la respuesta deja de ser
   un atenuador efectivo y el modelo reasigna sus pesos en
   consecuencia.

---

## 2. Objetivos

### 2.1 Objetivo general

Producir un atlas digital público que combine los datos abiertos
disponibles en València con un modelo paramétrico de riesgo de
incendio residencial, accesible para tres audiencias simultáneas:

- **Las instituciones** (Ayuntamiento, Conselleria, SPEIS) como
  herramienta de priorización de campañas de inspección, mejora del
  protocolo de respuesta y orientación de la política de rehabilitación.
- **La ciudadanía** como herramienta de empoderamiento informativo
  sobre el riesgo de su propio edificio.
- **El tejido técnico y académico** (arquitectura, ingeniería,
  periodismo de datos) como referencia metodológica abierta y
  replicable.

### 2.2 Objetivos específicos

1. Documentar de forma trazable el estado actual de los datos abiertos
   municipales útiles para esta cuestión, incluyendo qué falta y qué
   sería deseable que el portal abriera.
2. Construir y publicar bajo licencia abierta un modelo paramétrico
   de riesgo replicable, no solo en València sino en cualquier
   ciudad con datos catastrales INSPIRE.
3. Generar derivados publicables (capa de parques operativos del
   SPEIS, agregados de riesgo medio por barrio) que devuelvan al
   ecosistema de datos abiertos información que no existía abierta
   antes del proyecto.
4. Ofrecer una herramienta web utilizable sin conocimientos técnicos
   previos que permita a cualquier persona ejecutar el modelo bajo
   sus propias hipótesis.

---

## 3. Metodología

### 3.1 Trazabilidad de las fuentes

Toda la cadena de datos del proyecto está documentada con su origen,
fecha de descarga, formato y licencia en
[`docs/inventario-datos.md`](../inventario-datos.md). El portal de
referencia es **`opendata.vlci.valencia.es`** (CKAN 2.10 del
Ajuntament de València). La descarga del catálogo entero se hace con
dos scripts reproducibles (`scripts/fetch_catalogo_vlci.py` y su
equivalente en PowerShell). El estado del portal a fecha del análisis
queda fijado en `data/raw/ckan_*.json` para auditabilidad.

Las fuentes complementarias son:

- **Catastro INSPIRE** de la Dirección General del Catastro
  (`datos.gob.es`), para los polígonos de edificios y sus atributos
  estructurales: número de plantas, número de viviendas, año de
  construcción y uso (residencial, industrial, etc.). 214.000
  edificios reales para el municipio 46900 de València.
- **Catálogo CKAN del Ajuntament**: 10 capas geoespaciales (hidrantes,
  fites para vehículos de bomberos, barrios oficiales, equipamientos
  municipales, centros para personas mayores, área de prioridad
  residencial, vulnerabilidad por barrios 2021, hospitales y centros
  sanitarios, centros educativos y manzanas con población).
- **Padrón Continuo INE 2023** para la calibración del factor de
  ocupación poblacional.

### 3.2 Pieza propia: ubicación de los parques de bomberos

El catálogo CKAN del Ajuntament publica los hidrantes y las «fites
bombers» (postes elastómeros para acceso de vehículos de emergencia)
pero **no publica la ubicación de los seis parques operativos del
SPEIS**. Las direcciones aparecen como contenido HTML en el portal
Infociudad pero no como dataset reutilizable.

El proyecto construye y publica esa capa bajo CC BY 4.0:

- Listado obtenido de la web oficial
  <https://www.valencia.es/cas/bomberos/parques/>.
- Dirección postal de cada parque verificada en su ficha individual
  de Infociudad.
- Geocodificación con Nominatim de OpenStreetMap, respetando su
  política de uso (1 petición/segundo, User-Agent identificable,
  bbox de descarte). Coordenadas verificadas dentro del bbox del
  término municipal.
- Trazabilidad completa en
  [`data/raw/parques_bomberos_FUENTES.md`](../../data/raw/parques_bomberos_FUENTES.md).

Esta capa es **devolución directa** al ecosistema de datos abiertos:
si el portal la incorporara mañana, este derivado quedaría obsoleto;
mientras tanto, está disponible para que cualquier otro proyecto la
reutilice citando la fuente.

### 3.3 El modelo paramétrico

La documentación completa del modelo vive en
[`docs/modelo-riesgo.md`](../modelo-riesgo.md) y está implementada en
[`scripts/calcular_riesgo.py`](../../scripts/calcular_riesgo.py)
(Python) y en [`web/modelo.js`](../../web/modelo.js) (JavaScript, para
la calculadora reactiva del frontend, manteniendo equivalencia literal
con la versión Python).

El modelo combina tres dimensiones del riesgo con una media
ponderada:

| Dimensión | Peso (normal) | Sub-factores |
|---|---:|---|
| **Vulnerabilidad intrínseca del edificio** | 45 % | edad, altura, fachada *, ITE *, sistema contra incendios *, cubierta * |
| **Exposición poblacional** | 30 % | densidad residencial del barrio, vulnerabilidad social, proximidad a residencias / hospitales / centros educativos |
| **Respuesta de emergencia** | 25 % | tiempo de llegada del parque más cercano (modulado por la hora del día), distancia al hidrante, accesibilidad de la calle |

Los sub-factores marcados con `*` son **paramétricos** porque sus
valores reales no son datos abiertos. La persona usuaria los fija
mediante la calculadora del frontend.

#### Régimen de pesos dinámico

El modelo incorpora una regla única y documentada que recoge el
aprendizaje de Campanar:

> Cuando la fachada se clasifica como combustible (composite con
> núcleo ACM-PE) **y** la altura del edificio amplifica el factor
> hasta saturar la vulnerabilidad intrínseca, los pesos se
> redistribuyen a (V=0,75 · E=0,20 · R=0,05).

La justificación física es directa: en un edificio alto con fachada
de revestimiento exterior combustible, el incendio se propaga más
rápido de lo que cualquier servicio de bomberos puede contener. El
informe del incidente de Campanar lo documenta: la unidad llegó al
parque inmediato en menos de 4 minutos y la torre estaba envuelta de
arriba a abajo antes de poder establecer un perímetro. En ese
régimen, la respuesta deja de ser un atenuador eficaz y el modelo lo
refleja matemáticamente.

#### Modelización del tiempo de respuesta

El tiempo de llegada del parque de bomberos se calcula como:

```
T = t_movilización + ( distancia_ruta / velocidad_efectiva(hora) )
```

donde la velocidad efectiva varía por franja horaria: 60 km/h en
madrugada, 30 km/h en hora punta, 40-50 km/h en horario regular. La
distancia por ruta se aproxima como euclidiana × 1,3 (factor de
tortuosidad típico de retículas urbanas mediterráneas). El proyecto
permite simular escenarios donde el parque más cercano está
saturado en otra intervención, en cuyo caso el modelo busca el
segundo más cercano y recalcula.

### 3.4 Validación

El modelo se valida con cuatro tests reproducibles:

1. **Caso Campanar**. Con los parámetros del incidente real
   (14 plantas · 2006 · ACM-PE · SCI parcial · ITE pendiente ·
   17:00 · parque al lado libre) el modelo debe arrojar un riesgo
   ≥ 80 / 100. **Resultado: 84,8** ✓
2. **Sensibilidad a la fachada**. El mismo edificio con fachada de
   ladrillo en lugar de ACM-PE debe bajar al menos un 30 %.
   **Resultado: 84,8 → 33,6 (-60 %)** ✓
3. **Sensibilidad horaria**. Un edificio lejano al parque más
   cercano (Borbotó, ≥ 6 km) debe mostrar riesgo mayor a las 8:00
   (hora punta) que a las 4:00 (madrugada). **Resultado: 28,4 →
   34,9 (+23 %)** ✓
4. **Orden de los tres escenarios canónicos** (Campanar, edificio
   histórico Centro, promoción nueva Quatre Carreres) coherente
   con la intuición técnica. ✓

Los cuatro tests viven en `scripts/validar_datos.py` y se pueden
re-ejecutar en cualquier momento.

### 3.5 Auditoría de los datos

El proyecto incluye una auditoría sistemática de todas las capas y
derivados (`scripts/validar_datos.py` + [`docs/validacion-datos.md`](../validacion-datos.md))
con comprobación de counts, geometrías, CRS, bbox, edge cases del
modelo y consistencia con cifras oficiales.

Durante la auditoría se detectaron y corrigieron tres bugs
metodológicos significativos:

- **Sobreestimación poblacional del +27,9 %** al aplicar
  inicialmente el factor INE de 2,4 habitantes por vivienda
  principal habitada sobre todas las viviendas catastradas
  (incluidas vacías, secundarias y en alquiler turístico).
  Calibrado empíricamente contra el padrón INE 2023 da un factor
  efectivo de 1,88 hab/vivienda catastrada. Tras la corrección la
  estimación queda en **+0,17 %** del padrón real.
- **Cero matches** en el cruce entre la capa de vulnerabilidad
  social y los barrios oficiales por usar identificadores con
  formato distinto (índice dentro de distrito vs código compuesto).
  Corregido a cruce por nombre normalizado: 84,5 % de los edificios
  reciben vulnerabilidad asignada; el resto son pedanías sin datos
  censales publicados.
- **Inversión del índice de vulnerabilidad** del dataset oficial:
  valor numérico bajo = vulnerabilidad alta (contraintuitivo).
  Verificado contra el campo de etiqueta categórica del propio
  dataset y reescalado correctamente.

La transparencia sobre estos errores y su corrección es deliberada:
forma parte del compromiso del proyecto con la calidad metodológica
auditable.

---

## 4. Resultados

### 4.1 Cálculo batch sobre los 214.000 edificios de València

El modelo se ejecuta sobre todos los edificios del Catastro bajo un
escenario por defecto (paramétricos en valores medios) en 17 segundos
con `scripts/calcular_riesgo_batch.py`. La distribución resultante:

- **Riesgo medio**: 41,6 / 100
- **σ entre edificios**: 6,3
- **Rango**: 20 - 59
- **88 barrios** con riesgo medio entre 25 y 52

### 4.2 Distribución por barrio

El top de barrios por riesgo medio (escenario por defecto):

| Barrio | Riesgo medio | Tiempo llegada bomberos | Comentario |
|---|---:|---:|---|
| Els Orriols | 51,8 | 4,3 min | Vulnerabilidad social alta + altura media 12 m |
| L'Amistat | 50,6 | 2,7 min | Buena cobertura pero stock antiguo |
| L'Illa Perduda | 50,5 | 4,4 min | Altura media 17 m |
| El Calvari | 50,3 | 3,2 min | Vulnerabilidad social oficialmente alta |
| Aiora | 49,9 | 4,3 min | Densidad + altura |
| Sant Marcel·lí | 49,6 | 5,1 min | |
| Betero | 49,4 | 4,4 min | Vulnerabilidad media |
| La Creu del Grau | 48,7 | 4,0 min | |
| Benifaraig | 47,7 | 10,0 min | Pedanía, tiempo de respuesta alto |
| Ciutat Jardí | 47,5 | 3,3 min | Altura media 23 m |

La señal del modelo es coherente con la información oficial: los
barrios catalogados como vulnerabilidad social alta por el propio
Ajuntament (El Calvari, Orriols) aparecen en el top, y las pedanías
penalizadas por tiempo de llegada elevado también.

---

## 5. La herramienta web

El frontend (`web/`) es una página HTML estática que sirve cualquier
servidor sin necesidad de backend ni base de datos. Combina:

- **MapLibre GL JS** como motor de mapas (libre, fork de Mapbox).
- **Base cartográfica CARTO Positron** (gratuita, sin clave de API).
- **Tres capas propias**: barrios coloreados por riesgo medio,
  parques de bomberos del SPEIS y los 2.000 edificios de mayor
  riesgo del batch (visibles a zoom 13 y superiores).
- **Calculadora paramétrica reactiva** que permite a la persona
  usuaria mover sliders de plantas, año, hora del día y elegir
  fachada / ITE / SCI / cubierta, viendo en directo cómo cambia el
  índice de riesgo y sus componentes V / E / R.
- **Tres escenarios canónicos pre-configurados**: el incidente real
  de Campanar, un edificio histórico de Centro en madrugada y una
  promoción nueva de Quatre Carreres en hora punta. Permiten
  comparar de un vistazo cómo afectan los distintos factores.

El modelo está implementado dos veces: una en Python para los
cálculos batch y la validación, y otra en JavaScript para la
calculadora del frontend. Ambas versiones comparten exactamente las
mismas constantes y la misma lógica matemática; un comentario en
cabecera de cada archivo advierte que deben mantenerse en
sincronización. Esta decisión deja todo el cálculo en el navegador,
evita la latencia de un backend y mantiene el proyecto desplegable
sobre cualquier hosting estático.

---

## 6. Innovación y originalidad · criterio 1

- **El modelo paramétrico como respuesta al dilema datos abiertos vs
  datos sensibles**. Es la decisión metodológica central: aceptar que
  los datos clave (fachada, ITE, SCI) no son abiertos y nunca podrán
  serlo plenamente, y construir un instrumento que igualmente
  informe rigurosamente la conversación pública sin etiquetar
  edificios concretos como «de alto riesgo».
- **Modelización del tiempo de respuesta por hora del día y por
  saturación del parque más cercano**. El factor R del modelo no es
  una constante sino una función explícita de la hora del incidente y
  de la posibilidad de que el parque adyacente esté cubriendo otra
  intervención. Es un grado de finura que no se encuentra en los
  pocos análisis previos sobre riesgo de incendio urbano publicados
  para municipios españoles.
- **Régimen dinámico de pesos**. El modelo no es lineal: cuando se
  cumplen las condiciones físicas que invalidaron la respuesta
  operativa en Campanar (fachada combustible en edificio alto), los
  pesos se redistribuyen para reflejar que la respuesta deja de ser
  un atenuador efectivo. La regla es única, documentada y trazable
  hasta el informe del incidente real.
- **Calculadora reactiva en navegador puro**. La persona usuaria no
  necesita instalar nada, registrarse ni esperar. Cada movimiento de
  un slider recalcula el índice en tiempo real porque el modelo
  vive embebido en la página.
- **Capa propia publicada**. La ubicación de los seis parques de
  bomberos del SPEIS no estaba abierta; el proyecto la construye y
  la libera para que cualquier otro análisis la reutilice.

---

## 7. Valor público e impacto · criterio 2

- **Relevancia social directa**. La cuestión de fondo —¿cuántos
  edificios de mi ciudad podrían comportarse como Campanar?— afecta
  a 791.000 personas empadronadas en València y al stock de 214.000
  edificios catastrales. No es un tema lateral, es la cuestión que
  ha marcado la agenda de seguridad residencial desde febrero de
  2024.
- **Empoderamiento ciudadano**. Cualquier persona con una conexión
  a internet puede consultar, sin intermediarios y sin credenciales,
  el riesgo asociado a las condiciones de su propio edificio. El
  proyecto desplaza la información del expediente técnico al
  conocimiento público.
- **Aporte a la rendición de cuentas**. La herramienta permite
  observar visualmente qué barrios concentran riesgo medio elevado y
  cuáles son los factores que lo impulsan. Es una pieza de trabajo
  que el periodismo de datos puede usar para sus análisis y que la
  ciudadanía puede invocar en cualquier interacción con sus
  representantes.
- **Apoyo a la toma de decisiones públicas**. El agregado por barrio
  es directamente aplicable a la priorización de campañas de
  inspección por parte de los servicios municipales: empieza por
  donde el riesgo medio del modelo es mayor. La capa publicada de
  parques de bomberos puede integrarse en cualquier sistema de
  información geográfica del Ayuntamiento o de la Conselleria.

---

## 8. Viabilidad, sostenibilidad y calidad · criterio 3

- **Trazabilidad completa**. Cada dato del proyecto puede
  rastrearse hasta su fuente original. Cada decisión metodológica
  está documentada en el repositorio. La cadena
  catálogo → descarga → procesado → modelo → frontend es
  reproducible íntegramente con los scripts del repositorio.
- **Reproducibilidad técnica**. Cualquier persona con Python 3.11 y
  los paquetes del archivo de dependencias puede regenerar todos
  los derivados ejecutando los ocho pasos documentados en el
  `README.md`. El proyecto entero se construye desde cero en menos
  de 20 minutos en un equipo doméstico.
- **Formatos abiertos en toda la cadena**. JSON, CSV, GeoJSON,
  GPKG, GML. Nada propietario.
- **Modularidad**. El modelo (`scripts/calcular_riesgo.py`) es una
  pieza independiente con una API clara. El batch (`calcular_riesgo_batch.py`)
  lo aplica a 214.000 edificios. El frontend lo replica en JS. Los
  tres pueden evolucionar por separado.
- **Validación con tests**. Cuatro pruebas de comportamiento del
  modelo y una auditoría sistemática de los datos verifican que la
  herramienta hace lo que dice.
- **Calibración con fuentes oficiales**. La estimación poblacional
  se calibra contra el padrón INE; los parques de bomberos se
  verifican con la web oficial del SPEIS; la vulnerabilidad social
  utiliza el índice publicado por el propio Ajuntament.
- **Continuidad y actualización**. Cuando el Ajuntament publique
  nuevos datasets o actualice los existentes, basta con re-ejecutar
  los scripts del pipeline para regenerar el atlas. La capa propia
  de parques de bomberos viene con un procedimiento documentado de
  refresco.

---

## 9. Carácter colaborativo y apertura · criterio 4

- **Licencias explícitas**. Código bajo MIT; datos derivados y
  documentación bajo CC BY 4.0. Cualquier persona puede usar,
  modificar y republicar el proyecto citando su fuente.
- **Publicación íntegra del código**. El repositorio en GitHub
  incluye el 100 % del código, los scripts, la documentación y las
  capas derivadas. El historial de cambios queda público.
- **Devolución al ecosistema de datos abiertos**. La capa de
  parques de bomberos, el agregado de riesgo por barrio y el CSV
  de viviendas/población por barrio son datasets nuevos que el
  proyecto pone a disposición del Ajuntament, otros proyectos y la
  ciudadanía. Cualquier servicio municipal puede incorporarlos.
- **Transparencia sobre los procesos**. La auditoría de datos
  documenta tres bugs detectados y corregidos durante el desarrollo;
  la metodología del modelo se publica antes que su implementación;
  las limitaciones se reconocen explícitamente.
- **Reutilización por terceros**. El modelo es replicable a
  cualquier otro municipio español con datos catastrales INSPIRE,
  recalibrando el factor de ocupación con el padrón local. La
  estructura del repositorio facilita el fork y la adaptación.
- **Apertura al diálogo**. El proyecto identifica explícitamente
  qué datasets municipales sería deseable que el Ajuntament
  publicara para mejorar el modelo (parques de bomberos como capa
  oficial, histórico anonimizado de tiempos de respuesta, año de
  construcción consolidado de Catastro), proponiendo así una agenda
  concreta de apertura de datos para próximas ediciones del portal.

---

## 10. Limitaciones reconocidas

El proyecto declara abiertamente sus limitaciones:

- **No es un dictamen técnico** para edificios concretos. Es una
  herramienta educativa y de priorización política. Cualquier
  decisión jurídica, urbanística o de inspección debe basarse en
  peritaje físico.
- Los **pesos del modelo** son valores defendibles en su orden de
  magnitud pero no son únicos. Refinar sus valores concretos
  requeriría un histórico estadístico de siniestros estructurales
  que no es público.
- La **velocidad por hora del día** es una heurística defendida
  con literatura general de movilidad urbana, no una medición
  directa para los vehículos del SPEIS. Si en una futura edición
  del portal apareciese un dataset de tiempos de respuesta
  históricos, el factor R del modelo podría reemplazarse por una
  función directamente aprendida de datos.
- El modelo **no introduce viento, temperatura ambiente ni
  hidráulica de la red de hidrantes** porque no se dispone de los
  datos correspondientes con suficiente granularidad. Son factores
  reales pero el modelo no pretende sustituir a la simulación
  ingenieril.
- **La asignación de equipamientos sensibles** usa una proximidad
  geométrica simple (radio 200 m) y un filtro por palabras clave
  para identificar residencias dentro del dataset municipal mixto;
  un dataset municipal específico de residencias geriátricas
  mejoraría esta dimensión.

---

## 11. Continuidad y mantenimiento

El proyecto se concibe como un instrumento vivo:

- El repositorio GitHub queda público tras la presentación del
  premio, con licencia que permite a cualquier persona forkearlo,
  modificarlo y proponer mejoras.
- Las dependencias técnicas son habituales y bien mantenidas
  (geopandas, MapLibre, NumPy). No hay riesgo de obsolescencia a
  corto plazo.
- La publicación se hace sobre un hosting estático
  (`Cloudflare Pages` o equivalente), gratuito y sin coste de
  mantenimiento operativo. La regeneración del atlas cuando el
  Ajuntament actualice sus datasets es trivial.
- El modelo está versionado (v0.1.1) y cada cambio futuro tendrá su
  entrada en el `CHANGELOG.md` del repositorio, con justificación
  metodológica.

---

## 12. Compromiso con la convocatoria

El proyecto se ha desarrollado siguiendo los principios y obligaciones
formales del procedimiento AD.TR.15:

- **Implantación local efectiva** en València: todos los datos, las
  fuentes y los resultados se refieren al municipio.
- **Lenguaje inclusivo y no sexista** en toda la documentación,
  código y contenido del frontend.
- **Autoría individual**.
- **Datos abiertos como pilar central** del proyecto, tanto en el
  consumo como en la devolución de derivados.
- **Transparencia sobre el proceso**, incluida la documentación
  abierta de los errores detectados y corregidos.
- **No haber recibido subvención previa** del Ayuntamiento por el
  mismo objeto.

---

## 13. Estructura del repositorio

```
cendraVLC/
├── README.md                · presentación e instrucciones
├── CHANGELOG.md             · historia de cambios versionada
├── LICENSE                  · MIT + nota CC BY 4.0
├── data/
│   ├── raw/                 · descargas crudas + parques manuales
│   ├── processed/           · derivados del análisis (CSV)
│   └── external/            · Catastro INSPIRE (no versionado)
├── scripts/                 · pipeline reproducible Python
├── docs/
│   ├── inventario-datos.md  · estado de todos los datasets
│   ├── fuentes-encontradas.md · catálogo CKAN clasificado por tema
│   ├── hallazgos-exploracion.md · IDs verificados y decisiones
│   ├── modelo-riesgo.md     · diseño del modelo paramétrico
│   ├── validacion-datos.md  · auditoría de calidad
│   └── memoria/             · este documento
├── web/
│   ├── index.html           · estructura del atlas
│   ├── style.css            · paleta brasa/ceniza
│   ├── modelo.js            · modelo replicado en JS
│   ├── app.js               · mapa + reactividad
│   └── data/                · GeoJSON optimizados que sirve la web
└── notebooks/               · análisis exploratorios
```

---

_Memoria preparada con el modelo de Anexo II indicado en la
convocatoria. Toda la información presentada es reproducible y
auditable desde el repositorio público referenciado en la primera
sección._
