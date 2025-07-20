# src/settings_dialog.py
import pathlib
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

        # Image background color (simplified)
        self.image_bg_combo = QComboBox()
        self.image_bg_combo.addItems(["White", "Black", "Gray", "Transparent"])
        image_layout.addRow("Image Background:", self.image_bg_combo)

        layout.addWidget(image_group)

        # Text Preview Settings
        text_group = QGroupBox("Text Preview Settings")
        text_layout = QFormLayout(text_group)

        # Font family selection
        self.text_font_combo = QComboBox()
        self.text_font_combo.addItems(["Consolas", "Monaco", "Courier New", "Fira Code", "Source Code Pro", "DejaVu Sans Mono"])
        text_layout.addRow("Text Font Family:", self.text_font_combo)

        # Font size
        self.text_font_size_spin = QSpinBox()
        self.text_font_size_spin.setRange(8, 24)
        self.text_font_size_spin.setValue(10)
        text_layout.addRow("Font Size:", self.text_font_size_spin)

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
        self.theme_combo.addItems(["System Default", "Light", "Dark"])
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
        self.text_font_combo.currentTextChanged.connect(
            lambda: self._update_temp_setting("text_font_family", self.text_font_combo.currentText())
        )
        self.text_font_size_spin.valueChanged.connect(
            lambda: self._update_temp_setting("text_font_size", self.text_font_size_spin.value())
        )
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
        self.image_bg_combo.currentTextChanged.connect(
            lambda: self._update_temp_setting("image_background", self.image_bg_combo.currentText())
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
            self.current_settings.get("theme", "System Default")
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
        self.text_font_combo.setCurrentText(
            self.current_settings.get("text_font_family", "Consolas")
        )
        self.text_font_size_spin.setValue(
            self.current_settings.get("text_font_size", 10)
        )
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
        self.image_bg_combo.setCurrentText(
            self.current_settings.get("image_background", "White")
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
                self.text_font_combo.setCurrentText("Consolas")
                self.text_font_size_spin.setValue(10)
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
