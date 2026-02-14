import logging
from typing import Optional

from PySide6.QtCore import Qt  # Qt for flags, QMimeData for drag/drop
from PySide6.QtGui import (
    QIcon,
)  # QIcon for icons, QMouseEvent for drag, QDrag for drag/drop
from PySide6.QtWidgets import (
    QHBoxLayout,
    QMessageBox,  # For user feedback
    QToolButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from src.controllers.node_controller import NodeController
from src.models.application_model import ApplicationModel
from src.models.nodes.group_node import GroupNode
from src.models.nodes.scene_node import SceneNode
from src.shared.constants import IconPath


class LayersTab(QWidget):
    # Column indices
    COL_NAME = 0
    COL_TYPE = 1

    # Drag and Drop MIME type
    _NODE_MIME_TYPE = "application/x-scifig-node-id"

    def __init__(
        self,
        model: ApplicationModel,
        node_controller: NodeController,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        # TODO: Check if I even pass a parent
        self.model = model
        self.node_controller = node_controller
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info("LayersTab initialized.")

        self._main_layout = QVBoxLayout(self)
        self._main_layout.setContentsMargins(5, 5, 5, 5)

        # --- Toolbar for Layer Actions (Group/Ungroup) ---
        self._toolbar_layout = QHBoxLayout()
        self._group_button = QToolButton(self)
        self._group_button.setText("Group")
        self._group_button.setIcon(QIcon(IconPath.get_path("toolbar.group")))
        self._group_button.setToolTip("Group selected nodes")
        self._group_button.clicked.connect(self._group_selected_nodes)
        self._toolbar_layout.addWidget(self._group_button)

        self._ungroup_button = QToolButton(self)
        self._ungroup_button.setText("Ungroup")
        self._ungroup_button.setIcon(QIcon(IconPath.get_path("toolbar.ungroup")))
        self._ungroup_button.setToolTip("Ungroup selected GroupNode")
        self._ungroup_button.clicked.connect(self._ungroup_selected_node)
        self._toolbar_layout.addWidget(self._ungroup_button)
        self._toolbar_layout.addStretch()  # Push buttons to left

        self._main_layout.addLayout(self._toolbar_layout)

        # --- QTreeWidget for Node Hierarchy ---
        self._tree_widget = QTreeWidget(self)
        self._tree_widget.setHeaderLabels(["Name", "Type"])  # Headers for columns
        self._tree_widget.setColumnCount(2)
        self._tree_widget.setDragEnabled(True)
        self._tree_widget.setAcceptDrops(True)
        self._tree_widget.setDropIndicatorShown(True)
        self._tree_widget.setDragDropMode(
            QTreeWidget.InternalMove
        )  # Enable internal reordering
        self._tree_widget.setDefaultDropAction(Qt.MoveAction)

        # Connect signals
        self._tree_widget.itemChanged.connect(self._handle_item_changed)
        self._tree_widget.itemDoubleClicked.connect(self._handle_item_double_clicked)
        self._tree_widget.itemSelectionChanged.connect(
            self._update_toolbar_buttons
        )  # To enable/disable group/ungroup
        # Custom drag/drop events
        self._tree_widget.setContextMenuPolicy(
            Qt.CustomContextMenu
        )  # For custom context menu if needed later
        # self._tree_widget.customContextMenuRequested.connect(self._show_context_menu) # Connect to context menu handler

        self._main_layout.addWidget(self._tree_widget)
        self._main_layout.addStretch()

        self._drag_start_position = None  # For drag and drop tracking

        # Connect model signals
        self.model.modelChanged.connect(self._update_content)
        self.model.selectionChanged.connect(self._update_selection_in_tree)

        self._update_content()  # Initial population
        self._update_toolbar_buttons()  # Initial state of buttons

    def _update_content(self):
        """
        Clears and rebuilds the QTreeWidget based on the current ApplicationModel.
        """
        self.logger.debug("LayersTab: Updating content of QTreeWidget.")
        self._tree_widget.blockSignals(True)  # Block signals during rebuild
        self._tree_widget.clear()

        self._add_node_to_tree(
            self.model.scene_root, self._tree_widget.invisibleRootItem()
        )

        self._tree_widget.expandAll()  # Expand all nodes by default
        self._update_selection_in_tree()  # Ensure tree selection matches model
        self._tree_widget.blockSignals(False)  # Re-enable signals
        self.logger.debug("LayersTab: QTreeWidget content updated.")

    def _add_node_to_tree(self, node: SceneNode, parent_item: QTreeWidgetItem):
        """
        Recursively adds a SceneNode and its children to the QTreeWidget.
        """
        if node == self.model.scene_root:  # Don't add the invisible root node itself
            for child in node.children:
                self._add_node_to_tree(child, parent_item)
            return

        item = QTreeWidgetItem(parent_item)
        item.setText(self.COL_NAME, node.name)
        item.setText(self.COL_TYPE, type(node).__name__)
        item.setData(
            self.COL_NAME, Qt.UserRole, node.id
        )  # Store node ID in UserRole for easy retrieval
        item.setFlags(
            item.flags()
            | Qt.ItemIsEditable
            | Qt.ItemIsSelectable
            | Qt.ItemIsDragEnabled
            | Qt.ItemIsDropEnabled
        )

        # Visibility Checkbox/Icon
        item.setCheckState(
            self.COL_NAME, Qt.Checked if node.visible else Qt.Unchecked
        )  # Checkbox in first column
        # item.setIcon(0, QIcon(IconPath.get_path("visible_icon" if node.visible else "hidden_icon"))) # Alternative: icon

        # Lock Icon/State
        if node.locked:
            item.setIcon(
                self.COL_TYPE, QIcon(IconPath.get_path("lock_icon"))
            )  # Lock icon in second column
            item.setFlags(
                item.flags() & ~Qt.ItemIsEditable & ~Qt.ItemIsDragEnabled
            )  # Disable editing/dragging if locked

        for child in node.children:
            self._add_node_to_tree(child, item)

    def _handle_item_changed(self, item: QTreeWidgetItem, column: int):
        """
        Handles changes to a QTreeWidgetItem (e.g., checkbox state, text edit).
        """
        node_id = item.data(self.COL_NAME, Qt.UserRole)
        if not node_id:
            return

        node = self.model.scene_root.find_node_by_id(node_id)
        if not node:
            return

        if column == self.COL_NAME:  # Name or Visibility
            if item.checkState(self.COL_NAME) != (Qt.Checked if node.visible else Qt.Unchecked):
                # Visibility changed
                new_visibility = item.checkState(self.COL_NAME) == Qt.Checked
                self.node_controller.set_node_visibility(node_id, new_visibility)
            elif item.text(self.COL_NAME) != node.name:
                # Name changed
                new_name = item.text(self.COL_NAME)
                self.node_controller.rename_node(node_id, new_name)
        # TODO: Handle lock icon/state change in column 1 if implemented as checkbox

    def _handle_item_double_clicked(self, item: QTreeWidgetItem, column: int):
        """
        Handles double-clicking an item in the tree.
        Could be used for in-place renaming or opening properties.
        """
        # For now, allow in-place renaming on double-click if not locked
        node_id = item.data(self.COL_NAME, Qt.UserRole)
        node = self.model.scene_root.find_node_by_id(node_id)
        if node and not node.locked:
            self._tree_widget.editItem(item, self.COL_NAME)  # Start editing the name column

    def _update_selection_in_tree(self):
        """Ensures the selection in the QTreeWidget matches the model's selection."""
        self.logger.debug("LayersTab: Updating tree selection to match model.")
        self._tree_widget.blockSignals(
            True
        )  # Block signals to avoid triggering itemChanged
        self._tree_widget.clearSelection()

        for selected_node in self.model.selection:
            items = self._tree_widget.findItems(
                selected_node.id, Qt.UserRole | Qt.MatchRecursive, column=self.COL_NAME
            )
            for item in items:
                if (
                    item.data(self.COL_NAME, Qt.UserRole) == selected_node.id
                ):  # Ensure correct item by ID
                    item.setSelected(True)
                    self._tree_widget.scrollToItem(item)
                    break
        self._tree_widget.blockSignals(False)

    def _group_selected_nodes(self):
        """Triggers grouping action for currently selected nodes."""
        selected_node_ids = [
            item.data(self.COL_NAME, Qt.UserRole)
            for item in self._tree_widget.selectedItems()
            if item.data(self.COL_NAME, Qt.UserRole)
        ]
        if len(selected_node_ids) > 1:
            self.node_controller.group_nodes(selected_node_ids)
        else:
            QMessageBox.warning(
                self, "Grouping Error", "Select at least two nodes to group."
            )

    def _ungroup_selected_node(self):
        """Triggers ungrouping action for a selected GroupNode."""
        selected_items = self._tree_widget.selectedItems()
        if len(selected_items) == 1:
            node_id = selected_items[0].data(self.COL_NAME, Qt.UserRole)
            node = self.model.scene_root.find_node_by_id(node_id)
            if isinstance(node, GroupNode):
                self.node_controller.ungroup_node(node_id)
            else:
                QMessageBox.warning(
                    self, "Ungrouping Error", "Select a GroupNode to ungroup."
                )
        else:
            QMessageBox.warning(
                self, "Ungrouping Error", "Select exactly one GroupNode to ungroup."
            )

    def _update_toolbar_buttons(self):
        """Updates the enabled state of toolbar buttons based on selection."""
        selected_items = self._tree_widget.selectedItems()
        self._group_button.setEnabled(len(selected_items) > 1)

        ungroup_enabled = False
        if len(selected_items) == 1:
            node_id = selected_items[0].data(self.COL_NAME, Qt.UserRole)
            node = self.model.scene_root.find_node_by_id(node_id)
            if isinstance(node, GroupNode):
                ungroup_enabled = True
        self._ungroup_button.setEnabled(ungroup_enabled)
