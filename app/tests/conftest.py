"""Fixtures con un mini-corpus sintético: los tests no necesitan descargar PharmaCoNER."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from cu03.corpus import Annotation, Document  # noqa: E402
from cu03.pipeline import Pipeline  # noqa: E402


def _doc(doc_id, text, spans):
    anns = []
    for i, (mention, label, code) in enumerate(spans, 1):
        s = text.index(mention)
        anns.append(Annotation(f"T{i}", label, s, s + len(mention), mention, code))
    return Document(doc_id, "train", text, anns)


@pytest.fixture(scope="session")
def train_docs():
    return [
        _doc("syn-1", "Se inició tratamiento con enoxaparina y omeprazol.",
             [("enoxaparina", "NORMALIZABLES", "372744005"), ("omeprazol", "NORMALIZABLES", "387137007")]),
        _doc("syn-2", "Recibió ácido acetilsalicílico; PSA elevado.",
             [("ácido acetilsalicílico", "NORMALIZABLES", "387458008"), ("PSA", "PROTEINAS", "102687007")]),
        # 'heparina' se anota con dos códigos distintos -> caso ambiguo
        _doc("syn-3", "Se administró heparina.", [("heparina", "NORMALIZABLES", "372877000")]),
        _doc("syn-4", "Continuó con heparina.", [("heparina", "NORMALIZABLES", "96382006")]),
        # sustancia sin código -> not_found
        _doc("syn-5", "Exposición a disolventes orgánicos.",
             [("disolventes orgánicos", "NO_NORMALIZABLES", None)]),
    ]


@pytest.fixture(scope="session")
def pipe(train_docs):
    return Pipeline.train(train_docs, min_precision=0.5, min_agreement=0.8)
