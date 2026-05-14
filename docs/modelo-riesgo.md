# Modelo paramétrico de riesgo de incendio residencial

> Versión 0.2.1 · 2026-05-22 · Documento de diseño.
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
| Año de construcción (V_edad) | conocido | `post-2017` = 0 (RIPCI revisado) · `2006-2017` = 20 (CTE DB-SI) · `1991-2006` = 50 (NBE-CPI-91) · `pre-1991` = 100 (sin normativa) |
| Altura del edificio (V_altura) | conocido | Función continua: `min(100, plantas × 7)`. Captura el efecto chimenea sin saltos abruptos |
| Tipo de fachada (V_fachada) | **paramétrico** | ladrillo = 0 · mortero = 10 · vidrio = 30 · composite-CTE = 60 · **sate-combustible = 80** · composite-ACM-PE = 100 |
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

Mide cuánta gente puede verse afectada y cuán vulnerable es. Desde v0.2
modula además por **ocupación efectiva del edificio** según uso y hora:

| Sub-factor | Tipo | Escala |
|---|---|---|
| Densidad residencial estimada del barrio (E_densidad) | conocido | percentil sobre los 88 barrios de València |
| Vulnerabilidad social del barrio (E_vulnerab) | conocido | índice del dataset `vulnerabilitat_barris 2021` reescalado a 0-100 |
| Proximidad a equipamientos sensibles (E_sensibles) | conocido | 100 si hay residencia de mayores · 80 si hospital · 60 si centro educativo · 0 si nada · todo a < 200 m |

Combinación interna:

```
E_exposición = (0.40·E_densidad + 0.35·E_vulnerab + 0.25·E_sensibles) × factor_ocupación(uso, hora)
```

El **factor de ocupación** reconoce que un edificio residencial a las
3 AM tiene 1,0 (todos durmiendo) mientras que un edificio de oficinas
a la misma hora tiene 0,1 (vacío). Y al revés a las 11:00. Se aplica
cuando el `currentUse` del Catastro está disponible (99,8 % de los
edificios).

### 3.3 R_respuesta (penalización por respuesta de emergencia · 0 a 100)

Aquí entra el requisito clave: **el riesgo no es solo lo que arde,
sino lo que se tarda en apagarlo**. Cuanto más tarden los bomberos,
mayor es la probabilidad de que un incendio contenible se convierta
en colapso estructural y víctimas mortales.

| Sub-factor | Tipo | Escala |
|---|---|---|
| Tiempo estimado de llegada al edificio (R_tiempo) | conocido + paramétrico | ver §3.3.1 |
| Distancia al hidrante más cercano (R_hidrante) | conocido | < 50 m = 0 · 50-100 m = 30 · 100-200 m = 70 · > 200 m = 100 |
| Acceso preparado para vehículos pesados (R_acceso) | conocido | hay `fites bombers` a < 50 m = 0 · calle normal = 30 (default) |

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

### Régimen normal

Pesos de las tres dimensiones cuando ningún factor está saturado:

```
Riesgo = 0.45·V_intrínseca + 0.30·E_exposición + 0.25·R_respuesta
```

Justificación:

- **V_intrínseca 45 %**: la causa material es lo que enciende y
  propaga. Sin V_intrínseca alta, los otros factores son irrelevantes
  (no hay incendio).
- **E_exposición 30 %**: importante para la política pública
  (priorizar inspección en zonas con mayor impacto humano) pero
  secundario respecto al edificio.
- **R_respuesta 25 %**: factor modulador. No "crea" el incendio pero
  determina su gravedad final.

### Régimen «fachada crítica»

Cuando la fachada se clasifica como combustible (`composite-acmpe`)
**y** su valor amplificado por altura satura V_intrínseca al 100, los
pesos se redistribuyen así:

```
Riesgo = 0.75·V_intrínseca + 0.20·E_exposición + 0.05·R_respuesta
```

Justificación física: en un edificio alto con fachada combustible, el
incendio se propaga por el revestimiento exterior a una velocidad que
**supera la capacidad de respuesta operativa de cualquier servicio de
bomberos**. La investigación post-Campanar lo documenta: los bomberos
llegaron en menos de 5 minutos al edificio Maravillas y la torre quedó
envuelta de arriba a abajo antes de que pudieran establecer un perímetro.

En este régimen:

- la respuesta deja de ser un atenuador eficaz (peso baja del 25 % al
  5 %);
- la exposición poblacional sigue importando porque determina las
  víctimas, pero cede peso a la vulnerabilidad estructural (del 30 %
  al 20 %);
- la vulnerabilidad intrínseca pasa a ser el factor dominante (45 %
  → 75 %).

Esta regla es **explícita y única** del modelo: un único «interruptor»
documentado, no una colección de casos especiales ad hoc. El régimen
aplicado en cada cálculo se reporta en el campo `pesos.regimen` del
resultado.

### Una sola constante a tocar

Los seis pesos del modelo (`W_VULN`, `W_EXP`, `W_RESP` × dos regímenes)
viven en las primeras líneas de `scripts/calcular_riesgo.py`. Cambiarlos
afecta a todos los cálculos posteriores sin tocar el resto del código.

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

El modelo se validará en cuatro direcciones:

1. **Test del caso Campanar**: con los parámetros del incidente real,
   el modelo debe arrojar un riesgo `≥ 80`. Esto significa que cae en
   el quintil superior de la escala. No exigimos `= 100` porque un
   edificio con fachada ACM-PE Y sin ningún sistema SCI Y con ITE
   desfavorable Y en zona ultra-vulnerable representa un caso aún
   peor; la escala debe dejar margen para distinguir los dos.
2. **Test de sensibilidad a la fachada**: un edificio idéntico al de
   Campanar pero con fachada de ladrillo debe arrojar al menos
   **30 % menos de riesgo**. Esto demuestra que la variable más crítica
   del modelo (la fachada) realmente domina cuando se activa.
3. **Sanidad por barrio**: la distribución de riesgos medios por
   barrio debe correlacionar (Pearson > 0,5) con el índice de
   vulnerabilidad publicado por el Ajuntament, manteniendo todos los
   parámetros constantes en su valor «intermedio».
4. **Sanidad por hora**: para un edificio **lejano** del parque más
   cercano (distancia euclidiana ≥ 3 km), el riesgo en hora punta
   (08:00 o 20:00) debe ser estrictamente mayor que en madrugada
   (04:00). Para edificios próximos a un parque, ambos tiempos pueden
   caer bajo el umbral mínimo (`≤ 4 min`) y la hora deja de discriminar
   — esto es realista: cerca del parque la respuesta es robusta a la
   hora del día. Bajo régimen de fachada crítica, esta sensibilidad es
   pequeña en cualquier caso porque la respuesta pesa solo el 5 %.

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

## 8. Extensiones derivadas del modelo (v0.2.1)

### 8.1 Motor de recomendaciones

Para cualquier edificio simulado, el modelo identifica las **tres
mejoras paramétricas con mayor reducción de riesgo**. El algoritmo
prueba, manteniendo todo lo demás constante, cada valor mejor que el
actual para fachada, ITE, SCI y cubierta, y devuelve las tres
variables con mayor caída ordenadas por impacto.

Cuando el edificio está en régimen «fachada crítica», las otras
mejoras (ITE, SCI, cubierta) tienen efecto cuasi nulo porque
V_intrínseca queda saturada por la fachada. El motor reconoce esto
explícitamente y añade una nota al usuario: *«mientras la fachada
combustible persista, las demás mejoras no reducen significativamente
el riesgo»*.

### 8.2 Banda de confianza

Cada cálculo se acompaña de su rango plausible: el riesgo bajo el
**mejor caso paramétrico** (todas las variables paramétricas en su
óptimo) y el **peor caso paramétrico** (todas al extremo). Sirve para
comunicar que el modelo es una estimación, no un veredicto.

### 8.3 Plan de respuesta operativa del SPEIS

Para cualquier edificio, el modelo estima el despliegue de bomberos
necesario en caso de incendio:

- **Dotaciones y efectivos** según altura (1 dotación ≤ 3 plantas,
  hasta 4-5 si fachada combustible + altura > 14).
- **Vehículos**: BUL, BUP, autoescala, UEMSV, refuerzo provincial.
- **Caudal hidráulico**: 500 L/min por dotación + 30 % de reserva.
- **Tiempo estimado de contención**: 8 min base + 4 min por planta
  > 5, duplicado si fachada combustible (aprendizaje de Campanar).
- **Radio de evacuación inmediata**: 50-100 m según altura.
- **Radio del perímetro operativo**: el doble del de evacuación.

Es una heurística basada en doctrina común de respuesta a incendio
estructural urbano, **no es protocolo oficial del SPEIS**. Sirve para
que la persona usuaria visualice qué implica «que arda»: el atlas
pasa de diagnóstico (riesgo X) a acción (despliegue Y).

## 9. Versionado y trazabilidad

Cada versión del modelo se identifica con la fecha de este documento
y un número de versión menor. El código de `calcular_riesgo.py`
referencia siempre la versión documentada aquí.

| Versión | Fecha | Cambio |
|---|---|---|
| 0.1 | 2026-04-22 | Diseño inicial del modelo (este documento) |
| 0.1.1 | 2026-04-24 | Régimen de pesos dinámico cuando la fachada satura V_intrínseca. Test del caso Campanar relajado a `≥ 80` y añadido test de sensibilidad a la fachada |
| 0.2 | 2026-05-14 | Cortes normativos del año (NBE-CPI-91, CTE DB-SI, RIPCI). v_altura continua. Nueva fachada `sate-combustible`. R_acceso real con `fites_bombers` a <50 m. Modulación de E_exposición por `uso × hora` con el `currentUse` del Catastro. Régimen «fachada crítica» se activa siempre que la fachada combustible esté presente, no solo cuando el piso eleva V |
| 0.2.1 | 2026-05-22 | Motor de recomendaciones top-3 con explicación cuando la fachada combustible domina. Banda de confianza (mejor caso / peor caso paramétrico). Plan de respuesta operativa estimado del SPEIS (dotaciones, vehículos, caudal hidráulico, tiempo de contención, perímetro de evacuación) |
