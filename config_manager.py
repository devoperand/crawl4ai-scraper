#!/usr/bin/env python3
"""
Configuration persistence system for crawl4ai-scraper.
Allows saving, loading, and managing crawling configurations.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime


class ConfigManager:
    """Manages saving and loading of crawling configurations."""
    
    def __init__(self, config_dir: Optional[Path] = None):
        """
        Initialize configuration manager.
        
        Args:
            config_dir: Directory to store config files. Defaults to ~/.crawl4ai/configs
        """
        if config_dir:
            self.config_dir = Path(config_dir)
        else:
            # Use user's home directory
            self.config_dir = Path.home() / '.crawl4ai' / 'configs'
        
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.default_config_path = self.config_dir / 'default.json'
        
        # Ensure default config exists
        if not self.default_config_path.exists():
            self._create_default_config()
    
    def _create_default_config(self):
        """Create default configuration file."""
        default_config = {
            "name": "default",
            "description": "Default crawling configuration",
            "created_at": datetime.now().isoformat(),
            "settings": {
                "max_depth": 2,
                "max_pages": 50,
                "include_external": False,
                "concurrent_limit": 3,
                "delay_between_requests": 1.0,
                "timeout": 30,
                "cache_mode": True,
                "organize_by_structure": False,
                "output_dir": "output",
                "verbose": True
            },
            "output_settings": {
                "organization_strategy": "flat",
                "naming_convention": "url_based",
                "include_metadata": True
            }
        }
        
        self.save_config("default", default_config)
    
    def save_config(self, name: str, config_dict: Dict[str, Any]) -> bool:
        """
        Save configuration to file.
        
        Args:
            name: Configuration name
            config_dict: Configuration dictionary to save
            
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            config_path = self.config_dir / f"{name}.json"
            
            # Add metadata
            config_dict["name"] = name
            config_dict["saved_at"] = datetime.now().isoformat()
            
            with open(config_path, 'w') as f:
                json.dump(config_dict, f, indent=2)
            
            return True
            
        except Exception as e:
            print(f"Error saving config '{name}': {e}")
            return False
    
    def load_config(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Load configuration from file.
        
        Args:
            name: Configuration name
            
        Returns:
            Configuration dictionary or None if not found
        """
        try:
            config_path = self.config_dir / f"{name}.json"
            
            if not config_path.exists():
                return None
            
            with open(config_path, 'r') as f:
                return json.load(f)
                
        except Exception as e:
            print(f"Error loading config '{name}': {e}")
            return None
    
    def list_configs(self) -> List[Dict[str, Any]]:
        """
        List all available configurations.
        
        Returns:
            List of configuration summaries
        """
        configs = []
        
        for config_file in self.config_dir.glob("*.json"):
            try:
                with open(config_file, 'r') as f:
                    config_data = json.load(f)
                
                configs.append({
                    "name": config_data.get("name", config_file.stem),
                    "description": config_data.get("description", "No description"),
                    "created_at": config_data.get("created_at", "Unknown"),
                    "saved_at": config_data.get("saved_at", "Unknown"),
                    "settings_count": len(config_data.get("settings", {})),
                    "file_path": str(config_file)
                })
                
            except Exception as e:
                print(f"Error reading config {config_file}: {e}")
                continue
        
        # Sort by save time (most recent first)
        configs.sort(key=lambda x: x.get("saved_at", ""), reverse=True)
        return configs
    
    def delete_config(self, name: str) -> bool:
        """
        Delete configuration file.
        
        Args:
            name: Configuration name
            
        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            if name == "default":
                print("Cannot delete default configuration")
                return False
            
            config_path = self.config_dir / f"{name}.json"
            
            if not config_path.exists():
                print(f"Configuration '{name}' not found")
                return False
            
            config_path.unlink()
            return True
            
        except Exception as e:
            print(f"Error deleting config '{name}': {e}")
            return False
    
    def export_config(self, name: str, export_path: Path) -> bool:
        """
        Export configuration to specified path.
        
        Args:
            name: Configuration name
            export_path: Path to export to
            
        Returns:
            True if exported successfully, False otherwise
        """
        try:
            config_data = self.load_config(name)
            if not config_data:
                print(f"Configuration '{name}' not found")
                return False
            
            with open(export_path, 'w') as f:
                json.dump(config_data, f, indent=2)
            
            return True
            
        except Exception as e:
            print(f"Error exporting config '{name}': {e}")
            return False
    
    def import_config(self, import_path: Path, name: Optional[str] = None) -> bool:
        """
        Import configuration from file.
        
        Args:
            import_path: Path to import from
            name: New configuration name (optional)
            
        Returns:
            True if imported successfully, False otherwise
        """
        try:
            if not import_path.exists():
                print(f"Import file '{import_path}' not found")
                return False
            
            with open(import_path, 'r') as f:
                config_data = json.load(f)
            
            # Use provided name or derive from file
            if name:
                config_name = name
            else:
                config_name = config_data.get("name", import_path.stem)
            
            # Validate config structure
            if not self._validate_config(config_data):
                print(f"Invalid configuration format in '{import_path}'")
                return False
            
            return self.save_config(config_name, config_data)
            
        except Exception as e:
            print(f"Error importing config from '{import_path}': {e}")
            return False
    
    def _validate_config(self, config_data: Dict[str, Any]) -> bool:
        """
        Validate configuration data structure.
        
        Args:
            config_data: Configuration dictionary
            
        Returns:
            True if valid, False otherwise
        """
        required_fields = ["settings"]
        
        for field in required_fields:
            if field not in config_data:
                return False
        
        # Validate settings structure
        settings = config_data["settings"]
        required_settings = [
            "max_depth", "max_pages", "concurrent_limit", 
            "delay_between_requests", "timeout", "cache_mode"
        ]
        
        for setting in required_settings:
            if setting not in settings:
                return False
        
        return True
    
    def create_presets(self):
        """Create common configuration presets."""
        presets = {
            "fast": {
                "name": "fast",
                "description": "Fast crawling for quick results",
                "created_at": datetime.now().isoformat(),
                "settings": {
                    "max_depth": 1,
                    "max_pages": 10,
                    "include_external": False,
                    "concurrent_limit": 5,
                    "delay_between_requests": 0.5,
                    "timeout": 15,
                    "cache_mode": True,
                    "organize_by_structure": False,
                    "output_dir": "output",
                    "verbose": False
                },
                "output_settings": {
                    "organization_strategy": "flat",
                    "naming_convention": "url_based",
                    "include_metadata": True
                }
            },
            
            "comprehensive": {
                "name": "comprehensive",
                "description": "Comprehensive crawling for complete coverage",
                "created_at": datetime.now().isoformat(),
                "settings": {
                    "max_depth": 3,
                    "max_pages": 200,
                    "include_external": False,
                    "concurrent_limit": 2,
                    "delay_between_requests": 2.0,
                    "timeout": 60,
                    "cache_mode": True,
                    "organize_by_structure": True,
                    "output_dir": "comprehensive_crawl",
                    "verbose": True
                },
                "output_settings": {
                    "organization_strategy": "mirror",
                    "naming_convention": "title_based",
                    "include_metadata": True
                }
            },
            
            "api_docs": {
                "name": "api_docs",
                "description": "Optimized for API documentation sites",
                "created_at": datetime.now().isoformat(),
                "settings": {
                    "max_depth": 2,
                    "max_pages": 100,
                    "include_external": False,
                    "concurrent_limit": 3,
                    "delay_between_requests": 1.0,
                    "timeout": 45,
                    "cache_mode": True,
                    "organize_by_structure": True,
                    "output_dir": "api_docs",
                    "verbose": True
                },
                "output_settings": {
                    "organization_strategy": "mirror",
                    "naming_convention": "url_based",
                    "include_metadata": True
                }
            }
        }
        
        for name, preset in presets.items():
            if not (self.config_dir / f"{name}.json").exists():
                self.save_config(name, preset)


def config_to_crawl_config(config_data: Dict[str, Any], crawl_config_class):
    """
    Convert saved configuration to CrawlConfig object.
    
    Args:
        config_data: Saved configuration dictionary
        crawl_config_class: CrawlConfig class to instantiate
        
    Returns:
        Configured CrawlConfig object
    """
    config = crawl_config_class()
    settings = config_data.get("settings", {})
    
    # Apply settings
    for key, value in settings.items():
        if hasattr(config, key):
            setattr(config, key, value)
    
    return config


def crawl_config_to_dict(config, output_manager=None) -> Dict[str, Any]:
    """
    Convert CrawlConfig object to dictionary for saving.
    
    Args:
        config: CrawlConfig object
        output_manager: Optional OutputManager for output settings
        
    Returns:
        Configuration dictionary
    """
    config_dict = {
        "name": "current",
        "description": "Current session configuration",
        "created_at": datetime.now().isoformat(),
        "settings": {}
    }
    
    # Extract crawling settings
    crawl_settings = [
        "max_depth", "max_pages", "include_external", "concurrent_limit",
        "delay_between_requests", "timeout", "cache_mode", "organize_by_structure",
        "output_dir", "verbose"
    ]
    
    for setting in crawl_settings:
        if hasattr(config, setting):
            value = getattr(config, setting)
            # Convert Path objects to strings
            if isinstance(value, Path):
                value = str(value)
            config_dict["settings"][setting] = value
    
    # Extract output settings if manager provided
    if output_manager:
        config_dict["output_settings"] = {
            "organization_strategy": getattr(output_manager, "organization_strategy", "flat"),
            "naming_convention": getattr(output_manager, "naming_convention", "url_based"),
            "include_metadata": getattr(output_manager, "include_metadata", True)
        }
    
    return config_dict