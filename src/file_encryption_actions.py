# src/file_encryption_actions.py
import pathlib
from typing import List, Optional
from PySide6.QtWidgets import QMenu, QMessageBox, QInputDialog
from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QAction

from core.encryption_engine import EncryptionEngine
from ui.password_dialog import PasswordDialog, DecryptDialog
from utils.settings_manager import SettingsManager


class FileEncryptionActions(QObject):
    """Handles file encryption/decryption actions in the file browser."""
    
    status_message = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.encryption_engine = EncryptionEngine()
        self.settings_manager = SettingsManager()
    
    def add_encryption_actions(self, menu: QMenu, selected_files: List[pathlib.Path]):
        """Add encryption-related actions to the context menu."""
        if not selected_files:
            return
        
        menu.addSeparator()
        
        # Check if any files are encrypted
        has_encrypted = any(self.encryption_engine.is_encrypted_file(f) for f in selected_files)
        has_unencrypted = any(not self.encryption_engine.is_encrypted_file(f) for f in selected_files)
        
        # Always show encrypt action
        encrypt_action = QAction("Encrypt", menu)
        encrypt_action.triggered.connect(lambda: self.encrypt_files(selected_files))
        menu.addAction(encrypt_action)
        
        # Always show decrypt action (will show error if not encrypted)
        decrypt_action = QAction("Decrypt", menu)
        decrypt_action.triggered.connect(lambda: self.decrypt_files(selected_files))
        menu.addAction(decrypt_action)
        
        # Always show verify integrity action
        verify_action = QAction("Verify Integrity", menu)
        verify_action.triggered.connect(lambda: self.verify_files(selected_files))
        menu.addAction(verify_action)
    
    def encrypt_files(self, files: List[pathlib.Path]):
        """Encrypt selected files."""
        if not files:
            return
        
        # Filter out already encrypted files
        files_to_encrypt = [f for f in files if not self.encryption_engine.is_encrypted_file(f)]
        if not files_to_encrypt:
            QMessageBox.information(None, "Info", "All selected files are already encrypted.")
            return
        
        # Get encryption settings
        settings = self.settings_manager.load_settings()
        encryption_settings = settings.get('encryption', {})
        
        # Show password dialog
        password_dialog = PasswordDialog(
            parent=None,
            operation="encrypt",
            filename=f"Encrypt {len(files_to_encrypt)} file(s)"
        )
        
        if password_dialog.exec() != PasswordDialog.Accepted:
            return
        
        password = password_dialog.get_password()
        template_name = password_dialog.get_template_name()
        
        try:
            success_count = 0
            for file_path in files_to_encrypt:
                try:
                    # Get template settings
                    from utils.encryption_templates import EncryptionTemplateManager
                    template_manager = EncryptionTemplateManager()
                    template = template_manager.get_template(template_name)
                    
                    # Encrypt file
                    encrypted_path = self.encryption_engine.encrypt_file(
                        file_path, 
                        password,
                        algorithm=template.algorithm,
                        key_iterations=template.key_iterations
                    )
                    
                    if encrypted_path:
                        success_count += 1
                        
                except Exception as e:
                    QMessageBox.warning(
                        None, 
                        "Encryption Error", 
                        f"Failed to encrypt {file_path.name}: {str(e)}"
                    )
            
            if success_count > 0:
                self.status_message.emit(f"Successfully encrypted {success_count} file(s)")
                QMessageBox.information(
                    None, 
                    "Success", 
                    f"Successfully encrypted {success_count} file(s)"
                )
                
        except Exception as e:
            QMessageBox.critical(None, "Encryption Error", f"Encryption failed: {str(e)}")
    
    def decrypt_files(self, files: List[pathlib.Path]):
        """Decrypt selected files."""
        if not files:
            return
        
        # Filter for encrypted files
        encrypted_files = [f for f in files if self.encryption_engine.is_encrypted_file(f)]
        if not encrypted_files:
            QMessageBox.information(None, "Info", "No encrypted files selected.")
            return
        
        # Show decrypt dialog
        password_dialog = DecryptDialog(parent=None, filename=f"Decrypt {len(encrypted_files)} file(s)")
        if password_dialog.exec() != PasswordDialog.Accepted:
            return
        
        password = password_dialog.get_password()
        
        try:
            success_count = 0
            for file_path in encrypted_files:
                try:
                    decrypted_path = self.encryption_engine.decrypt_file(file_path, password)
                    if decrypted_path:
                        success_count += 1
                        
                except Exception as e:
                    QMessageBox.warning(
                        None, 
                        "Decryption Error", 
                        f"Failed to decrypt {file_path.name}: {str(e)}"
                    )
            
            if success_count > 0:
                self.status_message.emit(f"Successfully decrypted {success_count} file(s)")
                QMessageBox.information(
                    None, 
                    "Success", 
                    f"Successfully decrypted {success_count} file(s)"
                )
                
        except Exception as e:
            QMessageBox.critical(None, "Decryption Error", f"Decryption failed: {str(e)}")
    
    def verify_files(self, files: List[pathlib.Path]):
        """Verify integrity of selected files."""
        if not files:
            return
        
        encrypted_files = [f for f in files if self.encryption_engine.is_encrypted_file(f)]
        if not encrypted_files:
            QMessageBox.information(None, "Info", "No encrypted files to verify.")
            return
        
        # Show decrypt dialog for verification (same as decrypt)
        password_dialog = DecryptDialog(parent=None, filename=f"Verify {len(encrypted_files)} file(s)")
        if password_dialog.exec() != PasswordDialog.Accepted:
            return
        
        password = password_dialog.get_password()
        
        try:
            results = []
            for file_path in encrypted_files:
                try:
                    is_valid = self.encryption_engine.verify_encrypted_file(file_path, password)
                    results.append((file_path.name, is_valid))
                except Exception as e:
                    results.append((file_path.name, False))
            
            # Show results
            valid_count = sum(1 for _, valid in results if valid)
            invalid_count = len(results) - valid_count
            
            message = f"Verification Results:\n\n"
            message += f"Valid: {valid_count}\n"
            message += f"Invalid: {invalid_count}\n\n"
            
            if invalid_count > 0:
                message += "Invalid files:\n"
                for name, valid in results:
                    if not valid:
                        message += f"- {name}\n"
            
            QMessageBox.information(None, "Verification Results", message)
            self.status_message.emit(f"Verified {len(results)} file(s)")
            
        except Exception as e:
            QMessageBox.critical(None, "Verification Error", f"Verification failed: {str(e)}")