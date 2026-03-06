import pytest
from unittest.mock import MagicMock, ANY
from PySide6.QtWidgets import QWidget, QVBoxLayout, QComboBox, QLineEdit, QGroupBox, QPushButton

from src.ui.factories.plot_properties_ui_factory import (
    PlotPropertiesUIFactory,
    _build_data_source_ui,
    _build_column_selectors,
    _build_limit_selectors,
    _build_base_plot_properties_ui,
    _build_line_plot_ui_widgets,
    _build_scatter_plot_ui_widgets
)
from src.models.plots.plot_types import ArtistType
from src.shared.events import Events


@pytest.fixture
def factory(mock_event_aggregator):
    """Provides a PlotPropertiesUIFactory instance."""
    return PlotPropertiesUIFactory(mock_event_aggregator)


@pytest.fixture
def ui_container(qtbot):
    """Provides a widget and layout for building UI elements."""
    widget = QWidget()
    layout = QVBoxLayout(widget)
    qtbot.addWidget(widget)
    return widget, layout


class TestPlotPropertiesUIFactory:
    """
    Unit tests for PlotPropertiesUIFactory.
    Verifies dispatch logic and registration.
    """

    def test_register_and_dispatch(self, factory, mock_plot_node, ui_container):
        """Verifies that the factory dispatches to the registered builder."""
        parent, layout = ui_container
        mock_builder = MagicMock()
        
        # Setup node to have SCATTER type
        mock_plot_node.plot_properties.artists[0].artist_type = ArtistType.SCATTER
        
        factory.register_builder(ArtistType.SCATTER, mock_builder)
        
        factory.build_widgets(
            node=mock_plot_node,
            layout=layout,
            parent=parent,
            limit_edits={},
            x_combo=QComboBox(),
            y_combo=QComboBox()
        )
        
        mock_builder.assert_called_once()

    def test_register_builder_overwrites_existing(self, factory, mock_plot_node, ui_container):
        """Verify that registering a builder for an existing ArtistType overwrites the previous one."""
        parent, layout = ui_container
        mock_builder_v1 = MagicMock(name="builder_v1")
        mock_builder_v2 = MagicMock(name="builder_v2")

        # 1. Register first builder
        factory.register_builder(ArtistType.LINE, mock_builder_v1)
        assert factory._builders[ArtistType.LINE] == mock_builder_v1

        # 2. Overwrite with second builder
        factory.register_builder(ArtistType.LINE, mock_builder_v2)
        assert factory._builders[ArtistType.LINE] == mock_builder_v2

        # 3. Setup node and dispatch
        mock_plot_node.plot_properties.artists[0].artist_type = ArtistType.LINE
        
        factory.build_widgets(
            node=mock_plot_node,
            layout=layout,
            parent=parent,
            limit_edits={},
            x_combo=QComboBox(),
            y_combo=QComboBox()
        )

        # 4. Verify only the second builder was called
        mock_builder_v2.assert_called_once()
        mock_builder_v1.assert_not_called()

    def test_fallback_to_base_ui(self, factory, mock_plot_node, sample_plot_properties, ui_container):
        """Verifies fallback when no specific builder is registered."""
        parent, layout = ui_container
        # Ensure no builder is registered for the node's type
        factory._builders = {}
        mock_plot_node.plot_properties = sample_plot_properties
        mock_plot_node.data_file_path = None
        
        factory.build_widgets(
            node=mock_plot_node,
            layout=layout,
            parent=parent,
            limit_edits={},
            x_combo=QComboBox(),
            y_combo=QComboBox()
        )
        
        # Check that group boxes were added (at least 5 for base UI)
        group_boxes = parent.findChildren(QGroupBox)
        assert len(group_boxes) >= 5


class TestPlotPropertiesHelpers:
    """
    Unit tests for individual UI building helper functions.
    """

    def test_build_data_source_ui_triggers_events(self, mock_plot_node, mock_event_aggregator, qtbot):
        """Verifies that data source buttons publish correct events."""
        parent = QWidget()
        from PySide6.QtWidgets import QFormLayout
        layout = QFormLayout(parent)
        
        mock_plot_node.id = "p1"
        mock_plot_node.data_file_path = "test.csv"
        
        _build_data_source_ui(mock_plot_node, layout, parent, mock_event_aggregator)
        
        # Find and trigger 'Select File' button
        btn_select = parent.findChild(QPushButton, "select_file_button")
        btn_select.click()
        mock_event_aggregator.publish.assert_any_call(
            Events.SELECT_DATA_FILE_FOR_NODE_REQUESTED, node_id="p1"
        )
        
        # Find and trigger 'Apply' button
        btn_apply = parent.findChild(QPushButton, "apply_data_button")
        btn_apply.click()
        mock_event_aggregator.publish.assert_any_call(
            Events.APPLY_DATA_TO_NODE_REQUESTED, node_id="p1", file_path="test.csv"
        )

    def test_build_column_selectors_updates_properties(self, mock_plot_node, sample_dataframe, mock_event_aggregator, qtbot):
        """Verifies that column combo boxes publish property change events."""
        mock_plot_node.data = sample_dataframe # Columns: Time, Voltage, Current
        mock_plot_node.id = "p1"
        
        from PySide6.QtWidgets import QFormLayout
        parent = QWidget()
        layout = QFormLayout(parent)
        x_combo = QComboBox()
        y_combo = QComboBox()
        
        _build_column_selectors(mock_plot_node, layout, x_combo, y_combo, mock_event_aggregator)
        
        # Change X selection
        x_combo.setCurrentText("Voltage")
        mock_event_aggregator.publish.assert_any_call(
            Events.CHANGE_PLOT_COMPONENT_REQUESTED,
            node_id="p1",
            path="artists.0.x_column",
            value="Voltage"
        )

    def test_build_limit_selectors_updates_properties(self, mock_plot_node, sample_plot_properties, mock_event_aggregator, qtbot):
        """Verifies that limit line edits publish property change events."""
        mock_plot_node.plot_properties = sample_plot_properties
        mock_plot_node.id = "p1"
        
        from PySide6.QtWidgets import QFormLayout
        parent = QWidget()
        layout = QFormLayout(parent)
        limit_edits = {}
        
        _build_limit_selectors(mock_plot_node, layout, limit_edits, mock_event_aggregator)
        
        # Simulate typing in xlim_min
        edit_min = limit_edits["xlim_min"]
        edit_min.setText("10.5")
        edit_min.editingFinished.emit()
        
        mock_event_aggregator.publish.assert_any_call(
            Events.CHANGE_PLOT_COMPONENT_REQUESTED,
            node_id="p1",
            path="coords.xaxis.limits",
            value=(10.5, ANY)
        )

    def test_build_scatter_specific_properties(self, mock_plot_node, sample_plot_properties, mock_event_aggregator, qtbot):
        """Verifies that scatter-specific marker size edit is built and working."""
        # Setup as scatter plot
        mock_plot_node.plot_properties = sample_plot_properties
        mock_plot_node.data_file_path = None
        artist = mock_plot_node.plot_properties.artists[0]
        artist.artist_type = ArtistType.SCATTER
        artist.visuals.markersize = 5.0
        mock_plot_node.id = "p1"
        
        parent, layout = QWidget(), QVBoxLayout()
        limit_edits = {}
        x_combo, y_combo = QComboBox(), QComboBox()
        
        _build_scatter_plot_ui_widgets(
            mock_plot_node, layout, parent, mock_event_aggregator,
            limit_edits, x_combo, y_combo
        )
        
        # Find marker size edit
        marker_edit = parent.findChild(QLineEdit, "marker_size_edit")
        assert marker_edit is not None
        assert marker_edit.text() == "5.0"
        
        marker_edit.setText("12.0")
        marker_edit.editingFinished.emit()
        
        mock_event_aggregator.publish.assert_any_call(
            Events.CHANGE_PLOT_COMPONENT_REQUESTED,
            node_id="p1",
            path="artists.0.visuals.markersize",
            value="12.0"
        )
