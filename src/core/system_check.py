#!/usr/bin/env python3
"""
Comprovacions del sistema per a DogeSolo.
"""

import platform
import shutil
from pathlib import Path

def check_disk_space(path: Path, required_gb: float = 50) -> bool:
    """
    Comprova si hi ha espai suficient al disc per al node (per defecte 50 GB).
    """
    try:
        # Assegurar que el directori existeix per a la comprovació
        path.mkdir(parents=True, exist_ok=True)
        usage = shutil.disk_usage(path)
        free_gb = usage.free / (1024**3)
        return free_gb >= required_gb
    except Exception:
        return False

def get_system_info() -> dict:
    """
    Retorna informació del sistema: sistema operatiu, arquitectura, etc.
    """
    return {
        'system': platform.system().lower(),
        'architecture': platform.machine().lower(),
        'processor': platform.processor(),
        'python_version': platform.python_version(),
        'disk_free_gb': shutil.disk_usage(Path.home()).free / (1024**3)
    }

def is_windows() -> bool:
    return platform.system().lower() == 'windows'

def is_macos() -> bool:
    return platform.system().lower() == 'darwin'

def is_linux() -> bool:
    return platform.system().lower() == 'linux'