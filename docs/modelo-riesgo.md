# Modelo paramétrico de riesgo de incendio residencial

> Versión 0.1 · 2026-05-14 · Documento de diseño.
> El código que implementa este modelo vive en
> `scripts/calcular_riesgo.py` (pendiente). Cualquier cambio del modelo
> debe versionarse aquí primero y reflejarse después en el código.

## 1. La pregunta

> ¿Cuál es el riesgo de incendio de tu edificio?

El modelo asigna a cada edificio residencial de València una
**puntuación de riesgo entre 0 y 100** y permite a la persona usuaria
**simular escenarios**: ¿qué pasa si la fachada es de aluminio
composite con núcleo combustible? ¿Y si la ITE está pendiente? ¿Y si
el incendio se produce a las 8 de la mañana en hora punta, con el
parque más cercano cubriendo otra intervención?

La puntuación es **una probabilidad relativa de daño grave**, no una
predicción absoluta. Compara edificios entre sí bajo las mismas
hipótesis.

## 2. Filosofía: lo conocido + escenarios sobre lo desconocido

El modelo combina **dos clases** de variables:

### 2.1 Conocidas (datos abiertos)

Aquellas que pueden derivarse de fuentes públicas sin necesidad de
inspección física:

- **Geometría y atributos catastrales** (`Catastro INSPIRE
  Buildings 46900`): año de construcción, número de plantas, número de
  viviendas, uso (`currentUse`).
- **Geometría territorial** (`barris.geojson`): asignación a barrio.
- **Vulnerabilidad social del barrio** (`vulnerabilitat_barris.geojson`):
  índice 2021 publicado por el Ajuntament.
- **Equipamientos sensibles cercanos** (residencias, hospitales,
  centros educativos, ya descargados): proximidad < 200 m amplifica el
  impacto.
- **Infraestructura de respuesta** (hidrantes municipales, fites bombers,
  parques de bomberos): distancia a cada uno.

### 2.2 Paramétricas (las decide la persona usuaria)

Los datos críticos que **no son abiertos** y por buenas razones
(privacidad, seguridad):

- **Tipo de fachada**: ladrillo · mortero · vidrio · composite con
  cumplimiento CTE · composite con núcleo combustible tipo ACM-PE
  (el caso Campanar).
- **Estado de la ITE**: favorable · pendiente · desfavorable.
- **Sistemas de protección contra incendios (SCI)**: completo
  (rociadores + detección + columna seca) · parcial · solo extintores ·
  ninguno.
- **Estado de la cubierta**: tradicional · mixto · combustible.
- **Hora del incidente**: franja horaria de 0-23 (afecta al tiempo de
  respuesta de los bomberos por el tráfico).
- **Saturación del parque más cercano**: libre · ocupado en otra
  intervención (en ese caso el segundo parque más cercano).

El producto **no almacena** las hipótesis de la persona usuaria sobre
edificios concretos. La simulación es local y efímera (criterio ético).

## 3. Componentes del índice de riesgo

El índice combina **tres dimensiones** mediante una media ponderada:

```
Riesgo = w_V · V_intrínseca + w_E · E_exposición + w_R · R_respuesta
con w_V + w_E + w_R = 1
```

### 3.1 V_intrínseca (vulnerabilidad del edificio · 0 a 100)

Mide cómo de combustible / propagador / colapsable es el edificio si
arde. Combina factores conocidos y paramétricos:

| Sub-factor | Tipo | Escala 0 (bajo) → 100 (alto) |
|---|---|---|
| Año de construcción (V_edad) | conocido | `> 2010` = 0 · `1980-2010` = 30 · `1950-1980` = 60 · `< 1950` = 100 |
| Altura del edificio (V_altura) | conocido | `≤ 3 plantas` = 10 · `4-7` = 40 · `8-12` = 70 · `> 12` = 100 |
| Tipo de fachada (V_fachada) | **paramétrico** | ladrillo = 0 · mortero = 10 · vidrio = 30 · composite-CTE = 60 · composite-ACM-PE = 100 |
| Estado ITE (V_ITE) | **paramétrico** | favorable = 0 · pendiente = 50 · desfavorable = 100 |
| Sistema SCI (V_SCI) | **paramétrico** | completo = 0 · parcial = 35 · solo extintores = 70 · ninguno = 100 |
| Cubierta (V_cubierta) | **paramétrico** | tradicional = 0 · mixto = 40 · combustible = 100 |

Combinación interna (pesos a refinar tras pruebas):

```
V_intrínseca = 0.10·V_edad + 0.15·V_altura + 0.30·V_fachada
             + 0.15·V_ITE  + 0.20·V_SCI    + 0.10·V_cubierta
```

**Por qué la fachada pesa 30 %**: la investigación post-Campanar
identifica la fachada combustible como el factor crítico que convierte
un incendio contenible en un incendio de propagación total.

### 3.2 E_exposición (impacto poblacional · 0 a 100)

Mide cuánta gente puede verse afectada y cuán vulnerable es:

| Sub-factor | Tipo | Escala |
|---|---|---|
| Densidad residencial estimada del barrio (E_densidad) | conocido | percentil sobre los 88 barrios de València |
| Vulnerabilidad social del barrio (E_vulnerab) | conocido | índice del dataset `vulnerabilitat_barris 2021` reescalado a 0-100 |
| Proximidad a equipamientos sensibles (E_sensibles) | conocido | 100 si hay residencia de mayores · 80 si hospital · 60 si centro educativo · 0 si nada · todo a < 200 m |

Combinación interna:

```
E_exposición = 0.40·E_densidad + 0.35·E_vulnerab + 0.25·E_sensibles
```

### 3.3 R_respuesta (penalización por respuesta de emergencia · 0 a 100)

Aquí entra el requisito clave: **el riesgo no es solo lo que arde,
sino lo que se tarda en apagarlo**. Cuanto más tarden los bomberos,
mayor es la probabilidad de que un incendio contenible se convierta
en colapso estructural y víctimas mortales.

| Sub-factor | Tipo | Escala |
|---|---|---|
| Tiempo estimado de llegada al edificio (R_tiempo) | conocido + paramétrico | ver §3.3.1 |
| Distancia al hidrante más cercano (R_hidrante) | conocido | < 50 m = 0 · 50-100 m = 30 · 100-200 m = 70 · > 200 m = 100 |
| Acceso preparado para vehículos pesados (R_acceso) | conocido | hay `fites bombers` o la calle es categoría de tráfico rodado normal = 0 · vía estrecha sin fites = 60 · zona peatonalizada sin fites = 100 |

Combinación interna:

```
R_respuesta = 0.65·R_tiempo + 0.20·R_hidrante + 0.15·R_acceso
```

#### 3.3.1 Modelización del tiempo de llegada

El tiempo de llegada estimado a un edificio se calcula así:

```
T_llegada(edificio, hora, escenario_saturación) =
    T_movilización
    + ( D_ruta(edificio, parque_efectivo) / V_efectiva(hora) )
```

con:

- **`T_movilización`** = 1,0 min (tiempo entre la alerta y la salida
  del vehículo, valor estándar para parques municipales urbanos).
- **`D_ruta`** = distancia por la red viaria desde el parque al
  edificio. Aproximación inicial: distancia euclidiana × 1,3
  (factor de tortuosidad típico de retículas urbanas mediterráneas).
  Refinamiento posterior con `velocitat_carrers` + grafo de calles.
- **`V_efectiva(hora)`** = velocidad media de los vehículos de
  emergencia a esa hora. Punto de partida:
  - Madrugada 00-06: 60 km/h
  - Hora punta mañana 07-09: 30 km/h
  - Mañana 10-13: 45 km/h
  - Mediodía 14-15: 40 km/h
  - Tarde 16-18: 40 km/h
  - Hora punta tarde 19-20: 30 km/h
  - Noche 21-23: 50 km/h
- **`parque_efectivo`** = el parque de bomberos más cercano salvo que
  el escenario marque saturación, en cuyo caso el segundo más
  cercano. Si el segundo también está saturado, el tercero.

#### 3.3.2 Mapeo tiempo → puntuación de riesgo

| `T_llegada` (min) | R_tiempo |
|---|---|
| ≤ 4 | 0 |
| 4 - 6 | 30 |
| 6 - 8 | 60 |
| 8 - 12 | 85 |
| > 12 | 100 |

Estos umbrales se alinean con la doctrina internacional de respuesta a
incendio estructural: la regla operativa de "primer chorro de agua en
8 minutos desde la alerta" es el límite por debajo del cual el incendio
todavía es contenible en su origen sin que comprometa la estructura.
A partir de 12 minutos, el riesgo de colapso estructural es alto.

## 4. Combinación final

Pesos de las tres dimensiones (punto de partida, sujetos a iteración):

```
Riesgo = 0.45·V_intrínseca + 0.30·E_exposición + 0.25·R_respuesta
```

### Justificación de los pesos

- **V_intrínseca 45 %**: la causa material es lo que enciende y
  propaga. Sin V_intrínseca alta, los otros factores son irrelevantes
  (no hay incendio).
- **E_exposición 30 %**: importante para la política pública
  (priorizar inspección en zonas con mayor impacto humano) pero
  secundario respecto al edificio.
- **R_respuesta 25 %**: factor modulador. No "crea" el incendio pero
  determina su gravedad final.

Estos pesos se documentan aquí para que el jurado y cualquier persona
auditora vea exactamente qué decisión metodológica se ha tomado, y
para que se puedan modificar fácilmente (`scripts/calcular_riesgo.py`
los lee desde una constante al principio del fichero).

## 5. Escenarios canónicos

El frontend ofrecerá **tres escenarios pre-configurados** además del
modo manual:

1. **"Edificio Campanar"** · 14 plantas · 2006 · fachada
   composite-ACM-PE · SCI parcial · ITE pendiente · cubierta mixta ·
   parque más cercano libre · 18:00 (hora real del incidente).
2. **"Edificio histórico Carmen"** · 5 plantas · 1920 · fachada
   ladrillo · sin SCI · ITE pendiente · cubierta combustible (madera) ·
   acceso por vía estrecha · 03:00 (hora baja).
3. **"Edificio nuevo Quatre Carreres"** · 8 plantas · 2020 · fachada
   cumple CTE · SCI completo · ITE favorable · 09:00 (hora punta).

El objetivo es que la persona usuaria compare estos tres anclajes y
después juegue con los parámetros para ver el efecto de cada decisión
constructiva o de mantenimiento.

## 6. Validación

El modelo se validará en tres direcciones:

1. **Test del caso Campanar**: con los parámetros del incidente real,
   el modelo debe arrojar un riesgo en la franja `[85, 100]`. Si no
   lo hace, los pesos son inadecuados.
2. **Sanidad por barrio**: la distribución de riesgos medios por
   barrio debe correlacionar (Pearson > 0,5) con el índice de
   vulnerabilidad publicado por el Ajuntament, manteniendo todos los
   parámetros constantes en su valor "intermedio".
3. **Sanidad por hora**: para un mismo edificio, el riesgo a las 8:00
   debe ser estrictamente mayor que a las 4:00 (efecto del tráfico
   en la respuesta).

Los tres tests viven en `tests/test_modelo.py` (pendiente).

## 7. Limitaciones que el jurado debe conocer

- **No es un dictamen técnico** para edificios concretos. Es una
  herramienta educativa y de priorización política. Cualquier decisión
  jurídica o de inspección debe basarse en peritaje físico.
- **Los pesos son arbitrarios** en su valor concreto, aunque
  justificados en su orden de magnitud. Refinarlos requeriría
  estadísticas históricas de siniestros que no son públicas.
- **La velocidad por hora del día** es una heurística, no un dato
  medido. La modelización detallada requeriría datos reales de
  movilidad por hora (`velocitat_carrers` solo da velocidad
  nominal por tramo, no por franja horaria).
- **No se modeliza** el viento, la temperatura ambiente, ni la
  hidráulica de la red contra incendios (presión, caudal). Son
  factores reales pero los datos abiertos no permiten introducirlos
  sin inventárselos.
- **El usuario no puede consultar el modelo sobre edificios concretos
  "qué fachada tiene"**. El producto no etiqueta edificios reales;
  solo permite explorar el espacio de escenarios.

## 8. Versionado y trazabilidad

Cada versión del modelo se identifica con la fecha de este documento
y un número de versión menor. El código de `calcular_riesgo.py`
referencia siempre la versión documentada aquí.

| Versión | Fecha | Cambio |
|---|---|---|
| 0.1 | 2026-05-14 | Diseño inicial del modelo (este documento) |
