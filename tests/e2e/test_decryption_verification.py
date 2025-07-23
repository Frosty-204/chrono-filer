#!/usr/bin/env python3
"""
Test script to verify decryption and integrity verification functionality.
"""

import os
import tempfile
import pathlib
from src.encryption_engine import EncryptionEngine

def test_decryption_and_verification():
    """Test decryption and verification functionality."""
    
    # Create temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = pathlib.Path(temp_dir)
        
        # Create test file
        test_file = temp_path / "test_document.txt"
        test_content = b"This is a test document for encryption and decryption testing."
        test_file.write_bytes(test_content)
        
        # Initialize encryption engine
        engine = EncryptionEngine()
        
        # Test password
        password = "test_password_123"
        
        print("=== Testing Encryption ===")
        
        # Encrypt the file
        encrypted_file = engine.encrypt_file(test_file, password)
        print(f"✓ Encrypted file created: {encrypted_file}")
        print(f"✓ File exists: {encrypted_file.exists()}")
        
        print("\n=== Testing Decryption ===")
        
        # Decrypt the file
        try:
            decrypted_file = engine.decrypt_file(encrypted_file, password)
            print(f"✓ Decrypted file created: {decrypted_file}")
            print(f"✓ File exists: {decrypted_file.exists()}")
            
            # Verify content
            decrypted_content = decrypted_file.read_bytes()
            if decrypted_content == test_content:
                print("✓ Decrypted content matches original")
            else:
                print("✗ Decrypted content does not match original")
                return False
                
        except Exception as e:
            print(f"✗ Decryption failed: {e}")
            return False
        
        print("\n=== Testing Verification ===")
        
        # Test verification with correct password
        is_valid = engine.verify_encrypted_file(encrypted_file, password)
        if is_valid:
            print("✓ Verification with correct password: PASSED")
        else:
            print("✗ Verification with correct password: FAILED")
            return False
        
        # Test verification with incorrect password
        is_valid = engine.verify_encrypted_file(encrypted_file, "wrong_password")
        if not is_valid:
            print("✓ Verification with incorrect password: FAILED (as expected)")
        else:
            print("✗ Verification with incorrect password: PASSED (unexpected)")
            return False
        
        print("\n=== Testing Edge Cases ===")
        
        # Test with wrong password for decryption
        try:
            engine.decrypt_file(encrypted_file, "wrong_password")
            print("✗ Decryption with wrong password should have failed")
            return False
        except ValueError as e:
            if "invalid password" in str(e).lower():
                print("✓ Decryption with wrong password correctly failed")
            else:
                print(f"✗ Unexpected error: {e}")
                return False
        
        print("\n=== All Tests Passed! ===")
        return True

if __name__ == "__main__":
    success = test_decryption_and_verification()
    if success:
        print("\n🎉 All decryption and verification tests passed!")
    else:
        print("\n❌ Some tests failed!")
        exit(1)