"""
ui/tray_icon.py
------------------
Sistem tepsisi (system tray) ikonu. Uygulama arka planda calisirken
kullaniciya durum gosterir (hazir / modeller yukleniyor) ve basit
bir menu sunar (kisayolu goster, cikis).
"""

import os

from PyQt6.QtCore import pyqtSignal, QObject, Qt
from PyQt6.QtGui import QIcon, QAction, QPixmap, QPainter, QColor, QFont
from PyQt6.QtWidgets import QSystemTrayIcon, QMenu

from config import CONFIG, BASE_DIR
from utils.logger import get_logger

logger = get_logger("tray_icon")

ICON_PATH = os.path.join(BASE_DIR, "assets", "tray_icon.png")
ICON_LOADING_PATH = os.path.join(BASE_DIR, "assets", "tray_icon_loading.png")


def _build_fallback_icon(background_color: str) -> QIcon:
    """
    assets/ klasorunde ozel bir ikon dosyasi yoksa, boyle bos/gorunmez bir
    tray ikonu kalmasin diye kod icinde basit bir ikon cizer ("T" harfli
    renkli bir daire). Kendi tray_icon.png / tray_icon_loading.png
    dosyalarini assets/ klasorune koyarsan, kod otomatik onlari kullanir.
    """
    size = 64
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setBrush(QColor(background_color))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawEllipse(2, 2, size - 4, size - 4)

    painter.setPen(QColor("#ffffff"))
    font = QFont("Arial", 30, QFont.Weight.Bold)
    painter.setFont(font)
    painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "T")
    painter.end()

    return QIcon(pixmap)


class TrayIcon(QObject):
    quit_requested = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._tray = QSystemTrayIcon()
        self._setup_icon()
        self._setup_menu()

    def _setup_icon(self) -> None:
        if os.path.exists(ICON_PATH):
            self._tray.setIcon(QIcon(ICON_PATH))
        else:
            # Ozel ikon dosyasi yoksa, kod icinde basit bir ikon cizip
            # kullaniyoruz -- boylece tray'de hicbir zaman bos/gorunmez
            # bir ikon kalmiyor.
            logger.info(
                "Tray ikonu dosyasi bulunamadi (%s), yerlesik ikon kullaniliyor.",
                ICON_PATH,
            )
            self._tray.setIcon(_build_fallback_icon("#0078d4"))
        self._tray.setToolTip("Screen Translator")

    def _setup_menu(self) -> None:
        # NOT: menu ve action nesneleri self._menu / self._quit_action gibi
        # kalici ozniteliklerde tutulmali. QSystemTrayIcon.setContextMenu()
        # sahiplik almiyor -- eger 'menu' sadece bu fonksiyonun yerel
        # degiskeni olarak kalsaydi, Python cop toplayicisi onu fonksiyon
        # bitince silebilir ve tepsi menusu rastgele calismaz hale gelirdi.
        self._menu = QMenu()

        self._hotkey_info_action = QAction(f"Kisayol: {CONFIG['hotkey']}")
        self._hotkey_info_action.setEnabled(False)
        self._menu.addAction(self._hotkey_info_action)

        self._menu.addSeparator()

        self._quit_action = QAction("Cikis")
        self._quit_action.triggered.connect(self.quit_requested.emit)
        self._menu.addAction(self._quit_action)

        self._tray.setContextMenu(self._menu)

    def show(self) -> None:
        from PyQt6.QtWidgets import QSystemTrayIcon as _QSTI

        if not _QSTI.isSystemTrayAvailable():
            logger.error(
                "Bu sistemde sistem tepsisi (tray) desteklenmiyor gibi gorunuyor. "
                "Windows'ta 'Gizli simgeleri goster' okundan kontrol edin."
            )
        self._tray.show()
        logger.info("Tray ikonu gosterildi (visible=%s).", self._tray.isVisible())

    def set_loading_state(self, is_loading: bool) -> None:
        """Modeller yuklenirken / islem surerken ikonu degistirmek icin."""
        if is_loading:
            icon = (
                QIcon(ICON_LOADING_PATH)
                if os.path.exists(ICON_LOADING_PATH)
                else _build_fallback_icon("#e67e22")  # turuncu: isleniyor
            )
        else:
            icon = (
                QIcon(ICON_PATH)
                if os.path.exists(ICON_PATH)
                else _build_fallback_icon("#0078d4")  # mavi: hazir/bos
            )
        self._tray.setIcon(icon)
        tooltip = "Screen Translator - Isleniyor..." if is_loading else "Screen Translator"
        self._tray.setToolTip(tooltip)

    def show_message(self, title: str, message: str) -> None:
        self._tray.showMessage(title, message, QSystemTrayIcon.MessageIcon.Information, 3000)
