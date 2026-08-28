# PyInstaller spec for the Windows launcher (WSL2 edition).
#
# Built on a windows-latest GitHub Actions runner (PyInstaller does not
# cross-compile — this cannot be built from Linux/macOS) by:
#   pyinstaller hexstrike_windows.spec
#
# Much lighter than the old all-in-one build: this launcher only orchestrates
# `wsl.exe` and downloads the rootfs image — it never imports hexstrike_server
# or its dependencies (those live inside the WSL2 image, see wsl/Dockerfile),
# so there's no collect_all() work needed for mitmproxy/selenium/etc. here.

a = Analysis(
    ['hexstrike_windows_app.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='HexStrikeAI-Windows',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
