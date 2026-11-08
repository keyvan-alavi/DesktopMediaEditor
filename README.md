# Desktop Media Editor

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![PyQt6](https://img.shields.io/badge/GUI-PyQt6-green?logo=qt&logoColor=white)](https://www.riverbankcomputing.com/software/pyqt/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Release](https://img.shields.io/badge/Release-v0.3.0-orange?logo=github)](https://github.com/keyvan-alavi/DesktopMediaEditor/releases)

**ویرایشگر رسانه دسکتاپ** – نرم‌افزار سبک و دو زبانه (فارسی / انگلیسی) برای ویرایش پایه تصویر و ویدیو.

> در ارتقای این نسخه جدید از **Grok** (نسخه رایگان) نیز استفاده شده است.

---

## ✨ امکانات نسخه ۰.۳ / Features of v0.3

### ویرایش تصویر / Image Editing
- باز کردن و ذخیره تصویر (PNG, JPG, WebP و ...)
- **Undo / Redo** (تا ۲۵ مرحله)
- اسلایدرهای زنده **روشنایی** و **کنتراست**
- **مقایسه قبل/بعد**: دکمه «اصلی» و «پیش‌نمایش» + تصویر بندانگشتی اصلی
- فیلترهای کلاسیک: Blur, Contour, Detail, Emboss, Sharpen, Grayscale, Sepia, Negative, Vintage
- بهبود کیفیت و تنظیم رنگ
- چرخش، **آینه افقی/عمودی**، تغییر اندازه
- **ابزار حرفه‌ای جدید**:
  - بهبود خودکار (Auto Enhance)
  - برش مرکزی با نسبت‌های مربع / ۱۶:۹ / ۴:۳

### ویرایش ویدیو / Video Editing
- برش ویدیو بر اساس بازه زمانی (HH:MM:SS)
- استخراج صدا به MP3
- پیش‌نمایش فریم و نمایش مدت‌زمان

### رابط کاربری / User Interface
- چیدمان **کارت‌محور** (هر گروه ابزار داخل کادر مستقل)
- طراحی مدرن‌تر و حس نرم‌افزارهای حرفه‌ای
- چهار تم کامل: Default, Dark, Blue, Green
- منوی بالا + نوار وضعیت + Tooltip

### فنی / Technical
- تشخیص خودکار FFmpeg
- آماده برای بسته‌بندی با PyInstaller
- GitHub Actions برای ساخت و انتشار خودکار Release

---

## 🚀 نصب و اجرا / Installation & Run

```bash
git clone https://github.com/keyvan-alavi/DesktopMediaEditor.git
cd DesktopMediaEditor
pip install -r requirements.txt
python main.py
```

**نیازمندی‌ها:** Python 3.9+ ، PyQt6 ، Pillow ، moviepy ، opencv-python-headless ، numpy  
**FFmpeg:** در پوشه `ffmpeg/` قرار دهید یا در PATH سیستم نصب کنید.

---

## 📦 ساخت نسخه قابل نصب و انتشار Release

### ساخت دستی
```bash
pip install pyinstaller
pyinstaller --noconfirm build.spec
```
خروجی: `dist/DesktopMediaEditor.exe`

### انتشار خودکار روی GitHub Releases
```bash
git add .
git commit -m "Release v0.3.0"
git push origin main

git tag v0.3.0
git push origin v0.3.0
```
بعد از push کردن تگ، GitHub Actions بیلد می‌گیرد و فایل را در صفحه **Releases** قرار می‌دهد.

---

## 📂 ساختار پروژه

```
DesktopMediaEditor/
├── main.py
├── build.spec
├── requirements.txt
├── CHANGELOG.md
├── LICENSE
├── edit.ico
├── ffmpeg/
└── .github/workflows/release.yml
```

---

## 🗺 نقشه راه

- [ ] ابزار Crop آزاد با انتخاب ناحیه ماوس
- [ ] پردازش دسته‌ای (Batch)
- [ ] سوئیچر زبان کامل
- [ ] واترمارک متن/لوگو
- [ ] بیلد لینوکس و مک

---

## 📜 مجوز / License

MIT License – جزئیات در فایل `LICENSE`.

---

## English Overview

**Desktop Media Editor** v0.3.0 – lightweight bilingual image & video editor.

**New in 0.3:** Independent tool cards, before/after comparison (Original ↔ Preview), Flip H/V, Auto Enhance, center crop ratios (1:1, 16:9, 4:3), refined professional UI.

> This new version upgrade was also assisted by **Grok** (free version).
