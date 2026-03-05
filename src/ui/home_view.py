"""
HomeView — main screen showing the recording library.
"""

from __future__ import annotations

import os
import time

import cv2
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QIcon, QPixmap, QPainter, QPainterPath
from PyQt6.QtCore import QRectF
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from src.core.settings import SettingsManager
from src.ui.components.video_card import VideoCardWidget
from src.ui.settings_dialog import SettingsDialog
from src.ui.styles import COLORS, RADIUS, SPACING, get_gradient_button_style
from src.utils.rename import safe_rename_video
from src.utils.resource_path import get_resource_path


class HomeView(QWidget):
    start_recording_signal = pyqtSignal()
    play_video_signal = pyqtSignal(str)

    def __init__(self) -> None:
        super().__init__()
        self.all_files: list[str] = []
        self._duration_cache: dict[str, str] = {}
        self._card_map: dict[str, VideoCardWidget] = {}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        layout.addWidget(self._build_header())
        layout.addWidget(self._build_content())

        self.refresh_list()

    # ------------------------------------------------------------------
    # Header
    # ------------------------------------------------------------------

    def _build_header(self) -> QWidget:
        header = QWidget()
        header.setStyleSheet(f"""
            background-color: {COLORS['bg_card']};
            border-bottom: 1px solid {COLORS['border']};
        """)
        header.setFixedHeight(64)

        row = QHBoxLayout(header)
        row.setContentsMargins(SPACING['lg'], 0, SPACING['lg'], 0)
        row.setSpacing(SPACING['sm'])

        # Logo + title
        logo_label = QLabel()
        logo_label.setFixedSize(36, 36)
        logo_label.setStyleSheet("background-color: transparent;")
        logo_px = self._load_logo(36, 36)
        if logo_px:
            logo_label.setPixmap(logo_px)
        row.addWidget(logo_label)

        title = QLabel("WebCap")
        title.setObjectName("title")
        title.setStyleSheet(
            f"color: {COLORS['text_primary']}; background: transparent; font-size: 20px; font-weight: 800;"
        )
        row.addWidget(title)

        row.addSpacing(SPACING['md'])

        # Search field
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search recordings…")
        self.search_box.setFixedHeight(36)
        self.search_box.setMinimumWidth(200)
        self.search_box.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.search_box.textChanged.connect(self.filter_list)
        row.addWidget(self.search_box, 1)

        row.addSpacing(SPACING['sm'])

        # Settings button
        self.settings_btn = QPushButton("⚙")
        self.settings_btn.setObjectName("icon_btn")
        self.settings_btn.setFixedSize(36, 36)
        self.settings_btn.setToolTip("Settings")
        self.settings_btn.clicked.connect(self.open_settings)
        row.addWidget(self.settings_btn)

        # New Recording button
        self.new_record_btn = QPushButton("+ New Recording")
        self.new_record_btn.setFixedHeight(36)
        self.new_record_btn.setStyleSheet(get_gradient_button_style())
        self.new_record_btn.clicked.connect(self.on_new_recording_clicked)
        row.addWidget(self.new_record_btn)

        return header

    def _load_logo(self, w: int, h: int):
        """Load the new SVG logo or fall back to PNG, return a QPixmap or None."""
        svg_path = get_resource_path("assets/logos/webcap_logo.svg")
        png_path = get_resource_path("assets/logos/webcap_dark.png")

        if os.path.exists(svg_path):
            renderer = QSvgRenderer(svg_path)
            if renderer.isValid():
                px = QPixmap(w, h)
                from PyQt6.QtGui import QColor
                px.fill(QColor(0, 0, 0, 0))
                painter = QPainter(px)
                renderer.render(painter)
                painter.end()
                return px

        if os.path.exists(png_path):
            px = QPixmap(png_path).scaled(
                w, h, Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            return px

        return None

    # ------------------------------------------------------------------
    # Content area
    # ------------------------------------------------------------------

    def _build_content(self) -> QWidget:
        self._content_widget = QWidget()
        self._content_widget.setStyleSheet(f"background-color: {COLORS['bg_main']};")
        self._content_layout = QVBoxLayout(self._content_widget)
        self._content_layout.setContentsMargins(SPACING['xl'], SPACING['lg'], SPACING['xl'], SPACING['lg'])
        self._content_layout.setSpacing(SPACING['md'])

        # Section row: title + counter badge
        section_row = QHBoxLayout()
        section_row.setContentsMargins(0, 0, 0, 0)
        self.section_label = QLabel("Recent Recordings")
        section_label_font = QFont()
        section_label_font.setPointSize(11)
        section_label_font.setWeight(QFont.Weight.DemiBold)
        self.section_label.setFont(section_label_font)
        self.section_label.setStyleSheet(f"color: {COLORS['text_secondary']}; background: transparent;")
        section_row.addWidget(self.section_label)
        section_row.addStretch()

        self.count_badge = QLabel()
        self.count_badge.setObjectName("badge")
        section_row.addWidget(self.count_badge)
        self._content_layout.addLayout(section_row)

        # Scroll area with video cards
        self._scroll_area = QScrollArea()
        self._scroll_area.setWidgetResizable(True)
        self._scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll_area.setStyleSheet(f"""
            QScrollArea {{
                border: none;
                background-color: transparent;
            }}
            QWidget#scroll_content {{
                background-color: transparent;
            }}
        """)

        self._cards_container = QWidget()
        self._cards_container.setObjectName("scroll_content")
        self._cards_layout = QVBoxLayout(self._cards_container)
        self._cards_layout.setContentsMargins(0, 0, 0, 0)
        self._cards_layout.setSpacing(SPACING['sm'])
        self._cards_layout.addStretch()

        self._scroll_area.setWidget(self._cards_container)
        self._content_layout.addWidget(self._scroll_area, 1)

        # Empty state (hidden initially)
        self._empty_widget = self._build_empty_state()
        self._content_layout.addWidget(self._empty_widget)
        self._empty_widget.hide()

        return self._content_widget

    def _build_empty_state(self) -> QWidget:
        w = QWidget()
        w.setStyleSheet("background-color: transparent;")
        layout = QVBoxLayout(w)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(SPACING['sm'])

        # Webcam icon — render from SVG or show unicode fallback
        icon_label = QLabel()
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setStyleSheet("background: transparent;")
        icon_svg = get_resource_path("assets/icons/webcam.svg")
        if os.path.exists(icon_svg):
            renderer = QSvgRenderer(icon_svg)
            if renderer.isValid():
                px = QPixmap(64, 64)
                from PyQt6.QtGui import QColor
                px.fill(QColor(0, 0, 0, 0))
                p = QPainter(px)
                renderer.render(p)
                p.end()
                icon_label.setPixmap(px)
        else:
            icon_label.setText("📷")
            icon_label.setStyleSheet(f"font-size: 48px; color: {COLORS['text_muted']}; background: transparent;")
        layout.addWidget(icon_label)

        layout.addSpacing(SPACING['sm'])

        msg = QLabel("No recordings yet")
        msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        msg.setStyleSheet(f"font-size: 16px; font-weight: 600; color: {COLORS['text_secondary']}; background: transparent;")
        layout.addWidget(msg)

        hint = QLabel("Click the button above to start a new recording")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hint.setStyleSheet(f"font-size: 13px; color: {COLORS['text_muted']}; background: transparent;")
        layout.addWidget(hint)

        layout.addSpacing(SPACING['md'])

        empty_btn = QPushButton("+ New Recording")
        empty_btn.setFixedSize(200, 40)
        empty_btn.setStyleSheet(get_gradient_button_style())
        empty_btn.clicked.connect(self.on_new_recording_clicked)
        layout.addWidget(empty_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        return w

    # ------------------------------------------------------------------
    # Slots / actions
    # ------------------------------------------------------------------

    def on_new_recording_clicked(self) -> None:
        self.request_permissions()
        self.start_recording_signal.emit()

    def request_permissions(self) -> None:
        settings = SettingsManager.load_settings()
        cam_idx = settings.get("camera_index", 0)
        cap = cv2.VideoCapture(cam_idx)
        if cap.isOpened():
            cap.release()

        try:
            import sounddevice as sd
            with sd.InputStream(samplerate=44100, channels=1):
                pass
        except Exception:
            pass

    def open_settings(self) -> None:
        dialog = SettingsDialog(self)
        dialog.exec()
        self.refresh_list()

    # ------------------------------------------------------------------
    # List management
    # ------------------------------------------------------------------

    def refresh_list(self) -> None:
        settings = SettingsManager.load_settings()
        save_dir = settings.get("save_dir", os.path.expanduser("~/Movies"))

        if not os.path.exists(save_dir):
            self._show_empty_state()
            return

        self.all_files = sorted(
            [
                f for f in os.listdir(save_dir)
                if f.lower().endswith(('.mp4', '.mkv', '.mov'))
            ],
            key=lambda x: os.path.getmtime(os.path.join(save_dir, x)),
            reverse=True,
        )

        if not self.all_files:
            self._show_empty_state()
            return

        self._show_list_state()
        self._populate_cards(self.all_files)

    def _populate_cards(self, files: list[str]) -> None:
        """Rebuild the card list from *files* (filenames only)."""
        settings = SettingsManager.load_settings()
        save_dir = settings.get("save_dir", os.path.expanduser("~/Movies"))

        # Remove existing cards (keep the trailing stretch)
        while self._cards_layout.count() > 1:
            item = self._cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self._card_map.clear()

        for filename in files:
            path = os.path.join(save_dir, filename)
            if not os.path.exists(path):
                continue

            size_mb = os.path.getsize(path) / (1024 * 1024)
            date_str = time.strftime('%b %d, %Y  %H:%M', time.localtime(os.path.getmtime(path)))

            # Duration (cached)
            if path in self._duration_cache:
                duration_str = self._duration_cache[path]
            else:
                duration_str = ""
                try:
                    cap = cv2.VideoCapture(path)
                    if cap.isOpened():
                        fps = cap.get(cv2.CAP_PROP_FPS)
                        frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
                        if fps > 0:
                            secs = int(frame_count / fps)
                            m, s = divmod(secs, 60)
                            duration_str = f"{m:02d}:{s:02d}"
                        cap.release()
                except Exception:
                    pass
                self._duration_cache[path] = duration_str

            card = VideoCardWidget()
            card.set_video_data(path, filename, size_mb, duration_str, date_str)

            card.play_requested.connect(self.play_video_signal.emit)
            card.rename_requested.connect(self._on_rename_requested)
            card.delete_requested.connect(self._on_delete_requested)

            self._cards_layout.insertWidget(self._cards_layout.count() - 1, card)
            self._card_map[path] = card

        count = len(files)
        self.count_badge.setText(f"{count} video{'s' if count != 1 else ''}")

    def filter_list(self, text: str) -> None:
        filtered = [f for f in self.all_files if text.lower() in f.lower()]
        if filtered or not text:
            self._show_list_state()
            self._populate_cards(filtered if text else self.all_files)
        else:
            # Show empty state only if there are normally recordings
            self._populate_cards([])

    def _show_empty_state(self) -> None:
        self._scroll_area.hide()
        self.section_label.hide()
        self.count_badge.hide()
        self._empty_widget.show()

    def _show_list_state(self) -> None:
        self._empty_widget.hide()
        self._scroll_area.show()
        self.section_label.show()
        self.count_badge.show()

    # ------------------------------------------------------------------
    # Rename / delete handlers (called from VideoCardWidget signals)
    # ------------------------------------------------------------------

    def _on_rename_requested(self, path: str) -> None:
        old_name = os.path.basename(path)
        new_name, ok = QInputDialog.getText(self, "Rename Video", "New name:", text=old_name)
        if ok and new_name:
            try:
                safe_rename_video(path, new_name)
                self.refresh_list()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not rename file: {e}")

    def _on_delete_requested(self, path: str) -> None:
        confirm = QMessageBox.question(
            self, "Delete Video",
            f"Are you sure you want to delete\n{os.path.basename(path)}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if confirm == QMessageBox.StandardButton.Yes:
            try:
                os.remove(path)
                self.refresh_list()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not delete file: {e}")
