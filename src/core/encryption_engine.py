# src/encryption_engine.py
import os
import pathlib
import json
import base64
import secrets
from typing import Optional, List, Dict, Any
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
import keyring
import getpass


class EncryptionEngine:
    """Handles file encryption and decryption operations with AES-256 encryption."""
    
    # Encryption metadata file extension
    METADATA_EXTENSION = '.encrypted'
    
    # Key derivation parameters
    SALT_SIZE = 32  # 256-bit salt
    KEY_SIZE = 32   # 256-bit key for AES-256
    ITERATIONS = 100000  # PBKDF2 iterations
    
    # Service name for keyring storage
    KEYRING_SERVICE = "ChronoFiler"
    
    def __init__(self):
        self.backend = default_backend()
    
    def encrypt_file(self, 
                    source_path: pathlib.Path, 
                    password: str,
                    output_path: Optional[pathlib.Path] = None,
                    store_password: bool = False) -> pathlib.Path:
        """
        Encrypt a single file with AES-256 encryption.
        
        Args:
            source_path: Path to the file to encrypt
            password: Encryption password
            output_path: Output path (optional, defaults to source_path.encrypted)
            store_password: Whether to store password in system keyring
            
        Returns:
            Path to the encrypted file
        """
        if not source_path.exists():
            raise FileNotFoundError(f"Source file not found: {source_path}")
        
        if output_path is None:
            output_path = source_path.with_suffix(source_path.suffix + '.encrypted')
        
        # Generate salt and derive key
        salt = secrets.token_bytes(self.SALT_SIZE)
        key = self._derive_key(password, salt)
        
        # Generate IV
        iv = secrets.token_bytes(16)  # 128-bit IV for AES
        
        # Read source file
        with open(str(source_path), 'rb') as f:
            plaintext = f.read()
        
        # Encrypt data
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=self.backend)
        encryptor = cipher.encryptor()
        
        # Pad data to block size
        padded_data = self._pad_data(plaintext)
        ciphertext = encryptor.update(padded_data) + encryptor.finalize()
        
        # Create metadata
        metadata = {
            'original_filename': source_path.name,
            'original_size': len(plaintext),
            'encrypted_size': len(ciphertext),
            'salt': base64.b64encode(salt).decode('utf-8'),
            'iv': base64.b64encode(iv).decode('utf-8'),
            'algorithm': 'AES-256-CBC',
            'key_derivation': 'PBKDF2-SHA256',
            'iterations': self.ITERATIONS
        }
        
        # Write encrypted file with metadata
        with open(output_path, 'wb') as f:
            # Write metadata as JSON header
            metadata_json = json.dumps(metadata)
            metadata_bytes = metadata_json.encode('utf-8')
            metadata_length = len(metadata_bytes)
            
            # Write metadata length (4 bytes) + metadata + ciphertext
            f.write(metadata_length.to_bytes(4, byteorder='big'))
            f.write(metadata_bytes)
            f.write(ciphertext)
        
        # Store password in keyring if requested
        if store_password:
            self._store_password(source_path.name, password)
        
        return output_path
    
    def decrypt_file(self, 
                    encrypted_path: pathlib.Path, 
                    password: str,
                    output_path: Optional[pathlib.Path] = None) -> pathlib.Path:
        """
        Decrypt an encrypted file.
        
        Args:
            encrypted_path: Path to the encrypted file
            password: Decryption password
            output_path: Output path (optional, defaults to original filename)
            
        Returns:
            Path to the decrypted file
        """
        if not encrypted_path.exists():
            raise FileNotFoundError(f"Encrypted file not found: {encrypted_path}")
        
        # Read encrypted file
        with open(str(encrypted_path), 'rb') as f:
            # Read metadata length
            metadata_length_bytes = f.read(4)
            if len(metadata_length_bytes) != 4:
                raise ValueError("Invalid encrypted file format")
            
            metadata_length = int.from_bytes(metadata_length_bytes, byteorder='big')
            metadata_bytes = f.read(metadata_length)
            ciphertext = f.read()
        
        # Parse metadata
        try:
            metadata = json.loads(metadata_bytes.decode('utf-8'))
        except (json.JSONDecodeError, UnicodeDecodeError):
            raise ValueError("Invalid metadata in encrypted file")
        
        # Validate metadata
        if metadata.get('algorithm') != 'AES-256-CBC':
            raise ValueError("Unsupported encryption algorithm")
        
        # Extract salt and IV
        salt = base64.b64decode(metadata['salt'])
        iv = base64.b64decode(metadata['iv'])
        
        # Derive key
        key = self._derive_key(password, salt)
        
        # Decrypt data
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=self.backend)
        decryptor = cipher.decryptor()
        
        try:
            padded_plaintext = decryptor.update(ciphertext) + decryptor.finalize()
            plaintext = self._unpad_data(padded_plaintext)
        except Exception as e:
            raise ValueError("Decryption failed - invalid password or corrupted file") from e
        
        # Determine output path
        if output_path is None:
            # Use the same directory as the encrypted file
            output_path = encrypted_path.parent / metadata['original_filename']
        
        # Ensure we don't overwrite existing files
        if output_path.exists():
            # Add a counter to make filename unique
            counter = 1
            base_name = output_path.stem
            extension = output_path.suffix
            while output_path.exists():
                output_path = output_path.parent / f"{base_name}_{counter}{extension}"
                counter += 1
        
        # Write decrypted file
        with open(output_path, 'wb') as f:
            f.write(plaintext)
        
        return output_path
    
    def encrypt_archive(self,
                       archive_path: pathlib.Path,
                       password: str,
                       store_password: bool = False) -> pathlib.Path:
        """
        Encrypt an existing archive file.
        
        Args:
            archive_path: Path to the archive to encrypt
            password: Encryption password
            store_password: Whether to store password in system keyring
            
        Returns:
            Path to the encrypted archive
        """
        return self.encrypt_file(archive_path, password, store_password=store_password)
    
    def create_encrypted_archive(self,
                               source_paths: List[pathlib.Path],
                               archive_path: pathlib.Path,
                               password: str,
                               format_type: str = 'zip',
                               compression_level: str = 'normal',
                               store_password: bool = False) -> pathlib.Path:
        """
        Create an encrypted archive directly.
        
        Args:
            source_paths: List of files/directories to archive
            archive_path: Path for the output archive
            password: Encryption password
            format_type: Archive format
            compression_level: Compression level
            store_password: Whether to store password
            
        Returns:
            Path to the encrypted archive
        """
        from compression_engine import CompressionEngine
        
        # Create temporary archive
        compression_engine = CompressionEngine()
        
        # Let compression engine handle the extension
        temp_archive = archive_path.with_suffix('')  # Remove any extension
        
        try:
            # Create archive - compression engine will add appropriate extension
            created_files = compression_engine.create_archive(
                source_paths, temp_archive, format_type, compression_level
            )
            
            if created_files:
                # Use the actual created archive path
                actual_archive = created_files[0]
                
                # Encrypt the archive
                encrypted_path = self.encrypt_file(
                    actual_archive, password, archive_path.with_suffix('.encrypted'), store_password
                )
                return encrypted_path
            else:
                raise RuntimeError("Failed to create archive")
                
        finally:
            # Clean up temporary file
            temp_archive_with_ext = temp_archive.with_suffix('.zip')  # Default to .zip
            if temp_archive_with_ext.exists():
                temp_archive_with_ext.unlink()
            
            # Also check for other possible extensions
            for ext in ['.zip', '.tar.gz', '.tar.bz2', '.tar.xz']:
                temp_file = temp_archive.with_suffix(ext)
                if temp_file.exists():
                    temp_file.unlink()
    
    def verify_password(self, encrypted_path: pathlib.Path, password: str) -> bool:
        """
        Verify if a password is correct for an encrypted file.
        
        Args:
            encrypted_path: Path to the encrypted file
            password: Password to verify
            
        Returns:
            True if password is correct, False otherwise
        """
        try:
            # Try to read metadata
            with open(str(encrypted_path), 'rb') as f:
                metadata_length_bytes = f.read(4)
                if len(metadata_length_bytes) != 4:
                    return False
                
                metadata_length = int.from_bytes(metadata_length_bytes, byteorder='big')
                metadata_bytes = f.read(metadata_length)
                metadata = json.loads(metadata_bytes.decode('utf-8'))
                
                # Extract salt and derive key
                salt = base64.b64decode(metadata['salt'])
                key = self._derive_key(password, salt)
                
                # Try to decrypt a small portion to verify password
                iv = base64.b64decode(metadata['iv'])
                cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=self.backend)
                decryptor = cipher.decryptor()
                
                # Read a small portion of ciphertext
                f.seek(4 + metadata_length)
                test_data = f.read(32)  # Read first 32 bytes
                
                if len(test_data) > 0:
                    decryptor.update(test_data)
                
                return True
                
        except Exception:
            return False
    
    def verify_encrypted_file(self, encrypted_path: pathlib.Path, password: str) -> bool:
        """
        Verify the integrity of an encrypted file.
        
        Args:
            encrypted_path: Path to the encrypted file
            password: Password to verify
            
        Returns:
            True if file is valid and password is correct, False otherwise
        """
        try:
            # Read encrypted file
            with open(str(encrypted_path), 'rb') as f:
                # Read metadata length
                metadata_length_bytes = f.read(4)
                if len(metadata_length_bytes) != 4:
                    return False
                
                metadata_length = int.from_bytes(metadata_length_bytes, byteorder='big')
                metadata_bytes = f.read(metadata_length)
                ciphertext = f.read()
            
            # Parse metadata
            try:
                metadata = json.loads(metadata_bytes.decode('utf-8'))
            except (json.JSONDecodeError, UnicodeDecodeError):
                return False
            
            # Validate metadata
            if metadata.get('algorithm') != 'AES-256-CBC':
                return False
            
            # Extract salt and IV
            salt = base64.b64decode(metadata['salt'])
            iv = base64.b64decode(metadata['iv'])
            
            # Derive key
            key = self._derive_key(password, salt)
            
            # Decrypt data
            cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=self.backend)
            decryptor = cipher.decryptor()
            
            padded_plaintext = decryptor.update(ciphertext) + decryptor.finalize()
            plaintext = self._unpad_data(padded_plaintext)
            
            # Verify the decrypted data matches expected size
            expected_size = metadata.get('original_size', 0)
            if len(plaintext) != expected_size:
                return False
            
            return True
            
        except Exception:
            return False
    
    def get_encryption_info(self, encrypted_path: pathlib.Path) -> Dict[str, Any]:
        """
        Get information about an encrypted file.
        
        Args:
            encrypted_path: Path to the encrypted file
            
        Returns:
            Dictionary with encryption information
        """
        if not encrypted_path.exists():
            raise FileNotFoundError(f"Encrypted file not found: {encrypted_path}")
        
        try:
            with open(str(encrypted_path), 'rb') as f:
                metadata_length_bytes = f.read(4)
                metadata_length = int.from_bytes(metadata_length_bytes, byteorder='big')
                metadata_bytes = f.read(metadata_length)
                metadata = json.loads(metadata_bytes.decode('utf-8'))
                
                return {
                    'original_filename': metadata['original_filename'],
                    'original_size': metadata['original_size'],
                    'encrypted_size': metadata['encrypted_size'],
                    'algorithm': metadata['algorithm'],
                    'key_derivation': metadata['key_derivation'],
                    'iterations': metadata['iterations'],
                    'compression_ratio': (1 - metadata['encrypted_size'] / metadata['original_size']) * 100
                }
        except Exception as e:
            raise ValueError(f"Invalid encrypted file: {e}")

    def is_encrypted_file(self, file_path: pathlib.Path) -> bool:
        """
        Check if a file appears to be encrypted based on extension and signature.
        
        Args:
            file_path: Path to the file to check
            
        Returns:
            True if the file appears to be encrypted, False otherwise
        """
        if not file_path.exists() or not file_path.is_file():
            return False
        
        # Check extension
        if file_path.suffix.lower() == '.encrypted':
            return True
        
        # Check file signature
        try:
            with open(str(file_path), 'rb') as f:
                # Read first 4 bytes to check for metadata length
                metadata_length_bytes = f.read(4)
                if len(metadata_length_bytes) != 4:
                    return False
                
                metadata_length = int.from_bytes(metadata_length_bytes, byteorder='big')
                
                # Check if metadata length is reasonable (not too large)
                if metadata_length > 1024 * 1024:  # 1MB max metadata
                    return False
                
                # Read metadata
                metadata_bytes = f.read(metadata_length)
                if len(metadata_bytes) != metadata_length:
                    return False
                
                # Try to parse as JSON
                metadata = json.loads(metadata_bytes.decode('utf-8'))
                
                # Check for required encryption metadata fields
                required_fields = ['algorithm', 'salt', 'iv', 'original_filename']
                return all(field in metadata for field in required_fields)
                
        except (json.JSONDecodeError, UnicodeDecodeError, OSError):
            return False
    
    def _derive_key(self, password: str, salt: bytes) -> bytes:
        """Derive encryption key from password using PBKDF2."""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=self.KEY_SIZE,
            salt=salt,
            iterations=self.ITERATIONS,
            backend=self.backend
        )
        return kdf.derive(password.encode('utf-8'))
    
    def _pad_data(self, data: bytes) -> bytes:
        """Apply PKCS7 padding to data."""
        padding_length = 16 - (len(data) % 16)
        padding = bytes([padding_length] * padding_length)
        return data + padding
    
    def _unpad_data(self, data: bytes) -> bytes:
        """Remove PKCS7 padding from data."""
        if not data:
            return data
        padding_length = data[-1]
        if padding_length > 16:
            raise ValueError("Invalid padding")
        return data[:-padding_length]
    
    def _store_password(self, identifier: str, password: str):
        """Store password in system keyring."""
        try:
            keyring.set_password(self.KEYRING_SERVICE, identifier, password)
        except Exception as e:
            print(f"Warning: Could not store password in keyring: {e}")
    
    def _get_password(self, identifier: str) -> Optional[str]:
        """Retrieve password from system keyring."""
        try:
            return keyring.get_password(self.KEYRING_SERVICE, identifier)
        except Exception:
            return None
    
    def _delete_password(self, identifier: str):
        """Delete password from system keyring."""
        try:
            keyring.delete_password(self.KEYRING_SERVICE, identifier)
        except Exception:
            pass
    
    def batch_encrypt_files(self,
                          source_paths: List[pathlib.Path],
                          password: str,
                          output_dir: pathlib.Path,
                          store_password: bool = False) -> List[pathlib.Path]:
        """
        Encrypt multiple files in batch.
        
        Args:
            source_paths: List of files to encrypt
            password: Encryption password
            output_dir: Directory for encrypted files
            store_password: Whether to store passwords
            
        Returns:
            List of created encrypted file paths
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        encrypted_files = []
        
        for source_path in source_paths:
            if source_path.is_file():
                output_path = output_dir / f"{source_path.name}.encrypted"
                encrypted_path = self.encrypt_file(
                    source_path, password, output_path, store_password
                )
                encrypted_files.append(encrypted_path)
        
        return encrypted_files