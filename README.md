# Extracción y estructuración de información clínica en español mediante PLN

## 1. ¿Qué es el proyecto?

Este proyecto propone un sistema de procesamiento del lenguaje natural (PLN) que recibe textos clínicos en español —principalmente casos clínicos publicados y ejemplos sintéticos— y transforma la información clínica relevante en datos estructurados. El prototipo identificará enfermedades, síntomas y signos, fármacos y procedimientos; intentará normalizar las entidades mediante terminologías clínicas de referencia, como SNOMED CT o CIE-10-ES cuando exista una correspondencia adecuada; y generará una salida JSON validable y una representación inicial mediante recursos HL7 FHIR para las entidades que puedan mapearse de forma justificada.

El problema que se aborda es que una parte importante de la información clínica se expresa en texto libre, lo que dificulta su búsqueda, comparación y explotación estadística. El proyecto busca demostrar un flujo reproducible de extracción y estructuración, no sustituir el criterio de profesionales sanitarios.

## 2. Motivación y objetivos

El equipo ha elegido este caso porque conecta la inteligencia artificial y el PLN con una necesidad concreta del ámbito sanitario: reutilizar información expresada en lenguaje natural sin perder la trazabilidad de su origen. Existen corpus clínicos en español publicados para investigación, lo que permite experimentar sin trabajar con historias clínicas reales.

Al terminar el proyecto esperamos disponer de un prototipo ejecutable en un ordenador personal que:
- procese textos clínicos en español;
- identifique y clasifique entidades clínicas relevantes;
- proponga códigos normalizados cuando haya una correspondencia defendible;
- genere una salida JSON con esquema documentado;
- convierta a recursos FHIR un subconjunto definido de la información estructurada;
- permita evaluar sus resultados frente a corpus anotados y validar técnicamente las salidas.

El enfoque técnico (modelos preentrenados, reglas, ajuste de modelos o comparación de alternativas) queda por decidir. La decisión se tomará tras inspeccionar los corpus, sus anotaciones, las licencias y los recursos disponibles, y se documentará antes de la implementación.

## 3. Alcance

### Incluido en la primera versión

- Procesamiento de textos clínicos en español procedentes de corpus públicos permitidos y/o ejemplos sintéticos.
- Extracción de cuatro tipos de entidad: enfermedades, síntomas/signos, fármacos y procedimientos.
- Conservación del texto original de cada mención y de sus posiciones en el texto cuando el método y el corpus lo permitan.
- Normalización a SNOMED CT o CIE-10-ES cuando se disponga de recursos de referencia y la correspondencia esté justificada. Las entidades ambiguas o sin correspondencia podrán quedar sin código.
- Generación de JSON homogéneo y validable.
- Generación de una salida FHIR inicial para los tipos de información que se hayan mapeado y validado. El alcance no presupone representar todo el contenido del texto como un recurso FHIR.
- Evaluación con datos anotados, separando el conjunto de prueba de los datos usados para desarrollar o ajustar el sistema.
- Ejecución local y documentación de configuración, dependencias, versiones y limitaciones.

### Fuera del alcance

- Uso de historias clínicas reales o datos personales de pacientes.
- Diagnóstico, recomendación terapéutica o toma de decisiones clínicas.
- Integración con IANUS, sistemas del SERGAS u otros sistemas de producción.
- Despliegue como servicio clínico o garantía de uso asistencial.
- Implementación de una plataforma FHIR completa, servidor FHIR, autenticación, intercambio con hospitales o conformidad certificada.
- Cobertura exhaustiva de todas las especialidades, entidades o variantes lingüísticas del español.
- Garantizar que toda entidad tenga un código estándar.
- Elegir un modelo concreto antes de analizar los datos y comparar la viabilidad de los enfoques.

## 4. Usuarios destinatarios

El prototipo está dirigido principalmente a estudiantes e investigadores que quieran explorar métodos de PLN clínico y preparar datos textuales para análisis secundarios. No está destinado a pacientes ni a profesionales para su uso directo en decisiones asistenciales.

## 5. Datos y referencias

Se priorizarán corpus públicos anotados en español, comprobando sus condiciones de uso y la adecuación de sus anotaciones antes de incorporarlos. Entre las fuentes candidatas se encuentran:

- TeMU-BSC: https://temu.bsc.es/
- PlanTL-GOB-ES: https://huggingface.co/PlanTL-GOB-ES
- SPACCC: https://github.com/PlanTL-GOB-ES/SPACCC
- DisTEMIST (enfermedades): https://temu.bsc.es/distemist
- PharmaCoNER (fármacos y proteínas): https://huggingface.co/datasets/PlanTL-GOB-ES/pharmaconer
- MedProcNER (procedimientos): https://zenodo.org/records/8224056
- SympTEMIST (síntomas y signos): https://zenodo.org/records/10635215
- CodiEsp (codificación CIE-10): https://temu.bsc.es/codiesp/

Terminologías y estándares de referencia:
- SNOMED CT: https://www.snomed.org/
- CIE-10-ES: recursos oficiales del Ministerio de Sanidad.
- HL7 FHIR: https://www.hl7.org/fhir/

La disponibilidad, licencia, versión y formato de cada recurso se comprobarán antes de utilizarlo. La mención de una fuente no implica que todas sus anotaciones sean compatibles entre sí ni que cubran las cuatro clases de entidad.

## 6. Equipo

| Integrante | Rol principal | Correo |
|---|---|---|
| Lucas Amado Oseira | Pendiente de acordar | Pendiente de añadir |
| María Lestón Geada | Pendiente de acordar | Pendiente de añadir |
| Mariña Vilar Estévez | Pendiente de acordar | Pendiente de añadir |
| Mateo Fraguas Abal | Pendiente de acordar | Pendiente de añadir |

**Contacto de tutoría profesional:** Gema Novo Rego, DIH DATAlife — gema@dihdatalife.com.

Los roles y correos personales deben completarse por el equipo antes de la entrega. No se han inventado direcciones de correo.

## 7. Criterios generales de éxito

- El sistema acepta un texto clínico en español y devuelve JSON conforme al esquema documentado.
- La extracción se evalúa con precisión, recall y F1 sobre un conjunto de prueba anotado que no se utilice para entrenar ni ajustar el sistema.
- La normalización se evalúa por separado, informando de la exactitud de los códigos y de la cobertura.
- La salida FHIR se valida contra la versión y los perfiles de FHIR declarados en la implementación; los recursos que no puedan mapearse de forma justificada se informan como no representados, sin inventar datos.
- Los resultados, versiones de datos/modelos, decisiones técnicas y limitaciones quedan documentados.

Los umbrales cuantitativos iniciales y el protocolo detallado se recogen en las specs. Son objetivos propuestos, no resultados ya obtenidos; deberán revisarse si el corpus elegido no permite una evaluación válida.

## 8. Estructura del repositorio

```text
entregas/
└── cu-03-extraccion-clinica/
    ├── README.md
    └── specs/
        ├── extraccion-entidades.md
        ├── normalizacion-clinica.md
        ├── generacion-json.md
        ├── generacion-fhir.md
        └── evaluacion-resultados.md
```

- `README.md`: visión general, motivación, alcance, datos candidatos, equipo y organización.
- `specs/extraccion-entidades.md`: comportamiento esperado al detectar y clasificar menciones clínicas.
- `specs/normalizacion-clinica.md`: reglas para proponer códigos estándar y gestionar casos ambiguos o sin correspondencia.
- `specs/generacion-json.md`: contrato de salida JSON, validación y gestión de errores.
- `specs/generacion-fhir.md`: conversión del subconjunto acordado de datos a recursos FHIR y validación.
- `specs/evaluacion-resultados.md`: protocolo y métricas para comprobar la calidad del prototipo.

## 9. Seguridad y limitaciones

La primera versión trabajará únicamente con corpus públicos autorizados y/o textos sintéticos, sin datos identificables de pacientes. Los resultados son experimentales y no deben interpretarse como información validada para la asistencia sanitaria. El sistema debe distinguir entre una entidad detectada, un código propuesto y una entidad que no se ha podido normalizar. La conversión a FHIR no implica por sí sola que los datos sean clínicamente correctos ni que el sistema esté listo para integrarse en producción.
