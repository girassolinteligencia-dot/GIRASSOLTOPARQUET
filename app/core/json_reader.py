import json
import polars as pl
from typing import Dict, List, Any, Tuple
from app.core.schema import is_sensitive_column

def flatten_dict(d: Dict[str, Any], parent_key: str = "", sep: str = "_") -> Dict[str, Any]:
    """
    Recursively flattens a nested dictionary.
    Example: {'a': 1, 'b': {'c': 2}} -> {'a': 1, 'b_c': 2}
    """
    items: List[Tuple[str, Any]] = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)

def extract_records(data: Any) -> List[Dict[str, Any]]:
    """
    Extracts a list of dictionaries (records) from parsed JSON data.
    Supports:
    - List of dicts
    - Single dict (becomes a list with 1 dict)
    - Dict with a key containing a list of dicts
    """
    if isinstance(data, list):
        # List of items
        records = []
        for item in data:
            if isinstance(item, dict):
                records.append(item)
            else:
                # If it's a list of primitive values, wrap it
                records.append({"valor": item})
        return records
        
    elif isinstance(data, dict):
        # Check if there is a key containing a list of dicts (like 'data', 'results', etc.)
        for key, val in data.items():
            if isinstance(val, list) and len(val) > 0 and all(isinstance(x, dict) for x in val):
                return val
                
        # If no list of dicts was found inside, treat the dictionary itself as a single record
        return [data]
        
    else:
        # Primitive value
        return [{"valor": data}]

def cast_sensitive_columns_json(df: pl.DataFrame) -> pl.DataFrame:
    """
    Casts sensitive columns to String in the DataFrame.
    """
    for col in df.columns:
        if is_sensitive_column(col):
            # In Polars, cast directly to String
            df = df.with_columns(pl.col(col).cast(pl.String))
    return df

def read_json_file(file_path: str, flatten: bool = False, preserve_sensitive: bool = True) -> pl.DataFrame:
    """
    Reads a JSON file, extracts records, optionally flattens them,
    and returns a Polars DataFrame.
    """
    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            try:
                data = json.load(f)
                records = extract_records(data)
            except json.JSONDecodeError:
                # Tenta ler como JSON Lines (JSONL)
                f.seek(0)
                records = []
                for line in f:
                    line = line.strip()
                    if line:
                        line_data = json.loads(line)
                        records.extend(extract_records(line_data))
    except Exception as e:
        raise ValueError(f"Arquivo JSON malformado: {e}")
        
    if not records:
        raise ValueError("Nenhum registro válido encontrado no arquivo JSON.")
        
    if flatten:
        records = [flatten_dict(r) for r in records]
        
    try:
        df = pl.DataFrame(records)
    except Exception as e:
        raise ValueError(f"Não foi possível estruturar os dados do JSON: {e}")
        
    if preserve_sensitive:
        df = cast_sensitive_columns_json(df)
        
    return df
