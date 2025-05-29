# src/main.py
import sys
import pathlib

from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QSplitter,
    QTabWidget,
    QMessageBox
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

from engine import OrganizationEngine # This will be uncommented once engine.py is created

# --- TEMPORARY Placeholder for OrganizationEngine ---
# class OrganizationEngine:
#     def __init__(self, settings: OrganizationSettings, source_directory: pathlib.Path):
#         self.settings = settings
#         self.source_directory = source_directory
#         print(f"TEMP: OrganizationEngine initialized for '{source_directory}' with settings: {settings}")

#     def process_files(self) -> List[Tuple[pathlib.Path, pathlib.Path, str]]:
#         print(f"TEMP: OrganizationEngine.process_files() called. Dry Run: {self.settings.dry_run}")
#         # Simulate some results for testing the dialog
#         if self.settings.dry_run:
#             # Use more realistic paths for dialog testing
#                          base = self.source_directory
#                          return [
#                              (base / "source_file1.txt", base / self.settings.structure_template.split('/')[0] / "file1_moved.txt", "To be moved"),
#                              (base / "image_to_rename.jpg", base / "conflict_dir" / "image_to_rename.jpg", "Conflict: To be renamed to image_to_rename_1.jpg"),
#                              (base / "document_to_skip.docx", base / "existing_folder" / "document_to_skip.docx", "Skipped: Target exists"),
#                              (base / "another.png", base / "Photos" / "2023" / "another.png", "To be moved"),
#                              (base / "archive.zip", base / "Archives" / "archive.zip", "To be moved")
#                          ]
#         return []
# --- END TEMPORARY Placeholder ---


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Chrono Filer - v0.0.7") # Version bump
        self.setGeometry(100, 100, 1280, 800) # Slightly wider for comfort

        self._create_panels()
        self._create_menus()
        self._create_status_bar()
        self._create_main_layout()
        self._connect_signals()
        # self._create_dock_widgets() # We are removing the dock for OrganizationConfigPanel


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

    # def _create_dock_widgets(self):
    #     # This method is no longer needed for the OrganizationConfigPanel
    def on_start_organization(self, settings: OrganizationSettings):
        current_browse_path_str = self.file_browser_panel.current_path
        source_directory = pathlib.Path(current_browse_path_str)

        if not source_directory.is_dir():
            self.statusBar().showMessage(f"Error: Source path '{source_directory.name}' is not a valid directory.", 5000)
            QMessageBox.critical(self, "Error", f"The selected source path '{source_directory}' is not a valid directory.")
            return

        self.statusBar().showMessage(f"Processing: {source_directory.name} (Dry Run: {settings.dry_run})...", 3000)
        print(f"Organization started for: {source_directory}") # For debugging
        print(f"Using settings: {settings}")

        # Instantiate and run the engine
        # from engine import OrganizationEngine # This will be at the top of the file later
        engine = OrganizationEngine(settings, source_directory)
        results = engine.process_files()

        if settings.dry_run:
            self.statusBar().showMessage(f"Dry run complete. {len(results)} potential actions proposed.", 10000)
            self._show_dry_run_results_dialog(results, source_directory)
        else:
            # For actual run, we might want to refresh the file browser
            self.statusBar().showMessage(f"Organization complete. {len(results)} actions performed.", 10000)
            QMessageBox.information(self, "Organization Complete", f"{len(results)} actions were performed.")
            self.file_browser_panel.refresh_list() # Refresh browser after actual changes

    def _show_dry_run_results_dialog(self, results: List[Tuple[pathlib.Path, pathlib.Path, str]], source_directory: pathlib.Path):
        if not results:
                QMessageBox.information(self, "Dry Run Results", "No files matched the criteria or no actions proposed.")
                return

        # Instantiate and show the new dialog
        dialog = DryRunResultsDialog(results, source_directory, self) # Pass parent=self
        dialog.exec() # Use exec() for modal dialogs


        # For now, just print. We'll build a dialog in the next step.
        # print("\n--- DRY RUN RESULTS (Dialog Placeholder) ---")
        # for source, target, status in results:
        #     print(f"[{status}] {source.name}  ==>  {target}")
        # print("-------------------------------------------\n")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
