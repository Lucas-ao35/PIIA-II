# Spec: extracción de entidades clínicas

## 1. Propósito

Detectar en textos clínicos en español menciones de enfermedades, síntomas/signos, fármacos y procedimientos, y asignar una categoría a cada mención. Esta funcionalidad es la primera etapa del flujo: sus resultados alimentan la normalización y las salidas JSON y FHIR.

## 2. Problema e intención

La información clínica expresada en texto libre no puede analizarse de forma homogénea sin identificar primero qué conceptos aparecen y dónde. La extracción convierte menciones textuales en unidades explícitas y mantiene su vínculo con el texto de origen para facilitar la revisión y la evaluación.

## 3. Qué construir

Un componente que reciba un texto en español y devuelva una lista de menciones detectadas. Para cada mención incluirá, como mínimo:
- `text`: fragmento literal del texto de entrada;
- `type`: uno de `disease`, `symptom`, `drug` o `procedure`;
- `start` y `end`: posiciones de inicio y fin en el texto original, usando índices de caracteres con inicio inclusivo y fin exclusivo.

La información contextual adicional, como negación o temporalidad, queda fuera de la primera versión salvo que el equipo la incorpore expresamente y disponga de datos adecuados para evaluarla.

## 4. Restricciones y supuestos

- La entrada será texto en español procedente de corpus públicos permitidos o ejemplos sintéticos.
- Antes de usar un corpus, se documentará el mapeo de sus etiquetas a las cuatro categorías del proyecto.
- Los límites de cada mención deben corresponder al texto original, incluidos acentos y signos que formen parte de ella.
- Las menciones solapadas solo se conservarán si el esquema de anotación elegido las permite; la política se documentará.
- No se procesarán historias clínicas reales ni se utilizarán los resultados para diagnosticar.
- El enfoque técnico está por decidir. Si se usa un modelo preentrenado, se registrarán su nombre, versión y licencia.

## 5. Criterios de aceptación

1. Dado un texto no vacío, el componente devuelve entidades con `text`, `type`, `start` y `end`.
2. Para cada entidad, `text` coincide exactamente con `input[start:end]`.
3. Todos los valores de `type` pertenecen al conjunto `disease`, `symptom`, `drug`, `procedure`.
4. Ante una entrada vacía o formada solo por espacios, devuelve una lista vacía o un error de validación documentado; el comportamiento será consistente.
5. En el conjunto de prueba anotado, se informan precisión, recall y F1 por categoría y globales, con coincidencia exacta de límites y categoría. El objetivo inicial es F1 micro global ≥ 0,75; si el corpus no permite una comparación válida, se documentará y se propondrá una alternativa antes de evaluar.
6. La partición de prueba no se utiliza para entrenar ni seleccionar hiperparámetros.
7. La documentación identifica corpus, versión, mapeo de etiquetas y limitaciones conocidas.

## 6. Fuera de alcance

- Inferir enfermedades no mencionadas explícitamente.
- Resolver completamente negación, temporalidad, antecedentes familiares o relaciones clínicas.
- Asignar códigos SNOMED CT o CIE-10-ES, tarea definida en `normalizacion-clinica.md`.
