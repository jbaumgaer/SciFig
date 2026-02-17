from typing import Optional
from src.models.application_model import ApplicationModel
from src.models.nodes.group_node import GroupNode  # New Import
from src.services.commands.base_command import BaseCommand
from src.services.event_aggregator import EventAggregator
from src.shared.events import Events


class UngroupNodesCommand(BaseCommand):
    """
    Command to ungroup a specific GroupNode, moving its children to its parent
    and removing the GroupNode itself.
    """

    def __init__(self, model: ApplicationModel, event_aggregator: EventAggregator, group_id: str):
        super().__init__(model, event_aggregator)
        self.group_id = group_id
        self.ungrouped_children_ids: list[str] = []
        self.original_parent_id: Optional[str] = None
        self.original_group_index: Optional[int] = (
            None  # To restore group's original position
        )
        self.description = f"Ungroup node {group_id}"

    def execute(self):
        group_node = self.model.scene_root.find_node_by_id(self.group_id)
        if not (group_node and isinstance(group_node, GroupNode)):
            self.logger.warning(
                f"UngroupNodesCommand: Cannot execute, node {self.group_id} is not a GroupNode or not found."
            )
            return

        original_parent = (
            group_node.parent if group_node.parent else self.model.scene_root
        )
        self.original_parent_id = original_parent.id

        # Store original index of the group node within its parent
        if group_node in original_parent.children:
            self.original_group_index = original_parent.children.index(group_node)

        # Collect children before modifying the hierarchy
        children_to_ungroup = list(group_node.children)  # Make a copy
        self.ungrouped_children_ids = [child.id for child in children_to_ungroup]

        # Remove group from parent
        original_parent.remove_child(group_node)

        # Move children to original parent
        for child in children_to_ungroup:
            group_node.remove_child(
                child
            )  # Remove from group (changes child's parent to None)
            original_parent.add_child(child)  # Add to original parent

        self._event_aggregator.publish(Events.SCENE_GRAPH_CHANGED)

    def undo(self):
        group_node = GroupNode(id=self.group_id)  # Recreate group node with original ID
        original_parent = (
            self.model.scene_root.find_node_by_id(self.original_parent_id)
            if self.original_parent_id
            else self.model.scene_root
        )

        if not original_parent:
            self.logger.warning(
                f"UngroupNodesCommand: Cannot undo, original parent {self.original_parent_id} not found."
            )
            return

        # Re-add group node to original parent at original position
        if self.original_group_index is not None and self.original_group_index <= len(
            original_parent.children
        ):
            original_parent.children.insert(self.original_group_index, group_node)
            group_node._parent = original_parent
        else:
            original_parent.add_child(group_node)

        # Move children back into the group
        for child_id in self.ungrouped_children_ids:
            child = self.model.scene_root.find_node_by_id(child_id)
            if child:
                original_parent.remove_child(child)  # Remove from original parent
                group_node.add_child(child)  # Add to group

        self._event_aggregator.publish(Events.SCENE_GRAPH_CHANGED)
