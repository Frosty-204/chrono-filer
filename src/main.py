# src/main.py
import sys
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QSplitter,
    QDockWidget
)
from PySide6.QtCore import Qt, QSize # Import QSize

# try:
#     test_orientation_direct = Qt.Horizontal # This is what you're currently doing
#     test_orientation_enum = Qt.Orientation.Horizontal
#     test_alignment_enum = Qt.AlignmentFlag.AlignCenter
#     test_dock_area_enum = Qt.DockWidgetArea.BottomDockWidgetArea
#     print(test_orientation_direct, test_orientation_enum, test_alignment_enum, test_dock_area_enum) # To avoid "unused" warnings
# except AttributeError as e:
#     print(f"AttributeError during diagnostic: {e}")

# Assuming widgets.py is in the same directory (src)
from widgets import FileBrowserPanel, PreviewPanel, MetadataPanel, OrganizationConfigPanel

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Chrono Filer - v0.0.4")
        self.setGeometry(100, 100, 1200, 800) # x, y, width, height

        self._create_menus()
        self._create_status_bar()
        self._create_main_layout()
        self._create_dock_widgets()

        # --- New Connection ---
        if hasattr(self.file_browser_panel, 'selection_changed'):
            # Connect to MetadataPanel
            if hasattr(self.metadata_panel, 'update_metadata'):
                self.file_browser_panel.selection_changed.connect(self.metadata_panel.update_metadata)
            else:
                print("Warning: Could not connect to metadata_panel.update_metadata.")

            # --- New Connection for PreviewPanel ---
            if hasattr(self.preview_panel, 'update_preview'):
                self.file_browser_panel.selection_changed.connect(self.preview_panel.update_preview)
            else:
                print("Warning: Could not connect to preview_panel.update_preview.")
        else:
            print("Warning: file_browser_panel.selection_changed signal not found.")


    def _create_menus(self):
        menu_bar = self.menuBar()

        # File Menu
        file_menu = menu_bar.addMenu("&File")
        file_menu.addAction("E&xit", self.close) # self.close is a QWidget slot

        # Edit Menu (placeholder)
        edit_menu = menu_bar.addMenu("&Edit")
        # Add actions later: Undo, Redo, Preferences

        # View Menu (placeholder)
        view_menu = menu_bar.addMenu("&View")
        # Add actions later: Zoom, Layout options

        # Tools Menu (placeholder)
        tools_menu = menu_bar.addMenu("&Tools")
        # Add actions later: Start Organization

        # Help Menu (placeholder)
        help_menu = menu_bar.addMenu("&Help")
        help_menu.addAction("&About")
        # Add About Qt action later

    def _create_status_bar(self):
        self.statusBar().showMessage("Ready")

    def _create_main_layout(self):
        # --- Central Widget Panels ---
        self.file_browser_panel = FileBrowserPanel() # functional
        self.preview_panel = PreviewPanel()
        self.metadata_panel = MetadataPanel() # functional

        # Right vertical splitter (for Preview and Metadata)
        right_splitter = QSplitter(Qt.Orientation.Vertical)
        right_splitter.addWidget(self.preview_panel)
        right_splitter.addWidget(self.metadata_panel)
        right_splitter.setStretchFactor(0, 2) # Preview panel gets more space initially
        right_splitter.setStretchFactor(1, 1)
        right_splitter.setSizes([400, 200]) # Initial heights

        # Main horizontal splitter
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        main_splitter.addWidget(self.file_browser_panel)
        main_splitter.addWidget(right_splitter)
        main_splitter.setStretchFactor(0, 1) # File browser
        main_splitter.setStretchFactor(1, 1) # Right section (Preview + Metadata)
        main_splitter.setSizes([400, 800]) # Initial widths

        self.setCentralWidget(main_splitter)

    def _create_dock_widgets(self):
            self.organization_config_panel = OrganizationConfigPanel()

            organization_dock = QDockWidget("Organization Configuration", self)
            organization_dock.setWidget(self.organization_config_panel)

            # --- MODIFIED LINES ---
            organization_dock.setAllowedAreas(
                Qt.DockWidgetArea.BottomDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea # Fully qualified
            )
            organization_dock.setFeatures(
                QDockWidget.DockWidgetFeature.DockWidgetMovable | QDockWidget.DockWidgetFeature.DockWidgetClosable # Fully qualified
            )
            # --- END MODIFIED LINES ---

            self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, organization_dock) # Fully qualified for the area argument

            # To add to View menu later if you have self.view_menu defined:
            # if hasattr(self, 'view_menu') and self.view_menu:
            #     self.view_menu.addAction(organization_dock.toggleViewAction())


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
