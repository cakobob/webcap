"""
MainWindow — root window managing view navigation via QStackedWidget.
"""

from __future__ import annotations

import os

from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QMainWindow, QMessageBox, QStackedWidget

from src.ui.home_view import HomeView
from src.ui.player_view import PlayerView
from src.ui.recorder_view import RecorderView
from src.ui.styles import get_stylesheet
from src.utils.resource_path import get_resource_path


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("WebCap")
        self.setMinimumSize(900, 650)
        self.resize(1100, 750)
        self.setStyleSheet(get_stylesheet())

        # Window icon — prefer transparent PNG, fall back to original
        self._set_window_icon()

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
        self.previous_view: str | None = None

        # Connect Signals
        self.home_view.start_recording_signal.connect(self.go_to_recorder)
        self.home_view.play_video_signal.connect(self.go_to_player_from_home)

        self.recorder_view.finished_signal.connect(self.on_recording_finished)
        self.recorder_view.back_signal.connect(self.go_to_home)

        self.player_view.back_signal.connect(self.go_back_from_player)
        self.player_view.delete_signal.connect(self.on_video_deleted)
        self.player_view.rename_signal.connect(self.on_video_renamed)

    # ------------------------------------------------------------------
    # Window icon
    # ------------------------------------------------------------------

    def _set_window_icon(self) -> None:
        candidates = [
            "assets/logos/webcap_dark.png",
            "assets/logos/webcap_logo.svg",
            "assets/logos/webcap.png",
        ]
        for rel in candidates:
            path = get_resource_path(rel)
            if os.path.exists(path):
                self.setWindowIcon(QIcon(path))
                break

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------

    def go_to_home(self) -> None:
        self.recorder_view.stop_session()
        self.home_view.refresh_list()
        self.stack.setCurrentWidget(self.home_view)
        self.previous_view = None

    def go_to_recorder(self) -> None:
        self.recorder_view.start_session()
        self.stack.setCurrentWidget(self.recorder_view)

    def go_to_player_from_home(self, filename: str) -> None:
        self.previous_view = 'home'
        self.player_view.load_video(filename)
        self.stack.setCurrentWidget(self.player_view)

    def on_recording_finished(self, filename: str) -> None:
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

    def go_back_from_player(self) -> None:
        self.go_to_home()

    def on_video_deleted(self, filepath: str) -> None:
        self.go_to_home()

    def on_video_renamed(self, old_path: str, new_path: str) -> None:
        if self.previous_view == 'home':
            self.home_view.refresh_list()

    def closeEvent(self, event) -> None:
        self.recorder_view.stop_session()
        event.accept()
