import pytest
import pandas as pd
import numpy as np
from unittest.mock import MagicMock, Mock
from matplotlib.figure import Figure
from matplotlib.axes import Axes

from src.ui.renderers.plotting_strategies import (
    Cartesian2DStrategy,
    LineSyncStrategy,
    ScatterSyncStrategy,
    ImageSyncStrategy,
    MeshSyncStrategy
)

@pytest.fixture
def sample_data():
    """Create a sample Pandas DataFrame for testing."""
    return pd.DataFrame({
        "x": [1, 2, 3],
        "y": [10, 20, 30],
        "z": [100, 200, 300]
    })

class TestCoordinateStrategies:
    """Tests for CoordSyncStrategy implementations."""

    def test_cartesian_2d_creates_axes(self):
        figure = MagicMock(spec=Figure)
        strategy = Cartesian2DStrategy()
        rect = [0.1, 0.1, 0.8, 0.8]
        
        strategy.create_axes(figure, rect)
        
        figure.add_axes.assert_called_once_with(rect)

    def test_cartesian_2d_syncs_components(self):
        strategy = Cartesian2DStrategy()
        mock_ax = MagicMock() # Removed spec=Axes
        mock_props = MagicMock()
        mock_syncer = MagicMock()
        
        strategy.sync(mock_ax, mock_props, "path", mock_syncer)
        
        mock_syncer.assert_any_call(mock_ax.xaxis, mock_props.xaxis, "path.xaxis")
        mock_syncer.assert_any_call(mock_ax.yaxis, mock_props.yaxis, "path.yaxis")

class TestArtistSyncStrategies:
    """Tests for ArtistSyncStrategy implementations."""

    def test_line_sync_strategy_creates_artist(self):
        strategy = LineSyncStrategy()
        mock_ax = MagicMock(spec=Axes)
        mock_ax.get_lines.return_value = []
        mock_ax.plot.return_value = [MagicMock()]
        
        artist = strategy.get_or_create_artist(mock_ax, None, 0)
        
        mock_ax.plot.assert_called_once_with([], [])
        assert artist is not None

    def test_line_sync_data(self, sample_data):
        strategy = LineSyncStrategy()
        mock_artist = MagicMock()
        mock_props = MagicMock()
        mock_props.x_column = "x"
        mock_props.y_column = "y"
        
        strategy.sync_data(mock_artist, mock_props, sample_data)
        
        args, _ = mock_artist.set_data.call_args
        pd.testing.assert_series_equal(args[0], sample_data["x"])
        pd.testing.assert_series_equal(args[1], sample_data["y"])

    def test_scatter_sync_data(self, sample_data):
        strategy = ScatterSyncStrategy()
        mock_artist = MagicMock()
        mock_props = MagicMock()
        mock_props.x_column = "x"
        mock_props.y_column = "y"
        
        strategy.sync_data(mock_artist, mock_props, sample_data)
        
        args, _ = mock_artist.set_offsets.call_args
        expected_offsets = np.column_stack((sample_data["x"], sample_data["y"]))
        np.testing.assert_array_equal(args[0], expected_offsets)

    def test_image_sync_data(self, sample_data):
        strategy = ImageSyncStrategy()
        mock_artist = MagicMock()
        mock_props = MagicMock()
        mock_props.data_column = "z"
        
        strategy.sync_data(mock_artist, mock_props, sample_data)
        
        args, _ = mock_artist.set_data.call_args
        pd.testing.assert_series_equal(args[0], sample_data["z"])

    def test_mesh_sync_data(self, sample_data):
        strategy = MeshSyncStrategy()
        mock_artist = MagicMock()
        mock_props = MagicMock()
        mock_props.z_column = "z"
        
        strategy.sync_data(mock_artist, mock_props, sample_data)
        
        args, _ = mock_artist.set_array.call_args
        np.testing.assert_array_equal(args[0], sample_data["z"].values.flatten())
