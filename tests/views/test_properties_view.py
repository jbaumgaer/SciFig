import pandas as pd
import pytest
from matplotlib.figure import Figure
from PySide6.QtWidgets import QComboBox, QLineEdit, QVBoxLayout, QWidget

from src.commands.command_manager import CommandManager
from src.models.application_model import ApplicationModel
from src.models.nodes.plot_node import PlotNode
from src.models.nodes.plot_properties import (
    AxesLimits,
    LinePlotProperties,
    PlotMapping,
    ScatterPlotProperties,
)
from src.models.nodes.plot_types import PlotType
from src.views.properties_view import PropertiesView


@pytest.fixture
def app_model():
    """Provides a mock ApplicationModel."""
    return ApplicationModel(figure=Figure())


@pytest.fixture
def command_manager(app_model):
    """Provides a mock CommandManager."""
    return CommandManager(app_model)


@pytest.fixture
def properties_view(app_model, command_manager):
    """Provides a PropertiesView instance."""
    plot_types = [PlotType.LINE, PlotType.SCATTER]
    view = PropertiesView(app_model, command_manager, plot_types)
    return view


def test_properties_view_rebuilds_ui_on_plot_type_change(
    qtbot, properties_view, app_model
):
    """
    Tests that PropertiesView correctly rebuilds its UI when the plot type
    of a selected PlotNode changes from Line to Scatter, and vice-versa.
    """
    # 1. Setup: Create a PlotNode with LinePlotProperties and select it
    plot_node = PlotNode()
    plot_node.data = pd.DataFrame({"col1": [1, 2], "col2": [3, 4]})
    plot_node.plot_properties = LinePlotProperties(
        title="Initial Plot",
        xlabel="X",
        ylabel="Y",
        plot_mapping=PlotMapping(x="col1", y=["col2"]),
        axes_limits=AxesLimits(xlim=(0, 1), ylim=(0, 1)),
        plot_type=PlotType.LINE,
    )
    app_model.set_selection([plot_node])
    qtbot.addWidget(properties_view)
    properties_view.show()

    # Ensure initial UI is for LinePlot (no marker_size_edit)
    qtbot.waitUntil(
        lambda: properties_view.findChild(QLineEdit, "marker_size_edit") is None
    )
    assert properties_view.findChild(QLineEdit, "marker_size_edit") is None
    assert isinstance(plot_node.plot_properties, LinePlotProperties)
    assert plot_node.plot_properties.plot_type == PlotType.LINE

    # 2. Change plot type to SCATTER using the UI
    plot_type_combo = properties_view.findChild(QComboBox, "plot_type_combo")
    assert plot_type_combo is not None
    plot_type_combo.setCurrentText(PlotType.SCATTER.value)
    qtbot.waitUntil(
        lambda: isinstance(plot_node.plot_properties, ScatterPlotProperties)
    )

    # 3. Assert UI rebuild for ScatterPlot (marker_size_edit exists)
    qtbot.waitUntil(
        lambda: properties_view.findChild(QLineEdit, "marker_size_edit") is not None
    )
    marker_size_edit = properties_view.findChild(QLineEdit, "marker_size_edit")
    assert marker_size_edit is not None
    assert isinstance(plot_node.plot_properties, ScatterPlotProperties)
    assert plot_node.plot_properties.plot_type == PlotType.SCATTER


    # 4. Change plot type back to LINE using the UI
    plot_type_combo.setCurrentText(PlotType.LINE.value)
    qtbot.waitUntil(
        lambda: isinstance(plot_node.plot_properties, LinePlotProperties)
    )

    # 5. Assert UI rebuild for LinePlot (no marker_size_edit)
    qtbot.waitUntil(
        lambda: properties_view.findChild(QLineEdit, "marker_size_edit") is None
    )
    assert properties_view.findChild(QLineEdit, "marker_size_edit") is None
    assert isinstance(plot_node.plot_properties, LinePlotProperties)
    assert plot_node.plot_properties.plot_type == PlotType.LINE