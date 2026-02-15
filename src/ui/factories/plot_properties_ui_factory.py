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

from src.controllers.node_controller import NodeController
from src.models.nodes.plot_node import PlotNode
from src.models.plots.plot_properties import (
    ScatterPlotProperties,
    BasePlotProperties,
)
from src.models.plots.plot_types import PlotType


# New helper function for data source UI
def _build_data_source_ui(
    node: PlotNode,
    layout: QFormLayout,
    parent: QWidget,
    node_controller: NodeController,
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
        partial(node_controller.on_select_file_clicked, node=node)
    )

    apply_button = QPushButton("Apply", parent)
    apply_button.setObjectName("apply_data_button")
    apply_button.clicked.connect(
        partial(
            node_controller.on_apply_data_clicked,
            node=node,
            new_file_path=node.data_file_path,
        )
    )  # Path will be updated in controller

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
    node_controller: NodeController,
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
        partial(
            node_controller.on_column_mapping_changed,
            node=node,
            x_combo=x_combo,
            y_combo=y_combo,
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
        partial(
            node_controller.on_column_mapping_changed,
            node=node,
            x_combo=x_combo,
            y_combo=y_combo,
        )
    )
    layout.addRow("Y-Axis Column:", y_combo)


def _build_limit_selectors(
    node: PlotNode,
    layout: QFormLayout,
    limit_edits: dict,
    node_controller: NodeController,
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
    limit_edits["xlim_min"].editingFinished.connect(
        partial(
            node_controller.on_limit_editing_finished,
            node=node,
            xlim_min_edit=limit_edits["xlim_min"],
            xlim_max_edit=limit_edits["xlim_max"],
            ylim_min_edit=limit_edits["ylim_min"],
            ylim_max_edit=limit_edits["ylim_max"],
        )
    )
    limit_edits["xlim_max"].editingFinished.connect(
        partial(
            node_controller.on_limit_editing_finished,
            node=node,
            xlim_min_edit=limit_edits["xlim_min"],
            xlim_max_edit=limit_edits["xlim_max"],
            ylim_min_edit=limit_edits["ylim_min"],
            ylim_max_edit=limit_edits["ylim_max"],
        )
    )
    limit_edits["ylim_min"].editingFinished.connect(
        partial(
            node_controller.on_limit_editing_finished,
            node=node,
            xlim_min_edit=limit_edits["xlim_min"],
            xlim_max_edit=limit_edits["xlim_max"],
            ylim_min_edit=limit_edits["ylim_min"],
            ylim_max_edit=limit_edits["ylim_max"],
        )
    )
    limit_edits["ylim_max"].editingFinished.connect(
        partial(
            node_controller.on_limit_editing_finished,
            node=node,
            xlim_min_edit=limit_edits["xlim_min"],
            xlim_max_edit=limit_edits["xlim_max"],
            ylim_min_edit=limit_edits["ylim_min"],
            ylim_max_edit=limit_edits["ylim_max"],
        )
    )


def _build_base_plot_properties_ui(
    node: PlotNode,
    layout: QVBoxLayout,
    parent: QWidget,
    node_controller: NodeController,
    limit_edits: dict,
    x_combo: QComboBox,
    y_combo: QComboBox,
):
    """
    Builds the base UI elements for plot properties (Title, Labels, Column Selectors, Limits).
    """
    props = node.plot_properties

    # General Properties Group
    general_group = QGroupBox("General Properties", parent)
    general_layout = QFormLayout(general_group)

    # --- Title ---
    title_edit = QLineEdit(props.title, parent)
    title_edit.setObjectName("title_edit")
    title_edit.editingFinished.connect(
        partial(
            node_controller.on_property_changed,
            node=node,
            prop_name="title",
            new_value=title_edit.text(),
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
            node_controller.on_property_changed,
            node=node,
            prop_name="xlabel",
            new_value=xlabel_edit.text(),
        )
    )
    axis_layout.addRow("X-Axis Label:", xlabel_edit)

    # --- Y Label ---
    ylabel_edit = QLineEdit(props.ylabel, parent)
    ylabel_edit.setObjectName("ylabel_edit")
    ylabel_edit.editingFinished.connect(
        partial(
            node_controller.on_property_changed,
            node=node,
            prop_name="ylabel",
            new_value=ylabel_edit.text(),
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
                node, data_mapping_layout, x_combo, y_combo, node_controller
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
    _build_limit_selectors(node, limits_layout, limit_edits, node_controller)
    layout.addWidget(limits_group)


def _build_line_plot_ui_widgets(
    node: PlotNode,
    layout: QVBoxLayout,
    parent: QWidget,
    node_controller: NodeController,
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
        node_controller=node_controller,
        limit_edits=limit_edits,
        x_combo=x_combo,
        y_combo=y_combo,
    )
    layout.addLayout(
        base_form_layout
    )  # Add the base form layout to the main QVBoxLayout

    # Line-specific properties group
    line_specific_group = QGroupBox("Line Properties", parent)
    line_specific_layout = QFormLayout(line_specific_group)
    # Line-specific properties will go here later
    layout.addWidget(line_specific_group)


def _build_scatter_plot_ui_widgets(
    node: PlotNode,
    layout: QVBoxLayout,
    parent: QWidget,
    node_controller: NodeController,
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
        node_controller=node_controller,
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
                node_controller.on_property_changed,
                node=node,
                prop_name="marker_size",
                new_value=marker_size_edit.text(),
            )
        )
        scatter_specific_layout.addRow("Marker Size:", marker_size_edit)

    layout.addWidget(scatter_specific_group)


class PlotPropertiesUIFactory:
    """
    A factory class for creating the UI for the properties view
    based on the type of the plot.
    """

    def __init__(self, node_controller: NodeController):
        self._builders = {}
        self._node_controller = node_controller

    def register_builder(self, plot_type: PlotType, builder_func: callable):
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
                node_controller=self._node_controller,
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
                node_controller=self._node_controller,
                limit_edits=limit_edits,
                x_combo=x_combo,
                y_combo=y_combo,
            )
            layout.addLayout(base_form_layout)