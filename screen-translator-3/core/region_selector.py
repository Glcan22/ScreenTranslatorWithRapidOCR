"""
core/region_selector.py
-------------------------
Tum ekrani kaplayan, yari seffaf, frameless bir overlay penceresi.
Kullanici mouse ile bir dikdortgen cizer; cizim bitince secilen
(x, y, w, h) logical koordinatlari region_selected sinyali ile yayar.

DPI donusumu burada YAPILMAZ -- bu ekranin sorumlulugu degil.
Donusum, screen_capture.py cagrilmadan once utils/dpi_utils.py uzerinden
pipeline.py tarafindan yapilir. Boylece bu dosya tek bir isten sorumlu kalir.
"""

from PyQt6.QtCore import Qt, QRect, pyqtSignal
from PyQt6.QtGui import QColor, QPainter, QPen
from PyQt6.QtWidgets import QWidget, QApplication

from utils.logger import get_logger

logger = get_logger("region_selector")


class RegionSelector(QWidget):
    region_selected = pyqtSignal(int, int, int, int)  # x, y, w, h
    selection_cancelled = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._start_point = None
        self._end_point = None
        self._is_selecting = False

        self._setup_window()

    def _setup_window(self) -> None:
        # Tum sanal ekrani (birden fazla monitor dahil) kaplar.
        screen_geometry = self._get_virtual_screen_geometry()
        self.setGeometry(screen_geometry)

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool  # taskbar'da gorunmesin
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setCursor(Qt.CursorShape.CrossCursor)
        # ESC ile iptalin her zaman calismasi icin, pencere acilir acilmaz
        # klavye odagini (focus) zorla almasi gerekir -- bazi Windows
        # kurulumlarinda frameless/tool pencereler otomatik odak almayabilir.
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self.activateWindow()
        self.setFocus(Qt.FocusReason.ActiveWindowFocusReason)

    @staticmethod
    def _get_virtual_screen_geometry() -> QRect:
        """Coklu monitor kurulumlarinda tum ekranlarin birlesik alanini doner."""
        combined = QRect()
        for screen in QApplication.screens():
            combined = combined.united(screen.geometry())
        return combined

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._is_selecting = True
            self._start_point = event.position().toPoint()
            self._end_point = self._start_point
            self.update()

    def mouseMoveEvent(self, event) -> None:
        if self._is_selecting:
            self._end_point = event.position().toPoint()
            self.update()

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton and self._is_selecting:
            self._is_selecting = False
            self._end_point = event.position().toPoint()

            rect = QRect(self._start_point, self._end_point).normalized()

            # Cok kucuk (yanlissikla tiklama) secimleri iptal say.
            if rect.width() < 5 or rect.height() < 5:
                logger.debug("Secim cok kucuk, iptal edildi.")
                self.selection_cancelled.emit()
            else:
                # Widget-local koordinatlari global ekran koordinatlarina cevir.
                global_top_left = self.mapToGlobal(rect.topLeft())
                logger.info(
                    "Bolge secildi: x=%d y=%d w=%d h=%d",
                    global_top_left.x(), global_top_left.y(), rect.width(), rect.height(),
                )
                self.region_selected.emit(
                    global_top_left.x(), global_top_left.y(), rect.width(), rect.height()
                )

            self.close()

    def keyPressEvent(self, event) -> None:
        # ESC ile secim iptal edilebilir.
        if event.key() == Qt.Key.Key_Escape:
            logger.debug("Secim ESC ile iptal edildi.")
            self.selection_cancelled.emit()
            self.close()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 90))  # yari seffaf karartma

        if self._is_selecting and self._start_point and self._end_point:
            rect = QRect(self._start_point, self._end_point).normalized()
            # Secili alani aydinlat (yari saydam beyaz vurgu).
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Source)
            painter.fillRect(rect, QColor(255, 255, 255, 40))
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)

            pen = QPen(QColor(0, 150, 255), 2)
            painter.setPen(pen)
            painter.drawRect(rect)
