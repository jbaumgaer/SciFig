import pytest
from unittest.mock import MagicMock, ANY
from PySide6.QtWidgets import QWidget, QGroupBox, QComboBox, QLineEdit, QPushButton, QLabel
from pathlib import Path

from src.ui.panels.properties_tab import PropertiesTab
from src.models.plots.plot_types import ArtistType
from src.shared.events import Events


@pytest.fixture
def properties_tab(qtbot, mock_application_model, mock_event_aggregator, mock_plot_properties_ui_factory):
    """Provides a fresh PropertiesTab instance."""
    # Ensure IconPath is not a blocker
    from src.shared.constants import IconPath
    from src.services.config_service import ConfigService
    IconPath.set_config_service(MagicMock(spec=ConfigService))

    tab = PropertiesTab(
        model=mock_application_model,
        event_aggregator=mock_event_aggregator,
        plot_properties_ui_factory=mock_plot_properties_ui_factory
    )
    qtbot.addWidget(tab)
    return tab


def configure_node(node, props, node_id="p1", name="Plot 1", data_path=None):
    """Helper to initialize a mock node with real properties and attributes."""
    node.id = node_id
    node.name = name
    node.data_file_path = data_path
    node.plot_properties = props
    # Ensure artist type is set correctly in properties
    if props.artists:
        props.artists[0].artist_type = ArtistType.LINE
    return node


class TestPropertiesTab:
    """
    Unit tests for PropertiesTab.
    Verifies that the properties view correctly reflects the selection state
    and publishes modification requests via the EventAggregator.
    """

    def test_initial_ui_structure(self, properties_tab):
        """Verifies that the basic layout groups are created during initialization."""
        assert isinstance(properties_tab._subplot_selection_group, QGroupBox)
        assert isinstance(properties_tab._plot_type_group, QGroupBox)
        assert isinstance(properties_tab._dynamic_properties_area, QWidget)
        
        # Verify plot type combo is populated
        combo = properties_tab._plot_type_selector_combo
        assert combo.count() == len(ArtistType)
        assert combo.findText(ArtistType.LINE.value) != -1

    def test_update_content_no_selection(self, properties_tab, mock_application_model):
        """Verifies UI state when nothing is selected."""
        mock_application_model.selection = []
        mock_application_model.scene_root.all_descendants.return_value = []
        
        properties_tab._update_content()
        
        assert not properties_tab._subplot_selector_combo.isEnabled()
        assert properties_tab._subplot_selector_combo.currentText() == "No plots available"
        
        # Check placeholder in dynamic area
        layout = properties_tab._dynamic_properties_layout
        assert layout.count() > 0
        placeholder = layout.itemAt(0).widget()
        assert isinstance(placeholder, QLabel)
        assert "Select a plot" in placeholder.text()

    def test_update_content_single_plot_selected(self, properties_tab, mock_application_model, mock_plot_node, sample_plot_properties):
        """Verifies UI correctly reflects properties of a single selected PlotNode."""
        configure_node(mock_plot_node, sample_plot_properties, "p1", "MyPlot", Path("test.csv"))
        
        mock_application_model.selection = [mock_plot_node]
        mock_application_model.scene_root.all_descendants.return_value = [mock_plot_node]
        
        properties_tab._update_content()
        
        assert properties_tab._subplot_selector_combo.currentText() == "MyPlot"
        assert properties_tab._subplot_selector_combo.currentData() == "p1"
        assert properties_tab._data_file_path_edit.text() == "test.csv"
        assert properties_tab._plot_type_selector_combo.currentText() == ArtistType.LINE.value

    def test_subplot_selection_event(self, properties_tab, mock_application_model, mock_plot_node, sample_plot_properties, mock_event_aggregator):
        """Verifies that changing the subplot combo publishes a selection change event."""
        configure_node(mock_plot_node, sample_plot_properties, "p1", "Plot 1")
        mock_application_model.scene_root.all_descendants.return_value = [mock_plot_node]
        
        properties_tab._update_content()
        
        # Verify combo was populated correctly
        combo = properties_tab._subplot_selector_combo
        index = combo.findData("p1")
        assert index != -1
        
        # Reset mock after population
        mock_event_aggregator.publish.reset_mock()
        
        # Force a change signal by setting to different index first if needed,
        # but here we just trigger the signal manually or ensure change.
        combo.blockSignals(True)
        combo.setCurrentIndex(-1)
        combo.blockSignals(False)
        
        combo.setCurrentIndex(index)
        
        mock_event_aggregator.publish.assert_any_call(
            Events.SUBPLOT_SELECTION_IN_UI_CHANGED,
            plot_id="p1"
        )

    def test_plot_type_change_event(self, properties_tab, mock_application_model, mock_plot_node, sample_plot_properties, mock_event_aggregator):
        """Verifies that changing the plot type combo publishes a type change request."""
        configure_node(mock_plot_node, sample_plot_properties, "p1", "Plot 1")
        mock_application_model.selection = [mock_plot_node]
        mock_application_model.scene_root.all_descendants.return_value = [mock_plot_node]
        properties_tab._update_content()
        
        # Change type in UI
        mock_event_aggregator.publish.reset_mock()
        properties_tab._plot_type_selector_combo.setCurrentText(ArtistType.SCATTER.value)
        
        mock_event_aggregator.publish.assert_any_call(
            Events.CHANGE_PLOT_TYPE_REQUESTED,
            node_id="p1",
            new_plot_type_str=ArtistType.SCATTER.value
        )

    def test_select_file_button_event(self, properties_tab, mock_application_model, mock_plot_node, sample_plot_properties, mock_event_aggregator):
        """Verifies that clicking 'Select File' publishes the correct request."""
        configure_node(mock_plot_node, sample_plot_properties, "p1", "Plot 1")
        mock_application_model.selection = [mock_plot_node]
        mock_application_model.scene_root.all_descendants.return_value = [mock_plot_node]
        properties_tab._update_content()
        
        mock_event_aggregator.publish.reset_mock()
        properties_tab._select_file_button.click()
        
        mock_event_aggregator.publish.assert_any_call(
            Events.SELECT_DATA_FILE_FOR_NODE_REQUESTED,
            node_id="p1"
        )

    def test_apply_data_button_event(self, properties_tab, mock_application_model, mock_plot_node, sample_plot_properties, mock_event_aggregator):
        """Verifies that clicking 'Apply' publishes the data load request."""
        configure_node(mock_plot_node, sample_plot_properties, "p1", "Plot 1", Path("old.csv"))
        mock_application_model.selection = [mock_plot_node]
        mock_application_model.scene_root.all_descendants.return_value = [mock_plot_node]
        
        properties_tab._update_content()
        
        # Change text in line edit (simulating user selection)
        properties_tab._data_file_path_edit.setText("path/to/new_data.csv")
        
        mock_event_aggregator.publish.reset_mock()
        properties_tab._apply_data_button.click()
        
        mock_event_aggregator.publish.assert_any_call(
            Events.APPLY_DATA_TO_NODE_REQUESTED,
            node_id="p1",
            file_path=Path("path/to/new_data.csv")
        )

    def test_event_subscriptions_trigger_update(self, mock_event_aggregator, mock_application_model, mock_plot_properties_ui_factory, mocker):
        """Verifies that the tab subscribes to model changes and triggers updates."""
        # Patch the method on the class before instantiation
        mock_update = mocker.patch.object(PropertiesTab, "_update_content")
        
        tab = PropertiesTab(
            model=mock_application_model,
            event_aggregator=mock_event_aggregator,
            plot_properties_ui_factory=mock_plot_properties_ui_factory
        )
        
        # Initial call in __init__
        assert mock_update.call_count >= 1
        mock_update.reset_mock()
        
        # Get the callback for SELECTION_CHANGED
        selection_callback = None
        for call_args in mock_event_aggregator.subscribe.call_args_list:
            if call_args[0][0] == Events.SELECTION_CHANGED:
                selection_callback = call_args[0][1]
                break
        
        assert selection_callback is not None
        selection_callback(["p1"])
        
        assert mock_update.called

    def test_update_content_if_selected_filter(self, properties_tab, mocker):
        """Verifies that _update_content_if_selected only triggers update for the active node."""
        mock_update = mocker.patch.object(properties_tab, "_update_content")
        
        # Set current selected in combo using positional userData to be safe
        properties_tab._subplot_selector_combo.clear()
        properties_tab._subplot_selector_combo.addItem("Current", "active_id")
        properties_tab._subplot_selector_combo.setCurrentIndex(0)
        
        assert properties_tab._subplot_selector_combo.currentData() == "active_id"
        
        # 1. Trigger for a different node
        properties_tab._update_content_if_selected("other_id")
        assert not mock_update.called
        
        # 2. Trigger for the active node
        properties_tab._update_content_if_selected("active_id")
        assert mock_update.called

    def test_reactive_rebuild_on_external_change(self, properties_tab, mock_application_model, mock_plot_node, sample_plot_properties, mock_event_aggregator, mock_plot_properties_ui_factory, mocker):
        """Verifies that the UI rebuilds when an external PLOT_NODE_PROPERTY_CHANGED event occurs for the selected node."""
        configure_node(mock_plot_node, sample_plot_properties, "p1", "Plot 1")
        mock_application_model.selection = [mock_plot_node]
        mock_application_model.scene_root.all_descendants.return_value = [mock_plot_node]
        
        # Initial population
        properties_tab._update_content()
        mock_plot_properties_ui_factory.build_widgets.reset_mock()
        
        # Simulate external change event for THIS node
        # PropertiesTab subscribed to PLOT_NODE_PROPERTY_CHANGED in __init__
        callback = None
        for call_args in mock_event_aggregator.subscribe.call_args_list:
            if call_args[0][0] == Events.PLOT_NODE_PROPERTY_CHANGED:
                callback = call_args[0][1]
                break
        
        assert callback is not None
        callback(node_id="p1")
        
        # Verify that factory.build_widgets was called again (triggered by _update_content)
        mock_plot_properties_ui_factory.build_widgets.assert_called_once()
        assert mock_plot_properties_ui_factory.build_widgets.call_args[1]['node'] == mock_plot_node
