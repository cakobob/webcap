"""
SettingsDialog — application settings grouped in visual sections.
All styling is inherited from GLOBAL_STYLESHEET; no inline setStyleSheet.
"""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from src.core.settings import SettingsManager
from src.ui.styles import COLORS, RADIUS, SPACING, get_gradient_button_style


class SettingsDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setMinimumSize(480, 560)
        self.resize(480, 600)

        self.settings = SettingsManager.load_settings()

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Title bar
        outer.addWidget(self._build_title_bar())

        # Scrollable content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("border: none;")

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(SPACING['lg'], SPACING['md'], SPACING['lg'], SPACING['md'])
        content_layout.setSpacing(SPACING['md'])

        content_layout.addWidget(self._build_storage_section())
        content_layout.addWidget(self._build_recording_section())
        content_layout.addWidget(self._build_timing_section())
        content_layout.addStretch()

        scroll.setWidget(content)
        outer.addWidget(scroll, 1)

        # Save button
        outer.addWidget(self._build_save_bar())

    # ------------------------------------------------------------------
    # Sub-builders
    # ------------------------------------------------------------------

    def _build_title_bar(self) -> QWidget:
        bar = QWidget()
        bar.setStyleSheet(
            f"background-color: {COLORS['bg_card']}; "
            f"border-bottom: 1px solid {COLORS['border']};"
        )
        bar.setFixedHeight(56)
        row = QHBoxLayout(bar)
        row.setContentsMargins(SPACING['lg'], 0, SPACING['lg'], 0)

        title = QLabel("Settings")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        f = QFont()
        f.setPointSize(15)
        f.setWeight(QFont.Weight.Bold)
        title.setFont(f)
        title.setStyleSheet(f"color: {COLORS['text_primary']}; background: transparent;")
        row.addWidget(title)

        return bar

    def _build_storage_section(self) -> QGroupBox:
        box = QGroupBox("STORAGE")
        form = QFormLayout(box)
        form.setContentsMargins(SPACING['sm'], SPACING['md'], SPACING['sm'], SPACING['sm'])
        form.setSpacing(SPACING['md'])
        form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)

        dir_row = QHBoxLayout()
        dir_row.setSpacing(SPACING['sm'])
        self.dir_input = QLineEdit(self.settings.get("save_dir", ""))
        self.dir_input.setPlaceholderText("/Users/…/Movies")
        browse_btn = QPushButton("Browse")
        browse_btn.setFixedWidth(80)
        browse_btn.setFixedHeight(34)
        browse_btn.clicked.connect(self._browse_directory)
        dir_row.addWidget(self.dir_input)
        dir_row.addWidget(browse_btn)

        form.addRow(self._field_label("Save Directory"), dir_row)
        return box

    def _build_recording_section(self) -> QGroupBox:
        from src.core.recorder import Recorder

        box = QGroupBox("RECORDING")
        form = QFormLayout(box)
        form.setContentsMargins(SPACING['sm'], SPACING['md'], SPACING['sm'], SPACING['sm'])
        form.setSpacing(SPACING['md'])
        form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)

        # Camera
        self.camera_combo = QComboBox()
        for idx, name in Recorder.get_available_cameras():
            self.camera_combo.addItem(name, idx)
        cur_cam = self.settings.get("camera_index", 0)
        i = self.camera_combo.findData(cur_cam)
        if i >= 0:
            self.camera_combo.setCurrentIndex(i)
        form.addRow(self._field_label("Camera"), self.camera_combo)

        # Microphone
        self.mic_combo = QComboBox()
        self.mic_combo.addItem("Default", None)
        for idx, name in Recorder.get_available_microphones():
            self.mic_combo.addItem(name, idx)
        cur_mic = self.settings.get("mic_index", None)
        i = self.mic_combo.findData(cur_mic)
        if i >= 0:
            self.mic_combo.setCurrentIndex(i)
        form.addRow(self._field_label("Microphone"), self.mic_combo)

        # Resolution
        self.res_combo = QComboBox()
        self.res_combo.addItems(["1920x1080", "1280x720", "640x480"])
        self.res_combo.setCurrentText(self.settings.get("resolution", "1280x720"))
        form.addRow(self._field_label("Resolution"), self.res_combo)

        # Format
        self.format_combo = QComboBox()
        self.format_combo.addItems(["mp4", "mkv", "mov"])
        self.format_combo.setCurrentText(self.settings.get("video_format", "mp4"))
        form.addRow(self._field_label("Format"), self.format_combo)

        # Aspect ratio
        self.ar_combo = QComboBox()
        self.ar_combo.addItems(["Default", "16:9", "4:3", "1:1"])
        self.ar_combo.setCurrentText(self.settings.get("aspect_ratio", "Default"))
        form.addRow(self._field_label("Aspect Ratio"), self.ar_combo)

        # Frame Rate
        self.fps_combo = QComboBox()
        self.fps_combo.addItems(["15 fps", "24 fps", "30 fps", "60 fps"])
        current_fps = self.settings.get("fps", 30)
        fps_text = f"{current_fps} fps"
        fps_index = self.fps_combo.findText(fps_text)
        if fps_index >= 0:
            self.fps_combo.setCurrentIndex(fps_index)
        else:
            self.fps_combo.setCurrentText("30 fps")
        form.addRow(self._field_label("Frame Rate"), self.fps_combo)

        return box

    def _build_timing_section(self) -> QGroupBox:
        box = QGroupBox("TIMING")
        form = QFormLayout(box)
        form.setContentsMargins(SPACING['sm'], SPACING['md'], SPACING['sm'], SPACING['sm'])
        form.setSpacing(SPACING['md'])
        form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)

        # Start delay
        self.delay_spin = QSpinBox()
        self.delay_spin.setRange(0, 60)
        self.delay_spin.setSuffix(" sec")
        self.delay_spin.setValue(self.settings.get("start_delay", 0))
        form.addRow(self._field_label("Start Delay"), self.delay_spin)

        # Auto-stop
        autostop_row = QHBoxLayout()
        autostop_row.setSpacing(SPACING['sm'])

        self.autostop_check = QCheckBox("Enable")
        self.autostop_check.setChecked(self.settings.get("auto_stop_enabled", False))
        self.autostop_check.toggled.connect(self._toggle_autostop)

        self.autostop_spin = QSpinBox()
        self.autostop_spin.setRange(1, 120)
        self.autostop_spin.setSuffix(" min")
        self.autostop_spin.setValue(self.settings.get("auto_stop_duration", 0) or 1)
        self.autostop_spin.setEnabled(self.autostop_check.isChecked())

        autostop_row.addWidget(self.autostop_check)
        autostop_row.addWidget(self.autostop_spin)
        autostop_row.addStretch()

        form.addRow(self._field_label("Auto-stop"), autostop_row)

        return box

    def _build_save_bar(self) -> QWidget:
        bar = QWidget()
        bar.setStyleSheet(
            f"background-color: {COLORS['bg_card']}; "
            f"border-top: 1px solid {COLORS['border']};"
        )
        bar.setFixedHeight(64)

        row = QHBoxLayout(bar)
        row.setContentsMargins(SPACING['lg'], SPACING['sm'], SPACING['lg'], SPACING['sm'])

        self.save_btn = QPushButton("Save Settings")
        self.save_btn.setFixedHeight(44)
        self.save_btn.setStyleSheet(get_gradient_button_style())
        self.save_btn.clicked.connect(self.save_and_close)
        row.addWidget(self.save_btn)

        return bar

    @staticmethod
    def _field_label(text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet(
            f"color: {COLORS['text_secondary']}; background: transparent; font-size: 13px;"
        )
        return lbl

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    def _browse_directory(self) -> None:
        directory = QFileDialog.getExistingDirectory(self, "Select Save Directory")
        if directory:
            self.dir_input.setText(directory)

    def _toggle_autostop(self, checked: bool) -> None:
        self.autostop_spin.setEnabled(checked)

    def save_and_close(self) -> None:
        # Parse FPS from combo box text (e.g., "30 fps" -> 30)
        fps_text = self.fps_combo.currentText()
        fps_value = int(fps_text.split()[0])
        
        new_settings = {
            "save_dir": self.dir_input.text(),
            "start_delay": self.delay_spin.value(),
            "auto_stop_enabled": self.autostop_check.isChecked(),
            "auto_stop_duration": self.autostop_spin.value() if self.autostop_check.isChecked() else 0,
            "resolution": self.res_combo.currentText(),
            "camera_index": self.camera_combo.currentData(),
            "mic_index": self.mic_combo.currentData(),
            "video_format": self.format_combo.currentText(),
            "aspect_ratio": self.ar_combo.currentText(),
            "fps": fps_value,
        }
        SettingsManager.save_settings(new_settings)
        self.accept()

    def get_settings(self) -> dict:
        return SettingsManager.load_settings()

    # Backward-compatibility aliases
    def browse_directory(self) -> None:
        self._browse_directory()

    def toggle_autostop(self, checked: bool) -> None:
        self._toggle_autostop(checked)
