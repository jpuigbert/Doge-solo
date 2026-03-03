#!/usr/bin/env python3
"""
Pestanya de cartera: saldo, enviament de DOGE i historial de transaccions.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QLineEdit, QGroupBox, QFormLayout, QDoubleSpinBox,
    QMessageBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QDialog, QDialogButtonBox, QCheckBox, QFileDialog,
    QFrame, QSizePolicy
)
from PySide6.QtCore import Slot, QTimer, Qt, Signal
from PySide6.QtGui import QFont, QColor, QClipboard, QGuiApplication
from datetime import datetime
import logging

logger = logging.getLogger("DogeSolo")


class AmountWidget(QWidget):
    """Widget per introduir quantitat amb botó 'Tot'."""
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        self.spin = QDoubleSpinBox()
        self.spin.setDecimals(4)
        self.spin.setRange(0.0001, 999_999_999)
        self.spin.setSuffix("  DOGE")
        # Fem que l'spinbox s'expandeixi horitzontalment
        self.spin.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.spin.setMinimumWidth(250)

        self.max_btn = QPushButton("Tot")
        self.max_btn.setMaximumWidth(45)
        self.max_btn.setToolTip("Envia tot el saldo disponible (descomptant comissió)")
        self.max_btn.setObjectName("maxButton")

        layout.addWidget(self.spin)
        layout.addWidget(self.max_btn)

    def value(self) -> float:
        return self.spin.value()

    def setValue(self, v: float):
        self.spin.setValue(v)


class WalletTab(QWidget):
    def __init__(self, node_manager, wallet_manager):
        super().__init__()
        self.node_manager = node_manager
        self.wallet_manager = wallet_manager
        self._balance = 0.0
        self._setup_ui()
        self._setup_timers()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(12)
        main_layout.setContentsMargins(16, 16, 16, 16)

        # ── Capçalera saldo (amb estil) ──────────────────────────────
        balance_frame = QFrame()
        balance_frame.setObjectName("balanceFrame")
        balance_frame.setStyleSheet("""
            QFrame#balanceFrame {
                background-color: #2d2d2d;
                border-radius: 10px;
                padding: 15px;
                border: 1px solid #444;
            }
            QLabel#balanceTitle {
                color: #f0b90b;
                font-size: 14px;
                font-weight: bold;
                letter-spacing: 1px;
            }
            QLabel#balanceAmount {
                color: white;
                font-size: 28px;
                font-weight: bold;
            }
            QLabel#unconfirmedLabel {
                color: #ffaa33;
                font-size: 12px;
                font-style: italic;
            }
        """)
        balance_layout = QVBoxLayout(balance_frame)
        balance_layout.setAlignment(Qt.AlignCenter)

        balance_title = QLabel("SALDO DISPONIBLE")
        balance_title.setAlignment(Qt.AlignCenter)
        balance_title.setObjectName("balanceTitle")

        self.balance_label = QLabel("── DOGE")
        self.balance_label.setAlignment(Qt.AlignCenter)
        self.balance_label.setObjectName("balanceAmount")

        self.unconfirmed_label = QLabel("")
        self.unconfirmed_label.setAlignment(Qt.AlignCenter)
        self.unconfirmed_label.setObjectName("unconfirmedLabel")

        balance_layout.addWidget(balance_title)
        balance_layout.addWidget(self.balance_label)
        balance_layout.addWidget(self.unconfirmed_label)
        main_layout.addWidget(balance_frame)

        # ── Adreça receptora ──────────────────────────────────────────
        receive_group = QGroupBox("La teva adreça receptora")
        receive_layout = QHBoxLayout()

        self.my_address_label = QLineEdit()
        self.my_address_label.setReadOnly(True)
        self.my_address_label.setPlaceholderText("Esperant connexió al node...")
        self.my_address_label.setObjectName("addressDisplay")
        # Fem que sigui més ample
        self.my_address_label.setMinimumWidth(400)
        self.my_address_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.my_address_label.setStyleSheet("""
            QLineEdit {
                background-color: #3c3c3c;
                border: 1px solid #555;
                border-radius: 5px;
                padding: 8px;
                font-family: 'Courier New';
                font-size: 12px;
                color: #ffd700;
            }
        """)

        copy_btn = QPushButton("📋 Copiar")
        copy_btn.setMaximumWidth(90)
        copy_btn.setStyleSheet("""
            QPushButton {
                background-color: #4a4a4a;
                border: none;
                border-radius: 5px;
                padding: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #5a5a5a;
            }
        """)
        copy_btn.clicked.connect(self._copy_address)

        receive_layout.addWidget(self.my_address_label)
        receive_layout.addWidget(copy_btn)
        receive_group.setLayout(receive_layout)
        main_layout.addWidget(receive_group)

        # ── Enviament ─────────────────────────────────────────────────
        send_group = QGroupBox("Enviar DOGE")
        send_form = QFormLayout()
        send_form.setSpacing(10)
        send_form.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)  # Els camps s'expandeixen

        self.dest_address = QLineEdit()
        self.dest_address.setPlaceholderText("D... adreça Dogecoin destí")
        self.dest_address.setMinimumWidth(300)
        self.dest_address.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.dest_address.setStyleSheet("padding: 6px;")

        self.amount_widget = AmountWidget()
        self.amount_widget.max_btn.clicked.connect(self._set_max_amount)

        self.subtract_fee_check = QCheckBox("Descomptar comissió del total enviat")
        self.subtract_fee_check.setToolTip(
            "Si activat, el destinatari rebrà lleugerament menys "
            "(la comissió es treu de l'import enviat)"
        )

        self.comment_input = QLineEdit()
        self.comment_input.setPlaceholderText("Opcional: nota per a tu")
        self.comment_input.setMaxLength(80)
        self.comment_input.setMinimumWidth(300)
        self.comment_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.fee_label = QLabel("Comissió estimada: ~1.00 DOGE")
        self.fee_label.setObjectName("feeLabel")
        self.fee_label.setStyleSheet("color: #f0b90b; font-size: 11px;")

        send_form.addRow("Adreça destí:", self.dest_address)
        send_form.addRow("Quantitat:", self.amount_widget)
        send_form.addRow("", self.subtract_fee_check)
        send_form.addRow("Comentari:", self.comment_input)
        send_form.addRow("", self.fee_label)

        send_btn_layout = QHBoxLayout()
        self.send_btn = QPushButton("🚀  ENVIAR DOGE")
        self.send_btn.setObjectName("sendButton")
        self.send_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                font-weight: bold;
                font-size: 14px;
                padding: 10px 20px;
                border-radius: 8px;
                min-width: 200px;
            }
            QPushButton:hover {
                background-color: #2ecc71;
            }
            QPushButton:disabled {
                background-color: #7f8c8d;
            }
        """)
        self.send_btn.clicked.connect(self._send_doge)
        self.send_btn.setMinimumHeight(44)
        send_btn_layout.addStretch()
        send_btn_layout.addWidget(self.send_btn)
        send_btn_layout.addStretch()

        send_group_layout = QVBoxLayout()
        send_group_layout.addLayout(send_form)
        send_group_layout.addLayout(send_btn_layout)
        send_group.setLayout(send_group_layout)
        main_layout.addWidget(send_group)

        # ── Historial ─────────────────────────────────────────────────
        hist_group = QGroupBox("Historial de transaccions")
        hist_layout = QVBoxLayout()

        self.tx_table = QTableWidget(0, 5)
        self.tx_table.setHorizontalHeaderLabels(
            ["Data", "Tipus", "Quantitat (DOGE)", "Confirmacions", "TXID"]
        )
        self.tx_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tx_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.tx_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tx_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.tx_table.setAlternatingRowColors(True)
        self.tx_table.verticalHeader().setVisible(False)
        self.tx_table.setMinimumHeight(180)
        self.tx_table.setStyleSheet("""
            QTableWidget {
                gridline-color: #444;
                selection-background-color: #3a3a3a;
                alternate-background-color: #2a2a2a;
            }
            QTableWidget::item {
                padding: 5px;
            }
            QTableWidget::item:selected {
                background-color: #4a6fa5;
                color: white;
            }
            QHeaderView::section {
                background-color: #353535;
                padding: 6px;
                border: 1px solid #555;
                font-weight: bold;
            }
        """)

        refresh_layout = QHBoxLayout()
        refresh_btn = QPushButton("🔄 Actualitzar")
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #4a4a4a;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background-color: #5a5a5a;
            }
        """)
        refresh_btn.clicked.connect(self._refresh_transactions)

        backup_btn = QPushButton("💾 Backup cartera")
        backup_btn.setStyleSheet("""
            QPushButton {
                background-color: #e67e22;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #d35400;
            }
        """)
        backup_btn.clicked.connect(self._backup_wallet)

        refresh_layout.addWidget(refresh_btn)
        refresh_layout.addStretch()
        refresh_layout.addWidget(backup_btn)

        hist_layout.addWidget(self.tx_table)
        hist_layout.addLayout(refresh_layout)
        hist_group.setLayout(hist_layout)
        main_layout.addWidget(hist_group)

    def _setup_timers(self):
        self.timer = QTimer()
        self.timer.timeout.connect(self._refresh_all)
        self.timer.start(10000)
        QTimer.singleShot(1500, self._refresh_all)

    # ── Slots ─────────────────────────────────────────────────────────
    @Slot()
    def _refresh_all(self):
        if not self.node_manager.is_running():
            self.balance_label.setText("Node aturat")
            return
        self._refresh_balance()
        self._refresh_address()
        self._refresh_transactions()

    def _refresh_balance(self):
        balance = self.wallet_manager.get_balance()
        if balance is not None:
            self._balance = balance
            self.balance_label.setText(f"{balance:,.4f} DOGE")
        else:
            self.balance_label.setText("── DOGE")

        unconf = self.wallet_manager.get_unconfirmed_balance()
        if unconf and unconf > 0:
            self.unconfirmed_label.setText(f"(+{unconf:.4f} DOGE pendent de confirmar)")
        else:
            self.unconfirmed_label.setText("")

    def _refresh_address(self):
        if self.my_address_label.text() in ("", "Esperant connexió al node..."):
            addr = self.wallet_manager.get_receiving_address()
            if addr:
                self.my_address_label.setText(addr)

    def _refresh_transactions(self):
        txs = self.wallet_manager.list_transactions(50)
        if not txs:
            return

        self.tx_table.setRowCount(0)
        for tx in reversed(txs):
            row = self.tx_table.rowCount()
            self.tx_table.insertRow(row)

            # Data
            ts = tx.get("time", 0)
            date_str = datetime.fromtimestamp(ts).strftime("%d/%m/%Y %H:%M") if ts else "—"
            self.tx_table.setItem(row, 0, QTableWidgetItem(date_str))

            # Tipus
            category = tx.get("category", "")
            type_map = {
                "receive": "📥 Rebut",
                "generate": "⛏️  Mineria",
                "send": "📤 Enviat",
                "immature": "🔒 Immadur",
            }
            type_item = QTableWidgetItem(type_map.get(category, category))
            self.tx_table.setItem(row, 1, type_item)

            # Quantitat
            amount = float(tx.get("amount", 0))
            amount_item = QTableWidgetItem(f"{amount:+.4f}")
            amount_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            if amount > 0:
                amount_item.setForeground(QColor("#27ae60"))
            elif amount < 0:
                amount_item.setForeground(QColor("#e74c3c"))
            self.tx_table.setItem(row, 2, amount_item)

            # Confirmacions
            confs = tx.get("confirmations", 0)
            conf_item = QTableWidgetItem(str(confs))
            conf_item.setTextAlignment(Qt.AlignCenter)
            if confs < 6:
                conf_item.setForeground(QColor("#f39c12"))
            self.tx_table.setItem(row, 3, conf_item)

            # TXID (truncat)
            txid = tx.get("txid", "")
            txid_short = txid[:16] + "..." if txid else "—"
            txid_item = QTableWidgetItem(txid_short)
            txid_item.setToolTip(txid)
            self.tx_table.setItem(row, 4, txid_item)

    @Slot()
    def _copy_address(self):
        addr = self.my_address_label.text()
        if addr and addr != "Esperant connexió al node...":
            QGuiApplication.clipboard().setText(addr)
            QMessageBox.information(self, "Copiat", "Adreça copiada al porta-retalls!")

    @Slot()
    def _set_max_amount(self):
        balance = self.wallet_manager.get_balance() or 0.0
        fee = self.wallet_manager.estimate_fee()
        max_amount = max(0.0, balance - fee - 0.001)
        self.amount_widget.setValue(round(max_amount, 4))
        self.subtract_fee_check.setChecked(True)

    @Slot()
    def _send_doge(self):
        if not self.node_manager.is_running():
            QMessageBox.critical(self, "Node aturat",
                "El node no és accessible. Inicia'l primer a la pestanya 'Node'.")
            return

        dest = self.dest_address.text().strip()
        amount = self.amount_widget.value()
        comment = self.comment_input.text().strip()
        subtract = self.subtract_fee_check.isChecked()

        if not dest:
            QMessageBox.warning(self, "Camp buit", "Has d'introduir una adreça destí.")
            self.dest_address.setFocus()
            return

        if not self.wallet_manager.validate_address(dest):
            QMessageBox.warning(self, "Adreça invàlida",
                "L'adreça Dogecoin no és vàlida.\nHa de començar per 'D' i tenir 26-34 caràcters.")
            return

        if amount < 0.0001:
            QMessageBox.warning(self, "Quantitat massa petita",
                "La quantitat mínima és 0.0001 DOGE.")
            return

        fee_est = self.wallet_manager.estimate_fee()
        confirm_msg = (
            f"Confirma l'enviament:\n\n"
            f"  Destí:    {dest}\n"
            f"  Quantitat: {amount:.4f} DOGE\n"
            f"  Comissió:  ~{fee_est:.2f} DOGE\n"
        )
        if subtract:
            confirm_msg += f"  (la comissió es descompta del total)\n"
        confirm_msg += f"\nEls enviaments en blockchain són IRREVERSIBLES."

        reply = QMessageBox.question(
            self, "Confirma l'enviament", confirm_msg,
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return

        if self.wallet_manager.is_wallet_locked():
            passphrase, ok = self._ask_passphrase()
            if not ok or not passphrase:
                return
            if not self.wallet_manager.unlock_wallet(passphrase, 120):
                QMessageBox.critical(self, "Error", "Contrasenya incorrecta.")
                return

        self.send_btn.setEnabled(False)
        self.send_btn.setText("Enviant...")

        try:
            txid = self.wallet_manager.send_doge(dest, amount, comment, subtract)
            if txid:
                QMessageBox.information(
                    self, "✅ Enviament completat!",
                    f"DOGE enviat correctament!\n\nTXID:\n{txid}\n\n"
                    f"Pots verificar-ho a:\nhttps://dogechain.info/tx/{txid}"
                )
                self.dest_address.clear()
                self.amount_widget.setValue(0.0)
                self.comment_input.clear()
                QTimer.singleShot(2000, self._refresh_all)
        except (ValueError, RuntimeError) as e:
            QMessageBox.critical(self, "Error en l'enviament", str(e))
        finally:
            self.send_btn.setEnabled(True)
            self.send_btn.setText("🚀  ENVIAR DOGE")
            if self.wallet_manager.is_wallet_locked() is False:
                self.wallet_manager.lock_wallet()

    def _ask_passphrase(self) -> tuple:
        dialog = QDialog(self)
        dialog.setWindowTitle("Desbloqueja la cartera")
        dialog.setMinimumWidth(350)
        layout = QVBoxLayout(dialog)
        layout.addWidget(QLabel("La cartera està xifrada.\nIntrodueix la contrasenya:"))
        pwd_input = QLineEdit()
        pwd_input.setEchoMode(QLineEdit.Password)
        pwd_input.setPlaceholderText("Contrasenya...")
        layout.addWidget(pwd_input)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        ok = dialog.exec() == QDialog.Accepted
        return pwd_input.text(), ok

    @Slot()
    def _backup_wallet(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Backup de la cartera",
            f"wallet_backup_{datetime.now().strftime('%Y%m%d_%H%M')}.dat",
            "Wallet files (*.dat)"
        )
        if path:
            if self.wallet_manager.backup_wallet(path):
                QMessageBox.information(self, "Backup completat",
                    f"Cartera guardada a:\n{path}\n\n⚠️ Guarda aquest fitxer en un lloc segur!")
            else:
                QMessageBox.critical(self, "Error", "No s'ha pogut fer el backup.")