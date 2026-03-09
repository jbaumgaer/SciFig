import logging
from pathlib import Path

from PySide6.QtCore import QObject, QThread, Signal

from src.models.application_model import ApplicationModel
from src.models.nodes.plot_node import PlotNode
from src.processing.data_loader import DataLoader
from src.services.event_aggregator import EventAggregator
from src.shared.events import Events


class DataService(QObject):
    """
    A pure asynchronous service for loading scientific data.
    Listens for file requests and notifies the system when data is ready.
    Has NO direct dependency on theming or commands.
    """

    # Internal signal to bridge data from background thread to main thread
    # Parameters: dataframe, node, file_path, thread
    data_ready_internal = Signal(object, object, object, object)

    def __init__(
        self,
        model: ApplicationModel,
        event_aggregator: EventAggregator,
    ):
        super().__init__()
        self._model = model
        self._event_aggregator = event_aggregator
        self.logger = logging.getLogger(self.__class__.__name__)

        # Current active loading tasks: node_id -> (thread, worker)
        self._active_tasks: dict[str, tuple[QThread, DataLoader]] = {}

        # Connect internal signal to the handler.
        # Since DataService lives in the main thread, any signal emitted from 
        # a background thread will be automatically queued.
        self.data_ready_internal.connect(self._on_data_ready)

    def handle_load_request(self, node_id: str, file_path: Path):
        """
        Starts a background thread to load the specified file.
        Published by: Events.APPLY_DATA_FILE_REQUESTED
        """
        self.logger.debug(
            f"Received load request for node {node_id} from {file_path}"
        )

        if not file_path.exists():
            self.logger.error(f"File not found: {file_path}")
            # TODO: Publish error event
            return

        if node_id in self._active_tasks:
            self.logger.warning(
                f"Load already in progress for node {node_id}."
            )
            return

        thread = QThread()
        worker = DataLoader()
        worker.moveToThread(thread)

        node = self._model.scene_root.find_node_by_id(node_id)
        if not (node and isinstance(node, PlotNode)):
            self.logger.error(
                f"Node {node_id} not found or not a PlotNode."
            )
            return

        # Setup worker execution
        thread.started.connect(lambda: worker.process_data(file_path, node))
        
        # When data is ready in the background thread, emit the internal signal.
        # This emission is thread-safe and will trigger _on_data_ready in the main thread.
        worker.dataReady.connect(
            lambda df, n: self.data_ready_internal.emit(df, n, file_path, thread)
        )
        worker.errorOccurred.connect(self._on_load_error)

        # Cleanup logic
        worker.errorOccurred.connect(thread.quit)
        thread.finished.connect(lambda: self._cleanup_task(node_id))

        # Ensure objects are deleted only AFTER the thread finishes
        thread.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)

        self._active_tasks[node_id] = (thread, worker)
        thread.start()

    def _on_data_ready(self, dataframe, node: PlotNode, file_path: Path, thread: QThread):
        """
        Publishes the raw result to the system.
        The actual model update and theming are handled by listeners (e.g. NodeController).
        """
        self.logger.debug(f"Data successfully loaded for node {node.id}")
        self._event_aggregator.publish(
            Events.NODE_DATA_LOADED,
            node_id=node.id,
            data=dataframe,
            file_path=file_path,
        )
        thread.quit()

    def _on_load_error(self, error_msg: str):
        self.logger.error(f"Load error: {error_msg}")

    def _cleanup_task(self, node_id: str):
        self.logger.debug(f"Cleaning up task for node {node_id}")
        if node_id in self._active_tasks:
            del self._active_tasks[node_id]
