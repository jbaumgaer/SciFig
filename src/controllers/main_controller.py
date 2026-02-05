import json
import tempfile
import zipfile
from pathlib import Path
import logging # Added import

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QFileDialog

from src.models import ApplicationModel
from src.models.nodes import PlotNode
from src.models.nodes import scene_node 
from src.models.nodes.plot_properties import BasePlotProperties, PlotType 
from src.config_service import ConfigService

# MAX_RECENT_FILES = 10 
RECENT_FILES_KEY = "recentFiles" 


class MainController:
    """
    Manages application-level logic and orchestrates the other components.
    Connects main window UI actions to model-updating logic.
    """

    def __init__(self, model: ApplicationModel, config_service: ConfigService): 
        self.model = model
        self._config_service = config_service 
        self.settings = QSettings(
            self._config_service.get("organization", "SciFig"),
            self._config_service.get("app_name", "DataAnalysisGUI")
        )
        self.logger = logging.getLogger(self.__class__.__name__) # Added logger
        self.logger.info("MainController initialized.") # Added log
        self.logger.debug(f"QSettings initialized with organization: {self._config_service.get('organization')}, application: {self._config_service.get('app_name')}") # Added log


    def create_new_layout(self):
        """
        Clears the scene and populates it with new PlotNodes based on a layout template.
        Existing plot data is preserved and redistributed to the new layout slots.
        """
        self.logger.info("MainController.create_new_layout called.")
        self.logger.info("Creating a layout from template.")

        # 1. Extract existing plot data and properties
        existing_plot_states = []
        for node in self.model.scene_root.all_descendants():
            if isinstance(node, PlotNode) and node.data is not None:
                state = {
                    "data": node.data,
                    "plot_properties_dict": node.plot_properties.to_dict(exclude_geometry=True)
                }
                existing_plot_states.append(state)
        self.logger.debug(f"Extracted existing plot states. Found {len(existing_plot_states)} plots.") # Added log

        # 2. Get default template name and path from ConfigService
        default_template_name = self._config_service.get("layout.default_template", "2x2_default.json")
        layout_templates_dir = Path(self._config_service.get("paths.layout_templates_dir", "configs/layouts"))
        template_path = layout_templates_dir / default_template_name
        self.logger.debug(f"Loading layout template: {template_path}") # Added log


        if not template_path.exists():
            self.logger.error(f"Layout template not found at {template_path}. Clearing scene and adding default plot.") # Changed print to log
            # Optionally, create a single default empty plot or raise an error
            # For now, if template not found, clear scene and add a single default plot node
            self.model.clear_scene()
            self.model.add_node(PlotNode(name="Default Plot"))
            return

        # 3. Load and parse the JSON file
        try:
            with open(template_path, 'r') as f:
                template_data = json.load(f)
        except json.JSONDecodeError as e:
            self.logger.error(f"Error parsing layout template {template_path}: {e}. Clearing scene and adding error plot.", exc_info=True) # Changed print to log
            self.model.clear_scene()
            self.model.add_node(PlotNode(name="Error Plot"))
            return

        # 4. Use scene_node.node_factory to deserialize JSON into new_layout_root_node
        new_layout_root_node = scene_node.node_factory(template_data)
        self.logger.debug(f"Layout template deserialized. Root node: {new_layout_root_node.name} ({type(new_layout_root_node).__name__})") # Added log


        # 5. Iterate PlotNodes in new_layout_root_node, assign extracted plot state
        old_plot_index = 0
        for new_slot_node in new_layout_root_node.all_descendants():
            if isinstance(new_slot_node, PlotNode):
                if old_plot_index < len(existing_plot_states):
                    old_plot_state = existing_plot_states[old_plot_index]
                    
                    # Assign old data
                    new_slot_node.data = old_plot_state["data"]
                    
                    # Update plot properties, preserving new slot's geometry
                    if new_slot_node.plot_properties: # Ensure it has plot_properties
                        new_slot_node.plot_properties.update_from_dict(old_plot_state["plot_properties_dict"])
                    else: # If new slot had no default properties, create new ones
                        # Create new properties of the type specified in the old state
                        old_plot_type = old_plot_state["plot_properties_dict"].get("plot_type", "line") # Use lowercase default
                        new_slot_node.plot_properties = BasePlotProperties.create_properties_from_plot_type(
                            PlotType(old_plot_type)
                        )
                        new_slot_node.plot_properties.update_from_dict(old_plot_state["plot_properties_dict"])

                    self.logger.debug(f"Plot data assigned to new slot: {new_slot_node.name}, PlotType: {new_slot_node.plot_properties.plot_type}") # Added log
                    old_plot_index += 1
                # Else: new_slot_node remains an empty slot with its template defaults

        # 6. Set new_layout_root_node as the scene_root
        self.model.set_scene_root(new_layout_root_node)
        self.logger.info(f"New layout applied to model. Scene root: {new_layout_root_node.name}.") # Added log

        # 7. Emit modelChanged (already done by set_scene_root)
        # self.model.modelChanged.emit() # Redundant due to set_scene_root

    def save_project(self, parent=None):
        """Saves the current project to a .sci file."""
        file_path, _ = QFileDialog.getSaveFileName(
            parent,
            "Save Project",
            "",
            "SciFig Project (*.sci)",
        )

        if not file_path:
            self.logger.info("Project save cancelled by user.") # Added log
            return
        
        self.logger.info(f"Saving project to: {file_path}") # Added log


        with tempfile.TemporaryDirectory() as temp_dir_str:
            temp_dir = Path(temp_dir_str)
            data_dir = temp_dir / "data"
            data_dir.mkdir()
            self.logger.debug(f"Temporary directory for save: {temp_dir}") # Added log


            # 1. Save all dataframes to parquet files
            for node in self.model.scene_root.all_descendants():
                if isinstance(node, PlotNode) and node.data is not None:
                    parquet_path = data_dir / f"{node.id}.parquet"
                    node.data.to_parquet(parquet_path)
                    self.logger.debug(f"Saved data for node {node.id} to {parquet_path}") # Added log

            # 2. Get the model dictionary (which now contains data_path)
            project_dict = self.model.to_dict()

            # 3. Save the project dictionary to project.json
            json_path = temp_dir / "project.json"
            with open(json_path, "w") as f:
                json.dump(project_dict, f, indent=4)
            self.logger.debug(f"Saved project metadata to {json_path}") # Added log


            # 4. Zip the contents of the temporary directory
            with zipfile.ZipFile(file_path, "w", zipfile.ZIP_DEFLATED) as zf:
                for file_to_zip in temp_dir.rglob("*"):
                    zf.write(file_to_zip, file_to_zip.relative_to(temp_dir))
            self.logger.debug(f"Zipped project contents to {file_path}") # Added log


            self._add_to_recent_files(file_path)
            self.logger.info(f"Project saved to {file_path}") # Changed print to log

    def open_project(self, file_path: str | None = None, parent=None):
        """Opens a .sci project file."""
        if not file_path:
            file_path, _ = QFileDialog.getOpenFileName(
                parent,
                "Open Project",
                "",
                "SciFig Project (*.sci)",
            )

        if not file_path:
            self.logger.info("Project open cancelled by user.") # Added log
            return
        
        self.logger.info(f"Opening project from: {file_path}") # Added log


        try:
            with tempfile.TemporaryDirectory() as temp_dir_str:
                temp_dir = Path(temp_dir_str)
                self.logger.debug(f"Temporary directory for open: {temp_dir}") # Added log


                # Unzip the file
                with zipfile.ZipFile(file_path, "r") as zf:
                    zf.extractall(temp_dir)
                self.logger.debug(f"Unzipped project contents to {temp_dir}") # Added log


                # Load the project.json
                json_path = temp_dir / "project.json"
                with open(json_path, "r") as f:
                    project_dict = json.load(f)
                self.logger.debug(f"Loaded project metadata from {json_path}") # Added log


                # Load the model from the dictionary
                self.model.load_from_dict(project_dict, temp_dir)

            self._add_to_recent_files(file_path)
            self.logger.info(f"Project loaded from {file_path}") # Changed print to log

        except (
            zipfile.BadZipFile,
            FileNotFoundError,
            json.JSONDecodeError,
            KeyError,
        ) as e:
            self.logger.error(f"Error opening project file '{file_path}': {e}", exc_info=True) # Changed print to log
            # In a real application, show an error dialog to the user
            # print(f"Error opening project file: {e}") # Removed print

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
        self.logger.debug(f"Added '{file_path}' to recent files. Current list: {recent_files}") # Added log

        with tempfile.TemporaryDirectory() as temp_dir_str:
            temp_dir = Path(temp_dir_str)
            data_dir = temp_dir / "data"
            data_dir.mkdir()

            # 1. Save all dataframes to parquet files
            for node in self.model.scene_root.all_descendants():
                if isinstance(node, PlotNode) and node.data is not None:
                    parquet_path = data_dir / f"{node.id}.parquet"
                    node.data.to_parquet(parquet_path)

            # 2. Get the model dictionary (which now contains data_path)
            project_dict = self.model.to_dict()

            # 3. Save the project dictionary to project.json
            json_path = temp_dir / "project.json"
            with open(json_path, "w") as f:
                json.dump(project_dict, f, indent=4)

            # 4. Zip the contents of the temporary directory
            with zipfile.ZipFile(file_path, "w", zipfile.ZIP_DEFLATED) as zf:
                for file_to_zip in temp_dir.rglob("*"):
                    zf.write(file_to_zip, file_to_zip.relative_to(temp_dir))

            self._add_to_recent_files(file_path)
            self.logger.info(f"Project saved to {file_path}")

    def open_project(self, file_path: str | None = None, parent=None):
        """Opens a .sci project file."""
        if not file_path:
            file_path, _ = QFileDialog.getOpenFileName(
                parent,
                "Open Project",
                "",
                "SciFig Project (*.sci)",
            )

        if not file_path:
            return

        try:
            with tempfile.TemporaryDirectory() as temp_dir_str:
                temp_dir = Path(temp_dir_str)

                # Unzip the file
                with zipfile.ZipFile(file_path, "r") as zf:
                    zf.extractall(temp_dir)

                # Load the project.json
                json_path = temp_dir / "project.json"
                with open(json_path, "r") as f:
                    project_dict = json.load(f)

                # Load the model from the dictionary
                self.model.load_from_dict(project_dict, temp_dir)

            self._add_to_recent_files(file_path)
            self.logger.info(f"Project loaded from {file_path}")

        except (
            zipfile.BadZipFile,
            FileNotFoundError,
            json.JSONDecodeError,
            KeyError,
        ) as e:
            self.logger.error(f"Error opening project file '{file_path}': {e}", exc_info=True)

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
