"""
core/ocr_engine.py
---------------------
RapidOCR wrapper. Model sadece bir kere yuklenir (agir islem), sonraki
her cagri bu cache'lenmis nesneyi kullanir.

NOT: Daha once PaddleOCR kullaniliyordu, ancak PaddleOCR'in bagimliligi olan
torch, bazi Windows kurulumlarinda "DLL initialization routine failed" hatasi
veriyordu (torch\\lib\\c10.dll yuklenemiyordu). RapidOCR, ONNXRuntime tabanli
calistigi icin torch'a hic ihtiyac duymuyor, bu sinifin disindaki hicbir kod
bundan etkilenmedi (pipeline.py hala ayni extract_text() arayuzunu cagiriyor).
"""

import numpy as np
import onnxruntime
from rapidocr import RapidOCR

from utils.logger import get_logger

logger = get_logger("ocr_engine")


class OcrError(Exception):
    """OCR sirasinda beklenmeyen bir hata olustugunda firlatilir."""


class OcrEngine:
    """
    Singleton benzeri kullanim icin tasarlandi: pipeline.py bu sinifin
    TEK bir ornegini olusturup tekrar tekrar kullanmali, her cagri icin
    yeniden OcrEngine() yapilmamali (yoksa model her seferinde yeniden yuklenir).
    """

    _instance = None

    def __init__(self):
        logger.info("RapidOCR modeli yukleniyor (CPU/ONNXRuntime)...")
        try:
            # NOT: CPU'da calisma garantisi burada bir parametre ile degil,
            # requirements.txt'te DUZ "onnxruntime" paketinin kurulu olmasindan
            # gelir (onnxruntime-directml veya onnxruntime-gpu DEGIL). Duz
            # onnxruntime paketi sisteme sadece CPUExecutionProvider saglar,
            # bu yuzden RapidOCR'in ic tercih sirasi ne olursa olsun secilebilecek
            # tek motor CPU'dur. Boylece GPU/DirectML surucu sorunlarina karsi
            # sisteme bagli olmayan, kararli bir davranis elde edilir.
            self._ocr = RapidOCR()
            logger.info(
                "RapidOCR modeli hazir. Aktif ONNXRuntime execution providers: %s",
                onnxruntime.get_available_providers(),
            )
        except Exception as exc:
            logger.error("RapidOCR modeli yuklenemedi: %s", exc)
            raise OcrError(
                "OCR modeli yuklenemedi. Internet baglantinizi kontrol edin "
                "(ilk calistirmada model dosyalari indirilir)."
            ) from exc

    @classmethod
    def get_instance(cls) -> "OcrEngine":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def extract_text(self, image: np.ndarray) -> str:
        """
        Verilen goruntuden metni cikarir. Birden fazla satir tespit edilirse
        satirlari yeni satir karakteri ile birlestirir.
        """
        try:
            result = self._ocr(image)
        except Exception as exc:
            logger.error("OCR calistirilirken hata: %s", exc)
            raise OcrError("Metin taninirken bir hata olustu.") from exc

        if not result or not result.txts:
            logger.info("Secilen bolgede metin bulunamadi.")
            return ""

        extracted = "\n".join(result.txts)
        logger.debug("OCR sonucu: %s", extracted)
        return extracted
