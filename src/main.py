# src/main.py
import sys
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QSplitter,
    # QDockWidget, # No longer needed for OrganizationConfigPanel
    QTabWidget    # Import QTabWidget
)
from PySide6.QtCore import Qt, QSize

from widgets import FileBrowserPanel, PreviewPanel, MetadataPanel, OrganizationConfigPanel

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Chrono Filer - v0.0.5") # Version bump
        self.setGeometry(100, 100, 1280, 800) # Slightly wider for comfort

        self._create_menus()
        self._create_status_bar()
        self._create_main_layout()
        # self._create_dock_widgets() # We are removing the dock for OrganizationConfigPanel

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
        # You might want to set initial sizes too, e.g., right_splitter.setSizes([600, 200])

        # --- Main Horizontal Splitter ---
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        main_splitter.addWidget(self.file_browser_panel)
        main_splitter.addWidget(right_splitter)

        main_splitter.setStretchFactor(0, 1) # File browser (e.g., 1 part)
        main_splitter.setStretchFactor(1, 2) # Right section (Preview + Tabs) (e.g., 2 parts)
        # You might want to set initial sizes, e.g., main_splitter.setSizes([400, 800])

        self.setCentralWidget(main_splitter)

    # def _create_dock_widgets(self):
    #     # This method is no longer needed for the OrganizationConfigPanel
    #     # If you plan other dock widgets, you can keep/modify it.
    #     pass


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
