#!/usr/bin/env python3
"""
Script de descarga y preparación de datasets clínicos para el caso CU-03.
Utiliza Zenodo y Hugging Face para obtener los corpus oficiales en español.

Uso (Windows / Linux / macOS):
    python scripts/download_datasets.py [--dataset pharmaconer|distemist|medprocner|symptemist|all]
    o con uv:
    uv run python scripts/download_datasets.py [--dataset pharmaconer|distemist|medprocner|symptemist|all]
"""

import argparse
import io
import json
import os
import shutil
import sys
import urllib.request
import zipfile
from pathlib import Path

# Compatibilidad con terminales Windows (CMD / PowerShell con codepages no-UTF8)
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATA_DIR = PROJECT_ROOT / "data"

# Catálogo de datasets en Zenodo
DATASETS_CONFIG = {
    "pharmaconer": {
        "name": "PharmaCoNER (Fármacos y proteínas)",
        "zenodo_record": "4270158",
        "zip_filename": "pharmaconer.zip",
        "url": "https://zenodo.org/api/records/4270158/files/pharmaconer.zip/content",
        "description": "Gold standard de fármacos, sustancias y proteínas en casos clínicos (SPACCC).",
        "hf_conll_urls": {
            "train-set_1.1.conll": "https://huggingface.co/datasets/PlanTL-GOB-ES/pharmaconer/raw/main/train-set_1.1.conll",
            "dev-set_1.1.conll": "https://huggingface.co/datasets/PlanTL-GOB-ES/pharmaconer/raw/main/dev-set_1.1.conll",
            "test-set_1.1.conll": "https://huggingface.co/datasets/PlanTL-GOB-ES/pharmaconer/raw/main/test-set_1.1.conll",
        },
    },
    "distemist": {
        "name": "DisTEMIST (Enfermedades y diagnósticos)",
        "zenodo_record": "7614764",
        "zip_filename": "distemist_zenodo.zip",
        "url": "https://zenodo.org/api/records/7614764/files/distemist_zenodo.zip/content",
        "description": "Corpus de detección y normalización de enfermedades a SNOMED CT.",
    },
    "medprocner": {
        "name": "MedProcNER (Procedimientos clínicos)",
        "zenodo_record": "8224056",
        "zip_filename": "medprocner_gs_train+test+gazz+multilingual+crossmap_230808.zip",
        "url": "https://zenodo.org/api/records/8224056/files/medprocner_gs_train+test+gazz+multilingual+crossmap_230808.zip/content",
        "description": "Corpus de detección y normalización de procedimientos médicos a SNOMED CT.",
    },
    "symptemist": {
        "name": "SympTEMIST (Síntomas y signos)",
        "zenodo_record": "10635215",
        "zip_filename": "symptemist-complete_240208.zip",
        "url": "https://zenodo.org/api/records/10635215/files/symptemist-complete_240208.zip/content",
        "description": "Corpus de síntomas y signos normalizados a SNOMED CT (~450MB).",
    },
}


def download_with_progress(url: str, output_path: Path, label: str = ""):
    """Descarga un archivo remoto mostrando el progreso."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = output_path.with_suffix(".tmp")

    headers = {"User-Agent": "PIIA2-CU03-DatasetDownloader/1.0"}
    req = urllib.request.Request(url, headers=headers)

    print(f"[*] Descargando {label or output_path.name} desde:\n    {url}")
    with urllib.request.urlopen(req) as resp, open(temp_path, "wb") as f_out:
        total_size = resp.getheader("Content-Length")
        total_bytes = int(total_size) if total_size else None
        downloaded = 0
        chunk_size = 64 * 1024

        while True:
            chunk = resp.read(chunk_size)
            if not chunk:
                break
            f_out.write(chunk)
            downloaded += len(chunk)
            if total_bytes:
                percent = (downloaded / total_bytes) * 100
                mb_down = downloaded / (1024 * 1024)
                mb_total = total_bytes / (1024 * 1024)
                sys.stdout.write(f"\r    Progreso: {mb_down:6.2f} MB / {mb_total:6.2f} MB ({percent:5.1f}%)")
            else:
                mb_down = downloaded / (1024 * 1024)
                sys.stdout.write(f"\r    Descargados: {mb_down:6.2f} MB")
            sys.stdout.flush()

    print()
    try:
        os.replace(temp_path, output_path)
    except OSError:
        if output_path.exists():
            try:
                output_path.unlink()
            except OSError:
                pass
        shutil.move(temp_path, output_path)
    print(f"[+] Guardado correctamente en: {output_path}")


def extract_zip(zip_path: Path, target_dir: Path):
    """Extrae un archivo zip en target_dir."""
    print(f"[*] Extrayendo {zip_path.name} en {target_dir}...")
    target_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "r") as z:
        z.extractall(target_dir)
    print(f"[+] Extracción completada en: {target_dir}")


def download_hf_conll(dataset_key: str, dest_dir: Path):
    """Descarga ficheros CoNLL desde Hugging Face si están definidos."""
    cfg = DATASETS_CONFIG.get(dataset_key, {})
    conll_urls = cfg.get("hf_conll_urls", {})
    if not conll_urls:
        return

    conll_dir = dest_dir / "conll"
    conll_dir.mkdir(parents=True, exist_ok=True)
    print(f"[*] Descargando particiones CoNLL adicionales desde Hugging Face...")
    for filename, url in conll_urls.items():
        out_file = conll_dir / filename
        if out_file.exists():
            print(f"    - {filename} ya existe, omitiendo.")
            continue
        req = urllib.request.Request(url, headers={"User-Agent": "PIIA2-CU03-DatasetDownloader/1.0"})
        with urllib.request.urlopen(req) as resp, open(out_file, "wb") as f_out:
            f_out.write(resp.read())
        print(f"    [+] {filename} descargado ({out_file.stat().st_size / 1024:.1f} KB)")


def download_dataset(dataset_key: str, root_data_dir: Path, force: bool = False, include_conll: bool = True):
    """Descarga y descomprime un dataset específico."""
    cfg = DATASETS_CONFIG.get(dataset_key)
    if not cfg:
        print(f"[!] Error: Dataset '{dataset_key}' no reconocido.")
        return

    print("=" * 70)
    print(f"PROCESANDO: {cfg['name']}")
    print(f"Descripción: {cfg['description']}")
    print("=" * 70)

    dataset_dir = root_data_dir / dataset_key
    raw_archives_dir = root_data_dir / "archives"
    raw_archives_dir.mkdir(parents=True, exist_ok=True)

    archive_path = raw_archives_dir / cfg["zip_filename"]

    # Descarga de archivo ZIP
    if archive_path.exists() and not force:
        print(f"[i] El archivo comprimido ya existe: {archive_path}")
    else:
        download_with_progress(cfg["url"], archive_path, label=cfg["zip_filename"])

    # Extracción
    if dataset_dir.exists() and not force:
        print(f"[i] La carpeta de destino ya existe: {dataset_dir}")
        print("    (usa --force para re-extraer si lo deseas)")
    else:
        extract_zip(archive_path, dataset_dir)

    # Descargas adicionales CoNLL (Hugging Face)
    if include_conll and "hf_conll_urls" in cfg:
        download_hf_conll(dataset_key, dataset_dir)

    # Resumen de ficheros extraídos
    txt_count = len(list(dataset_dir.rglob("*.txt")))
    ann_count = len(list(dataset_dir.rglob("*.ann")))
    conll_count = len(list(dataset_dir.rglob("*.conll")))
    tsv_count = len(list(dataset_dir.rglob("*.tsv")))

    print("\nResumen del dataset:")
    print(f"  - Directorio: {dataset_dir}")
    print(f"  - Archivos de texto (.txt): {txt_count}")
    print(f"  - Archivos de anotación BRAT (.ann): {ann_count}")
    if conll_count > 0:
        print(f"  - Archivos CoNLL (.conll): {conll_count}")
    if tsv_count > 0:
        print(f"  - Archivos TSV (.tsv): {tsv_count}")
    print("=" * 70 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="Descarga y preparación de datasets para CU-03 (Extracción de información clínica)."
    )
    parser.add_argument(
        "--dataset",
        choices=["pharmaconer", "distemist", "medprocner", "symptemist", "all"],
        default="pharmaconer",
        help="Dataset a descargar (por defecto: pharmaconer, prioritario para Fase 1).",
    )
    parser.add_argument(
        "--dest-dir",
        type=Path,
        default=DEFAULT_DATA_DIR,
        help="Directorio base de destino (por defecto: ./data en la raíz del proyecto).",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Forzar la re-descarga y re-extracción incluso si ya existen los archivos.",
    )
    parser.add_argument(
        "--no-conll",
        action="store_true",
        help="No descargar particiones CoNLL adicionales de Hugging Face.",
    )

    args = parser.parse_args()
    root_data_dir = args.dest_dir.resolve()
    root_data_dir.mkdir(parents=True, exist_ok=True)

    print(f"[*] Directorio de datos: {root_data_dir}")

    if args.dataset == "all":
        datasets_to_run = ["pharmaconer", "distemist", "medprocner", "symptemist"]
    else:
        datasets_to_run = [args.dataset]

    for d in datasets_to_run:
        download_dataset(d, root_data_dir, force=args.force, include_conll=not args.no_conll)

    print("[✔] Proceso de descarga finalizado con éxito.")


if __name__ == "__main__":
    main()
