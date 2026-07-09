import polars as pl
import openpyxl
from typing import Dict, List, Tuple
from app.core.schema import is_sensitive_column

def get_excel_sheets(file_path: str) -> List[str]:
    """
    Returns the list of sheet names in an Excel file.
    Uses openpyxl in read-only mode for safety.
    """
    try:
        wb = openpyxl.load_workbook(file_path, read_only=True, keep_links=False)
        sheets = wb.sheetnames
        wb.close()
        return sheets
    except Exception as e:
        raise ValueError(f"Não foi possível abrir o arquivo Excel: {e}")

def cast_sensitive_columns_excel(df: pl.DataFrame) -> pl.DataFrame:
    """
    Casts sensitive columns to String, handling float conversion (.0) properly.
    """
    for col in df.columns:
        if is_sensitive_column(col):
            dtype = df.schema[col]
            if dtype.is_float():
                # To avoid trailing .0 on integer-like floats, format or cast selectively
                df = df.with_columns(
                    pl.when(pl.col(col).is_not_null())
                    .then(
                        pl.when(pl.col(col) % 1 == 0)
                        .then(pl.col(col).cast(pl.Int64).cast(pl.String))
                        .otherwise(pl.col(col).cast(pl.String))
                    )
                    .otherwise(pl.lit(None))
                    .alias(col)
                )
            elif dtype.is_integer():
                df = df.with_columns(pl.col(col).cast(pl.String))
            elif dtype != pl.String:
                df = df.with_columns(pl.col(col).cast(pl.String))
    return df

def read_excel_file(file_path: str, process_all_sheets: bool = False, preserve_sensitive: bool = True) -> Dict[str, pl.DataFrame]:
    """
    Reads an Excel file and returns a dictionary of {sheet_name: DataFrame}.
    Ignores empty sheets.
    """
    sheets = get_excel_sheets(file_path)
    if not sheets:
        raise ValueError("O arquivo Excel não contém nenhuma aba.")
        
    sheets_to_process = sheets if process_all_sheets else [sheets[0]]
    result: Dict[str, pl.DataFrame] = {}
    
    for sheet_name in sheets_to_process:
        try:
            # calamine is faster, let's try reading with calamine, fallback if needed
            df = pl.read_excel(file_path, sheet_name=sheet_name, engine="calamine")
        except Exception as e:
            # Check if it's NoDataError or contains empty sheet text
            if "empty" in str(e).lower() or "nodataerror" in str(type(e)).lower():
                continue
            try:
                # Fallback to openpyxl engine
                df = pl.read_excel(file_path, sheet_name=sheet_name, engine="openpyxl")
            except Exception as e2:
                if "empty" in str(e2).lower() or "nodataerror" in str(type(e2)).lower():
                    continue
                # If we are failing, let's raise a descriptive error
                raise ValueError(f"Erro ao ler a aba '{sheet_name}': {e2}")
                
        # Check if the sheet is empty
        if df.is_empty() or len(df.columns) == 0:
            continue
            
        # Enforce sensitive columns cast
        if preserve_sensitive:
            df = cast_sensitive_columns_excel(df)
            
        result[sheet_name] = df
        
    return result
