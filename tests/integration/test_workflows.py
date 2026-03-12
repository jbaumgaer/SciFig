import pytest
from unittest.mock import ANY
from PySide6.QtCore import Qt
from src.shared.events import Events
from src.shared.constants import ToolName
from src.models.nodes.plot_node import PlotNode

"""
Sociable Workflow Integration Tests.
Verifies the choreography between multiple stacks (Interaction, Node, Transaction, Layout).
"""

def test_add_plots_via_tool(interaction_stack, node_stack):
    """
    Scenario: User selects the Add Plot Tool and 'draws' three plots on the canvas.
    Flow: InteractionStack (Tool) -> NodeStack (Controller/Command) -> TransactionalStack (History).
    """
    int_stack = interaction_stack
    n_stack = node_stack
    ea = int_stack.ea
    
    # 1. Activate the Add Plot Tool
    int_stack.tool_service.set_active_tool(ToolName.PLOT.value)
    
    # Locations for 3 plots (Physical CM)
    # Plot 1: (2, 2) to (6, 6)
    # Plot 2: (8, 2) to (12, 6)
    # Plot 3: (2, 8) to (6, 12)
    geometries = [
        ((2.0, 2.0), (6.0, 6.0)),
        ((8.0, 2.0), (12.0, 6.0)),
        ((2.0, 8.0), (6.0, 12.0))
    ]
    
    # 2. Act: Simulate 3 drag-and-release interactions
    for start, end in geometries:
        # Press
        int_stack.tool_service.dispatch_mouse_press_event(
            node_id=None, 
            fig_coords=start, 
            button=Qt.MouseButton.LeftButton
        )
        # Release (finalizes the drag)
        int_stack.tool_service.dispatch_mouse_release_event(
            fig_coords=end
        )
        
    # 3. Assert: Verify the Model (Node Society)
    # Scene root should now have 3 children
    plots = list(n_stack.model.scene_root.all_descendants(of_type=PlotNode))
    assert len(plots) == 3
    
    # Verify exact geometries were preserved (using approx for float safety)
    assert pytest.approx(plots[0].geometry.x) == 2.0
    assert pytest.approx(plots[0].geometry.width) == 4.0
    
    assert pytest.approx(plots[1].geometry.x) == 8.0
    assert pytest.approx(plots[1].geometry.width) == 4.0
    
    # 4. Assert: Verify the Undo Stack (Transaction Society)
    # Each addition should be a separate undoable command
    assert len(n_stack.command_manager._undo_stack) == 3
    
    # 5. Act: Undo one addition
    n_stack.command_manager.undo()
    assert len(list(n_stack.model.scene_root.all_descendants(of_type=PlotNode))) == 2
    
    # 6. Verify Communication (Event Society)
    # The Tool publishes ADD_PLOT_REQUESTED
    # The Controller publishes SCENE_GRAPH_CHANGED
    ea.publish.assert_any_call(Events.ADD_PLOT_REQUESTED, geometry=ANY)
    ea.publish.assert_any_call(Events.SCENE_GRAPH_CHANGED)
