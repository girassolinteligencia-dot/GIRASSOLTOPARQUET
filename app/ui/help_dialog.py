import os
from PySide6.QtWidgets import QDialog, QVBoxLayout, QTextBrowser, QPushButton
from PySide6.QtCore import Qt

class HelpDialog(QDialog):
    """
    Help / Guide dialog explaining the application operations,
    supported formats, configurations, and button roles.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Guia de Uso - Conversor Parquet Offline")
        self.resize(780, 580)
        self.setMinimumSize(650, 480)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        self.browser = QTextBrowser(self)
        self.browser.setOpenExternalLinks(True)
        self.browser.setHtml(self._get_help_html())
        
        self.close_btn = QPushButton("Fechar Guia", self)
        self.close_btn.setObjectName("HelpCloseBtn")
        self.close_btn.setCursor(Qt.PointingHandCursor)
        self.close_btn.clicked.connect(self.accept)
        
        layout.addWidget(self.browser)
        layout.addWidget(self.close_btn)
        
        self._apply_style()
        
    def _apply_style(self):
        self.setStyleSheet("""
            QDialog {
                background-color: #F8FAFC;
            }
            QTextBrowser {
                background-color: #FFFFFF;
                border: 1px solid #CBD5E1;
                border-radius: 8px;
                padding: 16px;
            }
            #HelpCloseBtn {
                padding: 10px 20px;
                border: 1px solid #CBD5E1;
                border-radius: 8px;
                background-color: #FFFFFF;
                color: #475569;
                font-family: 'Inter', sans-serif;
                font-weight: 600;
                font-size: 13px;
            }
            #HelpCloseBtn:hover {
                background-color: #F8FAFC;
                border-color: #94A3B8;
            }
        """)
        
    def _get_help_html(self) -> str:
        return """
        <!DOCTYPE html>
        <html>
        <head>
        <style>
            body {
                font-family: 'Segoe UI', 'Inter', sans-serif;
                line-height: 1.6;
                color: #334155;
                margin: 0;
                padding: 0;
            }
            h1 {
                font-family: 'Playfair Display', 'Georgia', serif;
                color: #1E293B;
                font-size: 24px;
                border-bottom: 2px solid #F36616;
                padding-bottom: 8px;
                margin-top: 0;
            }
            h2 {
                font-family: 'Playfair Display', 'Georgia', serif;
                color: #0F172A;
                font-size: 18px;
                margin-top: 24px;
                margin-bottom: 12px;
            }
            h3 {
                font-family: 'Segoe UI', 'Inter', sans-serif;
                color: #1E293B;
                font-size: 14px;
                margin-top: 16px;
                margin-bottom: 6px;
                font-weight: 700;
            }
            p {
                margin-bottom: 12px;
                font-size: 13px;
            }
            ul, ol {
                margin-bottom: 16px;
                padding-left: 20px;
                font-size: 13px;
            }
            li {
                margin-bottom: 6px;
            }
            .file-format {
                display: inline-block;
                background-color: #F1F5F9;
                color: #475569;
                padding: 2px 8px;
                border-radius: 6px;
                font-family: monospace;
                font-size: 12px;
                font-weight: bold;
                margin-right: 6px;
            }
            .card {
                background-color: #F8FAFC;
                border: 1px solid #E2E8F0;
                border-radius: 8px;
                padding: 12px 16px;
                margin-bottom: 16px;
            }
            .highlight {
                color: #F36616;
                font-weight: bold;
            }
        </style>
        </head>
        <body>
            <h1>Guia de Uso - Conversor Parquet Offline</h1>
            <p>Esta aplicação foi desenvolvida para possibilitar a conversão rápida, segura e totalmente local de arquivos de dados estruturados para o formato de alta performance <strong>Apache Parquet</strong>.</p>
            
            <h2>1. Formatos de Arquivos Suportados</h2>
            <ul>
                <li><span class="file-format">.CSV</span><strong>Valores Separados por Vírgula</strong>: Detecta automaticamente a codificação de caracteres (UTF-8, Latin-1, etc.) e o separador (vírgula, ponto-e-vírgula, tabulação ou pipe).</li>
                <li><span class="file-format">.XLSX</span><strong>Planilhas Excel</strong>: Permite a leitura rápida de tabelas e a conversão de abas individuais ou em lote.</li>
                <li><span class="file-format">.JSON</span><strong>Estruturas de Dados JSON</strong>: Converte listas de objetos estruturados em colunas de tabelas.</li>
                <li><span class="file-format">.NDJSON / .JSONL</span><strong>JSON Delimitado por Nova Linha</strong>: Recomendado para exportação de bases de dados volumosas com eficiência.</li>
            </ul>

            <h2>2. Como Utilizar a Aplicação (Passo a Passo)</h2>
            <ol>
                <li><strong>Adicione os arquivos de origem:</strong> Arraste arquivos ou pastas para a área pontilhada cinza à esquerda ("Arquivos Origem"), ou clique nos botões <span class="highlight">Selecionar arquivos</span> ou <span class="highlight">Selecionar pasta</span>.</li>
                <li><strong>Confirme o destino:</strong> Ao adicionar arquivos pela primeira vez, o campo de destino é configurado automaticamente com a mesma pasta do arquivo. Se quiser salvar em outro lugar, clique em <span class="highlight">Selecionar destino</span>.</li>
                <li><strong>Ajuste as configurações:</strong> Selecione as opções de conversão que melhor se aplicam à sua base de dados (descritas abaixo).</li>
                <li><strong>Execute a conversão:</strong> Clique no botão laranja <span class="highlight">Converter</span> na parte inferior. O console mostrará o progresso do lote em tempo real.</li>
                <li><strong>Abra a pasta de saída:</strong> Ao terminar, clique em <span class="highlight">Abrir pasta de saída</span> para abrir a pasta de destino no Windows Explorer.</li>
            </ol>

            <h2>3. O que faz cada Configuração de Conversão?</h2>
            <div class="card">
                <h3>• Normalizar nomes das colunas</h3>
                <p>Padroniza o cabeçalho das tabelas para evitar erros em ferramentas de consulta (como DuckDB, BigQuery, ClickHouse). Converte para letras minúsculas, remove acentos, substitui espaços por sublinhados (<code>_</code>) e limpa caracteres especiais. Também corrige grafias comuns de e-mail (ex: emai_l vira email).</p>
                
                <h3>• Achatar JSON aninhado</h3>
                <p>Para arquivos JSON ou NDJSON, descompacta chaves ou dicionários internos complexos em colunas diretas da tabela (ex: <code>{"endereco": {"cidade": "São Paulo"}}</code> vira a coluna <code>endereco_cidade</code>).</p>
                
                <h3>• Gerar relatório de conversão</h3>
                <p>Gera arquivos complementares de texto (<code>.txt</code>) e de dados (<code>.json</code>) detalhando a quantidade de registros, tamanho original, integridade via hash SHA-256 e o tempo de execução da conversão.</p>
                
                <h3>• Processar todas as abas do Excel</h3>
                <p>Se marcado, cada aba com dados dentro de uma planilha <code>.xlsx</code> é convertida em um arquivo Parquet independente. Se desmarcado, converte apenas a aba principal (primeira).</p>
                
                <h3>• Preservar campos sensíveis como texto</h3>
                <p>Evita a perda de formatação (como a remoção de zeros à esquerda em CPFs/CNPJs ou conversão científica de números grandes) em campos de identificação comuns, forçando sua tipagem no Parquet como Texto (String).</p>
                
                <h3>• Continuar conversão mesmo com erro</h3>
                <p>Garante que erros em linhas isoladas (em arquivos NDJSON) ou a falha de conversão de um arquivo no lote de processamento não interrompam toda a execução, permitindo que a aplicação converta o restante da fila.</p>
                
                <h3>• Compressão Parquet</h3>
                <p>Opção para definir o algoritmo de redução de tamanho físico do Parquet: <strong>Snappy</strong> (padrão, excelente custo-benefício), <strong>Zstd</strong> (alta compressão para bases grandes) ou <strong>Nenhuma</strong>.</p>
            </div>
        </body>
        </html>
        """
