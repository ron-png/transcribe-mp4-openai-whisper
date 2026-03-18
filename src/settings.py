"""
Application settings management using QSettings.

Provides persistent storage for user preferences across sessions.
"""

from PyQt6.QtCore import QSettings

# Application identity
APP_NAME = "WhisperTranscriber"
ORG_NAME = "WhisperTranscriber"

# Default values
DEFAULTS = {
    "model": "large-v3",
    "language": "de",
    "beam_size": 5,
    "best_of": 5,
    "temperature": 0.0,
    "skip_transcribed": True,
    "output_same_dir": True,
    "output_directory": "",
    "condition_on_previous_text": True,
    "initial_prompt": "Folgende Wörter werden auf Deutsch transkribiert.",
    "window_width": 1100,
    "window_height": 750,
}

# Available Whisper models (name -> approximate VRAM)
WHISPER_MODELS = {
    "tiny": "~1 GB",
    "base": "~1 GB",
    "small": "~2 GB",
    "medium": "~5 GB",
    "turbo": "~6 GB",
    "large-v3": "~10 GB",
}

# Available languages for transcription
LANGUAGES = {
    "de": "German",
    "en": "English",
    "fr": "French",
    "es": "Spanish",
    "it": "Italian",
    "pt": "Portuguese",
    "nl": "Dutch",
    "pl": "Polish",
    "ru": "Russian",
    "tr": "Turkish",
    "uk": "Ukrainian",
    "ar": "Arabic",
    "ja": "Japanese",
    "zh": "Chinese",
    "ko": "Korean",
    "auto": "Auto-Detect",
}


class AppSettings:
    """Manages persistent application settings using QSettings."""

    def __init__(self):
        self._settings = QSettings(ORG_NAME, APP_NAME)

    def get(self, key: str):
        """Get a setting value, falling back to the default."""
        default = DEFAULTS.get(key)
        value = self._settings.value(key, default)
        # QSettings stores everything as strings; convert types
        if isinstance(default, bool):
            if isinstance(value, str):
                return value.lower() == "true"
            return bool(value)
        if isinstance(default, int):
            return int(value)
        if isinstance(default, float):
            return float(value)
        return value

    def set(self, key: str, value):
        """Set a setting value."""
        self._settings.setValue(key, value)

    def sync(self):
        """Force sync settings to disk."""
        self._settings.sync()
