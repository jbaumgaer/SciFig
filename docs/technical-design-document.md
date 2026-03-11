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

## Epic: Architectural Refinement - Decoupling Rendering and View

This epic focuses on strictly enforcing the "Passive View" MVP protocol by transforming the `Renderer` into a stateless domain service and removing all Matplotlib backend and coordinate transformation logic from the `CanvasWidget`. This is a prerequisite for headless reproducibility and high-resolution exports.

### Feature: Stateless Rendering Service with Harvested Pipeline
**Description:** Refactor the `Renderer` into a stateless service that performs explicit placement using "baked" coordinates from the `LayoutManager`.

**Core Principle: Shadow Rendering & Harvesting**
The `LayoutManager` owns the Matplotlib layout solver (`constrained_layout`). It calculates absolute geometries using a "Shadow Figure" and harvests the results. The `Renderer` never calls the layout solver; it only performs fixed placement.

**Property Categorization:**
*   **Layout-Affecting (Triggers Shadow Optimization):** `figsize`, `dpi`, `title`, `xlabel`, `ylabel`, `legend`, `tick_params`, `hspace`, `wspace`, `margins`, adding/removing nodes.
*   **Purely Aesthetic (Fast Path):** `color`, `linestyle`, `linewidth`, `alpha`, `marker`, `markersize`, `markerfacecolor`, `fontfamily`, `xlim`, `ylim`, `grid`, and data updates.

**Planned Implementation:**

1.  **Modify `Renderer` (`src/ui/renderers/renderer.py`):**
    *   **Task:** Implement a persistent `_node_artist_registry` (node_id -> Matplotlib objects) to support incremental updates.
    *   **Task:** Replace `figure.add_subplot()` with `figure.add_axes(rect)` to ensure Matplotlib skips internal layout logic.
    *   **Task:** Update `render(figure, root_node, selection, geometries, hint=None)`:
        *   If `hint` is Aesthetic: Update the registry artist and call `draw_idle()`.
        *   Else: Rebuild the figure using the explicit `geometries`.

2.  **Modify `LayoutManager` (`src/services/layout_manager.py`):**
    *   **Task:** Implement "Shadow Optimization": Create a temporary figure matching the real figure's DPI/Size, populate with titles/labels, run `execute_constrained_layout()`, and harvest `ax.get_position()`.
    *   **Task:** Return a `LayoutReport` containing absolute `Rects` and effective `Margins/Gutters`.

3.  **Refactor Events:**
    *   **`Events.NODE_LAYOUT_RECONCILED`:** Payload: `GridConfig`. Target: `LayoutTab` (UI sync) and `ApplicationModel`.
    *   **`Events.NODE_GEOMETRY_CHANGED`:** Payload: `dict[node_id, Rect]`. Target: `Renderer` and `ApplicationModel`.

4.  **Modify Application Entry Point (`main.py`):**
    *   **Task:** Move `matplotlib.use("QtAgg")` here to support headless overrides.

### Feature: Standardized Coordinate Transformations
**Description:** Centralize Matplotlib-to-Figure coordinate transformations to remove "leaks" in the View and Tools.

**Planned Implementation:**

1.  **Modify `src/shared/utils.py`:**
    *   **Task:** Add standardized helper functions for converting between Screen (Pixels), Figure (Normalized 0-1), and Data coordinates.

2.  **Update Interactive Tools (`src/services/tools/`):**
    *   **Task:** Refactor `SelectionTool` to use the new utility functions.

3.  **Modify `CanvasWidget` (`src/ui/widgets/canvas_widget.py`):**
    *   **Task:** Remove all coordinate transformation logic. The widget only emits raw events with pixel coordinates.

**Testing Plan:**
*   **Unit Tests (`tests/ui/renderers/test_renderer.py`):** Verify `Renderer` renders correctly given explicit geometries without an active layout solver.
*   **Unit Tests (`tests/services/test_layout_manager.py`):** Verify "Shadow Optimization" harvests correct coordinates.
*   **Integration Tests:** Verify that changing a label updates the model via the shadow-harvest cycle, while changing a color uses the direct fast-path.

**Risks & Mitigations:**
*   **Risk:** Text size mismatch between Shadow and Real figure.
*   **Mitigation:** Ensure Shadow Figure perfectly syncs DPI, figsize, and FontProperties with the Real figure before harvesting.
