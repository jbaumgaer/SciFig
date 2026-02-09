import pytest
from unittest.mock import MagicMock, patch, call
from PySide6.QtCore import QObject

from src.controllers.layout_controller import LayoutController
from src.models.application_model import ApplicationModel
from src.services.commands.command_manager import CommandManager
from src.services.layout_manager import LayoutManager
from src.shared.constants import LayoutMode

@pytest.fixture
def mock_app_model():
    model = MagicMock(spec=ApplicationModel)
    model.layoutConfigChanged = MagicMock()
    model.scene_root = MagicMock() # <--- ADDED THIS LINE to mock scene_root
    model.scene_root.all_plots.return_value = [] # Default for plots
    model.current_layout_config.mode = LayoutMode.FREE_FORM # Default mode
    return model

@pytest.fixture
def mock_command_manager():
    manager = MagicMock() # <--- REMOVED spec=CommandManager
    manager.execute = MagicMock()
    return manager

@pytest.fixture
def mock_layout_manager():
    return MagicMock(spec=LayoutManager)

@pytest.fixture
def layout_controller(mock_app_model, mock_command_manager, mock_layout_manager):
    return LayoutController(mock_app_model, mock_command_manager, mock_layout_manager)

def test_layout_controller_initialization(layout_controller, mock_app_model, mock_command_manager, mock_layout_manager):
    """
    Test that LayoutController initializes correctly and its attributes are set.
    """
    assert layout_controller.model is mock_app_model
    assert layout_controller.command_manager is mock_command_manager
    assert layout_controller._layout_manager is mock_layout_manager

def test_set_layout_mode(layout_controller, mock_app_model, mock_command_manager, mock_layout_manager):
    """
    Test that set_layout_mode calls LayoutManager.set_layout_mode and CommandManager.execute.
    """
    test_mode = LayoutMode.GRID
    layout_controller.set_layout_mode(test_mode)

    mock_layout_manager.set_layout_mode.assert_called_once_with(test_mode)
    mock_command_manager.execute.assert_called_once()
    # Optionally, assert that the command passed to execute is an UndoableCommand or has specific properties