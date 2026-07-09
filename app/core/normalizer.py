import re
import unicodedata
from typing import List, Dict, Tuple

def normalize_column_name(name: str) -> str:
    """
    Normalizes a single column name:
    - Removes accents.
    - Converts to lowercase.
    - Replaces spaces and dashes with underscores.
    - Removes special characters (keeping only a-z, 0-9, and _).
    - Removes leading/trailing underscores.
    """
    if not name:
        return "coluna_sem_nome"
        
    # Convert to string just in case
    name = str(name)
    
    # Lowercase
    name = name.lower().strip()
    
    # Replace common terms specifically to avoid unwanted underscores
    name = name.replace("e-mail", "email")
    name = name.replace("e_mail", "email")
    
    # Remove accents
    name = unicodedata.normalize("NFD", name)
    name = "".join(c for c in name if unicodedata.category(c) != "Mn")
    
    # Replace spaces, tabs, dashes and slashes with underscores
    name = re.sub(r"[\s\-\/\\]+", "_", name)
    
    # Remove all characters except a-z, 0-9, and _
    name = re.sub(r"[^a-z0-9_]", "", name)
    
    # Replace multiple consecutive underscores with a single underscore
    name = re.sub(r"_+", "_", name)
    
    # Remove leading/trailing underscores
    name = name.strip("_")
    
    if not name:
        name = "coluna"
        
    return name

def normalize_columns(columns: List[str]) -> Tuple[List[str], Dict[str, str]]:
    """
    Normalizes a list of column names, ensuring no duplicates.
    Returns:
    - List of normalized column names.
    - Dict mapping original column name -> final column name.
    """
    normalized_cols: List[str] = []
    mapping: Dict[str, str] = {}
    seen: Dict[str, int] = {}
    
    for original_name in columns:
        base_name = normalize_column_name(original_name)
        
        # Avoid duplicate names by appending a suffix if seen before
        if base_name in seen:
            seen[base_name] += 1
            final_name = f"{base_name}_{seen[base_name]}"
        else:
            seen[base_name] = 0
            final_name = base_name
            
        normalized_cols.append(final_name)
        mapping[original_name] = final_name
        
    return normalized_cols, mapping
