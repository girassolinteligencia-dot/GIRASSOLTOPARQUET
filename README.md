# Conversor Parquet Offline

O **Conversor Parquet Offline** é uma aplicação desktop Windows leve, profissional e 100% offline, desenvolvida em Python com **PySide6** (Qt) e impulsionada por **Polars**, **PyArrow** e **DuckDB**. Seu principal objetivo é converter bases de dados nos formatos `.csv`, `.xlsx`, `.json`, `.ndjson` e `.jsonl` para o formato de alta performance e compactação `.parquet` de forma totalmente local, rápida e auditável.

A aplicação foi projetada sob uma arquitetura de segurança rígida: **não há login, telemetria, conexões com internet, APIs externas ou envio de dados para servidores**.

---

## 🚀 Principais Funcionalidades

1. **Arraste e Solte (Drag & Drop)**: Recebe múltiplos arquivos ou pastas inteiras arrastando-os diretamente para a interface.
2. **Preservação de Campos Sensíveis**: Mantém colunas contendo CPFs, CNPJs, CEPs, telefones e códigos identificadores explicitamente como tipo texto no Parquet, prevenindo a perda automática de zeros à esquerda ou erros de representação decimal.
3. **Normalização de Cabeçalhos**: Opção para remover acentos, converter para letras minúsculas, substituir espaços/traços por underline (`_`) e remover caracteres especiais.
4. **Tratamento de Abas Excel**: Suporta leitura da primeira aba por padrão ou processamento completo de todas as abas (gerando um arquivo `.parquet` individual para cada aba não-vazia).
5. **Achatamento de JSONs (Flattening)**: Suporta desaninhar recursivamente objetos JSON aninhados em colunas planas (ex: `{"contato": {"email": "x"}}` torna-se `contato_email`).
6. **Tolerância a Falhas**: Fila assíncrona robusta. Se habilitado, ignora linhas malformadas em NDJSON/JSONL ou continua a fila de conversão mesmo que um arquivo falhe, emitindo relatórios individuais sobre os itens ignorados.
7. **Relatório de Auditoria**: Gera automaticamente arquivos `.json` e `.txt` detalhando o tamanho do arquivo, quantidade de linhas/colunas, hash SHA-256 da origem, tipos de campos inferidos, alterações no cabeçalho e erros.
8. **Compressão Customizada**: Opções de compressão `Snappy`, `Zstd` ou sem compressão.

---

## 🛠️ Stack Tecnológica

- **Interface Gráfica**: PySide6 (Qt 6 para Python)
- **Processamento de Dados**: Polars (alta performance e eficiência de memória)
- **Gravação Parquet**: PyArrow (motor padrão)
- **Motor Auxiliar**: DuckDB
- **Empacotamento**: PyInstaller
- **Testes**: pytest

---

## ⚙️ Instalação e Execução (Desenvolvimento)

### Pré-requisitos
- **Windows OS**
- **Python 3.9** ou superior instalado e adicionado às variáveis de ambiente (PATH).

### Instalação rápida das dependências:
1. Abra um terminal do PowerShell na raiz do projeto.
2. Crie e ative um ambiente virtual:
   ```powershell
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   ```
3. Instale as dependências exigidas:
   ```powershell
   pip install -r requirements.txt
   ```

### Executar em Desenvolvimento:
Para iniciar a interface gráfica diretamente com o interpretador Python:
```powershell
python app/main.py
```

---

## 📦 Como Gerar o Executável (.exe)

O projeto inclui um script automatizado que realiza todos os passos: criação do ambiente virtual, instalação de dependências, execução de testes unitários e empacotamento em um arquivo executável standalone (`dist/ConversorParquetOffline.exe`).

1. Abra o terminal do PowerShell na pasta do projeto.
2. Execute o script de build:
   ```powershell
   .\build_windows.ps1
   ```
3. Ao finalizar, o executável estará pronto na pasta `dist/` para ser utilizado ou distribuído.

---

## 📁 Estrutura de Logs e Relatórios

### 1. Logs de Execução
Todos os eventos importantes, warnings e exceções técnicas ocorridas durante o ciclo de vida do programa são mantidos localmente no seu computador em:
`C:\Users\<SeuUsuario>\AppData\Local\ConversorParquetOffline\logs\app.log`

### 2. Relatórios de Auditoria
Sempre que a opção "Gerar relatório de conversão" estiver marcada nas configurações, cada arquivo convertido gerará dois arquivos de auditoria na pasta de destino escolhida pelo usuário:
- **`[NomeOriginal]_relatorio.json`**: Metadados brutos e mapeamentos estruturados, ideias para automações e sistemas de auditoria.
- **`[NomeOriginal]_relatorio.txt`**: Documento em texto plano formatado e assinado com o hash criptográfico SHA-256 e o resumo do processamento de dados, ideal para anexação técnica ou histórico humano.

---

## ⚡ Limitações Conhecidas

- **Arquivos Excel Grandes**: A biblioteca de leitura de Excel necessita carregar a folha em memória para processamento. Arquivos `.xlsx` com centenas de megabytes podem apresentar consumo elevado de memória RAM durante a fase de conversão se comparados a formatos de texto estruturado.
- **Estruturas de Lista em JSON**: Ao achatar JSONs aninhados, a aplicação foca em desaninhar dicionários. Elementos do tipo lista (`list`) são preservados como arrays no DataFrame e gravados como tipos de lista nativos do Parquet.

---

## 🔏 Assinatura de Código (Code Signing)

Como o executável gerado (`dist/GIRASSOLtoPARQUET.exe`) é um utilitário que lida com dados estruturados, distribuí-lo sem assinatura digital pode fazer com que o Windows SmartScreen alerte o usuário com mensagens de "Fornecedor Desconhecido" ou bloqueie a execução imediata.

Para evitar esses avisos no ambiente do usuário final, você pode assinar o executável. Existem duas abordagens principais:

### 1. Assinatura Local (Autoassinada / Self-Signed)
Útil para testes internos em computadores controlados onde o certificado autoassinado pode ser previamente instalado na máquina (no repositório de Autoridades de Certificação Raiz Confiáveis).

Para gerar e assinar localmente via PowerShell (como Administrador):

```powershell
# Criar certificado autoassinado na pasta pessoal
$cert = New-SelfSignedCertificate -Type CodeSigningCert -Subject "CN=Girassol Inteligencia Local" -FriendlyName "Girassol Local Dev" -KeyLength 2048 -NotAfter (Get-Date).AddYears(2)

# Exportar o certificado (opcional, para instalar em outras maquinas)
Export-Certificate -Cert $cert -FilePath .\GirassolLocalDev.cer

# Assinar o executavel com o signtool (geralmente instalado com o Windows SDK)
& "C:\Program Files (x86)\Windows Kits\10\bin\<VersãoDoSDK>\x64\signtool.exe" sign /fd sha256 /a /sha1 $cert.Thumbprint .\dist\GIRASSOLtoPARQUET.exe
```

### 2. Certificado Comercial (Produção e Distribuição Externa)
Para distribuição ao público geral (por exemplo, candidatos e municípios parceiros), é estritamente recomendável adquirir um certificado de assinatura de código comercial emitido por uma Autoridade Certificadora pública confiável (comercializada por empresas como Digicert, Sectigo, GlobalSign ou credenciadas ICP-Brasil).

Uma vez obtido o arquivo do certificado `.pfx` ou a chave em hardware (token USB/HSM):

```powershell
# Assinatura usando arquivo PFX e senha
& "C:\Program Files (x86)\Windows Kits\10\bin\<VersãoDoSDK>\x64\signtool.exe" sign /f "caminho\para\certificado.pfx" /p "suasenha" /fd sha256 /t http://timestamp.digicert.com /v .\dist\GIRASSOLtoPARQUET.exe
```

O script [build.ps1](file:///c:/GIRASSOLTOPARQUET/parquet-converter/build.ps1) possui uma linha comentada no final que serve como referência para automatizar este passo após a compilação do executável.

---

## 🏬 Distribuição Comercial via Microsoft Store

Como alternativa ao custo anual recorrente de um Certificado de Assinatura de Código comercial, o aplicativo pode ser distribuído pela **Microsoft Store**. A própria loja da Microsoft valida, hospeda e assina digitalmente a aplicação com os certificados confiáveis do Windows, removendo alertas do SmartScreen de forma transparente.

### Fluxo de Preparação e Publicação

1. **Conta de Desenvolvedor (Microsoft Partner Center)**:
   - Crie uma conta em [partner.microsoft.com](https://partner.microsoft.com/dashboard/registration).
   - Pague a taxa única de inscrição (cerca de US$ 19 para pessoa física, US$ 99 para pessoa jurídica/CNPJ).
   - Reserve o nome do produto no painel da loja.

2. **Empacotamento MSIX**:
   - Instale o **MSIX Packaging Tool** diretamente da Microsoft Store.
   - Modifique a especificação ou compile a aplicação no modo diretório: `pyinstaller GIRASSOLtoPARQUET.spec --onedir` (isso gera uma pasta descompactada, otimizando o tempo de abertura da aplicação em runtime).
   - Execute o MSIX Packaging Tool, aponte para a pasta e configure `GIRASSOLtoPARQUET.exe` as executável principal. A ferramenta gerará um arquivo com extensão `.msix`.

3. **Submissão e Certificação**:
   - Faça o upload do arquivo `.msix` na seção de pacotes da sua submissão.
   - Cadastre capturas de tela (screenshots), descrição comercial do produto e a política de privacidade (declarando o compromisso de privacidade 100% offline).
   - Envie para a certificação (aproveitamento geralmente em 24 a 48 horas).
