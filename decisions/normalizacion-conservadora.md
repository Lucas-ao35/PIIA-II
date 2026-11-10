# ADR: Normalización conservadora con estados explícitos

## Estado

Aceptada

## Contexto

La normalización asocia cada mención detectada a un código de SNOMED CT o CIE-10-ES. Es la etapa de mayor riesgo del proyecto: la terminología clínica es ambigua, los sinónimos abundan y un código incorrecto es peor que ninguno, porque un consumidor posterior (investigador, sistema de información) lo trataría como dato fiable. Además, SNOMED CT tiene restricciones de licencia que condicionan qué se puede publicar en un repositorio abierto.

## Decisión

Adoptar una **política de normalización conservadora con estados explícitos**: cada entidad recibe exactamente un resultado de normalización con un estado de tres valores —`matched` (código asignado con correspondencia inequívoca), `not_found` (sin correspondencia defendible, campos `coding` a `null`) y `ambiguous` (candidatos múltiples que requieren revisión)—. No se asigna ningún código por similitud textual que no supere un umbral de confianza fijado y documentado, ninguna entidad sin código se elimina de la salida, y los casos `not_found` y `ambiguous` se contabilizan por separado en la evaluación.

## Motivación

- **Honestidad del resultado**: el sistema distingue siempre entre "detecté una mención", "propuse este código" y "no pude normalizarla". Presentar solo códigos ocultaría la cobertura real del prototipo.
- **Evaluabilidad**: con los estados explícitos, la métrica de exactitud de códigos se calcula solo sobre el subconjunto evaluable (entidades con referencia gold y mapeo inequívoco), y la cobertura se informa aparte, tal como exige `specs/evaluacion-resultados.md`.
- **Seguridad**: un prototipo académico que no inventa datos es seguro para su propósito (investigación y análisis secundario) y respeta el principio del proyecto de no sustituir criterio profesional.
- **Licencias**: no publicar descripciones ni fragmentos de SNOMED CT hasta confirmar condiciones (en España hay licencia nacional del Ministerio de Sanidad, pero hay que verificar qué se puede redistribuir); el diseño permite mantener los códigos como identificadores y documentar versiones de los recursos terminológicos usados.

## Alternativas consideradas

- **Asignar siempre el código más parecido (best-guess obligatorio)**: maximiza la cobertura aparente, pero introduce códigos incorrectos silenciosos y destruye la confianza en la salida; en un prototipo sin revisión clínica, inaceptable. Descartado.
- **Estado binario (con código / sin código)**: más simple, pero pierde la distinción entre "no hay correspondencia" y "hay varias candidatas y no sé cuál", que es justo la información útil para depurar y para una futura revisión asistida. Descartado.
- **Descartar las entidades no normalizadas de la salida**: viola directamente el criterio de aceptación de `specs/normalizacion-clinica.md` (una entidad sin código no debe perderse) y falsearía la evaluación. Descartado.

## Consecuencias

- El contrato JSON debe reservar los tres estados y permitir `coding` a `null` sin invalidar el documento.
- La primera fase dejará sin código (`not_found`) las categorías que aún no tengan fuente de mapeo fiable (todo lo que no sean fármacos/proteínas).
- La evaluación informa exactitud y cobertura por separado, y los umbrales de similitud (si se usan) deben fijarse y documentarse antes de la evaluación final.

## Referencias

- Spec de normalización: [`specs/normalizacion-clinica.md`](../specs/normalizacion-clinica.md)
- Contrato de estados: [`specs/generacion-json.md`](../specs/generacion-json.md)
- SNOMED CT (incluye condiciones de licencia y licencia nacional española): [snomed.org](https://www.snomed.org/)
- SNOMED CT Browser para verificar códigos: [browser.ihtsdotools.org](https://browser.ihtsdotools.org/)
- CIE-10-ES, recursos oficiales del Ministerio de Sanidad: [sanidad.gob.es](https://www.sanidad.gob.es/)

Ejemplo de los tres estados dentro del JSON canónico:

```json
[
  {"text": "enoxaparina", "type": "drug",
   "coding": {"system": "SNOMED_CT", "code": "372744005", "display": "enoxaparina"},
   "normalization_status": "matched"},
  {"text": "fármaco anticoagulante", "type": "drug",
   "coding": {"system": null, "code": null, "display": null},
   "normalization_status": "not_found"}
]
```
