"""
utils/logger.py
----------------
Merkezi loglama. Her modul buradan get_logger(__name__) cagirir.
Loglar hem konsola hem logs/app.log dosyasina yazilir, boylece
kullanici "hata var" dediginde bu dosyaya bakmak yeterli olur.
"""

import logging
import os
import sys

from config import CONFIG, BASE_DIR

_LOG_FILE = os.path.join(BASE_DIR, CONFIG.get("log_file", "logs/app.log"))
_LOG_LEVEL = getattr(logging, CONFIG.get("log_level", "INFO").upper(), logging.INFO)

_initialized = False


def _init_logging():
    global _initialized
    if _initialized:
        return

    log_dir = os.path.dirname(_LOG_FILE)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)

    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    root_logger = logging.getLogger("screen_translator")
    root_logger.setLevel(_LOG_LEVEL)

    file_handler = logging.FileHandler(_LOG_FILE, encoding="utf-8")
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    _initialized = True


def get_logger(name: str) -> logging.Logger:
    _init_logging()
    return logging.getLogger(f"screen_translator.{name}")
