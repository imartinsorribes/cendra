# Fuentes del fichero `parques_bomberos.geojson`

Capa elaborada manualmente por este proyecto. **No proviene del
catálogo CKAN** del Ayuntamiento de València: en el portal sólo están
los hidrantes municipales (`hidrants-per-als-bombers`) y las fites
elastoméricas para vehículos de bomberos (`fites-bombers-hitos-bomberos`),
no los puntos de servicio.

Fecha de elaboración y consulta de fuentes: **2026-05-14**.
Licencia de los datos derivados: **CC BY 4.0**.

## Procedimiento

1. **Listado de parques operativos** obtenido de la página oficial
 <https://www.valencia.es/cas/bomberos/parques/>.
2. **Dirección postal canónica** de cada parque obtenida de la ficha
 correspondiente del directorio Infociudad municipal
 (`valencia.es/-/infociudad-parque-...`).
3. **Verificación cruzada** con Páginas Amarillas y, donde aplica,
 con el foro corporativo Foro-Bomberos.
4. **Geocodificación** con Nominatim de OpenStreetMap (API pública
 gratuita, política de 1 petición por segundo respetada).
5. **Coordenadas de respaldo** verificadas en el mapa oficial del
 Ajuntament para los casos en que Nominatim devuelve algo fuera del
 término municipal o no encuentra resultado. La columna
 `fuente_coordenadas` del GeoJSON indica para cada parque cuál se
 usó.

## Detalle por parque

| Nombre canónico | Dirección | CP | Teléfono | URL de la ficha oficial |
|---|---|---|---|---|
| Parque Central de Bomberos | Avinguda de la Plata, s/n | 46013 | 96 208 77 87 | <https://www.valencia.es/es/-/infociudad-parque-central-de-bomberos> |
| Parque de Bomberos Campanar | Bulevard Nord (Prolong. Av. Pío Baroja), s/n | 46015 | 96 208 49 72 | <https://www.valencia.es/es/cas/bomberos/parques/-/content/parques?uid=7CAB415A14F5957EC12572C2002405DC> |
| Parque de Bomberos Norte | C/ Daniel Balaciart, s/n | 46020 | 96 353 99 39 | <https://www.valencia.es/-/infociudad-parque-de-bomberos-norte> |
| Parque de Bomberos Oeste | C/ Músic Ayllón, 8 | 46018 | 96 208 49 77 | <https://www.valencia.es/-/infociudad-parque-de-bomberos-oeste-1> |
| Parque de Bomberos Centro Histórico | C/ Dalt, 5 (acceso por C/ San Miguel) | 46003 | 96 208 77 84 | <https://www.valencia.es/es/-/infociudad-parque-de-bomberos-centro-hist%C3%B3rico> |
| Parque de Bomberos Saler/Devesa | Avinguda dels Pinars, s/n (CV-500 km 8,300) | 46012 | 96 353 99 88 | <https://www.valencia.es/es/-/infociudad-parque-de-bomberos-saler/devesa> |

Cuerpo operativo: **Servei de Prevenció, Extinció d'Incendis i Salvament
(SPEIS)** del Ajuntament de València.

## Lo que NO está incluido

- **Servicios Generales** (parque administrativo / logística). Es una
 instalación de soporte sin operativa de respuesta a incendios.
- **Parques del Consorcio Provincial de Bombers de València** que estén
 fuera del término municipal. Son competencia provincial y atienden a
 los municipios de la provincia, no a la ciudad de València. Sus
 parques sí pueden cubrir reservas, pero el SPEIS municipal es el
 servicio primario dentro de la ciudad.

## Versionado de la capa

Si los parques operativos cambian (apertura, traslado, cierre), la capa
debe regenerarse ejecutando:

```
python scripts/construir_parques_bomberos.py
```

y actualizando este documento con la fecha de la nueva consulta.
