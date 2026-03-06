import pytest
from unittest.mock import MagicMock

from src.models.layout.grid_layout_engine import GridLayoutEngine
from src.models.layout.layout_config import FreeConfig, GridConfig, Gutters, Margins
from src.models.nodes.plot_node import PlotNode


@pytest.fixture
def grid_engine():
    """Provides a GridLayoutEngine instance."""
    return GridLayoutEngine()


@pytest.fixture
def simple_grid_config():
    """Provides a basic 2x2 grid configuration."""
    return GridConfig(
        rows=2,
        cols=2,
        row_ratios=[1.0, 1.0],
        col_ratios=[1.0, 1.0],
        margins=Margins(0.1, 0.1, 0.1, 0.1),
        gutters=Gutters([0.05], [0.05]),
    )


@pytest.fixture
def four_plots():
    """Provides 4 plots with diverse initial positions for sorting verification."""
    p1 = PlotNode(id="p1", name="p1")
    p1.geometry = (0.1, 0.6, 0.3, 0.3)
    p2 = PlotNode(id="p2", name="p2")
    p2.geometry = (0.5, 0.7, 0.3, 0.2)
    p3 = PlotNode(id="p3", name="p3")
    p3.geometry = (0.05, 0.1, 0.4, 0.4)
    p4 = PlotNode(id="p4", name="p4")
    p4.geometry = (0.6, 0.2, 0.35, 0.35)
    return [p1, p2, p3, p4]

# Helper to fix plot geometries in fixture since semicolon is not allowed in literal
@pytest.fixture
def four_plots_ordered():
    p1 = PlotNode(id="p1")
    p1.geometry = (0.1, 0.6, 0.3, 0.3)
    p2 = PlotNode(id="p2")
    p2.geometry = (0.5, 0.7, 0.3, 0.2)
    p3 = PlotNode(id="p3")
    p3.geometry = (0.05, 0.1, 0.4, 0.4)
    p4 = PlotNode(id="p4")
    p4.geometry = (0.6, 0.2, 0.35, 0.35)
    return [p1, p2, p3, p4]


class TestGridLayoutEngine:

    def test_calculate_geometries_fixed_layout(self, grid_engine, four_plots_ordered, simple_grid_config):
        """Verifies geometry calculation for a fixed 2x2 grid."""
        # Cell width/height calculation:
        # Plot area: 1.0 - 0.1(L) - 0.1(R) = 0.8. Gutter=0.05. Net plot width = 0.75. Cell=0.375
        # Plot area: 1.0 - 0.1(T) - 0.1(B) = 0.8. Gutter=0.05. Net plot height = 0.75. Cell=0.375
        
        geometries, margins, gutters = grid_engine.calculate_geometries(
            four_plots_ordered, simple_grid_config, use_constrained_optimization=False
        )
        
        assert len(geometries) == 4
        assert margins == simple_grid_config.margins
        assert gutters == simple_grid_config.gutters
        
        # Sorting (-y, x): p2(-0.7, 0.5), p1(-0.6, 0.1), p4(-0.2, 0.6), p3(-0.1, 0.05)
        # Expected order: p2, p1, p4, p3
        # Cell mapping (row-major from top-left):
        # r0c0: p2, r0c1: p1
        # r1c0: p4, r1c1: p3
        
        # Row 0 (top) -> bottom coord = margin_bottom + cell_h + gutter = 0.1 + 0.375 + 0.05 = 0.525
        # Col 0 (left) -> left coord = 0.1
        assert geometries["p2"] == pytest.approx((0.1, 0.525, 0.375, 0.375))
        # Col 1 (right) -> left coord = 0.1 + 0.375 + 0.05 = 0.525
        assert geometries["p1"] == pytest.approx((0.525, 0.525, 0.375, 0.375))

    def test_calculate_geometries_zero_plots(self, grid_engine, simple_grid_config):
        """Verifies that empty plot list returns empty dict but preserves margins/gutters."""
        geometries, margins, gutters = grid_engine.calculate_geometries([], simple_grid_config)
        assert geometries == {}
        assert margins == simple_grid_config.margins
        assert gutters == simple_grid_config.gutters

    def test_calculate_geometries_incompatible_config(self, grid_engine, four_plots_ordered):
        """Verifies error handling for incompatible config."""
        geometries, margins, gutters = grid_engine.calculate_geometries(four_plots_ordered, FreeConfig())
        assert geometries == {}
        # Returns default (0,0,0,0) margins and empty gutters on error
        assert margins.top == 0.0
        assert gutters.hspace == []

    def test_calculate_geometries_variable_ratios(self, grid_engine, four_plots_ordered):
        """Tests grid calculation with non-equal ratios."""
        config = GridConfig(
            rows=1, cols=2,
            row_ratios=[1.0], col_ratios=[0.25, 0.75],
            margins=Margins(0.1, 0.1, 0.1, 0.1),
            gutters=Gutters([], [0.05])
        )
        # Net width = 0.75. Col0 = 0.75*0.25=0.1875. Col1 = 0.75*0.75=0.5625.
        
        geometries, _, _ = grid_engine.calculate_geometries(four_plots_ordered[:2], config)
        
        # p2 sorted before p1. p2 in col0, p1 in col1.
        assert geometries["p2"] == pytest.approx((0.1, 0.1, 0.1875, 0.8))
        assert geometries["p1"] == pytest.approx((0.1 + 0.1875 + 0.05, 0.1, 0.5625, 0.8))

    def test_apply_constrained_layout_logic(self, grid_engine, four_plots_ordered, simple_grid_config, mocker):
        """Verifies that use_constrained_optimization toggles the correct internal method."""
        # We don't want to actually run the complex matplotlib engine in a unit test if possible,
        # but we should verify the return structure of the calculated values.
        
        # Mock _apply_constrained_layout to avoid matplotlib overhead and return dummy values
        mock_ret = ({}, {"p1": (0,0,1,1)}, Margins(0.05, 0.05, 0.05, 0.05), Gutters([0.02], [0.02]))
        mocker.patch.object(grid_engine, "_apply_constrained_layout", return_value=mock_ret)
        
        geometries, margins, gutters = grid_engine.calculate_geometries(
            four_plots_ordered, simple_grid_config, use_constrained_optimization=True
        )
        
        grid_engine._apply_constrained_layout.assert_called_once()
        assert margins.top == 0.05
        assert gutters.hspace == [0.02]
