# ADR: Normalización conservadora con estados explícitos

## Estado

Aceptada

## Contexto

La normalización asocia cada mención detectada a un código de SNOMED CT o CIE-10-ES. Es la etapa de mayor riesgo del proyecto: la terminología clínica es ambigua, los sinónimos abundan y un código incorrecto es peor que ninguno, porque un consumidor posterior (investigador, sistema de información) lo trataría como dato fiable. Además, SNOMED CT tiene restricciones de licencia que condicionan qué se puede publicar en un repositorio abierto.

## Decisión

Adoptar una **política de normalización conservadora con estados explícitos** para las entidades que entran en el alcance de normalización: `matched` (la forma superficial coincide con un código dominante), `not_found` (no existe una forma en el recurso de referencia) y `ambiguous` (hay varios códigos observados y ninguno alcanza el acuerdo mínimo). La implementación actual no usa similitud textual difusa: normaliza la forma a minúsculas y tokens y busca una coincidencia exacta. Si hay varios códigos para la misma forma, asigna el más frecuente solo cuando su proporción sobre el total de observaciones alcanza `min_agreement` (por defecto `0.8`); en caso contrario devuelve `ambiguous`. Ninguna entidad dentro del alcance sin código se elimina de la salida, y `not_found` y `ambiguous` se contabilizan por separado.

Las entidades `protein` quedan fuera de esta política: no se normalizan y deben emitirse con `coding` a `null` y estado `not_applicable`, conforme a [`proteinas-categoria-propia.md`](proteinas-categoria-propia.md). **Esta es la decisión de diseño, no el comportamiento completo del código actual**: `Pipeline.normalize()` todavía envía todas las menciones al normalizador y el esquema 1.0 no admite `protein` ni `not_applicable`. La integración requiere actualizar el pipeline y el esquema en una tarea de implementación posterior.

## Motivación

- **Honestidad del resultado**: el sistema distingue siempre entre "detecté una mención", "propuse este código" y "no pude normalizarla". Presentar solo códigos ocultaría la cobertura real del prototipo.
- **Evaluabilidad**: con los estados explícitos, la métrica de exactitud de códigos se calcula solo sobre el subconjunto evaluable (entidades con referencia gold y mapeo inequívoco), y la cobertura se informa aparte, tal como exige `specs/evaluacion-resultados.md`.
- **Criterio de aceptación reproducible**: `matched` no significa que se haya superado una similitud textual genérica; significa que la forma exacta tiene un código dominante cuya cuota es igual o superior a `min_agreement`. Este umbral controla el acuerdo entre anotaciones del corpus para una misma forma.
- **Seguridad**: un prototipo académico que no inventa datos es más prudente para su propósito (investigación y análisis secundario) y respeta el principio del proyecto de no sustituir criterio profesional.
- **Licencias**: no publicar descripciones ni fragmentos de SNOMED CT hasta confirmar condiciones, el diseño permite mantener los códigos como identificadores y documentar versiones de los recursos terminológicos usados.

## Alternativas consideradas

- **Asignar siempre el código más parecido (best-guess obligatorio)**: maximiza la cobertura aparente, pero introduce códigos incorrectos silenciosos y destruye la confianza en la salida, en un prototipo sin revisión clínica, inaceptable. Descartado.
- **Estado binario (con código / sin código)**: más simple, pero pierde la distinción entre "no hay correspondencia" y "hay varias candidatas y no sé cuál", que es justo la información útil para depurar y para una futura revisión asistida. Descartado.
- **Descartar las entidades no normalizadas de la salida**: viola directamente el criterio de aceptación de `specs/normalizacion-clinica.md` (una entidad sin código no debe perderse) y falsearía la evaluación. Descartado.

## Consecuencias

- El contrato JSON debe reservar los tres estados y permitir `coding` a `null` sin invalidar el documento.
- La primera fase deja `not_found` las formas de fármacos que no estén en el recurso de referencia; si una forma aparece asociada a varios códigos sin que uno alcance `min_agreement`, devuelve `ambiguous`.
- Las proteínas deben excluirse de la normalización y recibir `not_applicable`, pero esa excepción aún no está aplicada en el pipeline ni admitida por el esquema 1.0.
- La evaluación informa exactitud y cobertura por separado. El valor de `min_agreement` debe seleccionarse con `dev` y quedar fijado antes de la evaluación final; no debe ajustarse con `test`.

## Referencias

- SNOMED CT (incluye condiciones de licencia y licencia nacional española): [snomed.org](https://www.snomed.org/)
- SNOMED CT Browser para verificar códigos: [browser.ihtsdotools.org](https://browser.ihtsdotools.org/)
- CIE-10-ES, recursos oficiales del Ministerio de Sanidad: [sanidad.gob.es](https://www.sanidad.gob.es/)

## Ejemplo de estados de normalización

Ejemplo conceptual de los estados previstos, incluidos los de la categoría `protein` (esta última requiere la ampliación del esquema):

```json
[
  {"text": "enoxaparina", "type": "drug",
   "coding": {"system": "SNOMED_CT", "code": "372744005", "display": "enoxaparina"},
   "normalization_status": "matched"},

  {"text": "fármaco anticoagulante", "type": "drug",
   "coding": {"system": null, "code": null, "display": null},
   "normalization_status": "not_found"},

  {"text": "heparina", "type": "drug",
   "coding": {"system": null, "code": null, "display": null},
   "normalization_status": "ambiguous"},

  {"text": "PSA", "type": "protein",
   "coding": {"system": null, "code": null, "display": null},
   "normalization_status": "not_applicable"}
]
```