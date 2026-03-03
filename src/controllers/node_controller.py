import logging
from pathlib import Path
from typing import Any, Optional

import pandas as pd
from PySide6.QtCore import QObject

from src.models.application_model import ApplicationModel
from src.models.nodes.plot_node import PlotNode
from src.models.nodes.scene_node import SceneNode
from src.models.plots.plot_types import ArtistType
from src.services.commands.apply_data_to_node_command import ApplyDataToNodeCommand
from src.services.commands.change_plot_property_command import ChangePlotPropertyCommand
from src.services.commands.command_manager import CommandManager
from src.services.event_aggregator import EventAggregator
from src.shared.events import Events


class NodeController(QObject):
    """
    TODO: In the future, there will be different node controllers, e.g. PlotNodeController.
    Orchestrates high-level node operations (Structure, Data, and High-Level properties).
    Delegates granular property updates to the generic path-based command system.
    """

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
        """
        Subscribes to high-level orchestration requests.
        Granular property updates now use a single generic event.
        """
        """Subscribes to all relevant application events. TODO: Unsure if subscribing should be handled by the controller itself or if there should be a separate layer (currently the composition root) responsible for wiring up event subscriptions."""
        self._event_aggregator.subscribe(
            Events.SUBPLOT_SELECTION_IN_UI_CHANGED, self._on_subplot_selection_request
        )
        self._event_aggregator.subscribe(
            Events.SELECT_DATA_FILE_FOR_NODE_REQUESTED,
            self._on_select_data_file_request,
        )
        self._event_aggregator.subscribe(
            Events.PATH_PROVIDED_FOR_NODE_DATA_OPEN, self._on_data_file_path_provided
        )
        self._event_aggregator.subscribe(
            Events.APPLY_DATA_TO_NODE_REQUESTED, self._on_apply_data_request
        )
        self._event_aggregator.subscribe(Events.NODE_DATA_LOADED, self._on_data_loaded)
        self._event_aggregator.subscribe(
            Events.CHANGE_PLOT_TYPE_REQUESTED, self._on_plot_type_change_request
        )
        self._event_aggregator.subscribe(
            Events.CHANGE_PLOT_COMPONENT_REQUESTED,
            self._on_generic_property_change_request,
        )
        self._event_aggregator.subscribe(
            Events.CHANGE_NODE_VISIBILITY_REQUESTED, self._on_node_visibility_request
        )
        self._event_aggregator.subscribe(
            Events.RENAME_NODE_REQUESTED, self._on_rename_node_request
        )
        self._event_aggregator.subscribe(
            Events.CHANGE_NODE_LOCKED_REQUESTED, self._on_node_locked_request
        )
        self._event_aggregator.subscribe(
            Events.TEMPLATE_LOADED, self._on_template_loaded
        )
        self._event_aggregator.subscribe(
            Events.SELECTION_CHANGED, self._on_selection_changed_for_ui
        )

        # TODO: Add subscriptions for group, ungroup, reorder requests when commands are implemented

    def _on_selection_changed_for_ui(self, selected_node_ids: list[str]):
        """
        Analyzes the selection and publishes events to manage UI components
        like the SidePanel based on the selection state.
        """
        if len(selected_node_ids) == 1:
            node = self._get_node_by_id(selected_node_ids[0])
            if isinstance(node, PlotNode):
                self.logger.debug(
                    "NodeController: Single PlotNode selected. Requesting SidePanel switch to 'properties' tab."
                )
                self._event_aggregator.publish(
                    Events.SWITCH_SIDEPANEL_TAB, tab_key="properties"
                )

    def _get_node_by_id(self, node_id: str) -> Optional[SceneNode]:
        node = self.model.scene_root.find_node_by_id(
            node_id
        )  # TODO: In the fugure, I might want to change this by asking the model for the node directly, instead of reaching deep into the model's scene graph
        if not node:
            self.logger.warning(f"NodeController: Node with ID '{node_id}' not found.")
        return node

    def _get_plot_node_by_id(self, node_id: str) -> Optional[PlotNode]:
        node = self._get_node_by_id(node_id)
        if not (node and isinstance(node, PlotNode)):
            self.logger.warning(
                f"NodeController: PlotNode with ID '{node_id}' not found or not a PlotNode."
            )
            return None
        return node

    def _on_subplot_selection_request(self, node_id: str):
        """Handles selection requests from UI components like the Layers Tab."""
        node = self._get_node_by_id(node_id)
        self.model.set_selection([node] if node else [])

    def _on_select_data_file_request(self, node_id: str):
        """
        Publishes a request for the UI to prompt for a data file path for a node.
        """
        node = self._get_plot_node_by_id(node_id)
        if not node:
            self.logger.warning(
                f"NodeController: Cannot request data file for non-existent node with ID: {node_id}"
            )
            return
        self.logger.debug(
            f"NodeController: Requesting data file selection for node {node_id}"
        )
        self._event_aggregator.publish(
            Events.PROMPT_FOR_OPEN_PATH_FOR_NODE_DATA_REQUESTED, node_id=node_id
        )
        # TODO: This event is currently not being answered by the ui

    def _on_data_file_path_provided(self, node_id: str, path: Optional[Path]):
        """
        Handles the provided data file path from the UI and updates the node.
        """
        node = self._get_plot_node_by_id(node_id)
        if not node:
            return

        cmd = ChangePlotPropertyCommand(
            node=node,
            path="data_file_path",
            new_value=path,
            event_aggregator=self._event_aggregator,
        )
        self.command_manager.execute_command(cmd)

    def _on_apply_data_request(self, node_id: str, file_path: Optional[Path]):
        """Triggers asynchronous data loading via DataService."""
        if file_path and file_path.exists():
            self._event_aggregator.publish(
                Events.APPLY_DATA_FILE_REQUESTED, node_id=node_id, file_path=file_path
            )

    def _on_data_loaded(self, node_id: str, data: pd.DataFrame, file_path: Path):
        """
        Triggered when DataService successfully loads a file.
        Orchestrates theming, default mapping, and model update via commands.
        """
        node = self._get_plot_node_by_id(node_id)
        if not node:
            return

        # 1. Ensure PlotProperties exist (Strict Theming)
        if not node.plot_properties:
            # Default to LINE plot for new data. This could be made configurable.
            self._event_aggregator.publish(
                Events.INITIALIZE_PLOT_THEME_REQUESTED,
                node_id=node.id,
                plot_type=ArtistType.LINE,
            )
            self.logger.info(f"Initialized themed properties for node {node_id}")

        commands = []

        # 2. Heuristic: Default Column Mapping (First two columns)
        if data.shape[1] >= 2 and node.plot_properties.artists:
            cols = data.columns
            # Update primary artist mapping
            commands.append(
                ChangePlotPropertyCommand(
                    node=node,
                    path="artists.0.x_column",
                    new_value=cols[0],
                    event_aggregator=self._event_aggregator,
                )
            )
            commands.append(
                ChangePlotPropertyCommand(
                    node=node,
                    path="artists.0.y_column",
                    new_value=cols[1],
                    event_aggregator=self._event_aggregator,
                )
            )

        # 3. Update Data
        commands.append(
            ChangePlotPropertyCommand(
                node=node,
                path="data",
                new_value=data,
                event_aggregator=self._event_aggregator,
            )
        )

        # 4. Update data_file_path (for persistence)
        commands.append(
            ChangePlotPropertyCommand(
                node=node,
                path="data_file_path",
                new_value=file_path,
                event_aggregator=self._event_aggregator,
            )
        )

        # 5. Reset Limits to (None, None) to trigger Matplotlib Autoscale
        # Resolve path based on coordinate system
        is_polar = (
            node.plot_properties.coords.coord_type == ArtistType.POLAR_LINE
        )  # CoordinateSystem.POLAR is used for POLAR_LINE artist
        # TODO: Refactor ArtistType/CoordinateSystem alignment
        x_path = "coords.theta_axis.limits" if is_polar else "coords.xaxis.limits"
        y_path = "coords.r_axis.limits" if is_polar else "coords.yaxis.limits"

        commands.append(
            ChangePlotPropertyCommand(
                node=node,
                path=x_path,
                new_value=(None, None),
                event_aggregator=self._event_aggregator,
            )
        )
        commands.append(
            ChangePlotPropertyCommand(
                node=node,
                path=y_path,
                new_value=(None, None),
                event_aggregator=self._event_aggregator,
            )
        )

        # Execute as a single atomic transaction to avoid redundant redraws
        macro_cmd = ApplyDataToNodeCommand(
            node=node, 
            commands=commands, 
            event_aggregator=self._event_aggregator
        )
        self.command_manager.execute_command(macro_cmd)

    def _on_plot_type_change_request(self, node_id: str, new_plot_type_str: str):
        """Swaps the entire property tree for a new themed one of a different type."""
        node = self._get_plot_node_by_id(node_id)
        if not (node and new_plot_type_str):
            return

        new_type = ArtistType(new_plot_type_str)

        # Check if unchanged
        if (
            node.plot_properties
            and hasattr(node.plot_properties, "plot_type")
            and node.plot_properties.plot_type == new_type
        ):
            return

        self._event_aggregator.publish(
            Events.INITIALIZE_PLOT_THEME_REQUESTED, node_id=node.id, plot_type=new_type
        )

    def _on_generic_property_change_request(self, node_id: str, path: str, value: Any):
        """Routes all granular property changes to the path-based command system."""
        node = self._get_node_by_id(node_id)
        if not node:
            return

        # Simple type conversion for common numeric inputs from UI
        if isinstance(value, str):
            try:
                if "." in value:
                    value = float(value)
                else:
                    value = int(value)
            except ValueError:
                pass  # Keep as string if conversion fails

        self.command_manager.execute_command(
            ChangePlotPropertyCommand(
                node=node,
                path=path,
                new_value=value,
                event_aggregator=self._event_aggregator,
            )
        )

    def _on_node_visibility_request(self, node_id: str, visible: bool):
        """
        Handles requests to set the visibility of a SceneNode.
        TODO: This should later go into a general node handler or maybe the layers controller
        """
        node = self._get_node_by_id(node_id)
        if node and node.visible != visible:
            cmd = ChangePlotPropertyCommand(
                node=node,
                path="visible",
                new_value=visible,
                event_aggregator=self._event_aggregator,
            )
            self.command_manager.execute_command(cmd)

    def _on_node_locked_request(self, node_id: str, locked: bool):
        """
        Handles requests to set the locked state of a SceneNode.
        TODO: This should later go into a general node handler or maybe the layers controller
        """
        node = self._get_node_by_id(node_id)
        if node and node.locked != locked:
            cmd = ChangePlotPropertyCommand(
                node=node,
                path="locked",
                new_value=locked,
                event_aggregator=self._event_aggregator,
            )
            self.command_manager.execute_command(cmd)

    def _on_rename_node_request(self, node_id: str, new_name: str):
        """
        Handles requests to rename a SceneNode.
        TODO: This should later go into a general node handler or maybe the layers controller
        """
        node = self._get_node_by_id(node_id)
        if node and node.name != new_name:
            cmd = ChangePlotPropertyCommand(
                node=node,
                path="name",
                new_value=new_name,
                event_aggregator=self._event_aggregator,
            )
            self.command_manager.execute_command(cmd)

    def _on_template_loaded(self, root_node: SceneNode):
        """
        Traverses the template root, identifies PlotNodes with sparse data,
        and triggers reactive theme hydration.
        """
        self.logger.info(
            "NodeController: Template loaded. Scanning for nodes to hydrate."
        )
        # Recursively find all PlotNodes in the newly loaded template tree
        for node in root_node.all_descendants(of_type=PlotNode):
            # Check if property hydration is needed (stored as sparse dict from template JSON)
            if isinstance(node.plot_properties, dict):
                overrides = node.plot_properties
                self.logger.debug(f"  Requesting hydration for PlotNode '{node.id}'.")
                self._event_aggregator.publish(
                    Events.HYDRATE_PLOT_PROPERTIES_REQUESTED,
                    node_id=node.id,
                    overrides=overrides,
                )

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
