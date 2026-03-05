"""
VideoCardWidget — displays a single video recording as a styled card.

Thumbnail generation is performed lazily in the background to avoid
blocking the main thread.  Results are cached in a class-level dict
so that switching views does not regenerate the same thumbnail twice.
"""

from __future__ import annotations

import os
import threading
from typing import Optional

import cv2
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QFont, QPixmap, QImage, QColor, QPainter, QPainterPath
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMenu,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from src.ui.styles import COLORS, RADIUS, SPACING


# Module-level thumbnail cache shared across all VideoCardWidget instances.
_THUMB_CACHE: dict[str, QPixmap] = {}


def _make_placeholder_pixmap(width: int, height: int) -> QPixmap:
    """Return a dark placeholder QPixmap while the real thumbnail loads."""
    px = QPixmap(width, height)
    px.fill(QColor(COLORS['bg_surface']))
    painter = QPainter(px)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setPen(QColor(COLORS['text_muted']))
    painter.setFont(QFont("Arial", 18))
    painter.drawText(px.rect(), Qt.AlignmentFlag.AlignCenter, "▶")
    painter.end()
    return _round_pixmap(px, RADIUS['sm'])


def _round_pixmap(pixmap: QPixmap, radius: int) -> QPixmap:
    """Return a copy of *pixmap* with rounded corners."""
    from PyQt6.QtCore import QRectF
    result = QPixmap(pixmap.size())
    result.fill(Qt.GlobalColor.transparent)
    painter = QPainter(result)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    path = QPainterPath()
    path.addRoundedRect(QRectF(result.rect()), radius, radius)
    painter.setClipPath(path)
    painter.drawPixmap(0, 0, pixmap)
    painter.end()
    return result


def _load_thumbnail_from_video(filepath: str, thumb_w: int, thumb_h: int) -> Optional[QPixmap]:
    """
    Extract a frame at ~10 % of the video duration using OpenCV.
    Returns a rounded QPixmap, or None on failure.
    Runs in a worker thread — must not touch Qt GUI objects.
    """
    try:
        cap = cv2.VideoCapture(filepath)
        if not cap.isOpened():
            return None

        frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
        seek_frame = max(0, int(frame_count * 0.10))
        cap.set(cv2.CAP_PROP_POS_FRAMES, seek_frame)

        ret, frame = cap.read()
        cap.release()

        if not ret or frame is None:
            return None

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        qi = QImage(rgb.data, w, h, ch * w, QImage.Format.Format_RGB888).copy()

        pixmap = QPixmap.fromImage(qi)
        pixmap = pixmap.scaled(
            thumb_w, thumb_h,
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation,
        )
        # Centre-crop to exact size
        if pixmap.width() > thumb_w or pixmap.height() > thumb_h:
            x = (pixmap.width() - thumb_w) // 2
            y = (pixmap.height() - thumb_h) // 2
            pixmap = pixmap.copy(x, y, thumb_w, thumb_h)

        return _round_pixmap(pixmap, RADIUS['sm'])
    except Exception:
        return None


class VideoCardWidget(QWidget):
    """
    A horizontal card widget that represents one video recording.

    Signals
    -------
    clicked(str)         — path of the video (emitted on single click)
    play_requested(str)  — user chose "Play" via double-click or context menu
    rename_requested(str)
    delete_requested(str)
    """

    clicked = pyqtSignal(str)
    play_requested = pyqtSignal(str)
    rename_requested = pyqtSignal(str)
    delete_requested = pyqtSignal(str)

    _THUMB_W = 100
    _THUMB_H = 68

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._filepath: str = ""
        self._hovered: bool = False

        self.setMouseTracking(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)

        self._build_ui()
        self._apply_style(hovered=False)

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        outer = QHBoxLayout(self)
        outer.setContentsMargins(SPACING['md'], SPACING['sm'], SPACING['md'], SPACING['sm'])
        outer.setSpacing(SPACING['md'])

        # Thumbnail
        self._thumb_label = QLabel()
        self._thumb_label.setFixedSize(self._THUMB_W, self._THUMB_H)
        self._thumb_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._thumb_label.setStyleSheet("background-color: transparent;")
        self._thumb_label.setPixmap(_make_placeholder_pixmap(self._THUMB_W, self._THUMB_H))
        outer.addWidget(self._thumb_label)

        # Info column
        info_col = QVBoxLayout()
        info_col.setSpacing(4)
        info_col.setContentsMargins(0, 0, 0, 0)

        self._name_label = QLabel()
        name_font = QFont()
        name_font.setPointSize(13)
        name_font.setWeight(QFont.Weight.DemiBold)
        self._name_label.setFont(name_font)
        self._name_label.setStyleSheet(f"color: {COLORS['text_primary']}; background: transparent;")
        info_col.addWidget(self._name_label)

        self._meta_label = QLabel()
        meta_font = QFont()
        meta_font.setPointSize(11)
        self._meta_label.setFont(meta_font)
        self._meta_label.setStyleSheet(f"color: {COLORS['text_secondary']}; background: transparent;")
        info_col.addWidget(self._meta_label)

        info_col.addStretch()
        outer.addLayout(info_col, 1)

        # Action buttons column
        btn_col = QVBoxLayout()
        btn_col.setSpacing(SPACING['xs'])
        btn_col.setContentsMargins(0, 0, 0, 0)
        btn_col.addStretch()

        self._play_btn = QPushButton("▶")
        self._play_btn.setFixedSize(QSize(32, 32))
        self._play_btn.setObjectName("icon_btn")
        self._play_btn.setToolTip("Play")
        self._play_btn.clicked.connect(lambda: self.play_requested.emit(self._filepath))

        btn_col.addWidget(self._play_btn)
        btn_col.addStretch()

        outer.addLayout(btn_col)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_video_data(
        self,
        filepath: str,
        filename: str,
        size_mb: float,
        duration_str: str,
        date_str: str,
    ) -> None:
        """Populate the card with video metadata and kick off thumbnail loading."""
        self._filepath = filepath

        # Truncate very long filenames
        display_name = filename if len(filename) <= 55 else filename[:52] + "…"
        self._name_label.setText(display_name)
        self._name_label.setToolTip(filename)

        parts = [f"{size_mb:.1f} MB"]
        if duration_str:
            parts.append(duration_str)
        parts.append(date_str)
        self._meta_label.setText("  •  ".join(parts))

        self._load_thumbnail_async(filepath)

    # ------------------------------------------------------------------
    # Thumbnail loading
    # ------------------------------------------------------------------

    def _load_thumbnail_async(self, filepath: str) -> None:
        if filepath in _THUMB_CACHE:
            self._thumb_label.setPixmap(_THUMB_CACHE[filepath])
            return

        def worker():
            px = _load_thumbnail_from_video(filepath, self._THUMB_W, self._THUMB_H)
            if px and not px.isNull():
                _THUMB_CACHE[filepath] = px
                # Must update GUI on main thread via signal trick
                self._deliver_thumbnail(px)

        t = threading.Thread(target=worker, daemon=True)
        t.start()

    def _deliver_thumbnail(self, pixmap: QPixmap) -> None:
        """Update the thumbnail label from any thread safely via a queued call."""
        from PyQt6.QtCore import QMetaObject, Q_ARG
        try:
            QMetaObject.invokeMethod(
                self._thumb_label,
                "setPixmap",
                Qt.ConnectionType.QueuedConnection,
                Q_ARG(QPixmap, pixmap),
            )
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Hover / mouse events
    # ------------------------------------------------------------------

    def _apply_style(self, hovered: bool) -> None:
        if hovered:
            self.setStyleSheet(f"""
                VideoCardWidget {{
                    background-color: {COLORS['bg_elevated']};
                    border: 1px solid {COLORS['primary']};
                    border-radius: {RADIUS['md']}px;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                VideoCardWidget {{
                    background-color: {COLORS['bg_card']};
                    border: 1px solid {COLORS['border_light']};
                    border-radius: {RADIUS['md']}px;
                }}
            """)

    def enterEvent(self, event) -> None:
        self._hovered = True
        self._apply_style(hovered=True)
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        self._hovered = False
        self._apply_style(hovered=False)
        super().leaveEvent(event)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self._filepath)
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton and self._filepath:
            self.play_requested.emit(self._filepath)
        super().mouseDoubleClickEvent(event)

    # ------------------------------------------------------------------
    # Context menu
    # ------------------------------------------------------------------

    def _show_context_menu(self, pos) -> None:
        if not self._filepath:
            return
        menu = QMenu(self)
        play_action = menu.addAction("▶  Play")
        rename_action = menu.addAction("✏  Rename")
        menu.addSeparator()
        delete_action = menu.addAction("🗑  Delete")

        action = menu.exec(self.mapToGlobal(pos))
        if action == play_action:
            self.play_requested.emit(self._filepath)
        elif action == rename_action:
            self.rename_requested.emit(self._filepath)
        elif action == delete_action:
            self.delete_requested.emit(self._filepath)
