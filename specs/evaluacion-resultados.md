# Spec: evaluación de extracción, normalización y salidas

## 1. Propósito

Definir un procedimiento reproducible para medir la calidad de la extracción y normalización y comprobar la validez técnica de las salidas JSON y FHIR.

## 2. Problema e intención

Una demostración con ejemplos elegidos manualmente no demuestra que el sistema generalice. Evaluar con datos anotados y validadores de formato permite detectar errores, comparar enfoques técnicos y justificar las limitaciones del prototipo.

## 3. Qué construir

Un procedimiento de evaluación que:
- seleccione un corpus público anotado en español y documente su versión, licencia y etiquetas;
- defina particiones de entrenamiento/desarrollo/prueba o utilice las particiones oficiales;
- mida extracción con precisión, recall y F1;
- mida normalización con exactitud top-1 y cobertura;
- valide el JSON contra su esquema;
- valide los recursos FHIR contra la versión y los perfiles declarados;
- genere un informe reproducible con configuración, resultados y limitaciones.

Para extracción, una predicción será correcta si coinciden exactamente el intervalo y la categoría con la anotación de referencia. Para normalización, será correcta si el código y el sistema coinciden con la referencia.

## 4. Restricciones y supuestos

- El conjunto de prueba permanecerá separado de los datos utilizados para entrenar, ajustar reglas o seleccionar modelos.
- Se documentará cualquier diferencia entre las etiquetas del corpus y las categorías del proyecto.
- No se combinarán puntuaciones de corpus incompatibles sin explicar las transformaciones.
- Se informarán las categorías con pocos ejemplos para obtener métricas estables.
- Los umbrales son objetivos iniciales, no resultados ya alcanzados.
- La evaluación FHIR medirá validez estructural y cumplimiento de las reglas declaradas; no demostrará validez clínica ni interoperabilidad en producción.

## 5. Criterios de aceptación

1. El informe identifica el corpus, versión, partición, mapeo de etiquetas, enfoque/modelo y versiones de dependencias relevantes.
2. El informe incluye precisión, recall y F1 globales y por categoría cuando haya ejemplos suficientes.
3. El F1 micro global de extracción en prueba es ≥ 0,75 como objetivo inicial; si no se alcanza, se reporta el valor observado y se describen los errores principales.
4. Para normalización se informa de exactitud top-1 y cobertura; objetivo inicial de exactitud ≥ 0,70 en el subconjunto evaluable, con resultados separados por terminología cuando haya datos suficientes.
5. Se informa del número de menciones evaluadas y de los falsos positivos y falsos negativos de extracción.
6. El conjunto de prueba no se usa para entrenar o seleccionar modelos; la partición queda documentada.
7. El 100 % de los casos JSON válidos de la batería supera la validación del esquema.
8. El 100 % de los recursos FHIR generados en la batería de prueba supera el validador estructural y las reglas declaradas.
9. El informe enumera al menos tres limitaciones observadas o esperables, como diferencias entre corpus, ambigüedad terminológica, variación lingüística o cobertura desigual.
10. Otra persona del equipo puede repetir la evaluación siguiendo las instrucciones documentadas y obtener las mismas métricas, salvo variaciones justificadas por aleatoriedad o entorno.

## 6. Fuera de alcance

- Demostrar validez clínica para uso asistencial.
- Afirmar que el rendimiento generaliza a historias clínicas reales por haber evaluado casos publicados.
- Comparar modelos con protocolos de evaluación incompatibles sin advertirlo.
