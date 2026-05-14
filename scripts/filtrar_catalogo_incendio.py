"""
Filtra el volcado del catálogo CKAN del portal de datos abiertos de
València (`data/raw/ckan_package_search_0.json`) por palabras clave del
dominio de riesgo de incendio urbano y produce un informe en Markdown
para `docs/fuentes-encontradas.md`.

Léxico cubierto (castellano y valenciano):
  - incendio, foc, fuego
  - bomberos, bombers, parc de bombers
  - emergencia, emergència, protecció civil
  - hidrante, boca de incendio
  - vulnerabilidad, riesgo, evacuación
  - equipamientos sensibles: residencias, hospitales, escuelas, sanitario
  - edificación: edificio, vivienda, padrón, manzanas, catastro
  - población y demografía (contexto necesario para impacto)

Salidas:
  data/processed/catalogo_incendio.csv  · tabla cruda para análisis
  docs/fuentes-encontradas.md           · informe legible agrupado por tema

Sin dependencias externas. Solo stdlib. Criterio 3 de la convocatoria
(trazabilidad y auditabilidad).

Uso:
    python scripts/filtrar_catalogo_incendio.py
"""
from __future__ import annotations

import csv
import json
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw" / "ckan_package_search_0.json"
OUT_CSV = ROOT / "data" / "processed" / "catalogo_incendio.csv"
OUT_MD = ROOT / "docs" / "fuentes-encontradas.md"
OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
OUT_MD.parent.mkdir(parents=True, exist_ok=True)


# Cada tema tiene su patrón regex y su prioridad en el informe.
# El orden de TEMAS define el orden de aparición en el Markdown.
TEMAS: list[tuple[str, str, re.Pattern[str]]] = [
    (
        "nucleo",
        "Núcleo · incendio, bomberos, emergencia",
        re.compile(
            r"\b("
            r"incend[ií]|incendio|fuego|foc|"
            r"bomber|parc[\s\-]*de[\s\-]*bomber|estaci[oó]n[\s\-]*de[\s\-]*bomber|"
            r"emerg[eè]nci|"
            r"protecci[oó]n[\s\-]*civil|protecci[oó][\s\-]*civil|"
            r"hidrant|boca[\s\-]*de[\s\-]*incendio|boca[\s\-]*d[\s\-]*incendi|"
            r"evacuaci[oó]"
            r")",
            re.IGNORECASE,
        ),
    ),
    (
        "vulnerabilidad",
        "Vulnerabilidad social y riesgo",
        re.compile(
            r"\b("
            r"vulnerab|risc|riesgo|"
            r"renta|ingres|pobreza|pobresa|desigualdad|equidad|"
            r"sensibilidad|sensibilitat"
            r")",
            re.IGNORECASE,
        ),
    ),
    (
        "equipamientos",
        "Equipamientos sensibles (residencias, sanitarios, escolares)",
        re.compile(
            r"\b("
            r"residenci|geri[aá]tric|mayor|gent[\s\-]*gran|"
            r"hospital|cl[ií]nic|centr[oe][\s\-]*de[\s\-]*salud|cent[ree][\s\-]*sanitari|"
            r"sanitari|salud|salut|"
            r"escola|colegio|escuel|instituto|institut|guarder|guarderia|llar[\s\-]*d[\s\-]*infants|"
            r"educac|"
            r"equipament|"
            r"asistenc|atenci[oó]n[\s\-]*social|centr[oe][\s\-]*social"
            r")",
            re.IGNORECASE,
        ),
    ),
    (
        "edificacion",
        "Edificación y vivienda",
        re.compile(
            r"\b("
            r"edifici|construcci|altura|"
            r"vivienda|habitatg|casa|residencial|"
            r"catastr|"
            r"manzana|illeta|"
            r"ITE|inspecci[oó]n[\s\-]*t[eè]cnic"
            r")",
            re.IGNORECASE,
        ),
    ),
    (
        "contexto",
        "Contexto urbano y demográfico",
        re.compile(
            r"\b("
            r"barri|barrio|secci[oó]n[\s\-]*censal|secci[oó][\s\-]*censal|"
            r"poblaci[oó]n|poblaci[oó]|padr[oó]n|padr[oó]|demograf|edad|edat|"
            r"callejer|carrer|callejero"
            r")",
            re.IGNORECASE,
        ),
    ),
]


def cargar_resultados() -> list[dict]:
    if not RAW.exists():
        print(
            f"ERROR: no existe {RAW}.\n"
            f"Ejecuta antes:  python scripts/fetch_catalogo_vlci.py",
            file=sys.stderr,
        )
        sys.exit(1)
    data = json.loads(RAW.read_text(encoding="utf-8"))
    return data["result"]["results"]


def blob(d: dict) -> str:
    """Texto donde buscar keywords: título + descripción + tags."""
    return " ".join(
        [
            d.get("title", "") or "",
            d.get("title_es", "") or "",
            d.get("title_en", "") or "",
            d.get("notes", "") or "",
            d.get("notes_es", "") or "",
            " ".join(t.get("name", "") for t in d.get("tags", [])),
            " ".join(g.get("name", "") for g in d.get("groups", [])),
        ]
    )


def fila(d: dict, temas_hit: dict[str, list[str]]) -> dict:
    recursos = d.get("resources", []) or []
    formatos = sorted({(r.get("format") or "").upper() for r in recursos if r.get("format")})
    return {
        "id": d.get("id"),
        "name": d.get("name"),
        "title": (d.get("title") or "").strip(),
        "organization": (d.get("organization") or {}).get("title")
        or (d.get("organization") or {}).get("name"),
        "groups": ", ".join(sorted(g.get("name", "") for g in d.get("groups", []))),
        "num_resources": len(recursos),
        "formats": "|".join(formatos),
        "metadata_modified": (d.get("metadata_modified") or "")[:10],
        "license_id": d.get("license_id"),
        "url_portal": f"https://opendata.vlci.valencia.es/dataset/{d.get('name')}",
        "first_resource_url": next(
            (r.get("url") for r in recursos if r.get("url")), ""
        ),
        "first_resource_format": next(
            (r.get("format") for r in recursos if r.get("format")), ""
        ),
        "tema_principal": next(iter(temas_hit)) if temas_hit else "",
        "todos_los_temas": ",".join(temas_hit.keys()),
        "keywords_encontradas": "; ".join(
            f"{t}={','.join(sorted(set(ks))[:6])}" for t, ks in temas_hit.items()
        ),
        "notes_preview": (d.get("notes") or "").replace("\n", " ").replace("\r", " ")[:300],
    }


def clasificar(datasets: list[dict]) -> dict[str, list[tuple[dict, dict[str, list[str]]]]]:
    """Devuelve un dict tema → [(dataset, hits_por_tema), ...].
    Un dataset puede aparecer en varios temas si matcha varios."""
    por_tema: dict[str, list[tuple[dict, dict[str, list[str]]]]] = defaultdict(list)
    for d in datasets:
        b = blob(d)
        hits: dict[str, list[str]] = {}
        for clave, _, patron in TEMAS:
            ms = [m.group(0).lower() for m in patron.finditer(b)]
            if ms:
                hits[clave] = ms
        if not hits:
            continue
        # Tema principal = el primero que matcha en orden de TEMAS.
        principal = next(c for c, _, _ in TEMAS if c in hits)
        por_tema[principal].append((d, hits))
    return por_tema


def escribir_csv(filas: list[dict]) -> None:
    if not filas:
        OUT_CSV.write_text("", encoding="utf-8")
        return
    with OUT_CSV.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(filas[0].keys()))
        w.writeheader()
        w.writerows(filas)


def escribir_md(por_tema: dict, total: int) -> None:
    ahora = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    n_match = sum(len(v) for v in por_tema.values())
    md: list[str] = []
    md.append("# Fuentes encontradas para cendra VLC\n\n")
    md.append(
        f"> Filtrado automático del catálogo CKAN del portal de datos\n"
        f"> abiertos de l'Ajuntament de València "
        f"(`opendata.vlci.valencia.es`).\n\n"
    )
    md.append(f"- **Fecha del análisis**: {ahora}\n")
    md.append(f"- **Fuente**: `data/raw/ckan_package_search_0.json`\n")
    md.append(f"- **Datasets totales en el portal**: {total}\n")
    md.append(f"- **Datasets que matchean al menos un tema**: {n_match}\n")
    md.append(
        f"- **Reproducible con**: `python scripts/fetch_catalogo_vlci.py` "
        f"y después `python scripts/filtrar_catalogo_incendio.py`\n\n"
    )
    md.append(
        "Cada dataset se asigna al primer tema que matchea según el orden\n"
        "de `TEMAS` en el script. Un dataset puede aparecer en más temas\n"
        "(columna *otros temas*), pero solo se lista en su tema principal.\n\n"
    )

    for clave, titulo, _ in TEMAS:
        bloques = por_tema.get(clave, [])
        md.append(f"\n## {titulo}\n\n")
        if not bloques:
            md.append("_Sin resultados._\n")
            continue
        md.append(f"_{len(bloques)} datasets._\n\n")
        # Tabla
        md.append("| Título | Org. | Recursos | Formatos | Última act. | Keywords | Otros temas |\n")
        md.append("|---|---|---|---|---|---|---|\n")
        for d, hits in sorted(
            bloques, key=lambda x: (x[0].get("metadata_modified") or ""), reverse=True
        ):
            f = fila(d, hits)
            otros = [t for t in hits.keys() if t != clave]
            kws_main = ", ".join(sorted(set(hits.get(clave, [])))[:4])
            md.append(
                f"| [{f['title']}]({f['url_portal']}) "
                f"| {f['organization'] or ''} "
                f"| {f['num_resources']} "
                f"| {f['formats']} "
                f"| {f['metadata_modified']} "
                f"| {kws_main} "
                f"| {', '.join(otros)} |\n"
            )
        md.append("\n")
        # Detalle: para el tema núcleo, incluir descripción y enlaces a recursos
        if clave == "nucleo":
            md.append("### Detalle de los datasets del núcleo\n\n")
            for d, _hits in sorted(
                bloques, key=lambda x: (x[0].get("metadata_modified") or ""), reverse=True
            ):
                f = fila(d, _hits)
                md.append(f"#### {f['title']}\n\n")
                md.append(f"- URL del portal: <{f['url_portal']}>\n")
                md.append(f"- Organización: {f['organization'] or '—'}\n")
                md.append(f"- Última actualización: {f['metadata_modified']}\n")
                md.append(f"- Licencia: {f['license_id']}\n")
                if f["notes_preview"]:
                    md.append(f"- Descripción: {f['notes_preview']}\n")
                recursos = d.get("resources", []) or []
                if recursos:
                    md.append(f"- Recursos ({len(recursos)}):\n")
                    for r in recursos:
                        nombre = r.get("name") or r.get("description") or ""
                        fmt = r.get("format") or ""
                        url = r.get("url") or ""
                        md.append(f"  - **{fmt}** {nombre} — <{url}>\n")
                md.append("\n")

    md.append(
        "\n---\n\n"
        "_Generado automáticamente por `scripts/filtrar_catalogo_incendio.py`._\n"
    )
    OUT_MD.write_text("".join(md), encoding="utf-8")


def main() -> None:
    datasets = cargar_resultados()
    print(f"Datasets totales en el catálogo: {len(datasets)}", file=sys.stderr)

    por_tema = clasificar(datasets)
    n_total = sum(len(v) for v in por_tema.values())
    print(f"Datasets relevantes: {n_total}", file=sys.stderr)
    for clave, titulo, _ in TEMAS:
        n = len(por_tema.get(clave, []))
        print(f"  - {clave:20s}  {n:>3d}  · {titulo}", file=sys.stderr)

    # CSV con todas las filas (no solo el tema principal, sino todos los hits)
    filas: list[dict] = []
    vistos: set[str] = set()
    for clave, _, _ in TEMAS:
        for d, hits in por_tema.get(clave, []):
            if d.get("id") in vistos:
                continue
            vistos.add(d.get("id"))
            filas.append(fila(d, hits))
    escribir_csv(filas)
    print(f"\n-> {OUT_CSV.relative_to(ROOT)}", file=sys.stderr)

    escribir_md(por_tema, len(datasets))
    print(f"-> {OUT_MD.relative_to(ROOT)}", file=sys.stderr)


if __name__ == "__main__":
    main()
