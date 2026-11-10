# ADR: Visualizador de corpus y resultados con Streamlit

## Estado

Aceptada

## Contexto

El proyecto necesita inspeccionar de forma continua un corpus anotado (PharmaCoNER) y, más adelante, los resultados del pipeline: leer casos clínicos con sus menciones resaltadas, verificar que los offsets y códigos cuadran con el texto, y obtener estadísticas del corpus (distribución por categoría y partición, términos y códigos más frecuentes). El equipo es de perfil Python/pandas y el prototipo es académico, con ejecución local y sin requisito de servicio en producción.

## Decisión

Implementar el visualizador como **aplicación Streamlit** (`app.py`) que consume directamente la salida del cargador BRAT: visor de casos con menciones resaltadas por categoría y enlazadas al SNOMED CT Browser, tabla e inspector de entidades, panel de estadísticas del corpus con Altair y vista del JSON canónico de cada documento. El visualizador es una capa de **solo lectura** sobre los datos: no forma parte del camino de procesamiento del pipeline.

## Motivación

- **Ciclo corto de desarrollo**: la aplicación completa (parser, resaltado por offsets, estadísticas, inspector JSON) cabe en un único script de Python sin frontend ni API que mantener, lo que deja el tiempo del equipo para el pipeline, que es el núcleo evaluable del proyecto.
- **Alineado con el stack**: el equipo ya trabaja con pandas, Streamlit lo consume de forma nativa (tablas, `st.dataframe`, caché de carga) y Altair viene integrado para los gráficos.
- **Útil para la depuración cualitativa**: ver el texto con las menciones marcadas y el código al lado es la forma más rápida de detectar errores de offsets o de mapeo de etiquetas antes de ejecutar la evaluación cuantitativa.
- **Buen vehículo de demostración**: para un proyecto académico con tutoría, una interfaz navegable comunica el caso de uso mucho mejor que un notebook.

## Alternativas consideradas

- **Notebooks de Jupyter**: excelentes para análisis exploratorio puntual, pero el estado se degrada (celdas ejecutadas en desorden), no hay una vista compartida y estable para el tutor, y las visualizaciones no se reutilizan fácilmente. Descartado como herramienta principal, se pueden usar para análisis sueltos.
- **Aplicación web propia (Flask/FastAPI + frontend)**: máximo control, pero obliga a mantener API, rutas y frontend para un prototipo local, esfuerzo desproporcionado para el valor que aporta. Descartado.
- **Herramienta de BI (Grafana, Metabase, Power BI)**: potente para métricas agregadas, pero requiere servir los datos en una base de datos o métricas, no maneja bien el caso central de "leer un documento con spans resaltados y offsets verificables", y añade infraestructura. Descartado.

## Consecuencias

- El resaltado de menciones se implementa insertando marcas HTML sobre el texto original por offsets, hay que mantener el filtro de solapamientos (quedarse con la mención más larga) y escapar el HTML para no romper la vista.
- La carga del corpus se cachea (`st.cache_data`) para no re-parsear los archivos BRAT en cada interacción.
- Al ser una capa de solo lectura, la evolución del pipeline no obliga a reescribir la app: basta con que las etapas nuevas respeten el contrato JSON canónico.

## Referencias

- Documentación oficial de Streamlit: [docs.streamlit.io](https://docs.streamlit.io/)
- Caché de datos: [st.cache_data](https://docs.streamlit.io/develop/api-reference/caching/st.cache_data)
- Altair (gráficos declarativos sobre pandas): [altair-viz.github.io](https://altair-viz.github.io/)
- SNOMED CT Browser (enlace por código de concepto): [browser.ihtsdotools.org](https://browser.ihtsdotools.org/)

Fragmento del patrón usado en `app.py` para resaltar por offsets (de final a principio para no desplazar índices):

```python
chars = list(raw_text)
for ent in sorted(entities, key=lambda x: x["start"], reverse=True):
    s, e = ent["start"], ent["end"]
    chars[s:e] = [f"<mark class='ent-mark'>{html.escape(''.join(chars[s:e]))}</mark>"]
rendered = "".join(chars)
```
