import os
import subprocess
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QProgressBar, QPlainTextEdit, QPushButton, QFrame
)
from PySide6.QtGui import QTextCursor
from PySide6.QtCore import Qt, Signal

class ProgressPanel(QFrame):
    """
    Console/Progress card containing:
    - Custom styled ProgressBar.
    - Read-only QPlainTextEdit console for live log streaming.
    """
    cancel_requested = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("ProgressPanel")
        self._setup_ui()
        self._apply_style()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)
        
        # Header & Status Label
        header_layout = QHBoxLayout()
        self.status_title = QLabel("Progresso e Log de Execução", self)
        self.status_title.setStyleSheet("font-family: 'IBM Plex Mono', monospace; font-size: 14px; font-weight: 700; color: #00FF66;")
        
        self.status_summary = QLabel("", self)
        self.status_summary.setStyleSheet("font-family: 'IBM Plex Mono', monospace; font-size: 12px; color: #FFB000; font-weight: 500;")
        
        header_layout.addWidget(self.status_title)
        header_layout.addStretch()
        header_layout.addWidget(self.status_summary)
        layout.addLayout(header_layout)
        
        # Progress Bar
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("%p%")
        layout.addWidget(self.progress_bar)
        
        # Console Log Box
        self.console = QPlainTextEdit(self)
        self.console.setReadOnly(True)
        self.console.setObjectName("ConsoleBox")
        self.console.setPlaceholderText("Os logs de conversão em tempo real serão exibidos aqui...")
        self.console.setMinimumHeight(60)
        layout.addWidget(self.console)

    def _apply_style(self):
        self.setStyleSheet("""
            #ProgressPanel {
                background-color: #071F17;
                border: 1px solid #2E3A34;
                border-radius: 4px;
            }
            QProgressBar {
                border: 1px solid #2E3A34;
                border-radius: 2px;
                background-color: #020403;
                height: 12px;
                text-align: center;
                color: #00FF66;
                font-family: 'IBM Plex Mono', monospace;
                font-size: 10px;
            }
            QProgressBar::chunk {
                background-color: #00B050;
                border-radius: 2px;
            }
            #ConsoleBox {
                background-color: #020403;
                color: #00FF66;
                font-family: 'IBM Plex Mono', 'Consolas', monospace;
                font-size: 12px;
                border: 1px solid #2E3A34;
                border-radius: 4px;
                padding: 8px;
                min-height: 60px;
            }
        """)

    def set_output_dir(self, directory: str):
        self._current_output_dir = directory

    def append_log(self, text: str):
        """Appends log text to the console and scrolls to the bottom."""
        self.console.appendPlainText(text)
        # Ensure scrollbar moves to bottom
        self.console.moveCursor(QTextCursor.End)

    def clear_log(self):
        self.console.clear()

    def set_progress(self, value: int):
        self.progress_bar.setValue(value)

    def set_running_state(self, is_running: bool):
        pass

    def set_status_summary(self, text: str):
        self.status_summary.setText(text)
