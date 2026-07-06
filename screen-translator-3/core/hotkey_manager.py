"""
core/hotkey_manager.py
------------------------
Global kisayol tusunu dinler (varsayilan: ctrl+shift+t).

'keyboard' kutuphanesi yerine 'pynput' kullaniyoruz cunku:
  - keyboard bazi Windows kurulumlarinda admin yetkisi gerektirebiliyor
  - pynput daha genis Windows surumunde ekstra yetki istemeden calisiyor
Bu secim mimaride onceden not edilen "Global hotkey admin yetkisi" riskine
karsi alinmis bir tedbirdir.
"""

from PyQt6.QtCore import QObject, pyqtSignal
from pynput import keyboard as pynput_keyboard

from config import CONFIG
from utils.logger import get_logger

logger = get_logger("hotkey_manager")


class HotkeyManager(QObject):
    """
    Belirlenen kisayol tusuna basildiginda hotkey_pressed sinyalini yayar.
    Qt sinyali kullanarak, pynput'in kendi thread'inden Qt ana thread'ine
    guvenli sekilde haber verilmesini saglar.
    """

    hotkey_pressed = pyqtSignal()

    def __init__(self, hotkey_str: str = None):
        super().__init__()
        self.hotkey_str = hotkey_str or CONFIG["hotkey"]
        self._listener = None
        self._hotkey_combination = self._parse_hotkey(self.hotkey_str)

    @staticmethod
    def _parse_hotkey(hotkey_str: str):
        """'ctrl+shift+t' gibi bir string'i pynput GlobalHotKeys formatina cevirir."""
        parts = hotkey_str.lower().split("+")
        key_map = {
            "ctrl": "<ctrl>",
            "shift": "<shift>",
            "alt": "<alt>",
            "cmd": "<cmd>",
            "win": "<cmd>",
        }
        formatted_parts = [key_map.get(p, p) for p in parts]
        return "+".join(formatted_parts)

    def start(self) -> None:
        """Dinlemeyi arka planda baslatir. main.py acilirken bir kere cagrilir."""
        try:
            self._listener = pynput_keyboard.GlobalHotKeys(
                {self._hotkey_combination: self._on_hotkey_triggered}
            )
            self._listener.start()
            logger.info("Hotkey dinleyici baslatildi: %s", self.hotkey_str)
        except Exception as exc:
            logger.error("Hotkey dinleyici baslatilamadi: %s", exc)
            raise

    def stop(self) -> None:
        if self._listener is not None:
            self._listener.stop()
            logger.info("Hotkey dinleyici durduruldu.")

    def _on_hotkey_triggered(self) -> None:
        logger.debug("Hotkey tetiklendi: %s", self.hotkey_str)
        self.hotkey_pressed.emit()
