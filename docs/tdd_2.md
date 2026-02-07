# Technical Design Document - Phase 2 Refactoring Roadmap

## Epic: Decouple Controllers and Refactor "God Objects"

**Overarching Goal:** To refactor the monolithic `MainController` and the "smart" `PropertiesPanel` into a set of smaller, cohesive controllers (`ProjectController`, `LayoutController`, `NodeController`) that adhere to the Single Responsibility Principle. This will improve architectural clarity, testability, and maintainability.

---

### Feature 1: Create New Controllers and Move Logic (Decoupling Phase)
**Description:** Create the new controller classes and move the existing business and controller logic out of `MainController` and `PropertiesPanel`. In this initial phase, the old classes will temporarily delegate calls to the new ones, ensuring the UI remains functional and allowing for isolated testing of the moved logic.

**Planned Implementation:**

1.  **Create New Controller Skeletons:**
    *   **Task:** Create `src/controllers/project_controller.py`. Define `ProjectController(QObject)` class. Ensure `QObject` is imported from `PySide6.QtCore`. Update its `__init__` to accept `model: ApplicationModel`, `command_manager: CommandManager`, `config_service: ConfigService`.
    *   **Task:** Create `src/controllers/layout_controller.py`. Define `LayoutController(QObject)` class. Ensure `QObject` is imported from `PySide6.QtCore`. Update its `__init__` to accept `model: ApplicationModel`, `command_manager: CommandManager`, `layout_manager: LayoutManager`.
    *   **Task:** Create `src/controllers/node_controller.py`. Define `NodeController(QObject)` class. Ensure `QObject` is imported from `PySide6.QtCore`. Update its `__init__` to accept `model: ApplicationModel`, `command_manager: CommandManager`.

2.  **Move Logic from `MainController`:**
    *   **Task:** Cut all project/file-related methods (`save_project`, `open_project`, `create_new_layout`, `get_recent_files`, `_add_to_recent_files`) from `src/controllers/main_controller.py` and paste them into `src/controllers/project_controller.py`.
    *   **Task:** Cut all layout-related methods (`set_layout_mode`, `toggle_layout_mode`, `align_selected_plots`, `distribute_selected_plots`, `apply_grid_layout_from_ui`, `snap_free_plots_to_grid_action`, `update_grid_parameters`, `apply_default_grid_layout`) from `src/controllers/main_controller.py` and paste them into `src/controllers/layout_controller.py`.
    *   **Task:** Update the `__init__` methods of the new controllers to accept their required dependencies (e.g., `model`, `command_manager`, `layout_manager`, `config_service`). Ensure all necessary imports are added to the new controller files.

3.  **Move Logic from `PropertiesPanel`:**
    *   **Task:** Cut all property-handling methods (`_on_plot_type_changed`, `_on_property_changed`, `_on_limit_editing_finished`, `_on_column_mapping_changed`) from `src/ui/panels/properties_panel.py` and paste them into `src/controllers/node_controller.py`.
    *   **Task:** Rename them to be public methods (e.g., `on_plot_type_changed`, `on_property_changed`). Adjust their signatures to accept the necessary parameters (e.g., `node`, `new_value`, `widget`). Ensure all necessary imports are added to the new controller file.

4.  **Create Temporary Delegations (Shim/Facade Pattern):**
    *   **Task:** In `src/controllers/main_controller.py`, keep the method signatures but change their implementation to simply instantiate the new controllers and delegate the calls to the corresponding method in `ProjectController` or `LayoutController`. The `MainController` will temporarily need to hold instances of these new controllers.
    *   **Task:** In `src/ui/panels/properties_panel.py`, keep the `_on_*` methods as private slots, but have them delegate their calls to the public methods on the new `NodeController` instance (which will be passed in during a later phase).

**Testing Plan (Feature 1):**
*   **Unit Tests:** Create new test files (`tests/controllers/test_project_controller.py`, `tests/controllers/test_layout_controller.py`, `tests/controllers/test_node_controller.py`). Adapt the relevant existing unit tests from `tests/controllers/test_main_controller.py` and `tests/ui/panels/test_properties_panel.py` to verify the logic in its new, isolated location. Mock their dependencies as needed.
*   **Regression Tests:** Run all existing integration and end-to-end tests. They should **all still pass** because the UI wiring has not changed yet, and the `MainController`/`PropertiesPanel` are just forwarding calls.

---

#### **Feature 2: Re-wire Application Dependencies in `CompositionRoot`**
**Description:** Update the `CompositionRoot` to create and inject the new, specialized controllers directly into the components that need them, bypassing and ultimately removing the monolithic `MainController`.

**Planned Implementation:**

1.  **Modify `CompositionRoot` (`src/core/composition_root.py`):**
    *   **Task:** In `_assemble_core_components` (or a new `_assemble_controllers` method), instantiate `ProjectController`, `LayoutController`, and `NodeController`, providing them with their necessary dependencies (which `CompositionRoot` already has, like `model`, `command_manager`, `config_service`, `layout_manager`).
    *   **Task:** Remove the instantiation of `MainController`.
    *   **Task:** Update the `ApplicationComponents` dataclass (in `src/core/application_components.py`) to hold references to the new controllers instead of `main_controller`.
    *   **Task:** Update the instantiation of other components (`MenuBarBuilder`, `MainWindow`, `PropertiesPanel`, `CanvasController`) to inject the new, more specific controllers instead of `main_controller`. For example:
        *   `MenuBarBuilder` will now receive `project_controller` and `layout_controller`.
        *   `MainWindow` will receive `project_controller`, `layout_controller`, and `node_controller`.
        *   `PropertiesPanel` will receive `node_controller` and `layout_controller`.
        *   `CanvasController` will receive `layout_controller`.

2.  **Modify `_connect_signals` in `CompositionRoot`:**
    *   **Task:** Update all signal connections that previously pointed to `main_controller` to now point to the correct method on the new controllers.
        *   Example: `self._view.save_project_action.triggered.connect(...)` will now connect to `self._project_controller.save_project`.
        *   Example: Connections from `PropertiesPanel` or `MainWindow` UI elements related to layout will go to `layout_controller`.

**Testing Plan (Feature 2):**
-   **Unit Tests:** Update unit tests for `CompositionRoot` to verify it correctly instantiates and injects the new controllers.
-   **Regression Tests:** Run all existing integration and end-to-end tests. They should **all still pass**, as the application should be functionally identical, just with better internal wiring.

---

#### **Feature 3: Simplify UI Components (Final Cleanup)**
**Description:** Remove the temporary delegation logic from `PropertiesPanel` and delete the `MainController` file, completing the refactor and leaving the UI components as true "views" that are driven by their respective controllers.

**Planned Implementation:**

1.  **Refactor `PropertiesPanel` (`src/ui/panels/properties_panel.py`):**
    *   **Task:** Remove the now-redundant `_on_*` delegation methods.
    *   **Task:** The `PropertiesUIFactory` (and its builder functions) will be modified to return widgets that emit semantic signals (e.g., `titleChanged(str)`). The `NodeController` (or its UI Builder, if applicable) will be responsible for creating the UI elements via the factory, and then *connecting those signals directly* to its own slots (e.g., `node_controller.on_title_changed`).
    *   **Task:** Simplify the `PropertiesPanel.__init__` method. It will receive `node_controller`, `layout_controller`, `properties_ui_factory`, and `layout_ui_factory` as dependencies, but will no longer contain direct controller logic itself. Its `_update_content` method will delegate UI construction directly to the factories, passing the appropriate controllers as context for wiring signals.

2.  **Delete `MainController`:**
    *   **Task:** Delete the file `src/controllers/main_controller.py`.

**Testing Plan (Phase 3):**
-   **Unit Tests:** Update unit tests for `PropertiesPanel` to reflect its new, simpler role as a UI container. Update tests for `PropertiesUIFactory` to ensure it returns widgets with appropriate signals.
-   **Regression Tests:** Run all integration and end-to-end tests again to ensure no functionality was broken during the final cleanup and re-wiring.

---
