#!/usr/bin/env python3
"""Procesa un texto clínico y escribe el JSON canónico (specs/generacion-json.md).

Ejemplos:
    python scripts/run_pipeline.py --text "Se pautó enoxaparina 40 mg y omeprazol."
    python scripts/run_pipeline.py --file caso.txt --out caso.json
    python scripts/run_pipeline.py --model models/baseline --file caso.txt

Sin --model entrena el baseline en la partición train (tarda unos segundos).
"""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from cu03.corpus import find_data_dir  # noqa: E402
from cu03.pipeline import InvalidInputError, Pipeline  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--text")
    src.add_argument("--file", type=Path)
    ap.add_argument("--id", default=None, help="Identificador del documento (sin datos personales)")
    ap.add_argument("--model", type=Path, default=None)
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()

    pipe = Pipeline.load(args.model) if args.model else Pipeline.from_corpus(("train",), find_data_dir(ROOT))
    raw = args.text if args.text is not None else args.file.read_bytes()
    doc_id = args.id or (args.file.stem if args.file else None)
    try:
        out = pipe.process_json(raw, doc_id)
    except InvalidInputError as exc:
        print(exc, file=sys.stderr)
        return 2
    if args.out:
        args.out.write_text(out + "\n", encoding="utf-8")
    else:
        sys.stdout.reconfigure(encoding="utf-8")
        print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
