# Spec: ejecución local, configuración y dependencias

## Propósito

Garantizar que cualquier miembro del equipo o revisor pueda instalar, probar, evaluar y ejecutar el prototipo en local de forma reproducible, con las dependencias y versiones documentadas.

## Qué construir

- **Entorno**: Python ≥ 3.11, gestionado con `uv`. Las dependencias se declaran en `app/pyproject.toml` (`jsonschema`, `pandas`, `altair`, `streamlit` y `pytest` en el grupo `dev`), con `app/requirements.txt` como alternativa para `pip`.
- **Datos**: `app/scripts/download_datasets.py` descarga PharmaCoNER 1.1 en `app/data/`. Los directorios `data/` y `models/` no se versionan (`.gitignore`), por las condiciones de licencia de SNOMED CT.
- **Órdenes**, ejecutadas desde `app/`:

| Tarea | Orden |
|---|---|
| Instalar dependencias | `uv sync --group dev` |
| Ejecutar las pruebas | `uv run python -m pytest` |
| Descargar el corpus | `uv run python scripts/download_datasets.py` |
| Evaluar en dev | `uv run python scripts/evaluate.py` |
| Evaluación final en test | `uv run python scripts/evaluate.py --split test --train-splits train dev` |
| Procesar un texto | `uv run python scripts/run_pipeline.py --text "…"` |
| Abrir el visualizador | `uv run streamlit run app.py` |

- **Windows**: los archivos `.bat` de `app/` (`descargar_datos.bat`, `ejecutar_tests.bat`, `evaluar.bat`, `ejecutar_app.bat`) ejecutan las mismas órdenes.
- **Configuración**: los parámetros (`--min-precision`, `--min-agreement`, `--data-dir`, `--out`, `--save-model`) tienen valores por defecto en `scripts/evaluate.py`, y los valores usados quedan registrados en el informe.

## Restricciones y supuestos

- La ejecución es completamente local: no se envían textos ni resultados a servicios externos.
- Las pruebas no necesitan el corpus descargado: usan un mini-corpus sintético.
- No se requiere GPU ni modelos externos en la primera fase.

## Criterios de aceptación

1. En un entorno limpio con Python ≥ 3.11 y `uv`, `uv sync --group dev` instala las dependencias sin errores.
2. `uv run python -m pytest` se ejecuta sin el corpus descargado y todas las pruebas pasan.
3. Con el corpus descargado, `uv run python scripts/evaluate.py` genera `reports/eval-dev.json` y `reports/eval-dev.md`.
4. El informe de evaluación registra las versiones de las dependencias utilizadas.
5. `app/README.md` documenta todas las órdenes de la tabla anterior.

## Fuera de alcance

- Despliegue en servidor, contenedores o servicios en la nube.
- Soporte de versiones de Python anteriores a 3.11.