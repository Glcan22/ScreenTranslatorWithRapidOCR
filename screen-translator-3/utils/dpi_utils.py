"""
utils/dpi_utils.py
-------------------
Windows'ta farkli DPI scaling (%100 / %125 / %150 / %175) yuzunden,
Qt'nin verdigi "logical" koordinatlar ile mss/screenshot'in bekledigi
"physical" piksel koordinatlari birbirinden kayabilir.

Bu modul, uygulamanin PROCESS_PER_MONITOR_DPI_AWARE olarak isaretlenmesini
ve gerekliyse koordinat/olcek donusumlerini tek bir yerden yonetir.
Boylece "secilen bolge ile yakalanan bolge farkli" tarzi hatalar
sadece bu dosyaya bakilarak teshis edilebilir.
"""

import ctypes
import sys

if sys.platform == "win32":
    import ctypes.wintypes  # noqa: F401  (ctypes.wintypes.POINT icin gerekli)

from utils.logger import get_logger

logger = get_logger("dpi_utils")


def enable_windows_dpi_awareness() -> None:
    """
    Uygulamayi Windows'a 'per-monitor DPI aware' olarak bildirir.
    main.py icinde QApplication olusturulmadan ONCE cagrilmalidir.
    Windows disinda (gelistirme/test ortami) sessizce atlanir.
    """
    if sys.platform != "win32":
        logger.info("Windows disi platform, DPI awareness atlandi.")
        return

    try:
        # PROCESS_PER_MONITOR_DPI_AWARE = 2
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
        logger.info("Per-monitor DPI awareness aktif edildi.")
    except (AttributeError, OSError) as exc:
        # Eski Windows surumlerinde shcore olmayabilir, fallback dene.
        try:
            ctypes.windll.user32.SetProcessDPIAware()
            logger.warning(
                "shcore.SetProcessDpiAwareness basarisiz (%s), "
                "eski SetProcessDPIAware fallback kullanildi.", exc
            )
        except (AttributeError, OSError) as exc2:
            logger.error("DPI awareness ayarlanamadi: %s", exc2)


def get_scale_factor_for_point(x: int, y: int) -> float:
    """
    Verilen ekran koordinatinin bulundugu monitorun DPI olcek faktorunu doner.
    Ornek: %150 scaling -> 1.5 doner.
    Windows disinda veya hata durumunda 1.0 (olceksiz) doner.
    """
    if sys.platform != "win32":
        return 1.0

    try:
        MONITOR_DEFAULTTONEAREST = 2
        point = ctypes.wintypes.POINT(int(x), int(y))
        hmonitor = ctypes.windll.user32.MonitorFromPoint(
            point, MONITOR_DEFAULTTONEAREST
        )

        dpi_x = ctypes.c_uint()
        dpi_y = ctypes.c_uint()
        ctypes.windll.shcore.GetDpiForMonitor(
            hmonitor, 0, ctypes.byref(dpi_x), ctypes.byref(dpi_y)
        )
        # 96 DPI = %100 (baz deger)
        scale = dpi_x.value / 96.0
        return scale
    except (AttributeError, OSError) as exc:
        logger.error("DPI olcek faktoru okunamadi, 1.0 kullanilacak: %s", exc)
        return 1.0


def logical_to_physical(x: int, y: int, w: int, h: int) -> tuple:
    """
    Qt'den gelen logical (DPI-independent) koordinatlari, ekran yakalama
    icin gereken physical piksel koordinatlarina cevirir.

    NOT: Uygulama enable_windows_dpi_awareness() ile per-monitor-aware
    isaretlendiginde, Qt6 genelde zaten physical piksel dondurur.
    Bu fonksiyon, olceklerin ustustte uygulanmasini (double-scaling) onlemek
    icin bir guvenlik katmani olarak tutulur; scale == 1.0 ise dokunmaz.
    """
    scale = get_scale_factor_for_point(x, y)

    if abs(scale - 1.0) < 1e-6:
        return x, y, w, h

    logger.debug("DPI scale=%.2f uygulaniyor: (%d,%d,%d,%d)", scale, x, y, w, h)
    return (
        int(x * scale),
        int(y * scale),
        int(w * scale),
        int(h * scale),
    )
