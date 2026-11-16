# ADR: Uso de las particiones oficiales de PharmaCoNER para entrenamiento y evaluación

## Estado

Aceptada

## Contexto

El proyecto utiliza PharmaCoNER 1.1 como corpus inicial para desarrollar y evaluar la extracción de entidades y la normalización terminológica. El corpus proporciona particiones oficiales de entrenamiento (`train`), validación (`dev`) y prueba (`test`), por lo que es importante mantener una separación clara entre los datos utilizados para construir el sistema, los empleados durante su desarrollo y los reservados para medir su rendimiento final.

Esta separación ya estaba recogida en la primera entrega. En concreto, `specs/evaluacion-resultados.md` establecía que el conjunto de prueba debía utilizarse únicamente en la evaluación final y no para entrenar ni seleccionar hiperparámetros. También `specs/extraccion-entidades.md` indicaba que la partición de prueba no debía intervenir en el entrenamiento ni en la selección de configuraciones.

La implementación actual necesita respetar ese criterio tanto al construir el extractor NER como al crear el recurso de normalización, ya que ambos componentes aprenden de las anotaciones del corpus.

## Decisión

Respetar las particiones oficiales de PharmaCoNER y asignarles las siguientes funciones:

- **Train**: partición utilizada para construir los recursos aprendidos por el sistema durante el desarrollo, tanto el diccionario del extractor NER como la tabla de correspondencias del normalizador.
- **Dev**: partición utilizada para comprobar el comportamiento del sistema, comparar configuraciones y decidir los parámetros que se utilizarán en la versión final. Sus anotaciones no deben incorporarse al entrenamiento mientras se estén tomando decisiones de desarrollo.
- **Test**: partición reservada exclusivamente para la evaluación final. No se utilizará para construir diccionarios o recursos, ajustar umbrales, seleccionar configuraciones ni tomar decisiones de diseño.

Una vez fijada la configuración del sistema, se permite volver a entrenar los componentes con **train + dev** y realizar la evaluación final sobre **test**. De este modo se aprovechan los datos de desarrollo disponibles sin utilizar las anotaciones del conjunto de prueba.

Esta política se aplica a todas las etapas que aprenden de las anotaciones gold, no únicamente al extractor NER. Por tanto, también afecta al normalizador basado en las formas y códigos observados en el corpus.

## Motivación

- **Evaluación independiente**: mantener test separado permite estimar el rendimiento sobre documentos que no han intervenido en el desarrollo ni en la selección de parámetros.
- **Prevención de fuga de información**: utilizar anotaciones de test para construir diccionarios, elegir umbrales o modificar el sistema produciría una evaluación sesgada.
- **Aprovechamiento de dev**: la partición de validación permite comparar alternativas durante el desarrollo sin consumir el conjunto reservado para la evaluación final.
- **Coherencia con la primera entrega**: la decisión mantiene el criterio ya establecido en las especificaciones de evaluación y extracción, evitando cambiar el protocolo definido inicialmente.
- **Reproducibilidad**: registrar las particiones utilizadas en cada ejecución permite interpretar los resultados y repetir la evaluación con la misma configuración.

## Alternativas consideradas

- **Mezclar todas las particiones y realizar una división aleatoria propia**: permitiría crear conjuntos de entrenamiento y evaluación a medida, pero descartaría la separación oficial de PharmaCoNER y dificultaría la comparación con resultados obtenidos siguiendo su protocolo. Descartado.
- **Utilizar test durante el desarrollo para comparar configuraciones**: facilitaría observar el rendimiento de cada cambio, pero convertiría el conjunto de prueba en parte del proceso de selección y dejaría de proporcionar una estimación independiente. Descartado.
- **Entrenar y evaluar únicamente con train**: evitaría utilizar particiones adicionales, pero no proporcionaría una validación independiente ni una evaluación final representativa. Descartado.
- **No aprovechar dev en el entrenamiento final**: es una opción válida y mantiene el entrenamiento limitado a train, pero, una vez fijada la configuración, incorporar train y dev permite aprovechar más anotaciones sin comprometer test. No se adopta como estrategia final por defecto, aunque puede utilizarse en experimentos concretos si se documenta.

## Consecuencias

- El entrenamiento habitual durante el desarrollo utiliza únicamente `train`; las decisiones sobre configuraciones y parámetros se toman a partir de los resultados en `dev`.
- La evaluación final debe ejecutarse con `test` y con la configuración ya fijada. Si se realiza un reentrenamiento final con `train + dev`, debe quedar registrado en el informe.
- Los recursos del extractor NER y del normalizador deben construirse exclusivamente con las particiones indicadas como entrenamiento en cada ejecución.
- Los informes deben identificar tanto la partición evaluada como las particiones utilizadas para entrenar, de forma que se pueda comprobar que no existe solapamiento.
- El script `app/scripts/evaluate.py` implementa esta separación para las ejecuciones realizadas mediante la interfaz de línea de comandos: permite evaluar en `dev` o `test`, limita el entrenamiento a `train` y `dev` e impide que la partición evaluada forme parte del entrenamiento.
- La evaluación en `dev` puede repetirse durante el desarrollo. La evaluación sobre `test` debe reservarse para cuando la configuración esté cerrada.

## Referencias

- Especificación de evaluación del proyecto: [`specs/evaluacion-resultados.md`](../specs/evaluacion-resultados.md)
- Especificación de extracción de entidades: [`specs/extraccion-entidades.md`](../specs/extraccion-entidades.md)
- Dataset PharmaCoNER de PlanTL-GOB-ES: [Hugging Face](https://huggingface.co/datasets/PlanTL-GOB-ES/pharmaconer)
- Artículo del task PharmaCoNER: [ACL Anthology D19-5701](https://aclanthology.org/D19-5701/)
