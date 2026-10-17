# Spec: generación y validación de recursos HL7 FHIR

## Propósito

Convertir el subconjunto de información clínica estructurada en JSON a recursos HL7 FHIR que representen de forma válida los conceptos extraídos y normalizados. Esta funcionalidad constituye una salida de demostración del prototipo y no una integración con sistemas sanitarios reales.

## Problema e intención

FHIR ofrece una forma estandarizada de representar e intercambiar información sanitaria. Mapear los resultados a recursos FHIR permite comprobar hasta qué punto la información extraída puede representarse mediante un estándar de interoperabilidad, sin asumir que la conversión por sí sola garantiza exactitud clínica o integración real.

## Qué construir

Un componente que reciba el JSON canónico y genere recursos FHIR JSON para los tipos de información acordados. Como punto de partida:
- las enfermedades o problemas de salud podrán representarse mediante `Condition`;
- los fármacos mencionados podrán representarse como `MedicationStatement` únicamente si el texto permite justificar que existe información sobre medicación tomada o declarada; una simple mención de un fármaco no se interpretará automáticamente como tratamiento activo;
- síntomas/signos y procedimientos se mapearán a recursos apropiados solo cuando el significado de la mención y el contenido disponible permitan una representación defendible. El recurso elegido y sus límites deberán documentarse antes de implementar el mapeo.

Cada recurso deberá incluir, cuando corresponda, un identificador de sistema y código en `CodeableConcept.coding`, además de un `text` que conserve el concepto original cuando sea adecuado. No se inventarán fechas, pacientes, estados clínicos ni otros campos ausentes del texto de origen.

La primera versión generará archivos FHIR JSON locales y un informe de validación. No transmitirá los recursos a un servidor FHIR.

## Restricciones y supuestos

- Se elegirá y documentará una versión concreta de FHIR antes de implementar; la versión y los perfiles aplicables serán consistentes en las pruebas.
- La salida debe cumplir la estructura y los tipos de datos de la versión seleccionada.
- No se fabricarán datos obligatorios que no estén disponibles. Si un recurso requiere información ausente, el sistema lo omitirá o marcará como no representable y explicará el motivo.
- Los códigos conservarán el identificador del sistema de codificación. Solo se incluirá un código cuando la normalización lo haya justificado.
- El texto de entrada procede de corpus públicos permitidos o ejemplos sintéticos.
- La primera versión no implementa perfiles nacionales específicos ni certificación de conformidad.

## Criterios de aceptación

1. La versión de FHIR y el formato de serialización se documentan en el README o en la documentación técnica.
2. Para cada ejemplo de prueba marcado como representable, el componente genera un recurso JSON con `resourceType` válido para el recurso seleccionado.
3. El 100 % de los recursos generados en la batería de pruebas supera la validación estructural contra la versión de FHIR elegida y las reglas/perfiles declarados que se hayan implementado.
4. Cuando se incluye un código, se identifica el sistema de codificación y el código coincide con el resultado de normalización de entrada.
5. Si la información no permite construir un recurso sin inventar datos, el sistema no fabrica esos datos: registra el elemento como no representable o lo omite según una política documentada.
6. Una batería de al menos 5 casos cubre: entidad con código, entidad sin código, tipo de entidad no mapeado, campo necesario ausente y texto con caracteres Unicode.
7. Se documenta una tabla de mapeo entre los campos JSON de origen y los campos FHIR de destino, incluidos los campos que no pueden transformarse.
8. La ejecución se limita a generar archivos locales; no se envían datos a servicios externos.

## Fuera de alcance

- Despliegue o mantenimiento de un servidor FHIR.
- Integración con IANUS, SERGAS u otros sistemas clínicos.
- Intercambio de datos reales de pacientes.
- Afirmar conformidad con perfiles nacionales o de producción que no se hayan validado explícitamente.
- Interpretar una mención textual como evidencia de un diagnóstico confirmado o de una medicación activa sin contexto suficiente.
