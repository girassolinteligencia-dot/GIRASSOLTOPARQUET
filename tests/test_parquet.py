import os
import tempfile
import polars as pl
from app.core.parquet_writer import write_parquet_file

def test_parquet_compression_writing():
    df = pl.DataFrame({
        "id": [1, 2, 3],
        "valor": [10.5, 20.0, 15.25]
    })
    
    # Test Snappy
    with tempfile.NamedTemporaryFile(suffix=".parquet", delete=False) as f:
        temp_snappy = f.name
    # Test Zstd
    with tempfile.NamedTemporaryFile(suffix=".parquet", delete=False) as f:
        temp_zstd = f.name
    # Test None
    with tempfile.NamedTemporaryFile(suffix=".parquet", delete=False) as f:
        temp_none = f.name

    try:
        # Write Snappy
        write_parquet_file(df, temp_snappy, compression="snappy")
        assert os.path.exists(temp_snappy)
        assert os.path.getsize(temp_snappy) > 0
        df_read = pl.read_parquet(temp_snappy)
        assert df_read.height == 3
        
        # Write Zstd
        write_parquet_file(df, temp_zstd, compression="zstd")
        assert os.path.exists(temp_zstd)
        df_read = pl.read_parquet(temp_zstd)
        assert df_read.width == 2
        
        # Write None
        write_parquet_file(df, temp_none, compression="none")
        assert os.path.exists(temp_none)
        df_read = pl.read_parquet(temp_none)
        assert df_read["valor"][0] == 10.5
        
    finally:
        for p in (temp_snappy, temp_zstd, temp_none):
            if os.path.exists(p):
                os.remove(p)
