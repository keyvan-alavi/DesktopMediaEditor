#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Entry point for Desktop Media Editor."""

import sys
from pathlib import Path

# Ensure project root is on sys.path when running as script
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from PyQt6.QtWidgets import QApplication

from app import __version__
from app.ui.main_window import MediaEditor, APP_NAME, ORG_NAME


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(__version__)
    app.setOrganizationName(ORG_NAME)
    window = MediaEditor()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
