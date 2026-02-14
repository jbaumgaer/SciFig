import json
import logging
import tempfile
import zipfile
from pathlib import Path
from typing import Optional


from src.interfaces.project_io import (
    ProjectActions,
    ProjectLifecycle,
    ProjectIOView,
)
from src.interfaces.ui_providers import RecentFilesProvider
from src.models.nodes.scene_node import node_factory
from src.services.commands.command_manager import CommandManager
from src.services.layout_manager import LayoutManager

RECENT_FILES_KEY = "recentFiles"


class ProjectController(ProjectActions, RecentFilesProvider):
    """
    Acts as the Presenter in an MVP pattern for all project I/O operations.
    """

    def __init__(
        self,
        lifecycle: ProjectLifecycle,
        view: ProjectIOView,
        command_manager: CommandManager,
        layout_manager: LayoutManager,
        template_dir: Path,
        max_recent_files: int,
    ):
        super().__init__()
        self._lifecycle = lifecycle
        self._view = view
        self._command_manager = command_manager
        self._layout_manager = layout_manager
        self._template_dir = template_dir
        self._max_recent_files = max_recent_files
        self.logger = logging.getLogger(self.__class__.__name__)

        # self.settings = QSettings("SciFig", "DataAnalysisGUI") # TODO: This is actually important for setting recent files. I should make this part of the view again
        self.logger.info("ProjectController initialized.")

    # def set_view(self, view: ProjectIOView):
    #     """Allows for deferred injection of the View to break circular dependencies."""
    #     self._view = view

    def handle_new_project(self) -> None:
        self.logger.info("Handling new project action.")
        self._lifecycle.reset_state()

    def handle_new_from_template(self) -> None:
        self.logger.info("Handling 'New from Template' action.")
        
        template_path = self._view.ask_for_template_path(self._template_dir)
        if not template_path:
            self.logger.info("Template selection cancelled by user.")
            return
            
        try:
            with open(template_path, "r") as f:
                template_data = json.load(f)
            
            template_root = node_factory(template_data)
            # self._layout_manager.apply_layout_template(template_root)
            self._lifecycle.set_scene_root(template_root)
            self._lifecycle.file_path = None
        except (IOError, json.JSONDecodeError) as e:
            self.logger.error(f"Error loading template {template_path}: {e}", exc_info=True)

    def handle_open_project(self) -> None:
        self.logger.info("Handling 'Open...' project action.")
        path = self._view.ask_for_open_path()
        if not path:
            self.logger.info("Project open cancelled by user.")
            return
        self._open_from_path(path)

    # def create_new_layout(
    #     self, parent=None
    # ):  # Parent added for QFileDialog consistency
    #     """
    #     Clears the scene and populates it with new PlotNodes based on a layout template.
    #     Existing plot data is preserved and redistributed to the new layout slots.
    #     """
    #     self.logger.info("ProjectController.create_new_layout called.")
    #     self.logger.info("Creating a layout from template.")

    #     # 1. Extract existing plot data and properties
    #     existing_plot_states = []
    #     for node in self.model.scene_root.all_descendants():
    #         if isinstance(node, PlotNode) and node.data is not None:
    #             state = {
    #                 "data": node.data,
    #                 "plot_properties_dict": node.plot_properties.to_dict(
    #                     exclude_geometry=True
    #                 ),
    #             }
    #             existing_plot_states.append(state)
    #     self.logger.debug(
    #         f"Extracted existing plot states. Found {len(existing_plot_states)} plots."
    #     )

    #     # 2. Get default template name and path from ConfigService
    #     default_template_name = self._config_service.get(
    #         "layout.default_template", "2x2_default.json"
    #     )
    #     layout_templates_dir = Path(
    #         self._config_service.get("paths.layout_templates_dir", "configs/layouts")
    #     )
    #     template_path = layout_templates_dir / default_template_name
    #     self.logger.debug(f"Loading layout template: {template_path}")

    #     if not template_path.exists():
    #         self.logger.error(
    #             f"Layout template not found at {template_path}. Clearing scene and adding default plot."
    #         )
    #         self.model.clear_scene()
    #         self.model.add_node(PlotNode(name="Default Plot"))
    #         return

    #     # 3. Load and parse the JSON file
    #     try:
    #         with open(template_path, "r") as f:
    #             template_data = json.load(f)
    #     except json.JSONDecodeError as e:
    #         self.logger.error(
    #             f"Error parsing layout template {template_path}: {e}. Clearing scene and adding error plot.",
    #             exc_info=True,
    #         )
    #         self.model.clear_scene()
    #         self.model.add_node(PlotNode(name="Error Plot"))
    #         return

    #     # 4. Use scene_node.node_factory to deserialize JSON into new_layout_root_node
    #     new_layout_root_node = node_factory(template_data)
    #     self.logger.debug(
    #         f"Layout template deserialized. Root node: {new_layout_root_node.name} ({type(new_layout_root_node).__name__})"
    #     )

    #     # 5. Iterate PlotNodes in new_layout_root_node, assign extracted plot state
    #     old_plot_index = 0
    #     for new_slot_node in new_layout_root_node.all_descendants():
    #         if isinstance(new_slot_node, PlotNode):
    #             if old_plot_index < len(existing_plot_states):
    #                 old_plot_state = existing_plot_states[old_plot_index]

    #                 # Assign old data
    #                 new_slot_node.data = old_plot_state["data"]

    #                 # Update plot properties, preserving new slot's geometry
    #                 if new_slot_node.plot_properties:
    #                     new_slot_node.plot_properties.update_from_dict(
    #                         old_plot_state["plot_properties_dict"]
    #                     )
    #                 else:
    #                     old_plot_type = old_plot_state["plot_properties_dict"].get(
    #                         "plot_type", "line"
    #                     )
    #                     new_slot_node.plot_properties = (
    #                         BasePlotProperties.create_properties_from_plot_type(
    #                             PlotType(old_plot_type)
    #                         )
    #                     )
    #                     new_slot_node.plot_properties.update_from_dict(
    #                         old_plot_state["plot_properties_dict"]
    #                     )

    #                 self.logger.debug(
    #                     f"Plot data assigned to new slot: {new_slot_node.name}, PlotType: {new_slot_node.plot_properties.plot_type}"
    #                 )
    #                 old_plot_index += 1
    #             # Else: new_slot_node remains an empty slot with its template defaults

    #     # 6. Set new_layout_root_node as the scene_root
    #     self.model.set_scene_root(new_layout_root_node)
    #     self.logger.info(
    #         f"New layout applied to model. Scene root: {new_layout_root_node.name}."
    #     )
    #     self._layout_manager.reset_cached_configs() # Reset cached layout configs
        
    def open_project(self, file_path: Path) -> None:
        """Handles opening a specific project file, e.g., from a recent file list."""
        self.logger.info(f"Opening project directly from path: {file_path}")
        self._open_from_path(file_path)

    def handle_save_project(self) -> None:
        self.logger.info("Handling save project action.")
        path = self._lifecycle.file_path
        if path:
            self._save_to_path(path)
        else:
            self.handle_save_as_project()

    def handle_save_as_project(self) -> None:
        self.logger.info("Handling save as project action.")
        path = self._view.ask_for_save_path()
        if not path:
            self.logger.info("Project save-as cancelled by user.")
            return
        self._save_to_path(path)

    def get_recent_files(self) -> list[str]:
        return self.settings.value(RECENT_FILES_KEY, []) #TODO: This is not implemented properly right now. I would have to write this back to the config

    # --- Slots and Private Helpers ---

    def on_model_changed(self):
        """Called when the model emits a change signal. Can be used to update UI state."""
        self.logger.debug("Model changed signal received in ProjectController. Currently not doing anything.")

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
            self._add_to_recent_files(path)
            self.logger.info(f"Project saved to {path}")
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
            self._add_to_recent_files(path)
            self.logger.info(f"Project loaded from {path}")
        except (zipfile.BadZipFile, FileNotFoundError, json.JSONDecodeError, KeyError) as e:
            self.logger.error(f"Error opening project file '{path}': {e}", exc_info=True)

    def _add_to_recent_files(self, file_path: Path):
        recent_files = self.get_recent_files()
        file_path_str = str(file_path)
        if file_path_str in recent_files:
            recent_files.remove(file_path_str)
        recent_files.insert(0, file_path_str)
        
        
        del recent_files[self.max_recent_files:]
        self.settings.setValue(RECENT_FILES_KEY, recent_files)
        self.logger.debug(f"Added '{file_path_str}' to recent files.")
