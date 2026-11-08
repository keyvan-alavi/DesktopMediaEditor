"""Main application window."""
from __future__ import annotations

import shutil
import time
from pathlib import Path

from moviepy import VideoFileClip
from PIL import Image
from PyQt6.QtCore import Qt, QSettings, QSize
from PyQt6.QtGui import QPixmap, QIcon, QAction
from PyQt6.QtWidgets import (
    QMainWindow, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QLineEdit, QFileDialog, QProgressBar, QMessageBox, QSplitter,
    QGridLayout, QSizePolicy, QComboBox, QSpinBox, QSlider, QStatusBar,
    QFrame, QScrollArea,
)

from app import __version__
from app.core.ffmpeg_utils import setup_moviepy_env, find_ffmpeg
from app.core.image_ops import apply_brightness_contrast, crop_box
from app.core.workers import ProgressThread
from app.ui.preview import PreviewLabel
from app.ui.styles import THEMES, build_stylesheet

APP_NAME = "Desktop Media Editor"
ORG_NAME = "KeyvanAlavi"
CACHE_DIR = Path("cache")
CACHE_DIR.mkdir(exist_ok=True)

FFMPEG_PATH, _ = setup_moviepy_env()


def make_btn(text: str, tooltip: str = "", primary: bool = True) -> QPushButton:
    btn = QPushButton(text)
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    if tooltip:
        btn.setToolTip(tooltip)
    btn.setMinimumHeight(30)
    btn.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
    if not primary:
        btn.setObjectName("secondaryBtn")
    return btn


class MediaEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME}  v{__version__}")
        icon_path = Path(__file__).resolve().parent.parent.parent / "edit.ico"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))
        self.setGeometry(60, 30, 1240, 760)
        self.setMinimumSize(880, 560)

        self.settings = QSettings(ORG_NAME, "MediaEditor")
        self.theme = self.settings.value("theme", "Default", type=str)
        self.font_size = self.settings.value("font_size", 13, type=int)

        self.filters = [
            ("🌫️ Blur", "BLUR"), ("📐 Contour", "CONTOUR"), ("✨ Detail", "DETAIL"),
            ("🗿 Emboss", "EMBOSS"), ("🔪 Sharpen", "SHARPEN"), ("⬛ Grayscale", "GRAYSCALE"),
            ("🟤 Sepia", "SEPIA"), ("🔄 Negative", "NEGATIVE"), ("📷 Vintage", "VINTAGE"),
        ]
        self.quality_buttons = [
            ("✦ نرم", "ENHANCE_SOFT"),
            ("✦ قوی", "ENHANCE_STRONG"),
            ("🎨 اشباع+", "COLOR_UP"),
            ("🎨 اشباع−", "COLOR_DOWN"),
        ]

        self.original_image: Image.Image | None = None
        self.current_image: Image.Image | None = None
        self.current_image_path: str | None = None
        self.history: list[Image.Image] = []
        self.history_index = -1
        self.max_history = 30
        self.show_original = False
        self._busy = False
        self._crop_active = False

        self.current_video_path: str | None = None
        self.video_duration = 0.0
        self._filter_thread: ProgressThread | None = None

        self.apply_theme()
        self._build_menubar()
        self._build_ui()
        self._update_undo_redo_buttons()

        msg = f"آماده  •  v{__version__}"
        if FFMPEG_PATH:
            msg += f"  •  FFmpeg: {Path(FFMPEG_PATH).name}"
        else:
            msg += "  •  ⚠ FFmpeg نیست"
        self.statusBar().showMessage(msg, 7000)

    # ----- theme -----
    def apply_theme(self):
        self.setStyleSheet(build_stylesheet(self.theme, self.font_size))

    def save_settings(self):
        self.settings.setValue("theme", self.theme)
        self.settings.setValue("font_size", self.font_size)
        self.apply_theme()
        self.statusBar().showMessage("✓ تنظیمات ذخیره شد", 2000)

    # ----- menu -----
    def _build_menubar(self):
        mb = self.menuBar()
        file_m = mb.addMenu("📁 فایل")
        for text, slot in (
            ("🖼 باز کردن تصویر", self.open_image),
            ("🎬 باز کردن ویدیو", self.open_video),
            (None, None),
            ("💾 ذخیره تصویر", self.save_image),
            (None, None),
            ("خروج", self.close),
        ):
            if text is None:
                file_m.addSeparator()
            else:
                a = QAction(text, self)
                a.triggered.connect(slot)
                file_m.addAction(a)

        edit_m = mb.addMenu("✏ ویرایش")
        for text, slot in (
            ("↩ Undo", self.undo),
            ("↪ Redo", self.redo),
            (None, None),
            ("↺ بازنشانی کامل", self.reset_image),
        ):
            if text is None:
                edit_m.addSeparator()
            else:
                a = QAction(text, self)
                a.triggered.connect(slot)
                edit_m.addAction(a)

        help_m = mb.addMenu("❓ راهنما")
        a = QAction("درباره", self)
        a.triggered.connect(self.show_about)
        help_m.addAction(a)

    def show_about(self):
        QMessageBox.about(
            self, "درباره برنامه",
            f"<h3>{APP_NAME}</h3>"
            f"<p>نسخه: <b>{__version__}</b></p>"
            "<p>ویرایشگر تصویر و ویدیو با رابط دو زبانه.</p>"
            "<p>توسعه‌دهنده: Keyvan Alavi</p>",
        )

    # ----- cards -----
    def _make_card(self, title: str):
        card = QFrame()
        card.setObjectName("toolCard")
        outer = QVBoxLayout(card)
        outer.setContentsMargins(12, 12, 12, 12)
        outer.setSpacing(8)
        title_lbl = QLabel(title)
        title_lbl.setObjectName("cardTitle")
        outer.addWidget(title_lbl)
        content = QVBoxLayout()
        content.setSpacing(6)
        outer.addLayout(content)
        return card, content

    def _build_ui(self):
        self.tab_widget = QTabWidget()
        self.setCentralWidget(self.tab_widget)
        self.image_tab = QWidget()
        self.video_tab = QWidget()
        self.settings_tab = QWidget()
        self.tab_widget.addTab(self.image_tab, "🖼  ویرایش تصویر")
        self.tab_widget.addTab(self.video_tab, "🎬  ویرایش ویدیو")
        self.tab_widget.addTab(self.settings_tab, "⚙  تنظیمات")
        self._init_image_tab()
        self._init_video_tab()
        self._init_settings_tab()
        self.setStatusBar(QStatusBar())

    def _init_image_tab(self):
        root = QHBoxLayout(self.image_tab)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(12)
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Sidebar tools
        sidebar = QFrame()
        sidebar.setObjectName("sidebarFrame")
        side_outer = QVBoxLayout(sidebar)
        side_outer.setContentsMargins(8, 8, 8, 8)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        content = QWidget()
        left = QVBoxLayout(content)
        left.setContentsMargins(4, 4, 4, 4)
        left.setSpacing(10)

        card, lay = self._make_card("📁 فایل")
        row = QHBoxLayout()
        self.btn_open = make_btn("📂 باز کردن")
        self.btn_open.clicked.connect(self.open_image)
        self.btn_save = make_btn("💾 ذخیره")
        self.btn_save.clicked.connect(self.save_image)
        self.btn_save.setEnabled(False)
        row.addWidget(self.btn_open)
        row.addWidget(self.btn_save)
        lay.addLayout(row)
        left.addWidget(card)

        card, lay = self._make_card("🕒 تاریخچه")
        row = QHBoxLayout()
        self.btn_undo = make_btn("↩ Undo")
        self.btn_undo.clicked.connect(self.undo)
        self.btn_redo = make_btn("↪ Redo")
        self.btn_redo.clicked.connect(self.redo)
        self.btn_reset = make_btn("↺ اصلی", primary=False)
        self.btn_reset.clicked.connect(self.reset_image)
        row.addWidget(self.btn_undo)
        row.addWidget(self.btn_redo)
        row.addWidget(self.btn_reset)
        lay.addLayout(row)
        left.addWidget(card)

        card, lay = self._make_card("👁 مقایسه")
        row = QHBoxLayout()
        self.btn_view_edit = make_btn("ویرایش‌شده")
        self.btn_view_edit.clicked.connect(lambda: self._set_compare(False))
        self.btn_view_orig = make_btn("اصلی", primary=False)
        self.btn_view_orig.clicked.connect(lambda: self._set_compare(True))
        row.addWidget(self.btn_view_edit)
        row.addWidget(self.btn_view_orig)
        lay.addLayout(row)
        left.addWidget(card)

        card, lay = self._make_card("🎚 روشنایی و کنتراست")
        br = QHBoxLayout()
        br.addWidget(QLabel("☀"))
        self.brightness_slider = QSlider(Qt.Orientation.Horizontal)
        self.brightness_slider.setRange(-100, 100)
        self.brightness_slider.valueChanged.connect(self._on_live_preview)
        self.brightness_slider.sliderReleased.connect(self._commit_live_adjust)
        self.brightness_value = QLabel("0")
        self.brightness_value.setFixedWidth(28)
        self.brightness_value.setAlignment(Qt.AlignmentFlag.AlignCenter)
        br.addWidget(self.brightness_slider)
        br.addWidget(self.brightness_value)
        lay.addLayout(br)
        ct = QHBoxLayout()
        ct.addWidget(QLabel("◐"))
        self.contrast_slider = QSlider(Qt.Orientation.Horizontal)
        self.contrast_slider.setRange(-100, 100)
        self.contrast_slider.valueChanged.connect(self._on_live_preview)
        self.contrast_slider.sliderReleased.connect(self._commit_live_adjust)
        self.contrast_value = QLabel("0")
        self.contrast_value.setFixedWidth(28)
        self.contrast_value.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ct.addWidget(self.contrast_slider)
        ct.addWidget(self.contrast_value)
        lay.addLayout(ct)
        hint = QLabel("با رها کردن اسلایدر ذخیره می‌شود")
        hint.setObjectName("mutedLabel")
        hint.setWordWrap(True)
        lay.addWidget(hint)
        left.addWidget(card)

        card, lay = self._make_card("✨ فیلترها")
        grid = QGridLayout()
        grid.setSpacing(6)
        for i, (name, code) in enumerate(self.filters):
            btn = make_btn(name)
            btn.clicked.connect(lambda _, c=code: self.apply_filter_async(c))
            grid.addWidget(btn, i // 3, i % 3)
        lay.addLayout(grid)
        self.btn_remove_last = make_btn("⌫ حذف آخرین فیلتر", primary=False)
        self.btn_remove_last.setObjectName("dangerBtn")
        self.btn_remove_last.clicked.connect(self.undo)
        lay.addWidget(self.btn_remove_last)
        left.addWidget(card)

        card, lay = self._make_card("🔧 وضوح و رنگ")
        grid = QGridLayout()
        grid.setSpacing(6)
        for i, (name, code) in enumerate(self.quality_buttons):
            btn = make_btn(name)
            btn.clicked.connect(lambda _, c=code: self.apply_filter_async(c))
            grid.addWidget(btn, i // 2, i % 2)
        lay.addLayout(grid)
        btn_auto = make_btn("★ بهبود خودکار", "متفاوت از وضوح نرم/قوی")
        btn_auto.clicked.connect(lambda: self.apply_filter_async("AUTO_ENHANCE"))
        lay.addWidget(btn_auto)
        left.addWidget(card)

        card, lay = self._make_card("🔄 چرخش و آینه")
        rot = QHBoxLayout()
        for name, code in (("↻ ۹۰°", "ROTATE_90"), ("⟳ ۱۸۰°", "ROTATE_180"), ("↺ ۲۷۰°", "ROTATE_270")):
            btn = make_btn(name)
            btn.clicked.connect(lambda _, c=code: self.apply_filter_async(c))
            rot.addWidget(btn)
        lay.addLayout(rot)
        flip = QHBoxLayout()
        for name, code in (("↔ افقی", "FLIP_H"), ("↕ عمودی", "FLIP_V")):
            btn = make_btn(name)
            btn.clicked.connect(lambda _, c=code: self.apply_filter_async(c))
            flip.addWidget(btn)
        lay.addLayout(flip)
        left.addWidget(card)

        card, lay = self._make_card("📐 اندازه")
        row = QHBoxLayout()
        btn_s = make_btn("⬇ نصف")
        btn_s.clicked.connect(lambda: self.apply_filter_async("RESIZE_HALF"))
        btn_l = make_btn("⬆ دو برابر")
        btn_l.clicked.connect(lambda: self.apply_filter_async("RESIZE_DOUBLE"))
        row.addWidget(btn_s)
        row.addWidget(btn_l)
        lay.addLayout(row)
        left.addWidget(card)

        card, lay = self._make_card("✂ برش دستی")
        self.btn_crop = make_btn("✂ شروع برش")
        self.btn_crop.clicked.connect(self.toggle_crop_mode)
        lay.addWidget(self.btn_crop)
        self.crop_hint = QLabel("روی تصویر بکشید و رها کنید")
        self.crop_hint.setObjectName("mutedLabel")
        self.crop_hint.setWordWrap(True)
        lay.addWidget(self.crop_hint)
        left.addWidget(card)

        left.addStretch()
        scroll.setWidget(content)
        side_outer.addWidget(scroll)
        splitter.addWidget(sidebar)

        # Canvas
        canvas = QFrame()
        canvas.setObjectName("canvasFrame")
        canvas_l = QVBoxLayout(canvas)
        canvas_l.setContentsMargins(10, 10, 10, 10)
        canvas_l.setSpacing(8)
        self.preview_title = QLabel("بوم پیش‌نمایش")
        self.preview_title.setObjectName("cardTitle")
        canvas_l.addWidget(self.preview_title)

        preview_frame = QFrame()
        preview_frame.setObjectName("previewFrame")
        pf = QVBoxLayout(preview_frame)
        pf.setContentsMargins(8, 8, 8, 8)
        self.image_preview = PreviewLabel()
        self.image_preview.setText("تصویری انتخاب نشده\n\n«باز کردن» را بزنید")
        self.image_preview.crop_done.connect(self._on_crop_done)
        pf.addWidget(self.image_preview)
        canvas_l.addWidget(preview_frame, stretch=1)

        thumb_row = QHBoxLayout()
        thumb_lbl = QLabel("اصلی:")
        thumb_lbl.setObjectName("mutedLabel")
        thumb_row.addWidget(thumb_lbl)
        self.original_thumb = QLabel("—")
        self.original_thumb.setObjectName("placeholderLabel")
        self.original_thumb.setFixedSize(140, 88)
        self.original_thumb.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.original_thumb.setStyleSheet("border: 1px dashed #94a3b8; border-radius: 8px;")
        thumb_row.addWidget(self.original_thumb)
        thumb_row.addStretch()
        self.busy_label = QLabel("")
        self.busy_label.setObjectName("mutedLabel")
        thumb_row.addWidget(self.busy_label)
        canvas_l.addLayout(thumb_row)

        splitter.addWidget(canvas)
        splitter.setStretchFactor(0, 34)
        splitter.setStretchFactor(1, 66)
        splitter.setSizes([380, 720])
        root.addWidget(splitter)
        self._update_compare_buttons()

    def _init_video_tab(self):
        root = QHBoxLayout(self.video_tab)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(12)
        splitter = QSplitter(Qt.Orientation.Horizontal)

        sidebar = QFrame()
        sidebar.setObjectName("sidebarFrame")
        left = QVBoxLayout(sidebar)
        left.setContentsMargins(10, 10, 10, 10)
        left.setSpacing(10)

        card, lay = self._make_card("📁 ویدیو")
        self.btn_open_video = make_btn("📂 باز کردن ویدیو")
        self.btn_open_video.clicked.connect(self.open_video)
        lay.addWidget(self.btn_open_video)
        self.video_info_label = QLabel("ویدیویی انتخاب نشده")
        self.video_info_label.setObjectName("mutedLabel")
        self.video_info_label.setWordWrap(True)
        lay.addWidget(self.video_info_label)
        left.addWidget(card)

        card, lay = self._make_card("✂ برش")
        r1 = QHBoxLayout()
        r1.addWidget(QLabel("شروع"))
        self.trim_start_input = QLineEdit("00:00:00")
        r1.addWidget(self.trim_start_input)
        lay.addLayout(r1)
        r2 = QHBoxLayout()
        r2.addWidget(QLabel("پایان"))
        self.trim_end_input = QLineEdit("00:00:10")
        r2.addWidget(self.trim_end_input)
        lay.addLayout(r2)
        self.btn_trim = make_btn("✂ برش و ذخیره")
        self.btn_trim.clicked.connect(self.start_trim_video)
        lay.addWidget(self.btn_trim)
        left.addWidget(card)

        card, lay = self._make_card("🎵 صدا")
        self.btn_mp3 = make_btn("🎵 تبدیل به MP3")
        self.btn_mp3.clicked.connect(self.start_convert_to_mp3)
        lay.addWidget(self.btn_mp3)
        left.addWidget(card)

        self.video_progress = QProgressBar()
        self.video_progress.setVisible(False)
        left.addWidget(self.video_progress)
        left.addStretch()
        splitter.addWidget(sidebar)

        canvas = QFrame()
        canvas.setObjectName("canvasFrame")
        cl = QVBoxLayout(canvas)
        cl.setContentsMargins(10, 10, 10, 10)
        pf = QFrame()
        pf.setObjectName("previewFrame")
        pfl = QVBoxLayout(pf)
        self.video_preview_label = QLabel("ویدیویی انتخاب نشده")
        self.video_preview_label.setObjectName("placeholderLabel")
        self.video_preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_preview_label.setMinimumSize(280, 220)
        self.video_preview_label.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        pfl.addWidget(self.video_preview_label)
        cl.addWidget(pf)
        splitter.addWidget(canvas)
        splitter.setStretchFactor(0, 34)
        splitter.setStretchFactor(1, 66)
        root.addWidget(splitter)

    def _init_settings_tab(self):
        layout = QVBoxLayout(self.settings_tab)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(14)

        card, lay = self._make_card("🎨 تم و ظاهر")
        r1 = QHBoxLayout()
        r1.addWidget(QLabel("تم:"))
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(list(THEMES.keys()))
        self.theme_combo.setCurrentText(self.theme)
        self.theme_combo.currentTextChanged.connect(self._on_theme_changed)
        r1.addWidget(self.theme_combo)
        r1.addStretch()
        lay.addLayout(r1)
        r2 = QHBoxLayout()
        r2.addWidget(QLabel("فونت:"))
        self.font_spin = QSpinBox()
        self.font_spin.setRange(10, 20)
        self.font_spin.setValue(self.font_size)
        self.font_spin.valueChanged.connect(self._on_font_changed)
        r2.addWidget(self.font_spin)
        r2.addStretch()
        lay.addLayout(r2)
        layout.addWidget(card)

        card, lay = self._make_card("ℹ درباره")
        about = QLabel(
            f"<b>{APP_NAME}</b><br>نسخه: <b>{__version__}</b><br><br>"
            "ویرایشگر تصویر و ویدیو با رابط دو زبانه.<br>"
            "توسعه‌دهنده: Keyvan Alavi"
        )
        about.setWordWrap(True)
        about.setTextFormat(Qt.TextFormat.RichText)
        lay.addWidget(about)
        btn = make_btn("🗑 پاک کردن کش", primary=False)
        btn.clicked.connect(self.clear_cache)
        lay.addWidget(btn)
        layout.addWidget(card)
        layout.addStretch()

    def _on_theme_changed(self, name: str):
        self.theme = name
        self.save_settings()

    def _on_font_changed(self, v: int):
        self.font_size = v
        self.save_settings()

    def clear_cache(self):
        try:
            for f in CACHE_DIR.iterdir():
                if f.is_file():
                    f.unlink()
            self.statusBar().showMessage("✓ کش پاک شد", 2500)
        except Exception as e:
            QMessageBox.warning(self, "خطا", str(e))

    # ----- busy / compare -----
    def _set_busy(self, busy: bool):
        self._busy = busy
        self.busy_label.setText("⏳ در حال پردازش..." if busy else "")
        for w in self.findChildren(QPushButton):
            if w not in (self.btn_undo, self.btn_redo):
                w.setEnabled(not busy)
        if not busy:
            self._update_undo_redo_buttons()
            self.btn_save.setEnabled(self.current_image is not None)

    def _set_compare(self, show_orig: bool):
        self.show_original = show_orig
        self._update_compare_buttons()
        self.display_current_image()
        self.preview_title.setText(
            "بوم پیش‌نمایش — اصلی" if show_orig else "بوم پیش‌نمایش — ویرایش‌شده"
        )

    def _update_compare_buttons(self):
        if self.show_original:
            self.btn_view_orig.setObjectName("activeToggle")
            self.btn_view_edit.setObjectName("secondaryBtn")
        else:
            self.btn_view_edit.setObjectName("activeToggle")
            self.btn_view_orig.setObjectName("secondaryBtn")
        self.apply_theme()

    # ----- image -----
    def open_image(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "انتخاب تصویر", "",
            "Images (*.png *.jpg *.jpeg *.bmp *.webp *.tiff);;All (*)",
        )
        if not path:
            return
        try:
            img = Image.open(path).convert("RGB")
            self.original_image = img.copy()
            self.current_image = img.copy()
            self.current_image_path = path
            self.history = [img.copy()]
            self.history_index = 0
            self.show_original = False
            self._exit_crop_mode()
            self._reset_sliders()
            self._update_compare_buttons()
            self.display_current_image()
            self._update_original_thumb()
            self.btn_save.setEnabled(True)
            self._update_undo_redo_buttons()
            self.statusBar().showMessage(f"✓ {Path(path).name}", 4000)
        except Exception as e:
            QMessageBox.warning(self, "خطا", str(e))

    def _update_original_thumb(self):
        if self.original_image is None:
            self.original_thumb.setText("—")
            return
        tmp = CACHE_DIR / f"othumb_{time.time_ns()}.png"
        try:
            t = self.original_image.copy()
            t.thumbnail((140, 88), Image.Resampling.LANCZOS)
            t.save(tmp, "PNG")
            self.original_thumb.setPixmap(QPixmap(str(tmp)))
            tmp.unlink(missing_ok=True)
        except Exception:
            pass

    def display_current_image(self):
        img = (
            self.original_image
            if (self.show_original and self.original_image)
            else self.current_image
        )
        if img is None:
            return
        tmp = CACHE_DIR / f"prev_{time.time_ns()}.png"
        try:
            img.save(tmp, "PNG")
            pix = QPixmap(str(tmp))
            if not pix.isNull():
                self.image_preview.show_pixmap(pix, img.width, img.height)
            tmp.unlink(missing_ok=True)
        except Exception:
            pass

    def _push_history(self, img: Image.Image):
        self.history = self.history[: self.history_index + 1]
        self.history.append(img.copy())
        if len(self.history) > self.max_history:
            self.history.pop(0)
        else:
            self.history_index += 1
        self._update_undo_redo_buttons()

    def _update_undo_redo_buttons(self):
        self.btn_undo.setEnabled(self.history_index > 0 and not self._busy)
        self.btn_redo.setEnabled(
            self.history_index < len(self.history) - 1 and not self._busy
        )
        has = self.current_image is not None
        self.btn_reset.setEnabled(has and not self._busy)
        self.btn_save.setEnabled(has and not self._busy)
        self.btn_remove_last.setEnabled(self.history_index > 0 and not self._busy)

    def undo(self):
        if self.history_index > 0 and not self._busy:
            self.history_index -= 1
            self.current_image = self.history[self.history_index].copy()
            self.show_original = False
            self._reset_sliders()
            self._update_compare_buttons()
            self.display_current_image()
            self._update_undo_redo_buttons()
            self.statusBar().showMessage("↩ Undo", 1200)

    def redo(self):
        if self.history_index < len(self.history) - 1 and not self._busy:
            self.history_index += 1
            self.current_image = self.history[self.history_index].copy()
            self.show_original = False
            self._reset_sliders()
            self._update_compare_buttons()
            self.display_current_image()
            self._update_undo_redo_buttons()
            self.statusBar().showMessage("↪ Redo", 1200)

    def reset_image(self):
        if self.original_image is None or self._busy:
            return
        self.current_image = self.original_image.copy()
        self.history = [self.original_image.copy()]
        self.history_index = 0
        self.show_original = False
        self._exit_crop_mode()
        self._reset_sliders()
        self._update_compare_buttons()
        self.display_current_image()
        self._update_undo_redo_buttons()
        self.statusBar().showMessage("↺ بازگشت به اصلی", 2000)

    def _reset_sliders(self):
        self.brightness_slider.blockSignals(True)
        self.contrast_slider.blockSignals(True)
        self.brightness_slider.setValue(0)
        self.contrast_slider.setValue(0)
        self.brightness_value.setText("0")
        self.contrast_value.setText("0")
        self.brightness_slider.blockSignals(False)
        self.contrast_slider.blockSignals(False)

    def _on_live_preview(self):
        if self.current_image is None or self.history_index < 0:
            return
        base = self.history[self.history_index]
        b = self.brightness_slider.value()
        c = self.contrast_slider.value()
        self.brightness_value.setText(str(b))
        self.contrast_value.setText(str(c))
        self.current_image = apply_brightness_contrast(base, b, c)
        self.show_original = False
        self.display_current_image()

    def _commit_live_adjust(self):
        if self.current_image is None:
            return
        if self.brightness_slider.value() == 0 and self.contrast_slider.value() == 0:
            return
        self._push_history(self.current_image)
        self._reset_sliders()
        self.statusBar().showMessage("✓ تنظیمات ذخیره شد", 1500)

    def apply_filter_async(self, code: str):
        if self.current_image is None:
            QMessageBox.warning(self, "توجه", "ابتدا یک تصویر باز کنید.")
            return
        if self._busy:
            return
        self._exit_crop_mode()
        self._set_busy(True)
        self.show_original = False
        self._update_compare_buttons()
        self._filter_thread = ProgressThread("filter", self.current_image.copy(), code)
        self._filter_thread.finished_signal.connect(self._on_filter_done)
        self._filter_thread.error_signal.connect(
            lambda m: QMessageBox.warning(self, "خطا", m)
        )
        self._filter_thread.start()

    def _on_filter_done(self, result):
        self._set_busy(False)
        if result is None:
            return
        self.current_image = result
        self._push_history(result)
        self._reset_sliders()
        self.display_current_image()
        self.statusBar().showMessage("✓ اعمال شد", 1500)

    # ----- crop (safe) -----
    def toggle_crop_mode(self):
        if self.current_image is None:
            QMessageBox.warning(self, "توجه", "ابتدا یک تصویر باز کنید.")
            return
        if self._crop_active:
            self._exit_crop_mode()
        else:
            self._crop_active = True
            self.image_preview.set_crop_mode(True)
            self.display_current_image()  # refresh paint path
            self.btn_crop.setText("✖ انصراف از برش")
            self.btn_crop.setObjectName("dangerBtn")
            self.apply_theme()
            self.crop_hint.setText("ناحیه را با ماوس بکشید و رها کنید")
            self.statusBar().showMessage("حالت برش فعال", 3000)

    def _exit_crop_mode(self):
        was = self._crop_active
        self._crop_active = False
        self.image_preview.set_crop_mode(False)
        self.btn_crop.setText("✂ شروع برش")
        self.btn_crop.setObjectName("")
        if was:
            self.apply_theme()
            self.display_current_image()
        self.crop_hint.setText("روی تصویر بکشید و رها کنید")

    def _on_crop_done(self, left: int, top: int, right: int, bottom: int):
        """Receive image-space coordinates from PreviewLabel."""
        if self.current_image is None or not self._crop_active:
            self._exit_crop_mode()
            return
        try:
            cropped = crop_box(self.current_image, left, top, right, bottom)
            if cropped.size[0] < 2 or cropped.size[1] < 2:
                self.statusBar().showMessage("ناحیه خیلی کوچک است", 2000)
                self._exit_crop_mode()
                return
            self.current_image = cropped
            self._push_history(cropped)
            self._exit_crop_mode()
            self.display_current_image()
            self.statusBar().showMessage(
                f"✓ برش ({cropped.size[0]}×{cropped.size[1]})", 3000
            )
        except Exception as e:
            self._exit_crop_mode()
            QMessageBox.warning(self, "خطا در برش", str(e))

    def save_image(self):
        if self.current_image is None:
            return
        default = "edited.png"
        if self.current_image_path:
            p = Path(self.current_image_path)
            default = f"{p.stem}_edited{p.suffix}"
        path, _ = QFileDialog.getSaveFileName(
            self, "ذخیره", default,
            "PNG (*.png);;JPEG (*.jpg *.jpeg);;WebP (*.webp);;All (*)",
        )
        if path:
            try:
                self.current_image.save(path)
                self.statusBar().showMessage("✓ ذخیره شد", 3000)
                QMessageBox.information(self, "موفق", f"ذخیره شد:\n{path}")
            except Exception as e:
                QMessageBox.warning(self, "خطا", str(e))

    # ----- video -----
    def open_video(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "انتخاب ویدیو", "",
            "Videos (*.mp4 *.mkv *.avi *.mov *.webm);;All (*)",
        )
        if not path:
            return
        try:
            clip = VideoFileClip(path)
            self.video_duration = clip.duration
            self.current_video_path = path
            thumb = CACHE_DIR / f"vthumb_{time.time_ns()}.png"
            clip.save_frame(str(thumb), t=min(1.0, self.video_duration / 2))
            clip.close()
            self._show_pix(self.video_preview_label, str(thumb))
            mins, secs = divmod(int(self.video_duration), 60)
            hours, mins = divmod(mins, 60)
            self.video_info_label.setText(
                f"<b>{Path(path).name}</b><br>مدت: {hours:02d}:{mins:02d}:{secs:02d}"
            )
            self.trim_end_input.setText(f"{hours:02d}:{mins:02d}:{secs:02d}")
            self.statusBar().showMessage("✓ ویدیو بارگذاری شد", 3000)
        except Exception as e:
            QMessageBox.warning(self, "خطا", str(e))

    def start_trim_video(self):
        if not self.current_video_path:
            QMessageBox.warning(self, "خطا", "ویدیو انتخاب نشده.")
            return
        if not find_ffmpeg():
            QMessageBox.warning(self, "خطا", "FFmpeg پیدا نشد.")
            return
        start = self._parse_time(self.trim_start_input.text())
        end = self._parse_time(self.trim_end_input.text())
        if start is None or end is None or start >= end:
            QMessageBox.warning(self, "خطا", "بازه زمانی نامعتبر است.")
            return
        out = str(CACHE_DIR / f"trim_{time.time_ns()}.mp4")
        self.video_progress.setVisible(True)
        self.video_progress.setValue(0)
        self._set_busy(True)
        self.thread = ProgressThread("trim", self.current_video_path, start, end, out)
        self.thread.progress_signal.connect(self.video_progress.setValue)
        self.thread.finished_signal.connect(self._finish_trim)
        self.thread.error_signal.connect(lambda m: QMessageBox.warning(self, "خطا", m))
        self.thread.start()

    def _finish_trim(self, path):
        self.video_progress.setVisible(False)
        self._set_busy(False)
        if path and Path(path).exists():
            try:
                t = CACHE_DIR / f"tthumb_{time.time_ns()}.png"
                c = VideoFileClip(path)
                c.save_frame(str(t), t=min(1.0, c.duration / 2))
                c.close()
                self._show_pix(self.video_preview_label, str(t))
            except Exception:
                pass
            save, _ = QFileDialog.getSaveFileName(
                self, "ذخیره",
                Path(self.current_video_path).stem + "_trimmed.mp4",
                "MP4 (*.mp4)",
            )
            if save:
                try:
                    shutil.move(path, save)
                    QMessageBox.information(self, "موفق", f"ذخیره شد:\n{save}")
                except Exception as e:
                    QMessageBox.warning(self, "خطا", str(e))
            else:
                Path(path).unlink(missing_ok=True)
        else:
            QMessageBox.warning(self, "خطا", "برش ناموفق بود.")

    def start_convert_to_mp3(self):
        if not self.current_video_path:
            QMessageBox.warning(self, "خطا", "ویدیو انتخاب نشده.")
            return
        if not find_ffmpeg():
            QMessageBox.warning(self, "خطا", "FFmpeg پیدا نشد.")
            return
        out = str(CACHE_DIR / f"mp3_{time.time_ns()}.mp3")
        self.video_progress.setVisible(True)
        self.video_progress.setValue(0)
        self._set_busy(True)
        self.thread = ProgressThread("mp3", self.current_video_path, out)
        self.thread.progress_signal.connect(self.video_progress.setValue)
        self.thread.finished_signal.connect(self._finish_mp3)
        self.thread.error_signal.connect(lambda m: QMessageBox.warning(self, "خطا", m))
        self.thread.start()

    def _finish_mp3(self, path):
        self.video_progress.setVisible(False)
        self._set_busy(False)
        if path and Path(path).exists():
            save, _ = QFileDialog.getSaveFileName(
                self, "ذخیره MP3",
                Path(self.current_video_path).stem + ".mp3",
                "MP3 (*.mp3)",
            )
            if save:
                try:
                    shutil.move(path, save)
                    QMessageBox.information(self, "موفق", f"ذخیره شد:\n{save}")
                except Exception as e:
                    QMessageBox.warning(self, "خطا", str(e))
            else:
                Path(path).unlink(missing_ok=True)
        else:
            QMessageBox.warning(self, "خطا", "تبدیل ناموفق بود.")

    def _parse_time(self, s: str):
        try:
            parts = s.strip().split(":")
            if len(parts) == 3:
                h, m, sec = map(int, parts)
                return h * 3600 + m * 60 + sec
            if len(parts) == 2:
                m, sec = map(int, parts)
                return m * 60 + sec
            return None
        except Exception:
            return None

    def _show_pix(self, label: QLabel, path: str):
        pix = QPixmap(path)
        if pix.isNull():
            label.setText("خطا")
            return
        target = label.size()
        if target.width() < 60:
            target = QSize(320, 240)
        label.setPixmap(
            pix.scaled(
                target,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.current_image is not None:
            self.display_current_image()

    def closeEvent(self, event):
        try:
            for pat in ("prev_*", "vthumb_*", "tthumb_*", "othumb_*", "trim_*", "mp3_*"):
                for f in CACHE_DIR.glob(pat):
                    f.unlink(missing_ok=True)
        except Exception:
            pass
        event.accept()
