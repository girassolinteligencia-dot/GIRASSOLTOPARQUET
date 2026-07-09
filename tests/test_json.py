import os
import json
import tempfile
import polars as pl
from app.core.json_reader import read_json_file, extract_records, flatten_dict

def test_flatten_dict():
    nested = {
        "a": 1,
        "b": {
            "c": 2,
            "d": {
                "e": 3
            }
        }
    }
    flat = flatten_dict(nested)
    assert flat == {"a": 1, "b_c": 2, "b_d_e": 3}

def test_extract_records_variations():
    # List of objects
    assert extract_records([{"a": 1}, {"b": 2}]) == [{"a": 1}, {"b": 2}]
    # Single object
    assert extract_records({"a": 1, "b": 2}) == [{"a": 1, "b": 2}]
    # Object with nested list of dicts
    assert extract_records({"status": "ok", "items": [{"id": 1}, {"id": 2}]}) == [{"id": 1}, {"id": 2}]

def test_read_json_file_flatten():
    data = [
        {
            "nome": "João",
            "cpf": "0123",
            "endereco": {
                "rua": "Principal",
                "numero": 10
            }
        }
    ]
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w", encoding="utf-8") as f:
        json.dump(data, f)
        temp_name = f.name
        
    try:
        df = read_json_file(temp_name, flatten=True, preserve_sensitive=True)
        assert df.height == 1
        assert "endereco_rua" in df.columns
        assert "endereco_numero" in df.columns
        assert df["endereco_rua"][0] == "Principal"
        assert df.schema["cpf"] == pl.String
    finally:
        os.remove(temp_name)
