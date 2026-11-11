"""Extracción de entidades (NER) — baseline de diccionario aprendido del corpus.

Primer enfoque del camino crítico: un *gazetteer* construido a partir de las
menciones gold de las particiones de entrenamiento, con emparejamiento greedy
por la mención más larga sobre tokens y un filtro de precisión estimado en el
propio entrenamiento. Sirve como línea base reproducible frente a la que
comparar un modelo transformer (ver ADR de modelo NER cuando se decida).

Garantías (specs/extraccion-entidades.md):
- El texto de entrada nunca se modifica; `text == input[start:end]` siempre.
- `start` inclusivo, `end` exclusivo, índices de carácter.
- No hay solapamientos entre menciones predichas.
"""

from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path

from .corpus import Document

# Emplemaos una expresión regular para dividir el texto en palabras o signos de puntuación independientes.
TOKEN_RE = re.compile(r"\w+|[^\w\s]", re.UNICODE)


"""
Representa una entidad detectada en el texto con su fragmento (text), categoria, posiciones inicio/fin
y un nivel de confianza (score correspondiente con la precisión estimada).
"""
@dataclass(frozen=True)
class Mention:
    text: str
    label: str
    start: int
    end: int
    score: float | None = None


# Retorna una lista de tuplas (token, start, end) para cada token en el texto.
def tokenize(text: str) -> list[tuple[str, int, int]]:
    return [(m.group().lower(), m.start(), m.end()) for m in TOKEN_RE.finditer(text)]



# Convertimos cualquier cadena de texto en una tupla de strings en minúsculas.
# Por ejemplo: "Ácido Acetilsalicílico" -> ("ácido", "acetilsalicílico")
def surface_key(text: str) -> tuple[str, ...]:
    return tuple(t for t, _, _ in tokenize(text))


class GazetteerNER:
    """NER por diccionario con filtro de precisión.

    Parámetros:
        min_precision: proporción mínima (anotada / total de apariciones en
            entrenamiento) para conservar una forma. Controla el balance P/R.
        min_count: número mínimo de veces anotada en entrenamiento.
    """

    name = "gazetteer-baseline"

    def __init__(self, min_precision: float = 0.5, min_count: int = 1):
        self.min_precision = min_precision
        self.min_count = min_count
        self.entries: dict[tuple[str, ...], dict] = {}
        self.max_len = 0

    # ------------------------------------------------------------------ fit
    def fit(self, docs: list[Document]) -> "GazetteerNER":
        labels: dict[tuple[str, ...], Counter] = defaultdict(Counter)
        # Iteramos sobre cada documento anotado y contamos el número de veces que aparece
        # cada tupla de tokens asociada a una etiqueta. 
        for doc in docs:
            for a in doc.annotations:
                key = surface_key(a.text)
                if key:
                    labels[key][a.label] += 1

        # Cuántas veces aparece cada forma en el texto de entrenamiento,
        # esté anotada o no -> precisión estimada de la forma.
        self.entries = {k: {"labels": dict(v), "seen": 0} for k, v in labels.items()}
        self.max_len = max((len(k) for k in self.entries), default=0)
        for doc in docs:
            for key, _, _ in self._raw_matches(doc.text, greedy=False):
                self.entries[key]["seen"] += 1

        # Filtro de precisión: calculamos la precisión estimada e cada forma textual
        # precisión = veces anotada/ max(veces vista, veces anotada)
        # Conservamos las entradas que superen los umbrales de min_count y min_precision,
        # en caso de que una palabra esté asociada a varias etiquetas, nos quedamos con la más frecuente.
        kept = {}
        for key, e in self.entries.items():
            annotated = sum(e["labels"].values())
            precision = annotated / max(e["seen"], annotated)
            if annotated >= self.min_count and precision >= self.min_precision:
                label = Counter(e["labels"]).most_common(1)[0][0]
                kept[key] = {"label": label, "precision": round(precision, 4),
                             "labels": e["labels"], "seen": e["seen"]}
        self.entries = kept
        self.max_len = max((len(k) for k in self.entries), default=0)
        return self

    # -------------------------------------------------------------- predict
    def _raw_matches(self, text: str, greedy: bool = True):
        """
        Recorremos los tokens del texto de entrada y hacemos una búsqueda de secuencias que coincidan con
        las claves aprendidas. 
        Para la Búsqueda Greedy, evaluaremos subcadenas desde la longitud máxima aprendida max_len hasta 1.
        Al encontrar la coincidencia más larga se emite yield y avanza la posición la posición saltando
        los tokens consumidos (i += matched) para evitar solapamientos."""
        toks = tokenize(text)
        i = 0
        while i < len(toks):
            matched = 0
            for n in range(min(self.max_len, len(toks) - i), 0, -1):
                key = tuple(t for t, _, _ in toks[i:i + n])
                if key in self.entries:
                    yield key, toks[i][1], toks[i + n - 1][2]
                    matched = n
                    break
            i += matched if (greedy and matched) else 1

    def predict(self, text: str) -> list[Mention]:
        """
        Recibimos una cadena de texto y generamos una lista de objetos Mention con las entidades detectadas.
        """
        if not isinstance(text, str):
            raise TypeError("El texto de entrada debe ser str")
        out = []
        for key, s, e in self._raw_matches(text): # Usamos _raw_matches para obtener los rangos de caracteres
            # Extraemos el texto exacto del original con text[s:e], garantizando un texto de entrado que no se modifique
            # y que los offsets coincidan
            entry = self.entries[key]
            out.append(Mention(text[s:e], entry["label"], s, e, entry["precision"]))
        return out

    # ------------------------------------------------------- persistencia
    # Permitimos guardar el estado del modelo entrenado con sus reglas y parámetros en un fichero JSON con save() y
    # reconstruimos el modelo con load() a partir de ese fichero. Esto permite reproducir resultados y compartir modelos.
    def config(self) -> dict:
        return {"name": self.name, "min_precision": self.min_precision,
                "min_count": self.min_count, "entries": len(self.entries)}

    def to_dict(self) -> dict:
        return {"config": self.config(),
                "entries": [{"key": list(k), **v} for k, v in self.entries.items()]}

    @classmethod
    def from_dict(cls, data: dict) -> "GazetteerNER":
        cfg = data["config"]
        ner = cls(cfg["min_precision"], cfg["min_count"])
        ner.entries = {tuple(e.pop("key")): e for e in (dict(x) for x in data["entries"])}
        ner.max_len = max((len(k) for k in ner.entries), default=0)
        return ner

    def save(self, path: Path) -> None:
        Path(path).write_text(json.dumps(self.to_dict(), ensure_ascii=False), encoding="utf-8")

    @classmethod
    def load(cls, path: Path) -> "GazetteerNER":
        return cls.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))


def mention_dict(m: Mention) -> dict: # Función simple que convierte la instancia de Mention en un diccionarion de Python
    return asdict(m)
