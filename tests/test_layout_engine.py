import pytest
from unittest.mock import MagicMock

from src.layout_engine import FreeLayoutEngine, GridLayoutEngine, LayoutEngine, Rect
from src.models.layout_config import FreeConfig, GridConfig
from src.models.nodes import PlotNode
from src.config_service import ConfigService
from src.types import PlotID

# Fixtures for engines and configs
@pytest.fixture
def free_engine():
    return FreeLayoutEngine()

@pytest.fixture
def mock_config_service():
    config = MagicMock(spec=ConfigService)
    config.get.side_effect = lambda key, default: {
        "layout.default_grid_rows": 2,
        "layout.default_grid_cols": 2,
        "layout.grid_margin": 0.05,
        "layout.grid_gutter": 0.05,
    }.get(key, default)
    return config

@pytest.fixture
def grid_engine(mock_config_service):
    return GridLayoutEngine(mock_config_service)

@pytest.fixture
def free_config():
    return FreeConfig()

@pytest.fixture
def grid_config():
    return GridConfig(rows=2, cols=2, margin=0.1, gutter=0.05)

@pytest.fixture
def four_plots():
    return [
        PlotNode(id="p1", geometry=(0.1, 0.6, 0.3, 0.3)), # Top-left
        PlotNode(id="p2", geometry=(0.5, 0.7, 0.3, 0.2)), # Top-right (higher y)
        PlotNode(id="p3", geometry=(0.05, 0.1, 0.4, 0.4)), # Bottom-left
        PlotNode(id="p4", geometry=(0.6, 0.2, 0.35, 0.35)), # Bottom-right
    ]

@pytest.fixture
def two_plots():
    return [
        PlotNode(id="p_a", geometry=(0.1, 0.1, 0.3, 0.3)),
        PlotNode(id="p_b", geometry=(0.5, 0.5, 0.3, 0.3)),
    ]

# Test cases for FreeLayoutEngine
def test_free_layout_engine_calculate_geometries_passthrough(free_engine, four_plots, free_config):
    """Test calculate_geometries for FreeLayoutEngine returns current geometries."""
    geometries = free_engine.calculate_geometries(four_plots, free_config)
    assert len(geometries) == 4
    for plot in four_plots:
        assert geometries[plot.id] == plot.geometry

def test_free_layout_engine_perform_align_left(free_engine, two_plots):
    """Test perform_align aligns plots to the leftmost edge."""
    # current geometries: p_a (0.1, 0.1, 0.3, 0.3), p_b (0.5, 0.5, 0.3, 0.3)
    aligned_geometries = free_engine.perform_align(two_plots, "left")
    
    # Target x should be 0.1 (min x of p_a)
    assert aligned_geometries["p_a"][0] == pytest.approx(0.1)
    assert aligned_geometries["p_b"][0] == pytest.approx(0.1)
    assert aligned_geometries["p_a"][1:] == two_plots[0].geometry[1:]
    assert aligned_geometries["p_b"][1:] == two_plots[1].geometry[1:]

def test_free_layout_engine_perform_align_h_center(free_engine, two_plots):
    """Test perform_align aligns plots to the horizontal center."""
    # p_a: (0.1, 0.1, 0.3, 0.3) -> center_x = 0.1 + 0.3/2 = 0.25
    # p_b: (0.5, 0.5, 0.3, 0.3) -> center_x = 0.5 + 0.3/2 = 0.65
    # Average center_x = (0.25 + 0.65) / 2 = 0.45
    aligned_geometries = free_engine.perform_align(two_plots, "h_center")
    
    assert aligned_geometries["p_a"][0] == pytest.approx(0.45 - two_plots[0].geometry[2] / 2)
    assert aligned_geometries["p_b"][0] == pytest.approx(0.45 - two_plots[1].geometry[2] / 2)

def test_free_layout_engine_perform_distribute_horizontal(free_engine):
    """Test perform_distribute distributes plots horizontally."""
    plots = [
        PlotNode(id="d1", geometry=(0.1, 0.1, 0.1, 0.1)),
        PlotNode(id="d2", geometry=(0.2, 0.1, 0.1, 0.1)),
        PlotNode(id="d3", geometry=(0.7, 0.1, 0.1, 0.1)),
    ]
    # Sorted by x: d1 (0.1), d2 (0.2), d3 (0.7)
    # Total width = 0.1 + 0.1 + 0.1 = 0.3
    # min_coord = 0.1, max_coord = 0.7 + 0.1 = 0.8
    # available_space = 0.8 - 0.1 - 0.3 = 0.4
    # spacing = 0.4 / (3 - 1) = 0.2
    
    distributed_geometries = free_engine.perform_distribute(plots, "horizontal")
    
    assert distributed_geometries["d1"][0] == pytest.approx(0.1)
    assert distributed_geometries["d2"][0] == pytest.approx(0.1 + 0.1 + 0.2) # min_coord + width1 + spacing
    assert distributed_geometries["d3"][0] == pytest.approx(0.1 + 0.1 + 0.2 + 0.1 + 0.2) # min_coord + width1 + spacing + width2 + spacing

# Test cases for GridLayoutEngine.calculate_geometries (new test stubs)
def test_grid_layout_engine_calculate_geometries_four_plots_2x2_grid(grid_engine, four_plots):
    """
    Test GridLayoutEngine.calculate_geometries for 4 plots in a 2x2 grid.
    Verifies intelligent assignment (top-left to bottom-right) and correct geometry calculation
    including margins and gutters.
    """
    # Grid: 2x2, margin=0.1, gutter=0.05
    # Effective width = 1.0 - 2*0.1 = 0.8
    # Effective height = 1.0 - 2*0.1 = 0.8
    # Total gutter width = (2-1)*0.05 = 0.05
    # Total gutter height = (2-1)*0.05 = 0.05
    # Plot area width = 0.8 - 0.05 = 0.75
    # Plot area height = 0.8 - 0.05 = 0.75
    # Cell width = 0.75 / 2 = 0.375
    # Cell height = 0.75 / 2 = 0.375

    grid_config = GridConfig(rows=2, cols=2, margin=0.1, gutter=0.05)
    
    # Sort order (top-to-bottom, left-to-right based on initial geometry):
    # p2 (0.5, 0.7, ...) -> row 0, col 1
    # p1 (0.1, 0.6, ...) -> row 0, col 0
    # p4 (0.6, 0.2, ...) -> row 1, col 1
    # p3 (0.05, 0.1, ...) -> row 1, col 0
    # Sorted plots: p2, p1, p4, p3
    # However, the code changed to sort by (-p.geometry[1], p.geometry[0])
    # p2 (y=0.7, x=0.5) -> (-0.7, 0.5)
    # p1 (y=0.6, x=0.1) -> (-0.6, 0.1)
    # p4 (y=0.2, x=0.6) -> (-0.2, 0.6)
    # p3 (y=0.1, x=0.05) -> (-0.1, 0.05)
    # Correct order: p2, p1, p4, p3

    geometries = grid_engine.calculate_geometries(four_plots, grid_config)

    # Expected positions for 2x2 grid, row-major from top-left
    # p2 -> (0.1, 0.1 + 0.375 + 0.05, 0.375, 0.375) -> (0.1, 0.525, 0.375, 0.375) -- This assumes bottom-up matplotlib
    # Top-left (0,0 in grid) is bottom-left (0.1, 0.1) for matplotlib
    # Plot cells are (col_idx, row_idx) with row 0 at the top, col 0 at the left
    # Matplotlib's add_axes expects [left, bottom, width, height]
    # Row 0 (top)
    # Col 0 (left) - p2
    expected_p2_geom = (0.1, 0.1 + 0.375 + 0.05, 0.375, 0.375) # Left, Bottom, Width, Height
    # Col 1 (right) - p1
    expected_p1_geom = (0.1 + 0.375 + 0.05, 0.1 + 0.375 + 0.05, 0.375, 0.375)
    # Row 1 (bottom)
    # Col 0 (left) - p4
    expected_p4_geom = (0.1, 0.1, 0.375, 0.375)
    # Col 1 (right) - p3
    expected_p3_geom = (0.1 + 0.375 + 0.05, 0.1, 0.375, 0.375)

    assert geometries["p2"] == pytest.approx(expected_p2_geom)
    assert geometries["p1"] == pytest.approx(expected_p1_geom)
    assert geometries["p4"] == pytest.approx(expected_p4_geom)
    assert geometries["p3"] == pytest.approx(expected_p3_geom)

def test_grid_layout_engine_calculate_geometries_zero_plots(grid_engine, grid_config):
    """Test calculate_geometries returns empty dict for zero plots."""
    geometries = grid_engine.calculate_geometries([], grid_config)
    assert geometries == {}

def test_grid_layout_engine_calculate_geometries_unassigned_plots(grid_engine, two_plots):
    """Test calculate_geometries with fewer plots than grid cells."""
    grid_config = GridConfig(rows=2, cols=2, margin=0.1, gutter=0.05) # 4 cells
    geometries = grid_engine.calculate_geometries(two_plots, grid_config)
    assert len(geometries) == 2 # Only 2 plots should have geometries
    assert "p_a" in geometries
    assert "p_b" in geometries

def test_grid_layout_engine_calculate_geometries_invalid_config_type(grid_engine, four_plots, free_config):
    """Test calculate_geometries returns empty dict for incompatible config."""
    geometries = grid_engine.calculate_geometries(four_plots, free_config)
    assert geometries == {}

def test_grid_layout_engine_calculate_geometries_single_plot_2x2_grid(grid_engine):
    """Test single plot in a 2x2 grid."""
    plot = [PlotNode(id="single_p", geometry=(0.5, 0.5, 0.1, 0.1))]
    grid_config = GridConfig(rows=2, cols=2, margin=0.1, gutter=0.05)
    geometries = grid_engine.calculate_geometries(plot, grid_config)

    # For a single plot in a 2x2 grid, it should occupy the first cell (top-left)
    # Based on sorting, the plot (single_p) will be the first item.
    # Expected position: Same as p2 in the four_plots test
    expected_geom = (0.1, 0.1 + 0.375 + 0.05, 0.375, 0.375)
    assert geometries["single_p"] == pytest.approx(expected_geom)

def test_grid_layout_engine_calculate_geometries_variable_ratios(grid_engine, two_plots):
    """Test grid calculation with explicit row and column ratios."""
    # 2 plots, in a 1x2 grid (1 row, 2 cols) with custom ratios
    grid_config = GridConfig(rows=1, cols=2, margin=0.1, gutter=0.05,
                             row_ratios=[1.0], col_ratios=[0.25, 0.75])
    
    # Effective width = 0.8, Effective height = 0.8
    # Total gutter width = 0.05
    # Plot area width = 0.75
    # Plot area height = 0.8

    # Col 0 width = 0.75 * 0.25 = 0.1875
    # Col 1 width = 0.75 * 0.75 = 0.5625

    # Plot 'p_b' (higher y) then 'p_a' (lower y) from fixtures based on sorting (-y, x)
    # sorted_plots: p_b, p_a (if geometries are (0.5, 0.5) and (0.1, 0.1))

    # Based on the fixture two_plots:
    # p_a: geometry=(0.1, 0.1, 0.3, 0.3) -> (-0.1, 0.1)
    # p_b: geometry=(0.5, 0.5, 0.3, 0.3) -> (-0.5, 0.5)
    # So sorted_plots = [p_b, p_a]

    geometries = grid_engine.calculate_geometries(two_plots, grid_config)

    # p_b in col 0
    expected_p_b_geom = (0.1, 0.1, 0.1875, 0.8) # left=margin, bottom=margin, width=col0_width, height=plot_area_height
    # p_a in col 1
    expected_p_a_geom = (0.1 + 0.1875 + 0.05, 0.1, 0.5625, 0.8) # left=margin+col0_width+gutter, bottom=margin, width=col1_width, height=plot_area_height

    assert geometries["p_b"] == pytest.approx(expected_p_b_geom)
    assert geometries["p_a"] == pytest.approx(expected_p_a_geom)
