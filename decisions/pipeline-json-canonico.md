# ADR: Pipeline por etapas desacopladas con un JSON canónico como contrato

## Estado

Aceptada

## Contexto

El sistema debe encadenar varias transformaciones (extracción de menciones, normalización terminológica, generación de salida estructurada y conversión a FHIR) sobre textos clínicos, y cada una puede fallar de forma independiente: se puede detectar una mención y no encontrarle código, o generar un JSON válido a partir de entidades mal extraídas. Las specs exigen además poder evaluar cada etapa por separado con métricas distintas (F1 para extracción, exactitud y cobertura para normalización, validez de esquema para JSON y FHIR).

## Decisión

Estructurar el sistema como un **pipeline secuencial de componentes desacoplados**. Las etapas se conectan mediante interfaces Python y utilizan estructuras internas adecuadas a cada responsabilidad: el NER devuelve objetos `Mention`, el normalizador devuelve objetos `NormalizationResult` y el orquestador construye un diccionario Python con el documento completo. Al finalizar, ese documento se serializa como **JSON canónico versionado** y se valida contra el esquema publicado en `app/cu03/schema.py` (actualmente `schema_version: 1.0`). Por tanto, el JSON es la representación canónica de salida y el contrato para persistencia e interoperabilidad posterior; no es obligatorio serializar y volver a parsear JSON entre cada llamada interna. La conversión FHIR, cuando se implemente, consumirá el JSON validado.

## Motivación

- **Aislamiento de errores**: la separación de componentes permite distinguir un error de extracción de uno de normalización y evaluar cada etapa por separado.
- **Trazabilidad**: el JSON final conserva `source_text` y los offsets exactos, así que cualquier resultado puede verificarse contra el texto original.
- **Testabilidad**: cada componente se prueba mediante sus interfaces y estructuras de entrada/salida; además, el documento final se valida contra el JSON Schema.
- **Extensibilidad**: los componentes internos pueden evolucionar sin cambiar la representación persistente, siempre que el documento final siga respetando el esquema versionado.

## Alternativas consideradas

- **Script monolítico de texto a FHIR**: más rápido de escribir la primera semana, pero funde extracción, normalización y serialización en un solo bloque. Se descarta por ser imposible evaluar etapas por separado y que cualquier cambio de modelo obligue a rehacer el análisis completo.
- **Generar FHIR directamente desde el NER, sin JSON intermedio**: eliminaría una etapa, pero acoplaría la salida interoperable al detalle del modelo y violaría la spec de FHIR, que exige partir del subconjunto normalizado y documentar qué no se representa. Descartado.
- **Almacenar resultados en una base de datos (SQL/documental)** como representación principal: útil para volumen y consulta, pero el prototipo no lo necesita y añadiría una pieza de infraestructura que mantener. El JSON validado con esquema ya cubre el caso de uso. Aplazado (figura como fuera de alcance en las specs).

## Consecuencias

- Mantener el esquema JSON (nombres de campo, valores permitidos de `type` y `normalization_status`, convención `start` inclusivo / `end` exclusivo) es una obligación de compatibilidad dentro de cada `schema_version`.
- El validador de esquema debe estar versionado con el proyecto para que la evaluación sea reproducible. La implementación actual valida el documento final con `schema_version: 1.0`; la categoría `protein` y el estado `not_applicable` todavía no están admitidos por ese esquema.
- Las entidades sin código que pertenezcan al alcance de normalización deben conservarse con `coding` a `null` y estado explícito: ninguna etapa puede descartarlas silenciosamente.
- Las estructuras internas Python no sustituyen al contrato JSON publicado; son una decisión de implementación entre componentes.

## Referencias

- Especificación JSON Schema: [json-schema.org](https://json-schema.org/)
- Validación en Python: [python-jsonschema (readthedocs)](https://python-jsonschema.readthedocs.io/)


## Ejemplo de salida

Fragmento de una entidad del documento JSON final:

```json
{
  "schema_version": "1.1",
  "language": "es",
  "source_text": "Paciente en tratamiento con enoxaparina.",
  "entities": [
    {
      "text": "enoxaparina",
      "type": "drug",
      "start": 32,
      "end": 43,
      "coding": {"system": "SNOMED_CT", "code": "372744005", "display": "enoxaparina"},
      "normalization_status": "matched"
    }
  ]
}
```
