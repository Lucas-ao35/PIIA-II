"""Orquestación del camino crítico: texto -> NER -> normalización -> JSON canónico.

Cada etapa intercambia estructuras simples y el resultado final se valida
contra el contrato antes de devolverse (ADR `decisions/pipeline-json-canonico.md`).
"""

from __future__ import annotations

import json
from pathlib import Path

from .corpus import LABEL_TO_TYPE, Document, load_splits
from .ner import GazetteerNER, Mention
from .normalization import DictionaryNormalizer, NormalizationResult
from .schema import SCHEMA_VERSION, validate_document



# ----------------------------------------------------------------- gestión de errores de entrada
class InvalidInputError(ValueError):
    """Entrada no procesable (tipo incorrecto o bytes no UTF-8). Código: CU03-E001."""

    code = "CU03-E001"


def _coerce_text(text) -> str:
    # Validamos y normalizamos un tipo de dato antes de procesarlo.
    if isinstance(text, bytes):
        # Intentamos decodificar bytes a str usando UTF-8. Si falla, lanzamos InvalidInputError
        try:
            return text.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise InvalidInputError(f"[{InvalidInputError.code}] la entrada no es UTF-8 válido") from exc
    # Si el dato de entrada no es str ni bytes, lanzamos InvalidInputError
    if not isinstance(text, str):
        raise InvalidInputError(f"[{InvalidInputError.code}] se esperaba str, recibido {type(text).__name__}")
    return text


class Pipeline:
    """
    Clase principal que coordina los componentes de GazetteerNER y DictionaryNormalizer.
    """
    def __init__(self, ner: GazetteerNER, normalizer: DictionaryNormalizer,
                 label_to_type: dict[str, str | None] | None = None):
        self.ner = ner
        self.normalizer = normalizer
        self.label_to_type = dict(LABEL_TO_TYPE if label_to_type is None else label_to_type)

    # ------------------------------------------------------------ factoría
    @classmethod
    def train(cls, docs: list[Document], min_precision: float = 0.5,
              min_agreement: float = 0.8) -> "Pipeline":
        # Ajusta el extractor NER y el normalizador utilizando la lista de documentos de entrenamiento
        return cls(GazetteerNER(min_precision=min_precision).fit(docs),
                   DictionaryNormalizer(min_agreement=min_agreement).fit(docs))

    @classmethod
    def from_corpus(cls, splits=("train",), data_dir: Path | None = None, **kw) -> "Pipeline":
        # Cargamos los splits especificados del corpus e invocamos a train().
        # Si no existe el corpus, inicializamos un pipeline vacío para poder
        # procesar textos de ejemplo sin romper la ejecución en entornos sin datos.
        try:
            return cls.train(load_splits(splits, data_dir), **kw)
        except FileNotFoundError:
            return cls.train([], **kw)

    def save(self, model_dir: Path) -> None:
        # Creamos el directorio de salida si no existe y guardamos el modelo NER y normalizar en formato JSON
        model_dir = Path(model_dir)
        model_dir.mkdir(parents=True, exist_ok=True)
        self.ner.save(model_dir / "ner.json")
        self.normalizer.save(model_dir / "normalizer.json")

    @classmethod
    def load(cls, model_dir: Path) -> "Pipeline":
        # Cargamos el modelo NER y normalizador desde los ficheros JSON en el directorio especificado
        model_dir = Path(model_dir)
        return cls(GazetteerNER.load(model_dir / "ner.json"),
                   DictionaryNormalizer.load(model_dir / "normalizer.json"))

    # ------------------------------------------------------------ etapas
    def extract(self, text: str) -> list[Mention]:
        # Pasamos el texto validado por el modelo NER para detectar las entidades
        return self.ner.predict(_coerce_text(text))

    def normalize(self, mentions: list[Mention]) -> list[NormalizationResult]:
        # Iteramos sobre la lista de menciones extraídas y obtiene el resultado de la normalización
        # de términos para cada un de ellas.
        return [self.normalizer.normalize(m.text) for m in mentions]

    def build_document(self, text: str, mentions: list[Mention],
                       results: list[NormalizationResult],
                       document_id: str | None = None) -> dict:
        entities = []
        # Relacionamos cada mención con su resultado de normalización
        for m, r in zip(mentions, results):
            # Mapeamos la etiqueta nativa a la categoría requerida por el esquema con label_to_type
            # Si la etiqueta no está en el diccionario se descarta
            etype = self.label_to_type.get(m.label)
            if etype is None:  # etiqueta fuera de las categorías del esquema 1.0
                continue
            entities.append({
                "text": m.text, "type": etype, "start": m.start, "end": m.end,
                "confidence": m.score,
                "coding": r.coding(), "normalization_status": r.status,
            })
        # Política de orden: por inicio; con el mismo inicio, la más larga primero.
        entities.sort(key=lambda e: (e["start"], -(e["end"] - e["start"])))
        # Construcción de la estrucutra completa del documento
        doc = {"schema_version": SCHEMA_VERSION, "document_id": document_id,
               "language": "es", "source_text": text, "entities": entities}
        validate_document(doc)
        return doc

    def process(self, text, document_id: str | None = None) -> dict:
        """Texto clínico -> JSON canónico validado.

        Texto vacío o solo espacios -> documento válido con `entities: []`.
        Tipo incorrecto o bytes no UTF-8 -> `InvalidInputError` (CU03-E001).
        """
        text = _coerce_text(text)
        mentions = self.ner.predict(text)
        return self.build_document(text, mentions, self.normalize(mentions), document_id)

    def process_json(self, text, document_id: str | None = None, indent: int | None = 2) -> str:
        # Mismo que process() pero devuelve un JSON canónico en formato string, listo para ser guardado en un fichero
        return json.dumps(self.process(text, document_id), ensure_ascii=False, indent=indent)

    def config(self) -> dict:
        # Devuelve la configuración técnia de todas las etapas
        return {"ner": self.ner.config(), "normalizer": self.normalizer.config(),
                "label_to_type": self.label_to_type, "schema_version": SCHEMA_VERSION}
