import sys
import os
import time
import cv2
import shutil
from moviepy import VideoFileClip
from PIL import Image, ImageFilter, ImageEnhance, ImageOps
from PyQt6.QtWidgets import (
    QMainWindow, QApplication, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QFileDialog, QProgressBar, QMessageBox,
    QSplitter, QGridLayout, QGroupBox, QCheckBox, QSpacerItem, QSizePolicy,
    QComboBox, QSpinBox
)
from PyQt6.QtGui import QPixmap, QIcon
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSettings

CACHE_DIR = 'cache'
if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)

class ProgressThread(QThread):
    progress_signal = pyqtSignal(int)
    finished_signal = pyqtSignal(str)

    def __init__(self, task, *args):
        super().__init__()
        self.task = task
        self.args = args

    def run(self):
        if self.task == 'trim':
            success = self.trim_video(*self.args)
            if success:
                self.finished_signal.emit(self.args[3])  # output_path
            else:
                self.finished_signal.emit(None)
        elif self.task == 'mp3':
            success = self.convert_to_mp3(*self.args)
            if success:
                self.finished_signal.emit(self.args[1])  # output_path
            else:
                self.finished_signal.emit(None)

    def trim_video(self, input_path, start_secs, end_secs, output_path):
        try:
            cap = cv2.VideoCapture(input_path)
            fps = cap.get(cv2.CAP_PROP_FPS)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

            start_frame = int(start_secs * fps)
            end_frame = int(end_secs * fps)

            if start_frame >= end_frame or end_frame > total_frames:
                return False

            out = cv2.VideoWriter(output_path, cv2.VideoWriter_fourcc(*'mp4v'), fps, (width, height))
            cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)

            frame_count = end_frame - start_frame
            for i in range(frame_count):
                ret, frame = cap.read()
                if not ret:
                    break
                out.write(frame)
                self.progress_signal.emit(int((i + 1) / frame_count * 100))

            cap.release()
            out.release()
            return os.path.exists(output_path)
        except Exception:
            return False

    def convert_to_mp3(self, input_path, output_path):
        try:
            video = VideoFileClip(input_path)
            video.audio.write_audiofile(output_path)
            video.close()
            self.progress_signal.emit(100)
            return True
        except Exception:
            return False

class MediaEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ویرایشگر تصویر و ویدئو")
        self.setWindowIcon(QIcon("edit.ico"))
        self.setGeometry(100, 100, 1000, 600)
        self.settings = QSettings("xAI", "MediaEditor")

        # Load saved settings
        self.is_dark_mode = self.settings.value("dark_mode", False, type=bool)
        self.theme = self.settings.value("theme", "Default", type=str)
        self.font_size = self.settings.value("font_size", 13, type=int)

        # Define themes
        self.themes = {
            "Default": {
                "main_bg": "#faf9f6",
                "button_bg": "#00bfa5",
                "button_hover": "#00997a",
                "text_color": "#333",
                "border_color": "#ddd",
                "tab_bg": "#f0f0f0",
                "tab_selected_bg": "white",
                "tab_selected_border": "#00bfa5",
                "preview_bg": "white"
            },
            "Dark": {
                "main_bg": "#2c2c2c",
                "button_bg": "#00bfa5",
                "button_hover": "#00997a",
                "text_color": "#ddd",
                "border_color": "#444",
                "tab_bg": "#3c3c3c",
                "tab_selected_bg": "#2c2c2c",
                "tab_selected_border": "#00bfa5",
                "preview_bg": "#3c3c3c"
            },
            "Blue": {
                "main_bg": "#e3f2fd",
                "button_bg": "#1976d2",
                "button_hover": "#1565c0",
                "text_color": "#333",
                "border_color": "#bbdefb",
                "tab_bg": "#bbdefb",
                "tab_selected_bg": "white",
                "tab_selected_border": "#1976d2",
                "preview_bg": "white"
            },
            "Green": {
                "main_bg": "#e8f5e9",
                "button_bg": "#388e3c",
                "button_hover": "#2e7d32",
                "text_color": "#333",
                "border_color": "#c8e6c9",
                "tab_bg": "#c8e6c9",
                "tab_selected_bg": "white",
                "tab_selected_border": "#388e3c",
                "preview_bg": "white"
            }
        }

        # Define filters and quality buttons
        self.filters = [
            ("Blur", "BLUR"), ("Contour", "CONTOUR"), ("Detail", "DETAIL"),
            ("Emboss", "EMBOSS"), ("Sharpen", "SHARPEN"), ("Grayscale", "GRAYSCALE"),
            ("Sepia", "SEPIA"), ("Negative", "NEGATIVE"), ("Vintage", "VINTAGE"),
        ]
        self.quality = [
            ("Brightness High", "BRIGHTNESS_H"), ("Brightness Low", "BRIGHTNESS_L"),
            ("Contrast High", "CONTRAST_H"), ("Contrast Low", "CONTRAST_L"),
            ("Enhance Quality High", "ENHANCE_QUALITY_H"), ("Enhance Quality Medium", "ENHANCE_QUALITY_M"),
            ("Color Adjust High", "COLOR_ADJUST_H"), ("Color Adjust Low", "COLOR_ADJUST_L"),
        ]

        self.apply_theme()

        self.tab_widget = QTabWidget()
        self.setCentralWidget(self.tab_widget)

        self.image_tab = QWidget()
        self.video_tab = QWidget()
        self.settings_tab = QWidget()

        self.tab_widget.addTab(self.image_tab, "ویرایش تصویر")
        self.tab_widget.addTab(self.video_tab, "ویرایش ویدئو")
        self.tab_widget.addTab(self.settings_tab, "تنظیمات")

        self.init_image_tab()
        self.init_video_tab()
        self.init_settings_tab()

        self.original_image = None
        self.current_image = None
        self.current_image_path = None
        self.current_video_path = None
        self.video_duration = 0.0
        self.history = []
        self.current_columns = 2  # Default to 2 columns

    def apply_theme(self):
        theme = self.themes[self.theme]
        stylesheet = f"""
            QMainWindow {{
                background-color: {theme['main_bg']};
                font-family: 'Segoe UI', sans-serif;
                font-size: {self.font_size}px;
            }}
            QPushButton {{
                background-color: {theme['button_bg']};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 14px;
                font-size: {self.font_size}px;
                font-weight: 600;
                transition: background-color 0.3s ease;
            }}
            QPushButton:hover {{
                background-color: {theme['button_hover']};
            }}
            QLabel {{
                font-size: {self.font_size}px;
                color: {theme['text_color']};
                font-weight: 500;
            }}
            QLineEdit {{
                border: 1px solid {theme['border_color']};
                border-radius: 6px;
                padding: 6px;
                background-color: {theme['preview_bg']};
                font-size: {self.font_size}px;
                color: {theme['text_color']};
            }}
            QProgressBar {{
                background-color: {theme['border_color']};
                border-radius: 6px;
                text-align: center;
                font-size: {self.font_size-2}px;
                color: {theme['text_color']};
            }}
            QProgressBar::chunk {{
                background-color: {theme['button_bg']};
                border-radius: 6px;
            }}
            QGroupBox {{
                border: 1px solid {theme['border_color']};
                border-radius: 8px;
                padding: 10px;
                margin-top: 10px;
                font-weight: bold;
                color: {theme['text_color']};
            }}
            QTabWidget::pane {{
                border: 1px solid {theme['border_color']};
                border-radius: 8px;
                background-color: {theme['preview_bg']};
            }}
            QTabBar::tab {{
                background-color: {theme['tab_bg']};
                border: 1px solid {theme['border_color']};
                border-bottom: none;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                padding: 8px 16px;
                font-size: {self.font_size}px;
                color: {theme['text_color']};
            }}
            QTabBar::tab:selected {{
                background-color: {theme['tab_selected_bg']};
                border-bottom: 2px solid {theme['tab_selected_border']};
            }}
            QComboBox {{
                border: 1px solid {theme['border_color']};
                border-radius: 6px;
                padding: 6px;
                background-color: {theme['preview_bg']};
                font-size: {self.font_size}px;
                color: {theme['text_color']};
            }}
            QSpinBox {{
                border: 1px solid {theme['border_color']};
                border-radius: 6px;
                padding: 6px;
                background-color: {theme['preview_bg']};
                font-size: {self.font_size}px;
                color: {theme['text_color']};
            }}
        """
        self.setStyleSheet(stylesheet)

    def save_settings(self):
        self.settings.setValue("dark_mode", self.is_dark_mode)
        self.settings.setValue("theme", self.theme)
        self.settings.setValue("font_size", self.font_size)
        self.apply_theme()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.tab_widget.currentWidget() == self.image_tab:
            self.update_image_tab_layout()

    def update_image_tab_layout(self):
        num_columns = 3 if self.isMaximized() else 2
        if num_columns == self.current_columns:
            return  # No need to update if column count hasn't changed

        self.current_columns = num_columns

        # Update filters group
        filters_group = self.image_tab.findChild(QGroupBox, "filters_group")
        if filters_group and filters_group.layout():
            # Remove existing buttons
            while filters_group.layout().count():
                item = filters_group.layout().takeAt(0)
                if item.widget():
                    item.widget().setParent(None)
            # Recreate buttons with new column count
            for i, (name, code) in enumerate(self.filters):
                btn = QPushButton(name)
                btn.setIcon(QIcon.fromTheme("image-x-generic"))
                btn.clicked.connect(lambda _, c=code: self.apply_filter(c))
                filters_group.layout().addWidget(btn, i // num_columns, i % num_columns)

        # Update quality group
        quality_group = self.image_tab.findChild(QGroupBox, "quality_group")
        if quality_group and quality_group.layout():
            # Remove existing buttons
            while quality_group.layout().count():
                item = quality_group.layout().takeAt(0)
                if item.widget():
                    item.widget().setParent(None)
            # Recreate buttons with new column count
            for i, (name, code) in enumerate(self.quality):
                btn = QPushButton(name)
                btn.setIcon(QIcon.fromTheme("preferences-desktop-color"))
                btn.clicked.connect(lambda _, c=code: self.apply_filter(c))
                quality_group.layout().addWidget(btn, i // num_columns, i % num_columns)

    def init_image_tab(self):
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left panel: Filters
        left_widget = QWidget()
        left_widget.setObjectName("left_widget")
        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(5)
        left_widget.setLayout(left_layout)

        filters_group = QGroupBox("فیلترها")
        filters_group.setObjectName("filters_group")
        filters_layout = QGridLayout()
        filters_layout.setSpacing(5)
        num_columns = 3 if self.isMaximized() else 2
        self.current_columns = num_columns
        for i, (name, code) in enumerate(self.filters):
            btn = QPushButton(name)
            btn.setIcon(QIcon.fromTheme("image-x-generic"))
            btn.clicked.connect(lambda _, c=code: self.apply_filter(c))
            filters_layout.addWidget(btn, i // num_columns, i % num_columns)
        filters_group.setLayout(filters_layout)
        left_layout.addWidget(filters_group)

        quality_group = QGroupBox("کیفیت")
        quality_group.setObjectName("quality_group")
        quality_layout = QGridLayout()
        quality_layout.setSpacing(5)
        for i, (name, code) in enumerate(self.quality):
            btn = QPushButton(name)
            btn.setIcon(QIcon.fromTheme("preferences-desktop-color"))
            btn.clicked.connect(lambda _, c=code: self.apply_filter(c))
            quality_layout.addWidget(btn, i // num_columns, i % num_columns)
        quality_group.setLayout(quality_layout)
        left_layout.addWidget(quality_group)

        rotates_group = QGroupBox("چرخش")
        rotates_layout = QHBoxLayout()
        rotates_layout.setSpacing(5)
        rotates = [
            ("Rotate 90°", "ROTATE_N"), ("Rotate 180°", "ROTATE_S"), ("Rotate 270°", "ROTATE_D"),
        ]
        for name, code in rotates:
            btn = QPushButton(name)
            btn.setIcon(QIcon.fromTheme("object-rotate-right"))
            btn.clicked.connect(lambda _, c=code: self.apply_filter(c))
            rotates_layout.addWidget(btn)
        rotates_group.setLayout(rotates_layout)
        left_layout.addWidget(rotates_group)

        resizes_group = QGroupBox("سایز")
        resizes_layout = QHBoxLayout()
        resizes_layout.setSpacing(5)
        resizes = [
            ("Resize Small", "RESIZE_S"), ("Resize Large", "RESIZE_L"),
        ]
        for name, code in resizes:
            btn = QPushButton(name)
            btn.setIcon(QIcon.fromTheme("transform-scale"))
            btn.clicked.connect(lambda _, c=code: self.apply_filter(c))
            resizes_layout.addWidget(btn)
        resizes_group.setLayout(resizes_layout)
        left_layout.addWidget(resizes_group)

        left_layout.addItem(QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        splitter.addWidget(left_widget)

        # Right panel: Previews and buttons
        right_widget = QWidget()
        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(10)
        right_widget.setLayout(right_layout)

        self.image_preview_label = QLabel("پیش‌نمایش اصلی")
        self.image_preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_preview_label.setStyleSheet("border: 1px solid #dee2e6; border-radius: 10px; background-color: white; padding: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);")
        self.image_preview_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self.edited_image_preview_label = QLabel("پیش‌نمایش ویرایش‌شده")
        self.edited_image_preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.edited_image_preview_label.setStyleSheet("border: 1px solid #dee2e6; border-radius: 10px; background-color: white; padding: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);")
        self.edited_image_preview_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        previews_layout = QHBoxLayout()
        previews_layout.setSpacing(10)
        previews_layout.addWidget(self.image_preview_label)
        previews_layout.addWidget(self.edited_image_preview_label)
        right_layout.addLayout(previews_layout, stretch=1)

        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(5)
        undo_btn = QPushButton("لغو آخرین تغییر")
        undo_btn.setIcon(QIcon.fromTheme("edit-undo"))
        undo_btn.clicked.connect(self.undo_filter)
        reset_btn = QPushButton("بازنشانی تغییرات")
        reset_btn.setIcon(QIcon.fromTheme("edit-clear"))
        reset_btn.clicked.connect(self.reset_filters)
        select_btn = QPushButton("انتخاب تصویر")
        select_btn.setIcon(QIcon.fromTheme("folder-open"))
        select_btn.clicked.connect(self.select_image)
        save_btn = QPushButton("ذخیره تصویر")
        save_btn.setIcon(QIcon.fromTheme("document-save"))
        save_btn.clicked.connect(self.save_edited_image)
        actions_layout.addWidget(undo_btn)
        actions_layout.addWidget(reset_btn)
        actions_layout.addWidget(select_btn)
        actions_layout.addWidget(save_btn)
        right_layout.addLayout(actions_layout)

        splitter.addWidget(right_widget)
        splitter.setSizes([250, 950])

        main_layout.addWidget(splitter)
        self.image_tab.setLayout(main_layout)

    def save_edited_image(self):
        if not self.current_image:
            QMessageBox.warning(self, "خطا", "هیچ تصویری برای ذخیره وجود ندارد.")
            return

        save_path, _ = QFileDialog.getSaveFileName(self, "ذخیره تصویر ویرایش‌شده", "edited_image.png",
                                                   "Image files (*.png *.jpg *.bmp)")
        if save_path:
            try:
                self.current_image.save(save_path)
                QMessageBox.information(self, "موفق", f"تصویر در {save_path} ذخیره شد.")
            except Exception as ex:
                QMessageBox.warning(self, "خطا", f"خطا در ذخیره تصویر: {ex}")

    def init_video_tab(self):
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left panel: Buttons
        left_widget = QWidget()
        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(5)
        left_widget.setLayout(left_layout)

        select_video_btn = QPushButton("انتخاب ویدیو")
        select_video_btn.setIcon(QIcon.fromTheme("folder-videos"))
        select_video_btn.clicked.connect(self.select_video)
        left_layout.addWidget(select_video_btn)

        convert_mp3_btn = QPushButton("تبدیل به MP3")
        convert_mp3_btn.setIcon(QIcon.fromTheme("audio-x-generic"))
        convert_mp3_btn.clicked.connect(self.start_convert_to_mp3)
        left_layout.addWidget(convert_mp3_btn)

        left_layout.addItem(QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        splitter.addWidget(left_widget)

        # Right panel: Preview and trim
        right_widget = QWidget()
        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(10)
        right_widget.setLayout(right_layout)

        self.video_status_label = QLabel("ویدیو انتخاب نشده")
        right_layout.addWidget(self.video_status_label)

        self.video_preview_label = QLabel("پیش‌نمایش ویدیو")
        self.video_preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_preview_label.setStyleSheet("border: 1px solid #dee2e6; border-radius: 10px; background-color: white; padding: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);")
        self.video_preview_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        right_layout.addWidget(self.video_preview_label, stretch=1)

        self.video_progress = QProgressBar()
        self.video_progress.setVisible(False)
        right_layout.addWidget(self.video_progress)

        trim_group = QGroupBox("برش ویدیو")
        trim_layout = QVBoxLayout()
        trim_layout.setSpacing(5)
        trim_inputs_layout = QHBoxLayout()
        trim_inputs_layout.setSpacing(5)
        self.trim_start_input = QLineEdit("00:00:00")
        self.trim_start_input.setPlaceholderText("شروع (HH:MM:SS)")
        self.trim_end_input = QLineEdit("00:00:00")
        self.trim_end_input.setPlaceholderText("پایان (HH:MM:SS)")
        trim_inputs_layout.addWidget(self.trim_start_input)
        trim_inputs_layout.addWidget(self.trim_end_input)
        trim_layout.addLayout(trim_inputs_layout)

        trim_btn = QPushButton("اعمال برش")
        trim_btn.setIcon(QIcon.fromTheme("edit-cut"))
        trim_btn.clicked.connect(self.start_trim_video)
        trim_layout.addWidget(trim_btn)
        trim_group.setLayout(trim_layout)
        right_layout.addWidget(trim_group)

        splitter.addWidget(right_widget)
        splitter.setSizes([250, 950])

        main_layout.addWidget(splitter)
        self.video_tab.setLayout(main_layout)

    def init_settings_tab(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        settings_group = QGroupBox("تنظیمات ظاهری")
        settings_layout = QVBoxLayout()
        settings_layout.setSpacing(10)

        # Theme selection
        theme_layout = QHBoxLayout()
        theme_label = QLabel("تم:")
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(self.themes.keys())
        self.theme_combo.setCurrentText(self.theme)
        self.theme_combo.currentTextChanged.connect(self.change_theme)
        theme_layout.addWidget(theme_label)
        theme_layout.addWidget(self.theme_combo)
        settings_layout.addLayout(theme_layout)

        # Font size selection
        font_size_layout = QHBoxLayout()
        font_size_label = QLabel("اندازه فونت:")
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(10, 20)
        self.font_size_spin.setValue(self.font_size)
        self.font_size_spin.valueChanged.connect(self.change_font_size)
        font_size_layout.addWidget(font_size_label)
        font_size_layout.addWidget(self.font_size_spin)
        settings_layout.addLayout(font_size_layout)

        # Dark mode toggle
        self.dark_mode_checkbox = QCheckBox("حالت تاریک")
        self.dark_mode_checkbox.setChecked(self.is_dark_mode)
        self.dark_mode_checkbox.stateChanged.connect(self.toggle_dark_mode)
        settings_layout.addWidget(self.dark_mode_checkbox)

        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)
        layout.addStretch()

        self.settings_tab.setLayout(layout)

    def toggle_dark_mode(self, state):
        self.is_dark_mode = bool(state)
        if self.is_dark_mode:
            self.theme = "Dark"
            self.theme_combo.setCurrentText("Dark")
        else:
            self.theme = "Default"
            self.theme_combo.setCurrentText("Default")
        self.save_settings()

    def change_theme(self, theme):
        self.theme = theme
        if theme == "Dark":
            self.is_dark_mode = True
            self.dark_mode_checkbox.setChecked(True)
        else:
            self.is_dark_mode = False
            self.dark_mode_checkbox.setChecked(False)
        self.save_settings()

    def change_font_size(self, size):
        self.font_size = size
        self.save_settings()

    def select_image(self):
        path, _ = QFileDialog.getOpenFileName(self, "انتخاب تصویر", "", "Image files (*.png *.jpg *.bmp)")
        if path:
            self.current_image_path = path
            try:
                self.original_image = Image.open(path)
                self.current_image = self.original_image.copy()
                self.display_image(self.image_preview_label, path)
                self.edited_image_preview_label.setPixmap(QPixmap())
                self.history.clear()
            except Exception as ex:
                QMessageBox.warning(self, "خطا", f"خطا در بارگذاری تصویر: {ex}")

    def apply_filter(self, filter_code):
        if not self.current_image:
            QMessageBox.warning(self, "خطا", "ابتدا یک تصویر انتخاب کنید.")
            return
        try:
            self.history.append(self.current_image.copy())
            image = self.current_image.copy()

            if filter_code == 'BLUR':
                filtered = image.filter(ImageFilter.BLUR)
            elif filter_code == 'CONTOUR':
                filtered = image.filter(ImageFilter.CONTOUR)
            elif filter_code == 'DETAIL':
                filtered = image.filter(ImageFilter.DETAIL)
            elif filter_code == 'EMBOSS':
                filtered = image.filter(ImageFilter.EMBOSS)
            elif filter_code == 'SHARPEN':
                filtered = image.filter(ImageFilter.SHARPEN)
            elif filter_code == 'RESIZE_S':
                filtered = image.resize((image.width // 2, image.height // 2))
            elif filter_code == 'RESIZE_L':
                filtered = image.resize((image.width * 2, image.height * 2))
            elif filter_code == 'ROTATE_N':
                filtered = image.rotate(90, expand=True)
            elif filter_code == 'ROTATE_S':
                filtered = image.rotate(180, expand=True)
            elif filter_code == 'ROTATE_D':
                filtered = image.rotate(270, expand=True)
            elif filter_code == 'BRIGHTNESS_H':
                enhancer = ImageEnhance.Brightness(image)
                filtered = enhancer.enhance(1.5)
            elif filter_code == 'BRIGHTNESS_L':
                enhancer = ImageEnhance.Brightness(image)
                filtered = enhancer.enhance(0.5)
            elif filter_code == 'CONTRAST_H':
                enhancer = ImageEnhance.Contrast(image)
                filtered = enhancer.enhance(1.7)
            elif filter_code == 'CONTRAST_L':
                enhancer = ImageEnhance.Contrast(image)
                filtered = enhancer.enhance(0.4)
            elif filter_code == 'ENHANCE_QUALITY_H':
                enhancer = ImageEnhance.Sharpness(image)
                filtered = enhancer.enhance(2.8)
            elif filter_code == 'ENHANCE_QUALITY_M':
                enhancer = ImageEnhance.Sharpness(image)
                filtered = enhancer.enhance(1.8)
            elif filter_code == 'GRAYSCALE':
                filtered = image.convert('L')
            elif filter_code == 'COLOR_ADJUST_H':
                enhancer = ImageEnhance.Color(image)
                filtered = enhancer.enhance(2)
            elif filter_code == 'COLOR_ADJUST_L':
                enhancer = ImageEnhance.Color(image)
                filtered = enhancer.enhance(0.4)
            elif filter_code == 'SEPIA':
                sepia_image = image.convert("RGB")
                width, height = sepia_image.size
                pixels = sepia_image.load()
                for py in range(height):
                    for px in range(width):
                        r, g, b = sepia_image.getpixel((px, py))
                        tr = int(0.393 * r + 0.769 * g + 0.189 * b)
                        tg = int(0.349 * r + 0.686 * g + 0.168 * b)
                        tb = int(0.272 * r + 0.534 * g + 0.131 * b)
                        pixels[px, py] = (min(tr, 255), min(tg, 255), min(tb, 255))
                filtered = sepia_image
            elif filter_code == 'NEGATIVE':
                filtered = ImageOps.invert(image.convert("RGB"))
            elif filter_code == 'VINTAGE':
                vintage_image = image.convert("RGB")
                enhancer = ImageEnhance.Color(vintage_image)
                filtered = enhancer.enhance(0.2)

            self.current_image = filtered
            edited_path = os.path.join(CACHE_DIR, f"edited_{time.time()}.png")
            filtered.save(edited_path)
            self.display_image(self.edited_image_preview_label, edited_path)
        except Exception as ex:
            QMessageBox.warning(self, "خطا", f"خطا در اعمال فیلتر: {ex}")

    def undo_filter(self):
        if self.history:
            self.current_image = self.history.pop()
            undone_path = os.path.join(CACHE_DIR, f"undone_{time.time()}.png")
            self.current_image.save(undone_path)
            self.display_image(self.edited_image_preview_label, undone_path)
        else:
            QMessageBox.warning(self, "خطا", "هیچ تغییری برای برگرداندن وجود ندارد.")

    def reset_filters(self):
        if self.original_image:
            self.current_image = self.original_image.copy()
            self.history.clear()
            self.display_image(self.image_preview_label, self.current_image_path)
            self.edited_image_preview_label.setPixmap(QPixmap())
        else:
            QMessageBox.warning(self, "خطا", "هیچ تصویری انتخاب نشده است.")

    def select_video(self):
        path, _ = QFileDialog.getOpenFileName(self, "انتخاب ویدیو", "", "Video files (*.mp4 *.avi *.mov)")
        if path:
            self.current_video_path = path
            self.video_status_label.setText(f"ویدیو انتخاب شده: {os.path.basename(path)}")
            try:
                video = VideoFileClip(path)
                self.video_duration = video.duration
                thumbnail_path = os.path.join(CACHE_DIR, f"thumb_{time.time()}.png")
                video.save_frame(thumbnail_path, t=1.0)
                video.close()
                self.display_image(self.video_preview_label, thumbnail_path, video=True)
            except Exception as ex:
                self.video_preview_label.setText(f"خطا در پیش‌نمایش ویدیو: {ex}")

    def start_trim_video(self):
        if not self.current_video_path:
            QMessageBox.warning(self, "خطا", "ابتدا یک ویدیو انتخاب کنید.")
            return

        start_time = self.trim_start_input.text()
        end_time = self.trim_end_input.text()
        start_secs = self.parse_time_to_secs(start_time)
        end_secs = self.parse_time_to_secs(end_time)

        if start_secs is None or end_secs is None:
            QMessageBox.warning(self, "خطا", "فرمت زمان نامعتبر است. از HH:MM:SS استفاده کنید.")
            return
        if start_secs >= end_secs:
            QMessageBox.warning(self, "خطا", "زمان شروع باید کمتر از پایان باشد.")
            return
        if start_secs < 0 or end_secs > self.video_duration:
            QMessageBox.warning(self, "خطا", "زمان‌ها خارج از محدوده ویدیو هستند.")
            return

        output_path = os.path.join(CACHE_DIR, f"trimmed_{time.time()}.mp4")

        self.video_progress.setVisible(True)
        self.video_progress.setValue(0)
        self.thread = ProgressThread('trim', self.current_video_path, start_secs, end_secs, output_path)
        self.thread.progress_signal.connect(self.video_progress.setValue)
        self.thread.finished_signal.connect(self.finish_trim_video)
        self.thread.start()

    def finish_trim_video(self, output_path):
        self.video_progress.setVisible(False)
        if output_path and os.path.exists(output_path):
            thumbnail_path = os.path.join(CACHE_DIR, f"trim_thumb_{time.time()}.png")
            try:
                temp_video = VideoFileClip(output_path)
                temp_video.save_frame(thumbnail_path, t=1.0)
                temp_video.close()
                self.display_image(self.video_preview_label, thumbnail_path, video=True)
            except Exception as ex:
                QMessageBox.warning(self, "خطا", f"خطا در ایجاد پیش‌نمایش: {ex}")
                return

            save_path, _ = QFileDialog.getSaveFileName(self, "ذخیره ویدیو برش‌خورده", os.path.splitext(os.path.basename(self.current_video_path))[0] + "_trimmed.mp4", "MP4 files (*.mp4)")
            if save_path:
                try:
                    shutil.move(output_path, save_path)
                    QMessageBox.information(self, "موفق", f"ویدیو در {save_path} ذخیره شد.")
                except Exception as ex:
                    QMessageBox.warning(self, "خطا", f"خطا در ذخیره فایل: {ex}")
        else:
            QMessageBox.warning(self, "خطا", "برش ویدیو ناموفق بود. لطفاً فرمت ویدیو یا مسیر را بررسی کنید.")

    def start_convert_to_mp3(self):
        if not self.current_video_path:
            QMessageBox.warning(self, "خطا", "ابتدا یک ویدیو انتخاب کنید.")
            return

        output_path = os.path.join(CACHE_DIR, f"converted_{time.time()}.mp3")

        self.video_progress.setVisible(True)
        self.video_progress.setValue(0)
        self.thread = ProgressThread('mp3', self.current_video_path, output_path)
        self.thread.progress_signal.connect(self.video_progress.setValue)
        self.thread.finished_signal.connect(self.finish_convert_to_mp3)
        self.thread.start()

    def finish_convert_to_mp3(self, output_path):
        self.video_progress.setVisible(False)
        if output_path and os.path.exists(output_path):
            save_path, _ = QFileDialog.getSaveFileName(self, "ذخیره فایل MP3", os.path.splitext(os.path.basename(self.current_video_path))[0] + ".mp3", "MP3 files (*.mp3)")
            if save_path:
                try:
                    shutil.move(output_path, save_path)
                    QMessageBox.information(self, "موفق", f"فایل MP3 در {save_path} ذخیره شد.")
                except Exception as ex:
                    QMessageBox.warning(self, "خطا", f"خطا در ذخیره فایل: {ex}")
        else:
            QMessageBox.warning(self, "خطا", "تبدیل به MP3 ناموفق بود. لطفاً فرمت ویدیو یا مسیر را بررسی کنید.")

    def parse_time_to_secs(self, time_str):
        try:
            h, m, s = map(int, time_str.strip().split(':'))
            return h * 3600 + m * 60 + s
        except:
            return None

    def display_image(self, label, path, video=False):
        pixmap = QPixmap(path)
        if pixmap.isNull():
            label.setText("خطا در بارگذاری تصویر")
        else:
            label.setPixmap(pixmap.scaled(400, 300, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MediaEditor()
    window.show()
    sys.exit(app.exec())