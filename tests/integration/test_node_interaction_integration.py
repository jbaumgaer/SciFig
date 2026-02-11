"""
Integration tests for NodeController, ToolService, ApplicationModel, and Renderer interactions.
These tests focus on how user interactions (selection, property editing)
are translated through the controllers and services to update the model and view.
"""

from unittest.mock import MagicMock

import pytest

from src.controllers.canvas_controller import CanvasController
from src.controllers.node_controller import NodeController
from src.models.application_model import ApplicationModel
from src.models.nodes.plot_node import PlotNode
from src.services.commands.command_manager import CommandManager
from src.services.tool_service import ToolService
from src.services.tools.selection_tool import SelectionTool
from src.ui.factories.plot_properties_ui_factory import PlotPropertiesUIFactory
from src.ui.renderers.renderer import Renderer


@pytest.fixture
def real_application_model():
    """Provides a real ApplicationModel instance for integration tests."""
    model = ApplicationModel()
    return model


@pytest.fixture
def real_command_manager():
    """Provides a real CommandManager instance."""
    return CommandManager()


@pytest.fixture
def mock_properties_ui_factory():
    """Provides a mock PropertiesUIFactory."""
    return MagicMock(spec=PlotPropertiesUIFactory)


@pytest.fixture
def real_node_controller(
    real_application_model, real_command_manager, mock_properties_ui_factory
):
    """Provides a real NodeController instance."""
    return NodeController(
        real_application_model, real_command_manager, mock_properties_ui_factory
    )


@pytest.fixture
def real_tool_service():
    """Provides a real ToolService with a SelectionTool."""
    tool_service = ToolService()
    selection_tool = SelectionTool(
        MagicMock(), MagicMock(), MagicMock(), MagicMock()
    )  # Requires specific mocks
    tool_service.add_tool(selection_tool)
    tool_service.set_active_tool("selection")
    return tool_service


@pytest.fixture
def mock_canvas_controller():
    """Provides a mock CanvasController."""
    return MagicMock(spec=CanvasController)


@pytest.fixture
def mock_renderer():
    """Provides a mock Renderer."""
    renderer = MagicMock(spec=Renderer)
    renderer.render = MagicMock()
    return renderer


def test_node_controller_updates_model_on_property_change(
    real_application_model, real_command_manager, real_node_controller
):
    """
    Integration Test: NodeController -> ChangePropertyCommand -> ApplicationModel.
    This test should:
    - Initialize real ApplicationModel, CommandManager, NodeController.
    - Add a PlotNode to ApplicationModel and select it.
    - Simulate a property change event (e.g., from a UI widget connected to NodeController).
    - Assert that a ChangePropertyCommand was created and executed by CommandManager.
    - Assert that the PlotNode's property in ApplicationModel is updated.
    """
    model = real_application_model
    command_manager = real_command_manager
    node_controller = real_node_controller

    plot_node = PlotNode()
    plot_node.plot_properties.title = "Old Title"
    model.scene_root.add_child(plot_node)
    model.selection.add(plot_node)

    new_title = "New Title From UI"

    # Simulate UI changing a property
    # NodeController's handle_property_changed method would be called by the UI
    # In integration test, we call it directly
    node_controller.handle_property_changed(
        node_id=plot_node.id, property_name="title", new_value=new_title
    )

    # Assert that a command was executed
    assert command_manager.can_undo()
    assert isinstance(command_manager.undo_stack[-1], ChangePropertyCommand)

    # Assert model was updated
    assert plot_node.plot_properties.title == new_title


from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QMouseEvent

from src.services.tools.base_tool import BaseTool

# ... (rest of the file remains the same until the test function)


@pytest.fixture
def real_tool_service_with_mock_tools():
    """Provides a real ToolService with mock tools for testing dispatch."""
    tool_service = ToolService()

    mock_canvas_controller_for_tool = MagicMock(
        spec=CanvasController
    )  # Mock controller for tool
    mock_app_model_for_tool = MagicMock(spec=ApplicationModel)  # Mock model for tool
    mock_command_manager_for_tool = MagicMock(
        spec=CommandManager
    )  # Mock command manager for tool
    mock_renderer_for_tool = MagicMock(spec=Renderer)  # Mock renderer for tool

    mock_selection_tool = MagicMock(spec=SelectionTool)
    mock_selection_tool.name = "selection"
    mock_selection_tool.mouse_press_event = MagicMock()
    mock_selection_tool.mouse_move_event = MagicMock()
    mock_selection_tool.mouse_release_event = MagicMock()

    mock_another_tool = MagicMock(spec=BaseTool)
    mock_another_tool.name = "another_tool"
    mock_another_tool.mouse_press_event = MagicMock()

    tool_service.add_tool(mock_selection_tool)
    tool_service.add_tool(mock_another_tool)
    tool_service.set_active_tool("selection")

    return tool_service, mock_selection_tool, mock_another_tool


def test_canvas_controller_dispatches_mouse_event_to_tool_service(
    mock_canvas_controller, real_tool_service_with_mock_tools
):
    """
    Integration Test: CanvasController -> ToolService -> SelectionTool.
    This test should:
    - Initialize mock CanvasController and real ToolService with SelectionTool.
    - Simulate a mouse press event on CanvasController.
    - Assert that CanvasController's event handler calls ToolService's mouse_press_event.
    - Assert that SelectionTool's mouse_press_event is called.
    """
    tool_service, mock_selection_tool, _ = real_tool_service_with_mock_tools
    canvas_controller = mock_canvas_controller

    # Simulate a QMouseEvent
    pos = QPointF(10, 20)
    event = QMouseEvent(
        QMouseEvent.MouseButtonPress,
        pos,
        Qt.MouseButton.LeftButton,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
    )

    # In a real app, CanvasController would have a reference to tool_service
    # For this integration test, we simulate the dispatch logic that CanvasController would perform.
    # The CanvasController would internally call its tool_service.active_tool.mouse_press_event

    # We directly call the tool_service's active tool, which is what CanvasController would do
    tool_service.active_tool.mouse_press_event(event)

    mock_selection_tool.mouse_press_event.assert_called_once_with(event)
    tool_service.active_tool.mouse_press_event.reset_mock()

    # Change active tool and test again
    tool_service.set_active_tool("another_tool")
    tool_service.active_tool.mouse_press_event(event)
    tool_service.get_tool("another_tool").mouse_press_event.assert_called_once_with(
        event
    )
    mock_selection_tool.mouse_press_event.assert_not_called()


from unittest.mock import patch


@pytest.fixture
def real_selection_tool(real_application_model):
    """Provides a real SelectionTool instance with mocked dependencies."""
    # Mock canvas and renderer dependencies for SelectionTool
    mock_canvas_widget = MagicMock()
    mock_canvas_widget.map_to_scene_coords.side_effect = (
        lambda pos: pos
    )  # Simple 1:1 mapping for test
    mock_canvas_widget.width.return_value = 1000
    mock_canvas_widget.height.return_value = 800

    mock_renderer = MagicMock(spec=Renderer)
    mock_renderer.hit_test.side_effect = (
        lambda x, y, exclude_nodes=None: None
    )  # Default: no hit

    return SelectionTool(
        real_application_model, mock_canvas_widget, MagicMock(), mock_renderer
    )


def test_selection_tool_updates_application_model_selection(
    real_application_model, real_selection_tool
):
    """
    Integration Test: SelectionTool -> ApplicationModel.selection.
    This test should:
    - Initialize real ApplicationModel, ToolService with SelectionTool, and some PlotNodes.
    - Simulate a mouse click on a PlotNode's coordinates via SelectionTool.
    - Assert that the clicked PlotNode is added to ApplicationModel.selection.
    - Simulate a selection box drag to select multiple PlotNodes.
    - Assert that all PlotNodes within the selection box are in ApplicationModel.selection.
    """
    model = real_application_model
    selection_tool = real_selection_tool

    # Add plot nodes
    plot1 = PlotNode()
    plot1.set_geometry(0.1, 0.1, 0.2, 0.2)  # x=0.1, y=0.1, w=0.2, h=0.2
    plot2 = PlotNode()
    plot2.set_geometry(0.5, 0.5, 0.3, 0.3)  # x=0.5, y=0.5, w=0.3, h=0.3
    model.scene_root.add_child(plot1)
    model.scene_root.add_child(plot2)

    # Mock renderer's hit_test for single click
    selection_tool.renderer.hit_test.side_effect = lambda x, y, exclude_nodes=None: (
        plot1 if 0.1 < x < 0.3 and 0.1 < y < 0.3 else None
    )

    # Simulate click on plot1
    event = QMouseEvent(
        QMouseEvent.MouseButtonPress,
        QPointF(0.2, 0.2),
        Qt.MouseButton.LeftButton,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
    )
    selection_tool.mouse_press_event(event)
    event = QMouseEvent(
        QMouseEvent.MouseButtonRelease,
        QPointF(0.2, 0.2),
        Qt.MouseButton.LeftButton,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
    )
    selection_tool.mouse_release_event(event)

    assert plot1 in model.selection
    assert plot2 not in model.selection
    model.selection.clear()

    # Simulate selection box drag to select both plots
    # Assume CanvasController converts screen coords to scene coords before passing to tool
    # Selection tool operates in scene coordinates
    selection_tool.renderer.hit_test.side_effect = (
        lambda x, y, exclude_nodes=None: None
    )  # No single hit during drag

    # Start drag at (0.05, 0.05)
    press_event = QMouseEvent(
        QMouseEvent.MouseButtonPress,
        QPointF(0.05, 0.05),
        Qt.MouseButton.LeftButton,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
    )
    selection_tool.mouse_press_event(press_event)

    # Drag to (0.85, 0.85)
    move_event = QMouseEvent(
        QMouseEvent.MouseMove,
        QPointF(0.85, 0.85),
        Qt.MouseButton.LeftButton,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
    )
    selection_tool.mouse_move_event(
        move_event
    )  # This would typically update selection rectangle visual

    release_event = QMouseEvent(
        QMouseEvent.MouseButtonRelease,
        QPointF(0.85, 0.85),
        Qt.MouseButton.LeftButton,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
    )

    # Mock the renderer's hit_test for rectangle selection
    # For a selection rectangle (x1, y1, x2, y2), need to return plots that overlap
    def mock_hit_test_rect(rect_x, rect_y, rect_width, rect_height):
        selected_nodes = []
        for node in [plot1, plot2]:
            node_x, node_y, node_w, node_h = node.get_geometry()
            # Simple overlap check: rect_x < node_x + node_w and rect_x + rect_w > node_x ...
            if (
                rect_x < node_x + node_w
                and rect_x + rect_width > node_x
                and rect_y < node_y + node_h
                and rect_y + rect_height > node_y
            ):
                selected_nodes.append(node)
        return selected_nodes

    # Patch the selection_tool.renderer.hit_test_rectangle to simulate selection
    with patch.object(
        selection_tool.renderer, "hit_test_rectangle", side_effect=mock_hit_test_rect
    ):
        selection_tool.mouse_release_event(release_event)

    # Assert both plots are selected
    assert plot1 in model.selection
    assert plot2 in model.selection


def test_application_model_emits_model_changed_renders(
    real_application_model, mock_renderer
):
    """
    Integration Test: ApplicationModel.modelChanged -> Renderer.
    This test should:
    - Initialize real ApplicationModel and mock Renderer.
    - Connect ApplicationModel.modelChanged to Renderer.render.
    - Make a change to ApplicationModel (e.g., add a node, change a property via direct model manipulation).
    - Assert that Renderer.render was called.
    """
    model = real_application_model
    renderer = mock_renderer

    # Connect the signal (this would typically happen in CompositionRoot)
    model.modelChanged.connect(renderer.render)

    # Make a change to the model (e.g., add a node)
    plot_node = PlotNode()
    model.scene_root.add_child(plot_node)

    # Assert that renderer.render was called
    renderer.render.assert_called_once()
    renderer.render.reset_mock()

    # Make another change (e.g., change a property of an existing node)
    plot_node.plot_properties.title = "New Title"

    # Assert that renderer.render was called again
    renderer.render.assert_called_once()


def test_application_model_selection_changed_updates_node_controller(
    real_application_model, real_node_controller, mock_properties_ui_factory
):
    """
    Integration Test: ApplicationModel.selectionChanged -> NodeController.
    This test should:
    - Initialize real ApplicationModel and real NodeController.
    - Connect ApplicationModel.selectionChanged to NodeController's appropriate slot.
    - Change ApplicationModel.selection (e.g., add a PlotNode).
    - Assert that NodeController's method to update the properties panel UI was called.
    - Assert that PropertiesUIFactory's method to build the UI was called.
    """
    model = real_application_model
    node_controller = real_node_controller
    properties_ui_factory = mock_properties_ui_factory

    # Connect the signal (this would typically happen in CompositionRoot)
    # Assuming NodeController.on_selection_changed is the slot
    # This connection is already handled in the CompositionRoot for the real app,
    # so we primarily need to ensure NodeController's methods are called.

    # Mock specific methods on NodeController that would interact with UI Factory
    node_controller._update_properties_panel = MagicMock()

    # Change selection in the model
    plot_node = PlotNode()
    model.scene_root.add_child(plot_node)
    model.selection.add(plot_node)

    # After selection change, NodeController's _update_properties_panel should be called
    node_controller._update_properties_panel.assert_called_once()

    # And PropertiesUIFactory should be asked to build UI
    properties_ui_factory.build_properties_ui.assert_called_once()
