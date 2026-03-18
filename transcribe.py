#!/usr/bin/env python3
"""
Transcribe video files using OpenAI Whisper.

Recursively finds video files in a directory, transcribes the audio
using the Whisper model, and saves the transcription as a .txt file
next to each video. Optimized for German language transcription.

Usage:
    python transcribe.py /path/to/videos
    python transcribe.py /path/to/videos --model medium
"""

import argparse
import sys
import time
from pathlib import Path

import whisper

VIDEO_EXTENSIONS = {".mp4", ".mkv", ".avi", ".mov", ".webm", ".flv", ".wmv"}


def find_video_files(directory: Path) -> list[Path]:
    """Recursively find all video files in the given directory."""
    videos = []
    for path in sorted(directory.rglob("*")):
        if path.is_file() and path.suffix.lower() in VIDEO_EXTENSIONS:
            videos.append(path)
    return videos


def format_duration(seconds: float) -> str:
    """Format seconds into a human-readable duration string."""
    minutes, secs = divmod(int(seconds), 60)
    hours, minutes = divmod(minutes, 60)
    if hours > 0:
        return f"{hours}h {minutes}m {secs}s"
    elif minutes > 0:
        return f"{minutes}m {secs}s"
    return f"{secs}s"


def transcribe_video(model, video_path: Path, language: str) -> str:
    """Transcribe a single video file and return the text."""
    result = model.transcribe(
        str(video_path),
        language=language,
        task="transcribe",
        verbose=False,
    )
    return result["text"].strip()


def main():
    parser = argparse.ArgumentParser(
        description="Transcribe video files using OpenAI Whisper (optimized for German)."
    )
    parser.add_argument(
        "directory",
        nargs="?",
        default=".",
        help="Directory containing video files (default: current directory)",
    )
    parser.add_argument(
        "--model",
        default="large",
        choices=["tiny", "base", "small", "medium", "large", "turbo"],
        help="Whisper model to use (default: large for best German accuracy)",
    )
    parser.add_argument(
        "--language",
        default="de",
        help="Language code for transcription (default: de for German)",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing transcription files",
    )
    args = parser.parse_args()

    directory = Path(args.directory).resolve()
    if not directory.is_dir():
        print(f"Error: '{directory}' is not a valid directory.", file=sys.stderr)
        sys.exit(1)

    # Find all video files
    print(f"Scanning for video files in: {directory}")
    videos = find_video_files(directory)

    if not videos:
        print("No video files found.")
        sys.exit(0)

    # Filter out already-transcribed files
    if not args.overwrite:
        to_process = []
        for v in videos:
            txt_path = v.with_suffix(".txt")
            if txt_path.exists():
                print(f"  Skipping (already transcribed): {v.name}")
            else:
                to_process.append(v)
    else:
        to_process = videos

    if not to_process:
        print("All videos already have transcriptions. Use --overwrite to redo them.")
        sys.exit(0)

    print(f"\nFound {len(to_process)} video(s) to transcribe "
          f"(skipped {len(videos) - len(to_process)} already done).\n")

    # Load the Whisper model
    print(f"Loading Whisper '{args.model}' model...")
    load_start = time.time()
    model = whisper.load_model(args.model)
    print(f"Model loaded in {format_duration(time.time() - load_start)}.\n")

    # Transcribe each video
    for i, video_path in enumerate(to_process, 1):
        print(f"[{i}/{len(to_process)}] Transcribing: {video_path.relative_to(directory)}")
        start_time = time.time()

        try:
            text = transcribe_video(model, video_path, args.language)
        except Exception as e:
            print(f"  ERROR: Failed to transcribe — {e}\n")
            continue

        # Save transcription
        output_path = video_path.with_suffix(".txt")
        output_path.write_text(text, encoding="utf-8")

        elapsed = time.time() - start_time
        print(f"  Done in {format_duration(elapsed)} → {output_path.name}")
        print(f"  Preview: {text[:120]}{'...' if len(text) > 120 else ''}\n")

    print("All done!")


if __name__ == "__main__":
    main()
