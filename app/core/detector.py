import os
from typing import Optional

SUPPORTED_FORMATS = {
    ".csv": "csv",
    ".xlsx": "xlsx",
    ".json": "json",
    ".ndjson": "ndjson",
    ".jsonl": "jsonl"
}

def detect_format(file_path: str) -> str:
    """
    Detects the file format based on its extension.
    Raises ValueError if the file format is not supported.
    """
    _, ext = os.path.splitext(file_path.lower())
    if ext not in SUPPORTED_FORMATS:
        raise ValueError(f"Extensão de arquivo não suportada: {ext}. Formatos válidos: {', '.join(SUPPORTED_FORMATS.keys())}")
    return SUPPORTED_FORMATS[ext]
