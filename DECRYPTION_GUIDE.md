# 🔓 How to Decrypt Archives in ChronoFiler

This guide explains how users can decrypt archives that have been encrypted using ChronoFiler's encryption feature.

## 📋 Overview

When you create an encrypted archive in ChronoFiler, the process involves:
1. **Compression**: Files are first compressed into an archive (ZIP, TAR.GZ, etc.)
2. **Encryption**: The archive is then encrypted using AES-256 encryption
3. **Result**: You get a `.encrypted` file that contains your compressed and encrypted data

## 🔍 How to Identify Encrypted Files

Encrypted files have these characteristics:
- **File extension**: `.encrypted` (e.g., `my_archive.zip.encrypted`)
- **File type**: Cannot be opened by standard archive tools directly
- **Size**: Usually smaller than the original due to compression + encryption overhead

## 🔓 Decryption Process

### Method 1: Using the File Browser (Recommended)

1. **Navigate** to the folder containing your `.encrypted` file
2. **Right-click** on the encrypted file
3. **Select "Decrypt"** from the context menu
4. **Enter the password** when prompted
5. **Choose output location** (optional - defaults to original filename)
6. **Click "Decrypt"** to proceed

### Method 2: Using the Command Line

```bash
# Navigate to your project directory
cd /path/to/chrono-filer

# Run the decryption script
python -c "
from src.encryption_engine import EncryptionEngine
import pathlib

engine = EncryptionEngine()
encrypted_file = pathlib.Path('your_file.zip.encrypted')
password = 'your_password_here'

decrypted_file = engine.decrypt_file(encrypted_file, password)
print(f'Decrypted to: {decrypted_file}')
"
```

## 📦 After Decryption

Once decrypted, you'll have:
- **Original archive file** (e.g., `my_archive.zip`)
- **Extractable content** that can be opened with standard archive tools

### Extracting the Archive

After decryption, you can extract the archive using:
- **ChronoFiler**: Right-click → "Extract Archive"
- **System tools**: Double-click or use your OS's archive manager
- **Command line**: `unzip my_archive.zip` or `tar -xzf my_archive.tar.gz`

## 🛠️ Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| **"Invalid password" error** | Double-check the password and try again |
| **"Invalid encrypted file" error** | The file may be corrupted or not a valid encrypted file |
| **Decrypted file won't extract** | Ensure you have the right archive tool for the format |
| **File extension missing** | The decrypted file should have the correct extension (e.g., `.zip`) |

### Password Recovery

- **No password recovery**: Encrypted files cannot be recovered without the correct password
- **Keyring storage**: If you chose to store the password in your system keyring, it may be retrievable
- **Password hints**: Consider using password hints or secure password managers

## 🔄 Complete Workflow Example

### Creating an Encrypted Archive
1. Select files in ChronoFiler
2. Right-click → "Create Archive"
3. Choose archive format and compression level
4. Enable encryption and set a strong password
5. Save as `my_backup.zip.encrypted`

### Decrypting and Extracting
1. Find `my_backup.zip.encrypted` in ChronoFiler
2. Right-click → "Decrypt"
3. Enter the same password used for encryption
4. Get `my_backup.zip` (decrypted archive)
5. Right-click → "Extract Archive" or use system tools

## 🔐 Security Notes

- **Password strength**: Use strong, unique passwords for encryption
- **Password storage**: Consider using a password manager
- **File backup**: Keep backups of important encrypted files
- **Sharing**: Never share encrypted files with the password in the same communication

## 📱 Integration Features

ChronoFiler provides seamless integration:
- **Context menus**: Right-click any file for encryption/decryption options
- **Batch operations**: Encrypt/decrypt multiple files at once
- **Progress indicators**: Visual feedback during operations
- **Error handling**: Clear error messages for troubleshooting