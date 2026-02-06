from typing import Any

from src.models.nodes import SceneNode
from src.models.nodes.plot_properties import BasePlotProperties
from src.models.nodes.plot_types import PlotType

from .base_command import BaseCommand


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
        property_dict_name: str | None = None,
    ):
        description = f"Change property '{property_name}' of node '{node.name}' to '{new_value}'"
        super().__init__(description)
        self.node = node
        self.property_name = property_name
        self.new_value = new_value
        self.property_dict_name = property_dict_name
        self.old_value = None  # Will be stored on execute #TODO: What is this for?

        # Special handling for plot_type changes, which alter the type of plot_properties
        self._is_plot_type_change = (
            self.property_name == "plot_type"
            and self.property_dict_name == "plot_properties"
        )

    def execute(self):
        """Applies the property change."""
        if self._is_plot_type_change:
            assert isinstance(self.new_value, PlotType)
            self.old_value = self.node.plot_properties
            self.node.plot_properties = (
                BasePlotProperties.create_properties_from_plot_type(
                    new_plot_type=self.new_value,
                    current_properties=self.old_value,
                )
            )
        else:
            target_object = (
                getattr(self.node, self.property_dict_name)
                if self.property_dict_name
                else self.node
            )
            self.old_value = getattr(target_object, self.property_name)
            setattr(target_object, self.property_name, self.new_value)

        # For now, we rely on the CommandManager to signal the model changed.
        pass

    def undo(self):
        """Reverts the property change."""
        if self._is_plot_type_change:
            self.node.plot_properties = self.old_value
        else:
            target_object = (
                getattr(self.node, self.property_dict_name)
                if self.property_dict_name
                else self.node
            )
            setattr(target_object, self.property_name, self.old_value)

        # For now, we rely on the CommandManager to signal the model changed.
        pass
