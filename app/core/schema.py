import unicodedata
from typing import Set

SENSITIVE_COLUMNS: Set[str] = {
    "cpf",
    "cnpj",
    "documento",
    "titulo_eleitoral",
    "inscrição",
    "inscricao",
    "inscrição_municipal",
    "inscricao_municipal",
    "cep",
    "telefone",
    "celular",
    "zona",
    "secao",
    "seção",
    "codigo",
    "código",
    "id_municipio",
    "id_municipio_tse",
    "numero_candidato",
    "numero_partido"
}

def remove_accents(text: str) -> str:
    """Helper to remove accents from a string for robust name matching."""
    text = unicodedata.normalize("NFD", text)
    return "".join(c for c in text if unicodedata.category(c) != "Mn")

def is_sensitive_column(column_name: str) -> bool:
    """
    Checks if a column name corresponds to a sensitive field.
    The check is case-insensitive, ignores spaces, and ignores accents.
    """
    cleaned_name = column_name.strip().lower()
    if cleaned_name in SENSITIVE_COLUMNS:
        return True
    
    # Also check without accents
    name_no_accents = remove_accents(cleaned_name)
    if name_no_accents in SENSITIVE_COLUMNS:
        return True
        
    # Check if any sensitive column name without accents matches
    sensitive_no_accents = {remove_accents(col) for col in SENSITIVE_COLUMNS}
    if name_no_accents in sensitive_no_accents:
        return True
        
    return False
