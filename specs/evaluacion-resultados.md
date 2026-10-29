# Spec: evaluación de extracción, normalización y salidas

## Propósito

Evaluar de forma reproducible el rendimiento del pipeline clínico en la extracción de entidades, su clasificación por tipo, la normalización a códigos clínicos y la generación de salidas estructuradas válidas en JSON y FHIR. La evaluación permitirá medir cada etapa de forma independiente mediante métricas adecuadas, identificar los principales errores y comprobar el cumplimiento de los objetivos iniciales. Los resultados servirán para comparar configuraciones, detectar limitaciones y orientar las mejoras del sistema, sin asumir que la validez estructural garantiza la validez clínica.

## Problema e intención

Nuestro pipeline clínico puede detectar muchas menciones y, sin embargo, asociarlas mal a códigos, medir cada etapa evita ocultar errores detrás de una única cifra y permite decidir si una mejora afecta a la extracción, a la normalización o solo al formato de salida.

## Qué construir

Se construirá un procedimiento de evaluación reproducible que ejecute el pipeline sobre las particiones del corpus y genere un informe. La evaluación cubrirá:

1. La estracción de entidades
2. La clasificación por tipo
3. La normallización
4. La validez de la salida estructurada

Para extracción se calcularán precisión, exhaustividad (recall) y F1-score, indicando si la coincidencia es estricta o parcial. Las métricas se mostrarán globalmente y por categoría. Para la normalización se informará también la exactitud de código entre las entidades correctamente extraídas y aquellas con referencia disponible.

El informe incluirá la configuración utilizada: corpus y versión, partición, modelo, parámetros, semilla aleatoria, fecha de ejecución y número de ejemplos.

## Restricciones y supuestos

- El conjunto de prueba sólo se usará en la evaluación final.
- Las métricas se calcularán con una herramienta o implementación versionada y documentada.
- Se documentará cualquier diferencia entre las etiquetas del corpus y las categorías del proyecto.
- No se combinarán puntuaciones de corpus incompatibles sin explicar las transformaciones.
- Los casos sin entidades deberán incluirse en el cálculo de errores de documento y no eliminarse silenciosamente.
- Se informarán las categorías con pocos ejemplos para obtener métricas estables.
- Los umbrales son objetivos de la primera iteración, no una garantía de rendimiento.
- La evaluación FHIR medirá validez estructural y cumplimiento de las reglas declaradas; no demostrará validez clínica ni interoperabilidad en producción.

## Criterios de aceptación

1. Una única orden o procedimiento documentado ejecuta la evaluación sobre la partición seleccionada y genera un informe reproducible.
2. El informe identifica el corpus, versión, partición, mapeo de etiquetas, enfoque/modelo y versiones de dependencias relevantes.
3. El informe incluye precisión, recall y F1 globales y por categoría evaluada.
4. El informe indica explícitamente si la coincidencia usada para cada métrica es estricta o parcial.
5. El informe enumera al menos, y en caso de producirse, tres limitaciones observadas o esperables, como diferencias entre corpus, ambigüedad terminológica, variación lingüística o cobertura desigual.
6. El F1 micro global de extracción en prueba es ≥ 0,75 como objetivo inicial; si no se alcanza, se reporta el valor observado y se describen los errores principales.
7. Para normalización se informa de exactitud top-1 y cobertura; objetivo inicial de exactitud ≥ 0,70 en el subconjunto evaluable, con resultados separados por terminología cuando haya datos suficientes.
8. El 100 % de los casos JSON válidos de la batería supera la validación del esquema.
9. El 100 % de los recursos FHIR generados en la batería de prueba supera el validador estructural y las reglas declaradas.

## Fuera de alcance

- Demostrar validez clínica para uso asistencial.
- Afirmar que el rendimiento generaliza a historias clínicas reales por haber evaluado casos publicados.
- Comparar modelos con protocolos de evaluación incompatibles sin advertirlo.
