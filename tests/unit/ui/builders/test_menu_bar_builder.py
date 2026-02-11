from unittest.mock import Mock

import pytest
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import QMenu, QMenuBar

from src.ui.builders.menu_bar_builder import MainMenuActions, MenuBarBuilder


@pytest.fixture
def menu_bar_builder(mock_project_controller, mock_layout_controller, mock_command_manager):
    """Fixture for a MenuBarBuilder instance."""
    return MenuBarBuilder(mock_project_controller, mock_layout_controller, mock_command_manager)

class TestMenuBarBuilder:
    def test_main_menu_actions_dataclass_structure(self):
        """Test that MainMenuActions has the expected attributes."""
        # Create mock QAction and QMenu instances for all attributes
        mock_objects = {field_name: Mock(spec=QAction if "action" in field_name else QMenu) 
                        for field_name in MainMenuActions.__annotations__.keys()}
        
        menu_actions = MainMenuActions(**mock_objects)

        # Dynamically check that all attributes defined in the dataclass are present
        for field_name in MainMenuActions.__annotations__.keys():
            assert hasattr(menu_actions, field_name), f"MainMenuActions is missing attribute: {field_name}"


    def test_build_creates_menu_bar_and_menus(self, menu_bar_builder, qtbot):
        """Test that build() creates a menu bar and the main menus."""
        menu_bar, menu_actions = menu_bar_builder.build()

        assert isinstance(menu_bar, QMenuBar)

        assert isinstance(menu_actions.file_menu, QMenu)
        assert menu_actions.file_menu.title() == "&File"

        assert isinstance(menu_actions.edit_menu, QMenu)
        assert menu_actions.edit_menu.title() == "&Edit"


    def test_build_creates_all_file_menu_actions(self, menu_bar_builder):
        """Test that all expected actions are created in the File menu."""
        _, menu_actions = menu_bar_builder.build()

        file_menu_action_attributes = [
            "new_layout_action",
            "new_file_action",
            "new_file_from_template_action",
            "open_project_action",
            "close_action",
            "save_project_action",
            "save_copy_action",
            "export_svg_action",
            "export_pdf_action",
            "export_eps_action",
            "export_png_action",
            "export_tiff_action",
            "export_python_action",
            "exit_action",
        ]

        for attr_name in file_menu_action_attributes:
            action = getattr(menu_actions, attr_name)
            assert isinstance(action, QAction), f"Attribute {attr_name} is not a QAction"


    def test_build_creates_all_edit_menu_actions(self, menu_bar_builder):
        """Test that all expected actions are created in the Edit menu."""
        _, menu_actions = menu_bar_builder.build()

        edit_menu_action_attributes = [
            "undo_action",
            "redo_action",
            "cut_action",
            "copy_action",
            "paste_action",
            "colors_action",
            "settings_action",
        ]

        for attr_name in edit_menu_action_attributes:
            action = getattr(menu_actions, attr_name)
            assert isinstance(action, QAction), f"Attribute {attr_name} is not a QAction"

    def test_menu_bar_builder_constructor_stores_dependencies(self, mock_project_controller, mock_layout_controller, mock_command_manager):
        """Test that the MenuBarBuilder constructor correctly stores its dependencies."""
        builder = MenuBarBuilder(mock_project_controller, mock_layout_controller, mock_command_manager)

        assert builder._project_controller is mock_project_controller
        assert builder._layout_controller is mock_layout_controller
        assert builder._command_manager is mock_command_manager

    def test_build_file_menu_actions_and_shortcuts(self, menu_bar_builder):
        """Test that all file menu actions are created with correct text and shortcuts."""
        expected_actions_data = [
            ("new_layout_action", "&New Layout...", None), # No standard shortcut for this
            ("new_file_action", "&New File...", QKeySequence.StandardKey.New),
            ("new_file_from_template_action", "New File from &Template...", QKeySequence("Shift+Ctrl+N")),
            ("open_project_action", "&Open Project...", QKeySequence.StandardKey.Open),
            ("close_action", "&Close", QKeySequence("Ctrl+W")),
            ("save_project_action", "&Save Project", QKeySequence.StandardKey.Save),
            ("save_copy_action", "Save a &Copy...", QKeySequence.StandardKey.SaveAs),
            ("export_svg_action", "SVG...", None),
            ("export_pdf_action", "PDF...", None),
            ("export_eps_action", "EPS...", None),
            ("export_png_action", "PNG...", None),
            ("export_tiff_action", "TIFF...", None),
            ("export_python_action", "Python...", None),
            ("exit_action", "&Exit", QKeySequence.StandardKey.Quit),
        ]

        _, menu_actions = menu_bar_builder.build()

        for attr_name, expected_text, expected_shortcut in expected_actions_data:
            action = getattr(menu_actions, attr_name)
            assert isinstance(action, QAction), f"Attribute {attr_name} is not a QAction"
            assert action.text() == expected_text, f"Action {attr_name} has incorrect text"
            if expected_shortcut:
                assert action.shortcut() == expected_shortcut, f"Action {attr_name} has incorrect shortcut"

    def test_build_file_menu_structure(self, menu_bar_builder):
        """Test the hierarchical structure of the file menu."""
        _, menu_actions = menu_bar_builder.build()

        # Check main File menu
        assert isinstance(menu_actions.file_menu, QMenu)
        assert menu_actions.file_menu.title() == "&File"

        # Check Open Recent Projects sub-menu
        assert isinstance(menu_actions.open_recent_projects_menu, QMenu)
        assert menu_actions.open_recent_projects_menu.title() == "Open &Recent Projects"
        assert menu_actions.open_recent_projects_menu.parent() == menu_actions.file_menu

        # Check Export Figure sub-menu
        assert isinstance(menu_actions.export_figure_menu, QMenu)
        assert menu_actions.export_figure_menu.title() == "&Export Figure"
        assert menu_actions.export_figure_menu.parent() == menu_actions.file_menu

        # Check Vector Export sub-menu
        assert isinstance(menu_actions.export_vector_menu, QMenu)
        assert menu_actions.export_vector_menu.title() == "&Vector"
        assert menu_actions.export_vector_menu.parent() == menu_actions.export_figure_menu

        # Check Raster Export sub-menu
        assert isinstance(menu_actions.export_raster_menu, QMenu)
        assert menu_actions.export_raster_menu.title() == "&Raster"
        assert menu_actions.export_raster_menu.parent() == menu_actions.export_figure_menu

    def test_file_menu_action_connections(self, menu_bar_builder, mock_project_controller, qtbot):
        """Test that file menu actions are connected to the correct ProjectController methods."""
        _, menu_actions = menu_bar_builder.build()

        # Test new_layout_action
        menu_actions.new_layout_action.triggered.emit()
        mock_project_controller.create_new_layout.assert_called_once()
        mock_project_controller.create_new_layout.reset_mock() # Reset for next assertion

        # Test open_project_action
        menu_actions.open_project_action.triggered.emit()
        mock_project_controller.open_project.assert_called_once()
        mock_project_controller.open_project.reset_mock()

        # Test save_project_action
        menu_actions.save_project_action.triggered.emit()
        mock_project_controller.save_project.assert_called_once()
        mock_project_controller.save_project.reset_mock()

    def test_build_edit_menu_actions_and_shortcuts(self, menu_bar_builder):
        """Test that all edit menu actions are created with correct text and shortcuts."""
        expected_actions_data = [
            ("undo_action", "&Undo", QKeySequence.StandardKey.Undo),
            ("redo_action", "&Redo", QKeySequence.StandardKey.Redo),
            ("cut_action", "Cu&t", QKeySequence.StandardKey.Cut),
            ("copy_action", "&Copy", QKeySequence.StandardKey.Copy),
            ("paste_action", "&Paste", QKeySequence.StandardKey.Paste),
            ("colors_action", "&Colors...", QKeySequence("Ctrl+Shift+C")),
            ("settings_action", "&Settings...", QKeySequence("Ctrl+,")),
        ]

        _, menu_actions = menu_bar_builder.build()

        for attr_name, expected_text, expected_shortcut in expected_actions_data:
            action = getattr(menu_actions, attr_name)
            assert isinstance(action, QAction), f"Attribute {attr_name} is not a QAction"
            assert action.text() == expected_text, f"Action {attr_name} has incorrect text"
            if expected_shortcut:
                assert action.shortcut() == expected_shortcut, f"Action {attr_name} has incorrect shortcut"

    def test_edit_menu_action_connections(self, menu_bar_builder, mock_command_manager, qtbot):
        """Test that edit menu actions are connected to the correct CommandManager methods."""
        _, menu_actions = menu_bar_builder.build()

        # Test undo_action
        menu_actions.undo_action.triggered.emit()
        mock_command_manager.undo.assert_called_once()
        mock_command_manager.undo.reset_mock()

        # Test redo_action
        menu_actions.redo_action.triggered.emit()
        mock_command_manager.redo.assert_called_once()
        mock_command_manager.redo.reset_mock()


    def test_update_recent_projects_menu_with_files(self, menu_bar_builder, mock_project_controller, qtbot):
        """Test that the 'Open Recent Projects' menu is correctly populated with recent files
        and their actions are connected."""
        test_files = ["/path/to/file1.project", "/path/to/file2.project"]
        mock_project_controller.get_recent_files.return_value = test_files

        _, menu_actions = menu_bar_builder.build()
        recent_projects_menu = menu_actions.open_recent_projects_menu
        
        # Simulate the menu being shown to trigger _update_recent_projects_menu
        recent_projects_menu.aboutToShow.emit() 

        # Check that the menu was cleared and repopulated
        assert len(recent_projects_menu.actions()) == len(test_files)
        mock_project_controller.get_recent_files.assert_called_once()

        for i, file_path in enumerate(test_files):
            action = recent_projects_menu.actions()[i]
            assert action.text() == file_path
            
            # Simulate clicking the action and verify the connection
            action.triggered.emit()
            mock_project_controller.open_project.assert_called_once_with(file_path)
            mock_project_controller.open_project.reset_mock()


    def test_update_recent_projects_menu_no_files(self, menu_bar_builder, mock_project_controller):
        """Test that the 'Open Recent Projects' menu displays 'No Recent Projects' when
        there are no recent files."""
        mock_project_controller.get_recent_files.return_value = []

        _, menu_actions = menu_bar_builder.build()
        recent_projects_menu = menu_actions.open_recent_projects_menu

        # Simulate the menu being shown to trigger _update_recent_projects_menu
        recent_projects_menu.aboutToShow.emit()

        assert len(recent_projects_menu.actions()) == 1
        no_recent_action = recent_projects_menu.actions()[0]
        assert no_recent_action.text() == "No Recent Projects"
        assert not no_recent_action.isEnabled()
        mock_project_controller.get_recent_files.assert_called_once()


    def test_build_returns_menu_bar_and_main_menu_actions(self, menu_bar_builder):
        """Test that the build method returns both a QMenuBar and a fully populated MainMenuActions instance."""
        menu_bar, menu_actions = menu_bar_builder.build()

        assert isinstance(menu_bar, QMenuBar)
        assert isinstance(menu_actions, MainMenuActions)

        # Verify that all attributes in MainMenuActions are populated
        for field_name in MainMenuActions.__annotations__.keys():
            attribute = getattr(menu_actions, field_name)
            assert attribute is not None, f"MainMenuActions attribute {field_name} was not populated."
            if "menu" in field_name:
                assert isinstance(attribute, QMenu), f"Attribute {field_name} is not a QMenu"
            elif "action" in field_name:
                assert isinstance(attribute, QAction), f"Attribute {field_name} is not a QAction"
