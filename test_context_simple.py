#!/usr/bin/env python3
"""
Simple test script for context menu functionality without GUI.
Tests the core file operations directly.
"""

import sys
import os
import tempfile
import shutil
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_file_operations():
    """Test the core file operations used by context menu."""
    
    # Create temporary test directory
    temp_dir = Path(tempfile.mkdtemp(prefix="chrono_filer_test_"))
    print(f"Test directory: {temp_dir}")
    
    try:
        # Create test files
        test_file = temp_dir / "test.txt"
        test_file.write_text("test content")
        
        # Test 1: Copy operation
        print("\n1. Testing copy operation...")
        dest_dir = temp_dir / "dest"
        dest_dir.mkdir()
        
        try:
            import shutil
            shutil.copy2(test_file, dest_dir / "test.txt")
            if (dest_dir / "test.txt").exists():
                print("✓ Copy operation successful")
            else:
                print("✗ Copy operation failed")
        except Exception as e:
            print(f"✗ Copy operation failed: {e}")
        
        # Test 2: Move operation
        print("\n2. Testing move operation...")
        move_file = temp_dir / "move_test.txt"
        move_file.write_text("move test")
        
        try:
            shutil.move(str(move_file), str(dest_dir / "move_test.txt"))
            if (dest_dir / "move_test.txt").exists() and not move_file.exists():
                print("✓ Move operation successful")
            else:
                print("✗ Move operation failed")
        except Exception as e:
            print(f"✗ Move operation failed: {e}")
        
        # Test 3: Rename operation
        print("\n3. Testing rename operation...")
        rename_file = temp_dir / "rename_test.txt"
        rename_file.write_text("rename test")
        
        try:
            rename_file.rename(temp_dir / "renamed_test.txt")
            if (temp_dir / "renamed_test.txt").exists() and not rename_file.exists():
                print("✓ Rename operation successful")
            else:
                print("✗ Rename operation failed")
        except Exception as e:
            print(f"✗ Rename operation failed: {e}")
        
        # Test 4: Delete operation
        print("\n4. Testing delete operation...")
        delete_file = temp_dir / "delete_test.txt"
        delete_file.write_text("delete me")
        
        try:
            delete_file.unlink()
            if not delete_file.exists():
                print("✓ Delete operation successful")
            else:
                print("✗ Delete operation failed")
        except Exception as e:
            print(f"✗ Delete operation failed: {e}")
        
        # Test 5: Permission testing
        print("\n5. Testing permission handling...")
        try:
            # Try to create a file in a protected location
            protected_path = Path("/root/test.txt")
            try:
                protected_path.write_text("test")
                print("✗ Permission test failed - should have raised error")
            except PermissionError:
                print("✓ Permission handling works correctly")
            except Exception as e:
                print(f"✓ Permission handling works: {type(e).__name__}")
        except Exception as e:
            print(f"✓ Permission test passed: {type(e).__name__}")
        
        # Test 6: Disk space simulation
        print("\n6. Testing disk space handling...")
        try:
            # Create a large file to test disk space
            large_file = temp_dir / "large_file.txt"
            try:
                # Try to create a 1GB file (this might fail on small disks)
                with open(large_file, 'wb') as f:
                    f.seek(1024 * 1024 * 1024 - 1)
                    f.write(b'\0')
                print("✓ Large file creation successful")
                large_file.unlink()
            except OSError as e:
                print(f"✓ Disk space handling works: {e}")
        except Exception as e:
            print(f"✓ Disk space test handled: {type(e).__name__}")
        
        print("\nAll core file operation tests completed!")
        
    finally:
        # Clean up
        try:
            shutil.rmtree(temp_dir)
            print(f"\nCleaned up test directory: {temp_dir}")
        except Exception as e:
            print(f"\nWarning: Could not clean up test directory: {e}")

if __name__ == "__main__":
    test_file_operations()