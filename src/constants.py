from enum import Enum
from pathlib import Path


class ToolName(str, Enum):
    """
    Defines the unique names for all interactive tools in the application.
    Using an Enum prevents magic strings and ensures consistency.
    """
    SELECTION = "selection"
    DIRECT_SELECTION = "direct_selection"
    EYEDROPPER = "eyedropper"
    PLOT = "plot"
    TEXT = "text"
    ZOOM = "zoom"
    # Add other tools as they are implemented
    # e.g., SHAPE = "shape"
    # e.g., PATH = "path"


class IconPath:
    """
    Provides a centralized and type-safe way to reference icon file paths.
    This prevents magic strings for icon paths and makes refactoring easier.
    """
    _BASE_TOOLBAR_PATH = Path("src/assets/icons/toolbar")

    # Toolbar icons
    SELECT_TOOL = str(_BASE_TOOLBAR_PATH / "Select.svg")
    DIRECT_SELECT_TOOL = str(_BASE_TOOLBAR_PATH / "Direct_Select.svg")
    EYEDROPPER_TOOL = str(_BASE_TOOLBAR_PATH / "Eyedropper.svg")
    PLOT_TOOL = str(_BASE_TOOLBAR_PATH / "Plot.svg")
    TEXT_TOOL = str(_BASE_TOOLBAR_PATH / "Text.svg")
    ZOOM_TOOL = str(_BASE_TOOLBAR_PATH / "Zoom.svg")
    # Add other icons as needed
