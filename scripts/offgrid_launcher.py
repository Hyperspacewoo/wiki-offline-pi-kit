#!/usr/bin/env python3
"""Small cross-platform launcher for Offgrid Kit.

This intentionally uses only Python's standard library so it can run from the
bundled runtime or a system Python without adding another dependency.
"""

from __future__ import annotations

import os
import platform
import subprocess
import sys
import threading
import urllib.request
import webbrowser
from pathlib import Path


KIT_ROOT = Path(__file__).resolve().parents[1]


URLS = {
    "Dashboard": "http://localhost:8090",
    "Setup Check": "http://localhost:8090/setup",
    "Knowledge": "http://localhost:8080",
    "Maps": "http://localhost:8091",
    "Offline AI": "http://localhost:8092",
    "Ebooks": "http://localhost:8090/ebooks",
    "Updates": "http://localhost:8090/updates",
    "Field Cards": "http://localhost:8090/field-cards",
    "Offline Proof": "http://localhost:8090/offline-proof",
}


def open_url(url: str) -> None:
    webbrowser.open(url, new=2)


def start_repair_command() -> list[str]:
    system = platform.system().lower()
    if system == "windows":
        return [
            "powershell.exe",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(KIT_ROOT / "scripts" / "windows_bootstrap.ps1"),
            "-KitDir",
            str(KIT_ROOT),
            "-OpenDashboard",
        ]
    return ["bash", str(KIT_ROOT / "INSTALL_OFFLINE_KNOWLEDGE.sh")]


def start_repair(log) -> None:
    cmd = start_repair_command()
    log(f"Running: {' '.join(cmd)}\n")
    try:
        proc = subprocess.Popen(
            cmd,
            cwd=str(KIT_ROOT),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        assert proc.stdout is not None
        for line in proc.stdout:
            log(line)
        code = proc.wait()
        if code == 0:
            log("\nSetup finished. Opening dashboard.\n")
            open_url(URLS["Setup Check"])
        else:
            log(f"\nSetup exited with code {code}.\n")
    except Exception as exc:
        log(f"Could not start kit: {exc}\n")


def health_check(log) -> None:
    try:
        with urllib.request.urlopen("http://localhost:8090/health", timeout=4) as resp:
            log(resp.read().decode("utf-8", errors="replace") + "\n")
    except Exception as exc:
        log(f"Dashboard is not responding yet. Start/repair the kit first.\n{exc}\n")


def console_main() -> int:
    print("Offgrid Kit Launcher")
    print("1. Start / Repair Kit")
    print("2. Open Dashboard")
    print("3. Open Setup Check")
    print("4. Health Check")
    choice = input("> ").strip()
    if choice == "1":
        start_repair(lambda s: print(s, end=""))
    elif choice == "2":
        open_url(URLS["Dashboard"])
    elif choice == "3":
        open_url(URLS["Setup Check"])
    elif choice == "4":
        health_check(lambda s: print(s, end=""))
    return 0


def gui_main() -> int:
    try:
        import tkinter as tk
        from tkinter import scrolledtext
    except Exception:
        return console_main()

    try:
        root = tk.Tk()
    except Exception:
        return console_main()
    root.title("Offgrid Kit Launcher")
    root.geometry("760x600")
    root.minsize(620, 500)
    root.configure(bg="#f6f8fc")

    title = tk.Label(root, text="Offgrid Kit", font=("Segoe UI", 26, "bold"), bg="#f6f8fc", fg="#172033")
    title.pack(anchor="w", padx=24, pady=(22, 2))
    subtitle = tk.Label(
        root,
        text="Start the kit, open the dashboard, and verify local offline services.",
        font=("Segoe UI", 11),
        bg="#f6f8fc",
        fg="#657086",
    )
    subtitle.pack(anchor="w", padx=26, pady=(0, 18))

    output = scrolledtext.ScrolledText(root, height=10, font=("Consolas", 9), wrap="word")
    output.pack(side="bottom", fill="both", expand=True, padx=24, pady=20)

    def log(text: str) -> None:
        root.after(0, lambda: (output.insert("end", text), output.see("end")))

    def run_background(fn) -> None:
        threading.Thread(target=fn, daemon=True).start()

    top = tk.Frame(root, bg="#f6f8fc")
    top.pack(fill="x", padx=24)

    primary_style = {"font": ("Segoe UI", 12, "bold"), "height": 2, "bd": 0, "fg": "white"}
    tk.Button(
        top,
        text="Start / Repair Kit",
        bg="#0a84ff",
        command=lambda: run_background(lambda: start_repair(log)),
        **primary_style,
    ).pack(side="left", fill="x", expand=True, padx=(0, 10))
    tk.Button(
        top,
        text="Open Dashboard",
        bg="#0b7f5f",
        command=lambda: open_url(URLS["Dashboard"]),
        **primary_style,
    ).pack(side="left", fill="x", expand=True, padx=(10, 0))

    grid = tk.Frame(root, bg="#f6f8fc")
    grid.pack(fill="x", padx=24, pady=18)
    for idx, (label, url) in enumerate(URLS.items()):
        if label == "Dashboard":
            continue
        b = tk.Button(grid, text=label, command=lambda u=url: open_url(u), font=("Segoe UI", 10), height=2)
        b.grid(row=(idx - 1) // 4, column=(idx - 1) % 4, sticky="ew", padx=5, pady=5)
    for col in range(4):
        grid.columnconfigure(col, weight=1)

    tools = tk.Frame(root, bg="#f6f8fc")
    tools.pack(fill="x", padx=24)
    tk.Button(tools, text="Health Check", command=lambda: run_background(lambda: health_check(log)), height=2).pack(
        side="left", fill="x", expand=True, padx=(0, 8)
    )
    tk.Button(tools, text="Open Kit Folder", command=lambda: open_folder(KIT_ROOT), height=2).pack(
        side="left", fill="x", expand=True, padx=8
    )
    tk.Button(tools, text="Close", command=root.destroy, height=2).pack(side="left", fill="x", expand=True, padx=(8, 0))

    output.insert("end", "Ready. Click Start / Repair Kit on a fresh machine, or Open Dashboard if services are already running.\n")
    root.mainloop()
    return 0


def open_folder(path: Path) -> None:
    system = platform.system().lower()
    if system == "darwin":
        subprocess.Popen(["open", str(path)])
    elif system == "windows":
        os.startfile(str(path))  # type: ignore[attr-defined]
    else:
        subprocess.Popen(["xdg-open", str(path)])


if __name__ == "__main__":
    raise SystemExit(gui_main())
