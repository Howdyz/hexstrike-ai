#!/usr/bin/env python3
"""
HexStrike AI — Windows edition, single-file, no terminal.

This is the entry point built into HexStrikeAI-Windows.exe by
hexstrike_windows.spec / .github/workflows/build-windows.yml. Unlike the
Linux flow (a tiny launcher process that starts hexstrike_server.py on
request from the browser), there is nothing to install and nothing to run
from a command line here: double-clicking the .exe *is* "starting the
server" — it imports hexstrike_server as a library, runs its Flask app on
127.0.0.1:8888 in a background thread, and shows a small status window so
the person running it can see it's alive without ever seeing a console.

The Ultimate Tool Kit — Windows panel on the site talks to the exact same
endpoints the Linux panel does (GET /health, POST /api/kill-switch) — same
process, same port, same JSON API — so nothing on the site's JS side needs
to know which OS produced the process it's talking to.
"""

import os
import sys
import threading
import webbrowser

# Must happen before hexstrike_server is imported: a windowed (--noconsole)
# PyInstaller build has no real stdout/stderr, and hexstrike_server.py (like
# any 17k-line script) has bare print() calls scattered through request
# handlers. Rather than track down every one, give it harmless no-op streams
# so none of them can ever crash a request with "NoneType has no attribute
# 'write'" — a well-known failure mode for frozen windowed apps.
class _NullStream:
    def write(self, *a, **k):
        pass

    def flush(self):
        pass


if sys.stdout is None:
    sys.stdout = _NullStream()
if sys.stderr is None:
    sys.stderr = _NullStream()

os.environ.setdefault("HEXSTRIKE_PORT", "8888")

import tkinter as tk
from tkinter import scrolledtext

import hexstrike_server as hx  # noqa: E402  (must come after the stdout/stderr guard above)
import hexstrike_tool_installer as tool_installer  # noqa: E402

# A previous run may have already installed tools to %LOCALAPPDATA%\HexStrike\tools —
# make them visible to this run's subprocess calls immediately, no re-download needed.
tool_installer.apply_to_path()

HOST = "127.0.0.1"
PORT = hx.API_PORT
DASHBOARD_URL = f"http://{HOST}:{PORT}"

_server_thread = None
_server_started = threading.Event()


def _run_server():
    try:
        hx.app.run(host=HOST, port=PORT, debug=False, use_reloader=False)
    except Exception as e:
        hx.logger.error(f"HexStrike server thread died: {e}")
    finally:
        _server_started.clear()


def start_server():
    global _server_thread
    if _server_thread and _server_thread.is_alive():
        return
    _server_thread = threading.Thread(target=_run_server, daemon=True)
    _server_thread.start()
    _server_started.set()


def build_ui():
    root = tk.Tk()
    root.title("HexStrike AI (Windows)")
    root.geometry("560x400")
    root.configure(bg="#14110F")

    fg = "#F2EDE1"
    dim = "#8C8377"
    accent = "#2F8F7A"
    warn = "#E8402C"

    tk.Label(root, text="🛰️ HexStrike AI", font=("Segoe UI", 16, "bold"),
              bg="#14110F", fg=fg).pack(pady=(18, 4))

    status_var = tk.StringVar(value=f"Starting on {DASHBOARD_URL} …")
    status_label = tk.Label(root, textvariable=status_var, font=("Segoe UI", 10),
                              bg="#14110F", fg=accent, wraplength=460, justify="center")
    status_label.pack(pady=(0, 14))

    tk.Label(root,
             text=("Runs entirely on this machine — nothing here is hosted, proxied,\n"
                   "or logged by Truth Button. Only point it at systems you own or are\n"
                   "explicitly authorized to test. Keep this window open while you use it —\n"
                   "closing it stops the server."),
             font=("Segoe UI", 9), bg="#14110F", fg=dim, justify="center").pack(pady=(0, 16), padx=20)

    btn_frame = tk.Frame(root, bg="#14110F")
    btn_frame.pack(pady=4)

    def open_dashboard():
        webbrowser.open(DASHBOARD_URL)

    def do_quit():
        os._exit(0)

    def mk_button(parent, text, cmd, bg):
        b = tk.Button(parent, text=text, command=cmd, bg=bg, fg="#14110F",
                      activebackground=bg, font=("Segoe UI", 10, "bold"),
                      relief="flat", padx=14, pady=8, cursor="hand2")
        return b

    install_btn = mk_button(btn_frame, "📦 Install Tools", lambda: None, accent)
    mk_button(btn_frame, "Open Dashboard →", open_dashboard, accent).grid(row=0, column=1, padx=6)
    mk_button(btn_frame, "🛑 Stop && Quit", do_quit, warn).grid(row=0, column=2, padx=6)
    install_btn.grid(row=0, column=0, padx=6)

    log_box = scrolledtext.ScrolledText(root, height=8, width=62, bg="#1C1814", fg=dim,
                                          font=("Consolas", 8), relief="flat")
    log_box.pack(pady=(16, 10), padx=16)
    log_box.configure(state="disabled")

    def log_line(msg):
        log_box.configure(state="normal")
        log_box.insert(tk.END, str(msg).rstrip("\n") + "\n")
        log_box.see(tk.END)
        log_box.configure(state="disabled")

    class _TkLogHandler:
        def write(self, msg):
            if msg.strip():
                log_line(msg)

        def flush(self):
            pass

    import logging
    handler = logging.StreamHandler(_TkLogHandler())
    handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s', datefmt='%H:%M:%S'))
    hx.logger.addHandler(handler)

    _installing = threading.Event()

    def do_install_tools():
        if _installing.is_set():
            return
        _installing.set()
        install_btn.configure(state="disabled", text="Installing…")
        log_line("— Installing tools (nmap, hashcat, nuclei, httpx, subfinder, katana, ffuf, gobuster, dalfox) —")

        def worker():
            try:
                # log_line() touches the Tk widget; schedule each line onto the
                # main thread instead of calling it directly from this worker.
                tool_installer.install_all(log=lambda m: root.after(0, log_line, m))
            finally:
                root.after(0, lambda: (install_btn.configure(state="normal", text="📦 Install Tools"),
                                        _installing.clear()))

        threading.Thread(target=worker, daemon=True).start()

    install_btn.configure(command=do_install_tools)
    if tool_installer.already_installed():
        log_line(f"Previously installed tools found at {tool_installer.TOOLS_DIR} — added to PATH for this session.")

    def poll_status():
        if _server_started.is_set():
            status_var.set(f"Running — {DASHBOARD_URL}")
            status_label.configure(fg=accent)
        else:
            status_var.set("Stopped")
            status_label.configure(fg=warn)
        root.after(1000, poll_status)

    root.protocol("WM_DELETE_WINDOW", do_quit)
    poll_status()
    return root


if __name__ == "__main__":
    start_server()
    ui = build_ui()
    ui.mainloop()
