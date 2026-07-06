@echo off
REM ============================================================
REM setup.bat
REM ------------------------------------------------------------
REM Turkce karakterlerin dogru gorunmesi icin UTF-8'e gecis.
REM (Onceki projede karsilasilan encoding sorunlarina karsi.)
chcp 65001 >nul

setlocal enabledelayedexpansion

echo ============================================
echo   Screen Translator - Kurulum
echo ============================================
echo.

REM ------------------------------------------------------------
REM 1) Python 3.11 kontrolu
REM    Proje bu surumle test edilip dogrulanmistir (PyQt6, RapidOCR,
REM    onnxruntime ve argos-translate hep birlikte sorunsuz calisiyor).
REM ------------------------------------------------------------
echo [1/6] Python 3.11 kontrol ediliyor...

py -3.11 --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo HATA: Python 3.11 bulunamadi.
    echo Bu proje Python 3.11 ile test edilip dogrulandi; sisteminizde
    echo baska bir Python surumu kurulu olabilir.
    echo.
    echo Lutfen https://www.python.org/downloads/release/python-3119/
    echo adresinden Python 3.11'i indirip kurun, ardindan bu scripti
    echo tekrar calistirin.
    echo.
    pause
    exit /b 1
)

echo Python 3.11 bulundu, devam ediliyor.
echo.

REM ------------------------------------------------------------
REM 2) Virtual environment olusturma
REM ------------------------------------------------------------
echo [2/6] Sanal ortam (venv) olusturuluyor...

if exist venv (
    echo Mevcut venv bulundu, bu adim atlaniyor.
) else (
    py -3.11 -m venv venv
    if errorlevel 1 (
        echo HATA: venv olusturulamadi.
        pause
        exit /b 1
    )
)
echo.

REM ------------------------------------------------------------
REM 3) venv aktive etme
REM ------------------------------------------------------------
echo [3/6] Sanal ortam aktive ediliyor...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo HATA: venv aktive edilemedi.
    pause
    exit /b 1
)
echo.

REM ------------------------------------------------------------
REM 4) Bagimliliklarin kurulumu
REM ------------------------------------------------------------
echo [4/6] Python paketleri kuruluyor (bu birkac dakika surebilir)...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo HATA: Paket kurulumu basarisiz oldu.
    echo Yukaridaki hata mesajini kontrol edin (internet baglantisi,
    echo antivirus engeli veya eksik Visual C++ Build Tools olabilir^).
    pause
    exit /b 1
)
echo.

REM ------------------------------------------------------------
REM 5) RapidOCR modelini onceden indirme
REM    Boylece uygulama ilk acilista "donmus" gibi gorunmez;
REM    model indirme hatasi burada, net bir sekilde ortaya cikar.
REM    RapidOCR CPU (ONNXRuntime) uzerinde calisir, GPU/torch gerekmez.
REM ------------------------------------------------------------
echo [5/6] RapidOCR modeli indiriliyor (Cince)...
python -c "from rapidocr import RapidOCR; RapidOCR(); print('RapidOCR modeli hazir.')"
if errorlevel 1 (
    echo.
    echo HATA: RapidOCR modeli indirilemedi.
    echo Internet baglantinizi kontrol edin ve tekrar deneyin.
    pause
    exit /b 1
)
echo.

REM ------------------------------------------------------------
REM 6) argos-translate zh->en paketini onceden indirme
REM ------------------------------------------------------------
echo [6/6] Ceviri modeli indiriliyor (Cince - Ingilizce)...
python -c "import argostranslate.package as pkg; pkg.update_package_index(); pkgs = pkg.get_available_packages(); target = next(p for p in pkgs if p.from_code == 'zh' and p.to_code == 'en'); pkg.install_from_path(target.download()); print('Ceviri modeli hazir.')"
if errorlevel 1 (
    echo.
    echo HATA: Ceviri modeli indirilemedi.
    echo Internet baglantinizi kontrol edin ve tekrar deneyin.
    pause
    exit /b 1
)
echo.

echo ============================================
echo   Kurulum tamamlandi!
echo ============================================
echo.
echo Uygulamayi calistirmak icin:
echo   1. venv\Scripts\activate.bat
echo   2. python main.py
echo.
echo Kisayol: Ctrl+Shift+T (ekran bolgesi secmek icin)
echo.
pause
