#!/usr/bin/env python3
"""
Simple test to verify the encryption fix works correctly.
"""

import tempfile
import pathlib
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from encryption_engine import EncryptionEngine

def test_simple_encryption():
    """Test basic encryption functionality."""
    print("Testing basic encryption...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = pathlib.Path(temp_dir)
        
        # Create test file
        test_file = temp_path / "test.txt"
        test_file.write_text("Hello, encryption world!")
        
        # Test encryption
        encryption_engine = EncryptionEngine()
        
        # Test 1: Basic encryption
        print("1. Testing basic file encryption...")
        encrypted_path = encryption_engine.encrypt_file(test_file, "test_password")
        assert encrypted_path.exists(), "Encrypted file not created"
        assert encrypted_path.suffix == ".encrypted", "Wrong extension"
        print(f"   ✓ Created: {encrypted_path}")
        
        # Test 2: Encryption detection
        print("2. Testing encryption detection...")
        is_encrypted = encryption_engine.is_encrypted_file(encrypted_path)
        assert is_encrypted, "Should detect encrypted file"
        print("   ✓ Detection works")
        
        # Test 3: Decryption
        print("3. Testing decryption...")
        decrypted_path = encryption_engine.decrypt_file(encrypted_path, "test_password")
        assert decrypted_path.exists(), "Decrypted file not created"
        
        content = decrypted_path.read_text()
        assert content == "Hello, encryption world!", "Content mismatch"
        print("   ✓ Decryption successful")
        
        # Test 4: Wrong password
        print("4. Testing wrong password...")
        try:
            encryption_engine.decrypt_file(encrypted_path, "wrong_password")
            assert False, "Should fail with wrong password"
        except ValueError as e:
            if "invalid password" in str(e).lower():
                print("   ✓ Wrong password correctly rejected")
            else:
                print(f"   ⚠ Unexpected error: {e}")
        
        print("\n🎉 All basic encryption tests passed!")
        return True

if __name__ == "__main__":
    try:
        test_simple_encryption()
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)