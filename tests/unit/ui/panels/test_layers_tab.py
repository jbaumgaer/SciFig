# tests/unit/ui/panels/test_layers_tab.py
from unittest.mock import MagicMock

import pytest
from PySide6.QtCore import QItemSelectionModel, Qt
from PySide6.QtWidgets import QApplication, QTreeWidget, QTreeWidgetItem

from src.models.nodes.group_node import GroupNode
from src.models.nodes.plot_node import PlotNode
from src.shared.constants import IconPath
from src.ui.panels.layers_tab import LayersTab


@pytest.fixture
def populated_model(mock_application_model):
    """
    Fixture to populate the application model with a standard node hierarchy.
    """
    root = mock_application_model.scene_root
    root.id = "root"
    root.name = "Scene"
    root.children = []

    # Create and configure mock nodes
    plot1 = MagicMock(spec=PlotNode)
    plot1.id = "p1"
    plot1.name = "Plot 1"
    plot1.visible = True
    plot1.locked = False
    plot1.parent = root
    plot1.children = []

    group1 = MagicMock(spec=GroupNode)
    group1.id = "g1"
    group1.name = "Group 1"
    group1.visible = True
    group1.locked = False
    group1.parent = root
    group1.children = []

    plot2 = MagicMock(spec=PlotNode)
    plot2.id = "p2"
    plot2.name = "Plot 2"
    plot2.visible = False
    plot2.locked = True
    plot2.parent = root
    plot2.children = []

    plot3_in_g1 = MagicMock(spec=PlotNode)
    plot3_in_g1.id = "p3"
    plot3_in_g1.name = "Plot 3 in G1"
    plot3_in_g1.visible = True
    plot3_in_g1.locked = False
    plot3_in_g1.parent = group1
    plot3_in_g1.children = []

    # Establish hierarchy
    group1.children = [plot3_in_g1]
    root.children = [plot1, group1, plot2]

    # Mock the model's find_node_by_id to traverse the mock hierarchy
    all_nodes = {node.id: node for node in [root, plot1, group1, plot2, plot3_in_g1]}
    mock_application_model.scene_root.find_node_by_id.side_effect = lambda nid: all_nodes.get(nid)

    return mock_application_model, plot1, group1, plot2, plot3_in_g1


@pytest.fixture
def layers_tab(qtbot, populated_model, mock_node_controller, mock_config_service):
    """Fixture to create and show a LayersTab instance with a populated model."""
    # QApplication is required for widgets
    QApplication.instance() or QApplication([])

    model, _, _, _, _ = populated_model

    # Configure mock_config_service to return paths for icons used in LayersTab
    original_side_effect = mock_config_service.get.side_effect
    def new_side_effect(key, default=None):
        if key == "paths.toolbar.group":
            return "dummy_group_icon.svg"
        if key == "paths.toolbar.ungroup":
            return "dummy_ungroup_icon.svg"
        if key == "paths.lock_icon":
            return "dummy_lock_icon.svg"
        return original_side_effect(key, default)
    mock_config_service.get.side_effect = new_side_effect

    # Set the config service for IconPath
    IconPath.set_config_service(mock_config_service)

    tab = LayersTab(
        model=model,
        node_controller=mock_node_controller,
        config_service=mock_config_service
    )
    qtbot.addWidget(tab)
    tab.show() # Ensure widget is visible for interactions

    # Wait for the initial _update_content call to complete
    qtbot.waitUntil(lambda: tab._tree_widget.topLevelItemCount() > 0)

    return tab, model, mock_node_controller


# Helper function to find a tree item by its node ID
def find_item_by_id(tree: QTreeWidget, node_id: str) -> QTreeWidgetItem | None:
    """Recursively finds a QTreeWidgetItem by the node ID stored in its data."""
    for i in range(tree.topLevelItemCount()):
        item = tree.topLevelItem(i)
        if item.data(0, Qt.UserRole) == node_id:
            return item
        # Check children recursively
        found = _find_in_children(item, node_id)
        if found:
            return found
    return None

def _find_in_children(parent_item: QTreeWidgetItem, node_id: str) -> QTreeWidgetItem | None:
    """Helper for recursive search."""
    for i in range(parent_item.childCount()):
        child = parent_item.child(i)
        if child.data(0, Qt.UserRole) == node_id:
            return child
        found = _find_in_children(child, node_id)
        if found:
            return found
    return None


class TestLayersTab:
    """Refactored test suite for the LayersTab widget."""

    def test_initialization_and_content_display(self, layers_tab, populated_model):
        """Verify the tree is built correctly from the model hierarchy."""
        # Arrange
        tab, _, _ = layers_tab
        _, plot1, group1, plot2, plot3_in_g1 = populated_model
        tree = tab._tree_widget

        # Act & Assert
        assert tree.topLevelItemCount() == 3, "Should have 3 top-level items"

        # Verify Plot 1
        item_p1 = find_item_by_id(tree, plot1.id)
        assert item_p1 is not None
        assert item_p1.text(LayersTab.COL_NAME) == plot1.name
        assert item_p1.checkState(LayersTab.COL_NAME) == Qt.Checked
        assert item_p1.icon(LayersTab.COL_TYPE) is not None

        # Verify Group 1 and its child
        item_g1 = find_item_by_id(tree, group1.id)
        assert item_g1 is not None
        assert item_g1.text(LayersTab.COL_NAME) == group1.name
        assert item_g1.childCount() == 1
        item_p3 = item_g1.child(0)
        assert item_p3.data(0, Qt.UserRole) == plot3_in_g1.id
        assert item_p3.text(LayersTab.COL_NAME) == plot3_in_g1.name

        # Verify Plot 2
        item_p2 = find_item_by_id(tree, plot2.id)
        assert item_p2 is not None
        assert item_p2.text(LayersTab.COL_NAME) == plot2.name
        assert item_p2.checkState(LayersTab.COL_NAME) == Qt.Unchecked
        assert item_p2.icon(LayersTab.COL_TYPE) is not None

    def test_visibility_toggle_calls_controller(self, layers_tab, populated_model, qtbot):
        """Verify toggling visibility checkbox calls the node controller."""
        # Arrange
        tab, _, node_controller = layers_tab
        _, plot1, _, _, _ = populated_model
        item_p1 = find_item_by_id(tab._tree_widget, plot1.id)

        # Act: Uncheck the visibility box
        with qtbot.wait_signal(tab._tree_widget.itemChanged) as blocker:
            item_p1.setCheckState(LayersTab.COL_NAME, Qt.Unchecked)

        # Assert
        node_controller.set_node_visibility.assert_called_once_with(plot1.id, False)

        # Arrange again for the other direction
        node_controller.set_node_visibility.reset_mock()

        # Act: Check the box
        with qtbot.wait_signal(tab._tree_widget.itemChanged) as blocker:
            item_p1.setCheckState(LayersTab.COL_NAME, Qt.Checked)

        # Assert
        node_controller.set_node_visibility.assert_called_once_with(plot1.id, True)

    def test_lock_toggle_calls_controller(self, layers_tab, populated_model, qtbot):
        """Verify toggling lock checkbox calls the node controller."""
        # Arrange
        tab, _, node_controller = layers_tab
        _, plot1, _, _, _ = populated_model
        item_p1 = find_item_by_id(tab._tree_widget, plot1.id)

        # Act: Check the lock box
        with qtbot.wait_signal(tab._tree_widget.itemChanged) as blocker:
            item_p1.setCheckState(LayersTab.COL_TYPE, Qt.Checked)

        # Assert
        node_controller.set_node_locked.assert_called_once_with(plot1.id, True)

        # Arrange again
        node_controller.set_node_locked.reset_mock()

        # Act: Uncheck the box
        with qtbot.wait_signal(tab._tree_widget.itemChanged) as blocker:
            item_p1.setCheckState(LayersTab.COL_TYPE, Qt.Unchecked)

        # Assert
        node_controller.set_node_locked.assert_called_once_with(plot1.id, False)

    def test_rename_node_calls_controller(self, layers_tab, populated_model, qtbot):
        """Verify that in-place editing of an item's name calls the node controller."""
        # Arrange
        tab, _, node_controller = layers_tab
        _, plot1, _, _, _ = populated_model
        item_p1 = find_item_by_id(tab._tree_widget, plot1.id)
        new_name = "Renamed Plot"

        # Act
        with qtbot.wait_signal(tab._tree_widget.itemChanged) as blocker:
            item_p1.setText(LayersTab.COL_NAME, new_name)

        # Assert
        node_controller.rename_node.assert_called_once_with(plot1.id, new_name)

    def test_model_changed_signal_rebuilds_tree(self, layers_tab, qtbot):
        """Verify the tree rebuilds when the model's modelChanged signal is emitted."""
        # Arrange
        tab, model, _ = layers_tab
        tree = tab._tree_widget
        assert tree.topLevelItemCount() == 3

        # Modify the model hierarchy
        new_plot = MagicMock(spec=PlotNode)
        new_plot.id = "p4"
        new_plot.name = "New Plot"
        new_plot.visible = True
        new_plot.locked = False
        new_plot.parent = model.scene_root
        new_plot.children = []
        model.scene_root.children.append(new_plot)

        all_nodes = {node.id: node for node in model.scene_root.children}
        all_nodes["root"] = model.scene_root
        model.scene_root.find_node_by_id.side_effect = lambda nid: all_nodes.get(nid)

        # Act
        with qtbot.wait_signal(model.modelChanged):
            model.modelChanged.emit()

        # Assert
        assert tree.topLevelItemCount() == 4, "Tree should have one more item"
        item_p4 = find_item_by_id(tree, new_plot.id)
        assert item_p4 is not None
        assert item_p4.text(LayersTab.COL_NAME) == new_plot.name

    def test_selection_sync_from_model_to_tree(self, layers_tab, populated_model, qtbot):
        """Verify that a selection change in the model updates the tree selection."""
        # Arrange
        tab, model, _ = layers_tab
        _, plot1, _, plot2, _ = populated_model

        item_p1 = find_item_by_id(tab._tree_widget, plot1.id)
        item_p2 = find_item_by_id(tab._tree_widget, plot2.id)

        # Act: Simulate model selection changing
        model.selection = [plot1, plot2]
        with qtbot.wait_signal(model.selectionChanged):
             model.selectionChanged.emit([plot1.id, plot2.id])

        # Assert
        assert item_p1.isSelected(), "Plot 1 item should be selected"
        assert item_p2.isSelected(), "Plot 2 item should be selected"
        assert len(tab._tree_widget.selectedItems()) == 2

    def test_selection_sync_from_tree_to_model(self, layers_tab, populated_model, qtbot):
        """Verify that a selection change in the tree updates the model selection."""
        # Arrange
        tab, _, node_controller = layers_tab
        _, plot1, _, plot2, _ = populated_model

        item_p1 = find_item_by_id(tab._tree_widget, plot1.id)
        item_p2 = find_item_by_id(tab._tree_widget, plot2.id)

        # Act: Simulate user selecting items in the tree
        selection_model = tab._tree_widget.selectionModel()
        selection_model.select(tab._tree_widget.indexFromItem(item_p1), QItemSelectionModel.Select)
        selection_model.select(tab._tree_widget.indexFromItem(item_p2), QItemSelectionModel.Select)

        # Assert
        node_controller.set_selection.assert_called_once()
        # The call should contain both IDs, but order is not guaranteed.
        called_args, _ = node_controller.set_selection.call_args
        assert set(called_args[0]) == {plot1.id, plot2.id}
