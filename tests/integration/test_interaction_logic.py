import pytest
from PySide6.QtCore import Qt
from src.shared.events import Events
from src.shared.geometry import Rect
from src.shared.types import CoordinateSpace
from src.models.nodes.plot_node import PlotNode
from src.models.nodes.group_node import GroupNode
from src.models.nodes.grid_node import GridNode
from src.models.nodes.grid_position import GridPosition

"""
Interaction & Coordinate Stack Integration Tests.
Verifies 'Headless User Logic' and numerical stability of transformations.
"""

def test_coordinate_transformation_integrity(interaction_stack):
    """
    Scenario: Perform a round-trip transformation (CM -> Fractional -> Pixel -> CM).
    Verify: High numerical precision.
    """
    stack = interaction_stack
    fig_w, fig_h = stack.model.figure_size # (20.0, 15.0)
    canvas_px_w = 1000.0 # Simulated canvas width in pixels
    
    original_cm = 10.0
    
    # 1. CM -> Fractional
    frac = stack.coord_service.transform_value(
        original_cm, CoordinateSpace.PHYSICAL, CoordinateSpace.FRACTIONAL_FIG, 
        figure_size_cm=fig_w
    )
    assert frac == 0.5
    
    # 2. Fractional -> Pixel
    px = stack.coord_service.transform_value(
        frac, CoordinateSpace.FRACTIONAL_FIG, CoordinateSpace.DISPLAY_PX,
        canvas_size_px=canvas_px_w
    )
    assert px == 500.0
    
    # 3. Round trip: Pixel -> CM
    final_cm = stack.coord_service.transform_value(
        px, CoordinateSpace.DISPLAY_PX, CoordinateSpace.PHYSICAL,
        canvas_size_px=canvas_px_w, figure_size_cm=fig_w
    )
    
    assert pytest.approx(final_cm, abs=1e-9) == original_cm

def test_selection_hit_test_recursion(interaction_stack):
    """
    Scenario: A deep scene hierarchy (Group -> Grid -> Plot). Simulate a 'click'.
    Verify: The hit-test correctly returns the leaf (PlotNode).
    """
    stack = interaction_stack
    
    # 1. Arrange: Deep Hierarchy
    # Root -> Group -> Grid (1x1) -> Plot
    group = GroupNode(name="Level1")
    stack.model.add_node(group)
    
    grid = GridNode(name="Level2", rows=1, cols=1)
    group.add_child(grid)
    
    plot = PlotNode(name="LeafPlot")
    plot.geometry = Rect(5.0, 5.0, 4.0, 4.0) # Centered at 7, 7
    grid.add_child(plot)
    
    # 2. Act: Click in the center of the plot (7.0, 7.0)
    hit_node = stack.model.get_node_at((7.0, 7.0))
    
    # 3. Assert: Verify we hit the leaf
    assert hit_node is not None
    assert hit_node.id == plot.id
    assert hit_node.name == "LeafPlot"
    
    # 4. Act: Click outside (0.0, 0.0)
    miss_node = stack.model.get_node_at((0.0, 0.0))
    assert miss_node is None

def test_tool_intent_to_command_flow(interaction_stack, transactional_stack):
    """
    Scenario: Use the CanvasController to simulate a node selection.
    Verify: The EventAggregator broadcasts the change.
    Note: We use InteractionStack which has CanvasController + ToolService.
    """
    stack = interaction_stack
    plot = PlotNode(name="Target")
    plot.geometry = Rect(1, 1, 5, 5)
    stack.model.add_node(plot)
    
    # Directly simulate the ToolService event dispatch
    # This bypasses the Matplotlib event mapping which is difficult to mock 
    # but still tests the Interaction Stack's core selection logic.
    stack.tool_service.dispatch_mouse_press_event(
        node_id=plot.id, 
        fig_coords=(3.5, 3.5), 
        button=Qt.MouseButton.LeftButton
    )
    
    # Verify Selection logic in Model
    assert len(stack.model.selection) == 1
    assert stack.model.selection[0].id == plot.id
    
    # Verify Communication
    stack.ea.publish.assert_any_call(Events.SELECTION_CHANGED, selected_node_ids=[plot.id])
