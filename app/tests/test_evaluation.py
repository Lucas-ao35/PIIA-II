"""specs/evaluacion-resultados.md — métricas estrictas y contenido del informe."""

from cu03.evaluation import evaluate, strict_ner_metrics, to_markdown


def test_metricas_estrictas():
    gold = {("d", 0, 5, "A"), ("d", 10, 15, "A"), ("d", 20, 25, "B")}
    pred = {("d", 0, 5, "A"), ("d", 10, 14, "A"), ("d", 20, 25, "A")}  # límite y etiqueta erróneos
    m = strict_ner_metrics(gold, pred)
    assert m["match"] == "strict"
    assert (m["micro"]["tp"], m["micro"]["fp"], m["micro"]["fn"]) == (1, 2, 2)
    assert m["per_label"]["B"]["recall"] == 0.0


def test_informe_completo(pipe, train_docs):
    r = evaluate(pipe, train_docs, "train-smoke", ["train"])
    assert r["extraction_native_labels"]["micro"]["f1"] == 1.0
    assert r["output_validity"]["rate"] == 1.0
    assert r["normalization"]["on_gold_mentions"]["status_counts"]["ambiguous"] == 2
    assert len(r["limitations"]) >= 3
    run = r["run"]
    for k in ("corpus", "corpus_version", "eval_split", "train_splits", "pipeline", "dependencies", "date"):
        assert k in run
    md = to_markdown(r)
    assert "coincidencia strict" in md and "Limitaciones" in md
