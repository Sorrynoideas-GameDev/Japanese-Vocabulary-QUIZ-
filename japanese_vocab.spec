# japanese_vocab.spec
# ────────────────────
# PyInstaller spec file for building a single-file executable.
#
# Usage:
#   pip install pyinstaller
#   pyinstaller japanese_vocab.spec
#
# The resulting executable will be in dist/japanese_vocab(.exe on Windows)
# The progress.json file will be written alongside the executable.

import os

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[os.path.abspath('.')],
    binaries=[],
    # Bundle the vocabulary JSON so it ships inside the executable
    datas=[
        ('vocabulary.json', '.'),
    ],
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
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='japanese_vocab',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,          # No terminal window on Windows
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
