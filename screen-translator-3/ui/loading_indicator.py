"""
ui/loading_indicator.py
--------------------------
Pipeline calisirken kullaniciya "isleniyor" hissini vermek icin
tray ikonu uzerinden basit bir durum bildirimi.

Ayri bir pencere acmiyoruz (bu kucuk bir islem icin fazla agir olur);
bunun yerine tray_icon.set_loading_state() cagrilarak ikon/tooltip
degistirilir. Bu modul, bu mantigi main.py'dan ayirmak icin
ince bir koordinator katmanidir.
"""

from ui.tray_icon import TrayIcon
from utils.logger import get_logger

logger = get_logger("loading_indicator")


class LoadingIndicator:
    def __init__(self, tray_icon: TrayIcon):
        self._tray_icon = tray_icon

    def start(self) -> None:
        logger.debug("Isleniyor durumu basladi.")
        self._tray_icon.set_loading_state(True)

    def stop(self) -> None:
        logger.debug("Isleniyor durumu bitti.")
        self._tray_icon.set_loading_state(False)
