# src/compression_dialog.py
import os
import pathlib
from typing import List, Optional
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                               QLineEdit, QComboBox, QSpinBox, QCheckBox, 
                               QPushButton, QGroupBox, QTextEdit, QFileDialog,
                               QProgressBar, QMessageBox, QTabWidget, QWidget)
from PySide6.QtCore import Qt, QThread, Signal, QTimer
from core.compression_engine import CompressionEngine
from core.encryption_engine import EncryptionEngine
from ui.password_dialog import PasswordDialog


class CompressionWorker(QThread):
    progress_updated = Signal(int, str)
    finished = Signal(list)
    error_occurred = Signal(str)
    
    def __init__(self, compression_engine, source_paths, archive_path, format_type,
                 compression_level, split_size=None, encrypt=False, password=None):
        super().__init__()
        self.compression_engine = compression_engine
        self.source_paths = source_paths
        self.archive_path = archive_path
        self.format_type = format_type
        self.compression_level = compression_level
        self.split_size = split_size
        self.encrypt = encrypt
        self.password = password
    
    def run(self):
        try:
            def progress_callback(processed, total):
                progress = int((processed / total) * 100) if total > 0 else 0
                self.progress_updated.emit(progress, f"Compressing... {processed}/{total} files")
            
            created_files = self.compression_engine.create_archive(
                self.source_paths,
                self.archive_path,
                self.format_type,
                self.compression_level,
                self.split_size,
                progress_callback
            )
            
            # Encrypt the created archive(s) if requested
            if self.encrypt and self.password:
                encryption_engine = EncryptionEngine()
                encrypted_files = []
                for archive_file in created_files:
                    if archive_file.exists():
                        encrypted_file = archive_file.with_suffix(archive_file.suffix + '.encrypted')
                        encryption_engine.encrypt_file(
                            archive_file,
                            self.password,
                            encrypted_file
                        )
                        # Remove unencrypted archive
                        archive_file.unlink()
                        encrypted_files.append(encrypted_file)
                created_files = encrypted_files
            
            self.finished.emit(created_files)
        except Exception as e:
            self.error_occurred.emit(str(e))


class CompressionDialog(QDialog):
    def __init__(self, parent=None, source_paths: Optional[List[pathlib.Path]] = None):
        super().__init__(parent)
        self.source_paths = source_paths or []
        self.compression_engine = CompressionEngine()
        self.created_files = []
        
        self.setWindowTitle("Compress Files")
        self.setModal(True)
        self.resize(600, 500)
        
        self._create_ui()
        self._connect_signals()
    
    def _create_ui(self):
        layout = QVBoxLayout(self)
        
        # Source files display
        source_group = QGroupBox("Source Files")
        source_layout = QVBoxLayout()
        
        self.source_text = QTextEdit()
        self.source_text.setMaximumHeight(100)
        self.source_text.setReadOnly(True)
        self._update_source_display()
        source_layout.addWidget(self.source_text)
        
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self._browse_source_files)
        source_layout.addWidget(browse_btn)
        
        source_group.setLayout(source_layout)
        layout.addWidget(source_group)
        
        # Archive settings
        settings_group = QGroupBox("Archive Settings")
        settings_layout = QVBoxLayout()
        
        # Archive name and location
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Archive Name:"))
        self.archive_name_edit = QLineEdit()
        self.archive_name_edit.setText("archive")
        name_layout.addWidget(self.archive_name_edit)
        settings_layout.addLayout(name_layout)
        
        # Location
        location_layout = QHBoxLayout()
        location_layout.addWidget(QLabel("Save Location:"))
        self.location_edit = QLineEdit()
        self.location_edit.setText(str(pathlib.Path.home() / "Documents"))
        location_layout.addWidget(self.location_edit)
        
        browse_location_btn = QPushButton("Browse...")
        browse_location_btn.clicked.connect(self._browse_location)
        location_layout.addWidget(browse_location_btn)
        settings_layout.addLayout(location_layout)
        
        # Format selection
        format_layout = QHBoxLayout()
        format_layout.addWidget(QLabel("Format:"))
        self.format_combo = QComboBox()
        for format_key, format_info in self.compression_engine.SUPPORTED_FORMATS.items():
            self.format_combo.addItem(format_info['description'], format_key)
        format_layout.addWidget(self.format_combo)
        settings_layout.addLayout(format_layout)
        
        # Compression level
        level_layout = QHBoxLayout()
        level_layout.addWidget(QLabel("Compression Level:"))
        self.level_combo = QComboBox()
        self.level_combo.addItems(["fast", "normal", "maximum"])
        self.level_combo.setCurrentText("normal")
        level_layout.addWidget(self.level_combo)
        settings_layout.addLayout(level_layout)
        
        # Split options
        split_group = QGroupBox("Split Archive")
        split_group.setCheckable(True)
        split_group.setChecked(False)
        split_layout = QVBoxLayout()
        
        split_size_layout = QHBoxLayout()
        split_size_layout.addWidget(QLabel("Split Size (MB):"))
        self.split_size_spin = QSpinBox()
        self.split_size_spin.setRange(1, 10000)
        self.split_size_spin.setValue(100)
        split_size_layout.addWidget(self.split_size_spin)
        split_layout.addLayout(split_size_layout)
        
        split_group.setLayout(split_layout)
        settings_layout.addWidget(split_group)
        
        # Encryption options
        self.encryption_group = QGroupBox("Encryption")
        self.encryption_group.setCheckable(True)
        self.encryption_group.setChecked(False)
        encryption_layout = QVBoxLayout()
        
        encryption_layout.addWidget(QLabel("Encrypt archive with AES-256"))
        encryption_layout.addWidget(QLabel("You will be prompted for a password when compression starts"))
        
        self.encryption_group.setLayout(encryption_layout)
        settings_layout.addWidget(self.encryption_group)
        
        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)
        
        # Preview
        preview_group = QGroupBox("Preview")
        preview_layout = QVBoxLayout()
        
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setMaximumHeight(100)
        preview_layout.addWidget(self.preview_text)
        
        preview_group.setLayout(preview_layout)
        layout.addWidget(preview_group)
        
        # Progress
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.compress_btn = QPushButton("Compress")
        self.compress_btn.clicked.connect(self._start_compression)
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(self.compress_btn)
        button_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(button_layout)
        
        # Store references
        self.split_group = split_group
        
        # Timer for delayed preview updates
        self.preview_timer = QTimer()
        self.preview_timer.setSingleShot(True)
        self.preview_timer.timeout.connect(self._update_preview)
        self.preview_timer.setInterval(500)  # 500ms delay
    
    def _connect_signals(self):
        self.archive_name_edit.textChanged.connect(self._schedule_preview_update)
        self.format_combo.currentTextChanged.connect(self._schedule_preview_update)
        self.level_combo.currentTextChanged.connect(self._schedule_preview_update)
        self.split_group.toggled.connect(self._schedule_preview_update)
        self.split_size_spin.valueChanged.connect(self._schedule_preview_update)
        self.encryption_group.toggled.connect(self._schedule_preview_update)
    
    def _update_source_display(self):
        if self.source_paths:
            display_text = "\n".join(str(p) for p in self.source_paths[:5])
            if len(self.source_paths) > 5:
                display_text += f"\n... and {len(self.source_paths) - 5} more files"
            self.source_text.setPlainText(display_text)
        else:
            self.source_text.setPlainText("No files selected")
    
    def _browse_source_files(self):
        from PySide6.QtWidgets import QFileDialog
        files, _ = QFileDialog.getOpenFileNames(
            self, "Select Files to Compress", str(pathlib.Path.home())
        )
        if files:
            self.source_paths = [pathlib.Path(f) for f in files]
            self._update_source_display()
            self._update_preview()
    
    def _browse_location(self):
        directory = QFileDialog.getExistingDirectory(
            self, "Select Save Location", self.location_edit.text()
        )
        if directory:
            self.location_edit.setText(directory)
            self._update_preview()
    
    def _schedule_preview_update(self):
        """Schedule a delayed preview update to prevent UI freezing."""
        self.preview_timer.start()

    def _update_preview(self):
        """Update preview with optimized file size calculation."""
        if not self.source_paths:
            self.preview_text.setPlainText("No source files selected")
            return
        
        archive_name = self.archive_name_edit.text() or "archive"
        format_type = self.format_combo.currentData()
        location = pathlib.Path(self.location_edit.text())
        
        extension = self.compression_engine.SUPPORTED_FORMATS[format_type]['extension']
        archive_path = location / f"{archive_name}{extension}"
        
        # Show encrypted extension if encryption is enabled
        if self.encryption_group.isChecked():
            archive_path = archive_path.with_suffix(archive_path.suffix + '.encrypted')
        
        preview_text = f"Archive: {archive_name}{extension}"
        if self.encryption_group.isChecked():
            preview_text += ".encrypted"
        preview_text += "\n"
        
        # Quick estimation - use cached values or limit calculation time
        total_size = 0
        file_count = 0
        
        try:
            for path in self.source_paths:
                if path.is_file():
                    try:
                        stat = path.stat()
                        total_size += stat.st_size
                        file_count += 1
                    except (OSError, FileNotFoundError):
                        continue
                elif path.is_dir():
                    try:
                        # Use faster directory size estimation
                        for root, dirs, files in os.walk(path):
                            for file in files:
                                file_path = pathlib.Path(root) / file
                                try:
                                    if file_path.is_file():
                                        total_size += file_path.stat().st_size
                                        file_count += 1
                                except (OSError, FileNotFoundError):
                                    continue
                    except (OSError, FileNotFoundError):
                        continue
        except Exception:
            # Fallback to basic info
            file_count = len(self.source_paths)
            preview_text += "Size: Calculating...\n"
        else:
            preview_text += f"Files: {file_count}\n"
            preview_text += f"Total Size: {self._format_size(total_size)}\n"
        
        if self.encryption_group.isChecked():
            preview_text += "Encryption: AES-256 enabled\n"
        
        if self.split_group.isChecked():
            split_size_mb = self.split_size_spin.value()
            split_size_bytes = split_size_mb * 1024 * 1024
            parts = max(1, (total_size + split_size_bytes - 1) // split_size_bytes)
            preview_text += f"Split into: {parts} parts ({split_size_mb}MB each)"
        
        self.preview_text.setPlainText(preview_text)
    
    def _format_size(self, size_bytes: int) -> str:
        """Format file size in human readable format."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} PB"
    
    def _start_compression(self):
        if not self.source_paths:
            QMessageBox.warning(self, "Warning", "Please select files to compress")
            return
        
        archive_name = self.archive_name_edit.text().strip()
        if not archive_name:
            QMessageBox.warning(self, "Warning", "Please enter an archive name")
            return
        
        location = pathlib.Path(self.location_edit.text())
        if not location.exists():
            try:
                location.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Cannot create directory: {e}")
                return
        
        format_type = self.format_combo.currentData()
        compression_level = self.level_combo.currentText()
        
        split_size = None
        if self.split_group.isChecked():
            split_size = self.split_size_spin.value() * 1024 * 1024
        
        encrypt = self.encryption_group.isChecked()
        password = None
        
        if encrypt:
            password_dialog = PasswordDialog(self, "encrypt", archive_name)
            if password_dialog.exec() == QDialog.Accepted:
                password = password_dialog.get_password()
                if password_dialog.should_store_password():
                    # Store password for this archive
                    from ui.password_dialog import PasswordManager
                    manager = PasswordManager()
                    manager.store_password(archive_name, password)
            else:
                return  # User cancelled
        
        archive_path = location / archive_name
        
        # Disable UI during compression
        self.compress_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        
        # Start compression worker
        self.worker = CompressionWorker(
            self.compression_engine,
            self.source_paths,
            archive_path,
            format_type,
            compression_level,
            split_size,
            encrypt,
            password
        )
        
        self.worker.progress_updated.connect(self._on_progress)
        self.worker.finished.connect(self._on_finished)
        self.worker.error_occurred.connect(self._on_error)
        
        self.worker.start()
    
    def _on_progress(self, value, message):
        self.progress_bar.setValue(value)
        self.progress_bar.setFormat(message)
    
    def _on_finished(self, created_files):
        self.created_files = created_files
        self.progress_bar.setVisible(False)
        self.compress_btn.setEnabled(True)
        
        file_list = "\n".join(str(f) for f in created_files)
        QMessageBox.information(
            self, "Compression Complete", 
            f"Archive created successfully:\n\n{file_list}"
        )
        self.accept()
    
    def _on_error(self, error_message):
        self.progress_bar.setVisible(False)
        self.compress_btn.setEnabled(True)
        QMessageBox.critical(self, "Compression Error", f"Error creating archive: {error_message}")