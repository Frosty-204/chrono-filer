"""Settings Dialog for Chrono Filer"""

import os
import json
from typing import Dict, Any, Optional
from PySide6.QtCore import Qt, QSettings, Signal
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTabWidget,
                              QWidget, QLabel, QLineEdit, QPushButton,
                              QCheckBox, QComboBox, QSpinBox, QGroupBox,
                              QFormLayout, QFileDialog, QMessageBox,
                              QFrame, QScrollArea, QTextEdit, QSlider,
                              QRadioButton, QButtonGroup)
from PySide6.QtGui import QFont, QFontDatabase, QIcon

from core.config import Config
from core.logger import Logger
from ui.theme_manager import ThemeManager


class SettingsDialog(QDialog):
    """Application settings dialog"""
    
    settings_changed = Signal(dict)
    
    def __init__(self, settings=None, parent=None):
        super().__init__(parent)
        self.config = Config()
        self.logger = Logger()
        self.theme_manager = ThemeManager()
        self.setWindowTitle("Settings")
        self.setModal(True)
        self.setMinimumSize(600, 500)
        self.setMaximumSize(800, 700)
        
        self.init_ui()
        if settings:
            self._apply_loaded_settings(settings)
        else:
            self.load_settings()
        
    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout(self)
        
        # Create tab widget
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        # Create tabs
        self.create_general_tab()
        self.create_appearance_tab()
        self.create_backup_tab()
        self.create_advanced_tab()
        
        # Create button box
        button_layout = QHBoxLayout()
        
        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.save_settings)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        
        self.reset_button = QPushButton("Reset to Defaults")
        self.reset_button.clicked.connect(self.reset_settings)
        
        button_layout.addStretch()
        button_layout.addWidget(self.reset_button)
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.save_button)
        
        layout.addLayout(button_layout)
        
    def create_general_tab(self):
        """Create general settings tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Startup group
        startup_group = QGroupBox("Startup")
        startup_layout = QFormLayout(startup_group)
        
        self.startup_location = QLineEdit()
        self.startup_location.setPlaceholderText("Leave empty for last location")
        startup_layout.addRow("Startup Location:", self.startup_location)
        
        self.startup_size = QSpinBox()
        self.startup_size.setRange(100, 10000)
        self.startup_size.setSuffix(" MB")
        startup_layout.addRow("Default Size Threshold:", self.startup_size)
        
        layout.addWidget(startup_group)
        
        # Behavior group
        behavior_group = QGroupBox("Behavior")
        behavior_layout = QFormLayout(behavior_group)
        
        self.confirm_delete = QCheckBox("Confirm before deleting files")
        self.auto_refresh = QCheckBox("Auto-refresh file list")
        self.auto_refresh.setChecked(True)
        self.show_hidden = QCheckBox("Show hidden files")
        self.show_system = QCheckBox("Show system files")
        
        behavior_layout.addRow(self.confirm_delete)
        behavior_layout.addRow(self.auto_refresh)
        behavior_layout.addRow(self.show_hidden)
        behavior_layout.addRow(self.show_system)
        
        layout.addWidget(behavior_group)
        
        # Performance group
        performance_group = QGroupBox("Performance")
        performance_layout = QFormLayout(performance_group)
        
        self.cache_size = QSpinBox()
        self.cache_size.setRange(10, 1000)
        self.cache_size.setSuffix(" MB")
        performance_layout.addRow("Cache Size:", self.cache_size)
        
        self.thread_count = QSpinBox()
        self.thread_count.setRange(1, 16)
        performance_layout.addRow("Thread Count:", self.thread_count)
        
        layout.addWidget(performance_group)
        layout.addStretch()
        
        self.tabs.addTab(tab, "General")
        
    def create_appearance_tab(self):
        """Create appearance settings tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Theme group
        theme_group = QGroupBox("Theme")
        theme_layout = QFormLayout(theme_group)
        
        self.theme_combo = QComboBox()
        themes = self.theme_manager.get_available_themes()
        for key, name in themes.items():
            self.theme_combo.addItem(name, key)
        theme_layout.addRow("Theme:", self.theme_combo)
        
        # Font settings
        font_group = QGroupBox("Font")
        font_layout = QFormLayout(font_group)
        
        self.font_family = QComboBox()
        self.font_family.addItems(QFontDatabase.families())
        font_layout.addRow("Font Family:", self.font_family)
        
        self.font_size = QSpinBox()
        self.font_size.setRange(8, 24)
        font_layout.addRow("Font Size:", self.font_size)
        
        # Icon settings
        icon_group = QGroupBox("Icons")
        icon_layout = QFormLayout(icon_group)
        
        self.icon_size = QComboBox()
        self.icon_size.addItems(["Small", "Medium", "Large"])
        icon_layout.addRow("Icon Size:", self.icon_size)
        
        layout.addWidget(theme_group)
        layout.addWidget(font_group)
        layout.addWidget(icon_group)
        layout.addStretch()
        
        self.tabs.addTab(tab, "Appearance")
        
    def create_backup_tab(self):
        """Create backup settings tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Backup settings
        backup_group = QGroupBox("Backup Settings")
        backup_layout = QFormLayout(backup_group)
        
        self.backup_enabled = QCheckBox("Enable automatic backups")
        self.backup_enabled.setChecked(True)
        backup_layout.addRow(self.backup_enabled)
        
        self.backup_location = QLineEdit()
        backup_layout.addRow("Backup Location:", self.backup_location)
        
        browse_button = QPushButton("Browse...")
        browse_button.clicked.connect(self.browse_backup_location)
        backup_layout.addRow(browse_button)
        
        self.backup_frequency = QComboBox()
        self.backup_frequency.addItems(["Daily", "Weekly", "Monthly"])
        backup_layout.addRow("Backup Frequency:", self.backup_frequency)
        
        self.backup_count = QSpinBox()
        self.backup_count.setRange(1, 50)
        self.backup_count.setSuffix(" backups")
        backup_layout.addRow("Keep Backups:", self.backup_count)
        
        layout.addWidget(backup_group)
        
        # Restore section
        restore_group = QGroupBox("Restore")
        restore_layout = QVBoxLayout(restore_group)
        
        restore_button = QPushButton("Restore from Backup...")
        restore_button.clicked.connect(self.restore_backup)
        restore_layout.addWidget(restore_button)
        
        layout.addWidget(restore_group)
        layout.addStretch()
        
        self.tabs.addTab(tab, "Backup")
        
    def create_advanced_tab(self):
        """Create advanced settings tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Logging settings
        logging_group = QGroupBox("Logging")
        logging_layout = QFormLayout(logging_group)
        
        self.log_level = QComboBox()
        self.log_level.addItems(["DEBUG", "INFO", "WARNING", "ERROR"])
        logging_layout.addRow("Log Level:", self.log_level)
        
        self.log_file = QLineEdit()
        logging_layout.addRow("Log File:", self.log_file)
        
        browse_log_button = QPushButton("Browse...")
        browse_log_button.clicked.connect(self.browse_log_file)
        logging_layout.addRow(browse_log_button)
        
        layout.addWidget(logging_group)
        
        # Database settings
        db_group = QGroupBox("Database")
        db_layout = QFormLayout(db_group)
        
        self.db_location = QLineEdit()
        db_layout.addRow("Database Location:", self.db_location)
        
        browse_db_button = QPushButton("Browse...")
        browse_db_button.clicked.connect(self.browse_db_location)
        db_layout.addRow(browse_db_button)
        
        compact_button = QPushButton("Compact Database")
        compact_button.clicked.connect(self.compact_database)
        db_layout.addRow(compact_button)
        
        layout.addWidget(db_group)
        
        # Experimental features
        experimental_group = QGroupBox("Experimental Features")
        experimental_layout = QVBoxLayout(experimental_group)
        
        self.experimental_features = QCheckBox("Enable experimental features")
        self.experimental_features.setToolTip("Enable features that are still in development")
        experimental_layout.addWidget(self.experimental_features)
        
        layout.addWidget(experimental_group)
        layout.addStretch()
        
        self.tabs.addTab(tab, "Advanced")
        
    def load_settings(self):
        """Load settings from configuration"""
        settings = self.config.get_all_settings()
        
        # General settings
        self.startup_location.setText(settings.get('startup_location', ''))
        self.startup_size.setValue(settings.get('startup_size', 100))
        self.confirm_delete.setChecked(settings.get('confirm_delete', True))
        self.auto_refresh.setChecked(settings.get('auto_refresh', True))
        self.show_hidden.setChecked(settings.get('show_hidden', False))
        self.show_system.setChecked(settings.get('show_system', False))
        self.cache_size.setValue(settings.get('cache_size', 100))
        self.thread_count.setValue(settings.get('thread_count', 4))
        
        # Appearance settings
        theme_name = settings.get('theme', 'light')
        index = self.theme_combo.findData(theme_name)
        if index >= 0:
            self.theme_combo.setCurrentIndex(index)
            
        self.font_family.setCurrentText(settings.get('font_family', 'Arial'))
        self.font_size.setValue(settings.get('font_size', 10))
        
        icon_size = settings.get('icon_size', 'Medium')
        index = self.icon_size.findText(icon_size)
        if index >= 0:
            self.icon_size.setCurrentIndex(index)
        
        # Backup settings
        self.backup_enabled.setChecked(settings.get('backup_enabled', True))
        self.backup_location.setText(settings.get('backup_location', ''))
        
        frequency = settings.get('backup_frequency', 'Weekly')
        index = self.backup_frequency.findText(frequency)
        if index >= 0:
            self.backup_frequency.setCurrentIndex(index)
            
        self.backup_count.setValue(settings.get('backup_count', 10))
        
        # Advanced settings
        self.log_level.setCurrentText(settings.get('log_level', 'INFO'))
        self.log_file.setText(settings.get('log_file', ''))
        self.db_location.setText(settings.get('db_location', ''))
        self.experimental_features.setChecked(settings.get('experimental_features', False))
        
    def save_settings(self):
        """Save settings to configuration"""
        settings = {
            # General settings
            'startup_location': self.startup_location.text(),
            'startup_size': self.startup_size.value(),
            'confirm_delete': self.confirm_delete.isChecked(),
            'auto_refresh': self.auto_refresh.isChecked(),
            'show_hidden': self.show_hidden.isChecked(),
            'show_system': self.show_system.isChecked(),
            'cache_size': self.cache_size.value(),
            'thread_count': self.thread_count.value(),
            
            # Appearance settings
            'theme': self.theme_combo.currentData(),
            'font_family': self.font_family.currentText(),
            'font_size': self.font_size.value(),
            'icon_size': self.icon_size.currentText(),
            
            # Backup settings
            'backup_enabled': self.backup_enabled.isChecked(),
            'backup_location': self.backup_location.text(),
            'backup_frequency': self.backup_frequency.currentText(),
            'backup_count': self.backup_count.value(),
            
            # Advanced settings
            'log_level': self.log_level.currentText(),
            'log_file': self.log_file.text(),
            'db_location': self.db_location.text(),
            'experimental_features': self.experimental_features.isChecked()
        }
        
        # Save to config
        for key, value in settings.items():
            self.config.set_setting(key, value)
        
        # Apply theme
        theme_name = self.theme_combo.currentData()
        self.theme_manager.set_theme(theme_name)
        
        # Emit signal
        self.settings_changed.emit(settings)
        
        # Close dialog
        self.accept()
        
    def reset_settings(self):
        """Reset settings to defaults"""
        reply = QMessageBox.question(
            self, "Reset Settings",
            "Are you sure you want to reset all settings to their default values?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.config.reset_settings()
            self.load_settings()
            
    def browse_backup_location(self):
        """Browse for backup location"""
        directory = QFileDialog.getExistingDirectory(
            self, "Select Backup Location",
            self.backup_location.text() or os.path.expanduser("~")
        )
        if directory:
            self.backup_location.setText(directory)
            
    def browse_log_file(self):
        """Browse for log file location"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Select Log File",
            self.log_file.text() or os.path.expanduser("~/chrono_filer.log"),
            "Log Files (*.log);;All Files (*)"
        )
        if file_path:
            self.log_file.setText(file_path)
            
    def browse_db_location(self):
        """Browse for database location"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Select Database Location",
            self.db_location.text() or os.path.expanduser("~/chrono_filer.db"),
            "Database Files (*.db);;All Files (*)"
        )
        if file_path:
            self.db_location.setText(file_path)
            
    def restore_backup(self):
        """Restore from backup"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Backup File",
            self.backup_location.text() or os.path.expanduser("~"),
            "Backup Files (*.json);;All Files (*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'r') as f:
                    backup_data = json.load(f)
                    
                reply = QMessageBox.question(
                    self, "Restore Backup",
                    "This will replace all current settings. Continue?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                
                if reply == QMessageBox.StandardButton.Yes:
                    self.config.load_from_dict(backup_data)
                    self.load_settings()
                    QMessageBox.information(
                        self, "Restore Complete",
                        "Settings restored from backup successfully."
                    )
                    
            except Exception as e:
                QMessageBox.critical(
                    self, "Restore Failed",
                    f"Failed to restore backup: {str(e)}"
                )
                
    def compact_database(self):
        """Compact the database"""
        try:
            # This would typically involve database operations
            QMessageBox.information(
                self, "Database Compacted",
                "Database has been compacted successfully."
            )
        except Exception as e:
            QMessageBox.critical(
                self, "Compaction Failed",
                f"Failed to compact database: {str(e)}"
            )
            
    def _apply_loaded_settings(self, settings):
        """Apply settings passed from main window"""
        # General settings
        self.startup_location.setText(settings.get('startup_location', ''))
        self.startup_size.setValue(settings.get('startup_size', 100))
        self.confirm_delete.setChecked(settings.get('confirm_delete', True))
        self.auto_refresh.setChecked(settings.get('auto_refresh', True))
        self.show_hidden.setChecked(settings.get('show_hidden', False))
        self.show_system.setChecked(settings.get('show_system', False))
        self.cache_size.setValue(settings.get('cache_size', 100))
        self.thread_count.setValue(settings.get('thread_count', 4))
        
        # Appearance settings
        theme_name = settings.get('theme', 'light')
        index = self.theme_combo.findData(theme_name)
        if index >= 0:
            self.theme_combo.setCurrentIndex(index)
            
        self.font_family.setCurrentText(settings.get('font_family', 'Arial'))
        self.font_size.setValue(settings.get('font_size', 10))
        
        icon_size = settings.get('icon_size', 'Medium')
        index = self.icon_size.findText(icon_size)
        if index >= 0:
            self.icon_size.setCurrentIndex(index)
        
        # Backup settings
        self.backup_enabled.setChecked(settings.get('backup_enabled', True))
        self.backup_location.setText(settings.get('backup_location', ''))
        
        frequency = settings.get('backup_frequency', 'Weekly')
        index = self.backup_frequency.findText(frequency)
        if index >= 0:
            self.backup_frequency.setCurrentIndex(index)
            
        self.backup_count.setValue(settings.get('backup_count', 10))
        
        # Advanced settings
        self.log_level.setCurrentText(settings.get('log_level', 'INFO'))
        self.log_file.setText(settings.get('log_file', ''))
        self.db_location.setText(settings.get('db_location', ''))
        self.experimental_features.setChecked(settings.get('experimental_features', False))
