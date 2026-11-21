# Spec: evaluación de extracción, normalización y salidas

## Propósito

Evaluar de forma reproducible el rendimiento del pipeline clínico en la extracción de entidades, su clasificación por tipo, la normalización a códigos clínicos y la generación de salidas estructuradas válidas en JSON y FHIR. La evaluación permitirá medir cada etapa de forma independiente mediante métricas adecuadas, identificar los principales errores y comprobar el cumplimiento de los objetivos iniciales. Los resultados servirán para comparar configuraciones, detectar limitaciones y orientar las mejoras del sistema, sin asumir que la validez estructural garantiza la validez clínica.

## Problema e intención

Nuestro pipeline clínico puede detectar muchas menciones y, sin embargo, asociarlas mal a códigos, medir cada etapa evita ocultar errores detrás de una única cifra y permite decidir si una mejora afecta a la extracción, a la normalización o solo al formato de salida.

## Qué construir

Se construirá un procedimiento de evaluación reproducible que ejecute el pipeline sobre las particiones del corpus y genere un informe. La evaluación cubrirá:

1. La extracción de entidades
2. La clasificación por tipo
3. La normalización
4. La validez de la salida estructurada

Para extracción se calcularán precisión, exhaustividad (recall) y F1-score con coincidencia estricta (límites y categoría exactos). Las métricas se mostrarán globalmente (micro) y por categoría, tanto con las etiquetas nativas del corpus como con los tipos del proyecto (`drug`, `protein`).

Para la normalización se informará también la exactitud top-1 de código entre las entidades correctamente extraídas y aquellas con referencia disponible.

El informe incluirá la configuración utilizada: corpus y versión, partición evaluada, modelo, parámetros, semilla aleatoria (o "no aplica" si el método es determinista), fecha de ejecución número de documentos y número de menciones gold por categoría.

## Restricciones y supuestos

- El conjunto de prueba sólo se usará en la evaluación final.
- Las métricas se calcularán con la implementación versionada del proyecto (`app/cu03/evaluation.py`), cubierta por pruebas.
- El mapeo entre las etiquetas del corpus y las categorías del proyecto es el de [`decisions/proteinas-categoria-propia.md`](../decisions/proteinas-categoria-propia.md).
- La categoría `protein` se evalúa en extracción por separado de `drug`, pero se excluye de las métricas de normalización (exactitud top-1 y cobertura), que se calculan solo sobre `drug`.
- No se combinarán puntuaciones de corpus incompatibles sin explicar las transformaciones.
- Los umbrales son objetivos de la primera iteración, no una garantía de rendimiento.
- La evaluación FHIR medirá validez estructural y cumplimiento de las reglas declaradas; no demostrará validez clínica ni interoperabilidad en producción.

## Criterios de aceptación

### Compromisos verificables

1. Una única orden documentada (`python scripts/evaluate.py --split <dev|test>`) ejecuta la evaluación sobre la partición seleccionada y genera `reports/eval-<partición>.json` y `reports/eval-<partición>.md`.
2. Con la misma configuración y los mismos datos, dos ejecuciones producen las mismas métricas.
3. El informe contiene todos los campos de configuración enumerados en «Qué construir».
4. El informe incluye precisión, recall y F1 micro globales y por categoría evaluada, con etiquetas nativas y con tipos del proyecto.
5. El informe indica explícitamente el tipo de coincidencia de cada métrica (estricta).
6. Todos los documentos de la partición evaluada se incluyen en el cálculo, también los que no tienen ninguna entidad gold: las predicciones en esos documentos cuentan como falsos positivos. El informe muestra el número de documentos evaluados y cuántos no tienen entidades gold.
7. Las categorías con menos de 50 menciones gold en la partición evaluada se marcan en el informe como *"pocos ejemplos"*.
8. El informe incluye una sección «Limitaciones» con al menos tres limitaciones observadas o esperables, como diferencias entre corpus, ambigüedad terminológica, variación lingüística o cobertura del diccionario.
9. Para normalización, el informe incluye exactitud top-1 y cobertura, solo sobre `drug` y solo con SNOMED CT (la primera fase no evalúa CIE-10-ES).
10. La ejecución rechaza que la partición evaluada figure entre las de entrenamiento.
11. El 100 % de los casos JSON válidos de la batería de pruebas supera la validación del esquema.
12. Solo si se implementa la ampliación FHIR: el 100 % de los recursos generados en su batería de pruebas supera la validación estructural definida en `specs/generacion-fhir.md`. Si no se implementa, el informe lo indica y este criterio no aplica. Su ausencia no impide considerar completado el núcleo funcional del proyecto, siempre que se cumplan los criterios relativos a extracción, normalización, generación JSON y evaluación.

### Objetivos deseables (no condicionan la aceptación)

- F1 micro global de extracción de `drug` ≥ 0,75 en la partición de prueba. Si no se alcanza, el informe registra el valor obtenido y describe los errores principales.
- Exactitud top-1 de normalización aislada ≥ 0,70 en el subconjunto evaluable. Si no se alcanza, el informe registra el valor obtenido y describe los errores principales.


## Fuera de alcance

- Demostrar validez clínica para uso asistencial.
- Afirmar que el rendimiento generaliza a historias clínicas reales por haber evaluado casos publicados.
- Comparar modelos con protocolos de evaluación incompatibles sin advertirlo.