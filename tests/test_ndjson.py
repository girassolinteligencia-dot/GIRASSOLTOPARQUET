import os
import tempfile
import polars as pl
from app.core.ndjson_reader import read_ndjson_file

def test_ndjson_valid():
    content = '{"id": 1, "cpf": "111", "nome": "A"}\n{"id": 2, "cpf": "222", "nome": "B"}\n'
    with tempfile.NamedTemporaryFile(suffix=".ndjson", delete=False, mode="w", encoding="utf-8") as f:
        f.write(content)
        temp_name = f.name
        
    try:
        df, invalid = read_ndjson_file(temp_name, flatten=False, ignore_invalid_lines=False, preserve_sensitive=True)
        assert df.height == 2
        assert len(invalid) == 0
        assert df.schema["cpf"] == pl.String
        assert df["nome"][1] == "B"
    finally:
        os.remove(temp_name)
