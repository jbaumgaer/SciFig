from unittest.mock import MagicMock

import pytest

from src.services.config_service import ConfigService
from src.models.layout.layout_engine import FreeLayoutEngine, GridLayoutEngine, LayoutMode
from src.services.layout_manager import LayoutManager
from src.models.application_model import ApplicationModel
from src.models.layout.layout_config import FreeConfig, GridConfig, Margins, Gutters
from src.models.nodes import GroupNode, PlotNode


@pytest.fixture
def mock_application_model():
    model = MagicMock(spec=ApplicationModel)
    model.scene_root = GroupNode(name="root_mock")
    model.modelChanged = MagicMock()
    model.layoutConfigChanged = MagicMock()
    # Ensure current_layout_config is an attribute that can be set and read
    model._current_layout_config = FreeConfig() # Default or initial state
    type(model).current_layout_config = property(
        lambda self: self._current_layout_config,
        lambda self, value: setattr(self, '_current_layout_config', value)
    )
    return model

@pytest.fixture
def mock_free_engine():
    engine = MagicMock(spec=FreeLayoutEngine)
    engine.calculate_geometries.return_value = {}
    return engine

@pytest.fixture
def mock_grid_engine():
    engine = MagicMock(spec=GridLayoutEngine)
    engine.calculate_geometries.return_value = {} # Default empty return
    return engine

@pytest.fixture
def mock_config_service():
    config = MagicMock(spec=ConfigService)
    config.get.side_effect = lambda key, default: {
        "ui.default_layout_mode": "free_form",
        "layout.default_grid_rows": 2,
        "layout.default_grid_cols": 2,
        "layout.grid_margin_top": 0.05,
        "layout.grid_margin_bottom": 0.05,
        "layout.grid_margin_left": 0.05,
        "layout.grid_margin_right": 0.05,
        "layout.grid_hspace": [],
        "layout.grid_wspace": [],
    }.get(key, default)
    return config

@pytest.fixture
def layout_manager(mock_application_model, mock_free_engine, mock_grid_engine, mock_config_service):
    return LayoutManager(mock_application_model, mock_free_engine, mock_grid_engine, mock_config_service)


# --- New Test Cases for LayoutManager ---

def test_layout_manager_init(layout_manager, mock_application_model):
    """
    Test LayoutManager initialization sets _last_grid_config to None and current_layout_config to FreeConfig.
    """
    assert layout_manager._last_grid_config is None
    assert isinstance(layout_manager._last_free_form_config, FreeConfig)
    assert layout_manager.layout_mode == LayoutMode.FREE_FORM # Default mode
    assert isinstance(mock_application_model.current_layout_config, FreeConfig)

def test_layout_manager_init_default_grid_mode_config(mock_application_model, mock_free_engine, mock_grid_engine, mock_config_service):
    """
    Test LayoutManager initialization when default_layout_mode is 'grid'.
    _last_grid_config should be set via set_layout_mode with a minimal config.
    """
    mock_config_service.get.side_effect = lambda key, default: {
        "ui.default_layout_mode": "grid",
        "layout.default_grid_rows": 3,
        "layout.default_grid_cols": 3,
        "layout.grid_margin_top": 0.1,
        "layout.grid_margin_bottom": 0.1,
        "layout.grid_margin_left": 0.1,
        "layout.grid_margin_right": 0.1,
        "layout.grid_hspace": [0.05],
        "layout.grid_wspace": [0.05],
    }.get(key, default)
    manager = LayoutManager(mock_application_model, mock_free_engine, mock_grid_engine, mock_config_service)
    
    assert manager.layout_mode == LayoutMode.GRID
    assert manager.ui_selected_layout_mode == LayoutMode.GRID # New assertion
    assert isinstance(manager._last_grid_config, GridConfig) # Should be initialized by set_layout_mode
    assert manager._last_grid_config.rows == 3 # From mock config
    assert isinstance(mock_application_model.current_layout_config, GridConfig)
    assert mock_application_model.current_layout_config.rows == 3

def test_create_minimal_grid_config(layout_manager):
    """
    Test that _create_minimal_grid_config returns a valid GridConfig with expected defaults.
    """
    minimal_config = layout_manager._create_minimal_grid_config()
    assert isinstance(minimal_config, GridConfig)
    assert minimal_config.rows == 2 # From mock_config_service.get("layout.default_grid_rows", 2)
    assert minimal_config.cols == 2 # From mock_config_service.get("layout.default_grid_cols", 2)
    assert minimal_config.margins.top == 0.05
    assert minimal_config.gutters.hspace == []

def test_set_layout_mode_to_grid_initializes_last_grid_config(layout_manager, mock_application_model):
    """
    Test that setting layout mode to GRID for the first time initializes _last_grid_config
    with a minimal config.
    """
    # Ensure _last_grid_config is None initially
    layout_manager._last_grid_config = None
    mock_application_model.current_layout_config = FreeConfig()

    layout_manager.set_layout_mode(LayoutMode.GRID)

    assert layout_manager.layout_mode == LayoutMode.GRID
    assert isinstance(layout_manager._last_grid_config, GridConfig)
    assert isinstance(mock_application_model.current_layout_config, GridConfig)
    # Check some properties of the minimal config
    assert layout_manager._last_grid_config.rows == 2
    assert layout_manager._last_grid_config.margins.top == 0.05
    mock_application_model.layoutConfigChanged.emit.assert_called_once()
    layout_manager.layoutModeChanged.emit.assert_called_once_with(LayoutMode.GRID)

def test_set_layout_mode_to_grid_preserves_last_grid_config(layout_manager, mock_application_model):
    """
    Test that setting layout mode to GRID when _last_grid_config already exists
    uses the existing _last_grid_config.
    """
    initial_margins = Margins(top=0.1, bottom=0.1, left=0.1, right=0.1)
    initial_gutters = Gutters(hspace=[0.01], wspace=[0.01])
    initial_grid_config = GridConfig(
        rows=5, cols=5, row_ratios=[1.0]*5, col_ratios=[1.0]*5,
        margins=initial_margins,
        gutters=initial_gutters
    )
    layout_manager._last_grid_config = initial_grid_config
    mock_application_model.current_layout_config = FreeConfig()

    layout_manager.set_layout_mode(LayoutMode.GRID)

    assert layout_manager.layout_mode == LayoutMode.GRID
    assert layout_manager._last_grid_config is initial_grid_config # Should be the same object
    assert mock_application_model.current_layout_config is initial_grid_config
    mock_application_model.layoutConfigChanged.emit.assert_called_once()
    layout_manager.layoutModeChanged.emit.assert_called_once_with(LayoutMode.GRID)

def test_set_layout_mode_to_free_from_grid_saves_grid_config(layout_manager, mock_application_model):
    """
    Test that switching from GRID to FREE_FORM saves the current GridConfig
    to _last_grid_config.
    """
    # First, ensure we are in GRID mode with a specific config
    layout_manager.set_layout_mode(LayoutMode.GRID)
    original_grid_config = layout_manager._last_grid_config
    mock_application_model.layoutConfigChanged.reset_mock()
    layout_manager.layoutModeChanged.reset_mock()

    layout_manager.set_layout_mode(LayoutMode.FREE_FORM)

    assert layout_manager.layout_mode == LayoutMode.FREE_FORM
    assert layout_manager._last_grid_config is original_grid_config # Should have been saved
    assert isinstance(mock_application_model.current_layout_config, FreeConfig)
    mock_application_model.layoutConfigChanged.emit.assert_called_once()
    layout_manager.layoutModeChanged.emit.assert_called_once_with(LayoutMode.FREE_FORM)


def test_update_grid_layout_parameters(layout_manager, mock_application_model, mock_grid_engine):
    """
    Test update_grid_layout_parameters correctly updates GridConfig and applies layout.
    Ensures _last_grid_config is correctly initialized if None.
    Also verifies ui_selected_layout_mode is unchanged and set_layout_mode is called.
    """
    # Ensure _last_grid_config starts as None
    layout_manager._last_grid_config = None
    # Ensure app starts in FREE_FORM and UI also selected FREE_FORM
    mock_application_model.current_layout_config = FreeConfig()
    layout_manager._ui_selected_layout_mode = LayoutMode.FREE_FORM 

    # Mock scene with plots for inference
    plot_mocks = [
        MagicMock(spec=PlotNode, id=f"p{i}", geometry=(0.1*i, 0.1*i, 0.2, 0.2)) for i in range(4)
    ]
    mock_application_model.scene_root.all_descendants.return_value = plot_mocks

    # Mock calculate_geometries return value
    mock_grid_engine.calculate_geometries.return_value = ({f"p{i}": (0,0,0.5,0.5) for i in range(4)}, Margins(0,0,0,0), Gutters([],[]))

    with patch.object(layout_manager, 'set_layout_mode') as mock_set_layout_mode:
        # Call with some explicit parameters
        updated_geometries = layout_manager.update_grid_layout_parameters(
            rows=2, cols=2, margin_top=0.1, margin_bottom=0.1, margin_left=0.1, margin_right=0.1,
            hspace_str="0.05", wspace_str="0.05"
        )
        mock_set_layout_mode.assert_called_once_with(LayoutMode.GRID)

    assert isinstance(updated_geometries, dict)
    assert layout_manager.layout_mode == LayoutMode.GRID
    assert isinstance(layout_manager._last_grid_config, GridConfig)
    assert layout_manager._last_grid_config.rows == 2
    assert layout_manager._last_grid_config.cols == 2
    assert layout_manager._last_grid_config.margins.top == 0.1
    assert layout_manager._last_grid_config.gutters.hspace == [0.05]
    mock_grid_engine.calculate_geometries.assert_called_once()
    mock_application_model.layoutConfigChanged.emit.assert_called()
    layout_manager.layoutModeChanged.emit.assert_called_with(LayoutMode.GRID) # Emitted by internal set_layout_mode
    # The UI selected mode should remain unchanged by this action
    assert layout_manager.ui_selected_layout_mode == LayoutMode.FREE_FORM


def test_infer_grid_parameters(layout_manager, mock_application_model):
    """
    Test infer_grid_parameters correctly infers and updates _last_grid_config,
    initializing it if it's None.
    Also verifies ui_selected_layout_mode is unchanged and set_layout_mode is called.
    """
    # Setup: ensure _last_grid_config is None initially
    layout_manager._last_grid_config = None
    # Ensure app starts in FREE_FORM and UI also selected FREE_FORM
    mock_application_model.current_layout_config = FreeConfig()
    layout_manager._ui_selected_layout_mode = LayoutMode.FREE_FORM 

    plot_mocks = [
        MagicMock(spec=PlotNode, id=f"p{i}", geometry=(0.1*i, 0.1*i, 0.2, 0.2)) for i in range(4)
    ]
    mock_application_model.scene_root.all_descendants.return_value = plot_mocks

    with patch.object(layout_manager, 'set_layout_mode') as mock_set_layout_mode:
        layout_manager.infer_grid_parameters()
        mock_set_layout_mode.assert_called_once_with(LayoutMode.GRID)

    assert isinstance(layout_manager._last_grid_config, GridConfig)
    assert layout_manager._last_grid_config.rows > 0
    assert layout_manager._last_grid_config.cols > 0
    # The active layout mode should now be GRID
    assert layout_manager.layout_mode == LayoutMode.GRID
    # The UI selected mode should remain unchanged by this action
    assert layout_manager.ui_selected_layout_mode == LayoutMode.FREE_FORM
    mock_application_model.layoutConfigChanged.emit.assert_called()
    layout_manager.layoutModeChanged.emit.assert_called_once_with(LayoutMode.GRID) # Emitted by internal set_layout_mode

def test_optimize_layout_action_none_config(layout_manager, mock_application_model, mock_grid_engine):
    """
    Test optimize_layout_action correctly handles _last_grid_config being None,
    logging an error and returning early.
    Also verifies ui_selected_layout_mode is unchanged and set_layout_mode is called.
    """
    layout_manager._last_grid_config = None
    # Ensure app starts in FREE_FORM and UI also selected FREE_FORM
    mock_application_model.current_layout_config = FreeConfig()
    layout_manager._ui_selected_layout_mode = LayoutMode.FREE_FORM 

    plot_mocks = [MagicMock(spec=PlotNode, id="p1")] # Some plots
    mock_application_model.scene_root.all_descendants.return_value = plot_mocks
    
    with patch.object(layout_manager, 'set_layout_mode') as mock_set_layout_mode:
        with patch.object(layout_manager.logger, 'error') as mock_logger_error:
            layout_manager.optimize_layout_action()
            mock_set_layout_mode.assert_called_once_with(LayoutMode.GRID) # Should try to activate grid mode
            mock_logger_error.assert_called_once_with("optimize_layout_action called but _last_grid_config is None. Cannot optimize without a grid config.")
    
    mock_grid_engine.calculate_geometries.assert_not_called()
    mock_application_model.layoutConfigChanged.emit.assert_not_called()
    layout_manager.layoutModeChanged.emit.assert_not_called() # No actual mode change, so no emit
    # The UI selected mode should remain unchanged by this action
    assert layout_manager.ui_selected_layout_mode == LayoutMode.FREE_FORM
    # The active layout mode should now be GRID due to set_layout_mode call
    assert layout_manager.layout_mode == LayoutMode.GRID

def test_optimize_layout_action(layout_manager, mock_application_model, mock_grid_engine):
    """
    Test optimize_layout_action updates _last_grid_config with calculated margins/gutters.
    Also verifies ui_selected_layout_mode is unchanged and set_layout_mode is called.
    """
    # Setup: ensure _last_grid_config is a valid GridConfig
    layout_manager._last_grid_config = GridConfig(
        rows=1, cols=1, row_ratios=[1.0], col_ratios=[1.0],
        margins=Margins(top=0.0, bottom=0.0, left=0.0, right=0.0),
        gutters=Gutters(hspace=[], wspace=[])
    )
    # Ensure app starts in FREE_FORM and UI also selected FREE_FORM
    mock_application_model.current_layout_config = FreeConfig()
    layout_manager._ui_selected_layout_mode = LayoutMode.FREE_FORM 

    plot_mocks = [MagicMock(spec=PlotNode, id="p1")]
    mock_application_model.scene_root.all_descendants.return_value = plot_mocks

    # Mock calculate_geometries to return specific calculated margins/gutters
    mock_grid_engine.calculate_geometries.return_value = (
        {plot_mocks[0]: (0.1, 0.1, 0.8, 0.8)},
        Margins(top=0.05, bottom=0.05, left=0.05, right=0.05),
        Gutters(hspace=[0.02], wspace=[0.02])
    )

    with patch.object(layout_manager, 'set_layout_mode') as mock_set_layout_mode:
        layout_manager.optimize_layout_action()
        mock_set_layout_mode.assert_called_once_with(LayoutMode.GRID)

    assert layout_manager._last_grid_config.margins.top == 0.05
    assert layout_manager._last_grid_config.gutters.hspace == [0.02]
    # The active layout mode should now be GRID
    assert layout_manager.layout_mode == LayoutMode.GRID
    # The UI selected mode should remain unchanged by this action
    assert layout_manager.ui_selected_layout_mode == LayoutMode.FREE_FORM
    mock_grid_engine.calculate_geometries.assert_called_once_with(
        plot_mocks, layout_manager._last_grid_config, use_constrained_optimization=True
    )
    mock_application_model.layoutConfigChanged.emit.assert_called()
    layout_manager.layoutModeChanged.emit.assert_called_once_with(LayoutMode.GRID) # Emitted by internal set_layout_mode

# Test cases for get_active_engine
def test_get_active_engine_free_form(layout_manager, mock_free_engine):
    """Test get_active_engine returns FreeLayoutEngine in FREE_FORM mode."""
    layout_manager.set_layout_mode(LayoutMode.FREE_FORM)
    assert layout_manager.get_active_engine() is mock_free_engine

def test_get_active_engine_grid(layout_manager, mock_grid_engine):
    """Test get_active_engine returns GridLayoutEngine in GRID mode."""
    layout_manager.set_layout_mode(LayoutMode.GRID)
    assert layout_manager.get_active_engine() is mock_grid_engine

# Test cases for get_current_layout_geometries
def test_get_current_layout_geometries_free_form(layout_manager, mock_free_engine, mock_application_model):
    """Test get_current_layout_geometries in FREE_FORM mode."""
    layout_manager.set_layout_mode(LayoutMode.FREE_FORM)
    plot_mock = MagicMock(spec=PlotNode, id="plot_free")
    mock_free_engine.calculate_geometries.return_value = {plot_mock: (0,0,0.5,0.5)}
    geometries = layout_manager.get_current_layout_geometries([plot_mock])
    mock_free_engine.calculate_geometries.assert_called_once_with([plot_mock], mock_application_model.current_layout_config)
    assert geometries == {"plot_free": (0,0,0.5,0.5)}

def test_get_current_layout_geometries_grid(layout_manager, mock_grid_engine, mock_application_model):
    """Test get_current_layout_geometries in GRID mode."""
    layout_manager.set_layout_mode(LayoutMode.GRID)
    plot_mock = MagicMock(spec=PlotNode, id="plot_grid")
    mock_grid_engine.calculate_geometries.return_value = {plot_mock: (0,0,0.5,0.5)}
    geometries = layout_manager.get_current_layout_geometries([plot_mock])
    mock_grid_engine.calculate_geometries.assert_called_once_with([plot_mock], mock_application_model.current_layout_config)
    assert geometries == {"plot_grid": (0,0,0.5,0.5)}