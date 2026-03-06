import pytest
from unittest.mock import MagicMock, ANY, patch, create_autospec
import matplotlib.figure
import matplotlib.axes
import matplotlib.axis
from src.ui.renderers.renderer import Renderer
from src.models.nodes.plot_node import PlotNode
from src.models.nodes.scene_node import SceneNode
from src.shared.events import Events


@pytest.fixture
def renderer(mock_layout_manager, mock_application_model, mock_event_aggregator):
    """Provides a Renderer instance with mocked dependencies."""
    # Ensure scene_root is hit-testable and visible for recursion
    mock_application_model.scene_root.visible = True
    return Renderer(
        layout_manager=mock_layout_manager,
        application_model=mock_application_model,
        event_aggregator=mock_event_aggregator
    )


class TestRenderer:

    # --- Core Orchestration ---

    def test_render_plots_delegates_to_strategies(self, renderer, mock_application_model, mock_layout_manager):
        """Verifies that rendering PlotNodes uses coordinate and artist strategies."""
        mock_fig = MagicMock(spec=matplotlib.figure.Figure)
        mock_fig.artists = [] # Required for _render_highlights
        
        # Setup: 1 PlotNode
        node = PlotNode(id="p1")
        node.plot_properties = MagicMock()
        node.plot_properties._version = 1
        node.plot_properties.coords = MagicMock()
        node.plot_properties.coords.coord_type = "cartesian_2d"
        mock_application_model.scene_root.all_descendants.return_value = [node]
        
        # Setup: Layout
        mock_layout_manager.get_current_layout_geometries.return_value = {"p1": (0,0,1,1)}
        
        # Mock Strategies
        mock_coord_strategy = MagicMock()
        mock_ax = MagicMock(spec=matplotlib.axes.Axes)
        mock_coord_strategy.create_axes.return_value = mock_ax
        renderer._coord_strategies["cartesian_2d"] = mock_coord_strategy
        
        # Render
        renderer.render(mock_fig, mock_application_model.scene_root, [])
        
        # Verify coordination
        mock_coord_strategy.create_axes.assert_called_once_with(mock_fig, (0,0,1,1))
        mock_coord_strategy.sync.assert_called_once()
        assert renderer._axes_registry["p1"] is mock_ax

    # --- Version Gating ---

    def test_render_skips_unchanged_versions(self, renderer, mock_application_model, mock_layout_manager):
        """Ensures the renderer doesn't re-sync if the model version hasn't increased."""
        node = PlotNode(id="p1")
        # Ensure _version is a real integer and nested objects exist for the initial checks
        node.plot_properties = MagicMock()
        node.plot_properties._version = 5
        node.plot_properties.coords = MagicMock()
        node.plot_properties.coords.coord_type = "cartesian_2d"
        
        # Identity is critical here: return the EXACT node instance
        mock_application_model.scene_root.all_descendants.return_value = [node]
        mock_layout_manager.get_current_layout_geometries.return_value = {"p1": (0,0,1,1)}
        
        # last_synced >= current_version should trigger the skip in _sync_plot_node
        renderer._last_synced_versions["p1"] = 5
        renderer._axes_registry["p1"] = MagicMock()
        
        # Mock Figure to avoid highlight cleanup errors
        mock_fig = MagicMock()
        mock_fig.artists = []

        # We mock _sync_artists (deeper level) to be absolutely sure we're skipping sync
        with patch.object(renderer, "_sync_artists") as mock_sync_artists:
            renderer.render(mock_fig, mock_application_model.scene_root, [])
            mock_sync_artists.assert_not_called()

    # --- Back-Sync (Reconciliation) ---

    def test_sync_back_limits_publishes_event_on_mismatch(self, renderer, mock_application_model, mock_event_aggregator):
        """Tests that user-driven axis changes in Matplotlib are detected and sent for reconciliation."""
        node = PlotNode(id="p1")
        node.plot_properties = MagicMock()
        node.plot_properties.coords.xaxis.limits = (0, 10)
        node.plot_properties.coords.yaxis.limits = (0, 10)
        mock_application_model.scene_root.find_node_by_id.return_value = node
        
        # Setup real axes state that differs from model
        mock_ax = MagicMock(spec=matplotlib.axes.Axes)
        mock_ax.get_xlim.return_value = (0, 20) # User zoomed out
        mock_ax.get_ylim.return_value = (0, 10) # No change
        renderer._axes_registry["p1"] = mock_ax
        
        # Trigger sync
        renderer.sync_back_limits("p1")
        
        # Verify event publication for X only
        mock_event_aggregator.publish.assert_called_once_with(
            Events.PLOT_COMPONENT_RECONCILIATION_REQUESTED,
            node_id="p1",
            path="coords.xaxis.limits",
            value=(0.0, 20.0)
        )

    # --- Property Synchronization ---

    def test_apply_property_direct_setters(self, renderer):
        """Tests the fallback setter logic (set_<field_name>)."""
        mock_obj = MagicMock()
        renderer._apply_property(mock_obj, "linewidth", 2.0)
        mock_obj.set_linewidth.assert_called_once_with(2.0)

    def test_apply_property_translation_overrides(self, renderer, mocker):
        """Tests that the _SETTER_MAP overrides standard naming conventions."""
        mock_ax = MagicMock(spec=matplotlib.axes.Axes)
        # Use a real Axis object type for type(obj).__name__ to match 'XAxis'
        mock_xaxis = MagicMock(spec=matplotlib.axis.XAxis)
        mock_xaxis.axes = mock_ax
        
        # We must ensure type(mock_xaxis).__name__ is "XAxis"
        mocker.patch("src.ui.renderers.renderer.type", return_value=MagicMock(__name__="XAxis"))
        
        # Limits is a translated property in _SETTER_MAP for XAxis
        renderer._apply_property(mock_xaxis, "limits", (10, 20))
        
        # Should call set_xlim on the parent axes
        mock_ax.set_xlim.assert_called_once_with(10, 20)

    # --- Cleanup ---

    def test_handle_node_removal_destroys_axes(self, renderer):
        """Verifies that deleting a node removes its Matplotlib axes."""
        mock_fig = MagicMock()
        mock_ax = MagicMock()
        mock_ax.figure = mock_fig
        renderer._axes_registry["p1"] = mock_ax
        renderer._last_synced_versions["p1"] = 1
        
        renderer.handle_node_removal("root", "p1")
        
        assert "p1" not in renderer._axes_registry
        assert "p1" not in renderer._last_synced_versions
        mock_fig.delaxes.assert_called_once_with(mock_ax)

    # --- Highlights ---

    def test_render_highlights_selection(self, renderer, mock_application_model):
        """Tests drawing blue selection rectangle around selected nodes."""
        mock_fig = MagicMock()
        mock_fig.artists = []
        
        node = PlotNode(name="Selected")
        node.geometry = (0.1, 0.1, 0.2, 0.2)
        
        renderer.render(mock_fig, mock_application_model.scene_root, [node])
        
        # Verify that a Rectangle was added to the figure artists
        mock_fig.add_artist.assert_called_once()
        highlight = mock_fig.add_artist.call_args[0][0]
        assert highlight.get_gid() == "selection_highlight"
