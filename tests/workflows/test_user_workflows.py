import tempfile
from pathlib import Path

import pytest
from PySide6.QtWidgets import QComboBox, QDockWidget, QLineEdit

from main import setup_application
from src.models.nodes.plot_node import PlotNode
from src.models.nodes.plot_properties import (
    AxesLimits,
    PlotMapping,
    PlotProperties,
)


@pytest.fixture
def app_context_with_plots(qtbot):
    """
    Sets up the application context with a main window and several plots.
    """
    context = setup_application()
    qtbot.addWidget(context["view"])  # Ensure widget is properly closed
    context["view"].show()  # Explicitly show the main window for tests

    # Add a few default plots for testing interaction between them
    plot_node1 = PlotNode(name="Plot 1")
    plot_node2 = PlotNode(name="Plot 2")

    # Set initial properties for easier testing of updates
    plot_node1.plot_properties = PlotProperties(
        title="Plot One Title",
        xlabel="",
        ylabel="",
        plot_mapping=PlotMapping(x=None, y=[]),
        axes_limits=AxesLimits(xlim=(None, None), ylim=(None, None)),
    )
    plot_node2.plot_properties = PlotProperties(
        title="Plot Two Title",
        xlabel="",
        ylabel="",
        plot_mapping=PlotMapping(x=None, y=[]),
        axes_limits=AxesLimits(xlim=(None, None), ylim=(None, None)),
    )

    context["model"].add_node(plot_node1)
    context["model"].add_node(plot_node2)

    return context


@pytest.fixture
def populated_plot_node(app_context_with_plots, qtbot):
    """
    Provides a plot node that has already been populated with data,
    and returns the core components needed for data tests.
    """
    model = app_context_with_plots["model"]
    canvas_controller = app_context_with_plots["canvas_controller"]
    plot_node = model.scene_root.children[0]

    csv_data = "Time;Voltage;Current\n1;10;1\n2;20;2\n3;30;3"
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as tmp:
        tmp.write(csv_data)
        file_path = str(Path(tmp.name))

    canvas_controller.load_data_into_node(file_path, plot_node)

    def data_is_loaded():
        return plot_node.data is not None

    qtbot.waitUntil(data_is_loaded, timeout=2000)

    # Yield the necessary components and the file path for cleanup
    yield app_context_with_plots, plot_node

    # Teardown: clean up the temporary file
    Path(file_path).unlink()


def test_reopening_panel_does_not_duplicate(app_context_with_plots, qtbot):
    """
    Regression test for the bug where closing and reopening the properties panel
    would cause duplicate, overlaid sidebars.
    """
    model = app_context_with_plots["model"]
    view = app_context_with_plots["view"]
    canvas_controller = app_context_with_plots["canvas_controller"]

    initial_dock_count = len(view.findChildren(QDockWidget))
    assert initial_dock_count == 1, "Expected one properties dock widget at start."

    # 1. Open panel, close it, then reopen it on another plot
    plot1 = model.scene_root.children[0]
    model.set_selection([plot1])
    canvas_controller.plotDoubleClicked.emit()
    qtbot.waitUntil(lambda: view.properties_dock.isVisible(), timeout=1000)

    view.properties_dock.close()
    qtbot.waitUntil(lambda: not view.properties_dock.isVisible(), timeout=1000)

    plot2 = model.scene_root.children[1]
    model.set_selection([plot2])
    canvas_controller.plotDoubleClicked.emit()
    qtbot.waitUntil(lambda: view.properties_dock.isVisible(), timeout=1000)

    # 2. Assert no duplicate docks were created
    final_dock_count = len(view.findChildren(QDockWidget))
    assert final_dock_count == 1, "Duplicate sidebars bug persists!"


def test_panel_correctly_updates_on_selection_change(app_context_with_plots, qtbot):
    """
    Tests that the PropertiesView correctly updates its displayed content
    when the selected plot node changes.
    """
    model = app_context_with_plots["model"]
    view = app_context_with_plots["view"]

    plot1 = model.scene_root.children[0]
    plot2 = model.scene_root.children[1]

    # 1. Select plot1 and check title
    model.set_selection([plot1])
    qtbot.waitUntil(
        lambda: view.properties_view.findChild(QLineEdit, "title_edit").text()
        == "Plot One Title"
    )
    assert (
        view.properties_view.findChild(QLineEdit, "title_edit").text()
        == "Plot One Title"
    )

    # 2. Select plot2 and check title
    model.set_selection([plot2])
    qtbot.waitUntil(
        lambda: view.properties_view.findChild(QLineEdit, "title_edit").text()
        == "Plot Two Title"
    )
    assert (
        view.properties_view.findChild(QLineEdit, "title_edit").text()
        == "Plot Two Title"
    )


def test_data_loading_updates_model(app_context_with_plots):
    # This test is now implicitly handled by the setup of populated_plot_node
    # Implicitly handled by populated_plot_node fixture; keeping for clarity.
    pass


def test_panel_shows_data_widgets_after_load(populated_plot_node, qtbot):
    """
    Tests that the properties view correctly shows data-related widgets (like
    column selectors) only after data has been loaded into a plot.
    """
    app_context, plot_node = populated_plot_node
    model = app_context["model"]
    view = app_context["view"]

    # 1. Select the node with data
    model.set_selection([plot_node])

    # 2. Wait for combo boxes to appear and assert they exist
    def combo_boxes_appeared():
        return len(view.properties_view.findChildren(QComboBox)) == 2

    qtbot.waitUntil(combo_boxes_appeared, timeout=1000)

    combo_boxes_after_load = view.properties_view.findChildren(QComboBox)
    assert (
        len(combo_boxes_after_load) == 2
    ), "Expected 2 column selectors after data is loaded."

    # 3. And check their content
    x_combo = combo_boxes_after_load[0]
    assert x_combo.count() == 3
    assert x_combo.itemText(0) == "Time"
    assert x_combo.itemText(1) == "Voltage"
    assert x_combo.itemText(2) == "Current"


def test_column_selector_updates_plot_mapping(populated_plot_node, qtbot):
    """
    Tests that changing the column selectors in the properties view correctly
    updates the plot_mapping property in the model.
    """
    app_context, plot_node = populated_plot_node
    model = app_context["model"]
    view = app_context["view"]

    # 1. Select the node to build the UI
    model.set_selection([plot_node])

    def combo_boxes_appeared():
        return len(view.properties_view.findChildren(QComboBox)) == 2

    qtbot.waitUntil(combo_boxes_appeared, timeout=1000)

    # 2. Get the combo boxes
    combo_boxes = view.properties_view.findChildren(QComboBox)
    x_combo = combo_boxes[0]
    y_combo = combo_boxes[1]

    # 3. Simulate user selecting new columns
    x_combo.setCurrentText("Voltage")
    y_combo.setCurrentText("Current")

    # 4. Wait for the model to be updated with the complete mapping
    def mapping_updated():
        mapping = plot_node.plot_properties.plot_mapping
        return mapping.x == "Voltage" and mapping.y == ["Current"]

    qtbot.waitUntil(mapping_updated, timeout=1000)

    # 5. Assert the final state
    final_mapping = plot_node.plot_properties.plot_mapping
    assert final_mapping.x == "Voltage"
    assert final_mapping.y == ["Current"]


def test_axis_limits_updates_model(app_context_with_plots, qtbot):
    """
    Tests that changing the axis limit fields in the properties view correctly
    updates the axes_limits property in the model using the debounced timer.
    """
    model = app_context_with_plots["model"]
    view = app_context_with_plots["view"]
    plot_node = model.scene_root.children[0]

    # 1. Select the plot node to build its UI
    model.set_selection([plot_node])

    # 2. Wait for the UI to build and find the QLineEdit widgets
    def editors_exist():
        return all(
            [
                view.properties_view.findChild(QLineEdit, "xlim_min_edit"),
                view.properties_view.findChild(QLineEdit, "xlim_max_edit"),
                view.properties_view.findChild(QLineEdit, "ylim_min_edit"),
                view.properties_view.findChild(QLineEdit, "ylim_max_edit"),
            ]
        )

    qtbot.waitUntil(editors_exist, timeout=1000)

    xlim_min_edit = view.properties_view.findChild(QLineEdit, "xlim_min_edit")
    xlim_max_edit = view.properties_view.findChild(QLineEdit, "xlim_max_edit")
    ylim_min_edit = view.properties_view.findChild(QLineEdit, "ylim_min_edit")
    ylim_max_edit = view.properties_view.findChild(QLineEdit, "ylim_max_edit")

    # 3. Simulate user input and trigger editingFinished
    xlim_min_edit.setText("10.5")
    xlim_min_edit.editingFinished.emit()  # Simulate user pressing Enter or moving focus
    xlim_max_edit.setText("99.5")
    xlim_max_edit.editingFinished.emit()
    ylim_min_edit.setText("-5")
    ylim_min_edit.editingFinished.emit()
    ylim_max_edit.setText("5")
    ylim_max_edit.editingFinished.emit()

    # 4. Wait for the model update to complete
    def limits_updated():
        limits = plot_node.plot_properties.axes_limits
        return limits.xlim == (10.5, 99.5) and limits.ylim == (-5.0, 5.0)

    qtbot.waitUntil(limits_updated, timeout=1000)

    # 5. Assert the final state
    final_limits = plot_node.plot_properties.axes_limits
    assert final_limits.xlim == (10.5, 99.5)
    assert final_limits.ylim == (-5.0, 5.0)
