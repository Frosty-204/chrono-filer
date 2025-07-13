import pathlib
from typing import List, Tuple, Any # Any for engine, if not fully typed yet
import time
from PySide6.QtCore import QThread, Signal

# from .widgets import OrganizationSettings # If settings is in widgets
# from .engine import OrganizationEngine    # If engine is in engine

# DEBUG_OPERATION_DELAY = 0  # SHOULD NOT BE USED IN PRODUCTION

class OrganizationWorker(QThread):
    progress_updated = Signal(int, int, str)
    finished = Signal(list)
    error_occurred = Signal(str)

    def __init__(self, settings: Any, source_directory: pathlib.Path, engine_class: Any, mode: str = "organize", parent=None):
        super().__init__(parent)
        self.settings = settings
        self.source_directory = source_directory
        self.engine_class = engine_class
        self.mode = mode
        self._is_cancelled = False

    def run(self):
        results = []
        try:
            engine = self.engine_class(self.settings, self.source_directory, self.mode)

            # files_to_process_potentially = [
            #     item for item in self.source_directory.iterdir() if item.is_file()
            # ]
            # total_items = len(files_to_process_potentially)

            print(f"Starting file scan (Recursive: {self.settings.process_recursively})...")
            if self.settings.process_recursively:
                # Use rglob() for a deep, recursive scan of all files
                files_to_process_potentially = [
                    item for item in self.source_directory.rglob('*') if item.is_file()
                ]
            else:
                # Use iterdir() for a shallow, non-recursive scan (the original behavior)
                files_to_process_potentially = [
                    item for item in self.source_directory.iterdir() if item.is_file()
                ]
            print(f"Scan complete. Found {len(files_to_process_potentially)} files to check.")


            total_items = len(files_to_process_potentially)

            if total_items == 0:
                self.progress_updated.emit(0, 0, "No files found in source directory.")
                self.finished.emit([])
                return

            processed_count = 0

            # Iterate through the generator provided by the engine
            # The engine itself will perform the actual file operations if not dry_run
            item_generator = engine.process_files_generator(files_to_process_potentially)

            while True:
                if self._is_cancelled:
                    self.progress_updated.emit(processed_count, total_items, "Operation Cancelling...")
                    break # Exit the processing loop

                try:
                    source_path, target_path, status_msg = next(item_generator)
                    # If next() succeeds, an item was processed (or yielded) by the engine
                    processed_count += 1 # Increment only after successfully getting an item
                    results.append((source_path, target_path, status_msg))
                    self.progress_updated.emit(processed_count, total_items, f"Status: {status_msg}")

                except StopIteration:
                    # Generator is exhausted, all items processed
                    break
                except Exception as e_gen: # Catch errors from the generator itself
                    self.error_occurred.emit(f"Error within engine processing: {str(e_gen)}")
                    # Decide if we should continue or break. For now, break.
                    # You might want to add the problematic item to results with an error status.
                    results.append((None, None, f"Engine Error: {str(e_gen)}")) # Placeholder for errored item
                    break


                # --- ARTIFICIAL DELAY FOR DEBUGGING ---
                # if DEBUG_OPERATION_DELAY > 0 and not self.settings.dry_run: # Delay only for actual runs
                #     time.sleep(DEBUG_OPERATION_DELAY)
                # --- END ARTIFICIAL DELAY ---

            self.finished.emit(results) # Emit whatever results were gathered

        except Exception as e_outer: # Catch errors in worker setup (e.g., engine init)
            self.error_occurred.emit(f"An error occurred in worker setup: {str(e_outer)}")
            if not results: # If results is empty and an error occurred, emit empty list for finished
                self.finished.emit([])


    def cancel(self):
        # print("DEBUG: Worker cancel method called")
        self._is_cancelled = True
