import os
import tempfile
import polars as pl
from app.core.csv_reader import read_csv_file, detect_csv_properties

def test_csv_comma_detection():
    content = "nome,cpf,cep\nJoão,012345,01001\nMaria,987654,02002"
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w", encoding="utf-8") as f:
        f.write(content)
        temp_name = f.name
        
    try:
        encoding, separator = detect_csv_properties(temp_name)
        assert separator == ","
        
        df, enc, sep = read_csv_file(temp_name, preserve_sensitive=True)
        assert df.height == 2
        assert df.columns == ["nome", "cpf", "cep"]
        # cpf and cep are sensitive, must be String
        assert df.schema["cpf"] == pl.String
        assert df.schema["cep"] == pl.String
    finally:
        os.remove(temp_name)

def test_csv_semicolon_cp1252():
    # CP1252 accents: João -> J\xe3o
    content_bytes = "nome;cpf;inscrição\nJo\xe3o;00123;555\nMaria;99999;666".encode("cp1252")
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
        f.write(content_bytes)
        temp_name = f.name
        
    try:
        encoding, separator = detect_csv_properties(temp_name)
        assert separator == ";"
        assert encoding == "cp1252"
        
        df, enc, sep = read_csv_file(temp_name, preserve_sensitive=True)
        assert df.height == 2
        assert df.schema["inscrição"] == pl.String
        assert df.schema["cpf"] == pl.String
        # Check value decoded correctly
        assert df["nome"][0] == "João"
    finally:
        os.remove(temp_name)
