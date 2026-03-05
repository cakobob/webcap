from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QFileDialog, QHBoxLayout, QSpinBox, QFormLayout, QCheckBox, QComboBox
from src.core.settings import SettingsManager

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setGeometry(200, 200, 400, 300)
        
        self.settings = SettingsManager.load_settings()
        self.main_layout = QVBoxLayout(self)
        self.form_layout = QFormLayout()
        
        # Save Directory
        self.dir_layout = QHBoxLayout()
        self.dir_input = QLineEdit(self.settings.get("save_dir", ""))
        self.browse_btn = QPushButton("Browse")
        self.browse_btn.clicked.connect(self.browse_directory)
        self.dir_layout.addWidget(self.dir_input)
        self.dir_layout.addWidget(self.browse_btn)
        self.form_layout.addRow("Save Directory:", self.dir_layout)
        
        # Start Delay
        self.delay_spin = QSpinBox()
        self.delay_spin.setRange(0, 60)
        self.delay_spin.setSuffix(" sec")
        self.delay_spin.setValue(self.settings.get("start_delay", 0))
        self.form_layout.addRow("Start Delay:", self.delay_spin)
        
        # Auto-stop Duration
        self.autostop_layout = QHBoxLayout()
        self.autostop_check = QCheckBox("Enable Auto-stop")
        self.autostop_check.setChecked(self.settings.get("auto_stop_enabled", False))
        self.autostop_check.toggled.connect(self.toggle_autostop)
        
        self.autostop_spin = QSpinBox()
        self.autostop_spin.setRange(0, 120)
        self.autostop_spin.setSuffix(" min")
        self.autostop_spin.setValue(self.settings.get("auto_stop_duration", 0))
        self.autostop_spin.setEnabled(self.autostop_check.isChecked())
        
        self.autostop_layout.addWidget(self.autostop_check)
        self.autostop_layout.addWidget(self.autostop_spin)
        self.form_layout.addRow("Auto-stop:", self.autostop_layout)

        # --- Quality & Source ---
        from src.core.recorder import Recorder

        # Camera Source
        self.camera_combo = QComboBox()
        cameras = Recorder.get_available_cameras()
        for idx, name in cameras:
            self.camera_combo.addItem(name, idx)
        # Set current index
        current_cam = self.settings.get("camera_index", 0)
        idx = self.camera_combo.findData(current_cam)
        if idx >= 0: self.camera_combo.setCurrentIndex(idx)
        self.form_layout.addRow("Camera:", self.camera_combo)

        # Microphone Source
        self.mic_combo = QComboBox()
        mics = Recorder.get_available_microphones()
        self.mic_combo.addItem("Default", None)
        for idx, name in mics:
            self.mic_combo.addItem(name, idx)
        # Set current index
        current_mic = self.settings.get("mic_index", None)
        idx = self.mic_combo.findData(current_mic)
        if idx >= 0: self.mic_combo.setCurrentIndex(idx)
        self.form_layout.addRow("Microphone:", self.mic_combo)

        # Resolution
        self.res_combo = QComboBox()
        resolutions = ["1920x1080", "1280x720", "640x480"]
        self.res_combo.addItems(resolutions)
        self.res_combo.setCurrentText(self.settings.get("resolution", "1280x720"))
        self.form_layout.addRow("Resolution:", self.res_combo)

        # Video Format
        self.format_combo = QComboBox()
        formats = ["mp4", "mkv", "mov"]
        self.format_combo.addItems(formats)
        self.format_combo.setCurrentText(self.settings.get("video_format", "mp4"))
        self.form_layout.addRow("Format:", self.format_combo)

        # Aspect Ratio
        self.ar_combo = QComboBox()
        ratios = ["Default", "16:9", "4:3", "1:1"]
        self.ar_combo.addItems(ratios)
        self.ar_combo.setCurrentText(self.settings.get("aspect_ratio", "Default"))
        self.form_layout.addRow("Aspect Ratio:", self.ar_combo)
        
        self.main_layout.addLayout(self.form_layout)

        # Save Button
        self.save_btn = QPushButton("Save")
        self.save_btn.clicked.connect(self.save_and_close)
        self.main_layout.addWidget(self.save_btn)

        # Stylesheet for ComboBox and CheckBox
        from src.utils.resource_path import get_resource_path
        check_icon_path = get_resource_path("assets/icons/check.svg").replace("\\", "/")
        
        self.setStyleSheet(f"""
            QComboBox {{
                padding: 5px;
                min-height: 25px;
                min-width: 150px;
                border: 1px solid #555;
                border-radius: 4px;
                background-color: #333;
                color: white;
            }}
            QComboBox::drop-down {{
                border: none;
            }}
            QComboBox QAbstractItemView {{
                background-color: #333;
                color: white;
                selection-background-color: #555;
            }}
            QCheckBox {{
                color: white;
                spacing: 8px;
            }}
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                border: 1px solid #666;
                border-radius: 4px;
                background-color: #333;
            }}
            QCheckBox::indicator:checked {{
                background-color: #333;
                border: 1px solid #007AFF;
                image: url({check_icon_path});
            }}
        """)

    def browse_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Save Directory")
        if directory:
            self.dir_input.setText(directory)

    def toggle_autostop(self, checked):
        self.autostop_spin.setEnabled(checked)

    def save_and_close(self):
        new_settings = {
            "save_dir": self.dir_input.text(),
            "start_delay": self.delay_spin.value(),
            "auto_stop_enabled": self.autostop_check.isChecked(),
            "auto_stop_duration": self.autostop_spin.value(),
            "resolution": self.res_combo.currentText(),
            "camera_index": self.camera_combo.currentData(),
            "mic_index": self.mic_combo.currentData(),
            "video_format": self.format_combo.currentText(),
            "aspect_ratio": self.ar_combo.currentText()
        }
        SettingsManager.save_settings(new_settings)
        self.accept()

    def get_settings(self):
        return SettingsManager.load_settings()
