# ADR: Visualizador de corpus y resultados con Streamlit

## Estado

Aceptada

## Contexto

El proyecto necesita inspeccionar de forma continua un corpus anotado (PharmaCoNER) y los resultados del pipeline: leer casos clínicos con sus menciones resaltadas, verificar que los offsets y códigos cuadren con el texto y obtener estadísticas del corpus (distribución por categoría y partición, términos y códigos más frecuentes). También interesa disponer de una demostración local que procese texto sintético y permita inspeccionar la salida. El equipo es de perfil Python/pandas y el prototipo es académico, sin requisito de servicio en producción.

## Decisión

Implementar el visualizador como **aplicación Streamlit** (`app/app.py`). La aplicación incluye un explorador del corpus que consume el cargador BRAT, resalta menciones, muestra tablas e inspectores de entidades y estadísticas con Altair; además, dispone de una pestaña de demostración que invoca el pipeline para procesar texto sintético y presenta las predicciones y el JSON resultante. La interfaz no entrena ni modifica los recursos del pipeline: la inferencia de esa pestaña es una operación de demostración, separada de la exploración del corpus.

## Motivación

- **Ciclo corto de desarrollo**: la interfaz de exploración y demostración se implementa en Python sin frontend ni API independiente, lo que deja el tiempo del equipo para el pipeline, que es el núcleo evaluable del proyecto.
- **Alineado con el stack**: el equipo ya trabaja con pandas. Streamlit lo consume de forma nativa (tablas, `st.dataframe`, caché de carga) y Altair viene integrado para los gráficos.
- **Útil para la depuración cualitativa**: ver el texto con las menciones marcadas y el código al lado es la forma más rápida de detectar errores de offsets o de mapeo de etiquetas antes de ejecutar la evaluación cuantitativa.
- **Buen vehículo de demostración**: una interfaz navegable comunica el caso de uso mucho mejor que un notebook.

## Alternativas consideradas

- **Notebooks de Jupyter**: excelentes para análisis exploratorio puntual, pero el estado se degrada (celdas ejecutadas en desorden), no hay una vista compartida y estable para el tutor y las visualizaciones no se reutilizan fácilmente. Descartado como herramienta principal, se pueden usar para análisis sueltos.
- **Aplicación web propia (Flask/FastAPI + frontend)**: máximo control, pero obliga a mantener API, rutas y frontend para un prototipo local. Constituye un esfuerzo desproporcionado para el valor que aporta, motivo por el que se descarta.
- **Herramienta de BI (Grafana, Metabase, Power BI)**: es potente para métricas agregadas, pero requiere servir los datos en una base de datos o métricas, no maneja bien el caso central de "leer un documento con spans resaltados y offsets verificables" y añade infraestructura. Descartado.

## Consecuencias

- El resaltado de menciones se implementa insertando marcas HTML sobre el texto original por offsets. Hay que mantener el filtro de solapamientos (quedarse con la mención más larga) y escapar el HTML para no romper la vista.
- La carga del corpus se cachea (`st.cache_data`) para no reparsear los archivos BRAT en cada interacción.
- La aplicación no modifica ni reentrena el pipeline. La pestaña de demostración sí ejecuta inferencia sobre el texto introducido y muestra la salida; si cambia la interfaz del pipeline o el esquema JSON, esa integración deberá mantenerse actualizada.

## Alcance implementado y evolución prevista

**Implementado en la aplicación actual:** exploración de documentos BRAT, resaltado de anotaciones, estadísticas por categoría y partición, tablas e inspector de entidades, vista del JSON del caso y pestaña de demostración que ejecuta inferencia sobre texto sintético.

**Evolución prevista:** ampliar la inspección para consumir de forma homogénea resultados persistidos de cada etapa del pipeline, una vez estabilizados el contrato JSON y las salidas de evaluación. La visualización no sustituye al evaluador ni modifica los resultados.

## Referencias

- Documentación oficial de Streamlit: [docs.streamlit.io](https://docs.streamlit.io/)
- Caché de datos: [st.cache_data](https://docs.streamlit.io/develop/api-reference/caching/st.cache_data)
- Altair (gráficos declarativos sobre pandas): [altair-viz.github.io](https://altair-viz.github.io/)
- SNOMED CT Browser (enlace por código de concepto): [browser.ihtsdotools.org](https://browser.ihtsdotools.org/)


## Ejemplo de resaltado por offsets

Fragmento del patrón usado en `app/app.py` para resaltar de final a principio y no desplazar índices:

```python
chars = list(raw_text)
for ent in sorted(entities, key=lambda x: x["start"], reverse=True):
    s, e = ent["start"], ent["end"]
    chars[s:e] = [f"<mark class='ent-mark'>{html.escape(''.join(chars[s:e]))}</mark>"]
rendered = "".join(chars)
```
