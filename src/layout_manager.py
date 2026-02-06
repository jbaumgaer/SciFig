import logging
from typing import Dict, List, Tuple, Any, Optional

from PySide6.QtCore import QObject, Signal

from src.config_service import ConfigService
from src.constants import LayoutMode
from src.models.application_model import ApplicationModel
from src.models.layout_config import LayoutConfig, FreeConfig, GridConfig
from src.models.nodes import PlotNode # Added import
from src.layout_engine import LayoutEngine, FreeLayoutEngine, GridLayoutEngine, Rect
from src.types import PlotID


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


    def _create_default_grid_config(self) -> GridConfig:
        """Helper to create a default GridConfig from ConfigService."""
        rows = self._config_service.get("layout.default_grid_rows", 2)
        cols = self._config_service.get("layout.default_grid_cols", 2)
        margin = self._config_service.get("layout.grid_margin", 0.05)
        gutter = self._config_service.get("layout.grid_gutter", 0.05)
        return GridConfig(rows=rows, cols=cols, margin=margin, gutter=gutter)

    def _infer_grid_dimensions(self, num_plots: int) -> Tuple[int, int]:
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
            # Call update_grid_layout_parameters to apply the stored grid config
            # This ensures that when switching to grid, the plots immediately snap
            # to the last used grid configuration.
            self.logger.debug(f"Calling update_grid_layout_parameters with: rows={self._last_grid_config.rows}, cols={self._last_grid_config.cols}, margin={self._last_grid_config.margin}, gutter={self._last_grid_config.gutter}")
            self.update_grid_layout_parameters(
                rows=self._last_grid_config.rows,
                cols=self._last_grid_config.cols,
                margin=self._last_grid_config.margin,
                gutter=self._last_grid_config.gutter
            )
            self.logger.debug("Transitioning to GRID. Applying last known grid config.")

        elif mode == LayoutMode.FREE_FORM:
            # Transition to FREE_FORM: use the last known free form config
            self._application_model.current_layout_config = self._last_free_form_config
            self.logger.debug("Transitioning to FREE_FORM.")
        
        self.layoutModeChanged.emit(mode)
        self._application_model.layoutConfigChanged.emit() # Notify model observers of config change
        self.logger.info(f"Layout mode successfully switched to {mode.value}.")


    def perform_align(self, plots: List[PlotNode], edge: str) -> Dict[PlotID, Rect]:
        """
        Performs alignment operation on selected plots using the FreeLayoutEngine.
        Raises ValueError if not in Free-Form mode.
        """
        if self._application_model.current_layout_config.mode != LayoutMode.FREE_FORM:
            self.logger.warning("Attempted align operation while not in FREE_FORM mode. Returning empty geometries.")
            return {}
        
        # Ensure the FreeLayoutEngine is used and returns plot ID to Rect mapping
        return {plot.id: rect for plot, rect in self._free_engine.perform_align(plots, edge).items()}


    def perform_distribute(self, plots: List[PlotNode], axis: str) -> Dict[PlotID, Rect]:
        """
        Performs distribution operation on selected plots using the FreeLayoutEngine.
        Raises ValueError if not in Free-Form mode.
        """
        if self._application_model.current_layout_config.mode != LayoutMode.FREE_FORM:
            self.logger.warning("Attempted distribute operation while not in FREE_FORM mode. Returning empty geometries.")
            return {}
        
        # Ensure the FreeLayoutEngine is used and returns plot ID to Rect mapping
        return {plot.id: rect for plot, rect in self._free_engine.perform_distribute(plots, axis).items()}

    def update_grid_layout_parameters(self, rows: Optional[int] = None, cols: Optional[int] = None, margin: Optional[float] = None, gutter: Optional[float] = None) -> Dict[PlotID, Rect]:
        """
        Updates the current GridConfig with new parameters and applies the layout.
        If rows or cols are None, they will be inferred from the number of plots.
        This method always uses the last known GridConfig as its base for updates.
        """
        self.logger.info(f"Updating grid layout parameters: rows={rows}, cols={cols}, margin={margin}, gutter={gutter}")
        self.logger.debug(f"Current _last_grid_config before update: {self._last_grid_config}")


        # Always use the last_grid_config as the base for updates
        base_grid_config = self._last_grid_config
        
        effective_rows = base_grid_config.rows
        effective_cols = base_grid_config.cols
        effective_margin = base_grid_config.margin
        effective_gutter = base_grid_config.gutter
        effective_row_ratios = base_grid_config.row_ratios
        effective_col_ratios = base_grid_config.col_ratios

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
        final_margin = margin if margin is not None else effective_margin
        final_gutter = gutter if gutter is not None else effective_gutter

        new_grid_config = GridConfig(
            rows=final_rows,
            cols=final_cols,
            margin=final_margin,
            gutter=final_gutter,
            row_ratios=effective_row_ratios, # Preserve ratios unless explicitly updated (Feature 4)
            col_ratios=effective_col_ratios, # Preserve ratios unless explicitly updated (Feature 4)
        )

        self._application_model.current_layout_config = new_grid_config
        self._last_grid_config = new_grid_config # Update stored last grid config for next time
        self.logger.debug(f"New _last_grid_config after update: {self._last_grid_config}")


        self.layoutModeChanged.emit(LayoutMode.GRID) # Ensure UI updates if needed
        self.logger.debug("Emitting layoutConfigChanged signal.")
        self._application_model.layoutConfigChanged.emit() # Notify model observers

        # Calculate geometries and return Dict[str, Rect]
        return {plot_id: rect for plot_id, rect in self._grid_engine.calculate_geometries(all_plots, new_grid_config).items()}


    def adjust_current_grid(
        self,
        rows: Optional[int] = None,
        cols: Optional[int] = None,
        row_ratios: List[float] | None = None,
        col_ratios: List[float] | None = None,
    ) -> Dict[PlotID, Rect]:
        """
        Adjusts parameters of the current GridConfig and recalculates layout.
        Raises ValueError if not in Grid mode.
        """
        if not isinstance(self._application_model.current_layout_config, GridConfig):
            self.logger.warning("Attempted to adjust grid while not in GRID mode. Returning empty geometries.")
            return {}
        
        current_grid_config: GridConfig = self._application_model.current_layout_config
        
        # Create a new GridConfig instance with updated values
        # This ensures immutability if GridConfig is a frozen dataclass
        new_grid_config = GridConfig(
            rows=rows if rows is not None else current_grid_config.rows,
            cols=cols if cols is not None else current_grid_config.cols,
            row_ratios=row_ratios if row_ratios is not None else current_grid_config.row_ratios,
            col_ratios=col_ratios if col_ratios is not None else current_grid_config.col_ratios,
            margin=current_grid_config.margin,
            gutter=current_grid_config.gutter
        )
        self.logger.info(f"Adjusting current grid: new config {new_grid_config}")
        self._application_model.current_layout_config = new_grid_config
        self._last_grid_config = new_grid_config # Update stored last grid config
        self._application_model.layoutConfigChanged.emit() # Notify model observers
        
        # Calculate geometries and return Dict[str, Rect]
        return {plot.id: rect for plot, rect in self._grid_engine.calculate_geometries(
            list(self._application_model.scene_root.all_descendants(of_type=PlotNode)),
            new_grid_config
        ).items()}


    def get_current_layout_geometries(self, plots: List[PlotNode]) -> Dict[PlotID, Rect]:
        """
        Returns the calculated geometries for the given plots based on the
        currently active layout engine and configuration.
        """
        active_engine = self.get_active_engine()
        return {plot_id: rect for plot_id, rect in active_engine.calculate_geometries(plots, self._application_model.current_layout_config).items()}
