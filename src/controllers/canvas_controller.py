import logging 
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
        self.logger = logging.getLogger(self.__class__.__name__) # Added logger
        self.logger.info("CanvasController initialized.") # Added log


        self.thread = None
        self.worker = None

        self._connect_events()

    def _connect_events(self):
        """
        Connects canvas signals to the appropriate handlers or dispatchers.
        Tool-related events are dispatched directly to the ToolManager.
        """
        self.logger.debug("Connecting canvas events.") # Added log
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
        self.logger.debug("Connected Matplotlib events to ToolManager.") # Added log


        # Connect data-related events
        self.view.fileDropped.connect(self.on_file_dropped)
        self.logger.debug("Connected fileDropped signal to on_file_dropped.") # Added log


    # --- Data Loading ---

    def _convert_qt_scene_to_mpl_figure_coords(
        self, scene_pos: QPointF
    ) -> tuple[float, float]:
        canvas_width = self.canvas.width()
        canvas_height = self.canvas.height()
        if canvas_width == 0 or canvas_height == 0:
            self.logger.warning("Canvas has zero width or height. Cannot convert scene coordinates.") # Added log
            return -1.0, -1.0
        x_ratio = scene_pos.x() / canvas_width
        y_ratio_from_top = scene_pos.y() / canvas_height
        y_ratio_from_bottom = 1.0 - y_ratio_from_top
        self.logger.debug(f"Converted scene_pos {scene_pos} to figure coords ({x_ratio}, {y_ratio_from_bottom}).") # Added log
        return (x_ratio, y_ratio_from_bottom)

    def on_file_dropped(self, file_path: str, scene_pos: QPointF):
        """
        Handles the file drop event, finds the target node, and starts the
        data loading process.
        """
        self.logger.info(f"File dropped: {file_path} at scene position {scene_pos}.") # Added log
        if not file_path.lower().endswith(".csv"):
            self.logger.warning(f"Dropped file '{file_path}' is not a CSV. Ignoring.") # Added log
            return

        fig_coords = self._convert_qt_scene_to_mpl_figure_coords(scene_pos)
        node = self.model.get_node_at(fig_coords)

        if node and isinstance(node, PlotNode):
            self.logger.info(f"Dropped file '{file_path}' onto PlotNode '{node.name}' (ID: {node.id}).") # Added log
            self.load_data_into_node(file_path, node)
        else:
            self.logger.warning(f"Dropped file '{file_path}' did not hit a PlotNode at figure coordinates {fig_coords}. Ignoring.") # Added log


    def load_data_into_node(self, file_path: str, node: PlotNode):
        """
        Loads data from a file into a specific PlotNode using a background thread.
        This method is separate from the drop event handler to improve testability.
        """
        self.logger.info(f"Starting background data load for '{file_path}' into PlotNode '{node.name}' (ID: {node.id}).") # Added log
        self.thread = QThread()
        self.worker = DataLoader()
        self.worker.moveToThread(self.thread)

        # Pass the file path and the target node to the worker
        self.thread.started.connect(lambda: self.worker.process_data(file_path, node))
        self.logger.debug(f"DataLoader worker assigned to thread for file: {file_path}.") # Added log


        self.worker.dataReady.connect(self.on_data_ready)
        self.worker.errorOccurred.connect(self.on_data_load_error)

        # Clean up the thread when the worker is finished
        self.worker.dataReady.connect(self.thread.quit)
        self.worker.errorOccurred.connect(self.thread.quit)
        self.thread.finished.connect(self.thread.deleteLater)

        self.thread.start()
        self.logger.debug("Data loading thread started.") # Added log


    def on_data_ready(self, dataframe, node: PlotNode):
        """
        Slot to receive the loaded data and update the model.
        Also sets a default plot mapping, updating existing properties if necessary.
        """
        self.logger.info(f"Data ready for PlotNode '{node.name}' (ID: {node.id}). DataFrame shape: {dataframe.shape}.")
        if node in self.model.scene_root.children:
            node.data = dataframe
            self.logger.debug(f"Data assigned to PlotNode '{node.name}'.")

            # Ensure plot_properties exist, creating defaults if necessary
            if not node.plot_properties:
                node.plot_properties = LinePlotProperties(title=node.name) # Create a basic one if not existing
                self.logger.debug(f"Created basic PlotProperties for '{node.name}' as none existed.")
            
            # Now, update plot_properties with default column mappings if the dataframe has enough columns
            if dataframe.shape[1] >= 2:
                col1 = dataframe.columns[0]
                col2 = dataframe.columns[1]
                
                # Check if plot_mapping is already set or if it's the default empty one
                if node.plot_properties.plot_mapping.x is None and not node.plot_properties.plot_mapping.y:
                    node.plot_properties.plot_mapping = PlotMapping(x=col1, y=[col2])
                    node.plot_properties.xlabel = col1
                    node.plot_properties.ylabel = col2
                    self.logger.info(f"Default plot mapping set for '{col1}' and '{col2}' on '{node.name}'.")
                else:
                    self.logger.debug(f"PlotNode '{node.name}' already has a custom plot mapping. Skipping default mapping.")
            else:
                self.logger.warning(f"PlotNode '{node.name}' has insufficient columns ({dataframe.shape[1]}) for default plot mapping.")

            self.model.modelChanged.emit()
            self.logger.debug(f"modelChanged signal emitted after data load for '{node.name}'.")
        else:
            self.logger.warning(f"Data ready for node '{node.name}' (ID: {node.id}) but it's no longer in the scene_root's children. Data not assigned.")


    def on_data_load_error(self, error_message):
        self.logger.error(f"Error loading data: {error_message}", exc_info=True) # Changed print to log
