# Spec: generación de salida JSON estructurada

## Propósito

Transformar el texto de entrada y los resultados de extracción y normalización en un objeto JSON consistente, validable y reutilizable. JSON será la representación estructurada canónica de la primera versión y servirá como entrada para la conversión a FHIR.

## Problema e intención

Los resultados de PLN no son fáciles de almacenar ni analizar si cada ejecución los representa de forma distinta. Un esquema estable facilita pruebas, revisión, comparación de resultados y conversión a formatos interoperables.

## Qué construir

El componente recibirá el texto original, un identificador de documento opcional, las entidades extraídas y sus resultados de normalización. Producirá un objeto con esta estructura mínima:

```json
{
  "schema_version": "1.1",
  "document_id": "S0004-06142006000500002-3",
  "language": "es",
  "source_text": "Paciente tratado con omeprazol.",
  "entities": [
    {
      "text": "omeprazol",
      "type": "drug",
      "start": 21,
      "end": 30,
      "confidence": 0.97,
      "coding": {
        "system": "SNOMED_CT",
        "code": "387137007",
        "display": "omeprazol"
      },
      "normalization_status": "matched"
    }
  ]
}
```

El ejemplo es ilustrativo; en la ejecución real las posiciones y el fragmento deben corresponder al texto de entrada. La versión del esquema identifica el contrato de salida. La conservación de `source_text` se limita al prototipo con datos públicos o sintéticos.

### Campos

- `schema_version` (obligatorio): versión del contrato, `"1.1"`.
- `document_id` (opcional, cadena o `null`): para documentos del corpus, el nombre del archivo BRAT sin extensión; para otros textos, el valor indicado explícitamente por el usuario (p. ej. `--id`) o `null`. Nunca se construye a partir del contenido de `source_text`.
- `language` (obligatorio): `"es"`.
- `source_text` (obligatorio): texto de entrada sin modificar.
- `entities` (obligatorio): lista de entidades, posiblemente vacía.
- Por entidad: `text`, `type`, `start`, `end`, `coding` (`system`, `code`, `display`) y `normalization_status` son obligatorios. `confidence` es opcional: número en [0, 1], o `null` si el método no proporciona confianza.

### Valores permitidos

Fijamos el conjunto de valores válidos, que utilizaremos a lo largo del proyecto:

- `type`: `disease` · `symptom` · `drug` · `procedure` · `protein`
- `normalization_status`: `matched` · `not_found` · `ambiguous` · `not_applicable`

El tipo `protein` corresponde a la etiqueta `PROTEINAS` de PharmaCoNER y es independiente de `drug`. Las entidades `protein` no se normalizan: llevan `coding` a `null` y `normalization_status` = `not_applicable`. Estos valores se incorporan en la versión 1.1 del esquema, tal y como se indica en [`decisions/proteinas-categoria-propia.md`](../decisions/proteinas-categoria-propia.md).

## Restricciones y supuestos

- Los nombres de campo y los valores permitidos serán estables dentro de una versión del esquema.
- `start` es inclusivo y `end` exclusivo; ambos son índices de caracteres del texto original.
- La salida debe codificar correctamente Unicode, incluidos acentos y eñes.
- Una entidad sin código no debe perderse de la salida.
- Los errores de entrada deben comunicarse explícitamente; no se devolverá silenciosamente una salida parcial como si fuera válida.
  - **Entrada válida**: una cadena de texto (`str`) o una secuencia de bytes que se decodifica correctamente como UTF-8. Una cadena vacía o formada solo por espacios es válida y produce `entities: []`.
  - **Entrada inválida**: cualquier otro tipo de dato (`null`/`None`, números, listas, objetos) o bytes que no son UTF-8 válido.
  - **Tratamiento**: una entrada inválida lanza `InvalidInputError` con el código `CU03-E001` y un mensaje que indica el motivo. No se devuelve ningún JSON parcial. Desde la línea de comandos (`scripts/run_pipeline.py`), el error se escribe en la salida de error y el proceso termina con código de salida `2`.

- No se incluirán datos personales reales en las pruebas.
- JSON es la representación canónica; la salida FHIR se genera en una etapa posterior definida en `generacion-fhir.md`.

## Criterios de aceptación

1. Para una entrada válida, la salida se analiza con un parser JSON estándar sin errores.
2. Toda salida válida contiene `schema_version`, `language`, `source_text` y `entities`.
3. Cada entidad contiene `text`, `type`, `start`, `end`, `coding` y `normalization_status`. Si contiene `confidence`, su valor es `null` o un número en [0, 1].
4. Cada intervalo cumple `0 <= start < end <= longitud(source_text)` y `source_text[start:end]` coincide con `text`.
5. `type` y `normalization_status` solo admiten los valores definidos en la sección «Valores permitidos» de esta spec.
6. Si `normalization_status` es `not_found`, `ambiguous` o `not_applicable`, los tres campos de `coding` son `null`; si es `matched`, los tres están informados.
7. Una batería de al menos 10 pruebas, que incluya acentos, texto vacío, ninguna entidad, varias entidades y entidad sin código, valida el 100 % de las salidas válidas contra el esquema.
8. Cada uno de los casos de entrada inválida definidos (`None`, número, lista y bytes no UTF-8) lanza `InvalidInputError` con el código `CU03-E001`, sin devolver salida.
9. Las entidades aparecen en orden de inicio en el texto, ordenadas por `start` ascendente. El extractor no emite menciones solapadas, por lo que dos entidades no pueden compartir `start`. Si una ampliación permitiera solapamientos, a igual `start` se ordenarán por `end` ascendente.
10. Para un documento del corpus, `document_id` es igual al nombre del archivo sin extensión; para un texto sin identificador explícito, `document_id` es `null`. El valor de `document_id` nunca depende de `source_text`: procesar el mismo texto con identificadores distintos conserva cada identificador indicado, y procesarlo sin identificador produce `null`.

## Fuera de alcance

- Base de datos de producción.
- Intercambio directo con sistemas sanitarios.
- Garantía de interoperabilidad clínica sin validación posterior.