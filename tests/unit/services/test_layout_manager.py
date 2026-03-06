import pytest
from unittest.mock import MagicMock, call
from pathlib import Path

from src.services.layout_manager import LayoutManager
from src.models.layout.layout_config import FreeConfig, GridConfig, Gutters, Margins
from src.models.nodes.plot_node import PlotNode
from src.models.nodes.group_node import GroupNode
from src.shared.constants import LayoutMode
from src.shared.events import Events
from src.models.plots.plot_types import ArtistType


@pytest.fixture
def layout_manager(
    mock_application_model,
    mock_free_layout_engine,
    mock_grid_layout_engine,
    mock_config_service,
    mock_event_aggregator,
):
    """Provides a LayoutManager instance with all dependencies mocked."""
    # Override conftest side_effect to provide the required key
    mock_config_service.get_required.side_effect = lambda k: "free_form"
    # Ensure model has an initial config to prevent NoneType error in init
    mock_application_model.current_layout_config = FreeConfig()
    
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
        mock_application_model.current_layout_config = FreeConfig()
        
        manager = LayoutManager(
            mock_application_model, MagicMock(), MagicMock(), mock_config_service, MagicMock()
        )
        
        assert manager.ui_selected_layout_mode == LayoutMode.FREE_FORM
        assert manager._last_grid_config is None
        assert isinstance(manager._last_free_form_config, FreeConfig)

    def test_init_default_grid_mode(self, mock_config_service, mock_application_model):
        """Verifies initialization when default mode is GRID."""
        mock_config_service.get_required.side_effect = lambda k: "grid"
        mock_application_model.current_layout_config = FreeConfig()
        
        manager = LayoutManager(
            mock_application_model, MagicMock(), MagicMock(), mock_config_service, MagicMock()
        )
        
        assert manager.layout_mode == LayoutMode.GRID
        assert isinstance(manager._last_grid_config, GridConfig)

    def test_on_model_reset(self, layout_manager):
        """Ensures that model reset clears the layout caches."""
        layout_manager._last_grid_config = MagicMock(spec=GridConfig)
        layout_manager.on_model_reset()
        assert layout_manager._last_grid_config is None

    # --- Mode Management Tests ---

    def test_set_layout_mode_to_grid_initializes_cache(self, layout_manager, mock_application_model):
        """Tests that switching to GRID for the first time creates a minimal config."""
        layout_manager._last_grid_config = None
        layout_manager.set_layout_mode(LayoutMode.GRID)
        
        assert isinstance(layout_manager._last_grid_config, GridConfig)
        assert mock_application_model.current_layout_config is layout_manager._last_grid_config

    def test_set_layout_mode_preserves_existing_cache(self, layout_manager, mock_application_model):
        """Tests that switching to GRID uses the existing cached config if present."""
        existing = GridConfig(5, 5, [1]*5, [1]*5, Margins(0,0,0,0), Gutters([],[]))
        layout_manager._last_grid_config = existing
        
        layout_manager.set_layout_mode(LayoutMode.GRID)
        
        assert mock_application_model.current_layout_config is existing

    def test_ui_selected_layout_mode_setter(self, layout_manager, mock_event_aggregator):
        """Tests the property setter and its event publication."""
        layout_manager.ui_selected_layout_mode = LayoutMode.GRID
        mock_event_aggregator.publish.assert_any_call(
            Events.UI_LAYOUT_MODE_CHANGED, ui_layout_mode=LayoutMode.GRID
        )

    # --- Orchestration & Delegation Tests ---

    def test_get_active_engine(self, layout_manager, mock_application_model, 
                               mock_free_layout_engine, mock_grid_layout_engine):
        """Verifies engine selection based on current model state."""
        mock_application_model.current_layout_config = FreeConfig()
        assert layout_manager.get_active_engine() is mock_free_layout_engine
        
        mock_application_model.current_layout_config = GridConfig(1,1,[1],[1], Margins(0,0,0,0), Gutters([],[]))
        assert layout_manager.get_active_engine() is mock_grid_layout_engine

    def test_get_current_layout_geometries(self, layout_manager, mock_free_layout_engine, mock_application_model):
        """Verifies coordination with engines to get geometries."""
        plot = PlotNode(id="p1")
        mock_free_layout_engine.calculate_geometries.return_value = ({"p1": (0,0,1,1)}, None, None)
        
        geoms = layout_manager.get_current_layout_geometries([plot])
        
        assert geoms == {"p1": (0,0,1,1)}
        mock_free_layout_engine.calculate_geometries.assert_called_once_with(
            [plot], mock_application_model.current_layout_config
        )

    # --- Inference Logic Tests ---

    def test_infer_grid_dimensions(self, layout_manager):
        """Tests the square-ish dimension inference logic."""
        assert layout_manager._infer_grid_dimensions(4) == (2, 2)
        assert layout_manager._infer_grid_dimensions(2) == (1, 2)
        assert layout_manager._infer_grid_dimensions(3) == (1, 3)

    def test_infer_grid_config_from_plots(self, layout_manager):
        """Tests that heuristics correctly identify grid parameters from free positions."""
        p1 = PlotNode(id="p1"); p1.geometry = (0.1, 0.1, 0.4, 0.4)
        p2 = PlotNode(id="p2"); p2.geometry = (0.5, 0.1, 0.4, 0.4)
        
        config = layout_manager.infer_grid_config_from_plots([p1, p2], None)
        
        assert config.rows == 1
        assert config.cols == 2
        assert config.margins.left == 0.1
        assert config.margins.bottom == 0.1
        # Right margin = 1.0 - (0.5 + 0.4) = 0.1
        assert config.margins.right == 0.1

    # --- Grid Parameter Updates (The big one) ---

    def test_update_grid_layout_parameters(self, layout_manager, mock_grid_layout_engine, mocker):
        """Tests merging logic of update_grid_layout_parameters."""
        # 1. Setup base state
        base_config = GridConfig(1, 1, [1.0], [1.0], Margins(0.05, 0.05, 0.05, 0.05), Gutters([], []))
        layout_manager._last_grid_config = base_config
        
        # Mock set_layout_mode to avoid side effects
        mocker.patch.object(layout_manager, "set_layout_mode")
        
        # Mock engine return
        mock_grid_layout_engine.calculate_geometries.return_value = ({}, base_config.margins, base_config.gutters)
        
        # 2. Update only rows and top margin
        layout_manager.update_grid_layout_parameters(rows=3, margin_top=0.2, hspace_str="0.1, 0.1")
        
        # 3. Verify resulting config
        updated = layout_manager._last_grid_config
        assert updated.rows == 3
        assert updated.cols == 1 # preserved from base
        assert updated.margins.top == 0.2
        assert updated.margins.bottom == 0.05 # preserved from base
        assert updated.gutters.hspace == [0.1, 0.1] # parsed from string

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
        
        # Ensure plots are present to avoid None return
        plot = PlotNode()
        mock_application_model.scene_root.all_descendants.return_value = [plot]
        
        mock_grid_layout_engine.calculate_geometries.return_value = (
            {}, Margins(0.1, 0.1, 0.1, 0.1), Gutters([], [])
        )
        
        opt_config = layout_manager.get_optimized_grid_config()
        
        assert opt_config.margins.top == 0.1
        args, kwargs = mock_grid_layout_engine.calculate_geometries.call_args
        assert kwargs["use_constrained_optimization"] is True

    # --- Utility Tests ---

    def test_create_minimal_grid_config(self, layout_manager, mock_config_service):
        """Verifies that minimal config correctly uses values from ConfigService."""
        mock_config_service.get.side_effect = lambda k, d: {
            "layout.default_grid_rows": 4,
            "layout.grid_margin_top": 0.15
        }.get(k, d)
        
        config = layout_manager._create_minimal_grid_config()
        
        assert config.rows == 4
        assert config.margins.top == 0.15

    @pytest.mark.parametrize("config_val, expected", [
        ("0.1, 0.2", [0.1, 0.2]),
        ("[0.3, 0.4]", [0.3, 0.4]),
        (0.5, [0.5]),
        ([0.6, 0.7], [0.6, 0.7]),
        ("invalid", [0.01]),
    ])
    def test_parse_float_list_from_config(self, layout_manager, mock_config_service, config_val, expected):
        """Tests robust parsing of float lists."""
        mock_config_service.get.side_effect = None
        mock_config_service.get.return_value = config_val
        result = layout_manager._parse_float_list_from_config("key", [0.01])
        assert result == expected
