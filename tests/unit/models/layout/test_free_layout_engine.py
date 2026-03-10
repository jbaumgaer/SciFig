import pytest
from unittest.mock import MagicMock

from src.models.layout.free_layout_engine import FreeLayoutEngine
from src.models.layout.layout_config import FreeConfig, GridConfig, NO_GUTTERS, NO_MARGINS
from src.models.nodes.plot_node import PlotNode
from src.shared.geometry import Rect
from src.models.layout.layout_protocols import FreeFormLayoutCapabilities


@pytest.fixture
def free_engine():
    """Provides a FreeLayoutEngine instance."""
    return FreeLayoutEngine()


@pytest.fixture
def free_config():
    """Provides a FreeConfig instance."""
    return FreeConfig()


@pytest.fixture
def defined_plots():
    p1 = PlotNode(id="p1")
    p1.geometry = Rect(0.1, 0.1, 0.2, 0.2)
    p2 = PlotNode(id="p2")
    p2.geometry = Rect(0.5, 0.5, 0.3, 0.3)
    return [p1, p2]


class TestFreeLayoutEngine:

    def test_calculate_geometries_passthrough(self, free_engine, defined_plots, free_config):
        """Verifies that FreeLayoutEngine returns original geometries and None for margins/gutters."""
        geometries, margins, gutters = free_engine.calculate_geometries(defined_plots, free_config, (20, 15))
        
        assert len(geometries) == 2
        assert geometries["p1"] == Rect(0.1, 0.1, 0.2, 0.2)
        assert geometries["p2"] == Rect(0.5, 0.5, 0.3, 0.3)
        assert margins is None
        assert gutters is None

    def test_calculate_geometries_incompatible_config(self, free_engine, defined_plots):
        """Verifies error handling for incompatible config types."""
        invalid_config = GridConfig(1, 1, [1], [1], NO_MARGINS, NO_GUTTERS)
        geometries, margins, gutters = free_engine.calculate_geometries(defined_plots, invalid_config, (20, 15))
        
        assert geometries == {}
        assert margins is None
        assert gutters is None

    def test_perform_align_left(self, free_engine, defined_plots):
        """Tests left alignment logic."""
        geometries = free_engine.perform_align(defined_plots, "left")
        assert geometries["p1"].x == pytest.approx(0.1)
        assert geometries["p2"].x == pytest.approx(0.1)
        # y and size should be preserved
        assert geometries["p1"].y == 0.1
        assert geometries["p2"].y == 0.5

    def test_perform_align_right(self, free_engine, defined_plots):
        """Tests right alignment logic."""
        # p1: x=0.1, w=0.2 (right=0.3). p2: x=0.5, w=0.3 (right=0.8)
        # target_right = 0.8
        geometries = free_engine.perform_align(defined_plots, "right")
        assert geometries["p1"].x == pytest.approx(0.6) # 0.8 - 0.2
        assert geometries["p2"].x == pytest.approx(0.5) # 0.8 - 0.3

    def test_perform_align_top(self, free_engine, defined_plots):
        """Tests top alignment logic."""
        # p1: y=0.1, h=0.2 (top=0.3). p2: y=0.5, h=0.3 (top=0.8)
        # target_top = 0.8
        geometries = free_engine.perform_align(defined_plots, "top")
        assert geometries["p1"].y == pytest.approx(0.6) # 0.8 - 0.2
        assert geometries["p2"].y == pytest.approx(0.5) # 0.8 - 0.3

    def test_perform_align_bottom(self, free_engine, defined_plots):
        """Tests bottom alignment logic."""
        geometries = free_engine.perform_align(defined_plots, "bottom")
        assert geometries["p1"].y == pytest.approx(0.1)
        assert geometries["p2"].y == pytest.approx(0.1)

    def test_perform_distribute_horizontal(self, free_engine):
        """Tests horizontal distribution."""
        p1 = PlotNode(id="d1"); p1.geometry = Rect(0.1, 0.1, 0.1, 0.1)
        p2 = PlotNode(id="d2"); p2.geometry = Rect(0.2, 0.1, 0.1, 0.1)
        p3 = PlotNode(id="d3"); p3.geometry = Rect(0.7, 0.1, 0.1, 0.1)
        plots = [p1, p2, p3]
        
        # items: (d1, 0.1), (d2, 0.2), (d3, 0.7)
        # min_x=0.1, max_right=0.8. total_plot_width=0.3. spacing = (0.8 - 0.1 - 0.3) / 2 = 0.4 / 2 = 0.2
        # d1: 0.1
        # d2: 0.1 + 0.1 + 0.2 = 0.4
        # d3: 0.4 + 0.1 + 0.2 = 0.7
        geometries = free_engine.perform_distribute(plots, "horizontal")
        assert geometries["d1"].x == pytest.approx(0.1)
        assert geometries["d2"].x == pytest.approx(0.4)
        assert geometries["d3"].x == pytest.approx(0.7)

    def test_perform_distribute_edge_cases(self, free_engine):
        """Verifies distribution no-ops for fewer than 2 plots."""
        assert free_engine.perform_distribute([], "horizontal") == {}
        p1 = PlotNode(id="p1")
        assert free_engine.perform_distribute([p1], "horizontal") == {}

    def test_perform_align_edge_cases(self, free_engine):
        """Verifies alignment no-ops for empty plot list."""
        assert free_engine.perform_align([], "left") == {}

    def test_protocol_implementation(self, free_engine):
        """Verifies that FreeLayoutEngine implements FreeFormLayoutCapabilities protocol at runtime."""
        assert isinstance(free_engine, FreeFormLayoutCapabilities)
