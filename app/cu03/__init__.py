"""CU-03 — Extracción y estructuración de información clínica en español.

Paquete del pipeline descrito en ARCHITECTURE.md:

    corpus         -> cargador BRAT de PharmaCoNER (única pieza que conoce el formato físico)
    ner            -> extracción de menciones (baseline de diccionario)
    normalization  -> normalización conservadora a SNOMED CT (matched / not_found / ambiguous)
    schema         -> contrato JSON canónico (schema_version 1.0) y su validación
    pipeline       -> orquestación texto -> JSON canónico
    evaluation     -> métricas estrictas P/R/F1, exactitud y cobertura de códigos
"""

__version__ = "0.1.0"
