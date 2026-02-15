import logging
from pathlib import Path  # New Import
from typing import Optional

from PySide6.QtCore import QObject
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QLineEdit,
)

from src.controllers.project_controller import ProjectController  # New Import
from src.models.application_model import ApplicationModel
from src.models.nodes.plot_node import PlotNode
from src.models.plots.plot_properties import AxesLimits, PlotMapping
from src.models.plots.plot_types import PlotType
from src.services.commands.change_property_command import ChangePropertyCommand
from src.services.commands.command_manager import CommandManager


class NodeController(QObject):
    def __init__(
        self,
        model: ApplicationModel,
        command_manager: CommandManager,
        project_controller: ProjectController,
    ):
        super().__init__()
        self.model = model
        self.command_manager = command_manager
        self.project_controller = project_controller  # Store project_controller
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info("NodeController initialized.")

    def on_subplot_selection_changed(self, plot_id: str):
        """
        Sets the application model's selection to the PlotNode with the given ID.
        """
        if not plot_id:
            self.model.selection = []
            return

        node = self.model.scene_root.find_node_by_id(plot_id)
        if node and isinstance(node, PlotNode):
            self.logger.debug(
                f"NodeController: Setting selection to PlotNode with ID: {plot_id}"
            )
            self.model.selection = [node]
        else:
            self.logger.warning(
                f"NodeController: PlotNode with ID '{plot_id}' not found for selection."
            )
            self.model.selection = []

    def on_select_file_clicked(self, node: PlotNode):
        """
        Opens a file dialog to allow the user to select a data file (e.g., CSV).
        Stores the selected path temporarily in the PlotNode.
        """
        self.logger.debug(f"NodeController: Select file clicked for node {node.id}")
        file_path, _ = QFileDialog.getOpenFileName(
            None, "Select Data File", "", "Data Files (*.csv *.tsv *.txt)"
        )
        if file_path:
            node.data_file_path = Path(file_path)
            self.logger.debug(
                f"NodeController: Selected file: {node.data_file_path} for node {node.id}"
            )
            # The UI will need to re-read node.data_file_path to update the QLineEdit
            self.model.modelChanged.emit()  # Force UI update

    def on_apply_data_clicked(self, node: PlotNode, new_file_path: Optional[Path]):
        """
        Triggers data loading for the given PlotNode from new_file_path.
        """
        self.logger.debug(
            f"NodeController: Apply data clicked for node {node.id} with path {new_file_path}"
        )
        if not new_file_path or not new_file_path.exists():
            self.logger.warning(
                f"NodeController: Invalid file path provided for data loading: {new_file_path}"
            )
            return

        try:
            # Delegate actual data loading to project_controller which manages DataLoader
            new_data = self.project_controller._data_loader.load_data(new_file_path)

            # Create a command to update node.data and node.data_file_path
            cmd = ChangePropertyCommand(
                node=node,
                property_name="data",
                new_value=new_data,
                property_dict_name=None,  # Direct property of PlotNode
                additional_properties={"data_file_path": new_file_path},
            )
            self.command_manager.execute_command(cmd)
            self.logger.info(
                f"NodeController: Successfully loaded and applied data from {new_file_path} to node {node.id}"
            )
        except Exception as e:
            self.logger.error(
                f"NodeController: Failed to load data from {new_file_path} for node {node.id}: {e}"
            )
            # Optionally show a message box to the user

    def on_plot_type_changed(self, new_plot_type_str: str, node: PlotNode):
        """Creates and executes a command when the plot type changes."""
        if not new_plot_type_str:
            return

        new_plot_type = PlotType(new_plot_type_str)

        assert node.plot_properties is not None
        old_plot_type = node.plot_properties.plot_type

        if new_plot_type != old_plot_type:
            cmd = ChangePropertyCommand(
                node=node,
                property_name="plot_type",
                new_value=new_plot_type,
                property_dict_name="plot_properties",
            )
            self.command_manager.execute_command(cmd)
            # Rebuilding UI would typically be handled by properties_panel listening to modelChanged/selectionChanged
            # self.on_selection_changed()  # Rebuild UI

    def on_property_changed(self, node: PlotNode, prop_name: str, new_value: str):
        """Creates and executes a command when a QLineEdit's editing is finished."""
        old_value = getattr(node.plot_properties, prop_name)

        if new_value != old_value:
            cmd = ChangePropertyCommand(
                node=node,
                property_name=prop_name,
                new_value=new_value,
                property_dict_name="plot_properties",
            )
            self.command_manager.execute_command(cmd)

    def on_limit_editing_finished(
        self,
        node: PlotNode,
        xlim_min_edit: QLineEdit,
        xlim_max_edit: QLineEdit,
        ylim_min_edit: QLineEdit,
        ylim_max_edit: QLineEdit,
    ):
        """
        This runs after the user has finished editing in the limit fields.
        It gathers all values from the QLineEdit widgets and executes a single command.
        """
        if not node:
            return

        def _parse_or_none(text: str) -> Optional[float]:
            try:
                return float(text)
            except (ValueError, TypeError):
                return None

        new_xlim_min = _parse_or_none(xlim_min_edit.text())
        new_xlim_max = _parse_or_none(xlim_max_edit.text())
        new_ylim_min = _parse_or_none(ylim_min_edit.text())
        new_ylim_max = _parse_or_none(ylim_max_edit.text())

        assert node.plot_properties is not None
        old_limits = node.plot_properties.axes_limits
        new_limits = AxesLimits(
            xlim=(new_xlim_min, new_xlim_max),
            ylim=(new_ylim_min, new_ylim_max),
        )

        if old_limits != new_limits:
            cmd = ChangePropertyCommand(
                node=node,
                property_name="axes_limits",
                new_value=new_limits,
                property_dict_name="plot_properties",
            )
            self.command_manager.execute_command(cmd)

    def on_column_mapping_changed(
        self,
        new_text_ignored: str,
        node: PlotNode,
        x_combo: QComboBox,
        y_combo: QComboBox,
    ):
        """
        Creates and executes a command when a column selection changes.
        Reads from BOTH combo boxes to create a complete mapping.
        """
        x_col = x_combo.currentText()
        y_col = y_combo.currentText()

        if not x_col or not y_col:
            return

        assert node.plot_properties is not None
        new_mapping = PlotMapping(x=x_col, y=[y_col])
        old_mapping = node.plot_properties.plot_mapping

        if new_mapping != old_mapping:
            cmd = ChangePropertyCommand(
                node=node,
                property_name="plot_mapping",
                new_value=new_mapping,
                property_dict_name="plot_properties",
            )
            self.command_manager.execute_command(cmd)

    def set_node_visibility(self, node_id: str, visible: bool):
        """
        Sets the visibility of a SceneNode.
        """
        node = self.model.scene_root.find_node_by_id(node_id)
        if node and node.visible != visible:
            cmd = ChangePropertyCommand(
                node=node,
                property_name="visible",
                new_value=visible,
                property_dict_name=None,  # Direct property of SceneNode
            )
            self.command_manager.execute_command(cmd)
            self.logger.debug(
                f"NodeController: Set visibility of node {node_id} to {visible}."
            )

    def set_node_locked(self, node_id: str, locked: bool):
        """
        Sets the locked state of a SceneNode.
        """
        node = self.model.scene_root.find_node_by_id(node_id)
        if node and node.locked != locked:
            cmd = ChangePropertyCommand(
                node=node,
                property_name="locked",
                new_value=locked,
                property_dict_name=None,  # Direct property of SceneNode
            )
            self.command_manager.execute_command(cmd)
            self.logger.debug(
                f"NodeController: Set locked state of node {node_id} to {locked}."
            )

    def reorder_nodes(self, parent_id: str, node_id: str, new_index: int):
        """
        Reorders a child node within its parent's children list.
        """
        parent_node = self.model.scene_root.find_node_by_id(parent_id)
        node_to_move = self.model.scene_root.find_node_by_id(node_id)

        if parent_node and node_to_move and node_to_move.parent == parent_node:
            # Need to create a new command for reordering children
            # This would likely involve a ChangeChildrenOrderCommand
            self.logger.warning(
                "NodeController: reorder_nodes not fully implemented yet, requires ChangeChildrenOrderCommand."
            )
            # Placeholder for now, full implementation once command is created.
            # cmd = ChangeChildrenOrderCommand(...)
            # self.command_manager.execute_command(cmd)
        else:
            self.logger.warning(
                f"NodeController: Could not reorder node {node_id} in parent {parent_id}."
            )

    def group_nodes(self, node_ids: list[str]):
        """
        Groups selected nodes under a new GroupNode.
        """
        nodes_to_group = [
            self.model.scene_root.find_node_by_id(nid) for nid in node_ids
        ]
        nodes_to_group = [n for n in nodes_to_group if n is not None]

        if len(nodes_to_group) < 2:
            self.logger.warning("NodeController: Grouping requires at least two nodes.")
            return

        self.logger.warning(
            "NodeController: group_nodes not fully implemented yet, requires GroupNodesCommand."
        )
        # Placeholder for now, full implementation once command is created.
        # cmd = GroupNodesCommand(...)
        # self.command_manager.execute_command(cmd)

    def ungroup_node(self, group_id: str):
        """
        Ungroups a GroupNode, moving its children to its parent.
        """
        # Need to import GroupNode for isinstance check
        from src.models.nodes.group_node import (
            GroupNode,
        )  # Local import to avoid circular dependency

        group_node = self.model.scene_root.find_node_by_id(group_id)
        if group_node and isinstance(group_node, GroupNode):
            self.logger.warning(
                "NodeController: ungroup_node not fully implemented yet, requires UngroupNodesCommand."
            )
            # Placeholder for now, full implementation once command is created.
            # cmd = UngroupNodesCommand(...)
            # self.command_manager.execute_command(cmd)
        else:
            self.logger.warning(
                f"NodeController: Node {group_id} is not a GroupNode or not found for ungrouping."
            )

    def rename_node(self, node_id: str, new_name: str):
        """
        Renames a SceneNode.
        """
        node = self.model.scene_root.find_node_by_id(node_id)
        if node and node.name != new_name:
            cmd = ChangePropertyCommand(
                node=node,
                property_name="name",
                new_value=new_name,
                property_dict_name=None,  # Direct property of SceneNode
            )
            self.command_manager.execute_command(cmd)
            self.logger.debug(f"NodeController: Renamed node {node_id} to {new_name}.")
