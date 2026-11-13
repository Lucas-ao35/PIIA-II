# CU-03 — Extracción y estructuración de información clínica en español mediante PLN

## ¿Qué es este proyecto?

Este repositorio desarrolla un prototipo de procesamiento del lenguaje natural para textos clínicos en español. La idea principal es transformar un texto clínico libre en datos estructurados, evaluables y reutilizables en distintos flujos de análisis.

El proyecto aborda tres piezas clave del caso de uso:

1. detectar entidades clínicas relevantes en texto libre,
2. normalizarlas a terminologías de referencia cuando existe una correspondencia defendible,
3. generar una salida estructurada en JSON y una representación inicial compatible con HL7 FHIR.

La solución se diseña como un pipeline modular con etapas claramente diferenciadas: ingest del corpus, extracción, normalización, validación JSON, evaluación y visualización.

La arquitectura general se describe en [ARCHITECTURE.md](ARCHITECTURE.md), y las decisiones de implementación se documentan en [decisions](decisions/). La parte funcional del proyecto está implementada dentro de [app](app/), con una guía operativa específica en [app/README.md](app/README.md).

---

## Motivación y objetivos

Como equipo, este caso nos ha llamado la atención por conectar con la inteligencia artificial y el PLN con una necesidad real concreta del ámbito sanitario. Responde al problema de que parte de la información clínica está en texto libre y resulta difícil de consultar y reutilizar. Este proyecto permite estudiar, de forma reproducible, las etapas necesarias para pasar de una frase clínica a un registro que pueda ser procesado por una base de datos.

En la primera reunión se nos recomendó comenzar por el tratamiento de fármacos, mas el equipo prevé una posible ampliación posterior del reconocimiento a enfermedades, síntomas/signos y procedimientos. El SERGAS aborda una necesidad relacionada mediante IANUS, que organiza la información por problemas de salud. Además, los corpus clínicos en español publicados para investigación permiten definir una evaluación sin usar historias clínicas reales.

El objetivo del proyecto es especificar y evidenciar, con una implementación funcional mínima viable, un pipeline que:

1. Reciba textos clínicos en español.
2. Detecte y clasifique entidades clínicas previstas.
3. Normalice las entidades cuando haya una correspondencia defendible en la terminología de referencia.
4. Genere una salida JSON validable.
5. Convierta a recursos FHIR un subconjunto definido de la información estructurada.
6. Permita evaluar sus resultados frente a corpus anotados y validar técnicamente las salidas mediante métricas estándar.

La primera fase de implementación priorizará fármacos con PharmaCoNER. La incorporación de enfermedades, síntomas/signos y procedimientos queda prevista como ampliación, sujeta a comprobar la compatibilidad y disponibilidad de sus corpus.

### Camino crítico y prioridades

El camino óptimo es: **fármacos → detección → normalización → JSON → métricas**. Como la normalización es la parte de mayor riesgo se abordará pronto, priorizando una normalización sencilla y funcional, antes que una buena salida FHIR que carezca de normalización. Tanto esta como las entidades adicionales serían posibles ampliaciones.

El enfoque técnico (modelos preentrenados, reglas, ajuste de modelos o comparación de alternativas) queda por decidir. La decisión se tomará tras inspeccionar los corpus, sus anotaciones, las licencias y los recursos disponibles, y se documentará antes de la implementación.


## Alcance

### Incluido en el proyecto

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

- Abordaje del resto de entidades (enfermedades, síntomas/signos y procedimientos).
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
| María Lestón Geada | Científica de datos | maria.leston0@rai.usc.es |
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
PIIA-II/
├── README.md                     # documentación general del proyecto
├── ARCHITECTURE.md               # arquitectura y flujo del sistema
├── decisions/                    # ADRs con decisiones de implementación
├── specs/                        # especificaciones funcionales
├── app/                          # implementación del pipeline
│   ├── README.md                 # guía de uso y puesta en marcha
│   ├── app.py                    # visualizador Streamlit
│   ├── cu03/                     # módulo principal del pipeline
│   ├── scripts/                  # ejecutables del proyecto
│   ├── tests/                    # pruebas funcionales
│   └── schemas/                  # JSON Schema
├── entregas/                     # copia de entrega formal
└── ...
```

Documentación principal:

- [README.md](README.md): visión general del caso de uso, motivación, alcance y estructura del repositorio.
- [ARCHITECTURE.md](ARCHITECTURE.md): componentes del sistema, flujo de datos y diseño global.
- [decisions](decisions/): decisiones de implementación con contexto, alternativas y consecuencias.
- [specs](specs/): requisitos funcionales de extracción, normalización, JSON y evaluación.
- [app/README.md](app/README.md): guía operativa del sistema y ejecución con uv.

---

## Coherencia entre la especificación y la implementación

La documentación técnica del proyecto está alineada con el código real y con la estructura del repositorio:

- [specs/extraccion-entidades.md](specs/extraccion-entidades.md) → [app/cu03/ner.py](app/cu03/ner.py)
  - la extracción se implementa como NER basado en diccionario y reglas, con validación de offsets y tipos.
- [specs/normalizacion-clinica.md](specs/normalizacion-clinica.md) → [app/cu03/normalization.py](app/cu03/normalization.py)
  - la normalización conserva estados explícitos y evita asignar código cuando la correspondencia no es inequívoca.
- [specs/generacion-json.md](specs/generacion-json.md) → [app/cu03/schema.py](app/cu03/schema.py) y [app/cu03/pipeline.py](app/cu03/pipeline.py)
  - el JSON canónico es el contrato de salida y se valida estrictamente antes de aceptar la salida del pipeline.
- [specs/evaluacion-resultados.md](specs/evaluacion-resultados.md) → [app/cu03/evaluation.py](app/cu03/evaluation.py) y [app/scripts/evaluate.py](app/scripts/evaluate.py)
  - la evaluación computa métricas de extracción, normalización y validez de salida.
- [specs/generacion-fhir.md](specs/generacion-fhir.md) → pendiente como ampliación
  - la conversión a FHIR queda documentada como etapa posterior al camino crítico, sin inventar datos no representables.

La coherencia general del repositorio es buena: la arquitectura, las ADRs, las specs y el código funcional se apoyan entre sí y no contradicen el caso de uso del proyecto.

---

## Estado actual del proyecto

El proyecto ya cuenta con una implementación funcional del pipeline en la carpeta [app](app/): carga de corpus, extracción de entidades, normalización conservadora, validación JSON, evaluación y ejecución local.

La construcción del sistema sigue la lógica de trabajo propuesta en la arquitectura: la lógica está dividida por etapas y cada módulo tiene una responsabilidad clara.

El entorno de ejecución se recomienda con `uv`, de acuerdo con la configuración del proyecto.

---

## Criterios de éxito

Se considera que el proyecto avanza correctamente cuando:

- acepta textos clínicos en español,
- detecta entidades relevantes,
- normaliza conceptos de forma defendible,
- genera un JSON validable,
- evalúa sus resultados con métricas reproducibles,
- mantiene la documentación alineada con el código real.

---

## Seguridad, ética y limitaciones

- La primera versión trabajará únicamente con corpus públicos autorizados y/o textos sintéticos, sin datos identificables de pacientes, por lo que no habrá un riesgo real de fuga de datos.

- Los resultados son experimentales y no deben interpretarse como información validada para la asistencia sanitaria.

- El sistema debe distinguir entre una entidad detectada, un código propuesto y una entidad que no se ha podido normalizar.

- SNOMED CT requiere licencia de afiliado (en España, cubierta por la licencia nacional del Ministerio de Sanidad). Antes de publicar mapeos en un repositorio abierto se confirmarán las condiciones de licencia y no se redistribuirán descripciones ni partes de la terminología hasta entonces.

- La conversión a FHIR no implica por sí sola que los datos sean clínicamente correctos ni que el sistema esté listo para integrarse en producción.