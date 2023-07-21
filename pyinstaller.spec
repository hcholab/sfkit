#!/usr/bin/env python3

import os
import pkgutil
import sys

block_cipher = None

# https://github.com/arrow-py/arrow/issues/353#issuecomment-1186596301
dateutil_path = os.path.dirname(pkgutil.get_loader("dateutil").path)

a = Analysis(
    [sys.prefix + '/bin/sfkit'],
    pathex=[],
    binaries=[('plink2', '.')] + [
        ('/usr/lib/' + lib, '.') for lib in (
            'libgmp.so.10',
            'libpcre2-8.so.0',
            'libsodium.so.23',
        )
    ],
    datas=[(dateutil_path, 'dateutil')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='sfkit',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='sfkit',
)
