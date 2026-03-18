# Transcribe Video with OpenAI Whisper

Recursively transcribe video files to text using [OpenAI Whisper](https://github.com/openai/whisper). Optimized for **German language** transcription with the highest-accuracy `large` model.

## Features

- 🎬 Supports `.mp4`, `.mkv`, `.avi`, `.mov`, `.webm`, `.flv`, `.wmv`
- 📂 Recursively scans directories and subdirectories
- 🇩🇪 Optimized for German (`--language de` by default)
- ⏭️ Skips already-transcribed files (unless `--overwrite`)
- 💾 Saves `.txt` transcription next to each video file

## Prerequisites

- **Python 3.8+**
- **[ffmpeg](https://ffmpeg.org/)** installed and available on your PATH

```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt update && sudo apt install ffmpeg
```

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
# Transcribe all videos in a directory (German, large model)
python transcribe.py /path/to/videos

# Use a smaller/faster model
python transcribe.py /path/to/videos --model medium

# Different language
python transcribe.py /path/to/videos --language en

# Re-transcribe files that already have a .txt
python transcribe.py /path/to/videos --overwrite
```

### Available Models

| Model  | VRAM   | Speed | Accuracy |
|--------|--------|-------|----------|
| tiny   | ~1 GB  | ★★★★★ | ★        |
| base   | ~1 GB  | ★★★★  | ★★       |
| small  | ~2 GB  | ★★★   | ★★★      |
| medium | ~5 GB  | ★★    | ★★★★     |
| large  | ~10 GB | ★     | ★★★★★    |
| turbo  | ~6 GB  | ★★★★  | ★★★★     |

> **Note:** The `large` model provides the best accuracy for non-English languages like German. The `turbo` model is faster but optimized primarily for English.

## Output

For each video file, a `.txt` file is created in the same directory:

```
videos/
├── lecture_01.mp4
├── lecture_01.txt   ← transcription
├── subfolder/
│   ├── interview.mkv
│   └── interview.txt   ← transcription
```

## License

[MIT](LICENSE)
