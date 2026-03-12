import pytest
from src.shared.events import Events
from src.shared.geometry import Rect
from src.shared.constants import LayoutMode
from src.models.nodes.plot_node import PlotNode
from src.models.nodes.grid_node import GridNode
from src.models.nodes.grid_position import GridPosition
from src.models.layout.layout_config import GridConfig, Margins, Gutters

"""
Layout & Geometry Stack Integration Tests.
Verifies the 'Reactive Reconciliation' and recursive math of 
the LayoutManager and Engines.
"""

def test_recursive_grid_calculation(layout_stack):
    """
    Scenario: A root GridNode containing another nested GridNode.
    Verify: 
    1. Leaf PlotNodes in the nested grid have mathematically correct Physical (CM) coordinates.
    2. Changing a margin on the root grid correctly shifts all nested children.
    """
    stack = layout_stack
    fig_w, fig_h = stack.model.figure_size # (20.0, 15.0) from conftest
    
    # 1. Create Root Grid (2x1)
    root_grid = GridNode(name="Root Grid")
    root_grid.rows = 2
    root_grid.cols = 1
    root_grid.margins = Margins(2.0, 2.0, 2.0, 2.0) # 2cm all around
    root_grid.gutters = Gutters(hspace=[1.0], wspace=[]) # 1cm between rows
    stack.model.add_node(root_grid)
    
    # 2. Add a Plot to Row 0 of Root
    p1 = PlotNode(name="Top Plot")
    p1.grid_position = GridPosition(0, 0)
    root_grid.add_child(p1)
    
    # 3. Add a Nested Grid to Row 1 of Root
    child_grid = GridNode(name="Child Grid")
    child_grid.grid_position = GridPosition(1, 0)
    child_grid.rows = 1
    child_grid.cols = 2
    child_grid.margins = Margins(1.0, 1.0, 1.0, 1.0) # 1cm nested margin
    child_grid.gutters = Gutters(hspace=[], wspace=[1.0]) # 1cm between cols
    root_grid.add_child(child_grid)
    
    # 4. Add two plots to the Nested Grid
    p2 = PlotNode(name="Nested Left")
    p2.grid_position = GridPosition(0, 0)
    child_grid.add_child(p2)
    
    p3 = PlotNode(name="Nested Right")
    p3.grid_position = GridPosition(0, 1)
    child_grid.add_child(p3)
    
    # 5. Act: Force layout reconciliation
    stack.manager.sync_layout()
    
    # 6. Verify Root Grid Geometry (should match figure)
    assert root_grid.geometry == Rect(0.0, 0.0, fig_w, fig_h)
    
    # 7. Verify P1 (Top Row)
    # Available height = 15 - 4 (margins) - 1 (gutter) = 10. Each row gets 5cm.
    # Bottom-Up Y: Row 1 is at bottom (2.0), Gutter is 1.0, Row 0 is at 3.0 + 5.0 = 8.0?
    # Let's check GridLayoutEngine logic: Y increases Bottom-to-Top.
    # net_rect.y = 2.0 (bottom margin)
    # row_heights = [5.0, 5.0]
    # row_ys = [2.0 + 5.0 + 1.0, 2.0] = [8.0, 2.0]
    # Row 0 (Top) is at Y=8.0. Row 1 (Bottom) is at Y=2.0.
    assert p1.geometry.y == 8.0
    assert p1.geometry.height == 5.0
    
    # 8. Verify Nested Grid Geometry (Row 1 of Root)
    assert child_grid.geometry.y == 2.0
    assert child_grid.geometry.height == 5.0
    assert child_grid.geometry.x == 2.0
    assert child_grid.geometry.width == 16.0
    
    # 9. Verify P2 (Nested Left)
    # available in child_grid: 16x5.
    # margins: 1cm all around. net = 14x3.
    # row_heights = [3.0]. col_widths = [6.5, 6.5] (1cm gutter).
    # P2 (Col 0) X = child_grid.x (2.0) + margin.left (1.0) = 3.0.
    assert p2.geometry.x == 3.0
    assert p2.geometry.width == 6.5
    
    # 10. Verify Reactivity: Change root margin
    stack.controller._handle_change_grid_parameter_request("margin_left", 5.0)
    # This should trigger re-calc via command
    assert p2.geometry.x == 6.0 # 5.0 (root) + 1.0 (child)

def test_layout_reaction_to_fig_size(layout_stack):
    """
    Scenario: Change the figure_size on the ApplicationModel.
    Verify: LayoutManager automatically recalculates.
    """
    stack = layout_stack
    
    # Setup a simple 1x1 grid
    grid = GridNode()
    grid.rows = 1
    grid.cols = 1
    grid.margins = Margins(0, 0, 0, 0)
    stack.model.add_node(grid)
    
    p1 = PlotNode()
    p1.grid_position = GridPosition(0, 0)
    grid.add_child(p1)
    
    stack.manager.sync_layout()
    assert p1.geometry.width == 20.0 # Default width
    
    # Act: Change figure size
    stack.model.figure_size = (30.0, 10.0)
    
    # Verify: LayoutManager should have reacted to FIGURE_SIZE_CHANGED
    assert p1.geometry.width == 30.0
    assert p1.geometry.height == 10.0

def test_grid_inference_heuristic(layout_stack):
    """
    Scenario: Place multiple plots at manual (free-form) positions.
    Verify: LayoutManager.infer_grid_parameters() correctly identifies the likely rows/cols.
    """
    stack = layout_stack
    stack.model.layout_mode = LayoutMode.FREE_FORM
    
    # Create 4 plots in a rough 2x2 arrangement
    p1 = PlotNode(name="TL"); p1.geometry = Rect(2, 8, 4, 4)
    p2 = PlotNode(name="TR"); p2.geometry = Rect(12, 8, 4, 4)
    p3 = PlotNode(name="BL"); p3.geometry = Rect(2, 2, 4, 4)
    p4 = PlotNode(name="BR"); p4.geometry = Rect(12, 2, 4, 4)
    
    for p in [p1, p2, p3, p4]:
        stack.model.add_node(p)
    
    # Act: Infer
    stack.controller._handle_infer_grid_parameters_request()
    
    # Verify: EA should have published GRID_CONFIG_PARAMETERS_CHANGED
    # with 2 rows and 2 columns
    calls = stack.ea.publish.call_args_list
    found = False
    for call in calls:
        if call.args[0] == Events.GRID_CONFIG_PARAMETERS_CHANGED:
            config = call.kwargs["grid_config"]
            assert config.rows == 2
            assert config.cols == 2
            found = True
            break
    assert found

def test_free_form_alignment_contracts(layout_stack):
    """
    Scenario: Select multiple plots in free-form mode and call align/distribute.
    Verify: Geometries are updated correctly and undoable.
    """
    stack = layout_stack
    stack.model.layout_mode = LayoutMode.FREE_FORM
    
    p1 = PlotNode(name="P1"); p1.geometry = Rect(2, 2, 5, 5)
    p2 = PlotNode(name="P2"); p2.geometry = Rect(10, 5, 5, 5)
    
    stack.model.add_node(p1)
    stack.model.add_node(p2)
    stack.model.set_selection([p1, p2])
    
    # Act: Align Left
    stack.controller._handle_align_plots_request("left")
    
    # Both should have x = 2.0 (min of the two)
    assert p1.geometry.x == 2.0
    assert p2.geometry.x == 2.0
    
    # Verify Undo
    stack.command_manager.undo()
    assert p2.geometry.x == 10.0
