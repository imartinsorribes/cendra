# Fuentes encontradas para cendra VLC

> Filtrado automático del catálogo CKAN del portal de datos
> abiertos de l'Ajuntament de València (`opendata.vlci.valencia.es`).

- **Fecha del análisis**: 2026-05-14
- **Fuente**: `data/raw/ckan_package_search_0.json`
- **Datasets totales en el portal**: 294
- **Datasets que matchean al menos un tema**: 130
- **Reproducible con**: `python scripts/fetch_catalogo_vlci.py` y después `python scripts/filtrar_catalogo_incendio.py`

Cada dataset se asigna al primer tema que matchea según el orden
de `TEMAS` en el script. Un dataset puede aparecer en más temas
(columna *otros temas*), pero solo se lista en su tema principal.


## Núcleo · incendio, bomberos, emergencia

_2 datasets._

| Título | Org. | Recursos | Formatos | Última act. | Keywords | Otros temas |
|---|---|---|---|---|---|---|
| [Hidrants per als bombers](https://opendata.vlci.valencia.es/dataset/hidrants-per-als-bombers) | Ajuntament de València | 5 | GEOJSON|HTML|JSON|KMZ|PBF | 2026-02-19 | bomber, hidrant, incendi | equipamientos, edificacion |
| [Fites Bombers](https://opendata.vlci.valencia.es/dataset/fites-bombers-hitos-bomberos) | Ajuntament de València | 5 | GEOJSON|HTML|JSON|KMZ|PBF | 2026-02-18 | bomber |  |

### Detalle de los datasets del núcleo

#### Hidrants per als bombers

- URL del portal: <https://opendata.vlci.valencia.es/dataset/hidrants-per-als-bombers>
- Organización: Ajuntament de València
- Última actualización: 2026-02-19
- Licencia: cc-by
- Descripción: Xarxa d'hidrants de protecció contra incendis.    Font: Geoportal https://geoportal.valencia.es/apps/GeoportalHome/es/inicio/geodatos-abiertos  
- Recursos (5):
  - **JSON** Hidrants per als bombers — <https://geoportal.valencia.es/server/rest/services/OPENDATA/UrbanismoEInfraestructuras/MapServer/222/query?where=1=1&outFields=*&f=json>
  - **HTML** Hidrants per als bombers — <https://geoportal.valencia.es/server/rest/services/OPENDATA/UrbanismoEInfraestructuras/MapServer/222/query?where=1=1&outFields=*&f=html>
  - **KMZ** Hidrants per als bombers — <https://geoportal.valencia.es/server/rest/services/OPENDATA/UrbanismoEInfraestructuras/MapServer/222/query?where=1=1&outFields=*&f=kmz>
  - **GeoJSON** Hidrants per als bombers — <https://geoportal.valencia.es/server/rest/services/OPENDATA/UrbanismoEInfraestructuras/MapServer/222/query?where=1=1&outFields=*&f=geojson>
  - **pbf** Hidrants per als bombers — <https://geoportal.valencia.es/server/rest/services/OPENDATA/UrbanismoEInfraestructuras/MapServer/222/query?where=1=1&outFields=*&f=pbf>

#### Fites Bombers

- URL del portal: <https://opendata.vlci.valencia.es/dataset/fites-bombers-hitos-bomberos>
- Organización: Ajuntament de València
- Última actualización: 2026-02-18
- Licencia: cc-by
- Descripción: Fites de material elastòmer que flexionen 90º per a l'accés de vehicles de bombers. 
- Recursos (5):
  - **JSON** Fites Bombers — <https://geoportal.valencia.es/server/rest/services/OPENDATA/Trafico/MapServer/239/query?where=1=1&outFields=*&f=json>
  - **HTML** Fites Bombers — <https://geoportal.valencia.es/server/rest/services/OPENDATA/Trafico/MapServer/239/query?where=1=1&outFields=*&f=html>
  - **KMZ** Fites Bombers — <https://geoportal.valencia.es/server/rest/services/OPENDATA/Trafico/MapServer/239/query?where=1=1&outFields=*&f=kmz>
  - **GeoJSON** Fites Bombers — <https://geoportal.valencia.es/server/rest/services/OPENDATA/Trafico/MapServer/239/query?where=1=1&outFields=*&f=geojson>
  - **pbf** Fites Bombers — <https://geoportal.valencia.es/server/rest/services/OPENDATA/Trafico/MapServer/239/query?where=1=1&outFields=*&f=pbf>


## Vulnerabilidad social y riesgo

_12 datasets._

| Título | Org. | Recursos | Formatos | Última act. | Keywords | Otros temas |
|---|---|---|---|---|---|---|
| [Estat de liquidació d'ingressos](https://opendata.vlci.valencia.es/dataset/estats_liq_ingresos_tot_2021-22_val_clean2) | Ajuntament de València | 1 | CSV | 2026-04-15 | ingres |  |
| [Ingressos i gastos. Pressuposts de 2020 a 2025](https://opendata.vlci.valencia.es/dataset/ingresos-y-gastos-presupuestos) | Ajuntament de València | 1 | CSV | 2026-04-01 | ingres |  |
| [Població en risc de pobresa relativa considerant el llindar nacional de pobresa segons ingressos](https://opendata.vlci.valencia.es/dataset/1_1) | Ajuntament de València | 1 | XLSX | 2026-03-19 | ingres, pobresa, pobreza, riesgo | contexto |
| [Vulnerabilitat per barris 2021](https://opendata.vlci.valencia.es/dataset/vulnerabilidad-por-barrios) | Ajuntament de València | 3 | CSV|GEOJSON|SHP | 2026-03-19 | vulnerab | equipamientos, edificacion, contexto |
| [Pressupost ingressos 2023 - 2025 per codi económic](https://opendata.vlci.valencia.es/dataset/presupuesto-ingresos-por-codigo-economico) | Ajuntament de València | 1 | CSV | 2026-03-16 | ingres |  |
| [Pressupost d'ingressos. Resum per articles 2023 - 2025](https://opendata.vlci.valencia.es/dataset/presupuesto-de-ingresos-resumen-por-articulos) | Ajuntament de València | 1 | CSV | 2026-03-16 | ingres |  |
| [Pressupost d'ingressos. Llistat econòmic 2023 - 2025](https://opendata.vlci.valencia.es/dataset/presupuesto-de-ingresos-listado-economico) | Ajuntament de València | 1 | CSV | 2026-03-16 | ingres |  |
| [Nombre total d'expedients d'ajuda a ciutadans en risc d'exclusió hídrica que s'han obert](https://opendata.vlci.valencia.es/dataset/is-bis-006) | Ajuntament de València | 1 | CSV | 2025-06-13 | riesgo, risc |  |
| [Nombre total d'expedients d'ajuda a ciutadans en risc d'exclusió hídrica que s'han resolt](https://opendata.vlci.valencia.es/dataset/is-bis-007) | Ajuntament de València | 1 | CSV | 2025-06-13 | riesgo, risc |  |
| [Imports pagats d'expedients d'ajuda a ciutadans en risc d'exclusió hídrica](https://opendata.vlci.valencia.es/dataset/is-bis-008) | Ajuntament de València | 1 | CSV | 2025-06-13 | riesgo, risc |  |
| [Ingressos per recàrrega de targeta de prepagament](https://opendata.vlci.valencia.es/dataset/is_sct_230305) | Ajuntament de València | 1 | CSV | 2024-04-29 | ingres |  |
| [Renda per llar i persona](https://opendata.vlci.valencia.es/dataset/income-per-household-and-person) | Ajuntament de València | 3 | CSV | 2022-11-17 | renta |  |


## Equipamientos sensibles (residencias, sanitarios, escolares)

_41 datasets._

| Título | Org. | Recursos | Formatos | Última act. | Keywords | Otros temas |
|---|---|---|---|---|---|---|
| [Equipamients municipals](https://opendata.vlci.valencia.es/dataset/equipamients-municipals-equipamientos-municipales) | Ajuntament de València | 5 | GEOJSON|HTML|JSON|KMZ|PBF | 2026-04-16 | equipament |  |
| [Fonts PUSDAR](https://opendata.vlci.valencia.es/dataset/pudsar-sources) | Ajuntament de València | 1 | GEOJSON | 2026-04-02 | salud, salut |  |
| [Dades horaris qualitat de l'aire desde 2016](https://opendata.vlci.valencia.es/dataset/hourly-air-quality-data-since-2016) | Ajuntament de València | 3 | CSV | 2026-04-02 | salud |  |
| [Dades emissions GEI a València](https://opendata.vlci.valencia.es/dataset/gei-emissions-data-in-valencia) | Ajuntament de València | 3 | CSV | 2026-04-02 | salud |  |
| [Recursos socials dirigits a majors](https://opendata.vlci.valencia.es/dataset/recursos-socials-dirigits-a-majors) | Ajuntament de València | 8 | CSV|DWG|GEOJSON|GML|KML|SHZ|WFS|WMS | 2026-04-01 | mayor |  |
| [Hospitals i altres centres sanitaris 2024](https://opendata.vlci.valencia.es/dataset/hospitales) | Ajuntament de València | 3 | CSV|GEOJSON|SHP | 2026-03-24 | hospital, salud, sanitari |  |
| [Velocitat Carrers](https://opendata.vlci.valencia.es/dataset/velocitat-carrers-velocidad-calles) | Ajuntament de València | 5 | GEOJSON|HTML|JSON|KMZ|PBF | 2026-03-23 | residenci | edificacion, contexto |
| [Mapa soroll vesprada (2022)](https://opendata.vlci.valencia.es/dataset/mapa-soroll-vesprada-mapa-ruido-tarde) | Ajuntament de València | 5 | GEOJSON|HTML|JSON|KMZ|PBF | 2026-03-23 | salud, salut |  |
| [Mapa soroll nit (2022)](https://opendata.vlci.valencia.es/dataset/mapa-soroll-nit-mapa-ruido-noche) | Ajuntament de València | 5 | GEOJSON|HTML|JSON|KMZ|PBF | 2026-03-23 | salud, salut |  |
| [Mapa soroll dia (2022)](https://opendata.vlci.valencia.es/dataset/mapa-soroll-dia-mapa-ruido-dia) | Ajuntament de València | 5 | GEOJSON|HTML|JSON|KMZ|PBF | 2026-03-23 | salud, salut |  |
| [Mapa soroll 24h (2022)](https://opendata.vlci.valencia.es/dataset/mapa-soroll-24h-mapa-ruido-24h) | Ajuntament de València | 5 | GEOJSON|HTML|JSON|KMZ|PBF | 2026-03-23 | mayor, salud, salut |  |
| [Colecamins](https://opendata.vlci.valencia.es/dataset/colecamins) | Ajuntament de València | 5 | GEOJSON|HTML|JSON|KMZ|PBF | 2026-03-20 | colegio |  |
| [Cartografia Base Toponímia](https://opendata.vlci.valencia.es/dataset/cartografia-base-toponimia-toponimia) | Ajuntament de València | 5 | GEOJSON|HTML|JSON|KMZ|PBF | 2026-03-20 | mayor | edificacion |
| [Cartografia Base quadrícula 500](https://opendata.vlci.valencia.es/dataset/cartografia-base-quadriculacuadricula-500) | Ajuntament de València | 5 | GEOJSON|HTML|JSON|KMZ|PBF | 2026-03-20 | mayor | edificacion |
| [Cartografia Base quadrícula 2000](https://opendata.vlci.valencia.es/dataset/cartografia-base-quadriculacuadricula-2000) | Ajuntament de València | 5 | GEOJSON|HTML|JSON|KMZ|PBF | 2026-03-20 | mayor | edificacion |
| [Cartografia Base Orografia](https://opendata.vlci.valencia.es/dataset/cartografia-base-orografia) | Ajuntament de València | 5 | GEOJSON|HTML|JSON|KMZ|PBF | 2026-03-20 | mayor | edificacion |
| [Cartografia Base Hidrografia](https://opendata.vlci.valencia.es/dataset/cartografia-base-hidrografia) | Ajuntament de València | 5 | GEOJSON|HTML|JSON|KMZ|PBF | 2026-03-20 | mayor | edificacion |
| [Cartografia Base Edificis](https://opendata.vlci.valencia.es/dataset/cartografia-base-edificis-edificios) | Ajuntament de València | 5 | GEOJSON|HTML|JSON|KMZ|PBF | 2026-03-20 | mayor | edificacion |
| [Cartografia Base Construccions Puntuals](https://opendata.vlci.valencia.es/dataset/cartografia-base-construcciones-puntuals-construcciones-puntuales) | Ajuntament de València | 5 | GEOJSON|HTML|JSON|KMZ|PBF | 2026-03-20 | mayor | edificacion |
| [Cartografia Base Construccions](https://opendata.vlci.valencia.es/dataset/cartografia-base-construcciones-construcciones) | Ajuntament de València | 5 | GEOJSON|HTML|JSON|KMZ|PBF | 2026-03-20 | mayor | edificacion |
| [Cartografia Base Comunicacions](https://opendata.vlci.valencia.es/dataset/cartografia-base-comunicacions-comunicaciones) | Ajuntament de València | 5 | GEOJSON|HTML|JSON|KMZ|PBF | 2026-03-20 | mayor | edificacion |
| [Cartografia Base Vegetació](https://opendata.vlci.valencia.es/dataset/cartografia-base-vegetacio-vegetacion) | Ajuntament de València | 5 | DBASE|GEOJSON|HTML|JSON|KMZ | 2026-03-20 | mayor | edificacion |
| [Cartografia Base Punts de Cota](https://opendata.vlci.valencia.es/dataset/cartografia-base-punt-de-cota-puntos-de-cota) | Ajuntament de València | 5 | GEOJSON|HTML|JSON|KMZ|PBF | 2026-03-20 | mayor | edificacion |
| [Centres Educatius en València](https://opendata.vlci.valencia.es/dataset/centros-educativos-en-valencia) | Ajuntament de València | 3 | CSV|GEOJSON|SHP | 2026-03-19 | educac, escola, escuel |  |
| [Informació quadre de mando àrea de prioritat residència (APR)](https://opendata.vlci.valencia.es/dataset/dataset_pasos-sanciones_mobilidad) | Ajuntament de València | 1 | CSV | 2026-03-17 | residenci |  |
| [Dades per hores qualitat aire 2021-2022](https://opendata.vlci.valencia.es/dataset/rvvcca_d_horarios_2021-2022) | Ajuntament de València | 1 | CSV | 2026-03-16 | salud |  |
| [Dades per hores qualitat aire 2016-2020](https://opendata.vlci.valencia.es/dataset/rvvcca_d_horarios_2016-2020) | Ajuntament de València | 1 | CSV | 2026-03-16 | salud |  |
| [Places vacants Ajuntament València 2023 - 2025](https://opendata.vlci.valencia.es/dataset/plazas-vacantes-ayuntamiento-valencia) | Ajuntament de València | 1 | CSV | 2026-03-16 | educac, escola |  |
| [Nivells i servicis RRCC 2023 - 2024](https://opendata.vlci.valencia.es/dataset/niveles-y-servicios-rrcc-2023-2024) | Ajuntament de València | 1 | CSV | 2026-03-16 | educac, escola |  |
| [Zones ZAS](https://opendata.vlci.valencia.es/dataset/zones-zas-zonas-zas) | Ajuntament de València | 5 | GEOJSON|HTML|JSON|KMZ|PBF | 2026-02-28 | salud |  |
| [Zones Jocs Infantils](https://opendata.vlci.valencia.es/dataset/zones-jocs-infantils-zona-juegos-infantiles) | Ajuntament de València | 5 | GEOJSON|HTML|JSON|KMZ|PBF | 2026-02-28 | educac |  |
| [Majors](https://opendata.vlci.valencia.es/dataset/majors-mayores) | Ajuntament de València | 5 | GEOJSON|HTML|JSON|KMZ|PBF | 2026-02-23 | mayor | contexto |
| [Area Prioritat Residencial](https://opendata.vlci.valencia.es/dataset/area-prioridad-residencial) | Ajuntament de València | 5 | GEOJSON|HTML|JSON|KMZ|PBF | 2026-02-13 | residenci | edificacion |
| [Consum elèctric 2018-2022](https://opendata.vlci.valencia.es/dataset/consumo-electrico-2018-2022) | Ajuntament de València | 1 | XLSX | 2026-02-09 | colegio |  |
| [Número de incidències](https://opendata.vlci.valencia.es/dataset/is_sct_230307) | Ajuntament de València | 1 | CSV | 2024-04-29 | equipament |  |
| [Àrees Escolarització](https://opendata.vlci.valencia.es/dataset/arees-escolaritzacio) | Ajuntament de València | 8 | CSV|DWG|GEOJSON|GML|KML|SHZ|WFS|WMS | 2022-04-13 | educac, escola |  |
| [Equipaments Municipales](https://opendata.vlci.valencia.es/dataset/equipaments-municipales) | Ajuntament de València | 8 | CSV|DWG|GEOJSON|GML|KML|SHZ|WFS|WMS | 2022-04-11 | equipament, sanitari | contexto |
| [Mapa Soroll Nit (23-7h)](https://opendata.vlci.valencia.es/dataset/mapa-soroll-nit-23-7h) | Ajuntament de València | 8 | CSV|DWG|GEOJSON|GML|KML|SHZ|WFS|WMS | 2022-04-08 | salud |  |
| [Mapa Soroll Dia (7h-19h)](https://opendata.vlci.valencia.es/dataset/mapa-soroll-dia-7h-19h) | Ajuntament de València | 8 | CSV|DWG|GEOJSON|GML|KML|SHZ|WFS|WMS | 2022-04-08 | salud |  |
| [Mapa Soroll LDen 24 h](https://opendata.vlci.valencia.es/dataset/mapa-soroll-lden-24-h) | Ajuntament de València | 8 | CSV|DWG|GEOJSON|GML|KML|SHZ|WFS|WMS | 2022-04-08 | mayor, salud |  |
| [Mapa Soroll Vesprada (19-23h)](https://opendata.vlci.valencia.es/dataset/mapa-soroll-vesprada-19-23h) | Ajuntament de València | 8 | CSV|DWG|GEOJSON|GML|KML|SHZ|WFS|WMS | 2022-04-05 | salud |  |


## Edificación y vivienda

_32 datasets._

| Título | Org. | Recursos | Formatos | Última act. | Keywords | Otros temas |
|---|---|---|---|---|---|---|
| [Habitatge lliure (preu metre quadrat)](https://opendata.vlci.valencia.es/dataset/free-housing-square-meter-price) | Ajuntament de València | 3 | CSV | 2026-04-02 | habitatg, vivienda |  |
| [Mobiliari urbà](https://opendata.vlci.valencia.es/dataset/servicios-e-instalaciones) | Ajuntament de València | 5 | GEOJSON|HTML|JSON|KMZ|PBF | 2026-03-23 | construcci |  |
| [Registre de Programes d'Actuació Integrada](https://opendata.vlci.valencia.es/dataset/egistro-de-programas-de-actuacion-integrada-registre-de-programes-dactuacio-int) | Ajuntament de València | 5 | GEOJSON|HTML|JSON|KMZ|PBF | 2026-03-23 | catastr, edifici |  |
| [Registre de Programes d'Actuació Aïllada](https://opendata.vlci.valencia.es/dataset/registro-de-programas-de-actuacion-aislada-registre-de-programes-dactuacio-ailla) | Ajuntament de València | 5 | GEOJSON|HTML|JSON|KMZ|PBF | 2026-03-23 | catastr |  |
| [Programes d'Actuació Integrada](https://opendata.vlci.valencia.es/dataset/programas-de-actuacion-integrada-programes-dactuacio-integrada) | Ajuntament de València | 5 | GEOJSON|HTML|JSON|KMZ|PBF | 2026-03-23 | catastr, edifici |  |
| [Parcel·les cadastrals rústica](https://opendata.vlci.valencia.es/dataset/parcelles-cadastrals-rustica-parcelas-catastrales-rustica) | Ajuntament de València | 5 | GEOJSON|HTML|JSON|KMZ|PBF | 2026-03-23 | catastr |  |
| [Llibre Registre Solars](https://opendata.vlci.valencia.es/dataset/libro-registro-solares-libre-registre-solars) | Ajuntament de València | 5 | GEOJSON|HTML|JSON|KMZ|PBF | 2026-03-23 | catastr, edifici |  |
| [Llibre Registre Edificis](https://opendata.vlci.valencia.es/dataset/libro-registro-edificios-llibre-registre-edificis) | Ajuntament de València | 5 | GEOJSON|HTML|JSON|KMZ|PBF | 2026-03-23 | catastr, edifici |  |
| [Illes](https://opendata.vlci.valencia.es/dataset/illes-amb-dades-de-poblacio-manzanas-con-datos-de-poblacion) | Ajuntament de València | 5 | GEOJSON|HTML|JSON|KMZ|PBF | 2026-03-23 | catastr, manzana | contexto |
| [Catàleg estructural urbà (BIC, BRL, BC, CH o NHT)](https://opendata.vlci.valencia.es/dataset/catalogo-urbano) | Ajuntament de València | 5 | GEOJSON|HTML|JSON|KMZ|PBF | 2026-03-20 | construcci | contexto |
| [Catàleg estructural rural (BIC, BRL, BC, CH o NHT) - línies](https://opendata.vlci.valencia.es/dataset/catalogo-rural-lineas) | Ajuntament de València | 5 | GEOJSON|HTML|JSON|KMZ|PBF | 2026-03-20 | construcci | contexto |
| [Catàleg estructural rural (BIC, BRL, BC, CH o NHT) - àrees](https://opendata.vlci.valencia.es/dataset/catalogo-rural) | Ajuntament de València | 5 | GEOJSON|HTML|JSON|KMZ|PBF | 2026-03-20 | construcci | contexto |
| [Cartografia Base Vorades](https://opendata.vlci.valencia.es/dataset/cartografia-base-vorades-bordillos) | Ajuntament de València | 5 | GEOJSON|HTML|JSON|KMZ|PBF | 2026-03-20 | catastr, edifici |  |
| [Xarxa Topogràfica Municipal](https://opendata.vlci.valencia.es/dataset/xarxa-topografica-municipal-red-topografica-municipal) | Ajuntament de València | 5 | GEOJSON|HTML|JSON|KMZ|PBF | 2026-02-28 | edifici |  |
| [Vivendes Protecció Pública (VPP)](https://opendata.vlci.valencia.es/dataset/vivendes-proteccio-publica-vpp-viviendas-proteccion-publica-vpp) | Ajuntament de València | 5 | GEOJSON|HTML|JSON|KMZ|PBF | 2026-02-26 | edifici, vivienda |  |
| [Ruta del Patrimoni Industrial del Grau](https://opendata.vlci.valencia.es/dataset/ruta-del-patrimonio-industrial-del-grao) | Ajuntament de València | 5 | GEOJSON|HTML|JSON|KMZ|PBF | 2026-02-25 | edifici |  |
| [Quioscs premsa](https://opendata.vlci.valencia.es/dataset/quioscs-premsa-quioscos-prensa) | Ajuntament de València | 5 | GEOJSON|HTML|JSON|KMZ|PBF | 2026-02-24 | edifici |  |
| [Quioscs flors](https://opendata.vlci.valencia.es/dataset/quioscs-flors-quioscos-flores) | Ajuntament de València | 5 | GEOJSON|HTML|JSON|KMZ|PBF | 2026-02-24 | edifici |  |
| [Quiosc ONCE](https://opendata.vlci.valencia.es/dataset/quiosc-once-quiosco-once) | Ajuntament de València | 5 | GEOJSON|HTML|JSON|KMZ|PBF | 2026-02-24 | edifici |  |
| [Portals dels carrers](https://opendata.vlci.valencia.es/dataset/portals-dels-carrers-portales-de-las-calles) | Ajuntament de València | 5 | GEOJSON|HTML|JSON|KMZ|PBF | 2026-02-24 | edifici | contexto |
| [Mupis OCOVAL](https://opendata.vlci.valencia.es/dataset/mupis-ocoval) | Ajuntament de València | 5 | GEOJSON|HTML|JSON|KMZ|PBF | 2026-02-23 | edifici |  |
| [Monuments turístics](https://opendata.vlci.valencia.es/dataset/monuments-turistics-monumentos-turisticos) | Ajuntament de València | 5 | GEOJSON|HTML|JSON|KMZ|PBF | 2026-02-23 | edifici |  |
| [Pilons extraïbles](https://opendata.vlci.valencia.es/dataset/pilons-extraibles-bolardos-extraibles) | Ajuntament de València | 5 | GEOJSON|HTML|JSON|KMZ|PBF | 2026-02-19 | edifici |  |
| [Estacionament Nocturn Permés BUS](https://opendata.vlci.valencia.es/dataset/estacionament-nocturn-permes-bus-estacionamiento-nocturno-permitido-bus) | Ajuntament de València | 5 | GEOJSON|HTML|JSON|KMZ|PBF | 2026-02-17 | edifici |  |
| [Edificacions Industrials](https://opendata.vlci.valencia.es/dataset/edificaciones-industriales) | Ajuntament de València | 5 | GEOJSON|HTML|JSON|KMZ|PBF | 2026-02-17 | edifici |  |
| [Àmbits de Foment de l'Edificació](https://opendata.vlci.valencia.es/dataset/ambitos-de-fomento-de-la-edificacion-ambits-de-foment-de-ledificacio) | Ajuntament de València | 5 | GEOJSON|HTML|JSON|KMZ|PBF | 2026-02-12 | edifici |  |
| [Textos dels portals dels carrers](https://opendata.vlci.valencia.es/dataset/textos-dels-portals-dels-carrers) | Ajuntament de València | 8 | CSV|DWG|GEOJSON|GML|KML|SHZ|WFS|WMS | 2022-10-25 | altura | contexto |
| [Parcel·les cadastrals de rústica amb fitxa urbanística](https://opendata.vlci.valencia.es/dataset/parcel-les-cadastrals-de-rustica-amb-fitxa-urbanistica) | Ajuntament de València | 8 | CSV|DWG|GEOJSON|GML|KML|SHZ|WFS|WMS | 2022-04-19 | catastr |  |
| [Parcel·les cadastrals d’urbana amb fitxa urbanística](https://opendata.vlci.valencia.es/dataset/parcel-les-cadastrals-d-urbana-amb-fitxa-urbanistica) | Ajuntament de València | 8 | CSV|DWG|GEOJSON|GML|KML|SHZ|WFS|WMS | 2022-04-11 | catastr, construcci, manzana |  |
| [Illa de cases cadastrals amb dades de població](https://opendata.vlci.valencia.es/dataset/illa-de-cases-cadastrals-amb-dades-de-poblacio) | Ajuntament de València | 8 | CSV|DWG|GEOJSON|GML|KML|SHZ|WFS|WMS | 2022-04-05 | catastr, manzana | contexto |
| [PGOU - Alineacions](https://opendata.vlci.valencia.es/dataset/pgou-alineacions) | Ajuntament de València | 8 | CSV|DWG|GEOJSON|GML|KML|SHZ|WFS|WMS | 2022-04-01 | altura |  |
| [Llistat dels carrers](https://opendata.vlci.valencia.es/dataset/llistat-dels-carrers) | Ajuntament de València | 1 | CSV | 2021-09-03 | catastr | contexto |


## Contexto urbano y demográfico

_43 datasets._

| Título | Org. | Recursos | Formatos | Última act. | Keywords | Otros temas |
|---|---|---|---|---|---|---|
| [Queixes i Suggeriments](https://opendata.vlci.valencia.es/dataset/total-castellano) | Ajuntament de València | 1 | CSV | 2026-04-28 | barri |  |
| [Dades diàries del sensor de soroll ubicat al barri de Russafa, en el carrer Capellà Femenía, 14](https://opendata.vlci.valencia.es/dataset/t251234-daily) | Ajuntament de València | 1 | CSV | 2026-04-21 | barri, carrer |  |
| [Relació de drets reals](https://opendata.vlci.valencia.es/dataset/relacio-de-drets-reals) | Ajuntament de València | 1 | CSV | 2026-04-01 | barri, carrer |  |
| [Relació de béns immobles](https://opendata.vlci.valencia.es/dataset/relacio-de-bens-immobles) | Ajuntament de València | 1 | CSV | 2026-04-01 | barri, carrer |  |
| [Aparcaments per districtes-barris](https://opendata.vlci.valencia.es/dataset/car-parks-by-districts-neighborhoods) | Ajuntament de València | 3 | CSV | 2026-04-01 | barri, edad, edat |  |
| [Divisió de les seccions censals de la ciutat](https://opendata.vlci.valencia.es/dataset/divisio-de-les-seccions-censals-de-la-ciutat) | Ajuntament de València | 8 | CSV|DWG|GEOJSON|GML|KML|SHZ|WFS|WMS | 2026-04-01 | barri, població, población |  |
| [Vies](https://opendata.vlci.valencia.es/dataset/vias) | Ajuntament de València | 5 | GEOJSON|HTML|JSON|KMZ|PBF | 2026-03-23 | carrer |  |
| [ValenBisi Disponibilitat](https://opendata.vlci.valencia.es/dataset/valenbisi-disponibilitat-valenbisi-dsiponibilidad) | Ajuntament de València | 5 | GEOJSON|HTML|JSON|KMZ|PBF | 2026-03-23 | carrer |  |
| [Guals](https://opendata.vlci.valencia.es/dataset/guals-vados) | Ajuntament de València | 5 | GEOJSON|HTML|JSON|KMZ|PBF | 2026-03-23 | carrer |  |
| [Eixos de carrer](https://opendata.vlci.valencia.es/dataset/eixos-de-carrer-ejes-de-calle) | Ajuntament de València | 5 | GEOJSON|HTML|JSON|KMZ|PBF | 2026-03-20 | carrer |  |
| [Barris](https://opendata.vlci.valencia.es/dataset/barris-barrios) | Ajuntament de València | 5 | GEOJSON|HTML|JSON|KMZ|PBF | 2026-03-20 | barri |  |
| [Aparcament per a motos](https://opendata.vlci.valencia.es/dataset/aparcament-per-a-motos-aparcamiento-para-motos) | Ajuntament de València | 5 | DBASE|GEOJSON|HTML|JSON|KMZ | 2026-03-20 | carrer |  |
| [Recolzaments propostes DecidimVLC](https://opendata.vlci.valencia.es/dataset/apoyo-propuestas-decidimvlc) | Ajuntament de València | 1 | CSV | 2026-03-19 | barri |  |
| [Rebuts guals 2020 - 2025](https://opendata.vlci.valencia.es/dataset/recibos-vados-2020-2025) | Ajuntament de València | 1 | CSV | 2026-03-16 | barri |  |
| [Rebuts IVTM 2020 al 2025](https://opendata.vlci.valencia.es/dataset/dataset_ivtm_2020-2025-cas) | Ajuntament de València | 1 | CSV | 2026-03-16 | barri |  |
| [Rebuts taules i cadires 2020 - 2025](https://opendata.vlci.valencia.es/dataset/recibos-mesas-y-sillas-2020-2025) | Ajuntament de València | 1 | CSV | 2026-03-16 | barri |  |
| [Rebuts IBI 2021 - 2025](https://opendata.vlci.valencia.es/dataset/recibos-ibi-2020-2025) | Ajuntament de València | 1 | CSV | 2026-03-16 | barri |  |
| [Rebuts IAE 2020-2025](https://opendata.vlci.valencia.es/dataset/recibos_iae_2020-2025) | Ajuntament de València | 1 | CSV | 2026-03-16 | barri |  |
| [Seccions censals](https://opendata.vlci.valencia.es/dataset/seccions-censals-secciones-censales) | Ajuntament de València | 5 | GEOJSON|HTML|JSON|KMZ|PBF | 2026-02-25 | barri, demograf, població, población |  |
| [Rutes Turisme Barri](https://opendata.vlci.valencia.es/dataset/rutas-turismo-barrio) | Ajuntament de València | 5 | GEOJSON|HTML|JSON|KMZ|PBF | 2026-02-25 | barri |  |
| [Barris Policials](https://opendata.vlci.valencia.es/dataset/barris-policials-barrios-policiales) | Ajuntament de València | 5 | GEOJSON|HTML|JSON|KMZ|PBF | 2026-02-13 | barri |  |
| [Àmbit territorial servicis socials](https://opendata.vlci.valencia.es/dataset/ambit-servicis-socials-ambito-servicios-sociales) | Ajuntament de València | 5 | GEOJSON|HTML|JSON|KMZ|PBF | 2026-02-12 | barri |  |
| [Dades diàries del sensor de soroll ubicat al barri de Russafa, en el carrer Sueca, amb carrer Dénia](https://opendata.vlci.valencia.es/dataset/t248652-daily) | Ajuntament de València | 1 | CSV | 2025-05-20 | barri, carrer |  |
| [Dades diàries del sensor de soroll ubicat al barri de Russafa, en el carrer Cadis, 16](https://opendata.vlci.valencia.es/dataset/t248671-daily) | Ajuntament de València | 1 | CSV | 2025-05-20 | barri, carrer |  |
| [Dades diàries del sensor de soroll ubicat al barri de Russafa, en el carrer Cadis, 3](https://opendata.vlci.valencia.es/dataset/t248655-daily) | Ajuntament de València | 1 | CSV | 2025-05-20 | barri, carrer |  |
| [Dades diàries del sensor de soroll ubicat al barri de Russafa, en el carrer Cuba, 3](https://opendata.vlci.valencia.es/dataset/t248682-daily) | Ajuntament de València | 1 | CSV | 2025-05-20 | barri, carrer |  |
| [Dades diàries del sensor de soroll ubicat al barri de Russafa, en el carrer Sueca, 2](https://opendata.vlci.valencia.es/dataset/t248683-daily) | Ajuntament de València | 1 | CSV | 2025-05-20 | barri, carrer |  |
| [Dades diàries del sensor de soroll ubicat al barri de Russafa, en el carrer Sueca, 61](https://opendata.vlci.valencia.es/dataset/t248684-daily) | Ajuntament de València | 1 | CSV | 2025-05-20 | barri, carrer |  |
| [Dades diàries del sensor de soroll ubicat al barri de Russafa, en el carrer Sueca, 32](https://opendata.vlci.valencia.es/dataset/t248680-daily) | Ajuntament de València | 1 | CSV | 2025-05-20 | barri, carrer |  |
| [Dades diàries del sensor de soroll ubicat al barri de Russafa, en el carrer Carles Cervera, chaflà amb Reina Doña María](https://opendata.vlci.valencia.es/dataset/t248670-daily) | Ajuntament de València | 1 | CSV | 2025-05-20 | barri, carrer |  |
| [Dades diàries del sensor de soroll ubicat al barri de Russafa, en el carrer Salvador Abril, chaflà amb Maestro José Serrano](https://opendata.vlci.valencia.es/dataset/t248676-daily) | Ajuntament de València | 1 | CSV | 2025-05-20 | barri, carrer |  |
| [Dades diàries del sensor de soroll ubicat al barri de Russafa, en el carrer Vivons, chaflà amb Cadis](https://opendata.vlci.valencia.es/dataset/t248677-daily) | Ajuntament de València | 1 | CSV | 2025-05-20 | barri, carrer |  |
| [Dades diàries del sensor de soroll ubicat al barri de Russafa, en el carrer Carles Cervera, 34](https://opendata.vlci.valencia.es/dataset/t248678-daily) | Ajuntament de València | 1 | CSV | 2025-05-20 | barri, carrer |  |
| [Dades diàries del sensor de soroll ubicat al barri de Russafa, en el carrer Puerto Rico, 21](https://opendata.vlci.valencia.es/dataset/t248672-daily) | Ajuntament de València | 1 | CSV | 2025-05-20 | barri, carrer |  |
| [Dades diàries del sensor de soroll ubicat al barri de Russafa, en el carrer Doctor Serrano, 21](https://opendata.vlci.valencia.es/dataset/t248669-daily) | Ajuntament de València | 1 | CSV | 2025-05-20 | barri, carrer |  |
| [Dades diàries del sensor de soroll ubicat al barri de Russafa, en el carrer General Prim, chaflà amb Donoso Cortés](https://opendata.vlci.valencia.es/dataset/t248661-daily) | Ajuntament de València | 1 | CSV | 2025-05-20 | barri, carrer |  |
| [Dades diàries del sensor de soroll ubicat al barri de Russafa, en el carrer Matías Perelló, amb carrer Doctor Sumsi](https://opendata.vlci.valencia.es/dataset/t248679-daily) | Ajuntament de València | 1 | CSV | 2025-05-20 | barri, carrer |  |
| [Superfície urbana per barris](https://opendata.vlci.valencia.es/dataset/urban-area-by-neighborhoods) | Ajuntament de València | 1 | CSV | 2022-12-21 | barri |  |
| [Jardins i espais verds](https://opendata.vlci.valencia.es/dataset/gardens-and-green-spaces) | Ajuntament de València | 18 | CSV|DWG|GML|JSON|KML|SHZ | 2022-05-26 | barri |  |
| [Talls trànsit falles (informació no actualitzada)](https://opendata.vlci.valencia.es/dataset/talls-transit-falles) | Ajuntament de València | 8 | CSV|DWG|GEOJSON|GML|KML|SHZ|WFS|WMS | 2022-05-04 | carrer |  |
| [Barraques de Falles (informació no actualitzada)](https://opendata.vlci.valencia.es/dataset/barraques-de-falles) | Ajuntament de València | 8 | CSV|DWG|GEOJSON|GML|KML|SHZ|WFS|WMS | 2022-05-04 | carrer |  |
| [Recursos socials dirigits a tota la població](https://opendata.vlci.valencia.es/dataset/recursos-socials-dirigits-a-tota-la-poblacio) | Ajuntament de València | 8 | CSV|DWG|GEOJSON|GML|KML|SHZ|WFS|WMS | 2022-04-07 | poblacio, població, población |  |
| [Eixos lineals dels carrers](https://opendata.vlci.valencia.es/dataset/eixos-lineals-dels-carrers) | Ajuntament de València | 8 | CSV|DWG|GEOJSON|GML|KML|SHZ|WFS|WMS | 2022-04-01 | carrer |  |


---

_Generado automáticamente por `scripts/filtrar_catalogo_incendio.py`._
