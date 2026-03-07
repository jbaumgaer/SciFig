from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QDockWidget,
    QFileDialog,
    QInputDialog,
    QMenuBar,
    QToolBar,
    QVBoxLayout,
    QWidget,
)
from qframelesswindow import FramelessMainWindow, StandardTitleBar

from src.services.event_aggregator import EventAggregator
from src.shared.events import Events
from src.shared.geometry import Rect
from src.ui.builders.menu_bar_builder import MainMenuActions
from src.ui.builders.ribbon_bar_builder import RibbonActions
from src.ui.builders.tool_bar_builder import ToolBarActions
from src.ui.panels.side_panel import SidePanel
from src.ui.widgets.canvas_widget import CanvasWidget
from src.ui.widgets.ribbon_bar import RibbonBar


class MainWindow(FramelessMainWindow):
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
        self.setTitleBar(StandardTitleBar(self))
        self.titleBar.setIcon(QIcon("src/assets/icons/menu/insert/plots/Line.svg"))
        
        self.setWindowTitle("SciFig")
        self.setGeometry(50, 50, 800, 700)

        self._event_aggregator = event_aggregator

        self.side_panel_view, self.side_panel_dock = self._add_side_panel(side_panel)

        self.menu_bar = menu_bar
        self.main_menu_actions = main_menu_actions
        
        # Configure and integrate menu bar into title bar
        self.menu_bar.setNativeMenuBar(False)
        self.menu_bar.setObjectName("IntegratedMenuBar")
        self.titleBar.titleLabel.hide()
        self.titleBar.hBoxLayout.insertWidget(2, self.menu_bar)

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

        # Fix layout overlap by pushing content down below the title bar
        title_bar_height = self.titleBar.height() if self.titleBar.height() > 0 else self.titleBar.sizeHint().height()
        self.setContentsMargins(0, title_bar_height, 0, 0)
        self.titleBar.raise_()

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
            Events.SHOW_ADD_PLOT_DIALOG_REQUESTED, self._on_show_add_plot_dialog_request
        )
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

    # --- Event Handlers for UI Services ---

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
        """Opens a dialog to select a layout template."""
        if not templates:
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
        """Opens a file dialog for selecting data for a specific node."""
        file_path_str, _ = QFileDialog.getOpenFileName(
            self, "Select Data File for Node", "", "Data Files (*.csv *.tsv *.txt)"
        )
        path = Path(file_path_str) if file_path_str else None
        self._event_aggregator.publish(
            Events.PATH_PROVIDED_FOR_NODE_DATA_OPEN, node_id=node_id, path=path
        )

    def _on_show_add_plot_dialog_request(self, center_pos: tuple[float, float]):
        """Shows a dialog to get dimensions for a new plot and requests its creation."""
        width, ok_w = QInputDialog.getDouble(
            self, "Add Plot", "Width (0.0 to 1.0):", 0.4, 0.01, 1.0, 3
        )
        if not ok_w:
            return

        height, ok_h = QInputDialog.getDouble(
            self, "Add Plot", "Height (0.0 to 1.0):", 0.4, 0.01, 1.0, 3
        )
        if not ok_h:
            return

        # Calculate Rect centered at center_pos
        rect = Rect.from_center(center_pos[0], center_pos[1], width, height)
        # Clamp to figure bounds
        rect = rect.clamp_to_bounds(0, 0, 1, 1)

        self._event_aggregator.publish(Events.ADD_PLOT_REQUESTED, geometry=rect)

    def _on_window_title_data_ready(self, title: str, is_dirty: bool):
        """Passively updates the window title."""
        self.setWindowModified(is_dirty)
        self.setWindowTitle(title)

    def _add_side_panel(self, side_panel: SidePanel):
        """Integrates the side panel into a dock widget."""
        dock = QDockWidget(self)
        dock.setObjectName("SidePanel")
        dock.setWidget(side_panel)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock)
        if dock:
            dock.show()
            dock.raise_()
        return side_panel, dock
