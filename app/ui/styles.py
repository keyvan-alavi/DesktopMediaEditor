"""Themes and stylesheet generation."""
from __future__ import annotations

THEMES = {
    "Default": {
        "main_bg": "#eef2f7", "sidebar_bg": "#ffffff",
        "button_bg": "#0f766e", "button_hover": "#0d9488", "button_pressed": "#115e59",
        "text_color": "#0f172a", "muted_text": "#64748b",
        "border_color": "#d0d7e2", "tab_bg": "#dce3ed",
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
        "main_bg": "#e8f0fe", "sidebar_bg": "#ffffff",
        "button_bg": "#1d4ed8", "button_hover": "#2563eb", "button_pressed": "#1e40af",
        "text_color": "#1e3a8a", "muted_text": "#64748b",
        "border_color": "#bfdbfe", "tab_bg": "#dbeafe",
        "tab_selected_bg": "#ffffff", "tab_selected_border": "#1d4ed8",
        "preview_bg": "#ffffff", "group_bg": "#ffffff", "accent": "#1d4ed8",
    },
    "Green": {
        "main_bg": "#ecfdf5", "sidebar_bg": "#ffffff",
        "button_bg": "#15803d", "button_hover": "#16a34a", "button_pressed": "#166534",
        "text_color": "#14532d", "muted_text": "#64748b",
        "border_color": "#bbf7d0", "tab_bg": "#dcfce7",
        "tab_selected_bg": "#ffffff", "tab_selected_border": "#15803d",
        "preview_bg": "#ffffff", "group_bg": "#ffffff", "accent": "#15803d",
    },
}


def build_stylesheet(theme_name: str, font_size: int) -> str:
    t = THEMES.get(theme_name, THEMES["Default"])
    return f"""
        QMainWindow, QWidget {{
            background-color: {t['main_bg']};
            font-family: 'Segoe UI', 'Vazirmatn', 'Tahoma', sans-serif;
            font-size: {font_size}px;
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
        }}
        QMenu::item:selected {{ background-color: {t['accent']}; color: white; }}
        QStatusBar {{
            background-color: {t['sidebar_bg']};
            color: {t['muted_text']};
            border-top: 1px solid {t['border_color']};
        }}
        QPushButton {{
            background-color: {t['button_bg']};
            color: white;
            border: none;
            border-radius: 8px;
            padding: 7px 11px;
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
        QPushButton#activeToggle {{
            background-color: {t['accent']};
            color: white;
            border: 2px solid {t['accent']};
        }}
        QPushButton#dangerBtn {{
            background-color: #b91c1c;
            color: white;
        }}
        QPushButton#dangerBtn:hover {{ background-color: #dc2626; }}
        QLabel {{ color: {t['text_color']}; background: transparent; font-weight: 500; }}
        QLabel#placeholderLabel {{ color: {t['muted_text']}; font-size: 14px; }}
        QLabel#mutedLabel {{ color: {t['muted_text']}; }}
        QLabel#cardTitle {{
            font-weight: 700;
            font-size: {font_size + 1}px;
            color: {t['text_color']};
            padding-bottom: 2px;
        }}
        QLineEdit, QSpinBox, QComboBox {{
            border: 1.5px solid {t['border_color']};
            border-radius: 7px;
            padding: 6px 10px;
            background-color: {t['preview_bg']};
            color: {t['text_color']};
            selection-background-color: {t['accent']};
        }}
        QLineEdit:focus, QSpinBox:focus, QComboBox:focus {{
            border: 2px solid {t['accent']};
        }}
        QComboBox QAbstractItemView {{
            background-color: {t['sidebar_bg']};
            color: {t['text_color']};
            selection-background-color: {t['accent']};
        }}
        QSlider::groove:horizontal {{
            height: 6px; background: {t['border_color']}; border-radius: 3px;
        }}
        QSlider::handle:horizontal {{
            background: {t['accent']};
            width: 16px; height: 16px; margin: -5px 0; border-radius: 8px;
        }}
        QSlider::sub-page:horizontal {{ background: {t['accent']}; border-radius: 3px; }}
        QProgressBar {{
            background-color: {t['border_color']};
            border-radius: 6px; text-align: center; height: 18px;
            color: {t['text_color']};
        }}
        QProgressBar::chunk {{ background-color: {t['button_bg']}; border-radius: 6px; }}
        QFrame#toolCard {{
            background-color: {t['group_bg']};
            border: 1px solid {t['border_color']};
            border-radius: 12px;
        }}
        QFrame#sidebarFrame {{
            background-color: {t['sidebar_bg']};
            border: 1px solid {t['border_color']};
            border-radius: 14px;
        }}
        QFrame#previewFrame {{
            background-color: {t['preview_bg']};
            border: 1px solid {t['border_color']};
            border-radius: 14px;
        }}
        QFrame#canvasFrame {{
            background-color: {t['main_bg']};
            border: 2px solid {t['border_color']};
            border-radius: 14px;
        }}
        QTabWidget::pane {{
            border: 1px solid {t['border_color']};
            border-radius: 10px;
            background-color: {t['preview_bg']};
        }}
        QTabBar::tab {{
            background-color: {t['tab_bg']};
            border: 1px solid {t['border_color']};
            border-bottom: none;
            border-top-left-radius: 8px;
            border-top-right-radius: 8px;
            padding: 8px 16px;
            color: {t['text_color']};
            margin-right: 3px;
        }}
        QTabBar::tab:selected {{
            background-color: {t['tab_selected_bg']};
            border-bottom: 3px solid {t['tab_selected_border']};
            font-weight: 700;
        }}
        QScrollArea {{ border: none; background: transparent; }}
        QScrollBar:vertical {{
            background: {t['border_color']}; width: 9px; border-radius: 4px;
        }}
        QScrollBar::handle:vertical {{
            background: {t['muted_text']}; border-radius: 4px; min-height: 28px;
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
    """
