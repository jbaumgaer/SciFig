import pytest
from unittest.mock import MagicMock
from PySide6.QtWidgets import QGraphicsScene, QGraphicsRectItem
from PySide6.QtCore import QPointF, QRectF
from matplotlib.figure import Figure

from src.ui.renderers.overlay_renderer import OverlayRenderer
from src.models.nodes.plot_node import PlotNode
from src.models.nodes.grid_node import GridNode
from src.shared.geometry import Rect
from src.shared.events import Events
from src.shared.constants import LayoutMode


@pytest.fixture
def mock_scene(qtbot):
    """Provides a fresh QGraphicsScene."""
    return QGraphicsScene()


@pytest.fixture
def mock_figure():
    """Provides a real matplotlib Figure for coordinate math."""
    fig = Figure(figsize=(5, 4), dpi=100)
    return fig


@pytest.fixture
def renderer(mock_scene, mock_figure, mock_application_model, real_event_aggregator):
    """Provides an OverlayRenderer instance wired to a mock model and real event bus."""
    return OverlayRenderer(mock_scene, mock_figure, mock_application_model, real_event_aggregator)


class TestOverlayRenderer:
    """
    Unit tests for OverlayRenderer.
    Verifies that the renderer reactively updates the Qt scene in response to events.
    """

    def test_selection_changed_triggers_handles(self, renderer, mock_scene, mock_application_model, real_event_aggregator):
        """Verifies that publishing SELECTION_CHANGED draws handles."""
        from src.models.nodes.plot_node import PlotNode
        mock_node = MagicMock(spec=PlotNode)
        mock_node.id = "p1"
        # Physical CM geometry
        mock_node.geometry = Rect(5.0, 5.0, 10.0, 10.0)
        mock_application_model.scene_root.find_node_by_id.return_value = mock_node
        
        # Trigger event
        real_event_aggregator.publish(Events.SELECTION_CHANGED, selected_node_ids=["p1"])
        
        # Check scene items (8 handles)
        rect_items = [i for i in mock_scene.items() if isinstance(i, QGraphicsRectItem) and i.zValue() == 1100]
        assert len(rect_items) == 8

    def test_update_previews_event_draws_ghosts(self, renderer, mock_scene, real_event_aggregator):
        """Verifies that publishing UPDATE_INTERACTION_PREVIEW_REQUESTED draws ghosts."""
        # 5cm x 5cm preview
        geoms = [Rect(2.0, 2.0, 5.0, 5.0)]
        
        real_event_aggregator.publish(
            Events.UPDATE_INTERACTION_PREVIEW_REQUESTED, 
            geometries=geoms, 
            style="ghost"
        )
        
        # Check scene items (ghost has zValue 1000)
        rect_items = [i for i in mock_scene.items() if isinstance(i, QGraphicsRectItem) and i.zValue() == 1000]
        assert len(rect_items) == 1
        assert rect_items[0].brush().color().alpha() < 255

    def test_clear_previews_event(self, renderer, mock_scene, real_event_aggregator):
        """Verifies that publishing CLEAR_INTERACTION_PREVIEW_REQUESTED removes ghosts."""
        # 1. Add ghosts
        renderer._on_update_previews_request([Rect(0,0,1,1)], style="ghost")
        assert len(renderer._ghost_items) == 1
        
        # 2. Trigger clear event
        real_event_aggregator.publish(Events.CLEAR_INTERACTION_PREVIEW_REQUESTED)
        
        assert len(renderer._ghost_items) == 0
        assert len(mock_scene.items()) == 0

    def test_fig_to_scene_math(self, renderer, mock_application_model):
        """Verifies coordinate translation logic from CM to Pixels."""
        # mock_application_model.figure_size is (20.0, 15.0) from conftest
        # mock_figure extent is 5*100 x 4*100 = 500x400 from fixture
        
        # 10.0 cm (Center X) on 20.0 cm figure -> 0.5 fractional -> 250px
        # 7.5 cm (Center Y) on 15.0 cm figure -> 0.5 fractional -> 200px
        scene_pos = renderer._fig_to_scene((10.0, 7.5))
        assert scene_pos.x() == pytest.approx(250)
        assert scene_pos.y() == pytest.approx(200)
        
        # Bottom-Left (0,0) CM -> Qt (0, 400)
        scene_pos = renderer._fig_to_scene((0, 0))
        assert scene_pos.x() == 0
        assert scene_pos.y() == 400

    def test_grid_overlay_rendering(self, renderer, mock_scene, mock_application_model, real_event_aggregator):
        """Verifies that GridNode overlays are drawn in GRID mode."""
        # Setup GRID mode
        mock_application_model.current_layout_config.mode = LayoutMode.GRID
        
        # Setup a GridNode
        grid = GridNode(id="g1")
        grid.geometry = Rect(0, 0, 10, 10)
        mock_application_model.scene_root.all_descendants.return_value = [grid]
        
        # Trigger redraw via scene graph change
        real_event_aggregator.publish(Events.SCENE_GRAPH_CHANGED)
        
        # Check grid items (lattice border has zValue 500)
        grid_items = [i for i in mock_scene.items() if i.zValue() == 500]
        assert len(grid_items) == 1
        assert isinstance(grid_items[0], QGraphicsRectItem)

    def test_ink_box_ghost_rendering(self, renderer, mock_scene, mock_application_model, real_event_aggregator):
        """Verifies that selected plots draw an Ink-Box ghost."""
        # Setup PlotNode
        node = PlotNode(id="p1")
        node.geometry = Rect(2, 2, 5, 5)
        mock_application_model.scene_root.find_node_by_id.return_value = node
        
        # Select node
        real_event_aggregator.publish(Events.SELECTION_CHANGED, selected_node_ids=["p1"])
        
        # Check ink-box (zValue 985)
        ink_boxes = [i for i in mock_scene.items() if i.zValue() == 985]
        assert len(ink_boxes) == 1
        assert isinstance(ink_boxes[0], QGraphicsRectItem)

    def test_clear_grid_items(self, renderer, mock_scene, mock_application_model, real_event_aggregator):
        """Verifies that grid items are cleared correctly."""
        # 1. Add grid and ink-box
        mock_application_model.current_layout_config.mode = LayoutMode.GRID
        node = PlotNode(id="p1")
        node.geometry = Rect(0,0,1,1)
        mock_application_model.scene_root.find_node_by_id.return_value = node
        mock_application_model.scene_root.all_descendants.return_value = [] # No grids for now
        
        real_event_aggregator.publish(Events.SELECTION_CHANGED, selected_node_ids=["p1"])
        assert len(renderer._grid_items) > 0
        
        # 2. Clear all
        renderer.clear_all()
        assert len(renderer._grid_items) == 0
        # Only check grid z-values to ensure lattice and ink-box are gone
        remaining = [i for i in mock_scene.items() if i.zValue() in (500, 985)]
        assert len(remaining) == 0
