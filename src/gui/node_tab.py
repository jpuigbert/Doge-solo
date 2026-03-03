#!/usr/bin/env python3
"""Pestanya de control del node Dogecoin Core."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QProgressBar, QGroupBox, QFormLayout, QPlainTextEdit, QMessageBox,
    QFrame
)
from PySide6.QtCore import Slot, QTimer, Qt, QThread, Signal
from datetime import datetime
import time
import logging

logger = logging.getLogger("DogeSolo")


class InstallThread(QThread):
    log_signal = Signal(str)
    finished_signal = Signal(bool)

    def __init__(self, node_manager):
        super().__init__()
        self.node_manager = node_manager

    def run(self):
        success = self.node_manager.install_node(callback=self.log_signal.emit)
        self.finished_signal.emit(success)


class NodeTab(QWidget):
    def __init__(self, node_manager):
        super().__init__()
        self.node_manager = node_manager
        self._install_thread = None
        self.last_blocks = 0
        self.last_time = time.time()
        self._setup_ui()
        self._setup_timers()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        # Controls
        control_group = QGroupBox("Control del Node Dogecoin Core")
        control_layout = QHBoxLayout()
        control_layout.setSpacing(10)

        self.install_btn = QPushButton("📥  Instal·lar node")
        self.install_btn.setObjectName("installButton")
        self.install_btn.clicked.connect(self._install_node)
        self.install_btn.setMinimumHeight(42)

        self.start_btn = QPushButton("▶  Iniciar node")
        self.start_btn.setObjectName("startButton")
        self.start_btn.clicked.connect(self._start_node)
        self.start_btn.setMinimumHeight(42)

        self.stop_btn = QPushButton("⏹  Aturar node")
        self.stop_btn.setObjectName("stopButton")
        self.stop_btn.clicked.connect(self._stop_node)
        self.stop_btn.setEnabled(False)
        self.stop_btn.setMinimumHeight(42)

        control_layout.addWidget(self.install_btn)
        control_layout.addWidget(self.start_btn)
        control_layout.addWidget(self.stop_btn)
        control_group.setLayout(control_layout)
        layout.addWidget(control_group)

        # Sincronització
        sync_group = QGroupBox("Sincronització de la Blockchain")
        sync_layout = QVBoxLayout()

        self.sync_progress = QProgressBar()
        self.sync_progress.setMinimumHeight(22)
        self.sync_progress.setFormat("%p% — %v / %m blocs")

        self.sync_label = QLabel("Esperant connexió al node...")
        self.sync_label.setAlignment(Qt.AlignCenter)
        self.sync_label.setObjectName("syncLabel")

        sync_layout.addWidget(self.sync_progress)
        sync_layout.addWidget(self.sync_label)
        sync_group.setLayout(sync_layout)
        layout.addWidget(sync_group)

        # Informació
        info_group = QGroupBox("Informació del Node")
        info_layout = QFormLayout()
        info_layout.setSpacing(8)

        self.version_lbl = QLabel("—")
        self.connections_lbl = QLabel("—")
        self.blocks_lbl = QLabel("—")
        self.headers_lbl = QLabel("—")
        self.difficulty_lbl = QLabel("—")
        self.hashrate_net_lbl = QLabel("—")
        self.chain_lbl = QLabel("—")

        info_layout.addRow("Versió:", self.version_lbl)
        info_layout.addRow("Xarxa:", self.chain_lbl)
        info_layout.addRow("Connexions:", self.connections_lbl)
        info_layout.addRow("Blocs sincronitzats:", self.blocks_lbl)
        info_layout.addRow("Capçaleres:", self.headers_lbl)
        info_layout.addRow("Dificultat:", self.difficulty_lbl)
        info_layout.addRow("Hashrate xarxa:", self.hashrate_net_lbl)

        info_group.setLayout(info_layout)
        layout.addWidget(info_group)

        # Log
        log_group = QGroupBox("Registre del Node")
        log_layout = QVBoxLayout()

        self.node_log = QPlainTextEdit()
        self.node_log.setReadOnly(True)
        self.node_log.setMaximumBlockCount(300)
        self.node_log.setMinimumHeight(140)

        log_layout.addWidget(self.node_log)
        log_group.setLayout(log_layout)
        layout.addWidget(log_group)

    def _setup_timers(self):
        self.timer = QTimer()
        self.timer.timeout.connect(self._update_info)
        self.timer.start(4000)

    # Slots
    @Slot()
    def _install_node(self):
        if self.node_manager.is_installed():
            QMessageBox.information(self, "Ja instal·lat",
                "El node Dogecoin Core ja està instal·lat.")
            return

        reply = QMessageBox.question(
            self, "Instal·lar Dogecoin Core",
            "Es descarregarà Dogecoin Core (~50 MB).\n"
            "Necessitaràs ~60 GB d'espai lliure per sincronitzar.\n\n"
            "Continues?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes
        )
        if reply != QMessageBox.Yes:
            return

        self.install_btn.setEnabled(False)
        self.install_btn.setText("📥  Instal·lant...")
        self._log("📥 Iniciant descàrrega de Dogecoin Core...")

        self._install_thread = InstallThread(self.node_manager)
        self._install_thread.log_signal.connect(self._log)
        self._install_thread.finished_signal.connect(self._on_install_finished)
        self._install_thread.start()

    @Slot(bool)
    def _on_install_finished(self, success: bool):
        self.install_btn.setEnabled(True)
        self.install_btn.setText("📥  Instal·lar node")
        if success:
            self._log("✅ Instal·lació completada!")
            QMessageBox.information(self, "Instal·lació completada",
                "Dogecoin Core instal·lat!\nAra pots iniciar el node.")
        else:
            self._log("❌ Error en la instal·lació. Comprova la connexió a Internet.")
            QMessageBox.critical(self, "Error",
                "No s'ha pogut instal·lar. Comprova la connexió.")

    @Slot()
    def _start_node(self):
        if not self.node_manager.is_installed():
            reply = QMessageBox.question(
                self, "Node no instal·lat",
                "El node no està instal·lat. Vols instal·lar-lo ara?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self._install_node()
            return

        self.start_btn.setEnabled(False)
        self.start_btn.setText("▶  Iniciant...")
        self._log("▶ Iniciant node Dogecoin Core...")

        from PySide6.QtCore import QThread
        class StartThread(QThread):
            done = Signal(bool)
            def __init__(self, nm):
                super().__init__()
                self.nm = nm
            def run(self):
                self.done.emit(self.nm.start_node())

        self._start_thread = StartThread(self.node_manager)
        self._start_thread.done.connect(self._on_start_done)
        self._start_thread.start()

    @Slot(bool)
    def _on_start_done(self, success: bool):
        if success:
            self.start_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            self.start_btn.setText("▶  En marxa")
            self._log("✅ Node iniciat correctament!")
        else:
            self.start_btn.setEnabled(True)
            self.start_btn.setText("▶  Iniciar node")
            self._log("❌ No s'ha pogut iniciar el node.")
            QMessageBox.critical(self, "Error", "No s'ha pogut iniciar el node Dogecoin Core.")

    @Slot()
    def _stop_node(self):
        self._log("⏹ Aturant node...")
        self.node_manager.stop_node()
        self.start_btn.setEnabled(True)
        self.start_btn.setText("▶  Iniciar node")
        self.stop_btn.setEnabled(False)
        self._log("🛑 Node aturat.")

    @Slot()
    def _update_info(self):
        if not self.node_manager.is_running():
            self.sync_label.setText("Node aturat")
            return

        # Blockchain info
        chain_info = self.node_manager.get_blockchain_info()
        if chain_info:
            blocks = chain_info.get("blocks", 0)
            headers = chain_info.get("headers", 0)
            chain = chain_info.get("chain", "main")

            self.blocks_lbl.setText(f"{blocks:,}")
            self.headers_lbl.setText(f"{headers:,}")
            self.chain_lbl.setText("Mainnet 🌐" if chain == "main" else f"⚠️ {chain.upper()}")

            if headers > 0:
                pct = min(100, int(blocks * 100 / headers))
                remaining = headers - blocks
                self.sync_progress.setMaximum(headers)
                self.sync_progress.setValue(blocks)

                # Temps restant estimat
                now = time.time()
                time_str = ""
                if remaining > 0 and self.last_blocks > 0 and blocks > self.last_blocks:
                    elapsed = now - self.last_time
                    blocks_per_sec = (blocks - self.last_blocks) / elapsed
                    if blocks_per_sec > 0:
                        seconds_remaining = remaining / blocks_per_sec
                        if seconds_remaining < 60:
                            time_str = f", {seconds_remaining:.0f} segons restants"
                        elif seconds_remaining < 3600:
                            time_str = f", {seconds_remaining/60:.1f} minuts restants"
                        else:
                            time_str = f", {seconds_remaining/3600:.1f} hores restants"
                self.sync_label.setText(
                    f"Sincronitzant: {pct}%  ({blocks:,} / {headers:,}){time_str}"
                )
                self.last_blocks = blocks
                self.last_time = now

            diff = chain_info.get("difficulty", 0)
            self.difficulty_lbl.setText(f"{diff:,.0f}")

        # Network info
        net_info = self.node_manager.get_network_info()
        if net_info:
            ver = net_info.get("subversion", "—").strip("/")
            self.version_lbl.setText(ver)
            conns = net_info.get("connections", 0)
            conn_txt = f"{conns}"
            if conns == 0:
                conn_txt = "0 ⚠️  (sense connexions)"
            self.connections_lbl.setText(conn_txt)

        # Mining info (hashrate xarxa)
        mining_info = self.node_manager.get_mining_info()
        if mining_info:
            net_hs = mining_info.get("networkhashps", 0)
            from src.core.miner_manager import format_hashrate
            self.hashrate_net_lbl.setText(f"{format_hashrate(net_hs)} (xarxa global)")

        # Actualitzar botons
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)

    def _log(self, text: str):
        ts = datetime.now().strftime("%H:%M:%S")
        self.node_log.appendPlainText(f"[{ts}] {text}")

    def show_installation_prompt(self):
        self._log("⚠️  El node Dogecoin Core no està instal·lat.")
        self._log("→ Prem 'Instal·lar node' per descarregar-lo automàticament.")