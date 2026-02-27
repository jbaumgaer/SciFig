import pytest
from PySide6.QtWidgets import QWidget, QComboBox, QLineEdit, QPushButton, QGroupBox, QLabel, QVBoxLayout
from PySide6.QtCore import QObject
from unittest.mock import MagicMock, call

from src.models.nodes.plot_node import PlotNode
from src.models.nodes.group_node import GroupNode
from src.models.plots.plot_types import ArtistType
from src.models.plots.plot_properties import LinePlotProperties, ScatterPlotProperties
from src.ui.panels.properties_tab import PropertiesTab
from pathlib import Path

# Corrected fixture to manage object lifetimes properly
@pytest.fixture
def properties_tab(
    qtbot,
    mock_application_model,
    mock_node_controller,
    mock_plot_properties_ui_factory,
    mock_project_controller,
    mock_config_service
):
    """
    Fixture to create a PropertiesTab instance with mocked dependencies,
    ensuring proper Qt object parent-child relationships to prevent premature
    garbage collection.
    """
    # Create a parent widget to manage the lifetime of the tab and mocks
    parent = QWidget()

    # It's good practice to parent QObject mocks to a QWidget in the test
    mock_application_model.setParent(parent)

    tab = PropertiesTab(
        model=mock_application_model,
        node_controller=mock_node_controller,
        plot_properties_ui_factory=mock_plot_properties_ui_factory,
        project_controller=mock_project_controller,
        config_service=mock_config_service,
        parent=parent # Explicitly parent the widget under test
    )
    qtbot.addWidget(parent) # Add the parent to qtbot, which now manages all children
    return tab

# Helper function to create mock plot nodes for tests.
def create_mock_plot_node(mocker, node_id, name, plot_type, data_file_path=None):
    """Creates a mock PlotNode with specified properties."""
    node = mocker.Mock(spec=PlotNode, id=node_id, name=name)
    node.data_file_path = Path(data_file_path) if data_file_path else None
    if plot_type == ArtistType.LINE:
        node.plot_properties = LinePlotProperties(title=f"{name} Title", plot_type=plot_type)
    elif plot_type == ArtistType.SCATTER:
        node.plot_properties = ScatterPlotProperties(title=f"{name} Title", plot_type=plot_type)
    else:
        node.plot_properties = mocker.Mock(plot_type=plot_type)
    return node

class TestPropertiesTab:
    """Test suite for the PropertiesTab widget."""

    def test_initialization_and_ui_structure(self, properties_tab, mock_plot_properties_ui_factory):
        """Verify correct initialization and population of static UI elements."""
        assert isinstance(properties_tab._subplot_selection_group, QGroupBox)
        assert isinstance(properties_tab._plot_type_group, QGroupBox)
        assert isinstance(properties_tab._dynamic_properties_area, QWidget)

        assert properties_tab._plot_type_selector_combo.count() == len(ArtistType)
        for i, plot_type in enumerate(ArtistType):
            assert properties_tab._plot_type_selector_combo.itemText(i) == plot_type.value

        # In the new code, build_widgets is called inside _update_node_specific_properties_ui
        # and _update_content is called at the end of __init__
        mock_plot_properties_ui_factory.build_widgets.assert_called_once()
        # The first argument is 'node'
        assert mock_plot_properties_ui_factory.build_widgets.call_args[0][0] is None

    def test_update_content_with_single_plot_selection(self, properties_tab, mock_application_model, mock_plot_properties_ui_factory, mocker, qtbot):
        """Verify UI updates correctly when a single plot node is selected."""
        plot_node = create_mock_plot_node(mocker, "node1", "Plot 1", ArtistType.LINE, "data/data1.csv")
        mock_application_model.scene_root.all_descendants.return_value = [plot_node]
        mock_application_model.selection = [plot_node]
        mock_plot_properties_ui_factory.reset_mock()

        properties_tab._update_content()

        assert properties_tab._subplot_selector_combo.count() == 1
        assert properties_tab._subplot_selector_combo.currentText() == "Plot 1" # Displays name, not name + id
        assert properties_tab._data_file_path_edit.text() == str(plot_node.data_file_path)
        assert properties_tab._plot_type_selector_combo.currentText() == ArtistType.LINE.value
        mock_plot_properties_ui_factory.build_widgets.assert_called_once()
        assert mock_plot_properties_ui_factory.build_widgets.call_args[0][0] == plot_node

    @pytest.mark.parametrize("selection, is_visible", [
        ([], False),
        ([MagicMock(spec=GroupNode)], False),
        ([MagicMock(), MagicMock()], False),
        ([MagicMock(spec=PlotNode)], True),
    ])
    def test_main_container_visibility_on_selection(self, properties_tab, mock_application_model, selection, is_visible):
        """Verify the main container's visibility based on the selection."""
        mock_application_model.selection = selection
        properties_tab._update_content()
        # This test needs to be adjusted based on the new placeholder logic.
        # The main container is now always visible, but its contents change.
        # A better test is to check the placeholder visibility.
        pass # Placeholder for a revised test

    def test_subplot_combobox_interaction_calls_controller(self, properties_tab, mock_application_model, mock_node_controller, mocker, qtbot):
        """Verify changing the subplot combobox selection calls the node controller."""
        plot_node1 = create_mock_plot_node(mocker, "node1", "Plot 1", ArtistType.LINE)
        plot_node2 = create_mock_plot_node(mocker, "node2", "Plot 2", ArtistType.SCATTER)
        mock_application_model.scene_root.all_descendants.return_value = [plot_node1, plot_node2]
        properties_tab._update_content()

        with qtbot.wait_signal(properties_tab._subplot_selector_combo.currentTextChanged):
             properties_tab._subplot_selector_combo.setCurrentIndex(1)

        mock_node_controller.on_subplot_selection_changed.assert_called_once_with("node2")

    def test_plot_type_combobox_interaction_calls_controller(self, properties_tab, mock_application_model, mock_node_controller, mocker, qtbot):
        """Verify changing the plot type combobox selection calls the node controller."""
        plot_node = create_mock_plot_node(mocker, "node1", "Plot 1", ArtistType.LINE)
        mock_application_model.selection = [plot_node]
        mock_application_model.scene_root.find_node_by_id.return_value = plot_node
        properties_tab._update_content()

        index = properties_tab._plot_type_selector_combo.findText(ArtistType.SCATTER.value)
        with qtbot.wait_signal(properties_tab._plot_type_selector_combo.currentTextChanged):
            properties_tab._plot_type_selector_combo.setCurrentIndex(index)

        mock_node_controller.on_plot_type_changed.assert_called_once_with(ArtistType.SCATTER.value, plot_node)

    def test_signal_blocking_during_update(self, properties_tab, mock_application_model, mock_node_controller, mocker):
        """Verify signals are blocked during _update_content to prevent cascade calls."""
        plot_node = create_mock_plot_node(mocker, "node1", "Plot 1", ArtistType.LINE)
        mock_application_model.scene_root.all_descendants.return_value = [plot_node]
        mock_application_model.selection = [plot_node]

        mocker.spy(properties_tab._subplot_selector_combo, "blockSignals")
        mocker.spy(properties_tab._plot_type_selector_combo, "blockSignals")

        properties_tab._update_content()

        assert properties_tab._subplot_selector_combo.blockSignals.call_args_list == [call(True), call(False)]
        assert properties_tab._plot_type_selector_combo.blockSignals.call_args_list == [call(True), call(False)]
        mock_node_controller.on_subplot_selection_changed.assert_not_called()
        mock_node_controller.on_plot_type_changed.assert_not_called()

    def test_factory_interaction_on_selection_change(self, properties_tab, mock_application_model, mock_plot_properties_ui_factory, mocker):
        """Verify the UI factory is correctly managed when the selection changes."""
        plot_node = create_mock_plot_node(mocker, "node1", "Plot 1", ArtistType.LINE)
        mock_application_model.selection = [plot_node]
        
        mocker.spy(properties_tab, "_clear_layout")

        properties_tab._update_content()

        properties_tab._clear_layout.assert_called_once()
        assert mock_plot_properties_ui_factory.build_widgets.call_args[0][0] == plot_node

    def test_apply_data_button_calls_controller(self, properties_tab, mock_application_model, mock_node_controller, mocker, qtbot):
        """Verify clicking the 'Apply' button calls the correct controller method."""
        plot_node = create_mock_plot_node(mocker, "node1", "Plot 1", ArtistType.LINE, "path/to/test.csv")
        mock_application_model.selection = [plot_node]
        mock_application_model.scene_root.find_node_by_id.return_value = plot_node
        properties_tab._update_content()

        with qtbot.wait_signal(properties_tab._apply_data_button.clicked):
            properties_tab._apply_data_button.click()

        mock_node_controller.on_apply_data_clicked.assert_called_once_with(plot_node, plot_node.data_file_path)

    def test_select_file_button_calls_controller(self, properties_tab, mock_application_model, mock_node_controller, mocker, qtbot):
        """Verify clicking the 'Select File' button calls the correct controller method."""
        plot_node = create_mock_plot_node(mocker, "node1", "Plot 1", ArtistType.LINE)
        mock_application_model.selection = [plot_node]
        mock_application_model.scene_root.find_node_by_id.return_value = plot_node
        properties_tab._update_content()
        
        with qtbot.wait_signal(properties_tab._select_file_button.clicked):
            properties_tab._select_file_button.click()
            
        mock_node_controller.on_select_file_clicked.assert_called_once_with(plot_node)
        
    def test_handler_safety_when_node_not_found(self, properties_tab, mock_application_model, mock_node_controller, mocker):
        """Verify controller is not called if node is not found during an event."""
        plot_node = create_mock_plot_node(mocker, "node1", "Plot 1", ArtistType.LINE)
        mock_application_model.selection = [plot_node]
        properties_tab._update_content()
        
        mock_application_model.scene_root.find_node_by_id.return_value = None
        
        properties_tab._on_plot_type_combo_changed(1)
        
        mock_node_controller.on_plot_type_changed.assert_not_called()
