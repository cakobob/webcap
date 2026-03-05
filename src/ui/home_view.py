from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QListWidget, QPushButton,
                             QHBoxLayout, QLabel, QListWidgetItem, QMenu,
                             QInputDialog, QMessageBox, QLineEdit)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QIcon
from src.core.settings import SettingsManager
from src.ui.settings_dialog import SettingsDialog
from src.core.recorder import Recorder
from src.utils.rename import safe_rename_video
import os
import time
import cv2

class HomeView(QWidget):
    start_recording_signal = pyqtSignal()
    play_video_signal = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(24, 24, 24, 24)
        self.main_layout.setSpacing(16)
        
        # Header
        self.header_layout = QHBoxLayout()
        self.title = QLabel("WebCap")
        self.title.setObjectName("title")
        self.header_layout.addWidget(self.title)
        self.header_layout.addStretch()
        
        self.settings_btn = QPushButton("⚙")
        self.settings_btn.setMinimumWidth(44)
        self.settings_btn.setMinimumHeight(44)
        self.settings_btn.clicked.connect(self.open_settings)
        self.header_layout.addWidget(self.settings_btn)

        self.new_record_btn = QPushButton("+ New Recording")
        self.new_record_btn.setObjectName("primary")
        self.new_record_btn.setMinimumHeight(40)
        self.new_record_btn.clicked.connect(self.on_new_recording_clicked)
        self.header_layout.addWidget(self.new_record_btn)
        
        self.main_layout.addLayout(self.header_layout)
        
        # Logo (if exists)
        from src.utils.resource_path import get_resource_path
        logo_path = get_resource_path("assets/logos/webcap.png")
        if os.path.exists(logo_path):
            from PyQt6.QtGui import QPixmap, QPainter, QPainterPath
            from PyQt6.QtCore import QRectF
            self.logo_label = QLabel()
            self.logo_label.setStyleSheet("border-radius: 12px; background-color: transparent;")
            pixmap = QPixmap(logo_path)
            scaled_pixmap = pixmap.scaled(80, 80, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            
            # Create rounded pixmap
            rounded_pixmap = QPixmap(scaled_pixmap.size())
            rounded_pixmap.fill(Qt.GlobalColor.transparent)
            
            painter = QPainter(rounded_pixmap)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            path = QPainterPath()
            path.addRoundedRect(QRectF(rounded_pixmap.rect()), 12, 12)
            painter.setClipPath(path)
            painter.drawPixmap(0, 0, scaled_pixmap)
            painter.end()
            
            self.logo_label.setPixmap(rounded_pixmap)
            self.logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.main_layout.addWidget(self.logo_label)
        
        # Search Box
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search recordings...")
        self.search_box.setStyleSheet("""
            QLineEdit {
                background-color: #2a2a2a;
                color: #FFFFFF;
                border: 1px solid #333333;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #007AFF;
            }
        """)
        self.search_box.textChanged.connect(self.filter_list)
        self.main_layout.addWidget(self.search_box)

        # Video List Label
        self.list_label = QLabel("Recent Recordings")
        self.list_label.setObjectName("secondary")
        font = QFont()
        font.setPointSize(12)
        font.setWeight(QFont.Weight.Medium)
        self.list_label.setFont(font)
        self.main_layout.addWidget(self.list_label)
        
        # Video List
        self.video_list = QListWidget()
        self.video_list.itemDoubleClicked.connect(self.on_item_double_clicked)
        self.video_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.video_list.customContextMenuRequested.connect(self.show_context_menu)
        self.main_layout.addWidget(self.video_list)
        
        # Empty State
        self.empty_label = QLabel("No recordings yet.\nClick 'New Recording' to get started.")
        self.empty_label.setObjectName("secondary")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_font = QFont()
        empty_font.setPointSize(14)
        self.empty_label.setFont(empty_font)
        self.empty_label.hide()
        self.main_layout.addWidget(self.empty_label)
        
        self.all_files = []
        self._duration_cache = {}  # {filepath: duration_str}
        self.refresh_list()

    def on_new_recording_clicked(self):
        # Request permissions here
        self.request_permissions()
        self.start_recording_signal.emit()

    def request_permissions(self):
        # Camera permission check (by trying to open it)
        settings = SettingsManager.load_settings()
        cam_idx = settings.get("camera_index", 0)
        cap = cv2.VideoCapture(cam_idx)
        if cap.isOpened():
            cap.release()
        
        # Microphone permission check (using sounddevice)
        try:
            import sounddevice as sd
            with sd.InputStream(samplerate=44100, channels=1):
                pass
        except Exception as e:
            print(f"Microphone permission check failed: {e}")

    def open_settings(self):
        dialog = SettingsDialog(self)
        dialog.exec()
        self.refresh_list() # Refresh list after settings closed

    def refresh_list(self):
        # Clear existing items
        self.video_list.clear()
        
        settings = SettingsManager.load_settings()
        save_dir = settings.get("save_dir", os.path.expanduser("~/Movies"))
        
        if not os.path.exists(save_dir):
            self.show_empty_state()
            return

        self.all_files = sorted(
            [f for f in os.listdir(save_dir) if f.lower().endswith(('.mp4', '.mkv', '.mov'))],
            key=lambda x: os.path.getmtime(os.path.join(save_dir, x)),
            reverse=True
        )
        
        if not self.all_files:
            self.show_empty_state()
            return
        
        self.empty_label.hide()
        self.list_label.show()
        self.video_list.show()
        self.search_box.show()
        
        self.populate_list(self.all_files)

    def populate_list(self, files):
        self.video_list.clear()
        settings = SettingsManager.load_settings()
        save_dir = settings.get("save_dir", os.path.expanduser("~/Movies"))
        
        for f in files:
            path = os.path.join(save_dir, f)
            size_mb = os.path.getsize(path) / (1024 * 1024)
            date_str = time.strftime('%b %d, %Y  %H:%M', time.localtime(os.path.getmtime(path)))
            
            # Get duration (cached to avoid re-opening the same file)
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
                            duration_sec = int(frame_count / fps)
                            mins, secs = divmod(duration_sec, 60)
                            duration_str = f" • {mins:02d}:{secs:02d}"
                        cap.release()
                except Exception:
                    pass
                self._duration_cache[path] = duration_str

            item_text = f"{f}\n{size_mb:.1f} MB{duration_str}  •  {date_str}"
            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, path)
            self.video_list.addItem(item)

    def filter_list(self, text):
        filtered_files = [f for f in self.all_files if text.lower() in f.lower()]
        self.populate_list(filtered_files)

    def show_empty_state(self):
        self.video_list.hide()
        self.list_label.hide()
        self.search_box.hide()
        self.empty_label.show()

    def on_item_double_clicked(self, item):
        path = item.data(Qt.ItemDataRole.UserRole)
        self.play_video_signal.emit(path)

    def show_context_menu(self, pos):
        item = self.video_list.itemAt(pos)
        if not item:
            return
            
        menu = QMenu()
        play_action = menu.addAction("▶ Play")
        rename_action = menu.addAction("✏ Rename")
        delete_action = menu.addAction("🗑 Delete")
        
        action = menu.exec(self.video_list.mapToGlobal(pos))
        
        path = item.data(Qt.ItemDataRole.UserRole)
        
        if action == play_action:
            self.play_video_signal.emit(path)
        elif action == rename_action:
            self.rename_video(item, path)
        elif action == delete_action:
            self.delete_video(item, path)

    def rename_video(self, item, path):
        old_name = os.path.basename(path)
        new_name, ok = QInputDialog.getText(self, "Rename Video", "New Name:", text=old_name)

        if ok and new_name:
            try:
                safe_rename_video(path, new_name)
                self.refresh_list()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not rename file: {e}")

    def delete_video(self, item, path):
        confirm = QMessageBox.question(
            self, "Delete Video", 
            f"Are you sure you want to delete\n{os.path.basename(path)}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if confirm == QMessageBox.StandardButton.Yes:
            try:
                os.remove(path)
                self.refresh_list()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not delete file: {e}")
