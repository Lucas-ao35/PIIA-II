# Spec: generación y validación de recursos HL7 FHIR

## Propósito

Convertir el subconjunto de información clínica estructurada en JSON a recursos HL7 FHIR que representen de forma válida los conceptos extraídos y normalizados. Esta funcionalidad constituye una salida de demostración del prototipo y no una integración con sistemas sanitarios reales. Es una ampliación: se aborda solo después de que el camino crítico (fármacos → detección → normalización → JSON → métricas) funcione de punta a punta, y es lo primero que se recortará si el tiempo es justo.

## Problema e intención

FHIR ofrece una forma estandarizada de representar e intercambiar información sanitaria. Mapear los resultados a recursos FHIR permite comprobar hasta qué punto la información extraída puede representarse mediante un estándar de interoperabilidad, sin asumir que la conversión por sí sola garantiza exactitud clínica o integración real.

## Qué construir

Un componente que reciba el JSON canónico (`specs/generacion-json.md`) y genere, por documento, un `Bundle` de tipo `collection` con los recursos FHIR JSON de las entidades representables, además de un informe de validación.

Como punto de partida:

- las enfermedades o problemas de salud podrán representarse mediante `Condition`;
- los fármacos mencionados podrán representarse como `MedicationStatement` únicamente si el texto permite justificar que existe información sobre medicación tomada o declarada; una simple mención de un fármaco no se interpretará automáticamente como tratamiento activo;
- las proteínas (`protein`) no se convierten a recursos FHIR y se registran como tipo no mapeado (ver [`decisions/proteinas-categoria-propia.md`](../decisions/proteinas-categoria-propia.md));
- síntomas/signos y procedimientos se mapearán a recursos apropiados solo cuando el significado de la mención y el contenido disponible permitan una representación defendible. El recurso elegido y sus límites deberán documentarse antes de implementar el mapeo.

Cada recurso deberá incluir, cuando corresponda, un identificador de sistema y código en `CodeableConcept.coding`, además de un `text` que conserve el concepto original cuando sea adecuado. No se inventarán fechas, pacientes, estados clínicos ni otros campos ausentes del texto de origen.

### Tabla de mapeo por defecto

| `type` en el JSON | Recurso FHIR R4 | Elemento con el concepto | Elementos obligatorios sin dato en el texto |
|---|---|---|---|
| `disease` | `Condition` | `Condition.code` | `subject` → paciente anónimo del documento |
| `drug` | `MedicationStatement` | `MedicationStatement.medicationCodeableConcept` | `status` = `unknown`; `subject` → paciente anónimo |
| `symptom` | `Observation` | `Observation.code` | `status` = `unknown` |
| `procedure` | `Procedure` | `Procedure.code` | `status` = `unknown`; `subject` → paciente anónimo |
| `protein` | No se convierte | — | — |

- **Paciente anónimo**: cada `Bundle` incluye un único `Patient` sin datos demográficos ni identificadores, cuyo `id` se deriva del `document_id` (o es un identificador secuencial si `document_id` es `null`). Solo sirve como referencia `subject` obligatoria, sin representar a ninguna persona real.
- **Estado `unknown`**: cuando un recurso exige `status` y el texto no lo aporta, se usa siempre `unknown`. Así, la mención de un fármaco nunca se representa como tratamiento activo (`active`).
- **Codificación**: si la entidad tiene `normalization_status` = `matched`, el `CodeableConcept` incluye `coding` con `system` = `http://snomed.info/sct` y el código normalizado. En otro caso solo incluye `text` con la mención original.

### Versión de FHIR

Se adopta **HL7 FHIR R4 (4.0.1)**, serializado en JSON, sin perfiles nacionales. Se elige R4 por ser la versión normativa con mayor soporte en herramientas y validadores. La validación estructural se realiza con el validador oficial de HL7 (`validator_cli`) indicando la versión `4.0.1`.

La primera versión generará archivos FHIR JSON locales y un informe de validación. No transmitirá los recursos a un servidor FHIR.

**Criterio de cambio**: la versión solo se cambiará si una herramienta de validación o un perfil que el proyecto necesite exige otra versión. El cambio se registrará en un ADR, se actualizará esta spec y se repetirá la batería de pruebas completa con la nueva versión.

### Regla de representabilidad

La decisión de si una entidad es representable no se toma caso a caso. La aplica automáticamente el conversor con esta regla, fijada por el equipo en esta spec:

> Una entidad es **representable** si y solo si su `type` figura en la tabla de mapeo con un recurso de destino y todos los elementos obligatorios de ese recurso pueden completarse con datos del JSON o con los valores fijos documentados arriba (`unknown` y paciente anónimo).

Las entidades no representables (p. ej. `protein` o un `type` sin fila en la tabla) no generan recurso y se registran en el informe con su `type` y el motivo `tipo no mapeado`.

## Restricciones y supuestos

- La salida debe cumplir la estructura y los tipos de datos de FHIR R4 4.0.1.
- No se fabricarán fechas, pacientes reales, estados clínicos distintos de `unknown` ni otros campos ausentes del texto de origen.
- Solo se incluirá un código cuando la normalización lo haya asignado con estado `matched`.
- El texto de entrada procede de corpus públicos permitidos o ejemplos sintéticos.
- La primera versión genera archivos locales y no implementa perfiles nacionales ni certificación de conformidad.

## Criterios de aceptación

Estos criterios se aplican solo si se implementa la ampliación FHIR. Su ausencia no impide completar el núcleo del proyecto, como se especifica en `specs/evaluacion-resultados.md`.

1. Cada `Bundle` generado declara recursos conformes a FHIR R4 4.0.1 serializados en JSON.
2. Para cada entidad representable según la regla anterior se genera exactamente un recurso del tipo indicado en la tabla de mapeo.
3. El 100 % de los recursos generados en la batería de pruebas supera la validación oficial de HL7 con la versión 4.0.1 sin errores (se admiten avisos).
4. Cuando se incluye un código, `system` es `http://snomed.info/sct` y el código coincide con `coding.code` del JSON de entrada.
5. Ningún recurso contiene fechas, datos demográficos ni valores de `status` distintos de `unknown` que no procedan del JSON de entrada.
6. Las entidades no representables no generan recurso y aparecen en el informe con su `type` y el motivo.
7. Una batería de al menos 5 casos cubre: entidad con código, entidad sin código, tipo de entidad no mapeado, campo necesario ausente y texto con caracteres Unicode.
8. La ejecución se limita a generar archivos locales; no se envían datos a servicios externos.

## Fuera de alcance

- Despliegue o mantenimiento de un servidor FHIR.
- Integración con IANUS, SERGAS u otros sistemas clínicos.
- Intercambio de datos reales de pacientes.
- Afirmar conformidad con perfiles nacionales o de producción que no se hayan validado explícitamente.
- Interpretar una mención textual como evidencia de un diagnóstico confirmado o de una medicación activa.