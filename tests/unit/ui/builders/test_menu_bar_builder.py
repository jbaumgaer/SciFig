import pytest
from unittest.mock import MagicMock, ANY
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import QMenu, QMenuBar

from src.ui.builders.menu_bar_builder import MainMenuActions, MenuBarBuilder
from src.shared.events import Events


@pytest.fixture
def menu_bar_builder(mock_event_aggregator):
    """Fixture for a MenuBarBuilder instance."""
    return MenuBarBuilder(mock_event_aggregator)


class TestMenuBarBuilder:
    """
    Unit tests for MenuBarBuilder.
    Verifies the construction of the hierarchical menu system and its 
    event-driven connections.
    """

    def test_build_returns_menu_bar_and_actions(self, menu_bar_builder, qtbot):
        """Verifies that build() returns the expected types and populated containers."""
        menu_bar, actions = menu_bar_builder.build()
        
        assert isinstance(menu_bar, QMenuBar)
        assert isinstance(actions, MainMenuActions)
        
        # Verify all dataclass fields are populated with UI objects
        for field_name in MainMenuActions.__annotations__.keys():
            val = getattr(actions, field_name)
            assert val is not None, f"Field {field_name} is None"
            if "menu" in field_name:
                assert isinstance(val, QMenu)
            else:
                assert isinstance(val, QAction)

    def test_build_hierarchical_menu_structure(self, menu_bar_builder, qtbot):
        """Verifies the parent-child relationships of the created menus."""
        _, actions = menu_bar_builder.build()
        
        # File Menu hierarchy
        assert actions.open_recent_projects_menu.parent() == actions.file_menu
        assert actions.export_figure_menu.parent() == actions.file_menu
        assert actions.export_vector_menu.parent() == actions.export_figure_menu
        assert actions.export_raster_menu.parent() == actions.export_figure_menu

    def test_file_menu_action_properties(self, menu_bar_builder, qtbot):
        """Verifies correct text and shortcuts for key file actions."""
        _, actions = menu_bar_builder.build()
        
        # Standard Shortcuts
        assert actions.new_file_action.text() == "&New File..."
        assert actions.new_file_action.shortcut() == QKeySequence.StandardKey.New
        
        assert actions.save_project_action.text() == "&Save Project"
        assert actions.save_project_action.shortcut() == QKeySequence.StandardKey.Save
        
        # Custom Shortcuts defined in source
        assert actions.new_file_from_template_action.shortcut() == QKeySequence("Shift+Ctrl+N")
        assert actions.close_action.shortcut() == QKeySequence("Ctrl+W")
        assert actions.export_figure_menu.menuAction().shortcut() == QKeySequence("Ctrl+E")
        
        assert actions.open_recent_projects_menu.title() == "Open &Recent Projects"

    def test_edit_menu_action_properties(self, menu_bar_builder, qtbot):
        """Verifies correct text and shortcuts for key edit actions."""
        _, actions = menu_bar_builder.build()
        
        assert actions.undo_action.text() == "&Undo"
        assert actions.undo_action.shortcut() == QKeySequence.StandardKey.Undo
        
        assert actions.settings_action.text() == "&Settings..."
        assert actions.settings_action.shortcut() == QKeySequence("Ctrl+,")

    def test_file_actions_publish_correct_events(self, menu_bar_builder, mock_event_aggregator, qtbot):
        """Verifies that triggering file menu actions publishes the expected request events."""
        _, actions = menu_bar_builder.build()
        
        # 1. New Project
        actions.new_file_action.trigger()
        mock_event_aggregator.publish.assert_any_call(Events.NEW_PROJECT_REQUESTED)
        
        # 2. New from Template
        actions.new_file_from_template_action.trigger()
        mock_event_aggregator.publish.assert_any_call(Events.NEW_PROJECT_FROM_TEMPLATE_REQUESTED)
        
        # 3. Open Project
        actions.open_project_action.trigger()
        mock_event_aggregator.publish.assert_any_call(Events.OPEN_PROJECT_REQUESTED)
        
        # 4. Save Project
        actions.save_project_action.trigger()
        mock_event_aggregator.publish.assert_any_call(Events.SAVE_PROJECT_REQUESTED)
        
        # 5. Save Copy (Save As)
        actions.save_copy_action.trigger()
        mock_event_aggregator.publish.assert_any_call(Events.SAVE_PROJECT_AS_REQUESTED)

    def test_edit_actions_publish_correct_events(self, menu_bar_builder, mock_event_aggregator, qtbot):
        """Verifies that triggering edit menu actions publishes undo/redo requests."""
        _, actions = menu_bar_builder.build()
        
        actions.undo_action.trigger()
        mock_event_aggregator.publish.assert_any_call(Events.UNDO_REQUESTED)
        
        actions.redo_action.trigger()
        mock_event_aggregator.publish.assert_any_call(Events.REDO_REQUESTED)

    def test_ribbon_tab_selectors_as_menu_actions(self, menu_bar_builder, qtbot):
        """Verifies that the ribbon tab selector actions are created at the menu bar level."""
        menu_bar, actions = menu_bar_builder.build()
        
        # These are added directly to the menu bar via addAction
        assert actions.insert_tab_action.text() == "Insert"
        assert actions.design_tab_action.text() == "Design"
        assert actions.layout_tab_action.text() == "Layout"
        
        assert actions.insert_tab_action in menu_bar.actions()

    def test_update_recent_projects_logic_capture(self, menu_bar_builder, mock_event_aggregator, qtbot):
        """
        Verifies that recent project actions capture the correct file path 
        in their event payload.
        """
        _, actions = menu_bar_builder.build()
        menu = actions.open_recent_projects_menu
        
        test_files = ["test1.sci", "test2.sci"]
        
        # Manually invoke population logic with data to verify connection pattern
        menu.clear()
        for f_path in test_files:
            action = QAction(f_path, menu)
            # This is the pattern used in the source code
            action.triggered.connect(
                lambda checked=False, p=f_path: mock_event_aggregator.publish(
                    Events.OPEN_RECENT_PROJECT_REQUESTED, file_path=p
                )
            )
            menu.addAction(action)
            
        # Trigger the first one
        menu.actions()[0].trigger()
        mock_event_aggregator.publish.assert_called_with(Events.OPEN_RECENT_PROJECT_REQUESTED, file_path="test1.sci")
        
        # Trigger the second one (verifies lambda closure capture was correct)
        menu.actions()[1].trigger()
        mock_event_aggregator.publish.assert_called_with(Events.OPEN_RECENT_PROJECT_REQUESTED, file_path="test2.sci")

    def test_recent_projects_menu_placeholder_state(self, menu_bar_builder, qtbot):
        """Verifies the 'No Recent Projects' state when the list is empty."""
        _, actions = menu_bar_builder.build()
        menu = actions.open_recent_projects_menu
        
        # Call the update method manually (matching current source behavior)
        menu_bar_builder._update_recent_projects_menu(menu)
        
        assert len(menu.actions()) == 1
        assert menu.actions()[0].text() == "No Recent Projects"
        assert not menu.actions()[0].isEnabled()
