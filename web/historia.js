/*
 * historia.js · Scrollytelling de Campanar.
 *
 * Activa la escena correspondiente del lado fijo cuando la persona
 * que lee llega al paso correspondiente del lado scrolleable. Usa
 * IntersectionObserver con un margen central, así la transición
 * ocurre cuando el paso entra en el centro de la pantalla.
 */
(function () {
  'use strict';

  const escenas = document.querySelectorAll('.escena');
  const pasos = document.querySelectorAll('.paso');
  if (!pasos.length || !escenas.length) return;

  function activar(idx) {
    escenas.forEach((esc, i) => {
      esc.classList.toggle('activa', i === idx);
    });
  }

  // Activar la primera por si nadie scrollea aún
  activar(0);

  // Observador con threshold a la mitad de la pantalla
  const obs = new IntersectionObserver(
    entries => {
      // Encontrar el paso más centrado entre los visibles
      const visibles = entries
        .filter(e => e.isIntersecting)
        .sort((a, b) => b.intersectionRatio - a.intersectionRatio);
      if (!visibles.length) return;
      const idx = parseInt(visibles[0].target.dataset.paso, 10);
      if (!isNaN(idx)) activar(idx);
    },
    {
      // El paso está «activo» cuando su centro pasa por el centro
      // de la pantalla (margen superior e inferior simétricos del 30%).
      rootMargin: '-30% 0px -30% 0px',
      threshold: [0.1, 0.5, 1.0],
    },
  );

  pasos.forEach(p => obs.observe(p));

  // Generar las ventanas del SVG del edificio dinámicamente
  // (14 plantas x 4 ventanas = 56 cuadritos). Lo hacemos en JS
  // para no inflar el HTML.
  document.querySelectorAll('.escena svg .ventanas').forEach(g => {
    const filas = 14;
    const cols = 4;
    const yTop = 70;
    const ventH = 14;
    const ventW = 22;
    const margenY = 4;
    const margenX = 8;
    const xStart = 50;
    let svg = '';
    for (let f = 0; f < filas; f++) {
      for (let c = 0; c < cols; c++) {
        const x = xStart + c * (ventW + margenX);
        const y = yTop + f * (ventH + margenY);
        svg += `<rect x="${x}" y="${y}" width="${ventW}" height="${ventH}" fill="#fbf8f3" opacity="0.85"/>`;
      }
    }
    g.innerHTML = svg;
  });
})();
