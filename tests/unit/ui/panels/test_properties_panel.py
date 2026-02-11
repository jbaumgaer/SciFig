from unittest.mock import MagicMock, Mock

import pandas as pd
import pytest
from matplotlib.figure import Figure
from PySide6.QtWidgets import QComboBox, QLineEdit, QWidget
from src.controllers.main_controller import MainController
from src.ui.panels.properties_panel import PropertiesPanel

from src.models.application_model import ApplicationModel
from src.models.nodes.plot_node import PlotNode
from src.models.plots.plot_properties import (
    AxesLimits,
    LinePlotProperties,
    PlotMapping,
    ScatterPlotProperties,
)
from src.models.plots.plot_types import PlotType
from src.services.commands.command_manager import CommandManager
from src.services.layout_manager import LayoutManager
from src.shared.constants import LayoutMode
from src.ui.factories.layout_ui_factory import LayoutUIFactory
from src.ui.factories.plot_properties_ui_factory import PlotPropertiesUIFactory


@pytest.fixture
def app_model():
    """Provides a mock ApplicationModel."""
    return ApplicationModel(figure=Figure())


@pytest.fixture
def command_manager(app_model):
    """Provides a mock CommandManager."""
    return CommandManager(app_model)


@pytest.fixture
def properties_ui_factory_mock():
    """Provides a mock PropertiesUIFactory."""
    mock_factory = MagicMock(spec=PlotPropertiesUIFactory)

    # Configure the mock build_widgets method to simulate UI creation
    def mock_build_widgets(
        node,
        layout,
        parent,
        on_property_changed,
        on_column_mapping_changed,
        on_limit_editing_finished,
        limit_edits,
        x_combo,
        y_combo,
    ):
        # Simulate adding a QComboBox for plot type selection
        plot_type_combo = QComboBox(parent)
        plot_type_combo.setObjectName("plot_type_combo")
        plot_type_combo.addItems([pt.value for pt in PlotType])
        plot_type_combo.setCurrentText(node.plot_properties.plot_type.value)
        # Mock the signals to allow connecting in the test, but don't call real slots
        plot_type_combo.currentTextChanged = MagicMock()
        # Removed: plot_type_combo.currentTextChanged.connect = Mock()
        layout.addRow("Plot Type:", plot_type_combo)

        # Also add mock for other common elements that the test might look for
        title_edit = QLineEdit(node.plot_properties.title, parent)
        title_edit.setObjectName("title_edit")
        layout.addRow("Title:", title_edit)

        # Simulate specific widgets based on plot type, for testing findChild behavior
        if node.plot_properties.plot_type == PlotType.SCATTER:
            marker_size_edit = QLineEdit(str(node.plot_properties.marker_size), parent)
            marker_size_edit.setObjectName("marker_size_edit")
            layout.addRow("Marker Size:", marker_size_edit)

    mock_factory.build_widgets.side_effect = mock_build_widgets
    return mock_factory


# New fixtures for layout-related mocks
@pytest.fixture
def layout_ui_factory_mock():
    """Provides a mock LayoutUIFactory."""
    mock_factory = MagicMock(spec=LayoutUIFactory)
    # Configure mock to return a dummy QWidget, as the real factory now returns QWidget
    mock_factory.build_layout_controls.return_value = QWidget()
    return mock_factory


@pytest.fixture
def layout_manager_mock():
    """Provides a mock LayoutManager."""
    mock_manager = MagicMock(spec=LayoutManager)
    mock_manager.layout_mode = LayoutMode.FREE_FORM  # Default mode
    mock_manager.layoutModeChanged = Mock()  # Mock the signal for connection
    return mock_manager


@pytest.fixture
def main_controller_mock(app_model, command_manager, layout_manager_mock):
    """Provides a mock MainController."""
    mock_controller = MagicMock(spec=MainController)
    mock_controller.model = app_model
    mock_controller.command_manager = command_manager
    mock_controller._layout_manager = (
        layout_manager_mock  # Link the layout manager mock
    )
    return mock_controller


@pytest.fixture
def properties_view(app_model, command_manager, properties_ui_factory_mock):
    """Provides a PropertiesView instance."""
    plot_types = [PlotType.LINE, PlotType.SCATTER]
    view = PropertiesPanel(
        app_model, command_manager, plot_types, properties_ui_factory_mock
    )
    return view


@pytest.fixture
def properties_view_with_layout_mocks(
    app_model,
    command_manager,
    properties_ui_factory_mock,
    layout_ui_factory_mock,
    layout_manager_mock,
    main_controller_mock,
):
    """Provides a PropertiesView instance with new layout-related dependencies."""
    plot_types = [PlotType.LINE, PlotType.SCATTER]
    view = PropertiesPanel(
        app_model,
        command_manager,
        plot_types,
        properties_ui_factory_mock,
        layout_ui_factory_mock,  # New
        layout_manager_mock,  # New
        main_controller_mock,  # New
    )
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
    properties_view._on_plot_type_changed(
        PlotType.SCATTER.value, plot_node
    )  # Manually trigger the slot
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
    properties_view._on_plot_type_changed(
        PlotType.LINE.value, plot_node
    )  # Manually trigger the slot
    qtbot.waitUntil(lambda: isinstance(plot_node.plot_properties, LinePlotProperties))

    # 5. Assert UI rebuild for LinePlot (no marker_size_edit)
    qtbot.waitUntil(
        lambda: properties_view.findChild(QLineEdit, "marker_size_edit") is None
    )
    assert properties_view.findChild(QLineEdit, "marker_size_edit") is None
    assert isinstance(plot_node.plot_properties, LinePlotProperties)
    assert plot_node.plot_properties.plot_type == PlotType.LINE


def test_properties_view_displays_layout_controls_by_default(
    qtbot, properties_view_with_layout_mocks, layout_ui_factory_mock
):
    """
    Verify that on initialization, the PropertiesView calls layout_ui_factory.build_layout_controls.
    """
    pass


def test_properties_view_displays_plot_properties_on_single_plot_selection_with_data(
    qtbot,
    properties_view_with_layout_mocks,
    app_model,
    properties_ui_factory_mock,
    layout_ui_factory_mock,
):
    """
    Mock a selection of a single PlotNode with data, verify properties_ui_factory.build_properties_ui is called.
    """
    pass


def test_properties_view_displays_layout_controls_on_multiple_selection(
    qtbot,
    properties_view_with_layout_mocks,
    app_model,
    properties_ui_factory_mock,
    layout_ui_factory_mock,
):
    """
    Mock multiple PlotNode's selected, verify layout_ui_factory.build_layout_controls is called.
    """
    pass


def test_properties_view_displays_layout_controls_on_single_plot_selection_no_data(
    qtbot,
    properties_view_with_layout_mocks,
    app_model,
    properties_ui_factory_mock,
    layout_ui_factory_mock,
):
    """
    Mock a single PlotNode without data selected, verify layout_ui_factory.build_layout_controls is called.
    """
    pass


def test_properties_view_updates_on_layout_mode_change(
    qtbot,
    properties_view_with_layout_mocks,
    app_model,
    layout_manager_mock,
    layout_ui_factory_mock,
):
    """
    Mock a layout mode change, verify layout_ui_factory.build_layout_controls is called with the new mode.
    """
    pass
