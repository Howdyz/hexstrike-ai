#!/usr/bin/env python3
"""
HexStrike AI — Windows tool installer.

HexStrike itself never bundled the ~150 external CLI security tools it
orchestrates (nmap, sqlmap, gobuster, ...) — it just shells out to whatever's
already on PATH, same on Linux and Windows. On Kali most of those come
preinstalled; on a fresh Windows machine none of them do.

This installs a curated subset with NO extra runtime dependency (no "also
go install Python/Ruby/Go yourself" step, which would break the whole
no-terminal premise): tools that ship as a single native .exe, either via
`winget` (silent, no UI) or downloaded straight from the project's GitHub
Releases and extracted. Tools that only exist as Python/Ruby scripts
(sqlmap, wpscan, ...) are intentionally NOT covered here.

Nothing is written to the persistent system PATH (setx has a well-known
footgun: naive use can silently truncate/corrupt a user's PATH past its
character limit). Instead, the tools directory is prepended to THIS
process's PATH only — effective immediately for HexStrike's own subprocess
calls, re-applied on every launch by checking whether it already exists.
"""

import os
import re
import shutil
import subprocess
import tempfile
import zipfile
import tarfile
from pathlib import Path

try:
    import requests
except ImportError:
    requests = None

TOOLS_DIR = Path(os.environ.get("LOCALAPPDATA", tempfile.gettempdir())) / "HexStrike" / "tools"

_ASSET_PATTERN = re.compile(r"windows.*(amd64|x86_64|64).*\.(zip|tar\.gz)$", re.IGNORECASE)

# (display name, exe filename to look for after extraction, GitHub "owner/repo")
GITHUB_RELEASE_TOOLS = [
    ("nuclei", "nuclei.exe", "projectdiscovery/nuclei"),
    ("httpx", "httpx.exe", "projectdiscovery/httpx"),
    ("subfinder", "subfinder.exe", "projectdiscovery/subfinder"),
    ("katana", "katana.exe", "projectdiscovery/katana"),
    ("ffuf", "ffuf.exe", "ffuf/ffuf"),
    ("gobuster", "gobuster.exe", "OJ/gobuster"),
    ("dalfox", "dalfox.exe", "hahwul/dalfox"),
]

# (display name, winget package id)
WINGET_TOOLS = [
    ("nmap", "Insecure.Nmap"),
    ("hashcat", "hashcat.hashcat"),
]

_NO_WINDOW = 0x08000000  # subprocess.CREATE_NO_WINDOW, defined only on Windows


def _run_hidden(cmd, timeout=180):
    kwargs = {}
    if os.name == "nt":
        kwargs["creationflags"] = _NO_WINDOW
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, **kwargs)


def already_installed():
    """True if a previous install already populated the tools dir — lets the
    app re-add it to PATH on every launch without re-downloading anything."""
    return TOOLS_DIR.is_dir() and any(TOOLS_DIR.iterdir())


def apply_to_path():
    """Prepend the tools dir to THIS process's PATH only. Safe to call even
    if the dir doesn't exist yet or is empty."""
    if TOOLS_DIR.is_dir():
        current = os.environ.get("PATH", "")
        tools_str = str(TOOLS_DIR)
        if tools_str not in current.split(os.pathsep):
            os.environ["PATH"] = tools_str + os.pathsep + current


def _extract_exe(archive_path, exe_name, dest_dir):
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        if archive_path.suffix == ".zip":
            with zipfile.ZipFile(archive_path) as z:
                z.extractall(tmp)
        else:
            with tarfile.open(archive_path) as t:
                t.extractall(tmp)
        for candidate in tmp.rglob("*.exe"):
            if candidate.name.lower() == exe_name.lower() or exe_name == "*":
                dest_dir.mkdir(parents=True, exist_ok=True)
                shutil.copy2(candidate, dest_dir / candidate.name)
                return dest_dir / candidate.name
    return None


def _install_github_release(name, exe_name, repo, log):
    if requests is None:
        log(f"[{name}] skipped — requests module unavailable")
        return False
    try:
        api_url = f"https://api.github.com/repos/{repo}/releases/latest"
        resp = requests.get(api_url, timeout=20, headers={"Accept": "application/vnd.github+json"})
        resp.raise_for_status()
        assets = resp.json().get("assets", [])
        match = next((a for a in assets if _ASSET_PATTERN.search(a["name"])), None)
        if not match:
            log(f"[{name}] no Windows build found in latest release — skipping")
            return False
        log(f"[{name}] downloading {match['name']} ...")
        dl = requests.get(match["browser_download_url"], timeout=120)
        dl.raise_for_status()
        with tempfile.TemporaryDirectory() as tmp:
            archive_path = Path(tmp) / match["name"]
            archive_path.write_bytes(dl.content)
            result = _extract_exe(archive_path, exe_name, TOOLS_DIR)
        if result:
            log(f"[{name}] installed -> {result}")
            return True
        log(f"[{name}] downloaded but couldn't find {exe_name} inside the archive")
        return False
    except Exception as e:
        log(f"[{name}] failed: {e}")
        return False


def _install_winget(name, package_id, log):
    if os.name != "nt":
        log(f"[{name}] skipped — winget is Windows-only")
        return False
    try:
        log(f"[{name}] installing via winget ({package_id}) ...")
        result = _run_hidden(
            ["winget", "install", "--id", package_id, "-e", "--silent",
             "--accept-package-agreements", "--accept-source-agreements"],
            timeout=300,
        )
        if result.returncode == 0:
            log(f"[{name}] installed via winget")
            return True
        log(f"[{name}] winget exited with code {result.returncode}: {result.stderr.strip()[:200]}")
        return False
    except FileNotFoundError:
        log(f"[{name}] skipped — winget isn't available on this system")
        return False
    except Exception as e:
        log(f"[{name}] failed: {e}")
        return False


def install_all(log=print):
    """Installs the curated tool set. `log` is called with one line of
    progress text at a time — pass a GUI-log-box writer to show progress
    live instead of the default print()."""
    TOOLS_DIR.mkdir(parents=True, exist_ok=True)
    log(f"Installing tools to {TOOLS_DIR}")

    succeeded, failed = [], []
    for name, exe_name, repo in GITHUB_RELEASE_TOOLS:
        (succeeded if _install_github_release(name, exe_name, repo, log) else failed).append(name)
    for name, package_id in WINGET_TOOLS:
        (succeeded if _install_winget(name, package_id, log) else failed).append(name)

    apply_to_path()
    log(f"Done — {len(succeeded)} installed, {len(failed)} failed/skipped.")
    if failed:
        log("Not installed: " + ", ".join(failed))
    log("Tools not covered here (sqlmap, wpscan, hydra, john, ...) need a "
        "separate Python/Ruby/build toolchain — see the site's Windows panel notes.")
    return succeeded, failed


if __name__ == "__main__":
    install_all()
