# -*- mode: python ; coding: utf-8 -*-
#
# [DEPRECATED] Este arquivo .spec está descontinuado.
# Use o spec oficial de produção em: app/GIRASSOLtoPARQUET.spec
#

pyarrow_excludes = [
    'pyarrow._orc',
    'pyarrow._feather',
    'pyarrow._flight',
    'pyarrow._gcsfs',
    'pyarrow._azurefs',
    'pyarrow._hdfs',
    'pyarrow._cuda',
    'pyarrow._substrait',
    'pyarrow._acero',
    'pytest',
    '_pytest'
]

a = Analysis(
    ['app\\main.py'],
    pathex=['.'],
    binaries=[],
    datas=[('app/assets', 'app/assets')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=pyarrow_excludes,
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='ALLtoParquet',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='app/assets/icon.ico',
    version='version_info.txt',
)
