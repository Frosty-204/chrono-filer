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
from PySide6.QtCore import Qt, QSize
from typing import List, Tuple

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

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Chrono Filer - v0.0.9") # Version bump
        self.setGeometry(100, 100, 1280, 800) # Slightly wider for comfort

        self._create_panels()
        self._create_menus()
        self._create_status_bar()
        self._create_main_layout()
        self._connect_signals()

        self.organization_worker = None
        self.progress_dialog = None

    def _create_panels(self):
        self.file_browser_panel = FileBrowserPanel()
        self.preview_panel = PreviewPanel()
        self.metadata_panel = MetadataPanel()
        self.organization_config_panel = OrganizationConfigPanel()
        self.bottom_right_tabs = QTabWidget() # Will hold metadata and org config

    def _connect_signals(self):
        # File Browser -> Metadata & Preview
        if hasattr(self.file_browser_panel, 'selection_changed'):
            if hasattr(self.metadata_panel, 'update_metadata'):
                self.file_browser_panel.selection_changed.connect(self.metadata_panel.update_metadata)
            if hasattr(self.preview_panel, 'update_preview'):
                self.file_browser_panel.selection_changed.connect(self.preview_panel.update_preview)

        # Organization Panel -> Start Organization
        if hasattr(self.organization_config_panel, 'organize_triggered'):
            self.organization_config_panel.organize_triggered.connect(self.on_start_organization)
        else:
            print("Warning: organization_config_panel.organize_triggered signal not found.")

        # Connections remain the same
        if hasattr(self.file_browser_panel, 'selection_changed'):
            if hasattr(self.metadata_panel, 'update_metadata'):
                self.file_browser_panel.selection_changed.connect(self.metadata_panel.update_metadata)
            else:
                print("Warning: Could not connect to metadata_panel.update_metadata.")

            if hasattr(self.preview_panel, 'update_preview'):
                self.file_browser_panel.selection_changed.connect(self.preview_panel.update_preview)
            else:
                print("Warning: Could not connect to preview_panel.update_preview.")
        else:
            print("Warning: file_browser_panel.selection_changed signal not found.")

    def _create_menus(self):
        # ... (menu creation remains the same)
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("&File")
        file_menu.addAction("E&xit", self.close)
        edit_menu = menu_bar.addMenu("&Edit")
        view_menu = menu_bar.addMenu("&View")
        tools_menu = menu_bar.addMenu("&Tools")
        help_menu = menu_bar.addMenu("&Help")
        help_menu.addAction("&About")


    def _create_status_bar(self):
        self.statusBar().showMessage("Ready")

    def _create_main_layout(self):
        # --- Instantiate Panels ---
        self.file_browser_panel = FileBrowserPanel()
        self.preview_panel = PreviewPanel()
        self.metadata_panel = MetadataPanel()
        self.organization_config_panel = OrganizationConfigPanel() # Now a regular widget

        # --- Bottom Right Tab Widget ---
        self.bottom_right_tabs = QTabWidget()
        self.bottom_right_tabs.addTab(self.metadata_panel, "Metadata")
        self.bottom_right_tabs.addTab(self.organization_config_panel, "Organization")

        # --- Right Vertical Splitter ---
        # Contains PreviewPanel on top, and the TabWidget on the bottom
        right_splitter = QSplitter(Qt.Orientation.Vertical)
        right_splitter.addWidget(self.preview_panel)
        right_splitter.addWidget(self.bottom_right_tabs)

        # Adjust stretch factors: Give more space to the preview panel
        right_splitter.setStretchFactor(0, 3) # Preview panel (e.g., 3 parts of available space)
        right_splitter.setStretchFactor(1, 1) # Tab widget (e.g., 1 part of available space)
        right_splitter.setSizes([550, 250]) # Adjusted initial sizes
        # You might want to set initial sizes too, e.g., right_splitter.setSizes([600, 200])

        # --- Main Horizontal Splitter ---
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        main_splitter.addWidget(self.file_browser_panel)
        main_splitter.addWidget(right_splitter)

        main_splitter.setStretchFactor(0, 1) # File browser (e.g., 1 part)
        main_splitter.setStretchFactor(1, 2) # Give more space to the right side
        main_splitter.setSizes([350, 930])   # Adjusted initial sizes


        self.setCentralWidget(main_splitter)

    def on_start_organization(self, settings: OrganizationSettings):
           print(f"DEBUG MAINWINDOW: Received settings with target_base_directory: {settings.target_base_directory}") # DBG
           current_browse_path_str = self.file_browser_panel.current_path
           source_directory = pathlib.Path(current_browse_path_str)

           if not source_directory.is_dir():
               QMessageBox.critical(self, "Error", f"The selected source path '{source_directory}' is not a valid directory.")
               return

           effective_output_base = settings.target_base_directory.resolve() if settings.target_base_directory else source_directory.resolve()

           if settings.target_base_directory:
                if not settings.target_base_directory.exists() and not settings.dry_run:
                # Attempt to create it if it doesn't exist for actual run (engine also does this, but good for early check)
                    try:
                        settings.target_base_directory.mkdir(parents=True, exist_ok=True)
                    except Exception as e:
                        QMessageBox.critical(self, "Error", f"Cannot create target directory '{settings.target_base_directory}': {e}")
                    return
                elif settings.target_base_directory.exists() and not settings.target_base_directory.is_dir():
                    QMessageBox.critical(self, "Error", f"Target path '{settings.target_base_directory}' exists but is not a directory.")
                    return

           if settings.dry_run:
                self.statusBar().showMessage(f"Performing Dry Run on: {source_directory.name}...", 3000)
                engine = OrganizationEngine(settings, source_directory)
                dry_run_results = []
                files_to_check_dry_run = [item for item in source_directory.iterdir() if item.is_file()]
                if not files_to_check_dry_run:
                    QMessageBox.information(self, "Dry Run Results", "No files found in source directory to process.")
                    self.statusBar().showMessage("Dry run: No files found.", 5000)
                    return

                # CONSISTENT VARIABLE NAME HERE
                for src_path, target_path, status_message in engine.process_files_generator(files_to_check_dry_run):
                    dry_run_results.append((src_path, target_path, status_message))

                self.statusBar().showMessage(f"Dry run complete. {len(dry_run_results)} potential actions.", 5000)
                self._show_dry_run_results_dialog(dry_run_results, source_directory, effective_output_base)
           else:
               # Actual Run - Use the Worker Thread

               self.statusBar().showMessage(f"Starting organization for: {source_directory.name}...", 0)
               self.organization_config_panel.organize_button.setEnabled(False)
               self.progress_dialog = QProgressDialog("Organizing files...", "Cancel", 0, 100, self)


               self.progress_dialog.setWindowTitle("Processing")
               self.progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
               self.progress_dialog.setAutoClose(False) # We will close it manually
               self.progress_dialog.setAutoReset(False) # We will reset it manually
               self.progress_dialog.setValue(0) # Start at 0%

               self.organization_worker = OrganizationWorker(settings, source_directory, OrganizationEngine) # Pass engine class

               self.organization_worker.progress_updated.connect(self._on_worker_progress)
               self.organization_worker.finished.connect(self._on_worker_finished)
               self.organization_worker.error_occurred.connect(self._on_worker_error)

               self.progress_dialog.canceled.connect(self.organization_worker.cancel) # Connect cancel signal

               self.organization_worker.start()
               self.progress_dialog.show()

    def _on_worker_progress(self, current_item: int, total_items: int, message: str):
            if self.progress_dialog:
                if total_items > 0:
                    percentage = int((current_item / total_items) * 100)
                    self.progress_dialog.setValue(percentage)
                else: # Should not happen if worker checks for total_items == 0
                    self.progress_dialog.setValue(0)
                self.progress_dialog.setLabelText(message)
                self.statusBar().showMessage(message, 3000) # Also update status bar

    def _on_worker_finished(self, results: list):
            if self.progress_dialog:
                self.progress_dialog.setValue(self.progress_dialog.maximum()) # Mark as 100%
                self.progress_dialog.close()
                self.progress_dialog = None

            self.organization_config_panel.organize_button.setEnabled(True) # Re-enable button

            # Check if operation was cancelled (last result might indicate this if worker appends "Cancelled")
            was_cancelled = any("Cancelled" in r[2] for r in results if len(r) > 2)

            if was_cancelled:
                QMessageBox.warning(self, "Operation Cancelled", "File organization was cancelled by the user.")
                self.statusBar().showMessage("Organization cancelled.", 5000)
            else:
                QMessageBox.information(self, "Organization Complete", f"{len(results)} file actions processed.")
                self.statusBar().showMessage("Organization complete.", 5000)

            self.file_browser_panel.refresh_list() # Refresh file browser
            self.organization_worker = None


    def _on_worker_error(self, error_message: str):
            if self.progress_dialog:
                self.progress_dialog.close() # Close progress dialog on error
                self.progress_dialog = None

            self.organization_config_panel.organize_button.setEnabled(True)
            QMessageBox.critical(self, "Organization Error", error_message)
            self.statusBar().showMessage(f"Error: {error_message}", 5000)
            self.organization_worker = None

    def _show_dry_run_results_dialog(self, results: List[Tuple[pathlib.Path, pathlib.Path, str]],
                                         source_directory: pathlib.Path,
                                         effective_output_base_dir: pathlib.Path): # Correct: 3 params other than self
            if not results:
                QMessageBox.information(self, "Dry Run Results", "No files matched the criteria or no actions proposed.")
                return
            # PASS effective_output_base_dir to dialog constructor
            dialog = DryRunResultsDialog(results, source_directory, effective_output_base_dir, self) # Calling with 4 args + implicit self for dialog
            dialog.exec()



if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
