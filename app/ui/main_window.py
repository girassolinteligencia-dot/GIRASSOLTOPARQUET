import os
import subprocess
import logging
from typing import List, Optional

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QGridLayout,
    QLabel, QPushButton, QListWidget, QFileDialog, QMessageBox, QFrame, QSplitter
)
from PySide6.QtCore import Qt, Slot, QUrl, QSize, QRectF
from PySide6.QtGui import QFont, QIcon, QPixmap, QGuiApplication, QDesktopServices, QPainter, QPainterPath, QPen, QColor

from app.ui.drag_drop_area import DragDropArea
from app.ui.settings_panel import SettingsPanel
from app.ui.progress_panel import ProgressPanel
from app.services.job_queue import ConversionWorker
from app.services.config_service import load_config, save_config
from app.services.log_service import log_emitter, setup_logging

def create_neon_icon(icon_type: str) -> QIcon:
    """
    Generates professional, neon-glow outline (vazado) icons programmatically.
    """
    pixmap = QPixmap(64, 64)
    pixmap.fill(Qt.transparent)
    
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    
    glow_color = QColor("#00FF66")
    core_color = QColor("#E6FFE9")
    
    path = QPainterPath()
    
    if icon_type == "conversor":
        # Professional hollowed-out conversion arrows (vazado)
        path.arcMoveTo(QRectF(14, 14, 36, 36), 45)
        path.arcTo(QRectF(14, 14, 36, 36), 45, 270)
        path.moveTo(32, 14)
        path.lineTo(36, 14)
        path.lineTo(36, 10)
        path.arcMoveTo(QRectF(14, 14, 36, 36), 225)
        path.arcTo(QRectF(14, 14, 36, 36), 225, 270)
        path.moveTo(32, 50)
        path.lineTo(28, 50)
        path.lineTo(28, 54)
        
    elif icon_type == "sobre":
        # Outline 'i' info icon inside a circular ring (vazado)
        path.addEllipse(QRectF(14, 14, 36, 36))
        path.addEllipse(QRectF(30, 22, 4, 4))
        path.moveTo(32, 29)
        path.lineTo(32, 41)
        
    elif icon_type == "guia":
        # Outline open book (vazado)
        path.moveTo(32, 45)
        path.quadTo(23, 47, 16, 45)
        path.lineTo(16, 19)
        path.quadTo(23, 21, 32, 19)
        path.quadTo(41, 21, 48, 19)
        path.lineTo(48, 45)
        path.quadTo(41, 47, 32, 45)
        path.moveTo(32, 19)
        path.lineTo(32, 45)
        
    glow_pen = QPen()
    glow_pen.setCapStyle(Qt.RoundCap)
    glow_pen.setJoinStyle(Qt.RoundJoin)
    
    # Wide, low opacity glow
    glow_pen.setWidth(8)
    glow_color.setAlpha(40)
    glow_pen.setColor(glow_color)
    painter.setPen(glow_pen)
    painter.drawPath(path)
    
    # Medium glow
    glow_pen.setWidth(4)
    glow_color.setAlpha(120)
    glow_pen.setColor(glow_color)
    painter.setPen(glow_pen)
    painter.drawPath(path)
    
    # Solid core
    glow_pen.setWidth(2)
    glow_pen.setColor(core_color)
    painter.setPen(glow_pen)
    painter.drawPath(path)
    
    painter.end()
    return QIcon(pixmap)

class MainWindow(QMainWindow):
    """
    Main application window implementing the GIRASSOLtoPARQUET layout:
    - Sidebar (vibrant orange, menu options, offline info)
    - Content area (dashboard grid, Playfair serif typography headers)
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ALL to Parquet")
        
        # Set default window size and limit the minimum size to prevent layout squashing
        self.setMinimumSize(960, 680)
        self.resize(1000, 700)
        
        # Center the window on the screen
        screen = QGuiApplication.primaryScreen()
        if screen:
            screen_geometry = screen.geometry()
            screen_w = screen_geometry.width()
            screen_h = screen_geometry.height()
            
            x = int((screen_w - 850) / 2)
            y = int((screen_h - 600) / 2)
            self.setGeometry(x, y, 850, 600)
        
        # Initialize internal queue paths
        self.queued_paths: List[str] = []
        self.worker: Optional[ConversionWorker] = None
        
        # Load user configuration
        self.config = load_config()
        
        # Setup UI
        self._setup_ui()
        self._apply_theme()
        
        # Pipe log service messages to UI Progress Panel
        log_emitter.log_received.connect(self.progress_panel.append_log)
        
        # Start logging system
        log_dir = setup_logging()
        logging.info(f"Pasta de logs configurada: {log_dir}")
        
        # Apply loaded configurations to UI components
        self.settings_panel.set_settings(self.config)
        self.progress_panel.set_output_dir(self.config.get("output_dir", ""))
        
        # Connect settings changes to save automatically
        self.settings_panel.settings_changed.connect(self._on_settings_changed)
        
        # Initial UI state update
        self._update_ui_state()

    def _setup_ui(self):
        # Central widget uses QHBoxLayout for Sidebar + Content layout
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 1. SIDEBAR (GIRASSOLtoPARQUET Laranja)
        sidebar = QFrame(self)
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(240)
        
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(16, 24, 16, 24)
        sidebar_layout.setSpacing(12)
        
        # Title/Logo Area
        logo_label = QLabel(sidebar)
        logo_path = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "logo.png"))
        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path)
            # Scale to width of 200px while maintaining aspect ratio
            scaled_pixmap = pixmap.scaledToWidth(208, Qt.SmoothTransformation)
            logo_label.setPixmap(scaled_pixmap)
        else:
            logo_label.setText("ALL to Parquet")
            logo_label.setObjectName("SidebarLogo")
        logo_label.setAlignment(Qt.AlignCenter)
        sidebar_layout.addWidget(logo_label)
        
        tagline = QLabel("Conversor Parquet", sidebar)
        tagline.setObjectName("SidebarTagline")
        tagline.setAlignment(Qt.AlignCenter)
        sidebar_layout.addWidget(tagline)
        
        sidebar_layout.addSpacing(24)
        
        # Navigation/Info Cards (Menu Mockup with professional neon outline icons)
        dash_btn = QPushButton(" Conversor", sidebar)
        dash_btn.setObjectName("SidebarBtnActive")
        dash_btn.setCursor(Qt.PointingHandCursor)
        dash_btn.setIcon(create_neon_icon("conversor"))
        dash_btn.setIconSize(QSize(22, 22))
        sidebar_layout.addWidget(dash_btn)
        
        about_btn = QPushButton(" Sobre o app", sidebar)
        about_btn.setObjectName("SidebarBtn")
        about_btn.setCursor(Qt.PointingHandCursor)
        about_btn.clicked.connect(self._show_about_dialog)
        about_btn.setIcon(create_neon_icon("sobre"))
        about_btn.setIconSize(QSize(22, 22))
        sidebar_layout.addWidget(about_btn)
        
        help_btn = QPushButton(" Guia de Uso", sidebar)
        help_btn.setObjectName("SidebarBtn")
        help_btn.setCursor(Qt.PointingHandCursor)
        help_btn.clicked.connect(self._show_help_dialog)
        help_btn.setIcon(create_neon_icon("guia"))
        help_btn.setIconSize(QSize(22, 22))
        sidebar_layout.addWidget(help_btn)
        
        sidebar_layout.addStretch()
        

        
        main_layout.addWidget(sidebar)
        
        # 2. CONTENT AREA (Light gray background)
        content_pane = QWidget(self)
        content_pane.setObjectName("ContentPane")
        content_layout = QVBoxLayout(content_pane)
        content_layout.setContentsMargins(24, 24, 24, 24)
        content_layout.setSpacing(16)
        

        
        subheader_lbl = QLabel("Converta seus arquivos locais em lote de forma extremamente segura e sem dependência de internet.", self)
        subheader_lbl.setObjectName("ContentSubheader")
        subheader_lbl.setWordWrap(True)
        content_layout.addWidget(subheader_lbl)
        
        # Grid layout for Dashboard panels
        dashboard_grid = QGridLayout()
        dashboard_grid.setSpacing(16)
        
        # Left Panel (Input files)
        left_card = QFrame(self)
        left_card.setObjectName("DashboardCard")
        left_layout = QVBoxLayout(left_card)
        left_layout.setContentsMargins(16, 16, 16, 16)
        left_layout.setSpacing(12)
        
        input_title = QLabel("Arquivos Origem", left_card)
        input_title.setStyleSheet("font-family: 'IBM Plex Mono', monospace; font-size: 15px; font-weight: 700; color: #00FF66;")
        left_layout.addWidget(input_title)
        
        # Drag & Drop Zone
        self.drag_drop_area = DragDropArea(left_card)
        self.drag_drop_area.files_dropped.connect(self._on_files_added)
        left_layout.addWidget(self.drag_drop_area)
        
        # Manual Add Buttons Row
        btn_row = QHBoxLayout()
        self.add_files_btn = QPushButton("Selecionar arquivos", left_card)
        self.add_files_btn.setObjectName("SecondaryBtn")
        self.add_files_btn.setCursor(Qt.PointingHandCursor)
        self.add_files_btn.clicked.connect(self._on_select_files_clicked)
        
        self.add_folder_btn = QPushButton("Selecionar pasta", left_card)
        self.add_folder_btn.setObjectName("SecondaryBtn")
        self.add_folder_btn.setCursor(Qt.PointingHandCursor)
        self.add_folder_btn.clicked.connect(self._on_select_folder_clicked)
        
        btn_row.addWidget(self.add_files_btn)
        btn_row.addWidget(self.add_folder_btn)
        left_layout.addLayout(btn_row)
        
        # Queue List Widget
        queue_lbl = QLabel("Fila de Processamento:", left_card)
        queue_lbl.setStyleSheet("font-family: 'IBM Plex Mono', monospace; font-size: 13px; font-weight: 600; color: #A8CBB0;")
        left_layout.addWidget(queue_lbl)
        
        self.file_list_widget = QListWidget(left_card)
        self.file_list_widget.setObjectName("FileListWidget")
        left_layout.addWidget(self.file_list_widget)
        
        # Queue Action Bar
        queue_actions = QHBoxLayout()
        self.clear_queue_btn = QPushButton("Limpar lista", left_card)
        self.clear_queue_btn.setObjectName("DangerBtn")
        self.clear_queue_btn.setCursor(Qt.PointingHandCursor)
        self.clear_queue_btn.clicked.connect(self._on_clear_queue_clicked)
        self.clear_queue_btn.setEnabled(False)
        queue_actions.addWidget(self.clear_queue_btn)
        queue_actions.addStretch()
        left_layout.addLayout(queue_actions)
        
        # Right Panel (Settings & Progress Stacked)
        right_layout = QVBoxLayout()
        right_layout.setSpacing(16)
        
        self.settings_panel = SettingsPanel(self)
        right_layout.addWidget(self.settings_panel)
        
        self.progress_panel = ProgressPanel(self)
        right_layout.addWidget(self.progress_panel)
        
        # Primary Action Converter Button & Aux Buttons
        action_layout = QHBoxLayout()
        action_layout.setSpacing(12)
        
        self.open_output_btn = QPushButton("Abrir pasta de saída", self)
        self.open_output_btn.setObjectName("SecondaryBtn")
        self.open_output_btn.setCursor(Qt.PointingHandCursor)
        self.open_output_btn.clicked.connect(self._on_open_output_clicked)
        self.open_output_btn.setEnabled(False)
        
        self.cancel_btn = QPushButton("Cancelar", self)
        self.cancel_btn.setObjectName("DangerBtn")
        self.cancel_btn.setCursor(Qt.PointingHandCursor)
        self.cancel_btn.clicked.connect(self._on_cancel_clicked)
        self.cancel_btn.setEnabled(False)
        
        self.convert_btn = QPushButton("Converter", self)
        self.convert_btn.setObjectName("PrimaryConvertBtn")
        self.convert_btn.setCursor(Qt.PointingHandCursor)
        self.convert_btn.setEnabled(False)
        self.convert_btn.clicked.connect(self._on_convert_clicked)
        
        action_layout.addWidget(self.open_output_btn)
        action_layout.addWidget(self.cancel_btn)
        action_layout.addWidget(self.convert_btn)
        
        right_layout.addLayout(action_layout)
        
        # Add Columns to Dashboard Grid
        dashboard_grid.addWidget(left_card, 0, 0)
        dashboard_grid.addLayout(right_layout, 0, 1)
        
        dashboard_grid.setColumnStretch(0, 5)
        dashboard_grid.setColumnStretch(1, 5)
        
        content_layout.addLayout(dashboard_grid)
        
        # Footer (with interactive link to website)
        footer_lbl = QLabel(self)
        footer_lbl.setText("Desenvolvido por <a href='https://girassolinteligencia.com.br/'>Girassol Inteligência</a> - Todos os Direitos Reservados")
        footer_lbl.setObjectName("ContentFooter")
        footer_lbl.setAlignment(Qt.AlignCenter)
        footer_lbl.setOpenExternalLinks(True)
        content_layout.addWidget(footer_lbl)
        
        main_layout.addWidget(content_pane)

    def _apply_theme(self):
        # IBM Terminal Aesthetic CSS (Green on dark, monospace)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #020403;
            }
            #Sidebar {
                background-color: #071F17; 
                border-right: 1px solid #2E3A34;
            }
            #SidebarLogo {
                font-family: 'IBM Plex Mono', monospace;
                font-size: 26px;
                font-weight: 800;
                color: #00FF66;
            }
            #SidebarTagline {
                font-family: 'IBM Plex Mono', monospace;
                font-size: 13px;
                color: #A8CBB0;
                padding-bottom: 8px;
            }
            #SidebarBtn {
                text-align: left;
                padding: 12px 18px;
                border: none;
                border-radius: 4px;
                background-color: transparent;
                color: #A8CBB0;
                font-family: 'IBM Plex Mono', monospace;
                font-size: 14px;
                font-weight: 600;
            }
            #SidebarBtn:hover {
                background-color: #1A241F;
                color: #00FF66;
            }
            #SidebarBtnActive {
                text-align: left;
                padding: 12px 18px;
                border: 1px solid #00FF66;
                border-radius: 4px;
                background-color: #0A261C;
                color: #00FF66;
                font-family: 'IBM Plex Mono', monospace;
                font-size: 14px;
                font-weight: 600;
            }
            #SidebarUserBox {
                background-color: #00B050;
                border-radius: 4px;
                border: none;
            }
            #ContentPane {
                background-color: #020403;
            }
            #ContentHeader {
                font-family: 'IBM Plex Mono', monospace;
                font-size: 24px;
                font-weight: 700;
                color: #00FF66;
            }
            #ContentSubheader {
                font-family: 'IBM Plex Mono', monospace;
                font-size: 13px;
                color: #A8CBB0;
                padding-bottom: 8px;
            }
            #ContentFooter {
                font-family: 'IBM Plex Mono', monospace;
                font-size: 11px;
                color: #5FAF7A;
                margin-top: 8px;
            }
            #ContentFooter a {
                color: #00FF66;
                text-decoration: none;
                font-weight: bold;
            }
            #ContentFooter a:hover {
                text-decoration: underline;
                color: #00B050;
            }
            #DashboardCard {
                background-color: #071F17;
                border: 1px solid #2E3A34;
                border-radius: 4px;
            }
            #FileListWidget {
                border: 1px solid #2E3A34;
                border-radius: 4px;
                background-color: #020403;
                padding: 4px;
                font-family: 'IBM Plex Mono', monospace;
                font-size: 12px;
                color: #E6FFE9;
            }
            #SecondaryBtn {
                padding: 8px 12px;
                border: 1px solid #FF8C00;
                border-radius: 4px;
                background-color: transparent;
                color: #FF8C00;
                font-family: 'IBM Plex Mono', monospace;
                font-weight: 600;
                font-size: 12px;
            }
            #SecondaryBtn:hover {
                background-color: #1A241F;
                border-color: #FFB000;
            }
            #DangerBtn {
                padding: 6px 12px;
                border: 1px solid #FF4D4D;
                border-radius: 4px;
                background-color: transparent;
                color: #FF4D4D;
                font-family: 'IBM Plex Mono', monospace;
                font-weight: 600;
                font-size: 11px;
            }
            #DangerBtn:hover {
                background-color: #1A241F;
            }
            #DangerBtn:disabled, #SecondaryBtn:disabled {
                border-color: #2E3A34;
                color: #5FAF7A;
                background-color: transparent;
            }
            #PrimaryConvertBtn {
                padding: 12px;
                border: 1px solid #00FF66;
                border-radius: 4px;
                background-color: #00B050;
                color: #020403;
                font-family: 'IBM Plex Mono', monospace;
                font-weight: 700;
                font-size: 15px;
            }
            #PrimaryConvertBtn:hover {
                background-color: #00FF66;
            }
            #PrimaryConvertBtn:disabled {
                background-color: #1A241F;
                border-color: #2E3A34;
                color: #5FAF7A;
            }
        """)

    @Slot(list)
    def _on_files_added(self, paths: List[str]):
        # Add files to queue and resolve duplicates
        resolved_files = self._resolve_supported_files(paths)
        for path in resolved_files:
            if path not in self.queued_paths:
                self.queued_paths.append(path)
                filename = os.path.basename(path)
                self.file_list_widget.addItem(filename)
                
                # Add tooltip with full path
                item = self.file_list_widget.item(self.file_list_widget.count() - 1)
                item.setToolTip(path)
                
        # If output directory is empty, default it to the directory of the first added file
        settings = self.settings_panel.get_settings()
        if not settings["output_dir"] and self.queued_paths:
            first_file_dir = os.path.dirname(self.queued_paths[0])
            self.settings_panel.output_path_input.setText(first_file_dir)
            
        self._update_ui_state()

    def _resolve_supported_files(self, paths: List[str]) -> List[str]:
        # Quick check for supported files
        from app.core.detector import SUPPORTED_FORMATS
        resolved = []
        for path in paths:
            if os.path.isfile(path):
                _, ext = os.path.splitext(path.lower())
                if ext in SUPPORTED_FORMATS:
                    resolved.append(path)
            elif os.path.isdir(path):
                for root, _, files in os.walk(path):
                    for file in files:
                        _, ext = os.path.splitext(file.lower())
                        if ext in SUPPORTED_FORMATS:
                            resolved.append(os.path.join(root, file))
        return resolved

    def _on_select_files_clicked(self):
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Selecionar arquivos origem",
            "",
            "Arquivos de Dados (*.csv *.xlsx *.json *.ndjson *.jsonl);;Todos os arquivos (*.*)"
        )
        if files:
            self._on_files_added(files)

    def _on_select_folder_clicked(self):
        folder = QFileDialog.getExistingDirectory(self, "Selecionar pasta origem")
        if folder:
            self._on_files_added([folder])

    def _on_clear_queue_clicked(self):
        self.queued_paths.clear()
        self.file_list_widget.clear()
        self._update_ui_state()

    def _on_settings_changed(self):
        # Retrieve current settings and save config file
        settings = self.settings_panel.get_settings()
        self.config.update(settings)
        save_config(self.config)
        
        # Keep ProgressPanel updated with the last output dir
        self.progress_panel.set_output_dir(settings["output_dir"])
        
        # Atualiza os botões (como o de Converter) caso a pasta tenha sido preenchida
        self._update_ui_state()

    def _update_ui_state(self):
        has_items = len(self.queued_paths) > 0
        has_dest = bool(self.settings_panel.get_settings()["output_dir"])
        
        self.convert_btn.setEnabled(has_items and has_dest)
        self.clear_queue_btn.setEnabled(has_items)
        self.open_output_btn.setEnabled(has_dest)

    def _on_convert_clicked(self):
        settings = self.settings_panel.get_settings()
        if not settings["output_dir"]:
            QMessageBox.warning(self, "Aviso", "Por favor, selecione uma pasta de destino.")
            return
            
        # Freeze UI during operation
        self.set_ui_frozen(True)
        self.progress_panel.clear_log()
        self.progress_panel.set_progress(0)
        self.progress_panel.set_status_summary("Processando fila...")
        
        # Instantiate and run QThread conversion queue
        self.worker = ConversionWorker(
            paths=self.queued_paths,
            output_dir=settings["output_dir"],
            normalize_cols=settings["normalize_cols"],
            flatten_json=settings["flatten_json"],
            process_all_sheets=settings["process_all_sheets"],
            preserve_sensitive=settings["preserve_sensitive"],
            continue_on_error=settings["continue_on_error"],
            generate_report=settings["generate_report"],
            compression=settings["compression"],
            preset=settings.get("preset", "default")
        )
        
        # Connect worker signals
        self.worker.status_message.connect(self.progress_panel.append_log)
        self.worker.progress_changed.connect(self.progress_panel.set_progress)
        self.worker.queue_finished.connect(self._on_queue_finished)
        
        # Launch background process
        self.worker.start()

    def _on_cancel_clicked(self):
        if self.worker and self.worker.isRunning():
            self.progress_panel.append_log("\n[AVISO] Solicitando cancelamento...")
            self.worker.stop()

    def _on_queue_finished(self, summary: dict):
        # Restore UI
        self.set_ui_frozen(False)
        self.worker = None
        
        success = summary["sucessos"]
        errors = summary["erros"]
        total = summary["arquivos_processados"]
        lines = summary["total_linhas"]
        out_dir = summary["pasta_saida"]
        
        self.progress_panel.set_status_summary(f"Fila finalizada! Sucessos: {success} | Erros: {errors}")
        
        # Display completion alert box
        msg = (
            f"Processamento concluído!\n\n"
            f"• Arquivos processados: {total}\n"
            f"• Convertidos com sucesso: {success}\n"
            f"• Arquivos com erro: {errors}\n"
            f"• Total de linhas convertidas: {lines}\n\n"
            f"Pasta de saída:\n{out_dir}"
        )
        
        if errors > 0:
            QMessageBox.warning(self, "Fila de Conversão Concluída", msg)
        else:
            QMessageBox.information(self, "Fila de Conversão Concluída", msg)

    def set_ui_frozen(self, frozen: bool):
        """Freezes or unfreezes inputs and action buttons during execution."""
        self.add_files_btn.setEnabled(not frozen)
        self.add_folder_btn.setEnabled(not frozen)
        self.clear_queue_btn.setEnabled(not frozen and len(self.queued_paths) > 0)
        self.drag_drop_area.setAcceptDrops(not frozen)
        self.settings_panel.setEnabled(not frozen)
        self.convert_btn.setEnabled(not frozen)
        self.cancel_btn.setEnabled(frozen)
        self.open_output_btn.setEnabled(not frozen and bool(self.settings_panel.get_settings()["output_dir"]))
        self.progress_panel.set_running_state(frozen)

    def _on_open_output_clicked(self):
        out_dir = self.settings_panel.get_settings()["output_dir"]
        if out_dir and os.path.exists(out_dir):
            try:
                subprocess.Popen(f'explorer "{os.path.abspath(out_dir)}"')
            except Exception as e:
                self.progress_panel.append_log(f"[ERRO] Não foi possível abrir a pasta: {e}")

    def _show_about_dialog(self):
        about_text = (
            "<h3>Conversor Parquet Offline</h3>"
            "<p>Versão 1.0.0 (Windows Desktop)</p>"
            "<p>Esta aplicação foi construída para funcionar de maneira 100% isolada e segura. "
            "Nenhum dado é enviado para a nuvem.</p>"
            "<p><b>Stack Técnica:</b> Python, PySide6, Polars, PyArrow, DuckDB e PyInstaller.</p>"
            "<p>© 2026 - Uso Profissional</p>"
        )
        QMessageBox.about(self, "Sobre a aplicação", about_text)

    def _show_help_dialog(self):
        from app.ui.help_dialog import HelpDialog
        dialog = HelpDialog(self)
        dialog.exec()
