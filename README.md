# Desktop Media Editor

**Version 0.2.0** | Python 3.9+ | PyQt6 | MIT License

**ویرایشگر رسانه دسکتاپ** – یک نرم‌افزار سبک و دو زبانه (فارسی / انگلیسی) برای ویرایش پایه تصویر و ویدیو.

> در ارتقای این نسخه جدید از **Grok** (نسخه رایگان) نیز استفاده شده است.

---

## ✨ امکانات نسخه ۰.۲ / Features of v0.2

### ویرایش تصویر / Image Editing
- باز کردن و ذخیره تصویر (PNG, JPG, WebP و ...)
- **Undo / Redo** (تا ۲۰ مرحله)
- اسلایدرهای زنده **روشنایی** و **کنتراست**
- فیلترهای کلاسیک: Blur, Contour, Detail, Emboss, Sharpen, Grayscale, Sepia, Negative, Vintage
- بهبود کیفیت و تنظیم رنگ
- چرخش (۹۰° / ۱۸۰° / ۲۷۰°) و تغییر اندازه
- بازنشانی به تصویر اصلی

### ویرایش ویدیو / Video Editing
- برش ویدیو بر اساس بازه زمانی (HH:MM:SS)
- استخراج صدا به MP3 با کیفیت خوب
- پیش‌نمایش فریم و نمایش مدت‌زمان

### رابط کاربری / User Interface
- طراحی مدرن‌تر با آیکون‌های نمادین
- چهار تم: Default, Dark, Blue, Green
- تنظیم اندازه فونت
- نوار وضعیت (Status Bar)
- Tooltip روی دکمه‌ها

### فنی / Technical
- تشخیص خودکار FFmpeg (پوشه محلی یا سیستم)
- ذخیره‌سازی تنظیمات با QSettings
- آماده برای بسته‌بندی با PyInstaller
- GitHub Actions برای ساخت خودکار و انتشار Release

---

## 🚀 نصب و اجرا / Installation & Run

```bash
# کلون کردن / Clone
git clone https://github.com/keyvan-alavi/DesktopMediaEditor.git
cd DesktopMediaEditor

# نصب وابستگی‌ها / Install dependencies
pip install -r requirements.txt

# اجرا / Run
python main.py
```

**نیازمندی‌ها / Requirements:**
- Python 3.9+
- PyQt6, Pillow, moviepy, opencv-python-headless, numpy
- FFmpeg (برای قابلیت‌های ویدیو) – یا در پوشه `ffmpeg/` قرار دهید یا در PATH سیستم نصب کنید.

---

## 📦 ساخت نسخه قابل نصب و انتشار Release

### ۱. ساخت دستی (روی سیستم خودتان)
```bash
pip install pyinstaller
pyinstaller --noconfirm build.spec
```
خروجی: `dist/DesktopMediaEditor.exe`

### ۲. انتشار خودکار روی GitHub Releases

برای اینکه Release ساخته شود، باید **تگ** بزنید:

```bash
# مطمئن شوید همه تغییرات push شده
git add .
git commit -m "Release v0.2.0"
git push origin main   # یا master

# سپس تگ بزنید و push کنید
git tag v0.2.0
git push origin v0.2.0
```

بعد از push کردن تگ `v0.2.0`، GitHub Actions به صورت خودکار:
1. برنامه را با PyInstaller روی ویندوز می‌سازد
2. فایل `.exe` را به عنوان Artifact آپلود می‌کند
3. یک **Release** جدید در صفحه Releases گیت‌هاب ایجاد می‌کند و فایل را ضمیمه می‌کند

**نکته مهم:**  
- Actions باید در تنظیمات ریپازیتوری فعال باشد.  
- اگر برای اولین بار است، ممکن است چند دقیقه طول بکشد تا workflow اجرا شود.  
- می‌توانید از تب Actions وضعیت بیلد را ببینید.

اگر تگ را قبلاً زده‌اید و می‌خواهید دوباره بیلد بگیرید، تگ را پاک کنید و دوباره بزنید، یا از `workflow_dispatch` در Actions استفاده کنید.

---

## 📂 ساختار پروژه / Project Structure

```
DesktopMediaEditor/
├── main.py                 # کد اصلی برنامه
├── build.spec              # تنظیمات PyInstaller
├── requirements.txt
├── CHANGELOG.md
├── LICENSE
├── edit.ico
├── ffmpeg/                 # (اختیاری) باینری‌های FFmpeg
└── .github/workflows/
    └── release.yml         # ساخت و انتشار خودکار
```

---

## 🗺 نقشه راه (آینده) / Roadmap

- [ ] ابزار Crop با انتخاب ناحیه
- [ ] پردازش دسته‌ای (Batch)
- [ ] سوئیچر زبان کامل (فارسی ↔ انگلیسی)
- [ ] افزودن واترمارک
- [ ] تبدیل فرمت تصویر/ویدیو
- [ ] بیلد لینوکس و مک
- [ ] ماژولار کردن کد

---

## 📜 مجوز / License

این پروژه تحت مجوز **MIT** منتشر شده است. جزئیات در فایل `LICENSE`.

This project is licensed under the **MIT License** – see the `LICENSE` file for details.

---

## English Overview

**Desktop Media Editor** is a lightweight bilingual (Persian/English) desktop application for basic image and video editing, built with Python and PyQt6.

**v0.2.0 highlights:**
- Undo / Redo (up to 20 steps)
- Live Brightness & Contrast sliders
- More modern UI with symbolic icons
- Better cross-platform FFmpeg detection
- Packaging support (PyInstaller) + GitHub Actions for automatic Releases

> This new version upgrade was also assisted by **Grok** (free version).
