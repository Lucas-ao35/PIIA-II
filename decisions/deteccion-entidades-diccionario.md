# ADR: Detección de entidades farmacológicas mediante diccionario y reglas

## Estado

Aceptada

## Contexto

La arquitectura dejaba pendiente fijar el enfoque técnico de la etapa de extracción de entidades (NER) tras inspeccionar los datos.

La primera fase del proyecto se limita a fármacos con PharmaCoNER 1.1. El camino crítico es **fármacos → detección → normalización → JSON → métricas**, y la normalización es la etapa de mayor riesgo, por lo que la extracción debía resolverse con un coste de desarrollo contenido para poder llegar pronto a un flujo completo y evaluable de punta a punta.

Al inspeccionar el corpus se observa que:

- Las menciones gold son, en su mayoría, nombres de principios activos, marcas comerciales y proteínas con formas superficiales relativamente estables y que se repiten entre documentos.
- Cada mención gold lleva asociado su código SNOMED CT, de modo que las mismas anotaciones de entrenamiento sirven para construir tanto el vocabulario de detección como la tabla de correspondencias del normalizador.
- El corpus ofrece particiones oficiales train / dev / test, lo que permite construir recursos solo con train (o train + dev en la configuración final) y medir en test sin fuga de información (ver [`estrategia-particiones-evaluacion.md`](estrategia-particiones-evaluacion.md)).

Además, el sistema debe conservar el texto de entrada sin modificar y garantizar que `texto[start:end] == text` para cada mención, tal y como se especifica en `specs/extraccion-entidades.md`, y la ejecución debe ser local y reproducible.

## Decisión

Implementar la detección de entidades farmacológicas con un sistema basado en diccionario y reglas (`app/cu03/ner.py`):

- **Diccionario**: lexicón de formas superficiales de menciones (términos y sus variantes) construido a partir de las anotaciones gold de las particiones de entrenamiento de cada ejecución (`train` durante el desarrollo; `train + dev` en la configuración final). La partición evaluada nunca contribuye al diccionario.
- **Reglas**: búsqueda de las entradas del diccionario sobre el texto original con reglas deterministas de coincidencia (respeto de límites de palabra, resolución de solapamientos a favor de la coincidencia más larga y tratamiento homogéneo de variantes de escritura cuando la regla correspondiente esté implementada), devolviendo `text`, `type`, `start`, `end` sobre el texto sin modificar y, cuando el método lo permite, una puntuación de confianza.
- **Categoría**: el tipo asignado se deriva de la etiqueta de origen de la entrada del diccionario, según el mapeo de etiquetas de PharmaCoNER a las categorías del proyecto previsto en [`corpus-pharmaconer-brat.md`](corpus-pharmaconer-brat.md).

El extractor respeta la interfaz de la etapa NER definida en la arquitectura: cualquier sustitución futura por otro método solo exige mantener el contrato JSON canónico ([`pipeline-json-canonico.md`](pipeline-json-canonico.md)).

## Motivación

- **Rapidez para cerrar el camino crítico**: un diccionario construido desde las anotaciones gold permite tener la extracción funcionando sin entrenamiento de modelos, liberando tiempo para la normalización, que es la etapa de mayor riesgo.
- **Ajuste a la naturaleza de los datos**: los nombres de fármacos tienen formas relativamente cerradas y repetidas, un escenario en el que el emparejamiento léxico ofrece una precisión alta.
- **Offsets exactos y trazabilidad**: la búsqueda directa sobre el texto original produce offsets de carácter verificables, sin realineamientos de subtokens. Cada detección puede explicarse por la entrada del diccionario y la regla que la generaron.
- **Determinismo y reproducibilidad**: con la misma configuración y las mismas particiones se obtiene siempre la misma salida, sin semillas, GPU ni versiones de pesos que registrar, lo que simplifica el informe exigido por `specs/evaluacion-resultados.md`.
- **Coherencia con la normalización**: el diccionario y la tabla de correspondencias del normalizador se construyen a partir de las mismas anotaciones y particiones, de forma que la política de separación de datos se aplica igual a ambas etapas.
- **Ejecución local ligera y sin dependencias de licencia de modelos**: no se requieren modelos externos ni servicios remotos, y no se envían textos clínicos a terceros.
- **Línea base de referencia**: proporciona un punto de comparación sencillo y explicable frente al que medir futuras alternativas basadas en aprendizaje automático.

## Alternativas consideradas

- **Modelo NER basado en aprendizaje automático (p. ej. transformer clínico en español ajustado a PharmaCoNER)**: existen modelos públicos de esta familia, como [`PlanTL-GOB-ES/bsc-bio-ehr-es-pharmaconer`](https://huggingface.co/PlanTL-GOB-ES/bsc-bio-ehr-es-pharmaconer) (RoBERTa clínico-biomédico). Generalizan mejor a formas no vistas y en principio superan el recall de un diccionario, pero exigen gestionar entrenamiento o inferencia con pesos externos, alineamiento de subtokens con offsets de carácter, registro de versión, licencia y semilla, y más recursos de cómputo. Además, los resultados declarados por un modelo de terceros no son directamente comparables con nuestro protocolo sin reevaluarlo con nuestras particiones y mapeo de etiquetas. No se adopta en la primera fase pero queda como posible alternativa a comparar con la línea base de diccionario.
- **Modelos de lenguaje generativos (LLM) con instrucciones o pocos ejemplos**: flexibles y sin necesidad de entrenamiento, pero no garantizan offsets exactos, pues la mención generada puede no coincidir literalmente con el texto. Son no deterministas, dificultan la reproducibilidad, pueden alucinar entidades y, si se usan como servicio remoto, implican enviar texto clínico a terceros, por lo que lo descartamos.
- **Reglas puramente morfológicas (sufijos farmacológicos como -cilina, -prazol, -olol) sin diccionario**: capturarían algunas formas no vistas, pero con muchos falsos positivos y sin cubrir marcas comerciales ni proteínas. Descartado como enfoque principal; puede considerarse como regla complementaria si se valida en dev.

## Consecuencias

- La extracción es determinista, explicable y ligera, y produce offsets exactos sobre el texto original por construcción, con una precisión esperable alta sobre las formas incluidas en el diccionario.

- El propio diccionario **limita la exhaustividad**, pues el sistema **solo reconoce los términos y variantes incluidos en el diccionario**. Un fármaco escrito de una forma no contemplada (otra grafía, abreviatura, errata, marca comercial no vista o fármaco ausente de entrenamiento) no se detecta. Tampoco se usa el contexto, lo que puede producir falsos positivos en formas polisémicas.

- Esta limitación fija un **techo de recall** igual a la **cobertura léxica del diccionario** sobre la partición evaluada: $\text{recall} \leq \frac{\#\{\text{menciones gold cuya forma está en el diccionario}\}}{\#\{\text{menciones gold}\}}$​. Ninguna mejora de las reglas lo supera, condiciona el objetivo de F1 ≥ 0,75 y las menciones perdidas tampoco llegan a la normalización.

- Surge la necesidad de reportar esa cobertura y separar los falsos negativos por *"forma fuera del diccionario"* y *"forma en el diccionario no detectada"*, sin usar test para modificar el diccionario.

- El diccionario se construye solo con las particiones de entrenamiento de cada ejecución, conforme a [`estrategia-particiones-evaluacion.md`](estrategia-particiones-evaluacion.md), y las reglas se fijan en dev. Si el recall en dev resulta insuficiente, se ampliará el diccionario o se incorporará un modelo NER aprendido.


## Referencias

- Especificación de extracción de entidades: [`specs/extraccion-entidades.md`](../specs/extraccion-entidades.md)
- Especificación de evaluación: [`specs/evaluacion-resultados.md`](../specs/evaluacion-resultados.md)
- Arquitectura, apartado NER: [`ARCHITECTURE.md`](../ARCHITECTURE.md#extracción-de-entidades-ner)
- Dataset PharmaCoNER de PlanTL-GOB-ES: [Hugging Face](https://huggingface.co/datasets/PlanTL-GOB-ES/pharmaconer)
- Artículo del task PharmaCoNER: [ACL Anthology D19-5701](https://aclanthology.org/D19-5701/)
- Modelo NER alternativo considerado: [PlanTL-GOB-ES/bsc-bio-ehr-es-pharmaconer](https://huggingface.co/PlanTL-GOB-ES/bsc-bio-ehr-es-pharmaconer)

##

Ejemplo de la limitación de exhaustividad:

```text
Diccionario:   {"enoxaparina", "omeprazol", "paracetamol"}

Texto:         "Se pautó enoxaparina y Clexane; previamente tomaba omeprazol y paracetamoll."
Detectadas:    enoxaparina, omeprazol
No detectadas: Clexane      (marca comercial no incluida en el diccionario)
               paracetamoll (errata: variante no contemplada)
```

Las dos menciones no detectadas son falsos negativos inevitables con este diccionario, independientemente de las reglas de coincidencia: reducen el recall y forman parte del techo de exhaustividad descrito arriba.
