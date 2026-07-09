import os
import pytest
import tempfile
import polars as pl
from app.core.ndjson_reader import read_ndjson_file

def test_jsonl_invalid_line_strict():
    content = '{"id": 1, "cpf": "111"}\n{invalid_json}\n{"id": 2, "cpf": "222"}\n'
    with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False, mode="w", encoding="utf-8") as f:
        f.write(content)
        temp_name = f.name
        
    try:
        # Strict mode: must raise ValueError on line 2
        with pytest.raises(ValueError) as exc:
            read_ndjson_file(temp_name, flatten=False, ignore_invalid_lines=False)
        assert "Linha 2 inválida" in str(exc.value)
    finally:
        os.remove(temp_name)

def test_jsonl_invalid_line_tolerant():
    content = '{"id": 1, "cpf": "111"}\n{invalid_json}\n{"id": 2, "cpf": "222"}\n'
    with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False, mode="w", encoding="utf-8") as f:
        f.write(content)
        temp_name = f.name
        
    try:
        # Tolerant mode: skips line 2, logs it in return list
        df, invalid = read_ndjson_file(temp_name, flatten=False, ignore_invalid_lines=True, preserve_sensitive=True)
        assert df.height == 2
        assert len(invalid) == 1
        assert invalid[0]["line_number"] == 2
        assert invalid[0]["content"] == "{invalid_json}"
        assert df.schema["cpf"] == pl.String
    finally:
        os.remove(temp_name)
