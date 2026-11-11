"""Evaluación reproducible por etapas (specs/evaluacion-resultados.md).

- Extracción: P/R/F1 con coincidencia ESTRICTA (mismos límites y misma
  etiqueta), por categoría, micro y macro. Se informa en dos vistas:
  etiquetas nativas de PharmaCoNER y categorías del proyecto (`type`).
- Normalización: sobre las menciones correctamente extraídas cuyo gold
  tiene código -> exactitud top-1 y cobertura (proporción `matched`).
- Salida: proporción de documentos JSON que validan contra el contrato.
"""

from __future__ import annotations

import datetime as dt
import importlib.metadata as md
import json
import platform
from collections import Counter
from pathlib import Path

from . import __version__
from .corpus import CORPUS_NAME, CORPUS_VERSION, LABEL_TO_TYPE, Document
from .pipeline import Pipeline
from .schema import SCHEMA_VERSION, is_valid

LOW_SUPPORT = 30  # por debajo, la métrica de la categoría se considera inestable


def prf(tp: int, fp: int, fn: int) -> dict:
    """
    Función para calcular las métricas fundamentales de clasificación binaria:
    - Precisión (Precision): proporción de verdaderos positivos sobre el total de predicciones positivas.   
    - Recall (Sensibilidad): proporción de verdaderos positivos sobre el total de casos positivos reales.
    - F1 Score: media armónica de precisión y recall, proporcionando una medida balanceada de la precisión y la sensibilidad.
    - Soporte (Support): número total de casos positivos reales.
    """
    p = tp / (tp + fp) if tp + fp else 0.0
    r = tp / (tp + fn) if tp + fn else 0.0
    f = 2 * p * r / (p + r) if p + r else 0.0
    return {"precision": round(p, 4), "recall": round(r, 4), "f1": round(f, 4),
            "tp": tp, "fp": fp, "fn": fn, "support": tp + fn}


def strict_ner_metrics(gold: set[tuple], pred: set[tuple]) -> dict:
    """
    Calcula las métricas del modulo NER (Named Entity Recognition) con coincidencia estricta.
    - Métricas por etiqueta (per_label): P/R/F1 y soporte para cada etiqueta presente en los conjuntos gold y pred de forma individual.
    - Métricas micro (micro): P/R/F1 y soporte considerando todas las etiquetas conjuntamente, proporcionando una visión global del rendimiento del modelo.
    - F1 macro (macro_f1): promedia de forma no ponderada las métricas del F1 de cadaa etiqueta individual.
    gold/pred: conjuntos de (doc_id, start, end, label)."""
    labels = sorted({g[3] for g in gold} | {p[3] for p in pred})
    per = {}
    for lab in labels:
        g = {x for x in gold if x[3] == lab}
        p = {x for x in pred if x[3] == lab}
        per[lab] = prf(len(g & p), len(p - g), len(g - p))
    micro = prf(len(gold & pred), len(pred - gold), len(gold - pred))
    macro_f1 = round(sum(v["f1"] for v in per.values()) / len(per), 4) if per else 0.0
    return {"match": "strict", "per_label": per, "micro": micro, "macro_f1": macro_f1}


def _deps() -> dict:
    """
    Devuelve un diccionario con las versiones de Python y de los paquetes relevantes
    """
    out = {"python": platform.python_version()}
    for pkg in ("jsonschema", "pandas", "streamlit"):
        try:
            out[pkg] = md.version(pkg)
        except md.PackageNotFoundError:
            pass
    return out


def evaluate(pipeline: Pipeline, docs: list[Document], split: str,
             train_splits: list[str]) -> dict:
    """
    Evaluación sobre una lista de documentos y mide 4 aspectos:
    - Extracción NER: nativa, manteniendo las etiquetas originales de PharmaCoNER
    - Normalización de terminología: mide el desempeño de la normalización sobre las menciones que
    el NER extrajo correctamente y que tienen código gold. Registra el número de menciones evaluables,
    el conteo por estados, la exactitud del Top-1 y la cobertura.
    - normalización aislada: aplicando normalización a todas las menciones reales del gold standard e
    ignorando el desempeño del NER. Sirve como referencia para la spec, sin el sesgo introducido de los
    errores por la extracción previa.
    - Validez de la salida: mide la proporción de documentos que validaDOS, también recopila los 15 FP y
    15 FN más frecuentes en términos de texto. Registra las limitaciones conocidas del pipeline y del corpus.

    """
    gold_native, pred_native = set(), set()
    gold_type, pred_type = set(), set()
    gold_codes: dict[tuple, str] = {}
    norm_counts = Counter()
    norm_correct = norm_evaluable = 0
    valid_docs = 0
    errors_fp, errors_fn = Counter(), Counter()
    pred_text: dict[tuple, str] = {}
    repaired = sum(len(d.repaired) for d in docs)
    dropped = sum(len(d.dropped) for d in docs)
    empty_docs = sum(1 for d in docs if not d.annotations)

    for d in docs:
        for a in d.annotations:
            gold_native.add((d.id, a.start, a.end, a.label))
            t = LABEL_TO_TYPE.get(a.label)
            if t:
                gold_type.add((d.id, a.start, a.end, t))
            if a.code:
                gold_codes[(d.id, a.start, a.end, a.label)] = a.code

        mentions = pipeline.extract(d.text)
        results = pipeline.normalize(mentions)
        for m, r in zip(mentions, results):
            key = (d.id, m.start, m.end, m.label)
            pred_native.add(key)
            pred_text[key] = m.text
            t = LABEL_TO_TYPE.get(m.label)
            if t:
                pred_type.add((d.id, m.start, m.end, t))
            if key in gold_codes:  # mención bien extraída con referencia de oro
                norm_evaluable += 1
                norm_counts[r.status] += 1
                norm_correct += int(r.status == "matched" and r.code == gold_codes[key])
        if is_valid(pipeline.build_document(d.text, mentions, results, d.id)):
            valid_docs += 1

    for x in pred_native - gold_native:
        errors_fp[pred_text[x].lower()] += 1
    text_by_id = {d.id: d.text for d in docs}
    for x in gold_native - pred_native:
        errors_fn[text_by_id[x[0]][x[1]:x[2]].lower()] += 1

    # Normalización aislada: se aplica a TODAS las menciones gold con código
    # (extracción perfecta), para medir la etapa sin el sesgo del NER.
    iso_counts, iso_correct = Counter(), 0
    for d in docs:
        for a in d.annotations:
            if a.code:
                r = pipeline.normalizer.normalize(a.text)
                iso_counts[r.status] += 1
                iso_correct += int(r.status == "matched" and r.code == a.code)
    iso_total = sum(iso_counts.values())

    native = strict_ner_metrics(gold_native, pred_native)
    project = strict_ner_metrics(gold_type, pred_type)
    matched = norm_counts["matched"]
    normalization = {
        "evaluable_mentions": norm_evaluable,
        "status_counts": dict(norm_counts),
        "accuracy_top1": round(norm_correct / norm_evaluable, 4) if norm_evaluable else 0.0,
        "accuracy_on_matched": round(norm_correct / matched, 4) if matched else 0.0,
        "coverage": round(matched / norm_evaluable, 4) if norm_evaluable else 0.0,
        "terminology": "SNOMED CT (códigos del gold de PharmaCoNER, sin descripciones)",
        "on_gold_mentions": {
            "mentions": iso_total, "status_counts": dict(iso_counts),
            "accuracy_top1": round(iso_correct / iso_total, 4) if iso_total else 0.0,
            "accuracy_on_matched": round(iso_correct / iso_counts["matched"], 4) if iso_counts["matched"] else 0.0,
            "coverage": round(iso_counts["matched"] / iso_total, 4) if iso_total else 0.0,
        },
    }

    limitations = [
        "El normalizador solo conoce formas vistas en entrenamiento: las menciones "
        "nuevas quedan como not_found (cobertura limitada por diseño).",
        "PROTEINAS y UNCLEAR no pertenecen a las categorías del esquema 1.0: se evalúan "
        "con etiqueta nativa pero no se emiten en el JSON.",
        "El baseline de diccionario no usa contexto: no distingue usos no clínicos de una "
        "misma forma ni resuelve abreviaturas ambiguas.",
        "PharmaCoNER contiene casos clínicos publicados; el rendimiento no generaliza "
        "necesariamente a historias clínicas reales.",
    ]
    for lab, v in native["per_label"].items():
        if v["support"] < LOW_SUPPORT:
            limitations.append(f"Categoría {lab} con soporte bajo ({v['support']}): métrica inestable.")
    if repaired or dropped:
        limitations.append(f"Gold con offsets inconsistentes: {repaired} reparados, {dropped} descartados.")

    return {
        "run": {
            "date": dt.datetime.now().isoformat(timespec="seconds"),
            "cu03_version": __version__,
            "corpus": CORPUS_NAME, "corpus_version": CORPUS_VERSION,
            "eval_split": split, "train_splits": train_splits,
            "documents": len(docs), "documents_without_entities": empty_docs,
            "seed": None, "deterministic": True,
            "pipeline": pipeline.config(), "label_to_type": LABEL_TO_TYPE,
            "schema_version": SCHEMA_VERSION, "dependencies": _deps(),
        },
        "extraction_native_labels": native,
        "extraction_project_types": project,
        "normalization": normalization,
        "output_validity": {"json_valid_documents": valid_docs, "documents": len(docs),
                            "rate": round(valid_docs / len(docs), 4) if docs else 0.0},
        "top_errors": {"false_positives": errors_fp.most_common(15),
                       "false_negatives": errors_fn.most_common(15)},
        "limitations": limitations,
    }


def to_markdown(r: dict) -> str:
    """
    Genera un informe en formato Markdown a partir del diccionario de resultados de la función evaluate()."""
    run = r["run"]
    lines = [
        f"# Informe de evaluación CU-03 — {run['eval_split']}",
        "",
        f"- Fecha: {run['date']} · cu03 {run['cu03_version']}",
        f"- Corpus: {run['corpus']} {run['corpus_version']} · evaluación sobre `{run['eval_split']}` "
        f"({run['documents']} documentos, {run['documents_without_entities']} sin entidades)",
        f"- Entrenamiento/ajuste: {', '.join(run['train_splits'])}",
        f"- NER: `{run['pipeline']['ner']['name']}` {run['pipeline']['ner']}",
        f"- Normalizador: `{run['pipeline']['normalizer']['name']}` {run['pipeline']['normalizer']}",
        f"- Determinista (sin semilla) · esquema JSON {run['schema_version']} · dependencias {run['dependencies']}",
        "",
    ]
    for title, key in (("Extracción — etiquetas nativas", "extraction_native_labels"),
                       ("Extracción — categorías del proyecto", "extraction_project_types")):
        m = r[key]
        lines += [f"## {title} (coincidencia {m['match']})", "",
                  "| Categoría | P | R | F1 | Soporte |", "|---|---|---|---|---|"]
        for lab, v in m["per_label"].items():
            lines.append(f"| {lab} | {v['precision']:.3f} | {v['recall']:.3f} | {v['f1']:.3f} | {v['support']} |")
        mi = m["micro"]
        lines += [f"| **micro** | **{mi['precision']:.3f}** | **{mi['recall']:.3f}** | **{mi['f1']:.3f}** | {mi['support']} |",
                  "", f"F1 macro: {m['macro_f1']:.3f}", ""]
    n = r["normalization"]
    g = n["on_gold_mentions"]
    lines += ["## Normalización aislada (todas las menciones gold con código)", "",
              "Mide la etapa sin depender del NER: es la cifra de referencia para la spec.", "",
              f"- Menciones: {g['mentions']} · estados: {g['status_counts']}",
              f"- Exactitud top-1: **{g['accuracy_top1']:.3f}** · exactitud sobre `matched`: {g['accuracy_on_matched']:.3f}",
              f"- Cobertura (`matched`): {g['coverage']:.3f}", ""]
    lines += ["## Normalización en cascada (menciones bien extraídas con código gold)", "",
              f"- Menciones evaluables: {n['evaluable_mentions']}",
              f"- Estados: {n['status_counts']}",
              f"- Exactitud top-1: **{n['accuracy_top1']:.3f}** · exactitud sobre `matched`: {n['accuracy_on_matched']:.3f}",
              f"- Cobertura (`matched`): {n['coverage']:.3f}",
              f"- Terminología: {n['terminology']}", "",
              "## Validez de la salida", "",
              f"- JSON válidos: {r['output_validity']['json_valid_documents']}/{r['output_validity']['documents']} "
              f"({r['output_validity']['rate']:.1%})", "",
              "## Errores más frecuentes", "",
              "Falsos positivos: " + ", ".join(f"`{t}` ({c})" for t, c in r["top_errors"]["false_positives"]),
              "",
              "Falsos negativos: " + ", ".join(f"`{t}` ({c})" for t, c in r["top_errors"]["false_negatives"]),
              "", "## Limitaciones", ""]
    lines += [f"- {x}" for x in r["limitations"]]
    return "\n".join(lines) + "\n"


def write_report(report: dict, out_dir: Path) -> tuple[Path, Path]:
    """
    Creamos una carpeta de salida y escribimos el informe en dos formatos: JSON y Markdown. 
    Devuelve las rutas de ambos ficheros."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = f"eval-{report['run']['eval_split']}"
    jp, mp = out_dir / f"{stem}.json", out_dir / f"{stem}.md"
    jp.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    mp.write_text(to_markdown(report), encoding="utf-8")
    return jp, mp
