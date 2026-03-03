import logging
from functools import partial

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
        partial(
            event_aggregator.publish,
            Events.SELECT_DATA_FILE_FOR_NODE_REQUESTED,
            node_id=node.id,
        )
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

    # Mapping: Use the first artist's columns
    artist = node.plot_properties.artists[0] if node.plot_properties.artists else None
    current_x = getattr(artist, "x_column", None) if artist else None
    current_y = getattr(artist, "y_column", None) if artist else None

    # Disconnect existing handlers to prevent signal accumulation on persistent widgets
    try:
        x_combo.currentTextChanged.disconnect()
    except (TypeError, RuntimeError):
        pass

    x_combo.blockSignals(True)
    x_combo.clear()
    x_combo.addItems(columns)
    if current_x in columns:
        x_combo.setCurrentText(current_x)
    x_combo.blockSignals(False)
    x_combo.currentTextChanged.connect(
        lambda text: event_aggregator.publish(
            Events.CHANGE_PLOT_COMPONENT_REQUESTED,
            node_id=node.id,
            path="artists.0.x_column",
            value=x_combo.currentText(),
        )
    )
    layout.addRow("X-Axis Column:", x_combo)

    # Disconnect existing handlers to prevent signal accumulation on persistent widgets
    try:
        y_combo.currentTextChanged.disconnect()
    except (TypeError, RuntimeError):
        pass

    y_combo.blockSignals(True)
    y_combo.clear()
    y_combo.addItems(columns)
    if current_y in columns:
        y_combo.setCurrentText(current_y)
    y_combo.blockSignals(False)
    y_combo.currentTextChanged.connect(
        lambda text: event_aggregator.publish(
            Events.CHANGE_PLOT_COMPONENT_REQUESTED,
            node_id=node.id,
            path="artists.0.y_column",
            value=y_combo.currentText(),
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

    # Mapping: Use axis-specific limits
    xlim = node.plot_properties.coords.xaxis.limits
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

    ylim = node.plot_properties.coords.yaxis.limits
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

    # Connect signals to the new generic path-based event
    def publish_xlim_change():
        try:
            v_min = (
                float(limit_edits["xlim_min"].text())
                if limit_edits["xlim_min"].text()
                else None
            )
            v_max = (
                float(limit_edits["xlim_max"].text())
                if limit_edits["xlim_max"].text()
                else None
            )
            event_aggregator.publish(
                Events.CHANGE_PLOT_COMPONENT_REQUESTED,
                node_id=node.id,
                path="coords.xaxis.limits",
                value=(v_min, v_max),
            )
        except ValueError:
            pass

    def publish_ylim_change():
        try:
            v_min = (
                float(limit_edits["ylim_min"].text())
                if limit_edits["ylim_min"].text()
                else None
            )
            v_max = (
                float(limit_edits["ylim_max"].text())
                if limit_edits["ylim_max"].text()
                else None
            )
            event_aggregator.publish(
                Events.CHANGE_PLOT_COMPONENT_REQUESTED,
                node_id=node.id,
                path="coords.yaxis.limits",
                value=(v_min, v_max),
            )
        except ValueError:
            pass

    limit_edits["xlim_min"].editingFinished.connect(publish_xlim_change)
    limit_edits["xlim_max"].editingFinished.connect(publish_xlim_change)
    limit_edits["ylim_min"].editingFinished.connect(publish_ylim_change)
    limit_edits["ylim_max"].editingFinished.connect(publish_ylim_change)


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

    # Data Source Group
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

    # Mapping: Title -> titles.center.text
    title_text = props.titles.get("center").text if props.titles.get("center") else ""
    title_edit = QLineEdit(title_text, parent)
    title_edit.setObjectName("title_edit")
    title_edit.editingFinished.connect(
        lambda: event_aggregator.publish(
            Events.CHANGE_PLOT_COMPONENT_REQUESTED,
            node_id=node.id,
            path="titles.center.text",
            value=title_edit.text(),
        )
    )
    general_layout.addRow("Title:", title_edit)

    layout.addWidget(general_group)

    # Axis Labels Group
    axis_group = QGroupBox("Axis Labels", parent)
    axis_layout = QFormLayout(axis_group)

    # Mapping: X Label -> coords.xaxis.label.text
    xlabel_text = props.coords.xaxis.label.text
    xlabel_edit = QLineEdit(xlabel_text, parent)
    xlabel_edit.setObjectName("xlabel_edit")
    xlabel_edit.editingFinished.connect(
        lambda: event_aggregator.publish(
            Events.CHANGE_PLOT_COMPONENT_REQUESTED,
            node_id=node.id,
            path="coords.xaxis.label.text",
            value=xlabel_edit.text(),
        )
    )
    axis_layout.addRow("X-Axis Label:", xlabel_edit)

    # Mapping: Y Label -> coords.yaxis.label.text
    ylabel_text = props.coords.yaxis.label.text
    ylabel_edit = QLineEdit(ylabel_text, parent)
    ylabel_edit.setObjectName("ylabel_edit")
    ylabel_edit.editingFinished.connect(
        lambda: event_aggregator.publish(
            Events.CHANGE_PLOT_COMPONENT_REQUESTED,
            node_id=node.id,
            path="coords.yaxis.label.text",
            value=ylabel_edit.text(),
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
    line_specific_layout = QFormLayout(
        line_specific_group
    )  # TODO: This doesn't do anything right now
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
    if props.artists and props.artists[0].artist_type == ArtistType.SCATTER:
        artist = props.artists[0]
        marker_size_edit = QLineEdit(str(artist.visuals.markersize), parent)
        marker_size_edit.setObjectName("marker_size_edit")
        marker_size_edit.editingFinished.connect(
            lambda: event_aggregator.publish(
                Events.CHANGE_PLOT_COMPONENT_REQUESTED,
                node_id=node.id,
                path="artists.0.visuals.markersize",
                value=marker_size_edit.text(),
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

        # Derive plot type from the first artist, defaulting to LINE
        plot_type = ArtistType.LINE
        if hasattr(props, "artists") and props.artists:
            plot_type = props.artists[0].artist_type

        builder = self._builders.get(plot_type)

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
