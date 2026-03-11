import pytest
from src.models.nodes.grid_node import GridNode, GridPosition
from src.models.nodes.scene_node import SceneNode, node_factory
from src.models.layout.layout_config import Gutters, Margins

class TestGridPosition:
    def test_grid_position_init(self):
        """Tests basic initialization of GridPosition."""
        pos = GridPosition(row=1, col=2, rowspan=2, colspan=3)
        assert pos.row == 1
        assert pos.col == 2
        assert pos.rowspan == 2
        assert pos.colspan == 3

    def test_grid_position_defaults(self):
        """Tests default values for spans."""
        pos = GridPosition(row=0, col=0)
        assert pos.rowspan == 1
        assert pos.colspan == 1

    def test_grid_position_serialization(self):
        """Tests to_dict and from_dict for GridPosition."""
        pos = GridPosition(row=1, col=1, rowspan=2, colspan=2)
        data = pos.to_dict()
        assert data == {"row": 1, "col": 1, "rowspan": 2, "colspan": 2}
        
        pos2 = GridPosition.from_dict(data)
        assert pos2 == pos

class TestGridNode:
    def test_grid_node_init(self):
        """Tests initialization of GridNode with default grid parameters."""
        node = GridNode(rows=2, cols=3, name="MyGrid")
        assert node.rows == 2
        assert node.cols == 3
        assert node.name == "MyGrid"
        assert len(node.row_ratios) == 2
        assert len(node.col_ratios) == 3
        assert all(r == 1.0 for r in node.row_ratios)
        assert len(node.gutters.hspace) == 1
        assert len(node.gutters.wspace) == 2

    def test_grid_node_serialization(self):
        """Tests recursive serialization of GridNode."""
        grid = GridNode(rows=2, cols=2, id="grid_1")
        grid.row_ratios = [1.0, 2.0]
        grid.gutters = Gutters(hspace=[0.8], wspace=[0.8])
        
        data = grid.to_dict()
        assert data["type"] == "GridNode"
        assert data["rows"] == 2
        assert data["row_ratios"] == [1.0, 2.0]
        assert data["gutters"]["hspace"] == [0.8]
        
        # Test reconstruction
        grid2 = GridNode.from_dict(data)
        assert grid2.id == "grid_1"
        assert grid2.rows == 2
        assert grid2.row_ratios == [1.0, 2.0]
        assert grid2.gutters.hspace == [0.8]

    def test_node_factory_integration(self):
        """Tests that node_factory correctly creates a GridNode and its children."""
        data = {
            "id": "root_grid",
            "type": "GridNode",
            "name": "Root",
            "visible": True,
            "rows": 2,
            "cols": 1,
            "children": [
                {
                    "id": "child_plot",
                    "type": "PlotNode",
                    "name": "Plot 1",
                    "visible": True,
                    "grid_position": {"row": 0, "col": 0, "rowspan": 1, "colspan": 1},
                    "children": []
                }
            ]
        }
        
        root = node_factory(data)
        assert isinstance(root, GridNode)
        assert root.rows == 2
        assert len(root.children) == 1
        
        child = root.children[0]
        assert child.grid_position is not None
        assert child.grid_position.row == 0
        assert child.id == "child_plot"

class TestSceneNodeGridIntegration:
    def test_scene_node_has_grid_attributes(self):
        """Tests that the base SceneNode has the necessary grid-related attributes."""
        node = SceneNode()
        assert hasattr(node, "grid_position")
        assert node.grid_position is None
        assert hasattr(node, "_geometry_version")
        assert node._geometry_version == 0

    def test_grid_position_assignment(self):
        """Tests assigning a GridPosition to a SceneNode."""
        node = SceneNode()
        pos = GridPosition(row=5, col=5)
        node.grid_position = pos
        
        data = node.to_dict()
        assert data["grid_position"] == {"row": 5, "col": 5, "rowspan": 1, "colspan": 1}
        
        node2 = SceneNode.from_dict(data)
        assert node2.grid_position == pos
