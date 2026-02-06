from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING 

if TYPE_CHECKING:
    from src.config_service import ConfigService


class ToolName(str, Enum):
    """
    Defines the unique internal names for all interactive tools in the application.
    These are used as keys for configuration and internal identification.
    """
    SELECTION = "selection"
    DIRECT_SELECTION = "direct_selection"
    EYEDROPPER = "eyedropper"
    PLOT = "plot"
    TEXT = "text"
    ZOOM = "zoom"
    # Add other tools as they are implemented

class LayoutMode(str, Enum):
    """
    Defines the different layout modes for the application canvas.
    """
    FREE_FORM = "free_form"
    GRID = "grid"


class IconPath:
    """
    Provides a centralized way to access icon file paths,
    retrieving them from the ConfigService.
    """
    _config_service: 'ConfigService' = None

    @classmethod
    def set_config_service(cls, config_service: 'ConfigService'):
        """Sets the ConfigService instance to be used for retrieving icon paths."""
        cls._config_service = config_service

    @classmethod
    def get_path(cls, icon_key: str) -> str:
        """
        Retrieves the full path for a given icon key from the ConfigService.
        e.g., IconPath.get_path("tool_icons.select") -> "src/assets/icons/toolbar/Select.svg"
        """
        if cls._config_service is None:
            raise RuntimeError("ConfigService not set for IconPath. Call IconPath.set_config_service() first.")
        
        base_dir = Path(cls._config_service.get("paths.icon_base_dir", "src/assets/icons"))
        icon_file = cls._config_service.get(f"paths.{icon_key}")
        if icon_file:
            return str(base_dir / icon_file)
        return "" # Or raise an error, depending on desired behavior
