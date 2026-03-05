from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QMessageBox
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QImage, QPixmap, QFont
from src.core.recorder import Recorder
from src.core.settings import SettingsManager
import cv2
import os
import time

class RecorderView(QWidget):
    finished_signal = pyqtSignal(str)
    back_signal = pyqtSignal() # Renamed from cancel_signal for clarity, but maps to same action

    def __init__(self):
        super().__init__()
        self.recorder = Recorder()
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # Top Bar
        self.top_widget = QWidget()
        self.top_widget.setStyleSheet("background-color: #1a1a1a;")
        self.top_widget.setMaximumHeight(60)
        self.top_layout = QHBoxLayout(self.top_widget)
        self.top_layout.setContentsMargins(16, 8, 16, 8)
        
        self.back_btn = QPushButton("← Back")
        self.back_btn.setMinimumWidth(80)
        self.back_btn.setMaximumHeight(34)
        self.back_btn.clicked.connect(self.on_back_clicked)
        self.top_layout.addWidget(self.back_btn)
        
        self.top_layout.addStretch()
        self.main_layout.addWidget(self.top_widget)

        # Video Preview (Full screen)
        self.video_label = QLabel("Initializing Camera...")
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_label.setStyleSheet("background-color: #000000; color: #A0A0A0;")
        self.main_layout.addWidget(self.video_label, 1)  # Stretch factor 1

        # Bottom Bar (Controls)
        self.controls_widget = QWidget()
        self.controls_widget.setStyleSheet("background-color: #1a1a1a;")
        self.controls_widget.setMaximumHeight(80) # Increased height for better touch targets
        self.controls_layout = QHBoxLayout(self.controls_widget)
        self.controls_layout.setContentsMargins(16, 16, 16, 16)
        self.controls_layout.setSpacing(12)
        
        # Cancel Button (Hidden by default)
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setMinimumWidth(100)
        self.cancel_btn.clicked.connect(self.cancel_countdown)
        self.cancel_btn.hide() 
        self.controls_layout.addWidget(self.cancel_btn)
        
        self.controls_layout.addStretch()
        
        # Recording Status Indicator
        self.status_label = QLabel("●")
        self.status_label.setStyleSheet("color: #34C759; font-size: 24px;")
        self.status_label.hide()
        self.controls_layout.addWidget(self.status_label)
        
        self.timer_label = QLabel("00:00")
        self.timer_label.setObjectName("timer")
        self.controls_layout.addWidget(self.timer_label)
        
        self.controls_layout.addStretch()
        
        self.start_btn = QPushButton("Start Recording")
        self.start_btn.setStyleSheet("""
            QPushButton {
                background-color: #2a2a2a;
                color: #FFFFFF;
                border: 2px solid #333333;
                border-radius: 8px;
                padding: 10px 20px;
                font-weight: 600;
                min-height: 20px;
            }
            QPushButton:hover {
                background-color: #242424;
                border-color: #007AFF;
            }
        """)
        self.start_btn.setMinimumWidth(150)
        self.start_btn.setMinimumHeight(44)
        self.start_btn.clicked.connect(self.toggle_recording)
        self.controls_layout.addWidget(self.start_btn)
        
        # Spacer to balance layout if needed, or just keep it centered
        # self.controls_layout.addSpacing(100) 
        
        self.main_layout.addWidget(self.controls_widget)

        # Timer for video loop
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        
        self.countdown_val = 0
        self.blink_timer = None
        self.countdown_timer = None
        self.recording_timer = None

    def start_session(self):
        """Called when entering this view"""
        # Reload settings to ensure we have the latest
        settings = SettingsManager.load_settings()
        
        cam_idx = settings.get("camera_index", 0)
        resolution = settings.get("resolution", "1280x720")
        aspect_ratio = settings.get("aspect_ratio", "Default")

        self.video_label.setText("Initializing Camera...")
        if self.recorder.start_camera(camera_index=cam_idx, resolution=resolution, aspect_ratio=aspect_ratio):
            self.timer.start(30)
        else:
            self.video_label.setText("Camera Error")
        
        # Reset state
        self.cancel_btn.hide()
        self.start_btn.setEnabled(True)
        self.start_btn.setText("Start Recording")
        self.start_btn.setStyleSheet("""
            QPushButton {
                background-color: #2a2a2a;
                color: #FFFFFF;
                border: 2px solid #333333;
                border-radius: 8px;
                padding: 10px 20px;
                font-weight: 600;
                min-height: 20px;
            }
            QPushButton:hover {
                background-color: #242424;
                border-color: #007AFF;
            }
        """)
        self.back_btn.setEnabled(True)

    def stop_session(self):
        """Called when leaving this view"""
        self.timer.stop()
        if self.blink_timer:
            self.blink_timer.stop()
        if self.countdown_timer:
            self.countdown_timer.stop()
        if self.recording_timer:
            self.recording_timer.stop()
            self.recording_timer = None
        self.recorder.stop_camera()
        self.video_label.clear()

    def update_frame(self):
        frame = self.recorder.get_frame()
        if frame is not None:
            rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_image.shape
            bytes_per_line = ch * w
            convert_to_Qt_format = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
            
            # Scale to fit while maintaining aspect ratio
            label_size = self.video_label.size()
            p = convert_to_Qt_format.scaled(
                label_size.width(), 
                label_size.height(), 
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.video_label.setPixmap(QPixmap.fromImage(p))

    def toggle_recording(self):
        if self.recorder.is_recording:
            self.stop_recording_ui()
        else:
            self.initiate_recording()

    def initiate_recording(self):
        settings = SettingsManager.load_settings()
        delay = settings.get("start_delay", 0)
        
        if delay > 0:
            # Stop video feed during countdown
            self.timer.stop()
            
            self.start_btn.setEnabled(False)
            self.back_btn.setEnabled(False)
            self.cancel_btn.show()
            self.cancel_btn.setEnabled(True)
            
            self.countdown_val = delay
            
            # Full screen countdown
            self.video_label.clear()
            self.video_label.setText(str(self.countdown_val))
            font = QFont()
            font.setPointSize(120)
            font.setWeight(QFont.Weight.Bold)
            self.video_label.setFont(font)
            self.video_label.setStyleSheet("background-color: #000000; color: #BCBCBC; font-size: 100px")
            
            self.countdown_timer = QTimer()
            self.countdown_timer.timeout.connect(self.update_countdown)
            self.countdown_timer.start(1000)
        else:
            self.start_recording_now()

    def update_countdown(self):
        self.countdown_val -= 1
        if self.countdown_val > 0:
            self.video_label.setText(str(self.countdown_val))
        else:
            self.countdown_timer.stop()
            self.start_recording_now()

    def cancel_countdown(self):
        if self.countdown_timer:
            self.countdown_timer.stop()
        
        self.cancel_btn.hide()
        self.start_btn.setEnabled(True)
        self.back_btn.setEnabled(True)
        
        # Reset video label
        self.video_label.clear()
        self.video_label.setText("")
        self.video_label.setFont(QFont())
        self.video_label.setStyleSheet("background-color: #000000; color: #A0A0A0;")
        
        # Restart video feed
        self.timer.start(30)

    def start_recording_now(self):
        # Reset UI from countdown state if needed
        self.cancel_btn.hide()
        self.video_label.clear()
        self.video_label.setText("")
        self.video_label.setFont(QFont())
        self.video_label.setStyleSheet("background-color: #000000; color: #A0A0A0;")
        
        # Ensure video feed is running
        if not self.timer.isActive():
            self.timer.start(30)

        settings = SettingsManager.load_settings()
        save_dir = settings.get("save_dir", os.path.expanduser("~/Movies"))
        video_format = settings.get("video_format", "mp4")
        
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
            
        timestamp = time.strftime("%Y-%m-%d_%H-%M-%S")
        filename = os.path.join(save_dir, f"WebCap_{timestamp}.{video_format}")
        
        mic_index = settings.get("mic_index", None)
        self.recorder.start_recording(filename, mic_index=mic_index)
        self.start_btn.setEnabled(True)
        self.start_btn.setText("Stop Recording")
        self.start_btn.setStyleSheet("""
            QPushButton {
                background-color: #2a2a2a;
                color: #FFFFFF;
                border: 2px solid #FF3B30;
                border-radius: 8px;
                padding: 10px 20px;
                font-weight: 600;
                min-height: 20px;
            }
            QPushButton:hover {
                background-color: #242424;
                border-color: #FF3B30;
            }
        """)
        self.back_btn.setEnabled(False) # Disable back during recording
        
        # Show blinking red dot
        self.status_label.show()
        self.blink_timer = QTimer()
        self.blink_timer.timeout.connect(self.blink_status)
        self.blink_timer.start(500)
        
        self.recording_start_time = time.time()
        self.recording_timer = QTimer()
        self.recording_timer.timeout.connect(self.update_recording_timer)
        self.recording_timer.start(1000)
        
        if settings.get("auto_stop_enabled", False):
            duration_min = settings.get("auto_stop_duration", 0)
            if duration_min > 0:
                QTimer.singleShot(duration_min * 60 * 1000, self.stop_recording_ui)

    def blink_status(self):
        if self.status_label.isVisible():
            self.status_label.setStyleSheet("color: #FF3B30; font-size: 24px;")
            QTimer.singleShot(250, lambda: self.status_label.setStyleSheet("color: transparent; font-size: 24px;"))

    def update_recording_timer(self):
        elapsed = int(time.time() - self.recording_start_time)
        mins, secs = divmod(elapsed, 60)
        self.timer_label.setText(f"{mins:02d}:{secs:02d}")

    def stop_recording_ui(self):
        if self.recorder.is_recording:
            # Disable buttons while processing
            self.start_btn.setEnabled(False)
            self.start_btn.setText("Processing...")
            
            # Define callback for when muxing is done.
            # Runs from a background thread — emit() is thread-safe in PyQt6.
            def on_mux_complete(filename):
                if filename and os.path.exists(filename):
                    self.finished_signal.emit(filename)
                else:
                    # Signal failure with an empty string so MainWindow can handle it.
                    print("Recording failed: output file not created")
                    self.finished_signal.emit("")
            
            try:
                self.recorder.stop_recording(on_finished=on_mux_complete)
            except Exception as e:
                self.start_btn.setEnabled(True)
                self.start_btn.setText("Start Recording")
                QMessageBox.critical(self, "Error", f"Failed to stop recording: {str(e)}")
                return
            
            self.start_btn.setStyleSheet("""
                QPushButton {
                    background-color: #2a2a2a;
                    color: #FFFFFF;
                    border: 2px solid #333333;
                    border-radius: 8px;
                    padding: 10px 20px;
                    font-weight: 600;
                    min-height: 20px;
                }
                QPushButton:hover {
                    background-color: #242424;
                    border-color: #007AFF;
                }
            """)
            self.back_btn.setEnabled(True)
            
            if self.blink_timer:
                self.blink_timer.stop()
            self.status_label.hide()
            
            if self.recording_timer:
                self.recording_timer.stop()
                self.recording_timer = None
            self.timer_label.setText("00:00")
            
            # Note: finished_signal is now emitted in the callback

    def on_back_clicked(self):
        self.stop_session()
        self.back_signal.emit()

