import sys

from matplotlib.figure import Figure
from PySide6.QtWidgets import QApplication

from src.commands.command_manager import CommandManager
from src.controllers.canvas_controller import CanvasController
from src.controllers.main_controller import MainController
from src.controllers.tool_manager import ToolManager
from src.controllers.tools.selection_tool import SelectionTool
from src.models.application_model import ApplicationModel
from src.views.main_window import MainWindow
from src.views.renderer import Renderer


def setup_application():
    """
    Creates and wires up all the core components of the application.
    This function is used by both the main entry point and the test suite.
    """
    # The QApplication instance is managed separately to avoid creating multiple
    # instances during testing.
    app = QApplication.instance() or QApplication(sys.argv)

    # 1. Create the figure, model, and command manager
    figure = Figure(figsize=(8.5, 6), dpi=150)
    model = ApplicationModel(figure=figure)
    command_manager = CommandManager(model=model)

    # 2. Create the main view and controller
    renderer = Renderer()
    plot_types = list(renderer.plotting_strategies.keys())
    """TODO: This is a bit of a hack to get the available plot types from the renderer. 
    We should probably have a more explicit way to manage this list in the model
    or a dedicated registry class."""

    main_controller = MainController(model=model)
    view = MainWindow(model, main_controller, command_manager, plot_types)

    # Connect main window actions to controller slots
    #TODO: Does this scale for more actions?
    view.new_layout_action.triggered.connect(main_controller.create_new_layout)
    view.save_project_action.triggered.connect(lambda: main_controller.save_project(parent=view))
    view.open_project_action.triggered.connect(lambda: main_controller.open_project(parent=view))

    # 3. Instantiate Tools and Manager
    tool_manager = ToolManager(model=model, command_manager=command_manager)
    selection_tool = SelectionTool(
        model=model,
        command_manager=command_manager,
        canvas_widget=view.canvas_widget,
    )
    tool_manager.add_tool(selection_tool)
    tool_manager.set_active_tool("selection")

    # 4. Create other controllers
    canvas_controller = CanvasController(
        model=model,
        canvas_widget=view.canvas_widget,
        tool_manager=tool_manager,
        command_manager=command_manager,
    )

    # 5. Redraw Callback
    def redraw_callback():
        renderer.render(view.canvas_widget.figure, model.scene_root, model.selection)
        view.canvas_widget.figure_canvas.draw()

    # 6. Connect signals to slots
    model.modelChanged.connect(redraw_callback)
    model.selectionChanged.connect(redraw_callback)
    selection_tool.plot_double_clicked.connect(view.show_properties_panel)

    # Return a dictionary of the core components for tests to use
    return {
        "app": app,
        "model": model,
        "view": view,
        "command_manager": command_manager,
        "main_controller": main_controller,
        "canvas_controller": canvas_controller
    }

def main():
    """The main entry point for the application."""
    context = setup_application()
    view = context["view"]
    app = context["app"]

    view.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
