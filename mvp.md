**I. Core Application Purpose:**
To empower users to efficiently organize large sets of files into a structured directory system based on user-defined criteria and patterns, with robust file management and preview capabilities.

**II. Feature Breakdown & Prioritization:**

**MVP (Minimum Viable Product):** Focus on core organization and viewing.

1. **File Browser:**

    - List view with sortable columns (name, date, size, type).

    - Basic tree view for navigation.

2. **Basic File Operations (Browser):**

    - Select single/multiple files.

    - Context menu for basic actions (e.g., preparing for move/copy in organization).

3. **Metadata Display:**

    - For selected files: creation/modification date/time, file type (from extension/mime), size.

4. **File Preview Pane:**

    - Images: PNG, JPEG.

    - Text Files: .txt, .log, .md.

    - Other types: Generic icon, option to "Open with default application."

5. **Organization Engine (Core):**

    - **Source Selection:** Select a source directory.

    - **Standard Filters:** Name (contains, starts/ends with, exact), creation/modification date (range), file type (by extension), file size (range).

    - **Automated Directory Creation & File Movement:**

        - Move files (copy can be later).

        - Define output structure (e.g., [Year]/[Month]/filename.ext).

    - **Conflict Resolution:** Basic options (e.g., skip, rename with suffix).

    - **"Dry Run" / Preview Mode:** Show proposed changes before execution.

6. **UI/UX Essentials:**

    - Clear visual feedback (status messages, progress indication for organization).

    - Session persistence (remember last used source directory, window size).


**Phase 2: Advanced Features & Polish**

1. **Enhanced File System Operations:**

    - Full tree view functionality in file browser.

    - Create, delete, and rename directories directly within the application.

    - Robust move, copy, and delete files (single and bulk) from the browser.

2. **Enhanced Metadata:**

    - Display file/directory permissions.

3. **Improved File Viewer:**

    - Support for more image formats (GIF, BMP, SVG).

    - Scroll navigation for large text files.

    - **Known Issue:** Syntax highlighting may not display correctly on some desktop environments (e.g., Hyprland with light mode). This will be addressed in Phase 3 UI/UX overhaul.

4. **Advanced Organization Engine:**

    - **Regex-Powered Filtering:**

        - Define/select regex patterns for filenames.

        - Interface to test patterns against sample filenames.

    - **Bulk Renaming Tool:**

        - Options: find/replace, add prefix/suffix.

        - Preview changes before applying.

    - **Advanced Structure Templates:** Use regex capture groups (e.g., [Capture Group 1]/filename.ext).

    - **Move/Copy Option:** User choice for organization tasks.

    - **Conflict Resolution:** More options (e.g., overwrite).

    - **Incremental Organization:** Integrate new files into an existing organized structure.

5. **UI/UX Enhancements:**

    - Basic Undo functionality for recent file moves/renames.

    - **Configurable settings panel** (e.g., default date formats, previewer options). ✅ COMPLETED

    - Improved progress bars and status reporting.


**Phase 3: Future Enhancements**

1. Advanced Bulk Renaming: Sequential numbering, change case, use metadata in renaming.

2. Advanced Preview: Basic navigation for multi-page documents (e.g., PDF, if feasible and libraries allow easily).

3. Full Undo/Redo stack for more operations.

4. User-defined presets for filters and organization rules.

5. Theming and greater UI customization.

6. Background processing for very large organization tasks with system notifications.

**Phase 4: Advanced File Processing Features**

1. **File Permissions Management:**
   - Set POSIX permissions (Unix/Linux/macOS) during file organization
   - Configurable permissions for different file types
   - Recursive permission setting for directories
   - Preview permissions changes before execution

2. **File Compression & Archiving:**
   - Support for multiple archive formats: ZIP, TAR.GZ, TAR.BZ2, TAR.XZ
   - Compression level selection (fast, normal, maximum)
   - Archive naming templates with variables
   - Option to compress individual files or entire directory structures
   - Split large archives into volumes

3. **File Encryption:**
   - AES-256 encryption for compressed archives
   - Password-based encryption with key derivation
   - Secure key management using system keyring
   - Encryption preview and verification
   - Support for encrypted individual files and archives


**III. High-Level Architecture:**

The application will be designed with a separation between the core logic (backend) and the graphical user interface (frontend).

- **Core Logic (Backend):**

    - FileManager: Handles all direct file system interactions (listing, reading, writing, moving, copying, deleting).

    - MetadataExtractor: Responsible for extracting and parsing file metadata (dates, type, size, permissions).

    - OrganizationEngine: Implements the logic for filtering files, applying rules, matching patterns, and determining target directory structures. It orchestrates FileManager for actual file operations.

    - RuleProcessor: Manages and interprets user-defined rules, including standard filters, regex patterns, and directory structure templates.

    - RenameEngine: Handles logic for bulk renaming operations.

    - OperationHistory: (For Undo) A stack of command objects representing reversible operations.

    - SettingsManager: Manages loading and saving application settings and user preferences.

- **GUI (Frontend):**

    - MainWindow: The main application window, containing and managing the various UI panels.

    - FileBrowserPanel: Displays the file system (tree and list views), handles file/directory selection.

    - PreviewPanel: Shows previews of selected files.

    - MetadataPanel: Displays detailed metadata for selected items.

    - OrganizationConfigPanel: UI for users to select source(s), define filters, rules, output structure templates, and choose organization options (dry run, move/copy).

    - BulkRenamePanel: UI for configuring and previewing bulk renaming operations.

    - FeedbackManager: Handles displaying progress bars, status messages, and error dialogs.

- **Interaction:**

    - The GUI will interact with the Core Logic components. For instance, user actions in OrganizationConfigPanel will configure the RuleProcessor and trigger the OrganizationEngine.

    - Long-running operations (file scanning, moving, copying, organizing) will be executed in separate worker threads to keep the UI responsive. Progress will be communicated back to the GUI for display.

    - A signal/slot mechanism (Qt) or a similar event-based system (GTK with GObject signals) will be used for communication between components.


**IV. Technology Stack Recommendations:**

- **Programming Language: Python 3**

    - **Rationale:** Rapid development, extensive standard library for file operations (os, shutil, pathlib), metadata (stat, mimetypes), and regex (re). Strong support for GUI toolkits. Its I/O-bound nature makes Python suitable as performance is less CPU-critical here.

- **GUI Toolkit: Qt 6 (via PySide6 or PyQt6) or GTK 4 (via PyGObject)**

    - **Qt (PySide6 - LGPL):**

        - **Pros:** Mature, comprehensive widget set, powerful layout and styling capabilities (can adapt to GNOME/KDE themes), excellent signal/slot mechanism, good documentation, QML for potentially richer UI elements if desired later.

        - **Cons:** Can sometimes require more effort to feel perfectly "native" on GNOME than a GTK app.

    - **GTK 4 (PyGObject - LGPL):**

        - **Pros:** Native look and feel on GNOME and GNOME-based desktops. Strong integration with the GNOME ecosystem. Modern features in GTK4.

        - **Cons:** API can be less straightforward for some developers compared to Qt. Might look less integrated on KDE/other environments if specific theming isn't perfect.

    - **Recommendation:** **Qt 6 with PySide6** is slightly favored for its comprehensive nature and flexibility in creating a polished UI that can work well across different Linux desktop environments. However, if targeting GNOME primarily, GTK 4 is an excellent choice.

- **Key Libraries (Python):**

    - **File System & OS:** os, shutil, pathlib (standard library).

    - **Metadata:**

        - os.stat, stat, mimetypes (standard library).

        - Pillow: For image dimensions, type detection, and generating previews.

        - Optional: python-magic (for more robust MIME type detection).

    - **Image Handling (Preview):** Pillow (for loading/manipulation), then displayed via QPixmap (Qt) or GdkPixbuf (GTK).

    - **Regex:** re module (standard library).

    - **Configuration/Settings:** json module (standard library) for JSON files, or configparser for INI-style files.

    - **Threading:** threading module (standard library) combined with GUI toolkit's mechanisms for updating UI from threads (e.g., QThread.signals in Qt, GLib.idle_add in GTK).


**V. Development Stages/Roadmap:**

- **Stage 0: Foundation & Initial Prototyping (2-3 weeks)**

    - Setup: Dev environment, Python, GUI toolkit, Git repository.

    - Basic application window with main layout (placeholder panels).

    - Simple directory lister (populating a list widget).

    - Prototype metadata display for a selected item.

- **Stage 1: MVP - Core Browsing, Viewing & Basic Organization (8-10 weeks)**

    - **File Browser:** Implement list view, sorting, basic tree navigation.

    - **Metadata Display:** Show name, date, size, type.

    - **Preview Pane:** Implement image (PNG, JPEG) and text file preview. Generic icon for others.

    - **Organization Engine (MVP features):**

        - Source selection.

        - Standard filters UI and logic.

        - Basic directory structure template UI and logic.

        - File moving mechanism.

        - Basic conflict resolution.

        - "Dry run" functionality.

    - **UI Feedback:** Status messages, basic progress display. Session persistence for last source.

- **Stage 2: Phase 2 - Advanced File Ops, Regex, Renaming (10-12 weeks)**

    - **Enhanced File Browser:** Full tree view, create/delete/rename directories, robust file move/copy/delete.

    - **Advanced Organization:** Regex filters, regex test UI, structure templates with regex groups, copy option for organization, incremental organization.

    - **Bulk Renaming:** Initial tool with find/replace, prefix/suffix, preview.

    - **Improved Previewer:** More image formats, text scrolling.

    - **Metadata:** Display permissions.

- **Stage 3: Phase 2 - Polish, Undo, Settings (6-8 weeks)**

    - **Undo Functionality:** Implement basic undo for file moves/renames.

    - **Configurable Settings:** Create settings panel.

    - **UI/UX Refinement:** Improve workflow, visual consistency, error handling.

    - Address feedback from early testing.

- **Stage 4: Beta Testing & Iteration (Ongoing)**

    - Package application (Flatpak, Snap, or .deb/.rpm).

    - Gather wider user feedback.

    - Bug fixing and performance optimization.

- **Stage 5: Phase 3 - Future Enhancements (Post-initial stable release)**

    - Implement features from "Phase 3" list based on priority and feedback.


**VI. Key UI/UX Design Principles:**

1. **Intuitive & Clean:** Prioritize ease of use. Avoid overwhelming users with too many options at once.

2. **Clarity & Feedback:** Users must always understand what the application is doing. Use progress bars, status messages, and visual cues.

3. **Efficiency:** Design for users managing large numbers of files. Keyboard shortcuts and streamlined workflows are important.

4. **Safety First:** "Dry run" is essential. Destructive operations should be confirmable. Undo is a key goal.

5. **Consistency:** Maintain consistent design language and interaction patterns throughout. Adhere to general Linux desktop environment guidelines.

6. **Discoverability:** Make features easy to find and understand. Use tooltips and clear labeling.

7. **Responsiveness:** The UI must never freeze. Long operations must use background threads.


**VII. Potential Challenges and Mitigation Strategies:**

1. **Performance with Large File Sets:**

    - **Mitigation:** Use os.scandir() for faster directory iteration. Thread I/O operations. Lazy load data. Optimize filter logic.

2. **Undo Functionality Complexity:**

    - **Mitigation:** Implement the Command Pattern. Start with undo for simpler operations (move/rename) and expand. Clearly define the scope of undo.

3. **Regex Usability:**

    - **Mitigation:** Provide pre-defined common patterns, a real-time regex tester, and clear examples/documentation.

4. **Robust Error Handling:**

    - **Mitigation:** Extensive try-except blocks for all file operations. User-friendly error messages. Options for handling errors in bulk operations (skip, abort, retry).

5. **Cross-Desktop Appearance (if Qt is chosen and high fidelity is needed everywhere):**

    - **Mitigation:** Utilize Qt's styling system, platform plugins, and consider tools like qt5ct/qt6ct for user-level theming. Prioritize a clean, neutral default style.

6. **State Management:**

    - **Mitigation:** Well-defined data models. Clear separation of UI state from application data. Use signals/events for state change notifications.


**VIII. Phase 2 Implementation Status:**

**✅ ALL PHASE 2 FEATURES COMPLETED:**
- ✅ Enhanced File System Operations (create, delete, rename with undo support)
- ✅ Enhanced Metadata (permissions display, file source detection)
- ✅ Improved File Viewer (extended formats, find functionality, basic syntax highlighting)
- ✅ Advanced Organization Engine (move/copy, regex filtering, bulk renaming)
- ✅ Configurable Settings Panel (comprehensive settings dialog with organization, preview, UI, and advanced options)

**Phase 2 Summary:**
Phase 2 development is now complete! The application includes all planned advanced features with comprehensive settings management, enhanced file operations, improved metadata display, and a robust file viewer with syntax highlighting support.

**Known Issues (Deferred to Phase 3):**
- Syntax highlighting may not render correctly on some desktop environments (Hyprland, light themes)
- Comprehensive theme system implementation pending

**IX. Testing and Quality Assurance:**

1. **Unit Tests:** For all core logic modules (file management, metadata, organization engine, rules, renaming). Mock file system where feasible.

2. **Integration Tests:** Test interactions between core modules and between UI and core logic.

3. **Manual UI Testing:** Essential for workflows, visual checks, and usability on target desktop environments (GNOME, KDE).

    - Test with diverse file sets: many files, large files, complex names, varied types.

    - Test edge cases: permissions issues, disk full, network paths (if supported).

    - Thoroughly test conflict resolution and "dry run" accuracy.

4. **Performance Testing:** Use sample large datasets to identify and address bottlenecks.

5. **Usability Testing:** Gather feedback from representative users throughout development.

6. **Regression Test Suite:** Build up a suite of tests to run regularly to catch regressions.

7. **Test Data:** Maintain a repository of test files and directory structures designed to cover various scenarios.


This development plan provides a structured approach to building Chrono Filer. Flexibility will be key, and priorities may shift based on development realities and early user feedback.
