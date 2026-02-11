from src.models.application_model import ApplicationModel
from src.services.commands.base_command import BaseCommand


class ChangeChildrenOrderCommand(BaseCommand):
    """
    Command to change the order of a child node within its parent's children list.
    """

    def __init__(
        self,
        model: ApplicationModel,
        parent_id: str,
        node_id: str,
        old_index: int,
        new_index: int,
    ):
        super().__init__(model)
        self.parent_id = parent_id
        self.node_id = node_id
        self.old_index = old_index
        self.new_index = new_index
        self.description = f"Reorder node {node_id} in parent {parent_id}"

    def execute(self):
        parent_node = self.model.scene_root.find_node_by_id(self.parent_id)
        node_to_move = self.model.scene_root.find_node_by_id(self.node_id)

        if parent_node and node_to_move and node_to_move.parent == parent_node:
            children = parent_node.children
            children.pop(self.old_index)
            children.insert(self.new_index, node_to_move)
            self.model.modelChanged.emit()
        else:
            self.logger.warning(
                f"ChangeChildrenOrderCommand: Failed to execute. Parent ({self.parent_id}) or child ({self.node_id}) not found or child not belonging to parent."
            )

    def undo(self):
        parent_node = self.model.scene_root.find_node_by_id(self.parent_id)
        node_to_move = self.model.scene_root.find_node_by_id(self.node_id)

        if parent_node and node_to_move and node_to_move.parent == parent_node:
            children = parent_node.children
            children.pop(self.new_index)
            children.insert(self.old_index, node_to_move)
            self.model.modelChanged.emit()
        else:
            self.logger.warning(
                f"ChangeChildrenOrderCommand: Failed to undo. Parent ({self.parent_id}) or child ({self.node_id}) not found or child not belonging to parent."
            )
