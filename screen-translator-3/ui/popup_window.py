"""
ui/popup_window.py
---------------------
Ceviri sonucunu gosteren kucuk, frameless popup.
- Orijinal metin (Cince) + Kopyala butonu
- Ceviri metni (Ingilizce) + Kopyala butonu
- Secilen bolgenin hemen altinda acilir; ekran disina tasarsa
  otomatik olarak yukari/sola kaydirilir.
- Disariya tiklaninca, ESC ile veya X butonuna basilinca kapanir (gizlenir).

ONEMLI - TEK, YENIDEN KULLANILABILIR POPUP MIMARISI:
Bu widget SILINMEZ (WA_DeleteOnClose kullanilmiyor), sadece gizlenir/gosterilir.
main.py TEK bir PopupWindow ornegi olusturup saklar; ust uste ceviri
yapildiginda ayni nesne yeni metin/konum ile guncellenip tekrar gosterilir.
Boylece ekranda birden fazla popup birikmez, her zaman en fazla bir tane
acik olur -- yeni ceviri eskisinin yerini alir.
"""

from PyQt6.QtCore import Qt, QPoint, QEvent
from PyQt6.QtGui import QGuiApplication
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QTextEdit,
    QPushButton,
    QApplication,
)

from config import CONFIG
from utils.logger import get_logger

logger = get_logger("popup_window")


class PopupWindow(QWidget):
    def __init__(self):
        super().__init__()
        self._setup_window()
        self._build_ui()

    def _setup_window(self) -> None:
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool  # taskbar'da gorunmesin
        )
        self.setFixedWidth(CONFIG["popup_width"])
        self.setMaximumHeight(CONFIG["popup_max_height"])
        self.setStyleSheet(
            """
            QWidget {
                background-color: #1e1e1e;
                border: 1px solid #3a3a3a;
                border-radius: 8px;
            }
            QLabel {
                color: #cccccc;
                font-size: 11px;
                font-weight: bold;
                border: none;
            }
            QTextEdit {
                background-color: #2a2a2a;
                color: #f0f0f0;
                border: 1px solid #3a3a3a;
                border-radius: 4px;
                padding: 6px;
                font-size: 13px;
            }
            QPushButton {
                background-color: #0078d4;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 4px 10px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #106ebe;
            }
            #closeButton {
                background-color: transparent;
                color: #999999;
                font-size: 14px;
                font-weight: bold;
            }
            #closeButton:hover {
                background-color: #c0392b;
                color: white;
            }
            """
        )

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 12)
        layout.setSpacing(8)

        # Ust satir: baslik + kapat butonu
        header_row = QHBoxLayout()
        title_label = QLabel("Screen Translator")
        close_button = QPushButton("\u2715")
        close_button.setObjectName("closeButton")
        close_button.setFixedSize(22, 22)
        close_button.clicked.connect(self.hide)
        header_row.addWidget(title_label)
        header_row.addStretch()
        header_row.addWidget(close_button)
        layout.addLayout(header_row)

        # Orijinal metin blogu
        layout.addWidget(self._build_text_block(
            label_text="Orijinal (Cince)",
            text_attr_name="original_text_edit",
            copy_slot=self._copy_original,
        ))

        # Ceviri metin blogu
        layout.addWidget(self._build_text_block(
            label_text="Ceviri (Ingilizce)",
            text_attr_name="translated_text_edit",
            copy_slot=self._copy_translated,
        ))

    def _build_text_block(self, label_text: str, text_attr_name: str, copy_slot) -> QWidget:
        container = QWidget()
        container.setStyleSheet("background: transparent; border: none;")
        v_layout = QVBoxLayout(container)
        v_layout.setContentsMargins(0, 0, 0, 0)
        v_layout.setSpacing(4)

        row = QHBoxLayout()
        label = QLabel(label_text)
        copy_button = QPushButton("Kopyala")
        copy_button.setFixedWidth(70)
        copy_button.clicked.connect(copy_slot)
        row.addWidget(label)
        row.addStretch()
        row.addWidget(copy_button)
        v_layout.addLayout(row)

        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setMaximumHeight(120)
        setattr(self, text_attr_name, text_edit)
        v_layout.addWidget(text_edit)

        return container

    def keyPressEvent(self, event) -> None:
        # ESC ile popup'i gizle (QTextEdit odaktaysa bile bu olay
        # yakalanmazsa Qt otomatik olarak ust widget'a -- yani buraya --
        # yollar, cunku QTextEdit read-only oldugu icin ESC'i kendi
        # kullanmiyor).
        if event.key() == Qt.Key.Key_Escape:
            logger.debug("Popup ESC ile kapatildi.")
            self.hide()
        else:
            super().keyPressEvent(event)

    def showEvent(self, event) -> None:
        super().showEvent(event)
        # Disari tiklamayi yakalamak icin uygulama genelinde fare
        # olaylarini dinlemeye basla. Popup gizlenince (hideEvent) bu
        # dinleyici kaldirilir, boylece popup kapaliyken gereksiz yere
        # her tikta calismaz.
        QApplication.instance().installEventFilter(self)

    def hideEvent(self, event) -> None:
        QApplication.instance().removeEventFilter(self)
        super().hideEvent(event)

    def eventFilter(self, watched_object, event) -> bool:
        if event.type() == QEvent.Type.MouseButtonPress:
            click_point = event.globalPosition().toPoint()
            if self.isVisible() and not self.geometry().contains(click_point):
                logger.debug("Popup disari tiklanarak kapatildi.")
                self.hide()
        return super().eventFilter(watched_object, event)

    def show_result(self, original_text: str, translated_text: str, anchor_rect: tuple) -> None:
        """
        anchor_rect: (x, y, w, h) -- secilen bolgenin logical koordinatlari.
        Popup bu bolgenin hemen altinda acilir; ekran disina tasarsa konum duzeltilir.
        """
        self.original_text_edit.setPlainText(original_text)
        self.translated_text_edit.setPlainText(translated_text)

        self._position_below(anchor_rect)
        self.show()
        self.raise_()
        self.activateWindow()

    def _position_below(self, anchor_rect: tuple) -> None:
        x, y, w, h = anchor_rect
        target_x = x
        target_y = y + h + 8  # secilen bolgenin 8px altinda

        screen = QGuiApplication.screenAt(QPoint(x, y)) or QGuiApplication.primaryScreen()
        screen_geometry = screen.availableGeometry()

        popup_width = self.width()
        popup_height = self.sizeHint().height() or CONFIG["popup_max_height"]

        # Sag kenara tasma kontrolu
        if target_x + popup_width > screen_geometry.right():
            target_x = screen_geometry.right() - popup_width - 8

        # Sol kenara tasma kontrolu
        if target_x < screen_geometry.left():
            target_x = screen_geometry.left() + 8

        # Alt kenara tasma kontrolu -> secimin USTUNE al
        if target_y + popup_height > screen_geometry.bottom():
            target_y = y - popup_height - 8
            if target_y < screen_geometry.top():
                target_y = screen_geometry.top() + 8

        self.move(target_x, target_y)
        logger.debug("Popup konumlandirildi: (%d, %d)", target_x, target_y)

    def _copy_original(self) -> None:
        QApplication.clipboard().setText(self.original_text_edit.toPlainText())
        logger.debug("Orijinal metin kopyalandi.")

    def _copy_translated(self) -> None:
        QApplication.clipboard().setText(self.translated_text_edit.toPlainText())
        logger.debug("Ceviri metni kopyalandi.")

    def show_error(self, step_name: str, message: str, anchor_rect: tuple = None) -> None:
        """Pipeline bir adimda hata verirse, sonucu degil bu hatayi gosterir."""
        step_labels = {
            "capture": "Ekran yakalama hatasi",
            "ocr": "Metin tanima hatasi",
            "translate": "Ceviri hatasi",
        }
        title = step_labels.get(step_name, "Hata")
        self.original_text_edit.setPlainText(f"{title}:\n{message}")
        self.translated_text_edit.setPlainText("")

        if anchor_rect:
            self._position_below(anchor_rect)

        self.show()
        self.raise_()
        self.activateWindow()
