# Despliegue público de cendra VLC

El frontend (`web/`) es un sitio estático puro: HTML + CSS + JS + tres
GeoJSON pequeños. Cualquier hosting estático lo sirve sin
configuración adicional.

Opciones recomendadas, en orden de simplicidad:

## Opción A · Cloudflare Pages (recomendada)

Por qué encaja: gratis, despliegue continuo desde GitHub, dominio
`*.pages.dev` automático, posibilidad de dominio propio gratis.

### Pasos

1. Acceder a <https://dash.cloudflare.com/?to=/:account/pages> y
 pulsar **Create a project → Connect to Git**.
2. Conectar la cuenta de GitHub y elegir el repositorio
 `imartinsorribes/cendra`.
3. En la configuración del proyecto:
 - **Project name**: `cendra`
 - **Production branch**: `main`
 - **Build command**: _(dejar vacío)_
 - **Build output directory**: `web`
 - **Root directory**: `/`
4. Pulsar **Save and Deploy**. Cloudflare hace el primer despliegue
 en ~30 segundos y devuelve una URL del tipo
 `https://cendra.pages.dev` (o `https://cendra-XX.pages.dev` si
 ese subdominio está cogido).
5. Cada `git push` a `main` lanza un nuevo despliegue automáticamente.

Las cabeceras HTTP que Cloudflare aplica al servir el sitio están en
[`web/_headers`](../web/_headers).

### Despliegue desde la línea de comandos

Equivalente al despliegue automático, útil para previsualizaciones
locales o despliegues manuales puntuales:

```bash
# Una sola vez
npm install -g wrangler

# Cada vez que se quiera desplegar
npx wrangler pages deploy web --project-name cendra
```

El repositorio **no incluye `wrangler.toml`** a propósito: si
Cloudflare lo encontrara, podría intentar desplegar el proyecto como
Worker (que necesita un script JS/TS de entrada) en lugar de como
Pages estático. Los flags `pages deploy ... --project-name` son
suficientes para identificar el proyecto.

## Opción B · GitHub Pages

Por qué considerarla: ya tienes el repositorio en GitHub, no requiere
ninguna cuenta adicional.

Inconveniente: el sitio se sirve desde la raíz del repo, así que
habría que mover el contenido de `web/` a una carpeta `docs/` o
configurar GitHub Pages para servir desde `web/` en la rama `main`.

### Pasos

1. En el repositorio en GitHub → **Settings → Pages**.
2. **Source**: Deploy from a branch.
3. **Branch**: `main` · **Folder**: `/web`.
4. Save. GitHub publica el sitio en
 `https://imartinsorribes.github.io/cendra/` en ~1 minuto.

## Opción C · Netlify

Similar a Cloudflare Pages, con un drag-and-drop opcional desde la
interfaz web.

1. <https://app.netlify.com> → **Add new site → Import an existing project**.
2. Conectar GitHub, elegir el repositorio.
3. **Build command**: vacío. **Publish directory**: `web`.

## Comprobaciones tras el despliegue

Independientemente de la opción elegida, verificar tras el primer
despliegue:

- [ ] El mapa carga la base CARTO Positron (fondo claro con calles).
- [ ] Los 88 barrios aparecen coloreados.
- [ ] Los 6 parques de bomberos aparecen como puntos azules.
- [ ] Al hacer zoom ≥ 13 aparecen los 2.000 edificios destacados.
- [ ] La calculadora reacciona en vivo a cualquier cambio de slider.
- [ ] Los tres botones de escenarios canónicos cargan parámetros y
 mueven el mapa correctamente.
- [ ] La leyenda flotante de la esquina inferior izquierda es legible.
- [ ] En móvil el panel pasa a apilado sobre el mapa.

## Actualizaciones tras un cambio de modelo

Cuando se modifique el modelo (`scripts/calcular_riesgo.py`) hay que
mantener `web/modelo.js` en sincronía. Después:

```bash
python scripts/calcular_riesgo_batch.py
python scripts/preparar_datos_web.py
git add web/data/ data/processed/
git commit -m "Regenerar derivados tras cambio del modelo"
git push
```

Si el despliegue automático está configurado, Cloudflare publica la
nueva versión en menos de un minuto.

## Activar el asistente con IA (Workers AI)

El asistente conversacional del panel derecho usa **Cloudflare
Workers AI** (Llama 3.1 8B) a través de una Pages Function en
`functions/api/asistente.js`. El binding `AI` está disponible
gratis en el plan free de Cloudflare Pages hasta 10.000 peticiones
por día.

Pasos para activarlo en el dashboard:

1. <https://dash.cloudflare.com> → tu proyecto Pages **cendra**.
2. **Settings** → **Functions** → **Bindings** → **Add binding**.
3. Tipo: **Workers AI**. Variable name: `AI` (en mayúsculas, exacto).
4. Guardar y **redesplegar** el último commit (Deployments → ⋯ →
   Retry deployment) para que el binding se inyecte.

Verificación:

```bash
curl -X POST https://cendra.pages.dev/api/asistente \
  -H 'Content-Type: application/json' \
  -d '{"pregunta":"¿Es obligatoria la columna seca en mi edificio?","contexto":{"plantas":14,"anio":2010,"riesgo_total":62}}'
```

Si responde JSON con `{"respuesta": "..."}` está activo. Si devuelve
`{"error":"Workers AI no está enlazado..."}` falta el binding del
paso 3.

## Por qué el asistente no se llama si no está el binding

El frontend siempre intenta llamar a `/api/asistente`. Si el binding
no está configurado, la Function devuelve `503` con un mensaje
explícito. La persona usuaria ve un mensaje rojo en el chat: «Workers
AI no está enlazado en este despliegue». La web sigue funcionando
perfectamente sin asistente — el bloque del chat queda desactivado
pero el resto del atlas opera normalmente.

Esta separación es deliberada: el asistente es un extra de
conveniencia, no un requisito. Cualquiera puede clonar el repo y
desplegar el atlas en su propio Pages sin tener que activar Workers
AI.
