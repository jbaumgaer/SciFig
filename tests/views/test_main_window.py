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
    A pytest fixture that sets up the main application window with a real
    model and a mocked command manager, instantiating a real MainWindow.
    """
    app = QApplication.instance() or QApplication([])
    
    figure = matplotlib.figure.Figure()
    model = ApplicationModel(figure=figure)
    mock_command_manager = MagicMock(spec=CommandManager)
    plot_types = [PlotType.LINE, PlotType.SCATTER]

    main_window = MainWindow(model, mock_command_manager, plot_types)
    qtbot.addWidget(main_window)
    main_window.show()
    qtbot.waitExposed(main_window)
    
    return {
        "window": main_window,
        "model": model,
        "command_manager": mock_command_manager,
    }


def test_main_window_init(app_context):
    """Test the initialization of the MainWindow with real components."""
    window = app_context["window"]
    assert window.windowTitle() == "SciFig - Data Analysis GUI"
    assert window.centralWidget() is not None
    assert window.canvas_widget is not None
    assert window.centralWidget() == window.canvas_widget

    properties_dock = window.properties_dock
    assert properties_dock is not None
    assert properties_dock.widget() == window.properties_view

    assert window.command_manager is app_context["command_manager"]

    assert window.menu_bar is not None
    assert window.file_menu is not None
    assert window.edit_menu is not None
    assert window.new_layout_action is not None
    assert window.undo_action is not None
    assert window.redo_action is not None


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


def test_new_layout_action_exists(app_context):
    """Test that the 'New Layout...' menu action exists."""
    window = app_context["window"]
    assert window.new_layout_action is not None
    assert window.new_layout_action.text() == "&New Layout..."


def test_show_properties_panel(app_context, qtbot):
    """Test that show_properties_panel makes the dock widget visible."""
    window = app_context["window"]
    properties_dock = window.properties_dock

    properties_dock.hide()
    qtbot.wait(10)
    assert not properties_dock.isVisible()

    window.show_properties_panel()

    qtbot.waitUntil(properties_dock.isVisible)
    assert properties_dock.isVisible()