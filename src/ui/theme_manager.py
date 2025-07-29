"""Theme Manager for Chrono Filer - Material Design Theme System"""

import os
from typing import Dict, Any
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QPalette, QColor


class ThemeManager(QObject):
    """Manages application themes and styling"""
    
    theme_changed = pyqtSignal(str)  # Emitted when theme changes
    
    def __init__(self):
        super().__init__()
        self.current_theme = 'material'
        self.themes = {
            'material': {
                'name': 'Material Design',
                'stylesheet': 'src/ui/styles/material.qss',
                'colors': {
                    'primary': '#1976D2',
                    'secondary': '#03DAC6',
                    'background': '#FAFAFA',
                    'surface': '#FFFFFF',
                    'error': '#B00020',
                    'on_primary': '#FFFFFF',
                    'on_secondary': '#000000',
                    'on_background': '#212121',
                    'on_surface': '#212121',
                    'on_error': '#FFFFFF'
                }
            },
            'dark': {
                'name': 'Material Dark',
                'stylesheet': 'src/ui/styles/material_dark.qss',
                'colors': {
                    'primary': '#BB86FC',
                    'secondary': '#03DAC6',
                    'background': '#121212',
                    'surface': '#1E1E1E',
                    'error': '#CF6679',
                    'on_primary': '#000000',
                    'on_secondary': '#000000',
                    'on_background': '#FFFFFF',
                    'on_surface': '#FFFFFF',
                    'on_error': '#000000'
                }
            },
            'high_contrast': {
                'name': 'High Contrast',
                'stylesheet': 'src/ui/styles/high_contrast.qss',
                'colors': {
                    'primary': '#000000',
                    'secondary': '#FFFFFF',
                    'background': '#FFFFFF',
                    'surface': '#FFFFFF',
                    'error': '#000000',
                    'on_primary': '#FFFFFF',
                    'on_secondary': '#000000',
                    'on_background': '#000000',
                    'on_surface': '#000000',
                    'on_error': '#FFFFFF'
                }
            }
        }
    
    def get_available_themes(self) -> Dict[str, str]:
        """Return list of available themes with their display names"""
        return {key: theme['name'] for key, theme in self.themes.items()}
    
    def get_current_theme(self) -> str:
        """Get current theme name"""
        return self.current_theme
    
    def set_theme(self, theme_name: str) -> bool:
        """Apply a theme to the application"""
        if theme_name not in self.themes:
            return False
        
        self.current_theme = theme_name
        theme = self.themes[theme_name]
        
        # Load stylesheet
        stylesheet_path = theme['stylesheet']
        if os.path.exists(stylesheet_path):
            with open(stylesheet_path, 'r') as f:
                stylesheet = f.read()
                QApplication.instance().setStyleSheet(stylesheet)
        
        # Apply palette based on theme
        if theme_name == 'dark':
            self._apply_dark_palette()
        elif theme_name == 'high_contrast':
            self._apply_high_contrast_palette()
        else:
            self._apply_light_palette()
        
        self.theme_changed.emit(theme_name)
        return True
    
    def get_theme_color(self, color_key: str) -> str:
        """Get a specific color from the current theme"""
        if self.current_theme in self.themes:
            colors = self.themes[self.current_theme]['colors']
            return colors.get(color_key, '#000000')
        return '#000000'
    
    def _apply_light_palette(self):
        """Apply light theme palette"""
        app = QApplication.instance()
        palette = QPalette()
        
        # Set colors for light theme
        palette.setColor(QPalette.ColorRole.Window, QColor("#FAFAFA"))
        palette.setColor(QPalette.ColorRole.WindowText, QColor("#212121"))
        palette.setColor(QPalette.ColorRole.Base, QColor("#FFFFFF"))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor("#F5F5F5"))
        palette.setColor(QPalette.ColorRole.ToolTipBase, QColor("#424242"))
        palette.setColor(QPalette.ColorRole.ToolTipText, QColor("#FFFFFF"))
        palette.setColor(QPalette.ColorRole.Text, QColor("#212121"))
        palette.setColor(QPalette.ColorRole.Button, QColor("#F5F5F5"))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor("#212121"))
        palette.setColor(QPalette.ColorRole.BrightText, QColor("#FFFFFF"))
        palette.setColor(QPalette.ColorRole.Link, QColor("#1976D2"))
        palette.setColor(QPalette.ColorRole.Highlight, QColor("#1976D2"))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#FFFFFF"))
        
        app.setPalette(palette)
    
    def _apply_dark_palette(self):
        """Apply dark theme palette"""
        app = QApplication.instance()
        palette = QPalette()
        
        # Set colors for dark theme
        palette.setColor(QPalette.ColorRole.Window, QColor("#121212"))
        palette.setColor(QPalette.ColorRole.WindowText, QColor("#FFFFFF"))
        palette.setColor(QPalette.ColorRole.Base, QColor("#1E1E1E"))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor("#2C2C2C"))
        palette.setColor(QPalette.ColorRole.ToolTipBase, QColor("#FFFFFF"))
        palette.setColor(QPalette.ColorRole.ToolTipText, QColor("#121212"))
        palette.setColor(QPalette.ColorRole.Text, QColor("#FFFFFF"))
        palette.setColor(QPalette.ColorRole.Button, QColor("#2C2C2C"))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor("#FFFFFF"))
        palette.setColor(QPalette.ColorRole.BrightText, QColor("#FFFFFF"))
        palette.setColor(QPalette.ColorRole.Link, QColor("#BB86FC"))
        palette.setColor(QPalette.ColorRole.Highlight, QColor("#BB86FC"))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#000000"))
        
        app.setPalette(palette)
    
    def _apply_high_contrast_palette(self):
        """Apply high contrast theme palette"""
        app = QApplication.instance()
        palette = QPalette()
        
        # Set colors for high contrast theme
        palette.setColor(QPalette.ColorRole.Window, QColor("#FFFFFF"))
        palette.setColor(QPalette.ColorRole.WindowText, QColor("#000000"))
        palette.setColor(QPalette.ColorRole.Base, QColor("#FFFFFF"))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor("#F0F0F0"))
        palette.setColor(QPalette.ColorRole.ToolTipBase, QColor("#000000"))
        palette.setColor(QPalette.ColorRole.ToolTipText, QColor("#FFFFFF"))
        palette.setColor(QPalette.ColorRole.Text, QColor("#000000"))
        palette.setColor(QPalette.ColorRole.Button, QColor("#FFFFFF"))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor("#000000"))
        palette.setColor(QPalette.ColorRole.BrightText, QColor("#FFFFFF"))
        palette.setColor(QPalette.ColorRole.Link, QColor("#0000FF"))
        palette.setColor(QPalette.ColorRole.Highlight, QColor("#000000"))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#FFFFFF"))
        
        app.setPalette(palette)
    
    def get_theme_settings(self) -> Dict[str, Any]:
        """Return theme-specific settings"""
        return {
            'current_theme': self.current_theme,
            'available_themes': self.get_available_themes()
        }
    
    def load_settings(self, settings: Dict[str, Any]):
        """Load theme settings from configuration"""
        theme_name = settings.get('current_theme', 'material')
        self.set_theme(theme_name)