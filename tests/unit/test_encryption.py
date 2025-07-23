#!/usr/bin/env python3
"""
Comprehensive test suite for encryption features in Chrono Filer.
Tests encryption engine, templates, key management, and integration.
"""

import os
import tempfile
import pathlib
import shutil
import unittest
from unittest.mock import patch, MagicMock
import json

# Import our encryption modules
from encryption_engine import EncryptionEngine
from encryption_templates import EncryptionTemplates, TemplateManager
from password_dialog import PasswordManager
from settings_manager import SettingsManager


class TestEncryptionEngine(unittest.TestCase):
    """Test the core encryption engine functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_file = pathlib.Path(self.temp_dir) / "test.txt"
        self.test_file.write_text("This is a test file for encryption testing")
        self.encryption_engine = EncryptionEngine()
        self.password = "test_password_123"
    
    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_encryption_decryption_round_trip(self):
        """Test basic encryption and decryption."""
        encrypted_file = self.test_file.with_suffix('.txt.enc')
        
        # Encrypt
        self.encryption_engine.encrypt_file(self.test_file, encrypted_file, self.password)
        self.assertTrue(encrypted_file.exists())
        
        # Decrypt
        decrypted_file = self.test_file.with_suffix('.txt.decrypted')
        self.encryption_engine.decrypt_file(encrypted_file, decrypted_file, self.password)
        
        # Verify content
        original_content = self.test_file.read_text()
        decrypted_content = decrypted_file.read_text()
        self.assertEqual(original_content, decrypted_content)
    
    def test_encryption_with_different_algorithms(self):
        """Test encryption with different algorithms."""
        algorithms = ["AES-256-CBC", "AES-256-GCM"]
        
        for algorithm in algorithms:
            with self.subTest(algorithm=algorithm):
                self.encryption_engine.algorithm = algorithm
                encrypted_file = self.test_file.with_suffix(f'.{algorithm.lower()}.enc')
                
                # Should not raise exception
                self.encryption_engine.encrypt_file(self.test_file, encrypted_file, self.password)
                self.assertTrue(encrypted_file.exists())
                
                # Clean up
                encrypted_file.unlink(missing_ok=True)
    
    def test_key_derivation_iterations(self):
        """Test different key derivation iteration counts."""
        iterations_list = [50000, 100000, 500000]
        
        for iterations in iterations_list:
            with self.subTest(iterations=iterations):
                self.encryption_engine.key_iterations = iterations
                encrypted_file = self.test_file.with_suffix(f'.iter{iterations}.enc')
                
                # Should not raise exception
                self.encryption_engine.encrypt_file(self.test_file, encrypted_file, self.password)
                self.assertTrue(encrypted_file.exists())
                
                # Clean up
                encrypted_file.unlink(missing_ok=True)
    
    def test_encryption_verification(self):
        """Test encryption verification functionality."""
        encrypted_file = self.test_file.with_suffix('.txt.enc')
        
        # Encrypt
        self.encryption_engine.encrypt_file(self.test_file, encrypted_file, self.password)
        
        # Verify
        is_valid = self.encryption_engine.verify_encrypted_file(encrypted_file, self.password)
        self.assertTrue(is_valid)
        
        # Test with wrong password
        is_valid_wrong = self.encryption_engine.verify_encrypted_file(encrypted_file, "wrong_password")
        self.assertFalse(is_valid_wrong)
    
    def test_encryption_metadata(self):
        """Test encryption metadata extraction."""
        encrypted_file = self.test_file.with_suffix('.txt.enc')
        
        # Encrypt
        self.encryption_engine.encrypt_file(self.test_file, encrypted_file, self.password)
        
        # Get metadata
        metadata = self.encryption_engine.get_encryption_metadata(encrypted_file)
        
        self.assertIsNotNone(metadata)
        self.assertIn('algorithm', metadata)
        self.assertIn('key_iterations', metadata)
        self.assertIn('salt_size', metadata)
        self.assertEqual(metadata['algorithm'], self.encryption_engine.algorithm)
    
    def test_large_file_encryption(self):
        """Test encryption of large files."""
        # Create a larger test file (1MB)
        large_file = pathlib.Path(self.temp_dir) / "large_test.txt"
        large_content = "A" * (1024 * 1024)  # 1MB of 'A's
        large_file.write_text(large_content)
        
        encrypted_file = large_file.with_suffix('.txt.enc')
        
        # Encrypt
        self.encryption_engine.encrypt_file(large_file, encrypted_file, self.password)
        self.assertTrue(encrypted_file.exists())
        
        # Decrypt
        decrypted_file = large_file.with_suffix('.txt.decrypted')
        self.encryption_engine.decrypt_file(encrypted_file, decrypted_file, self.password)
        
        # Verify content
        original_content = large_file.read_text()
        decrypted_content = decrypted_file.read_text()
        self.assertEqual(original_content, decrypted_content)
    
    def test_encryption_error_handling(self):
        """Test error handling for encryption operations."""
        non_existent_file = pathlib.Path(self.temp_dir) / "nonexistent.txt"
        output_file = pathlib.Path(self.temp_dir) / "output.enc"
        
        # Should raise exception for non-existent file
        with self.assertRaises(FileNotFoundError):
            self.encryption_engine.encrypt_file(non_existent_file, output_file, self.password)
    
    def test_password_strength_validation(self):
        """Test password strength validation."""
        weak_passwords = ["123", "abc", "password"]
        strong_passwords = ["ComplexP@ssw0rd123", "Strong#Password2023"]
        
        for password in weak_passwords:
            with self.subTest(password=password):
                is_strong = self.encryption_engine.validate_password_strength(password)
                self.assertFalse(is_strong)
        
        for password in strong_passwords:
            with self.subTest(password=password):
                is_strong = self.encryption_engine.validate_password_strength(password)
                self.assertTrue(is_strong)


class TestEncryptionTemplates(unittest.TestCase):
    """Test encryption templates functionality."""
    
    def test_template_creation(self):
        """Test template creation and validation."""
        template = EncryptionTemplates.get_template("secure_backup")
        self.assertIsNotNone(template)
        self.assertEqual(template.name, "Secure Backup")
        self.assertIn("algorithm", template.config)
    
    def test_template_validation(self):
        """Test template configuration validation."""
        valid_config = {
            "algorithm": "AES-256-GCM",
            "key_iterations": 100000,
            "store_password": True
        }
        
        errors = EncryptionTemplates.validate_template_config(valid_config)
        self.assertEqual(len(errors), 0)
        
        invalid_config = {
            "algorithm": "INVALID-ALGORITHM",
            "key_iterations": 1000,  # Too low
            "store_password": "not_boolean"
        }
        
        errors = EncryptionTemplates.validate_template_config(invalid_config)
        self.assertGreater(len(errors), 0)
    
    def test_template_manager(self):
        """Test template manager functionality."""
        manager = TemplateManager()
        
        # Test getting templates
        templates = manager.get_available_templates()
        self.assertGreater(len(templates), 0)
        
        # Test custom template creation
        custom_config = {
            "algorithm": "AES-256-CBC",
            "key_iterations": 75000,
            "store_password": True
        }
        
        success = manager.add_custom_template("custom_test", "Test template", custom_config)
        self.assertTrue(success)
        
        # Test template removal
        success = manager.remove_custom_template("custom_test")
        self.assertTrue(success)
    
    def test_template_export_import(self):
        """Test template export and import."""
        manager = TemplateManager()
        
        # Add a custom template
        custom_config = {
            "algorithm": "AES-256-CBC",
            "key_iterations": 75000,
            "store_password": True
        }
        manager.add_custom_template("export_test", "Export test template", custom_config)
        
        # Export
        temp_file = pathlib.Path(tempfile.mktemp(suffix='.json'))
        success = manager.export_template("export_test", temp_file)
        self.assertTrue(success)
        self.assertTrue(temp_file.exists())
        
        # Import
        new_manager = TemplateManager()
        success = new_manager.import_template(temp_file)
        self.assertTrue(success)
        
        # Clean up
        temp_file.unlink(missing_ok=True)


class TestPasswordManager(unittest.TestCase):
    """Test password management functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.password_manager = PasswordManager()
    
    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch('keyring.get_password')
    @patch('keyring.set_password')
    def test_password_storage(self, mock_set, mock_get):
        """Test password storage and retrieval."""
        mock_set.return_value = None
        mock_get.return_value = "stored_password"
        
        # Store password
        self.password_manager.store_password("test_service", "test_password")
        mock_set.assert_called_once()
        
        # Retrieve password
        password = self.password_manager.get_password("test_service")
        self.assertEqual(password, "stored_password")
        mock_get.assert_called_once()
    
    @patch('keyring.get_password')
    def test_password_retrieval_nonexistent(self, mock_get):
        """Test retrieval of non-existent password."""
        mock_get.return_value = None
        
        password = self.password_manager.get_password("nonexistent_service")
        self.assertIsNone(password)
    
    def test_password_generation(self):
        """Test secure password generation."""
        password = self.password_manager.generate_secure_password(16)
        
        self.assertEqual(len(password), 16)
        self.assertTrue(any(c.isupper() for c in password))
        self.assertTrue(any(c.islower() for c in password))
        self.assertTrue(any(c.isdigit() for c in password))
        self.assertTrue(any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password))


class TestIntegration(unittest.TestCase):
    """Test integration between encryption components."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_file = pathlib.Path(self.temp_dir) / "integration_test.txt"
        self.test_file.write_text("Integration test content")
        
        self.encryption_engine = EncryptionEngine()
        self.settings_manager = SettingsManager()
        self.template_manager = TemplateManager(self.settings_manager)
    
    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_template_application(self):
        """Test applying templates to encryption engine."""
        template_name = "secure_backup"
        success = self.template_manager.apply_template(template_name, self.encryption_engine)
        self.assertTrue(success)
        
        # Verify settings were applied
        self.assertEqual(self.encryption_engine.algorithm, "AES-256-GCM")
        self.assertEqual(self.encryption_engine.key_iterations, 500000)
    
    def test_settings_integration(self):
        """Test integration with settings manager."""
        # Update settings
        self.settings_manager.set("encryption_algorithm", "AES-256-GCM")
        self.settings_manager.set("key_iterations", 200000)
        
        # Apply settings to engine
        self.encryption_engine.algorithm = self.settings_manager.get("encryption_algorithm")
        self.encryption_engine.key_iterations = self.settings_manager.get("key_iterations")
        
        self.assertEqual(self.encryption_engine.algorithm, "AES-256-GCM")
        self.assertEqual(self.encryption_engine.key_iterations, 200000)
    
    def test_end_to_end_workflow(self):
        """Test complete encryption workflow."""
        # Apply template
        self.template_manager.apply_template("daily_work", self.encryption_engine)
        
        # Encrypt file
        encrypted_file = self.test_file.with_suffix('.txt.enc')
        password = "test_password_123"
        
        self.encryption_engine.encrypt_file(self.test_file, encrypted_file, password)
        self.assertTrue(encrypted_file.exists())
        
        # Verify encryption
        is_valid = self.encryption_engine.verify_encrypted_file(encrypted_file, password)
        self.assertTrue(is_valid)
        
        # Decrypt file
        decrypted_file = self.test_file.with_suffix('.txt.decrypted')
        self.encryption_engine.decrypt_file(encrypted_file, decrypted_file, password)
        
        # Verify content
        original_content = self.test_file.read_text()
        decrypted_content = decrypted_file.read_text()
        self.assertEqual(original_content, decrypted_content)


def run_tests():
    """Run all encryption tests."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTests(loader.loadTestsFromTestCase(TestEncryptionEngine))
    suite.addTests(loader.loadTestsFromTestCase(TestEncryptionTemplates))
    suite.addTests(loader.loadTestsFromTestCase(TestPasswordManager))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)