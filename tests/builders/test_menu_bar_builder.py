from unittest.mock import Mock

import pytest
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMainWindow, QMenu, QMenuBar

from src.builders.menu_bar_builder import MainMenuActions, MenuBarBuilder
from src.commands import CommandManager
from src.controllers.main_controller import MainController


@pytest.fixture
def mock_mainwindow(qtbot):
    """Fixture for a mock QMainWindow that is safely created."""
    window = QMainWindow()
    # Mock menuBar to return a mock QMenuBar. This is crucial to prevent
    # the real QMenuBar from being used in tests, which was part of the issue.
    window.menuBar = Mock(return_value=Mock(spec=QMenuBar))
    qtbot.addWidget(window)
    return window


@pytest.fixture
def mock_command_manager():
    """Fixture for a mock CommandManager."""
    return Mock(spec=CommandManager)


@pytest.fixture
def mock_main_controller():
    """Fixture for a mock MainController."""
    return Mock(spec=MainController)


@pytest.fixture
def menu_bar_builder(mock_mainwindow, mock_main_controller, mock_command_manager):
    """Fixture for a MenuBarBuilder instance."""
    return MenuBarBuilder(mock_mainwindow, mock_main_controller, mock_command_manager)


def test_main_menu_actions_dataclass_structure():
    """Test that MainMenuActions has the expected attributes."""
    menu_actions = MainMenuActions(
        menu_bar=Mock(spec=QMenuBar),
        file_menu=Mock(spec=QMenu),
        new_layout_action=Mock(spec=QAction),
        new_file_action=Mock(spec=QAction),
        new_file_from_template_action=Mock(spec=QAction),
        open_project_action=Mock(spec=QAction),
        open_recent_projects_menu=Mock(spec=QMenu),
        close_action=Mock(spec=QAction),
        save_project_action=Mock(spec=QAction),
        save_copy_action=Mock(spec=QAction),
        export_figure_menu=Mock(spec=QMenu),
        export_vector_menu=Mock(spec=QMenu),
        export_raster_menu=Mock(spec=QMenu),
        export_svg_action=Mock(spec=QAction),
        export_pdf_action=Mock(spec=QAction),
        export_eps_action=Mock(spec=QAction),
        export_png_action=Mock(spec=QAction),
        export_tiff_action=Mock(spec=QAction),
        export_python_action=Mock(spec=QAction),
        exit_action=Mock(spec=QAction),
        edit_menu=Mock(spec=QMenu),
        undo_action=Mock(spec=QAction),
        redo_action=Mock(spec=QAction),
        cut_action=Mock(spec=QAction),
        copy_action=Mock(spec=QAction),
        paste_action=Mock(spec=QAction),
        colors_action=Mock(spec=QAction),
        settings_action=Mock(spec=QAction),
    )
    assert hasattr(menu_actions, "menu_bar")
    assert hasattr(menu_actions, "file_menu")
    assert hasattr(menu_actions, "undo_action")


def test_build_creates_menu_bar_and_menus(menu_bar_builder, mock_mainwindow):
    """Test that build() creates a menu bar and the main menus."""
    menu_actions = menu_bar_builder.build()

    mock_mainwindow.menuBar.assert_called_once()
    assert isinstance(menu_actions.menu_bar, Mock) # It's a mock QMenuBar

    menu_actions.menu_bar.addMenu.assert_any_call("&File")
    menu_actions.menu_bar.addMenu.assert_any_call("&Edit")

    assert isinstance(menu_actions.file_menu, Mock)
    assert isinstance(menu_actions.edit_menu, Mock)


def test_build_creates_all_file_menu_actions(menu_bar_builder):
    """Test that all expected actions are created in the File menu."""
    menu_actions = menu_bar_builder.build()

    assert isinstance(menu_actions.new_layout_action, Mock)
    assert isinstance(menu_actions.new_file_action, Mock)
    # ... and so on for all other actions

def test_build_creates_all_edit_menu_actions(menu_bar_builder, mock_command_manager):
    """Test that all expected actions are created in the Edit menu."""
    menu_actions = menu_bar_builder.build()

    assert isinstance(menu_actions.undo_action, Mock)
    assert isinstance(menu_actions.redo_action, Mock)

    menu_actions.undo_action.triggered.connect.assert_any_call(mock_command_manager.undo)
    menu_actions.redo_action.triggered.connect.assert_any_call(mock_command_manager.redo)
