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
from src.services.commands.add_plot_command import AddPlotCommand
from src.services.commands.change_node_property_command import ChangeNodePropertyCommand
from src.services.commands.move_node_command import MoveNodeCommand
from src.services.commands.command_manager import CommandManager
from src.services.commands.delete_node_command import DeleteNodeCommand
from src.services.commands.macro_command import MacroCommand
from src.services.event_aggregator import EventAggregator
from src.services.property_service import PropertyService
from src.shared.events import Events
from src.shared.geometry import Rect


class NodeController(QObject):
    """
    TODO: In the future, there will be different node controllers, e.g. PlotNodeController.
    Orchestrates high-level node operations (Structure, Data, and High-Level properties).
    Delegates granular property updates to the generic path-based command system.
    Now supports the 'Bypass Pattern' for silent model reconciliation.
    """

    def __init__(
        self,
        model: ApplicationModel,
        command_manager: CommandManager,
        event_aggregator: EventAggregator,
        property_service: PropertyService,
    ):
        super().__init__()
        self.model = model
        self.command_manager = command_manager
        self._event_aggregator = event_aggregator
        self._property_service = property_service
        self.logger = logging.getLogger(self.__class__.__name__)

        self._subscribe_to_events()
        self.logger.info("NodeController initialized.")

    def _subscribe_to_events(self):
        """Subscribes to all relevant application events."""
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
            Events.CHANGE_PLOT_NODE_PROPERTY_REQUESTED,
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
        self._event_aggregator.subscribe(
            Events.PLOT_NODE_PROPERTY_RECONCILIATION_REQUESTED,
            self.reconcile_node_property,
        )
        self._event_aggregator.subscribe(
            Events.DELETE_NODES_REQUESTED, self._on_delete_nodes_request
        )
        self._event_aggregator.subscribe(
            Events.ADD_PLOT_REQUESTED, self._on_add_plot_request
        )

        # TODO: Add subscriptions for group, ungroup, reorder requests when commands are implemented

    def _on_add_plot_request(self, geometry: Rect):
        """
        Handles requests to add a new plot to the scene.
        """
        cmd = AddPlotCommand(
            model=self.model,
            event_aggregator=self._event_aggregator,
            geometry=geometry
        )
        self.command_manager.execute_command(cmd)
        
        # Immediately initialize theme so the plot becomes visible in the renderer
        if cmd.node:
            self.logger.info(f"NodeController: Initializing theme for new plot {cmd.node.id}")
            self._event_aggregator.publish(
                Events.INITIALIZE_PLOT_THEME_REQUESTED,
                node_id=cmd.node.id,
                plot_type=ArtistType.LINE  # Default to Line
            )

    def _on_delete_nodes_request(self, node_ids: list[str]):
        """
        Handles requests to delete multiple nodes.
        Wraps individual DeleteNodeCommands into a single atomic MacroCommand.
        """
        if not node_ids:
            return

        commands = []
        for node_id in node_ids:
            commands.append(
                DeleteNodeCommand(
                    model=self.model,
                    event_aggregator=self._event_aggregator,
                    node_id=node_id,
                )
            )

        if len(commands) == 1:
            self.command_manager.execute_command(commands[0])
        else:
            macro_cmd = MacroCommand(
                description=f"Delete {len(node_ids)} nodes",
                commands=commands,
                event_aggregator=self._event_aggregator,
            )
            self.command_manager.execute_command(macro_cmd)

    def reconcile_node_property(self, node_id: str, path: str, value: Any):
        """
        Implementation of the 'Bypass Pattern'. 
        Updates the model directly via PropertyService, bypassing the CommandManager.
        Publishes a RECONCILED event instead of a CHANGED event to avoid redraw loops.
        """
        node = self._get_node_by_id(node_id)
        if not node:
            return

        # 1. Map the path correctly
        # If it's a plot property, we prefix it so the PropertyService starts from the Node root
        full_path = path
        first_part = path.split(".")[0]
        if hasattr(node, "plot_properties") and node.plot_properties:
            if hasattr(node.plot_properties, first_part) or first_part == "artists":
                full_path = f"plot_properties.{path}"

        try:
            # 2. Update the value silently via the Node root to trigger automatic versioning
            self._property_service.set_value(node, full_path, value)
            
            # 3. Publish specific reconciled event (Property Panel listens, Renderer ignores)
            self._event_aggregator.publish(
                Events.PLOT_NODE_PROPERTY_RECONCILED,
                node_id=node_id,
                path=path,
                new_value=value
            )
            self.logger.debug(f"Reconciled {node_id}.{path} to {value}")
        except Exception as e:
            self.logger.error(f"Reconciliation failed for {node_id}.{path}: {e}")

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
        node = self.model.scene_root.find_node_by_id(node_id)
        if not node:
            self.logger.warning(f"Node with ID '{node_id}' not found.")
        return node

    def _get_plot_node_by_id(self, node_id: str) -> Optional[PlotNode]:
        node = self._get_node_by_id(node_id)
        if not (node and isinstance(node, PlotNode)):
            self.logger.warning(
                f"PlotNode with ID '{node_id}' not found or not a PlotNode."
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
            return
        self._event_aggregator.publish(
            Events.PROMPT_FOR_OPEN_PATH_FOR_NODE_DATA_REQUESTED, node_id=node_id
        )

    def _on_data_file_path_provided(self, node_id: str, path: Optional[Path]):
        """
        Handles the provided data file path from the UI and updates the node.
        """
        node = self._get_plot_node_by_id(node_id)
        if not node:
            return
        
        cmd = ChangeNodePropertyCommand(
            node=node,
            path="data_file_path",
            new_value=path,
            event_aggregator=self._event_aggregator,
            property_service=self._property_service,
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
        """
        node = self._get_plot_node_by_id(node_id)
        if not node:
            return

        if not node.plot_properties:
            self._event_aggregator.publish(
                Events.INITIALIZE_PLOT_THEME_REQUESTED,
                node_id=node.id,
                plot_type=ArtistType.LINE,
            )

        commands = []
        # TODO: This should be extracted into its own set plot axes method
        if data.shape[1] >= 2 and node.plot_properties and node.plot_properties.artists:
            cols = data.columns
            commands.append(
                ChangeNodePropertyCommand(
                    node=node,
                    path="artists.0.x_column",
                    new_value=cols[0],
                    event_aggregator=self._event_aggregator,
                    property_service=self._property_service,
                )
            )
            commands.append(
                ChangeNodePropertyCommand(
                    node=node,
                    path="artists.0.y_column",
                    new_value=cols[1],
                    event_aggregator=self._event_aggregator,
                    property_service=self._property_service,
                )
            )

        commands.append(
            ChangeNodePropertyCommand(
                node=node,
                path="data",
                new_value=data,
                event_aggregator=self._event_aggregator,
                property_service=self._property_service,
            )
        )
        commands.append(
            ChangeNodePropertyCommand(
                node=node,
                path="data_file_path",
                new_value=file_path,
                event_aggregator=self._event_aggregator,
                property_service=self._property_service,
            )
        )
        
        # TODO: This should also be extracted into its own method
        if node.plot_properties:
            is_polar = node.plot_properties.coords.coord_type == ArtistType.POLAR_LINE
            x_path = "coords.theta_axis.limits" if is_polar else "coords.xaxis.limits"
            y_path = "coords.r_axis.limits" if is_polar else "coords.yaxis.limits"

            commands.append(
                ChangeNodePropertyCommand(
                    node=node,
                    path=x_path,
                    new_value=(None, None),
                    event_aggregator=self._event_aggregator,
                    property_service=self._property_service,
                )
            )
            commands.append(
                ChangeNodePropertyCommand(
                    node=node,
                    path=y_path,
                    new_value=(None, None),
                    event_aggregator=self._event_aggregator,
                    property_service=self._property_service,
                )
            )

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
        self._event_aggregator.publish(
            Events.INITIALIZE_PLOT_THEME_REQUESTED, node_id=node.id, plot_type=new_type
        )

    def _on_generic_property_change_request(self, node_id: str, path: str, value: Any):
        node = self._get_node_by_id(node_id)
        if not node:
            return
        self.command_manager.execute_command(
            ChangeNodePropertyCommand(
                node=node,
                path=path,
                new_value=value,
                event_aggregator=self._event_aggregator,
                property_service=self._property_service,
            )
        )

    def _on_node_visibility_request(self, node_id: str, visible: bool):
        node = self._get_node_by_id(node_id)
        if node and node.visible != visible:
            cmd = ChangeNodePropertyCommand(
                node=node,
                path="visible",
                new_value=visible,
                event_aggregator=self._event_aggregator,
                property_service=self._property_service,
            )
            self.command_manager.execute_command(cmd)

    def _on_node_locked_request(self, node_id: str, locked: bool):
        node = self._get_node_by_id(node_id)
        if node and node.locked != locked:
            cmd = ChangeNodePropertyCommand(
                node=node,
                path="locked",
                new_value=locked,
                event_aggregator=self._event_aggregator,
                property_service=self._property_service,
            )
            self.command_manager.execute_command(cmd)

    def _on_rename_node_request(self, node_id: str, new_name: str):
        node = self._get_node_by_id(node_id)
        if node and node.name != new_name:
            cmd = ChangeNodePropertyCommand(
                node=node,
                path="name",
                new_value=new_name,
                event_aggregator=self._event_aggregator,
                property_service=self._property_service,
            )
            self.command_manager.execute_command(cmd)

    def _on_template_loaded(self, root_node: SceneNode):
        for node in root_node.all_descendants(of_type=PlotNode):
            if isinstance(node.plot_properties, dict):
                overrides = node.plot_properties
                self._event_aggregator.publish(
                    Events.HYDRATE_PLOT_PROPERTIES_REQUESTED,
                    node_id=node.id,
                    overrides=overrides,
                )

    def reorder_nodes(self, parent_id: str, node_id: str, new_index: int):
        self.logger.warning("NodeController: reorder_nodes not fully implemented yet.")

    def group_nodes(self, node_ids: list[str]):
        self.logger.warning("NodeController: group_nodes not fully implemented yet.")

    def ungroup_node(self, group_id: str):
        self.logger.warning("NodeController: ungroup_node not fully implemented yet.")
