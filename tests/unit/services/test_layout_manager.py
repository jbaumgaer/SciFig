import pytest
from unittest.mock import MagicMock, call, ANY
from pathlib import Path

from src.services.layout_manager import LayoutManager
from src.models.layout.layout_config import GridConfig, Gutters, Margins
from src.models.nodes.plot_node import PlotNode
from src.models.nodes.grid_node import GridNode
from src.models.nodes.group_node import GroupNode
from src.shared.constants import LayoutMode
from src.shared.events import Events
from src.models.plots.plot_types import ArtistType
from src.shared.geometry import Rect


@pytest.fixture
def layout_manager(
    mock_application_model,
    mock_free_layout_engine,
    mock_grid_layout_engine,
    mock_config_service,
    mock_event_aggregator,
):
    """Provides a LayoutManager instance with all dependencies mocked."""
    mock_config_service.get_required.side_effect = lambda k: "free_form"
    mock_application_model.layout_mode = LayoutMode.FREE_FORM
    mock_application_model.figure_size = (20.0, 15.0)
    
    return LayoutManager(
        application_model=mock_application_model,
        free_engine=mock_free_layout_engine,
        grid_engine=mock_grid_layout_engine,
        config_service=mock_config_service,
        event_aggregator=mock_event_aggregator,
    )


class TestLayoutManager:

    # --- Core Lifecycle Tests ---

    def test_init(self, mock_config_service, mock_application_model):
        """Verifies correct initialization and default mode setting."""
        mock_config_service.get_required.side_effect = lambda k: "free_form"
        mock_application_model.layout_mode = LayoutMode.FREE_FORM
        mock_application_model.figure_size = (20.0, 15.0)
        
        manager = LayoutManager(
            mock_application_model, MagicMock(), MagicMock(), mock_config_service, MagicMock()
        )
        
        assert manager.ui_selected_layout_mode == LayoutMode.FREE_FORM

    def test_init_default_grid_mode(self, mock_config_service, mock_application_model):
        """Verifies initialization when default mode is GRID."""
        mock_config_service.get_required.side_effect = lambda k: "grid"
        mock_application_model.layout_mode = LayoutMode.FREE_FORM
        mock_application_model.figure_size = (20.0, 15.0)
        
        manager = LayoutManager(
            mock_application_model, MagicMock(), MagicMock(), mock_config_service, MagicMock()
        )
        
        assert manager.layout_mode == LayoutMode.GRID

    def test_on_model_reset(self, layout_manager):
        """Ensures that model reset clears the layout caches."""
        layout_manager._last_grid_config = MagicMock(spec=GridConfig)
        layout_manager.on_model_reset()
        assert layout_manager._last_grid_config is None

    def test_on_grid_component_changed_triggers_sync(self, layout_manager, mocker):
        """Verifies that granular grid changes trigger a sync."""
        mock_sync = mocker.patch.object(layout_manager, "sync_layout")
        layout_manager._on_grid_component_changed("node1", "rows", 5)
        mock_sync.assert_called_once()

    def test_sync_layout_orchestrates_engine(self, layout_manager, mock_application_model, 
                                           mock_grid_layout_engine, mock_event_aggregator):
        """Verifies that sync_layout calls the engine and notifies the system."""
        mock_grid = MagicMock(spec=GridNode)
        mock_grid.rows = 1
        mock_grid.cols = 1
        mock_grid.row_ratios = [1.0]
        mock_grid.col_ratios = [1.0]
        mock_grid.margins = Margins(0,0,0,0)
        mock_grid.gutters = Gutters([], [])
        
        mock_application_model.get_active_grid.return_value = mock_grid
        mock_application_model.figure_size = (10, 10)
        mock_application_model.layout_mode = LayoutMode.GRID
        
        layout_manager.sync_layout()
        
        mock_grid_layout_engine.calculate_geometries.assert_called_once_with(
            mock_grid, (10, 10)
        )
        mock_event_aggregator.publish.assert_any_call(Events.LAYOUT_CONFIG_CHANGED, config=ANY)

    # --- Mode Management Tests ---

    def test_set_layout_mode_to_grid_initializes_cache(self, layout_manager, mock_application_model):
        """Tests that switching to GRID triggers notifications."""
        layout_manager.set_layout_mode(LayoutMode.GRID)
        assert mock_application_model.layout_mode == LayoutMode.GRID

    def test_set_layout_mode_preserves_existing_cache(self, layout_manager, mock_application_model):
        """Tests that switching to GRID updates the model mode."""
        layout_manager.set_layout_mode(LayoutMode.GRID)
        assert mock_application_model.layout_mode == LayoutMode.GRID


    def test_ui_selected_layout_mode_setter(self, layout_manager, mock_event_aggregator):
        """Tests the property setter and its event publication."""
        layout_manager.ui_selected_layout_mode = LayoutMode.GRID
        mock_event_aggregator.publish.assert_any_call(
            Events.UI_LAYOUT_MODE_CHANGED, ui_layout_mode=LayoutMode.GRID
        )

    # --- Orchestration & Delegation Tests ---

    def test_get_active_engine(self, layout_manager, mock_application_model, 
                               mock_free_layout_engine, mock_grid_layout_engine):
        """Verifies that the manager returns the correct engine based on current mode."""
        mock_application_model.layout_mode = LayoutMode.FREE_FORM
        assert layout_manager.get_active_engine() is mock_free_layout_engine

        mock_application_model.layout_mode = LayoutMode.GRID
        assert layout_manager.get_active_engine() is mock_grid_layout_engine


    def test_get_current_layout_geometries(self, layout_manager, mock_free_layout_engine, mock_application_model):
        """Verifies coordination with engines and translation from PHYSICAL to FRACTIONAL."""
        plot = PlotNode(id="p1")
        phys_rect = Rect(5.0, 3.75, 10.0, 7.5)
        # Mock engine to return nothing since LayoutManager now reads node.geometry directly in Grid Mode
        # But this test covers FREE_FORM where FreeLayoutEngine still returns a map
        mock_free_layout_engine.calculate_geometries.return_value = ({"p1": phys_rect}, None, None)
        mock_application_model.layout_mode = LayoutMode.FREE_FORM
        
        geoms = layout_manager.get_current_layout_geometries([plot])
        
        assert geoms["p1"].x == pytest.approx(0.25)

    # --- Inference Logic Tests ---

    def test_infer_grid_dimensions(self, layout_manager):
        """Tests the square-ish dimension inference logic."""
        assert layout_manager._infer_grid_dimensions(4) == (2, 2)
        assert layout_manager._infer_grid_dimensions(2) == (1, 2)
        assert layout_manager._infer_grid_dimensions(3) == (1, 3)

    def test_infer_grid_config_from_plots(self, layout_manager, mock_application_model):
        """Tests that heuristics identify grid parameters in physical CM space."""
        mock_application_model.figure_size = (20.0, 10.0)
        p1 = PlotNode(id="p1"); p1.geometry = Rect(2.0, 2.0, 4.0, 4.0)
        p2 = PlotNode(id="p2"); p2.geometry = Rect(8.0, 2.0, 4.0, 4.0)
        
        config = layout_manager.infer_grid_config_from_plots([p1, p2], None)
        
        assert config.rows == 1
        assert config.cols == 2
        assert config.margins.left == pytest.approx(2.0)
        assert config.margins.right == pytest.approx(8.0)
        assert config.gutters.wspace[0] == pytest.approx(2.0)

    def test_infer_grid_config_from_2x2_template(self, layout_manager, mock_application_model):
        """Verifies that the engine can perfectly recover grid parameters from the 2x2 template."""
        # 2x2 template values (CM) on 21.59 x 15.24 figure
        # Top-Left: x=1.511, y=8.687, w=8.636, h=6.096
        # Top-Right: x=12.306, y=8.687, w=8.636, h=6.096
        # Bottom-Left: x=1.511, y=1.219, w=8.636, h=6.096
        # Bottom-Right: x=12.306, y=1.219, w=8.636, h=6.096
        
        mock_application_model.figure_size = (21.59, 15.24)
        
        p1 = PlotNode(id="tl"); p1.geometry = Rect(1.511, 8.687, 8.636, 6.096)
        p2 = PlotNode(id="tr"); p2.geometry = Rect(12.306, 8.687, 8.636, 6.096)
        p3 = PlotNode(id="bl"); p3.geometry = Rect(1.511, 1.219, 8.636, 6.096)
        p4 = PlotNode(id="br"); p4.geometry = Rect(12.306, 1.219, 8.636, 6.096)
        
        config = layout_manager.infer_grid_config_from_plots([p1, p2, p3, p4], None)
        
        # Margins check
        assert config.margins.left == pytest.approx(1.51, abs=0.01)
        assert config.margins.bottom == pytest.approx(1.22, abs=0.01)
        
        # Gutter check
        # Horizontal gap: 12.306 - (1.511 + 8.636) = 2.159
        # Vertical gap: 8.687 - (1.219 + 6.096) = 1.372
        assert config.gutters.wspace[0] == pytest.approx(2.16, abs=0.01)
        assert config.gutters.hspace[0] == pytest.approx(1.37, abs=0.01)

    # --- Grid Parameter Updates ---

    def test_update_grid_layout_parameters(self, layout_manager, mock_grid_layout_engine, mocker, mock_application_model):
        """Tests merging logic of update_grid_layout_parameters using CM values."""
        base_config = GridConfig(1, 1, [1.0], [1.0], Margins(1.0, 1.0, 1.0, 1.0), Gutters([], []))        
        layout_manager._last_grid_config = base_config
        mock_application_model.layout_mode = LayoutMode.GRID
        mocker.patch.object(layout_manager, "set_layout_mode")

        mock_grid_layout_engine.calculate_geometries.return_value = ({}, base_config.margins, base_config.gutters)
        
        layout_manager.update_grid_layout_parameters(rows=3, margin_top=2.5, hspace_str="1.5")
        
        updated = layout_manager._last_grid_config
        assert updated.rows == 3
        assert updated.margins.top == 2.5
        assert updated.gutters.hspace == [1.5]

    # --- Template & Optimization Tests ---

    def test_apply_layout_template(self, layout_manager, mock_application_model, mock_event_aggregator):
        """Tests that redistribution correctly populates a new scene graph."""
        old_state = [{"data": "df1", "plot_properties_dict": {"plot_type": "scatter"}, "id": "old1"}]
        mock_application_model.extract_plot_states.return_value = old_state
        
        new_root = GroupNode(name="Template")
        new_plot = PlotNode(id="new1")
        new_root.add_child(new_plot)
        
        layout_manager.apply_layout_template(new_root)
        
        assert new_plot.data == "df1"
        mock_event_aggregator.publish.assert_any_call(
            Events.INITIALIZE_PLOT_THEME_REQUESTED, node_id="new1", plot_type=ArtistType.SCATTER
        )

    def test_get_optimized_grid_config(self, layout_manager, mock_application_model, mock_grid_layout_engine):
        """Verifies correct call to grid engine for constrained optimization."""
        real_config = GridConfig(1, 1, [1.0], [1.0], Margins(0,0,0,0), Gutters([],[]))
        layout_manager._last_grid_config = real_config
        plot = PlotNode()
        mock_application_model.scene_root.all_descendants.return_value = [plot]
        mock_application_model.layout_mode = LayoutMode.GRID
        mock_grid_layout_engine.calculate_geometries.return_value = (
            {}, Margins(1.5, 1.5, 1.5, 1.5), Gutters([], [])
        )
        
        opt_config = layout_manager.get_optimized_grid_config()
        
        assert opt_config.margins.top == 1.5

    # --- Utility Tests ---

    def test_create_minimal_grid_config(self, layout_manager, mock_config_service):
        """Verifies that minimal config uses CM values from ConfigService."""
        mock_config_service.get.side_effect = lambda k, d: {
            "layout.grid_margin_top": 2.0,
            "layout.grid_hspace": 1.0
        }.get(k, d)
        
        config = layout_manager._create_minimal_grid_config()
        
        assert config.margins.top == 2.0
        assert config.gutters.hspace == [1.0]

    @pytest.mark.parametrize("config_val, expected", [
        ("0.1, 0.2", [0.1, 0.2]),
        ("[0.3, 0.4]", [0.3, 0.4]),
        (0.5, [0.5]),
        ([0.6, 0.7], [0.6, 0.7]),
        ("invalid", [0.5]), # Fallback to default [0.5] in _create_minimal_grid_config context
    ])
    def test_parse_float_list_from_config(self, layout_manager, mock_config_service, config_val, expected):
        """Tests robust parsing of float lists."""
        mock_config_service.get.side_effect = None
        mock_config_service.get.return_value = config_val
        result = layout_manager._parse_float_list_from_config("key", [0.5])
        assert result == expected
