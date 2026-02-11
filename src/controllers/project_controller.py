import json
import logging
import tempfile
import zipfile
from pathlib import Path

from PySide6.QtCore import QObject, QSettings
from PySide6.QtWidgets import QFileDialog, QWidget

from src.models.application_model import ApplicationModel
from src.models.nodes.plot_node import PlotNode
from src.models.nodes.scene_node import node_factory
from src.models.plots.plot_properties import BasePlotProperties, PlotType
from src.services.commands.command_manager import CommandManager
from src.services.config_service import ConfigService
from src.services.layout_manager import LayoutManager

RECENT_FILES_KEY = "recentFiles"


class ProjectController(QObject):
    def __init__(
        self,
        model: ApplicationModel,
        command_manager: CommandManager,
        config_service: ConfigService,
        layout_manager: LayoutManager,
    ):
        super().__init__()
        self.model = model
        self.command_manager = command_manager
        self._config_service = config_service
        self._layout_manager = layout_manager  # Injected for create_new_layout
        self.logger = logging.getLogger(self.__class__.__name__)
        self.settings = QSettings(
            self._config_service.get("organization", "SciFig"),
            self._config_service.get("app_name", "DataAnalysisGUI"),
        )
        self.logger.info("ProjectController initialized.")

    def create_new_layout(
        self, parent=None
    ):  # Parent added for QFileDialog consistency
        """
        Clears the scene and populates it with new PlotNodes based on a layout template.
        Existing plot data is preserved and redistributed to the new layout slots.
        """
        self.logger.info("ProjectController.create_new_layout called.")
        self.logger.info("Creating a layout from template.")

        # 1. Extract existing plot data and properties
        existing_plot_states = []
        for node in self.model.scene_root.all_descendants():
            if isinstance(node, PlotNode) and node.data is not None:
                state = {
                    "data": node.data,
                    "plot_properties_dict": node.plot_properties.to_dict(
                        exclude_geometry=True
                    ),
                }
                existing_plot_states.append(state)
        self.logger.debug(
            f"Extracted existing plot states. Found {len(existing_plot_states)} plots."
        )

        # 2. Get default template name and path from ConfigService
        default_template_name = self._config_service.get(
            "layout.default_template", "2x2_default.json"
        )
        layout_templates_dir = Path(
            self._config_service.get("paths.layout_templates_dir", "configs/layouts")
        )
        template_path = layout_templates_dir / default_template_name
        self.logger.debug(f"Loading layout template: {template_path}")

        if not template_path.exists():
            self.logger.error(
                f"Layout template not found at {template_path}. Clearing scene and adding default plot."
            )
            self.model.clear_scene()
            self.model.add_node(PlotNode(name="Default Plot"))
            return

        # 3. Load and parse the JSON file
        try:
            with open(template_path, "r") as f:
                template_data = json.load(f)
        except json.JSONDecodeError as e:
            self.logger.error(
                f"Error parsing layout template {template_path}: {e}. Clearing scene and adding error plot.",
                exc_info=True,
            )
            self.model.clear_scene()
            self.model.add_node(PlotNode(name="Error Plot"))
            return

        # 4. Use scene_node.node_factory to deserialize JSON into new_layout_root_node
        new_layout_root_node = node_factory(template_data)
        self.logger.debug(
            f"Layout template deserialized. Root node: {new_layout_root_node.name} ({type(new_layout_root_node).__name__})"
        )

        # 5. Iterate PlotNodes in new_layout_root_node, assign extracted plot state
        old_plot_index = 0
        for new_slot_node in new_layout_root_node.all_descendants():
            if isinstance(new_slot_node, PlotNode):
                if old_plot_index < len(existing_plot_states):
                    old_plot_state = existing_plot_states[old_plot_index]

                    # Assign old data
                    new_slot_node.data = old_plot_state["data"]

                    # Update plot properties, preserving new slot's geometry
                    if new_slot_node.plot_properties:
                        new_slot_node.plot_properties.update_from_dict(
                            old_plot_state["plot_properties_dict"]
                        )
                    else:
                        old_plot_type = old_plot_state["plot_properties_dict"].get(
                            "plot_type", "line"
                        )
                        new_slot_node.plot_properties = (
                            BasePlotProperties.create_properties_from_plot_type(
                                PlotType(old_plot_type)
                            )
                        )
                        new_slot_node.plot_properties.update_from_dict(
                            old_plot_state["plot_properties_dict"]
                        )

                    self.logger.debug(
                        f"Plot data assigned to new slot: {new_slot_node.name}, PlotType: {new_slot_node.plot_properties.plot_type}"
                    )
                    old_plot_index += 1
                # Else: new_slot_node remains an empty slot with its template defaults

        # 6. Set new_layout_root_node as the scene_root
        self.model.set_scene_root(new_layout_root_node)
        self.logger.info(
            f"New layout applied to model. Scene root: {new_layout_root_node.name}."
        )
        self._layout_manager.reset_cached_configs() # Reset cached layout configs

    def save_project(self, parent: QWidget):
        """Saves the current project to a .sci file."""
        file_path, _ = QFileDialog.getSaveFileName(
            parent,
            "Save Project",
            "",
            "SciFig Project (*.sci)",
        )

        if not file_path:
            self.logger.info("Project save cancelled by user.")
            return

        self.logger.info(f"Saving project to: {file_path}")

        try:
            with tempfile.TemporaryDirectory() as temp_dir_str:
                temp_dir = Path(temp_dir_str)
                data_dir = temp_dir / "data"
                data_dir.mkdir()
                self.logger.debug(f"Temporary directory for save: {temp_dir}")

                # 1. Save all dataframes to parquet files
                for node in self.model.scene_root.all_descendants():
                    if isinstance(node, PlotNode) and node.data is not None:
                        parquet_path = data_dir / f"{node.id}.parquet"
                        node.data.to_parquet(parquet_path)
                        self.logger.debug(
                            f"Saved data for node {node.id} to {parquet_path}"
                        )

                # 2. Get the model dictionary (which now contains data_path)
                project_dict = self.model.to_dict()

                # 3. Save the project dictionary to project.json
                json_path = temp_dir / "project.json"
                with open(json_path, "w") as f:
                    json.dump(project_dict, f, indent=4)
                self.logger.debug(f"Saved project metadata to {json_path}")

                # 4. Zip the contents of the temporary directory
                with zipfile.ZipFile(file_path, "w", zipfile.ZIP_DEFLATED) as zf:
                    for file_to_zip in temp_dir.rglob("*"):
                        zf.write(file_to_zip, file_to_zip.relative_to(temp_dir))
                self.logger.debug(f"Zipped project contents to {file_path}")

                self._add_to_recent_files(file_path)
                self.logger.info(f"Project saved to {file_path}")
        except (IOError, zipfile.BadZipFile, Exception) as e:
            self.logger.error(
                f"Error saving project to '{file_path}': {e}", exc_info=True
            )

    def open_project(self, file_path: str | None = None, parent: QWidget = None):
        """Opens a .sci project file."""
        if not file_path:
            file_path, _ = QFileDialog.getOpenFileName(
                parent,
                "Open Project",
                "",
                "SciFig Project (*.sci)",
            )

        if not file_path:
            self.logger.info("Project open cancelled by user.")
            return

        self.logger.info(f"Opening project from: {file_path}")

        try:
            with tempfile.TemporaryDirectory() as temp_dir_str:
                temp_dir = Path(temp_dir_str)
                self.logger.debug(f"Temporary directory for open: {temp_dir}")

                # Unzip the file
                with zipfile.ZipFile(file_path, "r") as zf:
                    zf.extractall(temp_dir)
                self.logger.debug(f"Unzipped project contents to {temp_dir}")

                # Load the project.json
                json_path = temp_dir / "project.json"
                with open(json_path, "r") as f:
                    project_dict = json.load(f)
                self.logger.debug(f"Loaded project metadata from {json_path}")

                # Load the model from the dictionary
                self.model.load_from_dict(project_dict, temp_dir)

            self._add_to_recent_files(file_path)
            self.logger.info(f"Project loaded from {file_path}")
            self._layout_manager.reset_cached_configs() # Reset cached layout configs

        except (
            zipfile.BadZipFile,
            FileNotFoundError,
            json.JSONDecodeError,
            KeyError,
        ) as e:
            self.logger.error(
                f"Error opening project file '{file_path}': {e}", exc_info=True
            )

    def get_recent_files(self) -> list[str]:
        """Returns the list of recent file paths."""
        return self.settings.value(RECENT_FILES_KEY, [])

    def _add_to_recent_files(self, file_path: str):
        """Adds a file path to the top of the recent files list."""
        recent_files = self.get_recent_files()

        # Remove if it already exists to avoid duplicates and move to top
        if file_path in recent_files:
            recent_files.remove(file_path)

        # Add to the top
        recent_files.insert(0, file_path)

        # Trim the list using config value
        max_recent_files = self._config_service.get("layout.max_recent_files", 10)
        del recent_files[max_recent_files:]

        self.settings.setValue(RECENT_FILES_KEY, recent_files)
        self.logger.debug(
            f"Added '{file_path}' to recent files. Current list: {recent_files}"
        )
