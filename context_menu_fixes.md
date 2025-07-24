# Context Menu Fixes Required

## Issue Analysis

### 1. Copy/Move Functionality Missing
**Current State**: Lines 366-374 in `src/ui/widgets.py` show placeholder implementations that only display information dialogs.

**Required Fix**: Implement actual file copying and moving with:
- Directory selection dialog
- Progress indication
- Conflict resolution
- Undo support

### 2. Rename Dialog Issue
**Current State**: The rename function works but shows an inappropriate dialog message.

**Root Cause**: The error "File type associations could be expanded" appears to be a system-level message, not from our application. The actual issue might be in the import statement or error handling.

## Implementation Plan

### Fix 1: Implement Copy Functionality
```python
def copy_item(self, path_obj: pathlib.Path):
    """Copy a file or directory to a selected location."""
    target_dir = QFileDialog.getExistingDirectory(
        self, "Select Destination Directory", str(path_obj.parent)
    )
    
    if target_dir:
        try:
            target_path = pathlib.Path(target_dir) / path_obj.name
            if path_obj.is_dir():
                import shutil
                shutil.copytree(path_obj, target_path)
            else:
                import shutil
                shutil.copy2(path_obj, target_path)
            
            self.refresh_list()
            QMessageBox.information(self, "Success", f"Copied '{path_obj.name}' to '{target_dir}'")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to copy: {e}")
```

### Fix 2: Implement Move Functionality
```python
def move_item(self, path_obj: pathlib.Path):
    """Move a file or directory to a selected location."""
    target_dir = QFileDialog.getExistingDirectory(
        self, "Select Destination Directory", str(path_obj.parent)
    )
    
    if target_dir:
        try:
            target_path = pathlib.Path(target_dir) / path_obj.name
            if target_path.exists():
                reply = QMessageBox.question(
                    self, "File Exists",
                    f"'{path_obj.name}' already exists in target directory. Overwrite?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply != QMessageBox.StandardButton.Yes:
                    return
            
            # Move the file/directory
            path_obj.rename(target_path)
            self.refresh_list()
            
            # Add to undo manager
            if self.undo_manager:
                from ..utils.commands import MoveCommand
                command = MoveCommand(path_obj, target_path)
                self.undo_manager.add_command(command)
            
            QMessageBox.information(self, "Success", f"Moved '{path_obj.name}' to '{target_dir}'")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to move: {e}")
```

### Fix 3: Resolve Rename Dialog Issue
**Problem**: The rename dialog shows "File type associations could be expanded" which appears to be a system message.

**Solution**: Ensure proper error handling and message display:
```python
def rename_item(self, path_obj: pathlib.Path):
    """Rename a file or directory with proper error handling."""
    old_name = path_obj.name
    new_name, ok = QInputDialog.getText(
        self, "Rename", f"New name for '{old_name}':", text=old_name
    )
    
    if ok and new_name.strip() and new_name.strip() != old_name:
        new_name = new_name.strip()
        new_path = path_obj.parent / new_name
        
        try:
            # Check if target exists
            if new_path.exists():
                QMessageBox.warning(self, "Error", f"'{new_name}' already exists.")
                return
            
            # Perform rename
            old_path = path_obj
            path_obj.rename(new_path)
            self.refresh_list()
            
            # Add to undo manager
            if self.undo_manager:
                from ..utils.commands import RenameCommand
                command = RenameCommand(old_path, new_path)
                self.undo_manager.add_command(command)
            
            self.status_message.emit(f"'{old_name}' renamed to '{new_name}'.")
            QMessageBox.information(self, "Success", f"'{old_name}' renamed to '{new_name}'.")
            
        except PermissionError:
            QMessageBox.critical(self, "Error", "Permission denied. Check file permissions.")
        except OSError as e:
            QMessageBox.critical(self, "Error", f"Failed to rename: {e}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An unexpected error occurred: {e}")
```

## Additional Improvements

### Add MoveCommand to commands.py
```python
class MoveCommand(Command):
    def __init__(self, source_path: pathlib.Path, target_path: pathlib.Path):
        self.source_path = source_path
        self.target_path = target_path
    
    def execute(self):
        self.source_path.rename(self.target_path)
    
    def undo(self):
        self.target_path.rename(self.source_path)
    
    def description(self):
        return f"Move {self.source_path.name} to {self.target_path.parent}"
```

## Testing Checklist
- [ ] Copy single file to different directory
- [ ] Copy directory with contents
- [ ] Move single file to different directory
- [ ] Move directory with contents
- [ ] Test overwrite scenarios
- [ ] Test undo functionality
- [ ] Test error handling (permissions, disk space)
- [ ] Verify rename works without system messages