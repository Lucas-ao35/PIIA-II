# CU-03 — Extracción y estructuración de información clínica en español mediante PLN

## ¿Qué es el proyecto?

En este proyecto se propone definir un prototipo de Procesamiento del Lenguaje Natural (PLN) que lea textos clínicos en español, principalmente casos publicados y ejemplos sintéticos, y los transforme en datos estructurados. El flujo previsto extraerá menciones clínicas (enfermedades, síntomas, fármacos, procedimientos, ...), intentará normalizarlas con terminologías de referencia cuando haya correspondencia justificable y generará JSON; contempla además una representación inicial en recursos HL7 FHIR. En esta entrega se especifican esas funcionalidades, pero todavía no se implementan.

El caso de uso responde a que una parte importante de la información clínica se expresa en texto libre, lo que dificulta su consulta, análisis y explotación estadística. El proyecto busca facilitar el análisis posterior, la investigación biomédica y la interoperabilidad con sistemas de información sanitaria, no sustituir el criterio de profesionales sanitarios.


##  Motivación y objetivos

Como equipo, este caso nos ha llamado la atención por conectar con la inteligencia artificial y el PLN con una necesidad real concreta del ámbito sanitario. Responde al problema de que parte de la información clínica está en texto libre y resulta difícil de consultar y reutilizar. Este proyecto permite estudiar, de forma reproducible, las etapas necesarias para pasar de una frase clínica a un registro que pueda ser procesado por una base de datos.

En la primera reunión se nos recomendó comenzar por el tratamiento de fármacos, mas el equipo prevé una posible ampliación posterior del reconocimiento a enfermedades, síntomas/signos y procedimientos. El SERGAS aborda una necesidad relacionada mediante IANUS, que organiza la información por problemas de salud. Además, los corpus clínicos en español publicados para investigación permiten definir una evaluación sin usar historias clínicas reales.

El objetivo del proyecto es especificar, y en fases posteriores construir, un pipeline que:

1. Reciba textos clínicos en español.
2. Detecte y clasifique entidades clínicas previstas.
3. Normalice las entidades cuando haya una correspondencia defendible en la terminología de referencia.
4. Genere una salida JSON validable.
5. Convierta a recursos FHIR un subconjunto definido de la información estructurada.
6. Permita evaluar sus resultados frente a corpus anotados y validar técnicamente las salidas mediante métricas estándar.

La primera fase de implementación priorizará fármacos con PharmaCoNER. La incorporación de enfermedades, síntomas/signos y procedimientos queda prevista como ampliación, sujeta a comprobar la compatibilidad y disponibilidad de sus corpus.

El enfoque técnico (modelos preentrenados, reglas, ajuste de modelos o comparación de alternativas) queda por decidir. La decisión se tomará tras inspeccionar los corpus, sus anotaciones, las licencias y los recursos disponibles, y se documentará antes de la implementación.


## Alcance

### Definido en el proyecto

- Procesamiento de textos clínicos en español procedentes de corpus públicos permitidos.
- Inicio de la extracción con fármacos mediante el corpus PharmaCoNER; ampliación prevista a enfermedades, síntomas/signos y procedimientos con DisTEMIST, SympTEMIST y MedProcNER, si sus datos son compatibles.
- Detección de menciones y clasificación por tipo de entidad.
- Conservación del texto original de cada mención y de sus posiciones en el texto cuando el método y el corpus lo permitan.
- Normalización a SNOMED CT o CIE-10-ES cuando se disponga de recursos de referencia y la correspondencia sea inequívoca. Las entidades ambiguas o sin correspondencia podrán quedar sin código.
- Generación de JSON homogéneo, validable y con un esquema documentado.
- Especificación de una salida FHIR inicial para los tipos de información que puedan mapearse y validarse. No se presupone representar todo el contenido del texto como un recurso FHIR.
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

El prototipo está dirigido principalmente a estudiantes e investigadores que quieran explorar métodos de PLN clínico y preparar datos textuales para análisis secundarios. No está destinado a pacientes ni a profesionales para su uso directo en decisiones asistenciales. Sin embargo, puede ser una fuente de apoyo para profesionales del sector en un futuro, cuando se refinen sus funcionalidades.


## Datos y referencias

Se priorizarán corpus públicos escritos en español, comprobando sus condiciones de uso y la adecuación de sus anotaciones antes de incorporarlos. Entre las fuentes candidatas se encuentran:

- [TeMU-BSC](https://temu.bsc.es/): repositorio
- [PlanTL-GOB-ES](https://huggingface.co/PlanTL-GOB-ES): corpus y modelos
- [SPACCC](https://github.com/PlanTL-GOB-ES/SPACCC): corpus base de casos clínicos en español del que se derivan varios recursos
- [PharmaCoNER](https://huggingface.co/datasets/PlanTL-GOB-ES/pharmaconer): fármacos y proteínas
- [DisTEMIST](https://temu.bsc.es/distemist): enfermedades 
- [MedProcNER](https://zenodo.org/records/8224056): procedimientos
- [SympTEMIST](https://zenodo.org/records/10635215): síntomas y signos
- [CodiEsp](https://temu.bsc.es/codiesp/): codificación CIE-10

Como referencias terminológicas se considerarán SNOMED CT y CIE-10-ES, siempre respetando las licencias y condiciones de uso de cada recurso.
- [SNOMED CT](https://www.snomed.org/): terminología clínica que incorpora IANUS
- CIE-10-ES: recursos oficiales del Ministerio de Sanidad
- [HL7 FHIR](https://www.hl7.org/fhir/): formato de salida interoperable
    
La mención de una fuente no implica que todas sus anotaciones sean compatibles entre sí ni que cubran las cuatro clases de entidades.


## Equipo

| Integrante | Rol principal | Correo |
|---|---|---|
| Lucas Amado Oseira | Gestor del proyecto y científico de datos | lucas.amado@rai.usc.es |
| María Lestón Geada | Científica de datos| maria.leston0@rai.usc.es |
| Mariña Vilar Estévez | Portavoz e ingeniera de datos | marina.vilar.estevez@rai.usc.es |
| Mateo Fraguas Abal | Ingeniero de datos | mateo.fraguas@rai.usc.es |

- Contacto de tutoría profesional: **Gema Novo Rego**, DIH DATAlife — ([gema@dihdatalife.com](mailto:gema@dihdatalife.com)).


## Criterios generales de éxito

- El sistema acepta un texto clínico en español y devuelve JSON conforme al esquema documentado.
- La extracción se evalúa con precisión, recall y F1 sobre un conjunto de prueba anotado que no se utilice para entrenar ni ajustar el sistema.
- La normalización se evalúa por separado, informando de la exactitud de los códigos y de la cobertura.
- La salida FHIR se valida contra la versión y los perfiles de FHIR declarados en la implementación; los recursos que no puedan mapearse de forma justificada se informan como no representados, sin inventar datos.
- Los resultados, versiones de datos/modelos, decisiones técnicas y limitaciones quedan documentados.


## Estructura del repositorio

```text
entregas/
└── cu-03-extraccion-clinica/
    ├── README.md
    └── specs/
        ├── evaluacion-resultados.md
        ├── extraccion-entidades.md
        ├── generacion-fhir.md
        ├── generacion-json.md
        └── normalizacion-clinica.md
```

- `README.md`: visión general, motivación, alcance, datos candidatos, equipo y organización del proyecto.
- `specs/evaluacion-resultados.md`: protocolo y métricas para comprobar la calidad del prototipo.
- `specs/extraccion-entidades.md`: comportamiento esperado al detectar y clasificar menciones clínicas.
- `specs/generacion-fhir.md`: conversión del subconjunto acordado de datos a recursos FHIR y validación.
- `specs/generacion-json.md`: contrato de salida JSON, validación y gestión de errores.
- `specs/normalizacion-clinica.md`: reglas para proponer códigos estándar y gestionar casos ambiguos o sin correspondencia.



## Seguridad y limitaciones

- La primera versión trabajará únicamente con corpus públicos autorizados y/o textos sintéticos, sin datos identificables de pacientes, por lo que no habrá un riesgo real de fuga de datos.

- Los resultados son experimentales y no deben interpretarse como información validada para la asistencia sanitaria.

- El sistema debe distinguir entre una entidad detectada, un código propuesto y una entidad que no se ha podido normalizar.

- La conversión a FHIR no implica por sí sola que los datos sean clínicamente correctos ni que el sistema esté listo para integrarse en producción.