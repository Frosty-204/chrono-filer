"""Configuration management for Chrono Filer"""

import os
import json
from typing import Dict, Any, Optional
from PySide6.QtCore import QSettings, QStandardPaths


class Config:
    """Configuration manager using QSettings"""
    
    def __init__(self):
        self.settings = QSettings("ChronoFiler", "ChronoFiler")
        self._ensure_defaults()
        
    def _ensure_defaults(self):
        """Ensure default settings exist"""
        defaults = {
            'theme': 'light',
            'font_family': 'Arial',
            'font_size': 10,
            'icon_size': 'Medium',
            'startup_location': '',
            'startup_size': 100,
            'confirm_delete': True,
            'auto_refresh': True,
            'show_hidden': False,
            'show_system': False,
            'cache_size': 100,
            'thread_count': 4,
            'backup_enabled': True,
            'backup_location': '',
            'backup_frequency': 'Weekly',
            'backup_count': 10,
            'log_level': 'INFO',
            'log_file': '',
            'db_location': '',
            'experimental_features': False
        }
        
        for key, value in defaults.items():
            if not self.settings.contains(key):
                self.settings.setValue(key, value)
                
    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a setting value"""
        value = self.settings.value(key, default)
        # Convert QString to Python string if necessary
        if hasattr(value, 'toString'):
            value = str(value.toString())
        return value
        
    def set_setting(self, key: str, value: Any):
        """Set a setting value"""
        self.settings.setValue(key, value)
        
    def get_all_settings(self) -> Dict[str, Any]:
        """Get all settings as a dictionary"""
        settings = {}
        for key in self.settings.allKeys():
            settings[key] = self.get_setting(key)
        return settings
        
    def reset_settings(self):
        """Reset all settings to defaults"""
        self.settings.clear()
        self._ensure_defaults()
        
    def load_from_dict(self, data: Dict[str, Any]):
        """Load settings from a dictionary"""
        for key, value in data.items():
            self.set_setting(key, value)
            
    def export_settings(self, file_path: str):
        """Export settings to a JSON file"""
        settings = self.get_all_settings()
        with open(file_path, 'w') as f:
            json.dump(settings, f, indent=2)
            
    def import_settings(self, file_path: str):
        """Import settings from a JSON file"""
        with open(file_path, 'r') as f:
            settings = json.load(f)
        self.load_from_dict(settings)
        
    def get_data_dir(self) -> str:
        """Get the application data directory"""
        data_dir = QStandardPaths.writableLocation(QStandardPaths.AppDataLocation)
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
        return data_dir
        
    def get_config_dir(self) -> str:
        """Get the configuration directory"""
        config_dir = QStandardPaths.writableLocation(QStandardPaths.ConfigLocation)
        app_config_dir = os.path.join(config_dir, "ChronoFiler")
        if not os.path.exists(app_config_dir):
            os.makedirs(app_config_dir)
        return app_config_dir