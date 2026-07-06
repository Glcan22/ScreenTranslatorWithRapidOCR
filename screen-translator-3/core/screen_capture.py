"""
core/screen_capture.py
-------------------------
Verilen (x, y, w, h) PHYSICAL piksel koordinatlarindan ekran goruntusu yakalar.

Onemli: Bu modul DPI donusumu YAPMAZ, girdi olarak zaten physical piksel
koordinat bekler. Donusum sorumlulugu pipeline.py + utils/dpi_utils.py'dedir.
Bu ayrim, "hangi modulde koordinat kaydi oluyor" sorusunu netlestirmek icindir.
"""

import mss
import numpy as np
from PIL import Image

from utils.logger import get_logger

logger = get_logger("screen_capture")


class ScreenCaptureError(Exception):
    """Ekran yakalama sirasinda beklenmeyen bir hata olustugunda firlatilir."""


def capture_region(x: int, y: int, w: int, h: int) -> np.ndarray:
    """
    Belirtilen bolgeyi yakalar ve RapidOCR'in kabul ettigi RGB numpy array
    formatinda doner. (RapidOCR hem BGR hem RGB numpy array kabul eder,
    burada acikca RGB'ye ceviriyoruz.)
    """
    if w <= 0 or h <= 0:
        raise ScreenCaptureError(f"Gecersiz bolge boyutu: w={w}, h={h}")

    monitor = {"left": x, "top": y, "width": w, "height": h}

    try:
        with mss.mss() as sct:
            raw_screenshot = sct.grab(monitor)
    except mss.exception.ScreenShotError as exc:
        logger.error("mss ile ekran yakalama basarisiz: %s", exc)
        raise ScreenCaptureError(
            "Ekran goruntusu alinamadi. Baska bir uygulama ekran yakalamayi "
            "engelliyor olabilir (bazi DRM korumali pencereler gibi)."
        ) from exc

    # mss BGRA formatinda doner; RGB'ye ceviriyoruz.
    image = Image.frombytes(
        "RGB", raw_screenshot.size, raw_screenshot.bgra, "raw", "BGRX"
    )
    image_array = np.array(image)

    logger.debug("Bolge yakalandi: %dx%d piksel", w, h)
    return image_array
