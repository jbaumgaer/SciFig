import logging
import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

from src.core.application_components import ApplicationComponents
from src.core.composition_root import CompositionRoot
from src.core.theme_manager import ThemeManager
from src.services.config_service import ConfigService
from src.services.logger_service import setup_logging


def setup_application(
    app: QApplication, config_service: ConfigService
) -> ApplicationComponents:
    """
    Creates and wires up all the core components of the application using CompositionRoot.
    """
    assembler = CompositionRoot(app, config_service)
    return assembler.assemble()


def run_application():
    """The main entry point for the application."""
    # Configure logging first
    config_service = ConfigService(Path("configs/default_config.yaml"))
    setup_logging(config_service)

    logger = logging.getLogger(__name__)
    logger.info("Application starting...")

    app = QApplication.instance() or QApplication(
        sys.argv
    )  # QApplication is needed earlier for ThemeManager

    context = setup_application(app, config_service)
    view = context.view

    theme_manager = ThemeManager(app, config_service)
    default_theme_name = config_service.get("ui.default_theme", "dark")
    theme_manager.apply_theme(default_theme_name)

    view.show()
    logger.info("Application stopping...")
    sys.exit(app.exec())
