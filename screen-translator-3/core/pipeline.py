"""
core/pipeline.py
-------------------
"Yakala -> OCR -> Cevir" akisini yoneten orkestratör.
QThread icinde calisir, boylece UI thread'i (main thread) hicbir zaman
bloklanmaz -- popup donuk gorunmez, tray ikonu tepki vermeye devam eder.

Her adim ayri try/except ile sarilir; hangi adimda hata olduysa
error_occurred sinyali bu bilgiyle (adim adi + mesaj) birlikte yayilir.
Boylece kullaniciya "Yakalama basarisiz" / "Metin bulunamadi" /
"Ceviri basarisiz" gibi net, adima ozel mesajlar gosterilebilir.
"""

from PyQt6.QtCore import QThread, pyqtSignal

from core.screen_capture import capture_region, ScreenCaptureError
from core.ocr_engine import OcrEngine, OcrError
from core.translator_engine import TranslatorEngine, TranslationError
from utils.dpi_utils import logical_to_physical
from utils.logger import get_logger

logger = get_logger("pipeline")


class TranslationPipeline(QThread):
    """
    Kullanim:
        pipeline = TranslationPipeline(x, y, w, h, translator_engine)
        pipeline.result_ready.connect(on_result)
        pipeline.error_occurred.connect(on_error)
        pipeline.start()   # QThread.start() -> run() arka planda calisir

    translator_engine disaridan verilir cunku TranslatorEngine de OcrEngine
    gibi tekrar tekrar olusturulmamali; main.py'da bir kere olusturulup
    her pipeline cagrisina aktarilir.
    """

    # original_text, translated_text
    result_ready = pyqtSignal(str, str)
    # step_name, error_message  (step_name: "capture" | "ocr" | "translate")
    error_occurred = pyqtSignal(str, str)

    def __init__(self, x: int, y: int, w: int, h: int, translator_engine: TranslatorEngine):
        super().__init__()
        self._x, self._y, self._w, self._h = x, y, w, h
        self._translator = translator_engine

    def run(self) -> None:
        # --- Adim 1: DPI duzeltme + yakalama ---
        try:
            px, py, pw, ph = logical_to_physical(self._x, self._y, self._w, self._h)
            image = capture_region(px, py, pw, ph)
        except ScreenCaptureError as exc:
            logger.error("Pipeline durdu (capture): %s", exc)
            self.error_occurred.emit("capture", str(exc))
            return
        except Exception as exc:
            logger.exception("Pipeline'da beklenmeyen yakalama hatasi")
            self.error_occurred.emit("capture", f"Beklenmeyen hata: {exc}")
            return

        # --- Adim 2: OCR ---
        try:
            ocr_engine = OcrEngine.get_instance()
            original_text = ocr_engine.extract_text(image)
        except OcrError as exc:
            logger.error("Pipeline durdu (ocr): %s", exc)
            self.error_occurred.emit("ocr", str(exc))
            return
        except Exception as exc:
            logger.exception("Pipeline'da beklenmeyen OCR hatasi")
            self.error_occurred.emit("ocr", f"Beklenmeyen hata: {exc}")
            return

        if not original_text.strip():
            self.error_occurred.emit("ocr", "Secilen bolgede metin bulunamadi.")
            return

        # --- Adim 3: Ceviri ---
        try:
            translated_text = self._translator.translate(original_text)
        except TranslationError as exc:
            logger.error("Pipeline durdu (translate): %s", exc)
            self.error_occurred.emit("translate", str(exc))
            return
        except Exception as exc:
            logger.exception("Pipeline'da beklenmeyen ceviri hatasi")
            self.error_occurred.emit("translate", f"Beklenmeyen hata: {exc}")
            return

        logger.info("Pipeline basariyla tamamlandi.")
        self.result_ready.emit(original_text, translated_text)
