"""Build WinLuxCD.exe and create a real Windows desktop shortcut.

Run from Windows PowerShell in this folder:
    python build.py

The output is a PyInstaller one-file, windowed executable at dist\WinLuxCD.exe.
"""

import importlib.util
import os
import subprocess
import sys
from pathlib import Path


BASE = Path(__file__).resolve().parent
ICON = BASE / "icons" / "winluxcd.ico"
APP = BASE / "winluxcd_app.py"
DIST = BASE / "dist"
EXE = DIST / "WinLuxCD.exe"
DESKTOP = Path(os.environ.get("USERPROFILE", str(Path.home()))) / "Desktop"


def run(command, **kwargs):
    print(">", " ".join(str(item) for item in command))
    subprocess.check_call(command, **kwargs)


def ensure_dependencies():
    if importlib.util.find_spec("PyInstaller") is None:
        run([sys.executable, "-m", "pip", "install", "pyinstaller"])


def build_exe():
    DIST.mkdir(parents=True, exist_ok=True)
    separator = ";" if os.name == "nt" else ":"
    run(
        [
            sys.executable,
            "-m",
            "PyInstaller",
            "--noconfirm",
            "--clean",
            "--onefile",
            "--windowed",
            "--name",
            "WinLuxCD",
            "--icon",
            str(ICON),
            "--add-data",
            "{}{}icons".format(ICON, separator),
            "--add-data",
            "{}{}icons".format(BASE / "icons" / "winluxcd-32.png", separator),
            "--add-data",
            "{}{}icons".format(BASE / "icons" / "winluxcd-16.png", separator),
            "--distpath",
            str(DIST),
            "--workpath",
            str(BASE / "build" / "WinLuxCD"),
            "--specpath",
            str(BASE / "build"),
            str(APP),
        ],
        cwd=str(BASE),
    )


def powershell_quote(value) -> str:
    return "'{}'".format(str(value).replace("'", "''"))


def make_shortcut():
    if not EXE.exists():
        print("!! exe not found, skipping shortcut")
        return
    if os.name != "nt":
        print("!! Windows PowerShell unavailable; run this build with Windows Python")
        return

    DESKTOP.mkdir(parents=True, exist_ok=True)
    link = DESKTOP / "WinLuxCD.lnk"
    ps = "; ".join(
        [
            "$w = New-Object -ComObject WScript.Shell",
            "$s = $w.CreateShortcut({})".format(powershell_quote(link)),
            "$s.TargetPath = {}".format(powershell_quote(EXE)),
            "$s.WorkingDirectory = {}".format(powershell_quote(EXE.parent)),
            "$s.IconLocation = {}".format(powershell_quote(str(EXE) + ",0")),
            "$s.Description = 'WinLuxCD - Windows path to WSL converter'",
            "$s.Save()",
        ]
    )
    run(["powershell.exe", "-NoProfile", "-Command", ps])
    print("Shortcut:", link)


def main():
    ensure_dependencies()
    build_exe()
    make_shortcut()
    if not EXE.exists():
        raise SystemExit("Build completed without creating {}".format(EXE))
    print("\nDone.")
    print("  EXE      :", EXE)
    print("  Shortcut :", DESKTOP / "WinLuxCD.lnk")


if __name__ == "__main__":
    main()
