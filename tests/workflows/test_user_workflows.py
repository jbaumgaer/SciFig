import tempfile
import sys
from pathlib import Path
import matplotlib.figure

import pytest
from PySide6.QtWidgets import QApplication, QComboBox, QDockWidget, QLineEdit

from src.models.application_model import ApplicationModel
from src.commands.command_manager import CommandManager
from src.views.main_window import MainWindow
from src.controllers.main_controller import MainController
from src.controllers.canvas_controller import CanvasController
from src.controllers.tool_manager import ToolManager
from src.controllers.tools.selection_tool import SelectionTool
from src.views.renderer import Renderer
from src.models.nodes.plot_node import PlotNode
from src.models.nodes.plot_properties import (
    AxesLimits,
    LinePlotProperties,
    PlotMapping,
)
from src.models.nodes.plot_types import PlotType


@pytest.fixture
def app_context(qtbot):
    """
    A pytest fixture that sets up the full application context with real
    components for integration testing.
    """
    app = QApplication.instance() or QApplication(sys.argv)

    figure = matplotlib.figure.Figure()
    model = ApplicationModel(figure=figure)
    command_manager = CommandManager(model=model)

    renderer = Renderer()
    plot_types = list(renderer.plotting_strategies.keys())
    view = MainWindow(model, command_manager, plot_types)
    qtbot.addWidget(view)
    view.show()
    qtbot.waitExposed(view)

    tool_manager = ToolManager()
    selection_tool = SelectionTool(model=model, canvas=view.canvas_widget.figure_canvas)
    tool_manager.add_tool("selection", selection_tool)
    tool_manager.set_active_tool("selection")

    main_controller = MainController(model=model, view=view)
    canvas_controller = CanvasController(
        model=model,
        canvas_widget=view.canvas_widget,
        tool_manager=tool_manager,
        command_manager=command_manager,
    )

    def redraw_callback():
        renderer.render(view.canvas_widget.figure, model.scene_root, model.selection)
        view.canvas_widget.figure_canvas.draw()

    model.modelChanged.connect(redraw_callback)
    model.selectionChanged.connect(redraw_callback)
    canvas_controller.plotDoubleClicked.connect(view.show_properties_panel)

    plot_node1 = PlotNode(name="Plot 1")
    plot_node2 = PlotNode(name="Plot 2")

    plot_node1.plot_properties = LinePlotProperties(
        title="Plot One Title",
        xlabel="",
        ylabel="",
        plot_mapping=PlotMapping(x=None, y=[]),
        axes_limits=AxesLimits(xlim=(None, None), ylim=(None, None)),
    )
    plot_node2.plot_properties = LinePlotProperties(
        title="Plot Two Title",
        xlabel="",
        ylabel="",
        plot_mapping=PlotMapping(x=None, y=[]),
        axes_limits=AxesLimits(xlim=(None, None), ylim=(None, None)),
    )

    model.add_node(plot_node1)
    model.add_node(plot_node2)

    return {
        "app": app,
        "model": model,
        "view": view,
        "command_manager": command_manager,
        "main_controller": main_controller,
        "canvas_controller": canvas_controller
    }


@pytest.fixture
def populated_plot_node(app_context, qtbot):
    """
    Provides a plot node that has already been populated with data,
    and returns the core components needed for data tests.
    """
    model = app_context["model"]
    canvas_controller = app_context["canvas_controller"]
    plot_node = model.scene_root.children[0]

    csv_data = "Time;Voltage;Current\n1;10;1\n2;20;2\n3;30;3"
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as tmp:
        tmp.write(csv_data)
        file_path = str(Path(tmp.name))

    canvas_controller.load_data_into_node(file_path, plot_node)

    def data_is_loaded():
        return plot_node.data is not None

    qtbot.waitUntil(data_is_loaded, timeout=2000)

    yield app_context, plot_node

    Path(file_path).unlink()


def test_reopening_panel_does_not_duplicate(app_context, qtbot):
    model = app_context["model"]
    view = app_context["view"]
    canvas_controller = app_context["canvas_controller"]

    initial_dock_count = len(view.findChildren(QDockWidget))
    assert initial_dock_count == 1

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

    final_dock_count = len(view.findChildren(QDockWidget))
    assert final_dock_count == 1