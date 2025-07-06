# src/engine.py
import pathlib
import datetime
# import os
import re
import mimetypes
import shutil # For actual file operations
from typing import List, Tuple, Optional, Iterator

# Assuming OrganizationSettings is defined in widgets.py
# Adjust if you move OrganizationSettings to a models.py
try:
    from .widgets import OrganizationSettings
except ImportError:
    from widgets import OrganizationSettings


class OrganizationEngine:
    def __init__(self, settings: OrganizationSettings, source_directory: pathlib.Path):
        self.settings = settings
        self.source_directory = source_directory.resolve()


        if self.settings.target_base_directory:
            self.output_base_directory = pathlib.Path(self.settings.target_base_directory).resolve()
        else:
            self.output_base_directory = self.source_directory


    def process_files_generator(self, files_to_check: List[pathlib.Path]) -> Iterator[Tuple[pathlib.Path, pathlib.Path, str]]:
            if not self.source_directory.is_dir():
                yield (self.source_directory, self.source_directory, f"Error: Source '{self.source_directory.name}' is not a directory")
                return

            for item in files_to_check:
                if self._matches_filters(item):
                    try:
                        relative_target_path_str = self._calculate_target_path_relative(item)
                        current_proposed_target_abs = (self.output_base_directory / relative_target_path_str).resolve()

                        initial_proposed_target_for_status = current_proposed_target_abs

                        status_message = "To be moved"

                        if item.resolve() == current_proposed_target_abs.resolve():
                            status_message = f"Already in place: {current_proposed_target_abs.relative_to(self.output_base_directory)}"
                            yield item, current_proposed_target_abs, status_message
                            continue

                        if current_proposed_target_abs.exists():
                            if current_proposed_target_abs.is_dir():
                                status_message = f"Conflict: Target '{initial_proposed_target_for_status.relative_to(self.output_base_directory)}' is an existing directory. Skipped."
                            elif self.settings.conflict_resolution == "Skip":
                                status_message = f"Conflict: Target '{initial_proposed_target_for_status.relative_to(self.output_base_directory)}' exists. Skipped."
                            elif self.settings.conflict_resolution == "Overwrite":
                                status_message = f"Conflict: Target '{initial_proposed_target_for_status.relative_to(self.output_base_directory)}' exists. To be overwritten."
                            elif self.settings.conflict_resolution == "Rename with Suffix":
                                count = 1
                                original_stem = initial_proposed_target_for_status.stem
                                original_suffix = initial_proposed_target_for_status.suffix

                                current_proposed_target_abs = initial_proposed_target_for_status.with_name(f"{original_stem}_{count}{original_suffix}")
                                while current_proposed_target_abs.exists():
                                    count += 1
                                    current_proposed_target_abs = initial_proposed_target_for_status.with_name(f"{original_stem}_{count}{original_suffix}")

                                status_message = f"Conflict: Target '{initial_proposed_target_for_status.relative_to(self.output_base_directory)}' exists. To be renamed to '{current_proposed_target_abs.name}'."

                        if not self.settings.dry_run:
                            if "Skipped" not in status_message and "Error" not in status_message and "Already in place" not in status_message:
                                try:
                                    current_proposed_target_abs.parent.mkdir(parents=True, exist_ok=True)

                                       # DEBUG

                                    if "error.zip" in item.name and not self.settings.dry_run:
                                        status_message = "Error moving: Forced test error"
                                        yield item, current_proposed_target_abs, status_message
                                        continue # Skip actual move for this test

                                    shutil.move(str(item), str(current_proposed_target_abs))

                                    if "To be overwritten" in status_message:
                                        status_message = f"Overwritten: {initial_proposed_target_for_status.relative_to(self.output_base_directory)}"
                                    elif "To be renamed to" in status_message: # The status already mentions the new name from current_proposed_target_abs.name
                                        status_message = f"Moved and Renamed to: {current_proposed_target_abs.relative_to(self.output_base_directory)}"
                                    else:
                                        status_message = f"Moved to: {current_proposed_target_abs.relative_to(self.output_base_directory)}"

                                except shutil.Error as e_shutil:
                                    if "are the same file" in str(e_shutil).lower():
                                        status_message = f"Already in place (shutil err): {current_proposed_target_abs.relative_to(self.output_base_directory)}"
                                    else:
                                        status_message = f"Shutil Error moving: {e_shutil}"
                                except Exception as e_move:
                                    print(f"Error moving file {item.name} to {current_proposed_target_abs}: {e_move}")
                                    status_message = f"Error moving: {e_move}"

                        yield item, current_proposed_target_abs, status_message

                    except Exception as e_calc:
                        print(f"Error calculating/processing for {item.name}: {e_calc}")
                        current_proposed_target_abs_for_error = item
                        try:

                            current_proposed_target_abs_for_error = initial_proposed_target_for_status
                        except NameError:
                            pass
                        yield item, current_proposed_target_abs_for_error, f"Error processing: {e_calc}"
                # else: # File does not match filters (optional: yield a "Skipped: No filter match" status)
                #    yield item, item, "Skipped: No filter match"

    def _matches_filters(self, file_path: pathlib.Path) -> bool:
            if self.settings.name_filter_text:
                name_text = self.settings.name_filter_text
                file_name_for_compare = file_path.name
                name_text_for_compare = name_text

                match_mode = self.settings.name_filter_type
                if match_mode in ["Contains", "Starts with", "Ends with"]:
                    file_name_for_compare = file_path.name.lower()
                    name_text_for_compare = name_text.lower()

                if match_mode == "Contains" and name_text_for_compare not in file_name_for_compare: return False
                if match_mode == "Starts with" and not file_name_for_compare.startswith(name_text_for_compare): return False
                if match_mode == "Ends with" and not file_name_for_compare.endswith(name_text_for_compare): return False
                if match_mode == "Exact match" and file_path.name != name_text: return False # Case sensitive exact
                if match_mode == "Regex":
                    try:
                        if not re.search(name_text, file_path.name): return False
                    except re.error as e:
                        print(f"Warning: Invalid regex '{name_text}': {e}") # Good to have a warning
                        return False # Treat invalid regex as no match for this file

            # Type Filter
            if self.settings.type_filter_text:
                allowed_types_input = [t.strip().lower() for t in self.settings.type_filter_text.split(',') if t.strip()]
                file_ext_lower = file_path.suffix.lower() # e.g., ".txt"

                # Also get MIME type for more robust checking
                mime_type_guess, _ = mimetypes.guess_type(file_path)
                mime_type_lower = mime_type_guess.lower() if mime_type_guess else ""

                match_found = False
                for t_input in allowed_types_input:
                    if not t_input: continue # Skip empty strings from multiple commas

                    # Check against extension (e.g. ".jpg" or "jpg")
                    if (t_input.startswith('.') and file_ext_lower == t_input) or \
                       (not t_input.startswith('.') and file_ext_lower.lstrip('.') == t_input):
                        match_found = True
                        break
                    # Check against MIME type (e.g. "image/jpeg")
                    if mime_type_lower and t_input in mime_type_lower: # "jpeg" in "image/jpeg" or "image/jpeg" in "image/jpeg"
                        match_found = True
                        break
                if not match_found:
                    return False

            # Date Filters
            # Using st_mtime (modification time) for consistency.
            # st_ctime is creation on Windows, metadata change on Unix/Linux
            try:
                stat_info = file_path.stat()
                file_mod_date = datetime.datetime.fromtimestamp(stat_info.st_mtime).date()

                if self.settings.created_after_date: # This is semantically "Modified After" due to using st_mtime
                                                     # If true creation date is needed, it's more complex and OS-specific
                    if file_mod_date < self.settings.created_after_date:
                        return False

                if self.settings.modified_before_date:
                    if file_mod_date >= self.settings.modified_before_date:
                        # If modified_before_date is 2023-01-15, we want files *strictly before* this date.
                        # So, if file_mod_date is 2023-01-15 or later, it does NOT match.
                        return False
            except OSError: return False # File might have vanished or permissions issue

            # Size Filters (comparing KB with KB)
            # self.settings.size_max_kb == -1 means no upper limit
            if self.settings.size_min_kb > 0 or self.settings.size_max_kb != -1:
                try:
                    size_bytes = file_path.stat().st_size # Re-fetch stat_info if not already fetched, or pass it
                    size_kb = size_bytes / 1024.0

                    if self.settings.size_min_kb > 0 and size_kb < self.settings.size_min_kb:
                        return False
                    # Ensure size_max_kb is only checked if it's not the "no limit" sentinel
                    if self.settings.size_max_kb != -1 and size_kb > self.settings.size_max_kb:
                        return False
                except OSError: return False # File might have vanished

            return True

    def _get_detected_file_type_category(self, source_file: pathlib.Path) -> str:
        mime_type_guess, _ = mimetypes.guess_type(str(source_file))
        if mime_type_guess:
            mime_main = mime_type_guess.split('/')[0].lower()
            if mime_main == "image": return "Images"
            if mime_main == "text": return "TextFiles" # Or "Documents" if preferred for .txt, .md
            if mime_main == "application":
                if "pdf" in mime_type_guess: return "Documents"
                if "zip" in mime_type_guess or "tar" in mime_type_guess or "rar" in mime_type_guess or "7z" in mime_type_guess: return "Archives"
                if "msword" in mime_type_guess or "officedocument" in mime_type_guess: return "Documents" # .doc, .docx etc.
                # Add more application types if needed
                return "Applications" # Generic for other apps
            if mime_main == "video": return "Videos"
            if mime_main == "audio": return "Audio"
        # Fallback for unknown or simple extension check
        ext = source_file.suffix.lower()
        if ext in ['.doc', '.docx', '.odt', '.rtf', '.txt', '.md', '.pdf']: return "Documents"
        if ext in ['.xls', '.xlsx', '.ods', '.csv']: return "Spreadsheets"
        if ext in ['.ppt', '.pptx', '.odp']: return "Presentations"

        return "Other"


    def _calculate_target_path_relative(self, source_file: pathlib.Path) -> pathlib.Path:
        template = self.settings.structure_template

        stat_info = source_file.stat()
        # Use st_mtime consistently for template dates as it's used in filters
        time_for_template = datetime.datetime.fromtimestamp(stat_info.st_mtime)

        year = str(time_for_template.year)
        month = f"{time_for_template.month:02d}"
        day = f"{time_for_template.day:02d}"
        filename_stem = source_file.stem
        extension = source_file.suffix.lstrip('.')

        path_str = template
        path_str = path_str.replace("[YYYY]", year)
        path_str = path_str.replace("[MM]", month)
        path_str = path_str.replace("[DD]", day)
        path_str = path_str.replace("[Filename]", filename_stem)
        path_str = path_str.replace("[Ext]", extension)

        # Handle [DetectedFileType]
        if "[DetectedFileType]" in path_str:
            detected_type_category = self._get_detected_file_type_category(source_file)
            path_str = path_str.replace("[DetectedFileType]", detected_type_category)

        # Regex Group replacement
        # ... (this part remains the same) ...
        if "[RegexGroup" in path_str and self.settings.name_filter_type == "Regex" and self.settings.name_filter_text:
            try:
                match = re.search(self.settings.name_filter_text, source_file.name)
                if match:
                    groups = match.groups() # Returns a tuple of all subgroups
                    for i, group_val in enumerate(groups):
                        if group_val is not None: # Only replace if group captured something
                             path_str = path_str.replace(f"[RegexGroup{i+1}]", group_val)
                        else: # If group didn't capture, remove the placeholder or replace with empty
                             path_str = path_str.replace(f"[RegexGroup{i+1}]", "")
            except re.error: pass


        return pathlib.Path(path_str)
