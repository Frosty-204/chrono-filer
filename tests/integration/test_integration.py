#!/usr/bin/env python3
"""
Integration test for encryption functionality in Chrono Filer.
This test verifies that encryption actions are properly integrated into the UI.
"""

import sys
import os
import tempfile
import pathlib
from PySide6.QtWidgets import QApplication

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from encryption_engine import EncryptionEngine
from settings_manager import SettingsManager

def test_encryption_engine():
    """Test the encryption engine directly."""
    print("Testing encryption engine...")
    
    # Create test data
    test_data = b"This is sensitive data that needs encryption"
    password = "test_password_123"
    
    # Create encryption engine
    engine = EncryptionEngine()
    
    # Test encryption and decryption
    encrypted_data = engine.encrypt_data(test_data, password)
    assert encrypted_data != test_data, "Data not actually encrypted"
    
    decrypted_data = engine.decrypt_data(encrypted_data, password)
    assert decrypted_data == test_data, "Decrypted data doesn't match original"
    
    # Test verification
    assert engine.verify_encrypted_data(encrypted_data), "Encrypted data verification failed"
    
    print("✓ Encryption engine test passed!")

def test_settings_integration():
    """Test that encryption settings are properly integrated."""
    print("Testing settings integration...")
    
    # Create settings manager
    settings = SettingsManager()
    
    # Test encryption settings
    assert hasattr(settings, 'encryption_enabled'), "Encryption enabled setting missing"
    assert hasattr(settings, 'default_encryption_template'), "Default encryption template setting missing"
    assert hasattr(settings, 'store_passwords_in_keyring'), "Keyring setting missing"
    
    # Test default values
    assert isinstance(settings.encryption_enabled, bool), "Encryption enabled not boolean"
    assert isinstance(settings.store_passwords_in_keyring, bool), "Keyring setting not boolean"
    
    print("✓ Settings integration test passed!")

def test_file_operations():
    """Test file-based encryption operations."""
    print("Testing file operations...")
    
    # Create temporary test directory
    with tempfile.TemporaryDirectory() as temp_dir:
        test_dir = pathlib.Path(temp_dir)
        
        # Create test file
        test_file = test_dir / "test.txt"
        test_file.write_text("This is a test file for encryption")
        
        # Test encryption engine file operations
        engine = EncryptionEngine()
        password = "test_password_123"
        
        # Encrypt file
        encrypted_file = test_dir / "test.txt.enc"
        engine.encrypt_file(str(test_file), str(encrypted_file), password)
        
        assert encrypted_file.exists(), "Encrypted file not created"
        assert encrypted_file.stat().st_size > 0, "Encrypted file is empty"
        
        # Decrypt file
        decrypted_file = test_dir / "test_decrypted.txt"
        engine.decrypt_file(str(encrypted_file), str(decrypted_file), password)
        
        assert decrypted_file.exists(), "Decrypted file not created"
        assert decrypted_file.read_text() == test_file.read_text(), "Decrypted content doesn't match original"
        
        # Verify encrypted file
        assert engine.verify_encrypted_file(str(encrypted_file)), "Encrypted file verification failed"
        
        print("✓ File operations test passed!")

if __name__ == "__main__":
    try:
        test_encryption_engine()
        test_settings_integration()
        test_file_operations()
        print("\n🎉 All integration tests passed!")
    except Exception as e:
        print(f"\n❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)