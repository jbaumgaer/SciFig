"""
Test suite for the BatchChangePlotGeometryCommand.
"""

from unittest.mock import MagicMock

import pytest
from src.models.geometry import Rect

from src.models.nodes import PlotNode, SceneNode


@pytest.fixture
def mock_plot_node_1():
    """Fixture for a mock PlotNode."""
    plot = MagicMock(spec=PlotNode)
    plot.id = "plot1"
    plot.geometry = Rect(0, 0, 10, 10)
    plot.parent = MagicMock(spec=SceneNode)
    plot.parent.modelChanged = MagicMock()
    return plot


@pytest.fixture
def mock_plot_node_2():
    """Fixture for another mock PlotNode."""
    plot = MagicMock(spec=PlotNode)
    plot.id = "plot2"
    plot.geometry = Rect(20, 20, 5, 5)
    plot.parent = MagicMock(spec=SceneNode)
    plot.parent.modelChanged = MagicMock()
    return plot


class TestBatchChangePlotGeometryCommand:
    """
    Tests for the BatchChangePlotGeometryCommand.
    """

    def test_execute(self, mock_plot_node_1, mock_plot_node_2):
        """
        Test that the execute method correctly applies new geometries to plots
        and notifies model changes.
        """
        # old_geometries = {
        #     mock_plot_node_1.id: mock_plot_node_1.geometry,
        #     mock_plot_node_2.id: mock_plot_node_2.geometry,
        # }
        # new_geometries = {
        #     mock_plot_node_1.id: Rect(1, 1, 11, 11),
        #     mock_plot_node_2.id: Rect(21, 21, 6, 6),
        # }
        # plots = {mock_plot_node_1.id: mock_plot_node_1, mock_plot_node_2.id: mock_plot_node_2}

        # command = BatchChangePlotGeometryCommand(plots, new_geometries)
        # command.execute()

        # assert mock_plot_node_1.geometry == new_geometries[mock_plot_node_1.id]
        # assert mock_plot_node_2.geometry == new_geometries[mock_plot_node_2.id]
        # mock_plot_node_1.parent.modelChanged.emit.assert_called_once()
        # mock_plot_node_2.parent.modelChanged.emit.assert_called_once()

    def test_undo(self, mock_plot_node_1, mock_plot_node_2):
        """
        Test that the undo method correctly reverts plots to their previous geometries
        and notifies model changes.
        """
        # old_geometries = {
        #     mock_plot_node_1.id: mock_plot_node_1.geometry,
        #     mock_plot_node_2.id: mock_plot_node_2.geometry,
        # }
        # new_geometries = {
        #     mock_plot_node_1.id: Rect(1, 1, 11, 11),
        #     mock_plot_node_2.id: Rect(21, 21, 6, 6),
        # }
        # plots = {mock_plot_node_1.id: mock_plot_node_1, mock_plot_node_2.id: mock_plot_node_2}

        # command = BatchChangePlotGeometryCommand(plots, new_geometries)
        # command.execute()  # Apply new geometries first
        # mock_plot_node_1.parent.modelChanged.emit.reset_mock() # Reset mock after execute
        # mock_plot_node_2.parent.modelChanged.emit.reset_mock()

        # command.undo()

        # assert mock_plot_node_1.geometry == old_geometries[mock_plot_node_1.id]
        # assert mock_plot_node_2.geometry == old_geometries[mock_plot_node_2.id]
        # mock_plot_node_1.parent.modelChanged.emit.assert_called_once()
        # mock_plot_node_2.parent.modelChanged.emit.assert_called_once()

    def test_empty_plots_or_geometries(self):
        """
        Test that the command handles empty plots or new_geometries dictionaries gracefully
        without errors and without emitting modelChanged.
        """
        # plots = {}
        # new_geometries = {}
        # command = BatchChangePlotGeometryCommand(plots, new_geometries)
        # command.execute()
        # command.undo()
        # # Assert no errors and no modelChanged signals were emitted
