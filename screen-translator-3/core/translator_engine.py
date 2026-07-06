"""
core/translator_engine.py
----------------------------
argos-translate uzerinden offline zh->en ceviri yapar.
Model kurulumu setup.bat / utils/model_check.py tarafindan garanti edilir;
bu modul sadece cevirme islemine odaklanir.
"""

import argostranslate.translate

from config import CONFIG
from utils.logger import get_logger

logger = get_logger("translator_engine")


class TranslationError(Exception):
    """Ceviri sirasinda beklenmeyen bir hata olustugunda firlatilir."""


class TranslatorEngine:
    def __init__(self):
        self._source_lang = CONFIG["source_lang"]
        self._target_lang = CONFIG["target_lang"]
        self._translation = self._load_translation()

    def _load_translation(self):
        installed_languages = argostranslate.translate.get_installed_languages()
        from_lang = next(
            (l for l in installed_languages if l.code == self._source_lang), None
        )
        to_lang = next(
            (l for l in installed_languages if l.code == self._target_lang), None
        )

        if from_lang is None or to_lang is None:
            raise TranslationError(
                f"{self._source_lang}->{self._target_lang} ceviri paketi kurulu degil. "
                f"Lutfen setup.bat'i calistirin."
            )

        translation = from_lang.get_translation(to_lang)
        if translation is None:
            raise TranslationError(
                f"{self._source_lang}->{self._target_lang} ceviri modeli bulunamadi."
            )
        return translation

    def translate(self, text: str) -> str:
        if not text.strip():
            return ""

        try:
            translated = self._translation.translate(text)
            logger.debug("Ceviri basarili: '%s' -> '%s'", text, translated)
            return translated
        except Exception as exc:
            logger.error("Ceviri sirasinda hata: %s", exc)
            raise TranslationError("Metin cevrilirken bir hata olustu.") from exc
