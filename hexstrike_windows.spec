# PyInstaller spec for the Windows build of HexStrike AI.
#
# Built on a windows-latest GitHub Actions runner (PyInstaller does not
# cross-compile — this cannot be built from Linux/macOS) by:
#   pyinstaller hexstrike_windows.spec
#
# Produces one self-contained HexStrikeAI-Windows.exe: no separate install
# step, no terminal, no additional downloads for the person running it.
# mitmproxy, selenium, and webdriver_manager all do non-obvious dynamic
# imports (addon discovery, driver-manager backends) that PyInstaller's
# static analysis can miss, so their packages are bundled in full via
# collect_all rather than relying on hidden-import guesses.

from PyInstaller.utils.hooks import collect_all

# dashboard.html goes to the extraction root ('.') — hexstrike_server.py's
# dashboard route looks for it via sys._MEIPASS at runtime, which is exactly
# where PyInstaller unpacks entries whose destination is '.'.
datas = [('dashboard.html', '.')]
binaries = []
hiddenimports = []

for pkg in ("mitmproxy", "selenium", "webdriver_manager", "bs4"):
    pkg_datas, pkg_binaries, pkg_hiddenimports = collect_all(pkg)
    datas += pkg_datas
    binaries += pkg_binaries
    hiddenimports += pkg_hiddenimports

a = Analysis(
    ['hexstrike_windows_app.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['pwn', 'pwntools', 'angr'],
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
