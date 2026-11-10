"""Cargador del corpus PharmaCoNER en formato BRAT.

Es el único módulo que conoce el formato físico del corpus (ver ADR
`decisions/corpus-pharmaconer-brat.md`). El resto del pipeline trabaja con
`Document` y `Annotation`.

Decisiones relevantes:
- El texto se lee con `newline=""` para NO normalizar saltos de línea: los
  offsets BRAT son índices de caracteres sobre el fichero original.
- Si el texto de una anotación no coincide con `text[start:end]` (ocurre en
  el gold oficial, p. ej. S0211-69952015000200015-1 en train), se busca la
  ocurrencia más cercana en una ventana pequeña y se registra la reparación.
  Si no se encuentra, la anotación se descarta y se registra también.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

log = logging.getLogger(__name__)

CORPUS_NAME = "PharmaCoNER"
CORPUS_VERSION = "1.1"

# Particiones oficiales -> ruta relativa dentro del corpus.
SPLITS = {
    "train": Path("train-set_1.1") / "train" / "subtrack1",
    "dev": Path("dev-set_1.1") / "dev" / "subtrack1",
    "test": Path("test-set_1.1") / "test" / "subtrack1",
}

# Mapeo documentado de etiquetas PharmaCoNER -> categorías del proyecto
# (`type` en specs/generacion-json.md). `None` = fuera de las categorías del
# esquema 1.0: se evalúan con etiqueta nativa pero no se emiten en el JSON.
LABEL_TO_TYPE: dict[str, str | None] = {
    "NORMALIZABLES": "drug",
    "NO_NORMALIZABLES": "drug",
    "PROTEINAS": None,
    "UNCLEAR": None,
}

NULL_CODES = {"", "<null>", "null", "NONE"}
REPAIR_WINDOW = 10


@dataclass(frozen=True)
class Annotation:
    id: str
    label: str
    start: int
    end: int
    text: str
    code: str | None = None


@dataclass
class Document:
    id: str
    split: str
    text: str
    annotations: list[Annotation] = field(default_factory=list)
    repaired: list[str] = field(default_factory=list)
    dropped: list[str] = field(default_factory=list)


def _read(path: Path) -> str:
    with open(path, encoding="utf-8-sig", newline="") as fh:
        return fh.read()


def _repair_offsets(text: str, mention: str, start: int, end: int) -> tuple[int, int] | None:
    lo = max(0, start - REPAIR_WINDOW)
    hi = min(len(text), end + REPAIR_WINDOW)
    best = None
    idx = text.find(mention, lo, hi)
    while idx != -1:
        if best is None or abs(idx - start) < abs(best - start):
            best = idx
        idx = text.find(mention, idx + 1, hi)
    return (best, best + len(mention)) if best is not None else None


def parse_brat(ann_path: Path, txt_path: Path, split: str = "unknown") -> Document:
    """Parsea un par .ann/.txt y devuelve un `Document` con offsets verificados."""
    text = _read(txt_path)
    lines = _read(ann_path).splitlines() if ann_path.exists() else []
    doc = Document(id=txt_path.stem, split=split, text=text)

    notes: dict[str, str] = {}
    for line in lines:
        if line.startswith("#"):
            parts = line.split("\t")
            if len(parts) >= 3 and len(parts[1].split()) == 2:
                notes[parts[1].split()[1]] = parts[2].strip()

    for line in lines:
        if not line.startswith("T"):
            continue
        parts = line.split("\t")
        if len(parts) < 3:
            continue
        tid, meta, mention = parts[0], parts[1], parts[2]
        if ";" in meta:  # entidades discontinuas: no existen en PharmaCoNER 1.1
            doc.dropped.append(f"{tid}: discontinua")
            continue
        label, start, end = meta.split()[0], int(meta.split()[1]), int(meta.split()[-1])
        if text[start:end] != mention:
            fixed = _repair_offsets(text, mention, start, end)
            if fixed is None:
                doc.dropped.append(f"{tid}: '{mention}' no encontrado cerca de {start}")
                continue
            doc.repaired.append(f"{tid}: {start}-{end} -> {fixed[0]}-{fixed[1]}")
            start, end = fixed
        code = notes.get(tid)
        code = None if code is None or code in NULL_CODES else code
        doc.annotations.append(Annotation(tid, label, start, end, mention, code))

    doc.annotations.sort(key=lambda a: (a.start, -(a.end - a.start)))
    if doc.repaired or doc.dropped:
        log.warning("%s: %d offsets reparados, %d anotaciones descartadas",
                    doc.id, len(doc.repaired), len(doc.dropped))
    return doc


def find_data_dir(project_root: Path | None = None) -> Path:
    """Localiza la carpeta del corpus descargado por scripts/download_datasets.py."""
    root = project_root or Path(__file__).resolve().parent.parent
    candidates = [
        root / "data" / "pharmaconer" / "pharmaconer",
        root / "data" / "pharmaconer",
        Path("data/pharmaconer/pharmaconer").resolve(),
        Path("data/pharmaconer").resolve(),
    ]
    for c in candidates:
        if (c / "train-set_1.1").exists():
            return c
    return candidates[0]


def load_split(split: str, data_dir: Path | None = None) -> list[Document]:
    if split not in SPLITS:
        raise ValueError(f"Partición desconocida: {split!r}. Válidas: {sorted(SPLITS)}")
    base = (data_dir or find_data_dir()) / SPLITS[split]
    if not base.exists():
        raise FileNotFoundError(
            f"No existe {base}. Descarga el corpus con: python scripts/download_datasets.py"
        )
    return [parse_brat(ann, ann.with_suffix(".txt"), split) for ann in sorted(base.glob("*.ann"))]


def load_splits(splits, data_dir: Path | None = None) -> list[Document]:
    docs: list[Document] = []
    for s in splits:
        docs.extend(load_split(s, data_dir))
    return docs
