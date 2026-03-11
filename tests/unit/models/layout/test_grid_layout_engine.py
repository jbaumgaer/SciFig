import pytest
from src.models.layout.grid_layout_engine import GridLayoutEngine
from src.models.nodes.grid_node import GridNode, GridPosition
from src.models.nodes.plot_node import PlotNode
from src.shared.geometry import Rect

class TestGridLayoutEngine:
    @pytest.fixture
    def engine(self):
        return GridLayoutEngine()

    def test_single_cell_grid(self, engine):
        """Tests layout for a 1x1 grid with margins."""
        root = GridNode(rows=1, cols=1)
        root.margins = root.margins.__class__(top=1.0, bottom=1.0, left=1.0, right=1.0)
        plot = PlotNode(name="Plot1", parent=root)
        plot.grid_position = GridPosition(row=0, col=0)
        
        engine.calculate_geometries(root, (10.0, 10.0))
        
        # Plot should be centered within margins: 10 - 1 - 1 = 8
        assert plot.geometry == Rect(1.0, 1.0, 8.0, 8.0)
        assert plot._geometry_version == 1

    def test_simple_2x2_grid(self, engine):
        """Tests layout for a 2x2 grid with uniform ratios and gutters."""
        root = GridNode(rows=2, cols=2)
        root.gutters = root.gutters.__class__(hspace=[1.0], wspace=[1.0])
        
        # Assign 4 plots
        plots = []
        for r in range(2):
            for c in range(2):
                p = PlotNode(name=f"P{r}{c}", parent=root)
                p.grid_position = GridPosition(row=r, col=c)
                plots.append(p)
        
        # Fig 11x11cm. Margins 0. 
        # Gutters take 1cm. Content area = 10x10.
        # Each cell = 5x5.
        engine.calculate_geometries(root, (11.0, 11.0))
        
        # In Bottom-Up: Row 0 is at Top (High Y), Row 1 is at Bottom (Low Y)
        # P00: (0, 6, 5, 5) -> Row 0 (Top), Col 0 (Left)
        assert plots[0].geometry == Rect(0.0, 6.0, 5.0, 5.0)
        # P01: (6, 6, 5, 5) -> Row 0 (Top), Col 1 (Right)
        assert plots[1].geometry == Rect(6.0, 6.0, 5.0, 5.0)
        # P10: (0, 0, 5, 5) -> Row 1 (Bottom), Col 0 (Left)
        assert plots[2].geometry == Rect(0.0, 0.0, 5.0, 5.0)
        # P11: (6, 0, 5, 5) -> Row 1 (Bottom), Col 1 (Right)
        assert plots[3].geometry == Rect(6.0, 0.0, 5.0, 5.0)

    def test_nested_grid(self, engine):
        """Tests recursive layout for a grid within a grid."""
        # Root: 2 columns, 1 row. Col Ratios [1, 1]. Fig 21cm wide.
        # Gutter 1cm. Each root cell = 10cm wide.
        root = GridNode(rows=1, cols=2)
        root.gutters = root.gutters.__class__(hspace=[], wspace=[1.0])
        
        # Left child: a PlotNode
        p_left = PlotNode(name="Left", parent=root)
        p_left.grid_position = GridPosition(row=0, col=0)
        
        # Right child: a Nested Grid (2 rows, 1 col)
        nested = GridNode(name="Nested", parent=root, rows=2, cols=1)
        nested.grid_position = GridPosition(row=0, col=1)
        nested.gutters = nested.gutters.__class__(hspace=[2.0], wspace=[])
        
        # Nested children
        p_top = PlotNode(name="Top", parent=nested)
        p_top.grid_position = GridPosition(row=0, col=0)
        p_bottom = PlotNode(name="Bottom", parent=nested)
        p_bottom.grid_position = GridPosition(row=1, col=0)
        
        # Execute
        engine.calculate_geometries(root, (21.0, 12.0))
        
        # Verify Left Plot
        assert p_left.geometry == Rect(0.0, 0.0, 10.0, 12.0)
        
        # Verify Nested Grid geometry (assigned by parent)
        assert nested.geometry == Rect(11.0, 0.0, 10.0, 12.0)
        
        # Verify Nested Plots (assigned recursively)
        # Content area height = 12 - 2 (gutter) = 10. Each cell height = 5.
        # Top Plot (Row 0) -> y = 5 + 2 = 7
        assert p_top.geometry == Rect(11.0, 7.0, 10.0, 5.0)
        # Bottom Plot (Row 1) -> y = 0
        assert p_bottom.geometry == Rect(11.0, 0.0, 10.0, 5.0)

    def test_spanning_plot(self, engine):
        """Tests layout for a plot spanning multiple rows/cols."""
        root = GridNode(rows=2, cols=2)
        root.gutters = root.gutters.__class__(hspace=[1.0], wspace=[1.0])
        
        # Plot spanning entire bottom row
        p_span = PlotNode(name="Span", parent=root)
        p_span.grid_position = GridPosition(row=1, col=0, rowspan=1, colspan=2)
        
        # Fig 11x11. Cells 5x5.
        engine.calculate_geometries(root, (11.0, 11.0))
        
        # In Bottom-Up: Row 1 is at the bottom (y=0)
        assert p_span.geometry == Rect(0.0, 0.0, 11.0, 5.0)

    def test_version_gating(self, engine):
        """Tests that _geometry_version only increments on actual change."""
        root = GridNode(rows=1, cols=1)
        plot = PlotNode(parent=root)
        plot.grid_position = GridPosition(row=0, col=0)
        
        # Initial calc
        engine.calculate_geometries(root, (10.0, 10.0))
        v1 = plot._geometry_version
        assert v1 == 1
        
        # Re-calc with same parameters
        engine.calculate_geometries(root, (10.0, 10.0))
        assert plot._geometry_version == v1
        
        # Calc with change
        engine.calculate_geometries(root, (20.0, 20.0))
        assert plot._geometry_version == v1 + 1
