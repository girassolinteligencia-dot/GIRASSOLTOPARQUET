import json
import polars as pl
from typing import Dict, List, Tuple, Any
from app.core.schema import is_sensitive_column
from app.core.json_reader import flatten_dict, cast_sensitive_columns_json

def read_ndjson_file(
    file_path: str,
    flatten: bool = False,
    ignore_invalid_lines: bool = False,
    preserve_sensitive: bool = True
) -> Tuple[pl.DataFrame, List[Dict[str, Any]]]:
    """
    Reads a line-delimited JSON file (NDJSON / JSONL).
    Returns:
    - Polars DataFrame with successfully parsed records.
    - List of dictionaries representing invalid lines: [{'line_number': int, 'content': str, 'error': str}]
    """
    records: List[Dict[str, Any]] = []
    invalid_lines: List[Dict[str, Any]] = []
    
    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            for i, line in enumerate(f, start=1):
                stripped_line = line.strip()
                if not stripped_line:
                    continue  # Ignore empty lines
                    
                try:
                    record = json.loads(stripped_line)
                    if not isinstance(record, dict):
                        # Enforce dict record, if list or value, wrap it
                        if isinstance(record, (list, str, int, float, bool)) or record is None:
                            record = {"valor": record}
                        else:
                            raise ValueError("A linha JSON não é um objeto ou valor válido.")
                            
                    if flatten:
                        record = flatten_dict(record)
                        
                    records.append(record)
                except Exception as e:
                    err_msg = str(e)
                    invalid_lines.append({
                        "line_number": i,
                        "content": stripped_line[:100] + "..." if len(stripped_line) > 100 else stripped_line,
                        "error": err_msg
                    })
                    if not ignore_invalid_lines:
                        raise ValueError(f"Linha {i} inválida no JSONL: {err_msg}")
    except Exception as e:
        if not ignore_invalid_lines or not records:
            # Re-raise if we can't open file, or if we are not ignoring invalid lines
            raise e

    if not records:
        raise ValueError("Nenhum registro válido encontrado no arquivo NDJSON/JSONL.")

    try:
        df = pl.DataFrame(records)
    except Exception as e:
        raise ValueError(f"Não foi possível estruturar os dados do NDJSON/JSONL: {e}")

    if preserve_sensitive:
        df = cast_sensitive_columns_json(df)

    return df, invalid_lines
