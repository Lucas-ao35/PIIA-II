# Spec: generación de salida JSON estructurada

## Propósito

Transformar el texto de entrada y los resultados de extracción y normalización en un objeto JSON consistente, validable y reutilizable. JSON será la representación estructurada canónica de la primera versión y servirá como entrada para la conversión a FHIR.

## Problema e intención

Los resultados de PLN no son fáciles de almacenar ni analizar si cada ejecución los representa de forma distinta. Un esquema estable facilita pruebas, revisión, comparación de resultados y conversión a formatos interoperables.

## Qué construir

El componente recibirá el texto original, las entidades extraídas y sus resultados de normalización. Producirá un objeto con esta estructura mínima:

```json
{
  "schema_version": "1.0",
  "language": "es",
  "source_text": "Texto clínico de ejemplo.",
  "entities": [
    {
      "text": "ejemplo",
      "type": "disease",
      "start": 0,
      "end": 7,
      "coding": {
        "system": null,
        "code": null,
        "display": null
      },
      "normalization_status": "not_found"
    }
  ]
}
```

El ejemplo es ilustrativo; en la ejecución real las posiciones y el fragmento deben corresponder al texto de entrada. La versión del esquema identifica el contrato de salida. La conservación de `source_text` se limita al prototipo con datos públicos o sintéticos.

## Restricciones y supuestos

- Los nombres de campo y los valores permitidos serán estables dentro de una versión del esquema.
- `start` es inclusivo y `end` exclusivo; ambos son índices de caracteres del texto original.
- La salida debe codificar correctamente Unicode, incluidos acentos y eñes.
- Una entidad sin código no debe perderse de la salida.
- Los errores de entrada deben comunicarse explícitamente; no se devolverá silenciosamente una salida parcial como si fuera válida.
- No se incluirán datos personales reales en las pruebas.
- JSON es la representación canónica; la salida FHIR se genera en una etapa posterior definida en `generacion-fhir.md`.

## Criterios de aceptación

1. Para una entrada válida, la salida se analiza con un parser JSON estándar sin errores.
2. Toda salida válida contiene `schema_version`, `language`, `source_text` y `entities`.
3. Cada entidad contiene `text`, `type`, `start`, `end`, `coding` y `normalization_status`.
4. Cada intervalo cumple `0 <= start < end <= longitud(source_text)` y `source_text[start:end]` coincide con `text`.
5. `type` y `normalization_status` solo admiten los valores definidos en las specs relacionadas.
6. Si no existe código, los campos de código pueden ser `null` y el estado refleja que no se ha normalizado.
7. Una batería de al menos 10 pruebas, que incluya acentos, texto vacío, ninguna entidad, varias entidades y entidad sin código, valida el 100 % de las salidas válidas contra el esquema.
8. Una entrada inválida produce un error identificable y documentado.
9. Las entidades aparecen en orden de inicio en el texto; se documenta la política para entidades con el mismo inicio.

## Fuera de alcance

- Base de datos de producción.
- Intercambio directo con sistemas sanitarios.
- Garantía de interoperabilidad clínica sin validación posterior.
