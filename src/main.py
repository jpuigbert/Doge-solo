#!/usr/bin/env python3
"""DogeSolo — Mineria en solitari de Dogecoin per a tothom."""

import sys
import os
from pathlib import Path

# Assegurar que src/ és al path (necessari per PyInstaller i execució directa)
_root = Path(__file__).parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

# Per a executables PyInstaller, els recursos estan a _MEIPASS
def resource_path(relative_path: str) -> str:
    base = getattr(sys, "_MEIPASS", str(_root / "src"))
    return os.path.join(base, relative_path)

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from src.gui.main_window import MainWindow
from src.utils.logger import setup_logger
from src.utils.config import Config
from src.core.node_manager import NodeManager
from src.core.miner_manager import MinerManager
from src.core.wallet_manager import WalletManager


def main():
    logger = setup_logger()
    logger.info("Iniciant DogeSolo v1.0.0...")

    # Carregar configuració
    config = Config()

    # Crear gestors amb configuració
    node_manager = NodeManager(config=config)
    miner_manager = MinerManager()
    miner_manager.set_node_manager(node_manager)
    wallet_manager = WalletManager(node_manager)

    app = QApplication.instance() or QApplication(sys.argv)
    app.setApplicationName("DogeSolo")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("DogeSolo Project")
    app.setOrganizationDomain("dogesolo.org")
    app.setStyle("Fusion")

    # Alta resolució (HiDPI / Retina)
    app.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    window = MainWindow(
        config=config,
        node_manager=node_manager,
        miner_manager=miner_manager,
        wallet_manager=wallet_manager
    )
    window.show()
    window.raise_()
    window.activateWindow()

    logger.info("Finestra principal oberta.")
    sys.exit(app.exec())


if __name__ == "__main__":
    main()