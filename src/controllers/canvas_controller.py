from PySide6.QtCore import QObject, QPointF, QThread, Signal

from src.commands.command_manager import CommandManager
from src.models import ApplicationModel, PlotNode
from src.models.nodes.plot_properties import (
    AxesLimits,
    LinePlotProperties,
    PlotMapping,
)
from src.processing.data_loader import DataLoader
from src.views.canvas_widget import CanvasWidget

from .tool_manager import ToolManager


class CanvasController(QObject):
    """
    Manages user interactions on the canvas by delegating to a ToolManager.
    Also handles drag-and-drop data loading.
    """

    def __init__(
        self,
        model: ApplicationModel,
        canvas_widget: CanvasWidget,
        tool_manager: ToolManager,
        command_manager: CommandManager,
        parent: QObject | None = None,
    ):
        super().__init__(parent)
        self.model = model
        self.view = canvas_widget
        self.tool_manager = tool_manager
        self.command_manager = command_manager
        self.canvas = self.view.figure_canvas

        self.thread = None
        self.worker = None

        self._connect_events()

    def _connect_events(self):
        """
        Connects canvas signals to the appropriate handlers or dispatchers.
        Tool-related events are dispatched directly to the ToolManager.
        """
        # Connect tool events to the ToolManager
        self.canvas.mpl_connect(
            "button_press_event", self.tool_manager.dispatch_mouse_press_event
        )
        self.canvas.mpl_connect(
            "motion_notify_event", self.tool_manager.dispatch_mouse_move_event
        )
        self.canvas.mpl_connect(
            "button_release_event", self.tool_manager.dispatch_mouse_release_event
        )

        # Connect data-related events
        self.view.fileDropped.connect(self.on_file_dropped)

    # --- Data Loading ---

    def _convert_qt_scene_to_mpl_figure_coords(
        self, scene_pos: QPointF
    ) -> tuple[float, float]:
        canvas_width = self.canvas.width()
        canvas_height = self.canvas.height()
        if canvas_width == 0 or canvas_height == 0:
            return -1.0, -1.0
        x_ratio = scene_pos.x() / canvas_width
        y_ratio_from_top = scene_pos.y() / canvas_height
        y_ratio_from_bottom = 1.0 - y_ratio_from_top
        return (x_ratio, y_ratio_from_bottom)

    def on_file_dropped(self, file_path: str, scene_pos: QPointF):
        """
        Handles the file drop event, finds the target node, and starts the
        data loading process.
        """
        if not file_path.lower().endswith(".csv"):
            return

        fig_coords = self._convert_qt_scene_to_mpl_figure_coords(scene_pos)
        node = self.model.get_node_at(fig_coords)

        if node and isinstance(node, PlotNode):
            self.load_data_into_node(file_path, node)

    def load_data_into_node(self, file_path: str, node: PlotNode):
        """
        Loads data from a file into a specific PlotNode using a background thread.
        This method is separate from the drop event handler to improve testability.
        """
        self.thread = QThread()
        self.worker = DataLoader()
        self.worker.moveToThread(self.thread)

        # Pass the file path and the target node to the worker
        self.thread.started.connect(lambda: self.worker.process_data(file_path, node))

        self.worker.dataReady.connect(self.on_data_ready)
        self.worker.errorOccurred.connect(self.on_data_load_error)

        # Clean up the thread when the worker is finished
        self.worker.dataReady.connect(self.thread.quit)
        self.worker.errorOccurred.connect(self.thread.quit)
        self.thread.finished.connect(self.thread.deleteLater)

        self.thread.start()

    def on_data_ready(self, dataframe, node: PlotNode):
        """
        Slot to receive the loaded data and update the model.
        Also sets a default plot mapping.
        """
        if node in self.model.scene_root.children:
            node.data = dataframe

            # Set a default plot mapping if one doesn't exist
            if not node.plot_properties and dataframe.shape[1] >= 2:
                col1 = dataframe.columns[0]
                col2 = dataframe.columns[1]

                new_mapping = PlotMapping(x=col1, y=[col2])
                new_limits = AxesLimits(xlim=(None, None), ylim=(None, None))

                node.plot_properties = LinePlotProperties(
                    title=node.name,
                    xlabel=col1,
                    ylabel=col2,
                    plot_mapping=new_mapping,
                    axes_limits=new_limits,
                )

            self.model.modelChanged.emit()

    def on_data_load_error(self, error_message):
        print(f"Error loading data: {error_message}")
