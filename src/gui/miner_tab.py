from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                               QPushButton, QLabel, QLineEdit,
                               QGroupBox, QFormLayout,
                               QPlainTextEdit, QMessageBox, QCheckBox,
                               QSpinBox, QTabWidget)
from PySide6.QtCore import Slot, Signal, QThread, QTimer, Qt, QEvent
from PySide6.QtGui import QFont, QDesktopServices
from PySide6.QtCore import QUrl
from datetime import datetime
import webbrowser

from src.gui.graph_widget import HashrateGraph
from src.core.miner_manager import format_hashrate


class MinerThread(QThread):
    output_signal = Signal(str)
    stats_signal = Signal(object)  # MiningStats

    def __init__(self, miner_manager, address, num_threads):
        super().__init__()
        self.miner_manager = miner_manager
        self.address = address
        self.num_threads = num_threads
        self._running = True

    def run(self):
        def output_callback(msg: str):
            self.output_signal.emit(msg)

        def stats_callback(stats):
            self.stats_signal.emit(stats)

        self.miner_manager.start_mining(
            self.address,
            num_threads=self.num_threads,
            output_callback=output_callback,
            stats_callback=stats_callback
        )

        while self._running and self.miner_manager.is_mining():
            self.msleep(200)


class MinerTab(QWidget):
    def __init__(self, node_manager, miner_manager, config):
        super().__init__()
        self.node_manager = node_manager
        self.miner_manager = miner_manager
        self.config = config
        self.miner_thread = None
        self.last_activity = datetime.now()
        self._setup_ui()
        self._setup_idle_timer()
        self.installEventFilter(self)

        saved_addr = self.config.get("mining_address", "")
        if saved_addr:
            self.address_input.setText(saved_addr)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # Estat del node
        status_group = QGroupBox("Estat del Node")
        status_layout = QFormLayout()
        self.status_label = QLabel("🟡 Comprovant...")
        self.blocks_label = QLabel("—")
        self.difficulty_label = QLabel("—")
        self.connections_label = QLabel("—")
        status_layout.addRow("Estat:", self.status_label)
        status_layout.addRow("Blocs:", self.blocks_label)
        status_layout.addRow("Connexions:", self.connections_label)
        status_layout.addRow("Dificultat xarxa:", self.difficulty_label)
        status_group.setLayout(status_layout)
        layout.addWidget(status_group)

        # Configuració mineria
        config_group = QGroupBox("Configuració de Mineria")
        config_layout = QFormLayout()
        self.address_input = QLineEdit()
        self.address_input.setPlaceholderText("D... (adreça Dogecoin receptora)")
        config_layout.addRow("Adreça Dogecoin:", self.address_input)

        self.threads_spin = QSpinBox()
        self.threads_spin.setRange(1, 32)
        self.threads_spin.setValue(self.config.get("cpu_threads", 4))
        config_layout.addRow("Fils de CPU:", self.threads_spin)

        self.save_address_check = QCheckBox("Desar aquesta adreça per a properes sessions")
        self.save_address_check.setChecked(True)
        config_layout.addRow("", self.save_address_check)

        self.download_btn = QPushButton("⬇️ Descarregar miner (cpuminer-opt)")
        self.download_btn.setObjectName("downloadButton")
        self.download_btn.clicked.connect(self._open_download_page)
        config_layout.addRow("", self.download_btn)

        config_group.setLayout(config_layout)
        layout.addWidget(config_group)

        # Botons inici/aturar
        btn_layout = QHBoxLayout()
        self.start_btn = QPushButton("🚀  COMENÇAR A MINAR")
        self.start_btn.setObjectName("startButton")
        self.start_btn.clicked.connect(self.start_mining)

        self.stop_btn = QPushButton("🛑  ATURAR")
        self.stop_btn.setObjectName("stopButton")
        self.stop_btn.clicked.connect(self.stop_mining)
        self.stop_btn.setEnabled(False)

        btn_layout.addWidget(self.start_btn)
        btn_layout.addWidget(self.stop_btn)
        layout.addLayout(btn_layout)

        # Pestanyes per a rendiment i gràfiques
        stats_tabs = QTabWidget()
        perf_tab = QWidget()
        perf_layout = QVBoxLayout(perf_tab)

        stats_group = QGroupBox("Estadístiques de mineria")
        stats_form = QFormLayout()
        self.hashrate_label = QLabel("0 H/s")
        self.shares_label = QLabel("0")
        self.blocks_found_label = QLabel("0")
        self.hashes_total_label = QLabel("0")
        self.runtime_label = QLabel("00:00:00")
        stats_form.addRow("Hashrate actual:", self.hashrate_label)
        stats_form.addRow("Total hashes:", self.hashes_total_label)
        stats_form.addRow("Shares trobats:", self.shares_label)
        stats_form.addRow("Blocs trobats:", self.blocks_found_label)
        stats_form.addRow("Temps actiu:", self.runtime_label)
        stats_group.setLayout(stats_form)
        perf_layout.addWidget(stats_group)

        idle_group = QGroupBox("Inactivitat de l'ordinador")
        idle_layout = QVBoxLayout()
        self.idle_label = QLabel("⏱️ 00:00:00")
        self.idle_label.setAlignment(Qt.AlignCenter)
        idle_font = QFont()
        idle_font.setPointSize(14)
        idle_font.setBold(True)
        self.idle_label.setFont(idle_font)
        self.idle_status = QLabel("(esperant activitat)")
        self.idle_status.setAlignment(Qt.AlignCenter)
        idle_layout.addWidget(self.idle_label)
        idle_layout.addWidget(self.idle_status)
        idle_group.setLayout(idle_layout)
        perf_layout.addWidget(idle_group)

        stats_tabs.addTab(perf_tab, "📊 Rendiment")

        graph_tab = QWidget()
        graph_layout = QVBoxLayout(graph_tab)
        self.graph = HashrateGraph()
        graph_layout.addWidget(self.graph)
        stats_tabs.addTab(graph_tab, "📈 Gràfica")

        layout.addWidget(stats_tabs)

        # Logs
        log_group = QGroupBox("Registre de Mineria")
        log_layout = QVBoxLayout()
        self.log_text = QPlainTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Courier New", 9))
        self.log_text.setMaximumBlockCount(500)
        log_layout.addWidget(self.log_text)
        log_group.setLayout(log_layout)
        layout.addWidget(log_group)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_status)
        self.timer.start(3000)

        self.stats_timer = QTimer()
        self.stats_timer.timeout.connect(self._update_stats_display)
        self.stats_timer.start(1000)

    def _setup_idle_timer(self):
        self.idle_timer = QTimer()
        self.idle_timer.timeout.connect(self._update_idle_time)
        self.idle_timer.start(1000)

    def eventFilter(self, obj, event):
        if event.type() in (QEvent.MouseMove, QEvent.MouseButtonPress,
                            QEvent.KeyPress, QEvent.Wheel):
            self.last_activity = datetime.now()
        return super().eventFilter(obj, event)

    def _update_idle_time(self):
        if self.miner_manager.is_mining():
            delta = datetime.now() - self.last_activity
            seconds = int(delta.total_seconds())
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            secs = seconds % 60
            self.idle_label.setText(f"⏱️ {hours:02d}:{minutes:02d}:{secs:02d}")
            if seconds < 60:
                self.idle_status.setText("(actiu)")
            else:
                self.idle_status.setText("(inactiu - miner en segon pla)")
        else:
            self.idle_label.setText("⏱️ 00:00:00")
            self.idle_status.setText("(miner aturat)")

    def _update_stats_display(self):
        if self.miner_manager.is_mining():
            stats = self.miner_manager.get_stats()
            self.hashrate_label.setText(format_hashrate(stats.last_hashrate))
            self.shares_label.setText(str(stats.shares_found))
            self.blocks_found_label.setText(str(stats.blocks_found))
            self.hashes_total_label.setText(f"{stats.hashes_total:,}")
            if stats.start_time:
                delta = datetime.now() - stats.start_time
                hours = delta.seconds // 3600
                minutes = (delta.seconds % 3600) // 60
                secs = delta.seconds % 60
                self.runtime_label.setText(f"{hours:02d}:{minutes:02d}:{secs:02d}")
            self.graph.add_hashrate(stats.last_hashrate)

    @Slot()
    def _open_download_page(self):
        url = QUrl("https://github.com/JayDDee/cpuminer-opt/releases")
        if not QDesktopServices.openUrl(url):
            try:
                webbrowser.open(url.toString())
            except Exception as e:
                QMessageBox.warning(
                    self,
                    "Error",
                    f"No s'ha pogut obrir el navegador.\n{str(e)}\n\n"
                    "Pots descarregar manualment des de:\n"
                    "https://github.com/JayDDee/cpuminer-opt/releases"
                )

    @Slot()
    def update_status(self):
        if self.node_manager.is_running():
            self.status_label.setText("🟢 Actiu")
            blocks = self.node_manager.get_block_count()
            if blocks:
                self.blocks_label.setText(f"{blocks:,}")
            info = self.node_manager.get_mining_info()
            if info:
                diff = info.get("difficulty", 0)
                self.difficulty_label.setText(f"{diff:,.0f}")
            net_info = self.node_manager.get_network_info()
            if net_info:
                self.connections_label.setText(str(net_info.get("connections", 0)))
        else:
            self.status_label.setText("🔴 Aturat")
            self.blocks_label.setText("Node no disponible")

    @Slot()
    def start_mining(self):
        address = self.address_input.text().strip()
        if not address:
            QMessageBox.warning(self, "Adreça requerida",
                                "Has de posar una adreça Dogecoin vàlida.")
            return
        if not address.startswith("D") or len(address) < 26:
            QMessageBox.warning(self, "Adreça invàlida",
                                "L'adreça Dogecoin ha de començar per 'D'.")
            return
        if not self.node_manager.is_running():
            QMessageBox.warning(self, "Node aturat",
                                "El node Dogecoin no està en marxa.\n"
                                "Ves a la pestanya 'Node' i inicia'l primer.")
            return

        if self.save_address_check.isChecked():
            self.config.set("mining_address", address)

        num_threads = self.threads_spin.value()
        self.config.set("cpu_threads", num_threads)

        self.miner_thread = MinerThread(self.miner_manager, address, num_threads)
        self.miner_thread.output_signal.connect(self.add_log)
        self.miner_thread.stats_signal.connect(self._on_stats_update)
        self.miner_thread.start()

        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.add_log(f"🚀 Mineria iniciada amb {num_threads} fils!")

    def _on_stats_update(self, stats):
        pass  # ja es fa amb el timer

    @Slot()
    def stop_mining(self):
        self.miner_manager.stop_mining()
        if self.miner_thread:
            self.miner_thread._running = False
            self.miner_thread.wait(3000)
            self.miner_thread = None

        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.add_log("🛑 Mineria aturada")

    @Slot(str)
    def add_log(self, text: str):
        ts = datetime.now().strftime("%H:%M:%S")
        self.log_text.appendPlainText(f"[{ts}] {text}")