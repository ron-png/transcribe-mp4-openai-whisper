"""
Whisper transcription engine running in a background thread.

Handles model loading, transcription with optimal German settings,
and progress reporting via Qt signals.
"""

import os
import time
import traceback
from pathlib import Path

import torch
from PyQt6.QtCore import QThread, pyqtSignal


class TranscriberWorker(QThread):
    """
    Background worker that transcribes video files using OpenAI Whisper.

    Signals:
        progress(str, int): (status_message, percentage)
        file_started(int, str): (queue_index, file_path)
        file_completed(int, str, str): (queue_index, file_path, output_path)
        file_error(int, str, str): (queue_index, file_path, error_message)
        all_completed(): Emitted when the entire queue is done.
        log_message(str): Log message for the UI log panel.
        model_loading(str): Emitted when model starts loading.
        model_loaded(str): Emitted when model finishes loading.
    """

    progress = pyqtSignal(str, int)
    file_started = pyqtSignal(int, str)
    file_completed = pyqtSignal(int, str, str)
    file_error = pyqtSignal(int, str, str)
    all_completed = pyqtSignal()
    log_message = pyqtSignal(str)
    model_loading = pyqtSignal(str)
    model_loaded = pyqtSignal(str)

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

    def _get_output_path(self, video_path: str) -> str:
        """Determine the output .txt file path for a given video."""
        video = Path(video_path)
        if self._output_same_dir:
            return str(video.with_suffix(".txt"))
        else:
            output_dir = Path(self._output_directory)
            output_dir.mkdir(parents=True, exist_ok=True)
            return str(output_dir / (video.stem + ".txt"))

    def _detect_device(self) -> str:
        """Detect and log the compute device."""
        if torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name(0)
            vram = torch.cuda.get_device_properties(0).total_mem / (1024**3)
            self.log_message.emit(f"GPU detected: {gpu_name} ({vram:.1f} GB)")
            return "cuda"
        elif torch.backends.mps.is_available():
            self.log_message.emit("Apple Silicon GPU detected (MPS backend)")
            return "mps"
        else:
            self.log_message.emit("No GPU detected — using CPU (transcription will be slower)")
            return "cpu"

    def run(self):
        """Main transcription loop — runs in background thread."""
        try:
            import whisper  # Import here to keep startup fast
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
        self.log_message.emit(f"Loading Whisper model '{self._model_name}' on {device}...")
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
            self.log_message.emit(
                f"[{idx + 1}/{total_files}] Transcribing: {filename}"
            )
            overall_pct = int((idx / total_files) * 100)
            self.progress.emit(
                f"Transcribing ({idx + 1}/{total_files}): {filename}",
                overall_pct,
            )

            try:
                # Build transcription options for highest quality
                transcribe_options = {
                    "beam_size": self._beam_size,
                    "best_of": self._best_of,
                    "temperature": self._temperature,
                    "condition_on_previous_text": self._condition_on_previous_text,
                    "verbose": False,
                    "fp16": (device != "cpu"),  # Use fp16 on GPU, fp32 on CPU
                }

                # Set language (None for auto-detect)
                if self._language != "auto":
                    transcribe_options["language"] = self._language
                    transcribe_options["task"] = "transcribe"

                # Add initial prompt for better German transcription
                if self._initial_prompt.strip():
                    transcribe_options["initial_prompt"] = self._initial_prompt.strip()

                start_time = time.time()
                result = self._model.transcribe(file_path, **transcribe_options)
                elapsed = time.time() - start_time

                if self._cancelled:
                    self.log_message.emit("Transcription cancelled by user.")
                    break

                # Write transcription to .txt file
                output_path = self._get_output_path(file_path)
                text = result.get("text", "").strip()

                # Also build segment-by-segment output with timestamps
                segments = result.get("segments", [])
                lines = []
                for seg in segments:
                    start = self._format_timestamp(seg["start"])
                    end = self._format_timestamp(seg["end"])
                    seg_text = seg["text"].strip()
                    lines.append(f"[{start} --> {end}]  {seg_text}")

                output_content = text + "\n\n" + "─" * 60 + "\n"
                output_content += "Timestamped Segments:\n"
                output_content += "─" * 60 + "\n\n"
                output_content += "\n".join(lines)

                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(output_content)

                detected_lang = result.get("language", "unknown")
                self.log_message.emit(
                    f"  ✓ Completed in {elapsed:.1f}s "
                    f"(detected: {detected_lang}) → {Path(output_path).name}"
                )
                self.file_completed.emit(idx, file_path, output_path)

            except Exception as e:
                error_msg = f"{type(e).__name__}: {e}"
                self.log_message.emit(f"  ✗ Error: {error_msg}")
                self.log_message.emit(traceback.format_exc())
                self.file_error.emit(idx, file_path, error_msg)

        # Final progress
        total_elapsed = time.time() - queue_start_time
        if not self._cancelled:
            self.progress.emit("All transcriptions completed!", 100)
            self.log_message.emit(
                f"All transcriptions completed! "
                f"({total_files} file(s) in {total_elapsed:.1f}s)"
            )
        else:
            self.progress.emit("Transcription cancelled.", 0)

        self.all_completed.emit()

    @staticmethod
    def _format_timestamp(seconds: float) -> str:
        """Format seconds into HH:MM:SS.mmm timestamp."""
        hrs = int(seconds // 3600)
        mins = int((seconds % 3600) // 60)
        secs = seconds % 60
        return f"{hrs:02d}:{mins:02d}:{secs:06.3f}"
