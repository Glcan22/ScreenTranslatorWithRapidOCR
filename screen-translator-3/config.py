"""
config.py
---------
Uygulama ayarlarini config.json'dan okur.
Dosya eksikse veya bozuksa, sabit DEFAULT_CONFIG ile calismaya devam eder
(uygulama asla sadece config yuzunden coker).
"""

import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")

DEFAULT_CONFIG = {
    "hotkey": "ctrl+alt+q",
    "popup_position": "below_selection",
    "source_lang": "zh",
    "target_lang": "en",
    "popup_width": 420,
    "popup_max_height": 400,
    "log_file": "logs/app.log",
    "log_level": "INFO",
}


def load_config() -> dict:
    """config.json'u okur; eksik alanlari DEFAULT_CONFIG ile tamamlar."""
    config = DEFAULT_CONFIG.copy()

    if not os.path.exists(CONFIG_PATH):
        return config

    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            user_config = json.load(f)
        config.update(user_config)
    except (json.JSONDecodeError, OSError):
        # Bozuk config dosyasi uygulamayi durdurmamali; default ile devam.
        pass

    return config


# Modul import edildiginde bir kere yuklenir, her yerden CONFIG olarak kullanilir.
CONFIG = load_config()
