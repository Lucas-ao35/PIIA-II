#!/usr/bin/env python3
"""
Visualizador interactivo para los datos clínicos del proyecto CU-03 (PharmaCoNER / SPACCC).
Genera un informe interactivo HTML auto-contenido (reports/visualization.html) con:
  - Visor interactivo de casos clínicos con resaltado de menciones (NER) y códigos SNOMED CT.
  - Inspector de entidades (offsets, categoría, notas terminológicas, enlace a SNOMED browser).
  - Generador de JSON canónico en tiempo real según la especificación specs/generacion-json.md.
  - Panel analítico y estadísticas del corpus (distribución por etiquetas, splits, top términos y códigos).

Uso (Windows / Linux / macOS):
    python scripts/visualize_data.py [--serve] [--port 8000]
    o con uv:
    uv run python scripts/visualize_data.py [--serve] [--port 8000]
"""

import argparse
import html
import json
import os
import re
import sys
import webbrowser
from collections import Counter, defaultdict
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

# Compatibilidad con terminales Windows (evitar UnicodeEncodeError en CMD / PowerShell)
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATA_DIR = PROJECT_ROOT / "data" / "pharmaconer" / "pharmaconer"
DEFAULT_OUTPUT_HTML = PROJECT_ROOT / "reports" / "visualization.html"


def parse_brat_file(ann_path: Path, txt_path: Path):
    """Parsea un par de archivos .ann y .txt en formato BRAT."""
    if not txt_path.exists():
        return None

    raw_text = txt_path.read_text(encoding="utf-8-sig").replace("\r\n", "\n")
    lines = ann_path.read_text(encoding="utf-8-sig").splitlines() if ann_path.exists() else []

    # Mapeo de notas terminológicas (#1 AnnotatorNotes T1 85600001)
    notes = {}
    for line in lines:
        if line.startswith("#"):
            parts = line.split("\t")
            if len(parts) >= 3:
                nparts = parts[1].split()
                if len(nparts) == 2:
                    notes[nparts[1]] = parts[2].strip()

    entities = []
    for line in lines:
        if line.startswith("T"):
            parts = line.split("\t")
            if len(parts) >= 3:
                tid = parts[0]
                meta_parts = parts[1].split()
                cat = meta_parts[0]
                # En caso de spans discontinuos (ej: '907 920;925 930'), tomamos el primer start y el último end
                start = int(meta_parts[1])
                end = int(meta_parts[-1])
                term_text = parts[2].strip()
                code = notes.get(tid, None)

                # Estado de normalización acorde a specs/normalizacion-clinica.md
                norm_status = "mapped" if (code and code != "<null>") else "not_found"

                entities.append({
                    "id": tid,
                    "label": cat,
                    "start": start,
                    "end": end,
                    "text": term_text,
                    "code": code if code != "<null>" else None,
                    "norm_status": norm_status
                })

    # Ordenar por start ascendente
    entities.sort(key=lambda x: (x["start"], x["end"]))

    return {
        "text": raw_text,
        "entities": entities
    }


def highlight_html_text(raw_text: str, entities: list) -> str:
    """
    Inserta etiquetas <mark> en el texto plano respetando offsets de caracteres.
    Para evitar problemas de solapamiento y alteración de índices, se procesa de final a principio.
    """
    if not entities:
        return html.escape(raw_text).replace("\n", "<br>")

    # Filtrar entidades que se solapan estrictamente (quedarse con la más larga)
    valid_ents = []
    last_end = -1
    for ent in sorted(entities, key=lambda x: (x["start"], -(x["end"] - x["start"]))):
        if ent["start"] >= last_end:
            valid_ents.append(ent)
            last_end = ent["end"]

    # Procesar desde el final hacia el principio para no alterar los offsets
    valid_ents_rev = sorted(valid_ents, key=lambda x: x["start"], reverse=True)
    chars = list(raw_text)

    for ent in valid_ents_rev:
        s, e = ent["start"], ent["end"]
        if s < 0 or e > len(raw_text):
            continue

        label_class = ent["label"].lower().replace("_", "-")
        code_badge = f'<span class="sn-tag">{html.escape(ent["code"])}</span>' if ent.get("code") else ""
        open_tag = f'<mark class="ent-mark ent-{label_class}" data-id="{ent["id"]}" data-label="{ent["label"]}" data-start="{s}" data-end="{e}" data-code="{html.escape(ent.get("code") or "")}">'
        close_tag = f'{code_badge}</mark>'

        orig_slice = "".join(chars[s:e])
        escaped_slice = html.escape(orig_slice)
        replacement = open_tag + escaped_slice + close_tag
        chars[s:e] = [replacement]

    rendered = "".join(chars)
    # Escapar saltos de línea para visualización en navegador
    rendered = rendered.replace("\n\n", "</p><p>").replace("\n", "<br>")
    return f"<p>{rendered}</p>"


def load_all_dataset(data_dir: Path):
    """Carga y analiza todos los documentos del dataset PharmaCoNER."""
    splits_info = [
        ("train", Path("train-set_1.1") / "train" / "subtrack1"),
        ("dev", Path("dev-set_1.1") / "dev" / "subtrack1"),
        ("test", Path("test-set_1.1") / "test" / "subtrack1"),
    ]

    documents = []
    stats = {
        "total_docs": 0,
        "total_entities": 0,
        "by_split": Counter(),
        "by_label": Counter(),
        "terms_by_label": defaultdict(Counter),
        "code_counter": Counter(),
        "code_to_names": defaultdict(Counter),
    }

    # Contar background si existe
    bg_dir = data_dir / "background-set" / "background"
    bg_count = len(list(bg_dir.glob("*.txt"))) if bg_dir.exists() else 0
    stats["background_docs"] = bg_count

    for split_name, rel_path in splits_info:
        sub_dir = data_dir / rel_path
        if not sub_dir.exists():
            continue

        ann_files = sorted(sub_dir.glob("*.ann"))
        for ann_file in ann_files:
            doc_id = ann_file.stem
            txt_file = ann_file.with_suffix(".txt")
            parsed = parse_brat_file(ann_file, txt_file)
            if not parsed:
                continue

            ents = parsed["entities"]
            stats["total_docs"] += 1
            stats["by_split"][split_name] += 1
            stats["total_entities"] += len(ents)

            for ent in ents:
                stats["by_label"][ent["label"]] += 1
                stats["terms_by_label"][ent["label"]][ent["text"].lower()] += 1
                if ent["code"]:
                    stats["code_counter"][ent["code"]] += 1
                    stats["code_to_names"][ent["code"]][ent["text"].lower()] += 1

            highlighted_html = highlight_html_text(parsed["text"], ents)

            documents.append({
                "id": doc_id,
                "split": split_name,
                "char_length": len(parsed["text"]),
                "entities_count": len(ents),
                "entities": ents,
                "text_highlighted": highlighted_html,
                "raw_text": parsed["text"]
            })

    # Resumen de top términos y códigos
    top_terms = {
        label: [
            {"term": t, "count": c}
            for t, c in counter.most_common(12)
        ]
        for label, counter in stats["terms_by_label"].items()
    }

    top_codes = []
    for code, count in stats["code_counter"].most_common(15):
        top_name = stats["code_to_names"][code].most_common(1)[0][0] if stats["code_to_names"][code] else "—"
        top_codes.append({
            "code": code,
            "representative_term": top_name.title(),
            "count": count
        })

    summary_stats = {
        "total_docs": stats["total_docs"],
        "background_docs": stats["background_docs"],
        "total_entities": stats["total_entities"],
        "avg_entities_per_doc": round(stats["total_entities"] / max(stats["total_docs"], 1), 2),
        "by_split": dict(stats["by_split"]),
        "by_label": dict(stats["by_label"]),
        "top_terms": top_terms,
        "top_codes": top_codes
    }

    return documents, summary_stats


def generate_html_dashboard(documents: list, stats: dict, output_file: Path):
    """Genera la aplicación web interactiva en un archivo HTML autónomo."""
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Convertir documentos a JSON embebido seguro para JavaScript
    docs_json = json.dumps(documents, ensure_ascii=False)
    stats_json = json.dumps(stats, ensure_ascii=False)

    html_content = f"""<!DOCTYPE html>
<html lang="es" data-theme="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>CU-03 | Visualizador Clínico & Dataset Explorer</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
  <style>
    :root {{
      --bg: #090d16;
      --surface: #111827;
      --surface-elevated: #1f2937;
      --surface-border: rgba(255, 255, 255, 0.08);
      --text: #f3f4f6;
      --text-muted: #9ca3af;
      --primary: #6366f1;
      --primary-light: #818cf8;
      
      /* Entity Colors */
      --color-normalizables: #10b981;
      --bg-normalizables: rgba(16, 185, 129, 0.18);
      --border-normalizables: rgba(16, 185, 129, 0.45);

      --color-proteinas: #0ea5e9;
      --bg-proteinas: rgba(14, 165, 233, 0.18);
      --border-proteinas: rgba(14, 165, 233, 0.45);

      --color-unclear: #a855f7;
      --bg-unclear: rgba(168, 85, 247, 0.18);
      --border-unclear: rgba(168, 85, 247, 0.45);

      --color-no-normalizables: #f59e0b;
      --bg-no-normalizables: rgba(245, 158, 11, 0.18);
      --border-no-normalizables: rgba(245, 158, 11, 0.45);
    }}

    [data-theme="light"] {{
      --bg: #f8fafc;
      --surface: #ffffff;
      --surface-elevated: #f1f5f9;
      --surface-border: #e2e8f0;
      --text: #0f172a;
      --text-muted: #64748b;
      --primary: #4f46e5;
      --primary-light: #6366f1;

      --bg-normalizables: rgba(16, 185, 129, 0.14);
      --border-normalizables: #10b981;
      --bg-proteinas: rgba(14, 165, 233, 0.14);
      --border-proteinas: #0284c7;
      --bg-unclear: rgba(168, 85, 247, 0.14);
      --border-unclear: #9333ea;
      --bg-no-normalizables: rgba(245, 158, 11, 0.14);
      --border-no-normalizables: #d97706;
    }}

    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: 'Plus Jakarta Sans', system-ui, -apple-system, sans-serif;
      background-color: var(--bg);
      color: var(--text);
      line-height: 1.5;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
    }}

    /* Top Navigation Header */
    header {{
      background: var(--surface);
      border-bottom: 1px solid var(--surface-border);
      padding: 1rem 1.75rem;
      position: sticky;
      top: 0;
      z-index: 50;
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 1rem;
      backdrop-filter: blur(12px);
    }}

    .brand-title {{
      display: flex;
      align-items: center;
      gap: 0.75rem;
    }}
    .brand-badge {{
      background: linear-gradient(135deg, #4f46e5, #06b6d4);
      color: white;
      font-size: 0.75rem;
      font-weight: 700;
      padding: 0.25rem 0.6rem;
      border-radius: 9999px;
      letter-spacing: 0.05em;
    }}
    h1 {{
      font-size: 1.15rem;
      font-weight: 700;
      letter-spacing: -0.01em;
    }}
    .subtitle {{
      font-size: 0.8rem;
      color: var(--text-muted);
    }}

    .nav-actions {{
      display: flex;
      align-items: center;
      gap: 0.75rem;
    }}

    .tab-btn {{
      background: transparent;
      border: 1px solid var(--surface-border);
      color: var(--text-muted);
      padding: 0.45rem 0.9rem;
      border-radius: 8px;
      font-size: 0.85rem;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.2s ease;
      display: flex;
      align-items: center;
      gap: 0.4rem;
    }}
    .tab-btn:hover {{
      color: var(--text);
      background: var(--surface-elevated);
    }}
    .tab-btn.active {{
      background: var(--primary);
      color: white;
      border-color: var(--primary);
      box-shadow: 0 0 12px rgba(99, 102, 241, 0.4);
    }}

    .theme-toggle {{
      background: var(--surface-elevated);
      border: 1px solid var(--surface-border);
      color: var(--text);
      width: 36px;
      height: 36px;
      border-radius: 8px;
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      font-size: 1rem;
    }}

    /* Main Container */
    main {{
      flex: 1;
      padding: 1.5rem 1.75rem;
      max-width: 1600px;
      width: 100%;
      margin: 0 auto;
    }}

    .tab-content {{ display: none; }}
    .tab-content.active {{ display: block; }}

    /* KPI Summary Row */
    .kpi-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 1rem;
      margin-bottom: 1.5rem;
    }}
    .kpi-card {{
      background: var(--surface);
      border: 1px solid var(--surface-border);
      padding: 1.1rem 1.25rem;
      border-radius: 12px;
      display: flex;
      flex-direction: column;
      gap: 0.35rem;
      position: relative;
      overflow: hidden;
    }}
    .kpi-card::after {{
      content: '';
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      height: 3px;
      background: linear-gradient(90deg, var(--primary), var(--primary-light));
    }}
    .kpi-label {{
      font-size: 0.78rem;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      color: var(--text-muted);
      font-weight: 600;
    }}
    .kpi-value {{
      font-size: 1.75rem;
      font-weight: 700;
      letter-spacing: -0.02em;
    }}
    .kpi-subtext {{
      font-size: 0.75rem;
      color: var(--text-muted);
    }}

    /* Explorer View Layout */
    .explorer-layout {{
      display: grid;
      grid-template-columns: 320px 1fr 340px;
      gap: 1.25rem;
      align-items: start;
    }}
    @media (max-width: 1200px) {{
      .explorer-layout {{ grid-template-columns: 280px 1fr; }}
      .side-inspector {{ grid-column: span 2; }}
    }}
    @media (max-width: 850px) {{
      .explorer-layout {{ grid-template-columns: 1fr; }}
      .side-inspector {{ grid-column: span 1; }}
    }}

    /* Sidebar Document Selector */
    .doc-sidebar {{
      background: var(--surface);
      border: 1px solid var(--surface-border);
      border-radius: 12px;
      padding: 1rem;
      display: flex;
      flex-direction: column;
      gap: 0.85rem;
      max-height: calc(100vh - 170px);
      position: sticky;
      top: 5rem;
    }}
    .search-box {{
      position: relative;
    }}
    .search-input {{
      width: 100%;
      background: var(--surface-elevated);
      border: 1px solid var(--surface-border);
      color: var(--text);
      padding: 0.55rem 0.85rem;
      border-radius: 8px;
      font-size: 0.85rem;
      outline: none;
    }}
    .search-input:focus {{
      border-color: var(--primary);
    }}
    .quick-actions {{
      display: flex;
      gap: 0.4rem;
      flex-wrap: wrap;
    }}
    .chip-btn {{
      background: var(--surface-elevated);
      border: 1px solid var(--surface-border);
      color: var(--text-muted);
      font-size: 0.72rem;
      padding: 0.25rem 0.55rem;
      border-radius: 6px;
      cursor: pointer;
      transition: all 0.15s;
    }}
    .chip-btn:hover {{
      color: var(--text);
      border-color: var(--primary-light);
    }}

    .filter-row {{
      display: flex;
      gap: 0.4rem;
    }}
    .filter-select {{
      flex: 1;
      background: var(--surface-elevated);
      border: 1px solid var(--surface-border);
      color: var(--text);
      padding: 0.4rem 0.6rem;
      border-radius: 6px;
      font-size: 0.78rem;
    }}

    .doc-list {{
      overflow-y: auto;
      display: flex;
      flex-direction: column;
      gap: 0.35rem;
      padding-right: 0.25rem;
    }}
    .doc-item {{
      background: transparent;
      border: 1px solid transparent;
      border-radius: 8px;
      padding: 0.55rem 0.75rem;
      text-align: left;
      cursor: pointer;
      transition: all 0.15s;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }}
    .doc-item:hover {{
      background: var(--surface-elevated);
    }}
    .doc-item.active {{
      background: var(--surface-elevated);
      border-color: var(--primary);
      box-shadow: 0 0 0 1px var(--primary);
    }}
    .doc-item-id {{
      font-size: 0.8rem;
      font-weight: 600;
      font-family: 'JetBrains Mono', monospace;
    }}
    .doc-badge {{
      font-size: 0.68rem;
      padding: 0.15rem 0.45rem;
      border-radius: 4px;
      font-weight: 600;
    }}
    .badge-train {{ background: rgba(99, 102, 241, 0.2); color: #818cf8; }}
    .badge-dev {{ background: rgba(16, 185, 129, 0.2); color: #34d399; }}
    .badge-test {{ background: rgba(245, 158, 11, 0.2); color: #fbbf24; }}

    /* Clinical Narrative Viewer Panel */
    .doc-viewer {{
      background: var(--surface);
      border: 1px solid var(--surface-border);
      border-radius: 12px;
      overflow: hidden;
      display: flex;
      flex-direction: column;
      min-height: calc(100vh - 170px);
    }}
    .viewer-header {{
      padding: 1rem 1.25rem;
      background: var(--surface-elevated);
      border-bottom: 1px solid var(--surface-border);
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 0.75rem;
    }}
    .viewer-title-group {{
      display: flex;
      align-items: center;
      gap: 0.6rem;
    }}
    .viewer-doc-id {{
      font-size: 1rem;
      font-weight: 700;
      font-family: 'JetBrains Mono', monospace;
    }}
    .legend {{
      display: flex;
      gap: 0.6rem;
      flex-wrap: wrap;
      font-size: 0.75rem;
    }}
    .legend-item {{
      display: flex;
      align-items: center;
      gap: 0.3rem;
    }}
    .legend-dot {{
      width: 10px;
      height: 10px;
      border-radius: 50%;
    }}

    .viewer-body {{
      padding: 1.5rem 1.75rem;
      font-size: 0.95rem;
      line-height: 1.85;
      overflow-y: auto;
      flex: 1;
    }}
    .viewer-body p {{
      margin-bottom: 1.2rem;
    }}

    /* Highlighted Mark Styles */
    mark.ent-mark {{
      border-radius: 4px;
      padding: 0.15rem 0.4rem;
      margin: 0 0.1rem;
      cursor: pointer;
      transition: all 0.15s ease;
      display: inline-block;
      font-weight: 500;
      border-bottom: 2px solid;
    }}
    mark.ent-mark:hover {{
      transform: translateY(-1px);
      filter: brightness(1.15);
      box-shadow: 0 4px 10px rgba(0, 0, 0, 0.25);
    }}
    mark.ent-mark.selected {{
      outline: 2px solid #ffffff;
      outline-offset: 1px;
      animation: pulse 1s infinite alternate;
    }}
    @keyframes pulse {{
      from {{ transform: scale(1); }}
      to {{ transform: scale(1.04); }}
    }}

    mark.ent-normalizables {{
      background: var(--bg-normalizables);
      color: var(--color-normalizables);
      border-color: var(--border-normalizables);
    }}
    mark.ent-proteinas {{
      background: var(--bg-proteinas);
      color: var(--color-proteinas);
      border-color: var(--border-proteinas);
    }}
    mark.ent-unclear {{
      background: var(--bg-unclear);
      color: var(--color-unclear);
      border-color: var(--border-unclear);
    }}
    mark.ent-no-normalizables {{
      background: var(--bg-no-normalizables);
      color: var(--color-no-normalizables);
      border-color: var(--border-no-normalizables);
    }}

    .sn-tag {{
      font-size: 0.65rem;
      font-family: 'JetBrains Mono', monospace;
      opacity: 0.85;
      margin-left: 0.3rem;
      font-weight: 400;
      border: 1px solid currentColor;
      padding: 0 0.2rem;
      border-radius: 3px;
    }}

    /* Right Inspector Sidepanel */
    .side-inspector {{
      display: flex;
      flex-direction: column;
      gap: 1rem;
      position: sticky;
      top: 5rem;
    }}
    .inspector-card {{
      background: var(--surface);
      border: 1px solid var(--surface-border);
      border-radius: 12px;
      padding: 1.1rem;
    }}
    .inspector-title {{
      font-size: 0.8rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      color: var(--text-muted);
      margin-bottom: 0.8rem;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }}
    .detail-row {{
      display: flex;
      justify-content: space-between;
      padding: 0.45rem 0;
      border-bottom: 1px solid var(--surface-border);
      font-size: 0.82rem;
    }}
    .detail-row:last-child {{ border-bottom: none; }}
    .detail-key {{ color: var(--text-muted); }}
    .detail-val {{ font-weight: 600; font-family: 'JetBrains Mono', monospace; }}

    .snomed-link-btn {{
      display: inline-flex;
      align-items: center;
      gap: 0.4rem;
      background: var(--surface-elevated);
      border: 1px solid var(--surface-border);
      color: var(--primary-light);
      text-decoration: none;
      padding: 0.45rem 0.75rem;
      border-radius: 6px;
      font-size: 0.8rem;
      font-weight: 600;
      margin-top: 0.75rem;
      width: 100%;
      justify-content: center;
      transition: all 0.15s;
    }}
    .snomed-link-btn:hover {{
      background: var(--primary);
      color: white;
    }}

    .doc-entities-table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 0.78rem;
      margin-top: 0.5rem;
    }}
    .doc-entities-table th {{
      text-align: left;
      padding: 0.4rem;
      color: var(--text-muted);
      border-bottom: 1px solid var(--surface-border);
    }}
    .doc-entities-table td {{
      padding: 0.45rem 0.4rem;
      border-bottom: 1px solid var(--surface-border);
    }}
    .doc-entities-table tr:hover td {{
      background: var(--surface-elevated);
      cursor: pointer;
    }}

    /* JSON Schema Export Modal / Accordion */
    .btn-export-json {{
      background: linear-gradient(135deg, #10b981, #059669);
      color: white;
      border: none;
      padding: 0.4rem 0.85rem;
      border-radius: 6px;
      font-size: 0.8rem;
      font-weight: 600;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 0.35rem;
    }}

    /* Analytics Tab Styles */
    .analytics-grid {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 1.5rem;
    }}
    @media (max-width: 900px) {{
      .analytics-grid {{ grid-template-columns: 1fr; }}
    }}
    .chart-card {{
      background: var(--surface);
      border: 1px solid var(--surface-border);
      border-radius: 12px;
      padding: 1.25rem;
    }}
    .chart-card h3 {{
      font-size: 0.95rem;
      font-weight: 700;
      margin-bottom: 1rem;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }}
    .bar-row {{
      display: flex;
      align-items: center;
      gap: 0.75rem;
      margin-bottom: 0.65rem;
      font-size: 0.82rem;
    }}
    .bar-label {{
      width: 150px;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
      color: var(--text-muted);
    }}
    .bar-track {{
      flex: 1;
      height: 10px;
      background: var(--surface-elevated);
      border-radius: 9999px;
      overflow: hidden;
    }}
    .bar-fill {{
      height: 100%;
      border-radius: 9999px;
      transition: width 0.8s cubic-bezier(0.4, 0, 0.2, 1);
    }}
    .bar-value {{
      width: 60px;
      text-align: right;
      font-family: 'JetBrains Mono', monospace;
      font-weight: 600;
    }}

    /* Modal Styling */
    .modal-overlay {{
      display: none;
      position: fixed;
      inset: 0;
      background: rgba(0, 0, 0, 0.7);
      backdrop-filter: blur(4px);
      z-index: 100;
      align-items: center;
      justify-content: center;
      padding: 1rem;
    }}
    .modal-overlay.active {{ display: flex; }}
    .modal-body {{
      background: var(--surface);
      border: 1px solid var(--surface-border);
      border-radius: 12px;
      max-width: 800px;
      width: 100%;
      max-height: 85vh;
      display: flex;
      flex-direction: column;
      overflow: hidden;
    }}
    .modal-header {{
      padding: 1rem 1.25rem;
      border-bottom: 1px solid var(--surface-border);
      display: flex;
      justify-content: space-between;
      align-items: center;
    }}
    .code-viewer {{
      background: #0d1117;
      color: #c9d1d9;
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.82rem;
      padding: 1.25rem;
      overflow: auto;
      flex: 1;
    }}
  </style>
</head>
<body>

  <header>
    <div class="brand-title">
      <span class="brand-badge">CU-03 PIIA2</span>
      <div>
        <h1>Visualizador Clínico & Dataset Explorer</h1>
        <p class="subtitle">Corpus PharmaCoNER (1.000 Casos Oro • SNOMED CT • Offsets exactos)</p>
      </div>
    </div>
    <div class="nav-actions">
      <button class="tab-btn active" onclick="switchTab('explorer')">📖 Visor de Casos Clínicos</button>
      <button class="tab-btn" onclick="switchTab('analytics')">📊 Estadísticas & Métricas</button>
      <button class="theme-toggle" onclick="toggleTheme()" title="Cambiar tema">🌓</button>
    </div>
  </header>

  <main>
    <!-- KPI SUMMARY BAR -->
    <div class="kpi-grid">
      <div class="kpi-card">
        <span class="kpi-label">Casos Clínicos Anotados</span>
        <span class="kpi-value">{stats['total_docs']}</span>
        <span class="kpi-subtext">500 train • 250 dev • 250 test (+{stats['background_docs']} background)</span>
      </div>
      <div class="kpi-card">
        <span class="kpi-label">Total Menciones Extraídas</span>
        <span class="kpi-value">{stats['total_entities']:,}</span>
        <span class="kpi-subtext">Promedio de {stats['avg_entities_per_doc']} entidades por informe</span>
      </div>
      <div class="kpi-card">
        <span class="kpi-label">Fármacos Normalizables</span>
        <span class="kpi-value" style="color: var(--color-normalizables);">{stats['by_label'].get('NORMALIZABLES', 0):,}</span>
        <span class="kpi-subtext">Menciones enlazables a códigos estándar SNOMED CT</span>
      </div>
      <div class="kpi-card">
        <span class="kpi-label">Proteínas & Genes</span>
        <span class="kpi-value" style="color: var(--color-proteinas);">{stats['by_label'].get('PROTEINAS', 0):,}</span>
        <span class="kpi-subtext">Biomarcadores, receptores y sustancias químicas</span>
      </div>
    </div>

    <!-- TAB 1: CLINICAL EXPLORER -->
    <section id="tab-explorer" class="tab-content active">
      <div class="explorer-layout">
        
        <!-- SIDEBAR: LISTA DE DOCUMENTOS -->
        <aside class="doc-sidebar">
          <div class="search-box">
            <input type="text" id="docSearch" class="search-input" placeholder="🔍 Buscar por ID o término..." oninput="filterDocuments()">
          </div>

          <div class="filter-row">
            <select id="splitFilter" class="filter-select" onchange="filterDocuments()">
              <option value="all">Todos los splits ({stats['total_docs']})</option>
              <option value="dev" selected>Dev set (250)</option>
              <option value="train">Train set (500)</option>
              <option value="test">Test set (250)</option>
            </select>
          </div>

          <div class="quick-actions">
            <button class="chip-btn" onclick="selectSpecificDoc('S0004-06142006000700013-1')">⭐ Caso 0013-1 (LHRH)</button>
            <button class="chip-btn" onclick="selectRandomDoc()">🎲 Aleatorio</button>
            <button class="chip-btn" onclick="selectDocWithMaxEntities()">🔝 Más entidades</button>
          </div>

          <div id="docListContainer" class="doc-list">
            <!-- Renderizado dinámico en JS -->
          </div>
        </aside>

        <!-- MAIN VIEWER: TEXTO CLÍNICO CON MARCAS -->
        <article class="doc-viewer">
          <div class="viewer-header">
            <div class="viewer-title-group">
              <span id="currentDocId" class="viewer-doc-id">Documento</span>
              <span id="currentSplitBadge" class="doc-badge badge-dev">dev</span>
              <span id="currentEntitiesCount" class="chip-btn">0 menciones</span>
            </div>
            
            <div class="legend">
              <div class="legend-item"><span class="legend-dot" style="background: var(--color-normalizables);"></span> NORMALIZABLES</div>
              <div class="legend-item"><span class="legend-dot" style="background: var(--color-proteinas);"></span> PROTEINAS</div>
              <div class="legend-item"><span class="legend-dot" style="background: var(--color-unclear);"></span> UNCLEAR</div>
              <div class="legend-item"><span class="legend-dot" style="background: var(--color-no-normalizables);"></span> NO_NORMALIZABLES</div>
            </div>

            <button class="btn-export-json" onclick="openJsonModal()">
              ⚙️ Ver JSON Canónico (CU-03)
            </button>
          </div>

          <div id="narrativeBody" class="viewer-body">
            <!-- Texto clínico con <mark> renderizado -->
          </div>
        </article>

        <!-- RIGHT INSPECTOR: DETALLES DE ENTIDAD -->
        <aside class="side-inspector">
          
          <div class="inspector-card">
            <div class="inspector-title">
              <span>Inspector de Mención</span>
              <span id="inspectorBadge" class="doc-badge badge-dev" style="display:none;">-</span>
            </div>
            <div id="inspectorDetails">
              <p style="color: var(--text-muted); font-size: 0.8rem; font-style: italic;">
                Haz click en cualquier término resaltado en el texto clínico para inspeccionar sus offsets y código SNOMED CT.
              </p>
            </div>
          </div>

          <div class="inspector-card" style="max-height: 400px; overflow-y: auto;">
            <div class="inspector-title">
              <span>Menciones del Caso</span>
            </div>
            <table class="doc-entities-table">
              <thead>
                <tr>
                  <th>Término</th>
                  <th>Categoría</th>
                  <th>SNOMED</th>
                </tr>
              </thead>
              <tbody id="docEntitiesTableBody">
                <!-- Filas renderizadas en JS -->
              </tbody>
            </table>
          </div>

        </aside>

      </div>
    </section>

    <!-- TAB 2: ANALYTICS -->
    <section id="tab-analytics" class="tab-content">
      <div class="analytics-grid">
        
        <!-- Categorías -->
        <div class="chart-card">
          <h3>Distribución por Categoría Clínica</h3>
          <div id="categoryBars"></div>
        </div>

        <!-- Splits -->
        <div class="chart-card">
          <h3>Distribución por Partición Oficial</h3>
          <div id="splitBars"></div>
        </div>

        <!-- Top Términos -->
        <div class="chart-card">
          <h3>Top Menciones Farmacológicas Más Frecuentes</h3>
          <div id="topTermsBars"></div>
        </div>

        <!-- Top Códigos SNOMED CT -->
        <div class="chart-card">
          <h3>Top Códigos SNOMED CT Asignados</h3>
          <div id="topCodesBars"></div>
        </div>

      </div>
    </section>

  </main>

  <!-- MODAL JSON CANÓNICO -->
  <div id="jsonModal" class="modal-overlay" onclick="closeJsonModal(event)">
    <div class="modal-body" onclick="event.stopPropagation()">
      <div class="modal-header">
        <h3 style="font-size: 1rem; font-weight: 700;">Salida JSON Canónica (Contrato specs/generacion-json.md)</h3>
        <button class="chip-btn" onclick="closeJsonModal()">✕ Cerrar</button>
      </div>
      <pre id="jsonViewer" class="code-viewer"></pre>
      <div style="padding: 0.75rem 1.25rem; background: var(--surface-elevated); display: flex; justify-content: flex-end; gap: 0.5rem;">
        <button class="chip-btn" onclick="copyJsonToClipboard()">📋 Copiar JSON</button>
      </div>
    </div>
  </div>

  <script>
    // Inyección de datos
    const DOCUMENTS = {docs_json};
    const STATS = {stats_json};
    let currentDocIndex = 0;

    // Inicialización
    window.addEventListener('DOMContentLoaded', () => {{
      // Por defecto buscar el caso que Mateo tenía abierto:
      const targetIndex = DOCUMENTS.findIndex(d => d.id === 'S0004-06142006000700013-1');
      currentDocIndex = targetIndex !== -1 ? targetIndex : 0;
      
      renderDocList();
      renderCurrentDoc();
      renderAnalytics();
      setupEntityListeners();
    }});

    function switchTab(tabId) {{
      document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
      document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
      
      if (tabId === 'explorer') {{
        document.querySelectorAll('.tab-btn')[0].classList.add('active');
        document.getElementById('tab-explorer').classList.add('active');
      }} else {{
        document.querySelectorAll('.tab-btn')[1].classList.add('active');
        document.getElementById('tab-analytics').classList.add('active');
      }}
    }}

    function toggleTheme() {{
      const htmlEl = document.documentElement;
      const current = htmlEl.getAttribute('data-theme');
      const next = current === 'dark' ? 'light' : 'dark';
      htmlEl.setAttribute('data-theme', next);
    }}

    function renderDocList() {{
      const container = document.getElementById('docListContainer');
      const search = document.getElementById('docSearch').value.toLowerCase();
      const split = document.getElementById('splitFilter').value;

      let filtered = DOCUMENTS.filter((d, idx) => {{
        const matchSplit = (split === 'all' || d.split === split);
        const matchSearch = (!search || d.id.toLowerCase().includes(search) || d.raw_text.toLowerCase().includes(search));
        return matchSplit && matchSearch;
      }});

      container.innerHTML = filtered.slice(0, 150).map(d => {{
        const isCurrent = (DOCUMENTS[currentDocIndex].id === d.id);
        const badgeClass = `badge-${{d.split}}`;
        return `
          <div class="doc-item ${{isCurrent ? 'active' : ''}}" onclick="selectDocById('${{d.id}}')">
            <span class="doc-item-id">${{d.id}}</span>
            <div style="display: flex; gap: 0.3rem; align-items: center;">
              <span style="font-size: 0.7rem; color: var(--text-muted);">${{d.entities_count}} ents</span>
              <span class="doc-badge ${{badgeClass}}">${{d.split}}</span>
            </div>
          </div>
        `;
      }}).join('');

      if (filtered.length === 0) {{
        container.innerHTML = '<div style="color: var(--text-muted); font-size: 0.8rem; padding: 1rem; text-align: center;">No se encontraron casos.</div>';
      }}
    }}

    function filterDocuments() {{
      renderDocList();
    }}

    function selectDocById(docId) {{
      const idx = DOCUMENTS.findIndex(d => d.id === docId);
      if (idx !== -1) {{
        currentDocIndex = idx;
        renderDocList();
        renderCurrentDoc();
      }}
    }}

    function selectSpecificDoc(docId) {{
      document.getElementById('splitFilter').value = 'all';
      document.getElementById('docSearch').value = '';
      selectDocById(docId);
    }}

    function selectRandomDoc() {{
      const randIdx = Math.floor(Math.random() * DOCUMENTS.length);
      currentDocIndex = randIdx;
      renderDocList();
      renderCurrentDoc();
    }}

    function selectDocWithMaxEntities() {{
      let maxIdx = 0;
      let maxCount = -1;
      DOCUMENTS.forEach((d, idx) => {{
        if (d.entities_count > maxCount) {{
          maxCount = d.entities_count;
          maxIdx = idx;
        }}
      }});
      currentDocIndex = maxIdx;
      renderDocList();
      renderCurrentDoc();
    }}

    function renderCurrentDoc() {{
      const doc = DOCUMENTS[currentDocIndex];
      document.getElementById('currentDocId').textContent = doc.id;
      
      const badge = document.getElementById('currentSplitBadge');
      badge.textContent = doc.split;
      badge.className = `doc-badge badge-${{doc.split}}`;

      document.getElementById('currentEntitiesCount').textContent = `${{doc.entities_count}} menciones`;
      document.getElementById('narrativeBody').innerHTML = doc.text_highlighted;

      // Render tabla de menciones
      const tbody = document.getElementById('docEntitiesTableBody');
      if (doc.entities.length === 0) {{
        tbody.innerHTML = '<tr><td colspan="3" style="text-align:center; color: var(--text-muted);">Sin menciones detectadas</td></tr>';
      }} else {{
        tbody.innerHTML = doc.entities.map(ent => `
          <tr onclick="focusEntity('${{ent.id}}')">
            <td style="font-weight: 600;">${{escapeHtml(ent.text)}}</td>
            <td><span class="sn-tag" style="border:none; color: var(--color-${{ent.label.toLowerCase().replace('_', '-')}})">${{ent.label}}</span></td>
            <td>${{ent.code ? `<span class="sn-tag">${{ent.code}}</span>` : '<span style="color:var(--text-muted)">—</span>'}}</td>
          </tr>
        `).join('');
      }}

      // Reset inspector
      document.getElementById('inspectorBadge').style.display = 'none';
      document.getElementById('inspectorDetails').innerHTML = `
        <p style="color: var(--text-muted); font-size: 0.8rem; font-style: italic;">
          Haz click en cualquier término resaltado para inspeccionar offsets y código SNOMED CT.
        </p>
      `;

      setupEntityListeners();
    }}

    function setupEntityListeners() {{
      document.querySelectorAll('mark.ent-mark').forEach(el => {{
        el.addEventListener('click', (e) => {{
          e.stopPropagation();
          const tid = el.getAttribute('data-id');
          focusEntity(tid);
        }});
      }});
    }}

    function focusEntity(entityId) {{
      const doc = DOCUMENTS[currentDocIndex];
      const ent = doc.entities.find(e => e.id === entityId);
      if (!ent) return;

      // Resaltar visualmente en el texto
      document.querySelectorAll('mark.ent-mark').forEach(m => m.classList.remove('selected'));
      const activeMark = document.querySelector(`mark.ent-mark[data-id="${{entityId}}"]`);
      if (activeMark) {{
        activeMark.classList.add('selected');
        activeMark.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
      }}

      // Rellenar inspector lateral
      const badge = document.getElementById('inspectorBadge');
      badge.style.display = 'inline-block';
      badge.textContent = ent.label;
      badge.className = `doc-badge badge-${{doc.split}}`;

      const snomedBtn = ent.code 
        ? `<a href="https://browser.ihtsdotools.org/?perspective=full&conceptId1=${{ent.code}}" target="_blank" class="snomed-link-btn">
             🌐 Consultar Concepto ${{ent.code}} en SNOMED CT ↗
           </a>`
        : `<p style="font-size: 0.75rem; color: var(--text-muted); margin-top: 0.5rem;">
             ⚠️ Sin código inequívoco asignado (marcado como not_found).
           </p>`;

      document.getElementById('inspectorDetails').innerHTML = `
        <div style="font-size: 1.15rem; font-weight: 700; color: var(--color-${{ent.label.toLowerCase().replace('_', '-')}}); margin-bottom: 0.5rem;">
          "${{escapeHtml(ent.text)}}"
        </div>
        <div class="detail-row">
          <span class="detail-key">Categoría:</span>
          <span class="detail-val">${{ent.label}}</span>
        </div>
        <div class="detail-row">
          <span class="detail-key">Offsets Caracteres:</span>
          <span class="detail-val">[${{ent.start}} : ${{ent.end}}]</span>
        </div>
        <div class="detail-row">
          <span class="detail-key">Longitud:</span>
          <span class="detail-val">${{ent.end - ent.start}} caracteres</span>
        </div>
        <div class="detail-row">
          <span class="detail-key">Código SNOMED CT:</span>
          <span class="detail-val">${{ent.code || '<null>'}}</span>
        </div>
        <div class="detail-row">
          <span class="detail-key">Estado Normalización:</span>
          <span class="detail-val">${{ent.norm_status}}</span>
        </div>
        ${{snomedBtn}}
      `;
    }}

    function openJsonModal() {{
      const doc = DOCUMENTS[currentDocIndex];
      // Construir objeto conforme al esquema canónico de specs/generacion-json.md
      const canonicalJson = {{
        "schema_version": "1.0",
        "document_id": doc.id,
        "language": "es",
        "source_text": doc.raw_text,
        "entities": doc.entities.map(e => ({{
          "text": e.text,
          "type": e.label === "NORMALIZABLES" ? "farmaco" : (e.label === "PROTEINAS" ? "proteina" : e.label.toLowerCase()),
          "start": e.start,
          "end": e.end,
          "coding": {{
            "system": e.code ? "SNOMED_CT" : null,
            "code": e.code || null,
            "display": e.code ? e.text : null
          }},
          "normalization_status": e.norm_status
        }}))
      }};

      document.getElementById('jsonViewer').textContent = JSON.stringify(canonicalJson, null, 2);
      document.getElementById('jsonModal').classList.add('active');
    }}

    function closeJsonModal(e) {{
      document.getElementById('jsonModal').classList.remove('active');
    }}

    function copyJsonToClipboard() {{
      const code = document.getElementById('jsonViewer').textContent;
      navigator.clipboard.writeText(code).then(() => {{
        alert('¡JSON canónico copiado al portapapeles!');
      }});
    }}

    function renderAnalytics() {{
      // Categorías
      const catContainer = document.getElementById('categoryBars');
      const totalEnts = STATS.total_entities;
      const catColors = {{
        'NORMALIZABLES': 'var(--color-normalizables)',
        'PROTEINAS': 'var(--color-proteinas)',
        'UNCLEAR': 'var(--color-unclear)',
        'NO_NORMALIZABLES': 'var(--color-no-normalizables)'
      }};

      catContainer.innerHTML = Object.entries(STATS.by_label).map(([label, count]) => {{
        const pct = ((count / totalEnts) * 100).toFixed(1);
        const col = catColors[label] || 'var(--primary)';
        return `
          <div class="bar-row">
            <span class="bar-label">${{label}}</span>
            <div class="bar-track">
              <div class="bar-fill" style="width: ${{pct}}%; background: ${{col}};"></div>
            </div>
            <span class="bar-value">${{count.toLocaleString()}} <small style="color:var(--text-muted)">(${{pct}}%)</small></span>
          </div>
        `;
      }}).join('');

      // Splits
      const splitContainer = document.getElementById('splitBars');
      splitContainer.innerHTML = Object.entries(STATS.by_split).map(([split, count]) => {{
        const pct = ((count / STATS.total_docs) * 100).toFixed(0);
        return `
          <div class="bar-row">
            <span class="bar-label" style="text-transform:uppercase;">${{split}}</span>
            <div class="bar-track">
              <div class="bar-fill" style="width: ${{pct}}%; background: var(--primary);"></div>
            </div>
            <span class="bar-value">${{count}} docs <small style="color:var(--text-muted)">(${{pct}}%)</small></span>
          </div>
        `;
      }}).join('');

      // Top Términos
      const topTermsContainer = document.getElementById('topTermsBars');
      const normTerms = (STATS.top_terms['NORMALIZABLES'] || []).slice(0, 8);
      const maxTermCount = normTerms[0] ? normTerms[0].count : 1;
      topTermsContainer.innerHTML = normTerms.map(item => {{
        const pct = ((item.count / maxTermCount) * 100).toFixed(0);
        return `
          <div class="bar-row">
            <span class="bar-label" style="font-weight:600;">${{item.term}}</span>
            <div class="bar-track">
              <div class="bar-fill" style="width: ${{pct}}%; background: var(--color-normalizables);"></div>
            </div>
            <span class="bar-value">${{item.count}}</span>
          </div>
        `;
      }}).join('');

      // Top Códigos SNOMED CT
      const topCodesContainer = document.getElementById('topCodesBars');
      const topCodes = STATS.top_codes.slice(0, 8);
      const maxCodeCount = topCodes[0] ? topCodes[0].count : 1;
      topCodesContainer.innerHTML = topCodes.map(item => {{
        const pct = ((item.count / maxCodeCount) * 100).toFixed(0);
        return `
          <div class="bar-row">
            <span class="bar-label" title="${{item.code}}">
              <strong style="font-family:monospace">${{item.code}}</strong> (${{item.representative_term}})
            </span>
            <div class="bar-track">
              <div class="bar-fill" style="width: ${{pct}}%; background: var(--primary-light);"></div>
            </div>
            <span class="bar-value">${{item.count}}</span>
          </div>
        `;
      }}).join('');
    }}

    function escapeHtml(str) {{
      if (!str) return '';
      return str.replace(/&/g, '&amp;')
                .replace(/</g, '&lt;')
                .replace(/>/g, '&gt;')
                .replace(/"/g, '&quot;')
                .replace(/'/g, '&#039;');
    }}
  </script>
</body>
</html>
"""

    output_file.write_text(html_content, encoding="utf-8")
    print(f"[+] Archivo HTML generado exitosamente en:\n    {output_file.resolve()}")


def serve_dashboard(html_path: Path, port: int = 8000):
    """Lanza un servidor web local para visualizar el dashboard."""
    html_path = html_path.resolve()
    directory = html_path.parent
    os.chdir(directory)

    class CustomHandler(SimpleHTTPRequestHandler):
        def end_headers(self):
            self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
            super().end_headers()

    # Intentar vincular puerto (manejar conflicto si el puerto está en uso en Windows)
    server = None
    actual_port = port
    for p in range(port, port + 10):
        try:
            server = HTTPServer(("127.0.0.1", p), CustomHandler)
            actual_port = p
            break
        except OSError:
            continue

    if not server:
        print(f"[!] No se pudo vincular un puerto local disponible entre {port} y {port + 9}.")
        return

    url = f"http://127.0.0.1:{actual_port}/{html_path.name}"
    print("=" * 70)
    print(f"[*] Servidor web iniciado en: {url}")
    print("    Presiona Ctrl + C para detener el servidor.")
    print("=" * 70)

    try:
        webbrowser.open(url)
    except Exception:
        pass

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[*] Servidor detenido.")
    finally:
        try:
            server.server_close()
        except Exception:
            pass


def main():
    parser = argparse.ArgumentParser(
        description="Genera una visualización interactiva y análisis de los datos clínicos para CU-03."
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=DEFAULT_DATA_DIR,
        help="Ruta al directorio de datos descomprimidos de PharmaCoNER.",
    )
    parser.add_argument(
        "--output-html",
        type=Path,
        default=DEFAULT_OUTPUT_HTML,
        help="Ruta del archivo HTML generado (por defecto: reports/visualization.html).",
    )
    parser.add_argument(
        "--serve",
        action="store_true",
        help="Iniciar un servidor web local y abrir el navegador automáticamente.",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Puerto para el servidor HTTP local (por defecto: 8000).",
    )

    args = parser.parse_args()
    data_dir = args.data_dir.resolve()

    # Si la ruta por defecto no existe directamente, comprobar si está en el nivel superior de data/pharmaconer
    if not data_dir.exists():
        fallback_dir = PROJECT_ROOT / "data" / "pharmaconer"
        if fallback_dir.exists() and (fallback_dir / "train-set_1.1").exists():
            data_dir = fallback_dir

    if not data_dir.exists() or not (data_dir / "train-set_1.1").exists():
        print(f"[!] Error: No se encontró el dataset en: {data_dir}")
        print("    Descárgalo primero ejecutando:")
        print("        python scripts/download_datasets.py")
        print("    o con uv:")
        print("        uv run python scripts/download_datasets.py")
        sys.exit(1)

    print("=" * 70)
    print(f"[*] Leyendo y parseando casos clínicos desde:\n    {data_dir}")
    print("=" * 70)

    documents, stats = load_all_dataset(data_dir)

    print(f"\nResumen Estadístico:")
    print(f"  - Documentos Anotados (Oro):   {stats['total_docs']}")
    print(f"  - Partición train:             {stats['by_split'].get('train', 0)}")
    print(f"  - Partición dev:               {stats['by_split'].get('dev', 0)}")
    print(f"  - Partición test:              {stats['by_split'].get('test', 0)}")
    print(f"  - Documentos background:       {stats['background_docs']}")
    print(f"  - Total Menciones Extraídas:   {stats['total_entities']}")
    print(f"  - Menciones por categoría:")
    for cat, cnt in stats['by_label'].items():
        pct = (cnt / stats['total_entities']) * 100
        print(f"      • {cat:16}: {cnt:5} ({pct:4.1f}%)")

    generate_html_dashboard(documents, stats, args.output_html)

    print("\n[✔] Visualización generada.")
    print("    Puedes abrir el archivo directamente en tu navegador:")
    print(f"    {args.output_html.resolve().as_uri()}")

    if args.serve:
        serve_dashboard(args.output_html, port=args.port)


if __name__ == "__main__":
    main()
