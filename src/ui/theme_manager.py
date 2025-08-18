"""Theme Manager for Chrono Filer - Fusion Style Theme System"""

import os
from typing import Dict, Any
from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPalette, QColor

from .icon_manager import IconManager


class ThemeManager(QObject):
    """Manages application themes and styling"""
    
    theme_changed = Signal(str)  # Emitted when theme changes
    
    def __init__(self):
        super().__init__()
        self.current_theme = 'light'
        self.icon_manager = IconManager()
        self.themes = {
            'light': {
                'name': 'Light',
                'stylesheet': 'src/ui/styles/fusion_light.qss',
                'colors': {
                    'primary': '#2563eb',
                    'secondary': '#64748b',
                    'accent': '#06b6d4',
                    'background': '#ffffff',
                    'surface': '#f8fafc',
                    'surface-variant': '#f1f5f9',
                    'error': '#ef4444',
                    'warning': '#f59e0b',
                    'success': '#10b981',
                    'text-primary': '#0f172a',
                    'text-secondary': '#475569',
                    'text-muted': '#94a3b8',
                    'border': '#e2e8f0',
                    'border-light': '#f1f5f9'
                }
            },
            'dark': {
                'name': 'Dark',
                'stylesheet': 'src/ui/styles/fusion_dark.qss',
                'colors': {
                    'primary': '#3b82f6',
                    'secondary': '#64748b',
                    'accent': '#06b6d4',
                    'background': '#0f172a',
                    'surface': '#1e293b',
                    'surface-variant': '#334155',
                    'error': '#ef4444',
                    'warning': '#f59e0b',
                    'success': '#10b981',
                    'text-primary': '#f8fafc',
                    'text-secondary': '#cbd5e1',
                    'text-muted': '#64748b',
                    'border': '#334155',
                    'border-light': '#475569'
                }
            },
            # High contrast theme removed - only light/dark themes supported
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
        
        # Update icon manager theme
        self.icon_manager.set_theme(theme_name)
        
        # Load stylesheet
        stylesheet_path = theme['stylesheet']
        if os.path.exists(stylesheet_path):
            with open(stylesheet_path, 'r') as f:
                stylesheet = f.read()
                QApplication.instance().setStyleSheet(stylesheet)
        
        # Apply palette based on theme
        if theme_name == 'dark':
            self._apply_dark_palette()
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
        palette.setColor(QPalette.ColorRole.Window, QColor("#ffffff"))
        palette.setColor(QPalette.ColorRole.WindowText, QColor("#0f172a"))
        palette.setColor(QPalette.ColorRole.Base, QColor("#ffffff"))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor("#f8fafc"))
        palette.setColor(QPalette.ColorRole.ToolTipBase, QColor("#1e293b"))
        palette.setColor(QPalette.ColorRole.ToolTipText, QColor("#f8fafc"))
        palette.setColor(QPalette.ColorRole.Text, QColor("#0f172a"))
        palette.setColor(QPalette.ColorRole.Button, QColor("#f8fafc"))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor("#0f172a"))
        palette.setColor(QPalette.ColorRole.BrightText, QColor("#ffffff"))
        palette.setColor(QPalette.ColorRole.Link, QColor("#2563eb"))
        palette.setColor(QPalette.ColorRole.Highlight, QColor("#2563eb"))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
        
        app.setPalette(palette)
    
    def _apply_dark_palette(self):
        """Apply dark theme palette"""
        app = QApplication.instance()
        palette = QPalette()
        
        # Set colors for dark theme
        palette.setColor(QPalette.ColorRole.Window, QColor("#0f172a"))
        palette.setColor(QPalette.ColorRole.WindowText, QColor("#f8fafc"))
        palette.setColor(QPalette.ColorRole.Base, QColor("#1e293b"))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor("#334155"))
        palette.setColor(QPalette.ColorRole.ToolTipBase, QColor("#f8fafc"))
        palette.setColor(QPalette.ColorRole.ToolTipText, QColor("#0f172a"))
        palette.setColor(QPalette.ColorRole.Text, QColor("#f8fafc"))
        palette.setColor(QPalette.ColorRole.Button, QColor("#1e293b"))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor("#f8fafc"))
        palette.setColor(QPalette.ColorRole.BrightText, QColor("#ffffff"))
        palette.setColor(QPalette.ColorRole.Link, QColor("#3b82f6"))
        palette.setColor(QPalette.ColorRole.Highlight, QColor("#3b82f6"))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#0f172a"))
        
        app.setPalette(palette)
    
    def get_theme_settings(self) -> Dict[str, Any]:
        """Return theme-specific settings"""
        return {
            'current_theme': self.current_theme,
            'available_themes': self.get_available_themes()
        }
    
    def load_settings(self, settings: Dict[str, Any]):
        """Load theme settings from configuration"""
        theme_name = settings.get('current_theme', 'light')
        self.set_theme(theme_name)
    
    def get_icon(self, icon_name: str, color: str = None) -> Any:
        """Get a theme-aware icon from the icon manager"""
        return self.icon_manager.get_icon(icon_name, color)

    def get_standard_icon(self, standard_type: str) -> Any:
        """Get a standard icon for common actions"""
        return self.icon_manager.get_standard_icon(standard_type)
    
    def get_color(self, color_key: str) -> str:
        """Get a specific color from the current theme (alias for get_theme_color)"""
        return self.get_theme_color(color_key)