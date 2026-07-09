import os
import logging
from typing import List, Dict, Any
from PySide6.QtCore import QThread, Signal

from app.core.converter import convert_file
from app.core.detector import SUPPORTED_FORMATS
from app.services.report_service import write_reports

class ConversionWorker(QThread):
    """
    Background worker thread that processes a queue of files and directories.
    Emits signals to update the UI on progress, status logs, and final completion.
    """
    progress_changed = Signal(int)       # 0 to 100
    status_message = Signal(str)         # Realtime console message
    file_started = Signal(str)           # Path of the file being processed
    file_finished = Signal(str, dict)     # Path of finished file and its report dict
    queue_finished = Signal(dict)        # Summary dictionary of all jobs done
    
    def __init__(
        self,
        paths: List[str],
        output_dir: str,
        normalize_cols: bool,
        flatten_json: bool,
        process_all_sheets: bool,
        preserve_sensitive: bool,
        continue_on_error: bool,
        generate_report: bool,
        compression: str,
        preset: str = "default"
    ):
        super().__init__()
        self.paths = paths
        self.output_dir = output_dir
        self.normalize_cols = normalize_cols
        self.flatten_json = flatten_json
        self.process_all_sheets = process_all_sheets
        self.preserve_sensitive = preserve_sensitive
        self.continue_on_error = continue_on_error
        self.generate_report = generate_report
        self.compression = compression
        self.preset = preset
        self._is_running = True

    def stop(self):
        """Requests the worker to stop processing early."""
        self._is_running = False

    def run(self):
        # 1. Resolve files list (expanding folders)
        files_to_process = self._resolve_paths(self.paths)
        total_files = len(files_to_process)
        
        logging.info(f"Fila de conversão iniciada. Total de arquivos: {total_files}")
        self.status_message.emit(f"Fila iniciada: {total_files} arquivos encontrados para conversão.")
        
        if total_files == 0:
            self.progress_changed.emit(100)
            self.queue_finished.emit({
                "arquivos_processados": 0,
                "sucessos": 0,
                "erros": 0,
                "total_linhas": 0,
                "pasta_saida": self.output_dir
            })
            return

        success_count = 0
        error_count = 0
        total_rows_processed = 0
        
        for index, file_path in enumerate(files_to_process, start=1):
            if not self._is_running:
                logging.warning("Fila cancelada pelo usuário.")
                self.status_message.emit("Conversão cancelada pelo usuário.")
                break
                
            file_name = os.path.basename(file_path)
            logging.info(f"Processando arquivo [{index}/{total_files}]: {file_name}")
            self.status_message.emit(f"\n[{index}/{total_files}] Processando: {file_name}...")
            self.file_started.emit(file_path)
            
            # Run conversion
            try:
                report = convert_file(
                    file_path=file_path,
                    output_dir=self.output_dir,
                    normalize_cols=self.normalize_cols,
                    flatten_json=self.flatten_json,
                    process_all_sheets=self.process_all_sheets,
                    preserve_sensitive=self.preserve_sensitive,
                    continue_on_error=self.continue_on_error,
                    compression=self.compression,
                    preset=self.preset
                )
                
                if report["status"] in ("sucesso", "sucesso_com_alertas"):
                    success_count += 1
                    total_rows_processed += report["linhas_lidas"]
                    msg = f"Sucesso: {file_name} convertido ({report['linhas_lidas']} linhas)."
                    if report["status"] == "sucesso_com_alertas":
                        msg += f" (Alertas: {len(report['ndjson_linhas_invalidas'])} linhas inválidas ignoradas)"
                    logging.info(msg)
                    self.status_message.emit(msg)
                    
                    # Generate reports in destination folder if checked
                    if self.generate_report:
                        json_rep, txt_rep = write_reports(report, self.output_dir)
                        self.status_message.emit(f"Relatório gravado: {os.path.basename(txt_rep)}")
                else:
                    error_count += 1
                    err_msg = report["erros"][0] if report["erros"] else "Erro desconhecido"
                    logging.error(f"Erro ao converter {file_name}: {err_msg}")
                    self.status_message.emit(f"Erro em {file_name}: {err_msg}")
                    
                    # Write failure report if checked
                    if self.generate_report:
                        write_reports(report, self.output_dir)
                        
                    if not self.continue_on_error:
                        logging.warning("Interrompendo fila por conta de erro (opção de continuar desmarcada).")
                        self.status_message.emit("Fila interrompida devido ao erro.")
                        self.file_finished.emit(file_path, report)
                        # Progress reflects the stop point
                        progress = int((index / total_files) * 100)
                        self.progress_changed.emit(progress)
                        break
                        
                self.file_finished.emit(file_path, report)
                
            except Exception as e:
                error_count += 1
                logging.exception(f"Exceção não tratada ao processar {file_name}: {e}")
                self.status_message.emit(f"Falha crítica em {file_name}: {e}")
                if not self.continue_on_error:
                    break
                    
            # Update progress bar
            progress = int((index / total_files) * 100)
            self.progress_changed.emit(progress)

        summary = {
            "arquivos_processados": success_count + error_count,
            "sucessos": success_count,
            "erros": error_count,
            "total_linhas": total_rows_processed,
            "pasta_saida": self.output_dir
        }
        
        logging.info(f"Fila concluída. Sucessos: {success_count}, Erros: {error_count}, Linhas totais: {total_rows_processed}")
        self.queue_finished.emit(summary)

    def _resolve_paths(self, paths: List[str]) -> List[str]:
        """Resolves a list of files/folders into a list of absolute paths of supported files."""
        resolved = []
        for path in paths:
            if not os.path.exists(path):
                continue
            if os.path.isfile(path):
                _, ext = os.path.splitext(path.lower())
                if ext in SUPPORTED_FORMATS:
                    resolved.append(os.path.abspath(path))
            elif os.path.isdir(path):
                # Search directory for supported files
                for root, _, files in os.walk(path):
                    for file in files:
                        _, ext = os.path.splitext(file.lower())
                        if ext in SUPPORTED_FORMATS:
                            resolved.append(os.path.abspath(os.path.join(root, file)))
                            
        # De-duplicate and sort alphabetically
        return sorted(list(set(resolved)))
