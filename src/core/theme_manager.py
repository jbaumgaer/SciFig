import logging

from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication

from src.services.config_service import ConfigService


class ThemeManager:
    """
    Manages application themes, loading them from ConfigService and applying them
    to the QApplication instance.
    """
    def __init__(self, app: QApplication, config_service: ConfigService):
        self._app = app
        self._config_service = config_service
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info("ThemeManager initialized.")

    def apply_theme(self, theme_name: str):
        """
        Loads the specified theme from configuration and applies it to the QApplication.
        """
        self.logger.info(f"Attempting to apply theme: '{theme_name}'")
        theme_definition = self._config_service.get(f"themes.{theme_name}")

        if not theme_definition:
            self.logger.error(f"Theme '{theme_name}' not found in configuration. Falling back to default.")
            # Fallback to default theme if the requested one is not found
            default_theme_name = self._config_service.get("ui.default_theme", "dark")
            if theme_name != default_theme_name: # Avoid infinite recursion
                self.apply_theme(default_theme_name)
            else:
                self.logger.critical(f"Default theme '{default_theme_name}' also not found. Application may not be themed correctly.")
            return

        # Apply style (e.g., "Fusion")
        style_name = theme_definition.get("style")
        if style_name:
            self._app.setStyle(style_name)
            self.logger.debug(f"Applied Qt style: '{style_name}'")
        else:
            self.logger.warning(f"No 'style' defined for theme '{theme_name}'. Using current application style.")

        # Apply palette colors
        palette_colors = theme_definition.get("palette", {})
        new_palette = QPalette()

        for role_name, rgb_list in palette_colors.items():
            try:
                role = getattr(QPalette, role_name)
                color = QColor(*rgb_list)
                new_palette.setColor(role, color)
                self.logger.debug(f"  Set palette role '{role_name}' to RGB: {rgb_list}")
            except AttributeError:
                self.logger.warning(f"QPalette role '{role_name}' not found. Skipping.")
            except TypeError:
                self.logger.warning(f"Invalid RGB list for palette role '{role_name}'. Expected [R,G,B]. Skipping.")

        self._app.setPalette(new_palette)
        self.logger.info(f"Theme '{theme_name}' applied successfully.")

    def get_available_themes(self) -> list[str]:
        """
        Returns a list of all theme names defined in the configuration.
        """
        themes_config = self._config_service.get("themes", {})
        return list(themes_config.keys())
