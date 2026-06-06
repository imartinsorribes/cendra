# Guión del vídeo de presentación · 60 segundos

Pensado para grabar con OBS o el grabador del navegador, con voz en off
encima de la pantalla. Castellano, tono claro y directo, lenguaje
inclusivo. Cada bloque indica qué se ve en pantalla y qué se dice.

Total: 60 segundos · 7 escenas · ~165 palabras de narración (~2,7 palabras/s).

---

## Escena 1 · 0:00 → 0:08 (8 s) · Hook

**Pantalla**: la home de `cendra.pages.dev` con el mapa de barrios de
València coloreado por riesgo. Cerrar el tutorial de bienvenida si
aparece.

**Voz en off**:
> «En febrero de 2024 ardió un edificio en Campanar. Diez personas
> murieron. La fachada tardó siete minutos en propagar el fuego
> de planta a planta.»

---

## Escena 2 · 0:08 → 0:16 (8 s) · La pregunta

**Pantalla**: zoom hacia el barrio de Campanar / Aiora con el mapa
ya cargado.

**Voz en off**:
> «¿Cuántos edificios más en València comparten ese perfil de riesgo?
> Hasta ahora, nadie tenía la respuesta abierta y comprobable.»

---

## Escena 3 · 0:16 → 0:26 (10 s) · La herramienta

**Pantalla**: cambio a la vista «Propuestas». Mostrar la cifra grande
«154 edificios cumplen el perfil Campanar».

**Voz en off**:
> «cendra es un atlas paramétrico construido con datos abiertos del
> Ajuntament y del Catastro. Identifica los 154 edificios de la
> ciudad que comparten el perfil de Campanar: diez plantas o más
> y construidos entre el año 2000 y 2017, la era del composite
> con núcleo combustible.»

---

## Escena 4 · 0:26 → 0:38 (12 s) · La interacción

**Pantalla**: vuelta a la vista «Análisis». Hacer zoom a la zona de
Aiora. Click en un polígono dorado (candidato Campanar). Mostrar el
panel derecho rellenando los valores reales y el bloque «Por qué
este riesgo».

**Voz en off**:
> «Cualquier persona puede hacer click en su edificio y ver no solo
> su riesgo simulado, sino exactamente por qué: qué pesa más, qué
> pesa menos, y cómo se propagaría el fuego según la fachada y la
> cubierta.»

---

## Escena 5 · 0:38 → 0:48 (10 s) · La simulación

**Pantalla**: cambiar el slider «Fachada» de combustible a no
combustible. La cifra del riesgo cae visiblemente del rango 60-70 al
rango 35-45.

**Voz en off**:
> «Y puede simular: si esta fachada se sustituyera por una no
> combustible, el riesgo del edificio bajaría a la mitad. Esta cifra
> es lo que cuesta una decisión municipal.»

---

## Escena 6 · 0:48 → 0:55 (7 s) · La acción

**Pantalla**: vuelta a vista «Propuestas». Mostrar la tabla de los
154 candidatos, hacer scroll y resaltar el botón «Descargar CSV».

**Voz en off**:
> «La lista de los 154 edificios es descargable en CSV. Cualquier
> técnico municipal puede usarla mañana para empezar las inspecciones.»

---

## Escena 7 · 0:55 → 1:00 (5 s) · Cierre

**Pantalla**: zoom out al título grande con la URL del proyecto
visible.

**Voz en off**:
> «cendra punto pages punto dev. Los datos abiertos no sirven si
> no los cruzamos.»

---

## Notas de producción

- **Resolución de grabación**: 1920×1080. Zoom del navegador al 110 %
  para que el texto se lea bien comprimido en YouTube / vídeo del
  jurado.
- **Audio**: voz en off limpia, sin música de fondo (más serio para un
  proyecto técnico). Si añades música, que sea ambiental muy baja
  (-25 dB).
- **Cursor**: si OBS / Loom permiten resaltar el cursor, actívalo.
  Ayuda a seguir los clicks.
- **Recortes**: que no se vean URLs personales (history del navegador)
  ni notificaciones. Pestaña incógnita o ventana limpia.
- **Subtítulos**: añadirlos en post (.srt). El jurado puede que vea
  el vídeo sin sonido.
- **Cierre con frame fijo**: los últimos 2-3 segundos pueden ser un
  frame fijo con la URL grande y el lema, da tiempo a que se quede
  grabado.

## Checklist antes de grabar

- [ ] Cerrado el tutorial de bienvenida (`localStorage.setItem('cendra_tutorial_visto_v1', '1')`).
- [ ] Limpiado el caché del navegador para que los cambios recientes
  se carguen (Ctrl+F5).
- [ ] Probado que el deploy actual de `cendra.pages.dev` muestra los
  últimos cambios (puntos coherentes con polígonos, explicador de
  riesgo, vista Propuestas).
- [ ] Pestaña incógnita y ventana maximizada.
- [ ] Bandeja de notificaciones del sistema en silencio.
- [ ] Practicar la narración una vez en voz alta para ajustar el ritmo
  a los 60 segundos exactos.

## Versión cortada (30 segundos)

Si necesitas una versión más corta para redes sociales:

- Mantener escenas 1, 4 y 5 (hook, interacción, simulación).
- Recortar la voz en off a unas 75 palabras.
- Acabar con la URL en pantalla.
