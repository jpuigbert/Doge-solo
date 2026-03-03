#!/usr/bin/env python3
"""
Script de compilació DogeSolo amb PyInstaller.
Ús:
    python build.py           → detecta la plataforma actual
    python build.py --clean   → esborra dist/ i build/ primer
"""

import sys
import os
import shutil
import platform
import subprocess

APP_NAME = "DogeSolo"
VERSION = "1.0.0"
ENTRY_POINT = "src/main.py"

SYSTEM = platform.system().lower()


def clean():
    for folder in ["dist", "build"]:
        if os.path.exists(folder):
            shutil.rmtree(folder)
            print(f"  Eliminat: {folder}/")
    for spec in [f"{APP_NAME}.spec"]:
        if os.path.exists(spec):
            os.remove(spec)


def get_icon():
    if SYSTEM == "windows":
        return "src/resources/icon.ico"
    elif SYSTEM == "darwin":
        return "src/resources/icon.icns"
    else:
        return "src/resources/icon.png"


def get_datas():
    """Fitxers addicionals a incloure en l'executable."""
    datas = [
        ("src/resources", "resources"),
        ("src/gui/styles", "gui/styles"),
    ]
    return datas


def build():
    icon = get_icon()
    datas = get_datas()

    data_args = []
    sep = ";" if SYSTEM == "windows" else ":"
    for src, dst in datas:
        if os.path.exists(src):
            data_args += ["--add-data", f"{src}{sep}{dst}"]

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--windowed",
        f"--name={APP_NAME}",
        f"--icon={icon}",
    ] + data_args + [
        # Imports ocults necessaris
        "--hidden-import=scrypt",
        "--hidden-import=_scrypt",               # Important per a la part nativa
        "--collect-all=scrypt",                  # Inclou totes les dades de scrypt
        "--hidden-import=bitcoinrpc",
        "--hidden-import=bitcoinrpc.authproxy",
        "--hidden-import=base58",
        "--hidden-import=PySide6.QtCore",
        "--hidden-import=PySide6.QtWidgets",
        "--hidden-import=PySide6.QtGui",
        "--hidden-import=matplotlib",
        "--hidden-import=matplotlib.backends.backend_qt5agg",
        "--collect-all=matplotlib",
        ENTRY_POINT,
    ]

    print(f"\n{'='*50}")
    print(f"  Compilant {APP_NAME} v{VERSION} per {SYSTEM.upper()}")
    print(f"{'='*50}\n")

    result = subprocess.run(cmd)

    if result.returncode == 0:
        print(f"\n✅ Compilació exitosa!")
        if SYSTEM == "windows":
            print(f"   Executable: dist/{APP_NAME}.exe")
        elif SYSTEM == "darwin":
            print(f"   Bundle: dist/{APP_NAME}.app")
            print(f"   Ara executa: cd installers/macos && ./create_dmg.sh")
        else:
            print(f"   Executable: dist/{APP_NAME}")
            print(f"   Ara executa: cd installers/linux && ./create_deb.sh")
    else:
        print(f"\n❌ Error en la compilació (codi {result.returncode})")
        sys.exit(1)


if __name__ == "__main__":
    if "--clean" in sys.argv:
        print("Netejant directoris anteriors...")
        clean()

    build()