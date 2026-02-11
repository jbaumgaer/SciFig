from unittest.mock import Mock

import pandas as pd
import pytest

from src.ui.renderers.plotting_strategies import (
    LinePlotStrategy,
    ScatterPlotStrategy,
)


@pytest.fixture
def sample_data():
    """Create a sample Pandas DataFrame for testing."""
    return pd.DataFrame(
        {
            "x": [1, 2, 3, 4, 5],
            "y1": [2, 3, 5, 7, 11],
            "y2": [1, 4, 9, 16, 25],
        }
    )


def test_line_plot_strategy(sample_data):
    """Test that the LinePlotStrategy calls ax.plot with the correct data."""
    # 1. Arrange
    mock_ax = Mock()
    strategy = LinePlotStrategy()
    x_col = "x"
    y_cols = ["y1", "y2"]

    # 2. Act
    strategy.plot(mock_ax, sample_data, x_col, y_cols)

    # 3. Assert
    assert mock_ax.plot.call_count == 2
    # Check the first call
    call_args_1 = mock_ax.plot.call_args_list[0]
    pd.testing.assert_series_equal(
        call_args_1[0][0], sample_data[x_col], check_names=False
    )
    pd.testing.assert_series_equal(
        call_args_1[0][1], sample_data[y_cols[0]], check_names=False
    )
    assert call_args_1[1]["label"] == y_cols[0]

    # Check the second call
    call_args_2 = mock_ax.plot.call_args_list[1]
    pd.testing.assert_series_equal(
        call_args_2[0][0], sample_data[x_col], check_names=False
    )
    pd.testing.assert_series_equal(
        call_args_2[0][1], sample_data[y_cols[1]], check_names=False
    )
    assert call_args_2[1]["label"] == y_cols[1]

    mock_ax.legend.assert_called_once()


def test_scatter_plot_strategy(sample_data):
    """Test that the ScatterPlotStrategy calls ax.scatter with the correct data."""
    # 1. Arrange
    mock_ax = Mock()
    strategy = ScatterPlotStrategy()
    x_col = "x"
    y_cols = ["y1", "y2"]

    # 2. Act
    strategy.plot(mock_ax, sample_data, x_col, y_cols)

    # 3. Assert
    assert mock_ax.scatter.call_count == 2
    # Check the first call
    call_args_1 = mock_ax.scatter.call_args_list[0]
    pd.testing.assert_series_equal(
        call_args_1[0][0], sample_data[x_col], check_names=False
    )
    pd.testing.assert_series_equal(
        call_args_1[0][1], sample_data[y_cols[0]], check_names=False
    )
    assert call_args_1[1]["label"] == y_cols[0]

    # Check the second call
    call_args_2 = mock_ax.scatter.call_args_list[1]
    pd.testing.assert_series_equal(
        call_args_2[0][0], sample_data[x_col], check_names=False
    )
    pd.testing.assert_series_equal(
        call_args_2[0][1], sample_data[y_cols[1]], check_names=False
    )
    assert call_args_2[1]["label"] == y_cols[1]

    mock_ax.legend.assert_called_once()


def test_line_plot_strategy_single_y(sample_data):
    """Test line plot with a single Y column does not call legend."""
    mock_ax = Mock()
    strategy = LinePlotStrategy()
    x_col = "x"
    y_cols = ["y1"]

    strategy.plot(mock_ax, sample_data, x_col, y_cols)

    assert mock_ax.plot.call_count == 1
    mock_ax.legend.assert_not_called()


def test_scatter_plot_strategy_single_y(sample_data):
    """Test scatter plot with a single Y column does not call legend."""
    mock_ax = Mock()
    strategy = ScatterPlotStrategy()
    x_col = "x"
    y_cols = ["y1"]

    strategy.plot(mock_ax, sample_data, x_col, y_cols)

    assert mock_ax.scatter.call_count == 1
    mock_ax.legend.assert_not_called()
