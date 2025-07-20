# src/main.py
import sys
import pathlib

from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QSplitter,
    QTabWidget,
    QMessageBox,
    QProgressDialog
)
from PySide6.QtCore import Qt
from typing import List, Tuple
from PySide6.QtGui import QAction

from widgets import (
FileBrowserPanel,
PreviewPanel,
MetadataPanel,
OrganizationConfigPanel,
OrganizationSettings,
DryRunResultsDialog
)

from engine import OrganizationEngine
from worker import OrganizationWorker
from settings_manager import SettingsManager
from settings_dialog import SettingsDialog
from commands import UndoManager, BatchMoveCommand, BatchCopyCommand, CreateFolderCommand, RenameCommand, DeleteCommand

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.undo_manager = UndoManager()
        self.settings_manager = SettingsManager()
        self.setWindowTitle("Chrono Filer - v0.1.0")
        self.setGeometry(100, 100, 1280, 800)

        # Create panels first
        self._create_panels()

        # Then create the layout that arranges them
        self._create_main_layout()

        # Now that all widgets are in place, connect signals
        self._connect_signals()

        # Create menus and status bar
        self._create_menus()
        self._create_status_bar()

        # Load state and finish setup
        self.load_app_state()
        self.organization_worker = None
        self.progress_dialog = None

    def load_app_state(self):
            """Loads application state from config file and applies it."""
            print("Loading application state...")
            state = self.settings_manager.load_settings()
            if not state:
                print("No previous state found or error loading.")
                return

            # Apply window geometry
            geometry = state.get("main_window_geometry")
            if geometry:
                self.setGeometry(geometry[0], geometry[1], geometry[2], geometry[3])

            # Apply organization panel settings
            org_panel_state = state.get("organization_panel")
            if org_panel_state:
                self.organization_config_panel.set_ui_state(org_panel_state)

            # Apply last browsed path
            last_path = state.get("last_browsed_path")
            if last_path and pathlib.Path(last_path).is_dir():
                self.file_browser_panel.current_path = last_path
                self.file_browser_panel.refresh_list()

            # Apply user settings
            self.apply_settings(state)

            print("Application state loaded.")

    def save_app_state(self):
        """Saves current application state to config file."""
        print("Saving application state...")

        # Load existing settings to preserve user preferences
        current_state = self.settings_manager.load_settings()

        # Update with current application state
        current_state.update({
            "main_window_geometry": [self.x(), self.y(), self.width(), self.height()],
            "organization_panel": self.organization_config_panel.get_ui_state(),
            "last_browsed_path": self.file_browser_panel.current_path,
            # We could add splitter sizes here later if desired
        })

        self.settings_manager.save_settings(current_state)
        print("Application state saved.")

    def closeEvent(self, event):
        """Overrides the QWidget.closeEvent() to save settings before closing."""
        self.save_app_state()
        super().closeEvent(event)

    def _create_panels(self):
        self.file_browser_panel = FileBrowserPanel(undo_manager=self.undo_manager)
        self.preview_panel = PreviewPanel()
        self.metadata_panel = MetadataPanel()
        # self.organization_config_panel = OrganizationConfigPanel()
        self.organization_config_panel = OrganizationConfigPanel(file_browser_panel_ref = self.file_browser_panel)
        self.bottom_right_tabs = QTabWidget()

    def _connect_signals(self):
        # File Browser -> Metadata & Preview
        self.file_browser_panel.selection_changed.connect(self.metadata_panel.update_metadata)
        self.file_browser_panel.selection_changed.connect(self.preview_panel.update_preview)

        # File Browser -> Status Bar
        self.file_browser_panel.status_message.connect(self.show_status_message)

        # Connect signals for both organization and rename
        self.organization_config_panel.organize_triggered.connect(self.on_start_organization)
        self.organization_config_panel.rename_triggered.connect(self.on_start_rename)

        # Undo/Redo Manager
        self.undo_manager.stack_changed.connect(self.on_undo_stack_changed)
        self.undo_manager.command_executed.connect(self.on_command_executed)
        self.undo_manager.batch_operation_started.connect(self.pause_file_watching)
        self.undo_manager.batch_operation_finished.connect(self.resume_file_watching)


    def pause_file_watching(self):
        # Temporarily disable file system watching/refreshing
        if hasattr(self, 'file_browser_panel'):
            self.file_browser_panel.blockSignals(True)
        # Or pause QFileSystemModel updates, etc.

    def resume_file_watching(self):
        # Re-enable file system watching and do a single refresh
        if hasattr(self, 'file_browser_panel'):
            self.file_browser_panel.blockSignals(False)
        # Trigger a single refresh instead of per-file updates
        self.preview_panel.update_preview()

    def on_command_executed(self, status_message: str):
            """
            Slot called after an undo or redo operation is attempted.
            Refreshes the UI and updates the status bar.
            """
            print(f"Command executed with status: {status_message}")
            self.statusBar().showMessage(status_message, 5000)

            self.file_browser_panel.refresh_list()

    def on_undo_stack_changed(self, can_undo: bool, can_redo: bool):
            """Slot to enable/disable Undo/Redo menu actions."""
            self.undo_action.setEnabled(can_undo)
            self.redo_action.setEnabled(can_redo)
            # Update action text to show what will be undone (optional but nice)
            if can_undo:
                command_description = self.undo_manager.undo_stack[-1].description
                self.undo_action.setText(f"Undo {command_description}")
            else:
                self.undo_action.setText("Undo")

            if can_redo:
                command_description = self.undo_manager.redo_stack[-1].description
                self.redo_action.setText(f"Redo {command_description}")
            else:
                self.redo_action.setText("Redo")

    def _create_menus(self):
        """Create and configure the application menu bar."""
        menu_bar = self.menuBar()

        self._create_file_menu(menu_bar)
        self._create_edit_menu(menu_bar)
        self._create_tools_menu(menu_bar)
        self._create_help_menu(menu_bar)

    def _create_file_menu(self, menu_bar):
        """Create the File menu with its actions."""
        file_menu = menu_bar.addMenu("&File")
        file_menu.addAction("E&xit", self.close)

    def _create_edit_menu(self, menu_bar):
        """Create the Edit menu with undo/redo actions."""
        edit_menu = menu_bar.addMenu("&Edit")

        # Create undo action
        self.undo_action = self._create_action(
            text="Undo",
            shortcut=Qt.Key.Key_Z | Qt.KeyboardModifier.ControlModifier,
            slot=self.undo_manager.undo,
            enabled=False
        )
        edit_menu.addAction(self.undo_action)

        # Create redo action
        self.redo_action = self._create_action(
            text="Redo",
            shortcut=Qt.Key.Key_Y | Qt.KeyboardModifier.ControlModifier,
            slot=self.undo_manager.redo,
            enabled=False
        )
        edit_menu.addAction(self.redo_action)

    def _create_tools_menu(self, menu_bar):
        """Create the Tools menu with settings and other tools."""
        tools_menu = menu_bar.addMenu("&Tools")

        # Settings action
        settings_action = self._create_action(
            text="&Settings...",
            shortcut=Qt.Key.Key_Comma | Qt.KeyboardModifier.ControlModifier,
            slot=self.show_settings_dialog,
            enabled=True
        )
        tools_menu.addAction(settings_action)

    def _create_help_menu(self, menu_bar):
        """Create the Help menu with its actions."""
        help_menu = menu_bar.addMenu("&Help")
        help_menu.addAction("&About")

    def _create_action(self, text, shortcut=None, slot=None, enabled=True):
        """Helper method to create QAction with common configuration."""
        action = QAction(text, self)

        if shortcut:
            action.setShortcut(shortcut)
        if slot:
            action.triggered.connect(slot)

        action.setEnabled(enabled)
        return action

    def show_settings_dialog(self):
        """Show the settings dialog."""
        try:
            current_settings = self.settings_manager.load_settings()
            dialog = SettingsDialog(current_settings, self)

            # Connect settings changed signal
            dialog.settings_changed.connect(self.on_settings_changed)

            if dialog.exec() == SettingsDialog.DialogCode.Accepted:
                # Settings were applied via the signal
                pass
        except Exception as e:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Error", f"Failed to open settings dialog: {e}")

    def on_settings_changed(self, new_settings: dict):
        """Handle settings changes."""
        try:
            # Save the new settings
            self.settings_manager.save_settings(new_settings)

            # Apply settings to the application
            self.apply_settings(new_settings)

            self.statusBar().showMessage("Settings applied successfully", 3000)
        except Exception as e:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Error", f"Failed to apply settings: {e}")

    def apply_settings(self, settings: dict):
        """Apply settings to the application."""
        # Apply preview settings
        if hasattr(self, 'preview_panel'):
            # Update line numbers default
            show_line_numbers = settings.get('show_line_numbers_default', True)
            if hasattr(self.preview_panel, 'line_numbers_checkbox'):
                self.preview_panel.line_numbers_checkbox.setChecked(show_line_numbers)

            # Update word wrap default
            word_wrap = settings.get('word_wrap_default', True)
            if hasattr(self.preview_panel, 'word_wrap_checkbox'):
                self.preview_panel.word_wrap_checkbox.setChecked(word_wrap)

        # Apply organization settings to the config panel
        if hasattr(self, 'organization_config_panel'):
            # Update default structure template
            default_template = settings.get('default_structure_template', '[YYYY]/[MM]/[Filename].[Ext]')
            if hasattr(self.organization_config_panel, 'structure_template_edit'):
                self.organization_config_panel.structure_template_edit.setText(default_template)
                # Set preset to custom since we're setting a template
                if hasattr(self.organization_config_panel, 'structure_preset_combo'):
                    self.organization_config_panel.structure_preset_combo.setCurrentText('Custom')

            # Update default conflict resolution
            default_conflict = settings.get('default_conflict_resolution', 'Skip')
            if hasattr(self.organization_config_panel, 'conflict_resolution_combo'):
                self.organization_config_panel.conflict_resolution_combo.setCurrentText(default_conflict)

            # Update rename conflict resolution too
            if hasattr(self.organization_config_panel, 'rename_conflict_resolution_combo'):
                self.organization_config_panel.rename_conflict_resolution_combo.setCurrentText(default_conflict)

            # Update default operation type
            default_operation = settings.get('default_operation_type', 'Move')
            if hasattr(self.organization_config_panel, 'operation_type_combo'):
                self.organization_config_panel.operation_type_combo.setCurrentText(default_operation)

            # Update default dry run
            default_dry_run = settings.get('default_dry_run', True)
            if hasattr(self.organization_config_panel, 'dry_run_checkbox'):
                self.organization_config_panel.dry_run_checkbox.setChecked(default_dry_run)
            if hasattr(self.organization_config_panel, 'rename_dry_run_checkbox'):
                self.organization_config_panel.rename_dry_run_checkbox.setChecked(default_dry_run)

            # Update default name filter type
            default_name_filter = settings.get('default_name_filter_type', 'Contains')
            if hasattr(self.organization_config_panel, 'name_filter_type'):
                self.organization_config_panel.name_filter_type.setCurrentText(default_name_filter)

        # Apply UI settings
        theme = settings.get('theme', 'System Default')
        if theme != 'System Default':
            # Apply theme (this would need theme implementation)
            pass

        # Apply undo manager settings
        undo_history_size = settings.get('undo_history_size', 50)
        if hasattr(self, 'undo_manager'):
            self.undo_manager.max_undo_levels = undo_history_size

    def _create_status_bar(self):
        self.statusBar().showMessage("Ready")

    def show_status_message(self, message: str):
        """Show a status message in the status bar."""
        self.statusBar().showMessage(message, 3000)

    def _create_main_layout(self):
        # --- Bottom Right Tab Widget ---
        # This uses the panels created in _create_panels()
        self.bottom_right_tabs.addTab(self.metadata_panel, "Metadata")
        self.bottom_right_tabs.addTab(self.organization_config_panel, "Actions") # Renamed for clarity

        # --- Right Vertical Splitter ---
        right_splitter = QSplitter(Qt.Orientation.Vertical)
        right_splitter.addWidget(self.preview_panel)
        right_splitter.addWidget(self.bottom_right_tabs)
        right_splitter.setStretchFactor(0, 3)
        right_splitter.setStretchFactor(1, 1)
        right_splitter.setSizes([550, 250])

        # --- Main Horizontal Splitter ---
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        main_splitter.addWidget(self.file_browser_panel)
        main_splitter.addWidget(right_splitter)
        main_splitter.setStretchFactor(0, 1)
        main_splitter.setStretchFactor(1, 2)
        main_splitter.setSizes([350, 930])

        self.setCentralWidget(main_splitter)

    def on_start_rename(self, settings: OrganizationSettings):
        """Slot to handle the rename_triggered signal."""
        self._start_worker(settings, mode="rename")

    def on_start_organization(self, settings: OrganizationSettings):
        """Slot to handle the organize_triggered signal."""
        self._start_worker(settings, mode="organize")

    def _start_worker(self, settings: OrganizationSettings, mode: str):
        current_browse_path_str = self.file_browser_panel.current_path
        source_directory = pathlib.Path(current_browse_path_str).resolve()

        if not source_directory.is_dir():
            QMessageBox.critical(self, "Error", f"The selected source path '{source_directory}' is not a valid directory.")
            return

        # --- Target Directory Validation (Only for Organize Mode) ---
        if mode == "organize":
            effective_output_base = source_directory
            if settings.target_base_directory:
                effective_output_base = pathlib.Path(settings.target_base_directory)
                if not effective_output_base.exists():
                    reply = QMessageBox.question(self, "Create Target Directory?",
                                                 f"The target base directory:\n{effective_output_base}\ndoes not exist. Create it?",
                                                 QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                                 QMessageBox.StandardButton.No)
                    if reply == QMessageBox.StandardButton.Yes:
                        try:
                            effective_output_base.mkdir(parents=True, exist_ok=True)
                            self.statusBar().showMessage(f"Created target base directory: {effective_output_base}", 3000)
                        except Exception as e:
                            QMessageBox.critical(self, "Error", f"Could not create target base directory:\n{effective_output_base}\nError: {e}")
                            return
                    else:
                        self.statusBar().showMessage("Target base directory creation cancelled. Operation aborted.", 3000)
                        return
                elif not effective_output_base.is_dir():
                    QMessageBox.critical(self, "Error", f"The specified target base path:\n{effective_output_base}\nis not a directory.")
                    return
        else:
            effective_output_base = source_directory # For rename, output is same as source

        # --- Dry Run ---
        if settings.dry_run:
            self.statusBar().showMessage(f"Performing Dry Run on: {source_directory.name}...", 3000)
            engine = OrganizationEngine(settings, source_directory, mode)
            dry_run_results = []
            files_to_check_dry_run = [item for item in source_directory.iterdir() if item.is_file()]
            if not files_to_check_dry_run:
                QMessageBox.information(self, "Dry Run Results", "No files found in source directory to process.")
                self.statusBar().showMessage("Dry run: No files found.", 5000)
                return

            for src_path, target_path, status_message in engine.process_files_generator(files_to_check_dry_run):
                dry_run_results.append((src_path, target_path, status_message))

            self.statusBar().showMessage(f"Dry run complete. {len(dry_run_results)} potential actions.", 5000)
            self._show_dry_run_results_dialog(dry_run_results, source_directory, effective_output_base)
            return

        # --- Live Run ---
        self.statusBar().showMessage(f"Starting {mode} for: {source_directory.name}...", 0)
        self.organization_config_panel.organize_button.setEnabled(False)
        self.organization_config_panel.rename_button.setEnabled(False)

        self.progress_dialog = QProgressDialog(f"{mode.capitalize()} files...", "Cancel", 0, 100, self)
        self.progress_dialog.setWindowTitle("Processing")
        self.progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        self.progress_dialog.setAutoClose(False)
        self.progress_dialog.setAutoReset(False)
        self.progress_dialog.setValue(0)

        self.organization_worker = OrganizationWorker(settings, source_directory, OrganizationEngine, mode)
        self.organization_worker.progress_updated.connect(self._on_worker_progress)
        self.organization_worker.finished.connect(self._on_worker_finished)
        self.organization_worker.error_occurred.connect(self._on_worker_error)
        self.progress_dialog.canceled.connect(self.organization_worker.cancel)

        self.organization_worker.start()
        self.progress_dialog.show()

    def _on_worker_progress(self, current_item: int, total_items: int, message: str):
            if self.progress_dialog:
                if total_items > 0:
                    percentage = int((current_item / total_items) * 100)
                    self.progress_dialog.setValue(percentage)
                else:
                    self.progress_dialog.setValue(0)
                self.progress_dialog.setLabelText(message)
                self.statusBar().showMessage(message, 3000)

    def _on_worker_finished(self, results: list):
        if self.progress_dialog:
            self.progress_dialog.setValue(self.progress_dialog.maximum())
            self.progress_dialog.close()
            self.progress_dialog = None

        # Re-enable buttons
        self.organization_config_panel.organize_button.setEnabled(True)
        self.organization_config_panel.rename_button.setEnabled(True)

        if not self.organization_worker:
            return # Should not happen, but good practice

        mode = self.organization_worker.mode
        was_cancelled = any("Cancelled" in r[2] for r in results if len(r) > 2 and r[2])

        if not self.organization_worker.settings.dry_run and not was_cancelled:
            successful_moves = []
            for result_item in results:
                if len(result_item) == 3:
                    source_path, target_path, status_msg = result_item
                    if status_msg and (status_msg.startswith("Moved") or status_msg.startswith("Copied") or status_msg.startswith("Overwritten") or status_msg.startswith("Renamed")):
                        successful_moves.append((source_path, target_path))

            if successful_moves:
                # Create appropriate command based on operation type
                operation_type = getattr(self.organization_worker.settings, 'operation_type', 'Move')
                if operation_type == "Copy":
                    command = BatchCopyCommand(successful_moves)
                    command.description = f"Copied {len(successful_moves)} file(s)"
                else:
                    command = BatchMoveCommand(successful_moves)
                    if mode == "organize":
                        command.description = f"Moved {len(successful_moves)} file(s)"
                    else:
                        command.description = f"Renamed {len(successful_moves)} file(s)"
                self.undo_manager.add_command(command)

        if was_cancelled:
            QMessageBox.warning(self, "Operation Cancelled", f"File {mode} was cancelled by the user.")
            self.statusBar().showMessage(f"{mode.capitalize()} cancelled.", 5000)
        else:
            successful_ops = 0
            failed_ops_details = []
            for result_item in results:
                if len(result_item) == 3:
                    source_path, target_path, status_msg = result_item
                    if status_msg and (status_msg.startswith("Error") or status_msg.startswith("Shutil Error")):
                        source_name = source_path.name if source_path else "Unknown source"
                        failed_ops_details.append((source_name, status_msg))
                    elif not status_msg.startswith("Skipped") and not status_msg.startswith("Already in place"):
                        successful_ops += 1
                else:
                    failed_ops_details.append(("Unknown item", "Malformed result from worker"))

            # Get operation type for better status messages
            operation_type = getattr(self.organization_worker.settings, 'operation_type', 'Move')
            if operation_type == "Copy":
                operation_verb = "copied"
            else:
                operation_verb = "moved"

            if not failed_ops_details:
                if mode == "organize":
                    message = f"{successful_ops} files {operation_verb} successfully."
                else:
                    message = f"{successful_ops} files renamed successfully."
                QMessageBox.information(self, f"{mode.capitalize()} Complete", message)
                self.statusBar().showMessage(f"{mode.capitalize()} complete.", 5000)
            else:
                if mode == "organize":
                    operation_desc = operation_verb
                else:
                    operation_desc = "renamed"

                summary_message = (
                    f"{mode.capitalize()} finished with errors.\n\n"
                    f"Successfully {operation_desc}: {successful_ops} item(s).\n"
                    f"Failed to process: {len(failed_ops_details)} item(s).\n\n"
                    "First few errors:\n"
                )
                for i, (name, err) in enumerate(failed_ops_details):
                    if i < 5:
                        summary_message += f"- {name}: {err}\n"
                    else:
                        summary_message += "\n...and more. Check console output for all errors."
                        break
                QMessageBox.warning(self, f"{mode.capitalize()} Complete with Errors", summary_message)
                self.statusBar().showMessage(f"{mode.capitalize()} complete with {len(failed_ops_details)} errors.", 5000)

        self.file_browser_panel.refresh_list()
        self.organization_worker = None


    def _on_worker_error(self, error_message: str):
            if self.progress_dialog:
                self.progress_dialog.close() # Close progress dialog on error
                self.progress_dialog = None

            self.organization_config_panel.organize_button.setEnabled(True)
            self.organization_config_panel.rename_button.setEnabled(True)
            QMessageBox.critical(self, "Organization Error", error_message)
            self.statusBar().showMessage(f"Error: {error_message}", 5000)
            self.organization_worker = None

    def _show_dry_run_results_dialog(self, results: List[Tuple[pathlib.Path, pathlib.Path, str]],
                                         source_directory: pathlib.Path,
                                         effective_output_base_dir: pathlib.Path):
            if not results:
                QMessageBox.information(self, "Dry Run Results", "No files matched the criteria or no actions proposed.")
                return
            dialog = DryRunResultsDialog(results, source_directory, effective_output_base_dir, self)
            dialog.exec()



if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
