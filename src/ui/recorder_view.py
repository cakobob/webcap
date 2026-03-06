"""
RecorderView — camera preview and recording controls.

Recording logic (start_recording_now, stop_recording_ui, etc.) is
preserved exactly.  Only visual presentation has changed.
"""

from __future__ import annotations

import os
import time

import cv2
from PyQt6.QtCore import (
    Qt,
    QPropertyAnimation,
    QEasingCurve,
    QTimer,
    pyqtSignal,
)
from PyQt6.QtGui import QFont, QImage, QPixmap, QKeyEvent
from PyQt6.QtWidgets import (
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from src.core.recorder import Recorder
from src.core.settings import SettingsManager
from src.ui.styles import (
    COLORS,
    RADIUS,
    SPACING,
    get_record_btn_active_style,
    get_record_btn_idle_style,
    get_top_bar_style,
)


class RecorderView(QWidget):
    finished_signal = pyqtSignal(str)
    back_signal = pyqtSignal()

    def __init__(self) -> None:
        super().__init__()
        self.recorder = Recorder()

        self._countdown_val = 0
        self._countdown_timer: QTimer | None = None
        self._recording_timer: QTimer | None = None
        self._blink_anim: QPropertyAnimation | None = None
        self._recording_start_time: float = 0.0
        self._auto_stop_total_secs: int = 0

        main = QVBoxLayout(self)
        main.setContentsMargins(0, 0, 0, 0)
        main.setSpacing(0)

        main.addWidget(self._build_top_bar())
        main.addWidget(self._build_preview(), 1)
        main.addWidget(self._build_controls())

        # Frame update timer
        self._frame_timer = QTimer()
        self._frame_timer.timeout.connect(self.update_frame)

        # Enable keyboard focus for shortcuts
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
        self.back_btn.clicked.connect(self.on_back_clicked)
        row.addWidget(self.back_btn)

        row.addStretch()

        self._rec_indicator_label = QLabel("● REC")
        self._rec_indicator_label.setStyleSheet(
            f"color: {COLORS['danger']}; font-size: 12px; font-weight: 700; "
            f"letter-spacing: 1px; background: transparent;"
        )
        self._rec_indicator_label.hide()
        row.addWidget(self._rec_indicator_label)

        row.addStretch()
        # Reserve space so back button stays left-aligned even without stretch
        spacer = QWidget()
        spacer.setFixedWidth(80)
        row.addWidget(spacer)

        return bar

    def _build_preview(self) -> QWidget:
        container = QWidget()
        container.setStyleSheet("background-color: #000000;")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)

        self.video_label = QLabel("Initializing Camera…")
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_label.setStyleSheet(
            f"background-color: #000000; color: {COLORS['text_secondary']}; border: none;"
        )
        self.video_label.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        layout.addWidget(self.video_label)

        return container

    def _build_controls(self) -> QWidget:
        wrapper = QWidget()
        wrapper_layout = QVBoxLayout(wrapper)
        wrapper_layout.setContentsMargins(0, 0, 0, 0)
        wrapper_layout.setSpacing(0)

        # Main controls bar
        self.controls_widget = QWidget()
        self.controls_widget.setStyleSheet(
            f"background-color: {COLORS['bg_card']}; "
            f"border-top: 1px solid {COLORS['border']};"
        )
        self.controls_widget.setFixedHeight(72)

        row = QHBoxLayout(self.controls_widget)
        row.setContentsMargins(SPACING['lg'], 0, SPACING['lg'], 0)
        row.setSpacing(SPACING['md'])

        # Cancel button (shown only during countdown)
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setFixedHeight(36)
        self.cancel_btn.setMinimumWidth(88)
        self.cancel_btn.clicked.connect(self.cancel_countdown)
        self.cancel_btn.hide()
        row.addWidget(self.cancel_btn)

        row.addStretch()

        # Status dot (blinking, shown when recording)
        self.status_label = QLabel("●")
        self.status_label.setStyleSheet(
            f"color: {COLORS['danger']}; font-size: 20px; background: transparent;"
        )
        self.status_label.hide()
        row.addWidget(self.status_label)

        # Timer label
        self.timer_label = QLabel("00:00")
        self.timer_label.setObjectName("timer")
        row.addWidget(self.timer_label)

        row.addStretch()

        # Start / Stop button
        self.start_btn = QPushButton("Start Recording")
        self.start_btn.setFixedHeight(44)
        self.start_btn.setMinimumWidth(160)
        self.start_btn.setStyleSheet(get_record_btn_idle_style())
        self.start_btn.clicked.connect(self.toggle_recording)
        row.addWidget(self.start_btn)

        wrapper_layout.addWidget(self.controls_widget)

        # Auto-stop progress bar (hidden by default)
        self.autostop_bar = QProgressBar()
        self.autostop_bar.setFixedHeight(4)
        self.autostop_bar.setTextVisible(False)
        self.autostop_bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: {COLORS['bg_surface']};
                border: none;
                border-radius: 0px;
            }}
            QProgressBar::chunk {{
                background-color: {COLORS['primary']};
            }}
        """)
        self.autostop_bar.hide()
        wrapper_layout.addWidget(self.autostop_bar)

        return wrapper

    # ------------------------------------------------------------------
    # Session lifecycle (unchanged logic, updated style calls)
    # ------------------------------------------------------------------

    def start_session(self) -> None:
        """Called when entering this view."""
        settings = SettingsManager.load_settings()
        cam_idx = settings.get("camera_index", 0)
        resolution = settings.get("resolution", "1280x720")
        aspect_ratio = settings.get("aspect_ratio", "Default")
        fps = settings.get("fps", 30)

        self.video_label.setText("Initializing Camera…")
        if self.recorder.start_camera(
            camera_index=cam_idx, resolution=resolution, aspect_ratio=aspect_ratio, fps=fps
        ):
            self._frame_timer.start(30)
        else:
            self.video_label.setText("Camera Error")

        self._reset_ui_to_idle()

    def stop_session(self) -> None:
        """Called when leaving this view."""
        self._frame_timer.stop()
        self._stop_blink_animation()
        if self._countdown_timer:
            self._countdown_timer.stop()
        if self._recording_timer:
            self._recording_timer.stop()
            self._recording_timer = None
        self.recorder.stop_camera()
        self.video_label.clear()

    def update_frame(self) -> None:
        frame = self.recorder.get_frame()
        if frame is None:
            return
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        qi = QImage(rgb.data, w, h, ch * w, QImage.Format.Format_RGB888)
        scaled = qi.scaled(
            self.video_label.width(),
            self.video_label.height(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.video_label.setPixmap(QPixmap.fromImage(scaled))

    # ------------------------------------------------------------------
    # Recording control
    # ------------------------------------------------------------------

    def toggle_recording(self) -> None:
        if self.recorder.is_recording:
            self.stop_recording_ui()
        else:
            self.initiate_recording()

    def initiate_recording(self) -> None:
        settings = SettingsManager.load_settings()
        delay = settings.get("start_delay", 0)

        if delay > 0:
            self._frame_timer.stop()
            self.start_btn.setEnabled(False)
            self.back_btn.setEnabled(False)
            self.cancel_btn.show()
            self.cancel_btn.setEnabled(True)

            self._countdown_val = delay
            self._show_countdown_number(self._countdown_val)

            self._countdown_timer = QTimer()
            self._countdown_timer.timeout.connect(self.update_countdown)
            self._countdown_timer.start(1000)
        else:
            self.start_recording_now()

    def update_countdown(self) -> None:
        self._countdown_val -= 1
        if self._countdown_val > 0:
            self._show_countdown_number(self._countdown_val)
        else:
            self._countdown_timer.stop()
            self.start_recording_now()

    def _show_countdown_number(self, number: int) -> None:
        """Display countdown number with a fade-in animation."""
        self.video_label.clear()
        self.video_label.setText(str(number))
        font = QFont()
        font.setPointSize(100)
        font.setWeight(QFont.Weight.Black)
        self.video_label.setFont(font)
        self.video_label.setStyleSheet(
            f"background-color: #000000; color: {COLORS['text_primary']}; border: none;"
        )

        # Fade-in via QPropertyAnimation on opacity effect
        effect = QGraphicsOpacityEffect(self.video_label)
        self.video_label.setGraphicsEffect(effect)
        anim = QPropertyAnimation(effect, b"opacity", self)
        anim.setDuration(400)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        anim.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)

    def cancel_countdown(self) -> None:
        if self._countdown_timer:
            self._countdown_timer.stop()

        self.cancel_btn.hide()
        self.start_btn.setEnabled(True)
        self.back_btn.setEnabled(True)

        self._reset_video_label()
        self._frame_timer.start(30)

    def start_recording_now(self) -> None:
        """Start actual recording (logic unchanged)."""
        self.cancel_btn.hide()
        self._reset_video_label()

        if not self._frame_timer.isActive():
            self._frame_timer.start(30)

        settings = SettingsManager.load_settings()
        save_dir = settings.get("save_dir", os.path.expanduser("~/Movies"))
        video_format = settings.get("video_format", "mp4")

        os.makedirs(save_dir, exist_ok=True)

        timestamp = time.strftime("%Y-%m-%d_%H-%M-%S")
        filename = os.path.join(save_dir, f"WebCap_{timestamp}.{video_format}")

        mic_index = settings.get("mic_index", None)
        audio_channels = settings.get("audio_channels", 1)
        self.recorder.start_recording(filename, mic_index=mic_index, audio_channels=audio_channels)

        # Update UI
        self.start_btn.setEnabled(True)
        self.start_btn.setText("Stop Recording")
        self.start_btn.setStyleSheet(get_record_btn_active_style())
        self.back_btn.setEnabled(False)

        # Show blinking indicator using QPropertyAnimation
        self.status_label.show()
        self._rec_indicator_label.show()
        self._start_blink_animation()

        # Recording elapsed timer
        self._recording_start_time = time.time()
        self._recording_timer = QTimer()
        self._recording_timer.timeout.connect(self._update_recording_timer)
        self._recording_timer.start(1000)

        # Auto-stop
        if settings.get("auto_stop_enabled", False):
            duration_min = settings.get("auto_stop_duration", 0)
            if duration_min > 0:
                self._auto_stop_total_secs = duration_min * 60
                self.autostop_bar.setRange(0, self._auto_stop_total_secs)
                self.autostop_bar.setValue(0)
                self.autostop_bar.show()
                QTimer.singleShot(duration_min * 60 * 1000, self.stop_recording_ui)
            else:
                self._auto_stop_total_secs = 0

    def _update_recording_timer(self) -> None:
        elapsed = int(time.time() - self._recording_start_time)
        m, s = divmod(elapsed, 60)
        self.timer_label.setText(f"{m:02d}:{s:02d}")

        if self._auto_stop_total_secs > 0:
            self.autostop_bar.setValue(min(elapsed, self._auto_stop_total_secs))

    def stop_recording_ui(self) -> None:
        if not self.recorder.is_recording:
            return

        self.start_btn.setEnabled(False)
        self.start_btn.setText("Processing…")

        def on_mux_complete(filename: str) -> None:
            if filename and os.path.exists(filename):
                self.finished_signal.emit(filename)
            else:
                self.finished_signal.emit("")

        try:
            self.recorder.stop_recording(on_finished=on_mux_complete)
        except Exception as e:
            self.start_btn.setEnabled(True)
            self.start_btn.setText("Start Recording")
            QMessageBox.critical(self, "Error", f"Failed to stop recording: {e}")
            return

        self._reset_ui_to_idle()

    def _reset_ui_to_idle(self) -> None:
        """Restore controls to initial / idle state."""
        self.cancel_btn.hide()
        self.start_btn.setEnabled(True)
        self.start_btn.setText("Start Recording")
        self.start_btn.setStyleSheet(get_record_btn_idle_style())
        self.back_btn.setEnabled(True)

        self._stop_blink_animation()
        self.status_label.hide()
        self._rec_indicator_label.hide()

        if self._recording_timer:
            self._recording_timer.stop()
            self._recording_timer = None
        self.timer_label.setText("00:00")

        self.autostop_bar.hide()
        self.autostop_bar.setValue(0)
        self._auto_stop_total_secs = 0

    def _reset_video_label(self) -> None:
        self.video_label.clear()
        self.video_label.setText("")
        self.video_label.setFont(QFont())
        self.video_label.setGraphicsEffect(None)
        self.video_label.setStyleSheet(
            f"background-color: #000000; color: {COLORS['text_secondary']}; border: none;"
        )

    # ------------------------------------------------------------------
    # Blink animation (QPropertyAnimation instead of QTimer)
    # ------------------------------------------------------------------

    def _start_blink_animation(self) -> None:
        self._stop_blink_animation()
        effect = QGraphicsOpacityEffect(self.status_label)
        self.status_label.setGraphicsEffect(effect)

        anim = QPropertyAnimation(effect, b"opacity", self)
        anim.setDuration(900)
        anim.setStartValue(1.0)
        anim.setEndValue(0.1)
        anim.setEasingCurve(QEasingCurve.Type.SineCurve)
        anim.setLoopCount(-1)  # loop forever
        anim.start()
        self._blink_anim = anim

    def _stop_blink_animation(self) -> None:
        if self._blink_anim:
            self._blink_anim.stop()
            self._blink_anim = None
        if self.status_label.graphicsEffect():
            self.status_label.setGraphicsEffect(None)

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------

    def on_back_clicked(self) -> None:
        self.stop_session()
        self.back_signal.emit()

    # Kept for backward compatibility — blink_status was public in old code
    def blink_status(self) -> None:
        pass

    # ------------------------------------------------------------------
    # Keyboard shortcuts
    # ------------------------------------------------------------------

    def keyPressEvent(self, a0) -> None:
        """Handle keyboard shortcuts."""
        key = a0.key()
        modifiers = a0.modifiers()

        # Space: Toggle recording (start/stop)
        if key == Qt.Key.Key_Space:
            if self.start_btn.isEnabled():
                self.toggle_recording()
            return

        # ESC: Cancel countdown OR go back
        if key == Qt.Key.Key_Escape:
            # If countdown is active, cancel it
            if self._countdown_timer is not None:
                self.cancel_countdown()
            # If recording, stop it
            elif self.recorder.is_recording:
                self.stop_recording_ui()
            # Otherwise, go back
            elif self.back_btn.isEnabled():
                self.on_back_clicked()
            return

        # Call parent implementation for unhandled keys
        super().keyPressEvent(a0)
