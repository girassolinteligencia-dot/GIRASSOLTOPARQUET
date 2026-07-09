import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QLineEdit, QPushButton, QCheckBox, QComboBox, QFileDialog, QFrame
)
from PySide6.QtCore import Qt, Signal

class SettingsPanel(QFrame):
    """
    Form-like card layout containing configuration settings for Parquet conversion:
    - Output directory selection.
    - Checkboxes for conversion features.
    - Compression level dropdown.
    """
    settings_changed = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("SettingsPanel")
        self._setup_ui()
        self._apply_style()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)
        
        # Section Header
        header = QLabel("Configurações de Conversão", self)
        header.setStyleSheet("font-family: 'IBM Plex Mono', monospace; font-size: 15px; font-weight: 700; color: #00FF66;")
        main_layout.addWidget(header)
        
        # 0. Preset Selection Row
        preset_layout = QHBoxLayout()
        preset_layout.setSpacing(8)
        
        preset_label = QLabel("Perfil de Uso:", self)
        preset_label.setStyleSheet("font-family: 'IBM Plex Mono', monospace; font-size: 13px; font-weight: 600; color: #A8CBB0;")
        
        self.preset_combo = QComboBox(self)
        self.preset_combo.setObjectName("PresetCombo")
        self.preset_combo.addItems([
            "Preservação Máxima (Padrão)",
            "BI de Dados (Power BI / SQL)",
            "GIS & Geoprocessamento"
        ])
        self.preset_combo.currentTextChanged.connect(self._on_preset_changed)
        
        preset_layout.addWidget(preset_label)
        preset_layout.addWidget(self.preset_combo)
        preset_layout.addStretch()
        main_layout.addLayout(preset_layout)
        
        # 1. Output Path Row
        path_layout = QHBoxLayout()
        path_layout.setSpacing(8)
        
        self.output_path_input = QLineEdit(self)
        self.output_path_input.setPlaceholderText("Selecione a pasta de destino...")
        self.output_path_input.setObjectName("PathInput")
        self.output_path_input.textChanged.connect(self._on_setting_changed)
        
        self.browse_btn = QPushButton("Selecionar destino", self)
        self.browse_btn.setObjectName("BrowseButton")
        self.browse_btn.setCursor(Qt.PointingHandCursor)
        self.browse_btn.clicked.connect(self._on_browse_clicked)
        
        path_layout.addWidget(self.output_path_input, 8)
        path_layout.addWidget(self.browse_btn, 2)
        main_layout.addLayout(path_layout)
        
        # 2. Checkboxes Layout (Stacked vertically for perfect responsiveness)
        checkboxes_layout = QVBoxLayout()
        checkboxes_layout.setSpacing(8)
        
        self.normalize_cols_cb = QCheckBox("Normalizar nomes das colunas", self)
        self.normalize_cols_cb.stateChanged.connect(self._on_setting_changed)
        
        self.flatten_json_cb = QCheckBox("Achatar JSON aninhado", self)
        self.flatten_json_cb.stateChanged.connect(self._on_setting_changed)
        
        self.generate_report_cb = QCheckBox("Gerar relatório de conversão", self)
        self.generate_report_cb.stateChanged.connect(self._on_setting_changed)
        
        self.process_all_sheets_cb = QCheckBox("Processar todas as abas do Excel", self)
        self.process_all_sheets_cb.stateChanged.connect(self._on_setting_changed)
        
        self.preserve_sensitive_cb = QCheckBox("Preservar campos sensíveis como texto", self)
        self.preserve_sensitive_cb.stateChanged.connect(self._on_setting_changed)
        
        self.continue_on_error_cb = QCheckBox("Continuar conversão mesmo com erro", self)
        self.continue_on_error_cb.stateChanged.connect(self._on_setting_changed)
        
        # Add to layout
        checkboxes_layout.addWidget(self.normalize_cols_cb)
        checkboxes_layout.addWidget(self.flatten_json_cb)
        checkboxes_layout.addWidget(self.generate_report_cb)
        checkboxes_layout.addWidget(self.process_all_sheets_cb)
        checkboxes_layout.addWidget(self.preserve_sensitive_cb)
        checkboxes_layout.addWidget(self.continue_on_error_cb)
        
        main_layout.addLayout(checkboxes_layout)
        
        # 3. Compression Choice Row
        comp_layout = QHBoxLayout()
        comp_layout.setSpacing(8)
        
        comp_label = QLabel("Compressão Parquet:", self)
        comp_label.setObjectName("CompLabel")
        
        self.compression_combo = QComboBox(self)
        self.compression_combo.setObjectName("CompCombo")
        self.compression_combo.addItems(["Snappy", "Zstd", "Nenhuma"])
        self.compression_combo.currentTextChanged.connect(self._on_setting_changed)
        
        comp_layout.addWidget(comp_label)
        comp_layout.addWidget(self.compression_combo)
        comp_layout.addStretch()
        
        main_layout.addLayout(comp_layout)

    def _on_setting_changed(self, *args, **kwargs):
        self.settings_changed.emit()

    def _apply_style(self):
        assets_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets"))
        checkmark_path = os.path.join(assets_dir, "checkmark.png").replace("\\", "/")
        
        self.setStyleSheet(f"""
            #SettingsPanel {{
                background-color: #071F17;
                border: 1px solid #2E3A34;
                border-radius: 4px;
            }}
            #PathInput {{
                padding: 8px 12px;
                border: 1px solid #2E3A34;
                border-radius: 4px;
                font-family: 'IBM Plex Mono', monospace;
                font-size: 13px;
                background-color: #020403;
                color: #E6FFE9;
            }}
            #PathInput:focus {{
                border: 1px solid #00FF66;
                background-color: #031A12;
            }}
            #BrowseButton {{
                padding: 8px 14px;
                border: 1px solid #FF8C00;
                border-radius: 4px;
                background-color: transparent;
                color: #FF8C00;
                font-family: 'IBM Plex Mono', monospace;
                font-weight: 600;
                font-size: 13px;
            }}
            #BrowseButton:hover {{
                background-color: #1A241F;
            }}
            QCheckBox {{
                font-family: 'IBM Plex Mono', monospace;
                font-size: 13px;
                color: #A8CBB0;
                min-height: 22px;
            }}
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                border: 1px solid #2E3A34;
                border-radius: 2px;
                background-color: #020403;
            }}
            QCheckBox::indicator:checked {{
                border-color: #00FF66;
                background-color: #00B050;
                image: none; /* Removed checkmark image for strict terminal block feel */
            }}
            #CompLabel {{
                font-family: 'IBM Plex Mono', monospace;
                font-size: 13px;
                font-weight: 600;
                color: #A8CBB0;
            }}
            #PresetCombo, #CompCombo {{
                padding: 6px 12px;
                border: 1px solid #2E3A34;
                border-radius: 4px;
                background-color: #020403;
                min-width: 120px;
                font-family: 'IBM Plex Mono', monospace;
                font-size: 13px;
                color: #E6FFE9;
            }}
            #PresetCombo QAbstractItemView, #CompCombo QAbstractItemView {{
                background-color: #020403;
                color: #E6FFE9;
                selection-background-color: #071F17;
                selection-color: #00FF66;
                border: 1px solid #2E3A34;
            }}
            #PresetCombo::drop-down, #CompCombo::drop-down {{
                border: none;
            }}
            #PresetCombo:hover, #CompCombo:hover {{
                border-color: #00FF66;
            }}
        """)

    def _on_preset_changed(self, text: str):
        """Toggles checkbox selection and enables/disables them based on preset selection."""
        if text in ("BI de Dados (Power BI / SQL)", "GIS & Geoprocessamento"):
            self.normalize_cols_cb.setChecked(True)
            self.normalize_cols_cb.setEnabled(False)
            self.flatten_json_cb.setChecked(True)
            self.flatten_json_cb.setEnabled(False)
            self.preserve_sensitive_cb.setChecked(True)
            self.preserve_sensitive_cb.setEnabled(False)
        else: # "Preservação Máxima (Padrão)"
            self.normalize_cols_cb.setEnabled(True)
            self.flatten_json_cb.setEnabled(True)
            self.preserve_sensitive_cb.setEnabled(True)
            
        self._on_setting_changed()

    def _on_browse_clicked(self):
        dir_path = QFileDialog.getExistingDirectory(
            self,
            "Selecionar pasta de destino",
            self.output_path_input.text()
        )
        if dir_path:
            self.output_path_input.setText(dir_path)

    def get_settings(self) -> dict:
        """Returns the dictionary of currently selected settings."""
        # Map UI values to internal config values
        comp_val = self.compression_combo.currentText()
        comp_map = {
            "Snappy": "snappy",
            "Zstd": "zstd",
            "Nenhuma": "none"
        }
        
        preset_map = {
            "Preservação Máxima (Padrão)": "default",
            "BI de Dados (Power BI / SQL)": "bi",
            "GIS & Geoprocessamento": "gis"
        }
        preset_val = preset_map.get(self.preset_combo.currentText(), "default")
        
        return {
            "output_dir": self.output_path_input.text().strip(),
            "normalize_cols": self.normalize_cols_cb.isChecked(),
            "flatten_json": self.flatten_json_cb.isChecked(),
            "generate_report": self.generate_report_cb.isChecked(),
            "process_all_sheets": self.process_all_sheets_cb.isChecked(),
            "preserve_sensitive": self.preserve_sensitive_cb.isChecked(),
            "continue_on_error": self.continue_on_error_cb.isChecked(),
            "compression": comp_map.get(comp_val, "snappy"),
            "preset": preset_val
        }

    def set_settings(self, settings: dict):
        """Populates the UI fields from a settings dictionary."""
        self.output_path_input.setText(settings.get("output_dir", ""))
        
        # Determine preset to apply
        preset_val = settings.get("preset", "default")
        preset_inv_map = {
            "default": "Preservação Máxima (Padrão)",
            "bi": "BI de Dados (Power BI / SQL)",
            "gis": "GIS & Geoprocessamento"
        }
        self.preset_combo.setCurrentText(preset_inv_map.get(preset_val, "Preservação Máxima (Padrão)"))
        
        # Apply checkbox values. If using default, load from settings, otherwise preset logic handles it
        if preset_val == "default":
            self.normalize_cols_cb.setChecked(settings.get("normalize_cols", True))
            self.flatten_json_cb.setChecked(settings.get("flatten_json", False))
            self.preserve_sensitive_cb.setChecked(settings.get("preserve_sensitive", True))
        
        # Trigger locked state
        self._on_preset_changed(self.preset_combo.currentText())
        
        self.generate_report_cb.setChecked(settings.get("generate_report", True))
        self.process_all_sheets_cb.setChecked(settings.get("process_all_sheets", True))
        self.continue_on_error_cb.setChecked(settings.get("continue_on_error", True))
        
        comp_val = settings.get("compression", "snappy")
        comp_inv_map = {
            "snappy": "Snappy",
            "zstd": "Zstd",
            "none": "Nenhuma"
        }
        self.compression_combo.setCurrentText(comp_inv_map.get(comp_val, "Snappy"))
