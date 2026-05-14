<#
.SYNOPSIS
  Descarga reproducible del catálogo CKAN del portal de datos abiertos del
  Ayuntamiento de València (opendata.vlci.valencia.es).

.DESCRIPTION
  Guarda en `data/raw/` el volcado completo del catálogo CKAN. El portal de
  Valencia migró de la plataforma Opendatasoft (valencia.opendatasoft.com,
  hoy fuera de servicio) a CKAN 2.10 alojado en VLCi (Valencia Smart City).

  Endpoints usados:
    - /api/3/action/package_search?rows=1000        (datasets completos)
    - /api/3/action/package_list                    (lista plana de IDs)
    - /api/3/action/group_list?all_fields=true      (categorías)
    - /api/3/action/organization_list?all_fields=true (organismos publicadores)
    - /catalog.xml                                  (volcado DCAT/RDF)

.NOTES
  La trazabilidad de esta descarga es uno de los argumentos clave para los
  criterios 3 (viabilidad/calidad técnica) y 4 (transparencia/apertura) de
  la convocatoria 2026 del Ayuntamiento.
#>
[CmdletBinding()]
param(
  [string]$OutDir = "$(Split-Path -Parent $PSScriptRoot)\data\raw",
  [string]$Base = 'https://opendata.vlci.valencia.es'
)

$ErrorActionPreference = 'Stop'
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

$ua = 'Mozilla/5.0 (compatible; cendra-fetch/0.1; +https://github.com/imartinsorribes/cendra)'
$headers = @{ 'User-Agent' = $ua; 'Accept' = 'application/json' }

$endpoints = @(
  @{ Url = "$Base/api/3/action/package_search?rows=1000&start=0"; File = 'ckan_package_search_0.json' }
  @{ Url = "$Base/api/3/action/package_list";                     File = 'ckan_package_list.json' }
  @{ Url = "$Base/api/3/action/group_list?all_fields=true";       File = 'ckan_group_list.json' }
  @{ Url = "$Base/api/3/action/organization_list?all_fields=true"; File = 'ckan_organization_list.json' }
  @{ Url = "$Base/catalog.xml";                                   File = 'ckan_catalog_dcat.xml' }
)

foreach ($e in $endpoints) {
  $dst = Join-Path $OutDir $e.File
  Write-Host "[fetch] $($e.Url) -> $dst"
  Invoke-WebRequest -Uri $e.Url -UseBasicParsing -Headers $headers -OutFile $dst -TimeoutSec 120
}

# Resumen para validar la descarga
$j = Get-Content (Join-Path $OutDir 'ckan_package_search_0.json') -Raw | ConvertFrom-Json
"OK. total reportado por CKAN = $($j.result.count); resultados descargados = $($j.result.results.Count)"
