# src/widgets.py
import os
import pathlib
import datetime
import mimetypes
from dataclasses import dataclass
from typing import Optional, List, Tuple

from PySide6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QListWidget, QListWidgetItem,
    QStyle, QGridLayout, QTextEdit,
    QSizePolicy, QSpacerItem, QStackedWidget,
    QGroupBox, QFormLayout, QComboBox, QDateEdit,
    QSpinBox, QCheckBox, QScrollArea, QDialog,
    QTableWidget, QTableWidgetItem, QAbstractItemView, QMessageBox,
    QFileDialog, QTabWidget, QMenu, QInputDialog

)
from PySide6.QtGui import QPalette, QColor, QPixmap, QKeySequence, QShortcut

from PySide6.QtCore import Qt, Signal, QDate

@dataclass
class OrganizationSettings:
    # Common settings for both modes
    name_filter_text: str = ""
    name_filter_type: str = "Contains"
    type_filter_text: str = ""
    created_after_date: Optional[datetime.date] = None
    modified_before_date: Optional[datetime.date] = None
    size_min_kb: int = 0
    size_max_kb: int = -1
    conflict_resolution: str = "Skip"  # "Overwrite", "Rename with Suffix"
    dry_run: bool = True
    process_recursively: bool = False
    operation_type: str = "Move"  # "Move", "Copy"

    # Organize-specific settings
    structure_template: str = "[YYYY]/[MM]/[Filename].[Ext]"
    target_base_directory: Optional[pathlib.Path] = None

    # Rename-specific settings
    rename_template: str = "[Filename]_[Num]"
    rename_start_number: int = 1
    rename_template_padding: int = 4


class PlaceholderWidget(QWidget):
    def __init__(self, name, color_name="lightgray", parent=None):
        super().__init__(parent)
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor(color_name))
        self.setPalette(palette)

        layout = QVBoxLayout(self)
        label = QLabel(f"{name}\n(Placeholder)")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)
        self.setLayout(layout)

# --- New FileBrowserPanel Implementation ---
class FileBrowserPanel(QWidget):

    # Define the custom signals
    # It will emit a pathlib.Path object, or None if no valid item is selected
    selection_changed = Signal(object) # Use 'object' to allow sending pathlib.Path or None
    status_message = Signal(str) # Signal to send status messages to main window

    def __init__(self, undo_manager=None, parent=None):
        super().__init__(parent)
        self.current_path = str(pathlib.Path.home()) # Start in user's home directory
        self.undo_manager = undo_manager

        self.layout = QVBoxLayout(self)

        # Path navigation bar
        nav_bar_layout = QHBoxLayout()
        self.up_button = QPushButton()
        # Using a standard icon
        self.up_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogToParent))
        self.up_button.setToolTip("Go to parent directory")

        self.path_edit = QLineEdit(self.current_path)

        nav_bar_layout.addWidget(self.up_button)
        nav_bar_layout.addWidget(self.path_edit)
        self.layout.addLayout(nav_bar_layout)

        # Toolbar with file operations
        toolbar_layout = QHBoxLayout()

        self.create_folder_button = QPushButton("New Folder")
        self.create_folder_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogNewFolder))
        self.create_folder_button.setToolTip("Create new folder")
        self.create_folder_button.clicked.connect(self.create_folder)

        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_BrowserReload))
        self.refresh_button.setToolTip("Refresh file list")
        self.refresh_button.clicked.connect(self.refresh_list)

        toolbar_layout.addWidget(self.create_folder_button)
        toolbar_layout.addWidget(self.refresh_button)
        toolbar_layout.addStretch()  # Push buttons to the left

        self.layout.addLayout(toolbar_layout)

        # File and directory list
        self.item_list_widget = QListWidget()
        self.item_list_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.layout.addWidget(self.item_list_widget)

        self.setLayout(self.layout)

        # Connect signals
        self.up_button.clicked.connect(self.go_up)
        self.path_edit.returnPressed.connect(self.path_changed) # Navigate when Enter is pressed in QLineEdit
        # self.item_list_widget.itemDoubleClicked.connect(self.item_double_clicked)
        self.item_list_widget.itemActivated.connect(self.item_double_clicked)
        self.item_list_widget.currentItemChanged.connect(self.on_current_item_changed)
        self.item_list_widget.customContextMenuRequested.connect(self.show_context_menu)

        # Setup keyboard shortcuts
        self._setup_shortcuts()

        self.refresh_list()

    def on_current_item_changed(self, current_item: QListWidgetItem, previous_item: QListWidgetItem):
            if current_item:
                path_obj = current_item.data(Qt.ItemDataRole.UserRole)
                if path_obj: # Ensure path_obj is not None (e.g. for error messages in list)
                    self.selection_changed.emit(path_obj)
                else:
                    self.selection_changed.emit(None) # Emit None if item has no valid path data
            else:
                self.selection_changed.emit(None) # Emit None if no item is selected

        # ... (refresh_list, go_up, path_changed, item_double_clicked methods remain mostly the same) ...
        # Small refinement in refresh_list: clear selection when list is refreshed

    def refresh_list(self):
        self.item_list_widget.clear()
        self.selection_changed.emit(None) # Explicitly emit None as selection is cleared
        self.path_edit.setText(self.current_path) # Ensure QLineEdit is up to date

        try:
            path_obj = pathlib.Path(self.current_path)
            if not path_obj.exists():
                # Handle case where path doesn't exist (e.g., user typed invalid path)
                error_item = QListWidgetItem("Path does not exist.")
                error_item.setForeground(Qt.GlobalColor.red)
                self.item_list_widget.addItem(error_item)
                return

            if not os.access(str(path_obj), os.R_OK):
                # Handle case where path is not readable
                error_item = QListWidgetItem("Permission denied.")
                error_item.setForeground(Qt.GlobalColor.red)
                self.item_list_widget.addItem(error_item)
                return

            # List directories first, then files
            items_to_add = []
            for entry in path_obj.iterdir():
                item = QListWidgetItem(entry.name)
                item.setData(Qt.ItemDataRole.UserRole, entry) # Store the Path object with the item

                icon_type = QStyle.StandardPixmap.SP_FileIcon
                if entry.is_dir():
                    icon_type = QStyle.StandardPixmap.SP_DirIcon

                item.setIcon(self.style().standardIcon(icon_type))
                items_to_add.append((entry.is_dir(), item)) # Tuple for sorting: (is_dir, item)

            # Sort: directories first (True > False), then by name alphabetically
            items_to_add.sort(key=lambda x: (not x[0], x[1].text().lower()))

            for _, item_widget in items_to_add:
                self.item_list_widget.addItem(item_widget)

        except Exception as e:
            # Catch-all for other potential errors (though specific checks above are better)
            error_item = QListWidgetItem(f"Error listing directory: {e}")
            error_item.setForeground(Qt.GlobalColor.red)
            self.item_list_widget.addItem(error_item)
            print(f"Error refreshing list: {e}")


    def go_up(self):
        path_obj = pathlib.Path(self.current_path)
        parent_path = path_obj.parent
        if parent_path != path_obj: # Check if we are not already at the root
            self.current_path = str(parent_path)
            self.refresh_list()

    def path_changed(self):
        new_path = self.path_edit.text()
        path_obj = pathlib.Path(new_path)
        if path_obj.is_dir(): # Check if it's a valid directory
            self.current_path = str(path_obj.resolve()) # Resolve to get absolute, cleaned path
            self.refresh_list()
        elif path_obj.exists():
             # If it exists but isn't a dir, maybe it's a file. Don't navigate, maybe select it in future?
             # For now, just indicate it's not a directory or revert.
            self.path_edit.setText(self.current_path) # Revert to old path
            # Optionally, show a status message
        else:
            # Path doesn't exist
            self.path_edit.setText(self.current_path) # Revert
            # Optionally, show a status message

    def item_double_clicked(self, item_widget: QListWidgetItem):
        path_obj = item_widget.data(Qt.ItemDataRole.UserRole) # Retrieve the stored Path object
        if path_obj and path_obj.is_dir():
            self.current_path = str(path_obj.resolve())
            self.refresh_list()
        # Later, you could add handling for opening files here

    def show_context_menu(self, position):
        """Show context menu for file operations."""
        item = self.item_list_widget.itemAt(position)
        menu = QMenu(self)

        # Always available actions
        create_folder_action = menu.addAction("Create Folder")
        create_folder_action.triggered.connect(self.create_folder)

        if item:
            path_obj = item.data(Qt.ItemDataRole.UserRole)
            if path_obj and path_obj.exists():
                menu.addSeparator()

                # Rename action
                rename_action = menu.addAction("Rename")
                rename_action.triggered.connect(lambda: self.rename_item(path_obj))

                # Delete action
                delete_action = menu.addAction("Delete")
                delete_action.triggered.connect(lambda: self.delete_item(path_obj))

                # Copy/Move actions (placeholder for now)
                menu.addSeparator()
                copy_action = menu.addAction("Copy")
                copy_action.triggered.connect(lambda: self.copy_item(path_obj))

                move_action = menu.addAction("Move")
                move_action.triggered.connect(lambda: self.move_item(path_obj))

        menu.exec(self.item_list_widget.mapToGlobal(position))

    def create_folder(self):
        """Create a new folder in the current directory."""
        folder_name, ok = QInputDialog.getText(self, "Create Folder", "Folder name:")
        if ok and folder_name.strip():
            folder_name = folder_name.strip()
            new_folder_path = pathlib.Path(self.current_path) / folder_name
            try:
                new_folder_path.mkdir(exist_ok=False)
                self.refresh_list()

                # Add to undo manager if available
                if self.undo_manager:
                    from commands import CreateFolderCommand
                    command = CreateFolderCommand(new_folder_path)
                    self.undo_manager.add_command(command)

                self.status_message.emit(f"Folder '{folder_name}' created successfully.")
                QMessageBox.information(self, "Success", f"Folder '{folder_name}' created successfully.")
            except FileExistsError:
                QMessageBox.warning(self, "Error", f"Folder '{folder_name}' already exists.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to create folder: {e}")

    def rename_item(self, path_obj: pathlib.Path):
        """Rename a file or directory."""
        old_name = path_obj.name
        new_name, ok = QInputDialog.getText(self, "Rename", f"New name for '{old_name}':", text=old_name)
        if ok and new_name.strip() and new_name.strip() != old_name:
            new_name = new_name.strip()
            new_path = path_obj.parent / new_name
            try:
                old_path = path_obj
                path_obj.rename(new_path)
                self.refresh_list()

                # Add to undo manager if available
                if self.undo_manager:
                    from commands import RenameCommand
                    command = RenameCommand(old_path, new_path)
                    self.undo_manager.add_command(command)

                self.status_message.emit(f"'{old_name}' renamed to '{new_name}'.")
                QMessageBox.information(self, "Success", f"'{old_name}' renamed to '{new_name}'.")
            except FileExistsError:
                QMessageBox.warning(self, "Error", f"'{new_name}' already exists.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to rename: {e}")

    def delete_item(self, path_obj: pathlib.Path):
        """Delete a file or directory."""
        item_type = "folder" if path_obj.is_dir() else "file"
        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Are you sure you want to delete the {item_type} '{path_obj.name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                # Create command before deletion for undo support
                if self.undo_manager:
                    from commands import DeleteCommand
                    command = DeleteCommand(path_obj)

                if path_obj.is_dir():
                    # For directories, check if empty
                    if any(path_obj.iterdir()):
                        reply = QMessageBox.question(
                            self, "Confirm Delete",
                            f"The folder '{path_obj.name}' is not empty. Delete it and all its contents?",
                            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                            QMessageBox.StandardButton.No
                        )
                        if reply == QMessageBox.StandardButton.Yes:
                            import shutil
                            shutil.rmtree(path_obj)
                        else:
                            return
                    else:
                        path_obj.rmdir()
                else:
                    path_obj.unlink()

                self.refresh_list()

                # Add to undo manager if available
                if self.undo_manager:
                    self.undo_manager.add_command(command)

                self.status_message.emit(f"'{path_obj.name}' deleted successfully.")
                QMessageBox.information(self, "Success", f"'{path_obj.name}' deleted successfully.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete: {e}")

    def copy_item(self, path_obj: pathlib.Path):
        """Copy a file or directory (placeholder for now)."""
        QMessageBox.information(self, "Feature Coming Soon",
                               f"Copy operation for '{path_obj.name}' will be implemented in the next update.")

    def move_item(self, path_obj: pathlib.Path):
        """Move a file or directory (placeholder for now)."""
        QMessageBox.information(self, "Feature Coming Soon",
                               f"Move operation for '{path_obj.name}' will be implemented in the next update.")

    def _setup_shortcuts(self):
        """Setup keyboard shortcuts for file operations."""
        # Create new folder - Ctrl+Shift+N
        new_folder_shortcut = QShortcut(QKeySequence("Ctrl+Shift+N"), self)
        new_folder_shortcut.activated.connect(self.create_folder)

        # Refresh - F5
        refresh_shortcut = QShortcut(QKeySequence("F5"), self)
        refresh_shortcut.activated.connect(self.refresh_list)

        # Delete - Delete key
        delete_shortcut = QShortcut(QKeySequence("Delete"), self)
        delete_shortcut.activated.connect(self._delete_selected_item)

        # Rename - F2
        rename_shortcut = QShortcut(QKeySequence("F2"), self)
        rename_shortcut.activated.connect(self._rename_selected_item)

        # Go up - Alt+Up
        go_up_shortcut = QShortcut(QKeySequence("Alt+Up"), self)
        go_up_shortcut.activated.connect(self.go_up)

    def _delete_selected_item(self):
        """Delete the currently selected item."""
        current_item = self.item_list_widget.currentItem()
        if current_item:
            path_obj = current_item.data(Qt.ItemDataRole.UserRole)
            if path_obj and path_obj.exists():
                self.delete_item(path_obj)

    def _rename_selected_item(self):
        """Rename the currently selected item."""
        current_item = self.item_list_widget.currentItem()
        if current_item:
            path_obj = current_item.data(Qt.ItemDataRole.UserRole)
            if path_obj and path_obj.exists():
                self.rename_item(path_obj)

# The other placeholder classes remain unchanged for now
# ... (FileBrowserPanel class above) ...

class MetadataPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QGridLayout(self) # Using QGridLayout for a structured label-value display
        self.setLayout(self.layout)

        self.name_label = QLabel("Name:")
        self.name_value = QLabel()
        self.type_label = QLabel("Type:")
        self.type_value = QLabel()
        self.size_label = QLabel("Size:")
        self.size_value = QLabel()
        self.created_label = QLabel("Created:")
        self.created_value = QLabel()
        self.modified_label = QLabel("Modified:")
        self.modified_value = QLabel()

        # Add widgets to the grid layout
        self.layout.addWidget(self.name_label, 0, 0)
        self.layout.addWidget(self.name_value, 0, 1)
        self.layout.addWidget(self.type_label, 1, 0)
        self.layout.addWidget(self.type_value, 1, 1)
        self.layout.addWidget(self.size_label, 2, 0)
        self.layout.addWidget(self.size_value, 2, 1)
        self.layout.addWidget(self.created_label, 3, 0)
        self.layout.addWidget(self.created_value, 3, 1)
        self.layout.addWidget(self.modified_label, 4, 0)
        self.layout.addWidget(self.modified_value, 4, 1)

        # Add a spacer to push content to the top if there's extra space
        self.layout.addItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding), 5, 0, 1, 2)
        self.layout.setColumnStretch(1, 1) # Allow the value column to expand

        self.clear_display() # Initialize with empty values

    def clear_display(self):
        self.name_value.setText("-")
        self.type_value.setText("-")
        self.size_value.setText("-")
        self.created_value.setText("-")
        self.modified_value.setText("-")

    def _format_size(self, num_bytes):
        if num_bytes is None: return "-"
        for unit in ['B', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB']:
            if abs(num_bytes) < 1024.0:
                return f"{num_bytes:3.1f} {unit}"
            num_bytes /= 1024.0
        return f"{num_bytes:.1f} YB"

    def _format_timestamp(self, timestamp):
        if timestamp is None: return "-"
        try:
            dt_object = datetime.datetime.fromtimestamp(timestamp)
            return dt_object.strftime("%Y-%m-%d %H:%M:%S")
        except TypeError:
            return "-"


    def update_metadata(self, path_obj: pathlib.Path = None):
        if not path_obj or not path_obj.exists():
            self.clear_display()
            return

        self.name_value.setText(path_obj.name)

        try:
            stat_info = path_obj.stat() # os.stat(path_obj) would also work

            # File Type
            if path_obj.is_dir():
                self.type_value.setText("Folder")
            else:
                mime_type, _ = mimetypes.guess_type(path_obj)
                self.type_value.setText(mime_type if mime_type else "File")

            # Size
            self.size_value.setText(self._format_size(stat_info.st_size if not path_obj.is_dir() else None))

            # Dates
            self.created_value.setText(self._format_timestamp(stat_info.st_ctime)) # ctime is platform-dependent (creation on Win, metadata change on Unix)
                                                                                # For more reliable creation time, OS-specific APIs might be needed
            self.modified_value.setText(self._format_timestamp(stat_info.st_mtime))

        except OSError as e:
            print(f"Error reading metadata for {path_obj}: {e}")
            self.clear_display()
            self.name_value.setText(f"Error: {e.strerror}") # Show OS error
        except Exception as e: # Catch any other potential error
            print(f"Unexpected error reading metadata for {path_obj}: {e}")
            self.clear_display()
            self.name_value.setText("Error reading metadata")


class PreviewPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_layout = QVBoxLayout(self)
        self.setLayout(self.main_layout)

        self.stacked_widget = QStackedWidget(self)
        self.main_layout.addWidget(self.stacked_widget)

        # Page 0: No preview / Placeholder
        self.no_preview_label = QLabel("Select a file to preview.")
        self.no_preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.stacked_widget.addWidget(self.no_preview_label)

        # Page 1: Image Preview
        self.image_scroll_area = QScrollArea(self) # For large images
        self.image_scroll_area.setWidgetResizable(True)
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_scroll_area.setWidget(self.image_label)
        self.stacked_widget.addWidget(self.image_scroll_area)

        # Page 2: Text Preview
        self.text_edit = QTextEdit(self)
        self.text_edit.setReadOnly(True)
        self.stacked_widget.addWidget(self.text_edit)

        # Page 3: Unsupported file type
        self.unsupported_label = QLabel("Preview not available for this file type.")
        self.unsupported_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.stacked_widget.addWidget(self.unsupported_label)

        # Page 4: Error display  <--- NEW PAGE
        self.error_label = QLabel()
        self.error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.error_label.setStyleSheet("color: red;") # Make errors stand out
        self.error_label.setWordWrap(True) # For longer error messages
        self.stacked_widget.addWidget(self.error_label)

        self.current_path = None

    def clear_preview(self):
        self.stacked_widget.setCurrentWidget(self.no_preview_label)
        self.current_path = None

    def update_preview(self, path_obj: pathlib.Path = None):
            if not path_obj or not path_obj.exists() or path_obj.is_dir():
                self.clear_preview()
                return

            if self.current_path == path_obj:
                return
            self.current_path = path_obj

            mime_type, _ = mimetypes.guess_type(path_obj)
            file_suffix = path_obj.suffix.lower()

            # Image Preview
            image_extensions = ['.png', '.jpg', '.jpeg', '.gif', '.bmp']
            is_image_mime = mime_type and mime_type.startswith('image/')

            if file_suffix in image_extensions or is_image_mime:
                pixmap = QPixmap(str(path_obj))
                if not pixmap.isNull():
                    # Scale the pixmap to fit the label, preserving aspect ratio
                    scaled_pixmap = pixmap.scaled(self.image_label.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                    self.image_label.setPixmap(scaled_pixmap)
                    self.stacked_widget.setCurrentWidget(self.image_scroll_area)
                else:
                    # This is a genuine image loading failure
                    self.error_label.setText(f"Could not load image: {path_obj.name}\n(Format might be unsupported or file corrupted)")
                    self.stacked_widget.setCurrentWidget(self.error_label)
                return # Processed as image (or image attempt)

            # Text Preview
            text_extensions = ['.txt', '.log', '.md', '.py', '.c', '.cpp', '.h', '.json', '.xml', '.html', '.css', '.js', '.ini', '.conf', '.cfg', '.yaml', '.yml'] # Added more
            is_text_mime = mime_type and (
                mime_type.startswith('text/') or
                mime_type in ['application/json', 'application/xml', 'application/x-python', 'application/javascript'] # Added more common text mimes
            )

            if file_suffix in text_extensions or is_text_mime:
                try:
                    MAX_PREVIEW_SIZE = 1 * 1024 * 1024  # 1MB
                    content = ""
                    # Try with utf-8 first, then with locale's default, then latin-1 as a last resort for binary-ish text
                    encodings_to_try = ['utf-8', os.device_encoding(0) or 'latin-1', 'latin-1']

                    file_opened = False
                    for enc in encodings_to_try:
                        try:
                            with open(path_obj, 'r', encoding=enc) as f:
                                content = f.read(MAX_PREVIEW_SIZE)
                                file_opened = True
                                break # Successfully read
                        except UnicodeDecodeError:
                            continue # Try next encoding
                        except Exception as e_open: # Other file opening errors
                            self.error_label.setText(f"Error opening file: {path_obj.name}\n{e_open}")
                            self.stacked_widget.setCurrentWidget(self.error_label)
                            return


                    if not file_opened:
                        self.error_label.setText(f"Could not decode text file: {path_obj.name}\n(Tried UTF-8, {encodings_to_try[1]}, Latin-1)")
                        self.stacked_widget.setCurrentWidget(self.error_label)
                        return

                    if len(content) == MAX_PREVIEW_SIZE:
                        content += "\n\n[File content truncated for preview]"

                    self.text_edit.setPlainText(content)
                    self.stacked_widget.setCurrentWidget(self.text_edit)
                except Exception as e: # Catch-all for other unexpected errors during text processing
                    self.error_label.setText(f"Error reading text file: {path_obj.name}\n{e}")
                    self.stacked_widget.setCurrentWidget(self.error_label)
                return # Processed as text

            # If no specific preview is available
            self.unsupported_label.setText(f"Preview not available for '{path_obj.name}'\n(Type: {mime_type or 'Unknown'})")
            self.stacked_widget.setCurrentWidget(self.unsupported_label)

class OrganizationConfigPanel(QWidget):
    organize_triggered = Signal(OrganizationSettings)
    rename_triggered = Signal(OrganizationSettings)

    RENAME_PRESET_TEMPLATES = {
        "Custom": "",
        "Filename - Sequence": "[Filename]_[Num]",
        "Date - Filename": "[YYYY]-[MM]-[DD] - [Filename]",
        "Image - Sequence": "IMG_[Num]",
        "Regex Group 1 - Filename": "[RegexGroup1] - [Filename]",
    }

    PRESET_TEMPLATES = {
        "Custom": "", # Special value, means use QLineEdit directly
        "Year/Month/Filename": "[YYYY]/[MM]/[Filename].[Ext]",
        "Year-Month-Day/Filename": "[YYYY]-[MM]-[DD]/[Filename].[Ext]",
        "File Type/Year/Filename": "[DetectedFileType]/[YYYY]/[Filename].[Ext]",
        "Capture Group 1/Filename (Regex)": "[RegexGroup1]/[Filename].[Ext]",
    }
    def __init__(self, file_browser_panel_ref=None, parent=None):
        super().__init__(parent)
        self.file_browser_panel_ref = file_browser_panel_ref
        self.main_layout = QVBoxLayout(self)
        self.setLayout(self.main_layout)

        # --- Scroll Area for potentially many options ---
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        self.main_layout.addWidget(scroll_area)

        container_widget = QWidget() # Widget to hold all the group boxes
        scroll_area.setWidget(container_widget)

        container_layout = QVBoxLayout(container_widget)
        container_widget.setLayout(container_layout)


        # --- Filters Group (Common to both modes) ---
        filters_group = QGroupBox("Filtering Criteria")
        filters_layout = QFormLayout(filters_group)

        self.process_recursively_checkbox = QCheckBox("Recursively process subdirectories")
        self.process_recursively_checkbox.setToolTip(
            "If checked, Chrono Filer will scan all subdirectories of the source folder.\n"
            "If unchecked (default), it only processes files in the root of the source folder."
        )
        filters_layout.addRow(self.process_recursively_checkbox)

        # Name Filter
        self.name_filter_text = QLineEdit()
        self.name_filter_type = QComboBox()
        self.name_filter_type.addItems(["Contains", "Starts with", "Ends with", "Exact match", "Regex"])
        name_filter_layout = QHBoxLayout()
        name_filter_layout.addWidget(self.name_filter_text)
        name_filter_layout.addWidget(self.name_filter_type)
        filters_layout.addRow("Name:", name_filter_layout)

        # Type Filter
        self.type_filter_text = QLineEdit()
        self.type_filter_text.setPlaceholderText("e.g., .txt, .jpg, image/png")
        filters_layout.addRow("File Type/Extension:", self.type_filter_text)

        # Date Filters
        self.created_after_date = QDateEdit()
        self.created_after_date.setCalendarPopup(True)
        self.created_after_date.setDisplayFormat("yyyy-MM-dd")
        self.created_after_date.setDate(datetime.date(2010, 1, 1))
        filters_layout.addRow("Created After:", self.created_after_date)

        self.modified_before_date = QDateEdit()
        self.modified_before_date.setCalendarPopup(True)
        self.modified_before_date.setDisplayFormat("yyyy-MM-dd")
        self.modified_before_date.setDate(datetime.date.today()) # Default today
        filters_layout.addRow("Modified Before:", self.modified_before_date)

        # Size Filters
        size_filter_layout = QHBoxLayout()
        self.size_min_spinbox = QSpinBox()
        self.size_min_spinbox.setRange(0, 1024 * 1024)
        self.size_min_spinbox.setSuffix(" KB")
        self.size_max_spinbox = QSpinBox()
        self.size_max_spinbox.setRange(0, 1024 * 1024)
        self.size_max_spinbox.setSuffix(" KB")
        self.size_max_spinbox.setValue(1024 * 1024)
        size_filter_layout.addWidget(QLabel("Min:"))
        size_filter_layout.addWidget(self.size_min_spinbox)
        size_filter_layout.addWidget(QLabel("Max:"))
        size_filter_layout.addWidget(self.size_max_spinbox)
        filters_layout.addRow("Size:", size_filter_layout)

        container_layout.addWidget(filters_group)

        # --- Tab Widget for Organize and Rename ---
        self.action_tabs = QTabWidget()
        container_layout.addWidget(self.action_tabs)

        # --- Create Organize Tab ---
        organize_tab_widget = QWidget()
        self._create_organize_tab(organize_tab_widget)
        self.action_tabs.addTab(organize_tab_widget, "Organize")

        # --- Create Rename Tab ---
        rename_tab_widget = QWidget()
        self._create_rename_tab(rename_tab_widget)
        self.action_tabs.addTab(rename_tab_widget, "Rename")


        # Add a spacer at the bottom of the container to push content up
        container_layout.addStretch(1)
        self.setLayout(self.main_layout)

        # --- Connect Signals ---
        self.organize_button.clicked.connect(self._on_organize_clicked)
        self.rename_button.clicked.connect(self._on_rename_clicked)

        self.structure_preset_combo.currentTextChanged.connect(self._on_structure_preset_changed)
        self.rename_preset_combo.currentTextChanged.connect(self._on_rename_preset_changed)

        self.template_info_button.clicked.connect(self._show_template_info)
        self.rename_template_info_button.clicked.connect(self._show_template_info) # Reuse same info dialog

        self.browse_target_button.clicked.connect(self._on_browse_target_directory)
        self.operation_type_combo.currentTextChanged.connect(self._on_operation_type_changed)

        # Initial state for template edits
        self._on_structure_preset_changed(self.structure_preset_combo.currentText())
        self._on_rename_preset_changed(self.rename_preset_combo.currentText())
        self._on_operation_type_changed(self.operation_type_combo.currentText())


    def _create_organize_tab(self, tab_widget):
        """Creates the UI for the 'Organize' tab."""
        tab_layout = QVBoxLayout(tab_widget)

        # --- Output Structure Group ---
        output_group = QGroupBox("Output Configuration")
        output_layout = QVBoxLayout(output_group)

        target_base_layout = QHBoxLayout()
        target_base_label = QLabel("Target Base Directory (Optional):")
        self.target_base_dir_edit = QLineEdit()
        self.target_base_dir_edit.setPlaceholderText("Leave empty to organize within source directory")
        self.browse_target_button = QPushButton("Browse...")
        target_base_layout.addWidget(target_base_label)
        target_base_layout.addWidget(self.target_base_dir_edit)
        target_base_layout.addWidget(self.browse_target_button)
        output_layout.addLayout(target_base_layout)

        preset_label = QLabel("Structure Template Preset:")
        output_layout.addWidget(preset_label)
        self.structure_preset_combo = QComboBox()
        self.structure_preset_combo.addItems(list(self.PRESET_TEMPLATES.keys()))
        output_layout.addWidget(self.structure_preset_combo)

        template_edit_label = QLabel("Structure Template:")
        output_layout.addWidget(template_edit_label)
        template_edit_layout = QHBoxLayout()
        self.structure_template_edit = QLineEdit()
        self.structure_template_edit.setPlaceholderText("Define custom structure or see preset")
        default_preset_key = "Year/Month/Filename"
        self.structure_template_edit.setText(self.PRESET_TEMPLATES.get(default_preset_key, "[YYYY]/[MM]/[Filename].[Ext]"))
        self.structure_preset_combo.setCurrentText(default_preset_key)
        template_edit_layout.addWidget(self.structure_template_edit)
        self.template_info_button = QPushButton()
        self.template_info_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MessageBoxInformation))
        self.template_info_button.setToolTip("Show available template placeholders")
        template_edit_layout.addWidget(self.template_info_button)
        output_layout.addLayout(template_edit_layout)
        tab_layout.addWidget(output_group)

        # --- Actions Group ---
        actions_group = QGroupBox("Actions")
        actions_layout = QVBoxLayout(actions_group)

        # First row: Operation type and conflict resolution
        first_row_layout = QHBoxLayout()

        self.operation_type_combo = QComboBox()
        self.operation_type_combo.addItems(["Move", "Copy"])
        self.operation_type_combo.setToolTip("Move: Files are moved to new location\nCopy: Files are copied, originals remain")
        first_row_layout.addWidget(QLabel("Operation:"))
        first_row_layout.addWidget(self.operation_type_combo)

        first_row_layout.addWidget(QLabel("Conflicts:"))
        self.conflict_resolution_combo = QComboBox()
        self.conflict_resolution_combo.addItems(["Skip", "Overwrite", "Rename with Suffix"])
        first_row_layout.addWidget(self.conflict_resolution_combo)
        first_row_layout.addStretch()

        actions_layout.addLayout(first_row_layout)

        # Second row: Dry run and organize button
        second_row_layout = QHBoxLayout()
        self.dry_run_checkbox = QCheckBox("Dry Run (Preview Changes)")
        self.dry_run_checkbox.setChecked(True)
        second_row_layout.addWidget(self.dry_run_checkbox)
        second_row_layout.addStretch()

        self.organize_button = QPushButton("Organize Files")
        second_row_layout.addWidget(self.organize_button)

        actions_layout.addLayout(second_row_layout)
        tab_layout.addWidget(actions_group)

        tab_layout.addStretch(1) # Pushes content to the top

    def _create_rename_tab(self, tab_widget):
        """Creates the UI for the 'Rename' tab."""
        tab_layout = QVBoxLayout(tab_widget)

        # --- Rename Template Group ---
        rename_group = QGroupBox("Rename Configuration")
        rename_layout = QVBoxLayout(rename_group)

        preset_label = QLabel("Rename Template Preset:")
        rename_layout.addWidget(preset_label)
        self.rename_preset_combo = QComboBox()
        self.rename_preset_combo.addItems(list(self.RENAME_PRESET_TEMPLATES.keys()))
        rename_layout.addWidget(self.rename_preset_combo)

        template_edit_label = QLabel("Rename Template (extension is preserved):")
        rename_layout.addWidget(template_edit_label)
        template_edit_layout = QHBoxLayout()
        self.rename_template_edit = QLineEdit()
        self.rename_template_edit.setPlaceholderText("Define custom rename format or see preset")
        default_preset_key = "Filename - Sequence"
        self.rename_template_edit.setText(self.RENAME_PRESET_TEMPLATES.get(default_preset_key, "[Filename]_[Num]"))
        self.rename_preset_combo.setCurrentText(default_preset_key)
        template_edit_layout.addWidget(self.rename_template_edit)
        self.rename_template_info_button = QPushButton()
        self.rename_template_info_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MessageBoxInformation))
        self.rename_template_info_button.setToolTip("Show available template placeholders")
        template_edit_layout.addWidget(self.rename_template_info_button)
        rename_layout.addLayout(template_edit_layout)

        # --- Sequence Number Options ---
        sequence_layout = QHBoxLayout()
        self.rename_start_spinbox = QSpinBox()
        self.rename_start_spinbox.setRange(0, 99999)
        self.rename_start_spinbox.setValue(1)
        sequence_layout.addWidget(QLabel("Start Number:"))
        sequence_layout.addWidget(self.rename_start_spinbox)

        self.rename_padding_spinbox = QSpinBox()
        self.rename_padding_spinbox.setRange(0, 10)
        self.rename_padding_spinbox.setValue(4)
        sequence_layout.addWidget(QLabel("Number Padding (zeros):"))
        sequence_layout.addWidget(self.rename_padding_spinbox)
        sequence_layout.addStretch()
        rename_layout.addLayout(sequence_layout)

        tab_layout.addWidget(rename_group)

        # --- Actions Group for Rename ---
        actions_group = QGroupBox("Actions")
        actions_layout = QHBoxLayout(actions_group)

        # Conflict resolution is also applicable here
        self.rename_conflict_resolution_combo = QComboBox()
        self.rename_conflict_resolution_combo.addItems(["Skip", "Overwrite", "Rename with Suffix"])
        actions_layout.addWidget(QLabel("Filename Conflicts:"))
        actions_layout.addWidget(self.rename_conflict_resolution_combo)
        actions_layout.addStretch()

        self.rename_dry_run_checkbox = QCheckBox("Dry Run (Preview Changes)")
        self.rename_dry_run_checkbox.setChecked(True)
        actions_layout.addWidget(self.rename_dry_run_checkbox)

        self.rename_button = QPushButton("Rename Files")
        actions_layout.addWidget(self.rename_button)
        tab_layout.addWidget(actions_group)

        tab_layout.addStretch(1)

    def _on_browse_target_directory(self):
        # This now correctly references the file_browser_panel_ref passed in __init__
        start_path = self.target_base_dir_edit.text()
        if not start_path and self.file_browser_panel_ref:
            start_path = self.file_browser_panel_ref.current_path

        directory = QFileDialog.getExistingDirectory(
            self, "Select Target Base Directory", start_path
        )
        if directory:
            self.target_base_dir_edit.setText(directory)

    def _on_structure_preset_changed(self, preset_name: str):
        template = self.PRESET_TEMPLATES.get(preset_name, "")
        if preset_name == "Custom":
            self.structure_template_edit.setEnabled(True)
        else:
            self.structure_template_edit.setText(template)
            self.structure_template_edit.setEnabled(False)

    def _on_rename_preset_changed(self, preset_name: str):
        template = self.RENAME_PRESET_TEMPLATES.get(preset_name, "")
        if preset_name == "Custom":
            self.rename_template_edit.setEnabled(True)
        else:
            self.rename_template_edit.setText(template)
            self.rename_template_edit.setEnabled(False)

    def _show_template_info(self):
        info_text = """
        <b>Available Placeholders:</b><br><br>
        - <code>[YYYY]</code>: Full year (e.g., 2023)<br>
        - <code>[MM]</code>: Month with leading zero (e.g., 01, 12)<br>
        - <code>[DD]</code>: Day of month with leading zero (e.g., 05, 31)<br>
        - <code>[Filename]</code>: Original filename without extension<br>
        - <code>[Ext]</code>: Original file extension (without the dot)<br>
        - <code>[DetectedFileType]</code>: General category (e.g., "Images", "Documents")<br>
        - <code>[RegexGroup1]</code>, etc.: Capture group from 'Name' filter.<br>
        - <code>[Num]</code>: A sequence number (for Rename mode).<br><br>
        <b>Organize Example:</b> <code>[YYYY]/[MM]/[Filename].[Ext]</code><br>
        <b>Rename Example:</b> <code>MyPhoto_[Num]</code> (don't add .[Ext])
        """
        QMessageBox.information(self, "Structure Template Info", info_text)

    def _on_operation_type_changed(self, operation_type: str):
        """Updates the organize button text based on the selected operation type."""
        if operation_type == "Copy":
            self.organize_button.setText("Copy Files")
        else:
            self.organize_button.setText("Move Files")

    def _on_organize_clicked(self):
        settings = self.get_current_settings()
        self.organize_triggered.emit(settings)

    def _on_rename_clicked(self):
        settings = self.get_current_settings()
        self.rename_triggered.emit(settings)

    def get_current_settings(self) -> OrganizationSettings:
        # --- Common Filters ---
        name_text = self.name_filter_text.text().strip()
        type_text = self.type_filter_text.text().strip()
        created_val = self.created_after_date.date().toPython()
        created_after = created_val if self.created_after_date.isEnabled() and created_val != datetime.date(2010, 1, 1) else None
        modified_val = self.modified_before_date.date().toPython()
        modified_before = modified_val if self.modified_before_date.isEnabled() and modified_val != datetime.date.today() else None
        size_min = self.size_min_spinbox.value()
        size_max = self.size_max_spinbox.value()
        actual_size_max = -1 if size_max == self.size_max_spinbox.maximum() else size_max
        process_recursively = self.process_recursively_checkbox.isChecked()

        # --- Tab-specific settings ---
        current_tab_text = self.action_tabs.tabText(self.action_tabs.currentIndex())
        if current_tab_text == "Organize":
            conflict = self.conflict_resolution_combo.currentText()
            dry_run = self.dry_run_checkbox.isChecked()
            operation_type = self.operation_type_combo.currentText()
            structure = self.structure_template_edit.text().strip()
            target_base_dir_str = self.target_base_dir_edit.text().strip()
            target_base = str(pathlib.Path(target_base_dir_str).expanduser().resolve()) if target_base_dir_str else None
            rename_template = "" # Not relevant for organize mode
            rename_start_num = 0
            rename_padding = 0
        else: # Rename
            conflict = self.rename_conflict_resolution_combo.currentText()
            dry_run = self.rename_dry_run_checkbox.isChecked()
            operation_type = "Move"  # Rename mode always moves files
            structure = "" # Not relevant for rename mode
            target_base = None
            rename_template = self.rename_template_edit.text().strip()
            rename_start_num = self.rename_start_spinbox.value()
            rename_padding = self.rename_padding_spinbox.value()

        return OrganizationSettings(
            name_filter_text=name_text,
            name_filter_type=self.name_filter_type.currentText(),
            type_filter_text=type_text,
            created_after_date=created_after,
            modified_before_date=modified_before,
            size_min_kb=size_min,
            size_max_kb=actual_size_max,
            process_recursively=process_recursively,
            operation_type=operation_type,
            conflict_resolution=conflict,
            dry_run=dry_run,
            structure_template=structure,
            target_base_directory=target_base,
            rename_template=rename_template,
            rename_start_number=rename_start_num,
            rename_template_padding=rename_padding
        )

    def get_ui_state(self) -> dict[str, any]:
        """Returns a dictionary representing the current state of the UI widgets."""
        state = {
            "name_filter_text": self.name_filter_text.text(),
            "name_filter_type_index": self.name_filter_type.currentIndex(),
            "type_filter_text": self.type_filter_text.text(),
            "created_after_date": self.created_after_date.date().toString(Qt.DateFormat.ISODate),
            "modified_before_date": self.modified_before_date.date().toString(Qt.DateFormat.ISODate),
            "size_min_kb": self.size_min_spinbox.value(),
            "size_max_kb": self.size_max_spinbox.value(),
            "process_recursively_checked": self.process_recursively_checkbox.isChecked(),
            "active_tab_index": self.action_tabs.currentIndex(),

            # Organize Tab
            "structure_preset_name": self.structure_preset_combo.currentText(),
            "structure_template_text": self.structure_template_edit.text(),
            "operation_type_index": self.operation_type_combo.currentIndex(),
            "conflict_resolution_index": self.conflict_resolution_combo.currentIndex(),
            "dry_run_checked": self.dry_run_checkbox.isChecked(),
            "target_base_directory": self.target_base_dir_edit.text(),

            # Rename Tab
            "rename_preset_name": self.rename_preset_combo.currentText(),
            "rename_template_text": self.rename_template_edit.text(),
            "rename_conflict_resolution_index": self.rename_conflict_resolution_combo.currentIndex(),
            "rename_dry_run_checked": self.rename_dry_run_checkbox.isChecked(),
            "rename_start_number": self.rename_start_spinbox.value(),
            "rename_padding": self.rename_padding_spinbox.value(),
        }
        return state

    def set_ui_state(self, state: dict[str, any]):
        """Sets the state of the UI widgets from a dictionary."""
        self.name_filter_text.setText(state.get("name_filter_text", ""))
        self.name_filter_type.setCurrentIndex(state.get("name_filter_type_index", 0))
        self.type_filter_text.setText(state.get("type_filter_text", ""))
        if "created_after_date" in state:
            self.created_after_date.setDate(QDate.fromString(state["created_after_date"], Qt.DateFormat.ISODate))
        if "modified_before_date" in state:
            self.modified_before_date.setDate(QDate.fromString(state["modified_before_date"], Qt.DateFormat.ISODate))
        self.size_min_spinbox.setValue(state.get("size_min_kb", 0))
        self.size_max_spinbox.setValue(state.get("size_max_kb", 1024*1024))
        self.process_recursively_checkbox.setChecked(state.get("process_recursively_checked", False))
        self.action_tabs.setCurrentIndex(state.get("active_tab_index", 0))

        # Organize Tab
        self.structure_preset_combo.setCurrentText(state.get("structure_preset_name", "Custom"))
        self.structure_template_edit.setText(state.get("structure_template_text", ""))
        self.operation_type_combo.setCurrentIndex(state.get("operation_type_index", 0))
        self.conflict_resolution_combo.setCurrentIndex(state.get("conflict_resolution_index", 0))
        self.dry_run_checkbox.setChecked(state.get("dry_run_checked", True))
        self.target_base_dir_edit.setText(state.get("target_base_directory", ""))

        # Rename Tab
        self.rename_preset_combo.setCurrentText(state.get("rename_preset_name", "Custom"))
        self.rename_template_edit.setText(state.get("rename_template_text", ""))
        self.rename_conflict_resolution_combo.setCurrentIndex(state.get("rename_conflict_resolution_index", 0))
        self.rename_dry_run_checkbox.setChecked(state.get("rename_dry_run_checked", True))
        self.rename_start_spinbox.setValue(state.get("rename_start_number", 1))
        self.rename_padding_spinbox.setValue(state.get("rename_padding", 4))

        # Ensure the enabled state of the template line edits is correct
        self._on_structure_preset_changed(self.structure_preset_combo.currentText())
        self._on_rename_preset_changed(self.rename_preset_combo.currentText())

class DryRunResultsDialog(QDialog):
    def __init__(self, results: List[Tuple[pathlib.Path, pathlib.Path, str]],
                    source_directory: pathlib.Path,
                    effective_output_base_dir: pathlib.Path,
                    parent=None):
        super().__init__(parent)
        self.setWindowTitle("Dry Run - Proposed Changes")
        self.setMinimumSize(800, 400) # Give it a reasonable default size
        self.setModal(True) # Make it modal

        self.source_dir = source_directory.resolve()
        self.output_base_dir = effective_output_base_dir.resolve()

        layout = QVBoxLayout(self)

        # Table to display results
        self.table_widget = QTableWidget()
        self.table_widget.setColumnCount(3)
        self.table_widget.setHorizontalHeaderLabels(["Original File", "Proposed Location", "Action/Status"])
        self.table_widget.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers) # Read-only
        self.table_widget.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table_widget.setAlternatingRowColors(True)

        # Populate table
        self.table_widget.setRowCount(len(results))
        for row, (source_path, target_path, status) in enumerate(results):
            try:
                # Try to make paths relative to the source directory for readability
                # If target is outside source_dir (e.g. different base output dir), show full path

                source_display = str(source_path.relative_to(self.source_dir)) \
                                 if source_path.is_relative_to(self.source_dir) \
                                 else str(source_path)

                target_display = str(target_path.relative_to(self.output_base_dir)) \
                                 if target_path.is_relative_to(self.output_base_dir) \
                                 else str(target_path)

            except ValueError: # Fallback if relative_to fails (e.g. different drives on Windows)
                source_display = str(source_path)
                target_display = str(target_path)


            self.table_widget.setItem(row, 0, QTableWidgetItem(source_display))
            self.table_widget.setItem(row, 1, QTableWidgetItem(target_display))
            self.table_widget.setItem(row, 2, QTableWidgetItem(status))

        # Resize columns to content, but allow interactive resize
        self.table_widget.resizeColumnsToContents()
        self.table_widget.horizontalHeader().setStretchLastSection(True) # Make last column fill space
        # Or, for more control:
        # self.table_widget.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        # self.table_widget.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        # self.table_widget.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
        # self.table_widget.setColumnWidth(0, 250)
        # self.table_widget.setColumnWidth(1, 350)
        # self.table_widget.setColumnWidth(2, 150)


        layout.addWidget(self.table_widget)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch() # Push buttons to the right

        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.accept) # QDialog.accept() closes and returns QDialog.Accepted
        button_layout.addWidget(self.ok_button)

        layout.addLayout(button_layout)
        self.setLayout(layout)
