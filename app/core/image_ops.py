"""Pure image operations (safe to call from worker threads)."""
from __future__ import annotations

from PIL import Image, ImageEnhance, ImageFilter, ImageOps


def apply_filter(img: Image.Image, code: str) -> Image.Image:
    img = img.copy()
    if code == "BLUR":
        return img.filter(ImageFilter.GaussianBlur(radius=2))
    if code == "CONTOUR":
        return img.filter(ImageFilter.CONTOUR)
    if code == "DETAIL":
        return img.filter(ImageFilter.DETAIL)
    if code == "EMBOSS":
        return img.filter(ImageFilter.EMBOSS)
    if code == "SHARPEN":
        return img.filter(ImageFilter.SHARPEN)
    if code == "GRAYSCALE":
        return ImageOps.grayscale(img).convert("RGB")
    if code == "SEPIA":
        return _sepia(img)
    if code == "NEGATIVE":
        return ImageOps.invert(img.convert("RGB"))
    if code == "VINTAGE":
        img = ImageEnhance.Color(img).enhance(0.65)
        img = ImageEnhance.Contrast(img).enhance(1.15)
        return ImageOps.autocontrast(img, cutoff=1)
    if code == "ENHANCE_SOFT":
        img = ImageEnhance.Sharpness(img).enhance(1.25)
        return ImageEnhance.Contrast(img).enhance(1.1)
    if code == "ENHANCE_STRONG":
        img = ImageEnhance.Sharpness(img).enhance(1.7)
        img = ImageEnhance.Contrast(img).enhance(1.25)
        return ImageEnhance.Color(img).enhance(1.1)
    if code == "COLOR_UP":
        return ImageEnhance.Color(img).enhance(1.4)
    if code == "COLOR_DOWN":
        return ImageEnhance.Color(img).enhance(0.65)
    if code == "ROTATE_90":
        return img.transpose(Image.Transpose.ROTATE_270)
    if code == "ROTATE_180":
        return img.transpose(Image.Transpose.ROTATE_180)
    if code == "ROTATE_270":
        return img.transpose(Image.Transpose.ROTATE_90)
    if code == "FLIP_H":
        return ImageOps.mirror(img)
    if code == "FLIP_V":
        return ImageOps.flip(img)
    if code == "RESIZE_HALF":
        w, h = img.size
        return img.resize((max(1, w // 2), max(1, h // 2)), Image.Resampling.LANCZOS)
    if code == "RESIZE_DOUBLE":
        w, h = img.size
        if w * 2 > 8000 or h * 2 > 8000:
            return img
        return img.resize((w * 2, h * 2), Image.Resampling.LANCZOS)
    if code == "AUTO_ENHANCE":
        img = ImageOps.autocontrast(img, cutoff=2)
        img = ImageEnhance.Color(img).enhance(1.12)
        return ImageEnhance.Sharpness(img).enhance(1.2)
    return img


def apply_brightness_contrast(
    img: Image.Image, brightness: int, contrast: int
) -> Image.Image:
    """brightness/contrast in range -100..100 relative to base image."""
    out = img.copy()
    if brightness:
        out = ImageEnhance.Brightness(out).enhance(1.0 + brightness / 100.0)
    if contrast:
        out = ImageEnhance.Contrast(out).enhance(1.0 + contrast / 100.0)
    return out


def crop_box(img: Image.Image, left: int, top: int, right: int, bottom: int) -> Image.Image:
    w, h = img.size
    left = max(0, min(int(left), w - 1))
    top = max(0, min(int(top), h - 1))
    right = max(left + 1, min(int(right), w))
    bottom = max(top + 1, min(int(bottom), h))
    return img.crop((left, top, right, bottom))


def _sepia(img: Image.Image) -> Image.Image:
    img = img.convert("RGB")
    px = img.load()
    for y in range(img.height):
        for x in range(img.width):
            r, g, b = px[x, y]
            tr = min(255, int(0.393 * r + 0.769 * g + 0.189 * b))
            tg = min(255, int(0.349 * r + 0.686 * g + 0.168 * b))
            tb = min(255, int(0.272 * r + 0.534 * g + 0.131 * b))
            px[x, y] = (tr, tg, tb)
    return img
