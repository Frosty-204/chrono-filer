# src/encryption_templates.py
"""
Encryption templates for common use cases and scenarios.
Provides predefined encryption configurations and templates.
"""

from typing import Dict, Any, List
import pathlib


class EncryptionTemplate:
    """Represents a predefined encryption configuration."""
    
    def __init__(self, name: str, description: str, config: Dict[str, Any]):
        self.name = name
        self.description = description
        self.config = config
    
    def apply_to_engine(self, encryption_engine, settings_manager=None):
        """Apply this template configuration to an encryption engine."""
        for key, value in self.config.items():
            if hasattr(encryption_engine, key):
                setattr(encryption_engine, key, value)
            elif settings_manager and hasattr(settings_manager, key):
                setattr(settings_manager, key, value)


class EncryptionTemplates:
    """Collection of predefined encryption templates."""
    
    TEMPLATES = {
        "secure_backup": EncryptionTemplate(
            "Secure Backup",
            "High-security encryption for long-term backups with maximum key derivation",
            {
                "algorithm": "AES-256-GCM",
                "key_iterations": 500000,
                "store_password": True,
                "auto_verify": True,
                "compression_before_encryption": True
            }
        ),
        
        "daily_work": EncryptionTemplate(
            "Daily Work Files",
            "Balanced security and performance for everyday file encryption",
            {
                "algorithm": "AES-256-CBC",
                "key_iterations": 100000,
                "store_password": True,
                "auto_verify": False,
                "compression_before_encryption": False
            }
        ),
        
        "maximum_security": EncryptionTemplate(
            "Maximum Security",
            "Ultra-secure encryption for sensitive documents",
            {
                "algorithm": "AES-256-GCM",
                "key_iterations": 1000000,
                "store_password": False,
                "auto_verify": True,
                "compression_before_encryption": True,
                "additional_entropy": True
            }
        ),
        
        "quick_share": EncryptionTemplate(
            "Quick Share",
            "Fast encryption for temporary file sharing",
            {
                "algorithm": "AES-256-CBC",
                "key_iterations": 50000,
                "store_password": False,
                "auto_verify": False,
                "compression_before_encryption": False
            }
        ),
        
        "archival": EncryptionTemplate(
            "Long-term Archival",
            "Optimized for long-term storage with future-proof settings",
            {
                "algorithm": "AES-256-GCM",
                "key_iterations": 250000,
                "store_password": True,
                "auto_verify": True,
                "compression_before_encryption": True,
                "include_metadata": True
            }
        )
    }
    
    @classmethod
    def get_template(cls, name: str) -> EncryptionTemplate:
        """Get a specific encryption template by name."""
        return cls.TEMPLATES.get(name)
    
    @classmethod
    def get_all_templates(cls) -> List[EncryptionTemplate]:
        """Get all available encryption templates."""
        return list(cls.TEMPLATES.values())
    
    @classmethod
    def get_template_names(cls) -> List[str]:
        """Get names of all available templates."""
        return list(cls.TEMPLATES.keys())
    
    @classmethod
    def get_template_descriptions(cls) -> Dict[str, str]:
        """Get descriptions for all templates."""
        return {name: template.description for name, template in cls.TEMPLATES.items()}
    
    @classmethod
    def create_custom_template(cls, name: str, description: str, config: Dict[str, Any]) -> EncryptionTemplate:
        """Create a custom encryption template."""
        return EncryptionTemplate(name, description, config)
    
    @classmethod
    def validate_template_config(cls, config: Dict[str, Any]) -> List[str]:
        """Validate a template configuration and return any errors."""
        errors = []
        
        valid_algorithms = ["AES-256-CBC", "AES-256-GCM"]
        if "algorithm" in config and config["algorithm"] not in valid_algorithms:
            errors.append(f"Invalid algorithm: {config['algorithm']}")
        
        if "key_iterations" in config:
            iterations = config["key_iterations"]
            if not isinstance(iterations, int) or iterations < 10000 or iterations > 1000000:
                errors.append("key_iterations must be between 10000 and 1000000")
        
        boolean_fields = ["store_password", "auto_verify", "compression_before_encryption", 
                         "additional_entropy", "include_metadata"]
        for field in boolean_fields:
            if field in config and not isinstance(config[field], bool):
                errors.append(f"{field} must be a boolean value")
        
        return errors


class TemplateManager:
    """Manages encryption templates and user preferences."""
    
    def __init__(self, settings_manager=None):
        self.settings_manager = settings_manager
        self.custom_templates = {}
    
    def apply_template(self, template_name: str, encryption_engine):
        """Apply a template to the encryption engine."""
        template = EncryptionTemplates.get_template(template_name)
        if template:
            template.apply_to_engine(encryption_engine, self.settings_manager)
            return True
        elif template_name in self.custom_templates:
            self.custom_templates[template_name].apply_to_engine(encryption_engine, self.settings_manager)
            return True
        return False
    
    def add_custom_template(self, name: str, description: str, config: Dict[str, Any]) -> bool:
        """Add a custom encryption template."""
        errors = EncryptionTemplates.validate_template_config(config)
        if errors:
            return False
        
        self.custom_templates[name] = EncryptionTemplate(name, description, config)
        return True
    
    def remove_custom_template(self, name: str) -> bool:
        """Remove a custom encryption template."""
        if name in self.custom_templates:
            del self.custom_templates[name]
            return True
        return False
    
    def get_available_templates(self) -> List[EncryptionTemplate]:
        """Get all available templates including custom ones."""
        templates = EncryptionTemplates.get_all_templates()
        templates.extend(self.custom_templates.values())
        return templates
    
    def get_template_for_file_type(self, file_path: pathlib.Path) -> str:
        """Suggest a template based on file type."""
        suffix = file_path.suffix.lower()
        
        if suffix in ['.doc', '.docx', '.pdf', '.txt', '.md']:
            return "daily_work"
        elif suffix in ['.zip', '.tar', '.gz', '.bz2']:
            return "archival"
        elif suffix in ['.jpg', '.png', '.mp4', '.avi']:
            return "secure_backup"
        else:
            return "daily_work"
    
    def export_template(self, template_name: str, file_path: pathlib.Path) -> bool:
        """Export a template to a JSON file."""
        template = EncryptionTemplates.get_template(template_name)
        if not template and template_name not in self.custom_templates:
            return False
        
        if not template:
            template = self.custom_templates[template_name]
        
        try:
            import json
            with open(file_path, 'w') as f:
                json.dump({
                    "name": template.name,
                    "description": template.description,
                    "config": template.config
                }, f, indent=2)
            return True
        except Exception:
            return False
    
    def import_template(self, file_path: pathlib.Path) -> bool:
        """Import a template from a JSON file."""
        try:
            import json
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            name = data.get("name")
            description = data.get("description")
            config = data.get("config")
            
            if not all([name, description, config]):
                return False
            
            errors = EncryptionTemplates.validate_template_config(config)
            if errors:
                return False
            
            self.custom_templates[name] = EncryptionTemplate(name, description, config)
            return True
        except Exception:
            return False