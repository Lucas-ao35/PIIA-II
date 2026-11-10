"""specs/extraccion-entidades.md — criterios 1 a 5."""

import pytest

from cu03.ner import GazetteerNER


def test_no_modifica_texto_y_offsets_exactos(pipe):
    text = "Pautamos OMEPRAZOL y enoxaparina; después, ácido acetilsalicílico."
    original = str(text)
    mentions = pipe.extract(text)
    assert text == original
    assert {m.text.lower() for m in mentions} == {"omeprazol", "enoxaparina", "ácido acetilsalicílico"}
    for m in mentions:
        assert text[m.start:m.end] == m.text and m.start < m.end


def test_coincidencia_mas_larga_y_sin_solapes(train_docs):
    ner = GazetteerNER().fit(train_docs)
    ms = ner.predict("Tomaba ácido acetilsalicílico a diario.")
    assert [m.text for m in ms] == ["ácido acetilsalicílico"]


def test_no_detecta_subcadenas_de_palabras(pipe):
    assert pipe.extract("La omeprazolemia no existe.") == []


@pytest.mark.parametrize("text", ["", "   ", "\n\t"])
def test_entrada_vacia_devuelve_lista_vacia(pipe, text):
    assert pipe.extract(text) == []


def test_filtro_de_precision(train_docs):
    # 'heparina' anotada 2 veces de 2 apariciones -> precisión 1.0, se conserva
    ner = GazetteerNER(min_precision=0.9).fit(train_docs)
    assert ("heparina",) in ner.entries


def test_persistencia(tmp_path, train_docs):
    ner = GazetteerNER().fit(train_docs)
    ner.save(tmp_path / "ner.json")
    text = "Se administró heparina y omeprazol."
    assert GazetteerNER.load(tmp_path / "ner.json").predict(text) == ner.predict(text)
