from unittest.mock import MagicMock

import matplotlib.figure
import pytest
from PySide6.QtWidgets import QApplication, QMenuBar, QToolBar, QMenu
from PySide6.QtGui import QAction # Corrected import for QAction # Added QMenuBar, QToolBar

from src.builders.menu_bar_builder import MainMenuActions # Added MainMenuActions
from src.builders.tool_bar_builder import ToolBarActions # Added ToolBarActions
from src.commands.command_manager import CommandManager
from src.controllers.main_controller import MainController
from src.models.application_model import ApplicationModel
from src.models.nodes.plot_types import PlotType
from src.views.main_window import MainWindow


@pytest.fixture
def mock_main_controller():
    """Fixture for a mock MainController."""
    return MagicMock(spec=MainController)

@pytest.fixture
def app_context(qtbot, mock_main_controller):
    """
    A pytest fixture that sets up the main application window with a real
    model and a mocked command manager, instantiating a real MainWindow.
    """
    app = QApplication.instance() or QApplication([])

    figure = matplotlib.figure.Figure()
    model = ApplicationModel(figure=figure)
    mock_command_manager = MagicMock(spec=CommandManager)
    plot_types = [PlotType.LINE, PlotType.SCATTER]

    # Create mock objects for the new MainWindow arguments
    mock_menu_bar = QMenuBar()
    mock_main_menu_actions = MagicMock(spec=MainMenuActions)
    mock_main_menu_actions.file_menu = MagicMock(spec=QMenu)
    mock_main_menu_actions.new_layout_action = MagicMock(spec=QAction)
    mock_main_menu_actions.new_layout_action.text.return_value = "&New Layout..."
    mock_main_menu_actions.new_file_action = MagicMock(spec=QAction)
    mock_main_menu_actions.new_file_from_template_action = MagicMock(spec=QAction)
    mock_main_menu_actions.open_project_action = MagicMock(spec=QAction)
    mock_main_menu_actions.open_recent_projects_menu = MagicMock(spec=QMenu)
    mock_main_menu_actions.close_action = MagicMock(spec=QAction)
    mock_main_menu_actions.save_project_action = MagicMock(spec=QAction)
    mock_main_menu_actions.save_copy_action = MagicMock(spec=QAction)
    mock_main_menu_actions.export_figure_menu = MagicMock(spec=QMenu)
    mock_main_menu_actions.export_vector_menu = MagicMock(spec=QMenu)
    mock_main_menu_actions.export_raster_menu = MagicMock(spec=QMenu)
    mock_main_menu_actions.export_svg_action = MagicMock(spec=QAction)
    mock_main_menu_actions.export_pdf_action = MagicMock(spec=QAction)
    mock_main_menu_actions.export_eps_action = MagicMock(spec=QAction)
    mock_main_menu_actions.export_png_action = MagicMock(spec=QAction)
    mock_main_menu_actions.export_tiff_action = MagicMock(spec=QAction)
    mock_main_menu_actions.export_python_action = MagicMock(spec=QAction)
    mock_main_menu_actions.exit_action = MagicMock(spec=QAction)
    mock_main_menu_actions.edit_menu = MagicMock(spec=QMenu)

    mock_main_menu_actions.undo_action = MagicMock(spec=QAction)
    mock_main_menu_actions.undo_action.trigger.side_effect = mock_command_manager.undo

    mock_main_menu_actions.redo_action = MagicMock(spec=QAction)
    mock_main_menu_actions.redo_action.trigger.side_effect = mock_command_manager.redo

    mock_main_menu_actions.cut_action = MagicMock(spec=QAction)
    mock_main_menu_actions.copy_action = MagicMock(spec=QAction)
    mock_main_menu_actions.paste_action = MagicMock(spec=QAction)
    mock_main_menu_actions.colors_action = MagicMock(spec=QAction)
    mock_main_menu_actions.settings_action = MagicMock(spec=QAction)
    mock_tool_bar = QToolBar()
    mock_tool_bar_actions = MagicMock(spec=ToolBarActions)

    main_window = MainWindow(
        model,
        mock_main_controller,
        mock_command_manager,
        plot_types,
        menu_bar=mock_menu_bar,
        main_menu_actions=mock_main_menu_actions,
        tool_bar=mock_tool_bar,
        tool_bar_actions=mock_tool_bar_actions,
    )

    qtbot.addWidget(main_window)
    main_window.show()
    qtbot.waitExposed(main_window)

    return {
        "window": main_window,
        "model": model,
        "command_manager": mock_command_manager,
        "main_controller": mock_main_controller,
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
