from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QSlider, QStyle, QInputDialog, QMessageBox
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget
from PyQt6.QtCore import Qt, QUrl, pyqtSignal, QTimer
from PyQt6.QtGui import QFont
from src.utils.rename import safe_rename_video
import os

class PlayerView(QWidget):
    back_signal = pyqtSignal()
    delete_signal = pyqtSignal(str)  # Emits filepath
    rename_signal = pyqtSignal(str, str)  # Emits old_path, new_path

    def __init__(self):
        super().__init__()
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # Top Bar - Standardized
        self.top_widget = QWidget()
        self.top_widget.setStyleSheet("background-color: #1a1a1a;")
        self.top_widget.setMaximumHeight(60)
        self.top_layout = QHBoxLayout(self.top_widget)
        self.top_layout.setContentsMargins(16, 8, 16, 8)
        
        self.back_btn = QPushButton("← Back")
        self.back_btn.setMinimumWidth(80)
        self.back_btn.setMaximumHeight(34)
        self.back_btn.clicked.connect(self.stop_and_back)
        self.top_layout.addWidget(self.back_btn)
        
        self.title_label = QLabel("Video Player")
        self.title_label.setObjectName("secondary")
        font = QFont()
        font.setPointSize(12)
        self.title_label.setFont(font)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.top_layout.addWidget(self.title_label)
        
        # Action buttons
        self.rename_btn = QPushButton("✏ Rename")
        self.rename_btn.setMinimumWidth(90)
        self.rename_btn.setMaximumHeight(34)
        self.rename_btn.clicked.connect(self.rename_video)
        self.top_layout.addWidget(self.rename_btn)
        
        self.delete_btn = QPushButton("🗑 Delete")
        self.delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #2a2a2a;
                color: #FFFFFF;
                border: 2px solid #333333;
                border-radius: 8px;
                padding: 10px 20px;
                font-weight: 500;
                min-height: 20px;
            }
            QPushButton:hover {
                background-color: #242424;
                border-color: #FF3B30;
            }
        """)
        self.delete_btn.setMinimumWidth(90)
        self.delete_btn.setMaximumHeight(34)
        self.delete_btn.clicked.connect(self.delete_video)
        self.top_layout.addWidget(self.delete_btn)
        
        self.main_layout.addWidget(self.top_widget)

        # Video Widget - Maximize space
        self.video_widget = QVideoWidget()
        self.video_widget.setStyleSheet("background-color: #000000;")
        self.video_widget.setContentsMargins(0, 0, 0, 0)
        self.main_layout.addWidget(self.video_widget, 1)  # Stretch factor
        
        # Player Setup
        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.media_player.setAudioOutput(self.audio_output)
        self.media_player.setVideoOutput(self.video_widget)
        
        # Controls - Standardized
        self.controls_widget = QWidget()
        self.controls_widget.setStyleSheet("background-color: #1a1a1a;")
        self.controls_widget.setMaximumHeight(80)
        self.controls_layout = QHBoxLayout(self.controls_widget)
        self.controls_layout.setContentsMargins(16, 16, 16, 16)
        self.controls_layout.setSpacing(12)
        
        self.play_btn = QPushButton()
        self.play_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay))
        self.play_btn.setMinimumSize(44, 44)
        self.play_btn.clicked.connect(self.toggle_playback)
        self.controls_layout.addWidget(self.play_btn)
        
        self.time_label = QLabel("00:00")
        self.time_label.setObjectName("timer")
        self.controls_layout.addWidget(self.time_label)
        
        self.position_slider = QSlider(Qt.Orientation.Horizontal)
        self.position_slider.sliderMoved.connect(self.set_position)
        self.controls_layout.addWidget(self.position_slider)
        
        self.duration_label = QLabel("00:00")
        self.duration_label.setObjectName("timer")
        self.controls_layout.addWidget(self.duration_label)
        
        self.main_layout.addWidget(self.controls_widget)
        
        # Signals
        self.media_player.positionChanged.connect(self.position_changed)
        self.media_player.durationChanged.connect(self.duration_changed)
        self.media_player.playbackStateChanged.connect(self.media_state_changed)

    def load_video(self, path):
        self.current_file_path = path
        self.media_player.setSource(QUrl.fromLocalFile(path))
        filename = path.split("/")[-1]
        self.title_label.setText(filename)
        self.play_btn.setEnabled(True)
        self.media_player.play()

    def toggle_playback(self):
        if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.media_player.pause()
        else:
            self.media_player.play()

    def media_state_changed(self, state):
        if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.play_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPause))
        else:
            self.play_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay))

    def position_changed(self, position):
        self.position_slider.setValue(position)
        self.time_label.setText(self.format_time(position))

    def duration_changed(self, duration):
        self.position_slider.setRange(0, duration)
        self.duration_label.setText(self.format_time(duration))

    def set_position(self, position):
        self.media_player.setPosition(position)

    def format_time(self, ms):
        seconds = ms // 1000
        mins, secs = divmod(seconds, 60)
        return f"{mins:02d}:{secs:02d}"

    def rename_video(self):
        if not hasattr(self, 'current_file_path'):
            return

        old_name = os.path.basename(self.current_file_path)
        new_name, ok = QInputDialog.getText(self, "Rename Video", "New Name:", text=old_name)

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

    def delete_video(self):
        if not hasattr(self, 'current_file_path'):
            return
            
        filename = os.path.basename(self.current_file_path)
        confirm = QMessageBox.question(
            self, "Delete Video", 
            f"Are you sure you want to delete\n{filename}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if confirm == QMessageBox.StandardButton.Yes:
            try:
                self.media_player.stop()
                os.remove(self.current_file_path)
                self.delete_signal.emit(self.current_file_path)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not delete file: {e}")

    def stop_and_back(self):
        self.media_player.stop()
        self.back_signal.emit()
