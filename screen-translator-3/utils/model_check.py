"""
utils/model_check.py
---------------------
Uygulama baslamadan once argos-translate (zh->en) ceviri modelinin
kurulu olup olmadigini kontrol eder.

RapidOCR modeli kendi ic mekanizmasiyla ilk kullanimda otomatik indirilip
~/.rapidocr klasorune cache'lenir (bkz. core/ocr_engine.py), bu yuzden onun
icin ayri bir kontrol fonksiyonu gerekmez.

Argos-translate modeli setup.bat sirasinda onceden indirilir (bkz. proje
mimarisi). Bu modul, kullanici setup.bat'i atlayip main.py'i direkt
calistirirsa anlasilir bir hata mesaji ile durdurmak icin bir guvenlik agi
gorevi gorur.
"""

import argostranslate.package
import argostranslate.translate

from config import CONFIG
from utils.logger import get_logger

logger = get_logger("model_check")


class ModelNotReadyError(Exception):
    """Gerekli OCR/ceviri modelleri kurulu degilse firlatilir."""


def check_argos_translate_installed() -> bool:
    """zh->en ceviri paketinin argos-translate icinde kurulu olup olmadigini kontrol eder."""
    source_lang = CONFIG["source_lang"]
    target_lang = CONFIG["target_lang"]

    installed_languages = argostranslate.translate.get_installed_languages()
    from_lang = next((l for l in installed_languages if l.code == source_lang), None)
    to_lang = next((l for l in installed_languages if l.code == target_lang), None)

    if from_lang is None or to_lang is None:
        return False

    translation = from_lang.get_translation(to_lang)
    return translation is not None


def ensure_argos_translate_installed() -> None:
    """
    zh->en paketi kurulu degilse indirmeyi dener (internet gerektirir).
    setup.bat bunu zaten yapmis olmali; burasi sadece eksik kalirsa devreye girer.
    """
    if check_argos_translate_installed():
        logger.info("argos-translate zh->en paketi kurulu, devam ediliyor.")
        return

    logger.warning("argos-translate zh->en paketi bulunamadi, indiriliyor...")
    try:
        argostranslate.package.update_package_index()
        available_packages = argostranslate.package.get_available_packages()
        package_to_install = next(
            (
                p
                for p in available_packages
                if p.from_code == CONFIG["source_lang"] and p.to_code == CONFIG["target_lang"]
            ),
            None,
        )
        if package_to_install is None:
            raise ModelNotReadyError(
                f"{CONFIG['source_lang']}->{CONFIG['target_lang']} paketi "
                f"argos-translate deposunda bulunamadi."
            )
        argostranslate.package.install_from_path(package_to_install.download())
        logger.info("argos-translate paketi basariyla indirildi ve kuruldu.")
    except Exception as exc:
        logger.error("argos-translate paketi indirilemedi: %s", exc)
        raise ModelNotReadyError(
            "Ceviri modeli kurulu degil ve internetten indirilemedi. "
            "Lutfen setup.bat'i yeniden calistirin."
        ) from exc


def ensure_models_ready() -> None:
    """
    main.py baslarken bir kere cagrilir. Sadece argos-translate kontrolu
    yapiyoruz; RapidOCR modeli kendi lazy-loading mekanizmasiyla ilk
    kullanimda otomatik iner, burada tekrar tetiklemek istemeyiz
    (agir bir islem, gereksiz yere baslangicta beklemek yaratir).
    """
    ensure_argos_translate_installed()
