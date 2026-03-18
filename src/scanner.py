"""
Recursive video file scanner.

Walks directories and subdirectories to find video files for transcription.
"""

import os
from pathlib import Path
from typing import List, Set

# Supported video file extensions
VIDEO_EXTENSIONS: Set[str] = {
    ".mp4", ".mkv", ".avi", ".mov", ".webm",
    ".flv", ".wmv", ".m4v", ".mpeg", ".mpg",
    ".3gp", ".ogv", ".ts", ".mts", ".m2ts",
}


def is_video_file(filepath: Path) -> bool:
    """Check if a file is a supported video format."""
    return filepath.suffix.lower() in VIDEO_EXTENSIONS


def has_transcription(filepath: Path) -> bool:
    """Check if a transcription .txt file already exists for the given video."""
    txt_path = filepath.with_suffix(".txt")
    return txt_path.exists()


def scan_directory(
    directory: str,
    skip_transcribed: bool = False,
) -> List[str]:
    """
    Recursively scan a directory for video files.

    Args:
        directory: Path to the directory to scan.
        skip_transcribed: If True, skip files that already have a .txt transcription.

    Returns:
        Sorted list of absolute paths to video files.
    """
    directory_path = Path(directory).resolve()
    if not directory_path.is_dir():
        return []

    video_files: List[str] = []

    for root, _dirs, files in os.walk(directory_path):
        for filename in files:
            filepath = Path(root) / filename
            if is_video_file(filepath):
                if skip_transcribed and has_transcription(filepath):
                    continue
                video_files.append(str(filepath))

    video_files.sort()
    return video_files


def scan_files(
    file_paths: List[str],
    skip_transcribed: bool = False,
) -> List[str]:
    """
    Filter a list of file paths to only include valid video files.

    Args:
        file_paths: List of file paths to check.
        skip_transcribed: If True, skip files that already have a .txt transcription.

    Returns:
        List of absolute paths to valid video files.
    """
    valid_files: List[str] = []

    for file_path in file_paths:
        filepath = Path(file_path).resolve()
        if filepath.is_file() and is_video_file(filepath):
            if skip_transcribed and has_transcription(filepath):
                continue
            valid_files.append(str(filepath))

    return valid_files
