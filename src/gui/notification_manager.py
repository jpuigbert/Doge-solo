from PySide6.QtWidgets import QSystemTrayIcon, QMenu
from PySide6.QtGui import QIcon, QAction
from PySide6.QtCore import QObject, Signal, Slot, Qt
import logging

logger = logging.getLogger("DogeSolo")


class NotificationManager(QObject):
    """Gestiona les notificacions d'escriptori i la icona a la safata."""

    show_notification_signal = Signal(str, str)  # títol, missatge

    def __init__(self, parent=None):
        super().__init__(parent)
        self.tray_icon = None
        self.parent = parent
        self._create_tray_icon()
        self.show_notification_signal.connect(self._show_notification)

    def _create_tray_icon(self):
        if not QSystemTrayIcon.isSystemTrayAvailable():
            logger.warning("Sistema de safata no disponible.")
            return

        self.tray_icon = QSystemTrayIcon(self.parent)
        # Carregar icona (intenta des de recursos, si no, crea una de color)
        icon = QIcon.fromTheme("dogesolo")
        if icon.isNull():
            from PySide6.QtGui import QPixmap
            pixmap = QPixmap(64, 64)
            pixmap.fill(Qt.darkYellow)
            icon = QIcon(pixmap)
        self.tray_icon.setIcon(icon)
        self.tray_icon.setToolTip("DogeSolo")

        menu = QMenu()
        show_action = QAction("Mostra finestra", self.parent)
        show_action.triggered.connect(self._show_window)
        menu.addAction(show_action)

        quit_action = QAction("Surt", self.parent)
        quit_action.triggered.connect(self._quit_app)
        menu.addAction(quit_action)

        self.tray_icon.setContextMenu(menu)
        self.tray_icon.show()

    def _show_window(self):
        if self.parent:
            self.parent.show()
            self.parent.raise_()
            self.parent.activateWindow()

    def _quit_app(self):
        if self.parent:
            self.parent.close()

    @Slot(str, str)
    def _show_notification(self, title, message):
        if self.tray_icon:
            self.tray_icon.showMessage(title, message, QSystemTrayIcon.Information, 5000)

    def notify(self, title, message):
        """Crida aquest mètode per emetre una notificació (thread-safe)."""
        self.show_notification_signal.emit(title, message)