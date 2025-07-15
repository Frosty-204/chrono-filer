# src/commands.py
import shutil
import pathlib
from typing import List, Tuple
from PySide6.QtCore import QObject, Signal, QTimer

class Command:
    """Base class for a command."""
    def execute(self):
        raise NotImplementedError

    def undo(self):
        raise NotImplementedError

class BatchMoveCommand(Command):
    """Represents a batch of file move/rename operations."""
    def __init__(self, operations: List[Tuple[pathlib.Path, pathlib.Path]]):
        # operations is a list of (source_path, destination_path) tuples
        self.operations = operations
        self.description = f"Moved {len(operations)} file(s)"

    def execute(self):
        """
        Executes the batch move.
        Note: In our current design, the move has already happened in the engine.
        This command object will be created *after* the successful operation,
        so its main purpose is to hold the data needed for the undo.
        The `execute` method here is more for the "redo" functionality.
        """

        for src, dest in self.operations:
            # For a "redo", the file is back at the original source.
            # We need to ensure the destination parent directory exists.
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(dest))


    def undo(self):
        """
        Undoes the batch move by moving files from their destination back to their original source.
        This is done in reverse order to handle directory creations/deletions properly.
        """

        for src, dest in reversed(self.operations):
            # For an "undo", the file is at the destination. We move it back to the source.
            # Ensure the original source parent directory exists.
            src.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(dest), str(src))


class BatchCopyCommand(Command):
    """Represents a batch of file copy operations."""
    def __init__(self, operations: List[Tuple[pathlib.Path, pathlib.Path]]):
        # operations is a list of (source_path, destination_path) tuples
        self.operations = operations
        self.description = f"Copied {len(operations)} file(s)"

    def execute(self):
        """
        Executes the batch copy.
        Note: In our current design, the copy has already happened in the engine.
        This command object will be created *after* the successful operation,
        so its main purpose is to hold the data needed for the undo.
        The `execute` method here is more for the "redo" functionality.
        """
        for src, dest in self.operations:
            # For a "redo", we need to copy the file again from source to destination.
            # We need to ensure the destination parent directory exists.
            dest.parent.mkdir(parents=True, exist_ok=True)
            # Only copy if the source still exists and destination doesn't exist
            if src.exists() and not dest.exists():
                shutil.copy2(str(src), str(dest))

    def undo(self):
        """
        Undoes the batch copy by deleting the copied files.
        This is done in reverse order to handle directory cleanup properly.
        """
        for src, dest in reversed(self.operations):
            # For an "undo", we need to delete the copied file at the destination.
            try:
                if dest.exists():
                    dest.unlink()
                # Try to clean up empty directories
                try:
                    parent = dest.parent
                    # Only remove if it's empty and not the root directory
                    if parent != parent.parent and not any(parent.iterdir()):
                        parent.rmdir()
                except OSError:
                    pass  # Directory not empty or can't be removed, that's fine
            except Exception as e:
                print(f"Error deleting copied file {dest}: {e}")

class CreateFolderCommand(Command):
    """Represents a folder creation operation."""
    def __init__(self, folder_path: pathlib.Path):
        self.folder_path = folder_path
        self.description = f"Created folder '{folder_path.name}'"

    def execute(self):
        """Creates the folder."""
        self.folder_path.mkdir(parents=True, exist_ok=True)

    def undo(self):
        """Removes the created folder if it's empty."""
        try:
            if self.folder_path.exists() and self.folder_path.is_dir():
                self.folder_path.rmdir()  # Only removes if empty
        except OSError:
            pass  # Folder not empty or can't be removed

class RenameCommand(Command):
    """Represents a file/folder rename operation."""
    def __init__(self, old_path: pathlib.Path, new_path: pathlib.Path):
        self.old_path = old_path
        self.new_path = new_path
        self.description = f"Renamed '{old_path.name}' to '{new_path.name}'"

    def execute(self):
        """Renames from old_path to new_path."""
        self.old_path.rename(self.new_path)

    def undo(self):
        """Renames back from new_path to old_path."""
        if self.new_path.exists():
            self.new_path.rename(self.old_path)

class DeleteCommand(Command):
    """Represents a file/folder deletion operation."""
    def __init__(self, item_path: pathlib.Path):
        self.item_path = item_path
        self.was_directory = item_path.is_dir()
        self.description = f"Deleted '{item_path.name}'"

        # For undo, we'll need to store the item's content
        # This is a simplified version - full implementation would need to backup the content
        self.backup_content = None
        if not self.was_directory:
            try:
                self.backup_content = item_path.read_bytes()
            except Exception:
                pass

    def execute(self):
        """Deletes the file or directory."""
        if self.item_path.exists():
            if self.was_directory:
                shutil.rmtree(self.item_path)
            else:
                self.item_path.unlink()

    def undo(self):
        """Attempts to restore the deleted item."""
        if not self.item_path.exists():
            if self.was_directory:
                self.item_path.mkdir(parents=True, exist_ok=True)
            else:
                if self.backup_content is not None:
                    self.item_path.parent.mkdir(parents=True, exist_ok=True)
                    self.item_path.write_bytes(self.backup_content)

class UndoManager(QObject):
    """Manages the undo and redo stacks and emits signals when their state changes."""
    # Signal to enable/disable Undo/Redo actions in the UI
    stack_changed = Signal(bool, bool)  # (can_undo, can_redo)
    command_executed = Signal(str)

    # New signals for better UI performance
    batch_operation_started = Signal()
    batch_operation_finished = Signal()

    def __init__(self, max_undo_levels: int = 50):
        super().__init__()
        self.undo_stack: List[Command] = []
        self.redo_stack: List[Command] = []
        self.max_undo_levels = max_undo_levels

        # Debounce timer for UI updates
        self._update_timer = QTimer()
        self._update_timer.setSingleShot(True)
        self._update_timer.timeout.connect(self._emit_stack_changed)

    def add_command(self, command: Command):
        """Adds a new, executed command to the undo stack."""
        self.undo_stack.append(command)
        self.redo_stack.clear()  # Any new action clears the redo stack

        # Limit stack size to prevent unbounded growth
        if len(self.undo_stack) > self.max_undo_levels:
            self.undo_stack.pop(0)  # Remove oldest command

        self._schedule_ui_update()

    def undo(self):
        """Perform undo operation."""
        if not self.undo_stack:
            return

        # Signal that we're starting a batch operation
        self.batch_operation_started.emit()

        command = self.undo_stack.pop()
        try:
            command.undo()
            self.redo_stack.append(command)
            self.command_executed.emit(f"Undid: {command.description}")
        except Exception as e:
            # Restore command to undo stack on failure
            self.undo_stack.append(command)
            print(f"Error during undo for command '{command.description}': {e}")
            self.command_executed.emit(f"Undo Failed: {e}")
        finally:
            # Signal that batch operation is complete
            self.batch_operation_finished.emit()
            self._schedule_ui_update()

    def redo(self):
        """Perform redo operation."""
        if not self.redo_stack:
            return

        # Signal that we're starting a batch operation
        self.batch_operation_started.emit()

        command = self.redo_stack.pop()
        try:
            command.execute()
            self.undo_stack.append(command)
            self.command_executed.emit(f"Redid: {command.description}")
        except Exception as e:
            # Restore command to redo stack on failure
            self.redo_stack.append(command)
            print(f"Error during redo for command '{command.description}': {e}")
            self.command_executed.emit(f"Redo Failed: {e}")
        finally:
            # Signal that batch operation is complete
            self.batch_operation_finished.emit()
            self._schedule_ui_update()

    def _schedule_ui_update(self):
        """Schedule UI update with debouncing to avoid excessive updates."""
        # Use a short delay to batch multiple rapid operations
        self._update_timer.start(10)  # 10ms delay

    def _emit_stack_changed(self):
        """Emit stack changed signal."""
        can_undo = len(self.undo_stack) > 0
        can_redo = len(self.redo_stack) > 0
        self.stack_changed.emit(can_undo, can_redo)

    def can_undo(self) -> bool:
        """Check if undo is possible."""
        return len(self.undo_stack) > 0

    def can_redo(self) -> bool:
        """Check if redo is possible."""
        return len(self.redo_stack) > 0

    def clear_history(self):
        """Clear undo/redo history to free memory."""
        self.undo_stack.clear()
        self.redo_stack.clear()
        self._schedule_ui_update()

    def get_stack_sizes(self) -> tuple:
        """Get current stack sizes for debugging."""
        return len(self.undo_stack), len(self.redo_stack)
