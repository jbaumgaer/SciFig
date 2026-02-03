from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QDockWidget,
    QMainWindow,
    QMenu,
    QMenuBar,
    QWidget,
)

from src.builders.menu_bar_builder import MenuBarBuilder, MainMenuActions
from src.commands import CommandManager
from src.controllers.main_controller import MainController
from src.models import ApplicationModel
from src.models.nodes.plot_types import PlotType
from src.views.canvas_widget import CanvasWidget
from src.views.properties_view import PropertiesView


class MainWindow(QMainWindow):
    """
    The main application window (View). It acts as the primary container for
    the application's UI components, including the canvas and properties panel.
    """

    def __init__(self, model: ApplicationModel, main_controller: MainController, command_manager: CommandManager, plot_types: list[PlotType]):
        super().__init__()
        self.setWindowTitle("SciFig - Data Analysis GUI")
        self.setGeometry(50, 50, 800, 600)

        self.model = model
        self.command_manager = command_manager
        self.plot_types = plot_types

        # Now create the UI components
        self.canvas_widget = self._create_canvas()
        self.setCentralWidget(self.canvas_widget)

        self.properties_view, self.properties_dock = self._create_properties_dock()

        # Integrate MenuBarBuilder
        menu_builder = MenuBarBuilder(self, main_controller, self.command_manager)
        self.main_menu_actions: MainMenuActions = menu_builder.build()
        self.setMenuBar(self.main_menu_actions.menu_bar)

        # Assign menu components as direct attributes for easier access
        self.menu_bar: QMenuBar = self.main_menu_actions.menu_bar
        self.file_menu: QMenu = self.main_menu_actions.file_menu
        self.new_layout_action: QAction = self.main_menu_actions.new_layout_action
        self.new_file_action: QAction = self.main_menu_actions.new_file_action
        self.new_file_from_template_action: QAction = self.main_menu_actions.new_file_from_template_action
        self.open_project_action: QAction = self.main_menu_actions.open_project_action
        self.open_recent_projects_menu: QMenu = self.main_menu_actions.open_recent_projects_menu
        self.close_action: QAction = self.main_menu_actions.close_action
        self.save_project_action: QAction = self.main_menu_actions.save_project_action
        self.save_copy_action: QAction = self.main_menu_actions.save_copy_action
        self.export_figure_menu: QMenu = self.main_menu_actions.export_figure_menu
        self.export_vector_menu: QMenu = self.main_menu_actions.export_vector_menu
        self.export_raster_menu: QMenu = self.main_menu_actions.export_raster_menu
        self.export_svg_action: QAction = self.main_menu_actions.export_svg_action
        self.export_pdf_action: QAction = self.main_menu_actions.export_pdf_action
        self.export_eps_action: QAction = self.main_menu_actions.export_eps_action
        self.export_png_action: QAction = self.main_menu_actions.export_png_action
        self.export_tiff_action: QAction = self.main_menu_actions.export_tiff_action
        self.export_python_action: QAction = self.main_menu_actions.export_python_action
        self.exit_action: QAction = self.main_menu_actions.exit_action
        self.edit_menu: QMenu = self.main_menu_actions.edit_menu
        self.undo_action: QAction = self.main_menu_actions.undo_action
        self.redo_action: QAction = self.main_menu_actions.redo_action
        self.cut_action: QAction = self.main_menu_actions.cut_action
        self.copy_action: QAction = self.main_menu_actions.copy_action
        self.paste_action: QAction = self.main_menu_actions.paste_action
        self.colors_action: QAction = self.main_menu_actions.colors_action
        self.settings_action: QAction = self.main_menu_actions.settings_action

    def _create_canvas(self) -> CanvasWidget:
        canvas = CanvasWidget(figure=self.model.figure, parent=self)
        return canvas

    def _create_properties_dock(self) -> tuple[PropertiesView, QDockWidget]:
        properties_view = PropertiesView(
            model=self.model,
            command_manager=self.command_manager,
            plot_types=self.plot_types,
        )
        dock = QDockWidget("Properties", self)
        dock.setObjectName("Properties")
        dock.setWidget(properties_view)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock)
        return properties_view, dock

    def show_properties_panel(self):
        """Makes the properties dock widget visible and raises it to the top."""
        if self.properties_dock:
            self.properties_dock.show()
            self.properties_dock.raise_()