import os
import shutil
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, 
    QPushButton, QLineEdit, QFileDialog, QMessageBox, QFrame,
    QApplication
)
from PySide6.QtGui import QIcon, QFont, QClipboard
from PySide6.QtCore import Qt
from app.core.licensing.hardware_id import obter_hardware_id
from app.core.licensing.validator import validar_licenca, obter_caminho_licenca

class ActivationDialog(QDialog):
    def __init__(self, status_inicial=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Ativação - GIRASSOLtoPARQUET")
        self.setMinimumSize(500, 420)
        self.resize(550, 450)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        
        # Load local hardware ID
        self.local_hw_id = obter_hardware_id()
        self.status_inicial = status_inicial
        
        self.init_ui()
        self.apply_styles()
        
    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(16)
        
        # Header / Brand Section
        header_frame = QFrame()
        header_layout = QVBoxLayout(header_frame)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(6)
        
        title_label = QLabel("Ativação da Licença")
        title_label.setObjectName("TitleLabel")
        
        desc_label = QLabel(
            "Para utilizar o conversor, insira o arquivo de licença recebido. "
            "Se for sua primeira compra, informe o Hardware ID abaixo ao suporte."
        )
        desc_label.setWordWrap(True)
        desc_label.setObjectName("DescLabel")
        
        header_layout.addWidget(title_label)
        header_layout.addWidget(desc_label)
        main_layout.addWidget(header_frame)
        
        # Show Initial Error/Status if provided
        if self.status_inicial and not self.status_inicial.get("valido"):
            error_frame = QFrame()
            error_frame.setObjectName("ErrorFrame")
            err_layout = QVBoxLayout(error_frame)
            err_layout.setContentsMargins(12, 12, 12, 12)
            
            error_msg = self.status_inicial.get("mensagem", "Licença inválida ou ausente.")
            err_label = QLabel(f"⚠️ {error_msg}")
            err_label.setWordWrap(True)
            err_label.setObjectName("ErrorTextLabel")
            err_layout.addWidget(err_label)
            main_layout.addWidget(error_frame)
            
        # Hardware ID Section
        hw_frame = QFrame()
        hw_frame.setObjectName("HwFrame")
        hw_layout = QVBoxLayout(hw_frame)
        hw_layout.setContentsMargins(12, 12, 12, 12)
        hw_layout.setSpacing(8)
        
        hw_title = QLabel("Hardware ID deste computador:")
        hw_title.setObjectName("HwTitle")
        
        hw_input_layout = QHBoxLayout()
        hw_input_layout.setSpacing(8)
        
        self.hw_edit = QLineEdit(self.local_hw_id)
        self.hw_edit.setReadOnly(True)
        self.hw_edit.setObjectName("HwEdit")
        
        copy_btn = QPushButton("Copiar ID")
        copy_btn.setObjectName("CopyButton")
        copy_btn.clicked.connect(self.copy_hardware_id)
        
        hw_input_layout.addWidget(self.hw_edit, 4)
        hw_input_layout.addWidget(copy_btn, 1)
        
        hw_layout.addWidget(hw_title)
        hw_layout.addLayout(hw_input_layout)
        main_layout.addWidget(hw_frame)
        
        # License Content Input Section
        lic_label = QLabel("Cole o conteúdo do arquivo license.lic abaixo:")
        lic_label.setObjectName("LicLabel")
        main_layout.addWidget(lic_label)
        
        self.lic_text = QTextEdit()
        self.lic_text.setPlaceholderText('{"payload": ..., "signature": "..."}')
        self.lic_text.setObjectName("LicText")
        main_layout.addWidget(self.lic_text)
        
        # Action Buttons Section
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(12)
        
        import_file_btn = QPushButton("Selecionar Arquivo...")
        import_file_btn.setObjectName("ImportButton")
        import_file_btn.clicked.connect(self.import_license_file)
        
        activate_btn = QPushButton("Ativar Aplicativo")
        activate_btn.setObjectName("ActivateButton")
        activate_btn.clicked.connect(self.activate_license)
        
        actions_layout.addWidget(import_file_btn)
        actions_layout.addWidget(activate_btn)
        main_layout.addLayout(actions_layout)
        
    def apply_styles(self):
        # Professional dark/orange theme consistent with the Girassol style
        self.setStyleSheet("""
            QDialog {
                background-color: #111827; /* Dark Slate */
                color: #F3F4F6;
            }
            #TitleLabel {
                font-size: 20px;
                font-weight: bold;
                color: #F36616; /* Girassol Orange */
            }
            #DescLabel {
                font-size: 13px;
                color: #9CA3AF;
                line-height: 1.4;
            }
            #ErrorFrame {
                background-color: #7F1D1D;
                border: 1px solid #B91C1C;
                border-radius: 6px;
            }
            #ErrorTextLabel {
                color: #FCA5A5;
                font-size: 12px;
                font-weight: bold;
            }
            #HwFrame {
                background-color: #1F2937;
                border: 1px solid #374151;
                border-radius: 8px;
            }
            #HwTitle {
                font-size: 12px;
                font-weight: bold;
                color: #D1D5DB;
            }
            #HwEdit {
                background-color: #111827;
                color: #10B981; /* Emerald Green for IDs */
                border: 1px solid #4B5563;
                border-radius: 4px;
                padding: 6px 10px;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 12px;
            }
            #CopyButton {
                background-color: #374151;
                color: #F3F4F6;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                font-weight: bold;
            }
            #CopyButton:hover {
                background-color: #4B5563;
            }
            #LicLabel {
                font-size: 13px;
                font-weight: bold;
                color: #E5E7EB;
            }
            #LicText {
                background-color: #1F2937;
                color: #F3F4F6;
                border: 1px solid #374151;
                border-radius: 6px;
                padding: 8px;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 11px;
            }
            #ImportButton {
                background-color: #1F2937;
                color: #D1D5DB;
                border: 1px solid #4B5563;
                border-radius: 6px;
                padding: 10px 16px;
                font-weight: bold;
            }
            #ImportButton:hover {
                background-color: #374151;
                color: #FFFFFF;
            }
            #ActivateButton {
                background-color: #F36616;
                color: #FFFFFF;
                border: none;
                border-radius: 6px;
                padding: 10px 16px;
                font-weight: bold;
                font-size: 14px;
            }
            #ActivateButton:hover {
                background-color: #EA580C;
            }
        """)

    def copy_hardware_id(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.local_hw_id)
        QMessageBox.information(
            self, 
            "Copiado", 
            "Hardware ID copiado para a área de transferência com sucesso!"
        )
        
    def import_license_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Selecionar Arquivo de Licença",
            "",
            "Arquivos de Licença (*.lic);;Todos os arquivos (*)"
        )
        if file_path:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    conteudo = f.read()
                self.lic_text.setPlainText(conteudo)
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Erro ao Ler Arquivo",
                    f"Não foi possível ler o arquivo selecionado:\n{str(e)}"
                )

    def activate_license(self):
        conteudo = self.lic_text.toPlainText().strip()
        if not conteudo:
            QMessageBox.warning(
                self,
                "Campo Vazio",
                "Por favor, cole o conteúdo da licença ou selecione um arquivo de licença."
            )
            return
            
        # Validar conteúdo da licença
        resultado = validar_licenca(conteudo)
        if not resultado.get("valido"):
            QMessageBox.critical(
                self,
                "Ativação Falhou",
                resultado.get("mensagem", "Licença inválida.")
            )
            return
            
        # Salvar licença
        caminho_destino = obter_caminho_licenca()
        try:
            os.makedirs(os.path.dirname(caminho_destino), exist_ok=True)
            with open(caminho_destino, "w", encoding="utf-8") as f:
                f.write(conteudo)
                
            QMessageBox.information(
                self,
                "Sucesso",
                "Licença ativada com sucesso! O aplicativo será iniciado."
            )
            self.accept()
        except Exception as e:
            QMessageBox.critical(
                self,
                "Erro ao Salvar",
                f"Erro ao salvar o arquivo de licença no destino:\n{str(e)}"
            )
