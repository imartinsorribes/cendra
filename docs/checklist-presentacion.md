# Checklist del día de la presentación (5 jun 2026)

Última fecha de revisión: 6 jun 2026.

## Antes de la presentación

- [ ] **Hacer el repositorio público** en GitHub
  - <https://github.com/imartinsorribes/cendra/settings>
  - Sección «Danger Zone» → «Change repository visibility» → Public
  - Confirma que los enlaces del README y de la vista «Propuestas»
    (`https://github.com/imartinsorribes/cendra`) responden 200.

- [ ] **Verificar el deploy** en `https://cendra.pages.dev`
  - El último commit del `main` debe estar reflejado (Cloudflare Pages
    suele tardar ~1-2 min después del push).
  - Probar en una pestaña de incógnito para evitar caché del navegador.

- [ ] **Probar en móvil con datos** (no Wi-Fi del Ajuntament)
  - Tiempo de carga aceptable (< 5 s para ver el primer riesgo).
  - El mapa carga sin clavarse.
  - El cambio entre vistas Análisis ↔ Propuestas es fluido.

- [ ] **Comprobar los tests** localmente: `python -m pytest tests/ -q`
  (deben pasar los 40 en menos de 2 s).

- [ ] **Repasar la memoria** del Anexo II
  (`docs/memoria/anexo-ii.md`): que las cifras (36.300 edificios únicos,
  154 candidatos Campanar, 1.923 hidrantes, 6 parques, 40 tests) sean
  consistentes con lo que dice la web.

## Material para llevar

- [ ] La URL `cendra.pages.dev` impresa o en una nota visible.
- [ ] Un dispositivo de respaldo (móvil o tablet) por si la presentación
  principal falla.
- [ ] El CSV de los 154 candidatos descargado offline
  (`web/data/candidatos_campanar_completo.json` o exportarlo desde la
  vista Propuestas) por si quieren los datos sin acceso a internet.

## Demo en vivo (si la hay): camino sugerido

1. Abrir `cendra.pages.dev`. Cerrar el tutorial de bienvenida.
2. Mostrar el mapa coroplético por barrios (Aiora, Calvari, Sant Antoni
   en rojo brasa).
3. Hacer zoom hasta zoom 16 sobre Campanar / Aiora: aparecen los
   polígonos del Catastro con los bordes dorados de los candidatos.
4. Click en un polígono dorado: rellena los sliders con los valores
   reales del edificio. Mostrar el bloque «Por qué este riesgo» y la
   línea «Cómo se propagaría».
5. Cambiar el slider «Fachada» de combustible a no combustible: el
   riesgo cae del rango 60-70 al rango 35-45. Aquí es donde se ve el
   valor del modelo paramétrico.
6. Pulsar «Resetear simulación» → vuelve al centro de València.
7. Cambiar a vista «Propuestas».
8. Mostrar la cronología (Lacrosse, Address, Grenfell, Mocejón,
   Campanar) y la tabla de los 154 candidatos. Filtrar por barrio
   (`marxal`, `aiora`) y descargar el CSV.

## Después de la presentación

- [ ] Si gana, agradecer y subir un commit con la nota.
- [ ] Mantener el repo público y la web online: el atlas tiene valor
  más allá del concurso.
