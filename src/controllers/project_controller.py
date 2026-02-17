import json
import logging
import tempfile
import zipfile
from pathlib import Path
from typing import Optional

from src.services.event_aggregator import EventAggregator
from src.shared.events import Events
from src.interfaces.project_io import ProjectLifecycle
from src.models.nodes.scene_node import node_factory
from src.services.commands.command_manager import CommandManager
from src.services.layout_manager import LayoutManager

RECENT_FILES_KEY = "recentFiles"


class ProjectController:
    """
    Acts as the Presenter in an MVP pattern for all project I/O operations,
    driven by the EventAggregator.
    """

    def __init__(
        self,
        lifecycle: ProjectLifecycle,
        command_manager: CommandManager,
        template_dir: Path,
        max_recent_files: int,
        event_aggregator: EventAggregator,
    ):
        super().__init__()
        self._lifecycle = lifecycle
        self._command_manager = command_manager
        self._template_dir = template_dir
        self._max_recent_files = max_recent_files
        self._event_aggregator = event_aggregator
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info("ProjectController initialized.")
        # TODO: The QSettings dependency for recent files needs to be handled
        # by a dedicated service or through the View via events.

    def get_template_names(self) -> list[str]:
        """Returns a list of available template file names."""
        if not self._template_dir.exists():
            return []
        return [f.stem for f in self._template_dir.glob("*.json")]

    # --- Event Handlers for UI Requests ---

    def handle_new_project(self) -> None:
        self.logger.info("Handling new project action.")
        self._lifecycle.reset_state()
        self._event_aggregator.publish(Events.PROJECT_WAS_RESET)
        self._event_aggregator.publish(Events.PROJECT_IS_DIRTY_CHANGED, is_dirty=False)

    def handle_new_from_template_request(self) -> None:
        self.logger.info("Handling 'New from Template' request.")
        self._event_aggregator.publish(
            Events.PROMPT_FOR_TEMPLATE_SELECTION_REQUESTED,
            templates=self.get_template_names(),
        )

    def handle_open_project_request(self) -> None:
        self.logger.info("Handling 'Open...' project request.")
        self._event_aggregator.publish(Events.PROMPT_FOR_OPEN_PATH_REQUESTED)

    def handle_save_project(self) -> None:
        self.logger.info("Handling save project action.")
        path = self._lifecycle.file_path
        if path:
            self._save_to_path(path)
        else:
            self.handle_save_as_project_request()

    def handle_save_as_project_request(self) -> None:
        self.logger.info("Handling save as project request.")
        self._event_aggregator.publish(Events.PROMPT_FOR_SAVE_AS_PATH_REQUESTED)
        
    def handle_open_recent_project(self, file_path: Path) -> None:
        """Handles opening a specific project file from the recent file list."""
        self.logger.info(f"Opening project directly from path: {file_path}")
        self._open_from_path(file_path)

    # --- Event Handlers for UI Responses (File Dialogs) ---

    def on_template_provided(self, template_name: Optional[str]) -> None:
        self.logger.info(f"Template provided: {template_name}")
        if not template_name:
            self.logger.info("Template selection cancelled by user.")
            return

        template_path = self._template_dir / f"{template_name}.json"
        try:
            with open(template_path, "r") as f:
                template_data = json.load(f)

            template_root = node_factory(template_data)
            self._lifecycle.set_scene_root(template_root)
            self._lifecycle.file_path = None
            self._event_aggregator.publish(Events.PROJECT_WAS_RESET)
            self._lifecycle.set_dirty(True) #TODO: I should use events instead
            self._event_aggregator.publish(Events.PROJECT_IS_DIRTY_CHANGED, is_dirty=True)
        except (IOError, json.JSONDecodeError) as e:
            self.logger.error(f"Error loading template {template_path}: {e}", exc_info=True)

    def on_open_path_provided(self, path: Optional[Path]) -> None:
        self.logger.info(f"Open path provided: {path}")
        if not path:
            self.logger.info("Project open cancelled by user.")
            return
        self._open_from_path(path)

    def on_save_as_path_provided(self, path: Optional[Path]) -> None:
        self.logger.info(f"Save As path provided: {path}")
        if not path:
            self.logger.info("Project save-as cancelled by user.")
            return
        self._save_to_path(path)

    # --- Private Helper Methods ---

    def _save_to_path(self, path: Path) -> None:
        self.logger.info(f"Saving project to: {path}")
        try:
            with tempfile.TemporaryDirectory() as temp_dir_str:
                temp_dir = Path(temp_dir_str)
                project_dict = self._lifecycle.as_dict()
                json_path = temp_dir / "project.json"
                with open(json_path, "w") as f:
                    json.dump(project_dict, f, indent=4)
                with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
                    zf.write(json_path, "project.json")
            self._lifecycle.file_path = path
            # self._add_to_recent_files(path) # TODO: Re-implement via settings service/event
            self.logger.info(f"Project saved to {path}")
            self._lifecycle.set_dirty(False)
            self._event_aggregator.publish(Events.PROJECT_IS_DIRTY_CHANGED, is_dirty=False)
        except (IOError, zipfile.BadZipFile, Exception) as e:
            self.logger.error(f"Error saving project to '{path}': {e}", exc_info=True)

    def _open_from_path(self, path: Path) -> None:
        self.logger.info(f"Opening project from: {path}")
        try:
            with tempfile.TemporaryDirectory() as temp_dir_str:
                temp_dir = Path(temp_dir_str)
                with zipfile.ZipFile(path, "r") as zf:
                    zf.extractall(temp_dir)
                json_path = temp_dir / "project.json"
                with open(json_path, "r") as f:
                    project_dict = json.load(f)
                self._lifecycle.load_from_state(project_dict, temp_dir)
            self._lifecycle.file_path = path
            # self._add_to_recent_files(path) # TODO: Re-implement via settings service/event
            self.logger.info(f"Project loaded from {path}")
            self._event_aggregator.publish(Events.PROJECT_OPENED, project_metadata={'file_path': str(path)})
            self._lifecycle.set_dirty(False)
            self._event_aggregator.publish(Events.PROJECT_IS_DIRTY_CHANGED, is_dirty=False)
        except (zipfile.BadZipFile, FileNotFoundError, json.JSONDecodeError, KeyError) as e:
            self.logger.error(f"Error opening project file '{path}': {e}", exc_info=True)

    # def _add_to_recent_files(self, file_path: Path):
    #     # This logic needs to be moved to a settings service or handled by the View
    #     recent_files = [] # self.get_recent_files()
    #     file_path_str = str(file_path)
    #     if file_path_str in recent_files:
    #         recent_files.remove(file_path_str)
    #     recent_files.insert(0, file_path_str)
    #
    #
    #     del recent_files[self.max_recent_files:]
    #     # self.settings.setValue(RECENT_FILES_KEY, recent_files)
    #     self.logger.debug(f"Added '{file_path_str}' to recent files.")
