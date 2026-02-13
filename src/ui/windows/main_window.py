from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QDockWidget,
    QFileDialog,
    QMainWindow,
    QMenu,
    QMenuBar,
    QToolBar,
)

from src.controllers.layout_controller import LayoutController
from src.controllers.node_controller import NodeController
from src.controllers.project_controller import ProjectController
from src.interfaces.project_io import ProjectActions, ProjectIOView
from src.models.application_model import ApplicationModel
from src.models.plots.plot_types import PlotType
from src.services.commands import CommandManager
from src.ui.builders.menu_bar_builder import MainMenuActions
from src.ui.builders.tool_bar_builder import ToolBarActions
from src.ui.factories.layout_ui_factory import LayoutUIFactory
from src.ui.factories.plot_properties_ui_factory import PlotPropertiesUIFactory
from src.ui.panels.side_panel import SidePanel
from src.ui.widgets.canvas_widget import CanvasWidget


class MainWindow(QMainWindow, ProjectIOView):
    """
    The main application window (View). It acts as the primary container for
    the application's UI components and implements the ProjectIOView protocol
    to provide UI services for file operations.
    """

    def __init__(
        self,
        model: ApplicationModel,
        project_actions: ProjectActions,
        project_controller: ProjectController, # TODO: Remove this once SidePanel is refactored
        layout_controller: LayoutController,
        node_controller: NodeController,
        command_manager: CommandManager,
        plot_types: list[PlotType],
        menu_bar: QMenuBar,
        main_menu_actions: MainMenuActions,
        tool_bar: QToolBar,
        tool_bar_actions: ToolBarActions,
        plot_properties_ui_factory: PlotPropertiesUIFactory,
        layout_ui_factory: LayoutUIFactory,
    ):
        super().__init__()
        self.setWindowTitle("SciFig - Data Analysis GUI")
        self.setGeometry(50, 50, 800, 600)

        # --- Store Dependencies ---
        self.model = model
        self.project_actions = project_actions
        # The concrete project_controller is temporarily kept for legacy
        # dependencies like SidePanel. It will be removed in a future refactoring.
        self.project_controller = project_controller
        self.layout_controller = layout_controller
        self.node_controller = node_controller
        self.command_manager = command_manager
        self.plot_types = plot_types
        self.plot_properties_ui_factory = plot_properties_ui_factory
        self._layout_ui_factory = layout_ui_factory
        self._layout_manager = layout_controller._layout_manager

        # --- Create UI Components ---
        self.canvas_widget = self._create_canvas()
        self.setCentralWidget(self.canvas_widget)

        self.side_panel_view, self.side_panel_dock = self._create_side_panel()

        self.menu_bar = menu_bar
        self.main_menu_actions = main_menu_actions
        self.setMenuBar(self.menu_bar)

        self.tool_bar = tool_bar
        self.tool_bar_actions = tool_bar_actions
        self.addToolBar(Qt.ToolBarArea.LeftToolBarArea, self.tool_bar)

        # --- Assign menu components for easier access ---
        self.file_menu: QMenu = self.main_menu_actions.file_menu
        # self.new_layout_action: QAction = self.main_menu_actions.new_layout_action
        self.new_file_action: QAction = self.main_menu_actions.new_file_action
        self.new_file_from_template_action: QAction = (
            self.main_menu_actions.new_file_from_template_action
        )
        self.open_project_action: QAction = self.main_menu_actions.open_project_action
        self.open_recent_projects_menu: QMenu = (
            self.main_menu_actions.open_recent_projects_menu
        )
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

    # --- Protocol Implementation: ProjectIOView ---

    def ask_for_open_path(self) -> Optional[Path]:
        """Opens the system 'Open File' dialog and returns the selected path."""
        file_path_str, _ = QFileDialog.getOpenFileName(
            self,
            "Open Project",
            "",
            "SciFig Project (*.sci)",
        )
        return Path(file_path_str) if file_path_str else None

    def ask_for_save_path(self) -> Optional[Path]:
        """Opens the system 'Save As' dialog and returns the selected path."""
        file_path_str, _ = QFileDialog.getSaveFileName(
            self,
            "Save Project As",
            "",
            "SciFig Project (*.sci)",
        )
        return Path(file_path_str) if file_path_str else None

    def ask_for_template_path(self, template_dir: Path) -> Optional[Path]:
        """Opens a file dialog to select a layout template."""
        file_path_str, _ = QFileDialog.getOpenFileName(
            self,
            "Open Layout Template",
            str(template_dir),
            "JSON Layouts (*.json);;All Files (*)",
        )
        return Path(file_path_str) if file_path_str else None

    # --- Private UI Creation Methods ---

    def _create_canvas(self) -> CanvasWidget:
        canvas = CanvasWidget(figure=self.model.figure, parent=self)
        return canvas

    def _create_side_panel(self) -> tuple[SidePanel, QDockWidget]:
        side_panel = SidePanel(
            model=self.model,
            node_controller=self.node_controller,
            layout_controller=self.layout_controller,
            plot_properties_ui_factory=self.plot_properties_ui_factory,
            layout_ui_factory=self._layout_ui_factory,
            project_controller=self.project_controller, # Still uses the old concrete controller
        )
        dock = QDockWidget(self)
        dock.setObjectName("SidePanel")
        dock.setWidget(side_panel)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock)
        return side_panel, dock

    def show_side_panel(self):
        """Makes the side panel dock widget visible and raises it to the top."""
        if self.side_panel_dock:
            self.side_panel_dock.show()
            self.side_panel_dock.raise_()
