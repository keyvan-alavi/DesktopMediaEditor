"""Image preview widget with safe interactive crop selection."""
from __future__ import annotations

from PyQt6.QtCore import Qt, QPoint, QRect, pyqtSignal
from PyQt6.QtGui import QPainter, QPen, QColor, QPixmap
from PyQt6.QtWidgets import QLabel, QSizePolicy


class PreviewLabel(QLabel):
    """
    Displays a scaled pixmap and supports optional rubber-band crop selection.
    Selection is painted manually (no QRubberBand) to avoid native crashes on Windows.
    """

    crop_done = pyqtSignal(int, int, int, int)  # left, top, right, bottom in IMAGE coords

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumSize(280, 220)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setObjectName("placeholderLabel")
        self.setMouseTracking(True)

        self._crop_mode = False
        self._selecting = False
        self._origin = QPoint()
        self._current = QPoint()
        self._pixmap_rect = QRect()  # where scaled image sits inside widget
        self._image_size = (0, 0)  # original image width, height
        self._base_pixmap: QPixmap | None = None

    # ----- public API -----
    def set_crop_mode(self, enabled: bool) -> None:
        self._crop_mode = bool(enabled)
        self._selecting = False
        self.setCursor(
            Qt.CursorShape.CrossCursor if enabled else Qt.CursorShape.ArrowCursor
        )
        self.update()

    def show_pixmap(self, pix: QPixmap, image_width: int, image_height: int) -> None:
        """Set display pixmap and remember original image dimensions for crop mapping."""
        self._base_pixmap = pix
        self._image_size = (max(1, image_width), max(1, image_height))
        self._layout_pixmap()
        self.update()

    def clear_view(self, text: str = "") -> None:
        self._base_pixmap = None
        self._image_size = (0, 0)
        self._pixmap_rect = QRect()
        self.setPixmap(QPixmap())
        if text:
            self.setText(text)
        self.update()

    # ----- layout -----
    def _layout_pixmap(self) -> None:
        if self._base_pixmap is None or self._base_pixmap.isNull():
            self._pixmap_rect = QRect()
            return
        target = self.size()
        if target.width() < 20 or target.height() < 20:
            return
        scaled = self._base_pixmap.scaled(
            target,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        x = max(0, (self.width() - scaled.width()) // 2)
        y = max(0, (self.height() - scaled.height()) // 2)
        self._pixmap_rect = QRect(x, y, scaled.width(), scaled.height())
        # Avoid QLabel.setPixmap during paint; store and paint ourselves in crop mode
        if not self._crop_mode:
            super().setPixmap(scaled)
        else:
            # clear QLabel's pixmap so our paintEvent draws everything
            super().setPixmap(QPixmap())
            self._scaled_for_paint = scaled

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._layout_pixmap()

    # ----- painting selection -----
    def paintEvent(self, event):
        if self._crop_mode and self._base_pixmap is not None and not self._base_pixmap.isNull():
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
            scaled = getattr(self, "_scaled_for_paint", None)
            if scaled is None or scaled.isNull():
                scaled = self._base_pixmap.scaled(
                    self.size(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                x = max(0, (self.width() - scaled.width()) // 2)
                y = max(0, (self.height() - scaled.height()) // 2)
                self._pixmap_rect = QRect(x, y, scaled.width(), scaled.height())
            else:
                x, y = self._pixmap_rect.x(), self._pixmap_rect.y()
            painter.drawPixmap(x, y, scaled)

            if self._selecting:
                sel = QRect(self._origin, self._current).normalized()
                sel = sel.intersected(self._pixmap_rect)
                if sel.isValid() and sel.width() > 1 and sel.height() > 1:
                    # dim outside
                    overlay = QColor(0, 0, 0, 100)
                    painter.fillRect(self._pixmap_rect, overlay)
                    painter.setCompositionMode(
                        QPainter.CompositionMode.CompositionMode_Clear
                    )
                    painter.fillRect(sel, Qt.GlobalColor.transparent)
                    painter.setCompositionMode(
                        QPainter.CompositionMode.CompositionMode_SourceOver
                    )
                    # redraw selected region sharp
                    src = scaled.copy(
                        sel.x() - x, sel.y() - y, sel.width(), sel.height()
                    )
                    painter.drawPixmap(sel.topLeft(), src)
                    pen = QPen(QColor(20, 180, 160), 2, Qt.PenStyle.DashLine)
                    painter.setPen(pen)
                    painter.drawRect(sel.adjusted(0, 0, -1, -1))
            painter.end()
        else:
            super().paintEvent(event)

    # ----- mouse -----
    def mousePressEvent(self, event):
        if (
            self._crop_mode
            and event.button() == Qt.MouseButton.LeftButton
            and self._pixmap_rect.contains(event.position().toPoint())
        ):
            self._selecting = True
            self._origin = event.position().toPoint()
            self._current = self._origin
            self.update()
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._crop_mode and self._selecting:
            self._current = event.position().toPoint()
            self.update()
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if (
            self._crop_mode
            and self._selecting
            and event.button() == Qt.MouseButton.LeftButton
        ):
            self._selecting = False
            self._current = event.position().toPoint()
            sel = QRect(self._origin, self._current).normalized()
            sel = sel.intersected(self._pixmap_rect)
            self.update()

            if sel.width() >= 4 and sel.height() >= 4 and self._image_size[0] > 0:
                img_box = self._widget_rect_to_image(sel)
                if img_box is not None:
                    self.crop_done.emit(*img_box)
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def _widget_rect_to_image(self, sel: QRect) -> tuple[int, int, int, int] | None:
        area = self._pixmap_rect
        if area.width() <= 0 or area.height() <= 0:
            return None
        iw, ih = self._image_size
        scale_x = iw / area.width()
        scale_y = ih / area.height()
        left = int(round((sel.x() - area.x()) * scale_x))
        top = int(round((sel.y() - area.y()) * scale_y))
        right = int(round((sel.x() + sel.width() - area.x()) * scale_x))
        bottom = int(round((sel.y() + sel.height() - area.y()) * scale_y))
        left = max(0, min(left, iw - 1))
        top = max(0, min(top, ih - 1))
        right = max(left + 1, min(right, iw))
        bottom = max(top + 1, min(bottom, ih))
        if right - left < 2 or bottom - top < 2:
            return None
        return left, top, right, bottom
