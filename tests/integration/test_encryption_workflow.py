#!/usr/bin/env python3
"""
Test script to verify the complete encryption/decryption workflow.
This tests the fix for the "'PosixPath' object has no attribute 'encode'" error
and ensures the encryption/decryption flow works correctly.
"""

import tempfile
import pathlib
import shutil
import os
from src.encryption_engine import EncryptionEngine
from src.compression_engine import CompressionEngine

def test_encryption_workflow():
    """Test the complete encryption workflow."""
    print("Testing encryption workflow...")
    
    # Create temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = pathlib.Path(temp_dir)
        
        # Create test files
        test_file = temp_path / "test.txt"
        test_file.write_text("This is a test file for encryption testing.")
        
        # Create test archive
        archive_path = temp_path / "test_archive.zip"
        
        # Test 1: Create archive and encrypt
        print("1. Testing archive creation + encryption...")
        compression_engine = CompressionEngine()
        encryption_engine = EncryptionEngine()
        
        # Create archive
        created_files = compression_engine.create_archive(
            [test_file], archive_path, "zip", "normal"
        )
        assert created_files, "Failed to create archive"
        
        # Encrypt archive
        encrypted_path = encryption_engine.encrypt_archive(
            archive_path, "test_password"
        )
        assert encrypted_path.exists(), "Failed to create encrypted archive"
        assert encrypted_path.suffix == ".encrypted", "Wrong extension for encrypted file"
        
        print(f"   ✓ Created encrypted archive: {encrypted_path}")
        
        # Test 2: Verify encryption detection
        print("2. Testing encryption detection...")
        is_encrypted = encryption_engine.is_encrypted_file(encrypted_path)
        assert is_encrypted, "Failed to detect encrypted file"
        
        is_not_encrypted = encryption_engine.is_encrypted_file(test_file)
        assert not is_not_encrypted, "Incorrectly identified regular file as encrypted"
        
        print("   ✓ Encryption detection working correctly")
        
        # Test 3: Decrypt archive
        print("3. Testing decryption...")
        decrypted_path = encryption_engine.decrypt_file(
            encrypted_path, "test_password"
        )
        assert decrypted_path.exists(), "Failed to decrypt archive"
        assert decrypted_path.suffix == ".zip", "Wrong extension for decrypted archive"
        
        print(f"   ✓ Decrypted archive: {decrypted_path}")
        
        # Test 4: Verify decrypted archive can be extracted
        print("4. Testing archive extraction after decryption...")
        extract_dir = temp_path / "extracted"
        extract_dir.mkdir()
        
        extracted_files = compression_engine.extract_archive(
            decrypted_path, extract_dir
        )
        assert extracted_files, "Failed to extract decrypted archive"
        
        # Verify extracted content
        extracted_file = extract_dir / "test.txt"
        assert extracted_file.exists(), "Extracted file not found"
        assert extracted_file.read_text() == "This is a test file for encryption testing.", "Content mismatch"
        
        print("   ✓ Archive extraction successful")
        
        # Test 5: Test direct encrypted archive creation
        print("5. Testing direct encrypted archive creation...")
        direct_encrypted_path = temp_path / "direct_encrypted.zip"
        
        encrypted_direct = encryption_engine.create_encrypted_archive(
            [test_file], direct_encrypted_path, "direct_password", "zip", "normal"
        )
        assert encrypted_direct.exists(), "Failed to create direct encrypted archive"
        assert encrypted_direct.suffix == ".encrypted", "Wrong extension for direct encrypted archive"
        
        print(f"   ✓ Direct encrypted archive: {encrypted_direct}")
        
        # Test 6: Verify direct encrypted archive can be decrypted and extracted
        print("6. Testing direct encrypted archive workflow...")
        decrypted_direct = encryption_engine.decrypt_file(
            encrypted_direct, "direct_password"
        )
        assert decrypted_direct.exists(), "Failed to decrypt direct archive"
        
        extract_dir2 = temp_path / "extracted2"
        extract_dir2.mkdir()
        
        extracted_direct = compression_engine.extract_archive(
            decrypted_direct, extract_dir2
        )
        assert extracted_direct, "Failed to extract from direct encrypted archive"
        
        extracted_file2 = extract_dir2 / "test.txt"
        assert extracted_file2.exists(), "Extracted file not found from direct archive"
        assert extracted_file2.read_text() == "This is a test file for encryption testing.", "Content mismatch in direct archive"
        
        print("   ✓ Direct encrypted archive workflow successful")
        
        print("\n🎉 All encryption workflow tests passed!")
        return True

if __name__ == "__main__":
    try:
        test_encryption_workflow()
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        exit(1)