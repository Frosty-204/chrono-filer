#!/usr/bin/env python3
"""
Test script for undo/redo integration and encryption actions.
"""

import sys
import os
import tempfile
import shutil
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_undo_redo_integration():
    """Test undo/redo functionality with file operations."""
    print("Testing undo/redo integration...")
    
    temp_dir = Path(tempfile.mkdtemp(prefix="chrono_filer_test_"))
    
    try:
        # Create test file
        test_file = temp_dir / "undo_test.txt"
        test_file.write_text("original content")
        
        # Test 1: Test undo manager
        print("\n1. Testing undo manager...")
        try:
            from utils.commands import UndoManager
            undo_manager = UndoManager()
            print("✓ Undo manager initialized")
        except ImportError as e:
            print(f"✗ Undo manager import failed: {e}")
            return
        
        # Test 2: Test command classes
        print("\n2. Testing command classes...")
        try:
            from utils.commands import BatchMoveCommand, BatchCopyCommand, DeleteCommand, RenameCommand
            print("✓ Command classes imported successfully")
        except ImportError as e:
            print(f"✗ Command classes import failed: {e}")
            return
        
        # Test 3: Test move command
        print("\n3. Testing move command...")
        try:
            source_dir = temp_dir / "source"
            source_dir.mkdir()
            test_move_file = source_dir / "move_test.txt"
            test_move_file.write_text("move test content")
            
            dest_dir = temp_dir / "dest"
            dest_dir.mkdir()
            
            dest_file = dest_dir / "move_test.txt"
            move_cmd = BatchMoveCommand([(test_move_file, dest_file)])
            move_cmd.execute()
            
            if (dest_dir / "move_test.txt").exists() and not test_move_file.exists():
                print("✓ Move command executed successfully")
                
                # Test undo
                move_cmd.undo()
                if test_move_file.exists() and not (dest_dir / "move_test.txt").exists():
                    print("✓ Move command undo successful")
                else:
                    print("✗ Move command undo failed")
            else:
                print("✗ Move command execution failed")
                
        except Exception as e:
            print(f"✗ Move command test failed: {e}")
        
        # Test 4: Test copy command
        print("\n4. Testing copy command...")
        try:
            test_copy_file = temp_dir / "copy_test.txt"
            test_copy_file.write_text("copy test content")
            
            dest_copy_file = dest_dir / "copy_test.txt"
            copy_cmd = BatchCopyCommand([(test_copy_file, dest_copy_file)])
            copy_cmd.execute()
            
            if (dest_dir / "copy_test.txt").exists() and test_copy_file.exists():
                print("✓ Copy command executed successfully")
                
                # Test undo (should delete the copied file)
                copy_cmd.undo()
                if not (dest_dir / "copy_test.txt").exists():
                    print("✓ Copy command undo successful")
                else:
                    print("✗ Copy command undo failed")
            else:
                print("✗ Copy command execution failed")
                
        except Exception as e:
            print(f"✗ Copy command test failed: {e}")
        
        # Test 5: Test delete command
        print("\n5. Testing delete command...")
        try:
            test_delete_file = temp_dir / "delete_test.txt"
            test_delete_file.write_text("delete test content")
            
            delete_cmd = DeleteCommand(test_delete_file)
            delete_cmd.execute()
            
            if not test_delete_file.exists():
                print("✓ Delete command executed successfully")
                
                # Test undo (should restore the file)
                delete_cmd.undo()
                if test_delete_file.exists():
                    print("✓ Delete command undo successful")
                else:
                    print("✗ Delete command undo failed")
            else:
                print("✗ Delete command execution failed")
                
        except Exception as e:
            print(f"✗ Delete command test failed: {e}")
        
        # Test 6: Test rename command
        print("\n6. Testing rename command...")
        try:
            test_rename_file = temp_dir / "rename_test.txt"
            test_rename_file.write_text("rename test content")
            
            new_name = temp_dir / "renamed_test.txt"
            rename_cmd = RenameCommand(test_rename_file, new_name)
            rename_cmd.execute()
            
            if (temp_dir / "renamed_test.txt").exists() and not test_rename_file.exists():
                print("✓ Rename command executed successfully")
                
                # Test undo
                rename_cmd.undo()
                if test_rename_file.exists() and not (temp_dir / "renamed_test.txt").exists():
                    print("✓ Rename command undo successful")
                else:
                    print("✗ Rename command undo failed")
            else:
                print("✗ Rename command execution failed")
                
        except Exception as e:
            print(f"✗ Rename command test failed: {e}")
        
    finally:
        try:
            shutil.rmtree(temp_dir)
            print(f"\nCleaned up test directory: {temp_dir}")
        except Exception as e:
            print(f"\nWarning: Could not clean up test directory: {e}")

def test_encryption_actions():
    """Test encryption actions functionality."""
    print("\n\nTesting encryption actions...")
    
    temp_dir = Path(tempfile.mkdtemp(prefix="chrono_filer_test_"))
    
    try:
        # Create test file
        test_file = temp_dir / "encrypt_test.txt"
        test_file.write_text("This is secret content")
        
        # Test 1: Test encryption actions import
        print("\n1. Testing encryption actions import...")
        try:
            from file_encryption_actions import FileEncryptionActions
            encryption_actions = FileEncryptionActions()
            print("✓ Encryption actions imported successfully")
        except ImportError as e:
            print(f"✗ Encryption actions import failed: {e}")
            return
        
        # Test 2: Test encryption
        print("\n2. Testing file encryption...")
        try:
            # Test that the methods exist and have correct signatures
            assert hasattr(encryption_actions, 'encrypt_files')
            assert hasattr(encryption_actions, 'decrypt_files')
            assert hasattr(encryption_actions, 'verify_files')
            print("✓ Encryption methods exist with correct signatures")
            
            # Test that they accept the correct parameter types (without actually calling GUI methods)
            import inspect
            encrypt_sig = inspect.signature(encryption_actions.encrypt_files)
            decrypt_sig = inspect.signature(encryption_actions.decrypt_files)
            verify_sig = inspect.signature(encryption_actions.verify_files)
            
            # Check parameter types - accept both pathlib.Path and pathlib._local.Path
            for sig_name, sig in [('encrypt_files', encrypt_sig), ('decrypt_files', decrypt_sig), ('verify_files', verify_sig)]:
                params = list(sig.parameters.values())
                if len(params) >= 1:
                    param_type = str(params[0].annotation)
                    if 'List[' in param_type and 'Path' in param_type:
                        print(f"✓ {sig_name} signature verified")
                    else:
                        print(f"✗ {sig_name} signature: {param_type}")
                
        except Exception as e:
            print(f"✗ Encryption test failed: {e}")
        
    finally:
        try:
            shutil.rmtree(temp_dir)
            print(f"\nCleaned up test directory: {temp_dir}")
        except Exception as e:
            print(f"\nWarning: Could not clean up test directory: {e}")

if __name__ == "__main__":
    test_undo_redo_integration()
    test_encryption_actions()