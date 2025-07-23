#!/usr/bin/env python3
"""
Test the compression + encryption workflow to verify the original issue is fixed.
"""

import tempfile
import pathlib
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from compression_engine import CompressionEngine
from encryption_engine import EncryptionEngine

def test_compression_encryption_workflow():
    """Test the compression + encryption workflow."""
    print("Testing compression + encryption workflow...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = pathlib.Path(temp_dir)
        
        # Create test files
        test_file1 = temp_path / "test1.txt"
        test_file1.write_text("This is test file 1 for compression and encryption.")
        
        test_file2 = temp_path / "test2.txt"
        test_file2.write_text("This is test file 2 for compression and encryption.")
        
        # Test 1: Create archive then encrypt
        print("1. Testing create archive then encrypt...")
        compression_engine = CompressionEngine()
        encryption_engine = EncryptionEngine()
        
        # Create archive
        archive_path = temp_path / "test_archive"
        created_files = compression_engine.create_archive(
            [test_file1, test_file2], archive_path, "zip", "normal"
        )
        
        assert created_files, "Failed to create archive"
        actual_archive = created_files[0]
        print(f"   ✓ Created archive: {actual_archive}")
        
        # Encrypt the archive
        encrypted_path = encryption_engine.encrypt_archive(actual_archive, "test_password")
        assert encrypted_path.exists(), "Failed to encrypt archive"
        assert str(encrypted_path).endswith(".encrypted"), "Wrong extension for encrypted file"
        print(f"   ✓ Encrypted archive: {encrypted_path}")
        
        # Test 2: Decrypt and extract
        print("2. Testing decrypt and extract...")
        decrypted_path = encryption_engine.decrypt_file(encrypted_path, "test_password")
        assert decrypted_path.exists(), "Failed to decrypt archive"
        print(f"   ✓ Decrypted archive: {decrypted_path}")
        
        # Extract archive
        extract_dir = temp_path / "extracted"
        extract_dir.mkdir()
        extracted_files = compression_engine.extract_archive(decrypted_path, extract_dir)
        
        assert extracted_files, "Failed to extract archive"
        assert len(extracted_files) >= 2, "Not all files extracted"
        
        # Verify content
        for extracted_file in extracted_files:
            if extracted_file.name == "test1.txt":
                content = extracted_file.read_text()
                assert "test file 1" in content, "Content mismatch in test1.txt"
            elif extracted_file.name == "test2.txt":
                content = extracted_file.read_text()
                assert "test file 2" in content, "Content mismatch in test2.txt"
        
        print("   ✓ Archive extraction and content verification successful")
        
        print("\n🎉 Compression + encryption workflow test passed!")
        return True

if __name__ == "__main__":
    try:
        test_compression_encryption_workflow()
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)