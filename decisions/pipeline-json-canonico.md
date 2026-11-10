# ADR: Pipeline por etapas desacopladas con un JSON canónico como contrato

## Estado

Aceptada

## Contexto

El sistema debe encadenar varias transformaciones (extracción de menciones, normalización terminológica, generación de salida estructurada y conversión a FHIR) sobre textos clínicos, y cada una puede fallar de forma independiente: se puede detectar una mención y no encontrarle código, o generar un JSON válido a partir de entidades mal extraídas. Las specs exigen además poder evaluar cada etapa por separado con métricas distintas (F1 para extracción, exactitud y cobertura para normalización, validez de esquema para JSON y FHIR).

## Decisión

Estructurar el sistema como un **pipeline secuencial de componentes desacoplados**, donde cada etapa recibe y produce **el JSON canónico versionado** definido en `specs/generacion-json.md` (`schema_version`, `language`, `source_text`, `entities` con `text`, `type`, `start`, `end`, `coding`, `normalization_status`). El JSON canónico es el único contrato de datos entre etapas: la normalización enriquece las entidades del JSON, la conversión FHIR consume el JSON ya normalizado, y la evaluación mide cada etapa contra ese mismo documento. Toda salida se valida contra un **JSON Schema** publicado junto al proyecto antes de pasar a la etapa siguiente.

## Motivación

- **Aislamiento de errores**: un error de normalización (código equivocado) no debe confundirse con uno de extracción (mención no detectada). Con etapas desacopladas que intercambian un documento común, cada métrica mide una cosa.
- **Trazabilidad**: el JSON conserva `source_text` y los offsets exactos, así que cualquier resultado puede verificarse contra el texto original sin re-ejecutar nada.
- **Testabilidad**: cada componente se prueba con entradas y salidas JSON, sin acoplarse a los internos de los demás, las baterías de pruebas exigidas por las specs se definen naturalmente sobre el contrato.
- **Extensibilidad**: la salida FHIR es una etapa más que consume el contrato, si cambia el modelo de NER o el normalizador, nada más se entera mientras respeten el esquema.

## Alternativas consideradas

- **Script monolítico de texto a FHIR**: más rápido de escribir la primera semana, pero funde extracción, normalización y serialización en un solo bloque, imposible evaluar etapas por separado y cualquier cambio de modelo obliga a rehacer el análisis completo. Descartado.
- **Generar FHIR directamente desde el NER, sin JSON intermedio**: eliminaría una etapa, pero acoplaría la salida interoperable al detalle del modelo y violaría la spec de FHIR, que exige partir del subconjunto normalizado y documentar qué no se representa. Descartado.
- **Almacenar resultados en una base de datos (SQL/documental)** como representación principal: útil para volumen y consulta, pero el prototipo no lo necesita y añadiría una pieza de infraestructura que mantener, el JSON validado con esquema cubre el caso de uso académico. Aplazado (figura como fuera de alcance en las specs).

## Consecuencias

- Mantener el esquema JSON (nombres de campo, valores permitidos de `type` y `normalization_status`, convención `start` inclusivo / `end` exclusivo) es una obligación de compatibilidad dentro de cada `schema_version`.
- El validador de esquema debe estar versionado con el proyecto para que la evaluación sea reproducible.
- Las entidades sin código circulan por todo el pipeline con `coding` a `null` y estado explícito: ninguna etapa puede descartarlas.

## Referencias

- Especificación JSON Schema: [json-schema.org](https://json-schema.org/)
- Validación en Python: [python-jsonschema (readthedocs)](https://python-jsonschema.readthedocs.io/)

Esquema de ejemplo (fragmento) de la entidad del contrato:

```json
{
  "schema_version": "1.0",
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
