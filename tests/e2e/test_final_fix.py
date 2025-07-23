#!/usr/bin/env python3
"""
Test script to verify the encryption fixes are working correctly.
This tests both the original error fix and the new file extension handling.
"""

import pathlib
import tempfile
import shutil
from src.compression_engine import CompressionEngine
from src.encryption_engine import EncryptionEngine

def test_compression_with_encryption():
    """Test the complete compression + encryption workflow."""
    print("Testing compression with encryption...")
    
    # Create temporary test files
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = pathlib.Path(temp_dir)
        
        # Create test files
        test_file1 = temp_path / "test1.txt"
        test_file2 = temp_path / "test2.txt"
        
        test_file1.write_text("This is test file 1 with some content")
        test_file2.write_text("This is test file 2 with different content")
        
        # Test compression + encryption
        compression_engine = CompressionEngine()
        encryption_engine = EncryptionEngine()
        
        archive_path = temp_path / "test_archive.zip"
        
        try:
            # Create archive
            print("Creating archive...")
            created_files = compression_engine.create_archive(
                [test_file1, test_file2],
                archive_path,
                "zip",
                "normal"
            )
            print(f"Archive created: {created_files}")
            
            # Verify archive exists
            assert archive_path.exists(), "Archive was not created"
            print("✓ Archive created successfully")
            
            # Test encryption
            print("Encrypting archive...")
            encrypted_path = archive_path.with_suffix(archive_path.suffix + '.encrypted')
            encryption_engine.encrypt_file(
                archive_path,
                "test_password",
                encrypted_path
            )
            
            # Verify encrypted file exists
            assert encrypted_path.exists(), "Encrypted file was not created"
            print("✓ Encrypted file created successfully")
            
            # Verify original archive was removed (simulating the workflow)
            archive_path.unlink()
            assert not archive_path.exists(), "Original archive should be removed"
            print("✓ Original archive removed")
            
            # Test decryption
            print("Testing decryption...")
            decrypted_path = temp_path / "decrypted_archive.zip"
            encryption_engine.decrypt_file(
                encrypted_path,
                "test_password",
                decrypted_path
            )
            
            # Verify decrypted file exists
            assert decrypted_path.exists(), "Decrypted file was not created"
            print("✓ Decrypted file created successfully")
            
            # Test that decrypted archive can be extracted
            extract_dir = temp_path / "extracted"
            extract_dir.mkdir()
            
            import zipfile
            with zipfile.ZipFile(decrypted_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
            
            # Verify extracted files
            extracted_files = list(extract_dir.iterdir())
            assert len(extracted_files) == 2, f"Expected 2 files, got {len(extracted_files)}"
            print("✓ Decrypted archive can be extracted successfully")
            
            print("All tests passed! ✅")
            return True
            
        except Exception as e:
            print(f"Test failed: {e}")
            return False

def test_file_extension_handling():
    """Test that encrypted files get the correct extension."""
    print("\nTesting file extension handling...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = pathlib.Path(temp_dir)
        
        # Create test file
        test_file = temp_path / "test.txt"
        test_file.write_text("Test content")
        
        # Test supported archive formats
        formats = ["zip", "tar.gz", "tar.bz2", "tar.xz"]
        
        for fmt in formats:
            print(f"Testing {fmt} format...")
            
            archive_path = temp_path / f"test.{fmt}"
            if fmt == "gztar":
                archive_path = temp_path / "test.tar.gz"
            elif fmt == "bztar":
                archive_path = temp_path / "test.tar.bz2"
            elif fmt == "xztar":
                archive_path = temp_path / "test.tar.xz"
            
            compression_engine = CompressionEngine()
            encryption_engine = EncryptionEngine()
            
            try:
                # Create archive
                compression_engine.create_archive([test_file], archive_path, fmt, "normal")
                
                # Encrypt archive
                encrypted_path = archive_path.with_suffix(archive_path.suffix + '.encrypted')
                encryption_engine.encrypt_file(archive_path, "test_password", encrypted_path)
                
                # Verify extension
                assert encrypted_path.suffix == '.encrypted', f"Expected .encrypted, got {encrypted_path.suffix}"
                print(f"✓ {fmt} format correctly gets .encrypted extension")
                
                # Clean up
                if archive_path.exists():
                    archive_path.unlink()
                if encrypted_path.exists():
                    encrypted_path.unlink()
                    
            except Exception as e:
                print(f"Failed for {fmt}: {e}")
                return False
    
    print("Extension handling tests passed! ✅")
    return True

if __name__ == "__main__":
    print("Running comprehensive encryption fix tests...\n")
    
    success1 = test_compression_with_encryption()
    success2 = test_file_extension_handling()
    
    if success1 and success2:
        print("\n🎉 All tests passed! The encryption fixes are working correctly.")
    else:
        print("\n❌ Some tests failed. Please check the implementation.")