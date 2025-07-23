#!/usr/bin/env python3
import sys
import pathlib
import os

# Add src to path
sys.path.insert(0, 'src')

from core.encryption_engine import EncryptionEngine
from file_encryption_actions import FileEncryptionActions
from PySide6.QtWidgets import QApplication, QMenu

def test_encryption_detection():
    """Test if encrypted files are properly detected."""
    print("Testing encryption detection...")
    
    engine = EncryptionEngine()
    
    # Find any .encrypted files in current directory
    current_dir = pathlib.Path('.')
    encrypted_files = list(current_dir.rglob('*.encrypted'))
    
    if encrypted_files:
        print(f"Found {len(encrypted_files)} encrypted files:")
        for file in encrypted_files:
            is_encrypted = engine.is_encrypted_file(file)
            print(f"  {file}: {is_encrypted}")
    else:
        print("No .encrypted files found in current directory")
        
    # Test with a regular file
    test_file = pathlib.Path('test_regular.txt')
    test_file.write_text('This is a test file')
    is_encrypted = engine.is_encrypted_file(test_file)
    print(f"Regular file {test_file}: {is_encrypted}")
    test_file.unlink()

def test_context_menu():
    """Test context menu creation."""
    print("\nTesting context menu creation...")
    
    app = QApplication(sys.argv)
    
    try:
        actions = FileEncryptionActions()
        menu = QMenu()
        
        # Test with regular file
        regular_file = pathlib.Path('test.txt')
        regular_file.write_text('test content')
        
        actions.add_encryption_actions(menu, [regular_file])
        print(f"Actions for regular file: {len(menu.actions())}")
        for action in menu.actions():
            print(f"  - {action.text()}")
        
        menu.clear()
        
        # Test with encrypted file (if exists)
        encrypted_files = list(pathlib.Path('.').rglob('*.encrypted'))
        if encrypted_files:
            actions.add_encryption_actions(menu, encrypted_files[:1])
            print(f"Actions for encrypted file: {len(menu.actions())}")
            for action in menu.actions():
                print(f"  - {action.text()}")
        else:
            print("No encrypted files found for testing")
            
        regular_file.unlink()
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_encryption_detection()
    test_context_menu()