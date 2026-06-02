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

  // Capa de TOP-2000 edificios de mayor riesgo (puntos)
  // Solo se ve a zoom alto para no saturar la vista general.
  map.addSource('edificios', {
    type: 'geojson',
    data: 'data/edificios_top_riesgo.geojson',
  });
  map.addLayer({
    id: 'edificios',
    source: 'edificios',
    type: 'circle',
    minzoom: 11,
    paint: {
      'circle-radius': [
        'interpolate', ['linear'], ['zoom'],
        11, 2.5, 13, 4.5, 16, 7, 19, 11,
      ],
      'circle-color': colorRiesgo('r'),
      'circle-stroke-color': '#222220',
      'circle-stroke-width': 0.8,
      'circle-opacity': 0.95,
    },
  });

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
  map.addSource('op_ruta', { type: 'geojson', data: emptyFC });
  map.addLayer({
    id: 'op_ruta_line', source: 'op_ruta', type: 'line',
    layout: opLayout,
    paint: {
      // Color por orden: 0 azul oscuro, 1 medio, 2 claro
      'line-color': [
        'match', ['get', 'orden'],
        0, '#1f4f8b',
        1, '#5a7ba8',
        2, '#9ab0c8',
        '#cccccc',
      ],
      // Grosor decreciente por orden
      'line-width': [
        'match', ['get', 'orden'],
        0, 4, 1, 3, 2, 2, 1.5,
      ],
      // Las rutas reales (de OSRM) van sólidas; las de fallback (línea recta)
      // van punteadas para que se entienda que es estimación.
      'line-dasharray': [
        'case',
        ['==', ['get', 'real'], true], ['literal', [1]],
        ['literal', [2, 2]],
      ],
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
  map.on('click', 'edificios', e => {
    const p = e.features[0].properties;
    estado.lon = e.lngLat.lng;
    estado.lat = e.lngLat.lat;
    estado.barrio_nombre = p.b;  // barrio
    inputs.plantas.value = p.p;
    outputs.plantas.value = p.p;
    if (p.a != null && !isNaN(p.a)) {
      const a = Math.round(p.a);
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
          ${p.i ? `<span class="popup-ref">Ref. catastral: <a href="https://www1.sedecatastro.gob.es/CYCBienInmueble/OVCListaBienes.aspx?rc1=${p.i.slice(0,7)}&rc2=${p.i.slice(7)}" target="_blank" rel="noopener"><code>${p.i}</code></a></span>` : ''}
        </p>
        <p class="popup-cta">
          Los sliders del panel ya están con los valores reales de este
          edificio. Cambia fachada / ITE / SCI / cubierta para ver qué
          pasaría bajo otros escenarios.
        </p>
      `)
      .addTo(map);
  });
    map.on('mouseenter', 'edificios', () => map.getCanvas().style.cursor = 'pointer');
    map.on('mouseleave', 'edificios', () => map.getCanvas().style.cursor = '');

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

  // Recomendaciones
  actualizarRecomendaciones(leerInputs());

  // Plan de respuesta operativa
  actualizarPlanRespuesta(leerInputs(), r.detalle_respuesta);
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
   'op_ruta_line', 'op_target_circle'].forEach(id => {
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
  window.__map.setFilter('edificios', cond.length > 1 ? cond : null);

  // Visibilidad de capas
  const setVis = (layer, on) => {
    if (window.__map.getLayer(layer))
      window.__map.setLayoutProperty(layer, 'visibility', on ? 'visible' : 'none');
  };
  setVis('barris-fill', filtros.barris.checked);
  setVis('barris-hover', filtros.barris.checked);
  setVis('edificios', filtros.edificios.checked);
  setVis('parques', filtros.parques.checked);
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
    // Cerrar popups
    document.querySelectorAll('.maplibregl-popup').forEach(p => p.remove());
    // Quitar resaltado de barrio
    if (window.__map?.getLayer('barris-hover')) {
      window.__map.setFilter('barris-hover', ['==', 'codbarrio', -1]);
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
