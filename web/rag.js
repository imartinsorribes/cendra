/*
 * cendra VLC · RAG normativo en cliente
 *
 * Implementación de búsqueda BM25 (Okapi BM25) sobre el corpus curado
 * de normativa de incendios española (web/data/normativa.json).
 *
 * Diseñado para ejecutarse 100 % en el navegador, sin backend ni claves
 * de API. Carga el corpus una sola vez y mantiene el índice invertido
 * en memoria. La consulta devuelve los k pasajes con mayor relevancia
 * acompañados de su cita original al BOE / DOGV / fuente, para que la
 * usuaria pueda verificar la afirmación.
 *
 * BM25 es preferible a TF-IDF puro para corpus pequeños porque modera
 * el peso de los términos frecuentes (saturación de TF) y normaliza
 * por longitud del documento, evitando que pasajes largos eclipsen a
 * pasajes cortos pero precisos.
 */

(function () {
  'use strict';

  const CORPUS_URL = 'data/normativa.json';
  const STOPWORDS = new Set([
    'de', 'la', 'el', 'en', 'a', 'que', 'y', 'es', 'los', 'las', 'del',
    'se', 'un', 'una', 'por', 'con', 'su', 'al', 'lo', 'como', 'más',
    'o', 'pero', 'sus', 'le', 'ha', 'me', 'si', 'sin', 'sobre', 'este',
    'esta', 'entre', 'cuando', 'todo', 'son', 'fue', 'ser', 'también',
    'hay', 'mi', 'porque', 'nos', 'qué', 'quién', 'cuál', 'cómo',
    'donde', 'cuándo', 'para', 'tener', 'tiene', 'según', 'cada', 'no',
  ]);

  // Parámetros BM25 estándar
  const BM25_K1 = 1.5;
  const BM25_B = 0.75;

  /** Normaliza una cadena: minúsculas, sin acentos, sin signos. */
  function _norm(s) {
    return (s || '')
      .toLowerCase()
      .normalize('NFD')
      .replace(/[̀-ͯ]/g, '')
      .replace(/[^a-z0-9áéíóúñ\s]/g, ' ');
  }

  /** Tokeniza eliminando stopwords y términos demasiado cortos. */
  function _tokens(s) {
    return _norm(s)
      .split(/\s+/)
      .filter(t => t.length >= 3 && !STOPWORDS.has(t));
  }

  let _corpus = null;
  let _idx = null;     // término -> Map(docId -> tf)
  let _df = null;      // término -> nº de documentos en los que aparece
  let _docLen = null;  // docId -> longitud (tokens)
  let _avgLen = 0;
  let _N = 0;

  async function cargarCorpus() {
    if (_corpus) return _corpus;
    const r = await fetch(CORPUS_URL);
    if (!r.ok) throw new Error('No se pudo cargar el corpus normativo');
    const data = await r.json();
    _corpus = data.items;
    _N = _corpus.length;
    _idx = new Map();
    _df = new Map();
    _docLen = new Map();
    let sumLen = 0;
    for (const doc of _corpus) {
      // Indexar título + texto + categoría con peso x2 al título
      const docText = `${doc.articulo} ${doc.articulo} ${doc.texto} ${doc.categoria}`;
      const toks = _tokens(docText);
      _docLen.set(doc.id, toks.length);
      sumLen += toks.length;
      const tfMap = new Map();
      for (const t of toks) tfMap.set(t, (tfMap.get(t) || 0) + 1);
      for (const [t, tf] of tfMap.entries()) {
        if (!_idx.has(t)) _idx.set(t, new Map());
        _idx.get(t).set(doc.id, tf);
        _df.set(t, (_df.get(t) || 0) + 1);
      }
    }
    _avgLen = sumLen / Math.max(1, _N);
    return _corpus;
  }

  /**
   * Devuelve los k resultados más relevantes a la consulta `q`.
   * Cada resultado incluye el documento original más una propiedad
   * `score` (BM25) y `terminos_acertados` (los términos de la query
   * que se encontraron en el documento).
   */
  function buscar(q, k = 3) {
    if (!_corpus) throw new Error('cargarCorpus() primero');
    const qTokens = _tokens(q);
    if (!qTokens.length) return [];
    const scores = new Map();
    const acertados = new Map();
    for (const t of qTokens) {
      const docs = _idx.get(t);
      if (!docs) continue;
      const idf = Math.log(1 + (_N - docs.size + 0.5) / (docs.size + 0.5));
      for (const [docId, tf] of docs.entries()) {
        const dl = _docLen.get(docId);
        const denom = tf + BM25_K1 * (1 - BM25_B + BM25_B * (dl / _avgLen));
        const contrib = idf * (tf * (BM25_K1 + 1)) / denom;
        scores.set(docId, (scores.get(docId) || 0) + contrib);
        if (!acertados.has(docId)) acertados.set(docId, new Set());
        acertados.get(docId).add(t);
      }
    }
    if (!scores.size) return [];
    const ord = [...scores.entries()].sort((a, b) => b[1] - a[1]).slice(0, k);
    return ord.map(([docId, score]) => {
      const doc = _corpus.find(d => d.id === docId);
      return {
        ...doc,
        score: Math.round(score * 100) / 100,
        terminos_acertados: [...acertados.get(docId)],
      };
    });
  }

  /**
   * Genera sugerencias de preguntas en función de los inputs actuales
   * del simulador (año, plantas, fachada, sci, etc.). Útil para que la
   * usuaria descubra qué puede preguntar sin tener que escribir.
   */
  function sugerenciasParaInput(input) {
    const sug = [];
    const a = input.anio;
    if (a < 1991) sug.push(`¿Mi edificio de ${a} se construyó antes de cualquier normativa de protección contra incendios?`);
    else if (a < 2006) sug.push(`¿Qué exigía la NBE-CPI a un edificio residencial de ${a}?`);
    else if (a >= 2000 && a <= 2019) sug.push(`¿Qué decía el CTE sobre fachadas combustibles en ${a}?`);
    if (input.plantas >= 10) sug.push(`¿Qué instalaciones contra incendios obliga el CTE en mi edificio de ${input.plantas} plantas?`);
    if (input.plantas > 8) sug.push(`¿Cuándo es obligatoria la columna seca?`);
    if (input.fachada === 'composite-acmpe' || input.fachada === 'sate-combustible') {
      sug.push('¿Qué pasó en Campanar y por qué pueden afectarle?');
      sug.push('¿Es obligatorio sustituir mi fachada combustible si ya está construida?');
    }
    if (input.sci !== 'completa') sug.push('¿Cuántos años de antigüedad obligan a hacer la ITE en València?');
    sug.push('¿Cómo se mantiene el sistema contra incendios de la comunidad?');
    return sug.slice(0, 4);
  }

  // Exponer
  window.cendraRAG = { cargarCorpus, buscar, sugerenciasParaInput };
})();
