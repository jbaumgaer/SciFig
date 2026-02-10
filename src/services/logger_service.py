import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from src.services.config_service import ConfigService


def setup_logging(config_service: ConfigService):
    """
    Configures the application's logging system based on settings from ConfigService.
    """
    log_config = config_service._config.get("logging", {}) # Access raw config for simplicity

    log_level_str = log_config.get("level", "INFO").upper()
    log_level = getattr(logging, log_level_str, logging.INFO)

    file_output = log_config.get("file_output", False)
    file_path_str = log_config.get("file_path", "app.log")
    file_max_bytes = log_config.get("file_max_bytes", 10 * 1024 * 1024) # 10 MB
    file_backup_count = log_config.get("file_backup_count", 5)

    console_output = log_config.get("console_output", True)
    log_format = log_config.get("format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    date_format = log_config.get("date_format", "%Y-%m-%d %H:%M:%S")

    # Get the root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Clear existing handlers to prevent duplicate output when reloading config or in test runs
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Console Handler
    if console_output:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(log_format, datefmt=date_format))
        root_logger.addHandler(console_handler)

    # File Handler
    if file_output:
        log_dir = Path(file_path_str).parent
        log_dir.mkdir(parents=True, exist_ok=True) # Ensure log directory exists
        file_handler = RotatingFileHandler(
            file_path_str,
            maxBytes=file_max_bytes,
            backupCount=file_backup_count,
            encoding='utf-8'
        )
        file_handler.setFormatter(logging.Formatter(log_format, datefmt=date_format))
        root_logger.addHandler(file_handler)

    # Silence matplotlib's often verbose logging unless debugging
    logging.getLogger('matplotlib').setLevel(logging.WARNING)
    logging.getLogger('PySide6').setLevel(logging.WARNING)

    # Initial log message to confirm setup
    logging.info(f"Logging configured. Level: {log_level_str}, Console: {console_output}, File: {file_output}")
