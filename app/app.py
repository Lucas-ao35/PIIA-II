"""
CU-03 PIIA2 — Visualizador Clínico & Dataset Explorer en Streamlit.
Extracción y estructuración de información clínica en español (PharmaCoNER / SPACCC).
"""

import html
import json
import random
from collections import Counter, defaultdict
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

# -----------------------------------------------------------------------------
# Configuración inicial de Streamlit
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="CU-03 | Visualizador Clínico",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -----------------------------------------------------------------------------
# Estilos CSS personalizados
# -----------------------------------------------------------------------------
st.markdown(
    """
    <style>
    /* Estilos para etiquetas de entidades clínicas */
    mark.ent-mark {
        border-radius: 4px;
        padding: 0.18rem 0.45rem;
        margin: 0 0.12rem;
        display: inline-block;
        font-weight: 500;
        border-bottom: 2px solid;
        line-height: 1.4;
    }
    mark.ent-normalizables {
        background-color: rgba(16, 185, 129, 0.18);
        color: #10b981;
        border-color: rgba(16, 185, 129, 0.6);
    }
    mark.ent-proteinas {
        background-color: rgba(14, 165, 233, 0.18);
        color: #0ea5e9;
        border-color: rgba(14, 165, 233, 0.6);
    }
    mark.ent-unclear {
        background-color: rgba(168, 85, 247, 0.18);
        color: #a855f7;
        border-color: rgba(168, 85, 247, 0.6);
    }
    mark.ent-no-normalizables {
        background-color: rgba(245, 158, 11, 0.18);
        color: #f59e0b;
        border-color: rgba(245, 158, 11, 0.6);
    }
    .sn-tag {
        font-size: 0.72rem;
        font-family: monospace;
        margin-left: 0.35rem;
        padding: 0.05rem 0.25rem;
        border: 1px solid currentColor;
        border-radius: 3px;
        opacity: 0.85;
    }
    .clinical-narrative {
        font-size: 1.05rem;
        line-height: 1.85;
        padding: 1.5rem;
        background-color: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 10px;
        font-family: system-ui, -apple-system, sans-serif;
    }
    .badge-pill {
        display: inline-block;
        padding: 0.2rem 0.6rem;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
        letter-spacing: 0.03em;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# -----------------------------------------------------------------------------
# Funciones de carga y parseo de datos (con caché)
# -----------------------------------------------------------------------------
def parse_brat_file(ann_path: Path, txt_path: Path):
    """Parsea archivos .ann y .txt del corpus en formato BRAT."""
    if not txt_path.exists():
        return None

    raw_text = txt_path.read_text(encoding="utf-8-sig").replace("\r\n", "\n")
    lines = ann_path.read_text(encoding="utf-8-sig").splitlines() if ann_path.exists() else []

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
                start = int(meta_parts[1])
                end = int(meta_parts[-1])
                term_text = parts[2].strip()
                code = notes.get(tid, None)

                norm_status = "mapped" if (code and code != "<null>") else "not_found"

                entities.append({
                    "id": tid,
                    "label": cat,
                    "start": start,
                    "end": end,
                    "text": term_text,
                    "code": code if code != "<null>" else None,
                    "norm_status": norm_status,
                })

    entities.sort(key=lambda x: (x["start"], x["end"]))
    return {"text": raw_text, "entities": entities}


@st.cache_data(show_spinner="Cargando y parseando corpus PharmaCoNER...")
def load_dataset(data_dir_str: str):
    """Carga y procesa las tres particiones oficiales (train, dev, test)."""
    data_dir = Path(data_dir_str)
    splits = [
        ("train", Path("train-set_1.1") / "train" / "subtrack1"),
        ("dev", Path("dev-set_1.1") / "dev" / "subtrack1"),
        ("test", Path("test-set_1.1") / "test" / "subtrack1"),
    ]

    docs = []
    stats = {
        "by_split": Counter(),
        "by_label": Counter(),
        "terms_by_label": defaultdict(Counter),
        "code_counter": Counter(),
        "code_to_names": defaultdict(Counter),
        "entities_per_doc": [],
    }

    bg_dir = data_dir / "background-set" / "background"
    stats["background_docs"] = len(list(bg_dir.glob("*.txt"))) if bg_dir.exists() else 0

    for split_name, rel_path in splits:
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
            stats["by_split"][split_name] += 1
            stats["entities_per_doc"].append(len(ents))

            for ent in ents:
                stats["by_label"][ent["label"]] += 1
                stats["terms_by_label"][ent["label"]][ent["text"].lower()] += 1
                if ent["code"]:
                    stats["code_counter"][ent["code"]] += 1
                    stats["code_to_names"][ent["code"]][ent["text"].lower()] += 1

            docs.append({
                "id": doc_id,
                "split": split_name,
                "char_length": len(parsed["text"]),
                "entities_count": len(ents),
                "entities": ents,
                "raw_text": parsed["text"],
            })

    return docs, stats


def render_highlighted_text(raw_text: str, entities: list, active_labels: set) -> str:
    """Inserta marcas HTML para resaltar menciones según los offsets y categorías activas."""
    filtered_entities = [e for e in entities if e["label"] in active_labels]
    if not filtered_entities:
        return f"<div class='clinical-narrative'><p>{html.escape(raw_text).replace(chr(10), '<br>')}</p></div>"

    # Filtrar solapamientos (quedarse con la más larga)
    valid_ents = []
    last_end = -1
    for ent in sorted(filtered_entities, key=lambda x: (x["start"], -(x["end"] - x["start"]))):
        if ent["start"] >= last_end:
            valid_ents.append(ent)
            last_end = ent["end"]

    # Invertir orden para reemplazar de final a principio
    chars = list(raw_text)
    for ent in sorted(valid_ents, key=lambda x: x["start"], reverse=True):
        s, e = ent["start"], ent["end"]
        if s < 0 or e > len(raw_text):
            continue

        label_class = ent["label"].lower().replace("_", "-")
        code_tag = f"<span class='sn-tag'>{html.escape(ent['code'])}</span>" if ent.get("code") else ""
        code_str = ent.get('code') or 'no mapeado'
        open_tag = f"<mark class='ent-mark ent-{label_class}' title='{ent['label']} | SNOMED: {code_str}'>"
        close_tag = f"{code_tag}</mark>"

        orig_slice = "".join(chars[s:e])
        escaped_slice = html.escape(orig_slice)
        chars[s:e] = [open_tag + escaped_slice + close_tag]

    rendered = "".join(chars)
    rendered = rendered.replace("\n\n", "</p><p>").replace("\n", "<br>")
    return f"<div class='clinical-narrative'><p>{rendered}</p></div>"


# -----------------------------------------------------------------------------
# Carga principal de datos
# -----------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent
CANDIDATE_DATA_DIRS = [
    PROJECT_ROOT / "data" / "pharmaconer" / "pharmaconer",
    PROJECT_ROOT / "data" / "pharmaconer",
    Path("data/pharmaconer/pharmaconer").resolve(),
    Path("data/pharmaconer").resolve(),
]
found_data_dir = next(
    (p for p in CANDIDATE_DATA_DIRS if p.exists() and (p / "train-set_1.1").exists()),
    CANDIDATE_DATA_DIRS[0],
)
DATA_DIR = str(found_data_dir)
docs, stats = load_dataset(DATA_DIR)

if not docs:
    st.error(
        f"No se encontraron datos del corpus en `{DATA_DIR}`.\n\n"
        "Por favor, descarga el dataset ejecutando en tu terminal:\n\n"
        "```bash\npython scripts/download_datasets.py\n```\n\n"
        "o si usas `uv`:\n\n"
        "```bash\nuv run python scripts/download_datasets.py\n```"
    )
    st.stop()


# -----------------------------------------------------------------------------
# Barra Lateral (Sidebar)
# -----------------------------------------------------------------------------
with st.sidebar:
    st.title("🩺 CU-03 PLN Clínico")
    st.caption("Extracción de información y normalización a SNOMED CT")
    st.markdown("---")

    # Filtro por Split
    split_options = ["Todos", "train", "dev", "test"]
    selected_split = st.selectbox("📂 Partición oficial", split_options, index=2)  # 'dev' por defecto

    # Filtro de texto / búsqueda
    search_query = st.text_input("🔍 Buscar término o ID", value="")

    # Filtrar lista de documentos
    filtered_docs = docs
    if selected_split != "Todos":
        filtered_docs = [d for d in filtered_docs if d["split"] == selected_split]
    if search_query.strip():
        q = search_query.strip().lower()
        filtered_docs = [d for d in filtered_docs if q in d["id"].lower() or q in d["raw_text"].lower()]

    st.write(f"**Casos encontrados:** {len(filtered_docs)} de {len(docs)}")

    # Botones de acceso rápido
    col_q1, col_q2 = st.columns(2)
    with col_q1:
        if st.button("⭐ Caso 0013-1", use_container_width=True):
            st.session_state["target_doc_id"] = "S0004-06142006000700013-1"
    with col_q2:
        if st.button("🎲 Aleatorio", use_container_width=True):
            st.session_state["target_doc_id"] = random.choice(filtered_docs or docs)["id"]

    # Selector de documento
    doc_ids = [d["id"] for d in filtered_docs]
    default_id = st.session_state.get("target_doc_id", "S0004-06142006000700013-1")
    default_idx = doc_ids.index(default_id) if default_id in doc_ids else 0

    selected_doc_id = st.selectbox(
        "📄 Seleccionar caso clínico",
        doc_ids,
        index=default_idx if doc_ids else 0,
    )
    st.session_state["target_doc_id"] = selected_doc_id

    st.markdown("---")
    st.markdown("##### 🏷️ Categorías a resaltar")
    highlight_normalizables = st.checkbox("Fármacos (NORMALIZABLES)", value=True)
    highlight_proteinas = st.checkbox("Proteínas y Genes (PROTEINAS)", value=True)
    highlight_unclear = st.checkbox("Dudosos (UNCLEAR)", value=True)
    highlight_no_normalizables = st.checkbox("No Normalizables", value=True)

    active_labels = set()
    if highlight_normalizables:
        active_labels.add("NORMALIZABLES")
    if highlight_proteinas:
        active_labels.add("PROTEINAS")
    if highlight_unclear:
        active_labels.add("UNCLEAR")
    if highlight_no_normalizables:
        active_labels.add("NO_NORMALIZABLES")


# -----------------------------------------------------------------------------
# Documento activo
# -----------------------------------------------------------------------------
current_doc = next((d for d in docs if d["id"] == selected_doc_id), docs[0])


# -----------------------------------------------------------------------------
# Pestañas Principales (Tabs)
# -----------------------------------------------------------------------------
tab_viewer, tab_analytics, tab_about = st.tabs([
    "📖 Visor de Casos Clínicos",
    "📊 Estadísticas del Corpus",
    "ℹ️ Arquitectura & Caso de Uso",
])


# -----------------------------------------------------------------------------
# TAB 1: VISOR CLÍNICO
# -----------------------------------------------------------------------------
with tab_viewer:
    # Cabecera de metadatos del caso
    c1, c2, c3, c4 = st.columns([3, 1, 1, 1])
    with c1:
        st.subheader(f"Informe Clínico: `{current_doc['id']}`")
    with c2:
        st.metric("Partición", current_doc["split"].upper())
    with c3:
        st.metric("Menciones", current_doc["entities_count"])
    with c4:
        st.metric("Longitud", f"{current_doc['char_length']} car.")

    # Leyenda visual
    st.markdown(
        """
        <div style="display:flex; gap: 1rem; flex-wrap: wrap; margin-bottom: 0.8rem; font-size: 0.82rem;">
            <span>🟢 <strong style="color:#10b981">NORMALIZABLES</strong> (Fármacos mapeables)</span>
            <span>🔵 <strong style="color:#0ea5e9">PROTEINAS</strong> (Genes, receptores)</span>
            <span>🟣 <strong style="color:#a855f7">UNCLEAR</strong> (Dudosos)</span>
            <span>🟡 <strong style="color:#f59e0b">NO_NORMALIZABLES</strong> (Sustancias generales)</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Contenedor a dos columnas: Texto vs Menciones
    col_text, col_info = st.columns([3, 2])

    with col_text:
        st.markdown("##### 📄 Texto Clínico Anotado")
        highlighted_html = render_highlighted_text(
            current_doc["raw_text"],
            current_doc["entities"],
            active_labels,
        )
        st.markdown(highlighted_html, unsafe_allow_html=True)

    with col_info:
        st.markdown("##### 📋 Menciones Extraídas & Normalización")
        if current_doc["entities"]:
            # Tabla de entidades
            df_entities = pd.DataFrame([
                {
                    "Mención": e["text"],
                    "Categoría": e["label"],
                    "Offsets": f"[{e['start']}:{e['end']}]",
                    "SNOMED CT": e["code"] or "—",
                    "Estado": e["norm_status"],
                }
                for e in current_doc["entities"]
            ])
            st.dataframe(df_entities, use_container_width=True, hide_index=True)

            # Inspector interactivo de mención seleccionada
            st.markdown("---")
            st.markdown("##### 🔎 Inspector de Entidad")
            entity_names = [f"#{i+1}: {e['text']} ({e['label']})" for i, e in enumerate(current_doc["entities"])]
            selected_ent_idx = st.selectbox(
                "Seleccionar entidad para inspeccionar:",
                range(len(entity_names)),
                format_func=lambda i: entity_names[i],
            )
            ent_obj = current_doc["entities"][selected_ent_idx]

            st.write(f"**Término exacto:** `{ent_obj['text']}`")
            st.write(f"**Categoría:** `{ent_obj['label']}`")
            st.write(f"**Offsets:** `start={ent_obj['start']}`, `end={ent_obj['end']}` (longitud: {ent_obj['end'] - ent_obj['start']} car.)")
            st.write(f"**Estado de Normalización:** `{ent_obj['norm_status']}`")

            if ent_obj["code"]:
                st.success(f"**Código SNOMED CT:** `{ent_obj['code']}`")
                snomed_url = f"https://browser.ihtsdotools.org/?perspective=full&conceptId1={ent_obj['code']}"
                st.markdown(f"[🌐 Abrir concepto `{ent_obj['code']}` en el SNOMED CT Browser oficial ↗]({snomed_url})")
            else:
                st.info("Sin código terminológico unívoco asignado (marcado como `not_found`).")
        else:
            st.info("Este caso clínico no contiene menciones anotadas en el subtrack.")

    # Expander con el JSON Canónico según la especificación técnica
    st.markdown("---")
    with st.expander("⚙️ Ver Contrato JSON Canónico (specs/generacion-json.md)", expanded=False):
        canonical_json = {
            "schema_version": "1.0",
            "document_id": current_doc["id"],
            "language": "es",
            "source_text": current_doc["raw_text"],
            "entities": [
                {
                    "text": e["text"],
                    "type": "farmaco" if e["label"] == "NORMALIZABLES" else ("proteina" if e["label"] == "PROTEINAS" else e["label"].lower()),
                    "start": e["start"],
                    "end": e["end"],
                    "coding": {
                        "system": "SNOMED_CT" if e["code"] else None,
                        "code": e["code"],
                        "display": e["text"] if e["code"] else None,
                    },
                    "normalization_status": e["norm_status"],
                }
                for e in current_doc["entities"]
            ],
        }
        json_str = json.dumps(canonical_json, indent=2, ensure_ascii=False)
        st.code(json_str, language="json")
        st.download_button(
            label="💾 Descargar JSON canónico del caso",
            data=json_str,
            file_name=f"{current_doc['id']}_cu03.json",
            mime="application/json",
        )


# -----------------------------------------------------------------------------
# TAB 2: ANALYTICS & ESTADÍSTICAS DEL CORPUS
# -----------------------------------------------------------------------------
with tab_analytics:
    st.subheader("📊 Métricas Globales del Corpus PharmaCoNER")
    
    total_entities = sum(stats["by_label"].values())
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("Casos Oro Anotados", len(docs))
    with m2:
        st.metric("Total Menciones", f"{total_entities:,}")
    with m3:
        st.metric("Casos Background", f"{stats['background_docs']:,}")
    with m4:
        st.metric("Densidad Media", f"{round(total_entities / len(docs), 2)} menciones/caso")

    st.markdown("---")
    col_chart1, col_chart2 = st.columns(2)

    with col_chart1:
        st.markdown("##### 🏷️ Distribución de Menciones por Categoría")
        df_cat = pd.DataFrame([
            {"Categoría": cat, "Menciones": count, "Porcentaje": round((count / total_entities) * 100, 1)}
            for cat, count in stats["by_label"].items()
        ]).sort_values("Menciones", ascending=False)

        chart_cat = (
            alt.Chart(df_cat)
            .mark_bar(cornerRadius=6)
            .encode(
                x=alt.X("Menciones:Q", title="Total menciones"),
                y=alt.Y("Categoría:N", sort="-x", title="Categoría"),
                color=alt.Color("Categoría:N", legend=None),
                tooltip=["Categoría", "Menciones", "Porcentaje"],
            )
            .properties(height=260)
        )
        st.altair_chart(chart_cat, use_container_width=True)

    with col_chart2:
        st.markdown("##### 📂 Casos por Partición Oficial")
        df_splits = pd.DataFrame([
            {"Partición": sp.upper(), "Documentos": count}
            for sp, count in stats["by_split"].items()
        ])
        chart_split = (
            alt.Chart(df_splits)
            .mark_bar(cornerRadius=6, color="#6366f1")
            .encode(
                x=alt.X("Documentos:Q", title="Número de casos"),
                y=alt.Y("Partición:N", sort="-x"),
                tooltip=["Partición", "Documentos"],
            )
            .properties(height=260)
        )
        st.altair_chart(chart_split, use_container_width=True)

    st.markdown("---")
    col_terms, col_codes = st.columns(2)

    with col_terms:
        st.markdown("##### 💊 Top Fármacos Más Frecuentes (NORMALIZABLES)")
        top_norm_terms = stats["terms_by_label"]["NORMALIZABLES"].most_common(12)
        df_top_terms = pd.DataFrame(top_norm_terms, columns=["Fármaco / Sustancia", "Frecuencia"])
        chart_terms = (
            alt.Chart(df_top_terms)
            .mark_bar(cornerRadius=5, color="#10b981")
            .encode(
                x=alt.X("Frecuencia:Q", title="Apariciones en el corpus"),
                y=alt.Y("Fármaco / Sustancia:N", sort="-x"),
                tooltip=["Fármaco / Sustancia", "Frecuencia"],
            )
            .properties(height=350)
        )
        st.altair_chart(chart_terms, use_container_width=True)

    with col_codes:
        st.markdown("##### 🌐 Top Códigos SNOMED CT Más Asignados")
        top_codes_data = []
        for code, count in stats["code_counter"].most_common(12):
            rep_term = stats["code_to_names"][code].most_common(1)[0][0] if stats["code_to_names"][code] else "—"
            top_codes_data.append({
                "Código SNOMED": str(code),
                "Concepto Representativo": rep_term.title(),
                "Asignaciones": count,
            })
        df_top_codes = pd.DataFrame(top_codes_data)
        chart_codes = (
            alt.Chart(df_top_codes)
            .mark_bar(cornerRadius=5, color="#818cf8")
            .encode(
                x=alt.X("Asignaciones:Q", title="Total asignaciones"),
                y=alt.Y("Código SNOMED:N", sort="-x"),
                tooltip=["Código SNOMED", "Concepto Representativo", "Asignaciones"],
            )
            .properties(height=350)
        )
        st.altair_chart(chart_codes, use_container_width=True)


# -----------------------------------------------------------------------------
# TAB 3: ACERCA DEL PROYECTO & ARQUITECTURA
# -----------------------------------------------------------------------------
with tab_about:
    st.subheader("Caso de Uso CU-03 PIIA2")
    st.markdown(
        """
        ### Extracción y estructuración de información clínica en español mediante PLN
        - **Entidad colaboradora:** [DIH DATAlife](https://dihdatalife.com/) (Digital Innovation Hub).
        - **Tutora:** Gema Novo Rego (`gema@dihdatalife.com`).
        - **Problema de negocio:** El **80% de la información clínica** en los hospitales está en texto libre no estructurado (informes de alta, consultas). Esto impide su explotación estadística, análisis masivo y uso secundario en investigación.
        - **Referente asistencial:** El **SERGAS** avanza hacia la estructuración mediante el sistema **IANUS**, agrupando por problemas de salud y utilizando servidores terminológicos basados en **SNOMED CT**.

        ---
        ### Pipeline Arquitectónico por Etapas
        1. **Entrada de Texto Clínico:** Casos clínicos de revistas biomédicas en español (corpus SPACCC, sin datos personales sensibles).
        2. **Extracción de Entidades (NER):** Detección de fármacos, enfermedades, síntomas y procedimientos con offsets de caracteres exactos.
        3. **Normalización Terminológica:** Mapeo a identificadores de **SNOMED CT** y **CIE-10-ES**.
        4. **Salida Estructurada Canónica:** Generación y validación de esquemas **JSON** e interoperabilidad con recursos **HL7 FHIR**.
        """
    )
