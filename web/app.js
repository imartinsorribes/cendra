/*
 * cendra VLC · aplicación del atlas
 *
 * Tres responsabilidades:
 *   1. Inicializar el mapa MapLibre con base CARTO Positron + capas propias.
 *   2. Recoger los valores de los controles del panel y, a cada cambio,
 *      llamar al modelo (modelo.js) para recalcular el riesgo.
 *   3. Al hacer click en un barrio o en un escenario canónico, propagar
 *      los valores a los controles y al modelo.
 */

const M = window.cendraModelo;

const inputs = {
  plantas: document.getElementById('plantas'),
  anio: document.getElementById('anio'),
  uso: document.getElementById('uso'),
  fachada: document.getElementById('fachada'),
  ite: document.getElementById('ite'),
  sci: document.getElementById('sci'),
  cubierta: document.getElementById('cubierta'),
  hora: document.getElementById('hora'),
  saturacion: document.getElementById('saturacion'),
};
const outputs = {
  plantas: document.getElementById('plantas_val'),
  anio: document.getElementById('anio_val'),
  hora: document.getElementById('hora_val'),
};

const resultado = {
  total: document.getElementById('riesgo_total'),
  delta: document.getElementById('riesgo_delta'),
  baseline: document.getElementById('baseline_val'),
  barra: document.getElementById('barra_relleno'),
  V: document.getElementById('V_val'),
  E: document.getElementById('E_val'),
  R: document.getElementById('R_val'),
  V_bar: document.getElementById('V_bar'),
  E_bar: document.getElementById('E_bar'),
  R_bar: document.getElementById('R_bar'),
  contexto: document.getElementById('contexto'),
};

// Devuelve un color hex de la escala verde-amarillo-brasa según el valor 0-100
function colorPorValor(v) {
  if (v == null || isNaN(v)) return '#cccccc';
  if (v < 25) return '#6e9d4c';
  if (v < 35) return '#b8c155';
  if (v < 45) return '#f5b400';
  if (v < 55) return '#e57a37';
  return '#b03a1d';
}

// Baseline: el valor del riesgo en cuanto cargó la página. El delta
// del cuadro se compara contra esto, no contra el cambio anterior.
let _riesgoBaseline = null;

// Snapshot de los valores iniciales de los controles para que «Resetear
// simulación» pueda volverlos a poner.
const _valoresIniciales = {};

// Estado: ubicación del edificio (centro del mapa al inicio) y datos de barrio
let estado = {
  lon: -0.376,
  lat: 39.470,
  barrio_vuln: 50,
  densidad: 50,
  equip_sensibles: 'ninguno',
  barrio_nombre: null,
  hidrantes_cargados: null,  // FeatureCollection cargado al inicio
};

// === MAPA ===================================================================

const map = new maplibregl.Map({
  container: 'mapa',
  style: 'https://basemaps.cartocdn.com/gl/positron-gl-style/style.json',
  center: [-0.376, 39.470],
  zoom: 12,
  hash: false,
});
map.addControl(new maplibregl.NavigationControl({ visualizePitch: false }), 'top-left');
map.addControl(new maplibregl.AttributionControl({
  customAttribution: 'cendra VLC · CC BY 4.0 · datos del Ajuntament de València y Catastro INSPIRE',
}));

// Escala de color para el riesgo (verde-amarillo-rojo brasa)
function colorRiesgo(campo = 'riesgo_medio') {
  return [
    'interpolate', ['linear'], ['number', ['get', campo], 0],
    25, '#6e9d4c',
    35, '#b8c155',
    45, '#f5b400',
    55, '#e57a37',
    65, '#b03a1d',
  ];
}

// Exponer el mapa para depuración desde la consola.
window.__map = map;

async function inicializarMapa() {
  try {
    // Cargar parques de bomberos (necesario para el modelo)
    await M.cargarParques('data/parques_bomberos.geojson');

  // Capa de barrios coloreada por riesgo medio
  map.addSource('barris', {
    type: 'geojson',
    data: 'data/barris_riesgo.geojson',
  });
  map.addLayer({
    id: 'barris-fill',
    source: 'barris',
    type: 'fill',
    paint: {
      'fill-color': colorRiesgo(),
      'fill-opacity': 0.55,
      'fill-outline-color': '#5e5a52',
    },
  });
  map.addLayer({
    id: 'barris-hover',
    source: 'barris',
    type: 'line',
    paint: { 'line-color': '#b03a1d', 'line-width': 2 },
    filter: ['==', 'codbarrio', -1],
  });

  // Polígonos REALES del Top-500 edificios de mayor riesgo
  // (huella catastral completa, no centroide). Se ven a partir de
  // zoom 14 en rojo brasa translúcido, dan inmediatamente la idea
  // de qué casas son críticas.
  map.addSource('edificios-poligonos', {
    type: 'geojson',
    data: 'data/edificios_top_poligonos.geojson',
  });
  map.addLayer({
    id: 'edificios-poligonos-fill',
    source: 'edificios-poligonos',
    type: 'fill',
    minzoom: 14,
    paint: {
      'fill-color': colorRiesgo('r'),
      'fill-opacity': [
        'interpolate', ['linear'], ['zoom'],
        14, 0.35, 17, 0.6,
      ],
    },
  });
  map.addLayer({
    id: 'edificios-poligonos-line',
    source: 'edificios-poligonos',
    type: 'line',
    minzoom: 14,
    paint: {
      'line-color': '#222220',
      'line-width': 0.7,
    },
  });
  // Borde dorado para los candidatos perfil Campanar (≥10 plantas
  // construidos 2000-2017): edificios prioritarios para inspección
  // municipal de fachada
  map.addLayer({
    id: 'edificios-candidatos-line',
    source: 'edificios-poligonos',
    type: 'line',
    minzoom: 13,
    filter: ['==', ['get', 'c'], 1],
    paint: {
      'line-color': '#c47f1c',
      'line-width': 2.5,
    },
  });

  // Source de los 2.000 edificios destacados con CLUSTERING. Es el
  // MISMO conjunto que los polígonos del Catastro (edificios-poligonos)
  // — los puntos sirven solo para el clustering a zoom bajo, los
  // polígonos toman el relevo a zoom ≥ 14. Coherencia: el número que
  // muestra cada cluster coincide con los polígonos que aparecerán al
  // hacer zoom hasta esa zona.
  map.addSource('edificios', {
    type: 'geojson',
    data: 'data/edificios_top_riesgo.geojson',
    cluster: true,
    clusterMaxZoom: 14,
    clusterRadius: 38,
  });

  // Layer 1: clusters (burbujas grandes). maxzoom: 14 los desactiva
  // a partir del mismo umbral en el que aparecen los polígonos del
  // Catastro, evitando burbujas naranjas tapando polígonos rojos.
  map.addLayer({
    id: 'edificios-cluster',
    source: 'edificios',
    type: 'circle',
    maxzoom: 14,
    filter: ['has', 'point_count'],
    paint: {
      // Color y tamaño escalan con el número de edificios del cluster
      'circle-color': [
        'step', ['get', 'point_count'],
        '#f5b400', 30,
        '#e57a37', 100,
        '#b03a1d',
      ],
      'circle-radius': [
        'step', ['get', 'point_count'],
        14, 30, 18, 100, 24,
      ],
      'circle-stroke-color': 'rgba(255,255,255,0.85)',
      'circle-stroke-width': 2,
      'circle-opacity': 0.85,
    },
  });

  // Layer 2: número de edificios en cada cluster
  map.addLayer({
    id: 'edificios-cluster-count',
    source: 'edificios',
    type: 'symbol',
    maxzoom: 14,
    filter: ['has', 'point_count'],
    layout: {
      'text-field': ['get', 'point_count_abbreviated'],
      'text-font': ['Open Sans Bold', 'Arial Unicode MS Bold'],
      'text-size': 12,
      'text-allow-overlap': true,
    },
    paint: {
      'text-color': 'white',
    },
  });

  // Layer 3: puntos individuales (cuando NO están en cluster).
  // Solo se muestran si el zoom es bajo y para los edificios que no
  // tienen polígono en la capa edificios-poligonos. A zoom alto los
  // polígonos toman el protagonismo.
  map.addLayer({
    id: 'edificios',
    source: 'edificios',
    type: 'circle',
    filter: ['!', ['has', 'point_count']],
    maxzoom: 14,  // a partir de zoom 14, los polígonos los reemplazan
    paint: {
      'circle-radius': [
        'interpolate', ['linear'], ['zoom'],
        11, 3, 13, 4.5,
      ],
      'circle-color': colorRiesgo('r'),
      'circle-stroke-color': '#222220',
      'circle-stroke-width': 0.6,
      'circle-opacity': 0.85,
    },
  });

  // Click en cluster: zoom in al área del cluster
  map.on('click', 'edificios-cluster', e => {
    const features = map.queryRenderedFeatures(e.point, { layers: ['edificios-cluster'] });
    if (!features.length) return;
    const clusterId = features[0].properties.cluster_id;
    map.getSource('edificios').getClusterExpansionZoom(clusterId).then(zoom => {
      map.easeTo({ center: features[0].geometry.coordinates, zoom });
    }).catch(() => {});
  });
  map.on('mouseenter', 'edificios-cluster', () => map.getCanvas().style.cursor = 'pointer');
  map.on('mouseleave', 'edificios-cluster', () => map.getCanvas().style.cursor = '');

  // Parques de bomberos: cuadrado azul con la letra B encima
  // (más reconocible que un simple círculo, sin usar emojis ni iconos
  // raster).
  map.addSource('parques', { type: 'geojson', data: 'data/parques_bomberos.geojson' });
  map.addLayer({
    id: 'parques',
    source: 'parques',
    type: 'circle',
    paint: {
      'circle-radius': 13,
      'circle-color': '#1f4f8b',
      'circle-stroke-color': 'white',
      'circle-stroke-width': 2.5,
    },
  });
  map.addLayer({
    id: 'parques-label',
    source: 'parques',
    type: 'symbol',
    layout: {
      'text-field': 'B',
      'text-font': ['Open Sans Bold', 'Arial Unicode MS Bold'],
      'text-size': 13,
      'text-allow-overlap': true,
      'text-ignore-placement': true,
    },
    paint: {
      'text-color': 'white',
    },
  });

  // Capas operativas (despliegue del SPEIS) — empiezan vacías y
  // VISIBLES. La usuaria puede ocultarlas con el toggle «Ver despliegue
  // en el mapa» del bloque del plan de respuesta.
  const emptyFC = { type: 'FeatureCollection', features: [] };
  const opLayout = { visibility: 'visible' };
  map.addSource('op_perimetro', { type: 'geojson', data: emptyFC });
  map.addLayer({
    id: 'op_perimetro_fill', source: 'op_perimetro', type: 'fill',
    layout: opLayout,
    paint: { 'fill-color': '#1f4f8b', 'fill-opacity': 0.06 },
  });
  map.addLayer({
    id: 'op_perimetro_line', source: 'op_perimetro', type: 'line',
    layout: opLayout,
    paint: { 'line-color': '#1f4f8b', 'line-width': 1.5, 'line-dasharray': [3, 2] },
  });
  map.addSource('op_evacuacion', { type: 'geojson', data: emptyFC });
  map.addLayer({
    id: 'op_evacuacion_fill', source: 'op_evacuacion', type: 'fill',
    layout: opLayout,
    paint: { 'fill-color': '#b03a1d', 'fill-opacity': 0.1 },
  });
  map.addLayer({
    id: 'op_evacuacion_line', source: 'op_evacuacion', type: 'line',
    layout: opLayout,
    paint: { 'line-color': '#b03a1d', 'line-width': 1.5 },
  });
  // Source de rutas operativas: contiene tanto rutas reales (OSRM)
  // como fallbacks de línea recta. Usamos DOS layers separadas para
  // poder darle a cada una su línea sólida o punteada
  // (line-dasharray no admite expresiones data-driven en MapLibre).
  map.addSource('op_ruta', { type: 'geojson', data: emptyFC });
  const colorRuta = [
    'match', ['get', 'orden'],
    0, '#1f4f8b',
    1, '#5a7ba8',
    2, '#9ab0c8',
    '#cccccc',
  ];
  const grosorRuta = ['match', ['get', 'orden'], 0, 4, 1, 3, 2, 2, 1.5];

  map.addLayer({
    id: 'op_ruta_line', source: 'op_ruta', type: 'line',
    layout: opLayout,
    filter: ['==', ['get', 'real'], true],
    paint: { 'line-color': colorRuta, 'line-width': grosorRuta },
  });
  map.addLayer({
    id: 'op_ruta_line_fallback', source: 'op_ruta', type: 'line',
    layout: opLayout,
    filter: ['!=', ['get', 'real'], true],
    paint: {
      'line-color': colorRuta,
      'line-width': grosorRuta,
      'line-dasharray': [2, 2],
    },
  });
  map.addSource('op_target', { type: 'geojson', data: emptyFC });
  map.addLayer({
    id: 'op_target_circle', source: 'op_target', type: 'circle',
    layout: opLayout,
    paint: {
      'circle-radius': 9, 'circle-color': '#b03a1d',
      'circle-stroke-color': 'white', 'circle-stroke-width': 2.5,
    },
  });

  // Tooltip parques
  map.on('mouseenter', 'parques', e => {
    map.getCanvas().style.cursor = 'pointer';
    const p = e.features[0].properties;
    new maplibregl.Popup({ closeButton: false, offset: 12 })
      .setLngLat(e.lngLat)
      .setHTML(`<strong>${p.nombre}</strong><br>${p.direccion}`)
      .addTo(map)
      .__esTooltipParque = true;
  });
  map.on('mouseleave', 'parques', () => {
    map.getCanvas().style.cursor = '';
    document.querySelectorAll('.maplibregl-popup').forEach(el => {
      if (el.__esTooltipParque) el.remove();
    });
  });

  // Click en barrio: trasladar el contexto al modelo + mostrar info
  map.on('click', 'barris-fill', e => {
    // Si el click cae también sobre un edificio individual, ignoramos el
    // barrio (el handler del edificio ya gestiona la situación).
    const edif = map.queryRenderedFeatures(e.point, { layers: ['edificios'] });
    if (edif.length > 0) return;

    const f = e.features[0];
    const p = f.properties;
    estado.lon = e.lngLat.lng;
    estado.lat = e.lngLat.lat;
    estado.barrio_nombre = p.barrio;
    estado.densidad = Math.min(100, (p.densidad || 5000) / 100);
    estado.barrio_vuln = p.vulnerab || 50;
    map.setFilter('barris-hover', ['==', 'codbarrio', p.codbarrio]);
    map.flyTo({ center: e.lngLat, zoom: 14, duration: 800 });
    recalcular();

    // Popup con info del barrio (cierra otros antes)
    document.querySelectorAll('.maplibregl-popup').forEach(el => el.remove());
    new maplibregl.Popup({ offset: 8, closeButton: true, maxWidth: '260px' })
      .setLngLat(e.lngLat)
      .setHTML(`
        <div class="popup-titulo">Barrio · ${p.barrio}</div>
        <div class="popup-num">
          <span class="popup-num-val" style="color:${colorPorValor(p.riesgo_medio || 0)}">${p.riesgo_medio ?? '—'}</span>
          <span class="popup-num-lab">media del modelo · escenario base</span>
        </div>
        <p class="popup-detalle">
          ${p.n_edificios ?? '?'} edificios · altura media ${p.altura_media?.toFixed?.(1) ?? '?'} m<br>
          Tiempo medio bomberos: ${p.tiempo_llegada_medio?.toFixed?.(1) ?? '?'} min
        </p>
        <p class="popup-cta">
          Ahora el panel simula un edificio aquí. Mueve los sliders
          para explorar escenarios, o haz zoom y clic en un punto rojo
          para usar los datos reales de un edificio concreto.
        </p>
      `)
      .addTo(map);
  });
  map.on('mouseenter', 'barris-fill', () => map.getCanvas().style.cursor = 'pointer');
  map.on('mouseleave', 'barris-fill', () => map.getCanvas().style.cursor = '');

  // Click en edificio individual: rellenar los sliders con sus valores
  // reales y mostrar la ficha del edificio.
  // Handler unificado para click en edificio (sea punto o polígono).
  function clickEdificio(e) {
    const p = e.features[0].properties;
    estado.lon = e.lngLat.lng;
    estado.lat = e.lngLat.lat;
    estado.barrio_nombre = p.b;
    inputs.plantas.value = p.p;
    outputs.plantas.value = p.p;
    if (p.a != null && !isNaN(p.a)) {
      // Clamp explícito: el catastro tiene edificios fuera del rango
      // del slider (1850-2026); evitamos que el navegador silencie el
      // valor y deje el input desincronizado con el output visible.
      const aMin = parseInt(inputs.anio.min, 10) || 1850;
      const aMax = parseInt(inputs.anio.max, 10) || 2026;
      const a = Math.max(aMin, Math.min(aMax, Math.round(p.a)));
      inputs.anio.value = a;
      outputs.anio.value = a;
    }
    if (p.u) {
      const u = String(p.u);
      const opcionExiste = Array.from(inputs.uso.options).some(o => o.value === u);
      if (opcionExiste) inputs.uso.value = u;
      else inputs.uso.value = "";
    }
    // Para la exposición, usamos los valores del barrio (ya en su CSV)
    // — los conoceríamos solo si tuviéramos la fuente original, pero
    // los datasets del frontend solo dan info del barrio agregada.
    map.flyTo({ center: e.lngLat, zoom: 17, duration: 800 });
    recalcular();

    document.querySelectorAll('.maplibregl-popup').forEach(el => el.remove());
    new maplibregl.Popup({ offset: 10, closeButton: true, maxWidth: '280px' })
      .setLngLat(e.lngLat)
      .setHTML(`
        <div class="popup-titulo">Edificio del Catastro</div>
        <div class="popup-num">
          <span class="popup-num-val" style="color:${colorPorValor(p.r || 0)}">${p.r}</span>
          <span class="popup-num-lab">riesgo del modelo · escenario base</span>
        </div>
        <p class="popup-detalle">
          ${p.p ?? '?'} plantas · ${p.h ?? '?'} m
          · año ${p.a ? Math.round(p.a) : '—'}<br>
          ${p.b || '(sin barrio)'}${p.u ? ` · uso ${p.u}` : ''}<br>
          Bomberos: ${p.k ?? '—'} · ${p.t ?? '?'} min<br>
          ${p.i ? (() => {
            // El localId del Catastro INSPIRE viene como
            // «000100100YJ27F_part1» (la parte buildingpart). La referencia
            // catastral REAL es la base sin el sufijo _partN.
            const ref = p.i.split('_part')[0];
            return `<span class="popup-ref">Ref. catastral: <a href="https://www1.sedecatastro.gob.es/CYCBienInmueble/OVCListaBienes.aspx?rc1=${ref.slice(0,7)}&rc2=${ref.slice(7)}" target="_blank" rel="noopener"><code>${ref}</code></a></span>`;
          })() : ''}
        </p>
        <p class="popup-cta">
          Los sliders del panel ya están con los valores reales de este
          edificio. Cambia fachada / ITE / SCI / cubierta para ver qué
          pasaría bajo otros escenarios.
        </p>
      `)
      .addTo(map);
  }

  // Registrar el handler para los puntos individuales (zoom < 14) y para los
  // polígonos del Catastro (zoom >= 14). El mismo `clickEdificio` funciona
  // con ambos porque las propiedades abreviadas (r, p, h, a, u, b, t, k, i)
  // son las mismas en los dos GeoJSON.
  map.on('click', 'edificios', clickEdificio);
  map.on('click', 'edificios-poligonos-fill', clickEdificio);
  map.on('mouseenter', 'edificios', () => map.getCanvas().style.cursor = 'pointer');
  map.on('mouseleave', 'edificios', () => map.getCanvas().style.cursor = '');
  map.on('mouseenter', 'edificios-poligonos-fill', () => map.getCanvas().style.cursor = 'pointer');
  map.on('mouseleave', 'edificios-poligonos-fill', () => map.getCanvas().style.cursor = '');

  // Aviso de zoom: visible solo cuando el zoom < umbral de edificios
  const aviso = document.getElementById('ayuda-zoom');
  function actualizarAvisoZoom() {
    if (!aviso) return;
    aviso.classList.toggle('oculto', map.getZoom() >= 11);
  }
  actualizarAvisoZoom();
  map.on('zoom', actualizarAvisoZoom);

  // Primer cálculo
  recalcular();
  } catch (e) {
    console.error('cendra · error al inicializar el mapa:', e);
    // Aunque las capas del mapa fallen, intentamos al menos que la
    // calculadora muestre un primer resultado.
    try {
      await M.cargarParques('data/parques_bomberos.geojson');
      recalcular();
    } catch (e2) { console.error('cendra · fallback también falló:', e2); }
  }
}

// `map.on('load', ...)` puede perderse si el evento ya disparó antes de
// que el listener se registre (race condition en localhost u otros
// servidores rápidos). Comprobamos primero el estado del mapa.
if (map.loaded()) {
  inicializarMapa();
} else {
  map.once('load', inicializarMapa);
}

// Independientemente de que el mapa esté cargado, hacemos un primer
// cálculo «en frío» para que el panel muestre algo inmediatamente
// (riesgo, banda, recomendaciones). El mapa puede tardar en cargar el
// estilo del CDN pero la calculadora no debería esperar.
Promise.all([
  M.cargarParques('data/parques_bomberos.geojson'),
  fetch('data/hidrants.geojson').then(r => r.ok ? r.json() : null).catch(() => null),
]).then(([_, hidrants]) => {
  if (hidrants) estado.hidrantes_cargados = hidrants;
  try { recalcular(); } catch (e) { /* primer recalcular puede fallar si DOM no está */ }
}).catch(() => { /* offline o error de red */ });

// === LÓGICA DE LA CALCULADORA ==============================================

function leerInputs() {
  return {
    lon: estado.lon, lat: estado.lat,
    plantas: parseInt(inputs.plantas.value, 10),
    anio: parseInt(inputs.anio.value, 10),
    uso: inputs.uso.value || null,
    fachada: inputs.fachada.value,
    ite: inputs.ite.value,
    sci: inputs.sci.value,
    cubierta: inputs.cubierta.value,
    hora: parseInt(inputs.hora.value, 10),
    saturacion: inputs.saturacion.checked,
    barrio_vuln: estado.barrio_vuln,
    densidad: estado.densidad,
    equip_sensibles: estado.equip_sensibles,
  };
}

function recalcular() {
  if (!M.calcularRiesgo) return;
  const r = M.calcularRiesgo(leerInputs());

  // Número grande con pulso de animación
  resultado.total.textContent = r.riesgo_total;
  resultado.total.classList.remove('pulsando');
  // Forzar reflow para reiniciar la animación
  void resultado.total.offsetWidth;
  resultado.total.classList.add('pulsando');

  // Baseline: el primer riesgo calculado al cargar la página o tras un
  // reset. El cambio acumulado del aside se compara contra esto.
  // Mientras la usuaria no haya tocado nada (delta = 0), mostramos «—»
  // en ambos campos para no inducir a pensar que son dos valores
  // distintos.
  if (_riesgoBaseline === null) {
    _riesgoBaseline = r.riesgo_total;
  }
  const d = r.riesgo_total - _riesgoBaseline;
  if (Math.abs(d) >= 0.1) {
    resultado.baseline.textContent = _riesgoBaseline.toFixed(1);
    resultado.delta.textContent = `${d > 0 ? '+' : '−'}${Math.abs(d).toFixed(1)}`;
    resultado.delta.classList.toggle('up', d > 0);
    resultado.delta.classList.toggle('down', d < 0);
  } else {
    resultado.baseline.textContent = '—';
    resultado.delta.textContent = '—';
    resultado.delta.classList.remove('up', 'down');
  }

  // Barra global del riesgo total
  resultado.barra.style.width = `${r.riesgo_total}%`;

  // Componentes con su barrita y color por valor
  const setComp = (valBar, valEl, valor) => {
    valEl.textContent = valor.toFixed(1);
    valBar.style.width = `${Math.max(0, Math.min(100, valor))}%`;
    valBar.style.background = colorPorValor(valor);
  };
  setComp(resultado.V_bar, resultado.V, r.componentes.V_intrinseca);
  setComp(resultado.E_bar, resultado.E, r.componentes.E_exposicion);
  setComp(resultado.R_bar, resultado.R, r.componentes.R_respuesta);

  // Contexto: mostrar régimen + parque + tiempo
  const reg = r.pesos.regimen === 'fachada-critica'
    ? `<strong>Régimen fachada crítica</strong>: la respuesta de bomberos deja de ser efectiva porque el incendio se propaga más rápido de lo que pueden contener.`
    : `<strong>Régimen normal</strong>: la respuesta de emergencia atenúa el riesgo en el modelo.`;
  const t = r.detalle_respuesta;
  resultado.contexto.innerHTML = `
    ${reg}<br>
    Parque más cercano: <strong>${t.parque_efectivo ?? '—'}</strong>
    a ~${t.distancia_ruta_m} m · llegada estimada en
    <strong>${t.tiempo_llegada_min} min</strong> a las ${inputs.hora.value}:00.
    ${estado.barrio_nombre ? `Barrio: <strong>${estado.barrio_nombre}</strong>.` : ''}
  `;

  // Banda de confianza (mejor / peor caso paramétrico)
  const banda = M.bandaConfianza(leerInputs());
  document.getElementById('banda_best').textContent = banda.best;
  document.getElementById('banda_worst').textContent = banda.worst;

  // Explicación de por qué el riesgo es el que es (qué subfactor pesa más,
  // cómo se propagaría el incendio, qué normativa rige el edificio).
  const expLista = document.getElementById('explica_riesgo_lista');
  if (expLista && M.explicarRiesgo) {
    const lineas = M.explicarRiesgo(leerInputs(), r);
    expLista.innerHTML = lineas.map(l => `<li>${l}</li>`).join('');
  }

  // Recomendaciones
  actualizarRecomendaciones(leerInputs());

  // Plan de respuesta operativa
  actualizarPlanRespuesta(leerInputs(), r.detalle_respuesta);

  // Sugerencias del RAG normativo (preguntas plantilladas según el
  // edificio: año, plantas, fachada, sci...). El corpus se carga una
  // sola vez en background; mientras tanto el bloque queda visible
  // pero el botón Buscar avisa de que aún se está cargando.
  actualizarSugerenciasRAG(leerInputs());
}

// === RAG normativo (búsqueda BM25 sobre corpus curado) ====================

let _ragListo = false;
if (window.cendraRAG) {
  window.cendraRAG.cargarCorpus()
    .then(() => { _ragListo = true; })
    .catch(e => console.warn('cendra · RAG normativo no disponible:', e));
}

function actualizarSugerenciasRAG(input) {
  if (!window.cendraRAG) return;
  const cont = document.getElementById('rag_sugerencias');
  if (!cont) return;
  const sug = window.cendraRAG.sugerenciasParaInput(input);
  cont.innerHTML = sug.map(s =>
    `<button type="button" class="rag-sug">${s}</button>`
  ).join('');
  cont.querySelectorAll('.rag-sug').forEach(btn => {
    btn.addEventListener('click', () => {
      const inp = document.getElementById('rag_input');
      inp.value = btn.textContent;
      ejecutarBusquedaRAG();
    });
  });
}

function ejecutarBusquedaRAG() {
  if (!window.cendraRAG) return;
  const inp = document.getElementById('rag_input');
  const out = document.getElementById('rag_resultados');
  if (!inp || !out) return;
  const q = inp.value.trim();
  if (!q) { out.innerHTML = ''; return; }
  if (!_ragListo) {
    out.innerHTML = '<p class="rag-cargando">Cargando corpus normativo…</p>';
    setTimeout(ejecutarBusquedaRAG, 300);
    return;
  }
  const res = window.cendraRAG.buscar(q, 3);
  if (!res.length) {
    out.innerHTML = '<p class="rag-vacio">No he encontrado pasajes relevantes en el corpus. Reformula la pregunta usando términos como «fachada», «altura», «extintor», «ITE», «mantenimiento», «Campanar».</p>';
    return;
  }
  out.innerHTML = res.map(r => `
    <article class="rag-item">
      <header class="rag-cabecera">
        <span class="rag-norma">${r.norma}</span>
        <span class="rag-articulo">${r.articulo}</span>
        ${r.vigencia ? `<span class="rag-vigencia">${r.vigencia[0]}${r.vigencia[1] >= 9999 ? '–vigente' : `–${r.vigencia[1]}`}</span>` : ''}
      </header>
      <p class="rag-texto">${r.texto}</p>
      <footer class="rag-pie">
        ${r.boe ? `<span class="rag-boe">${r.boe}</span>` : ''}
        ${r.url ? `<a class="rag-link" href="${r.url}" target="_blank" rel="noopener">Texto oficial</a>` : ''}
      </footer>
    </article>
  `).join('');
}

document.addEventListener('DOMContentLoaded', () => {
  const btn = document.getElementById('rag_btn');
  const inp = document.getElementById('rag_input');
  if (btn) btn.addEventListener('click', ejecutarBusquedaRAG);
  if (inp) inp.addEventListener('keydown', e => {
    if (e.key === 'Enter') { e.preventDefault(); ejecutarBusquedaRAG(); }
  });
  const chatBtn = document.getElementById('chat_btn');
  const chatInp = document.getElementById('chat_input');
  if (chatBtn) chatBtn.addEventListener('click', enviarChat);
  if (chatInp) chatInp.addEventListener('keydown', e => {
    if (e.key === 'Enter') { e.preventDefault(); enviarChat(); }
  });

  // === FAB del chatbot (widget flotante) ===
  const fab = document.getElementById('chatbot_fab');
  const panel = document.getElementById('chatbot_panel');
  const cerrarBtn = document.getElementById('chatbot_cerrar');
  function abrirChatbot() {
    if (!panel || !fab) return;
    panel.classList.add('abierto');
    panel.setAttribute('aria-hidden', 'false');
    fab.classList.add('oculto');
    setTimeout(() => document.getElementById('chat_input')?.focus(), 200);
  }
  function cerrarChatbot() {
    if (!panel || !fab) return;
    panel.classList.remove('abierto');
    panel.setAttribute('aria-hidden', 'true');
    fab.classList.remove('oculto');
  }
  if (fab) fab.addEventListener('click', abrirChatbot);
  if (cerrarBtn) cerrarBtn.addEventListener('click', cerrarChatbot);
  // Cerrar con Escape cuando el panel esté abierto
  document.addEventListener('keydown', e => {
    if (e.key === 'Escape' && panel?.classList?.contains('abierto')) cerrarChatbot();
  });
});

// === Asistente conversacional con Workers AI =============================

async function enviarChat() {
  const inp = document.getElementById('chat_input');
  const btn = document.getElementById('chat_btn');
  const turnos = document.getElementById('chat_turnos');
  if (!inp || !turnos) return;
  const pregunta = inp.value.trim();
  if (!pregunta) return;

  // Limpiar bienvenida la primera vez
  const bienvenida = turnos.querySelector('.chat-bienvenida');
  if (bienvenida) bienvenida.remove();

  // Pintar el turno con la pregunta + indicador «pensando»
  const turno = document.createElement('div');
  turno.className = 'chat-turno';
  turno.innerHTML = `
    <div class="chat-pregunta">${_escaparHtml(pregunta)}</div>
    <div class="chat-respuesta chat-pensando">Pensando…</div>
  `;
  turnos.appendChild(turno);
  turnos.scrollTop = turnos.scrollHeight;
  inp.value = '';
  if (btn) { btn.disabled = true; btn.textContent = 'Pensando…'; }

  // Componer el contexto para el endpoint
  const i = leerInputs();
  const r = M.calcularRiesgo(i);
  const contexto = {
    plantas: i.plantas, anio: i.anio, uso: i.uso || 'no especificado',
    fachada: i.fachada, cubierta: i.cubierta, ite: i.ite, sci: i.sci,
    hora: i.hora, barrio: estado.barrio_nombre,
    riesgo_total: r.riesgo_total,
    V: r.componentes.V_intrinseca,
    E: r.componentes.E_exposicion,
    R: r.componentes.R_respuesta,
    regimen: r.pesos.regimen,
    parque: r.detalle_respuesta.parque_efectivo,
    tiempo_min: r.detalle_respuesta.tiempo_llegada_min,
  };
  // Recuperar pasajes RAG relevantes para contextualizar al modelo
  let normativa = [];
  if (window.cendraRAG && _ragListo) {
    try { normativa = window.cendraRAG.buscar(pregunta, 3); } catch {}
  }

  try {
    const resp = await fetch('/api/asistente', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ pregunta, contexto, normativa }),
    });
    const data = await resp.json();
    const cont = turno.querySelector('.chat-respuesta');
    cont.classList.remove('chat-pensando');
    if (!resp.ok) {
      cont.innerHTML = `<span class="chat-error">${_escaparHtml(data.error || 'Error desconocido')}</span>`;
    } else {
      cont.textContent = data.respuesta;
    }
  } catch (e) {
    const cont = turno.querySelector('.chat-respuesta');
    cont.classList.remove('chat-pensando');
    cont.innerHTML = `<span class="chat-error">No he podido contactar con el asistente. Comprueba tu conexión o vuelve a probar en unos segundos.</span>`;
  } finally {
    if (btn) { btn.disabled = false; btn.textContent = 'Enviar'; }
    turnos.scrollTop = turnos.scrollHeight;
  }
}

function _escaparHtml(s) {
  return String(s).replace(/[&<>"']/g, c => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
  })[c]);
}

// Pinta el plan de respuesta operativa + actualiza las capas del mapa
function actualizarPlanRespuesta(input, detalleRespuesta) {
  const plan = M.planRespuesta(input);
  document.getElementById('plan_efectivos').textContent = plan.efectivos;
  document.getElementById('plan_dotaciones').textContent = plan.dotaciones;
  document.getElementById('plan_caudal').textContent = plan.caudal_lmin.toLocaleString('es-ES');
  document.getElementById('plan_tiempo').textContent = plan.tiempo_control_min;

  const veh = document.getElementById('plan_vehiculos');
  veh.innerHTML = `<strong>Vehículos:</strong> ${plan.vehiculos.join(' · ')}`;

  const per = document.getElementById('plan_perimetro');
  per.textContent =
    `Evacuación inmediata en radio ${plan.radio_evacuacion_m} m. ` +
    `Perímetro operativo del SPEIS hasta ${plan.radio_perimetro_m} m.` +
    (plan.fachada_critica
      ? ' Tiempo de contención duplicado por fachada combustible.'
      : '');

  const horaEl = document.getElementById('plan_hora');
  if (horaEl) horaEl.textContent = plan.nota_hora;

  // Hidrantes operativos: los 3 más cercanos al edificio
  const hidrEl = document.getElementById('plan_hidrantes');
  if (hidrEl && estado.hidrantes_cargados) {
    const hidr = M.hidrantesOperativos(estado.hidrantes_cargados, input.lon, input.lat, 3);
    if (hidr.length) {
      hidrEl.innerHTML = '<strong>Hidrantes operativos:</strong> ' +
        hidr.map(h => `<code>${h.codigo}</code> (${h.distancia_m} m)`).join(' · ');
    }
  }

  // Actualizar capas del mapa con los círculos y la línea al parque
  actualizarCapasOperativas(input, plan, detalleRespuesta);
}

function actualizarCapasOperativas(input, plan, detalle) {
  if (!window.__map || !window.__map.getSource('op_evacuacion')) return;

  const lon = input.lon, lat = input.lat;
  window.__map.getSource('op_evacuacion').setData({
    type: 'Feature', properties: {}, geometry: M.circuloGeo(lon, lat, plan.radio_evacuacion_m),
  });
  window.__map.getSource('op_perimetro').setData({
    type: 'Feature', properties: {}, geometry: M.circuloGeo(lon, lat, plan.radio_perimetro_m),
  });
  window.__map.getSource('op_target').setData({
    type: 'Feature', properties: {}, geometry: { type: 'Point', coordinates: [lon, lat] },
  });

  // Rutas reales por calles desde los N parques que responden, con
  // debounce para no saturar el router OSRM mientras se mueven sliders.
  actualizarRutasOSRM(input, plan);
}

let _rutasTimer = null;
async function actualizarRutasOSRM(input, plan) {
  if (_rutasTimer) clearTimeout(_rutasTimer);
  _rutasTimer = setTimeout(async () => {
    const parquesResp = M.parquesQueResponden(
      input.lon, input.lat, plan.fachada_critica, input.plantas,
    );
    // Dibujamos primero líneas rectas como placeholder mientras OSRM responde
    const placeholder = parquesResp.map((p, i) => ({
      type: 'Feature',
      properties: { orden: i, parque: p.nombre, real: false },
      geometry: { type: 'LineString', coordinates: [
        [p.lon, p.lat], [input.lon, input.lat],
      ]},
    }));
    if (window.__map?.getSource('op_ruta')) {
      window.__map.getSource('op_ruta').setData({
        type: 'FeatureCollection', features: placeholder,
      });
    }

    // Ahora intentamos OSRM en paralelo
    const rutas = await Promise.all(parquesResp.map(p =>
      M.rutaPorCalles({ lon: p.lon, lat: p.lat }, { lon: input.lon, lat: input.lat }),
    ));

    const features = rutas.map((r, i) => {
      const p = parquesResp[i];
      if (!r) {
        return {
          type: 'Feature',
          properties: { orden: i, parque: p.nombre, real: false },
          geometry: { type: 'LineString', coordinates: [
            [p.lon, p.lat], [input.lon, input.lat],
          ]},
        };
      }
      return {
        type: 'Feature',
        properties: {
          orden: i, parque: p.nombre, real: true,
          duration_min: Math.round(r.duration_s / 60 * 10) / 10,
          distance_m: Math.round(r.distance_m),
        },
        geometry: r.geometry,
      };
    });
    if (window.__map?.getSource('op_ruta')) {
      window.__map.getSource('op_ruta').setData({
        type: 'FeatureCollection', features,
      });
    }

    // Actualizar el texto del panel con los detalles reales
    const txt = parquesResp.map((p, i) => {
      const r = rutas[i];
      if (r) {
        const t = Math.round(r.duration_s / 60 * 10) / 10;
        const km = (r.distance_m / 1000).toFixed(2);
        return `${p.nombre} → ${km} km, ${t} min reales`;
      }
      return `${p.nombre} → ${Math.round(p.distancia_m)} m en línea recta`;
    }).join(' · ');
    const rutasEl = document.getElementById('plan_rutas');
    if (rutasEl) rutasEl.innerHTML = `<strong>Parques que responden:</strong> ${txt}`;
  }, 400);
}

// Pintar la lista de recomendaciones
function actualizarRecomendaciones(input) {
  const ul = document.getElementById('lista_recomendaciones');
  if (!ul) return;
  const { recomendaciones, nota } = M.recomendaciones(input);
  const items = recomendaciones.map(r => `
    <li>
      <span class="reco-campo">${r.etiqueta_campo}</span>
      <span class="reco-delta">−${r.delta.toFixed(1)}</span>
      <span class="reco-cambio">
        ${r.label_actual} → <strong>${r.label_propuesto}</strong><br>
        Bajaría a <strong>${r.nuevo_riesgo.toFixed(1)}</strong> / 100
      </span>
    </li>
  `).join('');
  const notaHtml = nota ? `<li class="reco-nota">${nota}</li>` : '';
  if (!items && !notaHtml) {
    ul.innerHTML = '<li class="reco-vacia">Este edificio ya está en su mejor configuración paramétrica.</li>';
    return;
  }
  ul.innerHTML = items + notaHtml;
}

// Etiqueta dinámica para la franja horaria del slider de hora
function etiquetaHora(h) {
  const v = window.cendraModelo.V_HORA_KMH?.[h] ?? 45;
  let franja;
  if (h >= 0 && h <= 6) franja = 'madrugada';
  else if (h <= 9) franja = 'hora punta mañana';
  else if (h <= 13) franja = 'mañana';
  else if (h <= 15) franja = 'mediodía';
  else if (h <= 18) franja = 'tarde';
  else if (h <= 20) franja = 'hora punta tarde';
  else franja = 'noche';
  return `${String(h).padStart(2,'0')}:00 · ${franja} · ${v} km/h`;
}

// Reactividad
['plantas','anio','hora'].forEach(k => {
  inputs[k].addEventListener('input', () => {
    if (k === 'hora') outputs.hora.value = etiquetaHora(parseInt(inputs.hora.value, 10));
    else outputs[k].value = inputs[k].value;
    recalcular();
  });
});
['fachada','ite','sci','cubierta','uso'].forEach(k => {
  inputs[k].addEventListener('change', recalcular);
});
inputs.saturacion.addEventListener('change', recalcular);

// Toggle de visibilidad del despliegue operativo del SPEIS en el mapa
const togglePlanMapa = document.getElementById('f_plan_mapa');
function visibilidadPlanMapa() {
  if (!window.__map) return;
  const on = togglePlanMapa.checked ? 'visible' : 'none';
  ['op_evacuacion_fill', 'op_evacuacion_line',
   'op_perimetro_fill', 'op_perimetro_line',
   'op_ruta_line', 'op_ruta_line_fallback', 'op_target_circle'].forEach(id => {
    if (window.__map.getLayer(id))
      window.__map.setLayoutProperty(id, 'visibility', on);
  });
}
if (togglePlanMapa) togglePlanMapa.addEventListener('change', visibilidadPlanMapa);

// === Filtros del mapa ======================================================

const filtros = {
  alto: document.getElementById('f_alto'),
  lejos: document.getElementById('f_lejos'),
  alto_plantas: document.getElementById('f_alto_plantas'),
  pre1991: document.getElementById('f_pre1991'),
  barris: document.getElementById('f_barris'),
  edificios: document.getElementById('f_edificios'),
  parques: document.getElementById('f_parques'),
};

function aplicarFiltros() {
  if (!window.__map?.getSource?.('edificios')) return;
  const cond = ['all'];
  // El filtro 'all' aplica solo a edificios individuales (no clusters).
  // El cluster mantiene su propio filtro 'has point_count'.
  cond.push(['!', ['has', 'point_count']]);
  if (filtros.alto?.checked)
    cond.push(['>=', ['get', 'r'], 55]);
  if (filtros.lejos?.checked)
    cond.push(['>=', ['get', 't'], 8]);
  if (filtros.alto_plantas?.checked)
    cond.push(['>', ['get', 'p'], 12]);
  if (filtros.pre1991?.checked)
    cond.push(['all',
      ['has', 'a'],
      ['<', ['get', 'a'], 1991],
    ]);
  window.__map.setFilter('edificios', cond);

  // Visibilidad de capas
  const setVis = (layer, on) => {
    if (window.__map.getLayer(layer))
      window.__map.setLayoutProperty(layer, 'visibility', on ? 'visible' : 'none');
  };
  setVis('barris-fill', filtros.barris.checked);
  setVis('barris-hover', filtros.barris.checked);
  setVis('edificios', filtros.edificios.checked);
  setVis('edificios-cluster', filtros.edificios.checked);
  setVis('edificios-cluster-count', filtros.edificios.checked);
  setVis('edificios-poligonos-fill', filtros.edificios.checked);
  setVis('edificios-poligonos-line', filtros.edificios.checked);
  setVis('edificios-candidatos-line', filtros.edificios.checked);
  setVis('parques', filtros.parques.checked);
  setVis('parques-label', filtros.parques.checked);
}

Object.values(filtros).forEach(el => {
  if (el) el.addEventListener('change', aplicarFiltros);
});

// === Buscador de dirección con Nominatim ===================================
// Usa la API pública de OpenStreetMap, limitada al término de València.
// Cuando encuentra un resultado, vuela el mapa allí y dispara el click
// programático sobre el barrio que contiene ese punto.

const buscadorInput = document.getElementById('buscador');
const buscadorBtn = document.getElementById('buscador_btn');
const buscadorMsg = document.getElementById('buscador_msg');

async function buscarDireccion() {
  const q = buscadorInput.value.trim();
  if (!q) { buscadorMsg.textContent = ''; return; }
  buscadorMsg.classList.remove('error');
  buscadorMsg.textContent = 'Buscando…';
  // Restringimos al bbox del término municipal de València
  const bbox = '-0.50,39.28,-0.20,39.60';  // lon_min, lat_min, lon_max, lat_max
  const url = 'https://nominatim.openstreetmap.org/search?'
    + `q=${encodeURIComponent(q + ', València')}`
    + `&format=json&limit=1&countrycodes=es&viewbox=${bbox}&bounded=1`;
  try {
    const r = await fetch(url, { headers: { 'Accept-Language': 'es' } });
    const data = await r.json();
    if (!data?.length) {
      buscadorMsg.classList.add('error');
      buscadorMsg.textContent = 'Sin resultados en València. Prueba otra dirección.';
      return;
    }
    const lat = parseFloat(data[0].lat);
    const lon = parseFloat(data[0].lon);
    buscadorMsg.textContent = data[0].display_name.split(',').slice(0, 2).join(', ');
    if (window.__map) {
      window.__map.flyTo({ center: [lon, lat], zoom: 16, duration: 1200 });
      // Después del vuelo, disparar la lógica del click en barrio
      // como si la usuaria hubiera clickado en esa coordenada.
      window.__map.once('moveend', () => {
        const pt = window.__map.project([lon, lat]);
        const feats = window.__map.queryRenderedFeatures(pt, { layers: ['barris-fill'] });
        if (feats.length) {
          window.__map.fire('click', {
            lngLat: { lng: lon, lat },
            point: pt,
            features: feats,
          });
        } else {
          // Si no cae en un barrio (pedanía sin polígono visible),
          // al menos actualizamos coords y recalculamos.
          estado.lon = lon; estado.lat = lat;
          recalcular();
        }
      });
    } else {
      estado.lon = lon; estado.lat = lat;
      recalcular();
    }
  } catch (e) {
    buscadorMsg.classList.add('error');
    buscadorMsg.textContent = 'Error al buscar. Intenta de nuevo.';
  }
}
if (buscadorBtn) buscadorBtn.addEventListener('click', buscarDireccion);
if (buscadorInput) buscadorInput.addEventListener('keydown', e => {
  if (e.key === 'Enter') { e.preventDefault(); buscarDireccion(); }
});

// === Tabla de edificios más críticos =======================================

let _criticosData = null;
let _criticosTabActivo = 'riesgo';

async function cargarCriticos() {
  try {
    const r = await fetch('data/edificios_top_lista.json');
    if (!r.ok) return;
    _criticosData = await r.json();
    pintarCriticos();
  } catch (e) {
    /* offline o error */
  }
}

function pintarCriticos() {
  if (!_criticosData) return;
  const lista = document.getElementById('criticos_lista');
  const resumen = document.getElementById('criticos_resumen');
  if (!lista || !resumen) return;
  const items = _criticosTabActivo === 'campanar'
    ? _criticosData.top_candidatos_campanar
    : _criticosData.top_riesgo;
  resumen.textContent = _criticosTabActivo === 'campanar'
    ? `${_criticosData.n_total_candidatos_campanar.toLocaleString('es-ES')} edificios cumplen el perfil Campanar en València. Top 20 por riesgo:`
    : `Top 20 edificios con mayor riesgo del modelo (de ${_criticosData.n_total_edificios.toLocaleString('es-ES')} totales):`;
  lista.innerHTML = items.map(it => `
    <li class="critico-item ${it.candidato_campanar ? 'candidato' : ''}" data-lon="${it.lon}" data-lat="${it.lat}" data-plantas="${it.plantas}" data-anio="${it.anio || ''}" data-uso="${it.uso || ''}">
      <span class="critico-riesgo">${it.riesgo}</span>
      <span class="critico-barrio">${it.barrio || '(sin barrio)'}</span>
      ${it.candidato_campanar ? '<span class="critico-flag">perfil Campanar</span>' : ''}
      <div class="critico-meta">
        ${it.plantas} plantas${it.altura_m ? ` · ${it.altura_m} m` : ''}
        ${it.anio ? ` · ${it.anio}` : ''}
        · bomberos ${it.tiempo_llegada_min} min
      </div>
    </li>
  `).join('');
  // Click en una fila: vuela el mapa y simula
  lista.querySelectorAll('.critico-item').forEach(li => {
    li.addEventListener('click', () => {
      const lon = parseFloat(li.dataset.lon);
      const lat = parseFloat(li.dataset.lat);
      const plantas = parseInt(li.dataset.plantas, 10);
      const anio = parseInt(li.dataset.anio, 10);
      const uso = li.dataset.uso;
      estado.lon = lon; estado.lat = lat;
      inputs.plantas.value = plantas; outputs.plantas.value = plantas;
      if (!isNaN(anio)) { inputs.anio.value = anio; outputs.anio.value = anio; }
      if (uso) {
        const opcionExiste = Array.from(inputs.uso.options).some(o => o.value === uso);
        inputs.uso.value = opcionExiste ? uso : '';
      }
      if (window.__map) {
        window.__map.flyTo({ center: [lon, lat], zoom: 17, duration: 1200 });
      }
      recalcular();
    });
  });
}

document.querySelectorAll('.critico-tab').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.critico-tab').forEach(b => b.classList.remove('activo'));
    btn.classList.add('activo');
    _criticosTabActivo = btn.dataset.tab;
    pintarCriticos();
  });
});

cargarCriticos();

// === Cambio de vista entre Análisis y Propuestas ============================

document.querySelectorAll('.header-tab').forEach(btn => {
  btn.addEventListener('click', () => {
    const vista = btn.dataset.vista;
    document.querySelectorAll('.header-tab').forEach(b => b.classList.remove('activa'));
    btn.classList.add('activa');
    document.querySelectorAll('.vista').forEach(v => {
      v.hidden = (v.id !== `vista-${vista}`);
    });
    // Si pasamos a Propuestas, asegurarnos de cargar la tabla.
    if (vista === 'propuestas') cargarTablaCandidatos();
    // Si pasamos a Análisis y el mapa existe, forzar resize por si
    // estaba escondido y MapLibre no había recalculado dimensiones.
    if (vista === 'analisis' && window.__map) {
      setTimeout(() => window.__map.resize(), 50);
    }
  });
});

// === Tabla de los 154 candidatos Campanar (vista Propuestas) ===============

let _candidatosCompletos = null;

async function cargarTablaCandidatos() {
  if (_candidatosCompletos) {
    pintarTablaCandidatos(_candidatosCompletos);
    return;
  }
  try {
    const r = await fetch('data/candidatos_campanar_completo.json');
    if (!r.ok) return;
    _candidatosCompletos = await r.json();
    pintarTablaCandidatos(_candidatosCompletos);
  } catch (e) { /* offline */ }
}

function pintarTablaCandidatos(items) {
  const tbody = document.getElementById('tabla_candidatos_body');
  if (!tbody) return;
  tbody.innerHTML = items.map(it => {
    const refLink = it.ref
      ? `<a href="https://www1.sedecatastro.gob.es/CYCBienInmueble/OVCListaBienes.aspx?rc1=${it.ref.slice(0,7)}&rc2=${it.ref.slice(7)}" target="_blank" rel="noopener"><code>${it.ref}</code></a>`
      : '—';
    return `
      <tr data-lon="${it.lon}" data-lat="${it.lat}" data-plantas="${it.plantas}" data-anio="${it.anio || ''}" data-uso="${it.uso || ''}">
        <td class="num">${it.rank}</td>
        <td>${it.barrio || '—'}</td>
        <td class="num">${it.plantas}</td>
        <td class="num">${it.anio || '—'}</td>
        <td class="num">${it.riesgo}</td>
        <td class="num">${it.tiempo_llegada_min} min</td>
        <td>${refLink}</td>
        <td><button class="ver-link" type="button">Ver en mapa</button></td>
      </tr>
    `;
  }).join('');
  document.getElementById('tabla_pie').textContent =
    `Mostrando ${items.length} de ${_candidatosCompletos.length} candidatos.`;

  // Click en «Ver en mapa»: cambiar a vista análisis + simular ese edificio
  tbody.querySelectorAll('button.ver-link').forEach(btn => {
    btn.addEventListener('click', () => {
      const tr = btn.closest('tr');
      const lon = parseFloat(tr.dataset.lon);
      const lat = parseFloat(tr.dataset.lat);
      const plantas = parseInt(tr.dataset.plantas, 10);
      const anio = parseInt(tr.dataset.anio, 10);
      const uso = tr.dataset.uso;
      // Cambiar a vista análisis
      document.querySelector('.header-tab[data-vista="analisis"]').click();
      // Esperar a que el mapa termine de redimensionar (más fiable que
      // setTimeout fijo: la primera vez que se entra a la vista Análisis
      // el resize puede tardar más de 200 ms en navegadores móviles).
      const aplicar = () => {
        estado.lon = lon; estado.lat = lat;
        inputs.plantas.value = plantas; outputs.plantas.value = plantas;
        if (!isNaN(anio)) { inputs.anio.value = anio; outputs.anio.value = anio; }
        if (uso) {
          const opcionExiste = Array.from(inputs.uso.options).some(o => o.value === uso);
          inputs.uso.value = opcionExiste ? uso : '';
        }
        if (window.__map) window.__map.flyTo({ center: [lon, lat], zoom: 17, duration: 1200 });
        recalcular();
      };
      if (window.__map) window.__map.once('idle', aplicar);
      else setTimeout(aplicar, 200);
    });
  });
}

// Filtro por barrio en la tabla de candidatos. Normalizamos acentos
// (Sant Antoni == sant antoni == Sànt Antòni) para que el buscador
// funcione aunque el dataset incluya tildes.
function _norm(s) {
  return (s || '').toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '');
}
const filtroBarrioInput = document.getElementById('filtro_barrio');
if (filtroBarrioInput) {
  filtroBarrioInput.addEventListener('input', () => {
    if (!_candidatosCompletos) return;
    const q = _norm(filtroBarrioInput.value.trim());
    const filtrados = q
      ? _candidatosCompletos.filter(c => _norm(c.barrio).includes(q))
      : _candidatosCompletos;
    pintarTablaCandidatos(filtrados);
  });
}

// Descarga CSV
const descargarCSVBtn = document.getElementById('descargar_csv');
if (descargarCSVBtn) {
  descargarCSVBtn.addEventListener('click', () => {
    if (!_candidatosCompletos) return;
    const cols = ['rank', 'barrio', 'plantas', 'anio', 'altura_m', 'uso',
                  'riesgo', 'tiempo_llegada_min', 'parque_cercano', 'lon', 'lat', 'ref'];
    const lines = [cols.join(',')];
    for (const it of _candidatosCompletos) {
      lines.push(cols.map(c => {
        const v = it[c] ?? '';
        const s = String(v);
        return s.includes(',') || s.includes('"') ? `"${s.replace(/"/g, '""')}"` : s;
      }).join(','));
    }
    const blob = new Blob([lines.join('\n')], { type: 'text/csv;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'cendra_candidatos_campanar.csv';
    a.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  });
}

// === Tutorial de bienvenida (solo primera visita) ==========================

const tutorialEl = document.getElementById('tutorial');
const tutorialCerrar = document.getElementById('tutorial_cerrar');
const TUTORIAL_KEY = 'cendra_tutorial_visto_v1';
if (tutorialEl && !localStorage.getItem(TUTORIAL_KEY)) {
  tutorialEl.classList.remove('oculto');
}
function cerrarTutorial() {
  if (tutorialEl) tutorialEl.classList.add('oculto');
  try { localStorage.setItem(TUTORIAL_KEY, '1'); } catch (e) { /* localStorage no disp. */ }
}
if (tutorialCerrar) tutorialCerrar.addEventListener('click', cerrarTutorial);
if (tutorialEl) tutorialEl.addEventListener('click', e => {
  if (e.target === tutorialEl) cerrarTutorial();
});

// === Resetear simulación ===================================================

// Capturar los valores iniciales de los controles (antes de que el primer
// recalcular o el click de escenario los toque).
Object.entries(inputs).forEach(([k, el]) => {
  if (!el) return;
  if (el.type === 'checkbox') _valoresIniciales[k] = el.checked;
  else _valoresIniciales[k] = el.value;
});
const _estadoInicial = { ...estado };

const resetBtn = document.getElementById('reset_btn');
if (resetBtn) {
  resetBtn.addEventListener('click', () => {
    Object.entries(inputs).forEach(([k, el]) => {
      if (!el || !(k in _valoresIniciales)) return;
      if (el.type === 'checkbox') el.checked = _valoresIniciales[k];
      else el.value = _valoresIniciales[k];
    });
    // Sincronizar outputs de los range con su nuevo valor
    outputs.plantas.value = inputs.plantas.value;
    outputs.anio.value = inputs.anio.value;
    outputs.hora.value = etiquetaHora(parseInt(inputs.hora.value, 10));
    // Restaurar el estado del barrio
    Object.assign(estado, _estadoInicial);
    // Limpiar baseline para que el siguiente cálculo lo fije de nuevo
    _riesgoBaseline = null;
    resultado.delta.textContent = '';
    resultado.delta.classList.remove('up', 'down');
    // Limpiar buscador
    if (buscadorInput) { buscadorInput.value = ''; buscadorMsg.textContent = ''; }
    // Limpiar filtro de la tabla de candidatos
    if (filtroBarrioInput) filtroBarrioInput.value = '';
    if (_candidatosCompletos) pintarTablaCandidatos(_candidatosCompletos);
    // Cerrar popups
    document.querySelectorAll('.maplibregl-popup').forEach(p => p.remove());
    // Quitar resaltado de barrio
    if (window.__map?.getLayer('barris-hover')) {
      window.__map.setFilter('barris-hover', ['==', 'codbarrio', -1]);
    }
    // Vaciar capas operativas (radios, ruta, target) para no dejar restos
    // del último escenario apilados sobre el centro inicial.
    const empty = { type: 'FeatureCollection', features: [] };
    if (window.__map) {
      ['op_evacuacion', 'op_perimetro', 'op_ruta', 'op_target'].forEach(s => {
        const src = window.__map.getSource(s);
        if (src) src.setData(empty);
      });
      // Volver al encuadre inicial
      window.__map.flyTo({ center: [_estadoInicial.lon, _estadoInicial.lat], zoom: 12, duration: 800 });
    }
    recalcular();
  });
}

// Escenarios canónicos
document.querySelectorAll('.botones button').forEach(b => {
  b.addEventListener('click', () => {
    const e = M.ESCENARIOS[b.dataset.escenario];
    if (!e) return;
    estado.lon = e.lon; estado.lat = e.lat;
    estado.barrio_vuln = e.barrio_vuln;
    estado.densidad = e.densidad;
    estado.equip_sensibles = e.equip_sensibles;
    estado.barrio_nombre = null;
    inputs.plantas.value = e.plantas; outputs.plantas.value = e.plantas;
    inputs.anio.value = e.anio; outputs.anio.value = e.anio;
    inputs.fachada.value = e.fachada;
    inputs.ite.value = e.ite;
    inputs.sci.value = e.sci;
    inputs.cubierta.value = e.cubierta;
    inputs.hora.value = e.hora; outputs.hora.value = etiquetaHora(e.hora);
    inputs.saturacion.checked = e.saturacion;
    map.flyTo({ center: [e.lon, e.lat], zoom: 15, duration: 1200 });
    recalcular();
  });
});
