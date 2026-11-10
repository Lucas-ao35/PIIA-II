"""specs/normalizacion-clinica.md — criterios 1, 2, 3, 4 y 6."""

from cu03.normalization import AMBIGUOUS, MATCHED, NOT_FOUND


def test_caso_mapeado(pipe):
    r = pipe.normalizer.normalize("Enoxaparina")
    assert r.status == MATCHED and r.system == "SNOMED_CT" and r.code == "372744005"
    assert r.display and r.code in pipe.normalizer.known_codes


def test_caso_no_mapeado(pipe):
    r = pipe.normalizer.normalize("disolventes orgánicos")
    assert r.status == NOT_FOUND and r.coding() == {"system": None, "code": None, "display": None}


def test_forma_desconocida_es_not_found(pipe):
    assert pipe.normalizer.normalize("fármaco inventado").status == NOT_FOUND


def test_caso_ambiguo(pipe):
    r = pipe.normalizer.normalize("heparina")
    assert r.status == AMBIGUOUS and r.code is None and set(r.candidates) == {"372877000", "96382006"}


def test_un_resultado_por_entidad(pipe):
    text = "Heparina, enoxaparina y disolventes orgánicos."
    mentions = pipe.extract(text)
    results = pipe.normalize(mentions)
    assert len(results) == len(mentions) == 3
    assert sorted(r.status for r in results) == sorted([AMBIGUOUS, MATCHED, NOT_FOUND])


def test_documento_sin_entidades(pipe):
    assert pipe.process("Exploración física sin hallazgos.")["entities"] == []


def test_entrada_con_varias_categorias(pipe):
    # PSA (PROTEINAS) se detecta pero no se emite: fuera de las categorías del esquema 1.0
    doc = pipe.process("Omeprazol y PSA elevado.")
    assert [e["text"] for e in doc["entities"]] == ["Omeprazol"]
    assert {m.label for m in pipe.extract("Omeprazol y PSA elevado.")} == {"NORMALIZABLES", "PROTEINAS"}
