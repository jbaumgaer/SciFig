import pytest
from unittest.mock import MagicMock, ANY
from src.services.tool_service import ToolService
from src.services.tools.base_tool import BaseTool
from src.shared.events import Events


class MockTool(BaseTool):
    """A concrete mock tool for testing."""
    def __init__(self, name="mock_tool"):
        # We bypass BaseTool.__init__ complexity for simple registration tests
        self._name = name
        self.on_activated = MagicMock()
        self.on_deactivated = MagicMock()
        self.mouse_press_event = MagicMock()
        self.mouse_move_event = MagicMock()
        self.mouse_release_event = MagicMock()

    @property
    def name(self) -> str:
        return self._name

    @property
    def icon_path(self) -> str:
        return ""


@pytest.fixture
def tool_service(mock_event_aggregator):
    """Provides a ToolService instance with mocked event aggregator."""
    return ToolService(event_aggregator=mock_event_aggregator)


class TestToolService:

    def test_add_tool(self, tool_service):
        """Tests tool registration."""
        tool = MockTool("tool1")
        tool_service.add_tool(tool)
        assert tool_service._tools["tool1"] is tool

    def test_add_duplicate_tool_raises_error(self, tool_service):
        """Ensures unique tool names."""
        tool_service.add_tool(MockTool("dup"))
        with pytest.raises(ValueError, match="already exists"):
            tool_service.add_tool(MockTool("dup"))

    def test_set_active_tool_lifecycle_and_events(self, tool_service, mock_event_aggregator):
        """Verifies tool switching triggers lifecycle methods and events."""
        t1 = MockTool("t1")
        t2 = MockTool("t2")
        tool_service.add_tool(t1)
        tool_service.add_tool(t2)
        
        # 1. Activate T1
        tool_service.set_active_tool("t1")
        assert tool_service.active_tool is t1
        t1.on_activated.assert_called_once()
        mock_event_aggregator.publish.assert_any_call(Events.ACTIVE_TOOL_CHANGED, tool_name="t1")
        
        # 2. Switch to T2
        tool_service.set_active_tool("t2")
        assert tool_service.active_tool is t2
        t1.on_deactivated.assert_called_once()
        t2.on_activated.assert_called_once()
        mock_event_aggregator.publish.assert_any_call(Events.ACTIVE_TOOL_CHANGED, tool_name="t2")

    def test_set_active_tool_idempotency(self, tool_service, mock_event_aggregator):
        """Ensures setting the same tool twice does nothing."""
        t1 = MockTool("t1")
        tool_service.add_tool(t1)
        tool_service.set_active_tool("t1")
        
        mock_event_aggregator.publish.reset_mock()
        t1.on_activated.reset_mock()
        
        # Set again
        tool_service.set_active_tool("t1")
        
        t1.on_activated.assert_not_called()
        mock_event_aggregator.publish.assert_not_called()

    def test_dispatch_events_proxies_to_active_tool(self, tool_service):
        """Verifies that events are correctly forwarded to the active tool."""
        tool = MockTool("t1")
        tool_service.add_tool(tool)
        tool_service.set_active_tool("t1")
        
        coords = (0.5, 0.5)
        mods = "shift"
        
        # Mouse Press
        tool_service.dispatch_mouse_press_event("node1", coords, 1, modifiers=mods)
        tool.mouse_press_event.assert_called_once_with("node1", coords, 1, mods)
        
        # Mouse Move
        tool_service.dispatch_mouse_move_event(coords, modifiers=mods)
        tool.mouse_move_event.assert_called_once_with(coords, mods)
        
        # Mouse Release
        tool_service.dispatch_mouse_release_event(coords, modifiers=mods)
        tool.mouse_release_event.assert_called_once_with(coords, mods)

    def test_dispatch_events_no_active_tool_is_safe(self, tool_service):
        """Ensures no crash if events are dispatched without an active tool."""
        # Should just return without error
        tool_service.dispatch_mouse_press_event(None, (0,0), 1)
        tool_service.dispatch_mouse_move_event((0,0))

    def test_set_unknown_tool_raises_error(self, tool_service):
        """Ensures ValueError for missing tool names."""
        with pytest.raises(ValueError, match="No tool with name"):
            tool_service.set_active_tool("ghost")
