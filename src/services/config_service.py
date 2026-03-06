import logging
from pathlib import Path

import yaml

from src.shared.exceptions import ConfigError


class ConfigService:
    """
    A service for managing application configuration loaded from YAML files.
    Standardized as a standard class to support Dependency Injection and 
    isolated testing.
    """

    def __init__(self, config_path: Path = None):
        self._config = {}
        self._initialized = False
        self.logger = logging.getLogger(self.__class__.__name__)
        
        if config_path:
            self._load_config(config_path)

    def _load_config(self, config_path: Path):
        self.logger.info(f"Attempting to load configuration from: {config_path}")
        if not config_path.exists():
            self.logger.error(
                f"Configuration file not found at {config_path}. Using empty configuration."
            )
            self._config = {}
            self._initialized = False
            return
        try:
            with open(config_path, "r") as f:
                self._config = yaml.safe_load(f) or {}
            self._config["config_path"] = config_path
            self._initialized = True
            self.logger.info(f"Configuration loaded successfully from: {config_path}")
        except yaml.YAMLError as e:
            self.logger.error(
                f"Error parsing YAML configuration from {config_path}: {e}. Using empty configuration."
            )
            self._config = {}
            self._initialized = False

    def get(self, key_path: str, default=None):
        self.logger.debug(
            f"Getting config key: '{key_path}' with default: '{default}'."
        )
        if not self._initialized:
            self.logger.warning(
                f"ConfigService not initialized. Returning default '{default}' for key '{key_path}'."
            )
            return default

        keys = key_path.split(".")
        value = self._config
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                self.logger.warning(
                    f"Config key '{key_path}' not found. Returning default: '{default}'."
                )
                return default
        self.logger.debug(
            f"Successfully retrieved config key '{key_path}'. Result: '{value}'."
        )
        return value

    def get_required(self, key_path: str):
        self.logger.debug(f"Getting required config key: '{key_path}'.")
        if not self._initialized:
            raise ConfigError(
                f"ConfigService not initialized. Required key '{key_path}' cannot be retrieved."
            )

        keys = key_path.split(".")
        value = self._config
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                raise ConfigError(
                    f"Required configuration key '{key_path}' not found in the configuration."
                )
        self.logger.debug(
            f"Successfully retrieved required config key '{key_path}'. Result: '{value}'."
        )
        return value
