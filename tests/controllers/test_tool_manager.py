from unittest.mock import MagicMock, Mock

import pytest
from PySide6.QtCore import QObject

from src.controllers.tool_manager import ToolManager
from src.controllers.tools.base_tool import BaseTool


class MockTool(BaseTool):
    def __init__(self, model, command_manager, canvas_widget):
        super().__init__(model, command_manager, canvas_widget)
        self._name = "mock_tool"
        self._icon_path = "path/to/icon"

    @property
    def name(self) -> str:
        return self._name

    @property
    def icon_path(self) -> str:
        return self._icon_path

    def on_activated(self) -> None:
        pass

    def on_deactivated(self) -> None:
        pass

    def mouse_press_event(self, event) -> None:
        pass


@pytest.fixture
def tool_manager():
    """Fixture to create a ToolManager with mock dependencies."""
    model = Mock()
    command_manager = Mock()
    return ToolManager(model, command_manager)


def test_add_tool(tool_manager):
    """Test that a tool can be added to the manager."""
    model = Mock()
    command_manager = Mock()
    canvas_widget = Mock()
    tool = MockTool(model, command_manager, canvas_widget)
    tool_manager.add_tool(tool)
    assert tool_manager._tools["mock_tool"] == tool


def test_add_duplicate_tool_raises_error(tool_manager):
    """Test that adding a tool with a duplicate name raises a ValueError."""
    model = Mock()
    command_manager = Mock()
    canvas_widget = Mock()
    tool = MockTool(model, command_manager, canvas_widget)
    tool_manager.add_tool(tool)
    with pytest.raises(ValueError):
        tool_manager.add_tool(tool)


def test_set_active_tool(tool_manager, qtbot):
    """Test setting an active tool and that the correct signals are emitted."""
    model = Mock()
    command_manager = Mock()
    canvas_widget = Mock()
    tool1 = MockTool(model, command_manager, canvas_widget)
    tool1.on_activated = MagicMock()
    tool1.on_deactivated = MagicMock()

    tool2 = MockTool(model, command_manager, canvas_widget)
    tool2._name = "mock_tool_2"
    tool2.on_activated = MagicMock()

    tool_manager.add_tool(tool1)
    tool_manager.add_tool(tool2)

    with qtbot.waitSignal(tool_manager.active_tool_changed) as blocker:
        tool_manager.set_active_tool("mock_tool")

    assert blocker.args == ["mock_tool"]
    assert tool_manager.active_tool == tool1
    tool1.on_activated.assert_called_once()

    with qtbot.waitSignal(tool_manager.active_tool_changed) as blocker:
        tool_manager.set_active_tool("mock_tool_2")

    assert blocker.args == ["mock_tool_2"]
    tool1.on_deactivated.assert_called_once()
    tool2.on_activated.assert_called_once()


def test_set_unknown_tool_raises_error(tool_manager):
    """Test that setting an unknown tool raises a ValueError."""
    with pytest.raises(ValueError):
        tool_manager.set_active_tool("unknown_tool")


def test_event_dispatching(tool_manager):
    """Test that events are dispatched to the active tool."""
    model = Mock()
    command_manager = Mock()
    canvas_widget = Mock()
    tool = MockTool(model, command_manager, canvas_widget)
    tool.mouse_press_event = MagicMock()
    tool.mouse_move_event = MagicMock()
    tool.mouse_release_event = MagicMock()
    tool.key_press_event = MagicMock()
    tool.paint_event = MagicMock()

    tool_manager.add_tool(tool)
    tool_manager.set_active_tool("mock_tool")

    mouse_event = Mock()
    key_event = Mock()
    painter = Mock()

    tool_manager.dispatch_mouse_press_event(mouse_event)
    tool.mouse_press_event.assert_called_once_with(mouse_event)

    tool_manager.dispatch_mouse_move_event(mouse_event)
    tool.mouse_move_event.assert_called_once_with(mouse_event)

    tool_manager.dispatch_mouse_release_event(mouse_event)
    tool.mouse_release_event.assert_called_once_with(mouse_event)

    tool_manager.dispatch_key_press_event(key_event)
    tool.key_press_event.assert_called_once_with(key_event)

    tool_manager.dispatch_paint_event(painter)
    tool.paint_event.assert_called_once_with(painter)
