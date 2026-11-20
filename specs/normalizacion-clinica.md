# Spec: normalización de entidades clínicas

## Propósito

Vincular entidades detectadas con conceptos de terminologías clínicas estándar cuando exista una correspondencia defendible. Para cada entidad se devuelve una propuesta de código, el sistema terminológico y el estado de la normalización.

## Problema e intención

La extracción por sí sola produce texto localizado, pero no resuelve el problema de interoperabilidad: dos menciones equivalentes pueden escribirse de formas distintas. Asociarlas a identificadores normalizados permite agrupar, consultar y reutilizar la información. Mantener explícitamente los casos no resueltos evita presentar como segura una codificación que el sistema no puede justificar.

## Qué construir

Se definirá una etapa posterior a la extracción que intente asociar cada entidad clínica a un código estándar. Su resultado se incorporará a la entidad correspondiente del JSON canónico descrito en `generacion-json.md`, sin definir un segundo formato de documento. La normalización usará las correspondencias proporcionadas por los datasets o por los recursos terminológicos autorizados. Cuando no exista una coincidencia inequívoca, la entidad se conservará con estado `not_found` en vez de inventar un código. Los casos ambiguos usarán el estado `ambiguous`.

La primera implementación utilizará un normalizador basado en diccionario, construido a partir de las correspondencias observadas en las anotaciones de entrenamiento de PharmaCoNER. Este enfoque constituye una línea base inicial y no pretende cubrir toda la terminología SNOMED CT.

Se priorizará disponer de una normalización funcional y evaluable para las menciones de fármacos antes de ampliar la cobertura a otras categorías clínicas o incorporar mecanismos de normalización más complejos.

El siguiente fragmento ilustra los campos de normalización dentro de una entidad; los nombres y estados deben seguir el contrato de `generacion-json.md`:

```json
{
  "coding": {"system": "SNOMED_CT", "code": "36404004", "display": "..."},
  "normalization_status": "matched"
}
```

Los campos de `coding` podrán ser `null` cuando no haya código. El sistema distinguirá entre una entidad con código, una entidad no mapeada y un caso ambiguo que requiera revisión. El conjunto completo de estados permitidos (`matched`, `not_found`, `ambiguous`, `not_applicable`) se define únicamente en `generacion-json.md`.

## Restricciones y supuestos

- Cada código conservará el sistema de codificación en `coding.system`.
- No se generarán códigos mediante similitud textual si la correspondencia no supera el umbral de confianza fijado y documentado.
- La normalización de fármacos es parte del camino crítico del proyecto y se aborda pronto, en paralelo a la extracción y antes que FHIR. Se prefiere una normalización sencilla que funcione de principio a fin.
- La primera versión no necesita cubrir todos los sinónimos ni todos los conceptos.
- Antes de distribuir públicamente recursos derivados de SNOMED CT, se comprobarán las condiciones de la licencia de afiliado aplicable al proyecto y los permisos de redistribución correspondientes. En España existe una licencia nacional gestionada por el Ministerio de Sanidad, pero se verificará su alcance para el uso concreto del equipo.
- Hasta confirmar dichas condiciones, no se publicarán descripciones oficiales, extractos de la terminología ni tablas de mapeo que puedan implicar la redistribución de contenido licenciado. Los identificadores numéricos y el código desarrollado por el equipo se tratarán de forma diferenciada respecto al contenido terminológico. CIE-10-ES presenta un marco de acceso distinto, que también se respetará según sus condiciones de uso.
- Si el acceso a una terminología completa requiere licencia o autorización, se documentarán los recursos permitidos y sus limitaciones.
- La evaluación se limitará a menciones con una referencia de oro y un mapeo inequívoco al sistema evaluado.
- El JSON deberá ser válido, codificado en UTF-8 y conservar el orden de las entidades según su aparición en el texto.
- El identificador del documento no contendrá el texto clínico ni datos personales.
- La primera fase de implementación priorizará fármacos y podrá dejar sin código las categorías aún no cubiertas por una fuente de mapeo fiable.
- Las entidades `protein` quedan fuera de la normalización: no se envían al normalizador, reciben `normalization_status` = `not_applicable`, no se usan para construir las tablas de correspondencias y no cuentan en las métricas de normalización, tal y como se especifica en [`decisions/proteinas-categoria-propia.md`](../decisions/proteinas-categoria-propia.md).

## Criterios de aceptación

1. Cada entidad de entrada produce exactamente un resultado de normalización, incluso si no se encuentra código.
2. Si el estado es `matched`, `coding.system`, `coding.code` y `coding.display` están informados y el código existe en el recurso de referencia utilizado.
3. Una entidad sin correspondencia aparece con el estado `not_found`, mantiene los campos de `coding` a `null` y no provoca el fallo de todo el documento.
4. Las menciones sin código y ambiguas se contabilizan por separado.
5. Se documentan las versiones o fechas de los recursos terminológicos y las reglas de mapeo.
6. Existen pruebas para, como mínimo, un caso mapeado, un caso no mapeado, un documento sin entidades y una entrada con más de una categoría.
7. El resultado de normalización se integra en el JSON canónico y valida contra el esquema publicado por el proyecto.


## Fuera de alcance

- Codificación exhaustiva o certificada para uso asistencial.
- Resolver automáticamente todas las ambigüedades contextuales.
- Sustituir la revisión de especialistas en terminología clínica.
- Codificación para facturación o decisiones clínicas.