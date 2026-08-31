#!/usr/bin/env python3
"""
HexStrike AI — Windows launcher, WSL2 edition.

This does NOT run hexstrike_server.py itself anymore. It's a thin
orchestrator around a WSL2 distro ("HexStrikeAI") that has the real thing —
a genuine Kali userland with hexstrike_server.py and its whole tool
ecosystem installed via apt (see wsl/Dockerfile) — imported into it. That's
the entire reason this exists: the previous all-in-one PyInstaller exe could
only offer the handful of tools with a native Windows binary; running the
real Linux server inside a real (if minimal) Linux VM means every tool
HexStrike can drive on Kali just works here too, no picking and choosing.

Still "no terminal" for the person running it: every wsl.exe/dism call this
makes runs hidden (CREATE_NO_WINDOW) with output routed into the GUI's log
box, and enabling the WSL2 Windows feature (the one step that must be
elevated — Windows won't let anything toggle OS features without it) is
triggered via ShellExecute's "runas" verb, which raises the normal UAC
dialog rather than requiring the user to open an admin terminal themselves.

WSL2 gives a service bound to 0.0.0.0 inside the distro automatic loopback
forwarding to 127.0.0.1 on the Windows host — hexstrike_server.py's own
`app.run(host="0.0.0.0", ...)` already does the right thing unmodified, no
wrapper needed the way the old in-process exe needed one.
"""

import ctypes
import os
import subprocess
import sys
import tempfile
import threading
import time
import webbrowser
from pathlib import Path

import tkinter as tk
from tkinter import scrolledtext

try:
    import requests
except ImportError:
    requests = None

DISTRO_NAME = "HexStrikeAI"
DASHBOARD_URL = "http://127.0.0.1:8888"
ROOTFS_URL = "https://github.com/Howdyz/hexstrike-ai/releases/latest/download/hexstrike-wsl-rootfs.tar.gz"
INSTALL_DIR = Path(os.environ.get("LOCALAPPDATA", tempfile.gettempdir())) / "HexStrike" / "wsl"

_NO_WINDOW = 0x08000000  # subprocess.CREATE_NO_WINDOW, defined only on Windows


def _decode_wsl_bytes(raw):
    """wsl.exe writes UTF-16LE (often BOM-prefixed) to a redirected pipe
    instead of the console codepage it uses on a real terminal — decoding
    that as whatever the process's default text encoding happens to be
    (which varies by Windows locale/UTF-8-mode setting) either garbles the
    text or raises UnicodeDecodeError outright on the BOM bytes. Detect and
    decode it properly instead of guessing."""
    if raw[:2] == b"\xff\xfe":
        return raw[2:].decode("utf-16le", errors="replace")
    if raw[:2] == b"\xfe\xff":
        return raw[2:].decode("utf-16be", errors="replace")
    sample = raw[:200]
    if sample.count(b"\x00") > len(sample) // 4:
        return raw.decode("utf-16le", errors="replace")
    return raw.decode("utf-8", errors="replace")


def _run_hidden(cmd, timeout=None, **kwargs):
    flags = _NO_WINDOW if os.name == "nt" else 0
    return subprocess.run(cmd, capture_output=True, timeout=timeout,
                           creationflags=flags, **kwargs)


def _popen_hidden(cmd, **kwargs):
    flags = _NO_WINDOW if os.name == "nt" else 0
    return subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                             text=True, errors="replace", creationflags=flags, **kwargs)


def wsl_feature_enabled():
    """True if `wsl.exe` itself works well enough to list distros — i.e. the
    Windows optional features are already on, whether or not our distro is
    imported yet."""
    try:
        result = _run_hidden(["wsl", "--status"], timeout=15)
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def distro_imported():
    try:
        result = _run_hidden(["wsl", "-l", "-q"], timeout=15)
        names = [n.strip().replace("\x00", "") for n in _decode_wsl_bytes(result.stdout).splitlines()]
        return DISTRO_NAME in names
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def install_wsl_feature(log):
    """Enabling the WSL2 Windows feature is the one step Windows won't allow
    without elevation — ShellExecute's "runas" verb raises the standard UAC
    prompt rather than needing the user to find and open an admin terminal.
    Returns True once wsl.exe reports working, False if it still doesn't
    (most commonly: a restart is needed, which is a real Windows requirement
    we can't script around)."""
    log("WSL2 isn't set up yet on this PC — requesting permission to enable it "
        "(you'll see a Windows admin prompt) ...")
    try:
        rc = ctypes.windll.shell32.ShellExecuteW(
            None, "runas", "wsl.exe", "--install --no-distro", None, 0
        )
        if rc <= 32:
            log("Permission was denied, or Windows couldn't launch the installer. "
                "WSL2 setup needs to be approved to continue.")
            return False
    except Exception as e:
        log(f"Couldn't request elevation: {e}")
        return False

    for _ in range(60):
        time.sleep(2)
        if wsl_feature_enabled():
            log("WSL2 is enabled.")
            return True
    log("WSL2 still isn't responding after setup — this Windows install likely "
        "needs a restart before it finishes activating. Restart your PC, then "
        "run HexStrikeAI-Windows.exe again.")
    return False


def download_rootfs(dest_path, progress):
    if requests is None:
        progress(-1, "requests module unavailable — can't download")
        return False
    try:
        with requests.get(ROOTFS_URL, stream=True, timeout=30) as r:
            r.raise_for_status()
            total = int(r.headers.get("content-length", 0))
            done = 0
            with open(dest_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=1024 * 1024):
                    f.write(chunk)
                    done += len(chunk)
                    pct = int(done / total * 100) if total else -1
                    progress(pct, f"{done / (1024*1024):.0f} MB" + (f" / {total / (1024*1024):.0f} MB" if total else ""))
        return True
    except Exception as e:
        progress(-1, f"download failed: {e}")
        return False


def import_distro(tarball_path, log):
    INSTALL_DIR.mkdir(parents=True, exist_ok=True)
    log("Importing the HexStrike image into WSL2 (this can take a minute) ...")
    result = _run_hidden(
        ["wsl", "--import", DISTRO_NAME, str(INSTALL_DIR), str(tarball_path), "--version", "2"],
        timeout=600,
    )
    if result.returncode == 0:
        log("Import complete.")
        return True
    log(f"Import failed: {_decode_wsl_bytes(result.stderr).strip()[:300]}")
    return False


class ServerHandle:
    """Wraps the `wsl -d HexStrikeAI -- python3 hexstrike_server.py` process —
    same idea as the old in-process Flask thread, just one layer removed."""

    def __init__(self):
        self.process = None

    def start(self, log):
        if self.process and self.process.poll() is None:
            return
        self.process = _popen_hidden(
            ["wsl", "-d", DISTRO_NAME, "--", "python3", "hexstrike_server.py"]
        )

        def pump_output():
            for line in self.process.stdout:
                log(line.rstrip("\n"))

        threading.Thread(target=pump_output, daemon=True).start()

    def stop(self):
        if self.process and self.process.poll() is None:
            self.process.terminate()
        # `wsl --terminate` powers the whole lightweight VM off, not just the
        # one process — the same "power off this one appliance" idea a
        # VirtualBox-style player would give, just via the WSL2 CLI instead
        # of a GUI VM manager.
        _run_hidden(["wsl", "--terminate", DISTRO_NAME], timeout=30)

    def is_running(self):
        return self.process is not None and self.process.poll() is None


server = ServerHandle()


def build_ui():
    root = tk.Tk()
    root.title("HexStrike AI (Windows / WSL2)")
    root.geometry("640x460")
    root.configure(bg="#14110F")

    fg = "#F2EDE1"
    dim = "#8C8377"
    accent = "#2F8F7A"
    warn = "#E8402C"

    tk.Label(root, text="🛰️ HexStrike AI", font=("Segoe UI", 16, "bold"),
             bg="#14110F", fg=fg).pack(pady=(18, 4))

    status_var = tk.StringVar(value="Checking WSL2 …")
    status_label = tk.Label(root, textvariable=status_var, font=("Segoe UI", 10),
                             bg="#14110F", fg=accent, wraplength=560, justify="center")
    status_label.pack(pady=(0, 14))

    tk.Label(root,
             text=("Runs entirely on this machine, inside a small dedicated Linux\n"
                   "environment (WSL2) — nothing here is hosted, proxied, or logged by\n"
                   "Truth Button. Only point it at systems you own or are explicitly\n"
                   "authorized to test."),
             font=("Segoe UI", 9), bg="#14110F", fg=dim, justify="center").pack(pady=(0, 16), padx=20)

    btn_frame = tk.Frame(root, bg="#14110F")
    btn_frame.pack(pady=4)

    log_box = scrolledtext.ScrolledText(root, height=10, width=72, bg="#1C1814", fg=dim,
                                         font=("Consolas", 8), relief="flat")
    log_box.pack(pady=(16, 10), padx=16)
    log_box.configure(state="disabled")

    def log_line(msg):
        def _do():
            log_box.configure(state="normal")
            log_box.insert(tk.END, str(msg).rstrip("\n") + "\n")
            log_box.see(tk.END)
            log_box.configure(state="disabled")
        root.after(0, _do)

    def set_status(text, ok=True):
        def _do():
            status_var.set(text)
            status_label.configure(fg=accent if ok else warn)
        root.after(0, _do)

    def open_dashboard():
        webbrowser.open(DASHBOARD_URL)

    def do_quit():
        server.stop()
        os._exit(0)

    def mk_button(parent, text, cmd, bg):
        return tk.Button(parent, text=text, command=cmd, bg=bg, fg="#14110F",
                          activebackground=bg, font=("Segoe UI", 9, "bold"),
                          relief="flat", padx=12, pady=8, cursor="hand2")

    start_btn = mk_button(btn_frame, "▶ Start HexStrike", lambda: None, accent)
    dash_btn = mk_button(btn_frame, "Open Dashboard →", open_dashboard, accent)
    stop_btn = mk_button(btn_frame, "🛑 Stop && Quit", do_quit, warn)
    start_btn.grid(row=0, column=0, padx=4)
    dash_btn.grid(row=0, column=1, padx=4)
    stop_btn.grid(row=0, column=2, padx=4)
    dash_btn.configure(state="disabled")

    def do_start():
        start_btn.configure(state="disabled", text="Starting…")

        def worker():
            server.start(log_line)
            set_status(f"Running — {DASHBOARD_URL}", ok=True)
            root.after(0, lambda: dash_btn.configure(state="normal"))
            root.after(0, lambda: start_btn.configure(text="▶ Start HexStrike", state="normal"))

        threading.Thread(target=worker, daemon=True).start()

    start_btn.configure(command=do_start, state="disabled")

    def setup_flow():
        try:
            if not wsl_feature_enabled():
                set_status("Setting up WSL2 …", ok=False)
                if not install_wsl_feature(log_line):
                    set_status("WSL2 setup incomplete — see the log below.", ok=False)
                    return

            if not distro_imported():
                set_status("Downloading HexStrike image …", ok=True)
                with tempfile.TemporaryDirectory() as tmp:
                    tarball = Path(tmp) / "hexstrike-wsl-rootfs.tar.gz"

                    def progress(pct, text):
                        if pct >= 0:
                            set_status(f"Downloading HexStrike image — {pct}% ({text})")
                        else:
                            log_line(text)

                    if not download_rootfs(tarball, progress):
                        set_status("Download failed — see the log below.", ok=False)
                        return
                    if not import_distro(tarball, log_line):
                        set_status("Import failed — see the log below.", ok=False)
                        return

            set_status("Ready.", ok=True)
            root.after(0, lambda: start_btn.configure(state="normal"))
        except Exception as e:
            log_line(f"Unexpected error during setup: {e!r}")
            set_status("Setup failed unexpectedly — see the log below.", ok=False)

    threading.Thread(target=setup_flow, daemon=True).start()

    root.protocol("WM_DELETE_WINDOW", do_quit)
    return root


if __name__ == "__main__":
    ui = build_ui()
    ui.mainloop()
