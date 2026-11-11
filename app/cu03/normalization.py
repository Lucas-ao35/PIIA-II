"""Normalización conservadora a SNOMED CT (ADR `decisions/normalizacion-conservadora.md`).

Recurso de referencia de la primera versión: los pares (mención, código
SNOMED CT) de las anotaciones gold de entrenamiento de PharmaCoNER. No se usa
similitud textual difusa: solo coincidencia exacta de la forma normalizada
(minúsculas + tokens), por lo que el umbral de confianza aplica a la
consistencia del código observado para esa forma.

Estados (specs/generacion-json.md):
- matched   : la forma tiene un código dominante (cuota >= `min_agreement`).
- ambiguous : la forma se ha visto con varios códigos y ninguno domina.
- not_found : la forma no tiene código en el recurso de referencia.

Sobre `coding.display`: NO se publica la descripción SNOMED CT (licencia,
ver README). Se usa la forma superficial más frecuente en el corpus para ese
código, que procede de PharmaCoNER y no de la terminología.
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path

from .corpus import Document
from .ner import surface_key

SNOMED_SYSTEM = "SNOMED_CT"
MATCHED, NOT_FOUND, AMBIGUOUS = "matched", "not_found", "ambiguous"

"""
Representación del resultado del proceso de normalización para una mención individual.
- status: estado del mapeo (matched, not_found, ambiguous)
- system: sistema de codificación (SNOMED_CT)
- code: código SNOMED CT correspondiente a la mención (si status == matched)
- display: texto representativo del código (si status == matched)
- candidates: lista de códigos candidatos (si status == ambiguous)
- coding(): método que devuelve un diccionario con los campos system, code y display en un diccionario
estructurado listo para ser utilizado en la generación de JSON.
"""
@dataclass
class NormalizationResult:
    status: str
    system: str | None = None
    code: str | None = None
    display: str | None = None
    candidates: list[str] = field(default_factory=list)

    def coding(self) -> dict:
        return {"system": self.system, "code": self.code, "display": self.display}


class DictionaryNormalizer:
    """
    Normalizador basado en las frecuencias observadas en el corpus de entrenamiento.
    """
    name = "dictionary-exact-snomed"

    def __init__(self, min_agreement: float = 0.8):
        self.min_agreement = min_agreement
        self.table: dict[tuple[str, ...], Counter] = {}
        self.display: dict[str, str] = {}

    def fit(self, docs: list[Document]) -> "DictionaryNormalizer":
        """
        Construimos las tablas de mapeo a partir de las anotaciones que poseen código"""
        # Construimos una tabla de frecuencias de códigos SNOMED CT para cada forma superficial (tupla de tokens en minúsculas).
        table: dict[tuple[str, ...], Counter] = defaultdict(Counter)
        names: dict[str, Counter] = defaultdict(Counter)
        for doc in docs:
            for a in doc.annotations:
                if a.code:
                    table[surface_key(a.text)][a.code] += 1
                    names[a.code][a.text] += 1
        self.table = dict(table)
        # Creamos un diccionario de visualización que mapea cada código SNOMED CT a la forma superficial más frecuente observada en el corpus.
        self.display = {c: n.most_common(1)[0][0] for c, n in names.items()}
        return self

    @property
    def known_codes(self) -> set[str]:
        return set(self.display)

    def normalize(self, mention_text: str) -> NormalizationResult:
        """
        Se toma el texto de la mención y se devuelve un objeto NormalizationResult que indica el estado del mapeo
        (matched, not_found, ambiguous)
        """
        codes = self.table.get(surface_key(mention_text))
        if not codes:
            return NormalizationResult(NOT_FOUND)
        (top, n), total = codes.most_common(1)[0], sum(codes.values())
        if n / total >= self.min_agreement:
            return NormalizationResult(MATCHED, SNOMED_SYSTEM, top, self.display.get(top))
        return NormalizationResult(AMBIGUOUS, candidates=[c for c, _ in codes.most_common()])

    # ------------------------------------------------------- persistencia
    # Permite guardar el estado del normalizador entrenado con sus reglas y parámetros en un fichero JSON con save() y
    # reconstruimos el normalizador con load() a partir de ese fichero. Esto permite reproducir resultados y compartir modelos.
    def config(self) -> dict:
        return {"name": self.name, "min_agreement": self.min_agreement,
                "surface_forms": len(self.table), "codes": len(self.display)}

    def to_dict(self) -> dict:
        return {"config": self.config(),
                "table": [{"key": list(k), "codes": dict(v)} for k, v in self.table.items()],
                "display": self.display}

    @classmethod
    def from_dict(cls, data: dict) -> "DictionaryNormalizer":
        norm = cls(data["config"]["min_agreement"])
        norm.table = {tuple(e["key"]): Counter(e["codes"]) for e in data["table"]}
        norm.display = dict(data["display"])
        return norm

    def save(self, path: Path) -> None:
        Path(path).write_text(json.dumps(self.to_dict(), ensure_ascii=False), encoding="utf-8")

    @classmethod
    def load(cls, path: Path) -> "DictionaryNormalizer":
        return cls.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))
