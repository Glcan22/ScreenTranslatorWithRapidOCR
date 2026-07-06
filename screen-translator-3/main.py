"""
main.py
--------
Uygulama giris noktasi. Sirasiyla:
  1. Windows DPI awareness ayarlanir (QApplication olusmadan ONCE).
  2. QApplication baslatilir.
  3. Modellerin hazir oldugu kontrol edilir (argos-translate).
  4. TranslatorEngine bir kere olusturulur (OcrEngine ilk kullanimda,
     lazy olarak olusturulur -- boylece uygulama acilisi yavas olmaz).
  5. Tray ikonu ve hotkey dinleyici baslatilir.
  6. Hotkey'e basilinca: RegionSelector -> Pipeline -> PopupWindow akisi kurulur.

POPUP DAVRANISI: Tek bir PopupWindow nesnesi tembel (lazy) olusturulup
saklanir (_get_popup()); ust uste ceviri yapildiginda ayni nesne yeni
metin/konum ile guncellenir, ekranda popup birikmez. Popup; X butonuna
basinca, ESC ile veya disari tiklaninca kapanir (bkz. ui/popup_window.py).

Not: PyQt6 QApplication tek bir kere olusturulmali ve event loop
(app.exec()) uygulamanin sonuna kadar calismali; tray uygulamasi
oldugu icin ana pencere yok, uygulama sadece tray + popup ile yasar.
"""

import sys

from PyQt6.QtWidgets import QApplication, QMessageBox

from utils.dpi_utils import enable_windows_dpi_awareness
from utils.logger import get_logger
from utils.model_check import ensure_models_ready, ModelNotReadyError

logger = get_logger("main")


class ScreenTranslatorApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)  # tray uygulamasi, pencere kapaninca cikmasin

        self._translator_engine = None
        self._region_selector = None
        self._active_pipelines = []  # calisan QThread'lerin erken silinmesini onlemek icin
        self._popup = None  # TEK, yeniden kullanilabilir popup -- her ceviride guncellenir
        self._last_region = None

        self._tray_icon = None
        self._hotkey_manager = None
        self._loading_indicator = None

    def initialize(self) -> bool:
        """Modelleri kontrol eder, bilesenleri kurar. Basarisiz olursa False doner."""
        try:
            ensure_models_ready()
        except ModelNotReadyError as exc:
            logger.error("Modeller hazir degil: %s", exc)
            QMessageBox.critical(
                None,
                "Screen Translator - Kurulum Hatasi",
                f"{exc}\n\nLutfen setup.bat dosyasini calistirip tekrar deneyin.",
            )
            return False

        # Gec import: TranslatorEngine argos modellerinin kurulu olmasini bekler.
        from core.translator_engine import TranslatorEngine
        self._translator_engine = TranslatorEngine()

        from ui.tray_icon import TrayIcon
        from ui.loading_indicator import LoadingIndicator
        from core.hotkey_manager import HotkeyManager

        self._tray_icon = TrayIcon()
        self._tray_icon.quit_requested.connect(self._quit)
        self._tray_icon.show()

        self._loading_indicator = LoadingIndicator(self._tray_icon)

        self._hotkey_manager = HotkeyManager()
        self._hotkey_manager.hotkey_pressed.connect(self._on_hotkey_pressed)
        self._hotkey_manager.start()

        logger.info("Uygulama baslatildi, kisayol bekleniyor.")
        return True

    def _on_hotkey_pressed(self) -> None:
        """Kisayola basilinca bolge secim overlay'ini acar."""
        from core.region_selector import RegionSelector

        logger.debug("Kisayol tetiklendi, bolge secici aciliyor.")
        self._region_selector = RegionSelector()
        self._region_selector.region_selected.connect(self._on_region_selected)
        self._region_selector.selection_cancelled.connect(self._on_selection_cancelled)
        self._region_selector.show()

    def _on_selection_cancelled(self) -> None:
        logger.debug("Bolge secimi iptal edildi.")

    def _on_region_selected(self, x: int, y: int, w: int, h: int) -> None:
        from core.pipeline import TranslationPipeline

        self._last_region = (x, y, w, h)
        self._loading_indicator.start()

        pipeline = TranslationPipeline(x, y, w, h, self._translator_engine)
        self._active_pipelines.append(pipeline)

        pipeline.result_ready.connect(self._on_pipeline_result)
        pipeline.error_occurred.connect(self._on_pipeline_error)
        pipeline.finished.connect(self._loading_indicator.stop)
        pipeline.finished.connect(lambda: self._cleanup_pipeline(pipeline))
        pipeline.start()

    def _cleanup_pipeline(self, pipeline) -> None:
        """Bitmis pipeline'i referans listesinden cikarir (bellek sizintisi olmasin)."""
        if pipeline in self._active_pipelines:
            self._active_pipelines.remove(pipeline)

    def _get_popup(self):
        """
        TEK popup nesnesini tembel (lazy) olarak olusturur ve saklar.
        Sonraki her cagride ayni nesne yeniden kullanilir -- boylece
        ust uste ceviri yapildiginda ekranda popup birikmez, yenisi
        eskisinin yerini alir.
        """
        if self._popup is None:
            from ui.popup_window import PopupWindow
            self._popup = PopupWindow()
        return self._popup

    def _on_pipeline_result(self, original_text: str, translated_text: str) -> None:
        logger.debug("Pipeline sonucu alindi, popup gosteriliyor.")
        popup = self._get_popup()
        popup.show_result(original_text, translated_text, self._last_region)

    def _on_pipeline_error(self, step_name: str, message: str) -> None:
        logger.warning("Pipeline hatasi [%s]: %s", step_name, message)
        popup = self._get_popup()
        popup.show_error(step_name, message, self._last_region)

    def _quit(self) -> None:
        logger.info("Uygulama kapatiliyor.")
        if self._hotkey_manager:
            self._hotkey_manager.stop()
        self.app.quit()

    def run(self) -> int:
        return self.app.exec()


def main() -> int:
    enable_windows_dpi_awareness()  # QApplication'dan ONCE cagrilmali

    app = ScreenTranslatorApp()
    if not app.initialize():
        return 1

    return app.run()


if __name__ == "__main__":
    sys.exit(main())
