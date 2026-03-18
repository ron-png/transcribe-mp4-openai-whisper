#!/usr/bin/env python3
"""
Whisper Transcriber — Entry Point

Cross-platform GUI application for transcribing video files
using OpenAI's Whisper model, optimized for German language.
"""

import sys
import shutil

from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import Qt

from src.main_window import MainWindow
from src.styles import get_stylesheet


def check_ffmpeg() -> bool:
    """Check if ffmpeg is available on the system."""
    return shutil.which("ffmpeg") is not None


def main():
    # High-DPI support
    app = QApplication(sys.argv)
    app.setApplicationName("Whisper Transcriber")
    app.setOrganizationName("WhisperTranscriber")

    # Apply dark theme stylesheet
    app.setStyleSheet(get_stylesheet())

    # Check for ffmpeg
    if not check_ffmpeg():
        QMessageBox.critical(
            None,
            "FFmpeg Not Found",
            "FFmpeg is required but was not found on your system.\n\n"
            "Please install FFmpeg:\n"
            "  • macOS:   brew install ffmpeg\n"
            "  • Ubuntu:  sudo apt install ffmpeg\n"
            "  • Windows: choco install ffmpeg\n\n"
            "After installing, restart the application.",
        )
        sys.exit(1)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
