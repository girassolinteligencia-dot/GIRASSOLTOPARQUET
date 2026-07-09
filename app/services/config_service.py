import os
import json
from typing import Dict, Any

DEFAULT_CONFIG: Dict[str, Any] = {
    "output_dir": "",
    "normalize_cols": True,
    "flatten_json": False,
    "generate_report": True,
    "process_all_sheets": True,
    "preserve_sensitive": True,
    "continue_on_error": True,
    "compression": "snappy",
    "preset": "default"
}

def get_config_file_path() -> str:
    """Returns the configuration file path in AppData."""
    local_app_data = os.path.expandvars(r"%LOCALAPPDATA%")
    if local_app_data == "%LOCALAPPDATA%":
        local_app_data = os.path.join(os.path.expanduser("~"), "AppData", "Local")
    config_dir = os.path.join(local_app_data, "ConversorParquetOffline")
    os.makedirs(config_dir, exist_ok=True)
    return os.path.join(config_dir, "config.json")

def load_config() -> Dict[str, Any]:
    """Loads the settings. Falls back to default settings if file doesn't exist."""
    path = get_config_file_path()
    if not os.path.exists(path):
        return DEFAULT_CONFIG.copy()
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Ensure all keys in DEFAULT_CONFIG exist in loaded data
            config = DEFAULT_CONFIG.copy()
            config.update(data)
            return config
    except Exception:
        return DEFAULT_CONFIG.copy()

def save_config(config: Dict[str, Any]) -> None:
    """Saves the user configuration."""
    path = get_config_file_path()
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
    except Exception:
        pass
