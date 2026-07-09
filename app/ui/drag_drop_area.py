import os
from typing import List
from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QDragEnterEvent, QDragMoveEvent, QDropEvent

class DragDropArea(QFrame):
    """
    Custom widget providing a Drag & Drop zone for files and folders.
    Changes visual appearance (border, background) on hover.
    Emits files_dropped signal with a list of file paths.
    """
    files_dropped = Signal(list)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setObjectName("DragDropArea")
        self.setMinimumHeight(180)
        
        self.layout = QVBoxLayout(self)
        self.layout.setAlignment(Qt.AlignCenter)
        
        # Subtitle icon (Emoji representation of database/file for sleek offline design)
        self.icon_label = QLabel("📥", self)
        self.icon_label.setStyleSheet("font-size: 42px; margin-bottom: 8px; color: #00FF66;")
        self.icon_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.icon_label)
        
        # Primary prompt text
        self.text_label = QLabel("Arraste arquivos ou pastas aqui", self)
        self.text_label.setObjectName("DragDropText")
        self.text_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.text_label)
        
        # Secondary text
        self.subtext_label = QLabel("Formatos aceitos: CSV, Excel, JSON, NDJSON, JSONL", self)
        self.subtext_label.setObjectName("DragDropSubtext")
        self.subtext_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.subtext_label)
        
        self._apply_normal_style()

    def _apply_normal_style(self):
        self.setStyleSheet("""
            #DragDropArea {
                border: 2px dashed #2E3A34;
                border-radius: 4px;
                background-color: #071F17;
            }
            #DragDropText {
                font-family: 'IBM Plex Mono', monospace;
                font-size: 15px;
                font-weight: 600;
                color: #00FF66;
            }
            #DragDropSubtext {
                font-family: 'IBM Plex Mono', monospace;
                font-size: 12px;
                color: #A8CBB0;
                margin-top: 4px;
            }
        """)

    def _apply_active_style(self):
        # Styled active drag hover state - changes border to IBM terminal active color
        self.setStyleSheet("""
            #DragDropArea {
                border: 2px solid #00FF66;
                border-radius: 4px;
                background-color: #0A261C;
            }
            #DragDropText {
                font-family: 'IBM Plex Mono', monospace;
                font-size: 15px;
                font-weight: 600;
                color: #00FF66;
            }
            #DragDropSubtext {
                font-family: 'IBM Plex Mono', monospace;
                font-size: 12px;
                color: #FF8C00;
                margin-top: 4px;
            }
        """)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self._apply_active_style()
        else:
            event.ignore()

    def dragMoveEvent(self, event: QDragMoveEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        self._apply_normal_style()
        event.accept()

    def dropEvent(self, event: QDropEvent):
        self._apply_normal_style()
        if event.mimeData().hasUrls():
            paths = []
            for url in event.mimeData().urls():
                local_path = url.toLocalFile()
                if local_path and os.path.exists(local_path):
                    paths.append(local_path)
            
            if paths:
                self.files_dropped.emit(paths)
            event.acceptProposedAction()
        else:
            event.ignore()
