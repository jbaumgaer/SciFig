import logging
from pathlib import Path
from typing import Optional, Any

from PySide6.QtCore import QObject
import pandas as pd

from src.models.application_model import ApplicationModel
from src.models.nodes.plot_node import PlotNode
from src.models.nodes.scene_node import SceneNode
from src.models.plots.plot_properties import AxesLimits, PlotMapping
from src.models.plots.plot_types import PlotType
from src.services.commands.change_property_command import ChangePropertyCommand
from src.services.commands.command_manager import CommandManager
from src.services.event_aggregator import EventAggregator
from src.shared.events import Events


class NodeController(QObject):
    """TODO: In the future, there will be different node controllers, e.g. PlotNodeController."""
    def __init__(
        self,
        model: ApplicationModel,
        command_manager: CommandManager,
        event_aggregator: EventAggregator,
    ):
        super().__init__()
        self.model = model
        self.command_manager = command_manager
        self._event_aggregator = event_aggregator
        self.logger = logging.getLogger(self.__class__.__name__)

        self._subscribe_to_events()
        self.logger.info("NodeController initialized.")

    def _subscribe_to_events(self):
        """Subscribes to all relevant application events. TODO: Unsure if subscribing should be handled by the controller itself or if there should be a separate layer (currently the composition root) responsible for wiring up event subscriptions."""
        self._event_aggregator.subscribe(
            Events.SUBPLOT_SELECTION_IN_UI_CHANGED, self._handle_subplot_selection_changed_request
        )
        self._event_aggregator.subscribe(
            Events.SELECT_DATA_FILE_FOR_NODE_REQUESTED, self._handle_select_data_file_request
        )
        self._event_aggregator.subscribe(
            Events.PATH_PROVIDED_FOR_NODE_DATA_OPEN, self._handle_data_file_path_provided
        )
        self._event_aggregator.subscribe(
            Events.APPLY_DATA_TO_NODE_REQUESTED, self._handle_apply_data_request
        )
        self._event_aggregator.subscribe(
            Events.CHANGE_PLOT_TYPE_REQUESTED, self._handle_plot_type_change_request
        )
        self._event_aggregator.subscribe(
            Events.CHANGE_PLOT_TITLE_REQUESTED,
            lambda node_id, new_title: self._handle_generic_property_change_request(node_id, "title", new_title)
        )
        self._event_aggregator.subscribe(
            Events.CHANGE_PLOT_XLABEL_REQUESTED,
            lambda node_id, new_xlabel: self._handle_generic_property_change_request(node_id, "xlabel", new_xlabel)
        )
        self._event_aggregator.subscribe(
            Events.CHANGE_PLOT_YLABEL_REQUESTED,
            lambda node_id, new_ylabel: self._handle_generic_property_change_request(node_id, "ylabel", new_ylabel)
        )
        self._event_aggregator.subscribe(
            Events.CHANGE_PLOT_MARKER_SIZE_REQUESTED, self._handle_marker_size_change_request
        )
        self._event_aggregator.subscribe(
            Events.CHANGE_PLOT_AXIS_LIMITS_REQUESTED, self._handle_limit_editing_request
        )
        self._event_aggregator.subscribe(
            Events.MAP_PLOT_COLUMNS_REQUESTED, self._handle_column_mapping_request
        )
        self._event_aggregator.subscribe(
            Events.CHANGE_NODE_VISIBILITY_REQUESTED, self._handle_node_visibility_request
        )
        self._event_aggregator.subscribe(
            Events.RENAME_NODE_REQUESTED, self._handle_rename_node_request
        )
        self._event_aggregator.subscribe(
            Events.CHANGE_NODE_LOCKED_REQUESTED, self._handle_node_locked_request
        )
        self._event_aggregator.subscribe(
           Events.SELECTION_CHANGED, self._handle_selection_for_ui_management
       )
        # TODO: Add subscriptions for group, ungroup, reorder requests when commands are implemented

    def _handle_selection_for_ui_management(self, selected_node_ids: list[str]):
        """
        Analyzes the selection and publishes events to manage UI components
        like the SidePanel based on the selection state.
        """
        if len(selected_node_ids) == 1:
            # We must get the node from the model to check its type
            node = self._get_node_by_id(selected_node_ids[0])
            if isinstance(node, PlotNode):
                self.logger.debug(
                    "NodeController: Single PlotNode selected. Requesting SidePanel switch to 'properties' tab."
                )
                self._event_aggregator.publish(
                    Events.SWITCH_SIDEPANEL_TAB, tab_key="properties"
                )

    def _get_node_by_id(self, node_id: str) -> Optional[SceneNode]:
        node = self.model.scene_root.find_node_by_id(node_id) #TODO: In the fugure, I might want to change this by asking the model for the node directly, instead of reaching deep into the model's scene graph
        if not node:
            self.logger.warning(f"NodeController: Node with ID '{node_id}' not found.")
        return node

    def _get_plot_node_by_id(self, node_id: str) -> Optional[PlotNode]:
        node = self._get_node_by_id(node_id)
        if not (node and isinstance(node, PlotNode)):
            self.logger.warning(f"NodeController: PlotNode with ID '{node_id}' not found or not a PlotNode.")
            return None
        return node

    # --- Request Handlers ---

    def _handle_subplot_selection_changed_request(self, plot_id: str):
        """
        Sets the application model's selection to the PlotNode with the given ID
        and publishes SELECTION_CHANGED.
        """
        if not plot_id:
            self.model.set_selection([])
            self._event_aggregator.publish(Events.SELECTION_CHANGED, selected_node_ids=[])
            return

        node = self._get_plot_node_by_id(plot_id)
        if node:
            self.logger.debug(
                f"NodeController: Setting selection to PlotNode with ID: {plot_id}"
            )
            self.model.set_selection([node])
            self._event_aggregator.publish(Events.SELECTION_CHANGED, selected_node_ids=[node.id])
        else:
            self.model.set_selection([])
            self._event_aggregator.publish(Events.SELECTION_CHANGED, selected_node_ids=[])


    def _handle_select_data_file_request(self, node_id: str):
        """
        Publishes a request for the UI to prompt for a data file path for a node.
        """
        node = self._get_plot_node_by_id(node_id)
        if not node:
            self.logger.warning(f"NodeController: Cannot request data file for non-existent node with ID: {node_id}")
            return
        self.logger.debug(f"NodeController: Requesting data file selection for node {node_id}")
        self._event_aggregator.publish(Events.PROMPT_FOR_OPEN_PATH_FOR_NODE_DATA_REQUESTED, node_id=node_id)
        #TODO: This event is currently not being answered by the ui


    def _handle_data_file_path_provided(self, node_id: str, path: Optional[Path]):
        """
        Handles the provided data file path from the UI and updates the node.
        """
        node = self._get_plot_node_by_id(node_id)
        if not node:
            return

        # Use a command to update node.data_file_path, this will also publish NODE_DATA_FILE_PATH_UPDATED
        cmd = ChangePropertyCommand(
            node=node,
            property_name="data_file_path",
            new_value=path,
            property_dict_name=None,
            event_aggregator=self._event_aggregator,
        )
        self.command_manager.execute_command(cmd)


    def _handle_apply_data_request(self, node_id: str, file_path: Optional[Path]):
        """
        Triggers data loading for the given PlotNode from new_file_path.
        """
        node = self._get_plot_node_by_id(node_id)
        if not node:
            return

        if not file_path or not file_path.exists():
            self.logger.warning(
                f"NodeController: Invalid file path provided for data loading: {file_path}"
            )
            # TODO: Publish an error event
            return

        try:
            #TODO: Instead of the node and canvas controller handling this, I should invoke a data loader service with a request
            new_data = pd.read_csv(file_path, sep=";")  # Placeholder for loaded data, replace with actual loading logic

            cmd = ChangePropertyCommand(
                node=node,
                property_name="data",
                new_value=new_data,
                property_dict_name=None,
                event_aggregator=self._event_aggregator,
                # additional_properties={"data_file_path": file_path}, # TODO: Check if this is needed
            )
            self.command_manager.execute_command(cmd)
            self.logger.info(
                f"NodeController: Successfully loaded and applied data from {file_path} to node {node_id}"
            )
        except Exception as e:
            self.logger.error(
                f"NodeController: Failed to load data from {file_path} for node {node_id}: {e}"
            )
            # TODO: Publish an error event to be displayed by UI


    def _handle_plot_type_change_request(self, node_id: str, new_plot_type_str: str):
        """Creates and executes a command when the plot type changes."""
        node = self._get_plot_node_by_id(node_id)
        if not node:
            return

        if not new_plot_type_str:
            return

        new_plot_type = PlotType(new_plot_type_str)

        assert node.plot_properties is not None
        old_plot_type = node.plot_properties.plot_type

        if new_plot_type == old_plot_type:
            self.logger.debug(f"NodeController: Plot type unchanged for node {node_id}")
            return
        cmd = ChangePropertyCommand(
            node=node,
            property_name="plot_type",
            new_value=new_plot_type,
            property_dict_name="plot_properties",
            event_aggregator=self._event_aggregator,
        )
        self.command_manager.execute_command(cmd)


    def _handle_generic_property_change_request(self, node_id: str, prop_name: str, new_value: Any):
        """
        Handles requests to change a generic property (title, xlabel, ylabel, marker_size).
        """
        node = self._get_plot_node_by_id(node_id)
        if not node or not node.plot_properties:
            return

        # Attempt to convert value if needed, e.g., for marker_size
        if prop_name == "marker_size":
            try:
                new_value = float(new_value)
            except ValueError:
                self.logger.warning(f"Invalid value for marker_size: {new_value}. Not applying.")
                return

        # old_value = getattr(node.plot_properties, prop_name) # No longer needed, command handles comparison

        cmd = ChangePropertyCommand(
            node=node,
            property_name=prop_name,
            new_value=new_value,
            property_dict_name="plot_properties",
            event_aggregator=self._event_aggregator,
        )
        self.command_manager.execute_command(cmd)


    def _handle_marker_size_change_request(self, node_id: str, new_size: str):
        """Handles request to change marker size, including value parsing.
        TODO: Somehow refactor this together with the generic property change handler, so that parsing logic can be reused for different properties."""
        node = self._get_plot_node_by_id(node_id)
        if not node or not node.plot_properties:
            return
        
        try:
            parsed_size = float(new_size)
        except ValueError:
            self.logger.warning(f"Invalid marker size value: {new_size}. Request ignored.")
            return
        
        cmd = ChangePropertyCommand(
            node=node,
            property_name="marker_size",
            new_value=parsed_size,
            property_dict_name="plot_properties",
            event_aggregator=self._event_aggregator,
        )
        self.command_manager.execute_command(cmd)


    def _handle_limit_editing_request(
        self,
        node_id: str,
        xlim_min: str,
        xlim_max: str,
        ylim_min: str,
        ylim_max: str,
    ):
        """
        Handles requests to change axis limits. Parses string inputs.
        """
        node = self._get_plot_node_by_id(node_id)
        if not node or not node.plot_properties:
            return

        def _parse_or_none(text: str) -> Optional[float]:
            #TODO: Make this a general function in a utils module, since similar parsing is needed in multiple places. Maybe an InputValidationService
            try:
                return float(text)
            except (ValueError, TypeError):
                return None

        new_xlim_min = _parse_or_none(xlim_min)
        new_xlim_max = _parse_or_none(xlim_max)
        new_ylim_min = _parse_or_none(ylim_min)
        new_ylim_max = _parse_or_none(ylim_max)

        old_limits = node.plot_properties.axes_limits
        new_limits = AxesLimits(
            xlim=(new_xlim_min, new_xlim_max),
            ylim=(new_ylim_min, new_ylim_max),
        )

        if old_limits != new_limits: #TODO: This comparison logic is now duplicated in the command, maybe it should be handled solely in the command
            cmd = ChangePropertyCommand(
                node=node,
                property_name="axes_limits",
                new_value=new_limits,
                property_dict_name="plot_properties",
                event_aggregator=self._event_aggregator,
            )
            self.command_manager.execute_command(cmd)

    def _handle_column_mapping_request(
        self,
        node_id: str,
        x_column: str,
        y_column: str,
    ):
        """
        Handles requests to change column mappings for a plot.
        """
        node = self._get_plot_node_by_id(node_id)
        if not node or not node.plot_properties:
            self.logger.warning(f"NodeController: Cannot change column mapping for non-existent plot node with ID: {node_id}")
            return

        if not x_column or not y_column:
            self.logger.warning(f"NodeController: Cannot change column mapping for node {node_id} because x_column or y_column is empty.")
            return

        new_mapping = PlotMapping(x=x_column, y=[y_column])
        old_mapping = node.plot_properties.plot_mapping

        if new_mapping != old_mapping:
            cmd = ChangePropertyCommand(
                node=node,
                property_name="plot_mapping",
                new_value=new_mapping,
                property_dict_name="plot_properties",
                event_aggregator=self._event_aggregator,
            )
            self.command_manager.execute_command(cmd)

    def _handle_node_visibility_request(self, node_id: str, visible: bool):
        """
        Handles requests to set the visibility of a SceneNode.
        TODO: This should later go into a general node handler or maybe the layers controller
        """
        node = self._get_node_by_id(node_id)
        if node and node.visible != visible:
            cmd = ChangePropertyCommand(
                node=node,
                property_name="visible",
                new_value=visible,
                property_dict_name=None,
                event_aggregator=self._event_aggregator,
            )
            self.command_manager.execute_command(cmd)

    def _handle_node_locked_request(self, node_id: str, locked: bool):
        """
        Handles requests to set the locked state of a SceneNode.
        TODO: This should later go into a general node handler or maybe the layers controller
        """
        node = self._get_node_by_id(node_id)
        if node and node.locked != locked:
            cmd = ChangePropertyCommand(
                node=node,
                property_name="locked",
                new_value=locked,
                property_dict_name=None,
                event_aggregator=self._event_aggregator,
            )
            self.command_manager.execute_command(cmd)


    def _handle_rename_node_request(self, node_id: str, new_name: str):
        """
        Handles requests to rename a SceneNode.
        TODO: This should later go into a general node handler or maybe the layers controller
        """
        node = self._get_node_by_id(node_id)
        if node and node.name != new_name:
            cmd = ChangePropertyCommand(
                node=node,
                property_name="name",
                new_value=new_name,
                property_dict_name=None,
                event_aggregator=self._event_aggregator,
            )
            self.command_manager.execute_command(cmd)

    # These methods are currently just warnings, actual commands need to be implemented
    def reorder_nodes(self, parent_id: str, node_id: str, new_index: int):
        """
        Reorders a child node within its parent's children list.
        """
        # Placeholder for now, full implementation once command is created.
        # cmd = ChangeChildrenOrderCommand(...)
         # self.command_manager.execute_command(cmd)
        self.logger.warning(
            "NodeController: reorder_nodes not fully implemented yet, requires ChangeChildrenOrderCommand."
        )

    def group_nodes(self, node_ids: list[str]):
        """
        Groups selected nodes under a new GroupNode.
        """
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
        self.logger.warning(
            "NodeController: ungroup_node not fully implemented yet, requires UngroupNodesCommand."
        )
        # Placeholder for now, full implementation once command is created.
        # cmd = UngroupNodesCommand(...)
        # self.command_manager.execute_command(cmd)
