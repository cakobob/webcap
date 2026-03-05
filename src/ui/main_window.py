from PyQt6.QtWidgets import QMainWindow, QStackedWidget, QMessageBox
from src.ui.home_view import HomeView
from src.ui.recorder_view import RecorderView
from src.ui.player_view import PlayerView
from src.ui.styles import get_stylesheet

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("WebCap")
        self.setGeometry(100, 100, 1000, 700)
        self.setStyleSheet(get_stylesheet())

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        # Initialize Views
        self.home_view = HomeView()
        self.recorder_view = RecorderView()
        self.player_view = PlayerView()

        # Add Views to Stack
        self.stack.addWidget(self.home_view)      # Index 0
        self.stack.addWidget(self.recorder_view)  # Index 1
        self.stack.addWidget(self.player_view)    # Index 2

        # Track previous view for smart navigation
        self.previous_view = None

        # Connect Signals
        self.home_view.start_recording_signal.connect(self.go_to_recorder)
        self.home_view.play_video_signal.connect(self.go_to_player_from_home)
        
        self.recorder_view.finished_signal.connect(self.on_recording_finished)
        self.recorder_view.back_signal.connect(self.go_to_home)
        
        self.player_view.back_signal.connect(self.go_back_from_player)
        self.player_view.delete_signal.connect(self.on_video_deleted)
        self.player_view.rename_signal.connect(self.on_video_renamed)

    def go_to_home(self):
        self.recorder_view.stop_session()
        self.home_view.refresh_list()
        self.stack.setCurrentWidget(self.home_view)
        self.previous_view = None

    def go_to_recorder(self):
        self.recorder_view.start_session()
        self.stack.setCurrentWidget(self.recorder_view)

    def go_to_player_from_home(self, filename):
        self.previous_view = 'home'
        self.player_view.load_video(filename)
        self.stack.setCurrentWidget(self.player_view)

    def on_recording_finished(self, filename):
        self.recorder_view.stop_session()
        if not filename:
            QMessageBox.warning(
                self,
                "Recording Failed",
                "Recording failed. The output file could not be created.",
            )
            self.go_to_home()
            return
        self.previous_view = 'recorder'
        self.player_view.load_video(filename)
        self.stack.setCurrentWidget(self.player_view)

    def go_back_from_player(self):
        self.go_to_home()

    def on_video_deleted(self, filepath):
        # Always return to Home after deleting a video
        self.go_to_home()

    def on_video_renamed(self, old_path, new_path):
        # Refresh home view if it was the previous view
        if self.previous_view == 'home':
            self.home_view.refresh_list()

    def closeEvent(self, event):
        self.recorder_view.stop_session()
        event.accept()

