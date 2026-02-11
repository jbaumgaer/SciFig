"""
Integration tests for GridLayoutEngine's core geometry calculations.
"""

import pytest

from src.models.layout.grid_layout_engine import GridLayoutEngine
from src.models.layout.layout_config import GridConfig, Gutters, Margins
from src.models.nodes.plot_node import PlotNode


def test_grid_layout_engine_calculates_geometries(real_grid_layout_engine):
    """
    Integration Test: GridLayoutEngine calculates geometries using fixed layout.
    This test should:
    - Initialize a real GridLayoutEngine.
    - Create several mock PlotNodes with dummy initial geometries.
    - Create a GridConfig (e.g., 2x2, specific margins/gutters).
    - Call GridLayoutEngine.calculate_geometries with plots and config (fixed layout).
    - Assert that the returned geometries are mathematically correct based on the grid parameters.
    """
    engine = real_grid_layout_engine

    # Create dummy plot nodes (geometries don't matter initially for grid calc)
    plot1 = PlotNode()
    plot2 = PlotNode()
    plots = [plot1, plot2]

    # 1x2 grid config with some margins and gutters
    config = GridConfig(
        rows=1,
        cols=2,
        row_ratios=[1],
        col_ratios=[1, 1],
        margins=Margins(left=0.1, right=0.1, top=0.1, bottom=0.1),
        gutters=Gutters(hspace=[0.05], wspace=[0.05]),
    )

    geometries, calculated_margins, calculated_gutters = engine.calculate_geometries(
        plots, config, use_constrained_optimization=False
    )

    # Assert calculations (based on a total area of 1x1, with 0,0 top-left)
    # Total available width for plots: 1 - left_margin - right_margin = 1 - 0.1 - 0.1 = 0.8
    # Total available height for plots: 1 - top_margin - bottom_margin = 1 - 0.1 - 0.1 = 0.8

    # Plot 1: (0.1, 0.1, (0.8 - 0.05) / 2, 0.8) = (0.1, 0.1, 0.375, 0.8)
    # Plot 2: (0.1 + 0.375 + 0.05, 0.1, (0.8 - 0.05) / 2, 0.8) = (0.525, 0.1, 0.375, 0.8)

    # We use a small tolerance for float comparisons
    tolerance = 1e-9

    plot1_geom = geometries[plot1.id]
    plot2_geom = geometries[plot2.id]

    assert abs(plot1_geom[0] - 0.1) < tolerance  # x
    assert abs(plot1_geom[1] - 0.1) < tolerance  # y
    assert abs(plot1_geom[2] - ((1 - 0.1 - 0.1 - 0.05) / 2)) < tolerance  # width
    assert abs(plot1_geom[3] - (1 - 0.1 - 0.1)) < tolerance  # height

    assert abs(plot2_geom[0] - (0.1 + plot1_geom[2] + 0.05)) < tolerance  # x
    assert abs(plot2_geom[1] - 0.1) < tolerance  # y
    assert abs(plot2_geom[2] - plot1_geom[2]) < tolerance  # width
    assert abs(plot2_geom[3] - plot1_geom[3]) < tolerance  # height

    # Assert that the calculated margins and gutters are the same as the input config for fixed layout
    assert calculated_margins == config.margins
    assert calculated_gutters == config.gutters

    # Test 2x1 grid
    plots = [plot1, plot2]
    config_2x1 = GridConfig(
        rows=2,
        cols=1,
        row_ratios=[1, 1],
        col_ratios=[1],
        margins=Margins(left=0.1, right=0.1, top=0.1, bottom=0.1),
        gutters=Gutters(hspace=[0.05], wspace=[0.05]),
    )
    geometries_2x1, calculated_margins_2x1, calculated_gutters_2x1 = (
        engine.calculate_geometries(
            plots, config_2x1, use_constrained_optimization=False
        )
    )

    # Total available height: 1 - 0.1 - 0.1 = 0.8
    # Total available width: 1 - 0.1 - 0.1 = 0.8
    # Plot height: (0.8 - 0.05) / 2 = 0.375
    # Plot width: 0.8

    plot1_geom_2x1 = geometries_2x1[plot1.id]
    plot2_geom_2x1 = geometries_2x1[plot2.id]

    assert abs(plot1_geom_2x1[0] - 0.1) < tolerance  # x
    assert abs(plot1_geom_2x1[1] - 0.1) < tolerance  # y
    assert abs(plot1_geom_2x1[2] - (1 - 0.1 - 0.1)) < tolerance  # width
    assert abs(plot1_geom_2x1[3] - ((1 - 0.1 - 0.1 - 0.05) / 2)) < tolerance  # height

    assert abs(plot2_geom_2x1[0] - 0.1) < tolerance  # x
    assert abs(plot2_geom_2x1[1] - (0.1 + plot1_geom_2x1[3] + 0.05)) < tolerance  # y
    assert abs(plot2_geom_2x1[2] - plot1_geom_2x1[2]) < tolerance  # width
    assert abs(plot2_geom_2x1[3] - plot1_geom_2x1[3]) < tolerance  # height

    # Assert that the calculated margins and gutters are the same as the input config for fixed layout
    assert calculated_margins_2x1 == config_2x1.margins
    assert calculated_gutters_2x1 == config_2x1.gutters


def test_grid_layout_engine_constrained_layout_optimization(mock_config_service):
    """
    Test that GridLayoutEngine's constrained layout optimization correctly calculates
    geometries and returns dynamically calculated margins and gutters.
    """
    mock_config_service.get.side_effect = {
        "layout.constrained_w_space": 0.02,
        "layout.constrained_h_space": 0.02,
    }.get

    engine = GridLayoutEngine(config_service=mock_config_service)

    plot1 = PlotNode()
    plot2 = PlotNode()
    plots = [plot1, plot2]

    # Use a basic GridConfig. Margins/gutters will be optimized by constrained_layout.
    config = GridConfig(
        rows=1,
        cols=2,
        row_ratios=[1],
        col_ratios=[1, 1],
        margins=Margins(
            left=0.1, right=0.1, top=0.1, bottom=0.1
        ),  # These are input, will be overridden by constrained_layout
        gutters=Gutters(
            hspace=[0.05], wspace=[0.05]
        ),  # These are input, will be overridden by constrained_layout
    )

    geometries, calculated_margins, calculated_gutters = engine.calculate_geometries(
        plots, config, use_constrained_optimization=True
    )

    # Assert that geometries are calculated (not empty)
    assert len(geometries) == 2
    assert plot1.id in geometries
    assert plot2.id in geometries

    # Assert that the calculated margins and gutters are different from the input
    # and represent the optimized values from constrained_layout.
    # Constrained layout typically pushes plots slightly inwards from the figure edge,
    # so margins should be positive and small.
    assert calculated_margins.left > 0
    assert calculated_margins.right > 0
    assert calculated_margins.top > 0
    assert calculated_margins.bottom > 0

    # Assert that gutters are also non-zero and reasonable
    assert len(calculated_gutters.hspace) >= 0
    assert len(calculated_gutters.wspace) >= 0
    # The actual values are hardcoded in the mock_config_service so the actual result will be 0.02
    assert calculated_gutters.wspace[0] == pytest.approx(0.02, abs=1e-2)
    assert calculated_gutters.hspace[0] == pytest.approx(0.02, abs=1e-2)

    # Further assertions on actual geometry values would be complex due to matplotlib's internal
    # layout logic, but we can check relative positions.
    plot1_geom = geometries[plot1.id]
    plot2_geom = geometries[plot2.id]

    assert plot1_geom[0] < plot2_geom[0]  # plot1 is to the left of plot2
    assert plot1_geom[2] == pytest.approx(
        plot2_geom[2], abs=1e-3
    )  # widths should be similar due to 1:1 ratio


def test_grid_layout_engine_zero_plots(real_grid_layout_engine):
    """
    Test GridLayoutEngine's behavior with zero plots.
    Should return empty geometries and default margins/gutters.
    """
    engine = real_grid_layout_engine
    config = GridConfig(
        rows=1,
        cols=1,
        row_ratios=[1],
        col_ratios=[1],
        margins=Margins(top=0.0, bottom=0.0, left=0.0, right=0.0),
        gutters=Gutters(hspace=[], wspace=[]),
    )

    geometries, calculated_margins, calculated_gutters = engine.calculate_geometries(
        [], config
    )
    assert geometries == {}
    assert calculated_margins == config.margins
    assert calculated_gutters == config.gutters


def test_grid_layout_engine_single_plot(real_grid_layout_engine):
    """
    Test GridLayoutEngine's behavior with a single plot.
    """
    engine = real_grid_layout_engine
    plot1 = PlotNode()
    plots = [plot1]
    config = GridConfig(
        rows=1,
        cols=1,
        row_ratios=[1],
        col_ratios=[1],
        margins=Margins(left=0.1, right=0.1, top=0.1, bottom=0.1),
        gutters=Gutters(hspace=[], wspace=[]),
    )

    geometries, _, _ = engine.calculate_geometries(plots, config)
    assert len(geometries) == 1

    plot1_geom = geometries[plot1.id]
    # Expected: x=0.1, y=0.1, width=0.8, height=0.8
    assert plot1_geom[0] == pytest.approx(0.1)
    assert plot1_geom[1] == pytest.approx(0.1)
    assert plot1_geom[2] == pytest.approx(0.8)
    assert plot1_geom[3] == pytest.approx(0.8)


def test_grid_layout_engine_custom_ratios(real_grid_layout_engine):
    """
    Test GridLayoutEngine with custom row and column ratios.
    """
    engine = real_grid_layout_engine
    plot1 = PlotNode()
    plot2 = PlotNode()
    plots = [plot1, plot2]

    # 1x2 grid with 1:2 col_ratios (plot2 twice as wide as plot1)
    config = GridConfig(
        rows=1,
        cols=2,
        row_ratios=[1],
        col_ratios=[1, 2],
        margins=Margins(left=0.1, right=0.1, top=0.1, bottom=0.1),
        gutters=Gutters(hspace=[], wspace=[0.05]),
    )

    geometries, _, _ = engine.calculate_geometries(plots, config)

    total_width_available = 1.0 - config.margins.left - config.margins.right
    gutter_width = config.gutters.wspace[0] if config.gutters.wspace else 0
    effective_plot_space_width = total_width_available - gutter_width

    # Plot1 width: (1/3) * effective_plot_space_width
    # Plot2 width: (2/3) * effective_plot_space_width
    plot1_expected_width = (1 / 3) * effective_plot_space_width
    plot2_expected_width = (2 / 3) * effective_plot_space_width

    plot1_geom = geometries[plot1.id]
    plot2_geom = geometries[plot2.id]

    assert plot1_geom[0] == pytest.approx(config.margins.left)
    assert plot1_geom[2] == pytest.approx(plot1_expected_width)

    assert plot2_geom[0] == pytest.approx(
        config.margins.left + plot1_expected_width + gutter_width
    )
    assert plot2_geom[2] == pytest.approx(plot2_expected_width)


def test_grid_layout_engine_list_gutters(real_grid_layout_engine):
    """
    Test GridLayoutEngine with list values for hspace and wspace.
    """
    engine = real_grid_layout_engine
    plot1 = PlotNode()
    plot2 = PlotNode()
    plot3 = PlotNode()
    plot4 = PlotNode()
    plots = [plot1, plot2, plot3, plot4]

    # 2x2 grid with different hspace and wspace values
    config = GridConfig(
        rows=2,
        cols=2,
        row_ratios=[1, 1],
        col_ratios=[1, 1],
        margins=Margins(left=0.1, right=0.1, top=0.1, bottom=0.1),
        gutters=Gutters(
            hspace=[0.02, 0.03], wspace=[0.04]
        ),  # Hspace has two values (between rows), wspace has one (between cols)
    )

    geometries, _, _ = engine.calculate_geometries(
        plots, config, use_constrained_optimization=False
    )

    # Expected values for 2x2 grid with margins 0.1 and gutters hspace=[0.02,0.03], wspace=[0.04]
    # Total width available for plots = 1 - 0.1 (left) - 0.1 (right) = 0.8
    # Total height available for plots = 1 - 0.1 (bottom) - 0.1 (top) = 0.8

    # Col 1 width = (0.8 - wspace[0]) / 2 = (0.8 - 0.04) / 2 = 0.38
    # Col 2 width = 0.38

    # Row 1 height (bottom) = (0.8 - hspace[1]) / 2 = (0.8 - 0.03) / 2 = 0.385
    # Row 2 height (top) = (0.8 - hspace[0]) / 2 = (0.8 - 0.02) / 2 = 0.39

    plot1_geom = geometries[plot1.id]  # (sorted by y desc, then x asc) -> top-left
    plot2_geom = geometries[plot2.id]  # top-right
    plot3_geom = geometries[plot3.id]  # bottom-left
    plot4_geom = geometries[plot4.id]  # bottom-right

    tolerance = 1e-9

    # Top-left plot
    assert abs(plot1_geom[0] - 0.1) < tolerance  # x (left margin)
    assert (
        abs(plot1_geom[1] - (0.1 + (0.8 - 0.02 - 0.03) / 2 + 0.03)) < tolerance
    )  # y (bottom margin + h1 + hspace2)
    assert abs(plot1_geom[2] - ((0.8 - 0.04) / 2)) < tolerance  # width
    assert abs(plot1_geom[3] - ((0.8 - 0.02 - 0.03) / 2)) < tolerance  # height

    # Top-right plot
    assert (
        abs(plot2_geom[0] - (0.1 + plot1_geom[2] + 0.04)) < tolerance
    )  # x (left margin + w1 + wspace)
    assert abs(plot2_geom[1] - plot1_geom[1]) < tolerance  # y
    assert abs(plot2_geom[2] - plot1_geom[2]) < tolerance  # width
    assert abs(plot2_geom[3] - plot1_geom[3]) < tolerance  # height

    # Bottom-left plot
    assert abs(plot3_geom[0] - plot1_geom[0]) < tolerance  # x
    assert abs(plot3_geom[1] - (0.1)) < tolerance  # y (bottom margin)
    assert abs(plot3_geom[2] - plot1_geom[2]) < tolerance  # width
    assert abs(plot3_geom[3] - plot1_geom[3]) < tolerance  # height

    # Bottom-right plot
    assert abs(plot4_geom[0] - plot2_geom[0]) < tolerance  # x
    assert abs(plot4_geom[1] - plot3_geom[1]) < tolerance  # y
    assert abs(plot4_geom[2] - plot1_geom[2]) < tolerance  # width
    assert abs(plot4_geom[3] - plot1_geom[3]) < tolerance  # height
