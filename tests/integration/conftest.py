from unittest.mock import MagicMock

import matplotlib
import pytest

from src.controllers.layout_controller import LayoutController
from src.models.application_model import ApplicationModel
from src.models.layout.free_layout_engine import FreeLayoutEngine
from src.models.layout.grid_layout_engine import GridLayoutEngine
from src.models.nodes.scene_node import SceneNode
from src.services.commands.command_manager import CommandManager
from src.services.config_service import ConfigService
from src.services.layout_manager import LayoutManager


@pytest.fixture
def mock_figure():
    """Provides a mock matplotlib.figure.Figure instance."""
    return MagicMock(spec=matplotlib.figure.Figure)


@pytest.fixture
def mock_config_service():
    """
    Provides a comprehensive mock ConfigService, configurable with default values
    for figure, tools, and layout.
    """
    config_service = MagicMock(spec=ConfigService)
    config_service.get.side_effect = lambda key, default=None: {
        "figure.default_width": 5.0,
        "figure.default_height": 3.0,
        "figure.default_dpi": 200,
        "figure.default_facecolor": "blue",
        "tool.default_active_tool": "selection",
        "paths.icon_base_dir": "mock/icons",
        "paths.tool_icons.select": "mock_select.svg",
        "paths.tool_icons.direct_select": "mock_direct_select.svg",
        "paths.tool_icons.eyedropper": "mock_eyedropper.svg",
        "paths.tool_icons.plot": "mock_plot.svg",
        "paths.tool_icons.text": "mock_text.svg",
        "paths.tool_icons.zoom": "mock_zoom.svg",
        "organization": "TestOrg",
        "app_name": "TestApp",
        "layout.default_margin": 0.1,
        "layout.default_gutter": 0.08,
        "layout.max_recent_files": 5,
        "ui.default_layout_mode": "free_form",
        "layout.default_grid_rows": 1,
        "layout.default_grid_cols": 1,
        "layout.grid_margin_top": 0.05,
        "layout.grid_margin_bottom": 0.05,
        "layout.grid_margin_left": 0.05,
        "layout.grid_margin_right": 0.05,
        "layout.grid_hspace": "0.02",
        "layout.grid_wspace": "0.02",
        "layout.constrained_w_space": 0.02,
        "layout.constrained_h_space": 0.02,
    }.get(key, default)
    config_service.get_required.side_effect = lambda key: {
        "figure.default_width": 5.0,
        "figure.default_height": 3.0,
        "figure.default_dpi": 200,
        "figure.default_facecolor": "blue",
    }.get(key)
    return config_service


@pytest.fixture
def real_application_model(mock_figure, mock_config_service):
    """Provides a real ApplicationModel instance for integration tests."""
    model = ApplicationModel(figure=mock_figure, config_service=mock_config_service)
    model.scene_root = SceneNode()  # Initialize with a real scene root
    return model


@pytest.fixture
def real_command_manager(real_application_model):
    """Provides a real CommandManager instance."""
    return CommandManager(model=real_application_model)


@pytest.fixture
def real_grid_layout_engine(mock_config_service):
    """Provides a real GridLayoutEngine instance."""
    return GridLayoutEngine(config_service=mock_config_service)


@pytest.fixture
def real_free_layout_engine():
    """Provides a real FreeLayoutEngine instance."""
    return FreeLayoutEngine()


@pytest.fixture
def real_layout_manager(
    real_application_model,
    real_grid_layout_engine,
    real_free_layout_engine,
    mock_config_service,
):
    """Provides a real LayoutManager instance."""
    return LayoutManager(
        real_application_model,
        real_free_layout_engine,
        real_grid_layout_engine,
        mock_config_service,
    )


@pytest.fixture
def real_layout_controller(
    real_application_model, real_command_manager, real_layout_manager
):
    """Provides a real LayoutController instance for integration tests."""
    return LayoutController(
        real_application_model, real_command_manager, real_layout_manager
    )
