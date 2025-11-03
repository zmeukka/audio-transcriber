"""
Configuration loader module for Audio Transcriber
Handles loading and parsing of YAML configuration files
"""

import yaml
import os
from pathlib import Path


class ConfigLoader:
    """Handles loading and validation of configuration files"""

    @staticmethod
    def load(config_path: str) -> dict:
        """
        Load configuration from YAML file

        Args:
            config_path: Path to configuration file

        Returns:
            Configuration dictionary

        Raises:
            FileNotFoundError: If config file doesn't exist
            yaml.YAMLError: If config file is invalid YAML
        """
        config_file = Path(config_path)

        if not config_file.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        try:
            with open(config_file, 'r', encoding='utf-8') as file:
                config = yaml.safe_load(file)

            # Validate required fields
            ConfigLoader._validate_config(config)

            # Ensure directories exist
            ConfigLoader._ensure_directories(config)

            return config

        except yaml.YAMLError as e:
            raise yaml.YAMLError(f"Invalid YAML in config file: {e}")

    @staticmethod
    def _validate_config(config: dict) -> None:
        """Validate that required configuration fields are present"""
        required_fields = [
            'input_directory',
            'output_directory',
            'manual_processing_directory'
        ]

        for field in required_fields:
            if field not in config:
                raise ValueError(f"Required configuration field missing: {field}")

    @staticmethod
    def _ensure_directories(config: dict) -> None:
        """Create directories if they don't exist"""
        directories = [
            config['input_directory'],
            config['output_directory'],
            config['manual_processing_directory']
        ]

        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
