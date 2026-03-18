"""
Whisper transcription engine running in a background thread.

Handles audio extraction via ffmpeg, chunk-based transcription for
bounded memory usage, and progress reporting via Qt signals.
"""

import json
import os
import subprocess
import tempfile
import time
import traceback
from pathlib import Path

import torch
from PyQt6.QtCore import QThread, pyqtSignal


# Chunk size in seconds for splitting long audio files.
# Each chunk is transcribed independently to cap peak memory.
CHUNK_DURATION_SECONDS = 600  # 10 minutes


class TranscriberWorker(QThread):
    """
    Background worker that transcribes video files using OpenAI Whisper.

    Pipeline per file:
      1. Extract audio to a temp 16 kHz mono WAV with ffmpeg
      2. Split into 10-minute chunks (via ffmpeg -ss/-t)
      3. Transcribe each chunk, emitting live segments
      4. Write final .txt output
      5. Clean up temp files

    Signals:
        progress(str, int): (status_message, percentage 0-100)
        file_started(int, str): (queue_index, file_path)
        file_completed(int, str, str): (queue_index, file_path, output_path)
        file_error(int, str, str): (queue_index, file_path, error_message)
        file_progress(int, int): (queue_index, percentage 0-100)
        all_completed(): Emitted when the entire queue is done.
        log_message(str): Log message for the UI log panel.
        model_loading(str): Emitted when model starts loading.
        model_loaded(str): Emitted when model finishes loading.
        segment_transcribed(int, str, float, float):
            (queue_index, text, start_seconds, end_seconds)
    """

    progress = pyqtSignal(str, int)
    file_started = pyqtSignal(int, str)
    file_completed = pyqtSignal(int, str, str)
    file_error = pyqtSignal(int, str, str)
    file_progress = pyqtSignal(int, int)
    all_completed = pyqtSignal()
    log_message = pyqtSignal(str)
    model_loading = pyqtSignal(str)
    model_loaded = pyqtSignal(str)
    segment_transcribed = pyqtSignal(int, str, float, float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._file_queue: list = []
        self._model_name: str = "large-v3"
        self._language: str = "de"
        self._beam_size: int = 5
        self._best_of: int = 5
        self._temperature: float = 0.0
        self._condition_on_previous_text: bool = True
        self._initial_prompt: str = ""
        self._output_same_dir: bool = True
        self._output_directory: str = ""
        self._cancelled: bool = False
        self._model = None

    def configure(
        self,
        file_queue: list,
        model_name: str = "large-v3",
        language: str = "de",
        beam_size: int = 5,
        best_of: int = 5,
        temperature: float = 0.0,
        condition_on_previous_text: bool = True,
        initial_prompt: str = "",
        output_same_dir: bool = True,
        output_directory: str = "",
    ):
        """Configure the worker before starting."""
        self._file_queue = list(file_queue)
        self._model_name = model_name
        self._language = language
        self._beam_size = beam_size
        self._best_of = best_of
        self._temperature = temperature
        self._condition_on_previous_text = condition_on_previous_text
        self._initial_prompt = initial_prompt
        self._output_same_dir = output_same_dir
        self._output_directory = output_directory
        self._cancelled = False

    def cancel(self):
        """Request cancellation of the current transcription."""
        self._cancelled = True

    # ─── Helper: output path ──────────────────────────────────

    def _get_output_path(self, video_path: str) -> str:
        """Determine the output .txt file path for a given video."""
        video = Path(video_path)
        if self._output_same_dir:
            return str(video.with_suffix(".txt"))
        else:
            output_dir = Path(self._output_directory)
            output_dir.mkdir(parents=True, exist_ok=True)
            return str(output_dir / (video.stem + ".txt"))

    # ─── Helper: device detection ─────────────────────────────

    def _detect_device(self) -> str:
        """Detect and log the best available compute device."""
        if torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name(0)
            vram = torch.cuda.get_device_properties(0).total_mem / (1024**3)
            self.log_message.emit(f"GPU detected: {gpu_name} ({vram:.1f} GB)")
            return "cuda"
        elif torch.backends.mps.is_available():
            self.log_message.emit("Apple Silicon GPU detected (MPS backend)")
            return "mps"
        else:
            self.log_message.emit(
                "No GPU detected — using CPU (transcription will be slower)"
            )
            return "cpu"

    # ─── Helper: ffprobe duration ─────────────────────────────

    @staticmethod
    def _get_duration(file_path: str) -> float:
        """Get the duration of an audio/video file in seconds using ffprobe."""
        try:
            result = subprocess.run(
                [
                    "ffprobe",
                    "-v", "quiet",
                    "-print_format", "json",
                    "-show_format",
                    file_path,
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )
            info = json.loads(result.stdout)
            return float(info["format"]["duration"])
        except Exception:
            return 0.0

    # ─── Helper: extract audio ────────────────────────────────

    def _extract_audio(self, video_path: str, output_wav: str) -> bool:
        """
        Extract audio from a video file to a 16 kHz mono WAV using ffmpeg.

        This runs as a subprocess so the video data never enters Python memory.
        """
        try:
            subprocess.run(
                [
                    "ffmpeg",
                    "-y",              # overwrite
                    "-i", video_path,
                    "-vn",             # no video
                    "-ar", "16000",    # 16 kHz (Whisper native)
                    "-ac", "1",        # mono
                    "-f", "wav",
                    output_wav,
                ],
                capture_output=True,
                text=True,
                timeout=3600,  # 1-hour timeout for very large files
            )
            return Path(output_wav).exists() and Path(output_wav).stat().st_size > 0
        except Exception as e:
            self.log_message.emit(f"  ✗ Audio extraction failed: {e}")
            return False

    # ─── Helper: extract audio chunk ──────────────────────────

    @staticmethod
    def _extract_audio_chunk(
        wav_path: str, output_path: str, start_sec: float, duration_sec: float
    ) -> bool:
        """Extract a time-slice from a WAV file using ffmpeg."""
        try:
            subprocess.run(
                [
                    "ffmpeg",
                    "-y",
                    "-ss", str(start_sec),
                    "-t", str(duration_sec),
                    "-i", wav_path,
                    "-ar", "16000",
                    "-ac", "1",
                    "-f", "wav",
                    output_path,
                ],
                capture_output=True,
                text=True,
                timeout=120,
            )
            return Path(output_path).exists() and Path(output_path).stat().st_size > 0
        except Exception:
            return False

    # ─── Main run loop ────────────────────────────────────────

    def run(self):
        """Main transcription loop — runs in background thread."""
        try:
            import whisper
        except ImportError:
            self.log_message.emit(
                "ERROR: openai-whisper is not installed. "
                "Run: pip install openai-whisper"
            )
            self.all_completed.emit()
            return

        # Detect compute device
        device = self._detect_device()

        # Load model
        self.model_loading.emit(self._model_name)
        self.log_message.emit(
            f"Loading Whisper model '{self._model_name}' on {device}..."
        )
        self.progress.emit(f"Loading model '{self._model_name}'...", 0)
        try:
            start_load = time.time()
            self._model = whisper.load_model(self._model_name, device=device)
            load_time = time.time() - start_load
            self.log_message.emit(
                f"Model '{self._model_name}' loaded in {load_time:.1f}s"
            )
            self.model_loaded.emit(self._model_name)
        except Exception as e:
            self.log_message.emit(f"ERROR loading model: {e}")
            self.all_completed.emit()
            return

        total_files = len(self._file_queue)
        queue_start_time = time.time()

        for idx, file_path in enumerate(self._file_queue):
            if self._cancelled:
                self.log_message.emit("Transcription cancelled by user.")
                break

            filename = Path(file_path).name
            self.file_started.emit(idx, file_path)

            overall_pct = int((idx / total_files) * 100)
            self.progress.emit(
                f"Extracting audio ({idx + 1}/{total_files}): {filename}",
                overall_pct,
            )

            try:
                self._process_single_file(idx, file_path, device)
            except Exception as e:
                error_msg = f"{type(e).__name__}: {e}"
                self.log_message.emit(f"  ✗ Error: {error_msg}")
                self.log_message.emit(traceback.format_exc())
                self.file_error.emit(idx, file_path, error_msg)

        # Final summary
        total_elapsed = time.time() - queue_start_time
        if not self._cancelled:
            self.progress.emit("All transcriptions completed!", 100)
            self.log_message.emit(
                f"All transcriptions completed! "
                f"({total_files} file(s) in {self._format_elapsed(total_elapsed)})"
            )
        else:
            self.progress.emit("Transcription cancelled.", 0)

        self.all_completed.emit()

    # ─── Process a single file ────────────────────────────────

    def _process_single_file(self, idx: int, file_path: str, device: str):
        """Extract audio, chunk, transcribe, and write output for one file."""
        import whisper

        filename = Path(file_path).name
        total_files = len(self._file_queue)

        # --- Step 1: Get duration ---
        self.log_message.emit(
            f"[{idx + 1}/{total_files}] Preparing: {filename}"
        )
        duration = self._get_duration(file_path)
        if duration <= 0:
            raise RuntimeError(f"Could not determine duration of '{filename}'")
        self.log_message.emit(
            f"  Duration: {self._format_elapsed(duration)}"
        )

        # --- Step 2: Extract audio to temp WAV ---
        self.log_message.emit(f"  Extracting audio...")
        self.progress.emit(
            f"Extracting audio ({idx + 1}/{total_files}): {filename}",
            int((idx / total_files) * 100),
        )

        tmp_dir = tempfile.mkdtemp(prefix="whisper_")
        full_wav = os.path.join(tmp_dir, "full_audio.wav")

        try:
            extraction_start = time.time()
            if not self._extract_audio(file_path, full_wav):
                raise RuntimeError("FFmpeg audio extraction failed")
            extract_time = time.time() - extraction_start
            self.log_message.emit(
                f"  Audio extracted in {extract_time:.1f}s"
            )

            if self._cancelled:
                self.log_message.emit("Transcription cancelled by user.")
                return

            # --- Step 3: Chunk and transcribe ---
            all_segments = []
            full_text_parts = []
            num_chunks = max(1, int(duration // CHUNK_DURATION_SECONDS) + (
                1 if duration % CHUNK_DURATION_SECONDS > 0 else 0
            ))

            self.log_message.emit(
                f"  Transcribing in {num_chunks} chunk(s)..."
            )

            file_start_time = time.time()

            for chunk_idx in range(num_chunks):
                if self._cancelled:
                    self.log_message.emit("Transcription cancelled by user.")
                    return

                chunk_start = chunk_idx * CHUNK_DURATION_SECONDS
                chunk_dur = min(
                    CHUNK_DURATION_SECONDS, duration - chunk_start
                )

                # For short files (single chunk), use the full WAV directly
                if num_chunks == 1:
                    chunk_wav = full_wav
                else:
                    chunk_wav = os.path.join(
                        tmp_dir, f"chunk_{chunk_idx:04d}.wav"
                    )
                    if not self._extract_audio_chunk(
                        full_wav, chunk_wav, chunk_start, chunk_dur
                    ):
                        self.log_message.emit(
                            f"  ✗ Failed to extract chunk {chunk_idx + 1}"
                        )
                        continue

                # Build transcription options
                transcribe_options = {
                    "beam_size": self._beam_size,
                    "best_of": self._best_of,
                    "temperature": self._temperature,
                    "condition_on_previous_text": self._condition_on_previous_text,
                    "verbose": False,
                    "fp16": (device != "cpu"),
                }

                if self._language != "auto":
                    transcribe_options["language"] = self._language
                    transcribe_options["task"] = "transcribe"

                if self._initial_prompt.strip():
                    transcribe_options["initial_prompt"] = (
                        self._initial_prompt.strip()
                    )

                # Transcribe this chunk
                result = self._model.transcribe(chunk_wav, **transcribe_options)

                if self._cancelled:
                    self.log_message.emit("Transcription cancelled by user.")
                    return

                # Process segments — adjust timestamps by chunk offset
                chunk_text = result.get("text", "").strip()
                if chunk_text:
                    full_text_parts.append(chunk_text)

                for seg in result.get("segments", []):
                    adjusted_start = seg["start"] + chunk_start
                    adjusted_end = seg["end"] + chunk_start
                    seg_text = seg["text"].strip()

                    all_segments.append({
                        "start": adjusted_start,
                        "end": adjusted_end,
                        "text": seg_text,
                    })

                    # Emit live segment
                    self.segment_transcribed.emit(
                        idx, seg_text, adjusted_start, adjusted_end
                    )

                # Clean up chunk file (but not the full WAV yet)
                if chunk_wav != full_wav and os.path.exists(chunk_wav):
                    os.remove(chunk_wav)

                # Update progress
                chunk_end_time = chunk_start + chunk_dur
                file_pct = min(100, int((chunk_end_time / duration) * 100))
                self.file_progress.emit(idx, file_pct)

                overall_pct = int(
                    ((idx + chunk_end_time / duration) / total_files) * 100
                )
                self.progress.emit(
                    f"Transcribing ({idx + 1}/{total_files}): {filename} "
                    f"[{self._format_elapsed(chunk_end_time)}/{self._format_elapsed(duration)}]",
                    overall_pct,
                )

                self.log_message.emit(
                    f"  Chunk {chunk_idx + 1}/{num_chunks} done "
                    f"({self._format_elapsed(chunk_start)}–"
                    f"{self._format_elapsed(chunk_end_time)})"
                )

            # --- Step 4: Write output file ---
            elapsed = time.time() - file_start_time
            output_path = self._get_output_path(file_path)

            full_text = " ".join(full_text_parts)
            lines = []
            for seg in all_segments:
                s = self._format_timestamp(seg["start"])
                e = self._format_timestamp(seg["end"])
                lines.append(f"[{s} --> {e}]  {seg['text']}")

            output_content = full_text + "\n\n" + "─" * 60 + "\n"
            output_content += "Timestamped Segments:\n"
            output_content += "─" * 60 + "\n\n"
            output_content += "\n".join(lines)

            with open(output_path, "w", encoding="utf-8") as f:
                f.write(output_content)

            self.log_message.emit(
                f"  ✓ Completed in {self._format_elapsed(elapsed)} "
                f"→ {Path(output_path).name}"
            )
            self.file_completed.emit(idx, file_path, output_path)

        finally:
            # --- Cleanup temp files ---
            import shutil
            if os.path.exists(tmp_dir):
                shutil.rmtree(tmp_dir, ignore_errors=True)

    # ─── Formatting helpers ───────────────────────────────────

    @staticmethod
    def _format_timestamp(seconds: float) -> str:
        """Format seconds into HH:MM:SS.mmm timestamp."""
        hrs = int(seconds // 3600)
        mins = int((seconds % 3600) // 60)
        secs = seconds % 60
        return f"{hrs:02d}:{mins:02d}:{secs:06.3f}"

    @staticmethod
    def _format_elapsed(seconds: float) -> str:
        """Format seconds into a human-readable elapsed time string."""
        hrs = int(seconds // 3600)
        mins = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        if hrs > 0:
            return f"{hrs}h {mins:02d}m {secs:02d}s"
        elif mins > 0:
            return f"{mins}m {secs:02d}s"
        else:
            return f"{secs}s"
