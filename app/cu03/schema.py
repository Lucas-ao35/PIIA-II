"""Contrato JSON canónico (specs/generacion-json.md, schema_version 1.0).

Dos niveles de validación:
1. `JSON_SCHEMA` (Draft 2020-12): estructura, tipos y valores permitidos.
2. `semantic_errors`: reglas que JSON Schema no puede expresar
   (offsets dentro del texto, `source_text[start:end] == text`, orden,
   coherencia entre `normalization_status` y `coding`).
"""

from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator

SCHEMA_VERSION = "1.0"
ENTITY_TYPES = ("disease", "symptom", "drug", "procedure")
NORMALIZATION_STATUSES = ("matched", "not_found", "ambiguous")

_nullable_str = {"type": ["string", "null"]}

JSON_SCHEMA: dict = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "https://github.com/cu-03-extraccion-clinica/schema/1.0/document.json",
    "title": "Documento clínico estructurado CU-03",
    "type": "object",
    "required": ["schema_version", "language", "source_text", "entities"],
    "properties": {
        "schema_version": {"const": SCHEMA_VERSION},
        "document_id": {"type": ["string", "null"]},
        "language": {"const": "es"},
        "source_text": {"type": "string"},
        "entities": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["text", "type", "start", "end", "coding", "normalization_status"],
                "properties": {
                    "text": {"type": "string", "minLength": 1},
                    "type": {"enum": list(ENTITY_TYPES)},
                    "start": {"type": "integer", "minimum": 0},
                    "end": {"type": "integer", "minimum": 1},
                    "confidence": {"type": ["number", "null"], "minimum": 0, "maximum": 1},
                    "coding": {
                        "type": "object",
                        "required": ["system", "code", "display"],
                        "properties": {"system": _nullable_str, "code": _nullable_str,
                                       "display": _nullable_str},
                        "additionalProperties": False,
                    },
                    "normalization_status": {"enum": list(NORMALIZATION_STATUSES)},
                },
                "additionalProperties": False,
            },
        },
    },
    "additionalProperties": False,
}

_validator = Draft202012Validator(JSON_SCHEMA)

# ----------------------------------------------------------------- funciones de validación
class SchemaValidationError(ValueError):
    """La salida no cumple el contrato JSON canónico."""

    def __init__(self, errors: list[str]):
        super().__init__("; ".join(errors))
        self.errors = errors


def schema_errors(doc: dict) -> list[str]:
    # Validación declarativa de JSON Schema mediante _validator.iter_errors(doc)
    # Devuelve una lista con la ruta en formato JSON Pointer y el mensaje de error.
    return [f"{'/'.join(map(str, e.absolute_path)) or '<root>'}: {e.message}"
            for e in sorted(_validator.iter_errors(doc), key=lambda e: list(e.absolute_path))]


def semantic_errors(doc: dict) -> list[str]:
    errors: list[str] = []
    # Validación semántica
    # Comprueba las regals dinámicas de integridad refrencia y de negocio de un esquema estático
    text = doc.get("source_text", "")
    prev = None
    for i, ent in enumerate(doc.get("entities", [])):
        s, e = ent.get("start"), ent.get("end")
        # Verificamos rango de offsets válido
        if not (isinstance(s, int) and isinstance(e, int) and 0 <= s < e <= len(text)):
            errors.append(f"entities/{i}: intervalo inválido [{s}, {e})")
            continue
        # Revisamos que le fragmento recortado sea igual al campo text de su entidad
        if text[s:e] != ent.get("text"):
            errors.append(f"entities/{i}: source_text[{s}:{e}] != text")
        # Verificamos que las entidades estén ordenadas por inicio y, en caso de empate, por longitud decreciente
        key = (s, -(e - s))
        if prev is not None and key < prev:
            errors.append(f"entities/{i}: entidades fuera de orden")
        prev = key
        coding, status = ent.get("coding") or {}, ent.get("normalization_status")
        filled = [coding.get(k) is not None for k in ("system", "code", "display")]
        # Si el estado es matched, los tres campos de coding deben estar presentes
        if status == "matched" and not all(filled):
            errors.append(f"entities/{i}: 'matched' exige system, code y display")
        # Si el estado es not_found o ambiguous, los tres campos de coding deben ser null
        if status in ("not_found", "ambiguous") and any(filled):
            errors.append(f"entities/{i}: '{status}' exige coding a null")
    return errors


def validate_document(doc: dict) -> None:
    # Validación completa de un documento clínico estructurado
    errors = schema_errors(doc)
    # Si no hay errores de esquema, comprobamos las reglas semánticas
    if not errors:
        errors = semantic_errors(doc)
    if errors:
        raise SchemaValidationError(errors)


def is_valid(doc: dict) -> bool:
    # Función de utilidad que devuelve True si el documento es válido, False en caso contrario
    try:
        validate_document(doc)
        return True
    except SchemaValidationError:
        return False


def write_schema(path: Path) -> None:
    # Exporta la definición de JSON_SCHEMA a un fichero legible .json en disco
    Path(path).write_text(json.dumps(JSON_SCHEMA, indent=2, ensure_ascii=False) + "\n",
                          encoding="utf-8")
