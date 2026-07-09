# PowerShell script to build Conversor Parquet Offline on Windows
# Set ExecutionPolicy if needed: Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process

$ErrorActionPreference = "Stop"

Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "   CONVERSOR PARQUET OFFLINE - SCRIPT DE BUILD WINDOWS  " -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan

# 1. Check Python installation
Write-Host "[1/5] Verificando instalação do Python..." -ForegroundColor Yellow
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Error "Python não encontrado no sistema. Por favor, instale o Python 3.9+ e adicione ao PATH."
}
$pythonVersion = python --version
Write-Host "-> Utilizando $pythonVersion" -ForegroundColor Green

# 2. Setup Virtual Environment
Write-Host "[2/5] Configurando ambiente virtual (.venv)..." -ForegroundColor Yellow
if (-not (Test-Path ".venv")) {
    Write-Host "Criando novo ambiente virtual .venv..." -ForegroundColor Gray
    python -m venv .venv
}
Write-Host "Ativando ambiente virtual..." -ForegroundColor Gray

# Paths for virtualenv execution
$pipPath = ".venv\Scripts\pip.exe"
$pytestPath = ".venv\Scripts\pytest.exe"
$pyinstallerPath = ".venv\Scripts\pyinstaller.exe"

# 3. Install Dependencies
Write-Host "[3/5] Instalando dependências do requirements.txt..." -ForegroundColor Yellow
& $pipPath install --upgrade pip
& $pipPath install -r requirements.txt
Write-Host "-> Dependências instaladas com sucesso." -ForegroundColor Green

# 4. Run Automated Tests
Write-Host "[4/5] Executando suíte de testes (pytest)..." -ForegroundColor Yellow
try {
    & $pytestPath tests/
    Write-Host "-> Todos os testes passaram!" -ForegroundColor Green
} catch {
    Write-Host "[ERRO] Alguns testes falharam. O build foi abortado." -ForegroundColor Red
    exit 1
}

# 5. Build Executable with PyInstaller
Write-Host "[5/5] Compilando executável com PyInstaller..." -ForegroundColor Yellow

# Ensure assets are generated first by running main briefly to create the icons
Write-Host "Gerando ícones e assets padrão..." -ForegroundColor Gray
$env:PYTHONPATH = (Get-Item .).FullName
& .venv\Scripts\python.exe -c "from app.main import generate_default_icon; generate_default_icon()"

# Package options:
# --onefile: Generate a single executable
# --windowed: Do not open console window
# --icon: Set application icon
# --add-data: Bundle the app/assets folder containing the icons
& $pyinstallerPath --noconfirm --name="GIRASSOLtoPARQUET" --windowed --onefile --icon="app/assets/icon.ico" --add-data="app/assets;app/assets" app/main.py

Write-Host "========================================================" -ForegroundColor Green
Write-Host "              BUILD CONCLUÍDO COM SUCESSO!              " -ForegroundColor Green
Write-Host "========================================================" -ForegroundColor Green
Write-Host "O executável final está localizado em:" -ForegroundColor Gray
Write-Host "-> $(Get-Item .\dist\GIRASSOLtoPARQUET.exe).FullName" -ForegroundColor Cyan
Write-Host "Você já pode distribuir ou utilizar o executável standalone." -ForegroundColor Gray
