import pytest
from unittest.mock import MagicMock
from src.models.layout.grid_layout_engine import GridLayoutEngine
from src.models.layout.layout_config import GridConfig, Margins, Gutters
from src.models.nodes.plot_node import PlotNode

@pytest.fixture
def grid_layout_engine(mock_config_service):
    """Provides a GridLayoutEngine instance."""
    return GridLayoutEngine(config_service=mock_config_service)

def test_convert_gutters_to_relative_basic(grid_layout_engine):
    """
    Tests _convert_gutters_to_relative for basic 2x2 grid with single hspace/wspace values.
    """
    config = GridConfig(
        rows=2,
        cols=2,
        row_ratios=[1, 1],
        col_ratios=[1, 1],
        margins=Margins(left=0.1, right=0.1, top=0.1, bottom=0.1),
        gutters=Gutters(hspace=[0.05], wspace=[0.05]) # Absolute gutter values
    )
    
    plot_area_width = 1.0 - config.margins.left - config.margins.right # 0.8
    plot_area_height = 1.0 - config.margins.top - config.margins.bottom # 0.8

    # Expected calculations:
    # total_col_ratio = 2, total_row_ratio = 2
    # avg_subplot_width_fraction = 0.8 / 2 = 0.4
    # avg_subplot_height_fraction = 0.8 / 2 = 0.4

    # Expected relative wspace = 0.05 / 0.4 = 0.125
    # Expected relative hspace = 0.05 / 0.4 = 0.125
    
    gs_hspace, gs_wspace = grid_layout_engine._convert_gutters_to_relative(
        config, config.rows, config.cols, plot_area_width, plot_area_height
    )

    assert gs_hspace == pytest.approx(0.125)
    assert gs_wspace == pytest.approx(0.125)


def test_convert_gutters_to_relative_multiple_values(grid_layout_engine):
    """
    Tests _convert_gutters_to_relative with multiple hspace/wspace values.
    """
    config = GridConfig(
        rows=3,
        cols=2,
        row_ratios=[1, 1, 1],
        col_ratios=[1, 1],
        margins=Margins(left=0.1, right=0.1, top=0.1, bottom=0.1),
        gutters=Gutters(hspace=[0.02, 0.03], wspace=[0.04]) # Absolute gutter values
    )

    plot_area_width = 1.0 - config.margins.left - config.margins.right # 0.8
    plot_area_height = 1.0 - config.margins.top - config.margins.bottom # 0.8

    # Expected calculations:
    # total_col_ratio = 2, total_row_ratio = 3
    # avg_subplot_width_fraction = 0.8 / 2 = 0.4
    # avg_subplot_height_fraction = 0.8 / 3 = 0.2666...

    # Expected relative wspace = 0.04 / 0.4 = 0.1
    # Expected relative hspace[0] = 0.02 / (0.8/3) = 0.075
    # Expected relative hspace[1] = 0.03 / (0.8/3) = 0.1125
    
    gs_hspace, gs_wspace = grid_layout_engine._convert_gutters_to_relative(
        config, config.rows, config.cols, plot_area_width, plot_area_height
    )

    assert gs_wspace == pytest.approx(0.1)
    assert len(gs_hspace) == 2
    assert gs_hspace[0] == pytest.approx(0.075)
    assert gs_hspace[1] == pytest.approx(0.1125)

def test_convert_gutters_to_relative_single_row_col(grid_layout_engine):
    """
    Tests _convert_gutters_to_relative for single row or single column layouts.
    Should return None for hspace/wspace respectively.
    """
    # Single row, multiple cols
    config_1x2 = GridConfig(
        rows=1,
        cols=2,
        row_ratios=[1],
        col_ratios=[1, 1],
        margins=Margins(left=0.1, right=0.1, top=0.1, bottom=0.1),
        gutters=Gutters(hspace=[0.05], wspace=[0.05])
    )
    plot_area_width = 1.0 - config_1x2.margins.left - config_1x2.margins.right # 0.8
    plot_area_height = 1.0 - config_1x2.margins.top - config_1x2.margins.bottom # 0.8
    gs_hspace_1x2, gs_wspace_1x2 = grid_layout_engine._convert_gutters_to_relative(
        config_1x2, config_1x2.rows, config_1x2.cols, plot_area_width, plot_area_height
    )
    assert gs_hspace_1x2 is None
    assert gs_wspace_1x2 == pytest.approx(0.125) # Wspace should still be converted

    # Multiple rows, single col
    config_2x1 = GridConfig(
        rows=2,
        cols=1,
        row_ratios=[1, 1],
        col_ratios=[1],
        margins=Margins(left=0.1, right=0.1, top=0.1, bottom=0.1),
        gutters=Gutters(hspace=[0.05], wspace=[0.05])
    )
    plot_area_width = 1.0 - config_2x1.margins.left - config_2x1.margins.right # 0.8
    plot_area_height = 1.0 - config_2x1.margins.top - config_2x1.margins.bottom # 0.8
    gs_hspace_2x1, gs_wspace_2x1 = grid_layout_engine._convert_gutters_to_relative(
        config_2x1, config_2x1.rows, config_2x1.cols, plot_area_width, plot_area_height
    )
    assert gs_hspace_2x1 == pytest.approx(0.125) # Hspace should still be converted
    assert gs_wspace_2x1 is None

def test_convert_gutters_to_relative_zero_area(grid_layout_engine):
    """
    Tests _convert_gutters_to_relative when plot_area_width or plot_area_height is zero.
    Should handle division by zero gracefully and return None for relevant gutters.
    """
    config = GridConfig(
        rows=1,
        cols=1,
        row_ratios=[1],
        col_ratios=[1],
        margins=Margins(left=0.5, right=0.5, top=0.1, bottom=0.1), # Zero width plot area
        gutters=Gutters(hspace=[0.05], wspace=[0.05])
    )
    plot_area_width = 0.0 # 1 - 0.5 - 0.5
    plot_area_height = 0.8 # 1 - 0.1 - 0.1
    gs_hspace, gs_wspace = grid_layout_engine._convert_gutters_to_relative(
        config, config.rows, config.cols, plot_area_width, plot_area_height
    )
    assert gs_hspace is None # No hspace for single row
    assert gs_wspace is None # wspace calculation should avoid div by zero

    config_zero_height = GridConfig(
        rows=1,
        cols=1,
        row_ratios=[1],
        col_ratios=[1],
        margins=Margins(left=0.1, right=0.1, top=0.5, bottom=0.5), # Zero height plot area
        gutters=Gutters(hspace=[0.05], wspace=[0.05])
    )
    plot_area_width_h = 0.8
    plot_area_height_h = 0.0
    gs_hspace_h, gs_wspace_h = grid_layout_engine._convert_gutters_to_relative(
        config_zero_height, config_zero_height.rows, config_zero_height.cols, plot_area_width_h, plot_area_height_h
    )
    assert gs_hspace_h is None
    assert gs_wspace_h is None # hspace calculation should avoid div by zero