import sys
import tempfile
from pathlib import Path

import matplotlib.figure
import pytest
from PySide6.QtWidgets import QApplication, QComboBox, QDockWidget, QLineEdit

from src.commands.command_manager import CommandManager
from src.controllers.canvas_controller import CanvasController
from src.controllers.main_controller import MainController
from src.controllers.tool_manager import ToolManager
from src.controllers.tools.selection_tool import SelectionTool
from src.models.application_model import ApplicationModel
from src.models.nodes.plot_node import PlotNode
from src.models.nodes.plot_properties import (
    AxesLimits,
    LinePlotProperties,
    PlotMapping,
)
from src.views.main_window import MainWindow
from src.views.renderer import Renderer


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
    # Instantiate MainController without a view
    main_controller = MainController(model=model)

    # Instantiate MainWindow with the main_controller
    view = MainWindow(model, main_controller, command_manager, plot_types)
    qtbot.addWidget(view)
    view.show()
    qtbot.waitExposed(view)

    tool_manager = ToolManager(model=model, command_manager=command_manager)
    selection_tool = SelectionTool(
        model=model,
        command_manager=command_manager,
        canvas_widget=view.canvas_widget,
    )
    tool_manager.add_tool(selection_tool)
    tool_manager.set_active_tool("selection")

    # The connections are now handled in main.py, so we need to simulate them here for the test context
    view.new_layout_action.triggered.connect(main_controller.create_new_layout)
    view.save_project_action.triggered.connect(lambda: main_controller.save_project(parent=view))
    view.open_project_action.triggered.connect(lambda: main_controller.open_project(parent=view))

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
    selection_tool.plot_double_clicked.connect(view.show_properties_panel)

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
        "canvas_controller": canvas_controller,
        "selection_tool": selection_tool,
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
    selection_tool = app_context["selection_tool"]

    initial_dock_count = len(view.findChildren(QDockWidget))
    assert initial_dock_count == 1

    plot1 = model.scene_root.children[0]
    model.set_selection([plot1])
    selection_tool.plot_double_clicked.emit(plot1)
    qtbot.waitUntil(lambda: view.properties_dock.isVisible(), timeout=1000)

    view.properties_dock.close()
    qtbot.waitUntil(lambda: not view.properties_dock.isVisible(), timeout=1000)

    plot2 = model.scene_root.children[1]
    model.set_selection([plot2])
    selection_tool.plot_double_clicked.emit(plot2)
    qtbot.waitUntil(lambda: view.properties_dock.isVisible(), timeout=1000)

    final_dock_count = len(view.findChildren(QDockWidget))
    assert final_dock_count == 1


def test_panel_correctly_updates_on_selection_change(app_context, qtbot):
    model = app_context["model"]
    view = app_context["view"]

    plot1 = model.scene_root.children[0]
    plot2 = model.scene_root.children[1]

    model.set_selection([plot1])
    qtbot.waitUntil(
        lambda: view.properties_view.findChild(QLineEdit, "title_edit").text()
        == "Plot One Title"
    )
    assert (
        view.properties_view.findChild(QLineEdit, "title_edit").text()
        == "Plot One Title"
    )

    model.set_selection([plot2])
    qtbot.waitUntil(
        lambda: view.properties_view.findChild(QLineEdit, "title_edit").text()
        == "Plot Two Title"
    )
    assert (
        view.properties_view.findChild(QLineEdit, "title_edit").text()
        == "Plot Two Title"
    )


def test_panel_shows_data_widgets_after_load(populated_plot_node, qtbot):
    app_context, plot_node = populated_plot_node
    model = app_context["model"]
    view = app_context["view"]

    model.set_selection([plot_node])

    def combo_boxes_appeared():
        return len(view.properties_view.findChildren(QComboBox)) == 3

    qtbot.waitUntil(combo_boxes_appeared, timeout=1000)

    combo_boxes_after_load = view.properties_view.findChildren(QComboBox)
    assert len(combo_boxes_after_load) == 3

    x_combo = combo_boxes_after_load[1]
    y_combo = combo_boxes_after_load[2]

    assert x_combo.count() == 3
    assert x_combo.itemText(0) == "Time"
    assert x_combo.itemText(1) == "Voltage"
    assert x_combo.itemText(2) == "Current"

    assert y_combo.count() == 3


def test_column_selector_updates_plot_mapping(populated_plot_node, qtbot):
    app_context, plot_node = populated_plot_node
    model = app_context["model"]
    view = app_context["view"]

    model.set_selection([plot_node])

    def combo_boxes_appeared():
        return len(view.properties_view.findChildren(QComboBox)) == 3

    qtbot.waitUntil(combo_boxes_appeared, timeout=1000)

    combo_boxes = view.properties_view.findChildren(QComboBox)
    x_combo = combo_boxes[1]
    y_combo = combo_boxes[2]

    x_combo.setCurrentText("Voltage")
    y_combo.setCurrentText("Current")

    def mapping_updated():
        mapping = plot_node.plot_properties.plot_mapping
        return mapping.x == "Voltage" and mapping.y == ["Current"]

    qtbot.waitUntil(mapping_updated, timeout=1000)

    final_mapping = plot_node.plot_properties.plot_mapping
    assert final_mapping.x == "Voltage"
    assert final_mapping.y == ["Current"]


def test_axis_limits_updates_model(app_context, qtbot):
    """
    Tests that changing the axis limit fields in the properties view correctly
    updates the axes_limits property in the model using the debounced timer.
    """
    model = app_context["model"]
    view = app_context["view"]
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


from unittest.mock import patch


def test_save_project_workflow(populated_plot_node, monkeypatch):
    """
    Tests the complete save workflow from UI trigger to file creation.
    """
    import io
    import json
    import zipfile

    import pandas as pd

    app_context, plot_node_with_data = populated_plot_node
    main_controller = app_context["main_controller"]

    # Use an in-memory buffer for the zip file
    zip_buffer = io.BytesIO()

    # 1. Mock the file dialog to return a dummy path
    monkeypatch.setattr(
        "src.controllers.main_controller.QFileDialog.getSaveFileName",
        lambda *args, **kwargs: ("test_project.sci", "SciFig Project (*.sci)"),
    )

    # 2. Patch zipfile.ZipFile to use our in-memory buffer
    with patch("zipfile.ZipFile", return_value=zipfile.ZipFile(zip_buffer, "w")) as mock_zip:
        # 3. Trigger the save action
        main_controller.save_project()

    # 4. Verify the contents of the in-memory zip file
    zip_buffer.seek(0)
    with zipfile.ZipFile(zip_buffer, "r") as zf:
        # Check that the project.json file exists and is valid
        assert "project.json" in zf.namelist()
        with zf.open("project.json") as f:
            project_data = json.load(f)

        assert project_data["version"] == "1.0"
        assert "scene_root" in project_data

        # Check that the parquet file for the populated node exists
        data_path = f"data/{plot_node_with_data.id}.parquet"
        assert data_path in zf.namelist()

        # Check that the data in the parquet file is correct
        with zf.open(data_path) as f:
            df = pd.read_parquet(f)
            assert df.shape == (3, 3)
            assert "Voltage" in df.columns


def test_open_project_workflow(app_context, qtbot, monkeypatch):
    """
    Tests the complete open workflow, including loading the model state.
    """
    import io
    import json
    import zipfile

    import pandas as pd

    original_model = app_context["model"]
    main_controller = app_context["main_controller"]

    # 1. Create a dummy .sci file in memory
    zip_buffer_out = io.BytesIO()
    with zipfile.ZipFile(zip_buffer_out, "w", zipfile.ZIP_DEFLATED) as zf:
        # Create dummy project.json
        project_data = {
            "version": "1.0",
            "scene_root": {
                "id": "root_id",
                "class_name": "GroupNode",
                "name": "root",
                "visible": True,
                "children": [
                    {
                        "id": "plot_id_open_test",
                        "class_name": "PlotNode",
                        "name": "Loaded Plot",
                        "visible": True,
                        "geometry": [0.1, 0.1, 0.8, 0.8],
                        "plot_properties": {
                            "title": "Loaded Title",
                            "xlabel": "X",
                            "ylabel": "Y",
                            "plot_type": "line",
                            "plot_mapping": {"x": "colX", "y": ["colY"]},
                            "axes_limits": {"xlim": [None, None], "ylim": [0.0, 10.0]},
                        },
                        "data_path": "data/plot_id_open_test.parquet",
                        "children": [],
                    }
                ],
            },
        }
        zf.writestr("project.json", json.dumps(project_data))

        # Create dummy parquet data
        dummy_df = pd.DataFrame({"colX": [1, 2], "colY": [3, 4]})
        with io.BytesIO() as parquet_buffer:
            dummy_df.to_parquet(parquet_buffer)
            zf.writestr("data/plot_id_open_test.parquet", parquet_buffer.getvalue())

    # 2. Mock QFileDialog to return the path to the dummy file (which we'll use a temp file for real)
    with tempfile.NamedTemporaryFile(suffix=".sci", delete=False) as tmp_file:
        tmp_file.write(zip_buffer_out.getvalue())
        temp_file_path = tmp_file.name

    monkeypatch.setattr(
        "src.controllers.main_controller.QFileDialog.getOpenFileName",
        lambda *args, **kwargs: (temp_file_path, "SciFig Project (*.sci)"),
    )

    # 3. Trigger the open action
    main_controller.open_project()

    # 4. Verify the model state is updated
    new_model = app_context["model"]
    assert new_model.scene_root.name == "root"
    assert len(new_model.scene_root.children) == 1
    loaded_plot = new_model.scene_root.children[0]
    assert isinstance(loaded_plot, PlotNode)
    assert loaded_plot.name == "Loaded Plot"
    assert loaded_plot.plot_properties.title == "Loaded Title"
    pd.testing.assert_frame_equal(loaded_plot.data, dummy_df)

    # Clean up the temporary file
    Path(temp_file_path).unlink()


def test_open_recent_projects_workflow(app_context, qtbot, monkeypatch):
    """
    Tests the 'Open Recent Projects' menu functionality.
    """

    main_controller = app_context["main_controller"]
    main_window = app_context["view"]

    main_controller = app_context["main_controller"]
    main_window = app_context["view"]

    # Mock the get_recent_files method of the main_controller
    with monkeypatch.context() as m:
        m.setattr(main_controller, "get_recent_files", lambda: ["/path/to/project1.sci", "/path/to/project2.sci"])

        # Move the patch.object block here
        with patch.object(main_controller, "open_project") as mock_open_project:
            # Trigger the aboutToShow signal of the recent projects menu
            main_window.open_recent_projects_menu.aboutToShow.emit()
            qtbot.wait(10) # Give events a chance to process

            # Verify menu population
            menu_actions = main_window.open_recent_projects_menu.actions()
            assert len(menu_actions) == 2
            assert menu_actions[0].text() == "/path/to/project1.sci"
            assert menu_actions[1].text() == "/path/to/project2.sci"

            menu_actions[0].trigger()
            mock_open_project.assert_called_once_with("/path/to/project1.sci", parent=main_window) # Also update parent argument

        # Test 'No Recent Projects' case
        m.setattr(main_controller, "get_recent_files", lambda: []) # Reset for this specific case
        main_window.open_recent_projects_menu.aboutToShow.emit()
        qtbot.wait(10)
        menu_actions = main_window.open_recent_projects_menu.actions()
        assert len(menu_actions) == 1
        assert menu_actions[0].text() == "No Recent Projects"
        assert not menu_actions[0].isEnabled()
