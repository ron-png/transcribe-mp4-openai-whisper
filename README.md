# Whisper Transcriber

A cross-platform desktop application for transcribing video files using [OpenAI Whisper](https://github.com/openai/whisper), optimized for **German language** transcription with highest quality settings.

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![Platform](https://img.shields.io/badge/Platform-macOS%20%7C%20Linux%20%7C%20Windows-lightgrey)
![License](https://img.shields.io/badge/License-MIT-green)

## Features

- 🎬 **Video Transcription** — Transcribe `.mp4`, `.mkv`, `.avi`, `.mov`, `.webm`, and more
- 🇩🇪 **German Language Focus** — Defaults to `large-v3` model with German language for the lowest word error rate
- 📁 **Batch Processing** — Queue entire directories including all subdirectories
- 📝 **Timestamped Output** — Generates `.txt` files with both full text and timestamped segments
- 🖥️ **Cross-Platform** — Works on macOS, Linux, and Windows
- 🎨 **Premium Dark UI** — Modern, visually appealing interface powered by PyQt6
- ⚙️ **Configurable** — Select model size, language, beam size, temperature, and output options
- 🧠 **German Prompt Hint** — Uses `initial_prompt` to improve German orthography (ä, ö, ü, ß)
- ⚡ **GPU Acceleration** — Automatically detects CUDA, Apple MPS, or CPU
- 📂 **Drag & Drop** — Drop video files or folders directly into the app
- 🔄 **Skip Transcribed** — Optionally skip files that already have transcriptions

## Requirements

- **Python 3.10+**
- **FFmpeg** — Required by Whisper for audio extraction

### Install FFmpeg

```bash
# macOS
brew install ffmpeg

# Ubuntu / Debian
sudo apt update && sudo apt install ffmpeg

# Windows (Chocolatey)
choco install ffmpeg

# Windows (Scoop)
scoop install ffmpeg
```

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-username/transcribe-mp4-openai-whisper.git
   cd transcribe-mp4-openai-whisper
   ```

2. **Create a virtual environment (recommended):**
   ```bash
   python -m venv venv
   source venv/bin/activate  # macOS/Linux
   # or: venv\Scripts\activate  # Windows
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application:**
   ```bash
   python src/main.py
   ```

## Usage

1. **Add files** — Click "Add Files" to select individual videos, or "Add Folder" to scan a directory including all subdirectories
2. **Drag & drop** — You can also drag video files or folders directly onto the window
3. **Configure** — Click "Settings" to adjust the model, language, quality, and output settings
4. **Start** — Click "Start Transcription" and the app will process each file in the queue
5. **Output** — Transcription `.txt` files are saved next to the original video (or in a custom output directory)

## Whisper Models

| Model | VRAM | Quality | Speed |
|-------|------|---------|-------|
| `tiny` | ~1 GB | Low | Fastest |
| `base` | ~1 GB | Fair | Fast |
| `small` | ~2 GB | Good | Moderate |
| `medium` | ~5 GB | Great | Slow |
| `turbo` | ~6 GB | **Very Good** | Fast |
| `large-v3` | ~10 GB | **Best** | Slowest |

The default model is **`large-v3`** which provides the highest transcription quality for German. The `turbo` model (aka `large-v3-turbo`) is 8x faster with minimal accuracy loss — ideal for large batches where speed matters more.

## Quality Settings

| Setting | Default | Description |
|---------|---------|-------------|
| Beam Size | 5 | Higher = better quality, slower |
| Best Of | 5 | Number of candidates to evaluate |
| Temperature | 0.0 | Greedy decoding for max accuracy |
| Initial Prompt | German hint | Improves ä, ö, ü, ß handling |
| Condition on Previous | ✓ | Uses prior context for coherence |

## Output Format

Each transcription `.txt` file contains:
1. **Full text** — The complete transcription as a single block
2. **Timestamped segments** — Each segment with `[HH:MM:SS.mmm --> HH:MM:SS.mmm]` timestamps

## Dependencies

| Package | Version |
|---------|---------|
| `openai-whisper` | 20250625 |
| `PyQt6` | 6.10.2 |
| `torch` | 2.10.0 |

## License

MIT License — see [LICENSE](LICENSE) for details.
