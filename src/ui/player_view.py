"""
PlayerView — video playback with skip controls, volume slider, and keyboard shortcuts.
"""

from __future__ import annotations

import os

from PyQt6.QtCore import Qt, QUrl, pyqtSignal, QTimer
from PyQt6.QtGui import QFont
from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer
from PyQt6.QtMultimediaWidgets import QVideoWidget
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QSlider,
    QStyle,
    QVBoxLayout,
    QWidget,
)

from src.ui.styles import COLORS, RADIUS, SPACING, get_danger_btn_style, get_top_bar_style
from src.utils.rename import safe_rename_video


class PlayerView(QWidget):
    back_signal = pyqtSignal()
    delete_signal = pyqtSignal(str)
    rename_signal = pyqtSignal(str, str)

    _SKIP_MS = 10_000  # 10 seconds in milliseconds

    def __init__(self) -> None:
        super().__init__()
        self.current_file_path: str = ""

        main = QVBoxLayout(self)
        main.setContentsMargins(0, 0, 0, 0)
        main.setSpacing(0)

        main.addWidget(self._build_top_bar())
        main.addWidget(self._build_video_area(), 1)
        main.addWidget(self._build_controls())

        # Media player setup
        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.audio_output.setVolume(1.0)
        self.media_player.setAudioOutput(self.audio_output)
        self.media_player.setVideoOutput(self.video_widget)

        # Connect media signals
        self.media_player.positionChanged.connect(self._position_changed)
        self.media_player.durationChanged.connect(self._duration_changed)
        self.media_player.playbackStateChanged.connect(self._playback_state_changed)

        # Enable keyboard focus so keyPressEvent fires
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    # ------------------------------------------------------------------
    # Layout builders
    # ------------------------------------------------------------------

    def _build_top_bar(self) -> QWidget:
        bar = QWidget()
        bar.setStyleSheet(get_top_bar_style())
        bar.setFixedHeight(56)

        row = QHBoxLayout(bar)
        row.setContentsMargins(SPACING['md'], 0, SPACING['md'], 0)
        row.setSpacing(SPACING['sm'])

        self.back_btn = QPushButton("← Back")
        self.back_btn.setFixedHeight(32)
        self.back_btn.setMinimumWidth(80)
        self.back_btn.clicked.connect(self.stop_and_back)
        row.addWidget(self.back_btn)

        self.title_label = QLabel("Video Player")
        self.title_label.setObjectName("secondary")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        row.addWidget(self.title_label, 1)

        self.rename_btn = QPushButton("✏ Rename")
        self.rename_btn.setFixedHeight(32)
        self.rename_btn.setMinimumWidth(88)
        self.rename_btn.clicked.connect(self.rename_video)
        row.addWidget(self.rename_btn)

        self.delete_btn = QPushButton("🗑 Delete")
        self.delete_btn.setFixedHeight(32)
        self.delete_btn.setMinimumWidth(88)
        self.delete_btn.setStyleSheet(get_danger_btn_style())
        self.delete_btn.clicked.connect(self.delete_video)
        row.addWidget(self.delete_btn)

        return bar

    def _build_video_area(self) -> QWidget:
        container = QWidget()
        container.setStyleSheet("background-color: #000000;")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)

        self.video_widget = QVideoWidget()
        self.video_widget.setStyleSheet("background-color: #000000;")
        layout.addWidget(self.video_widget)

        return container

    def _build_controls(self) -> QWidget:
        controls = QWidget()
        controls.setStyleSheet(
            f"background-color: {COLORS['bg_card']}; "
            f"border-top: 1px solid {COLORS['border']};"
        )
        controls.setFixedHeight(88)

        col = QVBoxLayout(controls)
        col.setContentsMargins(SPACING['lg'], SPACING['sm'], SPACING['lg'], SPACING['sm'])
        col.setSpacing(SPACING['sm'])

        # --- Row 1: position slider (full width) ---
        self.position_slider = QSlider(Qt.Orientation.Horizontal)
        self.position_slider.sliderMoved.connect(self._set_position)
        col.addWidget(self.position_slider)

        # --- Row 2: buttons + time labels + volume ---
        row2 = QHBoxLayout()
        row2.setContentsMargins(0, 0, 0, 0)
        row2.setSpacing(SPACING['sm'])

        # Skip back button
        self.skip_back_btn = QPushButton("−10s")
        self.skip_back_btn.setFixedSize(48, 36)
        self.skip_back_btn.setObjectName("icon_btn")
        self.skip_back_btn.setToolTip("Skip back 10 seconds")
        self.skip_back_btn.clicked.connect(self.skip_back)
        row2.addWidget(self.skip_back_btn)

        # Play / Pause button
        self.play_btn = QPushButton()
        self.play_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay))
        self.play_btn.setFixedSize(44, 44)
        self.play_btn.setObjectName("icon_btn")
        self.play_btn.clicked.connect(self.toggle_playback)
        row2.addWidget(self.play_btn)

        # Skip forward button
        self.skip_fwd_btn = QPushButton("+10s")
        self.skip_fwd_btn.setFixedSize(48, 36)
        self.skip_fwd_btn.setObjectName("icon_btn")
        self.skip_fwd_btn.setToolTip("Skip forward 10 seconds")
        self.skip_fwd_btn.clicked.connect(self.skip_forward)
        row2.addWidget(self.skip_fwd_btn)

        row2.addSpacing(SPACING['sm'])

        # Time label: "01:23 / 05:45"
        self.time_label = QLabel("00:00 / 00:00")
        self.time_label.setObjectName("timer")
        self.time_label.setStyleSheet(
            f"font-size: 13px; font-family: 'SF Mono', 'Consolas', monospace; "
            f"color: {COLORS['text_secondary']}; background: transparent;"
        )
        row2.addWidget(self.time_label)

        row2.addStretch()

        # Volume label + slider
        vol_label = QLabel("🔊")
        vol_label.setStyleSheet(f"background: transparent; color: {COLORS['text_secondary']};")
        row2.addWidget(vol_label)

        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setFixedWidth(96)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(100)
        self.volume_slider.setToolTip("Volume")
        self.volume_slider.valueChanged.connect(self._set_volume)
        row2.addWidget(self.volume_slider)

        col.addLayout(row2)

        return controls

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load_video(self, path: str) -> None:
        self.current_file_path = path
        self.media_player.setSource(QUrl.fromLocalFile(path))
        filename = os.path.basename(path)
        # Truncate long filenames in the title bar
        display = filename if len(filename) <= 50 else filename[:47] + "…"
        self.title_label.setText(display)
        self.title_label.setToolTip(filename)
        self.play_btn.setEnabled(True)
        self.media_player.play()

    # ------------------------------------------------------------------
    # Playback controls
    # ------------------------------------------------------------------

    def toggle_playback(self) -> None:
        if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.media_player.pause()
        else:
            self.media_player.play()

    def skip_back(self) -> None:
        pos = max(0, self.media_player.position() - self._SKIP_MS)
        self.media_player.setPosition(pos)

    def skip_forward(self) -> None:
        duration = self.media_player.duration()
        pos = min(duration, self.media_player.position() + self._SKIP_MS)
        self.media_player.setPosition(pos)

    # ------------------------------------------------------------------
    # Keyboard shortcuts
    # ------------------------------------------------------------------

    def keyPressEvent(self, event) -> None:
        key = event.key()
        if key == Qt.Key.Key_Space:
            self.toggle_playback()
        elif key == Qt.Key.Key_Left:
            self.skip_back()
        elif key == Qt.Key.Key_Right:
            self.skip_forward()
        else:
            super().keyPressEvent(event)

    # ------------------------------------------------------------------
    # Media signal handlers
    # ------------------------------------------------------------------

    def _playback_state_changed(self, state) -> None:
        if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.play_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPause))
        else:
            self.play_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay))

    def _position_changed(self, position: int) -> None:
        self.position_slider.setValue(position)
        duration = self.media_player.duration()
        self.time_label.setText(
            f"{self._fmt(position)} / {self._fmt(duration)}"
        )

    def _duration_changed(self, duration: int) -> None:
        self.position_slider.setRange(0, duration)
        self.time_label.setText(
            f"{self._fmt(0)} / {self._fmt(duration)}"
        )

    def _set_position(self, position: int) -> None:
        self.media_player.setPosition(position)

    def _set_volume(self, value: int) -> None:
        self.audio_output.setVolume(value / 100.0)

    @staticmethod
    def _fmt(ms: int) -> str:
        seconds = ms // 1000
        m, s = divmod(seconds, 60)
        return f"{m:02d}:{s:02d}"

    # ------------------------------------------------------------------
    # Rename / Delete
    # ------------------------------------------------------------------

    def rename_video(self) -> None:
        if not self.current_file_path:
            return
        old_name = os.path.basename(self.current_file_path)
        new_name, ok = QInputDialog.getText(self, "Rename Video", "New name:", text=old_name)
        if ok and new_name:
            try:
                old_path = self.current_file_path
                self.media_player.stop()
                new_path = safe_rename_video(old_path, new_name)
                self.current_file_path = new_path
                self.title_label.setText(os.path.basename(new_path))
                self.rename_signal.emit(old_path, new_path)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not rename file: {e}")

    def delete_video(self) -> None:
        if not self.current_file_path:
            return
        filename = os.path.basename(self.current_file_path)
        confirm = QMessageBox.question(
            self, "Delete Video",
            f"Are you sure you want to delete\n{filename}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if confirm == QMessageBox.StandardButton.Yes:
            try:
                self.media_player.stop()
                os.remove(self.current_file_path)
                self.delete_signal.emit(self.current_file_path)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not delete file: {e}")

    def stop_and_back(self) -> None:
        self.media_player.stop()
        self.back_signal.emit()

    # ------------------------------------------------------------------
    # Backward-compatibility aliases
    # ------------------------------------------------------------------

    def format_time(self, ms: int) -> str:
        return self._fmt(ms)

    def position_changed(self, position: int) -> None:
        self._position_changed(position)

    def duration_changed(self, duration: int) -> None:
        self._duration_changed(duration)

    def media_state_changed(self, state) -> None:
        self._playback_state_changed(state)

    def set_position(self, position: int) -> None:
        self._set_position(position)
