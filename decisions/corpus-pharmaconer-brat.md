# ADR: Corpus inicial PharmaCoNER en formato BRAT, con los fármacos como camino crítico

## Estado

Aceptada

## Contexto

El proyecto necesita, desde el primer día, textos clínicos en español con anotaciones de referencia (gold) que permitan tanto entrenar y ajustar el sistema como evaluarlo con precisión, recall y F1 sobre datos que no se hayan usado para desarrollar. Las restricciones del proyecto descartan cualquier historia clínica real: solo valen corpus públicos con condiciones de uso compatibles. En la reunión inicial con el tutor se recomendó además comenzar por fármacos, y el SERGAS (referente asistencial vía IANUS) trabaja con SNOMED CT, lo que condiciona la terminología de destino.

## Decisión

Usar **PharmaCoNER 1.1, subtrack 1** (detección de menciones de fármacos y proteínas) como corpus inicial del proyecto, en su distribución original en **formato BRAT** (pares `.txt` + `.ann`), consumido por un cargador propio que parsea las anotaciones y las expone con sus offsets de caracteres y códigos SNOMED CT gold. La prioridad de implementación es el camino crítico **fármacos → detección → normalización → JSON → métricas**; las demás entidades (enfermedades, síntomas, procedimientos) quedan como ampliación con DisTEMIST, SympTEMIST y MedProcNER tras comprobar compatibilidad de etiquetas.

## Motivación

- Es un corpus clínico en **español** con anotación gold de menciones, publicado para investigación (plantrack/BioNLP), lo que permite una evaluación honesta sin tocar datos de pacientes.
- Incluye ya la **normalización a SNOMED CT** (subtrack 2), de modo que las menciones gold llevan código: se pueden evaluar extracción y normalización por separado sobre el mismo recurso.
- Tiene **particiones oficiales train / dev / test**, lo que encaja con el requisito de que el conjunto de prueba no se use para entrenar ni ajustar.
- El formato BRAT es texto plano y autoexplicativo: una anotación por línea con tipo y offsets, sin infraestructura de carga pesada.
- Su temática (fármacos) coincide con la recomendación recibida y con la terminología (SNOMED CT) que usa el referente asistencial.

## Alternativas consideradas

- **DisTEMIST / SympTEMIST / MedProcNER desde el inicio**: cubren las cuatro categorías del proyecto, pero multiplican el trabajo de mapeo de etiquetas y de verificación de compatibilidad antes de tener nada funcionando de punta a punta. Se descartaron como punto de partida y quedan como ampliación prevista.
- **CodiEsp**: corpus en español con códigos CIE-10, pero su tarea es codificación de documento completo, no detección de menciones con offsets; no encaja con la separación extracción/normalización que queremos evaluar.
- **Solo textos sintéticos**: sin coste de licencias y sin datos personales, pero sin anotación gold externa la evaluación sería circular (validaríamos contra nosotros mismos). Se usan solo como casos de prueba auxiliares.
- **Historias clínicas reales**: fuera de alcance por seguridad y privacidad desde la Entrega 1.

## Consecuencias

- La primera versión del sistema se centra en fármacos y proteínas; las demás categorías no tendrán código hasta que se incorporen sus corpus.
- El cargador BRAT (`dataloaders`) queda como única pieza que conoce el formato físico; añadir un corpus nuevo es añadir un parser, no tocar el pipeline.
- Las etiquetas de PharmaCoNER (`NORMALIZABLES`, `PROTEINAS`, `UNCLEAR`, `NO_NORMALIZABLES`) deben mapearse a las categorías del proyecto y ese mapeo debe documentarse.

## Referencias

- Dataset en Hugging Face: [PlanTL-GOB-ES/pharmaconer](https://huggingface.co/datasets/PlanTL-GOB-ES/pharmaconer)
- Artículo del task: *Pharmaceutical named entity recognition, drug normalization and adverse drug event extraction: overview of the PharmaCoNER task* — [ACL Anthology D19-5701](https://aclanthology.org/D19-5701/)
- Corpus base SPACCC del que deriva PharmaCoNER: [github.com/PlanTL-GOB-ES/SPACCC](https://github.com/PlanTL-GOB-ES/SPACCC)
- Repositorio de corpus clínicos en español: [TeMU-BSC](https://temu.bsc.es/)
- Formato BRAT: [brat.nlplab.org/standoff.html](https://brat.nlplab.org/standoff.html)

Ejemplo de anotación BRAT que el cargador parsea (mención con código SNOMED CT gold):

```text
T1  NORMALIZABLES 234 240  aspirina
#1  AnnotatorNotes T1  11978004
```

donde `11978004` es el identificador SNOMED CT de la mención `T1`.
