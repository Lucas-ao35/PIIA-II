# ADR: Tratamiento de las etiquetas `NO_NORMALIZABLES` y `UNCLEAR` de PharmaCoNER

## Estado

Aceptada

## Contexto

PharmaCoNER 1.1 distingue cuatro etiquetas para las menciones de fármacos y sustancias:

- `NORMALIZABLES`: menciones con un código de normalización asociado en el corpus.
- `NO_NORMALIZABLES`: menciones de fármacos o sustancias sin código asociado en la anotación.
- `PROTEINAS`: proteínas y genes, tratados como una categoría independiente mediante el ADR [Proteínas como categoría propia](proteinas-categoria-propia.md).
- `UNCLEAR`: menciones dudosas o heterogéneas que no se pueden asignar de forma fiable a las categorías anteriores.

Es necesario definir explícitamente qué ocurre con `NO_NORMALIZABLES` y `UNCLEAR` durante la extracción, la normalización y la generación del JSON canónico. En particular, no se deben confundir la etiqueta original del corpus y el resultado que obtiene el normalizador: que una mención esté anotada como `NO_NORMALIZABLES` significa que no tiene código de referencia en esa anotación, pero no implica por sí solo que el sistema deba omitirla ni que se haya ejecutado una búsqueda sin éxito.

## Decisión

Se adopta el siguiente tratamiento:

| Etiqueta PharmaCoNER | Tratamiento en extracción | Tipo JSON | Normalización |
|---|---|---|---|
| `NORMALIZABLES` | Se extrae | `drug` | Se intenta |
| `NO_NORMALIZABLES` | Se extrae | `drug` | Se intenta; el resultado depende del normalizador |
| `PROTEINAS` | Se extrae | `protein` | No se intenta; `not_applicable` |
| `UNCLEAR` | Se excluye del conjunto de entidades objetivo | No se emite | No se intenta |

### Tratamiento de `NO_NORMALIZABLES`

Las menciones `NO_NORMALIZABLES` se consideran menciones de tipo `drug`, igual que las `NORMALIZABLES`. Por tanto:

- Se mantienen como entidades objetivo de la extracción.
- Se pasan al proceso de normalización.
- El resultado de la normalización se expresa mediante el estado correspondiente: `matched`, `not_found` o `ambiguous`.
- La ausencia de un código en la anotación de PharmaCoNER no debe convertirse automáticamente en una decisión del normalizador. El estado final debe reflejar el resultado real del proceso de normalización.

En la evaluación frente al corpus, estas menciones deben identificarse como casos sin código de referencia, para no atribuirles una correspondencia SNOMED CT de referencia que el dataset no proporciona.

### Tratamiento de `UNCLEAR`

Las menciones `UNCLEAR` quedan fuera del alcance del sistema:

- No se consideran una categoría de entidad del proyecto.
- No se incluyen como objetivos positivos de extracción ni se utilizan para construir recursos de normalización.
- No se normalizan.
- No se emiten en el JSON canónico ni se convierten a FHIR.
- Deben excluirse de las métricas de las categorías objetivo, de acuerdo con el protocolo de evaluación documentado.

La exclusión debe aplicarse de forma coherente en la preparación de los datos, el entrenamiento y la evaluación. No se debe transformar una mención `UNCLEAR` en `drug` por defecto.

## Motivación

- **Separación entre anotación y resultado:** la etiqueta del corpus describe la anotación de referencia; el estado de normalización describe lo que ha conseguido el sistema.
- **Conservación de menciones farmacológicas:** las menciones `NO_NORMALIZABLES` siguen siendo fármacos o sustancias relevantes para la extracción, aunque no tengan código de referencia en el corpus.
- **Evitar resultados artificiales:** asignar automáticamente `not_found` a todas las menciones `NO_NORMALIZABLES` confundiría la ausencia de código de referencia con el resultado de una búsqueda.
- **Control del alcance:** `UNCLEAR` agrupa casos heterogéneos y dudosos; forzar su clasificación introduciría ruido en la extracción y en las métricas.
- **Coherencia del JSON:** solo se emiten entidades pertenecientes a las categorías admitidas por el esquema del proyecto.

## Alternativas consideradas

- **Excluir también `NO_NORMALIZABLES`:** descartada porque son menciones farmacológicas válidas para la tarea de extracción.
- **Asignar siempre `not_found` a `NO_NORMALIZABLES`:** descartada porque ese estado debe representar el resultado de una normalización realmente ejecutada.
- **Clasificar `UNCLEAR` como `drug`:** descartada porque su contenido es heterogéneo y no permite asumir esa categoría.
- **Crear una categoría JSON `unclear`:** descartada porque supondría incorporar al alcance del proyecto casos que se han decidido excluir.

## Consecuencias

- El mapeo de etiquetas debe conservar `NO_NORMALIZABLES` como `drug` y excluir `UNCLEAR` de las entidades objetivo.
- El pipeline debe evitar que las menciones `UNCLEAR` lleguen al normalizador o a la salida JSON.
- La evaluación de extracción y normalización debe documentar cómo se tratan las menciones `NO_NORMALIZABLES`, que carecen de código de referencia en el corpus, y excluir `UNCLEAR` de las métricas de las categorías objetivo.
- La implementación debe mantener la distinción entre `not_found` (se intentó normalizar y no se encontró correspondencia) y `not_applicable` (la normalización no corresponde a esa entidad, como ocurre con `protein`).

## Referencias

- [ADR: Proteínas como categoría propia](proteinas-categoria-propia.md)
- [ADR: Corpus PharmaCoNER en formato BRAT](corpus-pharmaconer-brat.md)
- [Especificación de generación del JSON](../specs/generacion-json.md)
- [Especificación de normalización clínica](../specs/normalizacion-clinica.md)
- [Especificación de evaluación de resultados](../specs/evaluacion-resultados.md)
- [Dataset PharmaCoNER de PlanTL-GOB-ES](https://huggingface.co/datasets/PlanTL-GOB-ES/pharmaconer)
