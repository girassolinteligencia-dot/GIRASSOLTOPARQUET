import io
import polars as pl
from typing import Dict, Tuple, Any
from app.core.schema import is_sensitive_column

def detect_csv_properties(file_path: str) -> Tuple[str, str]:
    """
    Detects the encoding and delimiter of a CSV file.
    Tests utf-8-sig, utf-8, cp1252, and latin-1.
    Tests delimiters: ',', ';', '\\t', '|'.
    """
    encodings = ["utf-8-sig", "utf-8", "cp1252", "latin-1"]
    detected_encoding = "utf-8"
    raw_bytes = b""
    
    try:
        with open(file_path, "rb") as f:
            raw_bytes = f.read(100 * 1024)  # Read up to 100 KB
    except Exception as e:
        raise IOError(f"Falha ao ler o arquivo para detecção: {e}")

    # Detect encoding
    for enc in encodings:
        try:
            raw_bytes.decode(enc)
            detected_encoding = enc
            break
        except UnicodeDecodeError:
            continue

    # Decode a sample to find separator
    try:
        sample_text = raw_bytes.decode(detected_encoding)
    except Exception:
        sample_text = raw_bytes.decode(detected_encoding, errors="replace")

    lines = [line.strip() for line in sample_text.splitlines() if line.strip()]
    
    delimiters = [",", ";", "\t", "|"]
    counts = {d: 0 for d in delimiters}
    
    # Analyze up to 5 header/data lines
    sample_lines = lines[:5]
    if sample_lines:
        for d in delimiters:
            # We look for a separator that is consistently present in all sample lines
            # and count its total occurrences
            occurrences = [line.count(d) for line in sample_lines]
            counts[d] = sum(occurrences)
            
    detected_sep = ","
    max_count = 0
    for d, count in counts.items():
        if count > max_count:
            max_count = count
            detected_sep = d
            
    return detected_encoding, detected_sep

def read_csv_file(file_path: str, preserve_sensitive: bool = True) -> Tuple[pl.DataFrame, str, str]:
    """
    Reads a CSV file into a Polars DataFrame.
    Automatically detects encoding and separator.
    Optionally overrides sensitive fields to be parsed as String type.
    """
    encoding, separator = detect_csv_properties(file_path)
    
    # 1. First read only headers to determine schema overrides
    try:
        if encoding in ("utf-8", "utf-8-sig"):
            headers_df = pl.read_csv(file_path, separator=separator, n_rows=0, ignore_errors=True)
        else:
            with open(file_path, "r", encoding=encoding, errors="replace") as f:
                header_line = f.readline()
            headers_df = pl.read_csv(header_line.encode("utf-8"), separator=separator, n_rows=0, ignore_errors=True)
            
        columns = headers_df.columns
    except Exception as e:
        raise ValueError(f"Não foi possível ler o cabeçalho do CSV: {e}")

    # 2. Build dtypes overrides for sensitive columns
    dtypes: Dict[str, Any] = {}
    if preserve_sensitive:
        for col in columns:
            if is_sensitive_column(col):
                dtypes[col] = pl.String

    # 3. Read the complete file
    try:
        if encoding in ("utf-8", "utf-8-sig"):
            df = pl.read_csv(
                file_path,
                separator=separator,
                schema_overrides=dtypes,
                infer_schema_length=10000,
                truncate_ragged_lines=True
            )
        else:
            # Read via memory conversion for non-utf8 encodings
            with open(file_path, "r", encoding=encoding, errors="replace") as f:
                content = f.read()
            df = pl.read_csv(
                content.encode("utf-8"),
                separator=separator,
                schema_overrides=dtypes,
                infer_schema_length=10000,
                truncate_ragged_lines=True
            )
    except Exception as e:
        raise ValueError(f"Erro ao analisar o arquivo CSV: {e}")

    # Deduplicate column names if Polars hasn't done it
    if len(df.columns) != len(set(df.columns)):
        # Polars usually appends _duplicated_1 but let's make sure
        seen = set()
        new_cols = []
        for i, col in enumerate(df.columns):
            if col in seen:
                new_col = f"{col}_duplicada_{i}"
                new_cols.append(new_col)
            else:
                seen.add(col)
                new_cols.append(col)
        df.columns = new_cols

    return df, encoding, separator
