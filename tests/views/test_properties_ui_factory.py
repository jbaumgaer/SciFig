import pandas as pd
import pytest
from PySide6.QtWidgets import QComboBox, QFormLayout, QLineEdit, QWidget

from src.models.nodes.plot_node import PlotNode
from src.models.nodes.plot_properties import (
    AxesLimits,
    LinePlotProperties,
    PlotMapping,
    ScatterPlotProperties,
)
from src.models.nodes.plot_types import PlotType
from src.views.properties_ui_factory import PropertiesUIFactory


@pytest.fixture
def empty_callbacks():
    """Provides a dictionary of mock callback functions."""
    return {
        "on_plot_type_changed": lambda: None,
        "on_property_changed": lambda: None,
        "on_column_mapping_changed": lambda: None,
        "on_limit_editing_finished": lambda: None,
    }


def test_create_ui_for_line_plot(qtbot, empty_callbacks):
    """
    Tests that the factory creates the correct basic widgets for a LinePlot.
    """
    parent_widget = QWidget()
    node = PlotNode()
    node.data = pd.DataFrame({"col1": [1, 2], "col2": [3, 4]})
    node.plot_properties = LinePlotProperties(
        title="My Line Plot",
        xlabel="X",
        ylabel="Y",
        plot_mapping=PlotMapping(x="col1", y=["col2"]),
        axes_limits=AxesLimits(xlim=(0, 1), ylim=(0, 1)),
        plot_type=PlotType.LINE,
    )

    form_layout = QFormLayout()
    limit_edits = {}
    x_combo = QComboBox()
    y_combo = QComboBox()

    PropertiesUIFactory.create_ui(
        node=node,
        layout=form_layout,
        parent=parent_widget,
        plot_types=[PlotType.LINE, PlotType.SCATTER],
        limit_edits=limit_edits,
        x_combo=x_combo,
        y_combo=y_combo,
        **empty_callbacks,
    )

    # --- Assertions ---
    assert form_layout.rowCount() == 8

    # Check for specific widgets by object name
    assert parent_widget.findChild(QComboBox, "plot_type_combo") is not None
    assert parent_widget.findChild(QLineEdit, "title_edit") is not None
    assert parent_widget.findChild(QLineEdit, "xlabel_edit") is not None
    assert parent_widget.findChild(QLineEdit, "ylabel_edit") is not None

    # Check that scatter-specific widgets do NOT exist
    assert parent_widget.findChild(QLineEdit, "marker_size_edit") is None


def test_create_ui_for_scatter_plot(qtbot, empty_callbacks):
    """
    Tests that the factory creates additional widgets for a ScatterPlot.
    """
    parent_widget = QWidget()
    node = PlotNode()
    node.data = pd.DataFrame({"col1": [1, 2], "col2": [3, 4]})
    node.plot_properties = ScatterPlotProperties(
        title="My Scatter Plot",
        xlabel="X",
        ylabel="Y",
        plot_mapping=PlotMapping(x="col1", y=["col2"]),
        axes_limits=AxesLimits(xlim=(0, 1), ylim=(0, 1)),
        plot_type=PlotType.SCATTER,
        marker_size=5,
    )

    form_layout = QFormLayout()
    limit_edits = {}
    x_combo = QComboBox()
    y_combo = QComboBox()

    PropertiesUIFactory.create_ui(
        node=node,
        layout=form_layout,
        parent=parent_widget,
        plot_types=[PlotType.LINE, PlotType.SCATTER],
        limit_edits=limit_edits,
        x_combo=x_combo,
        y_combo=y_combo,
        **empty_callbacks,
    )

    # --- Assertions ---
    assert form_layout.rowCount() == 9

    # Check that scatter-specific widgets DO exist
    marker_size_edit = parent_widget.findChild(QLineEdit, "marker_size_edit")
    assert marker_size_edit is not None
    assert marker_size_edit.text() == "5"
