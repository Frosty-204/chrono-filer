# src/settings_dialog.py
import pathlib
import os
from typing import Dict, Any, Optional
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QLabel, QLineEdit, QPushButton, QSpinBox, QDoubleSpinBox,
    QComboBox, QCheckBox, QGroupBox, QFormLayout, QGridLayout,
    QFileDialog, QColorDialog, QFontDialog, QSlider, QTextEdit,
    QSpacerItem, QSizePolicy, QMessageBox, QDialogButtonBox,
    QFrame, QScrollArea
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont

class SettingsDialog(QDialog):
    settings_changed = Signal(dict)  # Emitted when settings are applied

    def __init__(self, current_settings: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.current_settings = current_settings.copy()
        self.temp_settings = current_settings.copy()  # Working copy

        self.setWindowTitle("Chrono Filer Settings")
        self.setModal(True)
        self.setMinimumSize(600, 500)
        self.resize(700, 600)

        self._create_ui()
        self._load_current_settings()
        self._connect_signals()

    def _create_ui(self):
        """Create the main UI layout."""
        layout = QVBoxLayout(self)

        # Create tab widget for different setting categories
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)

        # Create different settings tabs
        self._create_organization_tab()
        self._create_preview_tab()
        self._create_ui_tab()
        self._create_advanced_tab()
        self._create_permissions_tab()
        self._create_encryption_tab()

        # Create button box
        button_layout = QHBoxLayout()

        # Reset to defaults button
        self.reset_button = QPushButton("Reset to Defaults")
        self.reset_button.clicked.connect(self._reset_to_defaults)
        button_layout.addWidget(self.reset_button)

        button_layout.addStretch()

        # Standard dialog buttons
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel |
            QDialogButtonBox.StandardButton.Apply
        )
        button_layout.addWidget(self.button_box)

        layout.addLayout(button_layout)

    def _create_organization_tab(self):
        """Create the Organization settings tab."""
        tab_widget = QWidget()
        layout = QVBoxLayout(tab_widget)

        # Default Organization Settings
        org_group = QGroupBox("Default Organization Settings")
        org_layout = QFormLayout(org_group)

        # Default structure template
        self.default_structure_edit = QLineEdit()
        self.default_structure_edit.setPlaceholderText("[YYYY]/[MM]/[Filename].[Ext]")
        org_layout.addRow("Default Structure Template:", self.default_structure_edit)

        # Default conflict resolution
        self.default_conflict_combo = QComboBox()
        self.default_conflict_combo.addItems(["Skip", "Overwrite", "Rename with Suffix"])
        org_layout.addRow("Default Conflict Resolution:", self.default_conflict_combo)

        # Default operation type
        self.default_operation_combo = QComboBox()
        self.default_operation_combo.addItems(["Move", "Copy"])
        org_layout.addRow("Default Operation Type:", self.default_operation_combo)

        # Default dry run
        self.default_dry_run_check = QCheckBox("Enable dry run by default")
        org_layout.addRow(self.default_dry_run_check)

        layout.addWidget(org_group)

        # Date Format Settings
        date_group = QGroupBox("Date Format Settings")
        date_layout = QFormLayout(date_group)

        # Date format for organization
        self.date_format_combo = QComboBox()
        self.date_format_combo.addItems([
            "YYYY/MM/DD", "YYYY-MM-DD", "DD/MM/YYYY", "DD-MM-YYYY",
            "MM/DD/YYYY", "MM-DD-YYYY", "YYYY/MM", "YYYY-MM"
        ])
        date_layout.addRow("Date Format for Organization:", self.date_format_combo)

        # Custom date format
        self.custom_date_edit = QLineEdit()
        self.custom_date_edit.setPlaceholderText("e.g., %Y-%m-%d")
        date_layout.addRow("Custom Date Format:", self.custom_date_edit)

        layout.addWidget(date_group)

        # Filtering Defaults
        filter_group = QGroupBox("Default Filter Settings")
        filter_layout = QFormLayout(filter_group)

        # Default name filter type
        self.default_name_filter_combo = QComboBox()
        self.default_name_filter_combo.addItems(["Contains", "Starts with", "Ends with", "Exact match", "Regex"])
        filter_layout.addRow("Default Name Filter Type:", self.default_name_filter_combo)

        # Default size limits
        self.default_size_min_spin = QSpinBox()
        self.default_size_min_spin.setRange(0, 1024*1024)
        self.default_size_min_spin.setSuffix(" KB")
        filter_layout.addRow("Default Min Size:", self.default_size_min_spin)

        self.default_size_max_spin = QSpinBox()
        self.default_size_max_spin.setRange(0, 1024*1024)
        self.default_size_max_spin.setValue(1024*1024)
        self.default_size_max_spin.setSuffix(" KB")
        filter_layout.addRow("Default Max Size:", self.default_size_max_spin)

        layout.addWidget(filter_group)

        layout.addStretch()
        self.tab_widget.addTab(tab_widget, "Organization")

    def _create_preview_tab(self):
        """Create the Preview settings tab."""
        tab_widget = QWidget()
        layout = QVBoxLayout(tab_widget)

        # Image Preview Settings
        image_group = QGroupBox("Image Preview Settings")
        image_layout = QFormLayout(image_group)

        # Default zoom behavior
        self.default_zoom_combo = QComboBox()
        self.default_zoom_combo.addItems(["Fit to Window", "Actual Size", "Custom Scale"])
        image_layout.addRow("Default Zoom Behavior:", self.default_zoom_combo)

        # Custom zoom scale
        self.custom_zoom_spin = QDoubleSpinBox()
        self.custom_zoom_spin.setRange(0.1, 10.0)
        self.custom_zoom_spin.setValue(1.0)
        self.custom_zoom_spin.setSingleStep(0.1)
        self.custom_zoom_spin.setSuffix("x")
        image_layout.addRow("Custom Zoom Scale:", self.custom_zoom_spin)

        layout.addWidget(image_group)

        # Text Preview Settings
        text_group = QGroupBox("Text Preview Settings")
        text_layout = QFormLayout(text_group)

        # Show line numbers by default
        self.show_line_numbers_check = QCheckBox("Show line numbers by default")
        text_layout.addRow(self.show_line_numbers_check)

        # Word wrap by default
        self.word_wrap_check = QCheckBox("Enable word wrap by default")
        text_layout.addRow(self.word_wrap_check)

        # Tab width
        self.tab_width_spin = QSpinBox()
        self.tab_width_spin.setRange(1, 16)
        self.tab_width_spin.setValue(4)
        text_layout.addRow("Tab Width:", self.tab_width_spin)

        # Max preview size
        self.max_preview_spin = QSpinBox()
        self.max_preview_spin.setRange(1, 100)
        self.max_preview_spin.setValue(1)
        self.max_preview_spin.setSuffix(" MB")
        text_layout.addRow("Max Preview Size:", self.max_preview_spin)

        layout.addWidget(text_group)

        # Syntax Highlighting Settings
        syntax_group = QGroupBox("Syntax Highlighting Settings")
        syntax_layout = QFormLayout(syntax_group)

        # Enable syntax highlighting
        self.enable_syntax_check = QCheckBox("Enable syntax highlighting")
        syntax_layout.addRow(self.enable_syntax_check)

        # Syntax highlighting theme
        self.syntax_theme_combo = QComboBox()
        self.syntax_theme_combo.addItems(["Default", "Dark", "Light", "Colorful"])
        syntax_layout.addRow("Syntax Theme:", self.syntax_theme_combo)

        layout.addWidget(syntax_group)

        layout.addStretch()
        self.tab_widget.addTab(tab_widget, "Preview")

    def _create_ui_tab(self):
        """Create the UI settings tab."""
        tab_widget = QWidget()
        layout = QVBoxLayout(tab_widget)

        # Window Settings
        window_group = QGroupBox("Window Settings")
        window_layout = QFormLayout(window_group)

        # Remember window geometry
        self.remember_geometry_check = QCheckBox("Remember window size and position")
        window_layout.addRow(self.remember_geometry_check)

        # Default window size
        window_size_layout = QHBoxLayout()
        self.default_width_spin = QSpinBox()
        self.default_width_spin.setRange(800, 3840)
        self.default_width_spin.setValue(1280)
        self.default_height_spin = QSpinBox()
        self.default_height_spin.setRange(600, 2160)
        self.default_height_spin.setValue(800)
        window_size_layout.addWidget(QLabel("Width:"))
        window_size_layout.addWidget(self.default_width_spin)
        window_size_layout.addWidget(QLabel("Height:"))
        window_size_layout.addWidget(self.default_height_spin)
        window_layout.addRow("Default Window Size:", window_size_layout)

        # Splitter proportions
        splitter_layout = QHBoxLayout()
        self.left_panel_spin = QSpinBox()
        self.left_panel_spin.setRange(10, 80)
        self.left_panel_spin.setValue(30)
        self.left_panel_spin.setSuffix("%")
        self.right_panel_spin = QSpinBox()
        self.right_panel_spin.setRange(20, 90)
        self.right_panel_spin.setValue(70)
        self.right_panel_spin.setSuffix("%")
        splitter_layout.addWidget(QLabel("Left Panel:"))
        splitter_layout.addWidget(self.left_panel_spin)
        splitter_layout.addWidget(QLabel("Right Panel:"))
        splitter_layout.addWidget(self.right_panel_spin)
        window_layout.addRow("Panel Proportions:", splitter_layout)

        layout.addWidget(window_group)

        # Appearance Settings
        appearance_group = QGroupBox("Appearance Settings")
        appearance_layout = QFormLayout(appearance_group)

        # Theme
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["System Default", "Material Design", "Material Dark", "High Contrast"])
        appearance_layout.addRow("Theme:", self.theme_combo)

        # Icon size
        self.icon_size_combo = QComboBox()
        self.icon_size_combo.addItems(["Small (16px)", "Medium (24px)", "Large (32px)"])
        appearance_layout.addRow("Icon Size:", self.icon_size_combo)

        # Show file extensions
        self.show_extensions_check = QCheckBox("Always show file extensions")
        appearance_layout.addRow(self.show_extensions_check)

        # Show hidden files
        self.show_hidden_check = QCheckBox("Show hidden files by default")
        appearance_layout.addRow(self.show_hidden_check)

        layout.addWidget(appearance_group)

        # Behavior Settings
        behavior_group = QGroupBox("Behavior Settings")
        behavior_layout = QFormLayout(behavior_group)

        # Confirm destructive actions
        self.confirm_delete_check = QCheckBox("Confirm before deleting files")
        behavior_layout.addRow(self.confirm_delete_check)

        # Auto-refresh
        self.auto_refresh_check = QCheckBox("Auto-refresh file lists")
        behavior_layout.addRow(self.auto_refresh_check)

        # Double-click behavior
        self.double_click_combo = QComboBox()
        self.double_click_combo.addItems(["Navigate (folders) / Preview (files)", "Open with default application"])
        behavior_layout.addRow("Double-click behavior:", self.double_click_combo)

        layout.addWidget(behavior_group)

        layout.addStretch()
        self.tab_widget.addTab(tab_widget, "UI & Behavior")

    def _create_advanced_tab(self):
        """Create the Advanced settings tab."""
        tab_widget = QWidget()
        layout = QVBoxLayout(tab_widget)

        # Performance Settings
        performance_group = QGroupBox("Performance Settings")
        performance_layout = QFormLayout(performance_group)

        # Undo history size
        self.undo_history_spin = QSpinBox()
        self.undo_history_spin.setRange(10, 1000)
        self.undo_history_spin.setValue(50)
        performance_layout.addRow("Undo History Size:", self.undo_history_spin)

        # File scanning limits
        self.max_files_spin = QSpinBox()
        self.max_files_spin.setRange(1000, 100000)
        self.max_files_spin.setValue(10000)
        performance_layout.addRow("Max Files to Scan:", self.max_files_spin)

        # Thumbnail cache size
        self.cache_size_spin = QSpinBox()
        self.cache_size_spin.setRange(10, 1000)
        self.cache_size_spin.setValue(100)
        self.cache_size_spin.setSuffix(" MB")
        performance_layout.addRow("Thumbnail Cache Size:", self.cache_size_spin)

        layout.addWidget(performance_group)

        # File Type Associations
        associations_group = QGroupBox("File Type Associations")
        associations_layout = QVBoxLayout(associations_group)

        # Create a scrollable text area for file associations
        self.file_associations_text = QTextEdit()
        self.file_associations_text.setMaximumHeight(150)
        self.file_associations_text.setPlainText(
            "# File type associations (one per line)\n"
            "# Format: extension=preview_type\n"
            ".py=text\n"
            ".js=text\n"
            ".json=text\n"
            ".md=text\n"
            ".txt=text\n"
            ".jpg=image\n"
            ".png=image\n"
            ".gif=image\n"
        )
        associations_layout.addWidget(QLabel("File Type Associations:"))
        associations_layout.addWidget(self.file_associations_text)

        layout.addWidget(associations_group)

        # Backup and Reset
        backup_group = QGroupBox("Backup and Reset")
        backup_layout = QFormLayout(backup_group)

        # Export settings
        self.export_button = QPushButton("Export Settings...")
        self.export_button.clicked.connect(self._export_settings)
        backup_layout.addRow("Export Settings:", self.export_button)

        # Import settings
        self.import_button = QPushButton("Import Settings...")
        self.import_button.clicked.connect(self._import_settings)
        backup_layout.addRow("Import Settings:", self.import_button)

        # Reset all settings
        self.reset_all_button = QPushButton("Reset All Settings")
        self.reset_all_button.clicked.connect(self._reset_all_settings)
        backup_layout.addRow("Reset All:", self.reset_all_button)

        layout.addWidget(backup_group)

        layout.addStretch()
        self.tab_widget.addTab(tab_widget, "Advanced")

    def _create_permissions_tab(self):
        """Create the Permissions settings tab."""
        tab_widget = QWidget()
        layout = QVBoxLayout(tab_widget)

        # Encryption Settings
        encryption_group = QGroupBox("Encryption Settings")
        encryption_layout = QFormLayout(encryption_group)

        # Enable encryption
        self.encryption_enabled_check = QCheckBox("Enable file encryption features")
        self.encryption_enabled_check.setToolTip("Allow encryption of files and archives")
        encryption_layout.addRow(self.encryption_enabled_check)

        # Default encryption algorithm
        self.encryption_algorithm_combo = QComboBox()
        self.encryption_algorithm_combo.addItems(["AES-256-CBC", "AES-256-GCM"])
        self.encryption_algorithm_combo.setToolTip("Default encryption algorithm for new operations")
        encryption_layout.addRow("Default Algorithm:", self.encryption_algorithm_combo)

        # Key derivation iterations
        self.key_iterations_spin = QSpinBox()
        self.key_iterations_spin.setRange(10000, 1000000)
        self.key_iterations_spin.setValue(100000)
        self.key_iterations_spin.setSingleStep(10000)
        encryption_layout.addRow("Key Derivation Iterations:", self.key_iterations_spin)

        # Store passwords in keyring
        self.store_passwords_check = QCheckBox("Store passwords in system keyring")
        self.store_passwords_check.setToolTip("Remember passwords securely using system keyring")
        encryption_layout.addRow(self.store_passwords_check)

        # Auto-verify encrypted files
        self.auto_verify_check = QCheckBox("Auto-verify encrypted files after creation")
        encryption_layout.addRow(self.auto_verify_check)

        layout.addWidget(encryption_group)

        # Permissions Settings
        permissions_group = QGroupBox("POSIX Permissions")
        permissions_layout = QFormLayout(permissions_group)

        # Enable permissions
        self.permissions_enabled_check = QCheckBox("Enable POSIX permissions management")
        self.permissions_enabled_check.setToolTip("Apply custom permissions to files during organization")
        permissions_layout.addRow(self.permissions_enabled_check)

        # Permission Presets
        preset_group = QGroupBox("Permission Presets")
        preset_layout = QFormLayout(preset_group)

        self.preset_combo = QComboBox()
        self.preset_combo.addItems([
            "Secure (Private)",
            "Standard (Recommended)",
            "Shared (Group Access)",
            "Public (Open)",
            "Custom"
        ])
        self.preset_combo.setToolTip("Choose from predefined permission sets or create custom permissions")
        preset_layout.addRow("Permission Preset:", self.preset_combo)

        # Directory permissions
        self.directory_permissions_spin = QSpinBox()
        self.directory_permissions_spin.setRange(0o000, 0o777)
        self.directory_permissions_spin.setDisplayIntegerBase(8)
        self.directory_permissions_spin.setPrefix("0o")
        self.directory_permissions_spin.setToolTip("Default permissions for newly created directories")
        preset_layout.addRow("Directory Permissions:", self.directory_permissions_spin)

        # File type permissions
        file_types_group = QGroupBox("File Type Permissions")
        file_types_layout = QFormLayout(file_types_group)

        self.image_permissions_spin = QSpinBox()
        self.image_permissions_spin.setRange(0o000, 0o777)
        self.image_permissions_spin.setDisplayIntegerBase(8)
        self.image_permissions_spin.setPrefix("0o")
        
        self.text_permissions_spin = QSpinBox()
        self.text_permissions_spin.setRange(0o000, 0o777)
        self.text_permissions_spin.setDisplayIntegerBase(8)
        self.text_permissions_spin.setPrefix("0o")
        
        self.document_permissions_spin = QSpinBox()
        self.document_permissions_spin.setRange(0o000, 0o777)
        self.document_permissions_spin.setDisplayIntegerBase(8)
        self.document_permissions_spin.setPrefix("0o")
        
        self.archive_permissions_spin = QSpinBox()
        self.archive_permissions_spin.setRange(0o000, 0o777)
        self.archive_permissions_spin.setDisplayIntegerBase(8)
        self.archive_permissions_spin.setPrefix("0o")
        
        self.executable_permissions_spin = QSpinBox()
        self.executable_permissions_spin.setRange(0o000, 0o777)
        self.executable_permissions_spin.setDisplayIntegerBase(8)
        self.executable_permissions_spin.setPrefix("0o")
        
        self.video_permissions_spin = QSpinBox()
        self.video_permissions_spin.setRange(0o000, 0o777)
        self.video_permissions_spin.setDisplayIntegerBase(8)
        self.video_permissions_spin.setPrefix("0o")
        
        self.audio_permissions_spin = QSpinBox()
        self.audio_permissions_spin.setRange(0o000, 0o777)
        self.audio_permissions_spin.setDisplayIntegerBase(8)
        self.audio_permissions_spin.setPrefix("0o")
        
        self.default_permissions_spin = QSpinBox()
        self.default_permissions_spin.setRange(0o000, 0o777)
        self.default_permissions_spin.setDisplayIntegerBase(8)
        self.default_permissions_spin.setPrefix("0o")

        file_types_layout.addRow("Images:", self.image_permissions_spin)
        file_types_layout.addRow("Text Files:", self.text_permissions_spin)
        file_types_layout.addRow("Documents:", self.document_permissions_spin)
        file_types_layout.addRow("Archives:", self.archive_permissions_spin)
        file_types_layout.addRow("Executables:", self.executable_permissions_spin)
        file_types_layout.addRow("Videos:", self.video_permissions_spin)
        file_types_layout.addRow("Audio:", self.audio_permissions_spin)
        file_types_layout.addRow("Other Files:", self.default_permissions_spin)

        # Recursive permissions
        self.recursive_permissions_check = QCheckBox("Apply permissions recursively to directories")
        self.recursive_permissions_check.setToolTip("When enabled, permissions will be applied to all files within directories")
        file_types_layout.addRow(self.recursive_permissions_check)

        # Reset button
        reset_button = QPushButton("Reset to Preset Defaults")
        reset_button.clicked.connect(self._reset_permissions_to_preset)
        preset_layout.addRow(reset_button)

        layout.addWidget(permissions_group)
        layout.addWidget(preset_group)
        layout.addWidget(file_types_group)
        layout.addStretch()
        self.tab_widget.addTab(tab_widget, "Permissions")

    def _connect_signals(self):
        """Connect all signals."""
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.button_box.button(QDialogButtonBox.StandardButton.Apply).clicked.connect(self._apply_settings)

        # Connect value change signals to update temp settings
        self._connect_value_changes()

        # Apply default template when structure template changes
        self._update_organization_defaults()

    def _connect_value_changes(self):
        """Connect all input widgets to update temp settings."""
        # Organization tab
        self.default_structure_edit.textChanged.connect(
            lambda: self._update_temp_setting("default_structure_template", self.default_structure_edit.text())
        )
        self.default_conflict_combo.currentTextChanged.connect(
            lambda: self._update_temp_setting("default_conflict_resolution", self.default_conflict_combo.currentText())
        )
        self.default_operation_combo.currentTextChanged.connect(
            lambda: self._update_temp_setting("default_operation_type", self.default_operation_combo.currentText())
        )
        self.default_dry_run_check.toggled.connect(
            lambda: self._update_temp_setting("default_dry_run", self.default_dry_run_check.isChecked())
        )

        # Date format connections
        self.date_format_combo.currentTextChanged.connect(
            lambda: self._update_temp_setting("date_format", self.date_format_combo.currentText())
        )
        self.custom_date_edit.textChanged.connect(
            lambda: self._update_temp_setting("custom_date_format", self.custom_date_edit.text())
        )

        # Filter default connections
        self.default_name_filter_combo.currentTextChanged.connect(
            lambda: self._update_temp_setting("default_name_filter_type", self.default_name_filter_combo.currentText())
        )
        self.default_size_min_spin.valueChanged.connect(
            lambda: self._update_temp_setting("default_size_min_kb", self.default_size_min_spin.value())
        )
        self.default_size_max_spin.valueChanged.connect(
            lambda: self._update_temp_setting("default_size_max_kb", self.default_size_max_spin.value())
        )

        # Preview tab
        self.default_zoom_combo.currentTextChanged.connect(
            lambda: self._update_temp_setting("default_zoom_behavior", self.default_zoom_combo.currentText())
        )
        self.show_line_numbers_check.toggled.connect(
            lambda: self._update_temp_setting("show_line_numbers_default", self.show_line_numbers_check.isChecked())
        )
        self.word_wrap_check.toggled.connect(
            lambda: self._update_temp_setting("word_wrap_default", self.word_wrap_check.isChecked())
        )

        # Text preview connections
        self.tab_width_spin.valueChanged.connect(
            lambda: self._update_temp_setting("tab_width", self.tab_width_spin.value())
        )
        self.max_preview_spin.valueChanged.connect(
            lambda: self._update_temp_setting("max_preview_size_mb", self.max_preview_spin.value())
        )

        # Image preview connections
        self.custom_zoom_spin.valueChanged.connect(
            lambda: self._update_temp_setting("custom_zoom_scale", self.custom_zoom_spin.value())
        )

        # UI tab
        self.remember_geometry_check.toggled.connect(
            lambda: self._update_temp_setting("remember_window_geometry", self.remember_geometry_check.isChecked())
        )
        self.theme_combo.currentTextChanged.connect(
            lambda: self._update_temp_setting("theme", self.theme_combo.currentText())
        )
        self.confirm_delete_check.toggled.connect(
            lambda: self._update_temp_setting("confirm_delete", self.confirm_delete_check.isChecked())
        )

        # UI behavior connections
        self.default_width_spin.valueChanged.connect(
            lambda: self._update_temp_setting("default_window_width", self.default_width_spin.value())
        )
        self.default_height_spin.valueChanged.connect(
            lambda: self._update_temp_setting("default_window_height", self.default_height_spin.value())
        )
        self.show_extensions_check.toggled.connect(
            lambda: self._update_temp_setting("show_file_extensions", self.show_extensions_check.isChecked())
        )
        self.show_hidden_check.toggled.connect(
            lambda: self._update_temp_setting("show_hidden_files", self.show_hidden_check.isChecked())
        )

        # Advanced connections
        self.undo_history_spin.valueChanged.connect(
            lambda: self._update_temp_setting("undo_history_size", self.undo_history_spin.value())
        )

        # Permissions connections
        self.permissions_enabled_check.toggled.connect(
            lambda: self._update_temp_setting("permissions_enabled", self.permissions_enabled_check.isChecked())
        )
        self.directory_permissions_spin.valueChanged.connect(
            lambda: self._update_temp_setting("directory_permissions", self.directory_permissions_spin.value())
        )
        self.image_permissions_spin.valueChanged.connect(
            lambda: self._update_temp_setting("image_permissions", self.image_permissions_spin.value())
        )
        self.text_permissions_spin.valueChanged.connect(
            lambda: self._update_temp_setting("text_permissions", self.text_permissions_spin.value())
        )
        self.document_permissions_spin.valueChanged.connect(
            lambda: self._update_temp_setting("document_permissions", self.document_permissions_spin.value())
        )
        self.archive_permissions_spin.valueChanged.connect(
            lambda: self._update_temp_setting("archive_permissions", self.archive_permissions_spin.value())
        )
        self.executable_permissions_spin.valueChanged.connect(
            lambda: self._update_temp_setting("executable_permissions", self.executable_permissions_spin.value())
        )
        self.video_permissions_spin.valueChanged.connect(
            lambda: self._update_temp_setting("video_permissions", self.video_permissions_spin.value())
        )
        self.audio_permissions_spin.valueChanged.connect(
            lambda: self._update_temp_setting("audio_permissions", self.audio_permissions_spin.value())
        )
        self.default_permissions_spin.valueChanged.connect(
            lambda: self._update_temp_setting("default_permissions", self.default_permissions_spin.value())
        )
        self.recursive_permissions_check.toggled.connect(
            lambda: self._update_temp_setting("recursive_permissions", self.recursive_permissions_check.isChecked())
        )
        self.preset_combo.currentTextChanged.connect(self._on_preset_changed)
        self.preset_combo.currentTextChanged.connect(
            lambda text: self._update_temp_setting("permissions_preset", text)
        )

        # Encryption settings connections
        self.encryption_enabled_check.toggled.connect(
            lambda: self._update_temp_setting("encryption_enabled", self.encryption_enabled_check.isChecked())
        )
        self.encryption_algorithm_combo.currentTextChanged.connect(
            lambda: self._update_temp_setting("encryption_algorithm", self.encryption_algorithm_combo.currentText())
        )
        self.key_iterations_spin.valueChanged.connect(
            lambda: self._update_temp_setting("key_iterations", self.key_iterations_spin.value())
        )
        self.store_passwords_check.toggled.connect(
            lambda: self._update_temp_setting("store_passwords", self.store_passwords_check.isChecked())
        )
        self.auto_verify_check.toggled.connect(
            lambda: self._update_temp_setting("auto_verify_encrypted", self.auto_verify_check.isChecked())
        )

    def _update_temp_setting(self, key: str, value: Any):
        """Update temporary settings dictionary."""
        self.temp_settings[key] = value

    def _update_organization_defaults(self):
        """Update organization panel with default template when settings change."""
        pass  # This will be connected to the main app to update defaults

    def _load_current_settings(self):
        """Load current settings into the UI."""
        # Organization settings
        self.default_structure_edit.setText(
            self.current_settings.get("default_structure_template", "[YYYY]/[MM]/[Filename].[Ext]")
        )
        self.default_conflict_combo.setCurrentText(
            self.current_settings.get("default_conflict_resolution", "Skip")
        )
        self.default_operation_combo.setCurrentText(
            self.current_settings.get("default_operation_type", "Move")
        )
        self.default_dry_run_check.setChecked(
            self.current_settings.get("default_dry_run", True)
        )

        # Preview settings
        self.default_zoom_combo.setCurrentText(
            self.current_settings.get("default_zoom_behavior", "Fit to Window")
        )
        self.show_line_numbers_check.setChecked(
            self.current_settings.get("show_line_numbers_default", True)
        )
        self.word_wrap_check.setChecked(
            self.current_settings.get("word_wrap_default", True)
        )

        # UI settings
        self.remember_geometry_check.setChecked(
            self.current_settings.get("remember_window_geometry", True)
        )
        self.theme_combo.setCurrentText(
            self.current_settings.get("theme", "Material Design")
        )
        self.confirm_delete_check.setChecked(
            self.current_settings.get("confirm_delete", True)
        )

        # Advanced settings
        self.undo_history_spin.setValue(
            self.current_settings.get("undo_history_size", 50)
        )

        # Load additional settings
        self.date_format_combo.setCurrentText(
            self.current_settings.get("date_format", "YYYY/MM/DD")
        )
        self.custom_date_edit.setText(
            self.current_settings.get("custom_date_format", "")
        )

        # Filter defaults
        self.default_name_filter_combo.setCurrentText(
            self.current_settings.get("default_name_filter_type", "Contains")
        )
        self.default_size_min_spin.setValue(
            self.current_settings.get("default_size_min_kb", 0)
        )
        self.default_size_max_spin.setValue(
            self.current_settings.get("default_size_max_kb", 1048576)
        )

        # Text preview settings
        self.tab_width_spin.setValue(
            self.current_settings.get("tab_width", 4)
        )
        self.max_preview_spin.setValue(
            self.current_settings.get("max_preview_size_mb", 1)
        )

        # Image preview settings
        self.custom_zoom_spin.setValue(
            self.current_settings.get("custom_zoom_scale", 1.0)
        )

        # UI settings
        self.default_width_spin.setValue(
            self.current_settings.get("default_window_width", 1280)
        )
        self.default_height_spin.setValue(
            self.current_settings.get("default_window_height", 800)
        )
        self.show_extensions_check.setChecked(
            self.current_settings.get("show_file_extensions", True)
        )
        self.show_hidden_check.setChecked(
            self.current_settings.get("show_hidden_files", False)
        )

        # Permissions settings
        self.permissions_enabled_check.setChecked(
            self.current_settings.get("permissions_enabled", False)
        )
        self.directory_permissions_spin.setValue(
            self.current_settings.get("directory_permissions", 0o755)
        )
        self.image_permissions_spin.setValue(
            self.current_settings.get("image_permissions", 0o644)
        )
        self.text_permissions_spin.setValue(
            self.current_settings.get("text_permissions", 0o644)
        )
        self.document_permissions_spin.setValue(
            self.current_settings.get("document_permissions", 0o644)
        )
        self.archive_permissions_spin.setValue(
            self.current_settings.get("archive_permissions", 0o644)
        )
        self.executable_permissions_spin.setValue(
            self.current_settings.get("executable_permissions", 0o755)
        )
        self.video_permissions_spin.setValue(
            self.current_settings.get("video_permissions", 0o644)
        )
        self.audio_permissions_spin.setValue(
            self.current_settings.get("audio_permissions", 0o644)
        )
        self.default_permissions_spin.setValue(
            self.current_settings.get("default_permissions", 0o644)
        )
        self.recursive_permissions_check.setChecked(
            self.current_settings.get("recursive_permissions", True)
        )
        
        # Load preset
        preset = self.current_settings.get("permissions_preset", "Standard (Recommended)")
        self.preset_combo.setCurrentText(preset)
        if preset != "Custom":
            self._on_preset_changed(preset)

        # Encryption settings
        self.encryption_enabled_check.setChecked(
            self.current_settings.get("encryption_enabled", True)
        )
        self.encryption_algorithm_combo.setCurrentText(
            self.current_settings.get("encryption_algorithm", "AES-256-CBC")
        )
        self.key_iterations_spin.setValue(
            self.current_settings.get("key_iterations", 100000)
        )
        self.store_passwords_check.setChecked(
            self.current_settings.get("store_passwords", True)
        )
        self.auto_verify_check.setChecked(
            self.current_settings.get("auto_verify_encrypted", True)
        )

    def get_current_template(self):
        """Get the currently set structure template."""
        return self.default_structure_edit.text() or "[YYYY]/[MM]/[Filename].[Ext]"

    def set_template(self, template: str):
        """Set the structure template."""
        self.default_structure_edit.setText(template)
        self._update_temp_setting("default_structure_template", template)

    def _export_settings(self):
        """Export current settings to file."""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Settings", "chrono_filer_settings.json", "JSON Files (*.json)"
        )
        if file_path:
            try:
                import json
                with open(file_path, 'w') as f:
                    json.dump(self.current_settings, f, indent=4)
                QMessageBox.information(self, "Success", "Settings exported successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export settings: {e}")

    def _import_settings(self):
        """Import settings from file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Import Settings", "", "JSON Files (*.json)"
        )
        if file_path:
            try:
                import json
                with open(file_path, 'r') as f:
                    imported_settings = json.load(f)

                # Merge imported settings with current settings
                self.temp_settings.update(imported_settings)
                self._load_current_settings()
                QMessageBox.information(self, "Success", "Settings imported successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to import settings: {e}")

    def _reset_to_defaults(self):
        """Reset current tab to default values."""
        reply = QMessageBox.question(
            self, "Reset to Defaults",
            "Reset all settings in the current tab to their default values?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            current_tab = self.tab_widget.currentIndex()
            if current_tab == 0:  # Organization tab
                self.default_structure_edit.setText("[YYYY]/[MM]/[Filename].[Ext]")
                self.default_conflict_combo.setCurrentText("Skip")
                self.default_operation_combo.setCurrentText("Move")
                self.default_dry_run_check.setChecked(True)
            elif current_tab == 1:  # Preview tab
                self.default_zoom_combo.setCurrentText("Fit to Window")
                self.show_line_numbers_check.setChecked(True)
                self.word_wrap_check.setChecked(True)
                self.tab_width_spin.setValue(4)
                self.max_preview_spin.setValue(1)
            elif current_tab == 2:  # UI tab
                self.remember_geometry_check.setChecked(True)
                self.theme_combo.setCurrentText("System Default")
                self.confirm_delete_check.setChecked(True)
                self.default_width_spin.setValue(1280)
                self.default_height_spin.setValue(800)
                self.show_extensions_check.setChecked(True)
                self.show_hidden_check.setChecked(False)
            elif current_tab == 3:  # Advanced tab
                self.undo_history_spin.setValue(50)

    def _reset_all_settings(self):
        """Reset all settings to defaults."""
        reply = QMessageBox.question(
            self, "Reset All Settings",
            "This will reset ALL settings to their default values. Are you sure?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.temp_settings.clear()
            self._load_current_settings()

    def _on_preset_changed(self, preset_name):
        """Handle preset selection changes."""
        if preset_name == "Custom":
            return  # Allow manual editing
        
        # Define preset values
        presets = {
            "Secure (Private)": {
                "directory_permissions": 0o700,
                "image_permissions": 0o600,
                "text_permissions": 0o600,
                "document_permissions": 0o600,
                "archive_permissions": 0o600,
                "executable_permissions": 0o700,
                "video_permissions": 0o600,
                "audio_permissions": 0o600,
                "default_permissions": 0o600
            },
            "Standard (Recommended)": {
                "directory_permissions": 0o755,
                "image_permissions": 0o644,
                "text_permissions": 0o644,
                "document_permissions": 0o644,
                "archive_permissions": 0o644,
                "executable_permissions": 0o755,
                "video_permissions": 0o644,
                "audio_permissions": 0o644,
                "default_permissions": 0o644
            },
            "Shared (Group Access)": {
                "directory_permissions": 0o775,
                "image_permissions": 0o664,
                "text_permissions": 0o664,
                "document_permissions": 0o664,
                "archive_permissions": 0o664,
                "executable_permissions": 0o775,
                "video_permissions": 0o664,
                "audio_permissions": 0o664,
                "default_permissions": 0o664
            },
            "Public (Open)": {
                "directory_permissions": 0o777,
                "image_permissions": 0o666,
                "text_permissions": 0o666,
                "document_permissions": 0o666,
                "archive_permissions": 0o666,
                "executable_permissions": 0o777,
                "video_permissions": 0o666,
                "audio_permissions": 0o666,
                "default_permissions": 0o666
            }
        }
        
        if preset_name in presets:
            values = presets[preset_name]
            self.directory_permissions_spin.setValue(values["directory_permissions"])
            self.image_permissions_spin.setValue(values["image_permissions"])
            self.text_permissions_spin.setValue(values["text_permissions"])
            self.document_permissions_spin.setValue(values["document_permissions"])
            self.archive_permissions_spin.setValue(values["archive_permissions"])
            self.executable_permissions_spin.setValue(values["executable_permissions"])
            self.video_permissions_spin.setValue(values["video_permissions"])
            self.audio_permissions_spin.setValue(values["audio_permissions"])
            self.default_permissions_spin.setValue(values["default_permissions"])

    def _reset_permissions_to_preset(self):
        """Reset permissions to the current preset defaults."""
        current_preset = self.preset_combo.currentText()
        if current_preset != "Custom":
            self._on_preset_changed(current_preset)
        else:
            # Reset to Standard preset if Custom
            self.preset_combo.setCurrentText("Standard (Recommended)")
            self._on_preset_changed("Standard (Recommended)")

    def _create_encryption_tab(self):
        """Create the Encryption settings tab."""
        tab_widget = QWidget()
        layout = QVBoxLayout(tab_widget)

        # Encryption Settings Group
        encryption_group = QGroupBox("Encryption Settings")
        encryption_layout = QFormLayout(encryption_group)

        # Default encryption template
        self.default_encryption_template_combo = QComboBox()
        self.default_encryption_template_combo.addItems([
            "Secure Backup", "Daily Work", "Maximum Security", "Custom"
        ])
        encryption_layout.addRow("Default Encryption Template:", self.default_encryption_template_combo)

        # Default encryption mode
        self.default_encryption_mode_combo = QComboBox()
        self.default_encryption_mode_combo.addItems(["AES-256-CBC", "AES-256-GCM"])
        encryption_layout.addRow("Default Encryption Mode:", self.default_encryption_mode_combo)

        # Default key derivation iterations
        self.default_iterations_spinbox = QSpinBox()
        self.default_iterations_spinbox.setRange(10000, 1000000)
        self.default_iterations_spinbox.setSingleStep(10000)
        self.default_iterations_spinbox.setValue(100000)
        encryption_layout.addRow("Default Key Derivation Iterations:", self.default_iterations_spinbox)

        # Store password in keyring
        self.store_password_check = QCheckBox("Store passwords in system keyring")
        self.store_password_check.setChecked(True)
        encryption_layout.addRow(self.store_password_check)

        # Auto-verify encrypted files
        self.auto_verify_check = QCheckBox("Auto-verify encrypted files after creation")
        self.auto_verify_check.setChecked(True)
        encryption_layout.addRow(self.auto_verify_check)

        layout.addWidget(encryption_group)

        # Advanced Encryption Settings
        advanced_group = QGroupBox("Advanced Encryption Settings")
        advanced_layout = QFormLayout(advanced_group)

        # Salt length
        self.salt_length_spinbox = QSpinBox()
        self.salt_length_spinbox.setRange(16, 64)
        self.salt_length_spinbox.setValue(32)
        advanced_layout.addRow("Salt Length (bytes):", self.salt_length_spinbox)

        # Chunk size for large files
        self.chunk_size_spinbox = QSpinBox()
        self.chunk_size_spinbox.setRange(1024, 1024*1024)
        self.chunk_size_spinbox.setSingleStep(1024)
        self.chunk_size_spinbox.setValue(64*1024)
        advanced_layout.addRow("Chunk Size (bytes):", self.chunk_size_spinbox)

        layout.addWidget(advanced_group)

        # Encryption Templates Info
        info_group = QGroupBox("Encryption Templates")
        info_layout = QVBoxLayout(info_group)
        
        info_text = QTextEdit()
        info_text.setReadOnly(True)
        info_text.setPlainText(
            "Encryption Templates:\n\n"
            "• Secure Backup: AES-256-CBC, 100,000 iterations, keyring storage\n"
            "• Daily Work: AES-256-CBC, 50,000 iterations, keyring storage\n"
            "• Maximum Security: AES-256-GCM, 1,000,000 iterations, no keyring storage\n"
            "• Custom: User-defined settings\n\n"
            "AES-256-CBC: Good balance of security and performance\n"
            "AES-256-GCM: Authenticated encryption with integrity verification"
        )
        info_layout.addWidget(info_text)
        layout.addWidget(info_group)

        layout.addStretch()
        self.tab_widget.addTab(tab_widget, "Encryption")

    def _apply_settings(self):
        """Apply settings without closing dialog."""
        self.current_settings.update(self.temp_settings)
        self.settings_changed.emit(self.current_settings)
        QMessageBox.information(self, "Settings Applied", "Settings have been applied successfully!")

    def accept(self):
        """Accept dialog and apply settings."""
        self.current_settings.update(self.temp_settings)
        self.settings_changed.emit(self.current_settings)
        super().accept()

    def get_settings(self) -> Dict[str, Any]:
        """Get the current settings."""
        return self.current_settings.copy()
