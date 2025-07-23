#!/usr/bin/env python3
"""
Test script to verify context menu shows decrypt option for encrypted files.
"""

import sys
import pathlib
import tempfile
import os
from PySide6.QtWidgets import QApplication, QMenu
from src.encryption_engine import EncryptionEngine
from src.file_encryption_actions import FileEncryptionActions

def test_context_menu_decrypt():
    """Test that decrypt option appears in context menu for encrypted files."""
    
    # Create QApplication
    app = QApplication(sys.argv)
    
    # Create temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = pathlib.Path(temp_dir)
        
        # Create encryption engine
        encryption_engine = EncryptionEngine()
        
        # Create test file
        test_file = temp_path / "test.txt"
        test_file.write_text("This is a test file for encryption")
        
        # Create encrypted file
        password = "testpassword123"
        encrypted_file = encryption_engine.encrypt_file(test_file, password)
        
        print(f"Created encrypted file: {encrypted_file}")
        print(f"File exists: {encrypted_file.exists()}")
        print(f"File extension: {encrypted_file.suffix}")
        
        # Test if file is detected as encrypted
        is_encrypted = encryption_engine.is_encrypted_file(encrypted_file)
        print(f"is_encrypted_file result: {is_encrypted}")
        
        # Test context menu
        encryption_actions = FileEncryptionActions()
        menu = QMenu()
        
        # Test with encrypted file
        selected_files = [encrypted_file]
        encryption_actions.add_encryption_actions(menu, selected_files)
        
        # Check menu actions
        actions = menu.actions()
        action_texts = [action.text() for action in actions]
        print(f"Context menu actions: {action_texts}")
        
        # Verify decrypt action is present
        has_decrypt = "Decrypt" in action_texts
        print(f"Decrypt action present: {has_decrypt}")
        
        # Test with regular file
        regular_menu = QMenu()
        encryption_actions.add_encryption_actions(regular_menu, [test_file])
        regular_actions = [action.text() for action in regular_menu.actions()]
        print(f"Regular file actions: {regular_actions}")
        
        return has_decrypt

if __name__ == "__main__":
    try:
        result = test_context_menu_decrypt()
        if result:
            print("✅ SUCCESS: Decrypt option appears in context menu for encrypted files")
        else:
            print("❌ FAILED: Decrypt option missing from context menu")
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()