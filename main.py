#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Desktop Media Editor v0.3.0
A bilingual (Persian/English) desktop app for basic image & video editing.
Modern card-based UI with before/after comparison and extra tools.
"""

import sys
import os
import time
import shutil
import subprocess
import shutil as sh
from pathlib import Path

from moviepy import VideoFileClip
from PIL import Image, ImageFilter, ImageEnhance, ImageOps, ImageDraw, ImageFont
from PyQt6.QtWidgets import (
    QMainWindow, QApplication, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QFileDialog, QProgressBar, QMessageBox,
    QSplitter, QGridLayout, QGroupBox, QCheckBox, QSpacerItem, QSizePolicy,
    QComboBox, QSpinBox, QSlider, QStatusBar, QFrame, QScrollArea,
    QMenuBar, QMenu
)
from PyQt6.QtGui import QPixmap, QIcon, QAction, QFont
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSettings, QSize

__version__ = "0.3.0"
APP_NAME = "Desktop Media Editor"
ORG_NAME = "KeyvanAlavi"

# ---------------------------------------------------------------------------
# FFmpeg discovery
# ---------------------------------------------------------------------------
def find_ffmpeg():
    if getattr(sys, 'frozen', False):
        base_dir = Path(sys._MEIPASS)
    else:
        base_dir = Path(__file__).resolve().parent
    for p in [base_dir / "ffmpeg" / "ffmpeg.exe", base_dir / "ffmpeg" / "ffmpeg",
              base_dir / "ffmpeg.exe", base_dir / "ffmpeg"]:
        if p.exists():
            return str(p)
    return sh.which("ffmpeg")


def find_ffprobe():
    if getattr(sys, 'frozen', False):
        base_dir = Path(sys._MEIPASS)
    else:
        base_dir = Path(__file__).resolve().parent
    for p in [base_dir / "ffmpeg" / "ffprobe.exe", base_dir / "ffmpeg" / "ffprobe",
              base_dir / "ffprobe.exe", base_dir / "ffprobe"]:
        if p.exists():
            return str(p)
    return sh.which("ffprobe")


FFMPEG_PATH = find_ffmpeg()
FFPROBE_PATH = find_ffprobe()
if FFMPEG_PATH:
    os.environ["FFMPEG_BINARY"] = FFMPEG_PATH
if FFPROBE_PATH:
    os.environ["FFPROBE_BINARY"] = FFPROBE_PATH

CACHE_DIR = Path("cache")
CACHE_DIR.mkdir(exist_ok=True)


# ---------------------------------------------------------------------------
# Worker
# ---------------------------------------------------------------------------
class ProgressThread(QThread):
    progress_signal = pyqtSignal(int)
    finished_signal = pyqtSignal(object)
    error_signal = pyqtSignal(str)

    def __init__(self, task, *args):
        super().__init__()
        self.task = task
        self.args = args

    def run(self):
        try:
            if self.task == 'trim':
                ok = self.trim_video(*self.args)
                self.finished_signal.emit(self.args[3] if ok else None)
            elif self.task == 'mp3':
                ok = self.convert_to_mp3(*self.args)
                self.finished_signal.emit(self.args[1] if ok else None)
        except Exception as e:
            self.error_signal.emit(str(e))
            self.finished_signal.emit(None)

    def trim_video(self, input_path, start_secs, end_secs, output_path):
        if not FFMPEG_PATH:
            self.error_signal.emit("FFmpeg پیدا نشد.")
            return False
        try:
            duration = end_secs - start_secs
            cmd = [FFMPEG_PATH, '-i', input_path, '-ss', str(start_secs),
                   '-t', str(duration), '-c:v', 'copy', '-c:a', 'copy', '-y', output_path]
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            self.progress_signal.emit(100)
            return Path(output_path).exists()
        except Exception as e:
            self.error_signal.emit(str(e))
            return False

    def convert_to_mp3(self, input_path, output_path):
        if not FFMPEG_PATH:
            self.error_signal.emit("FFmpeg پیدا نشد.")
            return False
        try:
            cmd = [FFMPEG_PATH, '-i', input_path, '-vn', '-acodec', 'libmp3lame',
                   '-q:a', '2', '-y', output_path]
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            self.progress_signal.emit(100)
            return True
        except Exception as e:
            self.error_signal.emit(str(e))
            return False


def make_btn(text, tooltip="", primary=True):
    btn = QPushButton(text)
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    if tooltip:
        btn.setToolTip(tooltip)
    btn.setMinimumHeight(30)
    btn.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
    if not primary:
        btn.setObjectName("secondaryBtn")
    return btn


# ---------------------------------------------------------------------------
# Main Window
# ---------------------------------------------------------------------------
class MediaEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME}  v{__version__}")
        self.setWindowIcon(QIcon("edit.ico"))
        self.setGeometry(70, 40, 1220, 740)
        self.setMinimumSize(860, 540)

        self.settings = QSettings(ORG_NAME, "MediaEditor")
        self.theme = self.settings.value("theme", "Default", type=str)
        self.font_size = self.settings.value("font_size", 13, type=int)

        self.themes = {
            "Default": {
                "main_bg": "#f1f5f9", "sidebar_bg": "#ffffff",
                "button_bg": "#0f766e", "button_hover": "#0d9488", "button_pressed": "#115e59",
                "text_color": "#0f172a", "muted_text": "#64748b",
                "border_color": "#e2e8f0", "tab_bg": "#e2e8f0",
                "tab_selected_bg": "#ffffff", "tab_selected_border": "#0f766e",
                "preview_bg": "#ffffff", "group_bg": "#ffffff", "accent": "#0f766e",
            },
            "Dark": {
                "main_bg": "#0b1120", "sidebar_bg": "#111827",
                "button_bg": "#14b8a6", "button_hover": "#2dd4bf", "button_pressed": "#0d9488",
                "text_color": "#f1f5f9", "muted_text": "#94a3b8",
                "border_color": "#1e293b", "tab_bg": "#1e293b",
                "tab_selected_bg": "#0b1120", "tab_selected_border": "#14b8a6",
                "preview_bg": "#111827", "group_bg": "#111827", "accent": "#14b8a6",
            },
            "Blue": {
                "main_bg": "#eff6ff", "sidebar_bg": "#ffffff",
                "button_bg": "#1d4ed8", "button_hover": "#2563eb", "button_pressed": "#1e40af",
                "text_color": "#1e3a8a", "muted_text": "#64748b",
                "border_color": "#bfdbfe", "tab_bg": "#dbeafe",
                "tab_selected_bg": "#ffffff", "tab_selected_border": "#1d4ed8",
                "preview_bg": "#ffffff", "group_bg": "#ffffff", "accent": "#1d4ed8",
            },
            "Green": {
                "main_bg": "#f0fdf4", "sidebar_bg": "#ffffff",
                "button_bg": "#15803d", "button_hover": "#16a34a", "button_pressed": "#166534",
                "text_color": "#14532d", "muted_text": "#64748b",
                "border_color": "#bbf7d0", "tab_bg": "#dcfce7",
                "tab_selected_bg": "#ffffff", "tab_selected_border": "#15803d",
                "preview_bg": "#ffffff", "group_bg": "#ffffff", "accent": "#15803d",
            },
        }

        self.filters = [
            ("🌫️ Blur", "BLUR"), ("📐 Contour", "CONTOUR"), ("✨ Detail", "DETAIL"),
            ("🗿 Emboss", "EMBOSS"), ("🔪 Sharpen", "SHARPEN"), ("⬛ Grayscale", "GRAYSCALE"),
            ("🟤 Sepia", "SEPIA"), ("🔄 Negative", "NEGATIVE"), ("📷 Vintage", "VINTAGE"),
        ]
        self.quality_buttons = [
            ("⬆ Enhance H", "ENHANCE_QUALITY_H"),
            ("↗ Enhance M", "ENHANCE_QUALITY_M"),
            ("🎨 Color+", "COLOR_ADJUST_H"),
            ("🎨 Color−", "COLOR_ADJUST_L"),
        ]

        self.original_image = None
        self.current_image = None
        self.current_image_path = None
        self.history = []
        self.history_index = -1
        self.max_history = 25
        self.show_original = False   # toggle for comparison

        self.current_video_path = None
        self.video_duration = 0.0

        self.apply_theme()
        self._build_menubar()
        self._build_ui()
        self._update_undo_redo_buttons()

        if FFMPEG_PATH:
            self.statusBar().showMessage(f"آماده  •  FFmpeg: {Path(FFMPEG_PATH).name}  •  v{__version__}", 6000)
        else:
            self.statusBar().showMessage(f"⚠ FFmpeg پیدا نشد  •  v{__version__}", 8000)

    # ------------------------------------------------------------------
    def apply_theme(self):
        t = self.themes[self.theme]
        ss = f"""
            QMainWindow, QWidget {{
                background-color: {t['main_bg']};
                font-family: 'Segoe UI', 'Vazirmatn', 'Tahoma', sans-serif;
                font-size: {self.font_size}px;
                color: {t['text_color']};
            }}
            QMenuBar {{
                background-color: {t['sidebar_bg']};
                color: {t['text_color']};
                border-bottom: 1px solid {t['border_color']};
                padding: 4px 6px;
            }}
            QMenuBar::item {{ padding: 5px 10px; border-radius: 5px; }}
            QMenuBar::item:selected {{ background-color: {t['accent']}; color: white; }}
            QMenu {{
                background-color: {t['sidebar_bg']};
                color: {t['text_color']};
                border: 1px solid {t['border_color']};
                padding: 4px;
            }}
            QMenu::item {{ padding: 6px 18px; border-radius: 4px; }}
            QMenu::item:selected {{ background-color: {t['accent']}; color: white; }}
            QStatusBar {{
                background-color: {t['sidebar_bg']};
                color: {t['muted_text']};
                border-top: 1px solid {t['border_color']};
                font-size: {max(10, self.font_size - 1)}px;
            }}
            QPushButton {{
                background-color: {t['button_bg']};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 7px 11px;
                font-size: {self.font_size}px;
                font-weight: 600;
                min-height: 28px;
            }}
            QPushButton:hover {{ background-color: {t['button_hover']}; }}
            QPushButton:pressed {{ background-color: {t['button_pressed']}; }}
            QPushButton:disabled {{
                background-color: {t['border_color']};
                color: {t['muted_text']};
            }}
            QPushButton#secondaryBtn {{
                background-color: transparent;
                color: {t['text_color']};
                border: 1.5px solid {t['border_color']};
            }}
            QPushButton#secondaryBtn:hover {{
                background-color: {t['border_color']};
                border-color: {t['accent']};
            }}
            QPushButton#secondaryBtn:pressed {{
                background-color: {t['accent']};
                color: white;
                border-color: {t['accent']};
            }}
            QPushButton#secondaryBtn:disabled {{
                color: {t['muted_text']};
                border-color: {t['border_color']};
            }}
            QPushButton#activeToggle {{
                background-color: {t['accent']};
                color: white;
                border: 2px solid {t['accent']};
            }}
            QLabel {{
                font-size: {self.font_size}px;
                color: {t['text_color']};
                font-weight: 500;
                background: transparent;
            }}
            QLabel#placeholderLabel {{
                font-size: 14px;
                color: {t['muted_text']};
                background: transparent;
            }}
            QLabel#mutedLabel {{
                color: {t['muted_text']};
                background: transparent;
            }}
            QLabel#cardTitle {{
                font-weight: 700;
                font-size: {self.font_size + 1}px;
                color: {t['text_color']};
                background: transparent;
                padding-bottom: 4px;
            }}
            QLineEdit, QSpinBox, QComboBox {{
                border: 1.5px solid {t['border_color']};
                border-radius: 7px;
                padding: 6px 10px;
                background-color: {t['preview_bg']};
                font-size: {self.font_size}px;
                color: {t['text_color']};
                selection-background-color: {t['accent']};
                selection-color: white;
            }}
            QLineEdit:focus, QSpinBox:focus, QComboBox:focus {{
                border: 2px solid {t['accent']};
            }}
            QComboBox QAbstractItemView {{
                background-color: {t['sidebar_bg']};
                color: {t['text_color']};
                border: 1px solid {t['border_color']};
                selection-background-color: {t['accent']};
                selection-color: white;
            }}
            QSlider::groove:horizontal {{
                height: 6px;
                background: {t['border_color']};
                border-radius: 3px;
            }}
            QSlider::handle:horizontal {{
                background: {t['accent']};
                width: 16px; height: 16px;
                margin: -5px 0;
                border-radius: 8px;
            }}
            QSlider::sub-page:horizontal {{
                background: {t['accent']};
                border-radius: 3px;
            }}
            QProgressBar {{
                background-color: {t['border_color']};
                border-radius: 6px;
                text-align: center;
                font-size: {max(10, self.font_size - 2)}px;
                color: {t['text_color']};
                height: 18px;
            }}
            QProgressBar::chunk {{
                background-color: {t['button_bg']};
                border-radius: 6px;
            }}
            /* Independent cards */
            QFrame#toolCard {{
                background-color: {t['group_bg']};
                border: 1px solid {t['border_color']};
                border-radius: 12px;
                padding: 4px;
            }}
            QGroupBox {{
                background-color: {t['group_bg']};
                border: 1px solid {t['border_color']};
                border-radius: 12px;
                margin-top: 12px;
                padding: 14px 10px 10px 10px;
                font-weight: 700;
                color: {t['text_color']};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 8px;
                color: {t['text_color']};
                background-color: {t['group_bg']};
            }}
            QTabWidget::pane {{
                border: 1px solid {t['border_color']};
                border-radius: 10px;
                background-color: {t['preview_bg']};
                top: -1px;
            }}
            QTabBar::tab {{
                background-color: {t['tab_bg']};
                border: 1px solid {t['border_color']};
                border-bottom: none;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                padding: 8px 16px;
                font-size: {self.font_size}px;
                color: {t['text_color']};
                margin-right: 3px;
            }}
            QTabBar::tab:selected {{
                background-color: {t['tab_selected_bg']};
                border-bottom: 3px solid {t['tab_selected_border']};
                font-weight: 700;
            }}
            QTabBar::tab:hover:!selected {{
                background-color: {t['preview_bg']};
            }}
            QFrame#previewFrame {{
                background-color: {t['preview_bg']};
                border: 1px solid {t['border_color']};
                border-radius: 12px;
            }}
            QFrame#sidebarFrame {{
                background-color: {t['sidebar_bg']};
                border: 1px solid {t['border_color']};
                border-radius: 12px;
            }}
            QScrollArea {{ border: none; background: transparent; }}
            QScrollBar:vertical {{
                background: {t['border_color']};
                width: 9px; margin: 0; border-radius: 4px;
            }}
            QScrollBar::handle:vertical {{
                background: {t['muted_text']};
                border-radius: 4px; min-height: 28px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
        """
        self.setStyleSheet(ss)

    def save_settings(self):
        self.settings.setValue("theme", self.theme)
        self.settings.setValue("font_size", self.font_size)
        self.apply_theme()
        self.statusBar().showMessage("✓ تنظیمات ذخیره شد", 2500)

    # ------------------------------------------------------------------
    def _build_menubar(self):
        menubar = self.menuBar()
        file_menu = menubar.addMenu("📁 فایل")
        act_open = QAction("🖼 باز کردن تصویر", self)
        act_open.triggered.connect(self.open_image)
        file_menu.addAction(act_open)
        act_vid = QAction("🎬 باز کردن ویدیو", self)
        act_vid.triggered.connect(self.open_video)
        file_menu.addAction(act_vid)
        file_menu.addSeparator()
        act_save = QAction("💾 ذخیره تصویر", self)
        act_save.triggered.connect(self.save_image)
        file_menu.addAction(act_save)
        file_menu.addSeparator()
        act_exit = QAction("خروج", self)
        act_exit.triggered.connect(self.close)
        file_menu.addAction(act_exit)

        edit_menu = menubar.addMenu("✏ ویرایش")
        act_undo = QAction("↩ Undo", self)
        act_undo.triggered.connect(self.undo)
        edit_menu.addAction(act_undo)
        act_redo = QAction("↪ Redo", self)
        act_redo.triggered.connect(self.redo)
        edit_menu.addAction(act_redo)
        edit_menu.addSeparator()
        act_reset = QAction("↺ بازنشانی", self)
        act_reset.triggered.connect(self.reset_image)
        edit_menu.addAction(act_reset)

        help_menu = menubar.addMenu("❓ راهنما")
        act_about = QAction("درباره برنامه", self)
        act_about.triggered.connect(self.show_about)
        help_menu.addAction(act_about)

    def show_about(self):
        QMessageBox.about(self, "درباره برنامه",
            f"<h3>{APP_NAME}</h3>"
            f"<p>نسخه: <b>{__version__}</b></p>"
            "<p>ویرایشگر تصویر و ویدیو با رابط دو زبانه.</p>"
            "<p>توسعه‌دهنده اصلی: Keyvan Alavi</p>"
            "<p><i>در ارتقای این نسخه جدید از Grok (نسخه رایگان) نیز استفاده شده است.</i></p>"
        )

    # ------------------------------------------------------------------
    def _build_ui(self):
        self.tab_widget = QTabWidget()
        self.setCentralWidget(self.tab_widget)
        self.image_tab = QWidget()
        self.video_tab = QWidget()
        self.settings_tab = QWidget()
        self.tab_widget.addTab(self.image_tab, "🖼  ویرایش تصویر")
        self.tab_widget.addTab(self.video_tab, "🎬  ویرایش ویدیو")
        self.tab_widget.addTab(self.settings_tab, "⚙  تنظیمات")
        self.init_image_tab()
        self.init_video_tab()
        self.init_settings_tab()
        self.setStatusBar(QStatusBar())

    def _make_card(self, title: str) -> tuple:
        """Create an independent card frame with title. Returns (frame, content_layout)"""
        card = QFrame()
        card.setObjectName("toolCard")
        outer = QVBoxLayout(card)
        outer.setContentsMargins(10, 10, 10, 10)
        outer.setSpacing(8)
        title_lbl = QLabel(title)
        title_lbl.setObjectName("cardTitle")
        outer.addWidget(title_lbl)
        content = QVBoxLayout()
        content.setSpacing(6)
        outer.addLayout(content)
        return card, content

    def init_image_tab(self):
        main_layout = QHBoxLayout(self.image_tab)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(12)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        # ===== Left tools (scrollable independent cards) =====
        sidebar = QFrame()
        sidebar.setObjectName("sidebarFrame")
        side_l = QVBoxLayout(sidebar)
        side_l.setContentsMargins(8, 8, 8, 8)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        content = QWidget()
        left = QVBoxLayout(content)
        left.setContentsMargins(4, 4, 4, 4)
        left.setSpacing(10)

        # Card: File
        card, lay = self._make_card("📁 فایل")
        row = QHBoxLayout()
        self.btn_open_image = make_btn("📂  باز کردن", "انتخاب تصویر")
        self.btn_open_image.clicked.connect(self.open_image)
        self.btn_save_image = make_btn("💾  ذخیره", "ذخیره تصویر")
        self.btn_save_image.clicked.connect(self.save_image)
        self.btn_save_image.setEnabled(False)
        row.addWidget(self.btn_open_image)
        row.addWidget(self.btn_save_image)
        lay.addLayout(row)
        left.addWidget(card)

        # Card: History
        card, lay = self._make_card("🕒 تاریخچه")
        row = QHBoxLayout()
        self.btn_undo = make_btn("↩ Undo", "بازگشت")
        self.btn_undo.clicked.connect(self.undo)
        self.btn_redo = make_btn("↪ Redo", "جلو")
        self.btn_redo.clicked.connect(self.redo)
        self.btn_reset = make_btn("↺ بازنشانی", "بازگشت به اصلی", primary=False)
        self.btn_reset.clicked.connect(self.reset_image)
        row.addWidget(self.btn_undo)
        row.addWidget(self.btn_redo)
        row.addWidget(self.btn_reset)
        lay.addLayout(row)
        left.addWidget(card)

        # Card: Comparison
        card, lay = self._make_card("👁 مقایسه")
        row = QHBoxLayout()
        self.btn_show_current = make_btn("پیش‌نمایش", "نمایش تصویر ویرایش‌شده")
        self.btn_show_current.clicked.connect(lambda: self._set_compare(False))
        self.btn_show_original = make_btn("اصلی", "نمایش تصویر اصلی برای مقایسه", primary=False)
        self.btn_show_original.clicked.connect(lambda: self._set_compare(True))
        row.addWidget(self.btn_show_current)
        row.addWidget(self.btn_show_original)
        lay.addLayout(row)
        self.compare_hint = QLabel("برای دیدن تفاوت، بین «پیش‌نمایش» و «اصلی» جابه‌جا شوید")
        self.compare_hint.setObjectName("mutedLabel")
        self.compare_hint.setWordWrap(True)
        lay.addWidget(self.compare_hint)
        left.addWidget(card)

        # Card: Live adjust
        card, lay = self._make_card("🎚 تنظیمات زنده")
        br = QHBoxLayout()
        br.addWidget(QLabel("☀ روشنایی"))
        self.brightness_slider = QSlider(Qt.Orientation.Horizontal)
        self.brightness_slider.setRange(-100, 100)
        self.brightness_slider.setValue(0)
        self.brightness_slider.valueChanged.connect(self._on_live_adjust)
        self.brightness_value = QLabel("0")
        self.brightness_value.setFixedWidth(28)
        self.brightness_value.setAlignment(Qt.AlignmentFlag.AlignCenter)
        br.addWidget(self.brightness_slider)
        br.addWidget(self.brightness_value)
        lay.addLayout(br)

        ct = QHBoxLayout()
        ct.addWidget(QLabel("◐ کنتراست"))
        self.contrast_slider = QSlider(Qt.Orientation.Horizontal)
        self.contrast_slider.setRange(-100, 100)
        self.contrast_slider.setValue(0)
        self.contrast_slider.valueChanged.connect(self._on_live_adjust)
        self.contrast_value = QLabel("0")
        self.contrast_value.setFixedWidth(28)
        self.contrast_value.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ct.addWidget(self.contrast_slider)
        ct.addWidget(self.contrast_value)
        lay.addLayout(ct)

        btn_apply = make_btn("✓  اعمال تنظیمات", "اعمال و ذخیره در تاریخچه")
        btn_apply.clicked.connect(self.apply_live_adjustments)
        lay.addWidget(btn_apply)
        left.addWidget(card)

        # Card: Filters
        card, lay = self._make_card("✨ فیلترها")
        grid = QGridLayout()
        grid.setSpacing(6)
        for i, (name, code) in enumerate(self.filters):
            btn = make_btn(name, f"فیلتر {name}")
            btn.clicked.connect(lambda _, c=code: self.apply_filter(c))
            grid.addWidget(btn, i // 3, i % 3)
        lay.addLayout(grid)
        left.addWidget(card)

        # Card: Quality
        card, lay = self._make_card("🔧 بهبود کیفیت")
        grid = QGridLayout()
        grid.setSpacing(6)
        for i, (name, code) in enumerate(self.quality_buttons):
            btn = make_btn(name, name)
            btn.clicked.connect(lambda _, c=code: self.apply_filter(c))
            grid.addWidget(btn, i // 2, i % 2)
        lay.addLayout(grid)
        left.addWidget(card)

        # Card: Transform (rotate + flip + resize)  ← new professional tools
        card, lay = self._make_card("🔄 چرخش، آینه و اندازه")
        rot = QHBoxLayout()
        for name, code in [("↻ ۹۰°", "ROTATE_N"), ("⟳ ۱۸۰°", "ROTATE_S"), ("↺ ۲۷۰°", "ROTATE_D")]:
            btn = make_btn(name, name)
            btn.clicked.connect(lambda _, c=code: self.apply_filter(c))
            rot.addWidget(btn)
        lay.addLayout(rot)

        flip = QHBoxLayout()
        btn_fh = make_btn("↔ آینه افقی", "Flip Horizontal")
        btn_fh.clicked.connect(lambda: self.apply_filter("FLIP_H"))
        btn_fv = make_btn("↕ آینه عمودی", "Flip Vertical")
        btn_fv.clicked.connect(lambda: self.apply_filter("FLIP_V"))
        flip.addWidget(btn_fh)
        flip.addWidget(btn_fv)
        lay.addLayout(flip)

        size = QHBoxLayout()
        for name, code in [("⬇ کوچک‌تر", "RESIZE_S"), ("⬆ بزرگ‌تر", "RESIZE_L")]:
            btn = make_btn(name, name)
            btn.clicked.connect(lambda _, c=code: self.apply_filter(c))
            size.addWidget(btn)
        lay.addLayout(size)
        left.addWidget(card)

        # Card: Professional – Auto Enhance + simple crop ratios
        card, lay = self._make_card("★ ابزار حرفه‌ای")
        btn_auto = make_btn("✨ بهبود خودکار", "Auto Contrast + Color + Sharpness")
        btn_auto.clicked.connect(lambda: self.apply_filter("AUTO_ENHANCE"))
        lay.addWidget(btn_auto)

        crop_row = QHBoxLayout()
        for label, code in [("✂ مربع", "CROP_SQUARE"), ("✂ ۱۶:۹", "CROP_16_9"), ("✂ ۴:۳", "CROP_4_3")]:
            btn = make_btn(label, f"برش به نسبت {label}")
            btn.clicked.connect(lambda _, c=code: self.apply_filter(c))
            crop_row.addWidget(btn)
        lay.addLayout(crop_row)
        left.addWidget(card)

        left.addStretch()
        scroll.setWidget(content)
        side_l.addWidget(scroll)
        splitter.addWidget(sidebar)

        # ===== Right: Preview area =====
        right = QWidget()
        right_l = QVBoxLayout(right)
        right_l.setContentsMargins(0, 0, 0, 0)
        right_l.setSpacing(8)

        # Main preview
        preview_frame = QFrame()
        preview_frame.setObjectName("previewFrame")
        pf_l = QVBoxLayout(preview_frame)
        pf_l.setContentsMargins(10, 10, 10, 10)

        self.preview_title = QLabel("پیش‌نمایش (ویرایش‌شده)")
        self.preview_title.setObjectName("cardTitle")
        pf_l.addWidget(self.preview_title)

        self.image_preview_label = QLabel("تصویری انتخاب نشده\n\nبرای شروع روی «باز کردن» کلیک کنید")
        self.image_preview_label.setObjectName("placeholderLabel")
        self.image_preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_preview_label.setMinimumSize(300, 240)
        self.image_preview_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        pf_l.addWidget(self.image_preview_label)
        right_l.addWidget(preview_frame, stretch=3)

        # Small original thumbnail strip
        orig_frame = QFrame()
        orig_frame.setObjectName("previewFrame")
        of_l = QHBoxLayout(orig_frame)
        of_l.setContentsMargins(8, 8, 8, 8)
        of_l.setSpacing(10)

        orig_info = QVBoxLayout()
        orig_lbl = QLabel("تصویر اصلی")
        orig_lbl.setObjectName("cardTitle")
        orig_info.addWidget(orig_lbl)
        self.orig_hint = QLabel("برای مقایسه سریع")
        self.orig_hint.setObjectName("mutedLabel")
        orig_info.addWidget(self.orig_hint)
        of_l.addLayout(orig_info)

        self.original_thumb = QLabel("—")
        self.original_thumb.setObjectName("placeholderLabel")
        self.original_thumb.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.original_thumb.setFixedSize(160, 100)
        self.original_thumb.setStyleSheet("border: 1px dashed #94a3b8; border-radius: 8px;")
        of_l.addWidget(self.original_thumb)
        of_l.addStretch()
        right_l.addWidget(orig_frame, stretch=0)

        splitter.addWidget(right)
        splitter.setStretchFactor(0, 36)
        splitter.setStretchFactor(1, 64)
        splitter.setSizes([400, 700])
        main_layout.addWidget(splitter)

        self._update_compare_buttons()

    def init_video_tab(self):
        main_layout = QHBoxLayout(self.video_tab)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(12)
        splitter = QSplitter(Qt.Orientation.Horizontal)

        sidebar = QFrame()
        sidebar.setObjectName("sidebarFrame")
        left = QVBoxLayout(sidebar)
        left.setContentsMargins(10, 10, 10, 10)
        left.setSpacing(10)

        card, lay = self._make_card("📁 فایل ویدیو")
        self.btn_open_video = make_btn("📂  باز کردن ویدیو", "انتخاب ویدیو")
        self.btn_open_video.clicked.connect(self.open_video)
        lay.addWidget(self.btn_open_video)
        self.video_info_label = QLabel("ویدیویی انتخاب نشده")
        self.video_info_label.setObjectName("mutedLabel")
        self.video_info_label.setWordWrap(True)
        lay.addWidget(self.video_info_label)
        left.addWidget(card)

        card, lay = self._make_card("✂ برش ویدیو")
        r1 = QHBoxLayout()
        r1.addWidget(QLabel("شروع"))
        self.trim_start_input = QLineEdit("00:00:00")
        self.trim_start_input.setPlaceholderText("HH:MM:SS")
        r1.addWidget(self.trim_start_input)
        lay.addLayout(r1)
        r2 = QHBoxLayout()
        r2.addWidget(QLabel("پایان"))
        self.trim_end_input = QLineEdit("00:00:10")
        self.trim_end_input.setPlaceholderText("HH:MM:SS")
        r2.addWidget(self.trim_end_input)
        lay.addLayout(r2)
        self.btn_trim = make_btn("✂  برش و ذخیره", "برش ویدیو")
        self.btn_trim.clicked.connect(self.start_trim_video)
        lay.addWidget(self.btn_trim)
        left.addWidget(card)

        card, lay = self._make_card("🎵 استخراج صدا")
        self.btn_mp3 = make_btn("🎵  تبدیل به MP3", "استخراج صدا")
        self.btn_mp3.clicked.connect(self.start_convert_to_mp3)
        lay.addWidget(self.btn_mp3)
        left.addWidget(card)

        self.video_progress = QProgressBar()
        self.video_progress.setVisible(False)
        left.addWidget(self.video_progress)
        left.addStretch()
        splitter.addWidget(sidebar)

        right = QWidget()
        right_l = QVBoxLayout(right)
        right_l.setContentsMargins(0, 0, 0, 0)
        preview_frame = QFrame()
        preview_frame.setObjectName("previewFrame")
        pf = QVBoxLayout(preview_frame)
        pf.setContentsMargins(10, 10, 10, 10)
        self.video_preview_label = QLabel("ویدیویی انتخاب نشده")
        self.video_preview_label.setObjectName("placeholderLabel")
        self.video_preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_preview_label.setMinimumSize(300, 240)
        self.video_preview_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        pf.addWidget(self.video_preview_label)
        right_l.addWidget(preview_frame)
        splitter.addWidget(right)
        splitter.setStretchFactor(0, 36)
        splitter.setStretchFactor(1, 64)
        splitter.setSizes([360, 700])
        main_layout.addWidget(splitter)

    def init_settings_tab(self):
        layout = QVBoxLayout(self.settings_tab)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        card, lay = self._make_card("🎨 تم و ظاهر")
        r1 = QHBoxLayout()
        r1.addWidget(QLabel("تم:"))
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Default", "Dark", "Blue", "Green"])
        self.theme_combo.setCurrentText(self.theme)
        self.theme_combo.currentTextChanged.connect(self._on_theme_changed)
        r1.addWidget(self.theme_combo)
        r1.addStretch()
        lay.addLayout(r1)
        r2 = QHBoxLayout()
        r2.addWidget(QLabel("اندازه فونت:"))
        self.font_spin = QSpinBox()
        self.font_spin.setRange(10, 20)
        self.font_spin.setValue(self.font_size)
        self.font_spin.valueChanged.connect(self._on_font_changed)
        r2.addWidget(self.font_spin)
        r2.addStretch()
        lay.addLayout(r2)
        layout.addWidget(card)

        card, lay = self._make_card("ℹ درباره برنامه")
        about = QLabel(
            f"<b>{APP_NAME}</b><br>نسخه: <b>{__version__}</b><br><br>"
            "ویرایشگر تصویر و ویدیو با رابط دو زبانه.<br>"
            "توسعه‌دهنده اصلی: Keyvan Alavi<br><br>"
            "<i>در ارتقای این نسخه جدید از Grok (نسخه رایگان) نیز استفاده شده است.</i>"
        )
        about.setWordWrap(True)
        about.setTextFormat(Qt.TextFormat.RichText)
        lay.addWidget(about)
        btn_cache = make_btn("🗑  پاک کردن کش", "حذف فایل‌های موقت", primary=False)
        btn_cache.clicked.connect(self.clear_cache)
        lay.addWidget(btn_cache)
        layout.addWidget(card)
        layout.addStretch()

    # ------------------------------------------------------------------
    def _on_theme_changed(self, name):
        self.theme = name
        self.save_settings()

    def _on_font_changed(self, value):
        self.font_size = value
        self.save_settings()

    def clear_cache(self):
        try:
            if CACHE_DIR.exists():
                for f in CACHE_DIR.iterdir():
                    if f.is_file():
                        f.unlink()
            self.statusBar().showMessage("✓ کش پاک شد", 3000)
            QMessageBox.information(self, "موفق", "فایل‌های موقت حذف شدند.")
        except Exception as e:
            QMessageBox.warning(self, "خطا", str(e))

    # ------------------------------------------------------------------
    # Comparison
    # ------------------------------------------------------------------
    def _set_compare(self, show_original: bool):
        self.show_original = show_original
        self._update_compare_buttons()
        self.display_current_image()
        if show_original:
            self.preview_title.setText("پیش‌نمایش (تصویر اصلی)")
            self.statusBar().showMessage("در حال نمایش تصویر اصلی", 2000)
        else:
            self.preview_title.setText("پیش‌نمایش (ویرایش‌شده)")
            self.statusBar().showMessage("در حال نمایش تصویر ویرایش‌شده", 2000)

    def _update_compare_buttons(self):
        if self.show_original:
            self.btn_show_original.setObjectName("activeToggle")
            self.btn_show_current.setObjectName("")
        else:
            self.btn_show_current.setObjectName("activeToggle")
            self.btn_show_original.setObjectName("secondaryBtn")
        # re-apply style so objectName changes take effect
        self.apply_theme()

    # ------------------------------------------------------------------
    # Image
    # ------------------------------------------------------------------
    def open_image(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "انتخاب تصویر", "",
            "Images (*.png *.jpg *.jpeg *.bmp *.webp *.tiff);;All Files (*)"
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
            self._reset_sliders()
            self._update_compare_buttons()
            self.display_current_image()
            self._update_original_thumb()
            self.btn_save_image.setEnabled(True)
            self._update_undo_redo_buttons()
            self.statusBar().showMessage(f"✓ تصویر بارگذاری شد: {Path(path).name}", 4000)
        except Exception as e:
            QMessageBox.warning(self, "خطا", f"نتوانست تصویر را باز کند:\n{e}")

    def _update_original_thumb(self):
        if self.original_image is None:
            self.original_thumb.setText("—")
            return
        tmp = CACHE_DIR / f"orig_thumb_{time.time_ns()}.png"
        try:
            thumb = self.original_image.copy()
            thumb.thumbnail((160, 100), Image.Resampling.LANCZOS)
            thumb.save(tmp, "PNG")
            pix = QPixmap(str(tmp))
            self.original_thumb.setPixmap(pix)
            tmp.unlink(missing_ok=True)
        except Exception:
            pass

    def display_current_image(self):
        img = None
        if self.show_original and self.original_image is not None:
            img = self.original_image
        elif self.current_image is not None:
            img = self.current_image
        if img is None:
            return
        tmp = CACHE_DIR / f"preview_{time.time_ns()}.png"
        try:
            img.save(tmp, "PNG")
            pix = QPixmap(str(tmp))
            if not pix.isNull():
                target = self.image_preview_label.size()
                if target.width() < 80 or target.height() < 60:
                    target = self.image_preview_label.minimumSize()
                scaled = pix.scaled(target, Qt.AspectRatioMode.KeepAspectRatio,
                                    Qt.TransformationMode.SmoothTransformation)
                self.image_preview_label.setPixmap(scaled)
            tmp.unlink(missing_ok=True)
        except Exception:
            pass

    def _push_history(self, img):
        self.history = self.history[: self.history_index + 1]
        self.history.append(img.copy())
        if len(self.history) > self.max_history:
            self.history.pop(0)
        else:
            self.history_index += 1
        self._update_undo_redo_buttons()

    def _update_undo_redo_buttons(self):
        self.btn_undo.setEnabled(self.history_index > 0)
        self.btn_redo.setEnabled(self.history_index < len(self.history) - 1)
        has = self.current_image is not None
        self.btn_reset.setEnabled(has)
        self.btn_save_image.setEnabled(has)

    def undo(self):
        if self.history_index > 0:
            self.history_index -= 1
            self.current_image = self.history[self.history_index].copy()
            self.show_original = False
            self._reset_sliders()
            self._update_compare_buttons()
            self.display_current_image()
            self._update_undo_redo_buttons()
            self.statusBar().showMessage("↩ Undo", 1500)

    def redo(self):
        if self.history_index < len(self.history) - 1:
            self.history_index += 1
            self.current_image = self.history[self.history_index].copy()
            self.show_original = False
            self._reset_sliders()
            self._update_compare_buttons()
            self.display_current_image()
            self._update_undo_redo_buttons()
            self.statusBar().showMessage("↪ Redo", 1500)

    def reset_image(self):
        if self.original_image is None:
            return
        self.current_image = self.original_image.copy()
        self.history = [self.original_image.copy()]
        self.history_index = 0
        self.show_original = False
        self._reset_sliders()
        self._update_compare_buttons()
        self.display_current_image()
        self._update_undo_redo_buttons()
        self.statusBar().showMessage("↺ به حالت اصلی بازگشت", 2500)

    def _reset_sliders(self):
        self.brightness_slider.blockSignals(True)
        self.contrast_slider.blockSignals(True)
        self.brightness_slider.setValue(0)
        self.contrast_slider.setValue(0)
        self.brightness_value.setText("0")
        self.contrast_value.setText("0")
        self.brightness_slider.blockSignals(False)
        self.contrast_slider.blockSignals(False)

    def _on_live_adjust(self):
        if self.current_image is None or self.history_index < 0:
            return
        base = self.history[self.history_index].copy()
        b = self.brightness_slider.value()
        c = self.contrast_slider.value()
        self.brightness_value.setText(str(b))
        self.contrast_value.setText(str(c))
        img = base
        if b != 0:
            img = ImageEnhance.Brightness(img).enhance(1.0 + b / 100.0)
        if c != 0:
            img = ImageEnhance.Contrast(img).enhance(1.0 + c / 100.0)
        self.current_image = img
        self.show_original = False
        self.display_current_image()

    def apply_live_adjustments(self):
        if self.current_image is None:
            return
        if self.brightness_slider.value() == 0 and self.contrast_slider.value() == 0:
            return
        self._push_history(self.current_image)
        self._reset_sliders()
        self.statusBar().showMessage("✓ تنظیمات زنده اعمال شد", 2500)

    def apply_filter(self, code):
        if self.current_image is None:
            QMessageBox.warning(self, "توجه", "ابتدا یک تصویر باز کنید.")
            return
        try:
            img = self.current_image.copy()
            if code == "BLUR":
                img = img.filter(ImageFilter.BLUR)
            elif code == "CONTOUR":
                img = img.filter(ImageFilter.CONTOUR)
            elif code == "DETAIL":
                img = img.filter(ImageFilter.DETAIL)
            elif code == "EMBOSS":
                img = img.filter(ImageFilter.EMBOSS)
            elif code == "SHARPEN":
                img = img.filter(ImageFilter.SHARPEN)
            elif code == "GRAYSCALE":
                img = ImageOps.grayscale(img).convert("RGB")
            elif code == "SEPIA":
                img = self._sepia(img)
            elif code == "NEGATIVE":
                img = ImageOps.invert(img)
            elif code == "VINTAGE":
                img = self._vintage(img)
            elif code == "ENHANCE_QUALITY_H":
                img = ImageEnhance.Sharpness(img).enhance(2.0)
                img = ImageEnhance.Contrast(img).enhance(1.3)
            elif code == "ENHANCE_QUALITY_M":
                img = ImageEnhance.Sharpness(img).enhance(1.4)
                img = ImageEnhance.Contrast(img).enhance(1.15)
            elif code == "COLOR_ADJUST_H":
                img = ImageEnhance.Color(img).enhance(1.5)
            elif code == "COLOR_ADJUST_L":
                img = ImageEnhance.Color(img).enhance(0.7)
            elif code == "ROTATE_N":
                img = img.rotate(-90, expand=True)
            elif code == "ROTATE_S":
                img = img.rotate(180, expand=True)
            elif code == "ROTATE_D":
                img = img.rotate(90, expand=True)
            elif code == "FLIP_H":
                img = ImageOps.mirror(img)
            elif code == "FLIP_V":
                img = ImageOps.flip(img)
            elif code == "RESIZE_S":
                w, h = img.size
                img = img.resize((max(1, w // 2), max(1, h // 2)), Image.Resampling.LANCZOS)
            elif code == "RESIZE_L":
                w, h = img.size
                img = img.resize((w * 2, h * 2), Image.Resampling.LANCZOS)
            elif code == "AUTO_ENHANCE":
                img = ImageOps.autocontrast(img, cutoff=2)
                img = ImageEnhance.Color(img).enhance(1.15)
                img = ImageEnhance.Sharpness(img).enhance(1.25)
            elif code == "CROP_SQUARE":
                img = self._crop_ratio(img, 1.0)
            elif code == "CROP_16_9":
                img = self._crop_ratio(img, 16 / 9)
            elif code == "CROP_4_3":
                img = self._crop_ratio(img, 4 / 3)

            self.current_image = img
            self.show_original = False
            self._push_history(img)
            self._reset_sliders()
            self._update_compare_buttons()
            self.display_current_image()
            self.statusBar().showMessage("✓ اعمال شد", 2000)
        except Exception as e:
            QMessageBox.warning(self, "خطا", f"خطا در اعمال:\n{e}")

    def _crop_ratio(self, img, ratio):
        """Center crop to the given width/height ratio."""
        w, h = img.size
        current = w / h
        if abs(current - ratio) < 0.01:
            return img
        if current > ratio:
            # too wide → crop width
            new_w = int(h * ratio)
            left = (w - new_w) // 2
            return img.crop((left, 0, left + new_w, h))
        else:
            # too tall → crop height
            new_h = int(w / ratio)
            top = (h - new_h) // 2
            return img.crop((0, top, w, top + new_h))

    def _sepia(self, img):
        img = img.convert("RGB")
        px = img.load()
        for y in range(img.height):
            for x in range(img.width):
                r, g, b = px[x, y]
                tr = int(0.393 * r + 0.769 * g + 0.189 * b)
                tg = int(0.349 * r + 0.686 * g + 0.168 * b)
                tb = int(0.272 * r + 0.534 * g + 0.131 * b)
                px[x, y] = (min(tr, 255), min(tg, 255), min(tb, 255))
        return img

    def _vintage(self, img):
        img = ImageEnhance.Color(img).enhance(0.6)
        img = ImageEnhance.Contrast(img).enhance(1.2)
        return ImageOps.autocontrast(img)

    def save_image(self):
        if self.current_image is None:
            return
        default = "edited.png"
        if self.current_image_path:
            p = Path(self.current_image_path)
            default = f"{p.stem}_edited{p.suffix}"
        path, _ = QFileDialog.getSaveFileName(
            self, "ذخیره تصویر", default,
            "PNG (*.png);;JPEG (*.jpg *.jpeg);;WebP (*.webp);;All Files (*)"
        )
        if path:
            try:
                self.current_image.save(path)
                self.statusBar().showMessage(f"✓ ذخیره شد: {path}", 4000)
                QMessageBox.information(self, "موفق", f"تصویر ذخیره شد:\n{path}")
            except Exception as e:
                QMessageBox.warning(self, "خطا", str(e))

    # ------------------------------------------------------------------
    # Video
    # ------------------------------------------------------------------
    def open_video(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "انتخاب ویدیو", "",
            "Videos (*.mp4 *.mkv *.avi *.mov *.webm);;All Files (*)"
        )
        if not path:
            return
        try:
            clip = VideoFileClip(path)
            self.video_duration = clip.duration
            self.current_video_path = path
            thumb = CACHE_DIR / f"vid_thumb_{time.time_ns()}.png"
            clip.save_frame(str(thumb), t=min(1.0, self.video_duration / 2))
            clip.close()
            self.display_image(self.video_preview_label, str(thumb))
            mins, secs = divmod(int(self.video_duration), 60)
            hours, mins = divmod(mins, 60)
            self.video_info_label.setText(
                f"<b>{Path(path).name}</b><br>"
                f"مدت: {hours:02d}:{mins:02d}:{secs:02d}"
            )
            self.trim_end_input.setText(f"{hours:02d}:{mins:02d}:{secs:02d}")
            self.statusBar().showMessage(f"✓ ویدیو بارگذاری شد • {self.video_duration:.1f}s", 4000)
        except Exception as e:
            QMessageBox.warning(self, "خطا", str(e))

    def start_trim_video(self):
        if not self.current_video_path:
            QMessageBox.warning(self, "خطا", "ابتدا یک ویدیو انتخاب کنید.")
            return
        if not FFMPEG_PATH:
            QMessageBox.warning(self, "خطا", "FFmpeg پیدا نشد.")
            return
        start = self.parse_time_to_secs(self.trim_start_input.text())
        end = self.parse_time_to_secs(self.trim_end_input.text())
        if start is None or end is None:
            QMessageBox.warning(self, "خطا", "فرمت زمان نامعتبر (HH:MM:SS)")
            return
        if start >= end or start < 0 or end > self.video_duration + 0.5:
            QMessageBox.warning(self, "خطا", "بازه زمانی نامعتبر است.")
            return
        out = str(CACHE_DIR / f"trimmed_{time.time_ns()}.mp4")
        self.video_progress.setVisible(True)
        self.video_progress.setValue(0)
        self.statusBar().showMessage("⏳ در حال برش...")
        self.thread = ProgressThread('trim', self.current_video_path, start, end, out)
        self.thread.progress_signal.connect(self.video_progress.setValue)
        self.thread.finished_signal.connect(self.finish_trim_video)
        self.thread.error_signal.connect(lambda m: QMessageBox.warning(self, "خطا", m))
        self.thread.start()

    def finish_trim_video(self, output_path):
        self.video_progress.setVisible(False)
        if output_path and Path(output_path).exists():
            try:
                thumb = CACHE_DIR / f"trim_thumb_{time.time_ns()}.png"
                t = VideoFileClip(output_path)
                t.save_frame(str(thumb), t=min(1.0, t.duration / 2))
                t.close()
                self.display_image(self.video_preview_label, str(thumb))
            except Exception:
                pass
            save, _ = QFileDialog.getSaveFileName(
                self, "ذخیره ویدیو", Path(self.current_video_path).stem + "_trimmed.mp4", "MP4 (*.mp4)"
            )
            if save:
                try:
                    shutil.move(output_path, save)
                    self.statusBar().showMessage("✓ ویدیو ذخیره شد", 5000)
                    QMessageBox.information(self, "موفق", f"ذخیره شد:\n{save}")
                except Exception as e:
                    QMessageBox.warning(self, "خطا", str(e))
            else:
                Path(output_path).unlink(missing_ok=True)
        else:
            QMessageBox.warning(self, "خطا", "برش ناموفق بود.")

    def start_convert_to_mp3(self):
        if not self.current_video_path:
            QMessageBox.warning(self, "خطا", "ابتدا یک ویدیو انتخاب کنید.")
            return
        if not FFMPEG_PATH:
            QMessageBox.warning(self, "خطا", "FFmpeg پیدا نشد.")
            return
        out = str(CACHE_DIR / f"converted_{time.time_ns()}.mp3")
        self.video_progress.setVisible(True)
        self.video_progress.setValue(0)
        self.statusBar().showMessage("⏳ در حال استخراج صدا...")
        self.thread = ProgressThread('mp3', self.current_video_path, out)
        self.thread.progress_signal.connect(self.video_progress.setValue)
        self.thread.finished_signal.connect(self.finish_convert_to_mp3)
        self.thread.error_signal.connect(lambda m: QMessageBox.warning(self, "خطا", m))
        self.thread.start()

    def finish_convert_to_mp3(self, output_path):
        self.video_progress.setVisible(False)
        if output_path and Path(output_path).exists():
            save, _ = QFileDialog.getSaveFileName(
                self, "ذخیره MP3", Path(self.current_video_path).stem + ".mp3", "MP3 (*.mp3)"
            )
            if save:
                try:
                    shutil.move(output_path, save)
                    self.statusBar().showMessage("✓ MP3 ذخیره شد", 5000)
                    QMessageBox.information(self, "موفق", f"ذخیره شد:\n{save}")
                except Exception as e:
                    QMessageBox.warning(self, "خطا", str(e))
            else:
                Path(output_path).unlink(missing_ok=True)
        else:
            QMessageBox.warning(self, "خطا", "تبدیل ناموفق بود.")

    def parse_time_to_secs(self, s):
        try:
            parts = s.strip().split(':')
            if len(parts) == 3:
                h, m, sec = map(int, parts)
                return h * 3600 + m * 60 + sec
            if len(parts) == 2:
                m, sec = map(int, parts)
                return m * 60 + sec
            return None
        except Exception:
            return None

    def display_image(self, label, path):
        pix = QPixmap(path)
        if pix.isNull():
            label.setText("خطا در بارگذاری")
        else:
            target = label.size()
            if target.width() < 80 or target.height() < 60:
                target.setWidth(max(280, target.width()))
                target.setHeight(max(220, target.height()))
            label.setPixmap(pix.scaled(target, Qt.AspectRatioMode.KeepAspectRatio,
                                       Qt.TransformationMode.SmoothTransformation))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, 'current_image') and self.current_image is not None:
            self.display_current_image()

    def closeEvent(self, event):
        try:
            for pat in ("preview_*", "vid_thumb_*", "trim_thumb_*", "orig_thumb_*"):
                for f in CACHE_DIR.glob(pat):
                    f.unlink(missing_ok=True)
        except Exception:
            pass
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(__version__)
    app.setOrganizationName(ORG_NAME)
    window = MediaEditor()
    window.show()
    sys.exit(app.exec())
