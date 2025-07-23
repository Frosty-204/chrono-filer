#!/usr/bin/env python3
"""
Test script to verify the encryption parameter order fix.
"""

import tempfile
import pathlib
from encryption_engine import EncryptionEngine

def test_encryption_parameter_order():
    """Test that encryption works with correct parameter order."""
    
    # Create temporary test files
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = pathlib.Path(temp_dir)
        
        # Create a test file
        test_file = temp_path / "test.txt"
        test_file.write_text("This is a test file for encryption testing")
        
        # Create encryption engine
        engine = EncryptionEngine()
        password = "testpassword123"
        
        # Test encryption with correct parameter order
        try:
            encrypted_file = temp_path / "test.txt.encrypted"
            result = engine.encrypt_file(
                test_file,           # source_path: pathlib.Path
                password,            # password: str
                encrypted_file       # output_path: pathlib.Path
            )
            
            print("✅ Encryption successful!")
            print(f"Encrypted file created: {result}")
            print(f"File exists: {result.exists()}")
            
            # Test decryption to verify the file is properly encrypted
            decrypted_file = temp_path / "decrypted.txt"
            engine.decrypt_file(
                result,              # encrypted_path: pathlib.Path
                password,            # password: str
                decrypted_file       # output_path: pathlib.Path
            )
            
            # Verify content
            original_content = test_file.read_text()
            decrypted_content = decrypted_file.read_text()
            
            if original_content == decrypted_content:
                print("✅ Decryption successful - content matches!")
                return True
            else:
                print("❌ Decryption failed - content mismatch!")
                return False
                
        except Exception as e:
            print(f"❌ Encryption failed: {e}")
            return False

if __name__ == "__main__":
    success = test_encryption_parameter_order()
    if success:
        print("\n🎉 All tests passed! The parameter order fix is working correctly.")
    else:
        print("\n💥 Tests failed!")