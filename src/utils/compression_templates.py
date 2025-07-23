# src/compression_templates.py
import datetime
import pathlib
import re
from typing import Dict, Any


class ArchiveNamingTemplates:
    """Handles archive naming templates with variables."""
    
    DEFAULT_TEMPLATES = {
        'simple': '{name}',
        'timestamp': '{name}_{timestamp}',
        'datetime': '{name}_{datetime}',
        'source_based': '{source_name}_{timestamp}',
        'size_based': '{name}_{total_size_human}_{timestamp}',
        'count_based': '{name}_{file_count}_files_{timestamp}',
    }
    
    @classmethod
    def get_available_templates(cls) -> Dict[str, str]:
        """Get available naming templates."""
        return cls.DEFAULT_TEMPLATES.copy()
    
    @classmethod
    def generate_name(cls, template: str, variables: Dict[str, Any]) -> str:
        """
        Generate archive name from template and variables.
        
        Args:
            template: Template string with placeholders
            variables: Dictionary of variable values
            
        Returns:
            Generated archive name
        """
        try:
            # Ensure all required variables are present
            default_vars = {
                'name': 'archive',
                'timestamp': datetime.datetime.now().strftime('%Y%m%d_%H%M%S'),
                'datetime': datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S'),
                'source_name': 'files',
                'total_size': '0',
                'total_size_human': '0B',
                'file_count': '0',
            }
            
            # Merge provided variables with defaults
            all_vars = {**default_vars, **variables}
            
            # Clean filename for filesystem compatibility
            name = template.format(**all_vars)
            name = cls._sanitize_filename(name)
            
            return name
        
        except KeyError as e:
            # Fallback to simple name if template is invalid
            return f"archive_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    @classmethod
    def _sanitize_filename(cls, filename: str) -> str:
        """Sanitize filename for filesystem compatibility."""
        # Remove or replace invalid characters
        invalid_chars = r'[<>:\"/\\|?*]'
        filename = re.sub(invalid_chars, '_', filename)
        
        # Remove leading/trailing spaces and dots
        filename = filename.strip('. ')
        
        # Ensure it's not empty
        if not filename:
            filename = "archive"
        
        # Limit length
        if len(filename) > 200:
            filename = filename[:200]
        
        return filename
    
    @classmethod
    def get_template_variables(cls) -> Dict[str, str]:
        """Get description of available template variables."""
        return {
            '{name}': 'Base archive name',
            '{timestamp}': 'Current timestamp (YYYYMMDD_HHMMSS)',
            '{datetime}': 'Current date and time (YYYY-MM-DD_HH-MM-SS)',
            '{source_name}': 'Name of source directory or first file',
            '{total_size}': 'Total size in bytes',
            '{total_size_human}': 'Total size in human-readable format',
            '{file_count}': 'Number of files being archived',
        }
    
    @classmethod
    def calculate_variables(cls, source_paths: list, base_name: str = "archive") -> Dict[str, Any]:
        """Calculate template variables from source paths."""
        variables = {
            'name': base_name,
            'timestamp': datetime.datetime.now().strftime('%Y%m%d_%H%M%S'),
            'datetime': datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S'),
        }
        
        if source_paths:
            # Get source name from first path
            first_path = pathlib.Path(source_paths[0])
            if first_path.is_file():
                variables['source_name'] = first_path.stem
            else:
                variables['source_name'] = first_path.name
            
            # Calculate total size and file count
            total_size = 0
            file_count = 0
            
            for path in source_paths:
                if path.is_file():
                    total_size += path.stat().st_size
                    file_count += 1
                elif path.is_dir():
                    for root, dirs, files in path.rglob('*'):
                        for file in files:
                            file_path = pathlib.Path(root) / file
                            if file_path.is_file():
                                total_size += file_path.stat().st_size
                                file_count += 1
            
            variables['total_size'] = str(total_size)
            variables['total_size_human'] = cls._format_size(total_size)
            variables['file_count'] = str(file_count)
        
        return variables
    
    @classmethod
    def _format_size(cls, size_bytes: int) -> str:
        """Format file size in human readable format."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.0f}{unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.0f}PB"
    
    @classmethod
    def get_template_examples(cls) -> Dict[str, Dict[str, str]]:
        """Get examples of template usage."""
        example_vars = {
            'name': 'backup',
            'timestamp': '20231225_143022',
            'datetime': '2023-12-25_14-30-22',
            'source_name': 'documents',
            'total_size': '10485760',
            'total_size_human': '10MB',
            'file_count': '25',
        }
        
        examples = {}
        for template_name, template in cls.DEFAULT_TEMPLATES.items():
            try:
                examples[template_name] = {
                    'template': template,
                    'result': cls.generate_name(template, example_vars),
                    'description': cls._get_template_description(template_name)
                }
            except Exception:
                examples[template_name] = {
                    'template': template,
                    'result': 'backup_20231225_143022',
                    'description': 'Simple backup name'
                }
        
        return examples
    
    @classmethod
    def _get_template_description(cls, template_name: str) -> str:
        """Get description for a template."""
        descriptions = {
            'simple': 'Basic archive name',
            'timestamp': 'Name with timestamp',
            'datetime': 'Name with detailed date/time',
            'source_based': 'Name based on source directory',
            'size_based': 'Name including total size',
            'count_based': 'Name including file count',
        }
        return descriptions.get(template_name, 'Custom template')