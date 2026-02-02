import sys

from matplotlib.figure import Figure
from PySide6.QtWidgets import QApplication

from src.builders.main_window_builder import MainWindowBuilder
from src.commands.command_manager import CommandManager
from src.controllers.canvas_controller import CanvasController
from src.controllers.main_controller import MainController
from src.controllers.tool_manager import ToolManager
from src.controllers.tools.selection_tool import SelectionTool
from src.models.application_model import ApplicationModel
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

    # 2. Use the MainWindowBuilder to create the main view
    builder = MainWindowBuilder(model, command_manager)
    view = (builder
            .build_canvas()
            .build_properties_dock()
            .build_menu()
            .get_window())

    # 3. Instantiate Renderer
    renderer = Renderer()

    # 4. Instantiate Tools and Manager
    tool_manager = ToolManager()
    selection_tool = SelectionTool(model=model, canvas=view.canvas_widget.figure_canvas)
    tool_manager.add_tool("selection", selection_tool)
    tool_manager.set_active_tool("selection")

    # 5. Create controllers
    main_controller = MainController(model=model, view=view)
    canvas_controller = CanvasController(
        model=model,
        canvas_widget=view.canvas_widget,
        tool_manager=tool_manager,
        command_manager=command_manager,
    )

    # 6. Redraw Callback
    def redraw_callback():
        renderer.render(view.canvas_widget.figure, model.scene_root, model.selection)
        view.canvas_widget.figure_canvas.draw()

    # 7. Connect signals to slots
    model.modelChanged.connect(redraw_callback)
    model.selectionChanged.connect(redraw_callback)
    canvas_controller.plotDoubleClicked.connect(view.show_properties_panel)

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
