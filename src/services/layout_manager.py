import logging
from typing import Optional

from src.models.application_model import ApplicationModel
from src.models.layout.free_layout_engine import FreeLayoutEngine
from src.models.layout.grid_layout_engine import GridLayoutEngine
from src.models.layout.layout_config import FreeConfig, GridConfig, Gutters, Margins
from src.models.layout.layout_engine import LayoutEngine
from src.models.layout.layout_protocols import FreeFormLayoutCapabilities
from src.models.nodes.plot_node import PlotNode
from src.models.plots.plot_types import ArtistType
from src.services.config_service import ConfigService
from src.services.coordinate_service import CoordinateService
from src.services.event_aggregator import EventAggregator
from src.shared.constants import LayoutMode
from src.shared.events import Events
from src.shared.geometry import Rect
from src.shared.types import CoordinateSpace, PlotID


class LayoutManager:
    """
    Orchestrates the layout engines, manages the active layout mode,
    and provides the interface for main application components to
    trigger layout operations. It is responsible for changing the
    LayoutConfig in the ApplicationModel and coordinating with the
    appropriate LayoutEngine. Translates between the model's PHYSICAL (CM) 
    space and the renderer's FRACTIONAL space.
    """

    _ui_selected_layout_mode: LayoutMode = LayoutMode.FREE_FORM

    def __init__(
        self,
        application_model: ApplicationModel,
        free_engine: FreeLayoutEngine,
        grid_engine: GridLayoutEngine,
        config_service: ConfigService,
        event_aggregator: EventAggregator,
    ):
        self._application_model = application_model
        self._free_engine = free_engine
        self._grid_engine = grid_engine
        self._config_service = config_service
        self._event_aggregator = event_aggregator
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info("LayoutManager initialized.")

        # Store last used configs for each mode to prevent loss of settings when switching
        self._last_grid_config: Optional[GridConfig] = None
        self._last_free_form_config: Optional[FreeConfig] = FreeConfig()

        # Initialize the UI selected mode and the application model's current_layout_config based on config service
        default_mode_str = self._config_service.get_required("ui.default_layout_mode")
        default_mode = LayoutMode(default_mode_str)
        self._ui_selected_layout_mode = default_mode  # Initialize new attribute
        self.logger.debug(
            f"Default UI selected layout mode from config: {default_mode.value}"
        )

        self.set_layout_mode(default_mode)

        self.logger.info(
            f"Initial active layout mode set to: {self._application_model.current_layout_config.mode.value}"
        )

    @property
    def layout_mode(self) -> LayoutMode:
        """Returns the current layout mode from the application model."""
        return self._application_model.current_layout_config.mode

    @property
    def ui_selected_layout_mode(self) -> LayoutMode:
        """Returns the layout mode currently selected in the UI."""
        return self._ui_selected_layout_mode

    @ui_selected_layout_mode.setter
    def ui_selected_layout_mode(self, mode: LayoutMode):
        """Sets the UI selected layout mode and publishes the event."""
        if self._ui_selected_layout_mode != mode:
            self.logger.info(f"UI selected layout mode changed to: {mode.value}")
            self._ui_selected_layout_mode = mode
            self._event_aggregator.publish(
                Events.UI_LAYOUT_MODE_CHANGED, ui_layout_mode=mode
            )

    def on_model_reset(self) -> None:
        """
        Public slot to be connected to a signal indicating a major model reset
        (e.g., loading a new project or template).
        """
        self.logger.info("Model has been reset, clearing layout caches.")
        self.reset_cached_configs()

    def get_last_grid_config(self) -> Optional[GridConfig]:
        """
        Returns the last used GridConfig. Can be None if no grid config has been set yet.
        """
        return self._last_grid_config

    def reset_cached_configs(self):
        """
        Resets any cached layout configurations to ensure that when a new project
        is loaded, or a new layout is created, previous settings do not persist
        incorrectly.
        """
        self.logger.info("LayoutManager: Resetting cached layout configurations.")
        self._last_grid_config = None
        self._last_free_form_config = None

    def apply_layout_template(self, template_root) -> None:
        """
        Applies a new layout template, preserving and redistributing
        existing plot data from the current model.
        """
        self.logger.info(f"Applying new layout template: {template_root.name}")
        plot_states = self._application_model.extract_plot_states()
        self._redistribute_plot_states(template_root, plot_states)
        self._application_model.set_scene_root(template_root)

    def _redistribute_plot_states(self, new_root, plot_states: list[dict]):
        """Populates the new layout's plot nodes with the extracted plot states."""
        old_plot_index = 0
        for new_slot_node in new_root.all_descendants():
            if isinstance(new_slot_node, PlotNode):
                if old_plot_index >= len(plot_states):
                    continue
                old_state = plot_states[old_plot_index]
                new_slot_node.data = old_state["data"]
                if new_slot_node.plot_properties:
                    new_slot_node.plot_properties.update_from_dict(
                        old_state["plot_properties_dict"]
                    )
                else:
                    old_type_str = old_state["plot_properties_dict"].get(
                        "plot_type", "line"
                    )
                    try:
                        old_type = ArtistType(old_type_str)
                    except ValueError:
                        old_type = ArtistType.LINE

                    self._event_aggregator.publish(
                        Events.INITIALIZE_PLOT_THEME_REQUESTED,
                        node_id=new_slot_node.id,
                        plot_type=old_type,
                    )
                old_plot_index += 1

    def infer_grid_config_from_plots(
        self, plots: list[PlotNode], base_grid_config: Optional[GridConfig]
    ) -> GridConfig:
        """
        Infers sensible grid rows, columns, margins, and gutters directly from the current
        free-form plot positions without applying any layout engine during inference.

        DISCLAIMER: This is a heuristic-based inference method. It works best when plots
        are already somewhat regularly arranged. In a future iteration, this method will
        need to become significantly more robust to handle arbitrary, overlapping, or
        poorly aligned free-form plot arrangements by employing more advanced clustering
        or spatial analysis techniques to infer rows, columns, and optimal spacing.
        The current implementation assumes a generally "grid-like" starting point.
        # TODO: This sets a lot of default values and needs thorough unit testing
        """
        self.logger.info(
            f"Inferring grid config from {len(plots)} plots based on current free-form positions."
        )
        if not plots:
            return (
                base_grid_config
                if base_grid_config is not None
                else self._create_minimal_grid_config()
            )

        # 1. Infer dimensions
        num_plots = len(plots)
        rows, cols = self._infer_grid_dimensions(num_plots)

        # 2. Calculate Bounding Box
        min_x = min(p.geometry.x for p in plots)
        min_y = min(p.geometry.y for p in plots)
        max_x_end = max(p.geometry.x + p.geometry.width for p in plots)
        max_y_end = max(p.geometry.y + p.geometry.height for p in plots)
        
        fig_w, fig_h = self._application_model.figure_size

        # 3. Infer Margins
        # Round margins for cleaner display
        inferred_margins = Margins(
            top=round(max(0.0, fig_h - max_y_end), 2),
            bottom=round(max(0.0, min_y), 2),
            left=round(max(0.0, min_x), 2),
            right=round(max(0.0, fig_w - max_x_end), 2),
        )

        # 4. Infer Gutters (hspace, wspace)) using Sequential Assignment
        plots_by_row = [[] for _ in range(rows)]
        plots_by_col = [[] for _ in range(cols)]

        # Sort: top-to-bottom (Matplotlib Y is inverted vs standard screen, 
        # but our Rect.y is bottom-up. So top is high Y)
        sorted_plots = sorted(plots, key=lambda p: (-p.geometry.y, p.geometry.x))

        idx = 0
        for r in range(rows):
            for c in range(cols):
                if idx >= num_plots: break
                plot = sorted_plots[idx]
                plots_by_row[r].append(plot)
                plots_by_col[c].append(plot)
                idx += 1

        def get_avg_gap(groups, is_horizontal=True):
            gaps = []
            for group in groups:
                # Sort along the axis we are measuring
                if is_horizontal:
                    group.sort(key=lambda p: p.geometry.x)
                else:
                    group.sort(key=lambda p: p.geometry.y)
                
                for i in range(len(group) - 1):
                    p1 = group[i]
                    p2 = group[i+1]
                    if is_horizontal:
                        gap = p2.geometry.x - (p1.geometry.x + p1.geometry.width)
                    else:
                        gap = p2.geometry.y - (p1.geometry.y + p1.geometry.height)
                    
                    if gap > 0.05: gaps.append(gap)
            return round(sum(gaps)/len(gaps), 2) if gaps else 0.5

        inferred_hspace = [get_avg_gap(plots_by_col, is_horizontal=False)]
        inferred_wspace = [get_avg_gap(plots_by_row, is_horizontal=True)]

        new_inferred_grid_config = GridConfig(
            rows=rows,
            cols=cols,
            row_ratios=[1.0] * rows,
            col_ratios=[1.0] * cols,
            margins=inferred_margins,
            gutters=Gutters(hspace=inferred_hspace, wspace=inferred_wspace),
        )

        self.logger.debug(f"Inferred GridConfig: {new_inferred_grid_config}")
        return new_inferred_grid_config

    def get_active_engine(self) -> LayoutEngine:
        """Returns the currently active layout engine."""
        if self._application_model.current_layout_config.mode == LayoutMode.FREE_FORM:
            return self._free_engine
        elif self._application_model.current_layout_config.mode == LayoutMode.GRID:
            return self._grid_engine
        else:
            self.logger.error(
                f"Unknown layout mode: {self._application_model.current_layout_config.mode}"
            )
            return self._free_engine

    def set_layout_mode(self, mode: LayoutMode):
        """
        Sets the active layout mode in the ApplicationModel.
        """
        current_config = self._application_model.current_layout_config
        current_mode = current_config.mode
        if current_mode == mode:
            self.logger.debug(f"Layout mode already {mode.value}. No change needed.")
            return

        self.logger.info(
            f"Attempting to switch active layout mode from {current_mode.value} to {mode.value}."
        )
        if isinstance(current_config, GridConfig):
            self._last_grid_config = current_config
        elif isinstance(current_config, FreeConfig):
            self._last_free_form_config = current_config

        if mode == LayoutMode.GRID:
            if self._last_grid_config is None:
                self.logger.debug(
                    "No last grid config found for active mode, creating minimal grid config."
                )
                self._last_grid_config = self._create_minimal_grid_config()
            self._application_model.current_layout_config = self._last_grid_config
            self.logger.debug(
                f"Active layout mode set to GRID with config: {self._last_grid_config}."
            )

        elif mode == LayoutMode.FREE_FORM:
            # Transition to FREE_FORM: use the last known free form config
            self._application_model.current_layout_config = self._last_free_form_config
            self.logger.debug("Active layout mode set to FREE_FORM.")

        self._event_aggregator.publish(Events.ACTIVE_LAYOUT_MODE_CHANGED, mode=mode)
        self.logger.debug(
            "Publishing ACTIVE_LAYOUT_MODE_CHANGED event from set_layout_mode."
        )
        self._event_aggregator.publish(
            Events.LAYOUT_CONFIG_CHANGED, config=current_config
        )  # TODO: Not sure what needs to go in as config
        self.logger.info(f"Active layout mode successfully switched to {mode.value}.")


    def update_grid_config_and_apply(
        self, new_grid_config: GridConfig
    ) -> dict[PlotID, Rect]:
        """
        Updates the current GridConfig in the ApplicationModel and LayoutManager,
        then calculates and returns the new geometries for all plots.
        This method is intended to be called by commands or other internal mechanisms
        that directly provide a complete GridConfig object.
        """
        self.logger.info(f"LayoutManager updating grid config to: {new_grid_config}")
        self._application_model.current_layout_config = new_grid_config
        self._last_grid_config = (
            new_grid_config  # Update stored last grid config for next time
        )

        self._event_aggregator.publish(
            Events.ACTIVE_LAYOUT_MODE_CHANGED, mode=LayoutMode.GRID
        )
        self.logger.debug("Publishing ACTIVE_LAYOUT_MODE_CHANGED event for GRID mode.")
        self._event_aggregator.publish(
            Events.LAYOUT_CONFIG_CHANGED, config=new_grid_config
        )

        all_plots = list(
            self._application_model.scene_root.all_descendants(of_type=PlotNode)
        )
        if not all_plots:
            return {}

        # GridEngine returns PHYSICAL (CM) geometries
        plot_geometries, _, _ = self._grid_engine.calculate_geometries(
            all_plots, new_grid_config
        )
        
        self.logger.debug(
            f"Final updated_grid_config margins: {new_grid_config.margins}"
        )
        self.logger.debug(
            f"Final updated_grid_config gutters: {new_grid_config.gutters}"
        )

        return plot_geometries

    def perform_align(self, plots: list[PlotNode], edge: str) -> dict[PlotID, Rect]:
        """
        Performs alignment operation on selected plots using the FreeLayoutEngine.
        Raises ValueError if not in Free-Form mode.
        """
        if self._application_model.current_layout_config.mode != LayoutMode.FREE_FORM:
            self.logger.warning(
                "Attempted align operation while not in FREE_FORM mode. Returning empty geometries."
            )
            return {}

        if isinstance(self._free_engine, FreeFormLayoutCapabilities):
            return self._free_engine.perform_align(plots, edge)
        else:
            self.logger.error(
                "FreeLayoutEngine does not support FreeFormLayoutCapabilities as expected for perform_align."
            )
            return {}

    def perform_distribute(
        self, plots: list[PlotNode], axis: str
    ) -> dict[PlotID, Rect]:
        """
        Performs distribution operation on selected plots using the FreeLayoutEngine.
        Raises ValueError if not in Free-Form mode.
        """
        if self._application_model.current_layout_config.mode != LayoutMode.FREE_FORM:
            self.logger.warning(
                "Attempted distribute operation while not in FREE_FORM mode. Returning empty geometries."
            )
            return {}

        if isinstance(self._free_engine, FreeFormLayoutCapabilities):
            return self._free_engine.perform_distribute(plots, axis)
        else:
            self.logger.error(
                "FreeLayoutEngine does not support FreeFormLayoutCapabilities as expected for perform_distribute."
            )
            return {}

    def infer_grid_parameters(self):
        """
        Infers sensible grid parameters (rows, cols, margins, gutters) from the current
        free-form plot positions and updates the model.
        This does NOT apply the layout to the canvas immediately but updates the UI fields.
        # TODO: The method name is kind of confusing when we already have infer_grid_config_from_plots
        """
        self.logger.info("LayoutManager received request to infer grid parameters.")

        # Ensure active layout mode is GRID
        if self._application_model.current_layout_config.mode != LayoutMode.GRID:
            self.logger.debug(
                "Active layout mode not GRID, switching to GRID before inferring parameters."
            )
            self.set_layout_mode(LayoutMode.GRID)

        all_plots = list(
            self._application_model.scene_root.all_descendants(of_type=PlotNode)
        )
        if not all_plots:
            self.logger.warning("No plots in scene to infer grid from.")
            return

        # Infer a new GridConfig based on geometric analysis of free-form plots
        # _last_grid_config is guaranteed to be non-None here because set_layout_mode initializes it.
        new_inferred_grid_config = self.infer_grid_config_from_plots(
            all_plots, self._last_grid_config
        )

        # Update _last_grid_config with the inferred config
        self._last_grid_config = new_inferred_grid_config

        # Emit signal to update UI fields
        self._event_aggregator.publish(
            Events.GRID_CONFIG_PARAMETERS_CHANGED, grid_config=new_inferred_grid_config
        )
        self.logger.info(f"Inferred grid parameters: {new_inferred_grid_config}")

    def get_optimized_grid_config(self) -> Optional[GridConfig]:
        """
        Calculates and returns an optimized GridConfig based on Matplotlib's
        constrained_layout, without applying it to the model.
        Returns None if no plots are available for optimization.
        """
        self.logger.info("LayoutManager calculating optimized grid config.")

        # Ensure active layout mode is GRID for calculation context
        if self._application_model.current_layout_config.mode != LayoutMode.GRID:
            self.logger.debug(
                "Active layout mode not GRID, switching to GRID before optimizing layout."
            )
            self.set_layout_mode(LayoutMode.GRID)

        current_grid_config: GridConfig = self._last_grid_config

        all_plots = list(
            self._application_model.scene_root.all_descendants(of_type=PlotNode)
        )
        if not all_plots:
            self.logger.warning("No plots in scene to optimize layout for.")
            return None

        # Use calculate_geometries with constrained optimization
        _, calculated_margins, calculated_gutters = (
            self._grid_engine.calculate_geometries(
                all_plots, current_grid_config, use_constrained_optimization=True
            )
        )

        # Create the optimized config
        optimized_grid_config = GridConfig(
            rows=current_grid_config.rows,
            cols=current_grid_config.cols,
            row_ratios=current_grid_config.row_ratios,
            col_ratios=current_grid_config.col_ratios,
            margins=calculated_margins,
            gutters=calculated_gutters,
        )
        return optimized_grid_config

    def update_grid_layout_parameters(
        self,
        rows: Optional[int] = None,
        cols: Optional[int] = None,
        margin: Optional[float] = None,
        gutter: Optional[float] = None,
        margin_top: Optional[float] = None,
        margin_bottom: Optional[float] = None,
        margin_left: Optional[float] = None,
        margin_right: Optional[float] = None,
        hspace_str: Optional[str] = None,
        wspace_str: Optional[str] = None,
    ) -> dict[PlotID, Rect]:
        """
        Updates the current GridConfig with new parameters and applies the layout.
        If rows or cols are None, they will be inferred from the number of plots.
        This method always uses the last known GridConfig as its base for updates.
        It can update old single margin/gutter values or new granular margin/gutter values.
        """
        self.logger.info(
            f"Updating grid layout parameters: rows={rows}, cols={cols}, "
            f"margin_old={margin}, gutter_old={gutter}, "
            f"margin_top={margin_top}, margin_bottom={margin_bottom}, "
            f"margin_left={margin_left}, margin_right={margin_right}, "
            f"hspace_str='{hspace_str}', wspace_str='{wspace_str}'"
        )
        self.logger.debug(
            f"Current _last_grid_config before update: {self._last_grid_config}"
        )

        # Ensure active layout mode is GRID
        if self._application_model.current_layout_config.mode != LayoutMode.GRID:
            self.logger.debug(
                "Active layout mode not GRID, switching to GRID before updating parameters."
            )
            self.set_layout_mode(LayoutMode.GRID)

        base_grid_config: GridConfig = self._last_grid_config
        effective_margins = base_grid_config.margins
        final_margins = Margins(
            top=margin_top if margin_top is not None else effective_margins.top,
            bottom=(
                margin_bottom if margin_bottom is not None else effective_margins.bottom
            ),
            left=margin_left if margin_left is not None else effective_margins.left,
            right=margin_right if margin_right is not None else effective_margins.right,
        )

        effective_gutters = base_grid_config.gutters
        final_hspace = effective_gutters.hspace
        final_wspace = effective_gutters.wspace

        if hspace_str is not None:
            try:
                final_hspace = [
                    float(x.strip()) for x in hspace_str.split(",") if x.strip()
                ]
            except ValueError:
                self.logger.warning(
                    f"Invalid hspace_str format: '{hspace_str}'. Keeping old hspace."
                )
        if wspace_str is not None:
            try:
                final_wspace = [
                    float(x.strip()) for x in wspace_str.split(",") if x.strip()
                ]
            except ValueError:
                self.logger.warning(
                    f"Invalid wspace_str format: '{wspace_str}'. Keeping old wspace."
                )

        final_gutters = Gutters(hspace=final_hspace, wspace=final_wspace)

        all_plots = list(
            self._application_model.scene_root.all_descendants(of_type=PlotNode)
        )
        num_plots = len(all_plots)
        
        if (rows is None or rows == 0) or (cols is None or cols == 0):
            inferred_rows, inferred_cols = self._infer_grid_dimensions(len(all_plots))
            rows = rows or inferred_rows
            cols = cols or inferred_cols
            self.logger.debug(
                f"Inferred grid dimensions: {rows}x{cols} for {num_plots} plots."
            )

        new_grid_config = GridConfig(
            rows=rows or base_grid_config.rows,
            cols=cols or base_grid_config.cols,
            row_ratios=base_grid_config.row_ratios,
            col_ratios=base_grid_config.col_ratios,
            margins=final_margins,
            gutters=final_gutters,
        )

        return self.update_grid_config_and_apply(new_grid_config)

    def get_current_layout_geometries(
        self, plots: list[PlotNode]
    ) -> dict[PlotID, Rect]:
        """
        Returns the calculated geometries for the given plots in FRACTIONAL space.
        Translates from the model's PHYSICAL (CM) space.
        """
        active_engine = self.get_active_engine()
        # Engines now return PHYSICAL (CM) geometries
        phys_geometries, _, _ = active_engine.calculate_geometries(
            plots, 
            self._application_model.current_layout_config,
            self._application_model.figure_size
        )
        
        fig_w, fig_h = self._application_model.figure_size
        fractional_geometries = {}
        
        for pid, rect in phys_geometries.items():
            fx = CoordinateService.transform_value(
                rect.x, CoordinateSpace.PHYSICAL, CoordinateSpace.FRACTIONAL_FIG, figure_size_cm=fig_w
            )
            fy = CoordinateService.transform_value(
                rect.y, CoordinateSpace.PHYSICAL, CoordinateSpace.FRACTIONAL_FIG, figure_size_cm=fig_h
            )
            fw = CoordinateService.transform_value(
                rect.width, CoordinateSpace.PHYSICAL, CoordinateSpace.FRACTIONAL_FIG, figure_size_cm=fig_w
            )
            fh = CoordinateService.transform_value(
                rect.height, CoordinateSpace.PHYSICAL, CoordinateSpace.FRACTIONAL_FIG, figure_size_cm=fig_h
            )
            fractional_geometries[pid] = Rect(fx, fy, fw, fh)
            
        return fractional_geometries

    def _parse_float_list_from_config(
        self, key: str, default: list[float]
    ) -> list[float]:
        """Helper to parse a config value."""
        value = self._config_service.get(key, default)
        self.logger.debug(
            f"[_parse_float_list_from_config] Key: {key}, Raw Value: {value}, Type: {type(value)}"
        )
        if isinstance(value, str):
            try:
                # Attempt to parse a string like "[0.1, 0.2]" or "0.1, 0.2"
                if value.startswith("[") and value.endswith("]"):
                    value = value[1:-1]  # Remove brackets

                parsed_list = [float(x.strip()) for x in value.split(",") if x.strip()]
                self.logger.debug(
                    f"[_parse_float_list_from_config] Parsed string to list: {parsed_list}"
                )
                return parsed_list
            except ValueError:
                self.logger.warning(
                    f"Could not parse '{value}' for config key '{key}' as a list of floats. Using default: {default}"
                )
                return default
        elif isinstance(value, (int, float)):  # Handle single numeric value
            self.logger.debug(
                f"[_parse_float_list_from_config] Wrapped single numeric value in list: {[float(value)]}"
            )
            return [float(value)]
        elif isinstance(value, list):
            # Ensure all elements in the list are floats
            try:
                float_list = [float(x) for x in value]
                self.logger.debug(
                    f"[_parse_float_list_from_config] Converted list elements to floats: {float_list}"
                )
                return float_list
            except ValueError:
                self.logger.warning(
                    f"List for config key '{key}' contains non-float elements. Using default: {default}"
                )
                return default
        else:  # Fallback for unexpected types
            self.logger.warning(
                f"Unexpected type '{type(value).__name__}' for config key '{key}'. Using default: {default}"
            )
            return default

    def _infer_grid_dimensions(self, num_plots: int) -> tuple[int, int]:
        """
        Infers sensible grid rows and columns based on the number of plots.
        Aims for a square-ish layout.
        # TODO: How is this different from the calculations in grid_layout_engine?
        # TODO: This needs unit testing
        """
        if num_plots <= 0:
            return 1, 1

        # Try to find two factors that are close to each other
        # Start from sqrt and work down
        sqrt_n = int(num_plots**0.5)
        for i in range(sqrt_n, 0, -1):
            if num_plots % i == 0:
                return i, num_plots // i  # rows, cols

        # If num_plots is prime or cannot be easily factored, default to num_plots x 1
        return num_plots, 1

    def _create_minimal_grid_config(self) -> GridConfig:
        """
        Helper to create a minimal GridConfig instance.
        This serves as the initial/fallback grid configuration when no specific
        grid layout has been loaded or inferred.
        Values are sourced from ConfigService or reasonable hardcoded defaults.
        # TODO: Remove these hard coded default values
        """
        rows = self._config_service.get(
            "layout.default_grid_rows", 1
        )  # Default to 1x1 if config missing
        cols = self._config_service.get(
            "layout.default_grid_cols", 1
        )  # Default to 1x1 if config missing

        m_top = self._config_service.get("layout.grid_margin_top", 1.5)
        m_bottom = self._config_service.get("layout.grid_margin_bottom", 1.5)
        m_left = self._config_service.get("layout.grid_margin_left", 1.5)
        m_right = self._config_service.get("layout.grid_margin_right", 1.5)

        hspace = self._parse_float_list_from_config("layout.grid_hspace", [0.5])
        wspace = self._parse_float_list_from_config("layout.grid_wspace", [0.5])

        minimal_margins = Margins(top=m_top, bottom=m_bottom, left=m_left, right=m_right)
        minimal_gutters = Gutters(hspace=hspace, wspace=wspace)

        return GridConfig(
            rows=rows,
            cols=cols,
            row_ratios=[1.0] * rows,
            col_ratios=[1.0] * cols,
            margins=minimal_margins,
            gutters=minimal_gutters,
        )
