from typing import List

from src.models.application_model import ApplicationModel
from src.models.nodes.group_node import GroupNode  # New Import
from src.models.nodes.scene_node import SceneNode
from src.services.commands.base_command import BaseCommand


class GroupNodesCommand(BaseCommand):
    """
    Command to group a list of SceneNodes under a new GroupNode.
    """

    def __init__(
        self, model: ApplicationModel, node_ids: List[str], group_name: str = "Group"
    ):
        super().__init__(model)
        self.node_ids = node_ids
        self.group_name = group_name
        self.group_id: str | None = None  # Will be set during execute
        self.original_parents: dict[str, str] = {}  # Store original parent IDs
        self.description = f"Group nodes: {', '.join(node_ids)}"

    def execute(self):
        nodes_to_group: List[SceneNode] = []
        for node_id in self.node_ids:
            node = self.model.scene_root.find_node_by_id(node_id)
            if node:
                nodes_to_group.append(node)
                if node.parent:
                    self.original_parents[node_id] = node.parent.id
                else:
                    self.original_parents[node_id] = (
                        self.model.scene_root.id
                    )  # Root parent

        if len(nodes_to_group) < 2:
            self.logger.warning(
                "GroupNodesCommand: Grouping requires at least two nodes."
            )
            return

        # Create a new GroupNode
        new_group = GroupNode(name=self.group_name)
        self.group_id = new_group.id

        # Add the new group to the parent of the first node (assuming all share a common parent)
        # Or, if multiple parents, add to the scene_root
        common_parent_id = (
            self.original_parents[self.node_ids[0]]
            if self.node_ids
            else self.model.scene_root.id
        )
        common_parent = self.model.scene_root.find_node_by_id(common_parent_id)

        if common_parent:
            common_parent.add_child(new_group)
            self.logger.debug(
                f"GroupNodesCommand: Added new group {new_group.id} to parent {common_parent.id}."
            )
        else:
            self.model.scene_root.add_child(new_group)
            self.logger.debug(
                f"GroupNodesCommand: Added new group {new_group.id} to scene root."
            )

        # Move nodes into the new group
        for node in nodes_to_group:
            if node.parent:  # Remove from old parent
                node.parent.remove_child(node)
            new_group.add_child(node)
            self.logger.debug(
                f"GroupNodesCommand: Moved node {node.id} into group {new_group.id}."
            )

        self.model.modelChanged.emit()

    def undo(self):
        if not self.group_id:
            self.logger.warning(
                "GroupNodesCommand: Cannot undo, group_id not set (execute failed or not run)."
            )
            return

        group_node = self.model.scene_root.find_node_by_id(self.group_id)
        if not group_node:
            self.logger.warning(
                f"GroupNodesCommand: Cannot undo, group node {self.group_id} not found."
            )
            return

        # Move nodes back to original parents
        for node_id in self.node_ids:
            node = self.model.scene_root.find_node_by_id(node_id)
            original_parent_id = self.original_parents.get(node_id)
            original_parent = (
                self.model.scene_root.find_node_by_id(original_parent_id)
                if original_parent_id
                else self.model.scene_root
            )

            if node and original_parent:
                group_node.remove_child(node)  # Remove from group
                original_parent.add_child(node)  # Add to original parent
                self.logger.debug(
                    f"GroupNodesCommand: Moved node {node_id} back to parent {original_parent.id}."
                )
            else:
                self.logger.warning(
                    f"GroupNodesCommand: Failed to undo move for node {node_id} to parent {original_parent_id}."
                )

        # Remove the group node itself
        if group_node.parent:
            group_node.parent.remove_child(group_node)
            self.logger.debug(
                f"GroupNodesCommand: Removed group node {group_node.id} from its parent."
            )
        else:
            self.model.scene_root.remove_child(group_node)
            self.logger.debug(
                f"GroupNodesCommand: Removed group node {group_node.id} from scene root."
            )

        self.model.modelChanged.emit()
