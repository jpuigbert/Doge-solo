#!/usr/bin/env python3
"""
Logger configuration for DogeSolo.
"""

import logging
import sys
import os
import time
from pathlib import Path
from logging.handlers import RotatingFileHandler

def clean_old_logs(log_dir: Path, days: int = 30):
    """Elimina fitxers de log amb més de 'days' dies."""
    now = time.time()
    cutoff = now - (days * 86400)
    for f in log_dir.glob("*.log*"):  # Inclou rotats
        if f.is_file():
            mtime = f.stat().st_mtime
            if mtime < cutoff:
                try:
                    f.unlink()
                    print(f"Netejat log antic: {f.name}")
                except Exception as e:
                    print(f"Error netejant {f.name}: {e}")

def setup_logger(name: str = "DogeSolo") -> logging.Logger:
    """
    Configura i retorna un logger amb sortida a fitxer i consola.
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    log_dir = Path.home() / ".dogesolo" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    # Neteja automàtica (si està activada a configuració)
    try:
        from src.utils.config import Config
        config = Config()
        if config.get("clean_logs_auto", True):
            clean_old_logs(log_dir, days=30)
    except:
        pass

    log_file = log_dir / "dogesolo.log"

    file_handler = RotatingFileHandler(
        log_file, maxBytes=5*1024*1024, backupCount=3, encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger