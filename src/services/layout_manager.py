import logging
from typing import Optional, List

from PySide6.QtCore import QObject, Signal

from src.services.config_service import ConfigService
from src.shared.constants import LayoutMode
from src.models.layout.layout_engine import FreeLayoutEngine, GridLayoutEngine, LayoutEngine, Rect
from src.models.application_model import ApplicationModel
from src.models.layout.layout_config import FreeConfig, GridConfig
from src.models.nodes.plot_node import PlotNode
from src.shared.types import PlotID, Margins, Gutters # Added Margins, Gutters


class LayoutManager(QObject):
    """
    Orchestrates the layout engines, manages the active layout mode,
    and provides the interface for main application components to
    trigger layout operations. It is responsible for changing the
    LayoutConfig in the ApplicationModel and coordinating with the
    appropriate LayoutEngine.
    """

    layoutModeChanged = Signal(LayoutMode)

    @property
    def layout_mode(self) -> LayoutMode:
        """Returns the current layout mode from the application model."""
        return self._application_model.current_layout_config.mode

    def __init__(
        self,
        application_model: ApplicationModel,
        free_engine: FreeLayoutEngine,
        grid_engine: GridLayoutEngine,
        config_service: ConfigService,
        parent: QObject | None = None,
    ):
        super().__init__(parent)
        self._application_model = application_model
        self._free_engine = free_engine
        self._grid_engine = grid_engine
        self._config_service = config_service
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info("LayoutManager initialized.")

        # Store last used configs for each mode to prevent loss of settings when switching
        self._last_grid_config: GridConfig = self._create_default_grid_config()
        self._last_free_form_config: FreeConfig = FreeConfig()

        # Initialize the application model's current_layout_config based on config service
        default_mode_str = self._config_service.get("ui.default_layout_mode", LayoutMode.FREE_FORM.value)
        default_mode = LayoutMode(default_mode_str)
        self.logger.debug(f"Default layout mode from config: {default_mode.value}")

        if default_mode == LayoutMode.GRID:
            self._application_model.current_layout_config = self._last_grid_config
        else:
            self._application_model.current_layout_config = self._last_free_form_config

        self.logger.info(f"Initial layout mode set to: {self._application_model.current_layout_config.mode.value}")


    def _parse_float_list_from_config(self, key: str, default: List[float]) -> List[float]:
        """Helper to parse a config value that might be a list of floats, a single float, or a string representation."""
        value = self._config_service.get(key, default)
        self.logger.debug(f"[_parse_float_list_from_config] Key: {key}, Raw Value: {value}, Type: {type(value)}")

        if isinstance(value, str):
            try:
                # Attempt to parse a string like "[0.1, 0.2]" or "0.1, 0.2"
                if value.startswith('[') and value.endswith(']'):
                    value = value[1:-1] # Remove brackets
                
                parsed_list = [float(x.strip()) for x in value.split(',') if x.strip()]
                self.logger.debug(f"[_parse_float_list_from_config] Parsed string to list: {parsed_list}")
                return parsed_list
            except ValueError:
                self.logger.warning(f"Could not parse '{value}' for config key '{key}' as a list of floats. Using default: {default}")
                return default
        elif isinstance(value, (int, float)): # Handle single numeric value
            self.logger.debug(f"[_parse_float_list_from_config] Wrapped single numeric value in list: {[float(value)]}")
            return [float(value)]
        elif isinstance(value, list):
            # Ensure all elements in the list are floats
            try:
                float_list = [float(x) for x in value]
                self.logger.debug(f"[_parse_float_list_from_config] Converted list elements to floats: {float_list}")
                return float_list
            except ValueError:
                self.logger.warning(f"List for config key '{key}' contains non-float elements. Using default: {default}")
                return default
        else: # Fallback for unexpected types
            self.logger.warning(f"Unexpected type '{type(value).__name__}' for config key '{key}'. Using default: {default}")
            return default

    def _create_default_grid_config(self) -> GridConfig:
        """Helper to create a default GridConfig from ConfigService."""
        rows = self._config_service.get("layout.default_grid_rows", 2)
        cols = self._config_service.get("layout.default_grid_cols", 2)
        
        # New way to get margins and gutters
        margin_top = self._config_service.get("layout.grid_margin_top", 0.05)
        margin_bottom = self._config_service.get("layout.grid_margin_bottom", 0.05)
        margin_left = self._config_service.get("layout.grid_margin_left", 0.05)
        margin_right = self._config_service.get("layout.grid_margin_right", 0.05)
        
        hspace = self._parse_float_list_from_config("layout.grid_hspace", [])
        wspace = self._parse_float_list_from_config("layout.grid_wspace", [])

        return GridConfig(
            rows=rows,
            cols=cols,
            margins=Margins(top=margin_top, bottom=margin_bottom, left=margin_left, right=margin_right),
            gutters=Gutters(hspace=hspace, wspace=wspace)
                                )
                        
    def _infer_grid_dimensions(self, num_plots: int) -> tuple[int, int]:
        """
        Infers sensible grid rows and columns based on the number of plots.
        Aims for a square-ish layout.
        """
        if num_plots <= 0:
            return 1, 1

        # Try to find two factors that are close to each other
        # Start from sqrt and work down
        sqrt_n = int(num_plots**0.5)
        for i in range(sqrt_n, 0, -1):
            if num_plots % i == 0:
                return i, num_plots // i # rows, cols

        # If num_plots is prime or cannot be easily factored, default to num_plots x 1
        return num_plots, 1
    

    def infer_grid_config_from_plots(self, plots: list[PlotNode], current_grid_config: GridConfig) -> GridConfig:
        """
        Infers sensible grid rows, columns, margins, and gutters directly from the current
        free-form plot positions without applying any layout engine during inference.

        DISCLAIMER: This is a heuristic-based inference method. It works best when plots
        are already somewhat regularly arranged. In a future iteration, this method will
        need to become significantly more robust to handle arbitrary, overlapping, or
        poorly aligned free-form plot arrangements by employing more advanced clustering
        or spatial analysis techniques to infer rows, columns, and optimal spacing.
        The current implementation assumes a generally "grid-like" starting point.
        """
        self.logger.info(f"Inferring grid config from {len(plots)} plots based on current free-form positions.")
        if not plots:
            return current_grid_config # Or a sensible default

        # 1. Infer rows and cols (using the helper method)
        num_plots = len(plots)
        inferred_rows, inferred_cols = self._infer_grid_dimensions(num_plots) # Now calls its own method

        # 2. Calculate Bounding Box of all plots
        min_x = min(p.geometry[0] for p in plots)
        min_y = min(p.geometry[1] for p in plots)
        max_x_end = max(p.geometry[0] + p.geometry[2] for p in plots)
        max_y_end = max(p.geometry[1] + p.geometry[3] for p in plots)

        # 3. Infer Margins
        inferred_margin_left = max(0.0, min_x)
        inferred_margin_bottom = max(0.0, min_y)
        inferred_margin_right = max(0.0, 1.0 - max_x_end)
        inferred_margin_top = max(0.0, 1.0 - max_y_end)

        # Round margins for cleaner display
        inferred_margin_left = round(inferred_margin_left, 3)
        inferred_margin_bottom = round(inferred_margin_bottom, 3)
        inferred_margin_right = round(inferred_margin_right, 3)
        inferred_margin_top = round(inferred_margin_top, 3)

        inferred_margins = Margins(
            top=inferred_margin_top,
            bottom=inferred_margin_bottom,
            left=inferred_margin_left,
            right=inferred_margin_right
        )

        # 4. Infer Gutters (hspace, wspace)
        # Group plots by their inferred row/column for gap measurement
        plots_by_row = [[] for _ in range(inferred_rows)]
        plots_by_col = [[] for _ in range(inferred_cols)]

        # Sort plots for consistent assignment (e.g., top-left to bottom-right)
        sorted_plots = sorted(plots, key=lambda p: (p.geometry[1], p.geometry[0]))

        # Simple assignment heuristic: distribute plots sequentially into the grid
        current_row_assign = 0
        current_col_assign = 0
        for plot in sorted_plots:
            if current_row_assign < inferred_rows and current_col_assign < inferred_cols:
                plots_by_row[current_row_assign].append((plot, current_col_assign))
                plots_by_col[current_col_assign].append((plot, current_row_assign))
                current_col_assign += 1
                if current_col_assign >= inferred_cols:
                    current_col_assign = 0
                    current_row_assign += 1

        horizontal_gaps = []
        for row_plots_with_idx in plots_by_row:
            row_plots_with_idx.sort(key=lambda x: x[1]) # Sort by col_idx to ensure correct order
            for i in range(len(row_plots_with_idx) - 1):
                p1, _ = row_plots_with_idx[i]
                p2, _ = row_plots_with_idx[i+1]
                gap = p2.geometry[0] - (p1.geometry[0] + p1.geometry[2])
                if gap > 0: # Only positive gaps contribute
                    horizontal_gaps.append(gap)

        vertical_gaps = []
        for col_plots_with_idx in plots_by_col:
            col_plots_with_idx.sort(key=lambda x: x[1]) # Sort by row_idx to ensure correct order
            for i in range(len(col_plots_with_idx) - 1):
                p1, _ = col_plots_with_idx[i]
                p2, _ = col_plots_with_idx[i+1]
                gap = p2.geometry[1] - (p1.geometry[1] + p1.geometry[3])
                if gap > 0: # Only positive gaps contribute
                    vertical_gaps.append(gap)

        # Matplotlib hspace/wspace are relative to subplot width/height.
        # Estimate average subplot dimensions to normalize gaps.
        estimated_subplot_width = (1.0 - inferred_margins.left - inferred_margins.right) / inferred_cols if inferred_cols > 0 else 0
        estimated_subplot_height = (1.0 - inferred_margins.top - inferred_margins.bottom) / inferred_rows if inferred_rows > 0 else 0

        inferred_hspace = []
        if horizontal_gaps and estimated_subplot_width > 0:
            avg_gap_h = sum(horizontal_gaps) / len(horizontal_gaps)
            inferred_hspace = [round(avg_gap_h / estimated_subplot_width, 3)]
        else: # Default if no gaps or zero width
            inferred_hspace = [0.02] # Sensible default

        inferred_wspace = []
        if vertical_gaps and estimated_subplot_height > 0:
            avg_gap_v = sum(vertical_gaps) / len(vertical_gaps)
            inferred_wspace = [round(avg_gap_v / estimated_subplot_height, 3)]
        else: # Default if no gaps or zero height
            inferred_wspace = [0.02] # Sensible default

        inferred_gutters = Gutters(hspace=inferred_hspace, wspace=inferred_wspace)

        # Return a new GridConfig with inferred values
        new_inferred_grid_config = GridConfig(
            rows=inferred_rows,
            cols=inferred_cols,
            row_ratios=[1.0] * inferred_rows, # Default ratios for now
            col_ratios=[1.0] * inferred_cols, # Default ratios for now
            margins=inferred_margins,
            gutters=inferred_gutters
        )

        self.logger.debug(f"Inferred GridConfig: {new_inferred_grid_config}")
        return new_inferred_grid_config

    
    def get_active_engine(self) -> LayoutEngine:
        """Returns the currently active layout engine based on the model's configuration."""
        if self._application_model.current_layout_config.mode == LayoutMode.FREE_FORM:
            return self._free_engine
        elif self._application_model.current_layout_config.mode == LayoutMode.GRID:
            return self._grid_engine
        else:
            self.logger.error(f"Unknown layout mode: {self._application_model.current_layout_config.mode}")
            return self._free_engine # Fallback


    def set_layout_mode(self, mode: LayoutMode):
        """
        Sets the active layout mode in the ApplicationModel.
        Triggers a layout update if transitioning to grid or from grid.
        """
        current_config = self._application_model.current_layout_config
        current_mode = current_config.mode
        if current_mode == mode:
            self.logger.debug(f"Layout mode already {mode.value}. No change needed.")
            return

        self.logger.info(f"Attempting to switch layout mode from {current_mode.value} to {mode.value}.")

        # Save current config to its respective _last_x_config before switching
        if isinstance(current_config, GridConfig):
            self._last_grid_config = current_config
        elif isinstance(current_config, FreeConfig):
            self._last_free_form_config = current_config

        if mode == LayoutMode.GRID:
            # Transition to GRID: use the last known grid config
            self._application_model.current_layout_config = self._last_grid_config
            # Removed call to update_grid_config_and_apply.
            # Grid layout will now only be applied when explicitly triggered (e.g., via "Snap to Grid").
            self.logger.debug(f"Transitioning to GRID. Loaded last known grid config: {self._last_grid_config}. Layout will not be automatically applied.")

        elif mode == LayoutMode.FREE_FORM:
            # Transition to FREE_FORM: use the last known free form config
            self._application_model.current_layout_config = self._last_free_form_config
            self.logger.debug("Transitioning to FREE_FORM.")

        self.layoutModeChanged.emit(mode)
        self._application_model.layoutConfigChanged.emit() # Notify model observers of config change
        self.logger.info(f"Layout mode successfully switched to {mode.value}.")


    def update_grid_config_and_apply(self, new_grid_config: GridConfig) -> dict[PlotID, Rect]:
        """
        Updates the current GridConfig in the ApplicationModel and LayoutManager,
        then calculates and returns the new geometries for all plots.
        This method is intended to be called by commands or other internal mechanisms
        that directly provide a complete GridConfig object.
        """
        self.logger.info(f"LayoutManager updating grid config to: {new_grid_config}")
        self.logger.debug(f"Incoming new_grid_config margins: {new_grid_config.margins}")
        self.logger.debug(f"Incoming new_grid_config gutters: {new_grid_config.gutters}")

        self._application_model.current_layout_config = new_grid_config
        self._last_grid_config = new_grid_config # Update stored last grid config for next time

        self.layoutModeChanged.emit(LayoutMode.GRID) # Ensure UI updates if needed
        self.logger.debug("Emitting layoutConfigChanged signal.")
        self._application_model.layoutConfigChanged.emit() # Notify model observers

        all_plots = list(self._application_model.scene_root.all_descendants(of_type=PlotNode))
        if not all_plots:
            return {}

        # Calculate geometries and return Dict[str, Rect]
        # With _apply_fixed_grid_layout, calculated_margins/gutters will now be the input new_grid_config.margins/gutters
        plot_geometries, _, _ = self._grid_engine.calculate_geometries(all_plots, new_grid_config)

        # The new_grid_config already contains the desired margins and gutters,
        # so we don't need to create a new one using 'calculated' values.
        # This ensures the user's input margins/gutters are retained in the model.
        # The _application_model.current_layout_config and _last_grid_config were already set to new_grid_config earlier.
        
        self.logger.debug(f"Final updated_grid_config margins: {new_grid_config.margins}")
        self.logger.debug(f"Final updated_grid_config gutters: {new_grid_config.gutters}")
        
        return plot_geometries


    def perform_align(self, plots: list[PlotNode], edge: str) -> dict[PlotID, Rect]:
        """
        Performs alignment operation on selected plots using the FreeLayoutEngine.
        Raises ValueError if not in Free-Form mode.
        """
        if self._application_model.current_layout_config.mode != LayoutMode.FREE_FORM:
            self.logger.warning("Attempted align operation while not in FREE_FORM mode. Returning empty geometries.")
            return {}

        # Ensure the FreeLayoutEngine is used and returns plot ID to Rect mapping
        return {plot.id: rect for plot, rect in self._free_engine.perform_align(plots, edge).items()}


    def perform_distribute(self, plots: list[PlotNode], axis: str) -> dict[PlotID, Rect]:
        """
        Performs distribution operation on selected plots using the FreeLayoutEngine.
        Raises ValueError if not in Free-Form mode.
        """
        if self._application_model.current_layout_config.mode != LayoutMode.FREE_FORM:
            self.logger.warning("Attempted distribute operation while not in FREE_FORM mode. Returning empty geometries.")
            return {}

        # Ensure the FreeLayoutEngine is used and returns plot ID to Rect mapping
        return {plot.id: rect for plot, rect in self._free_engine.perform_distribute(plots, axis).items()}


    def infer_grid_parameters(self):
        """
        Infers sensible grid parameters (rows, cols, margins, gutters) from the current
        free-form plot positions and updates the model.
        This does NOT apply the layout to the canvas immediately but updates the UI fields.
        """
        self.logger.info("LayoutManager received request to infer grid parameters.")

        all_plots = list(self._application_model.scene_root.all_descendants(of_type=PlotNode))
        if not all_plots:
            self.logger.warning("No plots in scene to infer grid from.")
            return

        # Infer a new GridConfig based on geometric analysis of free-form plots
        new_inferred_grid_config = self.infer_grid_config_from_plots(all_plots, self._last_grid_config)

        # Update the model with the inferred config
        self._application_model.current_layout_config = new_inferred_grid_config
        self._last_grid_config = new_inferred_grid_config
        
        # Emit signal to update UI fields
        self.layoutModeChanged.emit(LayoutMode.GRID) # Ensure UI updates if needed
        self.logger.debug("Emitting layoutConfigChanged signal to update UI with inferred parameters.")
        self._application_model.layoutConfigChanged.emit()
        self.logger.info(f"Inferred grid parameters: {new_inferred_grid_config}")

    def optimize_layout_action(self):
        """
        Optimizes the current grid layout using Matplotlib's constrained_layout,
        based on the current grid parameters in the model.
        Updates the model with the actual calculated margins/gutters and triggers a redraw.
        """
        self.logger.info("LayoutManager received request to optimize layout.")

        current_grid_config: GridConfig = self._last_grid_config
        
        all_plots = list(self._application_model.scene_root.all_descendants(of_type=PlotNode))
        if not all_plots:
            self.logger.warning("No plots in scene to optimize layout for.")
            return

        # Use calculate_geometries with constrained optimization
        # This will return the geometries and the *calculated* margins/gutters from constrained_layout
        plot_geometries, calculated_margins, calculated_gutters = self._grid_engine.calculate_geometries(
            all_plots, current_grid_config, use_constrained_optimization=True
        )

        # Update the grid config with the *actual calculated* margins and gutters from constrained_layout
        updated_grid_config = GridConfig(
            rows=current_grid_config.rows,
            cols=current_grid_config.cols,
            row_ratios=current_grid_config.row_ratios,
            col_ratios=current_grid_config.col_ratios,
            margins=calculated_margins,
            gutters=calculated_gutters
        )

        # Apply the updated config and geometries
        self._application_model.current_layout_config = updated_grid_config
        self._last_grid_config = updated_grid_config

        if plot_geometries:
            for plot_id, rect in plot_geometries.items():
                plot_node = self._application_model.scene_root.find_node_by_id(plot_id)
                if plot_node:
                    plot_node.geometry = rect
            self._application_model.modelChanged.emit() # Redraw canvas

        self.layoutModeChanged.emit(LayoutMode.GRID) # Ensure UI updates if needed
        self.logger.debug("Emitting layoutConfigChanged signal to update UI with optimized parameters.")
        self._application_model.layoutConfigChanged.emit()
        self.logger.info(f"Optimized layout applied with config: {updated_grid_config}")

    def update_grid_layout_parameters(self, rows: Optional[int] = None, cols: Optional[int] = None,
                                        margin: Optional[float] = None, gutter: Optional[float] = None,
                                        margin_top: Optional[float] = None, margin_bottom: Optional[float] = None,
                                        margin_left: Optional[float] = None, margin_right: Optional[float] = None,
                                        hspace_str: Optional[str] = None, wspace_str: Optional[str] = None) -> dict[PlotID, Rect]:
        """
        Updates the current GridConfig with new parameters and applies the layout.
        If rows or cols are None, they will be inferred from the number of plots.
        This method always uses the last known GridConfig as its base for updates.
        It can update old single margin/gutter values or new granular margin/gutter values.
        """
        self.logger.info(f"Updating grid layout parameters: rows={rows}, cols={cols}, "
                          f"margin_old={margin}, gutter_old={gutter}, "
                          f"margin_top={margin_top}, margin_bottom={margin_bottom}, "
                          f"margin_left={margin_left}, margin_right={margin_right}, "
                          f"hspace_str='{hspace_str}', wspace_str='{wspace_str}'")
        self.logger.debug(f"Current _last_grid_config before update: {self._last_grid_config}")

        base_grid_config = self._last_grid_config

        effective_rows = base_grid_config.rows
        effective_cols = base_grid_config.cols
        effective_row_ratios = base_grid_config.row_ratios
        effective_col_ratios = base_grid_config.col_ratios

        # Handle granular margins
        effective_margins = base_grid_config.margins
        final_margins = Margins(
            top=margin_top if margin_top is not None else effective_margins.top,
            bottom=margin_bottom if margin_bottom is not None else effective_margins.bottom,
            left=margin_left if margin_left is not None else effective_margins.left,
            right=margin_right if margin_right is not None else effective_margins.right,
        )

        # Handle granular gutters
        effective_gutters = base_grid_config.gutters
        final_gutters = Gutters(
            hspace=effective_gutters.hspace,
            wspace=effective_gutters.wspace
        )

        if hspace_str is not None:
            try:
                final_gutters.hspace = [float(x.strip()) for x in hspace_str.split(',') if x.strip()]
            except ValueError:
                self.logger.warning(f"Invalid hspace_str format: '{hspace_str}'. Keeping old hspace.")
        if wspace_str is not None:
            try:
                final_gutters.wspace = [float(x.strip()) for x in wspace_str.split(',') if x.strip()]
            except ValueError:
                self.logger.warning(f"Invalid wspace_str format: '{wspace_str}'. Keeping old wspace.")


        all_plots = list(self._application_model.scene_root.all_descendants(of_type=PlotNode))
        num_plots = len(all_plots)

        # Infer rows/cols if not provided or set to a special sentinel (e.g., 0)
        if (rows is None or rows == 0) or (cols is None or cols == 0):
            inferred_rows, inferred_cols = self._infer_grid_dimensions(num_plots)
            if rows is None or rows == 0:
                rows = inferred_rows
            if cols is None or cols == 0:
                cols = inferred_cols
            self.logger.debug(f"Inferred grid dimensions: {rows}x{cols} for {num_plots} plots.")

        # Apply updates, preferring new values over effective values
        final_rows = rows if rows is not None else effective_rows
        final_cols = cols if cols is not None else effective_cols

        new_grid_config = GridConfig(
            rows=final_rows,
            cols=final_cols,
            row_ratios=effective_row_ratios,
            col_ratios=effective_col_ratios,
            margins=final_margins,
            gutters=final_gutters,
        )

        # Call the new method to update config and apply layout
        return self.update_grid_config_and_apply(new_grid_config)




    def get_current_layout_geometries(self, plots: list[PlotNode]) -> dict[PlotID, Rect]:
        """
        Returns the calculated geometries for the given plots based on the
        currently active layout engine and configuration.
        """
        active_engine = self.get_active_engine()
        geometries_dict, _, _ = active_engine.calculate_geometries(plots, self._application_model.current_layout_config)
        return geometries_dict
