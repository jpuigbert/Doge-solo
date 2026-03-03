from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                               QPushButton, QLabel, QLineEdit,
                               QGroupBox, QFormLayout, QComboBox,
                               QSpinBox, QCheckBox, QFileDialog,
                               QMessageBox)
from PySide6.QtCore import Slot

class SettingsTab(QWidget):
    def __init__(self, config):
        super().__init__()
        self.config = config

        self._setup_ui()
        self.load_settings()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # ===== CONFIGURACIÓ GENERAL =====
        general_group = QGroupBox("Configuració General")
        general_layout = QFormLayout()

        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Fosc", "Clar", "Sistema"])

        self.start_minimized = QCheckBox("Iniciar minimitzat")
        self.start_with_system = QCheckBox("Iniciar amb el sistema")

        general_layout.addRow("Tema:", self.theme_combo)
        general_layout.addRow("", self.start_minimized)
        general_layout.addRow("", self.start_with_system)

        general_group.setLayout(general_layout)
        layout.addWidget(general_group)

        # ===== CONFIGURACIÓ DEL NODE =====
        node_group = QGroupBox("Configuració del Node")
        node_layout = QFormLayout()

        self.data_dir_label = QLabel(str(self.config.get("data_dir", "~/.dogecoin")))
        self.change_dir_btn = QPushButton("Canvia")
        self.change_dir_btn.clicked.connect(self.change_data_dir)

        dir_layout = QHBoxLayout()
        dir_layout.addWidget(self.data_dir_label)
        dir_layout.addWidget(self.change_dir_btn)

        self.rpc_user = QLineEdit()
        self.rpc_password = QLineEdit()
        self.rpc_password.setEchoMode(QLineEdit.Password)

        node_layout.addRow("Directori dades:", dir_layout)
        node_layout.addRow("RPC Usuari:", self.rpc_user)
        node_layout.addRow("RPC Contrasenya:", self.rpc_password)

        node_group.setLayout(node_layout)
        layout.addWidget(node_group)

        # ===== CONFIGURACIÓ DEL MINER =====
        miner_group = QGroupBox("Configuració del Miner")
        miner_layout = QFormLayout()

        self.threads_spin = QSpinBox()
        self.threads_spin.setRange(1, 32)
        self.threads_spin.setValue(4)

        miner_layout.addRow("Nuclis CPU:", self.threads_spin)

        miner_group.setLayout(miner_layout)
        layout.addWidget(miner_group)

        # ===== OPCIONS AVANÇADES =====
        extra_group = QGroupBox("Opcions avançades")
        extra_layout = QFormLayout()

        self.follow_theme_check = QCheckBox("Segueix el tema del sistema")
        self.follow_theme_check.setToolTip("Canvia automàticament entre clar/fosc segons el sistema")
        extra_layout.addRow("", self.follow_theme_check)

        self.clean_logs_check = QCheckBox("Neteja logs automàticament (>30 dies)")
        self.clean_logs_check.setChecked(True)
        extra_layout.addRow("", self.clean_logs_check)

        self.auto_update_node_check = QCheckBox("Comprova actualitzacions del node automàticament")
        self.auto_update_node_check.setChecked(True)
        extra_layout.addRow("", self.auto_update_node_check)

        extra_group.setLayout(extra_layout)
        layout.addWidget(extra_group)

        # ===== BOTONS =====
        btn_layout = QHBoxLayout()

        self.save_btn = QPushButton("💾 Guardar Configuració")
        self.save_btn.clicked.connect(self.save_settings)

        self.reset_btn = QPushButton("↺ Restablir")
        self.reset_btn.clicked.connect(self.load_settings)

        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.reset_btn)
        layout.addLayout(btn_layout)

        layout.addStretch()

    @Slot()
    def change_data_dir(self):
        dir_path = QFileDialog.getExistingDirectory(
            self,
            "Selecciona directori per les dades del node",
            str(self.data_dir_label.text())
        )
        if dir_path:
            self.data_dir_label.setText(dir_path)

    @Slot()
    def save_settings(self):
        self.config.set("theme", self.theme_combo.currentText())
        self.config.set("start_minimized", self.start_minimized.isChecked())
        self.config.set("start_with_system", self.start_with_system.isChecked())
        self.config.set("data_dir", self.data_dir_label.text())
        self.config.set("rpc_user", self.rpc_user.text())
        self.config.set("rpc_password", self.rpc_password.text())
        self.config.set("cpu_threads", self.threads_spin.value())
        self.config.set("follow_system_theme", self.follow_theme_check.isChecked())
        self.config.set("clean_logs_auto", self.clean_logs_check.isChecked())
        self.config.set("auto_update_node", self.auto_update_node_check.isChecked())

        self.config.save()

        QMessageBox.information(self, "Configuració", "Configuració guardada correctament")

    @Slot()
    def load_settings(self):
        theme = self.config.get("theme", "Fosc")
        index = self.theme_combo.findText(theme)
        if index >= 0:
            self.theme_combo.setCurrentIndex(index)

        self.start_minimized.setChecked(self.config.get("start_minimized", False))
        self.start_with_system.setChecked(self.config.get("start_with_system", False))
        self.data_dir_label.setText(self.config.get("data_dir", "~/.dogecoin"))
        self.rpc_user.setText(self.config.get("rpc_user", "dogesolo_user"))
        self.rpc_password.setText(self.config.get("rpc_password", ""))
        self.threads_spin.setValue(self.config.get("cpu_threads", 4))
        self.follow_theme_check.setChecked(self.config.get("follow_system_theme", False))
        self.clean_logs_check.setChecked(self.config.get("clean_logs_auto", True))
        self.auto_update_node_check.setChecked(self.config.get("auto_update_node", True))