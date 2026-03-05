<div align="center">

<img src="assets/logos/webcap.png" alt="WebCap Logo" width="128" height="128">

# WebCap

**A lightweight, native webcam recorder for macOS.**

Record webcam video with audio, manage your recordings, and play them back — all in one clean, dark-mode interface. No bloat, no complex setup, no FFmpeg installation required.

![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)
![PyQt6](https://img.shields.io/badge/PyQt6-6.x-41CD52?logo=qt&logoColor=white)
![Platform](https://img.shields.io/badge/Platform-macOS-000000?logo=apple&logoColor=white)
![FFmpeg](https://img.shields.io/badge/FFmpeg-bundled-007808?logo=ffmpeg&logoColor=white)
![Tests](https://img.shields.io/badge/Tests-pytest-0A9EDC?logo=pytest&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)
![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)

<!--
Add screenshots here:
![WebCap Screenshot](docs/screenshots/home.png)
-->

</div>

---

## Why WebCap?

QuickTime can't do countdown timers or auto-stop. OBS is overkill for a simple webcam recording. Command-line FFmpeg requires memorizing flags every time.

**WebCap fills the gap** — a focused tool that does one thing well: record your webcam with audio, quickly and reliably.

---

## Features

### Recording
- **Multi-camera & multi-mic support** — auto-detects all connected devices
- **Countdown timer** — configurable 0–60 second delay before recording starts
- **Auto-stop** — set a max duration (up to 120 min) and walk away
- **Real-time aspect ratio crop** — Default, 16:9, 4:3, or 1:1, applied live before encoding
- **Multiple formats** — MP4, MKV, or MOV output
- **Multiple resolutions** — 1080p, 720p, or 480p
- **Live recording indicator** — blinking red dot + running timer

### Video Management
- **Built-in library** — browse all recordings sorted by date, with file size and duration
- **Search** — filter recordings by name in real-time
- **Right-click context menu** — Play, Rename, or Delete any recording
- **Smart rename** — preserves the original file extension automatically

### Playback
- **Integrated player** — play/pause, seek bar, duration display
- **Auto-play** — recordings play immediately after capture
- **Manage from player** — rename or delete without leaving the player view

### Technical
- **Bundled FFmpeg** — no need to `brew install ffmpeg`; ships with `imageio-ffmpeg`
- **Separate A/V pipelines** — video (OpenCV) and audio (PortAudio) are recorded independently, then muxed via FFmpeg for reliable sync
- **Background muxing** — UI never freezes during post-processing
- **Persistent settings** — your preferences are saved across sessions
- **Retina-ready** — high-resolution display support on macOS

---

## Installation

### Option A: Download (End Users)

> Coming soon — check [Releases](../../releases) for `.app` bundles.

### Option B: Run from Source (Developers)

```bash
# Clone the repository
git clone https://github.com/cakobob/webcap.git
cd webcap

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run
python main.py
```

> **Note:** macOS will prompt for Camera and Microphone permissions on first launch.

### Build `.app` Bundle

```bash
pip install pyinstaller
chmod +x build.sh
./build.sh
```

The built app will be in `dist/WebCap.app`.

---

## Usage

1. **Launch** WebCap — you'll see the Home screen with your recordings library
2. **Click "+ New Recording"** to open the recorder with a live camera preview
3. **Click "Start Recording"** — if you set a countdown, it'll count down first
4. **Click "Stop Recording"** when done — the video auto-plays in the built-in player
5. **Manage** your recordings from Home: right-click to play, rename, or delete

### Quick Tips

- **Countdown timer:** Set a delay in Settings to give yourself time to get in frame
- **Auto-stop:** Enable in Settings to automatically stop after a set duration
- **Aspect ratio:** Choose 1:1 for square videos (great for social media)
- **Keyboard shortcut:** Press `Cmd+,` in the recorder to open Settings

---

## Configuration

Settings are stored in `~/.webcap_settings.json` and can be changed via the Settings dialog.

| Setting | Options | Default |
|---------|---------|---------|
| Save Directory | Any folder | `~/Movies` |
| Camera | Auto-detected devices | Camera 0 |
| Microphone | Auto-detected devices | System default |
| Resolution | 1920x1080, 1280x720, 640x480 | 1280x720 |
| Video Format | MP4, MKV, MOV | MP4 |
| Aspect Ratio | Default, 16:9, 4:3, 1:1 | Default |
| Start Delay | 0–60 seconds | 0 |
| Auto-stop | 0–120 minutes | Disabled |

---

## Project Structure

```
webcap/
├── main.py                     # Entry point
├── src/
│   ├── core/
│   │   ├── recorder.py         # Recording engine (video + audio + muxing)
│   │   └── settings.py         # Settings persistence (JSON)
│   ├── ui/
│   │   ├── main_window.py      # Navigation controller (QStackedWidget)
│   │   ├── home_view.py        # Video library with search & context menu
│   │   ├── recorder_view.py    # Camera preview & recording controls
│   │   ├── player_view.py      # Video player with rename/delete
│   │   ├── settings_dialog.py  # Settings UI
│   │   └── styles.py           # Design system (colors, fonts, stylesheet)
│   └── utils/
│       ├── rename.py           # Safe file rename utility
│       └── resource_path.py    # PyInstaller-compatible path resolver
├── assets/                     # Icons and logos
├── tests/                      # Test suite (pytest)
├── WebCap.spec                 # PyInstaller build configuration
├── build.sh                    # Build script
└── requirements.txt            # Python dependencies
```

### Architecture

```
┌─────────────┐     signals      ┌──────────────┐
│  HomeView   │◄────────────────►│  MainWindow  │
│  (library)  │                  │  (navigator) │
└─────────────┘                  └──────┬───────┘
                                        │
                    ┌───────────────────┬┘
                    ▼                   ▼
            ┌──────────────┐    ┌─────────────┐
            │ RecorderView │    │ PlayerView  │
            │  (capture)   │    │ (playback)  │
            └──────┬───────┘    └─────────────┘
                   │
                   ▼
            ┌──────────────┐
            │   Recorder   │──── OpenCV (video frames)
            │   (engine)   │──── sounddevice (audio)
            └──────┬───────┘
                   │ background thread
                   ▼
            ┌──────────────┐
            │   FFmpeg     │──── mux video + audio
            │  (bundled)   │
            └──────────────┘
```

---

## Development

### Prerequisites

- Python 3.11+
- macOS 12+

### Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install pytest
```

### Running Tests

```bash
pytest tests/ -v
```

Tests cover settings management, file rename logic, recorder initialization, and resource path resolution — all without requiring camera/microphone hardware.

### Code Conventions

- **Layout naming:** Use `self.main_layout` (not `self.layout` which shadows a Qt method)
- **File rename:** Always use `safe_rename_video()` from `src/utils/rename.py`
- **Static methods:** `Recorder.get_available_cameras()` and `Recorder.get_available_microphones()` are static — don't instantiate `Recorder` just to list devices
- **Thread safety:** Muxing runs in a background thread; communicate back to UI only via Qt signals (`emit()` is thread-safe)
- **Temp files:** Use UUID-based names to avoid conflicts between concurrent instances

---

## Known Limitations

- **macOS only** — the build pipeline, codec (`avc1`), and permission handling are macOS-specific
- **30 FPS fixed** — frame rate is not configurable via the UI
- **Mono audio** — stereo recording is not supported
- **Max 5 cameras** — devices above index 4 are not detected
- **No multi-profile** — settings are global, stored in a single JSON file

---

## Roadmap

- [ ] Cross-platform support (Windows, Linux)
- [ ] Configurable frame rate
- [ ] Stereo audio recording
- [ ] Video thumbnails in the library
- [ ] Hotkey to start/stop recording
- [ ] Export / share integration

---

## Contributing

Contributions are welcome! Here's how to get started:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes and add tests
4. Run the test suite (`pytest tests/ -v`)
5. Commit your changes
6. Push to your fork and open a Pull Request

### Good First Issues

- Add Windows/Linux codec auto-detection in `recorder.py`
- Add video thumbnails to the home view list
- Add configurable FPS in settings
- Implement stereo audio recording

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| UI Framework | [PyQt6](https://www.riverbankcomputing.com/software/pyqt/) |
| Video Capture | [OpenCV](https://opencv.org/) |
| Audio Capture | [sounddevice](https://python-sounddevice.readthedocs.io/) (PortAudio) |
| Audio I/O | [soundfile](https://pysoundfile.readthedocs.io/) (libsndfile) |
| A/V Muxing | [FFmpeg](https://ffmpeg.org/) via [imageio-ffmpeg](https://github.com/imageio/imageio-ffmpeg) |
| Packaging | [PyInstaller](https://pyinstaller.org/) |

---

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

<div align="center">

Built with Python and a love for simplicity.

</div>
