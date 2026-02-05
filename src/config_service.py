import yaml
from pathlib import Path

class ConfigService:
    _instance = None

    def __new__(cls, config_path: Path = None):
        if cls._instance is None:
            cls._instance = super(ConfigService, cls).__new__(cls)
            cls._instance._config = {}
            cls._instance._initialized = False
            if config_path:
                cls._instance._load_config(config_path)
        return cls._instance

    def _load_config(self, config_path: Path):
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found at {config_path}")
        try:
            with open(config_path, 'r') as f:
                self._config = yaml.safe_load(f)
            self._initialized = True
        except yaml.YAMLError as e:
            raise ValueError(f"Error parsing YAML configuration: {e}")

    def get(self, key_path: str, default=None):
        if not self._initialized:
            # Attempt to load if not initialized but requested
            # This case might happen if __new__ was called without config_path initially
            # and then get() is called without subsequent load.
            # For simplicity, if not initialized, return default.
            return default 
            
        keys = key_path.split('.')
        value = self._config
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return value
