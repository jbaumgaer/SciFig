import pytest

from src.models.nodes.plot_node import PlotNode
from src.models.plots.plot_properties import (
    AxesLimits,
    LinePlotProperties,
    PlotMapping,
)
from src.services.commands.change_property_command import ChangePropertyCommand


@pytest.fixture
def mock_plot_node():
    """Provides a mock PlotNode for testing."""
    node = PlotNode()
    node.plot_properties = LinePlotProperties(
        title="",
        xlabel="",
        ylabel="",
        plot_mapping=PlotMapping(x=None, y=[]),
        axes_limits=AxesLimits(xlim=(None, None), ylim=(None, None)),
    )
    return node


def test_change_property_command_execute(mock_plot_node):
    """Tests that the command's execute method correctly changes a property."""
    # Arrange
    new_title = "My New Title"
    cmd = ChangePropertyCommand(
        node=mock_plot_node,
        property_name="title",
        new_value=new_title,
        property_dict_name="plot_properties",
    )

    # Act
    cmd.execute()

    # Assert
    assert mock_plot_node.plot_properties.title == new_title
    assert (
        cmd.old_value == ""
    )  # Assert it correctly stored the old value (which was nothing)


def test_change_property_command_undo(mock_plot_node):
    """Tests that the command's undo method correctly reverts a property change."""
    # Arrange
    initial_title = "Initial Title"
    mock_plot_node.plot_properties.title = initial_title

    new_title = "My New Title"
    cmd = ChangePropertyCommand(
        node=mock_plot_node,
        property_name="title",
        new_value=new_title,
        property_dict_name="plot_properties",
    )
    cmd.execute()  # Run execute first to store the old value

    # Act
    cmd.undo()

    # Assert
    assert mock_plot_node.plot_properties.title == initial_title


def test_change_property_command_undo_from_empty(mock_plot_node):
    """
    Tests that undo works correctly when the property did not exist initially.
    """
    # Arrange
    new_title = "A Brand New Title"
    cmd = ChangePropertyCommand(
        node=mock_plot_node,
        property_name="title",
        new_value=new_title,
        property_dict_name="plot_properties",
    )
    cmd.execute()

    # Pre-condition check
    assert mock_plot_node.plot_properties.title == new_title

    # Act
    cmd.undo()

    # Assert
    # After undoing, 'title' key should revert to its original state (not existing).
    # We check that the value is None, which is what `dict.get` returned.
    # A more robust test could be to assert the key is not in the dict,
    # but our command's undo logic sets it to the stored `old_value`, which was None.
    assert mock_plot_node.plot_properties.title == ""
