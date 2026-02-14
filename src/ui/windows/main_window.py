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

from src.interfaces.project_io import ProjectActions, ProjectIOView
from src.models.application_model import ApplicationModel
from src.models.plots.plot_types import PlotType
from src.services.commands import CommandManager
from src.ui.builders.menu_bar_builder import MainMenuActions
from src.ui.builders.tool_bar_builder import ToolBarActions
from src.ui.factories.layout_ui_factory import LayoutUIFactory
from src.ui.factories.plot_properties_ui_factory import PlotPropertiesUIFactory
from src.ui.panels import side_panel
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
        menu_bar: QMenuBar,
        main_menu_actions: MainMenuActions,
        tool_bar: QToolBar,
        tool_bar_actions: ToolBarActions,
        side_panel: SidePanel,
    ):
        super().__init__()
        self.setWindowTitle("SciFig - Data Analysis GUI")
        self.setGeometry(50, 50, 800, 600) #TODO: Inject these from the config service

        self.model = model
        self.project_actions = project_actions

        # --- Create UI Components ---

        self.side_panel_view, self.side_panel_dock = self._add_side_panel(side_panel)

        self.menu_bar = menu_bar
        self.main_menu_actions = main_menu_actions
        self.setMenuBar(self.menu_bar)

        self.tool_bar = tool_bar
        self.tool_bar_actions = tool_bar_actions
        self.addToolBar(Qt.ToolBarArea.LeftToolBarArea, self.tool_bar)

        self.canvas_widget: Optional[CanvasWidget] = None

    def set_canvas_widget(self, canvas_widget: CanvasWidget):
        """Sets the canvas_widget."""
        self.canvas_widget = canvas_widget
        self.setCentralWidget(self.canvas_widget)

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

    def _add_side_panel(self, side_panel: SidePanel):
        """Makes the side panel dock widget visible and raises it to the top."""
        dock = QDockWidget(self)
        dock.setObjectName("SidePanel")
        dock.setWidget(side_panel)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock)
        if dock:
            dock.show()
            dock.raise_()
        return side_panel, dock
