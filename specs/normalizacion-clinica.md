# Spec: normalización de entidades clínicas

## 1. Propósito

Vincular entidades detectadas con conceptos de terminologías clínicas estándar cuando exista una correspondencia defendible. Para cada entidad se devuelve una propuesta de código, el sistema terminológico y el estado de la normalización.

## 2. Problema e intención

Expresiones distintas pueden referirse a un mismo concepto, mientras que una expresión puede ser ambigua según el contexto. La normalización facilita la comparación y el análisis, pero una asignación no justificada puede introducir errores. Por ello, el sistema debe representar explícitamente los casos sin coincidencia o ambiguos.

## 3. Qué construir

Para cada entidad de entrada, generar:
- `entity_text`: mención original;
- `entity_type`: categoría recibida;
- `coding_system`: `SNOMED_CT`, `CIE10ES` o `null`;
- `code`: código propuesto o `null`;
- `display`: término preferido disponible o `null`;
- `normalization_status`: `matched`, `ambiguous`, `not_found` o `not_applicable`;
- `method`: método o recurso utilizado para la propuesta.

Se utilizarán SNOMED CT y/o CIE-10-ES según la clase de entidad, los recursos accesibles y las condiciones de licencia. No se asumirá que todos los tipos tienen una correspondencia adecuada en ambos sistemas.

## 4. Restricciones y supuestos

- Solo se utilizarán terminologías y recursos cuyas condiciones permitan el uso previsto.
- Todo código debe conservar su sistema de codificación.
- No se inventarán códigos. Si no existe una coincidencia justificable, `code` será `null`.
- La primera versión no necesita cubrir todos los sinónimos ni todos los conceptos.
- Si el acceso a una terminología completa requiere licencia o autorización, se documentarán los recursos permitidos y sus limitaciones.
- La evaluación se limitará a menciones con una referencia de oro y un mapeo inequívoco al sistema evaluado.

## 5. Criterios de aceptación

1. Cada entidad de entrada produce exactamente un resultado de normalización, incluso si no se encuentra código.
2. Si el estado es `matched`, `coding_system`, `code` y `display` están informados y el código existe en el recurso de referencia utilizado.
3. Si no hay correspondencia, se devuelve `code: null` y estado `not_found`; si hay varias opciones no resolubles, se devuelve `ambiguous` sin escoger un código arbitrario.
4. No se mezclan códigos SNOMED CT y CIE-10-ES sin identificar su sistema.
5. En el subconjunto de prueba con códigos de referencia, se informa de la exactitud top-1 y de la cobertura. Objetivo inicial: exactitud top-1 ≥ 0,70; se informará por separado por terminología y clase cuando haya suficientes ejemplos.
6. Las menciones sin código y ambiguas se contabilizan por separado.
7. Se documentan las versiones o fechas de los recursos terminológicos y las reglas de mapeo.

## 6. Fuera de alcance

- Codificación exhaustiva o certificada para uso asistencial.
- Resolver automáticamente todas las ambigüedades contextuales.
- Sustituir la revisión de especialistas en terminología clínica.
- Codificación para facturación o decisiones clínicas.
