"""Logging system for Chrono Filer"""

import os
import logging
from typing import Optional
from PySide6.QtCore import QStandardPaths
from core.config import Config


class Logger:
    """Centralized logging system"""
    
    def __init__(self, name: str = "ChronoFiler"):
        self.config = Config()
        self.logger = logging.getLogger(name)
        self._setup_logger()
        
    def _setup_logger(self):
        """Setup logger with configuration"""
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # Set level from config
        log_level = self.config.get_setting('log_level', 'INFO')
        level_map = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR
        }
        self.logger.setLevel(level_map.get(log_level, logging.INFO))
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        # File handler
        log_file = self.config.get_setting('log_file')
        if not log_file:
            log_dir = os.path.join(self.config.get_data_dir(), 'logs')
            os.makedirs(log_dir, exist_ok=True)
            log_file = os.path.join(log_dir, 'chrono_filer.log')
            
        try:
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
        except Exception as e:
            self.logger.error(f"Failed to setup file logging: {e}")
            
    def debug(self, message: str):
        """Log debug message"""
        self.logger.debug(message)
        
    def info(self, message: str):
        """Log info message"""
        self.logger.info(message)
        
    def warning(self, message: str):
        """Log warning message"""
        self.logger.warning(message)
        
    def error(self, message: str):
        """Log error message"""
        self.logger.error(message)
        
    def critical(self, message: str):
        """Log critical message"""
        self.logger.critical(message)
        
    def exception(self, message: str):
        """Log exception with traceback"""
        self.logger.exception(message)
        
    def update_level(self, level: str):
        """Update logging level from config"""
        level_map = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR
        }
        self.logger.setLevel(level_map.get(level, logging.INFO))
        
        # Update handlers
        for handler in self.logger.handlers:
            handler.setLevel(level_map.get(level, logging.INFO))