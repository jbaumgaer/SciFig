from typing import Any

from src.models.nodes import SceneNode

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
        super().__init__()
        self.node = node
        self.property_name = property_name
        self.new_value = new_value
        self.property_dict_name = property_dict_name
        self.old_value = None  # Will be stored on execute

    def execute(self):
        """Applies the property change."""
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
        target_object = (
            getattr(self.node, self.property_dict_name)
            if self.property_dict_name
            else self.node
        )
        setattr(target_object, self.property_name, self.old_value)

        # For now, we rely on the CommandManager to signal the model changed.
        pass
