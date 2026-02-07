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

## Epic: Dynamic Layout UI & Enhanced Grid Interaction

**Overarching Goal:** To enhance the user experience of the Layout Management System by integrating dynamic layout controls directly into the properties panel, providing clearer mode indication, and improving the "snap to grid" functionality.

---

### Feature 1: Dynamic Properties Panel Content
**Description:** Refactor the properties panel (`PropertiesView`) to dynamically display either layout-specific controls (by default) or plot-specific properties (when a plot with data is selected).

**Planned Implementation:**
1.  **Modify `src/ui/panels/properties_panel.py`:**
    *   **Task:** Update `PropertiesPanel.__init__` to accept `layout_ui_factory: LayoutUIFactory`, `layout_manager: LayoutManager`, and `layout_controller: LayoutController`. Store these as instance variables.
    *   **Task:** Implement a slot (e.g., `_update_content(self)`) that responds to changes in `ApplicationModel.selectionChanged` and `LayoutManager.layoutModeChanged`. This method will be responsible for clearing the current content and rebuilding it based on the current state.
    *   **Task:** Within `_update_content`:
        *   Clear any existing UI elements from the properties panel.
        *   **Condition 1: Single PlotNode with Data Selected:** If `self.model.selection` contains exactly one item which is a `PlotNode` and `plot_node.data` is not `None`:
            *   Call `self.properties_ui_factory.build_properties_ui(plot_node)` to get the plot-specific controls.
            *   Add these controls to the properties panel's layout.
        *   **Condition 2: Otherwise (Default/Layout Controls):**
            *   Call `self.layout_ui_factory.build_layout_controls(self.layout_manager.layout_mode, self.layout_controller, self)` to get the layout-specific controls.
            *   Add these controls to the properties panel's layout.
    *   **Task:** In `PropertiesPanel.__init__`, connect `self.model.selectionChanged` to `self._update_content` and `self.layout_manager.layoutModeChanged` to `self._update_content`.
    *   **Task:** Trigger `self._update_content()` once at the end of `PropertiesPanel.__init__` to set the initial state.
2.  **Modify `src/core/composition_root.py`:**
    *   **Task:** When instantiating `PropertiesPanel` in `_assemble_main_window` or `_create_properties_dock` (if applicable), pass the new dependencies: `layout_ui_factory`, `layout_manager`, and `layout_controller`.
3.  **Refine `src/ui/windows/main_window.py`:**
    *   **Task:** The separate `self.layout_menu` and its associated `_update_layout_menu` slot and connections can now be removed or significantly simplified, as the primary layout controls are moving to the properties panel. The "Layout" menu might still exist in the main menu for global layout actions, but not for dynamic controls.

**Testing Plan (Feature 1):**
*   **Unit Tests (`tests/ui/panels/test_properties_panel.py`):**
    *   `test_properties_panel_displays_layout_controls_by_default`: Verify that on initialization, the `PropertiesPanel` calls `layout_ui_factory.build_layout_controls`.
    *   `test_properties_panel_displays_plot_properties_on_single_plot_selection_with_data`: Mock a selection of a single `PlotNode` with data, verify `properties_ui_factory.build_properties_ui` is called.
    *   `test_properties_panel_displays_layout_controls_on_multiple_selection`: Mock multiple `PlotNode`s selected, verify `layout_ui_factory.build_layout_controls` is called.
    *   `test_properties_panel_displays_layout_controls_on_single_plot_selection_no_data`: Mock a single `PlotNode` without data selected, verify `layout_ui_factory.build_layout_controls` is called.
    *   `test_properties_panel_updates_on_layout_mode_change`: Mock a layout mode change, verify `layout_ui_factory.build_layout_controls` is called with the new mode.

---

### Feature 2: Clearer Layout Mode Toggle & SVG Icon Integration
**Description:** Implement a more intuitive "Free Form / Grid Layout" toggle in the UI (likely in `MainWindow`'s menu bar or toolbar) and ensure all layout actions generated by `LayoutUIFactory` use SVG icons.

**Planned Implementation:**
1.  **Modify `src/ui/windows/main_window.py`:**
    *   **Task:** In `MainWindow.__init__`, create a new `QAction` (e.g., `layout_mode_toggle_action`) for toggling between Free Form and Grid layout modes. Set `checkable=True` for this action.
    *   **Task:** Set its initial `checked` state based on `self._layout_manager.layout_mode == LayoutMode.GRID`.
    *   **Task:** Connect `layout_mode_toggle_action.toggled` signal to a new slot in `layout_controller` (e.g., `layout_controller.toggle_layout_mode(checked)`).
    *   **Task:** Connect `self._layout_manager.layoutModeChanged` signal to a slot in `MainWindow` (e.g., `_update_layout_mode_toggle_ui`) that updates the `layout_mode_toggle_action`'s text and checked state.
    *   **Task:** Add this action to a suitable menu (e.g., a "View" menu, or a simplified "Layout" menu that only contains this toggle).
2.  **Modify `src/controllers/layout_controller.py`:**
    *   **Task:** Add a new method `toggle_layout_mode(self, checked: bool)`:
        *   If `checked` is `True`, call `self._layout_manager.set_layout_mode(LayoutMode.GRID)`.
        *   If `checked` is `False`, call `self._layout_manager.set_layout_mode(LayoutMode.FREE_FORM)`.
3.  **Modify `src/ui/factories/layout_ui_factory.py`:**
    *   **Task:** Update `_build_free_form_controls` and `_build_grid_layout_controls` methods to ensure all `QAction`s use SVG icons (loaded via `IconPath` from `ConfigService`) instead of plain text where appropriate. This means updating `QAction` constructors to accept `QIcon`.
    *   **Task:** Remove the "Switch to Grid Mode" and "Switch to Free-Form Mode" actions, as these are now handled by the main toggle.
4.  **Modify `src/shared/constants.py`:**
    *   **Task:** Add new constants in `IconPath` (if not already present) for all layout-related actions that will now have SVG icons (e.g., align_left, distribute_horizontal, grid_layout_on, free_layout_off).
5.  **Modify `configs/default_config.yaml`:**
    *   **Task:** Add corresponding entries for the new SVG icon paths under `paths.icon_base_dir` and `tool_icons` or a new `layout_icons` section.

**Testing Plan (Feature 2):**
*   **Unit Tests (`tests/ui/windows/test_main_window.py`):**
    *   `test_layout_mode_toggle_action_exists`: Verify the new action is created and checkable.
    *   `test_layout_mode_toggle_action_updates_layout_controller`: Verify its `toggled` signal connects to `layout_controller.toggle_layout_mode`.
    *   `test_layout_mode_toggle_action_reflects_manager_state`: Verify `_update_layout_mode_toggle_ui` correctly updates the action's checked state and text.
*   **Unit Tests (`tests/controllers/test_layout_controller.py`):**
    *   `test_toggle_layout_mode_sets_layout_manager_mode`: Verify `toggle_layout_mode` correctly calls `layout_manager.set_layout_mode`.
*   **Unit Tests (`tests/ui/factories/test_layout_ui_factory.py`):**
    *   `test_build_free_form_controls_uses_svg_icons`: Verify actions have `QIcon` objects set.
    *   `test_build_grid_layout_controls_uses_svg_icons`: Verify actions have `QIcon` objects set.

---

### Feature 3: Enhanced "Snap to Grid" Functionality
**Description:** When transitioning from free-form to grid mode, the system will automatically infer suitable grid dimensions (rows/columns) and assign existing plots to these cells.

**Planned Implementation:**
1.  **Modify `src/services/layout_manager.py`:**
    *   **Task:** In `set_layout_mode`, ensure that when transitioning from `FREE_FORM` to `GRID`, `self._grid_engine.snap_plots_to_grid(all_plots, self._create_default_grid_config())` is called. The `_create_default_grid_config()` provides base margin/gutter, but the `snap_plots_to_grid` should infer rows/cols/ratios.
    *   **Task:** Update `_application_model.current_layout_config` with the `GridConfig` returned by `snap_plots_to_grid`.
2.  **Modify `src/models/layout/layout_engines.py`:**
    *   **Task:** Refine `GridLayoutEngine.snap_plots_to_grid(self, plots: List[PlotNode], current_grid_config: GridConfig) -> GridConfig`:
        *   **Heuristic 1: Determine Rows/Cols:**
            *   Calculate `num_plots = len(plots)`.
            *   Implement a heuristic to determine `inferred_rows` and `inferred_cols`. A simple approach is `inferred_rows = max(1, round(num_plots**0.5))` and `inferred_cols = (num_plots + inferred_rows - 1) // inferred_rows`.
            *   Ensure `inferred_rows` and `inferred_cols` are at least 1.
        *   **Heuristic 2: Sort Plots for Assignment:**
            *   Sort `plots` based on their current (x,y) positions. A common stable sort is by y-coordinate (descending for top-to-bottom) then x-coordinate (ascending for left-to-right): `sorted_plots = sorted(plots, key=lambda p: (-p.geometry[1], p.geometry[0]))`.
        *   **Heuristic 3: Infer Ratios:**
            *   For initial implementation, `inferred_row_ratios = [1.0 / inferred_rows] * inferred_rows` and `inferred_col_ratios = [1.0 / inferred_cols] * inferred_cols`.
        *   **Task:** Create and return a new `GridConfig` with these `inferred_rows`, `inferred_cols`, `inferred_row_ratios`, `inferred_col_ratios`, and existing `margin`/`gutter` from `current_grid_config`.
3.  **Add Test Stubs (Feature 3):**
    *   **Unit Tests (`tests/services/test_layout_manager.py`):**
        *   `test_set_layout_mode_free_to_grid_calls_snap_and_updates_config`: Verify `_grid_engine.snap_plots_to_grid` is called and `application_model.current_layout_config` is updated to the inferred `GridConfig`.
    *   **Unit Tests (`tests/models/layout/test_layout_engines.py`):**
        *   `test_grid_layout_engine_snap_plots_to_grid_basic_inference`: Test with varying numbers of plots (0, 1, 4, 5, 6, 9) to ensure correct `rows` and `cols` are inferred.
        *   `test_grid_layout_engine_snap_plots_to_grid_sorts_plots`: Test with plots at various positions to verify correct sorting before assignment.

---

### Feature 4: Live Update Performance & Command Wrappers for Grid Parameters
**Description:** Implement smooth, interactive adjustment of grid parameters (rows, columns, margins, gutters) in the properties panel, ensuring updates are debounced and changes are undoable.

**Planned Implementation:**
1.  **Modify `src/ui/factories/layout_ui_factory.py`:**
    *   **Task:** In `_build_grid_layout_controls`, for each grid parameter UI element (e.g., `QSpinBox` for rows/cols, `QDoubleSpinBox` for margin/gutter):
        *   Connect its relevant signal (e.g., `valueChanged`, `editingFinished`) to a *single debounced slot* in `layout_controller` (e.g., `layout_controller.on_grid_parameter_changed`).
        *   The debouncing mechanism should be implemented using `QTimer.singleShot` or similar.
    *   **Task:** The debounced slot will gather the *current values of all grid parameters* from the UI controls before calling `layout_controller.adjust_grid_parameters()`.
2.  **Modify `src/controllers/layout_controller.py`:**
    *   **Task:** Add a new method `on_grid_parameter_changed(self)` (the debounced slot). This will collect the values from the UI elements (passed as a dictionary or tuple) and call `adjust_grid_parameters`.
    *   **Task:** Add or refine `adjust_grid_parameters(self, rows: int, cols: int, margin: float, gutter: float, row_ratios: List[float] | None = None, col_ratios: List[float] | None = None)`:
        *   This method will construct a new `GridConfig` with the provided parameters.
        *   It will create a new `ChangeGridParametersCommand` (see below) passing the old and new `GridConfig`.
        *   Execute the command via `self.command_manager.execute_command()`.
3.  **Create `src/services/commands/change_grid_parameters_command.py`:**
    *   **Task:** Implement `ChangeGridParametersCommand(BaseCommand)`:
        *   `__init__(self, model: ApplicationModel, old_grid_config: GridConfig, new_grid_config: GridConfig, description: str)`: Stores the model, old config, and new config.
        *   `execute(self)`: Sets `model.current_layout_config = self._new_grid_config`.
        *   `undo(self)`: Sets `model.current_layout_config = self._old_grid_config`.
4.  **Add Test Stubs (Feature 4):**
    *   **Unit Tests (`tests/ui/factories/test_layout_ui_factory.py`):**
        *   `test_grid_parameter_controls_connected_to_debounced_slot`: Verify grid parameter UI elements connect to the debounced slot in `layout_controller`.
    *   **Unit Tests (`tests/controllers/test_layout_controller.py`):**
        *   `test_adjust_grid_parameters_executes_command`: Verify `adjust_grid_parameters` creates and executes a `ChangeGridParametersCommand`.
        *   `test_on_grid_parameter_changed_debounces_calls`: Mock `QTimer.singleShot` to verify debouncing behavior.
    *   **Unit Tests (`tests/services/commands/test_change_grid_parameters_command.py`):**
        *   `test_execute_change_grid_parameters_command`: Verify `execute` correctly updates `model.current_layout_config`.
        *   `test_undo_change_grid_parameters_command`: Verify `undo` correctly restores `model.current_layout_config`.

### General Refinements/Considerations for the Epic:

*   **Error Handling and User Feedback:** Implement robust validation for user input in grid parameter fields (e.g., non-negative numbers, valid ratios). Provide clear visual feedback (e.g., invalid input highlighting, status bar messages).
*   **Default Configuration:** Add new configuration keys to `configs/default_config.yaml` for default grid parameter values (if different from existing ones) and all new icon paths.
*   **Documentation:** Update `docs/technical-design-document.md` to include this new Epic and its features. Update any other relevant documentation (`README.md`, `backlog.md`).
