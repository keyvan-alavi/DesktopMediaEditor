# Desktop Media Editor

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![PyQt6](https://img.shields.io/badge/GUI-PyQt6-green?logo=qt&logoColor=white)](https://www.riverbankcomputing.com/software/pyqt/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Release](https://img.shields.io/badge/Release-v0.4.1-orange?logo=github)](https://github.com/keyvan-alavi/DesktopMediaEditor/releases)

**ویرایشگر رسانه دسکتاپ** – نرم‌افزار سبک و دو زبانه (فارسی / انگلیسی) برای ویرایش تصویر و ویدیو.

> در ارتقای این نسخه جدید از **Grok** (نسخه رایگان) نیز استفاده شده است.

---

## ✨ امکانات نسخه ۰.۴ / Features of v0.4

### ویرایش تصویر
- باز کردن و ذخیره (PNG, JPG, WebP و ...)
- **Undo / Redo** (تا ۳۰ مرحله) + دکمه «حذف آخرین فیلتر»
- اسلایدرهای زنده روشنایی و کنتراست (با رها کردن اسلایدر ذخیره می‌شود – بدون دکمه اعمال)
- **مقایسه قبل/بعد** (ویرایش‌شده ↔ اصلی) + بندانگشتی اصلی
- فیلترها: Blur, Contour, Detail, Emboss, Sharpen, Grayscale, Sepia, Negative, Vintage
- وضوح نرم / قوی، اشباع رنگ، **بهبود خودکار** (متفاوت از وضوح)
- چرخش و آینه با کیفیت بالا (بدون افت محسوس)
- تغییر اندازه با الگوریتم LANCZOS
- **برش دستی**: کاربر خودش با ماوس کادر را انتخاب می‌کند (دیگر برش خودکار مرکزی نیست)
- پردازش فیلترها در پس‌زمینه → دیگر با استفاده پشت‌سرهم هنگ نمی‌کند

### ویرایش ویدیو
- برش زمانی + استخراج MP3
- پیش‌نمایش فریم

### رابط کاربری
- پنل ابزارها به صورت **کارت‌های مستقل** جدا از بوم (Canvas)
- تم‌های کامل Default / Dark / Blue / Green
- منو + نوار وضعیت

---

## 🚀 نصب

```bash
git clone https://github.com/keyvan-alavi/DesktopMediaEditor.git
cd DesktopMediaEditor
pip install -r requirements.txt
python main.py
```

نیاز: Python 3.9+ ، PyQt6 ، Pillow ، moviepy ، numpy  
FFmpeg: در پوشه `ffmpeg/` یا در PATH سیستم.

---

## 📦 ساخت و Release

```bash
pip install pyinstaller
pyinstaller --noconfirm build.spec
```

برای انتشار خودکار:
```bash
git tag v0.4.1
git push origin v0.4.1
```

---

## 📜 مجوز

MIT – جزئیات در `LICENSE`.

---

## English

**v0.4.1:** Independent tool cards separate from canvas, interactive mouse crop (no more automatic center crop), high-quality rotate/resize (LANCZOS / transpose), non-blocking filter processing (no freeze), live brightness/contrast auto-commits on slider release, “remove last filter” button, clearer tool naming (soft/strong enhance vs auto-enhance).

> This upgrade was also assisted by **Grok** (free version).
