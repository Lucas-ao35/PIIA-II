#!/usr/bin/env python3
"""Evaluación reproducible del pipeline CU-03 con una única orden.

Ejemplos:
    python scripts/evaluate.py                       # entrena en train, evalúa en dev
    python scripts/evaluate.py --split test --train-splits train dev   # evaluación final
    python scripts/evaluate.py --min-precision 0.3   # explorar el balance P/R en dev

Genera reports/eval-<split>.json y reports/eval-<split>.md.
"""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from cu03.corpus import find_data_dir, load_split, load_splits  # noqa: E402
from cu03.evaluation import evaluate, write_report  # noqa: E402
from cu03.pipeline import Pipeline  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--split", choices=["dev", "test"], default="dev")  
                        # Selecciona la partición de evaluación
    ap.add_argument("--train-splits", nargs="+", default=["train"], choices=["train", "dev"])
                        # Selecciona las particiones de entrenamiento
    ap.add_argument("--min-precision", type=float, default=0.5)
                        # Establece el umbral mínimo de precisión para filtrar mediciones del extractor NER
    ap.add_argument("--min-agreement", type=float, default=0.8)
                        # Establece el umbral mínimo de acuerdo para filtrar mediciones del normalizador
    ap.add_argument("--data-dir", type=Path, default=None)
                        # Define una ruta personalizada al corpus
    ap.add_argument("--out", type=Path, default=ROOT / "reports")
                        # Define una ruta personalizada para guardar los informes de evaluación
    ap.add_argument("--save-model", type=Path, default=None,
                    help="Guarda el pipeline entrenado (p. ej. models/baseline)")
                        # Define una ruta personalizada para guardar el modelo entrenado
    args = ap.parse_args()

    if args.split in args.train_splits:
        # Comprobamos que la partición de evaluación no esté incluida en las particiones de entrenamiento
        ap.error(f"La partición de evaluación '{args.split}' no puede usarse para entrenar.")

    # Cargamos el directorio de datos del corpus o buscamos uno automáticamente
    data_dir = args.data_dir or find_data_dir(ROOT)
    # Cargamos los documentos de entrenamiento y evaluación
    train_docs = load_splits(args.train_splits, data_dir)
    # Cargamos los documentos de evaluación
    eval_docs = load_split(args.split, data_dir)

    # Entrenamos el pipeline con los documentos de entrenamiento y los parámetros especificados
    pipe = Pipeline.train(train_docs, args.min_precision, args.min_agreement)
    if args.save_model:
        pipe.save(args.save_model)

    # Invocamos evaluate para procesar los documentos de prueba y calcular todas las métricas NER, normalización y validez JSON. Devuelve un diccionario con los resultados y lo guardamos en disco.
    report = evaluate(pipe, eval_docs, args.split, args.train_splits)
    # Escribimos el informe de evaluación en formato Markdown y JSON en la ruta especificada por --out
    jp, mp = write_report(report, args.out)

    # Resumen en pantalla con las métricas clave
    nat, proj, norm = (report["extraction_native_labels"]["micro"],
                       report["extraction_project_types"]["micro"], report["normalization"])
    print(f"[{args.split}] NER nativo  F1={nat['f1']:.3f}  P={nat['precision']:.3f}  R={nat['recall']:.3f}")
    print(f"[{args.split}] NER 'drug'  F1={proj['f1']:.3f}  P={proj['precision']:.3f}  R={proj['recall']:.3f}")
    g = norm["on_gold_mentions"]
    print(f"[{args.split}] Normalización aislada  exactitud={g['accuracy_top1']:.3f}  cobertura={g['coverage']:.3f}")
    print(f"[{args.split}] Normalización cascada  exactitud={norm['accuracy_top1']:.3f}  cobertura={norm['coverage']:.3f}")
    print(f"[{args.split}] JSON válidos {report['output_validity']['rate']:.1%}")
    print(f"Informe: {mp}\n         {jp}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
