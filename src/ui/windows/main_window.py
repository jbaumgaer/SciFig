from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDockWidget,
    QFileDialog,
    QInputDialog,
    QMainWindow,
    QMenuBar,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from src.services.event_aggregator import EventAggregator
from src.shared.events import Events
from src.ui.builders.menu_bar_builder import MainMenuActions
from src.ui.builders.ribbon_bar_builder import RibbonActions
from src.ui.builders.tool_bar_builder import ToolBarActions
from src.ui.panels.side_panel import SidePanel
from src.ui.widgets.canvas_widget import CanvasWidget
from src.ui.widgets.ribbon_bar import RibbonBar


class MainWindow(QMainWindow):
    """
    The main application window (View). It acts as the primary container for
    the application's UI components and responds to events to provide UI
    services like file dialogs and window title updates.
    """

    def __init__(
        self,
        menu_bar: QMenuBar,
        main_menu_actions: MainMenuActions,
        ribbon_bar: RibbonBar,
        ribbon_actions: RibbonActions,
        tool_bar: QToolBar,
        tool_bar_actions: ToolBarActions,
        side_panel: SidePanel,
        event_aggregator: EventAggregator,
    ):
        super().__init__()
        self.setWindowTitle("SciFig")
        self.setGeometry(50, 50, 800, 700)  # Reverted to more standard size

        self._event_aggregator = event_aggregator

        self.side_panel_view, self.side_panel_dock = self._add_side_panel(side_panel)

        self.menu_bar = menu_bar
        self.main_menu_actions = main_menu_actions
        self.setMenuBar(self.menu_bar)

        self.ribbon_bar = ribbon_bar
        self.ribbon_actions = ribbon_actions

        # Central container for Ribbon and Canvas
        self.central_container = QWidget()
        self.main_layout = QVBoxLayout(self.central_container)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        self.main_layout.addWidget(self.ribbon_bar)

        self.setCentralWidget(self.central_container)

        self.tool_bar = tool_bar
        self.tool_bar_actions = tool_bar_actions
        self.addToolBar(Qt.ToolBarArea.LeftToolBarArea, self.tool_bar)

        self.canvas_widget: Optional[CanvasWidget] = None

        self._subscribe_to_events()
        self._connect_ribbon_controls()
        self._event_aggregator.publish(Events.WINDOW_TITLE_REQUESTED)

    def _connect_ribbon_controls(self):
        """Connects MenuBar actions to RibbonBar tab switching."""
        self.main_menu_actions.insert_tab_action.triggered.connect(
            lambda: self.ribbon_bar.setCurrentIndex(0)
        )
        self.main_menu_actions.design_tab_action.triggered.connect(
            lambda: self.ribbon_bar.setCurrentIndex(1)
        )
        self.main_menu_actions.layout_tab_action.triggered.connect(
            lambda: self.ribbon_bar.setCurrentIndex(2)
        )

    def _subscribe_to_events(self):
        """Subscribes to all relevant application events."""
        # --- Subscribe to UI service requests ---
        self._event_aggregator.subscribe(
            Events.PROMPT_FOR_OPEN_PATH_REQUESTED, self._prompt_for_open_path
        )
        self._event_aggregator.subscribe(
            Events.PROMPT_FOR_SAVE_AS_PATH_REQUESTED, self._prompt_for_save_as_path
        )
        self._event_aggregator.subscribe(
            Events.PROMPT_FOR_TEMPLATE_SELECTION_REQUESTED, self._prompt_for_template
        )
        self._event_aggregator.subscribe(
            Events.PROMPT_FOR_OPEN_PATH_FOR_NODE_DATA_REQUESTED,
            self._prompt_for_open_path_for_node_data,
        )
        self._event_aggregator.subscribe(
            Events.WINDOW_TITLE_DATA_READY, self._on_window_title_data_ready
        )

    def set_canvas_widget(self, canvas_widget: CanvasWidget):
        """Sets the canvas_widget."""
        self.canvas_widget = canvas_widget
        self.main_layout.addWidget(self.canvas_widget)

    # --- Event Handlers for UI Services (File Dialogs) ---

    def _prompt_for_open_path(self):
        """Opens the system 'Open File' dialog and publishes the result."""
        file_path_str, _ = QFileDialog.getOpenFileName(
            self, "Open Project", "", "SciFig Project (*.sci)"
        )
        path = Path(file_path_str) if file_path_str else None
        self._event_aggregator.publish(Events.PATH_PROVIDED_FOR_OPEN, path=path)

    def _prompt_for_save_as_path(self):
        """Opens the system 'Save As' dialog and publishes the result."""
        file_path_str, _ = QFileDialog.getSaveFileName(
            self, "Save Project As", "", "SciFig Project (*.sci)"
        )
        path = Path(file_path_str) if file_path_str else None
        self._event_aggregator.publish(Events.PATH_PROVIDED_FOR_SAVE_AS, path=path)

    def _prompt_for_template(self, templates: list[str]):
        """Opens a dialog to select a layout template and publishes the result."""
        if not templates:
            # Handle case where no templates are found if necessary
            return
        template_name, ok = QInputDialog.getItem(
            self, "New from Template", "Select a template:", templates, 0, False
        )
        if ok and template_name:
            self._event_aggregator.publish(
                Events.TEMPLATE_PROVIDED_FOR_NEW, template_name=template_name
            )
        else:
            self._event_aggregator.publish(
                Events.TEMPLATE_PROVIDED_FOR_NEW, template_name=None
            )

    def _prompt_for_open_path_for_node_data(self, node_id: str):
        """
        Opens a file dialog for selecting data for a specific node and publishes the result.
        """
        file_path_str, _ = QFileDialog.getOpenFileName(
            self, "Select Data File for Node", "", "Data Files (*.csv *.tsv *.txt)"
        )
        path = Path(file_path_str) if file_path_str else None
        self._event_aggregator.publish(
            Events.PATH_PROVIDED_FOR_NODE_DATA_OPEN, node_id=node_id, path=path
        )

    def _on_window_title_data_ready(self, title: str, is_dirty: bool):
        """
        Passively updates the window title and modified status from an event.
        """
        self.setWindowModified(is_dirty)
        self.setWindowTitle(title)

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
