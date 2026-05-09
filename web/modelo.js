/*
 * Modelo paramétrico de riesgo de incendio · v0.1.1
 *
 * Esta es la traducción a JavaScript del modelo Python en
 * `scripts/calcular_riesgo.py`. Cualquier cambio aquí debe reflejarse
 * en el Python y al revés. Las constantes y las tablas son
 * IDÉNTICAS — la lógica matemática también.
 *
 * Toda la documentación del modelo (justificación de pesos, régimen
 * fachada crítica, escenarios canónicos) vive en
 * `docs/modelo-riesgo.md`.
 */

// === Constantes del modelo v0.1.1 ============================================

const W_VULN = 0.45, W_EXP = 0.30, W_RESP = 0.25;
const W_VULN_FC = 0.75, W_EXP_FC = 0.20, W_RESP_FC = 0.05;  // régimen fachada-crítica

const TABLA_FACHADA = {
  "ladrillo": 0,
  "mortero": 10,
  "vidrio": 30,
  "composite-cte": 60,
  "sate-combustible": 80,
  "composite-acmpe": 100,
};
const TABLA_ITE = { "favorable": 0, "pendiente": 50, "desfavorable": 100 };
const TABLA_SCI = { "completo": 0, "parcial": 35, "extintores": 70, "ninguno": 100 };
const TABLA_CUBIERTA = { "tradicional": 0, "mixto": 40, "combustible": 100 };

// Etiquetas legibles para la UI (mantener en sync con las claves arriba)
const LABEL_FACHADA = {
  "ladrillo": "Ladrillo / mortero tradicional",
  "mortero": "Mortero (encalado tradicional)",
  "vidrio": "Muro cortina de vidrio",
  "composite-cte": "Composite con cumplimiento CTE",
  "sate-combustible": "SATE con núcleo combustible (EPS/XPS) ⚠",
  "composite-acmpe": "Composite con núcleo combustible (ACM-PE) ⚠",
};
const LABEL_ITE = {
  "favorable": "Favorable",
  "pendiente": "Pendiente / no realizada",
  "desfavorable": "Desfavorable",
};
const LABEL_SCI = {
  "completo": "Completo (rociadores + detección + columna seca)",
  "parcial": "Parcial",
  "extintores": "Solo extintores",
  "ninguno": "Ninguno",
};
const LABEL_CUBIERTA = {
  "tradicional": "Tradicional (no combustible)",
  "mixto": "Mixto",
  "combustible": "Combustible (madera, lámina bituminosa)",
};

const V_HORA_KMH = (() => {
  const v = {};
  for (let h = 0; h <= 6; h++) v[h] = 60;
  [7,8,9].forEach(h => v[h] = 30);
  [10,11,12,13].forEach(h => v[h] = 45);
  [14,15].forEach(h => v[h] = 40);
  [16,17,18].forEach(h => v[h] = 40);
  [19,20].forEach(h => v[h] = 30);
  [21,22,23].forEach(h => v[h] = 50);
  return v;
})();

const T_MOVILIZACION_MIN = 1.0;
const FACTOR_TORTUOSIDAD = 1.3;

// Coordenadas y datos de los 6 parques de bomberos del SPEIS.
// Se actualizan con `data/raw/parques_bomberos.geojson` al cargar.
let PARQUES = [];

async function cargarParques(url = 'data/parques_bomberos.geojson') {
  const r = await fetch(url);
  const g = await r.json();
  PARQUES = g.features.map(f => ({
    nombre: f.properties.nombre,
    lon: f.geometry.coordinates[0],
    lat: f.geometry.coordinates[1],
  }));
  return PARQUES;
}

// === Escenarios canónicos ====================================================

const ESCENARIOS = {
  "campanar": {
    descripcion: "Incidente Campanar real (2024-02-22)",
    lon: -0.3976, lat: 39.4847,
    plantas: 14, anio: 2006,
    fachada: "composite-acmpe", ite: "pendiente",
    sci: "parcial", cubierta: "mixto",
    hora: 17, saturacion: false,
    barrio_vuln: 55, densidad: 65, equip_sensibles: "ninguno",
  },
  "carmen": {
    descripcion: "Edificio histórico Centro · madrugada",
    lon: -0.3760, lat: 39.4790,
    plantas: 5, anio: 1920,
    fachada: "ladrillo", ite: "pendiente",
    sci: "ninguno", cubierta: "combustible",
    hora: 3, saturacion: false,
    barrio_vuln: 70, densidad: 90, equip_sensibles: "ninguno",
  },
  "quatre-carreres-nuevo": {
    descripcion: "Promoción nueva Quatre Carreres · hora punta",
    lon: -0.3590, lat: 39.4500,
    plantas: 8, anio: 2020,
    fachada: "composite-cte", ite: "favorable",
    sci: "completo", cubierta: "tradicional",
    hora: 9, saturacion: false,
    barrio_vuln: 35, densidad: 55, equip_sensibles: "educativo",
  },
};

// === Sub-factores ===========================================================

// v_edad alineado con hitos normativos españoles:
//   post-2017 = RIPCI · 2006-2017 = CTE DB-SI · 1991-2006 = NBE-CPI-91 · pre-1991 = sin normativa
function vEdad(anio) {
  if (anio > 2017) return 0;
  if (anio > 2006) return 20;
  if (anio > 1991) return 50;
  return 100;
}

// v_altura continua: 7 puntos por planta, saturado a 100 desde 15 plantas
function vAltura(plantas) {
  return Math.min(100, Math.max(0, plantas * 7));
}

function rTiempo(tMin) {
  if (tMin <= 4) return 0;
  if (tMin <= 6) return 30;
  if (tMin <= 8) return 60;
  if (tMin <= 12) return 85;
  return 100;
}

function rHidranteDefault() { return 50.0; }
function rAccesoDefault() { return 30.0; }

// === Geometría ==============================================================

function haversineMetros(lon1, lat1, lon2, lat2) {
  const R = 6371000;
  const rl1 = lat1 * Math.PI / 180;
  const rl2 = lat2 * Math.PI / 180;
  const dlat = (lat2 - lat1) * Math.PI / 180;
  const dlon = (lon2 - lon1) * Math.PI / 180;
  const a = Math.sin(dlat / 2) ** 2
          + Math.cos(rl1) * Math.cos(rl2) * Math.sin(dlon / 2) ** 2;
  return 2 * R * Math.asin(Math.sqrt(a));
}

function parqueMasCercano(lon, lat, saturados = []) {
  let mejor = null, mejorD = Infinity;
  for (const p of PARQUES) {
    if (saturados.includes(p.nombre)) continue;
    const d = haversineMetros(lon, lat, p.lon, p.lat);
    if (d < mejorD) { mejor = p; mejorD = d; }
  }
  return { parque: mejor, distancia_m: mejorD };
}

// === Dimensiones ============================================================

function vulnerabilidadIntrinseca({ plantas, anio, fachada, ite, sci, cubierta }) {
  const sub = {
    v_edad: vEdad(anio),
    v_altura: vAltura(plantas),
    v_fachada: TABLA_FACHADA[fachada],
    v_ite: TABLA_ITE[ite],
    v_sci: TABLA_SCI[sci],
    v_cubierta: TABLA_CUBIERTA[cubierta],
  };
  let V = 0.10 * sub.v_edad + 0.15 * sub.v_altura
        + 0.30 * sub.v_fachada + 0.15 * sub.v_ite
        + 0.20 * sub.v_sci + 0.10 * sub.v_cubierta;

  let fachadaCritica = false;
  if (sub.v_fachada >= 100) {
    const piso = Math.min(sub.v_fachada * (1.0 + 0.5 * sub.v_altura / 100), 100);
    if (piso > V) { V = piso; fachadaCritica = true; }
  }
  return { V, sub, fachadaCritica };
}

// Probabilidad de ocupación efectiva por uso y hora del día.
function factorUsoOcupacion(uso, hora) {
  if (!uso) return 1.0;
  const u = String(uso).toLowerCase();
  if (u.includes("residential") || u.startsWith("1_")) {
    if (hora < 6)  return 1.0;
    if (hora < 9)  return 0.85;
    if (hora < 17) return 0.45;
    if (hora < 22) return 0.9;
    return 1.0;
  }
  if (u.includes("industrial") || u.startsWith("3_")) return (hora >= 8 && hora < 18) ? 0.9 : 0.1;
  if (u.includes("office") || u.includes("4_1"))      return (hora >= 8 && hora < 19) ? 0.95 : 0.1;
  if (u.includes("agriculture") || u.startsWith("2_"))return (hora >= 7 && hora < 19) ? 0.4 : 0.05;
  return 0.6;
}

function exposicion({ barrio_vuln = 50, densidad = 50, equip_sensibles = "ninguno", uso = null, hora = 12 }) {
  const tabla = { residencia: 100, hospital: 80, educativo: 60, ninguno: 0 };
  const sub = {
    e_densidad: densidad,
    e_vulnerab: barrio_vuln,
    e_sensibles: tabla[equip_sensibles] ?? 0,
  };
  const base = 0.40 * sub.e_densidad + 0.35 * sub.e_vulnerab + 0.25 * sub.e_sensibles;
  const factor = factorUsoOcupacion(uso, hora);
  sub.factor_ocupacion = Math.round(factor * 100) / 100;
  return { E: base * factor, sub };
}

function respuesta({ lon, lat, hora, saturacion }) {
  let saturados = [];
  if (saturacion) {
    const { parque } = parqueMasCercano(lon, lat);
    if (parque) saturados = [parque.nombre];
  }
  const { parque: pEff, distancia_m: dEuclid } = parqueMasCercano(lon, lat, saturados);
  const dRuta = dEuclid * FACTOR_TORTUOSIDAD;
  const vKmh = V_HORA_KMH[hora] ?? 45;
  const tViaje = (dRuta / 1000) / vKmh * 60;
  const tLlegada = T_MOVILIZACION_MIN + tViaje;

  const sub = {
    r_tiempo: rTiempo(tLlegada),
    r_hidrante: rHidranteDefault(),
    r_acceso: rAccesoDefault(),
  };
  const R = 0.65 * sub.r_tiempo + 0.20 * sub.r_hidrante + 0.15 * sub.r_acceso;
  return {
    R, sub,
    parqueEfectivo: pEff,
    distanciaRutaM: Math.round(dRuta),
    velocidadKmh: vKmh,
    tiempoLlegadaMin: Math.round(tLlegada * 10) / 10,
  };
}

// === Riesgo total ===========================================================

function calcularRiesgo(input) {
  const { V, sub: subV, fachadaCritica } = vulnerabilidadIntrinseca(input);
  const { E, sub: subE } = exposicion(input);
  const { R, sub: subR, parqueEfectivo, tiempoLlegadaMin, distanciaRutaM, velocidadKmh }
    = respuesta(input);

  const [wV, wE, wR] = fachadaCritica
    ? [W_VULN_FC, W_EXP_FC, W_RESP_FC]
    : [W_VULN, W_EXP, W_RESP];

  const total = Math.max(0, Math.min(100, wV * V + wE * E + wR * R));

  return {
    riesgo_total: Math.round(total * 10) / 10,
    componentes: {
      V_intrinseca: Math.round(V * 10) / 10,
      E_exposicion: Math.round(E * 10) / 10,
      R_respuesta: Math.round(R * 10) / 10,
    },
    pesos: { w_V: wV, w_E: wE, w_R: wR,
             regimen: fachadaCritica ? "fachada-critica" : "normal" },
    subfactores_V: subV,
    subfactores_E: subE,
    subfactores_R: subR,
    detalle_respuesta: {
      parque_efectivo: parqueEfectivo?.nombre,
      tiempo_llegada_min: tiempoLlegadaMin,
      distancia_ruta_m: distanciaRutaM,
      velocidad_kmh: velocidadKmh,
    },
    version_modelo: "0.1.1",
  };
}

// === Motor de recomendaciones ==============================================
// Para cada variable paramétrica mejorable, encuentra el valor con mayor
// caída de riesgo y devuelve el top-3 ordenado por impacto.

const VARS_MEJORABLES = [
  { campo: "fachada", tabla: TABLA_FACHADA, label: LABEL_FACHADA, etiq: "Fachada" },
  { campo: "ite", tabla: TABLA_ITE, label: LABEL_ITE, etiq: "ITE" },
  { campo: "sci", tabla: TABLA_SCI, label: LABEL_SCI, etiq: "Sistema contra incendios" },
  { campo: "cubierta", tabla: TABLA_CUBIERTA, label: LABEL_CUBIERTA, etiq: "Cubierta" },
];

function recomendaciones(input) {
  const baseline = calcularRiesgo(input).riesgo_total;
  const propuestas = [];

  for (const m of VARS_MEJORABLES) {
    const valorActual = input[m.campo];
    const scoreActual = m.tabla[valorActual];
    let mejorDelta = 0;
    let mejorVal = null;
    let mejorRiesgo = null;

    for (const [nuevoVal, nuevoScore] of Object.entries(m.tabla)) {
      if (nuevoScore >= scoreActual) continue;  // solo si es mejor
      const inputMod = { ...input, [m.campo]: nuevoVal };
      const r = calcularRiesgo(inputMod).riesgo_total;
      const delta = baseline - r;
      if (delta > mejorDelta) {
        mejorDelta = delta;
        mejorVal = nuevoVal;
        mejorRiesgo = r;
      }
    }

    if (mejorVal !== null) {
      propuestas.push({
        campo: m.campo,
        etiqueta_campo: m.etiq,
        valor_actual: valorActual,
        valor_propuesto: mejorVal,
        label_actual: m.label[valorActual],
        label_propuesto: m.label[mejorVal],
        nuevo_riesgo: Math.round(mejorRiesgo * 10) / 10,
        delta: Math.round(mejorDelta * 10) / 10,
      });
    }
  }

  propuestas.sort((a, b) => b.delta - a.delta);
  return { baseline: Math.round(baseline * 10) / 10, recomendaciones: propuestas.slice(0, 3) };
}

// === Banda de confianza ====================================================
// Calcula el riesgo bajo el «mejor caso» (todos los paramétricos en óptimo)
// y «peor caso» (todos en el extremo) manteniendo lo demás constante.

function bandaConfianza(input) {
  const best = calcularRiesgo({
    ...input, fachada: "ladrillo", ite: "favorable",
    sci: "completo", cubierta: "tradicional",
  }).riesgo_total;
  const worst = calcularRiesgo({
    ...input, fachada: "composite-acmpe", ite: "desfavorable",
    sci: "ninguno", cubierta: "combustible",
  }).riesgo_total;
  return { best: Math.round(best * 10) / 10, worst: Math.round(worst * 10) / 10 };
}

// Exportar al ámbito global para que app.js pueda usarlas
window.cendraModelo = {
  cargarParques,
  calcularRiesgo,
  recomendaciones,
  bandaConfianza,
  ESCENARIOS,
  TABLA_FACHADA, TABLA_ITE, TABLA_SCI, TABLA_CUBIERTA,
  LABEL_FACHADA, LABEL_ITE, LABEL_SCI, LABEL_CUBIERTA,
  V_HORA_KMH,
};
