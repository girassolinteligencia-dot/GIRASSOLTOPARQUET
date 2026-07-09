# build.ps1
# Script de compilação automatizada com rastreabilidade

$ErrorActionPreference = "Stop"

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host " Iniciando build do Conversor Parquet Offline" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan

# 1. Ativar o ambiente virtual
Write-Host "[1/5] Ativando ambiente virtual .venv..." -ForegroundColor Green
if (Test-Path ".venv\Scripts\Activate.ps1") {
    .venv\Scripts\Activate.ps1
} else {
    Write-Warning "Diretorio .venv nao encontrado! Certifique-se de que o ambiente virtual está criado."
    exit 1
}

# 2. Verificar UPX
Write-Host "[2/5] Verificando presenca do UPX..." -ForegroundColor Green
$upxInstalled = $false
try {
    $upxCmd = Get-Command upx -ErrorAction SilentlyContinue
    if ($upxCmd) {
        $upxInstalled = $true
        Write-Host "UPX detectado: $upxCmd" -ForegroundColor Gray
        # Executa para confirmar o funcionamento
        & upx --version | Out-Null
    } else {
        Write-Warning "UPX nao encontrado no PATH! O executavel sera gerado sem compressao UPX, o que aumentara seu tamanho."
        Write-Warning "Para instalar o UPX no Windows, execute: choco install upx"
    }
} catch {
    Write-Warning "Erro ao verificar UPX: $_"
}

# 3. Executar testes unitários antes do build
Write-Host "[3/5] Executando testes unitarios com pytest..." -ForegroundColor Green
$pytestCmd = Get-Command pytest -ErrorAction SilentlyContinue
if ($pytestCmd) {
    try {
        & pytest
        Write-Host "Testes concluidos com sucesso!" -ForegroundColor Green
    } catch {
        Write-Error "Os testes unitarios falharam! Abortando build."
        exit 1
    }
} else {
    Write-Warning "pytest nao encontrado! Pulando a etapa de testes unitarios (comum em builds limpos de producao)."
}

# 4. Executar PyInstaller
Write-Host "[4/5] Executando PyInstaller..." -ForegroundColor Green
if (Test-Path "build") { Remove-Item -Recurse -Force "build" }
if (Test-Path "dist\ALLtoParquet.exe") { Remove-Item -Force "dist\ALLtoParquet.exe" }

pyinstaller ALLtoParquet.spec --clean

if (-not (Test-Path "dist\ALLtoParquet.exe")) {
    Write-Error "Erro: O executavel dist\ALLtoParquet.exe nao foi gerado."
    exit 1
}
Write-Host "Executavel gerado com sucesso!" -ForegroundColor Green

# 5. Validar metadados VERSIONINFO via pefile
Write-Host "[5/5] Validando metadados VERSIONINFO via pefile..." -ForegroundColor Green
$validationScript = @"
import sys
import pefile

try:
    pe = pefile.PE("dist/ALLtoParquet.exe")
    if not hasattr(pe, 'VS_VERSIONINFO'):
        print('ERRO: VS_VERSIONINFO nao encontrado no executavel.')
        sys.exit(1)
    
    info_list = []
    for fileinfo in pe.FileInfo:
        for info in fileinfo:
            if info.name == 'StringFileInfo':
                for string_table in info.StringTable:
                    for key, val in string_table.entries.items():
                        info_list.append((key.decode('utf-8', errors='ignore'), val.decode('utf-8', errors='ignore')))
    
    print('Metadados encontrados:')
    required_keys = ['CompanyName', 'ProductName', 'FileVersion']
    found_keys = {}
    for key, val in info_list:
        print(f'  {key}: {val}')
        if key in required_keys:
            found_keys[key] = val
            
    for req in required_keys:
        if req not in found_keys:
            print(f'ERRO: Chave obrigatoria {req} nao encontrada.')
            sys.exit(1)
            
    print('Validacao do VERSIONINFO concluida com sucesso!')
    sys.exit(0)
except Exception as e:
    print(f'ERRO na analise do executavel: {e}')
    sys.exit(1)
"@

$valPath = "dist\validate_pe.py"
$validationScript | Out-File -FilePath $valPath -Encoding utf8
python $valPath
$valExitCode = $LastExitCode
Remove-Item $valPath -ErrorAction SilentlyContinue

if ($valExitCode -ne 0) {
    Write-Error "Validacao de VERSIONINFO falhou! Abortando geracao de BUILD_INFO."
    exit 1
}

# 6. Gerar dist\BUILD_INFO.json com metadados do build
Write-Host "Gerando dist\BUILD_INFO.json..." -ForegroundColor Green
$exeFile = Get-Item "dist\ALLtoParquet.exe"
$hash = Get-FileHash "dist\ALLtoParquet.exe" -Algorithm SHA256
$timestamp = [DateTime]::UtcNow.ToString("yyyy-MM-ddTHH:mm:ssZ")
$sizeBytes = $exeFile.Length
$version = "1.0.0"

$buildInfo = @{
    "filename" = "ALLtoParquet.exe"
    "version" = $version
    "sha256" = $hash.Hash.ToLower()
    "timestamp_utc" = $timestamp
    "size_bytes" = $sizeBytes
    "upx_compressed" = $upxInstalled
} | ConvertTo-Json

$buildInfo | Out-File -FilePath "dist\BUILD_INFO.json" -Encoding utf8

Write-Host "=========================================" -ForegroundColor Green
Write-Host " Build concluido com SUCESSO!" -ForegroundColor Green
Write-Host " Arquivo: dist\ALLtoParquet.exe" -ForegroundColor Green
Write-Host " Tamanho: $([Math]::Round($sizeBytes / 1MB, 2)) MB" -ForegroundColor Green
Write-Host " Hash SHA-256: $($hash.Hash.ToLower())" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Green

# 7. Placeholder de Code Signing (Comentado)
# Para assinar digitalmente o executavel (evita SmartScreen):
# & "C:\Program Files (x86)\Windows Kits\10\bin\10.0.22621.0\x64\signtool.exe" sign /fd sha256 /a /t http://timestamp.digicert.com /n "Sua Empresa" dist\ALLtoParquet.exe
