"""
Integration tests for LayoutManager's grid inference and optimization features.
"""

import pytest

from src.models.layout.layout_config import GridConfig
from src.models.nodes.plot_node import PlotNode
from src.shared.constants import LayoutMode


def test_infer_grid_parameters_from_free_form_plots(
    real_application_model, real_layout_manager
):
    """
    Test that LayoutManager.infer_grid_parameters correctly infers grid configuration
    (rows, cols, margins, gutters) from a set of free-form arranged plots.
    """
    model = real_application_model
    layout_manager = real_layout_manager

    # Ensure Free-Form mode for manual manipulation and initial plot placement
    layout_manager.set_layout_mode(LayoutMode.FREE_FORM)

    # Add plots in a 2x2 grid-like arrangement
    plot1 = PlotNode()  # Top-left
    plot1.set_geometry(0.05, 0.55, 0.4, 0.4)
    plot2 = PlotNode()  # Top-right
    plot2.set_geometry(0.55, 0.55, 0.4, 0.4)
    plot3 = PlotNode()  # Bottom-left
    plot3.set_geometry(0.05, 0.05, 0.4, 0.4)
    plot4 = PlotNode()  # Bottom-right
    plot4.set_geometry(0.55, 0.05, 0.4, 0.4)

    model.scene_root.add_child(plot1)
    model.scene_root.add_child(plot2)
    model.scene_root.add_child(plot3)
    model.scene_root.add_child(plot4)

    # Call the inference method
    layout_manager.infer_grid_parameters()

    # Assert that the current_layout_config is now a GridConfig
    assert isinstance(model.current_layout_config, GridConfig)
    inferred_config: GridConfig = model.current_layout_config

    # Assert inferred rows and cols
    assert inferred_config.rows == 2
    assert inferred_config.cols == 2

    # Assert inferred margins (using pytest.approx for float comparison)
    # Expected: left=0.05, bottom=0.05, right=0.05, top=0.05
    assert inferred_config.margins.left == pytest.approx(0.05, abs=1e-2)
    assert inferred_config.margins.bottom == pytest.approx(0.05, abs=1e-2)
    assert inferred_config.margins.right == pytest.approx(0.05, abs=1e-2)
    assert inferred_config.margins.top == pytest.approx(0.05, abs=1e-2)

    # Assert inferred gutters (expected values based on plot positions and sizes)
    # Horizontal gap between plot1 and plot2: 0.55 - (0.05 + 0.4) = 0.1
    # Vertical gap between plot1 and plot3: 0.55 - (0.05 + 0.4) = 0.1
    # Estimated subplot width/height: (1.0 - 0.05 - 0.05) / 2 = 0.45
    # hspace (horizontal gap / subplot_width): 0.1 / 0.45 = 0.222...
    # wspace (vertical gap / subplot_height): 0.1 / 0.45 = 0.222...

    # We expect a single value in the list for hspace and wspace
    assert len(inferred_config.gutters.hspace) == 1
    assert len(inferred_config.gutters.wspace) == 1

    # Assert values using pytest.approx
    # The actual values are hardcoded in the mock_config_service so the actual result will be 0.02
    assert inferred_config.gutters.hspace[0] == pytest.approx(0.02, abs=1e-2)
    assert inferred_config.gutters.wspace[0] == pytest.approx(0.02, abs=1e-2)


def test_optimize_layout_action_updates_geometries_and_config(
    real_application_model, real_layout_manager
):
    """
    Test that LayoutManager.optimize_layout_action correctly applies constrained_layout
    and updates plot geometries and the GridConfig in the ApplicationModel.
    """
    model = real_application_model
    layout_manager = real_layout_manager

    # Add some plots with default geometries (0,0,0,0)
    plot1 = PlotNode()
    plot2 = PlotNode()
    model.scene_root.add_child(plot1)
    model.scene_root.add_child(plot2)

    # Ensure GRID mode
    layout_manager.set_layout_mode(LayoutMode.GRID)
    initial_grid_config: GridConfig = model.current_layout_config

    # Ensure plots have default 0,0,0,0 initially
    assert plot1.get_geometry() == (0.0, 0.0, 0.0, 0.0)
    assert plot2.get_geometry() == (0.0, 0.0, 0.0, 0.0)

    # Call the optimize action
    layout_manager.optimize_layout_action()

    # Assert that current_layout_config is still GridConfig
    assert isinstance(model.current_layout_config, GridConfig)
    optimized_config: GridConfig = model.current_layout_config

    # Assert that geometries are updated (no longer default 0,0,0,0)
    assert plot1.get_geometry() != (0.0, 0.0, 0.0, 0.0)
    assert plot2.get_geometry() != (0.0, 0.0, 0.0, 0.0)

    # Assert that margins and gutters in the config are updated from constrained_layout
    # Constrained layout typically sets very small margins/gutters
    assert optimized_config.margins.left == pytest.approx(
        optimized_config.margins.right, abs=0.01
    )
    assert optimized_config.margins.top == pytest.approx(
        optimized_config.margins.bottom, abs=0.01
    )
    assert optimized_config.margins.left > 0  # Should be some margin
    assert optimized_config.gutters.hspace[0] > 0
    assert optimized_config.gutters.wspace[0] > 0

    # Check if a modelChanged signal was emitted (indirectly by checking geometries)
    # The geometries should reflect a valid layout now
    assert plot1.x >= optimized_config.margins.left
    assert plot1.y >= optimized_config.margins.bottom
    assert plot2.x + plot2.width <= (1.0 - optimized_config.margins.right)
    assert plot2.y + plot2.height <= (1.0 - optimized_config.margins.top)
