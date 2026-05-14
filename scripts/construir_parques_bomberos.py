"""
Construye la capa `data/raw/parques_bomberos.geojson` con la ubicación
de los seis parques operativos del SPEIS (Servei de Prevenció,
Extinció d'Incendis i Salvament) del Ajuntament de València.

Este dataset NO está en el portal de datos abiertos municipal: solo
están disponibles los hidrantes y las fites para vehículos de bomberos.
Los parques operativos se documentan en `valencia.es/cas/bomberos/parques/`
pero como contenido HTML, no como capa abierta. Esta capa propia es,
por tanto, una contribución del proyecto bajo CC BY 4.0.

Direcciones canónicas obtenidas de la web oficial del Ajuntament
(Infociudad) y verificadas en una segunda fuente (Páginas Amarillas o
foro corporativo) el 2026-05-14. Trazabilidad detallada en
`data/raw/parques_bomberos_FUENTES.md`.

Las coordenadas se geocodifican con Nominatim de OpenStreetMap, que es
una opción abierta, gratuita y reproducible. Si Nominatim falla o
devuelve una coordenada fuera del recinto, se usa la coordenada manual
de respaldo verificada en el mapa oficial del Ajuntament.

Uso:
    python scripts/construir_parques_bomberos.py
"""
from __future__ import annotations

import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_GEOJSON = ROOT / "data" / "raw" / "parques_bomberos.geojson"
OUT_GEOJSON.parent.mkdir(parents=True, exist_ok=True)

NOMINATIM = "https://nominatim.openstreetmap.org/search"
UA = "cendra-fetch/0.1 (+https://github.com/imartinsorribes/cendra)"


# Cada parque se documenta con:
#   - nombre canónico (oficial del Ajuntament)
#   - dirección postal canónica
#   - código postal
#   - teléfono operativo
#   - consulta para Nominatim (formato libre, en castellano)
#   - lat / lon de respaldo verificada manualmente en mapa oficial
#     (consulta del 2026-05-14). Si Nominatim falla, se usan estas.
PARQUES: list[dict] = [
    {
        "nombre": "Parque Central de Bomberos",
        "direccion": "Avinguda de la Plata, s/n",
        "codigo_postal": "46013",
        "telefono": "962087787",
        "consulta_nominatim": "Avenida de la Plata 20, 46013 Valencia, España",
        "lon_fallback": -0.3805,
        "lat_fallback": 39.4475,
    },
    {
        "nombre": "Parque de Bomberos Campanar",
        "direccion": "Bulevard Nord (Prolongación Av. Pío Baroja, paralela a Av. General Avilés), s/n",
        "codigo_postal": "46015",
        "telefono": "962084972",
        "consulta_nominatim": "Avenida Pío Baroja, 46015 Valencia, España",
        "lon_fallback": -0.395,
        "lat_fallback": 39.486,
    },
    {
        "nombre": "Parque de Bomberos Norte",
        "direccion": "Carrer de Daniel Balaciart, s/n",
        "codigo_postal": "46020",
        "telefono": "963539939",
        "consulta_nominatim": "Calle Daniel Balaciart, 46020 Valencia, España",
        "lon_fallback": -0.357,
        "lat_fallback": 39.486,
    },
    {
        "nombre": "Parque de Bomberos Oeste",
        "direccion": "Carrer Músic Ayllón, 8",
        "codigo_postal": "46018",
        "telefono": "962084977",
        "consulta_nominatim": "Calle Músico Ayllón 8, 46018 Valencia, España",
        "lon_fallback": -0.395,
        "lat_fallback": 39.464,
    },
    {
        "nombre": "Parque de Bomberos Centro Histórico",
        "direccion": "Carrer de Dalt, 5 (acceso secundario por C/ San Miguel)",
        "codigo_postal": "46003",
        "telefono": "962087784",
        "consulta_nominatim": "Calle Alta 5, 46003 Valencia, España",
        "lon_fallback": -0.376,
        "lat_fallback": 39.479,
    },
    {
        "nombre": "Parque de Bomberos Saler/Devesa",
        "direccion": "Avinguda dels Pinars, s/n (CV-500, km 8,300)",
        "codigo_postal": "46012",
        "telefono": "963539988",
        "consulta_nominatim": "Avinguda dels Pinars, 46012 El Saler, Valencia, España",
        "lon_fallback": -0.333,
        "lat_fallback": 39.385,
    },
]

# Bbox del término municipal de València para descartar resultados
# fuera de la ciudad (Nominatim puede devolver homónimos en otras
# provincias). bbox aproximado: oeste, sur, este, norte.
BBOX_VLC = (-0.55, 39.30, -0.20, 39.55)


def en_bbox(lon: float, lat: float) -> bool:
    o, s, e, n = BBOX_VLC
    return o <= lon <= e and s <= lat <= n


def geocodificar(consulta: str) -> tuple[float, float] | None:
    """Devuelve (lon, lat) de Nominatim o None si falla."""
    params = urllib.parse.urlencode(
        {
            "q": consulta,
            "format": "json",
            "limit": 1,
            "countrycodes": "es",
            "addressdetails": 0,
        }
    )
    url = f"{NOMINATIM}?{params}"
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            data = json.loads(r.read())
        if not data:
            return None
        lat = float(data[0]["lat"])
        lon = float(data[0]["lon"])
        if not en_bbox(lon, lat):
            return None
        return (lon, lat)
    except Exception as e:
        print(f"  [warn] Nominatim falló para {consulta!r}: {e}", file=sys.stderr)
        return None


def main() -> None:
    features = []
    for p in PARQUES:
        print(f"[geocode] {p['nombre']}", file=sys.stderr)
        coords = geocodificar(p["consulta_nominatim"])
        if coords is None:
            print(
                f"  [fallback] sin resultado válido, uso coords manuales",
                file=sys.stderr,
            )
            lon, lat = p["lon_fallback"], p["lat_fallback"]
            fuente_coords = "manual_2026-05-14"
        else:
            lon, lat = coords
            fuente_coords = "nominatim_osm_2026-05-14"
        print(f"  -> ({lon:.5f}, {lat:.5f})  [{fuente_coords}]", file=sys.stderr)
        time.sleep(1.1)  # política de uso de Nominatim: 1 req/seg

        features.append(
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [lon, lat]},
                "properties": {
                    "nombre": p["nombre"],
                    "direccion": p["direccion"],
                    "codigo_postal": p["codigo_postal"],
                    "telefono": p["telefono"],
                    "fuente_direccion": "valencia.es/infociudad",
                    "fuente_coordenadas": fuente_coords,
                    "fecha_consulta": "2026-05-14",
                },
            }
        )

    out = {
        "type": "FeatureCollection",
        "name": "parques_bomberos_speis_valencia",
        "crs": {"type": "name", "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"}},
        "features": features,
    }
    OUT_GEOJSON.write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"\n-> {OUT_GEOJSON.relative_to(ROOT)} ({len(features)} parques)",
          file=sys.stderr)


if __name__ == "__main__":
    main()
