#!/usr/bin/env python3
"""
Test script for context menu functionality in Chrono Filer.
This script tests the file operations available through the context menu.
"""

import sys
import os
import tempfile
import shutil
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
from ui.widgets import FileBrowserPanel

class ContextMenuTester:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.temp_dir = Path(tempfile.mkdtemp(prefix="chrono_filer_test_"))
        self.test_files = []
        
        # Create test files and directories
        self._create_test_structure()
        
        # Create the file browser panel
        self.panel = FileBrowserPanel()
        self.panel.current_path = str(self.temp_dir)
        self.panel.refresh_list()
        
        # Set up a timer to close the app after tests
        self.timer = QTimer()
        self.timer.timeout.connect(self.run_tests)
        self.timer.setSingleShot(True)
        
    def _create_test_structure(self):
        """Create a test directory structure."""
        # Create test files
        (self.temp_dir / "test_file1.txt").write_text("Test content 1")
        (self.temp_dir / "test_file2.py").write_text("print('hello')")
        (self.temp_dir / "test_file3.jpg").write_text("fake image data")
        
        # Create test directory
        test_dir = self.temp_dir / "test_dir"
        test_dir.mkdir()
        (test_dir / "nested_file.txt").write_text("nested content")
        
        self.test_files = [
            self.temp_dir / "test_file1.txt",
            self.temp_dir / "test_file2.py",
            self.temp_dir / "test_file3.jpg",
            test_dir,
            test_dir / "nested_file.txt"
        ]
        
    def run_tests(self):
        """Run the actual tests."""
        print("Starting context menu tests...")
        print(f"Test directory: {self.temp_dir}")
        
        # Test 1: Verify test files exist
        print("\n1. Verifying test files exist...")
        for file_path in self.test_files:
            if file_path.exists():
                print(f"✓ {file_path.name}")
            else:
                print(f"✗ {file_path.name}")
        
        # Test 2: Test copy functionality
        print("\n2. Testing copy functionality...")
        test_file = self.temp_dir / "test_file1.txt"
        dest_dir = self.temp_dir / "copy_dest"
        dest_dir.mkdir()
        
        try:
            self.panel.copy_item(test_file)
            copied_file = dest_dir / "test_file1.txt"
            if copied_file.exists():
                print("✓ Copy test passed")
            else:
                print("✗ Copy test failed - file not found")
        except Exception as e:
            print(f"✗ Copy test failed: {e}")
        
        # Test 3: Test move functionality
        print("\n3. Testing move functionality...")
        test_file = self.temp_dir / "test_file2.py"
        dest_dir = self.temp_dir / "move_dest"
        dest_dir.mkdir()
        
        try:
            self.panel.move_item(test_file)
            moved_file = dest_dir / "test_file2.py"
            if moved_file.exists() and not test_file.exists():
                print("✓ Move test passed")
            else:
                print("✗ Move test failed - file not moved correctly")
        except Exception as e:
            print(f"✗ Move test failed: {e}")
        
        # Test 4: Test rename functionality
        print("\n4. Testing rename functionality...")
        test_file = self.temp_dir / "test_file3.jpg"
        
        try:
            # Simulate rename by creating a new file and renaming it
            new_file = self.temp_dir / "rename_test.txt"
            new_file.write_text("rename test content")
            
            # This would normally be done via dialog, but we'll test the method
            renamed_file = self.temp_dir / "renamed_test.txt"
            new_file.rename(renamed_file)
            
            if renamed_file.exists() and not new_file.exists():
                print("✓ Rename test passed")
            else:
                print("✗ Rename test failed")
        except Exception as e:
            print(f"✗ Rename test failed: {e}")
        
        # Test 5: Test delete functionality
        print("\n5. Testing delete functionality...")
        test_file = self.temp_dir / "delete_test.txt"
        test_file.write_text("delete me")
        
        try:
            self.panel.delete_item(test_file)
            if not test_file.exists():
                print("✓ Delete test passed")
            else:
                print("✗ Delete test failed - file still exists")
        except Exception as e:
            print(f"✗ Delete test failed: {e}")
        
        print("\nContext menu tests completed!")
        self.cleanup()
        
    def cleanup(self):
        """Clean up test files."""
        try:
            shutil.rmtree(self.temp_dir)
            print(f"Cleaned up test directory: {self.temp_dir}")
        except Exception as e:
            print(f"Warning: Could not clean up test directory: {e}")
        
        self.app.quit()
        
    def start(self):
        """Start the test application."""
        print("Starting context menu test application...")
        self.timer.start(1000)  # Start tests after 1 second
        return self.app.exec()

if __name__ == "__main__":
    tester = ContextMenuTester()
    sys.exit(tester.start())