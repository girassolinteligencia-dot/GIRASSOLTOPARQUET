import os
import time
import hashlib
import polars as pl
from typing import Dict, List, Any, Tuple, Optional

from app.core.detector import detect_format
from app.core.validator import validate_input_file, validate_output_directory
from app.core.normalizer import normalize_columns
from app.core.csv_reader import read_csv_file
from app.core.excel_reader import read_excel_file
from app.core.json_reader import read_json_file
from app.core.ndjson_reader import read_ndjson_file
from app.core.parquet_writer import write_parquet_file

def calculate_sha256(file_path: str) -> str:
    """Calculates the SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(65536), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception:
        return "indisponivel"

def get_inferred_types(df: pl.DataFrame) -> Dict[str, str]:
    """Returns a dictionary of column names mapped to their string datatype representations."""
    return {col: str(dtype) for col, dtype in df.schema.items()}

def apply_preset_casting(df: pl.DataFrame, preset: str) -> pl.DataFrame:
    """
    Applies smart type casting rules depending on the chosen preset.
    For 'bi' or 'gis':
    - Auto-detects columns indicating coordinates (lat, lon, lng, latitude, longitude, etc.)
      and attempts to cast them from String to Float64.
    """
    if preset not in ("bi", "gis"):
        return df
        
    from app.core.schema import remove_accents
    
    # Helper to check if a column name matches coordinate pattern
    def is_coordinate_col(name: str) -> bool:
        n = remove_accents(name.lower().strip())
        if n in {"lat", "lon", "lng", "latitude", "longitude"}:
            return True
        if "latitude" in n or "longitude" in n:
            return True
        if n.startswith("lat_") or n.endswith("_lat") or n.startswith("lon_") or n.endswith("_lon") or n.startswith("lng_") or n.endswith("_lng"):
            return True
        return False

    for col in df.columns:
        # Check if it's a coordinate column and currently represented as String (text)
        if is_coordinate_col(col) and df.schema[col] == pl.String:
            try:
                # Replace comma with dot, strip characters, and cast to Float64
                # We use strict=False to convert unparseable values to null instead of failing
                df = df.with_columns(
                    pl.col(col)
                    .str.strip_chars()
                    .str.replace(",", ".", literal=True)
                    .cast(pl.Float64, strict=False)
                )
            except Exception as e:
                import logging
                logging.warning(f"Falha ao realizar casting da coluna de coordenada '{col}': {e}")
                
    return df

def convert_file(
    file_path: str,
    output_dir: str,
    normalize_cols: bool = False,
    flatten_json: bool = False,
    process_all_sheets: bool = False,
    preserve_sensitive: bool = True,
    continue_on_error: bool = False,
    compression: str = "snappy",
    preset: str = "default"
) -> Dict[str, Any]:
    """
    Orchestrates the conversion of a single source file to Parquet format.
    Returns a dictionary of execution metrics suitable for logging and report generation.
    """
    start_time = time.time()
    file_name = os.path.basename(file_path)
    base_name_no_ext, _ = os.path.splitext(file_name)
    
    # Initialize report structure
    report: Dict[str, Any] = {
        "nome_original": file_name,
        "caminho_original": os.path.abspath(file_path),
        "tamanho_bytes": 0,
        "hash_sha256": "",
        "formato_detectado": "",
        "data_hora_conversao": time.strftime("%Y-%m-%d %H:%M:%S"),
        "status": "erro",
        "erros": [],
        "caminho_parquet_gerado": [],
        "compressao_usada": compression,
        "tempo_processamento_segundos": 0.0,
        # Format-specific fields
        "csv_encoding": None,
        "csv_separador": None,
        "xlsx_abas_processadas": [],
        "ndjson_linhas_invalidas": [],
        # Global metrics
        "linhas_lidas": 0,
        "colunas_lidas": 0,
        "colunas_originais": [],
        "colunas_finais": [],
        "tipos_inferidos": {}
    }
    
    try:
        # 1. Validation
        validate_input_file(file_path)
        validate_output_directory(output_dir)
        
        # Collect size and hash
        report["tamanho_bytes"] = os.path.getsize(file_path)
        report["hash_sha256"] = calculate_sha256(file_path)
        
        # 2. Detect Format
        fmt = detect_format(file_path)
        report["formato_detectado"] = fmt
        
        # 3. Read File according to type
        dataframes: Dict[str, pl.DataFrame] = {}
        
        if fmt == "csv":
            df, encoding, separator = read_csv_file(file_path, preserve_sensitive=preserve_sensitive)
            report["csv_encoding"] = encoding
            report["csv_separador"] = separator
            dataframes["default"] = df
            
        elif fmt == "xlsx":
            sheets_data = read_excel_file(
                file_path,
                process_all_sheets=process_all_sheets,
                preserve_sensitive=preserve_sensitive
            )
            for sheet, df in sheets_data.items():
                dataframes[sheet] = df
            report["xlsx_abas_processadas"] = list(sheets_data.keys())
            
        elif fmt == "json":
            df = read_json_file(file_path, flatten=flatten_json, preserve_sensitive=preserve_sensitive)
            dataframes["default"] = df
            
        elif fmt in ("ndjson", "jsonl"):
            df, invalid_lines = read_ndjson_file(
                file_path,
                flatten=flatten_json,
                ignore_invalid_lines=continue_on_error,
                preserve_sensitive=preserve_sensitive
            )
            report["ndjson_linhas_invalidas"] = invalid_lines
            dataframes["default"] = df
            
        # 4. Process and Write
        if not dataframes:
            raise ValueError("O arquivo não contém dados válidos para conversão.")
            
        written_files = []
        total_rows = 0
        
        # If there's only one dataframe (e.g. not multi-sheet Excel), base filename matches original
        # If there are multiple (multi-sheet Excel), file name will be file_name__sheet_name.parquet
        is_multi_sheet = (fmt == "xlsx" and len(dataframes) > 1)
        
        # Normalize and write each DataFrame
        for sheet_name, df in dataframes.items():
            orig_columns = df.columns
            final_columns = orig_columns
            col_mapping = {}
            
            # Apply column normalization if requested
            if normalize_cols:
                final_columns, col_mapping = normalize_columns(orig_columns)
                df.columns = final_columns
                
            # Apply preset-specific smart type conversions (Casting)
            if preset in ("bi", "gis"):
                df = apply_preset_casting(df, preset)
                
            # Write to Parquet
            if is_multi_sheet:
                out_name = f"{base_name_no_ext}__{sheet_name}.parquet"
            else:
                out_name = f"{base_name_no_ext}.parquet"
                
            out_path = os.path.join(output_dir, out_name)
            
            write_parquet_file(df, out_path, compression=compression)
            written_files.append(out_path)
            total_rows += df.height
            
            # For reporting, if multi-sheet Excel, we aggregate/record the last one or accumulate
            # Let's save the metadata (columns and types) of the first or main dataframe, or accumulate
            if len(dataframes) == 1 or sheet_name == list(dataframes.keys())[0]:
                report["colunas_originais"] = list(orig_columns)
                report["colunas_finais"] = list(final_columns)
                report["colunas_lidas"] = len(orig_columns)
                report["tipos_inferidos"] = get_inferred_types(df)
                if normalize_cols:
                    report["mapa_normalizacao"] = col_mapping
                    
        report["linhas_lidas"] = total_rows
        report["caminho_parquet_gerado"] = written_files
        
        # Set final status
        if fmt in ("ndjson", "jsonl") and report["ndjson_linhas_invalidas"]:
            report["status"] = "sucesso_com_alertas"
        else:
            report["status"] = "sucesso"
            
    except Exception as e:
        report["status"] = "erro"
        report["erros"].append(str(e))
        
    report["tempo_processamento_segundos"] = round(time.time() - start_time, 4)
    return report
