#!/usr/bin/env python3
"""
Final test to verify context menu shows decrypt option for encrypted files.
"""

import sys
import os
import tempfile
import pathlib
from PySide6.QtWidgets import QApplication, QMenu
from PySide6.QtCore import QTimer

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from file_encryption_actions import FileEncryptionActions
from encryption_engine import EncryptionEngine

def test_context_menu_decrypt_option():
    """Test that decrypt option appears in context menu for encrypted files."""
    print("Testing context menu decrypt option...")
    
    app = QApplication(sys.argv)
    
    # Create temporary test files
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = pathlib.Path(temp_dir)
        
        # Create a regular file
        regular_file = temp_path / "test.txt"
        regular_file.write_text("This is a test file")
        
        # Create an encrypted file
        encrypted_file = temp_path / "test.encrypted"
        engine = EncryptionEngine()
        
        # Encrypt the regular file
        password = "testpassword123"
        encrypted_path = engine.encrypt_file(regular_file, password, encrypted_file)
        
        print(f"Created encrypted file: {encrypted_path}")
        print(f"Encrypted file exists: {encrypted_path.exists()}")
        print(f"Is encrypted file: {engine.is_encrypted_file(encrypted_path)}")
        
        # Test context menu
        actions = FileEncryptionActions()
        menu = QMenu()
        
        # Test with regular file
        print("\nTesting context menu with regular file:")
        actions.add_encryption_actions(menu, [regular_file])
        actions_list = menu.actions()
        action_texts = [action.text() for action in actions_list if action.text()]
        print(f"Actions for regular file: {action_texts}")
        
        # Test with encrypted file
        print("\nTesting context menu with encrypted file:")
        menu2 = QMenu()
        actions.add_encryption_actions(menu2, [encrypted_path])
        actions_list2 = menu2.actions()
        action_texts2 = [action.text() for action in actions_list2 if action.text()]
        print(f"Actions for encrypted file: {action_texts2}")
        
        # Verify decrypt option appears
        has_decrypt = "Decrypt" in action_texts2
        has_verify = "Verify Integrity" in action_texts2
        
        print(f"\nResults:")
        print(f"Decrypt option appears: {has_decrypt}")
        print(f"Verify option appears: {has_verify}")
        
        if has_decrypt:
            print("✅ SUCCESS: Decrypt option appears in context menu for encrypted files")
            return True
        else:
            print("❌ FAILURE: Decrypt option does not appear")
            return False

if __name__ == "__main__":
    success = test_context_menu_decrypt_option()
    sys.exit(0 if success else 1)