/*
 * Cloudflare Pages Function · /api/asistente
 *
 * Asistente conversacional del atlas cendra. Recibe la pregunta de
 * la persona usuaria y el contexto de la simulación actual, y
 * responde con un texto en castellano basado ÚNICAMENTE en ese
 * contexto + un puñado de pasajes recuperados del corpus normativo.
 *
 * Arquitectura:
 *   1. Frontend llama a POST /api/asistente con { pregunta, contexto, normativa }
 *   2. Esta function compone el system prompt blindado anti-alucinación
 *      con todos los datos verificables.
 *   3. Llama al modelo Llama 3.1 8B Instruct vía binding `AI` de
 *      Workers AI (incluido en el plan free de Cloudflare Pages).
 *   4. Devuelve la respuesta como JSON.
 *
 * Por qué blindado:
 *   - El asistente NO puede inventar números (los lee del contexto).
 *   - NO puede listar edificios concretos por dirección.
 *   - NO puede hacer recomendaciones individuales ni profesionales.
 *   - SOLO explica el modelo de cendra y los pasajes normativos.
 *   - Si no sabe, dice explícitamente «no tengo datos sobre eso».
 *
 * Configuración necesaria en Cloudflare Pages:
 *   Settings → Functions → Bindings → Add → Workers AI
 *   Binding: AI · Modelo: ninguno (la function pasa el modelo en cada call)
 *
 * Sin coste para el plan free hasta 10.000 peticiones/día.
 */

const SYSTEM_PROMPT = `Eres el asistente del atlas cendra, una herramienta abierta que estima el riesgo de incendio de los edificios residenciales de València. Hablas castellano formal pero claro, con lenguaje inclusivo. Eres directo, no te enrolles, nunca usas más de 4 frases por respuesta.

REGLAS ABSOLUTAS:
1. SOLO usas la información del «CONTEXTO DEL EDIFICIO», la sección «MODELO DE CENDRA» y los «PASAJES NORMATIVOS» que te paso.
2. NUNCA inventas cifras, datos de incendios concretos, direcciones ni edificios. Si la pregunta requiere datos que no están en el contexto, respondes literalmente: «No tengo datos sobre eso en el atlas. Puedes mirar el bloque «Por qué este riesgo» del panel o pedir una inspección técnica al SPEIS.»
3. NUNCA das consejo profesional ni clínico. Eres una herramienta divulgativa, no un perito.
4. NO listas edificios concretos por dirección, calle o referencia catastral, aunque te lo pregunten.
5. NO predices incendios. El modelo de cendra estima riesgo paramétrico, no probabilidad real.
6. Cuando cites una norma (CTE DB-SI, NBE-CPI, RIPCI, ITE) usa el nombre corto. La cita textual completa la pone el frontend con su enlace al BOE.
7. Termina cada respuesta sugiriendo, si encaja, qué slider o bloque del atlas tocar para aprender más («prueba a poner la fachada en no combustible y verás que el riesgo baja a X»).

NUNCA digas «como modelo de IA» ni «soy un modelo de lenguaje». Eres «el asistente del atlas».`;

const MODEL = '@cf/meta/llama-3.1-8b-instruct';
const MAX_TOKENS = 320;

/** Construye el contexto a inyectar en el prompt. */
function _formatearContexto(contexto, normativa) {
  const c = contexto || {};
  const ctx = [
    'CONTEXTO DEL EDIFICIO SIMULADO (datos exactos, NO los inventes):',
    `- Plantas: ${c.plantas ?? '?'}`,
    `- Año de construcción: ${c.anio ?? '?'}`,
    `- Uso: ${c.uso ?? 'no especificado'}`,
    `- Fachada: ${c.fachada ?? '?'}`,
    `- Cubierta: ${c.cubierta ?? '?'}`,
    `- ITE: ${c.ite ?? '?'}`,
    `- Sistema contra incendios: ${c.sci ?? '?'}`,
    `- Hora simulada: ${c.hora ?? '?'}:00`,
    `- Barrio: ${c.barrio ?? 'no localizado'}`,
    '',
    'RESULTADO DEL MODELO DE CENDRA (no inventes, son las cifras reales):',
    `- Riesgo total: ${c.riesgo_total ?? '?'} / 100`,
    `- V (vulnerabilidad estructural): ${c.V ?? '?'} / 100`,
    `- E (exposición poblacional): ${c.E ?? '?'} / 100`,
    `- R (respuesta operativa): ${c.R ?? '?'} / 100`,
    `- Régimen: ${c.regimen ?? 'normal'}`,
    `- Parque más cercano: ${c.parque ?? '?'}, llegada en ${c.tiempo_min ?? '?'} min`,
  ].join('\n');

  let pasajes = '';
  if (Array.isArray(normativa) && normativa.length) {
    pasajes = '\n\nPASAJES NORMATIVOS RELEVANTES (cita los nombres si encajan; el enlace lo añade el frontend):\n';
    pasajes += normativa.slice(0, 3).map((n, i) => (
      `[${i + 1}] ${n.norma} · ${n.articulo}: ${n.texto}`
    )).join('\n');
  }

  return ctx + pasajes;
}

export async function onRequestPost({ request, env }) {
  // CORS preflight básico
  const cors = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Content-Type': 'application/json',
  };

  if (!env.AI) {
    return new Response(
      JSON.stringify({ error: 'Workers AI no está enlazado en este despliegue. Activa el binding AI en Cloudflare Pages → Settings → Functions.' }),
      { status: 503, headers: cors },
    );
  }

  let body;
  try {
    body = await request.json();
  } catch {
    return new Response(JSON.stringify({ error: 'Cuerpo JSON inválido' }), { status: 400, headers: cors });
  }

  const pregunta = (body?.pregunta || '').trim().slice(0, 500);
  if (!pregunta) {
    return new Response(JSON.stringify({ error: 'Falta el campo «pregunta»' }), { status: 400, headers: cors });
  }

  const contextoTxt = _formatearContexto(body.contexto, body.normativa);

  const messages = [
    { role: 'system', content: SYSTEM_PROMPT },
    { role: 'user', content: contextoTxt + '\n\nPREGUNTA: ' + pregunta },
  ];

  try {
    const res = await env.AI.run(MODEL, {
      messages,
      max_tokens: MAX_TOKENS,
      temperature: 0.3,  // baja creatividad, prioridad a la fidelidad del contexto
    });
    const respuesta = (res?.response || '').trim();
    return new Response(
      JSON.stringify({
        respuesta: respuesta || 'No he podido generar una respuesta. Vuelve a probar en unos segundos.',
        modelo: MODEL,
      }),
      { status: 200, headers: cors },
    );
  } catch (e) {
    return new Response(
      JSON.stringify({ error: 'Error al llamar al modelo: ' + (e?.message || 'desconocido') }),
      { status: 500, headers: cors },
    );
  }
}

export async function onRequestOptions() {
  return new Response(null, {
    status: 204,
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type',
      'Access-Control-Max-Age': '86400',
    },
  });
}
