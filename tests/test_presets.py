import polars as pl
from app.core.converter import apply_preset_casting

def test_apply_preset_casting_coordinates():
    # Setup test dataframe with coordinate columns represented as strings in various formats
    data = {
        "id_endereco": ["1", "2", "3", "4", "5"],
        "latitude": ["-23.55052", "-23,5467", "  -22.9068  ", None, ""],
        "lng_coord": ["-46.6333", "-46,6269", "-43.1729", "invalido", " -43,2000 "],
        "nome_rua": ["Av Paulista", "Rua Augusta", "Copacabana", "Rua Centro", "Av Atlantica"]
    }
    
    df = pl.DataFrame(data)
    
    # Verify initial schema - all should be String
    assert df.schema["id_endereco"] == pl.String
    assert df.schema["latitude"] == pl.String
    assert df.schema["lng_coord"] == pl.String
    assert df.schema["nome_rua"] == pl.String
    
    # Apply BI preset casting
    casted_df = apply_preset_casting(df, "bi")
    
    # Assert coordinate schemas are now Float64
    assert casted_df.schema["latitude"] == pl.Float64
    assert casted_df.schema["lng_coord"] == pl.Float64
    
    # Assert other columns are untouched
    assert casted_df.schema["id_endereco"] == pl.String
    assert casted_df.schema["nome_rua"] == pl.String
    
    # Assert values are parsed correctly
    # Row 0: "-23.55052" -> -23.55052, "-46.6333" -> -46.6333
    assert casted_df["latitude"][0] == -23.55052
    assert casted_df["lng_coord"][0] == -46.6333
    
    # Row 1: "-23,5467" (Brazilian comma) -> -23.5467, "-46,6269" -> -46.6269
    assert casted_df["latitude"][1] == -23.5467
    assert casted_df["lng_coord"][1] == -46.6269
    
    # Row 2: "  -22.9068  " (Padded) -> -22.9068, "-43.1729" -> -43.1729
    assert casted_df["latitude"][2] == -22.9068
    assert casted_df["lng_coord"][2] == -43.1729
    
    # Row 3: None (null) -> None, "invalido" (unparseable) -> None (due to strict=False)
    assert casted_df["latitude"][3] is None
    assert casted_df["lng_coord"][3] is None
    
    # Row 4: "" (empty string) -> None, " -43,2000 " (Brazilian comma + padded) -> -43.2000
    assert casted_df["latitude"][4] is None
    assert casted_df["lng_coord"][4] == -43.2000

def test_apply_preset_casting_default_preset():
    # Setup test dataframe
    data = {
        "latitude": ["-23.55052", "-23,5467"],
        "nome_rua": ["Av Paulista", "Rua Augusta"]
    }
    df = pl.DataFrame(data)
    
    # Apply default preset (no casting should happen)
    casted_df = apply_preset_casting(df, "default")
    
    # Schema should remain unchanged
    assert casted_df.schema["latitude"] == pl.String
    assert casted_df.schema["nome_rua"] == pl.String
