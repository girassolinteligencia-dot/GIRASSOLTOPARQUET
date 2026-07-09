# -*- mode: python ; coding: utf-8 -*-
#
# GIRASSOLtoPARQUET.spec
#
# Projeto: c:\GIRASSOLTOPARQUET\parquet-converter
# Entrypoint: app/main.py
# Build: executar com este .spec salvo em c:\GIRASSOLTOPARQUET\parquet-converter\
#   (mesma pasta que contém app/), com o .venv ativado:
#     .venv\Scripts\Activate.ps1
#     pyinstaller GIRASSOLtoPARQUET.spec --clean
#
# icon= abaixo assume app/assets/icon.ico — ajuste o nome do arquivo se o
# ícone real tiver outro nome, ou remova a linha 'icon=' se não houver ícone.

block_cipher = None

# Submódulos do PyArrow presentes no build atual mas sem uso identificado
# no código da aplicação (detector/reader/writer não referenciam flight,
# gcsfs, azurefs, hdfs, cuda, substrait). Excluí-los reduz o tamanho do
# onefile sem afetar a conversão CSV/Excel/JSON/NDJSON -> Parquet local.
PYARROW_EXCLUDES = [
    'pyarrow._flight',
    'pyarrow._gcsfs',
    'pyarrow._azurefs',
    'pyarrow._hdfs',
    'pyarrow._cuda',
    'pyarrow._substrait',
    'pyarrow._acero',
    'pyarrow._orc',           # remover também se não converte para ORC
    'pyarrow._feather',       # remover também se não converte para Feather
]

# Dependências de teste que não deveriam ir para o build de produção.
# Se pytest está sendo empacotado, provavelmente está vazando via um
# requirements.txt único (dev+prod). Ideal: requirements-dev.txt separado.
DEV_EXCLUDES = [
    'pytest',
    '_pytest',
    'py',
    'pluggy',
]

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        # Empacota toda a pasta app/assets preservando a estrutura relativa.
        # Se assets/ tiver subpastas (icons/, images/), isso já cobre.
        ('assets', 'assets'),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=PYARROW_EXCLUDES + DEV_EXCLUDES,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='GIRASSOLtoPARQUET',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,                       # requer UPX instalado e no PATH
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,                  # subsystem GUI (mantém comportamento atual)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icon.ico',     # ajustar nome se diferente; remover linha se não houver ícone
    version='version_info.txt',     # ver arquivo version_info.txt anexo
)

# --- Rastreabilidade de build ---------------------------------------------
# Após o build, gere BUILD_INFO.json ao lado do .exe com hash SHA-256 e
# timestamp. Adicione isto ao seu script de build (build.ps1/build.sh),
# não é executado pelo próprio PyInstaller:
#
#   python -c "
#   import hashlib, json, datetime, pathlib
#   p = pathlib.Path('dist/GIRASSOLtoPARQUET.exe')
#   h = hashlib.sha256(p.read_bytes()).hexdigest()
#   info = {
#       'nome': 'GIRASSOLtoPARQUET.exe',
#       'versao': '1.0.0.0',
#       'sha256': h,
#       'build_utc': datetime.datetime.utcnow().isoformat() + 'Z',
#       'tamanho_bytes': p.stat().st_size,
#   }
#   pathlib.Path('dist/BUILD_INFO.json').write_text(json.dumps(info, indent=2, ensure_ascii=False))
#   "
