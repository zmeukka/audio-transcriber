"""
Configuration loader for Audio Transcriber API
Loads and validates configuration from YAML files
"""

import os
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional

from core.logger import get_logger


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load configuration from YAML file

    Args:
        config_path: Path to config file (default: ./config.yaml)

    Returns:
        Configuration dictionary
    """
    logger = get_logger(__name__)

    if config_path is None:
        config_path = "config.yaml"

    config_file = Path(config_path)

    # Default configuration
    default_config = {
        "shared_directory": "./shared",
        "model_directory": "./models",
        "temp_directory": "./temp",
        "processing_timeout": 600,  # 10 minutes
        "max_retries": 3,
        "log_level": "INFO",
        "api": {
            "host": "0.0.0.0",
            "port": 8000,
            "debug": False
        },
        "whisperx": {
            "default_model": "small",
            "default_compute_type": "float32",
            "default_language": None,
            "batch_size": 16,
            "device": "cpu"
        },
        "monitoring": {
            "enabled": True,
            "scan_interval": 60
        }
    }

    try:
        if config_file.exists():
            logger.info(f"Loading configuration from {config_file}")

            with open(config_file, 'r', encoding='utf-8') as f:
                file_config = yaml.safe_load(f) or {}

            # Merge with defaults (file config takes precedence)
            config = _merge_configs(default_config, file_config)

        else:
            logger.warning(f"Configuration file {config_file} not found, using defaults")
            config = default_config

        # Override with environment variables
        config = _apply_env_overrides(config)

        # Validate configuration
        _validate_config(config)

        logger.info("Configuration loaded successfully")
        return config

    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        logger.info("Using default configuration")
        return default_config


def _merge_configs(default: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recursively merge configuration dictionaries

    Args:
        default: Default configuration
        override: Override configuration

    Returns:
        Merged configuration
    """
    result = default.copy()

    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _merge_configs(result[key], value)
        else:
            result[key] = value

    return result


def _apply_env_overrides(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Apply environment variable overrides to configuration

    Args:
        config: Base configuration

    Returns:
        Configuration with environment overrides
    """
    # Environment variable mappings
    env_mappings = {
        "SHARED_DIRECTORY": ("shared_directory",),
        "MODEL_DIRECTORY": ("model_directory",),
        "TEMP_DIRECTORY": ("temp_directory",),
        "PROCESSING_TIMEOUT": ("processing_timeout", int),
        "MAX_RETRIES": ("max_retries", int),
        "LOG_LEVEL": ("log_level",),
        "API_HOST": ("api", "host"),
        "API_PORT": ("api", "port", int),
        "API_DEBUG": ("api", "debug", bool),
        "WHISPERX_DEFAULT_MODEL": ("whisperx", "default_model"),
        "WHISPERX_DEVICE": ("whisperx", "device"),
        "MONITORING_ENABLED": ("monitoring", "enabled", bool),
    }

    for env_var, path in env_mappings.items():
        env_value = os.getenv(env_var)
        if env_value is not None:
            # Apply type conversion if specified
            if len(path) > 1 and callable(path[-1]):
                converter = path[-1]
                path = path[:-1]
                try:
                    if converter == bool:
                        env_value = env_value.lower() in ('true', '1', 'yes', 'on')
                    else:
                        env_value = converter(env_value)
                except (ValueError, TypeError):
                    continue

            # Set the value in config
            current = config
            for key in path[:-1]:
                if key not in current:
                    current[key] = {}
                current = current[key]
            current[path[-1]] = env_value

    return config


def _validate_config(config: Dict[str, Any]) -> None:
    """
    Validate configuration values

    Args:
        config: Configuration to validate

    Raises:
        ValueError: If configuration is invalid
    """
    # Validate required directories
    required_dirs = ["shared_directory", "model_directory", "temp_directory"]
    for dir_key in required_dirs:
        if dir_key not in config:
            raise ValueError(f"Missing required configuration: {dir_key}")

    # Validate numeric values
    if config.get("processing_timeout", 0) <= 0:
        raise ValueError("processing_timeout must be positive")

    if config.get("max_retries", 0) < 0:
        raise ValueError("max_retries must be non-negative")

    # Validate API configuration
    api_config = config.get("api", {})
    port = api_config.get("port", 8000)
    if not isinstance(port, int) or port <= 0 or port > 65535:
        raise ValueError("API port must be between 1 and 65535")

    # Validate WhisperX configuration
    whisperx_config = config.get("whisperx", {})
    valid_models = ["tiny", "base", "small", "medium", "large"]
    default_model = whisperx_config.get("default_model", "small")
    if default_model not in valid_models:
        raise ValueError(f"default_model must be one of: {valid_models}")

    valid_compute_types = ["float16", "float32", "int8"]
    compute_type = whisperx_config.get("default_compute_type", "float32")
    if compute_type not in valid_compute_types:
        raise ValueError(f"default_compute_type must be one of: {valid_compute_types}")


def save_config(config: Dict[str, Any], config_path: Optional[str] = None) -> None:
    """
    Save configuration to YAML file

    Args:
        config: Configuration to save
        config_path: Path to save config file (default: ./config.yaml)
    """
    logger = get_logger(__name__)

    if config_path is None:
        config_path = "config.yaml"

    config_file = Path(config_path)

    try:
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, indent=2)

        logger.info(f"Configuration saved to {config_file}")

    except Exception as e:
        logger.error(f"Error saving configuration: {e}")
        raise


# Global configuration instance
_config: Optional[Dict[str, Any]] = None


def get_config() -> Dict[str, Any]:
    """Get the global configuration instance"""
    global _config
    if _config is None:
        _config = load_config()
    return _config


def reload_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """Reload configuration from file"""
    global _config
    _config = load_config(config_path)
    return _config
