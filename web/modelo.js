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
  "sate-combustible": "SATE con núcleo combustible (EPS/XPS)",
  "composite-acmpe": "Composite con núcleo combustible (ACM-PE)",
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
    // El régimen «fachada crítica» se activa SIEMPRE que la fachada
    // combustible esté presente, independientemente de si el piso
    // eleva la V_intrínseca o no (puede ya estar al máximo por otros
    // factores).
    fachadaCritica = true;
    const piso = Math.min(sub.v_fachada * (1.0 + 0.5 * sub.v_altura / 100), 100);
    if (piso > V) V = piso;
  }
  return { V, sub, fachadaCritica };
}

// Mantenemos también el viejo nombre en español para los popups
// (cuando los popups consultaban si fachada crítica está activa).

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
  const top = propuestas.filter(p => p.delta >= 0.1).slice(0, 3);
  const fachadaCritica = ["composite-acmpe", "sate-combustible"].includes(input.fachada);
  let nota = null;
  if (fachadaCritica && top.length < 3) {
    nota = "Mientras la fachada combustible persista, las otras mejoras paramétricas (ITE, SCI, cubierta) tienen efecto muy limitado: la vulnerabilidad estructural queda saturada por la fachada. Por eso solo aparece la fachada como recomendación.";
  } else if (!top.length) {
    nota = "Este edificio ya está en la mejor configuración paramétrica posible.";
  }
  return {
    baseline: Math.round(baseline * 10) / 10,
    recomendaciones: top,
    nota,
  };
}

// === Banda de confianza ====================================================
// Calcula el rango plausible variando los paramétricos UN ESCALÓN
// arriba o abajo de su valor actual (no extremos absolutos). Comunica
// «lo que pasaría con una pequeña mejora» y «con un pequeño deterioro».
//
// Es metodológicamente más honesto que la versión anterior (que iba de
// ladrillo + todo perfecto hasta ACM-PE + todo desfavorable, una
// combinatoria casi imposible que daba bandas ridículamente anchas).

const ORDENES_PARAM = {
  fachada: ["ladrillo", "mortero", "vidrio", "composite-cte", "sate-combustible", "composite-acmpe"],
  ite: ["favorable", "pendiente", "desfavorable"],
  sci: ["completo", "parcial", "extintores", "ninguno"],
  cubierta: ["tradicional", "mixto", "combustible"],
};

function bandaConfianza(input) {
  const mejor = { ...input };
  const peor = { ...input };
  for (const [campo, orden] of Object.entries(ORDENES_PARAM)) {
    const idx = orden.indexOf(input[campo]);
    if (idx < 0) continue;
    if (idx > 0) mejor[campo] = orden[idx - 1];
    if (idx < orden.length - 1) peor[campo] = orden[idx + 1];
  }
  const b = calcularRiesgo(mejor).riesgo_total;
  const w = calcularRiesgo(peor).riesgo_total;
  return {
    best: Math.round(b * 10) / 10,
    worst: Math.round(w * 10) / 10,
  };
}

// === Plan de respuesta operativa ===========================================
// Para un edificio simulado, estima el despliegue del SPEIS necesario
// según altura, fachada y entorno. NO es protocolo oficial — es una
// heurística basada en doctrina común de respuesta a incendio
// estructural urbano. Sirve para que la persona usuaria visualice qué
// implica «que arda» y se entienda la dimensión de la operación.

function planRespuesta(input) {
  const plantas = Math.max(1, input.plantas | 0);
  const hora = input.hora ?? 12;
  const fachadaCritica = ["composite-acmpe", "sate-combustible"].includes(input.fachada);

  // Dotaciones base por altura (1 dotación ≈ 5 efectivos + 1 vehículo)
  let dotaciones, efectivos, vehiculos;
  if (plantas <= 3) {
    dotaciones = 1; efectivos = 5;
    vehiculos = ["BUL (bomba urbana ligera)"];
  } else if (plantas <= 8) {
    dotaciones = 2; efectivos = 12;
    vehiculos = ["BUL", "Autoescala"];
  } else if (plantas <= 14) {
    dotaciones = 3; efectivos = 18;
    vehiculos = ["BUL", "BUP (bomba urbana pesada)", "Autoescala", "UEMSV (médico)"];
  } else {
    dotaciones = 4; efectivos = 25;
    vehiculos = ["BUL", "BUP", "Autoescala-jumbo", "UEMSV", "Mando intermedio"];
  }

  // Refuerzo si fachada combustible: una dotación adicional + refuerzo
  // del Consorcio Provincial.
  if (fachadaCritica) {
    dotaciones += 1;
    efectivos += 7;
    vehiculos.push("Refuerzo del Consorcio Provincial");
  }

  // Refuerzo por equipamiento sensible cercano
  if (input.equip_sensibles === "residencia" || input.equip_sensibles === "hospital") {
    dotaciones += 1;
    efectivos += 5;
    vehiculos.push("UEMSV adicional (evacuación asistida)");
  }

  // Radios operativos
  const radio_evacuacion_m = plantas <= 5 ? 50 : plantas <= 10 ? 75 : 100;
  const radio_perimetro_m = radio_evacuacion_m * 2;

  // Caudal hidráulico aproximado: 500 L/min por dotación que entra en
  // ataque interno. Caudal total + 30 % de reserva.
  const caudal_lmin = Math.round(dotaciones * 500 * 1.3);

  // Tiempo estimado de control (cuando se contiene la propagación):
  // 8 min base + 4 min por planta adicional > 5, doble si fachada
  // combustible (basado en doctrina post-Campanar).
  let t_control_min = 8 + Math.max(0, plantas - 5) * 4;
  if (fachadaCritica) t_control_min *= 2;
  if (t_control_min > 240) t_control_min = 240;  // tope realista

  // Nota descriptiva sobre la hora del incidente.
  // No alteramos los números (sería invento sin datos del SPEIS), pero
  // explicamos qué implica la hora para el operativo.
  let nota_hora;
  if (hora >= 0 && hora < 6) {
    nota_hora = "Madrugada: turno reducido en activo. Si la incidencia es grande puede ser necesario activar el Consorcio Provincial.";
  } else if (hora >= 7 && hora <= 9) {
    nota_hora = "Hora punta de mañana: la unidad puede tardar más por el tráfico denso.";
  } else if (hora >= 19 && hora <= 20) {
    nota_hora = "Hora punta de tarde: dotaciones completas pero tráfico denso.";
  } else if (hora >= 21 || hora <= 23) {
    nota_hora = "Noche temprana: dotaciones completas en activo.";
  } else {
    nota_hora = "Horario diurno: dotaciones completas y tráfico fluido.";
  }

  return {
    dotaciones,
    efectivos,
    vehiculos,
    radio_evacuacion_m,
    radio_perimetro_m,
    caudal_lmin,
    tiempo_control_min: Math.round(t_control_min),
    fachada_critica: fachadaCritica,
    nota_hora,
  };
}

// Hidrantes operativos: los N más cercanos al edificio.
// Recibe el GeoJSON de hidrants ya cargado y el punto lon/lat.
function hidrantesOperativos(hidrantesGeo, lon, lat, n = 3) {
  if (!hidrantesGeo?.features) return [];
  const conDist = hidrantesGeo.features.map(f => {
    const [hlon, hlat] = f.geometry.coordinates;
    return { f, d: haversineMetros(lon, lat, hlon, hlat) };
  });
  conDist.sort((a, b) => a.d - b.d);
  return conDist.slice(0, n).map(({ f, d }) => ({
    codigo: f.properties.codigo,
    calle: f.properties.calle,
    numero: f.properties.numero,
    distancia_m: Math.round(d),
    lon: f.geometry.coordinates[0],
    lat: f.geometry.coordinates[1],
  }));
}

// === Geometría para visualizar el despliegue en el mapa ====================
// Calcula un círculo geodésico aproximado (50 puntos) alrededor de un
// punto lon/lat con un radio en metros. Sirve para dibujar buffers de
// evacuación y perímetro sin librerías externas.
function circuloGeo(lon, lat, radioM, n = 64) {
  const R = 6371000;
  const coords = [];
  for (let i = 0; i <= n; i++) {
    const b = (i / n) * 2 * Math.PI;
    const dLat = (radioM * Math.cos(b)) / R * (180 / Math.PI);
    const dLon = (radioM * Math.sin(b)) / (R * Math.cos(lat * Math.PI / 180)) * (180 / Math.PI);
    coords.push([lon + dLon, lat + dLat]);
  }
  return { type: "Polygon", coordinates: [coords] };
}

// Exportar al ámbito global para que app.js pueda usarlas
window.cendraModelo = {
  cargarParques,
  calcularRiesgo,
  recomendaciones,
  bandaConfianza,
  planRespuesta,
  hidrantesOperativos,
  circuloGeo,
  haversineMetros,
  ESCENARIOS,
  TABLA_FACHADA, TABLA_ITE, TABLA_SCI, TABLA_CUBIERTA,
  LABEL_FACHADA, LABEL_ITE, LABEL_SCI, LABEL_CUBIERTA,
  V_HORA_KMH,
};
