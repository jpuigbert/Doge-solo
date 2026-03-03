#!/usr/bin/env python3
"""
Utilitats per a la descàrrega de fitxers.
"""

import requests
from pathlib import Path
from typing import Callable, Optional

def download_file(url: str, dest_path: Path, callback: Optional[Callable[[int, int], None]] = None) -> bool:
    """
    Descarrega un fitxer des d'una URL i el guarda a dest_path.
    Si es proporciona callback, es crida amb (bytes_downloaded, total_bytes).
    Retorna True si èxit, False si error.
    """
    try:
        dest_path.parent.mkdir(parents=True, exist_ok=True)

        response = requests.get(url, stream=True)
        response.raise_for_status()

        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0

        with open(dest_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                downloaded += len(chunk)
                if callback and total_size:
                    callback(downloaded, total_size)

        return True
    except Exception as e:
        print(f"Error descarregant {url}: {e}")
        return False