# src/widgets.py
import os
import pathlib
import datetime
import mimetypes
from dataclasses import dataclass, field
from typing import Optional, List, Tuple

from PySide6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QListWidget, QListWidgetItem,
    QStyle, QGridLayout, QTextEdit, QScrollArea,
    QSizePolicy, QSpacerItem, QStackedWidget,
    QGroupBox, QFormLayout, QComboBox, QDateEdit,
    QSpinBox, QCheckBox, QScrollArea, QDialog,
    QTableWidget, QTableWidgetItem, QAbstractItemView, QHeaderView,
    QDialogButtonBox, QMessageBox, QFileDialog
)
from PySide6.QtGui import QPalette, QColor, QPixmap

from PySide6.QtCore import Qt, Signal

@dataclass
class OrganizationSettings:
    name_filter_text: str = ""
    name_filter_type: str = "Contains"
    type_filter_text: str = ""
    created_after_date: Optional[datetime.date] = None
    modified_before_date: Optional[datetime.date] = None
    size_min_kb: int = 0
    size_max_kb: int = -1
    structure_template: str = "[YYYY]/[MM]/[Filename].[Ext]"
    target_base_directory: Optional[pathlib.Path] = None
    conflict_resolution: str = "Skip" # "Overwrite", "Rename with Suffix"
    dry_run: bool = True

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

    # Define the custom signal
    # It will emit a pathlib.Path object, or None if no valid item is selected
    selection_changed = Signal(object) # Use 'object' to allow sending pathlib.Path or None

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_path = str(pathlib.Path.home()) # Start in user's home directory

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

        # File and directory list
        self.item_list_widget = QListWidget()
        self.layout.addWidget(self.item_list_widget)

        self.setLayout(self.layout)

        # Connect signals
        self.up_button.clicked.connect(self.go_up)
        self.path_edit.returnPressed.connect(self.path_changed) # Navigate when Enter is pressed in QLineEdit
        # self.item_list_widget.itemDoubleClicked.connect(self.item_double_clicked)
        self.item_list_widget.itemActivated.connect(self.item_double_clicked)
        self.item_list_widget.currentItemChanged.connect(self.on_current_item_changed)

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
                    self.image_label.setPixmap(pixmap)
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
    organize_triggered = Signal(OrganizationSettings) # type: ignore

    PRESET_TEMPLATES = {
        "Custom": "", # Special value, means use QLineEdit directly
        "Year/Month/Filename": "[YYYY]/[MM]/[Filename].[Ext]",
        "Year-Month-Day/Filename": "[YYYY]-[MM]-[DD]/[Filename].[Ext]",
        "File Type/Year/Filename": "[DetectedFileType]/[YYYY]/[Filename].[Ext]",
        "Capture Group 1/Filename (Regex)": "[RegexGroup1]/[Filename].[Ext]",
    }
    def __init__(self, parent=None):
        super().__init__(parent)
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


        # --- Filters Group ---
        filters_group = QGroupBox("Filtering Criteria")
        filters_layout = QFormLayout(filters_group)

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

        # Date Filters (Simplified for now, can add QCalendarWidget later for ranges)
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
        self.size_min_spinbox.setRange(0, 1024 * 1024) # 0 B to 1 TB (in KB, MB, GB later)
        self.size_min_spinbox.setSuffix(" KB")
        self.size_max_spinbox = QSpinBox()
        self.size_max_spinbox.setRange(0, 1024 * 1024)
        self.size_max_spinbox.setSuffix(" KB")
        self.size_max_spinbox.setValue(1024 * 1024) # Default max
        size_filter_layout.addWidget(QLabel("Min:"))
        size_filter_layout.addWidget(self.size_min_spinbox)
        size_filter_layout.addWidget(QLabel("Max:"))
        size_filter_layout.addWidget(self.size_max_spinbox)
        filters_layout.addRow("Size:", size_filter_layout)

        container_layout.addWidget(filters_group)


        # --- Output Structure Group ---
        output_group = QGroupBox("Output Configuration")
        output_layout_form = QFormLayout(output_group)

         # Target Base Directory
        target_dir_layout = QHBoxLayout()
        self.target_dir_edit = QLineEdit()
        self.target_dir_edit.setPlaceholderText("Optional: Leave blank to organize within source directory")
        target_dir_layout.addWidget(self.target_dir_edit)
        self.browse_target_dir_button = QPushButton("Browse...")
        target_dir_layout.addWidget(self.browse_target_dir_button)
        output_layout_form.addRow("Target Directory:", target_dir_layout)

        # Preset ComboBox
        self.structure_preset_combo = QComboBox()
        self.structure_preset_combo.addItems(list(self.PRESET_TEMPLATES.keys()))
        output_layout_form.addRow("Structure Preset:", self.structure_preset_combo)


        # Template Edit Line and Info Button
        template_edit_layout = QHBoxLayout()
        self.structure_template_edit = QLineEdit()
        self.structure_template_edit.setPlaceholderText("Define custom structure or see preset")
        # Set default text based on a default preset
        default_preset_key = "Year/Month/Filename"
        self.structure_template_edit.setText(self.PRESET_TEMPLATES.get(default_preset_key, "[YYYY]/[MM]/[Filename].[Ext]"))
        self.structure_preset_combo.setCurrentText(default_preset_key) # Sync combobox

        template_edit_layout.addWidget(self.structure_template_edit)

        self.template_info_button = QPushButton()
        self.template_info_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MessageBoxInformation))
        self.template_info_button.setToolTip("Show available template placeholders")
        template_edit_layout.addWidget(self.template_info_button)

        output_layout_form.addRow("Custom Structure:", template_edit_layout)
        container_layout.addWidget(output_group)

        # --- Actions Group ---
        actions_group = QGroupBox("Actions")
        actions_layout = QHBoxLayout(actions_group) # Use QHBoxLayout for buttons side-by-side

        self.conflict_resolution_combo = QComboBox()
        self.conflict_resolution_combo.addItems(["Skip", "Overwrite", "Rename with Suffix"])
        actions_layout.addWidget(QLabel("Filename Conflicts:"))
        actions_layout.addWidget(self.conflict_resolution_combo)
        actions_layout.addStretch() # Push buttons to the right or spread them

        self.dry_run_checkbox = QCheckBox("Dry Run (Preview Changes)")
        self.dry_run_checkbox.setChecked(True) # Default to dry run
        actions_layout.addWidget(self.dry_run_checkbox)

        self.organize_button = QPushButton("Organize Files")
        # self.organize_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogApplyButton)) # Example Icon
        actions_layout.addWidget(self.organize_button)

        container_layout.addWidget(actions_group)

        # Add a spacer at the bottom of the container to push content up if scroll area is larger
        container_layout.addStretch(1)
        self.setLayout(self.main_layout)

        self.organize_button.clicked.connect(self._on_organize_clicked)

        # added dropdown
        self.structure_preset_combo.currentTextChanged.connect(self._on_structure_preset_changed)
        self.template_info_button.clicked.connect(self._show_template_info)
        self.browse_target_dir_button.clicked.connect(self._browse_target_directory)

        # Initial state for template edit based on "Custom" or other preset
        self._on_structure_preset_changed(self.structure_preset_combo.currentText())


    def _browse_target_directory(self):
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Target Base Directory",
            self.target_dir_edit.text() or str(pathlib.Path.home()) # Start from current or home
        )
        if directory: # If a directory was selected (not cancelled)
            self.target_dir_edit.setText(directory)

    def _on_structure_preset_changed(self, preset_name: str):
        template = self.PRESET_TEMPLATES.get(preset_name, "")
        if preset_name == "Custom":
            self.structure_template_edit.setEnabled(True)
            # Optionally, you might want to clear it or leave the last custom/preset value
            # self.structure_template_edit.clear()
        else:
            self.structure_template_edit.setText(template)
            self.structure_template_edit.setEnabled(False) # Disable editing for presets

    def _show_template_info(self):
        info_text = """
        <b>Available Placeholders for Structure Template:</b><br><br>
        - <code>[YYYY]</code>: Full year (e.g., 2023)<br>
        - <code>[MM]</code>: Month with leading zero (e.g., 01, 12)<br>
        - <code>[DD]</code>: Day of month with leading zero (e.g., 05, 31)<br>
        - <code>[Filename]</code>: Original filename without extension<br>
        - <code>[Ext]</code>: Original file extension (without the dot)<br>
        - <code>[RegexGroup1]</code>, <code>[RegexGroup2]</code>, etc.:<br>
             Corresponds to the 1st, 2nd, etc. capture group from the<br>
             'Name' filter if 'Regex' mode is selected.<br>
        - <code>[DetectedFileType]</code>: A general category for the file type<br>
             (e.g., "Images", "Documents", "Videos", "Audio", "Archives", "Other").<br>
             <i>(Based on MIME type)</i><br><br>
        Example: <code>[YYYY]/[MM]/[MyPrefix]-[Filename].[Ext]</code>
        """
        QMessageBox.information(self, "Structure Template Info", info_text)


    def _on_organize_clicked(self):
                settings = self.get_current_settings()
                self.organize_triggered.emit(settings)

    def get_current_settings(self) -> OrganizationSettings:
                name_text = self.name_filter_text.text().strip()
                name_type = self.name_filter_type.currentText()
                type_text = self.type_filter_text.text().strip()

                # QDateEdit.date() returns QDate. Convert to datetime.date
                # Only use the date if it's different from the "ignore" default
                created_val = self.created_after_date.date().toPython()
                created_after = created_val if created_val != datetime.date(1970, 1, 1) else None

                modified_val = self.modified_before_date.date().toPython()
                modified_before = modified_val if modified_val != datetime.date.today() else None

                size_min = self.size_min_spinbox.value()
                size_max = self.size_max_spinbox.value()

                # If max is at its ceiling and min is at its floor, effectively no size filter from user.
                # However, it's better to let the engine handle 0 as "no min" and a very large number or a flag as "no max".
                # Let's pass them as is, and the engine can interpret.
                # If size_max is set to the spinbox's maximum, it could mean "no upper limit".
                if size_max == self.size_max_spinbox.maximum():
                    actual_size_max = -1 # Use -1 to signify no upper bound for the engine
                else:
                    actual_size_max = size_max


                structure = self.structure_template_edit.text().strip()
                if not structure and self.structure_preset_combo.currentText() != "Custom":
                            # If QLineEdit is empty but a non-custom preset is selected, re-fetch from preset
                            structure = self.PRESET_TEMPLATES.get(self.structure_preset_combo.currentText(), "[YYYY]/[MM]/[Filename].[Ext]")
                elif not structure and self.structure_preset_combo.currentText() == "Custom":
                            structure = "[YYYY]/[MM]/[Filename].[Ext]" # Fallback if custom is empty

                conflict = self.conflict_resolution_combo.currentText()
                dry_run = self.dry_run_checkbox.isChecked()
                target_base_dir_str = self.target_dir_edit.text().strip()
                target_base_dir_path = pathlib.Path(target_base_dir_str) if target_base_dir_str else None
                # print(f"DEBUG UI: Target dir string from UI: '{target_base_dir_str}', Path object: {target_base_dir_path}") # DBG

                return OrganizationSettings(
                    name_filter_text=name_text,
                    name_filter_type=name_type,
                    type_filter_text=type_text,
                    created_after_date=created_after,
                    modified_before_date=modified_before,
                    size_min_kb=size_min, # Pass as is
                    size_max_kb=actual_size_max, # Pass interpreted max
                    structure_template=structure,
                    target_base_directory=target_base_dir_path,
                    conflict_resolution=conflict,
                    dry_run=dry_run
                )

class DryRunResultsDialog(QDialog):
    def __init__(self, results: List[Tuple[pathlib.Path, pathlib.Path, str]],
                     source_directory: pathlib.Path,
                     effective_output_base_dir: pathlib.Path,
                     parent=None):
        super().__init__(parent)
        self.setWindowTitle("Dry Run - Proposed Changes")
        self.setMinimumSize(800, 400) # Give it a reasonable default size
        self.setModal(True) # Make it modal

        self.source_dir = source_directory.resolve() # Store for making paths relative

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

                target_display = str(target_path.relative_to(self.source_dir)) \
                                 if target_path.is_relative_to(self.source_dir) \
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
