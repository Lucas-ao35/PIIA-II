# Spec: extracción de entidades clínicas

## Propósito

Detectar menciones clínicas en textos en español y asignarles una categoría. La primera fase de implementación priorizará fármacos con PharmaCoNER. La especificación contempla ampliar el componente a enfermedades, síntomas/signos y procedimientos con DisTEMIST, SympTEMIST y MedProcNER, tras comprobar compatibilidad de etiquetas y datos. Los resultados alimentan la normalización y la salida JSON; FHIR es una representación posterior del subconjunto mapeable.


## Problema e intención

La información clínica aparece expresada de muchas formas en el texto libre. Detectar primero las menciones y distinguir su tipo reduce el problema a unidades que después pueden normalizarse y almacenarse. Esta separación permite evaluar el reconocimiento de entidades de forma independiente y evita mezclar los errores de extracción con los de codificación.


## Qué construir

Un componente que reciba un texto en español y devuelva una lista de menciones detectadas. Para cada mención incluirá, como mínimo:
- texto original de la mención
- categoría (`farmaco`, `enfermedad`, `sintoma` o `procedimiento`)
- índice de inicio y fin siguiendo una convención documentada
- identificador del documento de origen, cuando se procese un corpus anotado
- confianza del modelo, si el método utilizado la proporciona

La información contextual adicional, como negación o temporalidad, queda fuera de la primera versión salvo que el equipo la incorpore expresamente y disponga de datos adecuados para evaluarla. La extracción debe conservar el texto de entrada sin modificar para que los offsets puedan verificarse directamente.


## Restricciones y supuestos

- La entrada será texto en español procedente de corpus públicos permitidos o ejemplos sintéticos.
- Antes de usar un corpus, se documentará el mapeo de sus etiquetas a las cuatro categorías del proyecto.
- Los límites de cada mención deben corresponder al texto original, incluidos acentos y signos que formen parte de ella.
- No se procesarán historias clínicas reales ni se utilizarán los resultados para diagnosticar.
- El enfoque técnico está por decidir. Si se usa un modelo preentrenado, se registrarán su nombre, versión y licencia.


## Criterios de aceptación

1. Dado un texto válido, el componente devuelve una lista de entidades sin modificar el texto original.
2. Dado un texto no vacío, el componente devuelve entidades con `text`, `type`, `start` y `end`.
3. Para cada entidad, `text` coincide exactamente con `input[start:end]`.
4. Todos los valores de `type` pertenecen al conjunto `disease`, `symptom`, `drug`, `procedure`.
5. Ante una entrada vacía o formada solo por espacios, devuelve una lista vacía o un error de validación documentado; el comportamiento será consistente.
6. En el conjunto de prueba anotado, se informan precisión, recall y F1 por categoría y globales, con coincidencia exacta de límites y categoría. El objetivo inicial es F1 micro global ≥ 0,75; si el corpus no permite una comparación válida, se documentará y se propondrá una alternativa antes de evaluar.
7. La partición de prueba no se utiliza para entrenar ni seleccionar hiperparámetros.
8. La documentación identifica corpus, versión, mapeo de etiquetas y limitaciones conocidas.


## Fuera de alcance

- Inferir enfermedades no mencionadas explícitamente.
- Resolver completamente negación, temporalidad, antecedentes familiares o relaciones clínicas.
- Asignar códigos SNOMED CT o CIE-10-ES, tarea definida en `normalizacion-clinica.md`.