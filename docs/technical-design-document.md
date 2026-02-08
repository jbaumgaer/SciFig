## Epic: Configuration Management

This epic focuses on externalizing various application settings, user preferences, and content layouts into configurable files, moving away from hardcoded values. This enhances flexibility, maintainability, and user customizability, ensuring the application scales gracefully for future features.

### Feature: Integrating Matplotlib's Layout Engines (Togglable Auto-Layout)
**Description:** Provide a togglable option to enable Matplotlib's automatic layout adjustment (`constrained_layout`) for figures, allowing plots to intelligently resize and reposition to prevent overlapping elements. When disabled, the last calculated layout parameters will be saved and used as fixed values.

**Planned Implementation:**

1.  **Modify `configs/default_config.yaml`:**
    *   **Task:** Add `figure.auto_layout_enabled_default: true` to define the default state.

2.  **Modify `ApplicationModel` (`src/models/application_model.py`):**
    *   **Task:** Add a property `self.auto_layout_enabled: bool` initialized from `ConfigService.get("figure.auto_layout_enabled_default")` or a user setting from `QSettings`.
    *   **Task:** Add a signal `autoLayoutChanged = Signal(bool)` that emits when `auto_layout_enabled` is changed.
    *   **Task:** Add a property `self.figure_subplot_params: dict | None` to store captured explicit parameters (initialized to `None`).
    *   **Task:** Add a method `set_auto_layout_enabled(self, enabled: bool)`:
        *   Updates `self.auto_layout_enabled`.
        *   If `enabled` is `False` and `self.auto_layout_enabled` was previously `True`:
            *   Trigger one final auto-layout (`self.figure.tight_layout()` or equivalent).
            *   Capture the current subplot parameters (`self.figure.subplotpars` or iterate axes `get_position()`) and store them in `self.figure_subplot_params`.
            *   Emit `autoLayoutChanged(False)`.
        *   If `enabled` is `True` and `self.auto_layout_enabled` was previously `False`:
            *   Clear `self.figure_subplot_params = None`.
            *   Emit `autoLayoutChanged(True)`.

3.  **Modify `Renderer` (`src/ui/renderers/renderer.py`):**
    *   **Task:** Update `__init__` to accept `config_service: ConfigService` and `application_model: ApplicationModel`.
    *   **Task:** Store references to `config_service` and `application_model`.
    *   **Task:** In the `render(figure: Figure, root_node: SceneNode, selection: List[SceneNode])` method:
        *   Before drawing, check `application_model.auto_layout_enabled`.
        *   If `True`: Apply `figure.set_constrained_layout(True)` (or `figure.tight_layout()`).
        *   If `False` and `application_model.figure_subplot_params` is not `None`: Apply these explicit parameters using `figure.subplots_adjust(**application_model.figure_subplot_params)`.
    *   **Task:** Connect `application_model.autoLayoutChanged` to a redraw trigger.

4.  **Add UI Toggle:**
    *   **Task:** In `src/ui/windows/main_window.py`, add a `QAction` (e.g., in the "Plot" menu) for "Enable Auto Layout" with `checkable=True`.
    *   **Task:** Set its initial `checked` state based on `self._layout_manager.layout_mode == LayoutMode.GRID`.
    *   **Task:** Connect this action's `toggled` signal to `application_model.set_auto_layout_enabled()`.
    *   **Task:** Initialize the action's checked state from `application_model.auto_layout_enabled`.

5.  **Modify `CompositionRoot` (`src/core/composition_root.py`):**
    *   **Task:** Pass `ConfigService` to `ApplicationModel` constructor.
    *   **Task:** Pass `ApplicationModel` and `ConfigService` to `Renderer` constructor.

**Testing Plan:**
*   **Unit Tests (`tests/models/test_application_model.py`):**
    *   Test `set_auto_layout_enabled` for correct state changes.
    *   Verify `autoLayoutChanged` signal emission.
    *   Mock Matplotlib `Figure` and test that `capture_current_layout_params` correctly calls `figure.tight_layout()` and captures `subplotpars`.
*   **Unit Tests (`tests/ui/renderers/test_renderer.py`):**
    *   Mock `ApplicationModel` to control `auto_layout_enabled` and `figure_subplot_params`.
    *   Test `render` method to ensure `figure.set_constrained_layout(True)` or `figure.subplots_adjust` is called conditionally.
*   **Integration Tests:**
    *   Launch app, toggle auto-layout on/off, verify visual changes.
    *   Add axis labels while auto-layout is on, verify plots adjust.
    *   Toggle auto-layout off, add axis labels, verify plots *do not* adjust automatically.
    *   Verify captured parameters lead to consistent layout after toggle off/on.

**Risks & Mitigations:**
*   **Risk:** `tight_layout`/`constrained_layout` can sometimes produce unexpected results, especially with complex figures.
*   **Mitigation:** Provide robust error handling around these calls. Give user options to reset layout.
*   **Risk:** Capturing `figure.subplotpars` might not be robust enough for `constrained_layout`. `constrained_layout` changes axis positions directly.
*   **Mitigation:** For `constrained_layout`, capturing `ax.get_position()` for each axis might be more reliable when converting to fixed `geometry` values. This would mean updating `PlotNode.geometry` directly rather than `figure_subplot_params`. This option is preferable for more precise control. We would need a way to map each `ax` to its corresponding `PlotNode` for this to work.

---

### Feature: Adding New Plot with Redistribution Options + Advanced Plot Redistribution
**Description:** Implement the ability for users to add new plots to the canvas. When a new plot is added, the user will be presented with options to either intelligently redistribute all existing plots (including the new one) into a new optimal arrangement or to add the new plot as a free-form element that can be manually positioned. This includes a `LayoutManager` to handle dynamic plot sizing and positioning.

**Planned Implementation:**

1.  **Modify `ApplicationModel` (`src/models/application_model.py`):**
    *   **Task:** Add a method `add_plot(self, plot_node: PlotNode)` that adds a new plot.
    *   **Task:** Add a method `redistribute_plots(self, layout_algorithm: str = "grid")`:
        *   Uses `LayoutManager` to calculate new geometries for all current `PlotNode`s.
        *   Updates the `geometry` of each `PlotNode` in `self.scene_root` via `ChangePropertyCommand`.
        *   Emits `modelChanged`.

2.  **Modify `LayoutController` (`src/controllers/layout_controller.py`):**
    *   **Task:** Update `__init__` to accept `layout_manager: LayoutManager`.
    *   **Task:** Store `layout_manager` as a member variable.
    *   **Task:** Add a new method `add_new_plot_with_options()`:
        *   Presents a `QMessageBox` or custom dialog with options: "Distribute evenly", "Add free-form".
        *   If "Distribute evenly":
            *   Creates a new `PlotNode`.
            *   Calls `application_model.add_plot(new_plot_node)`.
            *   Calls `application_model.redistribute_plots("grid")` (or the chosen algorithm).
        *   If "Add free-form":
            *   Creates a new `PlotNode` with a default `geometry` (e.g., small, central).
            *   Calls `application_model.add_plot(new_plot_node)`.
    *   **Task:** Connect a new menu action (e.g., "Plot" -> "Add Plot") to `add_new_plot_with_options()`.

3.  **Modify `CompositionRoot` (`src/core/composition_root.py`):**
    *   **Task:** Instantiate `LayoutManager(application_model, free_engine, grid_engine, config_service)`.
    *   **Task:** Pass `LayoutManager` to `LayoutController`.

**Testing Plan:**
*   **Unit Tests (`tests/models/test_application_model.py`):**
    *   Test `add_plot` correctly adds to `scene_root` and emits `modelChanged`.
    *   Test `redistribute_plots` ensures all plots get new geometries and `modelChanged` is emitted. Mock `LayoutManager`.
*   **Unit Tests (`tests/controllers/test_layout_controller.py`):**
    *   Mock `ConfigService`.
    *   Test `add_new_plot_with_options` with various numbers of plots and grid dimensions to ensure correct geometry calculation (positive width/height, non-overlapping, respecting margins/gutters).
    *   Test edge cases (e.g., 1 plot, many plots).
*   **Integration Tests:**
    *   Launch app, create a layout.
    *   Add a new plot and choose "Distribute evenly", verify all plots resize/reposition.
    *   Add a new plot and choose "Add free-form", verify new plot appears with default geometry and others remain fixed.

**Risks & Mitigations:**
*   **Risk:** `LayoutManager` calculation errors leading to invalid geometries (e.g., negative width/height).
*   **Mitigation:** Thorough unit tests for `calculate_grid_layout` and edge cases. Implement validation checks in `PlotNode.geometry` setter.
*   **Risk:** Performance with a large number of plots during redistribution.
*   **Mitigation:** Optimize `LayoutManager` algorithms. Consider using a `QProgressDialog` for very long calculations.

---

### Feature: Drag-and-Drop Plot Reassignment
**Description:** Enable users to interactively reassign plots on the canvas by dragging and dropping them from one location to another. This includes swapping plots between existing slots or placing them into empty template slots.

**Planned Implementation:**

1.  **Modify `CanvasWidget` (`src/ui/widgets/canvas_widget.py`):**
    *   **Task:** Override `mousePressEvent`, `mouseMoveEvent`, `mouseReleaseEvent` to detect drag gestures on `PlotNode`s.
    *   **Task:** Implement logic to identify the `PlotNode` under the mouse press.
    *   **Task:** Store the `PlotNode` being dragged and its initial position.
    *   **Task:** During `mouseMoveEvent` (if a drag is in progress):
        *   Visually indicate the drag (e.g., draw a semi-transparent ghost of the plot).
        *   Detect potential drop targets (other `PlotNode`s or empty `PlotNode` slots).
        *   Visually indicate potential drop targets (e.g., highlight the target slot).
    *   **Task:** In `mouseReleaseEvent` (if a drag occurred):
        *   Identify the final drop target.
        *   Based on target, construct a `Command` (e.g., `RearrangePlotCommand`, `SwapPlotsCommand`).
        *   Pass the command to `command_manager.execute_command()`.

2.  **New Commands (`src/services/commands/rearrange_plot_command.py`, `src/services/commands/swap_plots_command.py`):**
    *   **Task:** Create `RearrangePlotCommand(plot_node: PlotNode, new_geometry: Tuple[float, float, float, float])`.
    *   **Task:** Create `SwapPlotsCommand(plot_node1: PlotNode, plot_node2: PlotNode)`.
    *   **Task:** Implement `execute()` and `undo()` for these commands, ensuring `ApplicationModel` is updated and `modelChanged` is emitted.

3.  **Modify `ApplicationModel` (`src/models/application_model.py`):**
    *   **Task:** Add helper methods for finding `PlotNode`s by ID or by `geometry` (e.g., `get_plot_node_at_position(pos)`).
    *   **Task:** Add methods to `swap_plot_geometries(plot_node1: PlotNode, plot_node2: PlotNode)` or `set_plot_node_geometry(plot_node: PlotNode, new_geometry: Tuple)`.

4.  **Modify `CanvasController` (`src/controllers/canvas_controller.py`):**
    *   **Task:** Update `__init__` to accept `command_manager: CommandManager`.
    *   **Task:** Connect `CanvasWidget`'s custom drag-and-drop signals (if any are emitted) to methods in `CanvasController` that construct and execute the appropriate `Command`s.

**Testing Plan:**
*   **Unit Tests (`tests/services/commands/test_rearrange_plot_command.py`, `tests/services/commands/test_swap_plots_command.py`):**
    *   Test `execute()` and `undo()` for correct state changes in `ApplicationModel`.
    *   Verify `modelChanged` signal is emitted.
*   **Unit Tests (`tests/ui/widgets/test_canvas_widget.py`):**
    *   Mock `CanvasController` and `ApplicationModel`.
    *   Test `mousePressEvent`, `mouseMoveEvent`, `mouseReleaseEvent` for correctly detecting drags and identifying drop targets.
*   **Integration Tests:**
    *   Launch app, create a layout.
    *   Drag one plot onto another, verify they swap positions.
    *   Drag a plot into an empty slot (if implemented), verify it moves.
    *   Verify undo/redo works for these operations.

**Risks & Mitigations:**
*   **Risk:** Complex state management during drag-and-drop, leading to visual glitches or incorrect model updates.
*   **Mitigation:** Clear separation of concerns between `CanvasWidget` (UI events), `CanvasController` (logic), and `CommandManager` (state changes). Thorough unit tests for event handling.
*   **Risk:** Performance issues with visual

---

##  Epic: Dynamic Grid Layout with constrained_layout Integration


  Description: This epic aims to enhance the application's grid layout capabilities by introducing granular control over margins and gutters, leveraging
  Matplotlib's constrained_layout for intelligent automatic spacing, and adapting the UI to expose these new controls to the user. This will lead to more
  flexible and visually appealing plot arrangements.

  ---


  Feature 1: Granular Layout Configuration Model

  Description: Extend the existing GridConfig to store individual top, bottom, left, and right margins, and to support list-based horizontal and vertical
  spacing (gutters) to align with Matplotlib's GridSpec and constrained_layout functionality.


  Planned Implementation:


   1. Modify `src/shared/types.py`:
       * Task: Update the Gutters dataclass:
           * Change hspace: float to hspace: List[float] = field(default_factory=list).
           * Change wspace: float to wspace: List[float] = field(default_factory=list).
           * Ensure to_dict() and from_dict() methods correctly handle lists.
           * Reason: To accurately represent Matplotlib's ability to define varying spacing between different rows/columns.
       * Task: Add List to import from typing.


   2. Modify `src/models/layout/layout_config.py`:
       * Task: Update the GridConfig dataclass:
           * Remove margin: float and gutter: float.
           * Add margins: Margins = field(default_factory=Margins) (using the existing Margins dataclass, which already supports top, bottom, left, right).
           * Add gutters: Gutters = field(default_factory=Gutters) (using the now-modified Gutters dataclass).
           * Reason: To directly store granular layout parameters.
       * Task: Update GridConfig.to_dict():
           * Replace margin and gutter serialization with self.margins.to_dict() and self.gutters.to_dict().
           * Reason: To serialize the new nested dataclass structure.
       * Task: Update GridConfig.from_dict():
           * Replace margin and gutter deserialization with Margins.from_dict(data.get("margins", {})) and Gutters.from_dict(data.get("gutters", {})).
           * Reason: To deserialize the new nested dataclass structure.
       * Task: Add List to import from typing.

  Testing Plan:


   * Unit Tests (`tests/shared/test_types.py`):
       * test_gutters_list_serialization: Verify Gutters.to_dict() correctly serializes lists for hspace and wspace.
       * test_gutters_list_deserialization: Verify Gutters.from_dict() correctly deserializes lists for hspace and wspace.
       * test_gutters_default_empty_lists: Verify default Gutters object has empty lists for hspace and wspace.
   * Unit Tests (`tests/models/layout/test_layout_config.py`):
       * test_gridconfig_granular_params_init: Verify GridConfig initializes with Margins and Gutters objects.
       * test_gridconfig_granular_params_to_dict: Verify GridConfig.to_dict() correctly serializes nested Margins and Gutters dictionaries.
       * test_gridconfig_granular_params_from_dict: Verify GridConfig.from_dict() correctly deserializes nested Margins and Gutters.
       * test_gridconfig_from_dict_partial_data: Verify from_dict handles missing 'margins' or 'gutters' keys gracefully, falling back to defaults.

  Risks & Mitigations:


   * Risk: Backward compatibility issues if old GridConfig JSONs/YAMLs are loaded without the new 'margins' and 'gutters' keys.
   * Mitigation: from_dict methods for Margins and Gutters use .get() with default values, ensuring older configurations can still be loaded without
     crashing (though they will revert to new defaults for margins/gutters). Documentation should highlight this change.

  ---

  Feature 2: Matplotlib constrained_layout Integration for Grid Layout


  Description: Modify GridLayoutEngine to use Matplotlib's constrained_layout for calculating plot geometries, respecting the granular margin and gutter
  configurations. This includes creating Matplotlib Axes based on GridSpec, applying the layout, and extracting the final calculated positions and spacings.

  Planned Implementation:


   1. Modify `src/models/layout/layout_engine.py`:
       * Task: Update imports: Add import matplotlib.pyplot as plt, import matplotlib.gridspec as gridspec, from matplotlib.figure import Figure, from
         matplotlib.axes import Axes, from matplotlib.transforms import Bbox.
       * Task: Refactor GridLayoutEngine.calculate_geometries():
           * Decision: This method will be deprecated or refactored to simply call apply_matplotlib_grid_layout to get the final Rect values from
             Matplotlib. It's inconsistent to have a separate calculation when Matplotlib is the renderer. For this feature, we will update it to call
             apply_matplotlib_grid_layout on a temporary figure to get the geometries.
           * Reason: To ensure all grid geometry calculations leverage Matplotlib for consistency.
       * Task: Update GridLayoutEngine.apply_matplotlib_grid_layout(self, figure: Figure, plot_nodes: List[PlotNode], grid_config: GridConfig) ->
         tuple[dict[PlotID, Axes], dict[PlotID, Rect], Margins, Gutters]:
           * Grid Dimension Calculation: Keep logic for inferring rows and cols if grid_config.rows or grid_config.cols are 0.
           * `GridSpec` Creation: Pass grid_config.gutters.hspace and grid_config.gutters.wspace directly to the gridspec.GridSpec constructor. Normalize
             row_ratios and col_ratios if they are empty or don't match dimensions.
           * Clear Figure: Add figure.clear() to ensure previous axes are removed when applying a new layout.
           * Add `Axes`: Iterate through plot_nodes (sorted by approximate current position) and add Axes to the figure using gs[r_idx, c_idx]. Store PlotID
             to Axes mapping.
           * Configure `constrained_layout`:
               * Convert grid_config.margins (figure fractions) to "inches" for figure.set_constrained_layout_pads(). For instance, w_pad_left =
                 grid_config.margins.left * figure.get_figwidth(). set_constrained_layout_pads requires w_pad, h_pad, w_space, h_space parameters, which are
                 global. The GridSpec's list-based hspace/wspace will guide internal spacing.
               * Set figure.set_layout_engine('constrained').
           * Retrieve Final Geometries: Iterate through the created Axes and get their final positions using ax.get_position(), converting Bbox to Rect.
           * Retrieve Effective Margins: Calculate effective_margin_top/bottom/left/right by finding the union bounding box of all Axes and comparing it to
             the figure's extent. Return as a Margins object.
           * Retrieve Effective Gutters: This is complex. constrained_layout does not directly expose per-row/per-column effective gutters.
               * Initial Approach: For hspace and wspace, return the target lists provided to GridSpec if they were provided and valid. If not, return
                 default (e.g., empty lists or averaged single values).
               * Refined Approach (Future): Implement logic to explicitly measure the distances between adjacent Axes in each row/column to calculate the
                 actual effective list of hspace and wspace. This would involve iterating gs.get_subplot_positions(figure) and analyzing the resulting Bbox
                 objects. For the initial implementation, relying on the target GridSpec values for Gutters will be sufficient, as constrained_layout
                 respects them.
           * Return Value: Return the mpl_axes_map, final_plot_geometries, calculated_margins, and calculated_gutters.

  Testing Plan:


   * Unit Tests (`tests/models/layout/test_layout_engine.py`):
       * test_apply_matplotlib_grid_layout_basic_grid: Test with a simple GridConfig (e.g., 2x2, default margins/gutters) to ensure correct Axes creation,
         and that returned Rects are sensible.
       * test_apply_matplotlib_grid_layout_with_ratios: Test with row_ratios and col_ratios to verify Axes dimensions reflect ratios.
       * test_apply_matplotlib_grid_layout_granular_margins: Test with custom Margins (e.g., large left margin) and verify calculated_margins reflect this,
         and Axes positions are adjusted.
       * test_apply_matplotlib_grid_layout_list_gutters: Test with GridConfig.gutters providing list values for hspace/wspace and verify GridSpec is created
         correctly and calculated_gutters reflect the target values. (If direct measurement is implemented, verify actual measured values).
       * test_apply_matplotlib_grid_layout_empty_plot_nodes: Verify handling of no PlotNodes.
       * test_apply_matplotlib_grid_layout_figure_clears_axes: Verify figure.clear() is called and new axes are added.
       * test_calculate_geometries_calls_apply_matplotlib_grid_layout: Verify the refactored calculate_geometries correctly delegates to
         apply_matplotlib_grid_layout on a temporary figure.

  Risks & Mitigations:


   * Risk: Accurate conversion of GridConfig's relative Margins and Gutters to constrained_layout's specific units (inches, fractions of font size).
   * Mitigation: Thorough testing with various GridConfig values and visual inspection of generated plots. Document any limitations or non-intuitive
     behaviors. Provide clear comments in code regarding unit conversions.
   * Risk: constrained_layout can sometimes fail or produce unexpected results with very complex GridSpec definitions or when many elements are present.
   * Mitigation: Implement robust error handling around figure.set_layout_engine(). Log warnings/errors gracefully. Consider providing a "reset layout" or
     "fallback to simple layout" option in the UI.
   * Risk: Calculating effective list-based hspace/wspace accurately after constrained_layout runs might be complex without direct Matplotlib API support.
   * Mitigation: Start with returning the target values if valid. If user feedback demands more precision, invest in measuring actual distances between Axes
     bounding boxes.

  ---


  Feature 3: UI for Granular Layout Controls

  Description: Adapt the Layout section of the Properties Panel to expose granular controls for top/bottom/left/right margins and list-based
  horizontal/vertical gutters, allowing users to fine-tune layout appearance.

  Planned Implementation:


   1. Modify `src/ui/factories/layout_ui_factory.py`:
       * Task: Update _build_grid_layout_controls(self, current_grid_config: GridConfig, layout_controller: LayoutController, parent: QWidget) -> QWidget
         (assuming this method builds the grid layout specific UI).
       * Task: Replace the single 'margin' input with four QDoubleSpinBoxes for margins.top, margins.bottom, margins.left, margins.right.
           * Reason: To enable granular control.
       * Task: Replace the single 'gutter' input with two QLineEdits for gutters.hspace and gutters.wspace.
           * Reason: To allow input of comma-separated lists for per-row/per-column spacing.
           * Input Handling: Connect editingFinished signal to controller methods, which will parse the comma-separated string into List[float].
       * Task: Connect the valueChanged (for QDoubleSpinBox) and editingFinished (for QLineEdit) signals of these new widgets to a unified debounced slot in
         layout_controller (e.g., layout_controller.on_grid_param_changed).
       * Task: Initialize each widget with values from current_grid_config.margins and current_grid_config.gutters.


   2. Modify `src/controllers/layout_controller.py`:
       * Task: Update on_grid_param_changed(self, param_name: str, value: Any):
           * When param_name is "margin_top", "margin_bottom", "margin_left", "margin_right", update the corresponding field in a temporary Margins object.
           * When param_name is "hspace" or "wspace":
               * Parse the value (string) into a List[float]. Implement robust error handling for invalid input (e.g., non-numeric values, incorrect
                 format).
               * Update the corresponding field in a temporary Gutters object.
           * After collecting all changes (perhaps after a debounce period), construct a new GridConfig and execute a ChangeGridParametersCommand (as
             outlined in the TDD's Feature 4).
       * Task: Ensure the ChangeGridParametersCommand accepts the new GridConfig structure.

  Testing Plan:


   * Unit Tests (`tests/ui/factories/test_layout_ui_factory.py`):
       * test_build_grid_layout_controls_has_granular_margin_inputs: Verify 4 QDoubleSpinBoxes for margins are present and correctly initialized.
       * test_build_grid_layout_controls_has_list_gutter_inputs: Verify 2 QLineEdits for hspace and wspace are present and correctly initialized.
       * test_grid_param_inputs_connect_to_controller: Verify all new input widgets connect their signals to layout_controller.on_grid_param_changed.
   * Unit Tests (`tests/controllers/test_layout_controller.py`):
       * test_on_grid_param_changed_updates_margins: Mock UI input for margins and verify ChangeGridParametersCommand is created with correct Margins.
       * test_on_grid_param_changed_parses_hspace_wspace_lists: Mock UI input for comma-separated hspace/wspace strings and verify
         ChangeGridParametersCommand is created with correct Gutters lists.
       * test_on_grid_param_changed_invalid_gutter_input_handled: Verify error handling for non-numeric or malformed list input.

  Risks & Mitigations:


   * Risk: Complex UI for list-based input might be cumbersome for users. Input validation and parsing of comma-separated strings can be error-prone.
   * Mitigation: Provide clear input instructions in the UI (e.g., tooltips, placeholder text). Implement robust parsing logic with clear user feedback for
     invalid input. Consider an alternative UI (e.g., a custom widget with dynamically added spinboxes) if the list input proves too difficult for users.
   * Risk: Increased number of UI controls could clutter the Properties Panel.
   * Mitigation: Group related controls visually (e.g., "Margins" group box, "Gutters" group box). Use sensible default values to minimize initial user
     configuration.

  ---

  Feature 4: Enhanced "Snap to Grid" with constrained_layout


  Description: The "Snap to Grid" functionality will be improved to use Matplotlib's constrained_layout during its inference process, intelligently
  determining optimal Margins and Gutters for the inferred grid.

  Planned Implementation:


   1. Modify `src/models/layout/layout_engine.py`:
       * Task: Update GridLayoutEngine.snap_plots_to_grid(self, plots: List[PlotNode], current_grid_config: GridConfig) -> GridConfig:
           * Initial Grid Inference: Keep existing logic for inferring rows and cols based on num_plots.
           * Initial Ratios: Keep logic for inferred_row_ratios and inferred_col_ratios.
           * Ephemeral Matplotlib Figure: Create a temporary matplotlib.pyplot.figure() for the dry run. Ensure it's closed in a try...finally block.
           * Temporary `GridConfig` for Dry Run: Create a temp_grid_config_for_dry_run using the inferred rows, cols, row_ratios, col_ratios. For margins
             and gutters in this temporary config, use the current_grid_config.margins and current_grid_config.gutters as initial suggestions for
             constrained_layout.
           * Call `apply_matplotlib_grid_layout`: Call self.apply_matplotlib_grid_layout(temp_fig, plots, temp_grid_config_for_dry_run).
           * Retrieve `calculated_margins` and `calculated_gutters`: Directly use the Margins and Gutters objects returned by apply_matplotlib_grid_layout.
           * Construct New `GridConfig`: Create and return a new_grid_config using the inferred rows, cols, row_ratios, col_ratios, and the
             calculated_margins/calculated_gutters. No more averaging or max() calls are needed for these specific attributes.
           * Reason: To intelligently leverage constrained_layout's optimization for spacing when snapping to a grid.

  Testing Plan:


   * Unit Tests (`tests/models/layout/test_layout_engine.py`):
       * test_snap_plots_to_grid_uses_ephemeral_figure: Verify a temporary Matplotlib figure is created and closed.
       * test_snap_plots_to_grid_calls_apply_matplotlib_grid_layout: Verify apply_matplotlib_grid_layout is called during the dry run.
       * test_snap_plots_to_grid_inferred_margins_match_constrained_layout_output: Test with various plot arrangements (e.g., plots with long titles/labels)
         and verify the margins in the returned GridConfig are consistent with what constrained_layout would produce.
       * test_snap_plots_to_grid_inferred_gutters_match_constrained_layout_output: Test with multiple plots and verify the gutters (lists) in the returned
         GridConfig are consistent with constrained_layout's spacing decisions.
       * test_snap_plots_to_grid_handles_empty_plots: Verify it returns the current config if no plots are present.
       * test_snap_plots_to_grid_error_handling: Verify graceful handling if apply_matplotlib_grid_layout encounters an error during the dry run.


  Risks & Mitigations:


   * Risk: constrained_layout's "intelligent" determination of margins/gutters might not always align with user expectations, especially when going from
     free-form to grid.
   * Mitigation: Document the behavior clearly. Provide UI controls (Feature 3) for manual adjustment after snapping. Allow the user to "undo" the snap
     operation.
   * Risk: Performance overhead of creating a temporary Matplotlib figure and running layout solver for each "snap" operation, especially with many plots.
   * Mitigation: Profile the snap_plots_to_grid method. If performance is an issue, consider debouncing snap requests or caching results for frequently
     snapped configurations.