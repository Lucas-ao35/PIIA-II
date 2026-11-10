"""specs/generacion-json.md — batería de >= 10 casos (criterios 1 a 9)."""

import json

import pytest

from cu03.pipeline import InvalidInputError
from cu03.schema import SchemaValidationError, is_valid, validate_document

CASOS_VALIDOS = {
    "acentos_y_enie": "Niño con ácido acetilsalicílico pautado por el señor médico.",
    "vacio": "",
    "solo_espacios": "   \n ",
    "sin_entidades": "Paciente asintomático, sin tratamiento.",
    "varias_entidades": "Enoxaparina, omeprazol y ácido acetilsalicílico.",
    "entidad_sin_codigo": "Exposición a disolventes orgánicos.",
    "entidad_ambigua": "Se mantuvo heparina.",
    "mayusculas": "OMEPRAZOL 20 MG.",
    "repetidas": "omeprazol ... omeprazol",
    "saltos_de_linea": "Antecedentes:\n\n- enoxaparina\r\n- omeprazol",
    "emoji_y_simbolos": "Toma omeprazol ✔ (20 mg/día) → bien.",
}


@pytest.mark.parametrize("name", sorted(CASOS_VALIDOS))
def test_salida_valida_contra_esquema(pipe, name):
    text = CASOS_VALIDOS[name]
    raw = pipe.process_json(text, document_id=f"test-{name}")
    doc = json.loads(raw)  # criterio 1: parser estándar
    validate_document(doc)  # criterios 2-6
    assert doc["source_text"] == text
    for e in doc["entities"]:
        assert set(e) >= {"text", "type", "start", "end", "coding", "normalization_status"}
        assert 0 <= e["start"] < e["end"] <= len(text) and text[e["start"]:e["end"]] == e["text"]


def test_unicode_sin_escapar(pipe):
    assert "ácido acetilsalicílico" in pipe.process_json("ácido acetilsalicílico")


def test_entidad_sin_codigo_no_se_pierde(pipe):
    (e,) = pipe.process("Exposición a disolventes orgánicos.")["entities"]
    assert e["normalization_status"] == "not_found" and e["coding"]["code"] is None


def test_orden_por_inicio(pipe):
    starts = [e["start"] for e in pipe.process(CASOS_VALIDOS["varias_entidades"])["entities"]]
    assert starts == sorted(starts) and len(starts) == 3


@pytest.mark.parametrize("bad", [None, 42, ["texto"], b"\xff\xfe"])
def test_entrada_invalida_error_identificable(pipe, bad):
    with pytest.raises(InvalidInputError, match="CU03-E001"):
        pipe.process(bad)


def test_bytes_utf8_se_aceptan(pipe):
    assert pipe.process("omeprazol".encode("utf-8"))["entities"][0]["text"] == "omeprazol"


@pytest.mark.parametrize("mutate", [
    lambda d: d["entities"][0].update(type="protein"),
    lambda d: d["entities"][0].update(normalization_status="mapped"),
    lambda d: d["entities"][0].update(end=999),
    lambda d: d["entities"][0].update(start=1),
    lambda d: d["entities"][0]["coding"].update(code=None),
    lambda d: d.pop("language"),
    lambda d: d["entities"].reverse(),
])
def test_validador_rechaza_salidas_incorrectas(pipe, mutate):
    doc = pipe.process("Enoxaparina y omeprazol.")
    assert is_valid(doc)
    mutate(doc)
    with pytest.raises(SchemaValidationError):
        validate_document(doc)
