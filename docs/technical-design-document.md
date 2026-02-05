## Epic: Configuration Management

This epic focuses on externalizing various application settings, user preferences, and content layouts into configurable files, moving away from hardcoded values. This enhances flexibility, maintainability, and user customizability, ensuring the application scales gracefully for future features.

### Feature: Application-Level Defaults (Base Configuration)
**Description:** Externalize application-wide default settings, "magic strings", and initial values into a `configs/default_config.yaml` file. This provides a stable, easily modifiable baseline for the application's core behavior, independent of code changes.

**Planned Implementation:**

1.  **Create `configs/default_config.yaml`:**
    *   **Task:** Create a new directory `configs/` in the project root.
    *   **Task:** Create the `default_config.yaml` file within `configs/`.
    *   **Task:** Populate `default_config.yaml` with the following initial structure and example values. This structure includes application metadata, UI/window defaults, Matplotlib figure defaults, layout/grid defaults, paths/resources, processing defaults, tool defaults, and debugging options.
        ```yaml
        # Application Metadata
        app_name: "SciFig"
        version: "1.0.0"
        organization: "YourOrganization" # Used for QSettings
        website: "https://www.scifig.org"
        authors:
          - "Your Name"
        license: "MIT"

        # UI/Window Defaults
        window_title_prefix: "SciFig - "
        default_window_geometry:
          x: 50
          y: 50
          width: 800
          height: 600
        default_toolbar_area: "LeftToolBarArea" # Corresponds to Qt.ToolBarArea.LeftToolBarArea
        default_dock_widget_area_properties: "RightDockWidgetArea" # Corresponds to Qt.DockWidgetArea.RightDockWidgetArea
        default_dock_widget_area_history: "LeftDockWidgetArea" # Example for future
        splash_screen_path: "src/assets/images/splash.png" # Example for future
        theme: "dark" # "dark", "light", etc.

        # Matplotlib Figure Defaults
        figure:
          default_width: 8.5
          default_height: 6
          default_dpi: 150
          default_facecolor: "white"
          default_edgecolor: "black" # Example for future
          subplot_left: 0.125 # Example for future
          subplot_right: 0.9 # Example for future
          subplot_bottom: 0.11 # Example for future
          subplot_top: 0.88 # Example for future
          subplot_wspace: 0.2 # Example for future
          subplot_hspace: 0.2 # Example for future
          axes_facecolor: "white" # Example for future
          axes_edgecolor: "black" # Example for future
          font_family: "sans-serif" # Example for future
          font_size: 10 # Example for future
          line_width: 1.0 # Example for future
          marker_size: 6.0 # Example for future

        # Layout & Grid Defaults
        layout:
          default_margin: 10
          default_gutter: 5
          max_recent_files: 10
          default_template: "2x2_default.json" # Points to a file in configs/layouts

        # Paths & Resources
        paths:
          icon_base_dir: "src/assets/icons"
          layout_templates_dir: "configs/layouts"
          project_extension: ".sci"
          default_save_location: "~Documents/SciFig Projects" # Default for user, can be overridden by QSettings

        # Processing Defaults
        processing:
          default_delimiter: "\t"
          default_comment_char: "#"
          max_file_size_mb: 100
          max_lines_preview: 1000

        # Tool Defaults
        tool:
          default_active_tool: "Selection" # Name of the tool
          selection:
            default_color: "red"
          zoom:
            zoom_factor: 1.15
            scroll_factor: 1 # In units of notches

        # Debugging/Developer Options
        debug:
          log_level: "INFO" # "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"
          enable_dev_tools: false
          show_perf_metrics: false
        ```

2.  **Add `PyYAML` to Dependencies:**
    *   **Task:** Add `pyyaml` to `requirements.txt`.
    *   **Task:** Add `PyYAML` to `pyproject.toml` (if using Poetry/Flit).

3.  **Create `src/config_service.py`:**
    *   **Task:** Create a new file `src/config_service.py`.
    *   **Task:** Implement a `ConfigService` class in this file.
        *   It should be responsible for loading the `default_config.yaml` at initialization.
        *   Implement a method `get(key_path: str, default=None)` that allows accessing nested configuration values using a dot-separated string (e.g., `config.get("figure.default_width")`).
        *   Consider making it a singleton or a module-level instance for easy access, or passing it via dependency injection.
        *   Handle file not found or parsing errors gracefully, falling back to hardcoded defaults or raising specific exceptions.
    *   **Task:** Create basic unit tests for `ConfigService` (e.g., `tests/test_config_service.py`) to ensure it loads and retrieves values correctly.

4.  **Modify `src/application_assembler.py`:**
    *   **Task:** Import `ConfigService`.
    *   **Task:** In `ApplicationAssembler.__init__`, instantiate `ConfigService`.
    *   **Task:** In `_assemble_core_components`, modify the `figure` creation to use values from `ConfigService`:
        ```python
        # old: figure = Figure(figsize=(8.5, 6), dpi=150, facecolor='white')
        # new:
        figure_width = self._config_service.get("figure.default_width", 8.5)
        figure_height = self._config_service.get("figure.default_height", 6)
        figure_dpi = self._config_service.get("figure.default_dpi", 150)
        figure_facecolor = self._config_service.get("figure.default_facecolor", "white")
        figure = Figure(figsize=(figure_width, figure_height), dpi=figure_dpi, facecolor=figure_facecolor)
        ```
    *   **Task:** Pass the `ConfigService` instance to other components (e.g., `ApplicationModel`, `MainController`) that will need access to application defaults during their construction.

5.  **Refactor `src/constants.py`:**
    *   **Task:** Modify `IconPath` and `ToolName` (and any other constants) to retrieve their values from the `ConfigService` instance (passed in or accessed globally if singleton). This might involve changing their implementation to be more dynamic (e.g., functions that return paths based on config).
    *   **Task:** Remove hardcoded values that are now in `default_config.yaml`.

6.  **Modify `src/controllers/main_controller.py`:**
    *   **Task:** Update `__init__` to accept the `ConfigService` instance.
    *   **Task:** Store `ConfigService` as a member variable `self._config_service`.
    *   **Task:** Replace hardcoded values for `default_margin`, `default_gutter`, and `MAX_RECENT_FILES` with values retrieved from `ConfigService`.

**Testing Plan:**
*   **Unit Tests (`tests/test_config_service.py`):**
    *   Verify `ConfigService` loads valid YAML.
    *   Test `get()` method for various key paths (nested, non-existent, default values).
    *   Test error handling for invalid YAML or non-existent files.
*   **Integration Tests (`tests/test_application_assembler.py`, `tests/test_main_window.py`):**
    *   Verify `ApplicationAssembler` successfully initializes `ConfigService` and uses its values for `Figure` creation (e.g., check `figure.get_figwidth()` after assembly).
    *   Verify `main_controller` uses config values for layout defaults.
    *   Ensure the application starts up correctly and the UI elements (e.g., toolbars) are initialized with paths/names derived from the config.
*   **Manual Verification:**
    *   Change values in `default_config.yaml` (e.g., default window size, figure facecolor) and verify that the application reflects these changes on startup.

**Risks & Mitigations:**
*   **Risk:** Circular dependencies if `ConfigService` tries to access components that depend on it during its own initialization.
*   **Mitigation:** `ConfigService` should only load and provide data; it should not depend on other application components. Its instantiation should happen very early in `ApplicationAssembler`.
*   **Risk:** Performance overhead if config values are re-read excessively.
*   **Mitigation:** Load the config once at startup and pass around the `ConfigService` instance. Cache values internally if necessary.
*   **Risk:** Errors due to incorrect key paths or missing values.
*   **Mitigation:** `ConfigService.get()` should provide robust default value handling. Consider a validation layer (e.g., Pydantic model for the config itself) for the `default_config.yaml` to ensure it always conforms to an expected schema.

### Feature: Customizable UI Layout (User-Level Preferences)
**Description:** Enable the application to save and restore the user's preferred main window geometry, toolbar positions, and dock widget states using Qt's `QSettings` mechanism. This ensures a persistent and personalized workspace.

**Planned Implementation:**

1.  **Modify `src/views/main_window.py`:**
    *   **Task:** Import `QSettings` from `PySide6.QtCore` and `QCloseEvent` from `PySide6.QtGui`.
    *   **Task:** In `MainWindow.__init__`:
        *   Instantiate `self.settings = QSettings(self._config_service.get("organization"), self._config_service.get("app_name"))`. The organization and app name should come from `ConfigService`.
        *   **Task:** After all dock widgets and toolbars have been added to the `QMainWindow` (this is crucial for `restoreState()` to work correctly), attempt to restore the state:
            ```python
            # ... after self.setCentralWidget, self.addToolBar, self.addDockWidget calls ...

            # Restore geometry and state
            geometry = self.settings.value("mainWindowGeometry")
            if geometry:
                self.restoreGeometry(geometry)
            else: # Apply default geometry if no saved state
                default_geom = self._config_service.get("default_window_geometry")
                if default_geom:
                    self.setGeometry(default_geom["x"], default_geom["y"], default_geom["width"], default_geom["height"])

            state = self.settings.value("mainWindowState")
            if state:
                self.restoreState(state)
            else: # Apply default toolbar/dock areas if no saved state
                # This would involve explicitly setting default toolbar and dock widget areas
                # if they were not set during their initial creation.
                # Since toolbars and dock widgets are already added with default positions,
                # this 'else' block might be primarily for future complex default layouts.
                pass # For now, relying on initial placement from Assembler
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
    *   (Optional) Delete the `QSettings` file/registry entry for SciFig to verify that default geometry is applied on first run.
*   **Integration Tests:**
    *   A simple integration test could launch the application, programmatically move/resize elements, simulate close, and then relaunch to assert the state is restored. This might be complex for initial implementation.

**Risks & Mitigations:**
*   **Risk:** `restoreState()` might not work correctly if dock widgets or toolbars are not yet created when it's called.
*   **Mitigation:** Ensure `restoreState()` is called *after* all relevant UI elements have been added to the `QMainWindow` in `MainWindow.__init__`.
*   **Risk:** Conflicts between application defaults and user settings.
*   **Mitigation:** `QSettings` values should always take precedence over application defaults. The `ConfigService` provides the fallback if `QSettings` has no value.

### Feature: Externalized Content Layouts (Project-Level Templates)
**Description:** Replace the hardcoded logic for creating layouts (e.g., the "2x2 layout") with a system that loads predefined layout templates from external JSON files. This allows for flexible and extensible canvas content arrangements.

**Planned Implementation:**

1.  **Create `configs/layouts` Directory and Layout Templates:**
    *   **Task:** Create a new directory `configs/layouts` in the project root.
    *   **Task:** Create `2x2_default.json` (and potentially other layout files like `vertical_split.json`) within `configs/layouts`.
    *   **Task:** Populate `2x2_default.json` with a serialized `GroupNode` structure, similar to the `.sci` file content but only containing the layout definition.
        ```json
        {
          "type": "GroupNode",
          "name": "2x2 Layout",
          "geometry": {"x": 0.0, "y": 0.0, "width": 1.0, "height": 1.0}, # Full canvas
          "children": [
            {
              "type": "PlotNode",
              "name": "Plot 1",
              "geometry": { "x": 0.0, "y": 0.0, "width": 0.5, "height": 0.5 },
              "plot_properties": { /* default properties, e.g., line color, style */ }
            },
            {
              "type": "PlotNode",
              "name": "Plot 2",
              "geometry": { "x": 0.5, "y": 0.0, "width": 0.5, "height": 0.5 },
              "plot_properties": { /* default properties */ }
            },
            {
              "type": "PlotNode",
              "name": "Plot 3",
              "geometry": { "x": 0.0, "y": 0.5, "width": 0.5, "height": 0.5 },
              "plot_properties": { /* default properties */ }
            },
            {
              "type": "PlotNode",
              "name": "Plot 4",
              "geometry": { "x": 0.5, "y": 0.5, "width": 0.5, "height": 0.5 },
              "plot_properties": { /* default properties */ }
            }
          ]
        }
        ```
    *   **Task:** Ensure the `plot_properties` within the template are suitable defaults or placeholders.

2.  **Modify `src/controllers/main_controller.py`:**
    *   **Task:** Update `__init__` to accept the `ConfigService` instance.
    *   **Task:** Store `ConfigService` as a member variable `self._config_service`.
    *   **Task:** Refactor `create_new_layout()`:
        *   Get the `default_template` path from `self._config_service.get("layout.default_template")`.
        *   Construct the full path to the template file using `pathlib` and `self._config_service.get("paths.layout_templates_dir")`.
        *   Load and parse the JSON file.
        *   Use `scene_node.node_factory(template_data)` (from `src/models/nodes/scene_node.py`) to deserialize the JSON into a `GroupNode`.
        *   Clear the existing `self._model.scene_root` and replace it with the loaded `GroupNode` (or append the children of the loaded `GroupNode` to the existing root).
        *   Emit `self._model.modelChanged.emit()`.
    *   **Task:** (Future consideration) Add a method `create_layout_from_template(template_name: str)` that takes a template name, loads the corresponding file, and applies it. This would be called from the "New figure from template" menu item.

3.  **Modify `src/application_assembler.py`:**
    *   **Task:** Pass the `ConfigService` instance to the `MainController` constructor.

**Testing Plan:**
*   **Unit Tests for `main_controller` (`tests/controllers/test_main_controller.py`):**
    *   Mock `ConfigService` to return specific template paths and data.
    *   Test `create_new_layout` to ensure it loads the correct template, deserializes it into `SceneNode` objects, and updates the `ApplicationModel`'s `scene_root` correctly.
    *   Verify `modelChanged` signal is emitted.
*   **Integration Tests:**
    *   Launch the application, create a new layout, and visually verify that the 2x2 layout (or whatever is in `2x2_default.json`) is correctly displayed.
    *   Modify `2x2_default.json` and verify the changes are reflected when a new layout is created.

**Risks & Mitigations:**
*   **Risk:** Errors in parsing JSON layout files or schema mismatches with `node_factory`.
*   **Mitigation:** Add robust error handling during JSON loading and deserialization. Use schema validation for layout JSONs if they become complex.
*   **Risk:** `plot_properties` within the template might be incomplete or conflict with application defaults.
*   **Mitigation:** Ensure `plot_properties` in templates define clear base states. The `PlotNode` constructor should merge these with its own defaults.

### Feature: Clean up "Magic Strings" (Refactor `src/constants.py`)
**Description:** Systematically replace hardcoded literal values (e.g., icon paths, tool names) across the codebase with references to configuration values provided by the `ConfigService`.

**Planned Implementation:**

1.  **Modify `src/constants.py`:**
    *   **Task:** Update `IconPath` and `ToolName` to dynamically fetch values from the `ConfigService`. This might involve changing them from simple enums to classes or functions that query the config.
    *   **Task:** Ensure `ConfigService` is accessible (e.g., passed to `constants.py` via a setter function or globally accessible if `ConfigService` is a singleton).
    *   **Task:** Remove any hardcoded strings or values that are now in `default_config.yaml`.

2.  **Iterate and Replace:**
    *   **Task:** Perform a project-wide search for hardcoded strings and values (e.g., "Selection", "Direct_Select", various paths).
    *   **Task:** Replace these with calls to `ConfigService.get()` where appropriate.
    *   **Task:** Focus initially on constants identified in the `default_config.yaml` example (e.g., `default_margin`, `default_gutter`, tool names, icon paths).

3.  **Modify other files as necessary:**
    *   **Task:** Update any file that directly uses the removed constants from `src/constants.py` to now access values via `ConfigService`.

**Testing Plan:**
*   **Regression Tests:**
    *   Run all existing unit and integration tests after each set of "magic string" replacements to ensure no functionality is broken.
*   **Manual Verification:**
    *   Visually inspect the UI to ensure icons are loading correctly, tool names are displayed as expected, and default layout behaviors match the config.

**Risks & Mitigations:**
*   **Risk:** Missing some "magic strings" or introducing typos in key paths.
*   **Mitigation:** A systematic search (e.g., using `grep` or IDE search) for literals and careful review. Unit tests for `ConfigService` will catch key path errors.
*   **Risk:** Refactoring `src/constants.py` might break many existing references.
*   **Mitigation:** Change `constants.py` incrementally, or provide backward compatibility (e.g., old constants redirect to `ConfigService` values) if the migration is too disruptive.