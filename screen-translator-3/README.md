# Screen Translator

Windows icin ekran bolgesi secip Cince metni Ingilizce'ye ceviren araç.
`Ctrl+Shift+T` ile ekranda bir bolge secilir, RapidOCR (CPU/ONNXRuntime) ile
metin okunur, argos-translate ile (offline) cevrilir ve kucuk bir popup
icinde orijinal + ceviri metni, her biri icin ayri "Kopyala" butonuyla
gosterilir.

## Kurulum

1. Python 3.11'in kurulu oldugundan emin olun (`py -3.11 --version`).
   Proje bu surumle test edilip dogrulandi.
2. `setup.bat` dosyasini calistirin. Bu script:
   - venv olusturur
   - Gerekli paketleri kurar (RapidOCR + duz `onnxruntime` -- CPU calisir,
     GPU/torch bagimliligi yoktur)
   - RapidOCR modelini onceden indirir
   - argos-translate zh->en paketini onceden indirir
3. Kurulum bitince:
   ```
   venv\Scripts\activate.bat
   python main.py
   ```

## Kullanim

- `Ctrl+Shift+T` tusuna basin.
- Ekranda Cince metin iceren bir bolgeyi surukleyerek secin (ESC ile iptal edebilirsiniz).
- Kisa bir sure sonra secilen bolgenin altinda bir popup acilir:
  orijinal metin ve Ingilizce cevirisi, her biri icin Kopyala butonuyla.

## Proje Yapisi

```
main.py                      Giris noktasi
config.py / config.json      Ayarlar
core/
  hotkey_manager.py          Global kisayol dinleme (pynput)
  region_selector.py         Ekran bolgesi secim overlay'i
  screen_capture.py          Ekran goruntusu yakalama (mss)
  ocr_engine.py               RapidOCR wrapper (CPU/ONNXRuntime)
  translator_engine.py       argos-translate wrapper
  pipeline.py                 Yakala->OCR->Cevir akisi (QThread)
ui/
  popup_window.py             Sonuc popup'i
  tray_icon.py                 Sistem tepsisi
  loading_indicator.py        Isleniyor durumu gostergesi
utils/
  dpi_utils.py                 Windows DPI scaling duzeltmeleri
  logger.py                    Merkezi loglama (logs/app.log)
  model_check.py               Model kurulum kontrolu (argos-translate)
```

## Bilinen Riskler / Sorun Giderme

| Belirti | Olasi Neden | Cozum |
|---|---|---|
| "Python 3.11 bulunamadi" | Sistemde farkli Python surumu | python.org'dan 3.11 kurun |
| Secilen bolge ile yakalanan goruntu uyusmuyor | DPI scaling (%125/%150) | `utils/dpi_utils.py` bu sorunu cozmek icin var; hala sorun varsa `logs/app.log`'a bakin |
| Kisayol calismiyor | pynput izin/engelleme sorunu | Uygulamayi yonetici olarak calistirmayi deneyin |
| Popup hic acilmiyor, hata da yok | Antivirus ekran yakalamayi engelliyor olabilir | `logs/app.log` icindeki "capture" hatalarina bakin |
| Ilk calistirmada uzun surede yanit yok | RapidOCR modeli henuz inmemis (ilk kullanimda otomatik iner) | Internet baglantisini kontrol edin, birkac saniye bekleyin |
| SSL sertifika hatasi (argos-translate model indirirken) | Sistem saati yanlis / antivirus SSL taramasi | Saat/tarihi duzeltin, antivirus SSL taramasini gecici kapatin |

Hatalarin tumu `logs/app.log` dosyasina yazilir; bir sorun oldugunda
oncelikle bu dosyayi kontrol edin. `logs/app.log` icinde ayrica hangi
ONNXRuntime execution provider'inin (CPU) kullanildigi da loglanir.

