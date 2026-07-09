import os
import logging
from PySide6.QtCore import QObject, Signal

class LogSignalEmitter(QObject):
    log_received = Signal(str)

class QtLogHandler(logging.Handler):
    """Custom logging handler that forwards log records to a PySide6 signal emitter."""
    def __init__(self, emitter: LogSignalEmitter):
        super().__init__()
        self.emitter = emitter

    def emit(self, record):
        try:
            msg = self.format(record)
            self.emitter.log_received.emit(msg)
        except Exception:
            self.handleError(record)

# Global emitter instance
log_emitter = LogSignalEmitter()

def setup_logging() -> str:
    """
    Sets up the application logger.
    Logs are written to C:\\Users\\<user>\\AppData\\Local\\ConversorParquetOffline\\logs\\app.log
    Also configures a handler to stream logs to the PySide6 interface.
    Returns the log directory path.
    """
    # Create the directory under Local AppData
    local_app_data = os.path.expandvars(r"%LOCALAPPDATA%")
    if local_app_data == "%LOCALAPPDATA%":  # If env var is not set, fallback to user profile
        local_app_data = os.path.join(os.path.expanduser("~"), "AppData", "Local")
        
    log_dir = os.path.join(local_app_data, "ConversorParquetOffline", "logs")
    os.makedirs(log_dir, exist_ok=True)
    
    log_file = os.path.join(log_dir, "app.log")
    
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # Remove existing handlers to avoid duplicates on re-init
    for h in logger.handlers[:]:
        logger.removeHandler(h)
        
    # File handler
    try:
        fh = logging.FileHandler(log_file, encoding="utf-8")
        fh.setLevel(logging.INFO)
        file_formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] (%(filename)s:%(lineno)d): %(message)s")
        fh.setFormatter(file_formatter)
        logger.addHandler(fh)
    except Exception as e:
        # Fallback to stdout if file cannot be opened
        print(f"Erro ao inicializar arquivo de log: {e}")
        
    # Qt signal handler
    qh = QtLogHandler(log_emitter)
    qh.setLevel(logging.INFO)
    qt_formatter = logging.Formatter("[%(asctime)s] %(message)s", datefmt="%H:%M:%S")
    qh.setFormatter(qt_formatter)
    logger.addHandler(qh)
    
    # Console handler (for debug/terminal run)
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(qt_formatter)
    logger.addHandler(ch)
    
    logging.info("=== Serviço de logs iniciado ===")
    logging.info(f"Diretório de logs: {log_dir}")
    
    return log_dir
