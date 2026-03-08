# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['data_share_client.py'],
    pathex=[],
    binaries=[],
    datas=[('config.json', '.')],
    hiddenimports=['requests', 'urllib3', 'charset_normalizer', 'certifi', 'idna'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
    name='即シェア君',
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
    icon=['rapidshare.ico'],
)
