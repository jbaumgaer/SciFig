import pytest
from unittest.mock import MagicMock, patch
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import QToolBar

from src.ui.builders.tool_bar_builder import ToolBarBuilder, ToolBarActions
from src.shared.events import Events
from src.shared.constants import ToolName


@pytest.fixture
def mock_icon_path():
    """Mock IconPath to avoid file system access."""
    with patch("src.ui.builders.tool_bar_builder.IconPath") as mock:
        mock.get_path.side_effect = lambda key: f"path/to/{key}.svg"
        yield mock


@pytest.fixture
def toolbar_builder(mock_tool_manager, mock_event_aggregator, mock_icon_path):
    """Provides a ToolBarBuilder instance."""
    # Setup mock_tool_manager for toolbar requirements
    mock_tool = MagicMock()
    mock_tool.name = ToolName.SELECTION.value
    mock_tool_manager.active_tool = mock_tool
    
    return ToolBarBuilder(mock_tool_manager, mock_event_aggregator)


class TestToolBarBuilder:
    """
    Unit tests for ToolBarBuilder.
    Verifies the construction of the tool bar and its interaction with ToolService.
    """

    def test_build_returns_toolbar_and_actions(self, toolbar_builder, qtbot):
        """Verifies that build() returns expected types and populated container."""
        toolbar, actions = toolbar_builder.build()
        
        assert isinstance(toolbar, QToolBar)
        assert isinstance(actions, ToolBarActions)
        
        # Verify all actions are QActions and checkable
        for field_name in ToolBarActions.__annotations__.keys():
            action = getattr(actions, field_name)
            assert isinstance(action, QAction)
            assert action.isCheckable()

    def test_build_subscribes_to_active_tool_changed(self, toolbar_builder, mock_event_aggregator, qtbot):
        """Verifies that the builder subscribes to the tool change event."""
        toolbar_builder.build()
        
        mock_event_aggregator.subscribe.assert_called_with(
            Events.ACTIVE_TOOL_CHANGED, 
            toolbar_builder._update_tool_bar_state
        )

    def test_action_trigger_calls_tool_service(self, toolbar_builder, mock_tool_manager, qtbot):
        """Verifies that clicking a toolbar action sets the active tool in the service."""
        _, actions = toolbar_builder.build()
        
        # Trigger 'plot' action
        actions.plot.trigger()
        
        mock_tool_manager.set_active_tool.assert_called_with(ToolName.PLOT)

    def test_update_tool_bar_state_updates_checked_action(self, toolbar_builder, qtbot):
        """Verifies that _update_tool_bar_state correctly sets the checked state."""
        _, actions = toolbar_builder.build()
        
        # Initially selection should be checked (set in fixture)
        assert actions.selection.isChecked()
        assert not actions.zoom.isChecked()
        
        # Update state to ZOOM
        toolbar_builder._update_tool_bar_state(ToolName.ZOOM.value)
        
        assert actions.zoom.isChecked()
        assert not actions.selection.isChecked()

    def test_initial_state_matches_service_active_tool(self, toolbar_builder, mock_tool_manager, qtbot):
        """Verifies that the toolbar state is initialized correctly from the service."""
        mock_tool_manager.active_tool.name = ToolName.TEXT.value
        
        _, actions = toolbar_builder.build()
        
        assert actions.text.isChecked()
        assert not actions.selection.isChecked()

    def test_build_handles_no_active_tool(self, toolbar_builder, mock_tool_manager, qtbot):
        """Verifies that build() handles the case where active_tool is None without crashing."""
        mock_tool_manager.active_tool = None
        
        # Should not raise AttributeError
        toolbar, actions = toolbar_builder.build()
        assert isinstance(toolbar, QToolBar)
        
        # Verify nothing is checked
        for field_name in ToolBarActions.__annotations__.keys():
            action = getattr(actions, field_name)
            assert not action.isChecked()
