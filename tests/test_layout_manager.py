from unittest.mock import MagicMock

import pytest

from src.services.config_service import ConfigService
from src.models.layout.layout_engine import FreeLayoutEngine, GridLayoutEngine, LayoutMode
from src.services.layout_manager import LayoutManager
from src.models.application_model import ApplicationModel
from src.models.layout.layout_config import GridConfig
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
        "layout.grid_margin": 0.05,
        "layout.grid_gutter": 0.05,
    }.get(key, default)
    return config

@pytest.fixture
def layout_manager(mock_application_model, mock_free_engine, mock_grid_engine, mock_config_service):
    return LayoutManager(mock_application_model, mock_free_engine, mock_grid_engine, mock_config_service)


# Test cases for LayoutManager initialization
def test_layout_manager_init_default_free_form(layout_manager, mock_application_model):
    """Test LayoutManager initializes with default free_form mode."""
    assert layout_manager.layout_mode == LayoutMode.FREE_FORM
    assert isinstance(mock_application_model.current_layout_config, FreeConfig)

def test_layout_manager_init_default_grid_mode(mock_application_model, mock_free_engine, mock_grid_engine, mock_config_service):
    """Test LayoutManager initializes with default grid mode if configured."""
    mock_config_service.get.side_effect = lambda key, default: {
        "ui.default_layout_mode": "grid",
        "layout.default_grid_rows": 3,
        "layout.default_grid_cols": 3,
        "layout.grid_margin": 0.1,
        "layout.grid_gutter": 0.1,
    }.get(key, default)
    manager = LayoutManager(mock_application_model, mock_free_engine, mock_grid_engine, mock_config_service)
    assert manager.layout_mode == LayoutMode.GRID
    assert isinstance(mock_application_model.current_layout_config, GridConfig)
    assert mock_application_model.current_layout_config.rows == 3

# Test cases for set_layout_mode
def test_set_layout_mode_to_grid_from_free(layout_manager, mock_application_model, mock_grid_engine):
    """
    Test setting layout mode from FREE_FORM to GRID.
    Should infer grid dimensions and call grid engine.
    """
    mock_application_model.scene_root.all_descendants.return_value = [
        PlotNode(id="p1"), PlotNode(id="p2"), PlotNode(id="p3"), PlotNode(id="p4")
    ]
    layout_manager.set_layout_mode(LayoutMode.GRID)
    assert layout_manager.layout_mode == LayoutMode.GRID
    assert isinstance(mock_application_model.current_layout_config, GridConfig)
    # Check that update_grid_layout_parameters was called, which internally calls grid_engine.calculate_geometries
    mock_grid_engine.calculate_geometries.assert_called_once()
    assert mock_application_model.layoutConfigChanged.emit.called
    assert layout_manager.layoutModeChanged.emit.called_once_with(LayoutMode.GRID)


def test_set_layout_mode_to_free_from_grid(layout_manager, mock_application_model):
    """Test setting layout mode from GRID to FREE_FORM."""
    # First set to GRID
    layout_manager.set_layout_mode(LayoutMode.GRID)
    mock_application_model.layoutConfigChanged.reset_mock() # Reset mock after initial grid setup
    layout_manager.layoutModeChanged.reset_mock()

    layout_manager.set_layout_mode(LayoutMode.FREE_FORM)
    assert layout_manager.layout_mode == LayoutMode.FREE_FORM
    assert isinstance(mock_application_model.current_layout_config, FreeConfig)
    assert mock_application_model.layoutConfigChanged.emit.called_once()
    assert layout_manager.layoutModeChanged.emit.called_once_with(LayoutMode.FREE_FORM)

def test_set_layout_mode_no_change(layout_manager, mock_application_model, mock_grid_engine):
    """Test setting layout mode to the current mode does nothing."""
    initial_mode = layout_manager.layout_mode
    layout_manager.set_layout_mode(initial_mode)
    mock_grid_engine.calculate_geometries.assert_not_called()
    mock_application_model.layoutConfigChanged.emit.assert_not_called()
    layout_manager.layoutModeChanged.emit.assert_not_called()

# Test cases for _infer_grid_dimensions (helper method)
def test_infer_grid_dimensions_perfect_square(layout_manager):
    assert layout_manager._infer_grid_dimensions(4) == (2, 2)

def test_infer_grid_dimensions_rectangle(layout_manager):
    assert layout_manager._infer_grid_dimensions(6) == (2, 3) or layout_manager._infer_grid_dimensions(6) == (3, 2)

def test_infer_grid_dimensions_prime_number(layout_manager):
    assert layout_manager._infer_grid_dimensions(5) == (5, 1) # Or (1, 5) depending on implementation

def test_infer_grid_dimensions_zero_plots(layout_manager):
    assert layout_manager._infer_grid_dimensions(0) == (1, 1)

def test_infer_grid_dimensions_single_plot(layout_manager):
    assert layout_manager._infer_grid_dimensions(1) == (1, 1)

# Test cases for perform_align
def test_perform_align(layout_manager, mock_free_engine):
    """Test that perform_align calls free_engine.perform_align and returns mapped geometries."""
    plot_mock1 = MagicMock(spec=PlotNode, id="plot1")
    plot_mock2 = MagicMock(spec=PlotNode, id="plot2")
    mock_free_engine.perform_align.return_value = {
        plot_mock1: (0.1, 0.1, 0.4, 0.4),
        plot_mock2: (0.2, 0.2, 0.3, 0.3),
    }
    geometries = layout_manager.perform_align([plot_mock1, plot_mock2], "left")
    mock_free_engine.perform_align.assert_called_once_with([plot_mock1, plot_mock2], "left")
    assert geometries == {
        "plot1": (0.1, 0.1, 0.4, 0.4),
        "plot2": (0.2, 0.2, 0.3, 0.3),
    }

def test_perform_align_not_free_form_mode(layout_manager, mock_free_engine):
    """Test perform_align returns empty dict if not in FREE_FORM mode."""
    layout_manager.set_layout_mode(LayoutMode.GRID) # Set to grid mode
    mock_free_engine.perform_align.reset_mock()
    geometries = layout_manager.perform_align([MagicMock(spec=PlotNode, id="plot1")], "left")
    assert geometries == {}
    mock_free_engine.perform_align.assert_not_called()

# Test cases for perform_distribute
def test_perform_distribute(layout_manager, mock_free_engine):
    """Test that perform_distribute calls free_engine.perform_distribute and returns mapped geometries."""
    plot_mock1 = MagicMock(spec=PlotNode, id="plot1")
    plot_mock2 = MagicMock(spec=PlotNode, id="plot2")
    mock_free_engine.perform_distribute.return_value = {
        plot_mock1: (0.1, 0.1, 0.4, 0.4),
        plot_mock2: (0.5, 0.1, 0.4, 0.4),
    }
    geometries = layout_manager.perform_distribute([plot_mock1, plot_mock2], "horizontal")
    mock_free_engine.perform_distribute.assert_called_once_with([plot_mock1, plot_mock2], "horizontal")
    assert geometries == {
        "plot1": (0.1, 0.1, 0.4, 0.4),
        "plot2": (0.5, 0.1, 0.4, 0.4),
    }

def test_perform_distribute_not_free_form_mode(layout_manager, mock_free_engine):
    """Test perform_distribute returns empty dict if not in FREE_FORM mode."""
    layout_manager.set_layout_mode(LayoutMode.GRID) # Set to grid mode
    mock_free_engine.perform_distribute.reset_mock()
    geometries = layout_manager.perform_distribute([MagicMock(spec=PlotNode, id="plot1")], "horizontal")
    assert geometries == {}
    mock_free_engine.perform_distribute.assert_not_called()

# Test cases for update_grid_layout_parameters (new test stubs)
def test_update_grid_layout_parameters_simple_update(layout_manager, mock_application_model, mock_grid_engine):
    """
    Test updating grid parameters with explicit rows/cols/margin/gutter.
    """
    mock_application_model.current_layout_config = GridConfig(rows=1, cols=1, margin=0.01, gutter=0.01)
    mock_application_model.scene_root.all_descendants.return_value = [PlotNode(id="p1"), PlotNode(id="p2")]

    expected_geometries = {"p1": (0,0,0.5,0.5), "p2": (0.5,0,0.5,0.5)}
    mock_grid_engine.calculate_geometries.return_value = {
        mock_application_model.scene_root.all_descendants.return_value[0]: expected_geometries["p1"],
        mock_application_model.scene_root.all_descendants.return_value[1]: expected_geometries["p2"]
    }

    result = layout_manager.update_grid_layout_parameters(rows=2, cols=1, margin=0.1, gutter=0.05)

    assert layout_manager.layout_mode == LayoutMode.GRID
    assert mock_application_model.current_layout_config.rows == 2
    assert mock_application_model.current_layout_config.cols == 1
    assert mock_application_model.current_layout_config.margin == 0.1
    assert mock_application_model.current_layout_config.gutter == 0.05
    mock_grid_engine.calculate_geometries.assert_called_once()
    assert result == expected_geometries
    assert mock_application_model.layoutConfigChanged.emit.called
    assert layout_manager.layoutModeChanged.emit.called_once_with(LayoutMode.GRID)

def test_update_grid_layout_parameters_infer_from_plots(layout_manager, mock_application_model, mock_grid_engine):
    """
    Test updating grid parameters with rows/cols=None to trigger inference.
    """
    mock_application_model.current_layout_config = FreeConfig() # Start in free mode
    mock_application_model.scene_root.all_descendants.return_value = [
        PlotNode(id="p1"), PlotNode(id="p2"), PlotNode(id="p3"), PlotNode(id="p4")
    ] # 4 plots

    expected_geometries = {"p1": (0,0,0.5,0.5), "p2": (0.5,0,0.5,0.5), "p3": (0,0.5,0.5,0.5), "p4": (0.5,0.5,0.5,0.5)}
    mock_grid_engine.calculate_geometries.return_value = {
        mock_application_model.scene_root.all_descendants.return_value[0]: expected_geometries["p1"],
        mock_application_model.scene_root.all_descendants.return_value[1]: expected_geometries["p2"],
        mock_application_model.scene_root.all_descendants.return_value[2]: expected_geometries["p3"],
        mock_application_model.scene_root.all_descendants.return_value[3]: expected_geometries["p4"]
    }

    result = layout_manager.update_grid_layout_parameters(rows=None, cols=None) # Infer rows/cols

    assert layout_manager.layout_mode == LayoutMode.GRID
    assert isinstance(mock_application_model.current_layout_config, GridConfig)
    # With 4 plots, _infer_grid_dimensions should return (2, 2)
    assert mock_application_model.current_layout_config.rows == 2
    assert mock_application_model.current_layout_config.cols == 2
    mock_grid_engine.calculate_geometries.assert_called_once()
    assert result == expected_geometries
    assert mock_application_model.layoutConfigChanged.emit.called
    assert layout_manager.layoutModeChanged.emit.called_once_with(LayoutMode.GRID)

def test_update_grid_layout_parameters_from_free_mode_with_explicit_params(layout_manager, mock_application_model, mock_grid_engine):
    """
    Test updating grid parameters from FreeConfig with explicit params.
    """
    mock_application_model.current_layout_config = FreeConfig() # Start in free mode
    mock_application_model.scene_root.all_descendants.return_value = [PlotNode(id="p1")]

    expected_geometries = {"p1": (0,0,1,1)}
    mock_grid_engine.calculate_geometries.return_value = {
        mock_application_model.scene_root.all_descendants.return_value[0]: expected_geometries["p1"]
    }

    result = layout_manager.update_grid_layout_parameters(rows=1, cols=1, margin=0.2, gutter=0.0)

    assert layout_manager.layout_mode == LayoutMode.GRID
    assert isinstance(mock_application_model.current_layout_config, GridConfig)
    assert mock_application_model.current_layout_config.rows == 1
    assert mock_application_model.current_layout_config.cols == 1
    assert mock_application_model.current_layout_config.margin == 0.2
    assert mock_application_model.current_layout_config.gutter == 0.0
    mock_grid_engine.calculate_geometries.assert_called_once()
    assert result == expected_geometries
    assert mock_application_model.layoutConfigChanged.emit.called
    assert layout_manager.layoutModeChanged.emit.called_once_with(LayoutMode.GRID)

def test_update_grid_layout_parameters_preserve_current_config_values(layout_manager, mock_application_model, mock_grid_engine):
    """
    Test that existing GridConfig values are preserved if not explicitly overridden.
    """
    initial_grid_config = GridConfig(rows=3, cols=3, margin=0.1, gutter=0.08)
    mock_application_model.current_layout_config = initial_grid_config
    mock_application_model.scene_root.all_descendants.return_value = [PlotNode(id="p1")]

    expected_geometries = {"p1": (0,0,1,1)}
    mock_grid_engine.calculate_geometries.return_value = {
        mock_application_model.scene_root.all_descendants.return_value[0]: expected_geometries["p1"]
    }

    # Only change rows and cols
    result = layout_manager.update_grid_layout_parameters(rows=2, cols=2)

    assert layout_manager.layout_mode == LayoutMode.GRID
    assert mock_application_model.current_layout_config.rows == 2
    assert mock_application_model.current_layout_config.cols == 2
    assert mock_application_model.current_layout_config.margin == initial_grid_config.margin # Should be preserved
    assert mock_application_model.current_layout_config.gutter == initial_grid_config.gutter # Should be preserved
    mock_grid_engine.calculate_geometries.assert_called_once()
    assert result == expected_geometries
    assert mock_application_model.layoutConfigChanged.emit.called
    assert layout_manager.layoutModeChanged.emit.called_once_with(LayoutMode.GRID)


def test_update_grid_layout_parameters_zero_plots(layout_manager, mock_application_model, mock_grid_engine):
    """
    Test behavior when there are no plots in the scene.
    Should still update config and call grid engine (which should return empty geometries).
    """
    mock_application_model.current_layout_config = FreeConfig()
    mock_application_model.scene_root.all_descendants.return_value = [] # No plots
    mock_grid_engine.calculate_geometries.return_value = {} # Should return empty dict

    result = layout_manager.update_grid_layout_parameters(rows=None, cols=None)

    assert layout_manager.layout_mode == LayoutMode.GRID
    assert isinstance(mock_application_model.current_layout_config, GridConfig)
    assert mock_application_model.current_layout_config.rows == 1 # Inferred for 0 plots
    assert mock_application_model.current_layout_config.cols == 1 # Inferred for 0 plots
    mock_grid_engine.calculate_geometries.assert_called_once() # Still called, but with empty plots
    assert result == {}
    assert mock_application_model.layoutConfigChanged.emit.called
    assert layout_manager.layoutModeChanged.emit.called_once_with(LayoutMode.GRID)

# Test cases for adjust_current_grid
def test_adjust_current_grid(layout_manager, mock_application_model, mock_grid_engine):
    """
    Test adjust_current_grid updates GridConfig and recalculates geometries.
    """
    initial_grid_config = GridConfig(rows=2, cols=2, margin=0.1, gutter=0.1)
    mock_application_model.current_layout_config = initial_grid_config
    mock_application_model.scene_root.all_descendants.return_value = [PlotNode(id="p1")]

    expected_geometries = {"p1": (0,0,1,1)}
    mock_grid_engine.calculate_geometries.return_value = {
        mock_application_model.scene_root.all_descendants.return_value[0]: expected_geometries["p1"]
    }

    result = layout_manager.adjust_current_grid(rows=3, cols=3)

    assert mock_application_model.current_layout_config.rows == 3
    assert mock_application_model.current_layout_config.cols == 3
    # Ensure margin and gutter are preserved
    assert mock_application_model.current_layout_config.margin == initial_grid_config.margin
    assert mock_application_model.current_layout_config.gutter == initial_grid_config.gutter
    mock_grid_engine.calculate_geometries.assert_called_once()
    assert result == expected_geometries
    assert mock_application_model.layoutConfigChanged.emit.called

def test_adjust_current_grid_not_in_grid_mode(layout_manager, mock_application_model, mock_grid_engine):
    """
    Test adjust_current_grid returns empty dict if not in Grid mode.
    """
    mock_application_model.current_layout_config = FreeConfig() # Not in grid mode
    mock_grid_engine.calculate_geometries.reset_mock()
    result = layout_manager.adjust_current_grid(rows=3, cols=3)
    assert result == {}
    mock_grid_engine.calculate_geometries.assert_not_called()
    mock_application_model.layoutConfigChanged.emit.assert_not_called()

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
