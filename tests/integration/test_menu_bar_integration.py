import pytest
from unittest.mock import MagicMock
from PySide6.QtWidgets import QApplication
from PySide6 import QtCore

from src.ui.builders.menu_bar_builder import MenuBarBuilder
from src.controllers.project_controller import ProjectController
from src.services.commands.command_manager import CommandManager
from src.controllers.layout_controller import LayoutController


@pytest.fixture(scope="function")
def integration_menu_bar_builder(real_project_controller, real_layout_controller, real_command_manager):
    """Provides a MenuBarBuilder instance with real controllers for integration tests."""
    return MenuBarBuilder(real_project_controller, real_layout_controller, real_command_manager)

@pytest.fixture(scope="function")
def real_project_controller():
    """Provides a real ProjectController instance with mocked dependencies for integration tests."""
    mock_app_model = MagicMock() # Mock ApplicationModel
    mock_config_service = MagicMock() # Mock ConfigService
    mock_command_manager = MagicMock() # Mock CommandManager
    mock_layout_manager = MagicMock() # Mock LayoutManager
    
    # Configure mock_config_service.get to return appropriate string values for ProjectController's init
    mock_config_service.get.side_effect = lambda key, default=None: {
        "organization": "TestOrg",
        "app_name": "TestApp",
        "layout.max_recent_files": 5,
    }.get(key, default)

    controller = ProjectController(mock_app_model, mock_command_manager, mock_config_service , mock_layout_manager)
    
    # Replace the real QSettings with a MagicMock for testing
    mock_qsettings = MagicMock()
    mock_qsettings.value.side_effect = lambda key, default=None: {
        "recentFiles": [], # Default empty list for recent files
        "organization": "TestOrg", # Ensure these are available if controller.settings.value is called for them
        "app_name": "TestApp",
    }.get(key, default)
    mock_qsettings.setValue = MagicMock() # Mock setValue as well

    controller.settings = mock_qsettings

    # Mocking internal methods that might interact with file system
    controller._save_project_to_file = MagicMock()
    controller._load_project_from_file = MagicMock()
    controller._get_open_file_name = MagicMock(return_value="test_project.json")
    controller._get_save_file_name = MagicMock(return_value="test_project_save.json")
    
    # Mock the methods that will be called for assertions
    controller.create_new_layout = MagicMock()
    controller.open_project = MagicMock()
    controller.save_project = MagicMock()

    return controller

@pytest.fixture(scope="function")
def real_layout_controller():
    """Provides a real LayoutController instance with mocked dependencies for integration tests."""
    mock_app_model = MagicMock()
    mock_command_manager = MagicMock()
    mock_layout_manager = MagicMock()
    return LayoutController(mock_app_model, mock_command_manager, mock_layout_manager)

@pytest.fixture(scope="session", autouse=True)
def qapp():
    """Ensure a QApplication is available for tests that need it."""
    app = QApplication.instance()
    if not app:
        app = QApplication([])
    yield app
    app.quit()


def test_file_menu_actions_trigger_project_controller_methods(integration_menu_bar_builder, real_project_controller, qapp, qtbot):
    """
    Test that clicking file menu actions correctly triggers corresponding methods
    in the ProjectController.
    """
    # Arrange
    menu_bar, menu_actions = integration_menu_bar_builder.build()

    # Act & Assert
    # Test new_layout_action
    menu_actions.new_layout_action.triggered.emit()
    real_project_controller.create_new_layout.assert_called_once()
    real_project_controller.create_new_layout.reset_mock()

    # Test open_project_action
    menu_actions.open_project_action.triggered.emit()
    real_project_controller.open_project.assert_called_once()
    real_project_controller.open_project.reset_mock()

    # Test save_project_action
    menu_actions.save_project_action.triggered.emit()
    real_project_controller.save_project.assert_called_once()
    real_project_controller.save_project.reset_mock()


def test_edit_menu_actions_trigger_command_manager_methods(integration_menu_bar_builder, real_command_manager, qapp, qtbot, mocker):
    """
    Test that clicking edit menu actions correctly triggers corresponding methods
    in the CommandManager.
    """
    # Arrange
    # Patch the real CommandManager's methods before building the menu
    mock_undo = mocker.patch.object(real_command_manager, 'undo', autospec=True)
    mock_redo = mocker.patch.object(real_command_manager, 'redo', autospec=True)

    menu_bar, menu_actions = integration_menu_bar_builder.build()

    # Act & Assert
    # Test undo_action
    menu_actions.undo_action.triggered.emit()
    mock_undo.assert_called_once()
    mock_undo.reset_mock()

    # Test redo_action
    menu_actions.redo_action.triggered.emit()
    mock_redo.assert_called_once()
    mock_redo.reset_mock()


def test_open_recent_projects_menu_updates(integration_menu_bar_builder, real_project_controller, qapp, qtbot):
    """
    Test that the 'Open Recent Projects' menu updates dynamically based on the ProjectController's
    recent files list.
    """
    # Arrange
    initial_files = ["/path/to/old_file1.project", "/path/to/old_file2.project"]
    
    # Configure the side_effect for settings.value to return initial_files when RECENT_FILES_KEY is queried
    real_project_controller.settings.value.side_effect = lambda key, default=None: \
        initial_files if key == "recentFiles" else default

    menu_bar, menu_actions = integration_menu_bar_builder.build()
    recent_projects_menu = menu_actions.open_recent_projects_menu

    # Act 1: Show menu with initial files
    recent_projects_menu.aboutToShow.emit()
    assert len(recent_projects_menu.actions()) == len(initial_files)
    assert recent_projects_menu.actions()[0].text() == initial_files[0]

    # Change recent files
    updated_files = ["/path/to/new_file1.project", "/path/to/new_file2.project", "/path/to/new_file3.project"]
    # Update the side_effect for settings.value to return updated_files
    real_project_controller.settings.value.side_effect = lambda key, default=None: \
        updated_files if key == "recentFiles" else default

    # Act 2: Show menu again to trigger update
    recent_projects_menu.aboutToShow.emit()

    # Assert
    assert len(recent_projects_menu.actions()) == len(updated_files)
    assert recent_projects_menu.actions()[0].text() == updated_files[0]
    assert recent_projects_menu.actions()[1].text() == updated_files[1]

    # Verify clicking an updated recent file triggers open_project
    recent_projects_menu.actions()[0].triggered.emit()
    real_project_controller.open_project.assert_called_once_with(updated_files[0])

