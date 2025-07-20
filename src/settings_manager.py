import os
import json
import pathlib
from typing import Dict, Any

DEFAULT_SETTINGS = {
    # Organization defaults
    "default_structure_template": "[YYYY]/[MM]/[Filename].[Ext]",
    "default_conflict_resolution": "Skip",
    "default_operation_type": "Move",
    "default_dry_run": True,
    "default_name_filter_type": "Contains",
    "default_size_min_kb": 0,
    "default_size_max_kb": 1048576,  # 1 GB in KB
    "date_format": "YYYY/MM/DD",
    "custom_date_format": "",

    # Preview defaults
    "default_zoom_behavior": "Fit to Window",
    "custom_zoom_scale": 1.0,
    "image_background": "White",
    "show_line_numbers_default": True,
    "word_wrap_default": True,
    "text_font_family": "Consolas",
    "text_font_size": 10,
    "tab_width": 4,
    "max_preview_size_mb": 1,
    "enable_syntax_highlighting": True,
    "syntax_theme": "Default",

    # UI defaults
    "remember_window_geometry": True,
    "default_window_width": 1280,
    "default_window_height": 800,
    "left_panel_percent": 30,
    "right_panel_percent": 70,
    "theme": "System Default",
    "icon_size": "Medium (24px)",
    "show_file_extensions": True,
    "show_hidden_files": False,

    # Behavior defaults
    "confirm_delete": True,
    "auto_refresh": True,
    "double_click_behavior": "Navigate (folders) / Preview (files)",

    # Advanced defaults
    "undo_history_size": 50,
    "max_files_to_scan": 10000,
    "thumbnail_cache_size_mb": 100,

    # File type associations
    "file_type_associations": {
        ".py": "text",
        ".js": "text",
        ".json": "text",
        ".md": "text",
        ".txt": "text",
        ".jpg": "image",
        ".png": "image",
        ".gif": "image",
        ".bmp": "image",
        ".svg": "image",
        ".html": "text",
        ".css": "text",
        ".xml": "text",
        ".log": "text"
    }
}

class SettingsManager:
    def __init__(self, app_name="ChronoFiler"):
        # Determine config path based on XDG Base Directory Specification
        config_home_str = os.environ.get('XDG_CONFIG_HOME', '~/.config')
        self.config_dir = pathlib.Path(config_home_str).expanduser() / app_name
        self.config_file = self.config_dir / "config.json"

        # Ensure the directory exists
        self.config_dir.mkdir(parents=True, exist_ok=True)

    def save_settings(self, settings_dict: Dict[str, Any]):
        """Saves a dictionary of settings to the JSON config file."""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(settings_dict, f, indent=4)
        except Exception as e:
            print(f"Error saving settings: {e}")

    def load_settings(self) -> Dict[str, Any]:
        """Loads settings from the JSON config file. Returns defaults if not found or error."""
        if not self.config_file.exists():
            return DEFAULT_SETTINGS.copy()

        try:
            with open(self.config_file, 'r') as f:
                loaded_settings = json.load(f)
                # Merge with defaults to ensure all settings are present
                merged_settings = DEFAULT_SETTINGS.copy()
                merged_settings.update(loaded_settings)
                return merged_settings
        except (json.JSONDecodeError, Exception) as e:
            print(f"Error loading settings file (it may be corrupted): {e}")
            # Optionally, create a backup of the corrupted file here
            return DEFAULT_SETTINGS.copy()

    def get_default_settings(self) -> Dict[str, Any]:
        """Returns a copy of the default settings."""
        return DEFAULT_SETTINGS.copy()

    def reset_to_defaults(self):
        """Reset all settings to defaults."""
        self.save_settings(DEFAULT_SETTINGS)
