#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Desktop Media Editor
A bilingual (Persian/English) desktop app for basic image & video editing.
"""

import sys
import os
import time
import shutil
import subprocess
import shutil as sh
from pathlib import Path

from moviepy import VideoFileClip
from PIL import Image, ImageFilter, ImageEnhance, ImageOps
from PyQt6.QtWidgets import (
    QMainWindow, QApplication, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QFileDialog, QProgressBar, QMessageBox,
    QSplitter, QGridLayout, QGroupBox, QCheckBox, QSpacerItem, QSizePolicy,
    QComboBox, QSpinBox, QSlider, QStatusBar, QToolButton, QFrame
)
from PyQt6.QtGui import QPixmap, QIcon, QAction, QFont
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSettings, QSize

__version__ = "0.2.0"
APP_NAME = "Desktop Media Editor"
ORG_NAME = "KeyvanAlavi"

# ---------------------------------------------------------------------------
# FFmpeg discovery (cross-platform)
# ---------------------------------------------------------------------------
def find_ffmpeg():
    """Try to locate ffmpeg binary. Prefer local folder, then system PATH."""
    if getattr(sys, 'frozen', False):
        base_dir = Path(sys._MEIPASS)
    else:
        base_dir = Path(__file__).resolve().parent

    local_candidates = [
        base_dir / "ffmpeg" / "ffmpeg.exe",
        base_dir / "ffmpeg" / "ffmpeg",
        base_dir / "ffmpeg.exe",
        base_dir / "ffmpeg",
    ]
    for p in local_candidates:
        if p.exists():
            return str(p)

    # Fall back to system PATH
    system = sh.which("ffmpeg")
    if system:
        return system
    return None


def find_ffprobe():
    if getattr(sys, 'frozen', False):
        base_dir = Path(sys._MEIPASS)
    else:
        base_dir = Path(__file__).resolve().parent

    local_candidates = [
        base_dir / "ffmpeg" / "ffprobe.exe",
        base_dir / "ffmpeg" / "ffprobe",
        base_dir / "ffprobe.exe",
        base_dir / "ffprobe",
    ]
    for p in local_candidates:
        if p.exists():
            return str(p)

    system = sh.which("ffprobe")
    if system:
        return system
    return None


FFMPEG_PATH = find_ffmpeg()
FFPROBE_PATH = find_ffprobe()

if FFMPEG_PATH:
    os.environ["FFMPEG_BINARY"] = FFMPEG_PATH
if FFPROBE_PATH:
    os.environ["FFPROBE_BINARY"] = FFPROBE_PATH

CACHE_DIR = Path("cache")
CACHE_DIR.mkdir(exist_ok=True)


# ---------------------------------------------------------------------------
# Background worker
# ---------------------------------------------------------------------------
class ProgressThread(QThread):
    progress_signal = pyqtSignal(int)
    finished_signal = pyqtSignal(object)  # path or None
    error_signal = pyqtSignal(str)

    def __init__(self, task, *args):
        super().__init__()
        self.task = task
        self.args = args

    def run(self):
        try:
            if self.task == 'trim':
                success = self.trim_video(*self.args)
                self.finished_signal.emit(self.args[3] if success else None)
            elif self.task == 'mp3':
                success = self.convert_to_mp3(*self.args)
                self.finished_signal.emit(self.args[1] if success else None)
        except Exception as e:
            self.error_signal.emit(str(e))
            self.finished_signal.emit(None)

    def trim_video(self, input_path, start_secs, end_secs, output_path):
        if not FFMPEG_PATH:
            self.error_signal.emit("FFmpeg پیدا نشد. لطفاً آن را نصب کنید یا در پوشه ffmpeg قرار دهید.")
            return False
        try:
            duration = end_secs - start_secs
            cmd = [
                FFMPEG_PATH,
                '-i', input_path,
                '-ss', str(start_secs),
                '-t', str(duration),
                '-c:v', 'copy',
                '-c:a', 'copy',
                '-y',
                output_path
            ]
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            self.progress_signal.emit(100)
            return Path(output_path).exists()
        except subprocess.CalledProcessError as e:
            self.error_signal.emit(e.stderr or str(e))
            return False
        except Exception as e:
            self.error_signal.emit(str(e))
            return False

    def convert_to_mp3(self, input_path, output_path):
        if not FFMPEG_PATH:
            self.error_signal.emit("FFmpeg پیدا نشد. لطفاً آن را نصب کنید یا در پوشه ffmpeg قرار دهید.")
            return False
        try:
            cmd = [
                FFMPEG_PATH, '-i', input_path,
                '-vn', '-acodec', 'libmp3lame', '-q:a', '2',
                '-y', output_path
            ]
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            self.progress_signal.emit(100)
            return True
        except Exception as e:
            self.error_signal.emit(str(e))
            return False


# ---------------------------------------------------------------------------
# Main Window
# ---------------------------------------------------------------------------
class MediaEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME}  v{__version__}")
        self.setWindowIcon(QIcon("edit.ico"))
        self.setGeometry(80, 60, 1100, 680)
        self.setMinimumSize(900, 560)

        self.settings = QSettings(ORG_NAME, "MediaEditor")

        # Load settings
        self.is_dark_mode = self.settings.value("dark_mode", False, type=bool)
        self.theme = self.settings.value("theme", "Default", type=str)
        self.font_size = self.settings.value("font_size", 13, type=int)

        # Themes – refined colors
        self.themes = {
            "Default": {
                "main_bg": "#f7f8fa",
                "button_bg": "#0d9488",
                "button_hover": "#0f766e",
                "button_pressed": "#115e59",
                "text_color": "#1e293b",
                "muted_text": "#64748b",
                "border_color": "#e2e8f0",
                "tab_bg": "#e2e8f0",
                "tab_selected_bg": "#ffffff",
                "tab_selected_border": "#0d9488",
                "preview_bg": "#ffffff",
                "group_bg": "#ffffff",
                "accent": "#0d9488",
            },
            "Dark": {
                "main_bg": "#0f172a",
                "button_bg": "#14b8a6",
                "button_hover": "#0d9488",
                "button_pressed": "#0f766e",
                "text_color": "#e2e8f0",
                "muted_text": "#94a3b8",
                "border_color": "#1e293b",
                "tab_bg": "#1e293b",
                "tab_selected_bg": "#0f172a",
                "tab_selected_border": "#14b8a6",
                "preview_bg": "#1e293b",
                "group_bg": "#1e293b",
                "accent": "#14b8a6",
            },
            "Blue": {
                "main_bg": "#eff6ff",
                "button_bg": "#2563eb",
                "button_hover": "#1d4ed8",
                "button_pressed": "#1e40af",
                "text_color": "#1e3a8a",
                "muted_text": "#64748b",
                "border_color": "#bfdbfe",
                "tab_bg": "#dbeafe",
                "tab_selected_bg": "#ffffff",
                "tab_selected_border": "#2563eb",
                "preview_bg": "#ffffff",
                "group_bg": "#ffffff",
                "accent": "#2563eb",
            },
            "Green": {
                "main_bg": "#f0fdf4",
                "button_bg": "#16a34a",
                "button_hover": "#15803d",
                "button_pressed": "#166534",
                "text_color": "#14532d",
                "muted_text": "#64748b",
                "border_color": "#bbf7d0",
                "tab_bg": "#dcfce7",
                "tab_selected_bg": "#ffffff",
                "tab_selected_border": "#16a34a",
                "preview_bg": "#ffffff",
                "group_bg": "#ffffff",
                "accent": "#16a34a",
            },
        }

        self.filters = [
            ("Blur", "BLUR"), ("Contour", "CONTOUR"), ("Detail", "DETAIL"),
            ("Emboss", "EMBOSS"), ("Sharpen", "SHARPEN"), ("Grayscale", "GRAYSCALE"),
            ("Sepia", "SEPIA"), ("Negative", "NEGATIVE"), ("Vintage", "VINTAGE"),
        ]
        self.quality_buttons = [
            ("Enhance High", "ENHANCE_QUALITY_H"),
            ("Enhance Medium", "ENHANCE_QUALITY_M"),
            ("Color Boost", "COLOR_ADJUST_H"),
            ("Color Soft", "COLOR_ADJUST_L"),
        ]

        # Image state
        self.original_image = None
        self.current_image = None
        self.current_image_path = None
        self.history = []          # list of PIL Images
        self.history_index = -1
        self.max_history = 20

        # Video state
        self.current_video_path = None
        self.video_duration = 0.0

        self.current_columns = 2

        self.apply_theme()
        self._build_ui()
        self._update_undo_redo_buttons()

        # Status
        if FFMPEG_PATH:
            self.statusBar().showMessage(f"آماده • FFmpeg: {Path(FFMPEG_PATH).name}", 5000)
        else:
            self.statusBar().showMessage("هشدار: FFmpeg پیدا نشد – قابلیت‌های ویدیو محدود خواهند بود", 8000)

    # ------------------------------------------------------------------
    # Theme & Styles
    # ------------------------------------------------------------------
    def apply_theme(self):
        t = self.themes[self.theme]
        stylesheet = f"""
            QMainWindow {{
                background-color: {t['main_bg']};
                font-family: 'Segoe UI', 'Vazirmatn', 'Tahoma', sans-serif;
                font-size: {self.font_size}px;
                color: {t['text_color']};
            }}
            QStatusBar {{
                background-color: {t['group_bg']};
                color: {t['muted_text']};
                border-top: 1px solid {t['border_color']};
                font-size: {self.font_size - 1}px;
            }}
            QPushButton {{
                background-color: {t['button_bg']};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 14px;
                font-size: {self.font_size}px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {t['button_hover']};
            }}
            QPushButton:pressed {{
                background-color: {t['button_pressed']};
            }}
            QPushButton:disabled {{
                background-color: {t['border_color']};
                color: {t['muted_text']};
            }}
            QToolButton {{
                background-color: {t['button_bg']};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 6px 12px;
                font-weight: 600;
            }}
            QToolButton:hover {{
                background-color: {t['button_hover']};
            }}
            QToolButton:disabled {{
                background-color: {t['border_color']};
                color: {t['muted_text']};
            }}
            QLabel {{
                font-size: {self.font_size}px;
                color: {t['text_color']};
                font-weight: 500;
            }}
            QLineEdit, QSpinBox, QComboBox {{
                border: 1px solid {t['border_color']};
                border-radius: 7px;
                padding: 6px 10px;
                background-color: {t['preview_bg']};
                font-size: {self.font_size}px;
                color: {t['text_color']};
                selection-background-color: {t['accent']};
            }}
            QLineEdit:focus, QSpinBox:focus, QComboBox:focus {{
                border: 2px solid {t['accent']};
            }}
            QSlider::groove:horizontal {{
                height: 6px;
                background: {t['border_color']};
                border-radius: 3px;
            }}
            QSlider::handle:horizontal {{
                background: {t['accent']};
                width: 16px;
                height: 16px;
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
                font-size: {self.font_size - 2}px;
                color: {t['text_color']};
                height: 18px;
            }}
            QProgressBar::chunk {{
                background-color: {t['button_bg']};
                border-radius: 6px;
            }}
            QGroupBox {{
                background-color: {t['group_bg']};
                border: 1px solid {t['border_color']};
                border-radius: 10px;
                margin-top: 14px;
                padding: 12px 10px 10px 10px;
                font-weight: 700;
                color: {t['text_color']};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 6px;
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
                padding: 9px 18px;
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
                border-radius: 10px;
            }}
        """
        self.setStyleSheet(stylesheet)

    def save_settings(self):
        self.settings.setValue("dark_mode", self.is_dark_mode)
        self.settings.setValue("theme", self.theme)
        self.settings.setValue("font_size", self.font_size)
        self.apply_theme()
        self.statusBar().showMessage("تنظیمات ذخیره شد", 2500)

    # ------------------------------------------------------------------
    # UI Construction
    # ------------------------------------------------------------------
    def _build_ui(self):
        self.tab_widget = QTabWidget()
        self.setCentralWidget(self.tab_widget)

        self.image_tab = QWidget()
        self.video_tab = QWidget()
        self.settings_tab = QWidget()

        self.tab_widget.addTab(self.image_tab, "ویرایش تصویر")
        self.tab_widget.addTab(self.video_tab, "ویرایش ویدیو")
        self.tab_widget.addTab(self.settings_tab, "تنظیمات")

        self.init_image_tab()
        self.init_video_tab()
        self.init_settings_tab()

        # Status bar
        self.setStatusBar(QStatusBar())

    def init_image_tab(self):
        main_layout = QHBoxLayout(self.image_tab)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(12)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        # ---------- Left controls ----------
        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(10)

        # File actions
        file_group = QGroupBox("فایل")
        file_l = QHBoxLayout()
        self.btn_open_image = QPushButton("باز کردن تصویر")
        self.btn_open_image.setToolTip("یک تصویر انتخاب کنید (Ctrl+O)")
        self.btn_open_image.clicked.connect(self.open_image)
        self.btn_save_image = QPushButton("ذخیره")
        self.btn_save_image.setToolTip("ذخیره تصویر ویرایش‌شده")
        self.btn_save_image.clicked.connect(self.save_image)
        self.btn_save_image.setEnabled(False)
        file_l.addWidget(self.btn_open_image)
        file_l.addWidget(self.btn_save_image)
        file_group.setLayout(file_l)
        left_layout.addWidget(file_group)

        # Undo / Redo + Reset
        hist_group = QGroupBox("تاریخچه")
        hist_l = QHBoxLayout()
        self.btn_undo = QPushButton("↩ Undo")
        self.btn_undo.setToolTip("بازگشت یک مرحله (Ctrl+Z)")
        self.btn_undo.clicked.connect(self.undo)
        self.btn_redo = QPushButton("Redo ↪")
        self.btn_redo.setToolTip("جلو رفتن یک مرحله (Ctrl+Y)")
        self.btn_redo.clicked.connect(self.redo)
        self.btn_reset = QPushButton("بازنشانی")
        self.btn_reset.setToolTip("بازگشت به تصویر اصلی")
        self.btn_reset.clicked.connect(self.reset_image)
        hist_l.addWidget(self.btn_undo)
        hist_l.addWidget(self.btn_redo)
        hist_l.addWidget(self.btn_reset)
        hist_group.setLayout(hist_l)
        left_layout.addWidget(hist_group)

        # Live adjustments
        adj_group = QGroupBox("تنظیمات زنده")
        adj_l = QVBoxLayout()
        adj_l.setSpacing(8)

        # Brightness
        br_row = QHBoxLayout()
        br_row.addWidget(QLabel("روشنایی"))
        self.brightness_slider = QSlider(Qt.Orientation.Horizontal)
        self.brightness_slider.setRange(-100, 100)
        self.brightness_slider.setValue(0)
        self.brightness_slider.setToolTip("مقدار روشنایی را تغییر دهید")
        self.brightness_slider.valueChanged.connect(self._on_live_adjust)
        self.brightness_value = QLabel("0")
        self.brightness_value.setFixedWidth(30)
        br_row.addWidget(self.brightness_slider)
        br_row.addWidget(self.brightness_value)
        adj_l.addLayout(br_row)

        # Contrast
        ct_row = QHBoxLayout()
        ct_row.addWidget(QLabel("کنتراست"))
        self.contrast_slider = QSlider(Qt.Orientation.Horizontal)
        self.contrast_slider.setRange(-100, 100)
        self.contrast_slider.setValue(0)
        self.contrast_slider.setToolTip("مقدار کنتراست را تغییر دهید")
        self.contrast_slider.valueChanged.connect(self._on_live_adjust)
        self.contrast_value = QLabel("0")
        self.contrast_value.setFixedWidth(30)
        ct_row.addWidget(self.contrast_slider)
        ct_row.addWidget(self.contrast_value)
        adj_l.addLayout(ct_row)

        btn_apply_live = QPushButton("اعمال تنظیمات زنده")
        btn_apply_live.setToolTip("مقدار فعلی اسلایدرها را روی تصویر اعمال و در تاریخچه ذخیره می‌کند")
        btn_apply_live.clicked.connect(self.apply_live_adjustments)
        adj_l.addWidget(btn_apply_live)

        adj_group.setLayout(adj_l)
        left_layout.addWidget(adj_group)

        # Filters
        filters_group = QGroupBox("فیلترها")
        filters_group.setObjectName("filters_group")
        filters_layout = QGridLayout()
        filters_layout.setSpacing(6)
        num_columns = 3
        for i, (name, code) in enumerate(self.filters):
            btn = QPushButton(name)
            btn.setToolTip(f"اعمال فیلتر {name}")
            btn.clicked.connect(lambda _, c=code: self.apply_filter(c))
            filters_layout.addWidget(btn, i // num_columns, i % num_columns)
        filters_group.setLayout(filters_layout)
        left_layout.addWidget(filters_group)

        # Quality / Enhance
        quality_group = QGroupBox("بهبود کیفیت")
        quality_group.setObjectName("quality_group")
        quality_layout = QGridLayout()
        quality_layout.setSpacing(6)
        for i, (name, code) in enumerate(self.quality_buttons):
            btn = QPushButton(name)
            btn.setToolTip(name)
            btn.clicked.connect(lambda _, c=code: self.apply_filter(c))
            quality_layout.addWidget(btn, i // 2, i % 2)
        quality_group.setLayout(quality_layout)
        left_layout.addWidget(quality_group)

        # Rotate & Resize
        transform_group = QGroupBox("چرخش و اندازه")
        transform_l = QVBoxLayout()
        rot_row = QHBoxLayout()
        for name, code in [("۹۰°", "ROTATE_N"), ("۱۸۰°", "ROTATE_S"), ("۲۷۰°", "ROTATE_D")]:
            btn = QPushButton(name)
            btn.setToolTip(f"چرخش {name}")
            btn.clicked.connect(lambda _, c=code: self.apply_filter(c))
            rot_row.addWidget(btn)
        transform_l.addLayout(rot_row)

        size_row = QHBoxLayout()
        for name, code in [("کوچک‌تر", "RESIZE_S"), ("بزرگ‌تر", "RESIZE_L")]:
            btn = QPushButton(name)
            btn.setToolTip(name)
            btn.clicked.connect(lambda _, c=code: self.apply_filter(c))
            size_row.addWidget(btn)
        transform_l.addLayout(size_row)
        transform_group.setLayout(transform_l)
        left_layout.addWidget(transform_group)

        left_layout.addStretch()
        splitter.addWidget(left)

        # ---------- Right preview ----------
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)

        preview_frame = QFrame()
        preview_frame.setObjectName("previewFrame")
        preview_layout = QVBoxLayout(preview_frame)
        preview_layout.setContentsMargins(8, 8, 8, 8)

        self.image_preview_label = QLabel("تصویری انتخاب نشده\nبرای شروع روی «باز کردن تصویر» کلیک کنید")
        self.image_preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_preview_label.setMinimumSize(420, 360)
        self.image_preview_label.setStyleSheet("font-size: 14px;")
        preview_layout.addWidget(self.image_preview_label)

        right_layout.addWidget(preview_frame)
        splitter.addWidget(right)

        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        main_layout.addWidget(splitter)

    def init_video_tab(self):
        main_layout = QHBoxLayout(self.video_tab)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(12)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left
        left = QWidget()
        left_l = QVBoxLayout(left)
        left_l.setContentsMargins(0, 0, 0, 0)
        left_l.setSpacing(10)

        file_group = QGroupBox("فایل ویدیو")
        file_l = QVBoxLayout()
        self.btn_open_video = QPushButton("باز کردن ویدیو")
        self.btn_open_video.setToolTip("یک فایل ویدیو انتخاب کنید")
        self.btn_open_video.clicked.connect(self.open_video)
        file_l.addWidget(self.btn_open_video)
        self.video_info_label = QLabel("ویدیویی انتخاب نشده")
        self.video_info_label.setWordWrap(True)
        file_l.addWidget(self.video_info_label)
        file_group.setLayout(file_l)
        left_l.addWidget(file_group)

        # Trim
        trim_group = QGroupBox("برش ویدیو")
        trim_l = QVBoxLayout()
        time_row = QHBoxLayout()
        time_row.addWidget(QLabel("شروع (HH:MM:SS)"))
        self.trim_start_input = QLineEdit("00:00:00")
        self.trim_start_input.setPlaceholderText("00:00:00")
        time_row.addWidget(self.trim_start_input)
        trim_l.addLayout(time_row)

        time_row2 = QHBoxLayout()
        time_row2.addWidget(QLabel("پایان (HH:MM:SS)"))
        self.trim_end_input = QLineEdit("00:00:10")
        self.trim_end_input.setPlaceholderText("00:00:10")
        time_row2.addWidget(self.trim_end_input)
        trim_l.addLayout(time_row2)

        self.btn_trim = QPushButton("برش و ذخیره")
        self.btn_trim.setToolTip("ویدیو را در بازه مشخص برش بزنید")
        self.btn_trim.clicked.connect(self.start_trim_video)
        trim_l.addWidget(self.btn_trim)
        trim_group.setLayout(trim_l)
        left_l.addWidget(trim_group)

        # MP3
        mp3_group = QGroupBox("استخراج صدا")
        mp3_l = QVBoxLayout()
        self.btn_mp3 = QPushButton("تبدیل به MP3")
        self.btn_mp3.setToolTip("صدای ویدیو را به فایل MP3 استخراج کنید")
        self.btn_mp3.clicked.connect(self.start_convert_to_mp3)
        mp3_l.addWidget(self.btn_mp3)
        mp3_group.setLayout(mp3_l)
        left_l.addWidget(mp3_group)

        self.video_progress = QProgressBar()
        self.video_progress.setVisible(False)
        left_l.addWidget(self.video_progress)

        left_l.addStretch()
        splitter.addWidget(left)

        # Right preview
        right = QWidget()
        right_l = QVBoxLayout(right)
        right_l.setContentsMargins(0, 0, 0, 0)

        preview_frame = QFrame()
        preview_frame.setObjectName("previewFrame")
        preview_layout = QVBoxLayout(preview_frame)
        preview_layout.setContentsMargins(8, 8, 8, 8)

        self.video_preview_label = QLabel("ویدیویی انتخاب نشده")
        self.video_preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_preview_label.setMinimumSize(420, 360)
        preview_layout.addWidget(self.video_preview_label)

        right_l.addWidget(preview_frame)
        splitter.addWidget(right)

        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        main_layout.addWidget(splitter)

    def init_settings_tab(self):
        layout = QVBoxLayout(self.settings_tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # Theme
        theme_group = QGroupBox("تم و ظاهر")
        theme_l = QVBoxLayout()

        row1 = QHBoxLayout()
        row1.addWidget(QLabel("تم:"))
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Default", "Dark", "Blue", "Green"])
        self.theme_combo.setCurrentText(self.theme)
        self.theme_combo.currentTextChanged.connect(self._on_theme_changed)
        row1.addWidget(self.theme_combo)
        row1.addStretch()
        theme_l.addLayout(row1)

        row2 = QHBoxLayout()
        row2.addWidget(QLabel("اندازه فونت:"))
        self.font_spin = QSpinBox()
        self.font_spin.setRange(10, 20)
        self.font_spin.setValue(self.font_size)
        self.font_spin.valueChanged.connect(self._on_font_changed)
        row2.addWidget(self.font_spin)
        row2.addStretch()
        theme_l.addLayout(row2)

        theme_group.setLayout(theme_l)
        layout.addWidget(theme_group)

        # About
        about_group = QGroupBox("درباره برنامه")
        about_l = QVBoxLayout()
        about_text = QLabel(
            f"<b>{APP_NAME}</b><br>"
            f"نسخه: <b>{__version__}</b><br><br>"
            "ویرایشگر ساده تصویر و ویدیو با رابط دو زبانه.<br>"
            "توسعه‌دهنده اصلی: Keyvan Alavi<br><br>"
            "<i>در ارتقای این نسخه جدید از Grok (نسخه رایگان) نیز استفاده شده است.</i>"
        )
        about_text.setWordWrap(True)
        about_text.setTextFormat(Qt.TextFormat.RichText)
        about_l.addWidget(about_text)

        btn_clear_cache = QPushButton("پاک کردن کش")
        btn_clear_cache.setToolTip("فایل‌های موقت را حذف می‌کند")
        btn_clear_cache.clicked.connect(self.clear_cache)
        about_l.addWidget(btn_clear_cache)

        about_group.setLayout(about_l)
        layout.addWidget(about_group)

        layout.addStretch()

    # ------------------------------------------------------------------
    # Settings handlers
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
            self.statusBar().showMessage("کش پاک شد", 3000)
            QMessageBox.information(self, "موفق", "فایل‌های موقت حذف شدند.")
        except Exception as e:
            QMessageBox.warning(self, "خطا", f"خطا در پاک‌سازی: {e}")

    # ------------------------------------------------------------------
    # Image handling
    # ------------------------------------------------------------------
    def open_image(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "انتخاب تصویر",
            "", "Images (*.png *.jpg *.jpeg *.bmp *.webp *.tiff);;All Files (*)"
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
            self._reset_sliders()
            self.display_current_image()
            self.btn_save_image.setEnabled(True)
            self._update_undo_redo_buttons()
            self.statusBar().showMessage(f"تصویر بارگذاری شد: {Path(path).name}", 4000)
        except Exception as e:
            QMessageBox.warning(self, "خطا", f"نتوانست تصویر را باز کند:\n{e}")

    def display_current_image(self):
        if self.current_image is None:
            return
        # Save temp for QPixmap
        tmp = CACHE_DIR / f"preview_{time.time_ns()}.png"
        try:
            self.current_image.save(tmp, "PNG")
            pix = QPixmap(str(tmp))
            if not pix.isNull():
                scaled = pix.scaled(
                    self.image_preview_label.size(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                self.image_preview_label.setPixmap(scaled)
            tmp.unlink(missing_ok=True)
        except Exception:
            pass

    def _push_history(self, img):
        # Truncate forward history
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
        has_img = self.current_image is not None
        self.btn_reset.setEnabled(has_img)
        self.btn_save_image.setEnabled(has_img)

    def undo(self):
        if self.history_index > 0:
            self.history_index -= 1
            self.current_image = self.history[self.history_index].copy()
            self._reset_sliders()
            self.display_current_image()
            self._update_undo_redo_buttons()
            self.statusBar().showMessage("Undo", 1500)

    def redo(self):
        if self.history_index < len(self.history) - 1:
            self.history_index += 1
            self.current_image = self.history[self.history_index].copy()
            self._reset_sliders()
            self.display_current_image()
            self._update_undo_redo_buttons()
            self.statusBar().showMessage("Redo", 1500)

    def reset_image(self):
        if self.original_image is None:
            return
        self.current_image = self.original_image.copy()
        self.history = [self.original_image.copy()]
        self.history_index = 0
        self._reset_sliders()
        self.display_current_image()
        self._update_undo_redo_buttons()
        self.statusBar().showMessage("به حالت اصلی بازگشت", 2500)

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
        # Work from the last committed history state
        base = self.history[self.history_index].copy()
        b_val = self.brightness_slider.value()
        c_val = self.contrast_slider.value()
        self.brightness_value.setText(str(b_val))
        self.contrast_value.setText(str(c_val))

        img = base
        if b_val != 0:
            enhancer = ImageEnhance.Brightness(img)
            # map -100..100 → 0.0 .. 2.0
            factor = 1.0 + (b_val / 100.0)
            img = enhancer.enhance(factor)
        if c_val != 0:
            enhancer = ImageEnhance.Contrast(img)
            factor = 1.0 + (c_val / 100.0)
            img = enhancer.enhance(factor)
        self.current_image = img
        self.display_current_image()

    def apply_live_adjustments(self):
        if self.current_image is None:
            return
        if self.brightness_slider.value() == 0 and self.contrast_slider.value() == 0:
            return
        self._push_history(self.current_image)
        self._reset_sliders()
        self.statusBar().showMessage("تنظیمات زنده اعمال شد", 2500)

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
            elif code == "RESIZE_S":
                w, h = img.size
                img = img.resize((max(1, w // 2), max(1, h // 2)), Image.Resampling.LANCZOS)
            elif code == "RESIZE_L":
                w, h = img.size
                img = img.resize((w * 2, h * 2), Image.Resampling.LANCZOS)

            self.current_image = img
            self._push_history(img)
            self._reset_sliders()
            self.display_current_image()
            self.statusBar().showMessage(f"فیلتر {code} اعمال شد", 2000)
        except Exception as e:
            QMessageBox.warning(self, "خطا", f"خطا در اعمال فیلتر:\n{e}")

    def _sepia(self, img):
        img = img.convert("RGB")
        pixels = img.load()
        for y in range(img.height):
            for x in range(img.width):
                r, g, b = pixels[x, y]
                tr = int(0.393 * r + 0.769 * g + 0.189 * b)
                tg = int(0.349 * r + 0.686 * g + 0.168 * b)
                tb = int(0.272 * r + 0.534 * g + 0.131 * b)
                pixels[x, y] = (min(tr, 255), min(tg, 255), min(tb, 255))
        return img

    def _vintage(self, img):
        img = ImageEnhance.Color(img).enhance(0.6)
        img = ImageEnhance.Contrast(img).enhance(1.2)
        img = ImageOps.autocontrast(img)
        return img

    def save_image(self):
        if self.current_image is None:
            return
        default_name = "edited.png"
        if self.current_image_path:
            p = Path(self.current_image_path)
            default_name = f"{p.stem}_edited{p.suffix}"
        path, _ = QFileDialog.getSaveFileName(
            self, "ذخیره تصویر",
            default_name,
            "PNG (*.png);;JPEG (*.jpg *.jpeg);;WebP (*.webp);;All Files (*)"
        )
        if path:
            try:
                self.current_image.save(path)
                self.statusBar().showMessage(f"ذخیره شد: {path}", 4000)
                QMessageBox.information(self, "موفق", f"تصویر در مسیر زیر ذخیره شد:\n{path}")
            except Exception as e:
                QMessageBox.warning(self, "خطا", f"خطا در ذخیره:\n{e}")

    # ------------------------------------------------------------------
    # Video handling
    # ------------------------------------------------------------------
    def open_video(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "انتخاب ویدیو",
            "", "Videos (*.mp4 *.mkv *.avi *.mov *.webm);;All Files (*)"
        )
        if not path:
            return
        try:
            clip = VideoFileClip(path)
            self.video_duration = clip.duration
            self.current_video_path = path

            # Thumbnail
            thumb = CACHE_DIR / f"vid_thumb_{time.time_ns()}.png"
            clip.save_frame(str(thumb), t=min(1.0, self.video_duration / 2))
            clip.close()

            self.display_image(self.video_preview_label, str(thumb), video=True)
            mins, secs = divmod(int(self.video_duration), 60)
            hours, mins = divmod(mins, 60)
            self.video_info_label.setText(
                f"فایل: {Path(path).name}\n"
                f"مدت: {hours:02d}:{mins:02d}:{secs:02d}\n"
                f"مسیر: {path}"
            )
            self.trim_end_input.setText(f"{hours:02d}:{mins:02d}:{secs:02d}")
            self.statusBar().showMessage(f"ویدیو بارگذاری شد • {self.video_duration:.1f} ثانیه", 4000)
        except Exception as e:
            QMessageBox.warning(self, "خطا", f"نتوانست ویدیو را باز کند:\n{e}")

    def start_trim_video(self):
        if not self.current_video_path:
            QMessageBox.warning(self, "خطا", "ابتدا یک ویدیو انتخاب کنید.")
            return
        if not FFMPEG_PATH:
            QMessageBox.warning(self, "خطا", "FFmpeg پیدا نشد. لطفاً آن را نصب کنید.")
            return

        start_secs = self.parse_time_to_secs(self.trim_start_input.text())
        end_secs = self.parse_time_to_secs(self.trim_end_input.text())

        if start_secs is None or end_secs is None:
            QMessageBox.warning(self, "خطا", "فرمت زمان نامعتبر است. از HH:MM:SS استفاده کنید.")
            return
        if start_secs >= end_secs:
            QMessageBox.warning(self, "خطا", "زمان شروع باید کمتر از پایان باشد.")
            return
        if start_secs < 0 or end_secs > self.video_duration + 0.5:
            QMessageBox.warning(self, "خطا", "زمان‌ها خارج از محدوده ویدیو هستند.")
            return

        output_path = str(CACHE_DIR / f"trimmed_{time.time_ns()}.mp4")
        self.video_progress.setVisible(True)
        self.video_progress.setValue(0)
        self.statusBar().showMessage("در حال برش ویدیو...")

        self.thread = ProgressThread('trim', self.current_video_path, start_secs, end_secs, output_path)
        self.thread.progress_signal.connect(self.video_progress.setValue)
        self.thread.finished_signal.connect(self.finish_trim_video)
        self.thread.error_signal.connect(lambda msg: QMessageBox.warning(self, "خطای FFmpeg", msg))
        self.thread.start()

    def finish_trim_video(self, output_path):
        self.video_progress.setVisible(False)
        if output_path and Path(output_path).exists():
            try:
                thumb = CACHE_DIR / f"trim_thumb_{time.time_ns()}.png"
                temp = VideoFileClip(output_path)
                temp.save_frame(str(thumb), t=min(1.0, temp.duration / 2))
                temp.close()
                self.display_image(self.video_preview_label, str(thumb), video=True)
            except Exception:
                pass

            save_path, _ = QFileDialog.getSaveFileName(
                self, "ذخیره ویدیو برش‌خورده",
                Path(self.current_video_path).stem + "_trimmed.mp4",
                "MP4 (*.mp4)"
            )
            if save_path:
                try:
                    shutil.move(output_path, save_path)
                    self.statusBar().showMessage(f"ویدیو ذخیره شد: {save_path}", 5000)
                    QMessageBox.information(self, "موفق", f"ویدیو ذخیره شد:\n{save_path}")
                except Exception as e:
                    QMessageBox.warning(self, "خطا", f"خطا در ذخیره: {e}")
            else:
                Path(output_path).unlink(missing_ok=True)
        else:
            QMessageBox.warning(self, "خطا", "برش ویدیو ناموفق بود.")

    def start_convert_to_mp3(self):
        if not self.current_video_path:
            QMessageBox.warning(self, "خطا", "ابتدا یک ویدیو انتخاب کنید.")
            return
        if not FFMPEG_PATH:
            QMessageBox.warning(self, "خطا", "FFmpeg پیدا نشد.")
            return

        output_path = str(CACHE_DIR / f"converted_{time.time_ns()}.mp3")
        self.video_progress.setVisible(True)
        self.video_progress.setValue(0)
        self.statusBar().showMessage("در حال استخراج صدا...")

        self.thread = ProgressThread('mp3', self.current_video_path, output_path)
        self.thread.progress_signal.connect(self.video_progress.setValue)
        self.thread.finished_signal.connect(self.finish_convert_to_mp3)
        self.thread.error_signal.connect(lambda msg: QMessageBox.warning(self, "خطای FFmpeg", msg))
        self.thread.start()

    def finish_convert_to_mp3(self, output_path):
        self.video_progress.setVisible(False)
        if output_path and Path(output_path).exists():
            save_path, _ = QFileDialog.getSaveFileName(
                self, "ذخیره فایل MP3",
                Path(self.current_video_path).stem + ".mp3",
                "MP3 (*.mp3)"
            )
            if save_path:
                try:
                    shutil.move(output_path, save_path)
                    self.statusBar().showMessage(f"MP3 ذخیره شد: {save_path}", 5000)
                    QMessageBox.information(self, "موفق", f"فایل MP3 ذخیره شد:\n{save_path}")
                except Exception as e:
                    QMessageBox.warning(self, "خطا", f"خطا در ذخیره: {e}")
            else:
                Path(output_path).unlink(missing_ok=True)
        else:
            QMessageBox.warning(self, "خطا", "تبدیل به MP3 ناموفق بود.")

    def parse_time_to_secs(self, time_str):
        try:
            parts = time_str.strip().split(':')
            if len(parts) == 3:
                h, m, s = map(int, parts)
                return h * 3600 + m * 60 + s
            elif len(parts) == 2:
                m, s = map(int, parts)
                return m * 60 + s
            return None
        except Exception:
            return None

    def display_image(self, label, path, video=False):
        pix = QPixmap(path)
        if pix.isNull():
            label.setText("خطا در بارگذاری تصویر")
        else:
            label.setPixmap(
                pix.scaled(400, 300, Qt.AspectRatioMode.KeepAspectRatio,
                           Qt.TransformationMode.SmoothTransformation)
            )

    def closeEvent(self, event):
        # Clean cache on exit (optional – keep recent for now)
        try:
            for f in CACHE_DIR.glob("preview_*"):
                f.unlink(missing_ok=True)
            for f in CACHE_DIR.glob("vid_thumb_*"):
                f.unlink(missing_ok=True)
            for f in CACHE_DIR.glob("trim_thumb_*"):
                f.unlink(missing_ok=True)
        except Exception:
            pass
        event.accept()


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(__version__)
    app.setOrganizationName(ORG_NAME)

    window = MediaEditor()
    window.show()
    sys.exit(app.exec())
