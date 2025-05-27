# src/engine.py
import pathlib
import datetime
import os
import re
import shutil # For actual file operations
from typing import List, Tuple, Optional

# Assuming OrganizationSettings is defined in widgets.py
# Adjust if you move OrganizationSettings to a models.py
try:
    from .widgets import OrganizationSettings
except ImportError: # Fallback for direct execution or different structure
    from widgets import OrganizationSettings


class OrganizationEngine:
    def __init__(self, settings: OrganizationSettings, source_directory: pathlib.Path):
        self.settings = settings
        self.source_directory = source_directory.resolve()

    def process_files(self) -> List[Tuple[pathlib.Path, pathlib.Path, str]]:
        proposed_actions: List[Tuple[pathlib.Path, pathlib.Path, str]] = []

        if not self.source_directory.is_dir():
            return [(self.source_directory, self.source_directory, f"Error: Source '{self.source_directory.name}' is not a directory")]

        for item in self.source_directory.iterdir():
            if item.is_file():
                if self._matches_filters(item):
                    try:
                        proposed_target_path_relative = self._calculate_target_path_relative(item)
                        # Output path is relative to source_directory for now
                        # A dedicated output base directory could be added later.
                        # For now, all structure is created *within* the source directory.
                        proposed_target_path_absolute = self.source_directory / proposed_target_path_relative

                        # Resolve to clean up ".." etc. and ensure it's absolute.
                        # This also helps in creating parent directories robustly.
                        proposed_target_path_absolute = proposed_target_path_absolute.resolve()

                        status = "To be moved"

                        if proposed_target_path_absolute.exists():
                            if proposed_target_path_absolute.is_dir():
                                status = f"Conflict: Target '{proposed_target_path_absolute.name}' is an existing directory. Skipped."
                            elif self.settings.conflict_resolution == "Skip":
                                status = f"Conflict: Target '{proposed_target_path_absolute.name}' exists. Skipped."
                            elif self.settings.conflict_resolution == "Overwrite":
                                status = f"Conflict: Target '{proposed_target_path_absolute.name}' exists. To be overwritten."
                            elif self.settings.conflict_resolution == "Rename with Suffix":
                                count = 1
                                original_stem = proposed_target_path_absolute.stem
                                original_suffix = proposed_target_path_absolute.suffix
                                temp_target_path = proposed_target_path_absolute
                                while temp_target_path.exists():
                                    temp_target_path = temp_target_path.with_name(f"{original_stem}_{count}{original_suffix}")
                                    count += 1
                                proposed_target_path_absolute = temp_target_path # Update the target path
                                status = f"Conflict: Target exists. To be renamed to '{proposed_target_path_absolute.name}'."

                        # Actual file operation if not dry run and not skipped/error
                        if not self.settings.dry_run and "Skipped" not in status and "Error" not in status:
                            try:
                                # Ensure target directory exists
                                proposed_target_path_absolute.parent.mkdir(parents=True, exist_ok=True)

                                # Perform the move
                                shutil.move(str(item), str(proposed_target_path_absolute))
                                status = f"Moved to '{proposed_target_path_absolute.relative_to(self.source_directory)}'" # Show relative path in status
                            except Exception as e_move:
                                print(f"Error moving file {item.name} to {proposed_target_path_absolute}: {e_move}")
                                status = f"Error moving: {e_move}" # Report error in status

                        proposed_actions.append((item, proposed_target_path_absolute, status))

                    except Exception as e_calc:
                        print(f"Error calculating target for {item.name}: {e_calc}")
                        proposed_actions.append((item, item, f"Error processing: {e_calc}"))

        return proposed_actions

    def _matches_filters(self, file_path: pathlib.Path) -> bool:
        # Name Filter
        if self.settings.name_filter_text:
            name_text = self.settings.name_filter_text
            # Case sensitivity for exact match and regex, case-insensitivity for others
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
                    print(f"Warning: Invalid regex '{name_text}': {e}")
                    return False

        # Type Filter
        if self.settings.type_filter_text:
            allowed_types_input = [t.strip().lower() for t in self.settings.type_filter_text.split(',') if t.strip()]
            file_ext_lower = file_path.suffix.lower() # e.g., ".txt"

            match_found = False
            for t_input in allowed_types_input:
                # Match if "txt" == "txt" (from ".txt") or ".txt" == ".txt"
                if (t_input.startswith('.') and file_ext_lower == t_input) or \
                   (not t_input.startswith('.') and file_ext_lower.lstrip('.') == t_input):
                    match_found = True
                    break
            if not match_found:
                 # TODO: Add mimetype check as an OR condition if desired
                return False

        # Date Filters
        try:
            stat_info = file_path.stat()
            # Using st_mtime (modification time) for date filters is generally more consistent
            # st_ctime is creation on Windows, metadata change on Unix/Linux
            file_date = datetime.datetime.fromtimestamp(stat_info.st_mtime).date()

            if self.settings.created_after_date and file_date < self.settings.created_after_date:
                return False
            if self.settings.modified_before_date and file_date >= self.settings.modified_before_date:
                # If modified_before_date is 2023-01-15, we want files *strictly before* this date.
                # So, if file_date is 2023-01-15 or later, it does NOT match.
                return False
        except OSError: return False # File might have vanished

        # Size Filters (comparing KB with KB)
        # self.settings.size_max_kb == -1 means no upper limit
        if self.settings.size_min_kb > 0 or self.settings.size_max_kb != -1:
            try:
                size_bytes = file_path.stat().st_size
                size_kb = size_bytes / 1024.0

                if self.settings.size_min_kb > 0 and size_kb < self.settings.size_min_kb:
                    return False
                if self.settings.size_max_kb != -1 and size_kb > self.settings.size_max_kb:
                    return False
            except OSError: return False # File might have vanished

        return True

    def _calculate_target_path_relative(self, source_file: pathlib.Path) -> pathlib.Path:
        """Calculates the target path relative to the base output directory."""
        template = self.settings.structure_template

        stat_info = source_file.stat()
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

        # Regex Group replacement
        if "[RegexGroup" in path_str and self.settings.name_filter_type == "Regex" and self.settings.name_filter_text:
            try:
                match = re.search(self.settings.name_filter_text, source_file.name)
                if match:
                    groups = match.groups() # Returns a tuple of all subgroups
                    for i, group_val in enumerate(groups):
                        path_str = path_str.replace(f"[RegexGroup{i+1}]", group_val if group_val is not None else "")
            except re.error: pass # Already handled in filter

        return pathlib.Path(path_str)
