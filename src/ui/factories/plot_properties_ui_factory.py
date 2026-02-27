import logging
from functools import partial
from typing import Optional
from pathlib import Path

from PySide6.QtGui import QDoubleValidator
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.models.nodes.plot_node import PlotNode
from src.models.plots.plot_properties import (
    ScatterPlotProperties,
    BasePlotProperties,
)
from src.models.plots.plot_types import ArtistType
from src.services.event_aggregator import EventAggregator
from src.shared.events import Events


# New helper function for data source UI
def _build_data_source_ui(
    node: PlotNode,
    layout: QFormLayout,
    parent: QWidget,
    event_aggregator: EventAggregator,
) -> None:
    """
    Builds the UI elements for selecting and applying data files.
    """
    data_file_path_edit = QLineEdit(
        str(node.data_file_path if node.data_file_path else ""), parent
    )
    data_file_path_edit.setPlaceholderText("No data file selected")
    data_file_path_edit.setReadOnly(True)  # Display only, selection through button
    data_file_path_edit.setObjectName("data_file_path_edit")

    select_file_button = QPushButton("Select File", parent)
    select_file_button.setObjectName("select_file_button")
    select_file_button.clicked.connect(
        partial(event_aggregator.publish, Events.SELECT_DATA_FILE_FOR_NODE_REQUESTED, node_id=node.id)
    )

    apply_button = QPushButton("Apply", parent)
    apply_button.setObjectName("apply_data_button")
    apply_button.clicked.connect(
        partial(
            event_aggregator.publish,
            Events.APPLY_DATA_TO_NODE_REQUESTED,
            node_id=node.id,
            file_path=node.data_file_path,
        )
    )

    h_layout = QHBoxLayout()
    h_layout.addWidget(data_file_path_edit)
    h_layout.addWidget(select_file_button)
    h_layout.addWidget(apply_button)

    layout.addRow("Data File:", h_layout)


def _build_column_selectors(
    node: PlotNode,
    layout: QFormLayout,
    x_combo: QComboBox,
    y_combo: QComboBox,
    event_aggregator: EventAggregator,
):
    assert node.data is not None
    assert node.plot_properties is not None
    columns = list(node.data.columns)
    current_mapping = node.plot_properties.plot_mapping
    current_x = current_mapping.x
    current_y_list = current_mapping.y
    current_y = current_y_list[0] if current_y_list else None

    x_combo.blockSignals(True)
    x_combo.clear()
    x_combo.addItems(columns)
    if current_x in columns:
        x_combo.setCurrentText(current_x)
    x_combo.blockSignals(False)
    x_combo.currentTextChanged.connect(
        lambda text: event_aggregator.publish(
            Events.MAP_PLOT_COLUMNS_REQUESTED,
            node_id=node.id,
            x_column=x_combo.currentText(),
            y_column=y_combo.currentText(),
        )
    )
    layout.addRow("X-Axis Column:", x_combo)

    y_combo.blockSignals(True)
    y_combo.clear()
    y_combo.addItems(columns)
    if current_y in columns:
        y_combo.setCurrentText(current_y)
    y_combo.blockSignals(False)
    y_combo.currentTextChanged.connect(
        lambda text: event_aggregator.publish(
            Events.MAP_PLOT_COLUMNS_REQUESTED,
            node_id=node.id,
            x_column=x_combo.currentText(),
            y_column=y_combo.currentText(),
        )
    )
    layout.addRow("Y-Axis Column:", y_combo)


def _build_limit_selectors(
    node: PlotNode,
    layout: QFormLayout,
    limit_edits: dict,
    event_aggregator: EventAggregator,
):
    assert node.plot_properties is not None
    validator = QDoubleValidator()
    current_limits = node.plot_properties.axes_limits

    xlim = current_limits.xlim
    limit_edits["xlim_min"] = QLineEdit(str(xlim[0] if xlim[0] is not None else ""))
    limit_edits["xlim_min"].setObjectName("xlim_min_edit")
    limit_edits["xlim_max"] = QLineEdit(str(xlim[1] if xlim[1] is not None else ""))
    limit_edits["xlim_max"].setObjectName("xlim_max_edit")

    for w in (limit_edits["xlim_min"], limit_edits["xlim_max"]):
        w.setValidator(validator)
    lim_layout_x = QHBoxLayout()
    lim_layout_x.addWidget(limit_edits["xlim_min"])
    lim_layout_x.addWidget(QLabel("to"))
    lim_layout_x.addWidget(limit_edits["xlim_max"])
    layout.addRow("X-Axis Limits:", lim_layout_x)

    ylim = current_limits.ylim
    limit_edits["ylim_min"] = QLineEdit(str(ylim[0] if ylim[0] is not None else ""))
    limit_edits["ylim_min"].setObjectName("ylim_min_edit")
    limit_edits["ylim_max"] = QLineEdit(str(ylim[1] if ylim[1] is not None else ""))
    limit_edits["ylim_max"].setObjectName("ylim_max_edit")

    for w in (limit_edits["ylim_min"], limit_edits["ylim_max"]):
        w.setValidator(validator)
    lim_layout_y = QHBoxLayout()
    lim_layout_y.addWidget(limit_edits["ylim_min"])
    lim_layout_y.addWidget(QLabel("to"))
    lim_layout_y.addWidget(limit_edits["ylim_max"])
    layout.addRow("Y-Axis Limits:", lim_layout_y)

    # Connect signals after all QLineEdit widgets are defined
    def publish_limit_change():
        event_aggregator.publish(
            Events.CHANGE_PLOT_AXIS_LIMITS_REQUESTED,
            node_id=node.id,
            xlim_min=limit_edits["xlim_min"].text(),
            xlim_max=limit_edits["xlim_max"].text(),
            ylim_min=limit_edits["ylim_min"].text(),
            ylim_max=limit_edits["ylim_max"].text(),
        )

    for w in (limit_edits["xlim_min"], limit_edits["xlim_max"], limit_edits["ylim_min"], limit_edits["ylim_max"]):
        w.editingFinished.connect(publish_limit_change)


def _build_base_plot_properties_ui(
    node: PlotNode,
    layout: QVBoxLayout,
    parent: QWidget,
    event_aggregator: EventAggregator,
    limit_edits: dict,
    x_combo: QComboBox,
    y_combo: QComboBox,
):
    """
    Builds the base UI elements for plot properties (Title, Labels, Column Selectors, Limits).
    """
    
    # Data Source Group (Moved from PropertiesTab for cleaner separation)
    data_source_group = QGroupBox("Data Source", parent)
    data_source_layout = QFormLayout(data_source_group)
    _build_data_source_ui(
        node=node,
        layout=data_source_layout,
        parent=data_source_group,
        event_aggregator=event_aggregator,
    )
    layout.addWidget(data_source_group)

    props = node.plot_properties

    # General Properties Group
    general_group = QGroupBox("General Properties", parent)
    general_layout = QFormLayout(general_group)

    # --- Title ---
    title_edit = QLineEdit(props.title, parent)
    title_edit.setObjectName("title_edit")
    title_edit.editingFinished.connect(
        partial(
            event_aggregator.publish,
            Events.CHANGE_PLOT_TITLE_REQUESTED,
            node_id=node.id,
            new_title=title_edit.text(),
        )
    )
    general_layout.addRow("Title:", title_edit)

    layout.addWidget(general_group)

    # Axis Labels Group
    axis_group = QGroupBox("Axis Labels", parent)
    axis_layout = QFormLayout(axis_group)

    # --- X Label ---
    xlabel_edit = QLineEdit(props.xlabel, parent)
    xlabel_edit.setObjectName("xlabel_edit")
    xlabel_edit.editingFinished.connect(
        partial(
            event_aggregator.publish,
            Events.CHANGE_PLOT_XLABEL_REQUESTED,
            node_id=node.id,
            new_xlabel=xlabel_edit.text(),
        )
    )
    axis_layout.addRow("X-Axis Label:", xlabel_edit)

    # --- Y Label ---
    ylabel_edit = QLineEdit(props.ylabel, parent)
    ylabel_edit.setObjectName("ylabel_edit")
    ylabel_edit.editingFinished.connect(
        partial(
            event_aggregator.publish,
            Events.CHANGE_PLOT_YLABEL_REQUESTED,
            node_id=node.id,
            new_ylabel=ylabel_edit.text(),
        )
    )
    axis_layout.addRow("Y-Axis Label:", ylabel_edit)

    layout.addWidget(axis_group)


    # Data Mapping Group
    data_mapping_group = QGroupBox("Data Mapping", parent)
    data_mapping_layout = QFormLayout(data_mapping_group)

    if node.data is not None:
        try:
            _build_column_selectors(
                node, data_mapping_layout, x_combo, y_combo, event_aggregator
            )
        except Exception as e:
            logging.error(f"Error building column selectors for node {node.id}: {e}")
            data_mapping_layout.addRow(QLabel("Error loading data columns."))
    else:
        data_mapping_layout.addRow(QLabel("Load data to map columns."))

    layout.addWidget(data_mapping_group)

    # Axis Limits Group
    limits_group = QGroupBox("Axis Limits", parent)
    limits_layout = QFormLayout(limits_group)
    _build_limit_selectors(node, limits_layout, limit_edits, event_aggregator)
    layout.addWidget(limits_group)


def _build_line_plot_ui_widgets(
    node: PlotNode,
    layout: QVBoxLayout,
    parent: QWidget,
    event_aggregator: EventAggregator,
    limit_edits: dict,
    x_combo: QComboBox,
    y_combo: QComboBox,
):
    """
    Builds UI widgets specific to Line plots.
    """
    # Create a QFormLayout for the base properties
    base_form_layout = QFormLayout()
    _build_base_plot_properties_ui(
        node=node,
        layout=base_form_layout,
        parent=parent,
        event_aggregator=event_aggregator,
        limit_edits=limit_edits,
        x_combo=x_combo,
        y_combo=y_combo,
    )
    layout.addLayout(
        base_form_layout
    )  # Add the base form layout to the main QVBoxLayout

    # Line-specific properties group
    line_specific_group = QGroupBox("Line Properties", parent)
    line_specific_layout = QFormLayout(line_specific_group) #TODO: This doesn't do anything right now
    # Line-specific properties will go here later
    layout.addWidget(line_specific_group)


def _build_scatter_plot_ui_widgets(
    node: PlotNode,
    layout: QVBoxLayout,
    parent: QWidget,
    event_aggregator: EventAggregator,
    limit_edits: dict,
    x_combo: QComboBox,
    y_combo: QComboBox,
):
    """
    Builds UI widgets specific to Scatter plots.
    """
    # Create a QFormLayout for the base properties
    base_form_layout = QFormLayout()
    _build_base_plot_properties_ui(
        node=node,
        layout=base_form_layout,
        parent=parent,
        event_aggregator=event_aggregator,
        limit_edits=limit_edits,
        x_combo=x_combo,
        y_combo=y_combo,
    )
    layout.addLayout(
        base_form_layout
    )  # Add the base form layout to the main QVBoxLayout

    # Scatter-specific properties group
    scatter_specific_group = QGroupBox("Scatter Properties", parent)
    scatter_specific_layout = QFormLayout(scatter_specific_group)

    props = node.plot_properties
    if isinstance(
        props, ScatterPlotProperties
    ):  # This check is still needed here as builder expects ScatterPlotProperties
        marker_size_edit = QLineEdit(str(props.marker_size), parent)
        marker_size_edit.setObjectName("marker_size_edit")
        marker_size_edit.editingFinished.connect(
            partial(
                event_aggregator.publish,
                Events.CHANGE_PLOT_MARKER_SIZE_REQUESTED,
                node_id=node.id,
                new_size=marker_size_edit.text(),
            )
        )
        scatter_specific_layout.addRow("Marker Size:", marker_size_edit)

    layout.addWidget(scatter_specific_group)


class PlotPropertiesUIFactory:
    """
    A factory class for creating the UI for the properties view
    based on the type of the plot.
    """

    def __init__(self, event_aggregator: EventAggregator):
        self._builders = {}
        self._event_aggregator = event_aggregator

    def register_builder(self, plot_type: ArtistType, builder_func: callable):
        self._builders[plot_type] = builder_func

    def build_widgets(
        self,
        node: PlotNode,
        layout: QVBoxLayout,
        parent: QWidget,
        limit_edits: dict,
        x_combo: QComboBox,
        y_combo: QComboBox,
    ):
        """
        Builds the UI for the given plot node by dispatching to a registered builder.
        If no builder is registered for the plot type, no plot-specific UI elements will be built beyond the default.
        This now expects a QVBoxLayout as the main layout, and will add QGroupBoxes to it.
        """
        props = node.plot_properties
        if not props:
            # Handle case where plot_properties is None
            layout.addWidget(QLabel("No plot properties available for selected node."))
            return

        builder = self._builders.get(props.plot_type)

        if builder:
            # Call the registered builder, passing all necessary arguments
            builder(
                node=node,
                layout=layout,
                parent=parent,
                event_aggregator=self._event_aggregator,
                limit_edits=limit_edits,
                x_combo=x_combo,
                y_combo=y_combo,
            )
        else:  # Explicitly call base builder if no specific builder is found
            base_form_layout = QFormLayout()
            _build_base_plot_properties_ui(
                node=node,
                layout=base_form_layout,
                parent=parent,
                event_aggregator=self._event_aggregator,
                limit_edits=limit_edits,
                x_combo=x_combo,
                y_combo=y_combo,
            )
            layout.addLayout(base_form_layout)