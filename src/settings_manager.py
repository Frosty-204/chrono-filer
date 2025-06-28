import os
import json
import pathlib
from typing import Dict, Any

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
        """Loads settings from the JSON config file. Returns empty dict if not found or error."""
        if not self.config_file.exists():
            return {}

        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, Exception) as e:
            print(f"Error loading settings file (it may be corrupted): {e}")
            # Optionally, create a backup of the corrupted file here
            return {}
