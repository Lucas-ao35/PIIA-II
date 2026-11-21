# Spec: extracción de entidades clínicas

## Propósito

Detectar menciones clínicas en textos en español y asignarles una categoría. La primera fase de implementación priorizará fármacos con PharmaCoNER. La especificación contempla ampliar el componente a enfermedades, síntomas/signos y procedimientos con DisTEMIST, SympTEMIST y MedProcNER, tras comprobar compatibilidad de etiquetas y datos. Los resultados alimentan la normalización y la salida JSON; FHIR es una representación posterior del subconjunto mapeable.


## Problema e intención

La información clínica aparece expresada de muchas formas en el texto libre. Detectar primero las menciones y distinguir su tipo reduce el problema a unidades que después pueden normalizarse y almacenarse. Esta separación permite evaluar el reconocimiento de entidades de forma independiente y evita mezclar los errores de extracción con los de codificación.


## Qué construir

Un componente que reciba un texto en español y devuelva una lista de menciones detectadas. Para cada mención incluirá, como mínimo:

- texto original de la mención
- categoría (`type`: `drug`, `disease`, `symptom`, `procedure` o `protein`, según los valores definidos en `generacion-json.md`)
- índice de inicio (`start`, inclusivo) y fin (`end`, exclusivo) en caracteres del texto original
- identificador del documento de origen (`document_id`), cuando se procese un corpus anotado: el nombre del archivo BRAT sin extensión, nunca un valor derivado del texto clínico
- confianza del modelo (`confidence`, número en [0, 1]) si el método la proporciona, si no, `null`. El extractor de diccionario de la primera fase sí la proporciona

La información contextual adicional, como negación o temporalidad, queda fuera de la primera versión salvo que el equipo la incorpore expresamente y disponga de datos adecuados para evaluarla. La extracción debe conservar el texto de entrada sin modificar para que los offsets puedan verificarse directamente.


## Restricciones y supuestos

- La entrada será texto en español procedente de corpus públicos permitidos o ejemplos sintéticos.
- Antes de usar un corpus, se documentará el mapeo de sus etiquetas a las categorías del proyecto.
    - El mapeo de PharmaCoNER está en [`decisions/proteinas-categoria-propia.md`](../decisions/proteinas-categoria-propia.md).
- Los límites de cada mención deben corresponder al texto original, incluidos acentos y signos que formen parte de ella.
- No se procesarán historias clínicas reales ni se utilizarán los resultados para diagnosticar.
- El enfoque técnico de la primera fase (diccionario y reglas) se documenta en [`decisions/ner-diccionario-reglas.md`](../decisions/ner-diccionario-reglas.md). La primera fase no usa ningún modelo preentrenado. Si una ampliación lo usa, se registrarán su nombre, versión (o revisión exacta) y licencia en el README de `app/` y en el bloque de configuración del informe de evaluación.

## Criterios de aceptación

1. Dado un texto válido, el componente devuelve una lista de entidades sin modificar el texto original.
2. Dado un texto no vacío, el componente devuelve entidades con `text`, `type`, `start` y `end`.
3. Para cada entidad, `text` coincide exactamente con `input[start:end]`.
4. Todos los valores de `type` pertenecen al conjunto definido en `generacion-json.md`, y ninguna mención con etiqueta de origen `PROTEINAS` recibe `type` = `drug`.
5. Ante una entrada vacía o formada solo por espacios, devuelve siempre una lista vacía.
6. Ante un texto sin ninguna mención detectable, devuelve una lista vacía y el documento se procesa sin error.
7. Cada entidad incluye `confidence` con un valor en [0, 1] cuando el método la proporciona, o `null` en caso contrario.
8. Al procesar un documento del corpus, todas sus entidades llevan asociado el `document_id` del documento, igual al nombre del archivo sin extensión.
9. El informe de evaluación sobre la partición de prueba incluye precisión, recall y F1 por categoría y micro globales, con coincidencia estricta de límites y categoría. El objetivo inicial es F1 micro global ≥ 0,75.
10. La partición de prueba no se utiliza para construir el diccionario ni para seleccionar parámetros (`min_precision`): las particiones de entrenamiento y evaluación registradas en el informe no se solapan.
11. Si se usa un modelo preentrenado, su nombre, versión y licencia figuran en el informe de evaluación; si no se usa, el informe identifica el método (diccionario y reglas).
12. La documentación identifica corpus, versión, mapeo de etiquetas y limitaciones conocidas (ver los ADRs de `decisions/`).


### Objetivo deseable (no condiciona la aceptación)

- F1 micro global ≥ 0,75 en la partición de prueba para `drug`. Si no se alcanza, el informe registra el valor obtenido y los errores principales. PharmaCoNER tiene partición de prueba oficial con anotación gold para las categorías evaluadas (`drug` y `protein`), por lo que la comparación es válida con este corpus.

## Fuera de alcance

- Inferir enfermedades no mencionadas explícitamente.
- Resolver completamente negación, temporalidad, antecedentes familiares o relaciones clínicas.
- Asignar códigos SNOMED CT o CIE-10-ES, tarea definida en `normalizacion-clinica.md`.