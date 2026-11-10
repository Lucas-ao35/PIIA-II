# CU-03 — Código del pipeline de extracción clínica

Implementación del camino crítico descrito en `entregas/cu-03-extraccion-clinica/ARCHITECTURE.md`:

```
texto ─▶ cu03.corpus (BRAT) ─▶ cu03.ner ─▶ cu03.normalization ─▶ cu03.schema (JSON canónico) ─▶ cu03.evaluation
                                   ▲                                                            │
                                   └──────────────── app.py (Streamlit) ◀───────────────────────┘
```

## Puesta en marcha

```bash
uv sync --group dev                   # o: pip install -r requirements.txt
python scripts/download_datasets.py   # descarga PharmaCoNER en data/ (o descargar_datos.bat)
python -m pytest                      # 48 tests, sin necesidad del corpus (o ejecutar_tests.bat)
python scripts/evaluate.py            # entrena en train, evalúa en dev (o evaluar.bat)
streamlit run app.py                  # visualizador (o ejecutar_app.bat)
```

Procesar un texto:

```bash
python scripts/run_pipeline.py --text "Se pautó enoxaparina y omeprazol."
python scripts/evaluate.py --save-model models/baseline     # guarda el modelo
python scripts/run_pipeline.py --model models/baseline --file caso.txt --out caso.json
```

## Estructura

| Ruta | Componente (ARCHITECTURE.md) | Spec |
|---|---|---|
| `cu03/corpus.py` | Cargador BRAT, mapeo de etiquetas, reparación de offsets | — |
| `cu03/ner.py` | Extracción de entidades (baseline de diccionario) | `extraccion-entidades.md` |
| `cu03/normalization.py` | Normalización conservadora a SNOMED CT | `normalizacion-clinica.md` |
| `cu03/schema.py` | Contrato JSON 1.0 + validación semántica | `generacion-json.md` |
| `cu03/pipeline.py` | Orquestación texto → JSON validado | — |
| `cu03/evaluation.py` | Métricas estrictas e informe reproducible | `evaluacion-resultados.md` |
| `schemas/documento-1.0.schema.json` | JSON Schema publicado (Draft 2020-12) | `generacion-json.md` |
| `scripts/evaluate.py` | Orden única de evaluación | `evaluacion-resultados.md` |
| `app.py` | Visualizador: gold vs predicción, pipeline en vivo | — |
| `tests/` | Criterios de aceptación como tests | todas |

## Resultados actuales (dev, entrenado solo con train)

| Métrica | Valor | Objetivo spec |
|---|---|---|
| F1 micro estricto, etiquetas nativas | 0,763 (P 0,913 · R 0,655) | ≥ 0,75 |
| F1 micro estricto, `drug` | 0,769 (P 0,940 · R 0,650) | ≥ 0,75 |
| Normalización aislada: exactitud top-1 | 0,692 | ≥ 0,70 |
| Normalización aislada: exactitud sobre `matched` | 0,998 | — |
| JSON válidos contra el esquema | 100 % | 100 % |

Informe completo en `reports/eval-dev.md`. El cuello de botella es el recall: fármacos no vistos en train
(bendamustina, imatinib, dasatinib…). La normalización casi nunca se equivoca cuando asigna código, pero
solo cubre formas vistas.

## Reglas de trabajo

- **El test no se toca para ajustar.** Los parámetros (`--min-precision`, `--min-agreement`) se eligen en dev.
  La evaluación final es `python scripts/evaluate.py --split test --train-splits train dev`, una sola vez.
- **Mapeo de etiquetas** en `cu03/corpus.py::LABEL_TO_TYPE`: `NORMALIZABLES` y `NO_NORMALIZABLES` → `drug`;
  `PROTEINAS` y `UNCLEAR` se evalúan pero no se emiten (no existen en el esquema 1.0).
- **Licencia SNOMED CT**: `data/` y `models/` están en `.gitignore`. `coding.display` es la forma más
  frecuente en el corpus, no la descripción oficial de SNOMED CT.
- **Defecto del gold**: `S0211-69952015000200015-1` (train) tiene 5 offsets desplazados; el cargador los
  repara y lo registra.
