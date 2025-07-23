# src/compression_engine.py
import os
import pathlib
import tarfile
import zipfile
from typing import List, Optional, Tuple
import tempfile
import shutil


class CompressionEngine:
    """Handles file compression and archiving operations."""
    
    SUPPORTED_FORMATS = {
        'zip': {'extension': '.zip', 'description': 'ZIP Archive'},
        'tar.gz': {'extension': '.tar.gz', 'description': 'Gzip Compressed Tar Archive'},
        'tar.bz2': {'extension': '.tar.bz2', 'description': 'Bzip2 Compressed Tar Archive'},
        'tar.xz': {'extension': '.tar.xz', 'description': 'XZ Compressed Tar Archive'},
    }
    
    COMPRESSION_LEVELS = {
        'fast': {'zip': zipfile.ZIP_DEFLATED, 'tar': 'gz', 'level': 1},
        'normal': {'zip': zipfile.ZIP_DEFLATED, 'tar': 'gz', 'level': 6},
        'maximum': {'zip': zipfile.ZIP_DEFLATED, 'tar': 'gz', 'level': 9},
    }
    
    def __init__(self):
        self.temp_dir = None
    
    def create_archive(self,
                       source_paths: List[pathlib.Path],
                       archive_path: pathlib.Path,
                       format_type: str = 'zip',
                       compression_level: str = 'normal',
                       split_size: Optional[int] = None,
                       progress_callback=None) -> List[pathlib.Path]:
        """
        Create an archive from source paths.
        
        Args:
            source_paths: List of files/directories to archive
            archive_path: Path for the output archive
            format_type: Archive format ('zip', 'tar.gz', 'tar.bz2', 'tar.xz')
            compression_level: Compression level ('fast', 'normal', 'maximum')
            split_size: Maximum size per volume in bytes (optional)
            progress_callback: Optional callback function for progress updates
            
        Returns:
            List of created archive file paths
        """
        if format_type not in self.SUPPORTED_FORMATS:
            raise ValueError(f"Unsupported format: {format_type}")
        
        if split_size and split_size > 0:
            return self._create_split_archive(source_paths, archive_path, format_type,
                                            compression_level, split_size, progress_callback)
        else:
            return [self._create_single_archive(source_paths, archive_path, format_type,
                                              compression_level, progress_callback)]
    
    def _create_single_archive(self,
                             source_paths: List[pathlib.Path],
                             archive_path: pathlib.Path,
                             format_type: str,
                             compression_level: str,
                             progress_callback=None) -> pathlib.Path:
        """Create a single archive file."""
        expected_suffix = self.SUPPORTED_FORMATS[format_type]['extension']
        if not str(archive_path).endswith(expected_suffix):
            archive_path = archive_path.with_suffix(expected_suffix)
        
        if format_type == 'zip':
            return self._create_zip_archive(source_paths, archive_path, compression_level, progress_callback)
        else:
            return self._create_tar_archive(source_paths, archive_path, format_type, compression_level, progress_callback)
    
    def _create_zip_archive(self,
                          source_paths: List[pathlib.Path],
                          archive_path: pathlib.Path,
                          compression_level: str,
                          progress_callback=None) -> pathlib.Path:
        """Create a ZIP archive."""
        compression_info = self.COMPRESSION_LEVELS[compression_level]
        
        # Count total files for progress
        total_files = 0
        for source_path in source_paths:
            if source_path.is_file():
                total_files += 1
            elif source_path.is_dir():
                for root, dirs, files in os.walk(source_path):
                    total_files += len(files)
        
        processed_files = 0
        
        with zipfile.ZipFile(archive_path, 'w', compression_info['zip'],
                           compresslevel=compression_info['level']) as zipf:
            for source_path in source_paths:
                if source_path.is_file():
                    arcname = source_path.name
                    zipf.write(str(source_path), arcname)
                    processed_files += 1
                    if progress_callback:
                        progress_callback(processed_files, total_files)
                elif source_path.is_dir():
                    for root, dirs, files in os.walk(source_path):
                        for file in files:
                            file_path = pathlib.Path(root) / file
                            arcname = file_path.relative_to(source_path.parent)
                            zipf.write(str(file_path), str(arcname))
                            processed_files += 1
                            if progress_callback:
                                progress_callback(processed_files, total_files)
        
        return archive_path
    
    def _create_tar_archive(self,
                          source_paths: List[pathlib.Path],
                          archive_path: pathlib.Path,
                          format_type: str,
                          compression_level: str,
                          progress_callback=None) -> pathlib.Path:
        """Create a TAR archive with compression."""
        compression_info = self.COMPRESSION_LEVELS[compression_level]
        tar_mode = f'w:{format_type.split(".")[-1]}'
        
        # Count total files for progress
        total_files = 0
        for source_path in source_paths:
            if source_path.is_file():
                total_files += 1
            elif source_path.is_dir():
                for root, dirs, files in os.walk(source_path):
                    total_files += len(files) + 1  # +1 for directory itself
        
        processed_files = 0
        
        with tarfile.open(archive_path, tar_mode) as tarf:
            for source_path in source_paths:
                if source_path.is_file():
                    arcname = source_path.name
                    tarf.add(source_path, arcname=arcname)
                    processed_files += 1
                    if progress_callback:
                        progress_callback(processed_files, total_files)
                elif source_path.is_dir():
                    tarf.add(str(source_path), arcname=source_path.name)
                    processed_files += 1
                    if progress_callback:
                        progress_callback(processed_files, total_files)
                    
                    # Add individual files for more granular progress
                    for root, dirs, files in os.walk(source_path):
                        for file in files:
                            file_path = pathlib.Path(root) / file
                            arcname = file_path.relative_to(source_path.parent)
                            tarf.add(str(file_path), arcname=str(arcname))
                            processed_files += 1
                            if progress_callback:
                                progress_callback(processed_files, total_files)
        
        return archive_path
    
    def _create_split_archive(self,
                            source_paths: List[pathlib.Path],
                            archive_path: pathlib.Path,
                            format_type: str,
                            compression_level: str,
                            split_size: int,
                            progress_callback=None) -> List[pathlib.Path]:
        """Create split archives for large files."""
        # First create a temporary archive
        with tempfile.NamedTemporaryFile(suffix=self.SUPPORTED_FORMATS[format_type]['extension'],
                                       delete=False) as temp_file:
            temp_archive_path = pathlib.Path(temp_file.name)
        
        try:
            # Create full archive with progress
            self._create_single_archive(source_paths, temp_archive_path, format_type,
                                      compression_level, progress_callback)
            
            # Split into volumes
            if progress_callback:
                progress_callback(100, 100)  # Mark as complete before splitting
            
            return self._split_file(temp_archive_path, archive_path, split_size)
        finally:
            # Clean up temporary file
            if temp_archive_path.exists():
                temp_archive_path.unlink()
    
    def _split_file(self, source_file: pathlib.Path, 
                   base_path: pathlib.Path, 
                   split_size: int) -> List[pathlib.Path]:
        """Split a file into multiple volumes."""
        created_files = []
        
        with open(source_file, 'rb') as f:
            part_num = 1
            while True:
                chunk = f.read(split_size)
                if not chunk:
                    break
                
                part_path = base_path.with_suffix(f"{base_path.suffix}.part{part_num:03d}")
                with open(part_path, 'wb') as part_file:
                    part_file.write(chunk)
                
                created_files.append(part_path)
                part_num += 1
        
        return created_files
    
    def get_archive_info(self, archive_path: pathlib.Path) -> dict:
        """Get information about an archive."""
        info = {
            'format': None,
            'file_count': 0,
            'total_size': 0,
            'compression_ratio': 0.0
        }
        
        if archive_path.suffix == '.zip':
            try:
                with zipfile.ZipFile(archive_path, 'r') as zipf:
                    info['format'] = 'ZIP'
                    info['file_count'] = len(zipf.namelist())
                    info['total_size'] = sum(zinfo.file_size for zinfo in zipf.filelist)
                    compressed_size = sum(zinfo.compress_size for zinfo in zipf.filelist)
                    if info['total_size'] > 0:
                        info['compression_ratio'] = (1 - compressed_size / info['total_size']) * 100
            except zipfile.BadZipFile:
                pass
        
        elif archive_path.suffix in ['.gz', '.bz2', '.xz'] and '.tar' in str(archive_path):
            try:
                with tarfile.open(archive_path, 'r') as tarf:
                    info['format'] = 'TAR'
                    info['file_count'] = len(tarf.getmembers())
                    info['total_size'] = sum(member.size for member in tarf.getmembers())
                    # Note: TAR compression ratio calculation is more complex
            except tarfile.TarError:
                pass
        
        return info
    
    def extract_archive(self, archive_path: pathlib.Path, 
                       extract_to: pathlib.Path) -> List[pathlib.Path]:
        """Extract an archive to a directory."""
        extracted_files = []
        
        if archive_path.suffix == '.zip':
            with zipfile.ZipFile(archive_path, 'r') as zipf:
                zipf.extractall(extract_to)
                extracted_files = [extract_to / name for name in zipf.namelist()]
        
        elif archive_path.suffix in ['.gz', '.bz2', '.xz'] and '.tar' in str(archive_path):
            with tarfile.open(archive_path, 'r') as tarf:
                tarf.extractall(extract_to)
                extracted_files = [extract_to / member.name for member in tarf.getmembers()]
        
        return extracted_files