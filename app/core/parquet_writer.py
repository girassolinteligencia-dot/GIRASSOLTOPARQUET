import polars as pl

def write_parquet_file(
    df: pl.DataFrame,
    output_path: str,
    compression: str = "snappy"
) -> None:
    """
    Writes a Polars DataFrame to a Parquet file.
    compression: 'snappy', 'zstd', or 'none'.
    """
    comp_map = {
        "snappy": "snappy",
        "zstd": "zstd",
        "none": "uncompressed"
    }
    
    comp_value = comp_map.get(compression.lower(), "snappy")
    
    try:
        # Polars write_parquet uses pyarrow/arrow-rs under the hood.
        # We can also pass use_pyarrow=True if we want to force PyArrow.
        df.write_parquet(
            output_path,
            compression=comp_value,
            use_pyarrow=True
        )
    except Exception as e:
        raise IOError(f"Falha ao gravar arquivo Parquet {output_path}: {e}")
