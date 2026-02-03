import pytest
from unittest.mock import MagicMock

import matplotlib.figure
from PySide6.QtWidgets import QApplication

from src.commands.command_manager import CommandManager
from src.models.application_model import ApplicationModel
from src.views.main_window import MainWindow
from src.models.nodes.plot_types import PlotType

@pytest.fixture
def app_context(qtbot):
    """
    A pytest fixture that sets up the main application window.
    """
    app = QApplication.instance() or QApplication([])
    
    figure = matplotlib.figure.Figure()
    model = ApplicationModel(figure=figure)
    mock_command_manager = MagicMock(spec=CommandManager)
    plot_types = [PlotType.LINE, PlotType.SCATTER]

    main_window = MainWindow(model, mock_command_manager, plot_types)
    qtbot.addWidget(main_window)
    
    return {
        "window": main_window,
        "model": model,
        "command_manager": mock_command_manager,
    }


def test_main_window_init(app_context):
    """Test the initialization of the MainWindow."""
    window = app_context["window"]
    assert window.windowTitle() == "SciFig - Data Analysis GUI"

def test_undo_action_triggers_command_manager(app_context):
    """Test that the 'Undo' menu action triggers the command manager's undo method."""
    window = app_context["window"]
    command_manager = app_context["command_manager"]

    window.undo_action.trigger()

    command_manager.undo.assert_called_once()

def test_redo_action_triggers_command_manager(app_context):
    """Test that the 'Redo' menu action triggers the command manager's redo method."""
    window = app_context["window"]
    command_manager = app_context["command_manager"]

    window.redo_action.trigger()

    command_manager.redo.assert_called_once()
