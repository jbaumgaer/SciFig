import logging
from pathlib import Path

import yaml

from src.shared.exceptions import ConfigError


class ConfigService:
    _instance = None

    def __new__(cls, config_path: Path = None):
        if cls._instance is None:
            cls._instance = super(ConfigService, cls).__new__(cls)
            cls._instance._config = {}
            cls._instance._initialized = False
            cls._instance.logger = logging.getLogger(cls.__name__)
            if config_path:
                cls._instance._load_config(config_path)
        return cls._instance

    def _load_config(self, config_path: Path):
        self.logger.info(f"Attempting to load configuration from: {config_path}")
        if not config_path.exists():
            self.logger.error(
                f"Configuration file not found at {config_path}. Using empty configuration."
            )
            self._config = {}  # Use empty config if file not found
            self._initialized = False  # Not fully initialized
            return
        try:
            with open(config_path, "r") as f:
                self._config = yaml.safe_load(f) or {}  # Handle empty YAML file
            self._config["config_path"] = config_path
            self._initialized = True
            self.logger.info(f"Configuration loaded successfully from: {config_path}")
        except yaml.YAMLError as e:
            self.logger.error(
                f"Error parsing YAML configuration from {config_path}: {e}. Using empty configuration."
            )
            self._config = {}  # Use empty config on parsing error
            self._initialized = False  # Not fully initialized

    def get(self, key_path: str, default=None):
        # TODO: Somehow this method is constantly being called together with LayoutTab Updating content for UI layout mode: grid and LayoutUIFactory - DEBUG - Building layout controls for UI selected mode: grid
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
