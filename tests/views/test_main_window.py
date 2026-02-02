from unittest.mock import MagicMock

import matplotlib.figure
import pytest

from src.builders.main_window_builder import MainWindowBuilder  # Import the builder
from src.commands.command_manager import CommandManager
from src.models.application_model import ApplicationModel

# Import core application components


@pytest.fixture
def app_context(qtbot):
    """
    A pytest fixture that sets up the main application window with a real
    model and a mocked command manager, using the MainWindowBuilder.
    """
    # Use a real model to ensure all underlying components are created correctly
    figure = matplotlib.figure.Figure()
    model = ApplicationModel(figure=figure)
    # Mock the command manager as we are only testing the view's connection to it
    mock_command_manager = MagicMock(spec=CommandManager)

    # Use the builder to construct the MainWindow
    builder = MainWindowBuilder(model, mock_command_manager, plot_types=[])
    main_window = (
        builder.build_canvas().build_properties_dock().build_menu().get_window()
    )

    qtbot.addWidget(main_window)
    main_window.show()  # Explicitly show the main window
    qtbot.waitExposed(main_window)  # Wait for it to be exposed

    return {
        "window": main_window,
        "model": model,
        "command_manager": mock_command_manager,
    }


def test_main_window_init(app_context):
    """Test the initialization of the MainWindow."""
    window = app_context["window"]
    assert window.windowTitle() == "SciFig - Data Analysis GUI"
    assert window.centralWidget() is not None
    assert window.canvas_widget is not None  # Check if builder populated
    assert window.centralWidget() == window.canvas_widget

    # Check that the properties dock widget is created and added
    properties_dock = window.properties_dock  # Access directly via attribute
    assert properties_dock is not None
    assert properties_dock.widget() == window.properties_view

    # Check command_manager is set
    assert window.command_manager is app_context["command_manager"]

    # Check menu elements are populated
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

    # Trigger the action directly
    window.undo_action.trigger()

    # Assert that the command manager's undo method was called
    command_manager.undo.assert_called_once()


def test_redo_action_triggers_command_manager(app_context):
    """Test that the 'Redo' menu action triggers the command manager's redo method."""
    window = app_context["window"]
    command_manager = app_context["command_manager"]

    # Trigger the action directly
    window.redo_action.trigger()

    # Assert that the command manager's redo method was called
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

    # Initially hide the dock
    properties_dock.hide()
    qtbot.wait(10)  # Give event loop a chance to process hide event
    assert not properties_dock.isVisible()

    # Call the method to show it
    window.show_properties_panel()

    # Use qtbot.waitUntil to wait for the widget to become visible
    qtbot.waitUntil(properties_dock.isVisible)

    # Assert that it's now visible
    assert properties_dock.isVisible()
