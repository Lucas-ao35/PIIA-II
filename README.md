# CU-03 — Extracción y estructuración de información clínica

## ¿Qué es el proyecto?

Este proyecto propone un sistema de procesamiento del lenguaje natural (PLN) para leer textos clínicos en español, principalmente casos clínicos publicados y ejemplos sintéticos, y transformarlos en información clínica estructurada. El programa identificará enfermedades, síntomas y signos, fármacos y procedimientos; intentará normalizar las entidades mediante terminologías clínicas de referencia, como SNOMED CT o CIE-10-ES cuando exista una correspondencia adecuada; y generará una salida JSON homogénea y validable y una representación inicial mediante recursos HL7 FHIR para las entidades que puedan mapearse de forma justificada.

El caso de uso responde a que una parte importante de la información clínica se expresa en texto libre, lo que dificulta su consulta, análisis y explotación estadística. El proyecto busca facilitar el análisis posterior, la investigación biomédica y la interoperabilidad con sistemas de información sanitaria, no sustituir el criterio de profesionales sanitarios.

##  Motivación y objetivos

El equipo ha elegido este caso porque conecta la inteligencia artificial y el PLN con una necesidad concreta del ámbito sanitario: la conversión de información expresada en lenguaje natural sin perder la trazabilidad de su origen y facilitando su explotación secundaria. Existen corpus clínicos en español publicados para investigación, lo que permite experimentar sin trabajar con historias clínicas reales. El SERGAS aborda una necesidad relacionada mediante IANUS, que organiza la información clínica porproblemas de salud y utiliza terminologías normalizadas. Este proyecto permite estudiar, de forma reproducible, las etapas necesarias para pasar de una frase clínica a un registro que pueda ser procesado por una base de datos.

Al terminar el proyecto esperamos disponer de una pipeline funcional que:
1. Reciba textos clínicos en español;
2. Detecte y clasifique entidades clínicas previstas;
3. Normalice las entidades cuando haya una correspondencia defendible en la terminología de referencia;
4. Genere una salida JSON validable;
5. Convierta a recursos FHIR un subconjunto definido de la información estructurada;
6. Permita evaluar sus resultados frente a corpus anotados y validar técnicamente las salidas mediante métricas estándar.

Se comenzará por la entidad de fármacos, tal como se recomendó en la primera reunión, y se diseñará la solución para poder incorporar posteriormente enfermedades, síntomas y procedimientos.
El enfoque técnico (modelos preentrenados, reglas, ajuste de modelos o comparación de alternativas) queda por decidir. La decisión se tomará tras inspeccionar los corpus, sus anotaciones, las licencias y los recursos disponibles, y se documentará antes de la implementación.

## Alcance

### Incluido en la primera versión

- Procesamiento de textos clínicos en español procedentes de corpus públicos permitidos.
- Extracción de fármacos mediante el corpus PharmaCoNER.
- Incorporación de enfermedades, síntomas y procedimientos mediante DisTEMIST, SympTEMIST y MedProcNER.
- Detección de menciones y clasificación por tipo de entidad.
- Conservación del texto original de cada mención y de sus posiciones en el texto cuando el método y el corpus lo permitan.
- Normalización a SNOMED CT o CIE-10-ES cuando se disponga de recursos de referencia y la correspondencia sea inequívoca. Las entidades ambiguas o sin correspondencia podrán quedar sin código.
- Generación de JSON homogéneo, validable y con un esquema documentado.
- Generación de una salida FHIR inicial para los tipos de información que se hayan mapeado y validado. El alcance no presupone representar todo el contenido del texto como un recurso FHIR.
- Evaluación con datos anotados, separando el conjunto de prueba de los datos usados para desarrollar o ajustar el sistema.
- Ejecución local y documentación de configuración, dependencias, versiones y limitaciones.

### Fuera del alcance

- Uso de historias clínicas reales o de datos personales de pacientes.
- Diagnóstico, recomendación terapéutica o toma de decisiones clínicas.
- Integración con IANUS, sistemas del SERGAS u otros sistemas de producción.
- Despliegue como servicio clínico o garantía de uso asistencial.
- Implementación de una plataforma FHIR completa, servidor FHIR, autenticación, intercambio con hospitales o conformidad certificada.
- Cobertura exhaustiva de todas las especialidades, entidades o variantes lingüísticas del español.
- Garantizar que toda entidad tenga un código estándar.
- Elegir un modelo concreto antes de analizar los datos y comparar la viabilidad de los enfoques.

## Usuarios destinatarios

El prototipo está dirigido principalmente a estudiantes e investigadores que quieran explorar métodos de PLN clínico y preparar datos textuales para análisis secundarios. No está destinado a pacientes ni a profesionales para su uso directo en decisiones asistenciales.

## Datos y referencias

Se priorizarán corpus públicos anotados en español, comprobando sus condiciones de uso y la adecuación de sus anotaciones antes de incorporarlos. Entre las fuentes candidatas se encuentran:

- [TeMU-BSC](https://temu.bsc.es/)
- PlanTL-GOB-ES: https://huggingface.co/PlanTL-GOB-ES
- [SPACCC](https://github.com/PlanTL-GOB-ES/SPACCC): corpus de casos clínicos
  en español del que se derivan varios recursos.
- [PharmaCoNER](https://huggingface.co/datasets/PlanTL-GOB-ES/pharmaconer): fármacos y proteínas
- [DisTEMIST](https://temu.bsc.es/distemist): enfermedades 
- [MedProcNER](https://zenodo.org/records/8224056): procedimientos
- [SympTEMIST](https://zenodo.org/records/10635215): síntomas y signos
- [CodiEsp](https://temu.bsc.es/codiesp/): codificación CIE-10

Como referencias terminológicas se considerarán SNOMED CT y CIE-10-ES, siempre respetando las licencias y condiciones de uso de cada recurso.
- [SNOMED CT](https://www.snomed.org/)
- CIE-10-ES: recursos oficiales del Ministerio de Sanidad.
- [HL7 FHIR](https://www.hl7.org/fhir/)
    
La mención de una fuente no implica que todas sus anotaciones sean compatibles entre sí ni que cubran las cuatro clases de entidad.

## Equipo

| Integrante | Rol principal | Correo |
|---|---|---|
| Lucas Amado Oseira | Pendiente de acordar | Pendiente de añadir |
| María Lestón Geada | Pendiente de acordar | Pendiente de añadir |
| Mariña Vilar Estévez | Pendiente de acordar | Pendiente de añadir |
| Mateo Fraguas Abal | Pendiente de acordar | mateofraguas@gmail.com |

- Contacto de tutoría profesional: **Gema Novo Rego**, DIH DATAlife — ([gema@dihdatalife.com](mailto:gema@dihdatalife.com)).

Los roles y correos personales deben completarse por el equipo antes de la entrega. No se han inventado direcciones de correo.

## Criterios generales de éxito

- El sistema acepta un texto clínico en español y devuelve JSON conforme al esquema documentado.
- La extracción se evalúa con precisión, recall y F1 sobre un conjunto de prueba anotado que no se utilice para entrenar ni ajustar el sistema.
- La normalización se evalúa por separado, informando de la exactitud de los códigos y de la cobertura.
- La salida FHIR se valida contra la versión y los perfiles de FHIR declarados en la implementación; los recursos que no puedan mapearse de forma justificada se informan como no representados, sin inventar datos.
- Los resultados, versiones de datos/modelos, decisiones técnicas y limitaciones quedan documentados.

Los umbrales cuantitativos iniciales y el protocolo detallado se recogen en las specs. Son objetivos propuestos, no resultados ya obtenidos; deberán revisarse si el corpus elegido no permite una evaluación válida.

## Estructura del repositorio

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

## Seguridad y limitaciones

La primera versión trabajará únicamente con corpus públicos autorizados y/o textos sintéticos, sin datos identificables de pacientes. Los resultados son experimentales y no deben interpretarse como información validada para la asistencia sanitaria. El sistema debe distinguir entre una entidad detectada, un código propuesto y una entidad que no se ha podido normalizar. La conversión a FHIR no implica por sí sola que los datos sean clínicamente correctos ni que el sistema esté listo para integrarse en producción.
