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

let _riesgoAnterior = null;

// Estado: ubicación del edificio (centro del mapa al inicio) y datos de barrio
let estado = {
  lon: -0.376,
  lat: 39.470,
  barrio_vuln: 50,
  densidad: 50,
  equip_sensibles: 'ninguno',
  barrio_nombre: null,
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
      'circle-color': colorRiesgo('riesgo'),
      'circle-stroke-color': '#222220',
      'circle-stroke-width': 0.8,
      'circle-opacity': 0.95,
    },
  });

  // Parques de bomberos
  map.addSource('parques', { type: 'geojson', data: 'data/parques_bomberos.geojson' });
  map.addLayer({
    id: 'parques',
    source: 'parques',
    type: 'circle',
    paint: {
      'circle-radius': 9,
      'circle-color': '#1f4f8b',
      'circle-stroke-color': 'white',
      'circle-stroke-width': 2,
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
          <span class="popup-num-lab">riesgo medio histórico</span>
        </div>
        <p class="popup-detalle">
          ${p.n_edificios ?? '?'} edificios · altura media ${p.altura_media?.toFixed?.(1) ?? '?'} m<br>
          Tiempo medio bomberos: ${p.tiempo_llegada_medio?.toFixed?.(1) ?? '?'} min
        </p>
        <p class="popup-cta">
          ↑ Ahora el panel simula un edificio aquí. Mueve los sliders
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
    estado.barrio_nombre = p.barrio;
    inputs.plantas.value = p.plantas;
    outputs.plantas.value = p.plantas;
    if (p.anio_construccion && !isNaN(p.anio_construccion)) {
      const a = Math.round(p.anio_construccion);
      inputs.anio.value = a;
      outputs.anio.value = a;
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
          <span class="popup-num-val" style="color:${colorPorValor(p.riesgo || 0)}">${p.riesgo}</span>
          <span class="popup-num-lab">riesgo bajo escenario medio</span>
        </div>
        <p class="popup-detalle">
          ${p.plantas} plantas · ${p.altura_m?.toFixed?.(0) ?? p.altura_m} m
          · año ${p.anio_construccion ? Math.round(p.anio_construccion) : '—'}<br>
          ${p.barrio || '(sin barrio)'}<br>
          Bomberos: ${p.parque_cercano} · ${p.tiempo_llegada_min} min
        </p>
        <p class="popup-cta">
          ↑ Los sliders del panel ya están con los valores reales de este
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

// === LÓGICA DE LA CALCULADORA ==============================================

function leerInputs() {
  return {
    lon: estado.lon, lat: estado.lat,
    plantas: parseInt(inputs.plantas.value, 10),
    anio: parseInt(inputs.anio.value, 10),
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

  // Delta respecto al cálculo anterior
  if (_riesgoAnterior !== null) {
    const d = r.riesgo_total - _riesgoAnterior;
    if (Math.abs(d) >= 0.1) {
      const sig = d > 0 ? '↑' : '↓';
      resultado.delta.textContent = `${sig} ${Math.abs(d).toFixed(1)}`;
      resultado.delta.classList.toggle('up', d > 0);
      resultado.delta.classList.toggle('down', d < 0);
      // Limpiar tras 2 s
      clearTimeout(window.__deltaTimer);
      window.__deltaTimer = setTimeout(() => {
        resultado.delta.textContent = '';
        resultado.delta.classList.remove('up', 'down');
      }, 2500);
    }
  }
  _riesgoAnterior = r.riesgo_total;

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
    ? `⚠ régimen <strong>fachada crítica</strong>: la respuesta de bomberos deja de ser efectiva.`
    : 'régimen normal';
  const t = r.detalle_respuesta;
  resultado.contexto.innerHTML = `
    ${reg}<br>
    Parque más cercano: <strong>${t.parque_efectivo ?? '—'}</strong>
    a ~${t.distancia_ruta_m} m · llegada estimada en
    <strong>${t.tiempo_llegada_min} min</strong> a las ${inputs.hora.value}:00.
    ${estado.barrio_nombre ? `Barrio: <strong>${estado.barrio_nombre}</strong>.` : ''}
  `;
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
['fachada','ite','sci','cubierta'].forEach(k => {
  inputs[k].addEventListener('change', recalcular);
});
inputs.saturacion.addEventListener('change', recalcular);

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
