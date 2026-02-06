import json
import logging
import tempfile
import zipfile
from pathlib import Path

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QFileDialog

from src.services.commands.batch_change_plot_geometry_command import (
    BatchChangePlotGeometryCommand,
)
from src.services.commands.command_manager import CommandManager
from src.services.config_service import ConfigService
from src.shared.constants import LayoutMode
from src.services.layout_manager import LayoutManager
from src.models.application_model import ApplicationModel
from src.models.layout.layout_config import GridConfig
from src.models.nodes.plot_node import PlotNode
from src.models.nodes.scene_node import node_factory
from src.models.plots.plot_properties import BasePlotProperties, PlotType

# MAX_RECENT_FILES is removed from here as it comes from config_service
RECENT_FILES_KEY = "recentFiles"


class MainController:
    """
    Manages application-level logic and orchestrates the other components.
    Connects main window UI actions to model-updating logic.
    """

    def __init__(self, model: ApplicationModel, config_service: ConfigService, layout_manager: LayoutManager, command_manager: CommandManager):
        self.model = model
        self._config_service = config_service
        self._layout_manager = layout_manager
        self.command_manager = command_manager # Store command manager for commands

        self.settings = QSettings(
            self._config_service.get("organization", "SciFig"),
            self._config_service.get("app_name", "DataAnalysisGUI")
        )
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info("MainController initialized.")
        self.logger.debug(f"QSettings initialized with organization: {self._config_service.get('organization')}, application: {self._config_service.get('app_name')}")

    def set_layout_mode(self, mode: LayoutMode):
        """
        Sets the application's layout mode via the LayoutManager.
        """
        self.logger.info(f"MainController received request to set layout mode to: {mode.value}")
        self._layout_manager.set_layout_mode(mode)

    def toggle_layout_mode(self, checked: bool):
        """
        Toggles the layout mode between GRID and FREE_FORM based on the checked state
        of a UI element (e.g., a QAction).
        """
        if checked:
            self.set_layout_mode(LayoutMode.GRID)
            self.logger.info("Layout mode toggled to GRID.")
        else:
            self.set_layout_mode(LayoutMode.FREE_FORM)
            self.logger.info("Layout mode toggled to FREE_FORM.")

    def align_selected_plots(self, edge: str):
        """
        Aligns the currently selected plots.
        """
        self.logger.info(f"MainController received request to align selected plots to: {edge}")
        selected_plots = [node for node in self.model.selection if isinstance(node, PlotNode)]
        if not selected_plots:
            self.logger.warning("No plots selected for alignment.")
            return

        # Delegate to LayoutManager to calculate new geometries
        new_geometries = self._layout_manager.perform_align(selected_plots, edge)
        if new_geometries:
            # Wrap changes in a command for undo/redo
            command = BatchChangePlotGeometryCommand(self.model, new_geometries, "Align Plots")
            self.command_manager.execute_command(command)
            self.logger.debug(f"Executed BatchChangePlotGeometryCommand for aligning plots to {edge}.")
        else:
            self.logger.info("No geometry changes after alignment calculation.")

    def distribute_selected_plots(self, axis: str):
        """
        Distributes the currently selected plots.
        """
        self.logger.info(f"MainController received request to distribute selected plots along: {axis}")
        selected_plots = [node for node in self.model.selection if isinstance(node, PlotNode)]
        if not selected_plots:
            self.logger.warning("No plots selected for distribution.")
            return

        # Delegate to LayoutManager to calculate new geometries
        new_geometries = self._layout_manager.perform_distribute(selected_plots, axis)
        if new_geometries:
            command = BatchChangePlotGeometryCommand(self.model, new_geometries, "Distribute Plots")
            self.command_manager.execute_command(command)
            self.logger.debug(f"Executed BatchChangePlotGeometryCommand for distributing plots along {axis}.")
        else:
            self.logger.info("No geometry changes after distribution calculation.")

    def apply_grid_layout_from_ui(self, rows: int, cols: int, margin: float, gutter: float):
        """
        Applies a new grid layout with specified rows, columns, margin, and gutter.
        This is typically called from the UI.
        """
        self.logger.info(f"MainController received request to apply grid layout from UI: {rows}x{cols}, Margin: {margin}, Gutter: {gutter}")
        # The actual logic for applying the layout is now in update_grid_parameters
        new_geometries = self._layout_manager.update_grid_layout_parameters(rows=rows, cols=cols, margin=margin, gutter=gutter)

        if new_geometries:
            command = BatchChangePlotGeometryCommand(self.model, new_geometries, f"Apply {rows}x{cols} Grid Layout")
            self.command_manager.execute_command(command)
            self.logger.debug(f"Executed BatchChangePlotGeometryCommand for {rows}x{cols} grid layout.")
        else:
            self.logger.info("No geometry changes after applying grid layout.")

    def snap_free_plots_to_grid_action(self):
        """
        Snaps selected free-form plots to a grid.
        This action is typically only available in FREE_FORM mode.
        It triggers a mode switch to GRID, which internally handles snapping.
        """
        self.logger.info("MainController received request to snap free plots to grid.")
        self._layout_manager.set_layout_mode(LayoutMode.GRID)
        self.logger.debug("Switched layout mode to GRID to snap plots.")

    def update_grid_parameters(self, rows: int, cols: int, margin: float, gutter: float):
        """
        Updates the grid layout parameters and applies the layout.
        This method is designed to be called by debounced UI signals.
        """
        self.logger.info(f"Updating grid parameters: Rows={rows}, Cols={cols}, Margin={margin}, Gutter={gutter}")

        # Call the layout manager's method directly with individual parameters
        new_geometries = self._layout_manager.update_grid_layout_parameters(rows=rows, cols=cols, margin=margin, gutter=gutter)

        if new_geometries:
            command = BatchChangePlotGeometryCommand(self.model, new_geometries, f"Update Grid Layout ({rows}x{cols})")
            self.command_manager.execute_command(command)
            self.logger.debug("Executed BatchChangePlotGeometryCommand for updating grid layout with new parameters.")
        else:
            self.logger.info("No geometry changes after updating grid parameters.")

    def apply_default_grid_layout(self):
        """
        Applies a default grid layout to all plots in the scene.
        This is typically called when a new plot is added in GRID mode,
        or when the grid layout needs to be refreshed with default parameters.
        """
        self.logger.info("MainController received request to apply default grid layout.")
        all_plots = [node for node in self.model.scene_root.all_descendants() if isinstance(node, PlotNode)]
        if not all_plots:
            self.logger.warning("No plots in scene to apply default grid layout.")
            return

        # Call update_grid_parameters with None for rows/cols to trigger inference
        # and use default margin/gutter from config.
        # This implicitly uses the defaults from _create_default_grid_config
        # and infers rows/cols if needed.
        new_geometries = self._layout_manager.update_grid_layout_parameters(rows=None, cols=None)

        if new_geometries:
            # The description for the command should reflect that it's a default application
            current_grid_config = self._layout_manager.current_layout_config # Get the config after update
            if isinstance(current_grid_config, GridConfig):
                description = f"Apply Default Grid Layout ({current_grid_config.rows}x{current_grid_config.cols})"
            else:
                description = "Apply Default Grid Layout (FreeForm fallback)"

            command = BatchChangePlotGeometryCommand(self.model, new_geometries, description)
            self.command_manager.execute_command(command)
            self.logger.debug("Executed BatchChangePlotGeometryCommand for default grid layout.")
        else:
            self.logger.info("No geometry changes after applying default grid layout.")

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
        self.logger.debug(f"Extracted existing plot states. Found {len(existing_plot_states)} plots.")

        # 2. Get default template name and path from ConfigService
        default_template_name = self._config_service.get("layout.default_template", "2x2_default.json")
        layout_templates_dir = Path(self._config_service.get("paths.layout_templates_dir", "configs/layouts"))
        template_path = layout_templates_dir / default_template_name
        self.logger.debug(f"Loading layout template: {template_path}")


        if not template_path.exists():
            self.logger.error(f"Layout template not found at {template_path}. Clearing scene and adding default plot.")
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
            self.logger.error(f"Error parsing layout template {template_path}: {e}. Clearing scene and adding error plot.", exc_info=True)
            self.model.clear_scene()
            self.model.add_node(PlotNode(name="Error Plot"))
            return

        # 4. Use scene_node.node_factory to deserialize JSON into new_layout_root_node
        new_layout_root_node = node_factory(template_data)
        self.logger.debug(f"Layout template deserialized. Root node: {new_layout_root_node.name} ({type(new_layout_root_node).__name__})")


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

                    self.logger.debug(f"Plot data assigned to new slot: {new_slot_node.name}, PlotType: {new_slot_node.plot_properties.plot_type}")
                    old_plot_index += 1
                # Else: new_slot_node remains an empty slot with its template defaults

        # 6. Set new_layout_root_node as the scene_root
        self.model.set_scene_root(new_layout_root_node)
        self.logger.info(f"New layout applied to model. Scene root: {new_layout_root_node.name}.")

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
            self.logger.info("Project save cancelled by user.")
            return

        self.logger.info(f"Saving project to: {file_path}")


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
                    self.logger.debug(f"Saved data for node {node.id} to {parquet_path}")

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
        self.logger.debug(f"Added '{file_path}' to recent files. Current list: {recent_files}")
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
        new_layout_root_node = node_factory(template_data)
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
