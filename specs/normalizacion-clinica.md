# Spec: normalización de entidades clínicas

## Propósito

Vincular entidades detectadas con conceptos de terminologías clínicas estándar cuando exista una correspondencia defendible. Para cada entidad se devuelve una propuesta de código, el sistema terminológico y el estado de la normalización.

## Problema e intención

La extracción por sí sola produce texto localizado, pero no resuelve el problema de interoperabilidad: dos menciones equivalentes pueden escribirse de formas distintas. Asociarlas a identificadores normalizados permite agrupar, consultar y reutilizar la información. Mantener explícitamente los casos no resueltos evita presentar como segura una codificación que el sistema no puede justificar.

## Qué construir

Se definirá una etapa posterior a la extracción que intente asociar cada entidad clínica a un código estándar. Su resultado se incorporará a la entidad correspondiente del JSON canónico descrito en `generacion-json.md`, sin definir un segundo formato de documento. La normalización usará las correspondencias proporcionadas por los datasets o por los recursos terminológicos autorizados. Cuando no exista una coincidencia inequívoca, la entidad se conservará con estado `not_found` en vez de inventar un código. Los casos ambiguos usarán el estado `ambiguous`.

El siguiente fragmento ilustra los campos de normalización dentro de una entidad; los nombres y estados deben seguir el contrato de `generacion-json.md`:

```json
{
  "coding": {"system": "SNOMED_CT", "code": "36404004", "display": "..."},
  "normalization_status": "matched"
}
```

Los campos de `coding` podrán ser `null` cuando no haya código. El sistema distinguirá entre una entidad con código, una entidad no mapeada y un caso ambiguo que requiera revisión. Se usarán los nombres de estado acordados en el esquema canónico.

## Restricciones y supuestos

- Cada código conservará el sistema de codificación en `coding.system`.
- No se generarán códigos mediante similitud textual si la correspondencia no supera el umbral de confianza fijado y documentado.
- La primera versión no necesita cubrir todos los sinónimos ni todos los conceptos.
- Si el acceso a una terminología completa requiere licencia o autorización, se documentarán los recursos permitidos y sus limitaciones.
- La evaluación se limitará a menciones con una referencia de oro y un mapeo inequívoco al sistema evaluado.
- El JSON deberá ser válido, codificado en UTF-8 y conservar el orden de las entidades según su aparición en el texto.
- El identificador del documento no contendrá el texto clínico ni datos personales.
- La primera fase de implementación priorizará fármacos y podrá dejar sin código las categorías aún no cubiertas por una fuente de mapeo fiable.

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
