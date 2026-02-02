from functools import partial
from typing import Callable

from PySide6.QtGui import QDoubleValidator
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QWidget,
)

from src.models.nodes.plot_node import PlotNode
from src.models.nodes.plot_properties import (
    AxesLimits,
    LinePlotProperties,
    PlotMapping,
    ScatterPlotProperties,
)
from src.models.nodes.plot_types import PlotType


class PropertiesUIFactory:
    """
    A factory class for creating the UI for the properties view
    based on the type of the plot.
    """

    @staticmethod
    def create_ui(
        node: PlotNode,
        layout: QFormLayout,
        parent: QWidget,
        plot_types: list[PlotType],
        on_plot_type_changed: Callable,
        on_property_changed: Callable,
        on_column_mapping_changed: Callable,
        on_limit_editing_finished: Callable,
        limit_edits: dict,
        x_combo: QComboBox,
        y_combo: QComboBox,
    ):
        """
        Creates the UI for the given plot node and adds it to the given layout.
        """
        props = node.plot_properties

        # --- Plot Type ---
        plot_type_combo = QComboBox(parent)
        plot_type_combo.setObjectName("plot_type_combo")
        for plot_type in plot_types:
            plot_type_combo.addItem(plot_type.value, plot_type)
        plot_type_combo.setCurrentText(props.plot_type.value)
        plot_type_combo.currentTextChanged.connect(
            partial(on_plot_type_changed, node=node)
        )
        layout.addRow("Plot Type:", plot_type_combo)

        # --- Title ---
        title_edit = QLineEdit(props.title, parent)
        title_edit.setObjectName("title_edit")
        title_edit.editingFinished.connect(
            partial(on_property_changed, node=node, prop_name="title", widget=title_edit)
        )
        layout.addRow("Title:", title_edit)

        # --- X Label ---
        xlabel_edit = QLineEdit(props.xlabel, parent)
        xlabel_edit.setObjectName("xlabel_edit")
        xlabel_edit.editingFinished.connect(
            partial(
                on_property_changed, node=node, prop_name="xlabel", widget=xlabel_edit
            )
        )
        layout.addRow("X-Axis Label:", xlabel_edit)

        # --- Y Label ---
        ylabel_edit = QLineEdit(props.ylabel, parent)
        ylabel_edit.setObjectName("ylabel_edit")
        ylabel_edit.editingFinished.connect(
            partial(
                on_property_changed, node=node, prop_name="ylabel", widget=ylabel_edit
            )
        )
        layout.addRow("Y-Axis Label:", ylabel_edit)

        # --- Plot-specific properties ---
        if isinstance(props, ScatterPlotProperties):
            marker_size_edit = QLineEdit(str(props.marker_size), parent)
            marker_size_edit.setObjectName("marker_size_edit")
            marker_size_edit.editingFinished.connect(
                partial(
                    on_property_changed,
                    node=node,
                    prop_name="marker_size",
                    widget=marker_size_edit,
                )
            )
            layout.addRow("Marker Size:", marker_size_edit)

        if node.data is not None:
            PropertiesUIFactory._build_column_selectors(
                node, layout, x_combo, y_combo, on_column_mapping_changed
            )

        PropertiesUIFactory._build_limit_selectors(
            node, layout, limit_edits, on_limit_editing_finished
        )

    @staticmethod
    def _build_column_selectors(
        node: PlotNode,
        layout: QFormLayout,
        x_combo: QComboBox,
        y_combo: QComboBox,
        on_column_mapping_changed: Callable,
    ):
        assert node.data is not None
        assert node.plot_properties is not None
        columns = list(node.data.columns)
        current_mapping = node.plot_properties.plot_mapping
        current_x = current_mapping.x
        current_y_list = current_mapping.y
        current_y = current_y_list[0] if current_y_list else None

        x_combo.clear()
        x_combo.addItems(columns)
        if current_x in columns:
            x_combo.setCurrentText(current_x)
        x_combo.currentTextChanged.connect(partial(on_column_mapping_changed, node=node))
        layout.addRow("X-Axis Column:", x_combo)

        y_combo.clear()
        y_combo.addItems(columns)
        if current_y in columns:
            y_combo.setCurrentText(current_y)
        y_combo.currentTextChanged.connect(partial(on_column_mapping_changed, node=node))
        layout.addRow("Y-Axis Column:", y_combo)

    @staticmethod
    def _build_limit_selectors(
        node: PlotNode,
        layout: QFormLayout,
        limit_edits: dict,
        on_limit_editing_finished: Callable,
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
            w.editingFinished.connect(partial(on_limit_editing_finished, node=node))
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
            w.editingFinished.connect(partial(on_limit_editing_finished, node=node))

        lim_layout_y = QHBoxLayout()
        lim_layout_y.addWidget(limit_edits["ylim_min"])
        lim_layout_y.addWidget(QLabel("to"))
        lim_layout_y.addWidget(limit_edits["ylim_max"])
        layout.addRow("Y-Axis Limits:", lim_layout_y)
