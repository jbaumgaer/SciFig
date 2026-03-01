"""
Unit tests for the NodeController.
These tests verify the logic for property-handling methods
(plot type changes, generic property changes, limit editing,
column mapping changes) in its new, isolated location.
"""
from unittest.mock import patch

import pandas as pd
import pytest
from PySide6.QtWidgets import QApplication, QLineEdit  # Added QLineEdit import

from src.controllers.node_controller import NodeController
from src.controllers.project_controller import ProjectController
from src.models.application_model import ApplicationModel
from src.models.nodes.group_node import (
    GroupNode,  # Added GroupNode import for group/ungroup tests
)
from src.models.nodes.plot_node import PlotNode
from src.models.plots.plot_properties import AxesLimits, LinePlotProperties, PlotMapping
from src.services.commands.change_children_order_command import (
    ChangeChildrenOrderCommand,  # Added for reorder
)
from src.services.commands.change_plot_property_command import ChangePlotPropertyCommand
from src.services.commands.command_manager import CommandManager
from src.services.commands.group_nodes_command import (
    GroupNodesCommand,  # Added for group
)
from src.services.commands.ungroup_nodes_command import (
    UngroupNodesCommand,  # Added for ungroup
)
from src.shared.types import PlotType


@pytest.fixture
def mock_app(qtbot):
    """Provides a QApplication instance for tests."""
    app = QApplication.instance()
    if not app:
        app = QApplication([])
    return app


@pytest.fixture
def node_controller_deps(mocker, mock_app):
    """Provides mocked dependencies for NodeController."""
    model = mocker.Mock(spec=ApplicationModel)
    model.selection = []
    model.modelChanged = mocker.Mock()
    model.selectionChanged = mocker.Mock()
    model.scene_root = mocker.Mock(spec=GroupNode) # Mock as GroupNode for find_node_by_id
    model.scene_root.find_node_by_id.return_value = None
    model.create_group_node = mocker.Mock(spec=GroupNode) # For group_nodes

    command_manager = mocker.Mock(spec=CommandManager)
    command_manager.execute_command = mocker.Mock()

    project_controller = mocker.Mock(spec=ProjectController)
    project_controller.load_data_into_plot_node = mocker.AsyncMock() # Async mock

    return model, command_manager, project_controller


@pytest.fixture
def node_controller(node_controller_deps):
    """Provides a NodeController instance with mocked dependencies."""
    model, command_manager, project_controller = node_controller_deps
    return NodeController(
        model=model,
        command_manager=command_manager,
        project_controller=project_controller,
    )


@pytest.fixture
def mock_plot_node_with_props(mocker):
    """Provides a mock PlotNode with basic plot properties."""
    plot_node = mocker.Mock(spec=PlotNode)
    plot_node.id = "test_plot_id"
    plot_node.name = "Test Plot"
    plot_node.data = pd.DataFrame({"x": [1, 2], "y": [1, 2]})
    plot_node.visible = True # Default for scene_node
    plot_node.locked = False # Default for scene_node
    plot_node.plot_properties = LinePlotProperties(
        title="Initial Title",
        plot_type=PlotType.LINE,
        plot_mapping=PlotMapping(x="x", y=["y"]),
        axes_limits=AxesLimits(xlim=(0, 10), ylim=(0, 10)),
    )
    return plot_node


# --- Existing tests would go here if there were any ---

# --- New tests to be added ---


def test_on_subplot_selection_changed_updates_selection_model(
    node_controller, node_controller_deps, mock_plot_node_with_props
):
    """
    Verify that on_subplot_selection_changed correctly updates the application
    model's selection with the identified PlotNode.
    """
    model, _, _ = node_controller_deps
    plot_id = mock_plot_node_with_props.id
    model.scene_root.find_node_by_id.return_value = mock_plot_node_with_props

    node_controller.on_subplot_selection_changed(plot_id)

    model.set_selection.assert_called_once_with([mock_plot_node_with_props])
    model.selectionChanged.emit.assert_called_once()


@pytest.mark.asyncio
async def test_on_select_file_clicked_opens_file_dialog(
    node_controller, node_controller_deps, mock_plot_node_with_props, mocker
):
    """
    Verify that on_select_file_clicked opens a file dialog and updates
    the data_file_path of the plot node temporarily.
    """
    model, _, _ = node_controller_deps
    mock_file_path = "/path/to/new/data.csv"

    # Mock QFileDialog to return a selected file
    mocker.patch(
        "PySide6.QtWidgets.QFileDialog.getOpenFileName",
        return_value=(mock_file_path, "CSV Files (*.csv)"),
    )

    await node_controller.on_select_file_clicked(mock_plot_node_with_props)

    assert mock_plot_node_with_props.data_file_path == mock_file_path


@pytest.mark.asyncio
async def test_on_apply_data_clicked_success_executes_command(
    node_controller, node_controller_deps, mock_plot_node_with_props, mocker
):
    """
    Verify that on_apply_data_clicked successfully loads data and executes a
    ChangePropertyCommand to update the plot node's data and data_file_path.
    """
    model, command_manager, project_controller = node_controller_deps
    file_path = "/path/to/data.csv"
    mock_dataframe = pd.DataFrame({"new_x": [10, 20], "new_y": [10, 20]})

    project_controller.load_data_into_plot_node.return_value = mock_dataframe

    await node_controller.on_apply_data_clicked(mock_plot_node_with_props, file_path)

    project_controller.load_data_into_plot_node.assert_called_once_with(
        file_path, mock_plot_node_with_props
    )
    command_manager.execute_command.assert_called_once()
    assert isinstance(command_manager.execute_command.call_args[0][0], ChangePlotPropertyCommand)

    # Further checks on the command's effect (via execute_command mock)
    # The command should set data and data_file_path
    assert mock_plot_node_with_props.data is mock_dataframe
    assert mock_plot_node_with_props.data_file_path == file_path
    assert mock_plot_node_with_props.plot_properties.plot_mapping.x == "new_x"
    assert mock_plot_node_with_props.plot_properties.plot_mapping.y == ["new_y"]
    assert mock_plot_node_with_props.plot_properties.xlabel == "new_x"
    assert mock_plot_node_with_props.plot_properties.ylabel == "new_y"
    model.modelChanged.emit.assert_called_once()


@pytest.mark.asyncio
async def test_on_apply_data_clicked_failure_handles_error(
    node_controller, node_controller_deps, mock_plot_node_with_props, mocker
):
    """
    Verify that on_apply_data_clicked handles data loading errors gracefully
    and does not execute a command.
    """
    model, command_manager, project_controller = node_controller_deps
    file_path = "/path/to/invalid.csv"

    project_controller.load_data_into_plot_node.side_effect = Exception("Load error")

    with patch.object(node_controller.logger, "error") as mock_logger_error:
        await node_controller.on_apply_data_clicked(mock_plot_node_with_props, file_path)
        mock_logger_error.assert_called_once()

    command_manager.execute_command.assert_not_called()
    model.modelChanged.emit.assert_not_called() # No change on error


def test_set_node_visibility_executes_command(node_controller, node_controller_deps, mock_plot_node_with_props):
    """
    Verify that set_node_visibility executes a ChangePropertyCommand to update
    the PlotNode's visible property.
    """
    model, command_manager, _ = node_controller_deps
    model.scene_root.find_node_by_id.return_value = mock_plot_node_with_props

    node_controller.set_node_visibility(mock_plot_node_with_props.id, False)

    command_manager.execute_command.assert_called_once()
    command = command_manager.execute_command.call_args[0][0]
    assert isinstance(command, ChangePlotPropertyCommand)
    assert command.target_object == mock_plot_node_with_props
    assert command.property_name == "visible"
    assert command.new_value == False
    assert command.old_value == True # Mock default for visible


def test_set_node_locked_executes_command(node_controller, node_controller_deps, mock_plot_node_with_props):
    """
    Verify that set_node_locked executes a ChangePropertyCommand to update
    the PlotNode's locked property.
    """
    model, command_manager, _ = node_controller_deps
    model.scene_root.find_node_by_id.return_value = mock_plot_node_with_props

    node_controller.set_node_locked(mock_plot_node_with_props.id, True)

    command_manager.execute_command.assert_called_once()
    command = command_manager.execute_command.call_args[0][0]
    assert isinstance(command, ChangePlotPropertyCommand)
    assert command.target_object == mock_plot_node_with_props
    assert command.property_name == "locked"
    assert command.new_value == True
    assert command.old_value == False # Mock default for locked


def test_reorder_nodes_executes_command(node_controller, node_controller_deps, mocker):
    """
    Verify that reorder_nodes executes a ChangeChildrenOrderCommand.
    """
    model, command_manager, _ = node_controller_deps
    mock_parent_node = mocker.Mock(spec=GroupNode, id="parent_id") # Must be a GroupNode or SceneNode
    model.scene_root.find_node_by_id.return_value = mock_parent_node

    # We directly verify the instantiation and execution of the command
    node_controller.reorder_nodes("parent_id", "child_id", 0)

    command_manager.execute_command.assert_called_once()
    command = command_manager.execute_command.call_args[0][0]
    assert isinstance(command, ChangeChildrenOrderCommand)
    assert command.target_node == mock_parent_node
    assert command.dragged_node_id == "child_id"
    assert command.new_index == 0


def test_group_nodes_executes_command(node_controller, node_controller_deps, mocker):
    """
    Verify that group_nodes executes a GroupNodesCommand.
    """
    model, command_manager, _ = node_controller_deps
    mock_node_ids = ["id1", "id2"]
    mock_node1 = mocker.Mock(spec=PlotNode, id="id1")
    mock_node2 = mocker.Mock(spec=PlotNode, id="id2")

    # Mock finding nodes and creating a new group
    model.scene_root.find_node_by_id.side_effect = lambda node_id: {
        "id1": mock_node1, "id2": mock_node2
    }.get(node_id)
    mock_new_group_node = mocker.Mock(spec=GroupNode, id="new_group_id")
    model.create_group_node.return_value = mock_new_group_node

    node_controller.group_nodes(mock_node_ids)

    model.create_group_node.assert_called_once()
    command_manager.execute_command.assert_called_once()
    command = command_manager.execute_command.call_args[0][0]
    assert isinstance(command, GroupNodesCommand)
    assert command.parent_node == model.scene_root
    assert command.nodes_to_group == [mock_node1, mock_node2]
    assert command.new_group == mock_new_group_node


def test_ungroup_node_executes_command(node_controller, node_controller_deps, mocker):
    """
    Verify that ungroup_node executes an UngroupNodesCommand.
    """
    model, command_manager, _ = node_controller_deps
    mock_group_node = mocker.Mock(spec=GroupNode, id="group_id")
    model.scene_root.find_node_by_id.return_value = mock_group_node

    node_controller.ungroup_node("group_id")

    command_manager.execute_command.assert_called_once()
    command = command_manager.execute_command.call_args[0][0]
    assert isinstance(command, UngroupNodesCommand)
    assert command.group_node == mock_group_node


def test_rename_node_executes_command(node_controller, node_controller_deps, mock_plot_node_with_props):
    """
    Verify that rename_node executes a ChangePropertyCommand to update
    the Node's name property.
    """
    model, command_manager, _ = node_controller_deps
    model.scene_root.find_node_by_id.return_value = mock_plot_node_with_props
    new_name = "New Plot Name"

    node_controller.rename_node(mock_plot_node_with_props.id, new_name)

    command_manager.execute_command.assert_called_once()
    command = command_manager.execute_command.call_args[0][0]
    assert isinstance(command, ChangePlotPropertyCommand)
    assert command.target_object == mock_plot_node_with_props
    assert command.property_name == "name"
    assert command.new_value == new_name
    assert command.old_value == "Test Plot"


def test_on_limit_editing_finished_reads_current_line_edit_values(node_controller, node_controller_deps, mock_plot_node_with_props, mocker):
    """
    Verify that on_limit_editing_finished reads values from provided QLineEdits
    and executes a ChangePropertyCommand to update the AxesLimits.
    """
    model, command_manager, _ = node_controller_deps
    mock_xlim_min_edit = mocker.Mock(spec=QLineEdit)
    mock_xlim_max_edit = mocker.Mock(spec=QLineEdit)
    mock_ylim_min_edit = mocker.Mock(spec=QLineEdit)
    mock_ylim_max_edit = mocker.Mock(spec=QLineEdit)

    mock_xlim_min_edit.text.return_value = "0.5"
    mock_xlim_max_edit.text.return_value = "9.5"
    mock_ylim_min_edit.text.return_value = "-1.0"
    mock_ylim_max_edit.text.return_value = "15.0"

    node_controller.on_limit_editing_finished(
        mock_plot_node_with_props,
        mock_xlim_min_edit,
        mock_xlim_max_edit,
        mock_ylim_min_edit,
        mock_ylim_max_edit,
    )

    command_manager.execute_command.assert_called_once()
    command = command_manager.execute_command.call_args[0][0]
    assert isinstance(command, ChangePlotPropertyCommand)
    assert command.target_object == mock_plot_node_with_props.plot_properties
    assert command.property_name == "axes_limits"
    assert command.new_value.xlim == (0.5, 9.5)
    assert command.new_value.ylim == (-1.0, 15.0)
    # Verify conversion to float
    assert isinstance(command.new_value.xlim[0], float)
    assert isinstance(command.new_value.ylim[0], float)


def test_on_plot_type_changed_updates_plot_type_property(node_controller, node_controller_deps, mock_plot_node_with_props):
    """
    Verify that on_plot_type_changed executes a ChangePropertyCommand to update
    the plot_type of the PlotNode's plot_properties.
    """
    model, command_manager, _ = node_controller_deps

    # Ensure current plot_type is different from new_plot_type for a change to occur
    mock_plot_node_with_props.plot_properties.plot_type = PlotType.LINE
    new_plot_type = PlotType.SCATTER

    node_controller.on_plot_type_changed(mock_plot_node_with_props, new_plot_type)

    command_manager.execute_command.assert_called_once()
    command = command_manager.execute_command.call_args[0][0]
    assert isinstance(command, ChangePlotPropertyCommand)
    assert command.target_object == mock_plot_node_with_props.plot_properties
    assert command.property_name == "plot_type"
    assert command.new_value == new_plot_type
    assert command.old_value == PlotType.LINE
