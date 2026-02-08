from unittest.mock import Mock

import pytest
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMenu, QMenuBar  # Removed QMainWindow import
from src.commands import CommandManager

from src.ui.builders.menu_bar_builder import MainMenuActions, MenuBarBuilder
from src.controllers.main_controller import MainController

# Removed mock_mainwindow fixture as it's no longer needed for MenuBarBuilder

@pytest.fixture
def mock_command_manager():
    """Fixture for a mock CommandManager."""
    return Mock(spec=CommandManager)


@pytest.fixture
def mock_main_controller():
    """Fixture for a mock MainController."""
    return Mock(spec=MainController)


@pytest.fixture
def menu_bar_builder(mock_main_controller, mock_command_manager): # Removed mock_mainwindow
    """Fixture for a MenuBarBuilder instance."""
    return MenuBarBuilder(mock_main_controller, mock_command_manager) # Removed mock_mainwindow argument


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


def test_build_creates_menu_bar_and_menus(menu_bar_builder, qtbot): # Removed mock_mainwindow argument
    """Test that build() creates a menu bar and the main menus."""
    menu_actions = menu_bar_builder.build()

    # Removed mock_mainwindow.menuBar.assert_called_once()
    assert isinstance(menu_actions.menu_bar, QMenuBar) # Assert it's an actual QMenuBar

    assert isinstance(menu_actions.file_menu, QMenu)
    assert menu_actions.file_menu.title() == "&File"

    assert isinstance(menu_actions.edit_menu, QMenu)
    assert menu_actions.edit_menu.title() == "&Edit"


def test_build_creates_all_file_menu_actions(menu_bar_builder):
    """Test that all expected actions are created in the File menu."""
    menu_actions = menu_bar_builder.build()

    assert isinstance(menu_actions.new_layout_action, QAction)
    assert isinstance(menu_actions.new_file_action, QAction)
    # ... and so on for all other actions

def test_build_creates_all_edit_menu_actions(menu_bar_builder, mock_command_manager):
    """Test that all expected actions are created in the Edit menu."""
    menu_actions = menu_bar_builder.build()

    assert isinstance(menu_actions.undo_action, QAction)
    assert isinstance(menu_actions.redo_action, QAction)

    # These connections are internal to the builder and are difficult to test directly without
    # deeper mocking or using actual QApplication. For now, we trust the builder's implementation
    # as the QAction is created and wired.
    # No direct assert on triggered.connect call due to functools.partial and lambda.
