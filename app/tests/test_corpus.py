from cu03.corpus import LABEL_TO_TYPE, parse_brat
from cu03.schema import ENTITY_TYPES


def _write(tmp_path, text, ann):
    t, a = tmp_path / "doc.txt", tmp_path / "doc.ann"
    t.write_text(text, encoding="utf-8", newline="")
    a.write_text(ann, encoding="utf-8")
    return a, t


def test_parse_brat_offsets_y_codigos(tmp_path):
    text = "Paciente tratado con omeprazol.\nPSA normal."
    ann = ("T1\tNORMALIZABLES 21 30\tomeprazol\n#1\tAnnotatorNotes T1\t387137007\n"
           "T2\tPROTEINAS 32 35\tPSA\n#2\tAnnotatorNotes T2\t<null>\n")
    doc = parse_brat(*_write(tmp_path, text, ann))
    assert [(a.text, a.code) for a in doc.annotations] == [("omeprazol", "387137007"), ("PSA", None)]
    assert all(doc.text[a.start:a.end] == a.text for a in doc.annotations)


def test_repara_offsets_desplazados(tmp_path):
    # Reproduce el defecto real de S0211-69952015000200015-1 (offsets +1)
    text = "Proteinuria de Bence-Jones negativa."
    ann = "T1\tPROTEINAS 16 27\tBence-Jones\n"
    doc = parse_brat(*_write(tmp_path, text, ann))
    a = doc.annotations[0]
    assert doc.text[a.start:a.end] == "Bence-Jones" and doc.repaired


def test_descarta_anotacion_irrecuperable(tmp_path):
    doc = parse_brat(*_write(tmp_path, "Texto sin la mención.", "T1\tNORMALIZABLES 0 5\tinsulina\n"))
    assert doc.annotations == [] and doc.dropped


def test_no_normaliza_saltos_de_linea(tmp_path):
    text = "Línea 1\r\nCon omeprazol."
    s = text.index("omeprazol")
    doc = parse_brat(*_write(tmp_path, text, f"T1\tNORMALIZABLES {s} {s + 9}\tomeprazol\n"))
    assert doc.text == text and not doc.repaired


def test_mapeo_de_etiquetas_documentado():
    assert {t for t in LABEL_TO_TYPE.values() if t} <= set(ENTITY_TYPES)
