"""
Main application window for the Whisper Transcription GUI.

Provides the primary user interface with file queue, controls,
progress tracking, settings dialog, and drag-and-drop support.
"""

import os
from pathlib import Path

from PyQt6.QtCore import Qt, QSize, QMimeData
from PyQt6.QtGui import QIcon, QDragEnterEvent, QDropEvent, QAction
from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QProgressBar,
    QTextEdit,
    QFileDialog,
    QSplitter,
    QDialog,
    QGroupBox,
    QFormLayout,
    QComboBox,
    QSpinBox,
    QDoubleSpinBox,
    QCheckBox,
    QLineEdit,
    QMessageBox,
    QAbstractItemView,
    QSizePolicy,
)

from .scanner import scan_directory, scan_files
from .settings import AppSettings, WHISPER_MODELS, LANGUAGES
from .transcriber import TranscriberWorker
from .styles import COLORS


class SettingsDialog(QDialog):
    """Settings/preferences dialog."""

    def __init__(self, settings: AppSettings, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.setWindowTitle("Settings")
        self.setMinimumWidth(520)
        self.setModal(True)
        self._build_ui()
        self._load_settings()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        # — Model settings —
        model_group = QGroupBox("Whisper Model")
        model_layout = QFormLayout(model_group)
        model_layout.setSpacing(12)

        self.model_combo = QComboBox()
        for model_name, vram in WHISPER_MODELS.items():
            self.model_combo.addItem(f"{model_name}  ({vram})", model_name)
        model_layout.addRow("Model:", self.model_combo)

        layout.addWidget(model_group)

        # — Language settings —
        lang_group = QGroupBox("Language")
        lang_layout = QFormLayout(lang_group)
        lang_layout.setSpacing(12)

        self.lang_combo = QComboBox()
        for code, name in LANGUAGES.items():
            self.lang_combo.addItem(f"{name} ({code})", code)
        lang_layout.addRow("Language:", self.lang_combo)

        self.initial_prompt_edit = QLineEdit()
        self.initial_prompt_edit.setPlaceholderText(
            "e.g. Folgende Wörter werden auf Deutsch transkribiert."
        )
        self.initial_prompt_edit.setToolTip(
            "A prompt to hint Whisper toward the target language.\n"
            "For German, this improves handling of ä, ö, ü, ß.\n"
            "Leave empty to disable."
        )
        lang_layout.addRow("Initial Prompt:", self.initial_prompt_edit)

        layout.addWidget(lang_group)

        # — Quality settings —
        quality_group = QGroupBox("Quality")
        quality_layout = QFormLayout(quality_group)
        quality_layout.setSpacing(12)

        self.beam_spin = QSpinBox()
        self.beam_spin.setRange(1, 10)
        self.beam_spin.setToolTip("Higher = better quality, slower speed")
        quality_layout.addRow("Beam Size:", self.beam_spin)

        self.best_of_spin = QSpinBox()
        self.best_of_spin.setRange(1, 10)
        self.best_of_spin.setToolTip(
            "Number of candidates to consider. Higher = better quality."
        )
        quality_layout.addRow("Best Of:", self.best_of_spin)

        self.temperature_spin = QDoubleSpinBox()
        self.temperature_spin.setRange(0.0, 1.0)
        self.temperature_spin.setSingleStep(0.1)
        self.temperature_spin.setDecimals(1)
        self.temperature_spin.setToolTip(
            "0.0 = greedy decoding (most accurate).\n"
            "Higher values add randomness.\n"
            "Recommended: 0.0 for maximum quality."
        )
        quality_layout.addRow("Temperature:", self.temperature_spin)

        self.condition_check = QCheckBox("Use previous text as context")
        self.condition_check.setToolTip(
            "Improves coherence but may propagate errors in long files"
        )
        quality_layout.addRow(self.condition_check)

        layout.addWidget(quality_group)

        # — Output settings —
        output_group = QGroupBox("Output")
        output_layout = QFormLayout(output_group)
        output_layout.setSpacing(12)

        self.same_dir_check = QCheckBox(
            "Save .txt next to video file"
        )
        output_layout.addRow(self.same_dir_check)

        self.skip_transcribed_check = QCheckBox(
            "Skip already transcribed files"
        )
        self.skip_transcribed_check.setToolTip(
            "When scanning directories, skip videos that already have a .txt file"
        )
        output_layout.addRow(self.skip_transcribed_check)

        out_dir_row = QHBoxLayout()
        self.output_dir_edit = QLineEdit()
        self.output_dir_edit.setPlaceholderText("Custom output directory...")
        self.output_dir_btn = QPushButton("Browse")
        self.output_dir_btn.clicked.connect(self._browse_output_dir)
        out_dir_row.addWidget(self.output_dir_edit)
        out_dir_row.addWidget(self.output_dir_btn)
        output_layout.addRow("Output Dir:", out_dir_row)

        self.same_dir_check.toggled.connect(
            lambda checked: self.output_dir_edit.setEnabled(not checked)
        )
        self.same_dir_check.toggled.connect(
            lambda checked: self.output_dir_btn.setEnabled(not checked)
        )

        layout.addWidget(output_group)

        # — Dialog buttons —
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        save_btn = QPushButton("Save")
        save_btn.setObjectName("primaryButton")
        save_btn.clicked.connect(self._save_and_close)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(save_btn)
        layout.addLayout(btn_layout)

    def _load_settings(self):
        # Model
        model = self.settings.get("model")
        idx = self.model_combo.findData(model)
        if idx >= 0:
            self.model_combo.setCurrentIndex(idx)

        # Language
        lang = self.settings.get("language")
        idx = self.lang_combo.findData(lang)
        if idx >= 0:
            self.lang_combo.setCurrentIndex(idx)

        # Initial prompt
        self.initial_prompt_edit.setText(
            self.settings.get("initial_prompt") or ""
        )

        # Quality
        self.beam_spin.setValue(self.settings.get("beam_size"))
        self.best_of_spin.setValue(self.settings.get("best_of"))
        self.temperature_spin.setValue(self.settings.get("temperature"))
        self.condition_check.setChecked(
            self.settings.get("condition_on_previous_text")
        )

        # Output
        self.same_dir_check.setChecked(self.settings.get("output_same_dir"))
        self.skip_transcribed_check.setChecked(
            self.settings.get("skip_transcribed")
        )
        self.output_dir_edit.setText(self.settings.get("output_directory"))
        self.output_dir_edit.setEnabled(
            not self.settings.get("output_same_dir")
        )
        self.output_dir_btn.setEnabled(
            not self.settings.get("output_same_dir")
        )

    def _browse_output_dir(self):
        directory = QFileDialog.getExistingDirectory(
            self, "Select Output Directory"
        )
        if directory:
            self.output_dir_edit.setText(directory)

    def _save_and_close(self):
        self.settings.set("model", self.model_combo.currentData())
        self.settings.set("language", self.lang_combo.currentData())
        self.settings.set("initial_prompt", self.initial_prompt_edit.text())
        self.settings.set("beam_size", self.beam_spin.value())
        self.settings.set("best_of", self.best_of_spin.value())
        self.settings.set("temperature", self.temperature_spin.value())
        self.settings.set(
            "condition_on_previous_text", self.condition_check.isChecked()
        )
        self.settings.set("output_same_dir", self.same_dir_check.isChecked())
        self.settings.set(
            "skip_transcribed", self.skip_transcribed_check.isChecked()
        )
        self.settings.set("output_directory", self.output_dir_edit.text())
        self.settings.sync()
        self.accept()


class MainWindow(QMainWindow):
    """Primary application window."""

    # Column indices for the queue table
    COL_STATUS = 0
    COL_FILENAME = 1
    COL_FOLDER = 2
    COL_PROGRESS = 3

    def __init__(self):
        super().__init__()
        self.settings = AppSettings()
        self._worker: TranscriberWorker | None = None
        self._is_transcribing = False
        self._file_queue: list[str] = []  # Ordered list of file paths

        self.setWindowTitle("Whisper Transcriber")
        self.setMinimumSize(900, 600)
        self.resize(
            self.settings.get("window_width"),
            self.settings.get("window_height"),
        )

        # Enable drag & drop
        self.setAcceptDrops(True)

        self._build_ui()
        self._update_button_states()

    # ─── UI Construction ──────────────────────────────────────

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(20, 16, 20, 16)
        main_layout.setSpacing(12)

        # ── Header ──
        header = QHBoxLayout()
        header.setSpacing(12)

        title_col = QVBoxLayout()
        title_col.setSpacing(2)
        title_label = QLabel("Whisper Transcriber")
        title_label.setObjectName("titleLabel")
        subtitle = QLabel("High-quality video transcription powered by OpenAI Whisper")
        subtitle.setObjectName("subtitleLabel")
        title_col.addWidget(title_label)
        title_col.addWidget(subtitle)
        header.addLayout(title_col)

        header.addStretch()

        # Device indicator (GPU/CPU)
        self.device_label = QLabel("")
        self.device_label.setObjectName("deviceLabel")
        self.device_label.setVisible(False)
        header.addWidget(self.device_label)

        # File count badge
        self.file_count_label = QLabel("0 files")
        self.file_count_label.setObjectName("fileCountLabel")
        header.addWidget(self.file_count_label)

        self.model_status_label = QLabel(
            f"Model: {self.settings.get('model')}"
        )
        self.model_status_label.setObjectName("modelStatusLabel")
        header.addWidget(self.model_status_label)

        settings_btn = QPushButton("⚙  Settings")
        settings_btn.setToolTip("Open settings")
        settings_btn.clicked.connect(self._open_settings)
        header.addWidget(settings_btn)

        main_layout.addLayout(header)

        # ── Toolbar ──
        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)

        add_files_btn = QPushButton("📄  Add Files")
        add_files_btn.setToolTip("Select individual video files")
        add_files_btn.clicked.connect(self._add_files)
        toolbar.addWidget(add_files_btn)

        add_folder_btn = QPushButton("📁  Add Folder")
        add_folder_btn.setToolTip(
            "Scan a folder (and subfolders) for video files"
        )
        add_folder_btn.clicked.connect(self._add_folder)
        toolbar.addWidget(add_folder_btn)

        toolbar.addStretch()

        self.remove_btn = QPushButton("Remove Selected")
        self.remove_btn.clicked.connect(self._remove_selected)
        toolbar.addWidget(self.remove_btn)

        self.clear_btn = QPushButton("Clear Queue")
        self.clear_btn.setObjectName("dangerButton")
        self.clear_btn.clicked.connect(self._clear_queue)
        toolbar.addWidget(self.clear_btn)

        main_layout.addLayout(toolbar)

        # ── Splitter: Queue table + Log panel ──
        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.setChildrenCollapsible(True)

        # Queue table
        queue_container = QWidget()
        queue_layout = QVBoxLayout(queue_container)
        queue_layout.setContentsMargins(0, 0, 0, 0)
        queue_layout.setSpacing(0)

        self.queue_table = QTableWidget()
        self.queue_table.setColumnCount(4)
        self.queue_table.setHorizontalHeaderLabels(
            ["Status", "File Name", "Folder", "Progress"]
        )
        self.queue_table.setAlternatingRowColors(True)
        self.queue_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.queue_table.setSelectionMode(
            QAbstractItemView.SelectionMode.ExtendedSelection
        )
        self.queue_table.verticalHeader().setVisible(False)
        self.queue_table.setShowGrid(False)

        # Column sizing
        header_view = self.queue_table.horizontalHeader()
        header_view.setSectionResizeMode(
            self.COL_STATUS, QHeaderView.ResizeMode.ResizeToContents
        )
        header_view.setSectionResizeMode(
            self.COL_FILENAME, QHeaderView.ResizeMode.Stretch
        )
        header_view.setSectionResizeMode(
            self.COL_FOLDER, QHeaderView.ResizeMode.Stretch
        )
        header_view.setSectionResizeMode(
            self.COL_PROGRESS, QHeaderView.ResizeMode.Fixed
        )
        header_view.resizeSection(self.COL_PROGRESS, 140)

        # Drop hint shown when queue is empty
        self.drop_hint = QLabel(
            "Drag & drop video files or folders here\nor use the buttons above to add files"
        )
        self.drop_hint.setObjectName("dropHintLabel")
        self.drop_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)

        queue_layout.addWidget(self.drop_hint)
        queue_layout.addWidget(self.queue_table)
        self.queue_table.setVisible(False)

        splitter.addWidget(queue_container)

        # Log panel
        log_container = QWidget()
        log_layout = QVBoxLayout(log_container)
        log_layout.setContentsMargins(0, 4, 0, 0)
        log_layout.setSpacing(4)

        log_header = QLabel("Log")
        log_header.setObjectName("sectionLabel")
        log_layout.addWidget(log_header)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(180)
        log_layout.addWidget(self.log_text)

        splitter.addWidget(log_container)
        splitter.setSizes([500, 150])

        main_layout.addWidget(splitter, 1)

        # ── Bottom: Progress + Controls ──
        bottom = QVBoxLayout()
        bottom.setSpacing(8)

        # Progress row
        progress_row = QHBoxLayout()
        self.status_label = QLabel("Ready")
        self.status_label.setObjectName("statusLabel")
        progress_row.addWidget(self.status_label, 1)

        self.elapsed_label = QLabel("")
        self.elapsed_label.setObjectName("statusLabel")
        progress_row.addWidget(self.elapsed_label)

        bottom.addLayout(progress_row)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        bottom.addWidget(self.progress_bar)

        # Action buttons
        action_row = QHBoxLayout()
        action_row.addStretch()

        self.start_btn = QPushButton("▶  Start Transcription")
        self.start_btn.setObjectName("primaryButton")
        self.start_btn.clicked.connect(self._start_transcription)
        action_row.addWidget(self.start_btn)

        self.stop_btn = QPushButton("■  Stop")
        self.stop_btn.setObjectName("dangerButton")
        self.stop_btn.clicked.connect(self._stop_transcription)
        self.stop_btn.setVisible(False)
        action_row.addWidget(self.stop_btn)

        action_row.addStretch()
        bottom.addLayout(action_row)

        main_layout.addLayout(bottom)

    # ─── Drag & Drop ──────────────────────────────────────────

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        files_to_add = []
        dirs_to_scan = []

        for url in urls:
            path = url.toLocalFile()
            if os.path.isdir(path):
                dirs_to_scan.append(path)
            elif os.path.isfile(path):
                files_to_add.append(path)

        skip = self.settings.get("skip_transcribed")

        # Scan directories
        for d in dirs_to_scan:
            found = scan_directory(d, skip_transcribed=skip)
            files_to_add.extend(found)

        # Filter to valid video files
        valid = scan_files(files_to_add, skip_transcribed=skip)
        self._add_to_queue(valid)

    # ─── File / Folder Pickers ────────────────────────────────

    def _add_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Video Files",
            "",
            "Video Files (*.mp4 *.mkv *.avi *.mov *.webm *.flv *.wmv *.m4v "
            "*.mpeg *.mpg *.3gp *.ogv *.ts *.mts *.m2ts);;All Files (*)",
        )
        if files:
            skip = self.settings.get("skip_transcribed")
            valid = scan_files(files, skip_transcribed=skip)
            self._add_to_queue(valid)

    def _add_folder(self):
        directory = QFileDialog.getExistingDirectory(
            self, "Select Folder to Scan"
        )
        if directory:
            skip = self.settings.get("skip_transcribed")
            found = scan_directory(directory, skip_transcribed=skip)
            if not found:
                self._log("No video files found in the selected folder.")
            else:
                self._log(
                    f"Found {len(found)} video file(s) in '{directory}'"
                )
            self._add_to_queue(found)

    # ─── Queue Management ─────────────────────────────────────

    def _add_to_queue(self, file_paths: list[str]):
        """Add files to the queue, avoiding duplicates."""
        existing = set(self._file_queue)
        new_files = [f for f in file_paths if f not in existing]
        if not new_files:
            return

        self._file_queue.extend(new_files)

        for file_path in new_files:
            row = self.queue_table.rowCount()
            self.queue_table.insertRow(row)

            p = Path(file_path)

            # Status
            status_item = QTableWidgetItem("⏳ Pending")
            status_item.setFlags(
                status_item.flags() & ~Qt.ItemFlag.ItemIsEditable
            )
            status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.queue_table.setItem(row, self.COL_STATUS, status_item)

            # Filename
            name_item = QTableWidgetItem(p.name)
            name_item.setFlags(
                name_item.flags() & ~Qt.ItemFlag.ItemIsEditable
            )
            name_item.setToolTip(str(file_path))
            self.queue_table.setItem(row, self.COL_FILENAME, name_item)

            # Folder
            folder_item = QTableWidgetItem(str(p.parent))
            folder_item.setFlags(
                folder_item.flags() & ~Qt.ItemFlag.ItemIsEditable
            )
            folder_item.setToolTip(str(p.parent))
            self.queue_table.setItem(row, self.COL_FOLDER, folder_item)

            # Progress bar
            progress = QProgressBar()
            progress.setValue(0)
            progress.setTextVisible(False)
            self.queue_table.setCellWidget(row, self.COL_PROGRESS, progress)

        self._update_visibility()
        self._update_button_states()
        self._update_file_count()

    def _remove_selected(self):
        if self._is_transcribing:
            return

        selected_rows = sorted(
            set(idx.row() for idx in self.queue_table.selectedIndexes()),
            reverse=True,
        )
        for row in selected_rows:
            if row < len(self._file_queue):
                self._file_queue.pop(row)
            self.queue_table.removeRow(row)

        self._update_visibility()
        self._update_button_states()
        self._update_file_count()

    def _clear_queue(self):
        if self._is_transcribing:
            return

        self._file_queue.clear()
        self.queue_table.setRowCount(0)
        self._update_visibility()
        self._update_button_states()
        self._update_file_count()

    def _update_visibility(self):
        has_items = len(self._file_queue) > 0
        self.queue_table.setVisible(has_items)
        self.drop_hint.setVisible(not has_items)

    def _update_button_states(self):
        has_items = len(self._file_queue) > 0
        self.start_btn.setEnabled(has_items and not self._is_transcribing)
        self.remove_btn.setEnabled(has_items and not self._is_transcribing)
        self.clear_btn.setEnabled(has_items and not self._is_transcribing)

    def _update_file_count(self):
        count = len(self._file_queue)
        self.file_count_label.setText(
            f"{count} file{'s' if count != 1 else ''}"
        )

    # ─── Transcription Control ────────────────────────────────

    def _start_transcription(self):
        if not self._file_queue:
            return

        self._is_transcribing = True
        self._update_button_states()
        self.start_btn.setVisible(False)
        self.stop_btn.setVisible(True)
        self.progress_bar.setValue(0)
        self.elapsed_label.setText("")

        # Reset all statuses to pending
        for row in range(self.queue_table.rowCount()):
            status_item = self.queue_table.item(row, self.COL_STATUS)
            if status_item:
                status_item.setText("⏳ Pending")
            progress = self.queue_table.cellWidget(row, self.COL_PROGRESS)
            if progress:
                progress.setValue(0)

        # Create and configure worker
        self._worker = TranscriberWorker(self)
        self._worker.configure(
            file_queue=self._file_queue,
            model_name=self.settings.get("model"),
            language=self.settings.get("language"),
            beam_size=self.settings.get("beam_size"),
            best_of=self.settings.get("best_of"),
            temperature=self.settings.get("temperature"),
            condition_on_previous_text=self.settings.get(
                "condition_on_previous_text"
            ),
            initial_prompt=self.settings.get("initial_prompt"),
            output_same_dir=self.settings.get("output_same_dir"),
            output_directory=self.settings.get("output_directory"),
        )

        # Connect signals
        self._worker.progress.connect(self._on_progress)
        self._worker.file_started.connect(self._on_file_started)
        self._worker.file_completed.connect(self._on_file_completed)
        self._worker.file_error.connect(self._on_file_error)
        self._worker.all_completed.connect(self._on_all_completed)
        self._worker.log_message.connect(self._log)
        self._worker.model_loading.connect(self._on_model_loading)
        self._worker.model_loaded.connect(self._on_model_loaded)

        self._worker.start()

    def _stop_transcription(self):
        if self._worker:
            self._worker.cancel()
            self._log("Cancellation requested... waiting for current operation to finish.")
            self.stop_btn.setEnabled(False)

    # ─── Worker Signal Handlers ───────────────────────────────

    def _on_progress(self, message: str, percentage: int):
        self.status_label.setText(message)
        self.progress_bar.setValue(percentage)

    def _on_file_started(self, index: int, file_path: str):
        if index < self.queue_table.rowCount():
            status_item = self.queue_table.item(index, self.COL_STATUS)
            if status_item:
                status_item.setText("🔄 Transcribing")
            # Pulse the progress bar for the active file
            progress = self.queue_table.cellWidget(index, self.COL_PROGRESS)
            if progress:
                progress.setMaximum(0)  # Indeterminate mode

    def _on_file_completed(self, index: int, file_path: str, output: str):
        if index < self.queue_table.rowCount():
            status_item = self.queue_table.item(index, self.COL_STATUS)
            if status_item:
                status_item.setText("✅ Done")
            progress = self.queue_table.cellWidget(index, self.COL_PROGRESS)
            if progress:
                progress.setMaximum(100)
                progress.setValue(100)

    def _on_file_error(self, index: int, file_path: str, error: str):
        if index < self.queue_table.rowCount():
            status_item = self.queue_table.item(index, self.COL_STATUS)
            if status_item:
                status_item.setText("❌ Error")
                status_item.setToolTip(error)
            progress = self.queue_table.cellWidget(index, self.COL_PROGRESS)
            if progress:
                progress.setMaximum(100)
                progress.setValue(0)

    def _on_all_completed(self):
        self._is_transcribing = False
        self.start_btn.setVisible(True)
        self.stop_btn.setVisible(False)
        self.stop_btn.setEnabled(True)
        self._update_button_states()

    def _on_model_loading(self, model_name: str):
        self.model_status_label.setText(f"Model: {model_name} (loading...)")

    def _on_model_loaded(self, model_name: str):
        self.model_status_label.setText(f"Model: {model_name} ✓")

        # Show device info
        import torch
        if torch.cuda.is_available():
            gpu = torch.cuda.get_device_name(0)
            self.device_label.setText(f"⚡ {gpu}")
        elif torch.backends.mps.is_available():
            self.device_label.setText("⚡ Apple GPU")
        else:
            self.device_label.setText("🖥 CPU")
        self.device_label.setVisible(True)

    # ─── Settings ─────────────────────────────────────────────

    def _open_settings(self):
        dialog = SettingsDialog(self.settings, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.model_status_label.setText(
                f"Model: {self.settings.get('model')}"
            )
            self._log("Settings saved.")

    # ─── Logging ──────────────────────────────────────────────

    def _log(self, message: str):
        self.log_text.append(message)
        # Auto-scroll to bottom
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    # ─── Window Lifecycle ─────────────────────────────────────

    def closeEvent(self, event):
        if self._is_transcribing and self._worker:
            reply = QMessageBox.question(
                self,
                "Transcription in Progress",
                "A transcription is still running. Are you sure you want to quit?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.No:
                event.ignore()
                return
            self._worker.cancel()
            self._worker.wait(5000)

        # Save window size
        self.settings.set("window_width", self.width())
        self.settings.set("window_height", self.height())
        self.settings.sync()
        event.accept()
