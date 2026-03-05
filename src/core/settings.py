import json
import os

class SettingsManager:
    DEFAULT_SETTINGS = {
        "save_dir": os.path.expanduser("~/Movies"),
        "start_delay": 0,
        "auto_stop_enabled": False,
        "auto_stop_duration": 0,  # in minutes
        "resolution": "1280x720",
        "camera_index": 0,
        "mic_index": None,  # None means default
        "video_format": "mp4",
        "aspect_ratio": "Default",  # Default, 16:9, 4:3, 1:1
    }
    
    SETTINGS_FILE = os.path.expanduser("~/.webcap_settings.json")

    @classmethod
    def load_settings(cls):
        if os.path.exists(cls.SETTINGS_FILE):
            try:
                with open(cls.SETTINGS_FILE, 'r') as f:
                    return {**cls.DEFAULT_SETTINGS, **json.load(f)}
            except (json.JSONDecodeError, OSError, ValueError):
                return cls.DEFAULT_SETTINGS
        return cls.DEFAULT_SETTINGS

    @classmethod
    def save_settings(cls, settings):
        try:
            with open(cls.SETTINGS_FILE, 'w') as f:
                json.dump(settings, f, indent=4)
        except Exception as e:
            print(f"Error saving settings: {e}")
