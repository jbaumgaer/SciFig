# Technical Design Document 2 (TDD_2)

This document provides detailed implementation and testing plans for subsequent features, following the initial configuration management. It is structured into Epics and Features, with atomic tasks, testing plans, and risk assessments.

---

## Epic: Configuration Management (Continued)

### Feature: Externalized Content Layouts (Project-Level Templates)
**Description:** Replace the hardcoded logic for creating layouts (e.g., the "2x2 layout") with a system that loads predefined layout templates from external JSON files. This allows for flexible and extensible canvas content arrangements. When a new layout is applied, existing plots are intelligently redistributed onto the new layout slots, preserving data where possible.

**Planned Implementation:**

1.  **Create `configs/layouts` Directory and Default Layout Template:**
    *   **Task:** Create a new directory `configs/layouts` in the project root.
    *   **Task:** Create `2x2_default.json` within `configs/layouts`.
    *   **Task:** Populate `2x2_default.json` with a serialized `GroupNode` structure, defining 4 `PlotNode` children with `geometry` and placeholder `plot_properties`. Example content:
        ```json
        {
          "type": "GroupNode",
          "name": "2x2 Layout",
          "geometry": {"x": 0.0, "y": 0.0, "width": 1.0, "height": 1.0},
          "children": [
            {
              "type": "PlotNode",
              "name": "Plot 1",
              "geometry": { "x": 0.02, "y": 0.52, "width": 0.46, "height": 0.46 },
              "plot_properties": { "plot_type": "LINE", "title": "Top-Left" }
            },
            {
              "type": "PlotNode",
              "name": "Plot 2",
              "geometry": { "x": 0.52, "y": 0.52, "width": 0.46, "height": 0.46 },
              "plot_properties": { "plot_type": "LINE", "title": "Top-Right" }
            },
            {
              "type": "PlotNode",
              "name": "Plot 3",
              "geometry": { "x": 0.02, "y": 0.02, "width": 0.46, "height": 0.46 },
              "plot_properties": { "plot_type": "SCATTER", "title": "Bottom-Left" }
            },
            {
              "type": "PlotNode",
              "name": "Plot 4",
              "geometry": { "x": 0.52, "y": 0.02, "width": 0.46, "height": 0.46 },
              "plot_properties": { "plot_type": "LINE", "title": "Bottom-Right" }
            }
          ]
        }
        ```
    *   **Task:** Ensure `plot_properties` includes suitable defaults or placeholders for new plots.

2.  **Modify `PlotProperties` and `PlotNode` for `update_from_dict`:**
    *   **Task:** In `src/models/nodes/plot_properties.py`, add a method `update_from_dict(self, data: dict, exclude_geometry: bool = False)` to `BasePlotProperties`. This method should iterate through the `data` dictionary and update the corresponding attributes of the `PlotProperties` instance. The `exclude_geometry` flag is for when we only want to update non-geometry properties during redistribution.
    *   **Task:** In `src/models/nodes/plot_node.py`, update `to_dict` to accept `exclude_geometry: bool = False` argument. This ensures that when extracting plot state, geometry can be optionally omitted.

3.  **Refactor `src/controllers/main_controller.py`:**
    *   **Task:** Modify `create_new_layout()` method:
        *   Extract existing plot data and properties (data, `PlotProperties` excluding `geometry`) from `self.model.scene_root.all_descendants()`.
        *   Clear `self.model.scene_root`'s children.
        *   Get the `default_template` name from `self._config_service.get("layout.default_template")`.
        *   Construct the full path to the template file using `pathlib` and `self._config_service.get("paths.layout_templates_dir")`.
        *   Load and parse the JSON file using `json.load()`.
        *   Use `scene_node.node_factory(template_data)` to deserialize the JSON into a `GroupNode` hierarchy (this will be the `new_layout_root_node`).
        *   Iterate through the `PlotNode`s within `new_layout_root_node`. For each new slot, try to assign an extracted plot state from the previous step (simple first-come, first-served matching).
            *   If an extracted plot state is assigned, update the `new_slot_node`'s `data` and call `new_slot_node.plot_properties.update_from_dict()` (preserving the new slot's geometry).
        *   Add `new_layout_root_node` (or its children) to `self.model.scene_root`.
        *   Emit `self.model.modelChanged.emit()`.
    *   **Task:** (Future consideration): Add a method `load_layout_template(template_name: str)` to encapsulate the loading and processing logic, to be reused by a template selection UI.

**Testing Plan:**
*   **Unit Tests (`tests/models/test_plot_properties.py`, `tests/models/nodes/test_plot_node.py`):**
    *   Verify `PlotProperties.update_from_dict` correctly updates properties and respects `exclude_geometry`.
    *   Verify `PlotNode.to_dict` correctly omits geometry when `exclude_geometry=True`.
*   **Unit Tests (`tests/controllers/test_main_controller.py`):**
    *   Mock `ConfigService` to return specific template paths and data.
    *   Mock `node_factory` to return predefined `SceneNode` hierarchies.
    *   Test `create_new_layout` to ensure:
        *   It extracts existing plot data/properties before clearing.
        *   It loads the correct template.
        *   It deserializes the template into `SceneNode` objects.
        *   It intelligently redistributes existing plot data/properties onto new slots (e.g., first N plots are assigned).
        *   It updates the `ApplicationModel`'s `scene_root` correctly.
        *   `modelChanged` signal is emitted.
        *   Handles scenarios where new layout has more/fewer slots than existing plots.
*   **Integration Tests:**
    *   Launch the application, load some data into plots, then trigger `create_new_layout`. Visually verify data is preserved and redistributed on the new 2x2 layout.
    *   Change `2x2_default.json` and verify changes are reflected.

**Risks & Mitigations:**
*   **Risk:** Errors in parsing JSON layout files or schema mismatches with `node_factory`.
*   **Mitigation:** Add robust error handling during JSON loading and deserialization. Use schema validation for layout JSONs if they become complex.
*   **Risk:** `plot_properties` within the template might be incomplete or conflict with existing plot properties.
*   **Mitigation:** Ensure `PlotProperties.update_from_dict` handles missing keys gracefully. The `PlotNode` constructor should merge template properties with its own defaults.
*   **Risk:** Complexities in correctly handling `GroupNode` vs `PlotNode` hierarchy during redistribution, especially when `all_descendants()` is used.
*   **Mitigation:** Thorough unit tests for `all_descendants()` and the redistribution logic. Ensure `node_factory` correctly rebuilds the hierarchy.

---

### Feature: Layout Template Selection UI and Previews
**Description:** Implement a modal dialog that allows users to select from available layout templates, displaying a small SVG preview of each template on hover, before applying a new layout to the canvas.

**Planned Implementation:**

1.  **Add `ConfigService` Entry for Layout Preview Cache:**
    *   **Task:** Add `paths.layout_preview_cache_dir: "cache/layout_previews"` to `default_config.yaml`.

2.  **Create `src/layout_preview_generator.py`:**
    *   **Task:** Create a new file `src/layout_preview_generator.py`.
    *   **Task:** Implement a class `LayoutPreviewGenerator`.
        *   `__init__(self, config_service: ConfigService, renderer: Renderer)`: Takes `ConfigService` for paths and `Renderer` for drawing.
        *   `_generate_preview_svg(self, template_data: dict, output_path: Path)`:
            *   Create a temporary headless Matplotlib `Figure` (small `figsize`, `dpi`).
            *   Use `node_factory` to deserialize `template_data` into a temporary `SceneNode` hierarchy.
            *   Use the `Renderer` to render this temporary scene onto the temporary figure.
            *   Save the figure to `output_path` as an SVG.
        *   `get_preview_svg_path(self, template_name: str) -> Path`:
            *   Construct path to the template JSON.
            *   Construct expected preview SVG path in `layout_preview_cache_dir`.
            *   If SVG doesn't exist or is outdated (e.g., template JSON is newer), call `_generate_preview_svg`.
            *   Return the path to the SVG.

3.  **Create `src/ui/layout_selection_dialog.py`:**
    *   **Task:** Create a new file `src/ui/layout_selection_dialog.py`.
    *   **Task:** Implement a `LayoutSelectionDialog(QDialog)`.
        *   `__init__(self, config_service: ConfigService, layout_preview_generator: LayoutPreviewGenerator, parent: QWidget = None)`: Takes `ConfigService` and the `LayoutPreviewGenerator`.
        *   **Layout Discovery:** On initialization, scan `ConfigService.get("paths.layout_templates_dir")` for `.json` files. For each, extract the template name (from filename or "name" key in JSON).
        *   **UI Elements:**
            *   A `QListWidget` or `QListView` to display template names.
            *   A `QLabel` or `QSvgWidget` for displaying the preview.
            *   "OK" and "Cancel" buttons.
        *   **Hover Event:** Connect `QListWidget.itemEntered` signal to a slot that calls `layout_preview_generator.get_preview_svg_path()` for the hovered template and loads the SVG into the preview widget.
        *   **Selection:** Store the selected template name when "OK" is pressed.
        *   **Property:** `selected_template_name` to be read by the caller.

4.  **Modify `src/controllers/main_controller.py`:**
    *   **Task:** Update `__init__` to accept `layout_preview_generator: LayoutPreviewGenerator`.
    *   **Task:** Modify `create_new_layout()` (or create a new `select_and_apply_layout()` method):
        *   Instantiate `LayoutSelectionDialog`.
        *   If `dialog.exec_() == QDialog.Accepted` and `dialog.selected_template_name` is available:
            *   Call the new `load_layout_template(dialog.selected_template_name)` method (from Task 3. of F3).

5.  **Modify `src/application_assembler.py`:**
    *   **Task:** In `_assemble_core_components` (or a new `_assemble_layout_components`), instantiate `LayoutPreviewGenerator(config_service, renderer)`.
    *   **Task:** Pass the `LayoutPreviewGenerator` instance to `MainController`.

**Testing Plan:**
*   **Unit Tests (`tests/test_layout_preview_generator.py`):**
    *   Mock `ConfigService` and `Renderer`.
    *   Test `_generate_preview_svg` to ensure it creates a valid SVG file for a given template.
    *   Test `get_preview_svg_path` to verify caching logic (generates only if needed).
    *   Verify correct SVG path is returned.
*   **Unit Tests (`tests/ui/test_layout_selection_dialog.py`):**
    *   Mock `ConfigService` and `LayoutPreviewGenerator`.
    *   Test dialog instantiation, template listing, and selection.
    *   Test that hovering over an item triggers `layout_preview_generator.get_preview_svg_path()` and the preview display updates.
*   **Integration Tests:**
    *   Launch app, click "New Layout", verify dialog appears with templates and functional previews. Select a template and verify it's applied.

**Risks & Mitigations:**
*   **Risk:** Performance of SVG generation for previews, especially with complex layouts or many templates.
*   **Mitigation:** Implement caching (`layout_preview_generator`). Generate previews during development build step, or lazily on first access. Keep preview SVG sizes small.
*   **Risk:** `QSvgWidget` or `QSvgRenderer` compatibility issues or performance.
*   **Mitigation:** Test across different Qt versions. Consider using `QLabel` with `QPixmap` if SVG performance is an issue.
*   **Risk:** `node_factory` might not correctly deserialize templates with `plot_properties`.
*   **Mitigation:** Thorough testing of `node_factory` with various template JSONs.

---

### Feature: Customizable UI Layout (User-Level Preferences)
**Description:** Enable the application to save and restore the user's preferred main window geometry, toolbar positions, and dock widget states using Qt's `QSettings` mechanism. This ensures a persistent and personalized workspace.

**Planned Implementation:**

1.  **Modify `src/views/main_window.py`:**
    *   **Task:** Import `QSettings` from `PySide6.QtCore` and `QCloseEvent` from `PySide6.QtGui`.
    *   **Task:** In `MainWindow.__init__`:
        *   Instantiate `self.settings = QSettings(self._config_service.get("organization"), self._config_service.get("app_name"))`.
        *   **Task:** After all dock widgets and toolbars have been added to the `QMainWindow`, attempt to restore the state:
            ```python
            # ... after self.setCentralWidget, self.addToolBar, self.addDockWidget calls ...

            # Restore geometry and state
            geometry = self.settings.value("mainWindowGeometry")
            if geometry:
                self.restoreGeometry(geometry)
            else: # Apply default geometry from config if no saved state
                default_geom = self._config_service.get("default_window_geometry")
                if default_geom:
                    self.setGeometry(default_geom["x"], default_geom["y"], default_geom["width"], default_geom["height"])

            state = self.settings.value("mainWindowState")
            if state:
                self.restoreState(state)
            # else: no specific action needed if default toolbar/dock positions are handled by initial creation
            ```
    *   **Task:** Override `MainWindow.closeEvent(self, event: QCloseEvent)`:
        ```python
        class MainWindow(QMainWindow):
            # ...
            def closeEvent(self, event: QCloseEvent):
                self.settings.setValue("mainWindowGeometry", self.saveGeometry())
                self.settings.setValue("mainWindowState", self.saveState())
                super().closeEvent(event)
        ```
    *   **Task:** Update `MainWindow.__init__` signature to accept `config_service: ConfigService`.
    *   **Task:** Store `config_service` as a member variable `self._config_service`.

2.  **Modify `src/application_assembler.py`:**
    *   **Task:** Pass the `ConfigService` instance to the `MainWindow` constructor.

**Testing Plan:**
*   **Manual Verification:**
    *   Run the application. Resize and reposition the main window. Move and resize dock widgets. Close the application. Re-open and verify that the window and dock widget layout are restored to their previous state.
    *   Delete `QSettings` for SciFig to verify that default geometry from `default_config.yaml` is applied on first run.
*   **Integration Tests:**
    *   A simple integration test could launch the application, programmatically move/resize elements, simulate close, and then relaunch to assert the state is restored. This might be complex for initial implementation.

**Risks & Mitigations:**
*   **Risk:** `restoreState()` might not work correctly if dock widgets or toolbars are not yet created when it's called.
*   **Mitigation:** Ensure `restoreState()` is called *after* all relevant UI elements have been added to the `QMainWindow` in `MainWindow.__init__`.
*   **Risk:** Conflicts between application defaults and user settings.
*   **Mitigation:** `QSettings` values should always take precedence over application defaults. The `ConfigService` provides the fallback if `QSettings` has no value.

---

### Feature: Integrating Matplotlib's Layout Engines (Togglable Auto-Layout)
**Description:** Provide a togglable option to enable Matplotlib's automatic layout adjustment (`constrained_layout`) for figures, allowing plots to intelligently resize and reposition to prevent overlapping elements. When disabled, the last calculated layout parameters will be saved and used as fixed values.

**Planned Implementation:**

1.  **Modify `default_config.yaml`:**
    *   **Task:** Add `figure.auto_layout_enabled_default: true` to define the default state.

2.  **Modify `ApplicationModel` (`src/models/application_model.py`):**
    *   **Task:** Add a property `self.auto_layout_enabled: bool` initialized from `ConfigService.get("figure.auto_layout_enabled_default")` or a user setting from `QSettings` (if F2 is already done).
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

3.  **Modify `Renderer` (`src/views/renderer.py`):**
    *   **Task:** Update `__init__` to accept `config_service: ConfigService` and `application_model: ApplicationModel`.
    *   **Task:** Store references to `config_service` and `application_model`.
    *   **Task:** In the `render(figure: Figure, root_node: SceneNode, selection: List[SceneNode])` method:
        *   Before drawing, check `application_model.auto_layout_enabled`.
        *   If `True`: Apply `figure.set_constrained_layout(True)` (or `figure.tight_layout()`).
        *   If `False` and `application_model.figure_subplot_params` is not `None`: Apply these explicit parameters using `figure.subplots_adjust(**application_model.figure_subplot_params)`.
    *   **Task:** Connect `application_model.autoLayoutChanged` to a redraw trigger.

4.  **Add UI Toggle:**
    *   **Task:** In `src/views/main_window.py`, add a `QAction` (e.g., in the "Plot" menu) for "Enable Auto Layout" with `checkable=True`.
    *   **Task:** Connect this action's `toggled` signal to `application_model.set_auto_layout_enabled()`.
    *   **Task:** Initialize the action's checked state from `application_model.auto_layout_enabled`.

5.  **Modify `src/application_assembler.py`:**
    *   **Task:** Pass `ConfigService` to `ApplicationModel` constructor.
    *   **Task:** Pass `ApplicationModel` and `ConfigService` to `Renderer` constructor.

**Testing Plan:**
*   **Unit Tests (`tests/models/test_application_model.py`):**
    *   Test `set_auto_layout_enabled` for correct state changes.
    *   Verify `autoLayoutChanged` signal emission.
    *   Mock Matplotlib `Figure` and test that `capture_current_layout_params` correctly calls `figure.tight_layout()` and captures `subplotpars`.
*   **Unit Tests (`tests/views/test_renderer.py`):**
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
**Description:** Implement the ability for users to add new plots to the canvas. When a new plot is added, the user will be presented with options to either intelligently redistribute all existing plots (including the new one) into a new optimal arrangement or to add the new plot as a free-form element that can be manually positioned. This includes a `CustomLayoutEngine` to handle dynamic plot sizing and positioning.

**Planned Implementation:**

1.  **Create `src/layout_engine.py`:**
    *   **Task:** Create a new file `src/layout_engine.py`.
    *   **Task:** Implement a class `CustomLayoutEngine`.
        *   `__init__(self, config_service: ConfigService)`: Takes `ConfigService` for defaults (margins, gutters).
        *   `calculate_grid_layout(self, plot_nodes: List[PlotNode], num_rows: int, num_cols: int) -> Dict[PlotNode, Tuple[float, float, float, float]]`:
            *   Takes a list of `PlotNode`s and target grid dimensions.
            *   Calculates new `(left, bottom, width, height)` `geometry` for each `PlotNode` based on equal division, respecting configurable margins and gutters.
            *   Returns a dictionary mapping `PlotNode`s to their new geometries.
        *   `calculate_auto_packed_layout(self, plot_nodes: List[PlotNode]) -> Dict[PlotNode, Tuple[float, float, float, float]]`:
            *   (Future/Advanced) Implements a more intelligent "packing" algorithm to fill available space, potentially resizing plots based on some heuristic.
            *   For initial implementation, `calculate_grid_layout` will suffice.

2.  **Modify `ApplicationModel` (`src/models/application_model.py`):**
    *   **Task:** Add a method `add_plot(self, plot_node: PlotNode)` that adds a new plot.
    *   **Task:** Add a method `redistribute_plots(self, layout_algorithm: str = "grid")`:
        *   Uses `CustomLayoutEngine` to calculate new geometries for all current `PlotNode`s.
        *   Updates the `geometry` of each `PlotNode` in `self.scene_root` via `ChangePropertyCommand`.
        *   Emits `modelChanged`.

3.  **Modify `MainController` (`src/controllers/main_controller.py`):**
    *   **Task:** Update `__init__` to accept `custom_layout_engine: CustomLayoutEngine`.
    *   **Task:** Store `custom_layout_engine` as a member variable.
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

4.  **Modify `src/application_assembler.py`:**
    *   **Task:** Instantiate `CustomLayoutEngine(config_service)`.
    *   **Task:** Pass `CustomLayoutEngine` to `MainController`.

**Testing Plan:**
*   **Unit Tests (`tests/test_layout_engine.py`):**
    *   Mock `ConfigService`.
    *   Test `calculate_grid_layout` with various numbers of plots and grid dimensions to ensure correct geometry calculation (positive width/height, non-overlapping, respecting margins/gutters).
    *   Test edge cases (e.g., 1 plot, many plots).
*   **Unit Tests (`tests/models/test_application_model.py`):**
    *   Test `add_plot` correctly adds to `scene_root` and emits `modelChanged`.
    *   Test `redistribute_plots` ensures all plots get new geometries and `modelChanged` is emitted. Mock `CustomLayoutEngine`.
*   **Integration Tests:**
    *   Launch app, create a layout.
    *   Add a new plot and choose "Distribute evenly", verify all plots resize/reposition.
    *   Add a new plot and choose "Add free-form", verify new plot appears with default geometry and others remain fixed.

**Risks & Mitigations:**
*   **Risk:** `CustomLayoutEngine` calculation errors leading to invalid geometries (e.g., negative width/height).
*   **Mitigation:** Thorough unit tests for `calculate_grid_layout` and edge cases. Implement validation checks in `PlotNode.geometry` setter.
*   **Risk:** Performance with a large number of plots during redistribution.
*   **Mitigation:** Optimize `CustomLayoutEngine` algorithms. Consider using a `QProgressDialog` for very long calculations.

---

### Feature: Drag-and-Drop Plot Reassignment
**Description:** Enable users to interactively reassign plots on the canvas by dragging and dropping them from one location to another. This includes swapping plots between existing slots or placing them into empty template slots.

**Planned Implementation:**

1.  **Modify `CanvasWidget` (`src/views/canvas_widget.py`):**
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

2.  **New Commands (`src/commands/rearrange_plot_command.py`, `src/commands/swap_plots_command.py`):**
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
*   **Unit Tests (`tests/commands/test_rearrange_plot_command.py`, `tests/commands/test_swap_plots_command.py`):**
    *   Test `execute()` and `undo()` for correct state changes in `ApplicationModel`.
    *   Verify `modelChanged` signal is emitted.
*   **Unit Tests (`tests/views/test_canvas_widget.py`):**
    *   Mock `CanvasController` and `ApplicationModel`.
    *   Test `mousePressEvent`, `mouseMoveEvent`, `mouseReleaseEvent` for correctly detecting drags and identifying drop targets.
*   **Integration Tests:**
    *   Launch app, create a layout with plots.
    *   Drag one plot onto another, verify they swap positions.
    *   Drag a plot into an empty slot (if implemented), verify it moves.
    *   Verify undo/redo works for these operations.

**Risks & Mitigations:**
*   **Risk:** Complex state management during drag-and-drop, leading to visual glitches or incorrect model updates.
*   **Mitigation:** Clear separation of concerns between `CanvasWidget` (UI events), `CanvasController` (logic), and `CommandManager` (state changes). Thorough unit tests for event handling.
*   **Risk:** Performance issues with visual feedback during drag (e.g., drawing ghost image).
*   **Mitigation:** Optimize drawing routines for ghost image. Keep it simple initially.

---

### Feature: Clean up "Magic Strings" (Broader Refactor)
**Description:** Systematically replace hardcoded literal values (e.g., strings used for messages, titles, default names, tooltips, etc.) across the codebase with references to configuration values provided by the `ConfigService`. This extends beyond the initial constants cleanup done for F1.

**Planned Implementation:**

1.  **Identify Candidates:**
    *   **Task:** Perform a project-wide search for hardcoded strings and values (e.g., "Save Project", "Properties", "SciFig Project (*.sci)", "No item selected.").
    *   **Task:** Review `default_config.yaml` to identify logical categories for these strings (e.g., `ui_strings.dialog_titles.save_project`, `file_filters.project_files`).

2.  **Extend `default_config.yaml`:**
    *   **Task:** Add new sections and keys to `default_config.yaml` for these identified "magic strings".

3.  **Refactor Codebase:**
    *   **Task:** Replace hardcoded strings with calls to `self._config_service.get("new.config.key")` in relevant files (e.g., `MainWindow`, `PropertiesView`, `MainController`).

4.  **Modify `ConfigService` (Optional, if needed):**
    *   **Task:** If a global `ConfigService` instance (e.g., a singleton) is desired for files that don't receive it via dependency injection, implement a global accessor (e.g., a `get_global_config_service()` function) being mindful of potential issues with explicit dependency passing.

**Testing Plan:**
*   **Regression Tests:**
    *   Run all existing unit and integration tests after each set of replacements to ensure no functionality is broken.
*   **Manual Verification:**
    *   Launch the app and visually inspect all replaced strings (dialog titles, tooltips, labels) to ensure they are correctly loaded from the config.

**Risks & Mitigations:**
*   **Risk:** Introducing errors due to incorrect key paths or typos during replacement.
*   **Mitigation:** Use a systematic search and replace approach. Thorough testing after each batch of changes.
*   **Risk:** `ConfigService` might not be accessible in all required locations without complicating dependency injection.
*   **Mitigation:** Evaluate the trade-offs of global access vs. explicit passing. For simple UI strings, a module-level `get_config()` helper might be acceptable if carefully managed.
