#!/usr/bin/env python3
"""Finestra principal de DogeSolo."""

import os
import sys
from PySide6.QtWidgets import (QMainWindow, QTabWidget, QVBoxLayout,
                               QWidget, QStatusBar, QLabel, QPushButton,
                               QMessageBox)
from PySide6.QtCore import Slot, QTimer, Qt
from PySide6.QtGui import QIcon

from src.gui.miner_tab import MinerTab
from src.gui.node_tab import NodeTab
from src.gui.wallet_tab import WalletTab
from src.gui.settings_tab import SettingsTab
from src.gui.guide_tab import GuideTab
from src.gui.notification_manager import NotificationManager
from src.core.miner_manager import format_hashrate


class MainWindow(QMainWindow):
    def __init__(self, config, node_manager, miner_manager, wallet_manager):
        super().__init__()
        self.config = config
        self.node_manager = node_manager
        self.miner_manager = miner_manager
        self.wallet_manager = wallet_manager

        self.setWindowTitle("DogeSolo — Solo Mining Dogecoin 🐕")
        self.setMinimumSize(960, 720)

        self.notifier = NotificationManager(self)

        self._apply_theme()
        self._load_icon()
        self._create_ui()
        self._create_status_bar()
        self._setup_timers()

        # Comprovar sistema en iniciar
        QTimer.singleShot(500, self._check_system)

        # Seguiment del tema del sistema si està activat
        self.follow_system_theme = self.config.get("follow_system_theme", False)
        if self.follow_system_theme:
            self._apply_system_theme()
            self.theme_timer = QTimer()
            self.theme_timer.timeout.connect(self._check_system_theme)
            self.theme_timer.start(60000)  # cada minut

    def _apply_theme(self):
        theme = self.config.get("theme", "Fosc")
        fname = "dark_theme.qss" if theme != "Clar" else "light_theme.qss"
        qss_path = os.path.join(os.path.dirname(__file__), "styles", fname)
        if os.path.exists(qss_path):
            with open(qss_path, "r", encoding="utf-8") as f:
                self.setStyleSheet(f.read())

    def _load_icon(self):
        for name in ["icon.png", "icon.ico", "icon.icns"]:
            path = os.path.join(os.path.dirname(__file__), "..", "resources", name)
            if os.path.exists(path):
                self.setWindowIcon(QIcon(path))
                break

    def _create_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)

        self.miner_tab = MinerTab(self.node_manager, self.miner_manager, self.config)
        self.node_tab = NodeTab(self.node_manager)
        self.wallet_tab = WalletTab(self.node_manager, self.wallet_manager)
        self.settings_tab = SettingsTab(self.config)
        self.guide_tab = GuideTab()

        self.tabs.addTab(self.miner_tab, "⛏️  Mineria")
        self.tabs.addTab(self.node_tab,  "🖥️  Node")
        self.tabs.addTab(self.wallet_tab, "💰  Cartera")
        self.tabs.addTab(self.settings_tab, "⚙️  Configuració")
        self.tabs.addTab(self.guide_tab, "📘  Guia")

        layout.addWidget(self.tabs)

    def _create_status_bar(self):
        bar = QStatusBar()
        self.setStatusBar(bar)

        self.node_lbl = QLabel("Node: 🔴 Aturat")
        self.miner_lbl = QLabel(" │ Miner: ⚪ Inactiu")
        self.balance_lbl = QLabel("")

        bar.addWidget(self.node_lbl)
        bar.addWidget(self.miner_lbl)
        bar.addWidget(self.balance_lbl)

        help_btn = QPushButton("❓")
        help_btn.setMaximumWidth(28)
        help_btn.setFlat(True)
        help_btn.setToolTip("Ajuda ràpida")
        help_btn.clicked.connect(self._show_help)
        bar.addPermanentWidget(help_btn)

    def _setup_timers(self):
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self._update_status)
        self.status_timer.start(2500)

    @Slot()
    def _update_status(self):
        # Node
        if self.node_manager.is_running():
            block = self.node_manager.get_block_count()
            txt = f"Node: 🟢 Bloc #{block:,}" if block else "Node: 🟢 En marxa"
            self.node_lbl.setText(txt)
        else:
            self.node_lbl.setText("Node: 🔴 Aturat")

        # Miner
        if self.miner_manager.is_mining():
            hs = self.miner_manager.get_stats().last_hashrate
            self.miner_lbl.setText(f" │ Miner: 🟢 {format_hashrate(hs)}")
        else:
            self.miner_lbl.setText(" │ Miner: ⚪ Inactiu")

        # Saldo
        balance = self.wallet_manager.get_balance()
        if balance is not None:
            self.balance_lbl.setText(f" │ 💰 {balance:,.4f} DOGE")
        else:
            self.balance_lbl.setText("")

    @Slot()
    def _check_system(self):
        if not self.node_manager.is_installed():
            self.node_tab.show_installation_prompt()

    @Slot()
    def _show_help(self):
        QMessageBox.information(
            self, "Ajuda Ràpida — DogeSolo",
            "📋  COM FUNCIONA:\n\n"
            "1️⃣   Pestanya 'Node' → Instal·la i inicia el node\n"
            "       (la sincronització inicial triga hores/dies, ~60 GB)\n\n"
            "2️⃣   Pestanya 'Mineria' → Posa la teva adreça Dogecoin\n"
            "       i prem 'COMENÇAR A MINAR'\n\n"
            "3️⃣   Pestanya 'Cartera' → Consulta el saldo i envia DOGE\n\n"
            "⚠️   La mineria CPU en solitari és honestament molt poc\n"
            "       probable de trobar blocs a la xarxa principal.\n"
            "       Cada hash és una loteria — però és 100% descentralitzat!\n\n"
            "🐕   Bona sort i Much WOW!"
        )

    def closeEvent(self, event):
        reply = QMessageBox.question(
            self, "Sortir",
            "Vols aturar el miner i el node en sortir?",
            QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
            QMessageBox.Yes
        )
        if reply == QMessageBox.Cancel:
            event.ignore()
            return

        if reply == QMessageBox.Yes:
            self.miner_manager.stop_mining()
            self.node_manager.stop_node()

        event.accept()

    # --- Mètodes per al seguiment del tema del sistema ---
    def _apply_system_theme(self):
        import platform
        system = platform.system()
        is_light = False
        try:
            if system == "Windows":
                import winreg
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                     r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize")
                value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
                is_light = (value == 1)
            elif system == "Darwin":
                import subprocess
                result = subprocess.run(
                    ["defaults", "read", "-g", "AppleInterfaceStyle"],
                    capture_output=True, text=True
                )
                is_light = (result.returncode != 0)  # si no troba clau, és clar
            else:  # Linux (assumim GNOME)
                import subprocess
                result = subprocess.run(
                    ["gsettings", "get", "org.gnome.desktop.interface", "gtk-theme"],
                    capture_output=True, text=True
                )
                theme = result.stdout.strip().strip("'")
                is_light = "light" in theme.lower()
        except Exception:
            pass

        theme_name = "Clar" if is_light else "Fosc"
        self._set_theme(theme_name)

    def _check_system_theme(self):
        if not self.follow_system_theme:
            return
        current = self.config.get("theme", "Fosc")
        self._apply_system_theme()
        new = self.config.get("theme", "Fosc")
        if current != new:
            self._apply_theme()  # Reaplica estil

    def _set_theme(self, theme_name):
        self.config.set("theme", theme_name)
        self._apply_theme()