#!/usr/bin/env python3
"""
Test script to verify context menu integration for encryption/decryption.
"""

import os
import tempfile
import pathlib
from PySide6.QtWidgets import QApplication, QMenu
from src.file_encryption_actions import FileEncryptionActions
from src.encryption_engine import EncryptionEngine

def test_context_menu_integration():
    """Test context menu integration for encryption/decryption."""
    
    # Create QApplication (required for Qt widgets)
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    
    # Create temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = pathlib.Path(temp_dir)
        
        # Create test files
        normal_file = temp_path / "normal.txt"
        normal_file.write_text("This is a normal file")
        
        encrypted_file = temp_path / "encrypted.txt.encrypted"
        
        # Initialize encryption engine
        engine = EncryptionEngine()
        
        # Create encrypted file
        password = "test123"
        engine.encrypt_file(normal_file, password, encrypted_file)
        
        print("=== Testing Context Menu Integration ===")
        
        # Create encryption actions
        encryption_actions = FileEncryptionActions()
        
        # Test 1: Normal file should show encrypt option
        print("\n1. Testing normal file context menu:")
        menu1 = QMenu()
        encryption_actions.add_encryption_actions(menu1, [normal_file])
        
        actions1 = [action.text() for action in menu1.actions() if action.text()]
        print(f"   Available actions: {actions1}")
        
        has_encrypt = any("Encrypt" in text for text in actions1)
        has_decrypt = any("Decrypt" in text for text in actions1)
        
        if has_encrypt and not has_decrypt:
            print("   ✓ Normal file shows Encrypt option correctly")
        else:
            print("   ✗ Normal file context menu issue")
            return False
        
        # Test 2: Encrypted file should show decrypt option
        print("\n2. Testing encrypted file context menu:")
        menu2 = QMenu()
        encryption_actions.add_encryption_actions(menu2, [encrypted_file])
        
        actions2 = [action.text() for action in menu2.actions() if action.text()]
        print(f"   Available actions: {actions2}")
        
        has_encrypt = any("Encrypt" in text for text in actions2)
        has_decrypt = any("Decrypt" in text for text in actions2)
        
        if has_decrypt and not has_encrypt:
            print("   ✓ Encrypted file shows Decrypt option correctly")
        else:
            print("   ✗ Encrypted file context menu issue")
            return False
        
        # Test 3: Mixed selection should show both options
        print("\n3. Testing mixed selection context menu:")
        menu3 = QMenu()
        encryption_actions.add_encryption_actions(menu3, [normal_file, encrypted_file])
        
        actions3 = [action.text() for action in menu3.actions() if action.text()]
        print(f"   Available actions: {actions3}")
        
        has_encrypt = any("Encrypt" in text for text in actions3)
        has_decrypt = any("Decrypt" in text for text in actions3)
        
        if has_encrypt and has_decrypt:
            print("   ✓ Mixed selection shows both Encrypt and Decrypt options")
        else:
            print("   ✗ Mixed selection context menu issue")
            return False
        
        # Test 4: Verify file detection
        print("\n4. Testing file detection:")
        is_encrypted = engine.is_encrypted_file(encrypted_file)
        is_normal_encrypted = engine.is_encrypted_file(normal_file)
        
        if is_encrypted and not is_normal_encrypted:
            print("   ✓ File detection works correctly")
        else:
            print("   ✗ File detection issue")
            return False
        
        print("\n=== All Context Menu Tests Passed! ===")
        return True

if __name__ == "__main__":
    success = test_context_menu_integration()
    if success:
        print("\n🎉 All context menu integration tests passed!")
    else:
        print("\n❌ Some context menu tests failed!")
        exit(1)