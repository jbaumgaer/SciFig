from typing import Any, Optional
import logging

from src.models.nodes.scene_node import SceneNode
from src.models.nodes.plot_node import PlotNode
from src.models.plots.plot_properties import BasePlotProperties, AxesLimits, PlotMapping
from src.models.plots.plot_types import PlotType
from src.services.commands.base_command import BaseCommand
from src.shared.events import Events
from src.services.event_aggregator import EventAggregator


class ChangePropertyCommand(BaseCommand):
    """
    A command to change a single property of a SceneNode.
    It can handle both direct attributes and nested dictionary properties.
    """

    def __init__(
        self,
        node: SceneNode,
        property_name: str,
        new_value: Any,
        event_aggregator: EventAggregator,
        property_dict_name: Optional[str] = None,
    ):
        description = (
            f"Change property '{property_name}' of node '{node.name}' to '{new_value}'"
        )
        super().__init__(description, event_aggregator)
        self.node = node
        self.property_name = property_name
        self.new_value = new_value
        self.property_dict_name = property_dict_name
        self.old_value: Optional[Any] = None

        self._is_plot_type_change = (
            self.property_name == "plot_type"
            and self.property_dict_name == "plot_properties"
        )

    def execute(self):
        """Applies the property change and publishes a specific event."""
        if self._is_plot_type_change:
            assert isinstance(self.new_value, PlotType)
            self.old_value = self.node.plot_properties
            self.node.plot_properties = (
                BasePlotProperties.create_properties_from_plot_type(
                    new_plot_type=self.new_value,
                    current_properties=self.old_value,
                )
            )
            # Need to store the old_plot_type as well to revert
            self.old_plot_type = self.old_value.plot_type if self.old_value else None
        else:
            target_object = self._get_target_object()
            self.old_value = getattr(target_object, self.property_name)
            setattr(target_object, self.property_name, self.new_value)

        self._publish_specific_event(self.node, self.new_value)

    def undo(self):
        """Reverts the property change and publishes a specific event."""
        if self._is_plot_type_change:
            # Revert plot_properties back to the old object
            self.node.plot_properties = self.old_value
            # Ensure the plot_type is also correctly set back
            if self.node.plot_properties and self.old_plot_type:
                self.node.plot_properties.plot_type = self.old_plot_type
        else:
            target_object = self._get_target_object()
            setattr(target_object, self.property_name, self.old_value)

        self._publish_specific_event(self.node, self.old_value)
        
    def _get_target_object(self):
        """Helper to get the object on which the property will be set."""
        return (
            getattr(self.node, self.property_dict_name)
            if self.property_dict_name
            else self.node
        )

    def _publish_specific_event(self, node: SceneNode, current_value: Any):
        """Publishes a specific event based on the property that was changed."""
        event_aggregator = self._event_aggregator
        if not event_aggregator:
            self.logger.warning("EventAggregator not available in ChangePropertyCommand.")
            return

        if self.property_name == "name":
            event_aggregator.publish(Events.NODE_RENAMED, node_id=node.id, new_name=current_value)
        elif self.property_name == "visible":
            event_aggregator.publish(Events.NODE_VISIBILITY_CHANGED, node_id=node.id, is_visible=current_value)
        elif self.property_name == "locked":
            event_aggregator.publish(Events.NODE_LOCKED_CHANGED, node_id=node.id, is_locked=current_value)
        elif self.property_name == "axes_limits":
            if isinstance(current_value, AxesLimits):
                event_aggregator.publish(
                    Events.PLOT_AXIS_LIMITS_CHANGED,
                    node_id=node.id,
                    xlim=current_value.xlim,
                    ylim=current_value.ylim,
                )
        elif self.property_name == "plot_mapping":
            if isinstance(current_value, PlotMapping):
                event_aggregator.publish(
                    Events.PLOT_MAPPING_CHANGED,
                    node_id=node.id,
                    x_column=current_value.x,
                    y_columns=current_value.y,
                )
        elif self.property_name == "plot_type":
            if isinstance(current_value, PlotType):
                event_aggregator.publish(Events.PLOT_TYPE_CHANGED, node_id=node.id, new_plot_type=current_value.value)
        elif self.property_name == "data":
            # Data loaded event, doesn't need to pass the full dataframe
            event_aggregator.publish(Events.NODE_DATA_LOADED, node_id=node.id)
            if isinstance(node, PlotNode):
                 event_aggregator.publish(Events.NODE_DATA_FILE_PATH_UPDATED, node_id=node.id, new_path=node.data_file_path)
        elif self.property_name == "data_file_path":
             event_aggregator.publish(Events.NODE_DATA_FILE_PATH_UPDATED, node_id=node.id, new_path=current_value)
        elif self.property_name == "title":
            event_aggregator.publish(Events.PLOT_TITLE_CHANGED, node_id=node.id, new_title=current_value)
        elif self.property_name == "xlabel":
            event_aggregator.publish(Events.PLOT_XLABEL_CHANGED, node_id=node.id, new_xlabel=current_value)
        elif self.property_name == "ylabel":
            event_aggregator.publish(Events.PLOT_YLABEL_CHANGED, node_id=node.id, new_ylabel=current_value)
        elif self.property_name == "marker_size":
            event_aggregator.publish(Events.PLOT_MARKER_SIZE_CHANGED, node_id=node.id, new_size=current_value)
        else:
            self.logger.debug(
                f"No specific event for property '{self.property_name}' on node '{node.id}'. "
                f"Consider adding one for granular updates."
            )
