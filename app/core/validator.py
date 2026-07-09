import os
from app.core.detector import detect_format

def validate_input_file(file_path: str) -> None:
    """
    Validates the input file:
    - Path exists and is a file.
    - Path is not empty (size > 0).
    - Format is supported.
    - Has read permissions.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")
        
    if not os.path.isfile(file_path):
        raise ValueError(f"O caminho fornecido não é um arquivo: {file_path}")
        
    # Check if format is supported
    detect_format(file_path)
    
    if os.path.getsize(file_path) == 0:
        raise ValueError(f"O arquivo está vazio (tamanho 0 bytes): {file_path}")
        
    # Check read permissions
    try:
        with open(file_path, "rb") as f:
            f.read(10)
    except Exception as e:
        raise PermissionError(f"Sem permissão de leitura no arquivo {file_path}: {e}")

def validate_output_directory(output_dir: str) -> None:
    """
    Validates the output directory:
    - Creates it if it doesn't exist.
    - Checks for write permissions.
    """
    if not output_dir:
        raise ValueError("O diretório de destino não foi especificado.")
        
    if not os.path.exists(output_dir):
        try:
            os.makedirs(output_dir, exist_ok=True)
        except Exception as e:
            raise PermissionError(f"Não foi possível criar o diretório de destino {output_dir}: {e}")
            
    # Check write permission by writing a temporary file
    temp_file = os.path.join(output_dir, ".write_test")
    try:
        with open(temp_file, "w") as f:
            f.write("test")
        os.remove(temp_file)
    except Exception as e:
        raise PermissionError(f"Sem permissão de gravação no diretório {output_dir}: {e}")
