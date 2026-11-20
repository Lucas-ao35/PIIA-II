# ADR: Proteínas como categoría propia (`protein`) fuera de la normalización y de FHIR

## Estado

Aceptada

## Contexto

PharmaCoNER 1.1 anota cuatro clases distintas de menciones:

- `NORMALIZABLES`: fármacos y sustancias con código SNOMED CT.
- `NO_NORMALIZABLES`: fármacos y sustancias sin código (muy pocos casos: 24 en train y 10 en test).
- `PROTEINAS`: proteínas y genes (1.405 menciones en train y 816 en test, más de un tercio de las menciones de cada partición).
- `UNCLEAR`: grupo heterogéneo de casos dudosos (vacunas, esquemas de quimioterapia, formulaciones…).

Las proteínas y los genes no son fármacos, son entidades biológicamente distintas que, en este corpus, aparecen sobre todo como analitos de laboratorio (hemoglobina, LDH, PSA, albúmina, PCR, inmunoglobulinas…). El ADR [`corpus-pharmaconer-brat.md`](corpus-pharmaconer-brat.md) exige documentar el mapeo de estas etiquetas a las categorías del proyecto, pero la lista oficial de `type` de [`specs/generacion-json.md`](../specs/generacion-json.md) solo admite `disease`, `symptom`, `drug` y `procedure`. Esto crea un gran problema, y es que no existe ninguna categoría válida para las proteínas, con el riesgo de que acaben clasificadas como `drug`, o de que se detecten sin mostrarse ni contabilizarse de forma coherente.

La tutora indicó que lo imprescindible es no mapear nunca una proteína a `drug`, y planteó dos opciones: dejar las proteínas fuera de alcance (opción A) o darles un tipo propio, detectándolas y mostrándolas pero manteniéndolas fuera de la normalización y de FHIR (opción B).

## Decisión

Adoptar la **opción B**: incorporar `protein` como categoría independiente de `drug`, con el siguiente mapeo de etiquetas de PharmaCoNER:

| Etiqueta PharmaCoNER | `type` | Normalización SNOMED CT | FHIR |
|---|---|---|---|
| `NORMALIZABLES` | `drug` | Sí | Sí, cuando el texto lo justifique |
| `NO_NORMALIZABLES` | `drug` | Sí (normalmente `not_found`) | Sí, cuando el texto lo justifique |
| `PROTEINAS` | `protein` | No: `normalization_status` = `not_applicable` | No |
| `UNCLEAR` | (no se emite) | No | No |

Las proteínas se detectan, se emiten en el JSON canónico y se muestran en el visualizador como entidades diferenciadas. Nunca se clasifican como `drug`. No pasan por el normalizador: salen con `coding` a `null` y el nuevo estado `not_applicable`, que indica que no se ha intentado normalizar, a diferencia de `not_found`, que indica que se intentó sin encontrar correspondencia. Tampoco se convierten a recursos FHIR. `UNCLEAR` sigue fuera de alcance, por su heterogeneidad.

Como cambian los valores permitidos de `type` y `normalization_status`, el esquema JSON pasa a la versión `1.1`.

## Motivación

- **Corrección conceptual**: una proteína no es un fármaco. Mezclarlas en `drug` falsearía tanto la salida como las métricas de la categoría principal del proyecto.
- **Aprovechamiento del corpus**: las proteínas suponen una parte muy importante de las menciones y el extractor las detecta con buen rendimiento. Descartarlas desaprovecharía material anotado.
- **Carril separado**: con un tipo propio, las proteínas se miden en extracción por categoría sin alterar las métricas de `drug`, ni de extracción ni de normalización.
- **Alcance de la normalización**: el camino crítico es la normalización de fármacos. Aunque la copia local del corpus asigna código SNOMED CT a la mayoría de las proteínas (1.291 de 1.405 en train), son sobre todo conceptos de analitos de laboratorio. Incluirlos mezclaría dos problemas distintos y alteraría la exactitud y la cobertura de la normalización farmacológica.
- **FHIR**: una mención de proteína no corresponde a un `MedicationStatement` ni a una `Condition`. Su representación natural (p. ej. `Observation`) exigiría valores y contexto que el prototipo no extrae.
- El **estado explícito** `not_applicable` evita que una proteína aparezca como `not_found`, que significaría que se buscó un código sin encontrarlo cuando en realidad no se intentó.

## Alternativas consideradas

- **Mantener las proteínas en `drug`**: es el error que se quiere corregir. Descartado.
- **Opción A, dejar las proteínas fuera de alcance**: es la más sencilla y mantiene el foco en lo clínico, pero desaprovecha una parte importante del corpus y las deja fuera del visualizador y de la evaluación. Descartado.
- **Normalizar también las proteínas con los códigos del corpus**: es técnicamente posible, pero amplía el camino crítico a un dominio distinto (analitos) y mezclaría sus resultados con los de fármacos. Aplazado como posible ampliación con métricas separadas.
- **Emitir las proteínas con `not_found`**: no exige ningún estado nuevo, pero confunde *"sin correspondencia"* con *"fuera de la normalización"* y las metería en los recuentos de cobertura. Descartado.

## Consecuencias

- La lista oficial de `type` en `specs/generacion-json.md` pasa a ser `disease` · `symptom` · `drug` · `procedure` · `protein`, y la de `normalization_status` añade `not_applicable`. El esquema pasa a `schema_version` `1.1`, y el JSON Schema publicado y su validador deben actualizarse en consecuencia.
- El ejemplo de [`normalizacion-conservadora.md`](normalizacion-conservadora.md) usa ahora `protein` con estado `not_applicable`, con las mismas categorías y denominaciones que la spec JSON.
- El mapeo de etiquetas del código (`LABEL_TO_TYPE`) debe enviar `PROTEINAS` a `protein`, el normalizador debe omitir esas entidades y el visualizador debe mostrarlas como categoría propia.
- La evaluación de extracción informa `protein` por separado de `drug`. Las métricas de normalización (exactitud top-1 y cobertura) se calculan solo sobre `drug`, y las tablas de correspondencias del normalizador no se construyen con anotaciones `PROTEINAS`.
- El conversor FHIR ignora las entidades `protein` y las registra como tipo no mapeado, según su política documentada.

## Referencias

- Especificación JSON: [`specs/generacion-json.md`](../specs/generacion-json.md)
- Especificación de normalización: [`specs/normalizacion-clinica.md`](../specs/normalizacion-clinica.md)
- Especificación FHIR: [`specs/generacion-fhir.md`](../specs/generacion-fhir.md)
- Especificación de evaluación: [`specs/evaluacion-resultados.md`](../specs/evaluacion-resultados.md)
- Dataset PharmaCoNER de PlanTL-GOB-ES: [Hugging Face](https://huggingface.co/datasets/PlanTL-GOB-ES/pharmaconer)
- Artículo del task PharmaCoNER: [ACL Anthology D19-5701](https://aclanthology.org/D19-5701/)

##

Ejemplo de un texto con un fármaco y una proteína en el JSON canónico 1.1:

```json
{
  "schema_version": "1.1",
  "language": "es",
  "source_text": "Omeprazol y PSA elevado.",
  "entities": [
    {"text": "Omeprazol", "type": "drug", "start": 0, "end": 9,
     "coding": {"system": "SNOMED_CT", "code": "387137007", "display": "omeprazol"},
     "normalization_status": "matched"},

    {"text": "PSA", "type": "protein", "start": 12, "end": 15,
     "coding": {"system": null, "code": null, "display": null},
     "normalization_status": "not_applicable"}
  ]
}
```
