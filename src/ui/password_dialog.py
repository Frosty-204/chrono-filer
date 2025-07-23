# src/password_dialog.py
import pathlib
from typing import Optional
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                               QLineEdit, QCheckBox, QPushButton, QMessageBox,
                               QProgressBar, QGroupBox, QFormLayout)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont, QFontMetrics

try:
    import keyring
    KEYRING_AVAILABLE = True
except ImportError:
    KEYRING_AVAILABLE = False

from core.encryption_engine import EncryptionEngine


class PasswordManager:
    """Manages password storage using system keyring."""
    
    def __init__(self, service_name="ChronoFiler"):
        self.service_name = service_name
    
    def store_password(self, identifier: str, password: str) -> bool:
        """Store password in system keyring."""
        if not KEYRING_AVAILABLE:
            return False
        
        try:
            keyring.set_password(self.service_name, identifier, password)
            return True
        except Exception:
            return False
    
    def get_password(self, identifier: str) -> Optional[str]:
        """Retrieve password from system keyring."""
        if not KEYRING_AVAILABLE:
            return None
        
        try:
            return keyring.get_password(self.service_name, identifier)
        except Exception:
            return None
    
    def delete_password(self, identifier: str) -> bool:
        """Delete password from system keyring."""
        if not KEYRING_AVAILABLE:
            return False
        
        try:
            keyring.delete_password(self.service_name, identifier)
            return True
        except Exception:
            return False
    
    def list_passwords(self) -> list[str]:
        """List all stored identifiers."""
        if not KEYRING_AVAILABLE:
            return []
        
        try:
            return keyring.get_credential(self.service_name, None) or []
        except Exception:
            return []


class PasswordDialog(QDialog):
    """Dialog for password input and management."""
    
    def __init__(self, parent=None, operation="encrypt", filename=None):
        super().__init__(parent)
        self.operation = operation
        self.filename = filename or "file"
        self.password = None
        self.store_password = False
        
        self.setWindowTitle(f"{operation.title()} {filename}")
        self.setModal(True)
        self.resize(400, 300)
        
        self._create_ui()
        self._connect_signals()
    
    def _create_ui(self):
        """Create the user interface."""
        layout = QVBoxLayout(self)
        
        # Header
        header = QLabel(f"Enter password to {self.operation}:")
        header.setFont(QFont("Arial", 12, QFont.Bold))
        layout.addWidget(header)
        
        # File info
        if self.filename:
            file_label = QLabel(f"File: {self.filename}")
            file_label.setStyleSheet("color: gray;")
            layout.addWidget(file_label)
        
        # Password input
        password_group = QGroupBox("Password")
        password_layout = QFormLayout()
        
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText("Enter password...")
        password_layout.addRow("Password:", self.password_input)
        
        self.confirm_input = QLineEdit()
        self.confirm_input.setEchoMode(QLineEdit.Password)
        self.confirm_input.setPlaceholderText("Confirm password...")
        password_layout.addRow("Confirm:", self.confirm_input)
        
        password_group.setLayout(password_layout)
        layout.addWidget(password_group)
        
        # Password strength indicator
        self.strength_label = QLabel("Password strength: ")
        self.strength_bar = QProgressBar()
        self.strength_bar.setRange(0, 100)
        self.strength_bar.setVisible(False)
        
        strength_layout = QVBoxLayout()
        strength_layout.addWidget(self.strength_label)
        strength_layout.addWidget(self.strength_bar)
        layout.addLayout(strength_layout)
        
        # Options
        options_group = QGroupBox("Options")
        options_layout = QVBoxLayout()
        
        self.store_checkbox = QCheckBox("Store password in system keyring")
        self.store_checkbox.setEnabled(KEYRING_AVAILABLE)
        if not KEYRING_AVAILABLE:
            self.store_checkbox.setToolTip("System keyring not available")
        
        self.show_password_checkbox = QCheckBox("Show password")
        options_layout.addWidget(self.store_checkbox)
        options_layout.addWidget(self.show_password_checkbox)
        
        options_group.setLayout(options_layout)
        layout.addWidget(options_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.ok_button = QPushButton("OK")
        self.ok_button.setDefault(True)
        self.cancel_button = QPushButton("Cancel")
        
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)
    
    def _connect_signals(self):
        """Connect UI signals."""
        self.password_input.textChanged.connect(self._update_strength)
        self.confirm_input.textChanged.connect(self._validate_passwords)
        self.show_password_checkbox.toggled.connect(self._toggle_password_visibility)
        self.ok_button.clicked.connect(self._on_ok)
        self.cancel_button.clicked.connect(self.reject)
    
    def _update_strength(self):
        """Update password strength indicator."""
        password = self.password_input.text()
        if not password:
            self.strength_bar.setVisible(False)
            self.strength_label.setText("Password strength: ")
            return
        
        strength = self._calculate_strength(password)
        self.strength_bar.setVisible(True)
        self.strength_bar.setValue(strength)
        
        if strength < 30:
            self.strength_label.setText("Password strength: Weak")
            self.strength_bar.setStyleSheet("QProgressBar::chunk { background-color: red; }")
        elif strength < 60:
            self.strength_label.setText("Password strength: Medium")
            self.strength_bar.setStyleSheet("QProgressBar::chunk { background-color: orange; }")
        else:
            self.strength_label.setText("Password strength: Strong")
            self.strength_bar.setStyleSheet("QProgressBar::chunk { background-color: green; }")
    
    def _calculate_strength(self, password: str) -> int:
        """Calculate password strength score (0-100)."""
        if not password:
            return 0
        
        score = 0
        
        # Length bonus
        score += min(len(password) * 4, 40)
        
        # Character variety
        has_lower = any(c.islower() for c in password)
        has_upper = any(c.isupper() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)
        
        if has_lower:
            score += 10
        if has_upper:
            score += 10
        if has_digit:
            score += 10
        if has_special:
            score += 20
        
        # Bonus for mixed types
        types = sum([has_lower, has_upper, has_digit, has_special])
        if types >= 3:
            score += 10
        
        return min(score, 100)
    
    def _validate_passwords(self):
        """Validate password confirmation."""
        password = self.password_input.text()
        confirm = self.confirm_input.text()
        
        if password and confirm and password != confirm:
            self.confirm_input.setStyleSheet("border: 1px solid red;")
        else:
            self.confirm_input.setStyleSheet("")
    
    def _toggle_password_visibility(self, show: bool):
        """Toggle password visibility."""
        mode = QLineEdit.Normal if show else QLineEdit.Password
        self.password_input.setEchoMode(mode)
        self.confirm_input.setEchoMode(mode)
    
    def _on_ok(self):
        """Handle OK button click."""
        password = self.password_input.text()
        confirm = self.confirm_input.text()
        
        if not password:
            QMessageBox.warning(self, "Warning", "Please enter a password")
            return
        
        if password != confirm:
            QMessageBox.warning(self, "Warning", "Passwords do not match")
            return
        
        if len(password) < 8:
            reply = QMessageBox.question(
                self, "Weak Password",
                "Password is less than 8 characters. Continue anyway?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                return
        
        self.password = password
        self.store_password = self.store_checkbox.isChecked()
        self.accept()
    
    def get_password(self) -> str:
        """Get the entered password."""
        return self.password
    
    def should_store_password(self) -> bool:
        """Check if password should be stored."""
        return self.store_password


class DecryptDialog(QDialog):
    """Dialog for decrypting files."""
    
    def __init__(self, parent=None, filename=None):
        super().__init__(parent)
        self.filename = filename or "file"
        self.password = None
        
        self.setWindowTitle(f"Decrypt {filename}")
        self.setModal(True)
        self.resize(400, 200)
        
        self._create_ui()
        self._connect_signals()
    
    def _create_ui(self):
        """Create the user interface."""
        layout = QVBoxLayout(self)
        
        # Header
        header = QLabel("Enter password to decrypt:")
        header.setFont(QFont("Arial", 12, QFont.Bold))
        layout.addWidget(header)
        
        # File info
        file_label = QLabel(f"File: {self.filename}")
        file_label.setStyleSheet("color: gray;")
        layout.addWidget(file_label)
        
        # Password input
        password_layout = QFormLayout()
        
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText("Enter password...")
        password_layout.addRow("Password:", self.password_input)
        
        layout.addLayout(password_layout)
        
        # Check for stored password
        manager = PasswordManager()
        stored_password = manager.get_password(self.filename)
        if stored_password:
            self.password_input.setText(stored_password)
            remember_label = QLabel("Using stored password from keyring")
            remember_label.setStyleSheet("color: green; font-size: 10px;")
            layout.addWidget(remember_label)
        
        # Show password checkbox
        self.show_password_checkbox = QCheckBox("Show password")
        layout.addWidget(self.show_password_checkbox)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.ok_button = QPushButton("OK")
        self.ok_button.setDefault(True)
        self.cancel_button = QPushButton("Cancel")
        
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)
    
    def _connect_signals(self):
        """Connect UI signals."""
        self.show_password_checkbox.toggled.connect(
            lambda checked: self.password_input.setEchoMode(
                QLineEdit.Normal if checked else QLineEdit.Password
            )
        )
        self.ok_button.clicked.connect(self._on_ok)
        self.cancel_button.clicked.connect(self.reject)
    
    def _on_ok(self):
        """Handle OK button click."""
        password = self.password_input.text()
        if not password:
            QMessageBox.warning(self, "Warning", "Please enter a password")
            return
        
        self.password = password
        self.accept()
    
    def get_password(self) -> str:
        """Get the entered password."""
        return self.password


if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    # Test password dialog
    dialog = PasswordDialog(None, "encrypt", "test.txt")
    if dialog.exec() == QDialog.Accepted:
        print(f"Password: {dialog.get_password()}")
        print(f"Store: {dialog.should_store_password()}")
    
    # Test decrypt dialog
    dialog = DecryptDialog(None, "test.txt.enc")
    if dialog.exec() == QDialog.Accepted:
        print(f"Password: {dialog.get_password()}")