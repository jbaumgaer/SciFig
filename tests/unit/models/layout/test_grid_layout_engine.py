import pytest
from unittest.mock import MagicMock

from src.models.layout.grid_layout_engine import GridLayoutEngine
from src.models.layout.layout_config import FreeConfig, GridConfig, Gutters, Margins
from src.models.nodes.plot_node import PlotNode
from src.shared.geometry import Rect


@pytest.fixture
def grid_engine():
    """Provides a GridLayoutEngine instance."""
    return GridLayoutEngine()


@pytest.fixture
def simple_grid_config():
    """Provides a basic 2x2 grid configuration in physical CM."""
    return GridConfig(
        rows=2,
        cols=2,
        row_ratios=[1.0, 1.0],
        col_ratios=[1.0, 1.0],
        margins=Margins(2.0, 2.0, 2.0, 2.0), # 2cm margins all around
        gutters=Gutters([1.0], [1.0]),       # 1cm gap
    )


@pytest.fixture
def four_plots():
    """Provides 4 plots with diverse initial positions for sorting verification."""
    # Note: Initial positions are in CM now
    p1 = PlotNode(id="p1", name="p1"); p1.geometry = Rect(2.0, 12.0, 6.0, 6.0)
    p2 = PlotNode(id="p2", name="p2"); p2.geometry = Rect(10.0, 14.0, 6.0, 4.0)
    p3 = PlotNode(id="p3", name="p3"); p3.geometry = Rect(1.0, 2.0, 8.0, 8.0)
    p4 = PlotNode(id="p4", name="p4"); p4.geometry = Rect(12.0, 4.0, 7.0, 7.0)
    return [p1, p2, p3, p4]


class TestGridLayoutEngine:

    def test_calculate_geometries_fixed_layout(self, grid_engine, four_plots, simple_grid_config):
        """Verifies geometry calculation for a fixed 2x2 grid in CM space."""
        # Figure size: 20x15 cm
        # Plot area: 20 - 2(L) - 2(R) = 16cm. Gutter=1cm. Net plot width = 15cm. Cell=7.5cm
        # Plot area: 15 - 2(T) - 2(B) = 11cm. Gutter=1cm. Net plot height = 10cm. Cell=5.5cm
        
        fig_size = (20.0, 15.0)
        geometries, margins, gutters = grid_engine.calculate_geometries(
            four_plots, simple_grid_config, figure_size_cm=fig_size, use_constrained_optimization=False
        )
        
        assert len(geometries) == 4
        assert margins == simple_grid_config.margins
        assert gutters == simple_grid_config.gutters
        
        # Sorting (-y, x): 
        # p2: y=14 -> -14, x=10
        # p1: y=12 -> -12, x=2
        # p4: y=4 -> -4, x=12
        # p3: y=2 -> -2, x=1
        # Expected order: p2, p1, p4, p3
        
        # Verify p2 (Top-Left cell)
        assert isinstance(geometries["p2"], Rect)
        assert geometries["p2"].x == pytest.approx(2.0)
        assert geometries["p2"].width == pytest.approx(7.5) # (16 - 1) / 2
        assert geometries["p2"].height == pytest.approx(5.0) # (11 - 1) / 2
        
        # Verify p1 (Top-Right cell)
        assert geometries["p1"].x == pytest.approx(2.0 + 7.5 + 1.0) # margin + cell + gutter

    def test_calculate_geometries_zero_plots(self, grid_engine, simple_grid_config):
        """Verifies that empty plot list returns empty dict."""
        geometries, margins, gutters = grid_engine.calculate_geometries([], simple_grid_config, (20, 15))
        assert geometries == {}

    def test_calculate_geometries_incompatible_config(self, grid_engine, four_plots):
        """Verifies error handling for incompatible config."""
        geometries, margins, gutters = grid_engine.calculate_geometries(four_plots, FreeConfig(), (20, 15))
        assert geometries == {}

    def test_calculate_geometries_variable_ratios(self, grid_engine, four_plots):
        """Tests grid calculation with non-equal ratios in CM."""
        # Figure: 20x15 cm. Margins: 2cm.
        # Net Width: 16cm. Gutter: 1cm. Available for plots: 15cm.
        # Col 0 (0.25): 3.75 cm. Col 1 (0.75): 11.25 cm.
        config = GridConfig(
            rows=1, cols=2,
            row_ratios=[1.0], col_ratios=[0.25, 0.75],
            margins=Margins(2.0, 2.0, 2.0, 2.0),
            gutters=Gutters([], [1.0])
        )
        
        geometries, _, _ = grid_engine.calculate_geometries(
            four_plots[:2], config, figure_size_cm=(20, 15)
        )
        
        # p2 sorted before p1 based on (-y, x) -> p2(14), p1(12)
        assert isinstance(geometries["p2"], Rect)
        assert isinstance(geometries["p1"], Rect)
        assert geometries["p2"].width == pytest.approx(3.75)
        assert geometries["p1"].width == pytest.approx(11.25)
        assert geometries["p1"].x == pytest.approx(2.0 + 3.75 + 1.0) # margin + col0 + gutter

    def test_calculate_geometries_excessive_margins(self, grid_engine):
        """Verifies that engine falls back to minimum 0.2cm plot size when margins exceed figure size."""
        # Figure: 10x10 cm. Margins: 6cm each (Total 12cm > 10cm)
        config = GridConfig(
            rows=1, cols=1,
            row_ratios=[1.0], col_ratios=[1.0],
            margins=Margins(6.0, 6.0, 6.0, 6.0),
            gutters=Gutters([], [])
        )
        p1 = PlotNode(id="p1"); p1.geometry = Rect(0,0,1,1)
        
        geometries, _, _ = grid_engine.calculate_geometries([p1], config, figure_size_cm=(10, 10))
        
        assert "p1" in geometries
        assert geometries["p1"].width == pytest.approx(0.2)
        assert geometries["p1"].height == pytest.approx(0.2)

    def test_apply_constrained_layout_logic(self, grid_engine, four_plots, simple_grid_config, mocker):
        """Verifies that use_constrained_optimization toggles the correct internal method."""
        mock_ret = ({}, {"p1": Rect(0,0,1,1)}, Margins(1,1,1,1), Gutters([0.5], [0.5]))
        mocker.patch.object(grid_engine, "_apply_constrained_layout", return_value=mock_ret)
        
        grid_engine.calculate_geometries(
            four_plots, simple_grid_config, figure_size_cm=(20, 15), use_constrained_optimization=True
        )
        
        grid_engine._apply_constrained_layout.assert_called_once()
